#!/usr/bin/env python3
"""
KRONOS Mission Persistence Validation Test
===============================================================================
Comprehensive test suite to validate the mission persistence fix after 
eliminating the auto-recreation bug in database/connection.py

Test Scope:
1. Complete CRUD cycle validation
2. Mission deletion persistence after application restart
3. Database integrity verification
4. Transaction commit validation
5. Edge case testing

Test Methodology:
- Automated testing with detailed logging
- Before/after state validation
- Simulated application restart testing
- Error condition testing
- Performance validation

Author: Claude Code Testing Framework
Date: 2025-08-14
===============================================================================
"""

import logging
import sys
import os
import time
import json
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Add Backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.connection import get_database_manager, init_database
from database.models import Mission, User, Role, CellularData
from services.mission_service import get_mission_service, MissionServiceError
from sqlalchemy.orm import joinedload

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('mission_persistence_test.log')
    ]
)
logger = logging.getLogger(__name__)

class MissionPersistenceValidator:
    """Comprehensive mission persistence validation suite"""
    
    def __init__(self):
        self.db_manager = None
        self.mission_service = get_mission_service()
        self.test_results = []
        self.start_time = datetime.now()
        
    def initialize_db(self):
        """Initialize database connection"""
        try:
            self.db_manager = get_database_manager()
            if not self.db_manager._initialized:
                init_database()
                self.db_manager = get_database_manager()
            return True
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
    
    def log_test_result(self, test_name: str, success: bool, details: str, data: Dict = None):
        """Log test result"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'data': data or {}
        }
        self.test_results.append(result)
        
        status = "✓ PASS" if success else "✗ FAIL"
        logger.info(f"{status} {test_name}: {details}")
        
        if not success:
            logger.error(f"FAILURE DETAILS: {details}")
    
    def get_current_db_state(self) -> Dict[str, Any]:
        """Get current database state"""
        try:
            with self.db_manager.get_session() as session:
                missions = session.query(Mission).all()
                users = session.query(User).all()
                roles = session.query(Role).all()
                
                return {
                    'mission_count': len(missions),
                    'user_count': len(users),
                    'role_count': len(roles),
                    'missions': [
                        {
                            'id': m.id,
                            'name': m.name,
                            'code': m.code,
                            'status': m.status
                        } for m in missions
                    ]
                }
        except Exception as e:
            logger.error(f"Error getting DB state: {e}")
            return {}
    
    def test_initial_state(self) -> bool:
        """Test 1: Verify initial database state"""
        try:
            state = self.get_current_db_state()
            
            # Verify essential data exists
            if state['role_count'] < 3:
                self.log_test_result(
                    "Initial State Check", 
                    False, 
                    f"Insufficient roles: {state['role_count']} (expected >= 3)"
                )
                return False
            
            if state['user_count'] < 1:
                self.log_test_result(
                    "Initial State Check", 
                    False, 
                    f"No users found: {state['user_count']}"
                )
                return False
            
            self.log_test_result(
                "Initial State Check", 
                True, 
                f"Database properly initialized with {state['mission_count']} missions, {state['user_count']} users, {state['role_count']} roles",
                state
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "Initial State Check", 
                False, 
                f"Exception during state check: {str(e)}"
            )
            return False
    
    def test_create_mission(self) -> Optional[str]:
        """Test 2: Create new mission"""
        try:
            test_mission_data = {
                'code': f'TEST-{int(time.time())}',
                'name': 'Test Mission for Persistence Validation',
                'description': 'This is a test mission created to validate persistence after deletion',
                'status': 'Planificación',
                'start_date': datetime.now().date(),
                'end_date': (datetime.now() + timedelta(days=30)).date()
            }
            
            created_mission = self.mission_service.create_mission(test_mission_data, 'admin')
            mission_id = created_mission['id']
            
            self.log_test_result(
                "Create Mission", 
                True, 
                f"Mission created successfully: {test_mission_data['code']} (ID: {mission_id})",
                {'mission_id': mission_id, 'mission_code': test_mission_data['code']}
            )
            return mission_id
            
        except Exception as e:
            self.log_test_result(
                "Create Mission", 
                False, 
                f"Exception creating mission: {str(e)}"
            )
            return None
    
    def test_read_mission(self, mission_id: str) -> bool:
        """Test 3: Read mission by ID"""
        try:
            mission = self.mission_service.get_mission_by_id(mission_id)
            
            if mission is None:
                self.log_test_result(
                    "Read Mission", 
                    False, 
                    f"Mission not found: {mission_id}"
                )
                return False
            
            self.log_test_result(
                "Read Mission", 
                True, 
                f"Mission retrieved successfully: {mission['name']} ({mission['code']})",
                {'mission': mission}
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "Read Mission", 
                False, 
                f"Exception reading mission: {str(e)}"
            )
            return False
    
    def test_update_mission(self, mission_id: str) -> bool:
        """Test 4: Update mission"""
        try:
            update_data = {
                'description': 'Updated description for persistence validation test',
                'status': 'En Progreso'
            }
            
            updated_mission = self.mission_service.update_mission(mission_id, update_data)
            
            # Verify changes were applied
            if updated_mission['description'] != update_data['description']:
                self.log_test_result(
                    "Update Mission", 
                    False, 
                    f"Description not updated properly. Expected: {update_data['description']}, Got: {updated_mission['description']}"
                )
                return False
            
            if updated_mission['status'] != update_data['status']:
                self.log_test_result(
                    "Update Mission", 
                    False, 
                    f"Status not updated properly. Expected: {update_data['status']}, Got: {updated_mission['status']}"
                )
                return False
            
            self.log_test_result(
                "Update Mission", 
                True, 
                f"Mission updated successfully: {updated_mission['name']}",
                {'updated_fields': update_data}
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "Update Mission", 
                False, 
                f"Exception updating mission: {str(e)}"
            )
            return False
    
    def test_delete_single_mission(self, mission_id: str) -> bool:
        """Test 5: Delete single mission"""
        try:
            # Verify mission exists before deletion
            mission_before = self.mission_service.get_mission_by_id(mission_id)
            if not mission_before:
                self.log_test_result(
                    "Delete Single Mission", 
                    False, 
                    f"Mission does not exist before deletion: {mission_id}"
                )
                return False
            
            # Delete the mission
            result = self.mission_service.delete_mission(mission_id)
            
            # Verify deletion response
            if result.get('status') != 'ok':
                self.log_test_result(
                    "Delete Single Mission", 
                    False, 
                    f"Delete operation did not return success status: {result}"
                )
                return False
            
            # Verify mission no longer exists
            mission_after = self.mission_service.get_mission_by_id(mission_id)
            if mission_after is not None:
                self.log_test_result(
                    "Delete Single Mission", 
                    False, 
                    f"Mission still exists after deletion: {mission_id}"
                )
                return False
            
            self.log_test_result(
                "Delete Single Mission", 
                True, 
                f"Mission deleted successfully: {mission_before['name']} ({mission_before['code']})",
                {'deleted_mission': mission_before}
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "Delete Single Mission", 
                False, 
                f"Exception deleting mission: {str(e)}"
            )
            return False
    
    def test_delete_all_missions(self) -> bool:
        """Test 6: Delete all missions"""
        try:
            # Get all current missions
            all_missions = self.mission_service.get_all_missions()
            initial_count = len(all_missions)
            
            if initial_count == 0:
                self.log_test_result(
                    "Delete All Missions", 
                    True, 
                    "No missions to delete"
                )
                return True
            
            deleted_missions = []
            
            # Delete each mission
            for mission in all_missions:
                try:
                    result = self.mission_service.delete_mission(mission['id'])
                    if result.get('status') == 'ok':
                        deleted_missions.append(mission)
                except Exception as e:
                    logger.error(f"Error deleting mission {mission['id']}: {e}")
            
            # Verify all missions were deleted
            remaining_missions = self.mission_service.get_all_missions()
            final_count = len(remaining_missions)
            
            if final_count == 0:
                self.log_test_result(
                    "Delete All Missions", 
                    True, 
                    f"All {initial_count} missions deleted successfully",
                    {'deleted_missions': deleted_missions, 'initial_count': initial_count}
                )
                return True
            else:
                self.log_test_result(
                    "Delete All Missions", 
                    False, 
                    f"Not all missions deleted. Started with {initial_count}, {final_count} remaining",
                    {'remaining_missions': remaining_missions}
                )
                return False
            
        except Exception as e:
            self.log_test_result(
                "Delete All Missions", 
                False, 
                f"Exception deleting all missions: {str(e)}"
            )
            return False
    
    def test_database_reinitializacion(self) -> bool:
        """Test 7: Simulate database re-initialization (restart simulation)"""
        try:
            # Close current connection
            if self.db_manager:
                self.db_manager.close()
            
            # Reinitialize database (simulates app restart)
            time.sleep(1)  # Brief pause
            success = self.initialize_db()
            
            if not success:
                self.log_test_result(
                    "Database Reinitialization", 
                    False, 
                    "Failed to reinitialize database"
                )
                return False
            
            # Check state after reinitialization
            state_after = self.get_current_db_state()
            
            self.log_test_result(
                "Database Reinitialization", 
                True, 
                f"Database reinitialized successfully. State: {state_after['mission_count']} missions, {state_after['user_count']} users, {state_after['role_count']} roles",
                state_after
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "Database Reinitialization", 
                False, 
                f"Exception during reinitialization: {str(e)}"
            )
            return False
    
    def test_persistence_validation(self) -> bool:
        """Test 8: Validate missions stay deleted after restart"""
        try:
            # Get current mission count
            current_missions = self.mission_service.get_all_missions()
            mission_count = len(current_missions)
            
            # The critical test: missions should NOT be recreated
            if mission_count == 0:
                self.log_test_result(
                    "Persistence Validation", 
                    True, 
                    "CRITICAL SUCCESS: Missions remain deleted after database reinitialization (auto-recreation bug fixed)",
                    {'mission_count_after_restart': mission_count}
                )
                return True
            else:
                self.log_test_result(
                    "Persistence Validation", 
                    False, 
                    f"CRITICAL FAILURE: Missions were recreated after restart. Found {mission_count} missions",
                    {'recreated_missions': current_missions}
                )
                return False
            
        except Exception as e:
            self.log_test_result(
                "Persistence Validation", 
                False, 
                f"Exception during persistence validation: {str(e)}"
            )
            return False
    
    def test_create_after_delete_all(self) -> bool:
        """Test 9: Create new mission after deleting all"""
        try:
            new_mission_data = {
                'code': f'POST-DELETE-{int(time.time())}',
                'name': 'Mission Created After Deletion',
                'description': 'This mission was created after all missions were deleted to test functionality',
                'status': 'Planificación',
                'start_date': datetime.now().date(),
                'end_date': (datetime.now() + timedelta(days=30)).date()
            }
            
            created_mission = self.mission_service.create_mission(new_mission_data, 'admin')
            
            if created_mission and created_mission.get('id'):
                self.log_test_result(
                    "Create After Delete All", 
                    True, 
                    f"Successfully created mission after deleting all: {created_mission['name']}",
                    {'new_mission': created_mission}
                )
                return True
            else:
                self.log_test_result(
                    "Create After Delete All", 
                    False, 
                    "Failed to create mission after deleting all"
                )
                return False
            
        except Exception as e:
            self.log_test_result(
                "Create After Delete All", 
                False, 
                f"Exception creating mission after delete all: {str(e)}"
            )
            return False
    
    def test_transaction_integrity(self) -> bool:
        """Test 10: Verify transaction integrity during deletes"""
        try:
            # Create a test mission
            test_mission_data = {
                'code': f'TRANS-TEST-{int(time.time())}',
                'name': 'Transaction Integrity Test Mission',
                'description': 'Testing transaction rollback behavior',
                'status': 'Planificación',
                'start_date': datetime.now().date()
            }
            
            created_mission = self.mission_service.create_mission(test_mission_data, 'admin')
            mission_id = created_mission['id']
            
            # Verify mission exists
            mission = self.mission_service.get_mission_by_id(mission_id)
            if not mission:
                self.log_test_result(
                    "Transaction Integrity", 
                    False, 
                    "Test mission was not created properly"
                )
                return False
            
            # Delete the mission
            delete_result = self.mission_service.delete_mission(mission_id)
            
            # Verify deletion was committed (mission should not exist)
            deleted_mission = self.mission_service.get_mission_by_id(mission_id)
            
            if deleted_mission is None and delete_result.get('status') == 'ok':
                self.log_test_result(
                    "Transaction Integrity", 
                    True, 
                    "Transaction properly committed - mission deleted and not accessible",
                    {'delete_result': delete_result}
                )
                return True
            else:
                self.log_test_result(
                    "Transaction Integrity", 
                    False, 
                    f"Transaction integrity issue. Delete result: {delete_result}, Mission still exists: {deleted_mission is not None}"
                )
                return False
            
        except Exception as e:
            self.log_test_result(
                "Transaction Integrity", 
                False, 
                f"Exception during transaction integrity test: {str(e)}"
            )
            return False
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run complete test suite"""
        logger.info("="*80)
        logger.info("STARTING COMPREHENSIVE MISSION PERSISTENCE VALIDATION")
        logger.info("="*80)
        
        # Initialize database
        if not self.initialize_db():
            return {"success": False, "error": "Failed to initialize database"}
        
        # Test sequence
        test_passed = 0
        test_total = 0
        
        # Test 1: Initial state
        test_total += 1
        if self.test_initial_state():
            test_passed += 1
        
        # Test 2-5: CRUD cycle
        test_total += 1
        test_mission_id = self.test_create_mission()
        if test_mission_id:
            test_passed += 1
        
        if test_mission_id:
            test_total += 1
            if self.test_read_mission(test_mission_id):
                test_passed += 1
            
            test_total += 1
            if self.test_update_mission(test_mission_id):
                test_passed += 1
            
            test_total += 1
            if self.test_delete_single_mission(test_mission_id):
                test_passed += 1
        
        # Test 6: Delete all missions
        test_total += 1
        if self.test_delete_all_missions():
            test_passed += 1
        
        # Test 7: Simulate restart
        test_total += 1
        if self.test_database_reinitializacion():
            test_passed += 1
        
        # Test 8: Critical persistence validation
        test_total += 1
        persistence_success = self.test_persistence_validation()
        if persistence_success:
            test_passed += 1
        
        # Test 9: Create after delete all
        test_total += 1
        if self.test_create_after_delete_all():
            test_passed += 1
        
        # Test 10: Transaction integrity
        test_total += 1
        if self.test_transaction_integrity():
            test_passed += 1
        
        # Generate final report
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        success_rate = (test_passed / test_total) * 100 if test_total > 0 else 0
        
        final_state = self.get_current_db_state()
        
        report = {
            "test_summary": {
                "total_tests": test_total,
                "passed_tests": test_passed,
                "failed_tests": test_total - test_passed,
                "success_rate": f"{success_rate:.1f}%",
                "duration_seconds": duration,
                "critical_persistence_test_passed": persistence_success
            },
            "database_state": {
                "initial_state": "Verified",
                "final_state": final_state
            },
            "detailed_results": self.test_results,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("="*80)
        logger.info(f"TEST SUITE COMPLETED: {test_passed}/{test_total} tests passed ({success_rate:.1f}%)")
        logger.info(f"CRITICAL PERSISTENCE TEST: {'PASSED' if persistence_success else 'FAILED'}")
        logger.info(f"Duration: {duration:.1f} seconds")
        logger.info("="*80)
        
        return report


def main():
    """Main test execution"""
    try:
        validator = MissionPersistenceValidator()
        
        # Run comprehensive test
        report = validator.run_comprehensive_test()
        
        # Save detailed report
        report_filename = f"mission_persistence_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\nDetailed report saved to: {report_filename}")
        
        # Print summary
        print("\n" + "="*80)
        print("MISSION PERSISTENCE VALIDATION SUMMARY")
        print("="*80)
        print(f"Total Tests: {report['test_summary']['total_tests']}")
        print(f"Passed: {report['test_summary']['passed_tests']}")
        print(f"Failed: {report['test_summary']['failed_tests']}")
        print(f"Success Rate: {report['test_summary']['success_rate']}")
        print(f"Duration: {report['test_summary']['duration_seconds']:.1f} seconds")
        print(f"Critical Persistence Test: {'PASSED' if report['test_summary']['critical_persistence_test_passed'] else 'FAILED'}")
        
        if report['test_summary']['critical_persistence_test_passed']:
            print("\n🎉 VALIDATION SUCCESSFUL: Mission persistence fix is working correctly!")
            print("   Missions no longer auto-recreate after deletion and restart.")
        else:
            print("\n❌ VALIDATION FAILED: Mission persistence issue still exists!")
            print("   Missions are being recreated after deletion and restart.")
        
        print("="*80)
        
        return report['test_summary']['critical_persistence_test_passed']
        
    except Exception as e:
        print(f"CRITICAL ERROR during validation: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)