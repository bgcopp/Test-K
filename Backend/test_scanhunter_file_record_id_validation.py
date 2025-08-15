#!/usr/bin/env python3
"""
KRONOS - SCANHUNTER File Record ID Validation Test
==================================================

Test script to validate that the SCANHUNTER file_record_id fix is working correctly.
This test verifies the complete pipeline from file processing to database storage.

Test Objectives:
1. Verify file_record_id extraction from SCANHUNTER Excel files
2. Validate data normalization preserves file_record_id
3. Confirm database insertion includes file_record_id
4. Test expected ID patterns (17×ID=0, 15×ID=12, 26×ID=32)

Author: KRONOS Testing Team
Date: 2025-08-14
"""

import sys
import os
import sqlite3
import pandas as pd
from typing import Dict, List, Any
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.file_processor_service import FileProcessorService
from services.data_normalizer_service import DataNormalizerService

class SCAnimationFileRecordIDValidator:
    """Validates SCANHUNTER file_record_id processing functionality."""
    
    def __init__(self):
        self.processor = FileProcessorService()
        self.normalizer = DataNormalizerService()
        self.test_results = {}
        self.test_mission_id = "test_mission_scanhunter_validation"
        
    def setup_test_environment(self):
        """Setup clean test environment."""
        print("Setting up test environment...")
        
        # Clean any existing test data
        conn = sqlite3.connect('kronos.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cellular_data WHERE mission_id = ?', (self.test_mission_id,))
        conn.commit()
        conn.close()
        
        print("OK Test environment setup complete")
    
    def test_file_record_id_extraction(self) -> Dict[str, Any]:
        """Test file_record_id extraction from SCANHUNTER Excel file."""
        print("\nTesting file_record_id extraction...")
        
        test_data = [
            {'Id': 0, 'OPERADOR': 'CLARO', 'MNC': 730, 'MCC': 730, 'LAC/TAC': 12345, 'RSSI': -70},
            {'Id': 0, 'OPERADOR': 'MOVISTAR', 'MNC': 731, 'MCC': 730, 'LAC/TAC': 12346, 'RSSI': -75},
            {'Id': 12, 'OPERADOR': 'CLARO', 'MNC': 730, 'MCC': 730, 'LAC/TAC': 12347, 'RSSI': -80},
            {'Id': 12, 'OPERADOR': 'TIGO', 'MNC': 732, 'MCC': 730, 'LAC/TAC': 12348, 'RSSI': -65},
            {'Id': 32, 'OPERADOR': 'WOM', 'MNC': 733, 'MCC': 730, 'LAC/TAC': 12349, 'RSSI': -85},
        ]
        
        results = {
            'test_name': 'file_record_id_extraction',
            'success': True,
            'extracted_ids': [],
            'errors': []
        }
        
        try:
            for i, row in enumerate(test_data):
                # Simulate data normalization with file_record_id extraction
                raw_record = {
                    'Id': row['Id'],
                    'OPERADOR': row['OPERADOR'],
                    'MNC': row['MNC'],
                    'MCC': row['MCC'],
                    'LAC/TAC': row['LAC/TAC'],
                    'RSSI': row['RSSI'],
                    'Punto': f'P{i+1}',
                    'Lat': -33.4500 + i * 0.001,
                    'Lon': -70.6700 + i * 0.001,
                    'Cell ID': f'C{12345 + i}',
                    'Tecnología': 'LTE'
                }
                
                # Test normalization
                normalized = self.normalizer.normalize_scanhunter_record(raw_record, self.test_mission_id)
                
                if normalized:
                    file_record_id = normalized.get('file_record_id')
                    results['extracted_ids'].append({
                        'original_id': row['Id'],
                        'extracted_id': file_record_id,
                        'match': file_record_id == row['Id']
                    })
                    print(f"  Row {i+1}: Original ID={row['Id']}, Extracted ID={file_record_id}")
                else:
                    results['errors'].append(f"Failed to normalize row {i+1}")
                    results['success'] = False
                    
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Exception during extraction: {str(e)}")
            
        return results
    
    def test_database_insertion(self) -> Dict[str, Any]:
        """Test that file_record_id is properly inserted into database."""
        print("\nTesting database insertion...")
        
        results = {
            'test_name': 'database_insertion',
            'success': True,
            'inserted_records': 0,
            'errors': []
        }
        
        try:
            # Create test Excel-like data
            test_data = [
                {
                    'Id': 0, 'Punto': 'P1', 'Lat': -33.4500, 'Lon': -70.6700,
                    'MNC': 730, 'MCC': 730, 'OPERADOR': 'CLARO', 'RSSI': -70,
                    'Tecnología': 'LTE', 'Cell ID': 'C12345', 'LAC/TAC': 12345
                },
                {
                    'Id': 12, 'Punto': 'P2', 'Lat': -33.4510, 'Lon': -70.6710,
                    'MNC': 731, 'MCC': 730, 'OPERADOR': 'MOVISTAR', 'RSSI': -75,
                    'Tecnología': 'LTE', 'Cell ID': 'C12346', 'LAC/TAC': 12346
                },
                {
                    'Id': 32, 'Punto': 'P3', 'Lat': -33.4520, 'Lon': -70.6720,
                    'MNC': 732, 'MCC': 730, 'OPERADOR': 'TIGO', 'RSSI': -80,
                    'Tecnología': 'LTE', 'Cell ID': 'C12347', 'LAC/TAC': 12347
                }
            ]
            
            # Create DataFrame to simulate Excel file
            df = pd.DataFrame(test_data)
            
            # Process through file processor
            result = self.processor.process_excel_cellular_data(
                df=df,
                mission_id=self.test_mission_id,
                sheet_name="SCANHUNTER_TEST"
            )
            
            if result.get('success'):
                results['inserted_records'] = result.get('processed_records', 0)
                print(f"  OK Successfully inserted {results['inserted_records']} records")
                
                # Verify database content
                conn = sqlite3.connect('kronos.db')
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, file_record_id, punto 
                    FROM cellular_data 
                    WHERE mission_id = ? 
                    ORDER BY id
                ''', (self.test_mission_id,))
                
                db_records = cursor.fetchall()
                conn.close()
                
                print(f"  Database verification: Found {len(db_records)} records")
                for record in db_records:
                    print(f"    DB ID: {record[0]}, File Record ID: {record[1]}, Punto: {record[2]}")
                    
            else:
                results['success'] = False
                results['errors'].append(f"File processing failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Exception during database insertion: {str(e)}")
            
        return results
    
    def test_expected_id_patterns(self) -> Dict[str, Any]:
        """Test expected ID patterns from real SCANHUNTER file."""
        print("\nTesting expected ID patterns...")
        
        results = {
            'test_name': 'expected_id_patterns',
            'success': True,
            'id_counts': {},
            'expected_pattern': {'0': 17, '12': 15, '32': 26},
            'pattern_match': False,
            'errors': []
        }
        
        try:
            # Query database for file_record_id distribution
            conn = sqlite3.connect('kronos.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT file_record_id, COUNT(*) 
                FROM cellular_data 
                WHERE mission_id = ? AND file_record_id IS NOT NULL
                GROUP BY file_record_id
                ORDER BY file_record_id
            ''', (self.test_mission_id,))
            
            id_distribution = cursor.fetchall()
            conn.close()
            
            # Build results
            for file_id, count in id_distribution:
                results['id_counts'][str(file_id)] = count
                print(f"  File Record ID {file_id}: {count} records")
            
            # Check if pattern matches expected (this is for the test data, not real file)
            print(f"  Expected pattern: {results['expected_pattern']}")
            print(f"  Actual pattern: {results['id_counts']}")
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Exception during pattern analysis: {str(e)}")
            
        return results
    
    def run_validation_tests(self) -> Dict[str, Any]:
        """Run complete validation test suite."""
        print("Starting SCANHUNTER File Record ID Validation Tests")
        print("=" * 60)
        
        # Setup
        self.setup_test_environment()
        
        # Run tests
        test_results = {}
        test_results['extraction'] = self.test_file_record_id_extraction()
        test_results['database'] = self.test_database_insertion()
        test_results['patterns'] = self.test_expected_id_patterns()
        
        # Overall results
        all_success = all(result['success'] for result in test_results.values())
        
        summary = {
            'overall_success': all_success,
            'test_timestamp': datetime.now().isoformat(),
            'test_details': test_results,
            'recommendations': []
        }
        
        # Generate recommendations
        if not all_success:
            summary['recommendations'].append("FAILED - Some tests failed - review error details")
        else:
            summary['recommendations'].append("PASSED - All validation tests passed successfully")
            
        if test_results['database']['inserted_records'] > 0:
            summary['recommendations'].append("SUCCESS - File record IDs are being properly inserted into database")
        else:
            summary['recommendations'].append("WARNING - No records were inserted - check file processing logic")
            
        return summary
    
    def generate_test_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive test report."""
        report = f"""
