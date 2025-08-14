#!/usr/bin/env python3
"""
KRONOS - Test Simple de Validación de Duplicados por Misión
==========================================================

Test simplificado que trabaja con la base de datos existente
para probar la lógica de duplicados por misión.

Fecha: 2025-08-13
Autor: Testing Engineer - Claude Code
"""

import os
import sys
import json
import base64
import hashlib
from datetime import datetime

# Agregar el directorio Backend al path
backend_path = os.path.join(os.path.dirname(__file__), 'Backend')
sys.path.insert(0, backend_path)

# Imports del sistema KRONOS
from services.operator_data_service import upload_operator_data

def create_test_file_data(content_variant="default"):
    """Crea datos de archivo de testing en formato CSV."""
    if content_variant == "default":
        csv_content = """numero_telefono,fecha_hora_inicio,fecha_hora_fin,celda_id,lac_tac,trafico_subida_bytes,trafico_bajada_bytes
573001234567,2025-01-01 10:00:00,2025-01-01 10:05:00,CLARO_CELL_001,1001,1024000,2048000
573001234568,2025-01-01 11:00:00,2025-01-01 11:03:00,CLARO_CELL_002,1002,512000,1024000"""
    elif content_variant == "different":
        csv_content = """numero_telefono,fecha_hora_inicio,fecha_hora_fin,celda_id,lac_tac,trafico_subida_bytes,trafico_bajada_bytes
573009876543,2025-01-02 14:00:00,2025-01-02 14:05:00,CLARO_CELL_004,1004,3072000,6144000
573009876544,2025-01-02 15:00:00,2025-01-02 15:03:00,CLARO_CELL_005,1005,1536000,3072000"""
    
    # Codificar en Base64
    file_bytes = csv_content.encode('utf-8')
    file_base64 = base64.b64encode(file_bytes).decode('utf-8')
    
    # Calcular checksum para verificación
    checksum = hashlib.sha256(file_bytes).hexdigest()
    
    return {
        'file_data': file_base64,
        'file_bytes': file_bytes,
        'checksum': checksum,
        'size': len(file_bytes)
    }

