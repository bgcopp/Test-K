#!/usr/bin/env python3
"""
SCANHUNTER File Record ID Fix - Direct Validation Test
======================================================

Simple, direct test to validate that the file_record_id fix is working correctly.

Author: KRONOS Testing Team
Date: 2025-08-14
"""

import sys
import os
import sqlite3
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.data_normalizer_service import DataNormalizerService

def test_file_record_id_extraction():
    """Test that file_record_id extraction works correctly."""
    print("Testing SCANHUNTER file_record_id extraction...")
    
    normalizer = DataNormalizerService()
    
    # Test with sample SCANHUNTER data using correct field names
    test_cases = [
        {'Id': 0, 'OPERADOR': 'CLARO', 'MNC': 730, 'MCC': 730, 'Punto': 'P1', 'Latitud': -33.4500, 'Longitud': -70.6700, 'RSSI': -70, 'CELLID': 'C12345', 'LAC/TAC': 12345, 'TECNOLOGIA': 'LTE'},
        {'Id': 12, 'OPERADOR': 'MOVISTAR', 'MNC': 731, 'MCC': 730, 'Punto': 'P2', 'Latitud': -33.4510, 'Longitud': -70.6710, 'RSSI': -75, 'CELLID': 'C12346', 'LAC/TAC': 12346, 'TECNOLOGIA': 'LTE'},
        {'Id': 32, 'OPERADOR': 'TIGO', 'MNC': 732, 'MCC': 730, 'Punto': 'P3', 'Latitud': -33.4520, 'Longitud': -70.6720, 'RSSI': -80, 'CELLID': 'C12347', 'LAC/TAC': 12347, 'TECNOLOGIA': 'LTE'},
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases):
        try:
            # Use the correct method name from the actual code
            normalized = normalizer.normalize_scanhunter_data(test_case, "test_upload", "test_mission")
            
            if normalized:
                file_record_id = normalized.get('file_record_id')
                original_id = test_case['Id']
                
                result = {
                    'case': i + 1,
                    'original_id': original_id,
                    'extracted_file_record_id': file_record_id,
                    'success': file_record_id == original_id,
                    'normalized_data': normalized
                }
                
                print(f"  Case {i+1}: Original ID={original_id}, Extracted={file_record_id}, Match={'YES' if result['success'] else 'NO'}")
                results.append(result)
            else:
                print(f"  Case {i+1}: FAILED - normalization returned None")
                results.append({'case': i + 1, 'success': False, 'error': 'normalization_failed'})
                
        except Exception as e:
            print(f"  Case {i+1}: ERROR - {str(e)}")
            results.append({'case': i + 1, 'success': False, 'error': str(e)})
    
    # Summary
    successful_cases = sum(1 for r in results if r.get('success'))
    print(f"\nSUMMARY: {successful_cases}/{len(test_cases)} cases passed")
    
    return results

def test_database_insertion():
    """Test that file_record_id is properly stored in database."""
    print("\nTesting database file_record_id storage...")
    
    # Check current state
    conn = sqlite3.connect('kronos.db')
    cursor = conn.cursor()
    
    # Count total records
    cursor.execute('SELECT COUNT(*) FROM cellular_data')
    total_records = cursor.fetchone()[0]
    
    # Count records with file_record_id
    cursor.execute('SELECT COUNT(*) FROM cellular_data WHERE file_record_id IS NOT NULL')
    records_with_file_id = cursor.fetchone()[0]
    
    # Get sample of records with file_record_id
    cursor.execute('SELECT id, file_record_id, punto, operator FROM cellular_data WHERE file_record_id IS NOT NULL LIMIT 5')
    sample_records = cursor.fetchall()
    
    conn.close()
    
    print(f"  Total records in cellular_data: {total_records}")
    print(f"  Records with file_record_id: {records_with_file_id}")
    print(f"  Sample records:")
    
    for record in sample_records:
        print(f"    DB ID: {record[0]}, File Record ID: {record[1]}, Punto: {record[2]}, Operador: {record[3]}")
    
    if records_with_file_id == 0:
        print("  WARNING: No records have file_record_id populated")
        print("  This means existing data needs to be cleared and re-uploaded")
        return False
    
    return True

def main():
    """Main test execution."""
    print("SCANHUNTER File Record ID Fix - Direct Validation")
    print("=" * 50)
    
    # Test 1: file_record_id extraction
    extraction_results = test_file_record_id_extraction()
    
    # Test 2: database state
    database_ok = test_database_insertion()
    
    # Overall assessment
    print("\n" + "=" * 50)
    print("OVERALL ASSESSMENT:")
    print("=" * 50)
    
    extraction_success = all(r.get('success') for r in extraction_results)
    
    if extraction_success:
        print("OK file_record_id extraction: WORKING")
    else:
        print("FAIL file_record_id extraction: FAILING")
    
    if database_ok:
        print("OK Database file_record_id storage: HAS DATA")
    else:
        print("WARN Database file_record_id storage: NO DATA (requires re-upload)")
    
    print("\nRECOMMENDAT IONS:")
    if extraction_success:
        print("- The fix is correctly implemented in the backend code")
    else:
        print("- There are issues with the file_record_id extraction logic")
        
    if not database_ok:
        print("- Existing data does not have file_record_id populated")
        print("- REQUIRED ACTION: Clear existing cellular data and re-upload SCANHUNTER.xlsx")
        print("- Only new uploads after the fix will show file_record_id in the frontend")
    
    print("\nFRONTEND TESTING:")
    print("1. Navigate to mission with SCANHUNTER data")
    print("2. Clear existing data using 'Limpiar Datos' button")
    print("3. Re-upload SCANHUNTER.xlsx file")
    print("4. Verify table shows both 'ID BD' and 'ID Archivo' columns")
    print("5. Check that 'ID Archivo' shows original file IDs (0, 12, 32, etc.)")
    
    return extraction_success

if __name__ == "__main__":
    success = main()
    exit_code = 0 if success else 1
    print(f"\nTest completed with exit code: {exit_code}")
    sys.exit(exit_code)