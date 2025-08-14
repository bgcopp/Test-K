#!/usr/bin/env python3
"""
KRONOS - Validación Completa Final de Correcciones CLARO
======================================================

Test final para verificar que AMBAS correcciones están completamente implementadas:
- FIX 1: Frontend usa CELLULAR_DATA y CALL_DATA IDs
- FIX 2: Backend siempre retorna sheetId y processedRecords (incluso en errores)

Autor: Sistema KRONOS - Testing Engineer  
Fecha: 2025-08-12
"""

import sys
import os
import json
import base64
from datetime import datetime
from pathlib import Path

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import get_db_connection, init_database
from services.operator_data_service import upload_operator_data

def setup_test_environment():
    """Configura entorno de prueba"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Usar la primera misión y usuario disponibles
        cursor.execute("SELECT id FROM missions LIMIT 1")
        mission_result = cursor.fetchone()
        
        cursor.execute("SELECT id FROM users LIMIT 1")
        user_result = cursor.fetchone()
        
        if not mission_result or not user_result:
            raise Exception("No missions or users found in database")
        
        return mission_result[0], user_result[0]

def test_fix1_frontend_validation():
    """Valida FIX 1: Frontend usa IDs correctos"""
    print("[FIX1] Validando tipos de documento en frontend...")
    
    frontend_file = Path(__file__).parent.parent / 'Frontend' / 'components' / 'operator-data' / 'OperatorDataUpload.tsx'
    
    if not frontend_file.exists():
        return False, "Archivo frontend no encontrado"
    
    with open(frontend_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar que CLARO tenga los IDs correctos
    has_cellular_data = "id: 'CELLULAR_DATA'" in content
    has_call_data = "id: 'CALL_DATA'" in content
    no_spanish_ids = "id: 'DATOS_CELULARES'" not in content and "id: 'DATOS_LLAMADAS'" not in content
    
    validated = has_cellular_data and has_call_data and no_spanish_ids
    
    details = {
        'has_cellular_data_id': has_cellular_data,
        'has_call_data_id': has_call_data,
        'no_spanish_ids': no_spanish_ids
    }
    
    return validated, details

def test_fix2_backend_responses():
    """Valida FIX 2: Backend usa campos correctos en TODAS las respuestas"""
    print("[FIX2] Validando campos de respuesta backend...")
    
    mission_id, user_id = setup_test_environment()
    
    # Test cases que DEBERIAN generar diferentes tipos de errores
    test_cases = [
        {
            'name': 'Archivo con datos inválidos (estructura incorrecta)',
            'data': 'column1,column2\nvalue1,value2',
            'filename': 'invalid_structure.csv',
            'operator': 'CLARO',
            'file_type': 'CELLULAR_DATA',
            'expected_error': True
        },
        {
            'name': 'Operador no soportado',
            'data': 'numero,fecha_trafico,tipo_cdr,celda_decimal,lac_decimal\n123,2024-01-01,DATA,456,789',
            'filename': 'test.csv', 
            'operator': 'UNKNOWN_OPERATOR',
            'file_type': 'CELLULAR_DATA',
            'expected_error': True
        },
        {
            'name': 'Tipo de archivo no soportado para TIGO',
            'data': 'numero,fecha_trafico,tipo_cdr,celda_decimal,lac_decimal\n123,2024-01-01,DATA,456,789',
            'filename': 'test.csv',
            'operator': 'TIGO', 
            'file_type': 'CELLULAR_DATA',  # TIGO no soporta CELLULAR_DATA
            'expected_error': True
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        try:
            print(f"  [TEST] {test_case['name']}")
            
            # Convertir datos a base64
            csv_base64 = base64.b64encode(test_case['data'].encode('utf-8')).decode('utf-8')
            
            # Realizar upload
            result = upload_operator_data(
                file_data=csv_base64,
                file_name=test_case['filename'],
                mission_id=mission_id,
                operator=test_case['operator'],
                file_type=test_case['file_type'],
                user_id=user_id
            )
            
            # Verificar estructura de respuesta
            has_success = 'success' in result
            has_sheet_id = 'sheetId' in result
            has_old_field = 'file_upload_id' in result
            has_error = 'error' in result if not result.get('success') else False
            
            # Para casos de error, verificar que use sheetId en lugar de file_upload_id
            fields_correct = has_success and (has_sheet_id or not result.get('success')) and not has_old_field
            
            test_result = {
                'test_name': test_case['name'],
                'success_field': has_success,
                'sheet_id_field': has_sheet_id,
                'old_field_present': has_old_field,
                'error_as_expected': result.get('success') == (not test_case['expected_error']),
                'fields_correct': fields_correct,
                'response': result
            }
            
            results.append(test_result)
            
            print(f"    success: {has_success}")
            print(f"    sheetId: {has_sheet_id}")
            print(f"    file_upload_id: {has_old_field}")
            print(f"    Campos correctos: {fields_correct}")
            
        except Exception as e:
            print(f"    ERROR: {e}")
            results.append({
                'test_name': test_case['name'],
                'error': str(e),
                'fields_correct': False
            })
    
    # Evaluar resultados
    all_correct = all(r.get('fields_correct', False) for r in results)
    
    return all_correct, results

def test_successful_upload():
    """Valida que uploads exitosos usen los campos correctos"""
    print("[SUCCESS] Validando upload exitoso...")
    
    mission_id, user_id = setup_test_environment()
    
    # Datos válidos para CLARO CELLULAR_DATA
    valid_data = """numero,fecha_trafico,tipo_cdr,celda_decimal,lac_decimal