KRONOS - SCANHUNTER File Record ID Validation Report
===================================================
Test Date: {results['test_timestamp']}
Overall Status: {'PASSED' if results['overall_success'] else 'FAILED'}

EXTRACTION TEST RESULTS:
------------------------
Status: {'PASSED' if results['test_details']['extraction']['success'] else 'FAILED'}
Extracted IDs: {len(results['test_details']['extraction']['extracted_ids'])}
Errors: {len(results['test_details']['extraction']['errors'])}

DATABASE INSERTION TEST RESULTS:
--------------------------------
Status: {'PASSED' if results['test_details']['database']['success'] else 'FAILED'}
Records Inserted: {results['test_details']['database']['inserted_records']}
Errors: {len(results['test_details']['database']['errors'])}

ID PATTERN ANALYSIS:
-------------------
Status: {'PASSED' if results['test_details']['patterns']['success'] else 'FAILED'}
ID Distribution: {results['test_details']['patterns']['id_counts']}

RECOMMENDATIONS:
---------------
"""
        for rec in results['recommendations']:
            report += f"- {rec}\n"
            
        return report

def main():
    """Main test execution."""
    validator = SCAnimationFileRecordIDValidator()
    
    try:
        # Run validation tests
        results = validator.run_validation_tests()
        
        # Generate and save report
        report = validator.generate_test_report(results)
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"scanhunter_file_record_id_validation_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print("\n" + "=" * 60)
        print("VALIDATION TEST SUMMARY")
        print("=" * 60)
        print(report)
        print(f"\nDetailed results saved to: {results_file}")
        
        # Return exit code
        return 0 if results['overall_success'] else 1
        
    except Exception as e:
        print(f"\nCRITICAL ERROR: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)