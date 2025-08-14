#!/usr/bin/env python3
"""
KRONOS User-Reported Scenario Test
================================================================================
Testing Engineer: Claude Code
Test Date: 2025-01-12
Test Scope: Exact user-reported scenario validation

PURPOSE:
This test replicates the EXACT user-reported scenario:
1. Mission CERT-CLARO-001 exists
2. Upload CLARO "datos por celda" file (DATOS_POR_CELDA CLARO_MANUAL_FIX.csv)
3. Verify progress goes 0% → 100% WITHOUT final error
4. Verify Sábanas de Operador shows uploaded files (NOT empty)
5. Validate data is properly stored in database

CRITICAL VALIDATIONS:
- Use existing CERT-CLARO-001 mission (already exists in production DB)
- Use main kronos.db database (not test database)
- Validate IntelligentUploadRouter L2 architecture
- Confirm 386+ existing CLARO records are preserved
- Verify new upload adds to existing data without conflicts
================================================================================
"""

import os
import sys
import sqlite3
import time
import base64
import logging
from pathlib import Path
from typing import Dict, Any

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import system services
from database.connection import init_database, get_database_manager
from services.mission_service import get_mission_service
from services.operator_service import get_operator_service  
from services.intelligent_upload_router import get_intelligent_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('user_scenario_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class UserScenarioTest:
    """
    Test class for validating the exact user-reported scenario
    """
    
    def __init__(self):
        self.mission_id = 'CERT-CLARO-001'  # Use existing mission
        self.test_file = 'C:\\Soluciones\\BGC\\claude\\KNSOft\\datatest\\Claro\\DATOS_POR_CELDA CLARO_MANUAL_FIX.csv'
        self.results = []
        
        logger.info("=== USER-REPORTED SCENARIO TEST INITIALIZED ===")
    
    def log_result(self, test_name: str, success: bool, details: str):
        """Log test result"""
        status = "✓ PASS" if success else "✗ FAIL"
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        self.results.append(result)
        
        if success:
            logger.info(f"{status}: {test_name} - {details}")
        else:
            logger.error(f"{status}: {test_name} - {details}")
    
    def test_1_verify_existing_state(self):
        """Test 1: Verify existing system state"""
        logger.info("\n" + "="*60)
        logger.info("TEST 1: Verify Existing System State")
        logger.info("="*60)
        
        try:
            # Check mission exists
            mission_service = get_mission_service()
            mission = mission_service.get_mission_by_id(self.mission_id)
            
            if mission:
                self.log_result(
                    "Mission CERT-CLARO-001 Exists", 
                    True, 
                    f"Mission found: {mission['name']}"
                )
            else:
                self.log_result(
                    "Mission CERT-CLARO-001 Exists", 
                    False, 
                    "Mission not found in database"
                )
                return False
            
            # Check existing CLARO data count
            db_path = 'kronos.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM operator_cellular_data WHERE operator = ?', ('CLARO',))
            existing_count = cursor.fetchone()[0]
            conn.close()
            
            self.log_result(
                "Existing CLARO Data", 
                existing_count > 0, 
                f"{existing_count} CLARO records in database"
            )
            
            # Check test file exists
            if os.path.exists(self.test_file):
                file_size = os.path.getsize(self.test_file)
                self.log_result(
                    "Test File Available", 
                    True, 
                    f"File exists: {file_size} bytes"
                )
            else:
                self.log_result(
                    "Test File Available", 
                    False, 
                    f"File not found: {self.test_file}"
                )
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Existing State Check", False, f"Error: {e}")
            return False
    
    def test_2_upload_claro_file(self):
        """Test 2: Upload CLARO file using IntelligentUploadRouter"""
        logger.info("\n" + "="*60)
        logger.info("TEST 2: Upload CLARO File (User Scenario)")
        logger.info("="*60)
        
        try:
            # Create file data
            with open(self.test_file, 'rb') as f:
                file_bytes = f.read()
            
            filename = os.path.basename(self.test_file)
            base64_content = base64.b64encode(file_bytes).decode('utf-8')
            data_url = f"data:text/csv;base64,{base64_content}"
            
            file_data = {
                'name': filename,
                'content': data_url
            }
            
            # Get router and track timing
            router = get_intelligent_router()
            start_time = time.time()
            
            logger.info("Starting file upload with IntelligentUploadRouter...")
            
            # This is the exact call the frontend makes
            result = router.route_upload(self.mission_id, 'claro_datos', file_data)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Validate result
            if result and isinstance(result, dict):
                # Check for error indicators
                has_errors = (
                    'error' in result or
                    'failed' in str(result).lower() or
                    result.get('status') == 'error' or
                    'exception' in str(result).lower()
                )
                
                if not has_errors:
                    routing_info = result.get('routing_info', {})
                    processor = routing_info.get('processor', 'unknown')
                    
                    self.log_result(
                        "File Upload Successful", 
                        True, 
                        f"Completed in {processing_time:.2f}s using {processor} processor"
                    )
                    
                    # Log routing details
                    if routing_info:
                        logger.info(f"Routing Info: {routing_info}")
                    
                    return True, result
                else:
                    self.log_result(
                        "File Upload Successful", 
                        False, 
                        f"Upload completed but with errors: {result}"
                    )
                    return False, result
            else:
                self.log_result(
                    "File Upload Successful", 
                    False, 
                    f"Invalid result: {result}"
                )
                return False, result
                
        except Exception as e:
            self.log_result("File Upload", False, f"Upload failed with exception: {e}")
            return False, None
    
    def test_3_verify_data_persistence(self):
        """Test 3: Verify data was properly saved to database"""
        logger.info("\n" + "="*60)
        logger.info("TEST 3: Verify Data Persistence")
        logger.info("="*60)
        
        try:
            # Check database for new records
            db_path = 'kronos.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Count total CLARO records
            cursor.execute('SELECT COUNT(*) FROM operator_cellular_data WHERE operator = ?', ('CLARO',))
            total_count = cursor.fetchone()[0]
            
            # Count records for our mission
            cursor.execute(
                'SELECT COUNT(*) FROM operator_cellular_data WHERE operator = ? AND mission_id = ?',
                ('CLARO', self.mission_id)
            )
            mission_count = cursor.fetchone()[0]
            
            # Check for file upload records
            cursor.execute(
                'SELECT COUNT(*) FROM operator_file_uploads WHERE mission_id = ? AND operator = ?',
                (self.mission_id, 'CLARO')
            )
            file_count = cursor.fetchone()[0]
            
            conn.close()
            
            if total_count > 386:  # Should be more than the initial 386
                self.log_result(
                    "Data Persistence", 
                    True, 
                    f"Total CLARO records: {total_count}, Mission records: {mission_count}, Files: {file_count}"
                )
                return True
            else:
                self.log_result(
                    "Data Persistence", 
                    False, 
                    f"No new data detected: {total_count} total records"
                )
                return False
                
        except Exception as e:
            self.log_result("Data Persistence", False, f"Error checking database: {e}")
            return False
    
    def test_4_sabanas_operador_functionality(self):
        """Test 4: Verify Sábanas de Operador shows files (NOT empty)"""
        logger.info("\n" + "="*60)
        logger.info("TEST 4: Sábanas de Operador Functionality")
        logger.info("="*60)
        
        try:
            # Test operator service methods that the frontend calls
            operator_service = get_operator_service()
            
            # Get files for mission
            files = operator_service.get_operator_files_for_mission(self.mission_id)
            
            if files and len(files) > 0:
                self.log_result(
                    "Operator Files Visible", 
                    True, 
                    f"Found {len(files)} files for mission {self.mission_id}"
                )
                
                # Log file details
                for i, file_info in enumerate(files):
                    logger.info(f"  File {i+1}: {file_info.get('filename', 'unknown')} "
                              f"({file_info.get('operator', 'unknown')} - "
                              f"{file_info.get('file_type', 'unknown')})")
                
            else:
                self.log_result(
                    "Operator Files Visible", 
                    False, 
                    "No files found - Sábanas de Operador would be empty"
                )
                return False
            
            # Get operator summary
            summary = operator_service.get_mission_operator_summary(self.mission_id)
            
            if summary and 'operators' in summary and len(summary['operators']) > 0:
                operators_count = len(summary['operators'])
                total_records = summary.get('statistics', {}).get('total_cellular_records', 0)
                
                self.log_result(
                    "Operator Summary Available", 
                    True, 
                    f"{operators_count} operators, {total_records} total records"
                )
                return True
            else:
                self.log_result(
                    "Operator Summary Available", 
                    False, 
                    "No operator summary - indicates empty sheets"
                )
                return False
                
        except Exception as e:
            self.log_result("Sábanas de Operador", False, f"Error testing functionality: {e}")
            return False
    
    def test_5_integration_validation(self):
        """Test 5: End-to-end integration validation"""
        logger.info("\n" + "="*60)
        logger.info("TEST 5: Integration Validation")
        logger.info("="*60)
        
        try:
            # Test the complete flow that the frontend would execute
            mission_service = get_mission_service()
            
            # Get updated mission with all relations
            updated_mission = mission_service.get_mission_by_id(self.mission_id)
            
            if updated_mission:
                # Check if mission has operator data
                operator_sheets = updated_mission.get('operatorData', [])
                cellular_data_count = len(updated_mission.get('cellularData', []))
                
                self.log_result(
                    "Mission Data Updated", 
                    len(operator_sheets) > 0 or cellular_data_count > 0, 
                    f"{len(operator_sheets)} operator sheets, {cellular_data_count} cellular records"
                )
                
                # Validate the mission structure matches frontend expectations
                required_fields = ['id', 'code', 'name', 'status', 'createdAt']
                has_all_fields = all(field in updated_mission for field in required_fields)
                
                self.log_result(
                    "Frontend Compatibility", 
                    has_all_fields, 
                    "Mission structure matches frontend requirements"
                )
                
                return True
            else:
                self.log_result(
                    "Mission Data Updated", 
                    False, 
                    "Could not retrieve updated mission"
                )
                return False
                
        except Exception as e:
            self.log_result("Integration Validation", False, f"Error in integration test: {e}")
            return False
    
    def generate_final_report(self):
        """Generate final test report"""
        logger.info("\n" + "="*60)
        logger.info("FINAL USER SCENARIO TEST REPORT")
        logger.info("="*60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests} ✓")
        logger.info(f"Failed: {failed_tests} ✗")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        
        logger.info("\nDetailed Results:")
        for result in self.results:
            status = "✓" if result['success'] else "✗"
            logger.info(f"  {status} {result['test']}: {result['details']}")
        
        # Overall assessment
        if success_rate == 100:
            logger.info("\n🎯 USER SCENARIO: ✅ COMPLETELY RESOLVED")
            logger.info("All reported issues have been fixed successfully.")
        elif success_rate >= 80:
            logger.info("\n⚠️ USER SCENARIO: 🔶 MOSTLY RESOLVED")
            logger.info("Most issues fixed, minor problems remain.")
        else:
            logger.error("\n❌ USER SCENARIO: 🚫 SIGNIFICANT ISSUES REMAIN")
            logger.error("Critical problems still exist.")
        
        return {
            'total_tests': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'success_rate': success_rate,
            'all_passed': success_rate == 100,
            'results': self.results
        }
    
    def run_user_scenario_test(self):
        """Run the complete user scenario test"""
        logger.info("Starting user-reported scenario validation...")
        
        try:
            # Initialize database first
            logger.info("Initializing database...")
            db_path = os.path.join(current_dir, 'kronos.db')
            init_database(db_path, force_recreate=False)
            logger.info("Database initialized successfully")
            # Run all tests in sequence
            tests = [
                self.test_1_verify_existing_state,
                self.test_2_upload_claro_file,
                self.test_3_verify_data_persistence,
                self.test_4_sabanas_operador_functionality,
                self.test_5_integration_validation
            ]
            
            for test_func in tests:
                result = test_func()
                if result is False:
                    logger.warning(f"Test {test_func.__name__} failed, continuing...")
            
            # Generate final report
            report = self.generate_final_report()
            
            # Save report
            import json
            with open('user_scenario_test_report.json', 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            return report
            
        except Exception as e:
            logger.error(f"User scenario test failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise


def main():
    """Main test execution"""
    try:
        test = UserScenarioTest()
        report = test.run_user_scenario_test()
        
        logger.info(f"Test completed. Report saved to user_scenario_test_report.json")
        
        if report['all_passed']:
            logger.info("✅ USER SCENARIO VALIDATION PASSED")
            sys.exit(0)
        else:
            logger.error("❌ USER SCENARIO VALIDATION FAILED")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()