def test_duplicate_validation():
    """Test principal de validación de duplicados por misión."""
    print("[START] Test de Validacion de Duplicados por Mision")
    print("=" * 60)
    
    # Test data preparation
    file_data = create_test_file_data("default")
    file_data_different = create_test_file_data("different")
    
    # Use existing missions and users from the database
    test_user_id = "admin"  # Admin user exists
    test_mission_a_id = "m1"  # Proyecto Fénix
    test_mission_b_id = "m2"  # Operación Inmersión Profunda  
    
    results = []
    
    print(f"\n[INFO] Using test file checksum: {file_data['checksum'][:8]}...")
    print(f"[INFO] Mission A: {test_mission_a_id}")
    print(f"[INFO] Mission B: {test_mission_b_id}")
    print(f"[INFO] User: {test_user_id}")
    
    # Test 1: Upload file to Mission A (should succeed)
    print(f"\n[TEST 1] Uploading file to Mission A...")
    result1 = upload_operator_data(
        file_data=file_data['file_data'],
        file_name='test_duplicate_mision_a.csv',
        mission_id=test_mission_a_id,
        operator='CLARO',
        file_type='CELLULAR_DATA',
        user_id=test_user_id
    )
    
    test1_success = result1.get('success', False)
    results.append({
        'test': 'Upload to Mission A',
        'success': test1_success,
        'details': result1
    })
    
    if test1_success:
        print(f"[PASS] Test 1 - Upload to Mission A succeeded")
    else:
        print(f"[FAIL] Test 1 - Upload to Mission A failed: {result1.get('error', 'Unknown error')}")
    
    # Test 2: Upload SAME file to Mission A again (should fail due to duplicate)
    print(f"\n[TEST 2] Uploading same file to Mission A again (should fail)...")
    result2 = upload_operator_data(
        file_data=file_data['file_data'],
        file_name='test_duplicate_mision_a_repeat.csv',
        mission_id=test_mission_a_id,
        operator='CLARO',
        file_type='CELLULAR_DATA',
        user_id=test_user_id
    )
    
    test2_failed_correctly = not result2.get('success', True)
    test2_correct_error = 'en esta misión' in result2.get('error', '') or 'duplicado' in result2.get('error', '').lower()
    
    results.append({
        'test': 'Same file to same mission (should fail)',
        'success': test2_failed_correctly and test2_correct_error,
        'details': result2
    })
    
    if test2_failed_correctly:
        print(f"[PASS] Test 2 - Duplicate correctly detected: {result2.get('error', '')}")
    else:
        print(f"[FAIL] Test 2 - Duplicate not detected, upload succeeded when it should fail")
    
    # Test 3: Upload SAME file to Mission B (should succeed - different mission)
    print(f"\n[TEST 3] Uploading same file to Mission B (should succeed)...")
    result3 = upload_operator_data(
        file_data=file_data['file_data'],
        file_name='test_duplicate_mision_b.csv',
        mission_id=test_mission_b_id,
        operator='CLARO',
        file_type='CELLULAR_DATA',
        user_id=test_user_id
    )
    
    test3_success = result3.get('success', False)
    results.append({
        'test': 'Same file to different mission',
        'success': test3_success,
        'details': result3
    })
    
    if test3_success:
        print(f"[PASS] Test 3 - Same file uploaded to different mission successfully")
    else:
        print(f"[FAIL] Test 3 - Same file to different mission failed: {result3.get('error', 'Unknown error')}")
    
    # Test 4: Upload DIFFERENT file to Mission A (should succeed)
    print(f"\n[TEST 4] Uploading different file to Mission A (should succeed)...")
    result4 = upload_operator_data(
        file_data=file_data_different['file_data'],
        file_name='test_different_file_mision_a.csv',
        mission_id=test_mission_a_id,
        operator='CLARO',
        file_type='CELLULAR_DATA',
        user_id=test_user_id
    )
    
    test4_success = result4.get('success', False)
    results.append({
        'test': 'Different file to same mission',
        'success': test4_success,
        'details': result4
    })
    
    if test4_success:
        print(f"[PASS] Test 4 - Different file uploaded to same mission successfully")
    else:
        print(f"[FAIL] Test 4 - Different file to same mission failed: {result4.get('error', 'Unknown error')}")
    
    # Summary
    print(f"\n{'='*60}")
    print("[SUMMARY] Test Results:")
    print(f"{'='*60}")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['success'])
    
    for i, result in enumerate(results, 1):
        status = "[PASS]" if result['success'] else "[FAIL]"
        print(f"Test {i}: {result['test']} - {status}")
    
    print(f"\nPassed: {passed_tests}/{total_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    # Key functionality assessment
    print(f"\n[ASSESSMENT] Duplicate Validation Logic:")
    
    # Check if the core functionality works
    duplicate_detection_works = not result2.get('success', True)  # Test 2 should fail
    cross_mission_works = result3.get('success', False)  # Test 3 should succeed
    different_files_work = result4.get('success', False)  # Test 4 should succeed
    
    if duplicate_detection_works and cross_mission_works and different_files_work:
        print("[SUCCESS] All core duplicate validation logic working correctly!")
        print("- Same file blocked within same mission [OK]")
        print("- Same file allowed across different missions [OK]") 
        print("- Different files allowed in same mission [OK]")
        overall_success = True
    else:
        print("[ISSUES DETECTED] Some duplicate validation logic not working:")
        print(f"- Same file blocked within same mission: {'[OK]' if duplicate_detection_works else '[FAIL]'}")
        print(f"- Same file allowed across different missions: {'[OK]' if cross_mission_works else '[FAIL]'}")
        print(f"- Different files allowed in same mission: {'[OK]' if different_files_work else '[FAIL]'}")
        overall_success = False
    
    # Save detailed report
    report = {
        'timestamp': datetime.now().isoformat(),
        'test_results': results,
        'summary': {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': (passed_tests/total_tests)*100,
            'overall_success': overall_success
        },
        'functionality_check': {
            'duplicate_detection_works': duplicate_detection_works,
            'cross_mission_works': cross_mission_works, 
            'different_files_work': different_files_work
        }
    }
    
    report_file = f"duplicate_validation_simple_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n[REPORT] Detailed report saved to: {report_file}")
    
    return overall_success

if __name__ == "__main__":
    try:
        success = test_duplicate_validation()
        exit_code = 0 if success else 1
        print(f"\n[EXIT] Test completed with exit code: {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n[CRITICAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)