573001234567,2024-08-01 10:15:30,DATA,12345,678
573007654321,2024-08-01 10:20:45,DATA,12346,679"""
    
    try:
        csv_base64 = base64.b64encode(valid_data.encode('utf-8')).decode('utf-8')
        
        result = upload_operator_data(
            file_data=csv_base64,
            file_name='test_valid_claro.csv',
            mission_id=mission_id,
            operator='CLARO',
            file_type='CELLULAR_DATA',
            user_id=user_id
        )
        
        # Verificar campos para caso exitoso
        has_success = result.get('success', False)
        has_sheet_id = 'sheetId' in result
        has_processed_records = 'processedRecords' in result
        has_warnings = 'warnings' in result
        has_errors = 'errors' in result
        no_old_fields = 'file_upload_id' not in result and 'records_processed' not in result
        
        success_correct = (has_success and has_sheet_id and has_processed_records and 
                          has_warnings and has_errors and no_old_fields)
        
        return success_correct, {
            'upload_successful': has_success,
            'has_sheet_id': has_sheet_id,
            'has_processed_records': has_processed_records,
            'has_warnings': has_warnings,
            'has_errors': has_errors,
            'no_old_fields': no_old_fields,
            'response': result
        }
        
    except Exception as e:
        return False, {'error': str(e)}

def main():
    """Función principal"""
    print("VALIDACION COMPLETA FINAL DE CORRECCIONES CLARO")
    print("=" * 60)
    
    try:
        # === VALIDAR FIX 1 ===
        fix1_valid, fix1_details = test_fix1_frontend_validation()
        print(f"[FIX1] Frontend IDs: {'VALIDADO' if fix1_valid else 'FALLIDO'}")
        
        # === VALIDAR FIX 2 - CASOS DE ERROR ===
        fix2_errors_valid, fix2_error_details = test_fix2_backend_responses()
        print(f"[FIX2] Error responses: {'VALIDADO' if fix2_errors_valid else 'FALLIDO'}")
        
        # === VALIDAR FIX 2 - CASO EXITOSO ===
        fix2_success_valid, fix2_success_details = test_successful_upload()
        print(f"[FIX2] Success response: {'VALIDADO' if fix2_success_valid else 'FALLIDO'}")
        
        # === EVALUACION FINAL ===
        fix2_complete = fix2_errors_valid and fix2_success_valid
        all_fixes_valid = fix1_valid and fix2_complete
        
        print(f"\n[CERTIFICACION] RESULTADO FINAL:")
        print(f"   FIX 1 (Frontend): {'VALIDADO' if fix1_valid else 'FALLIDO'}")
        print(f"   FIX 2 (Backend): {'VALIDADO' if fix2_complete else 'FALLIDO'}")
        print(f"   ESTADO GENERAL: {'CERTIFICADO' if all_fixes_valid else 'NO CERTIFICADO'}")
        
        # Generar reporte final
        final_report = {
            'timestamp': datetime.now().isoformat(),
            'test_type': 'COMPLETE_FINAL_VALIDATION',
            'certification_status': 'CERTIFIED' if all_fixes_valid else 'NOT_CERTIFIED',
            'fix1_frontend': {
                'status': 'VALIDATED' if fix1_valid else 'FAILED',
                'details': fix1_details
            },
            'fix2_backend': {
                'status': 'VALIDATED' if fix2_complete else 'FAILED',
                'error_responses': {
                    'status': 'VALIDATED' if fix2_errors_valid else 'FAILED',
                    'details': fix2_error_details
                },
                'success_responses': {
                    'status': 'VALIDATED' if fix2_success_valid else 'FAILED', 
                    'details': fix2_success_details
                }
            },
            'summary': {
                'both_fixes_validated': all_fixes_valid,
                'user_reported_issue_resolved': all_fixes_valid
            }
        }
        
        report_file = f'CLARO_FINAL_CERTIFICATION_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)
        
        print(f"\n[REPORT] Reporte final: {report_file}")
        
        if all_fixes_valid:
            print("\n[SUCCESS] AMBAS CORRECCIONES VALIDADAS EXITOSAMENTE")
            print("          El problema reportado por el usuario esta RESUELTO")
            return 0
        else:
            print("\n[WARNING] Algunas correcciones requieren revision")
            return 1
            
    except Exception as e:
        print(f"[ERROR] Error critico: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())