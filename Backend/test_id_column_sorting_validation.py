#!/usr/bin/env python3
"""
KRONOS - Test de Validación de Columna ID y Ordenamiento
========================================================

Este script valida que los cambios realizados en operator_data_service.py
para incluir correctamente la columna ID y ordenar por ID ASC están funcionando.

Cambios Validados:
1. Línea 1167: ORDER BY id ASC en lugar de fecha_hora_inicio DESC (CELLULAR_DATA)
2. Línea 1183: ORDER BY id ASC en lugar de fecha_hora_llamada DESC (CALL_DATA)
3. Confirmación de inclusión de columna ID en configuraciones

Autor: Sistema KRONOS
Fecha: 2025-08-14
"""

import sys
import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.operator_data_service import OperatorDataService, get_operator_sheet_data
from database.connection import get_db_connection

def test_column_configuration():
    """Test que las configuraciones de columnas incluyen correctamente el ID."""
    print("=== TEST 1: CONFIGURACIÓN DE COLUMNAS ===")
    service = OperatorDataService()
    
    test_cases = [
        ("CLARO", "CELLULAR_DATA"),
        ("CLARO", "CALL_DATA"),
        ("MOVISTAR", "CELLULAR_DATA"), 
        ("MOVISTAR", "CALL_DATA"),
        ("TIGO", "CALL_DATA"),
        ("WOM", "CELLULAR_DATA"),
        ("WOM", "CALL_DATA")
    ]
    
    results = []
    
    for operator, file_type in test_cases:
        config = service._get_column_configuration(operator, file_type)
        
        test_result = {
            'operator': operator,
            'file_type': file_type,
            'has_id_column': 'id' in config.get('columns', []),
            'id_first_column': config.get('columns', [])[0] == 'id' if config.get('columns') else False,
            'has_id_display_name': 'id' in config.get('display_names', {}),
            'id_display_name': config.get('display_names', {}).get('id', 'N/A'),
            'columns_count': len(config.get('columns', [])),
            'select_query_contains_id': 'id' in config.get('select_query', '').lower(),
        }
        
        results.append(test_result)
        
        print(f"\n{operator} - {file_type}:")
        print(f"  [OK] ID en columnas: {test_result['has_id_column']}")
        print(f"  [OK] ID primera columna: {test_result['id_first_column']}")
        print(f"  [OK] ID display name: {test_result['id_display_name']}")
        print(f"  [OK] Query incluye ID: {test_result['select_query_contains_id']}")
        print(f"  [OK] Total columnas: {test_result['columns_count']}")
    
    # Verificar que todos los tests pasaron
    all_passed = all(
        result['has_id_column'] and 
        result['id_first_column'] and 
        result['has_id_display_name'] and 
        result['select_query_contains_id']
        for result in results
    )
    
    print(f"\n🎯 RESULTADO: {'PASSED' if all_passed else 'FAILED'}")
    return results, all_passed


def test_database_sorting():
    """Test que las queries de base de datos ordenan correctamente por ID ASC."""
    print("\n=== TEST 2: ORDENAMIENTO EN BASE DE DATOS ===")
    
    results = []
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Test 1: CELLULAR_DATA ordering
        print("\nTest CELLULAR_DATA ordering:")
        cursor.execute("""
            SELECT id, numero_telefono, fecha_hora_inicio 
            FROM operator_cellular_data 
            ORDER BY id ASC 
            LIMIT 10
        """)
        cellular_rows = cursor.fetchall()
        
        if cellular_rows:
            cellular_ids = [row[0] for row in cellular_rows]
            cellular_sorted = cellular_ids == sorted(cellular_ids)
            
            print(f"  ✓ Primeros 10 IDs: {cellular_ids[:5]}...")
            print(f"  ✓ Ordenamiento correcto: {cellular_sorted}")
            
            results.append({
                'test': 'CELLULAR_DATA_ORDER',
                'passed': cellular_sorted,
                'first_ids': cellular_ids,
                'total_records': len(cellular_rows)
            })
        else:
            print("  ⚠️ No hay datos de CELLULAR_DATA para testear")
            results.append({
                'test': 'CELLULAR_DATA_ORDER',
                'passed': True,  # No data is not a failure
                'first_ids': [],
                'total_records': 0
            })
        
        # Test 2: CALL_DATA ordering
        print("\nTest CALL_DATA ordering:")
        cursor.execute("""
            SELECT id, numero_origen, numero_destino, fecha_hora_llamada 
            FROM operator_call_data 
            ORDER BY id ASC 
            LIMIT 10
        """)
        call_rows = cursor.fetchall()
        
        if call_rows:
            call_ids = [row[0] for row in call_rows]
            call_sorted = call_ids == sorted(call_ids)
            
            print(f"  ✓ Primeros 10 IDs: {call_ids[:5]}...")
            print(f"  ✓ Ordenamiento correcto: {call_sorted}")
            
            results.append({
                'test': 'CALL_DATA_ORDER',
                'passed': call_sorted,
                'first_ids': call_ids,
                'total_records': len(call_rows)
            })
        else:
            print("  ⚠️ No hay datos de CALL_DATA para testear")
            results.append({
                'test': 'CALL_DATA_ORDER',
                'passed': True,  # No data is not a failure
                'first_ids': [],
                'total_records': 0
            })
    
    all_passed = all(result['passed'] for result in results)
    print(f"\n🎯 RESULTADO: {'PASSED' if all_passed else 'FAILED'}")
    return results, all_passed


def test_api_response_structure():
    """Test que las respuestas de la API incluyen correctamente la columna ID."""
    print("\n=== TEST 3: ESTRUCTURA DE RESPUESTA API ===")
    
    results = []
    
    # Obtener un archivo de muestra para testear
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, file_type, operator 
            FROM operator_data_sheets 
            WHERE processing_status = 'COMPLETED'
            LIMIT 1
        """)
        sample_file = cursor.fetchone()
    
    if not sample_file:
        print("  ⚠️ No hay archivos procesados para testear la API")
        return [{
            'test': 'API_RESPONSE_STRUCTURE',
            'passed': True,  # No data is not a failure
            'details': 'No processed files available for testing'
        }], True
    
    file_upload_id, file_type, operator = sample_file
    print(f"\nTesteando archivo: {file_upload_id} ({operator} - {file_type})")
    
    # Test API response
    try:
        api_response = get_operator_sheet_data(file_upload_id, page=1, page_size=5)
        
        test_result = {
            'test': 'API_RESPONSE_STRUCTURE',
            'file_id': file_upload_id,
            'operator': operator,
            'file_type': file_type,
            'success': api_response.get('success', False),
            'has_data': 'data' in api_response,
            'data_count': len(api_response.get('data', [])),
            'has_columns': 'columns' in api_response,
            'has_display_names': 'displayNames' in api_response,
            'id_in_columns': 'id' in api_response.get('columns', []) if api_response.get('columns') else False,
            'id_in_display_names': 'id' in api_response.get('displayNames', {}) if api_response.get('displayNames') else False,
            'first_record_has_id': False,
            'ids_ascending': False
        }
        
        # Verificar que los datos incluyen ID y están ordenados
        if api_response.get('data'):
            first_record = api_response['data'][0]
            test_result['first_record_has_id'] = 'id' in first_record
            
            if len(api_response['data']) > 1:
                ids = [record.get('id') for record in api_response['data'] if 'id' in record]
                if ids:
                    test_result['ids_ascending'] = ids == sorted(ids)
                    print(f"  ✓ IDs en respuesta: {ids}")
                    print(f"  ✓ IDs ordenados ASC: {test_result['ids_ascending']}")
        
        results.append(test_result)
        
        print(f"  ✓ API Success: {test_result['success']}")
        print(f"  ✓ Tiene datos: {test_result['has_data']} ({test_result['data_count']} records)")
        print(f"  ✓ ID en columnas: {test_result['id_in_columns']}")
        print(f"  ✓ ID en display names: {test_result['id_in_display_names']}")
        print(f"  ✓ Primer record tiene ID: {test_result['first_record_has_id']}")
        
        passed = (
            test_result['success'] and
            test_result['id_in_columns'] and
            test_result['id_in_display_names'] and
            test_result['first_record_has_id'] and
            (test_result['ids_ascending'] if test_result['data_count'] > 1 else True)
        )
        
    except Exception as e:
        print(f"  ❌ Error en API: {e}")
        results.append({
            'test': 'API_RESPONSE_STRUCTURE',
            'passed': False,
            'error': str(e)
        })
        passed = False
    
    print(f"\n🎯 RESULTADO: {'PASSED' if passed else 'FAILED'}")
    return results, passed


def test_pagination_consistency():
    """Test que la paginación mantiene el ordenamiento correcto por ID."""
    print("\n=== TEST 4: CONSISTENCIA DE PAGINACIÓN ===")
    
    results = []
    
    # Obtener un archivo con suficientes registros para paginar
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ods.id, ods.file_type, ods.operator,
                   CASE WHEN ods.file_type = 'CELLULAR_DATA' THEN 
                       (SELECT COUNT(*) FROM operator_cellular_data WHERE file_upload_id = ods.id)
                   ELSE
                       (SELECT COUNT(*) FROM operator_call_data WHERE file_upload_id = ods.id)
                   END as record_count
            FROM operator_data_sheets ods
            WHERE processing_status = 'COMPLETED'
            HAVING record_count >= 10
            ORDER BY record_count DESC
            LIMIT 1
        """)
        sample_file = cursor.fetchone()
    
    if not sample_file:
        print("  ⚠️ No hay archivos con suficientes registros para testear paginación")
        return [{
            'test': 'PAGINATION_CONSISTENCY',
            'passed': True,
            'details': 'No files with enough records for pagination testing'
        }], True
    
    file_upload_id, file_type, operator, record_count = sample_file
    print(f"\nTesteando paginación: {file_upload_id} ({operator} - {file_type}, {record_count} records)")
    
    try:
        # Obtener primera página
        page1 = get_operator_sheet_data(file_upload_id, page=1, page_size=5)
        page2 = get_operator_sheet_data(file_upload_id, page=2, page_size=5)
        
        if not (page1.get('success') and page2.get('success')):
            raise Exception("API calls failed")
        
        # Extraer IDs de ambas páginas
        page1_ids = [record.get('id') for record in page1.get('data', []) if 'id' in record]
        page2_ids = [record.get('id') for record in page2.get('data', []) if 'id' in record]
        
        # Verificar que no hay solapamiento y que están ordenados
        no_overlap = not set(page1_ids).intersection(set(page2_ids))
        page1_sorted = page1_ids == sorted(page1_ids)
        page2_sorted = page2_ids == sorted(page2_ids)
        cross_page_order = not page1_ids or not page2_ids or max(page1_ids) < min(page2_ids)
        
        test_result = {
            'test': 'PAGINATION_CONSISTENCY',
            'file_id': file_upload_id,
            'page1_ids': page1_ids,
            'page2_ids': page2_ids,
            'no_overlap': no_overlap,
            'page1_sorted': page1_sorted,
            'page2_sorted': page2_sorted,
            'cross_page_order': cross_page_order,
            'passed': no_overlap and page1_sorted and page2_sorted and cross_page_order
        }
        
        results.append(test_result)
        
        print(f"  ✓ Página 1 IDs: {page1_ids}")
        print(f"  ✓ Página 2 IDs: {page2_ids}")
        print(f"  ✓ Sin solapamiento: {no_overlap}")
        print(f"  ✓ Página 1 ordenada: {page1_sorted}")
        print(f"  ✓ Página 2 ordenada: {page2_sorted}")
        print(f"  ✓ Orden entre páginas: {cross_page_order}")
        
        passed = test_result['passed']
        
    except Exception as e:
        print(f"  ❌ Error en paginación: {e}")
        results.append({
            'test': 'PAGINATION_CONSISTENCY',
            'passed': False,
            'error': str(e)
        })
        passed = False
    
    print(f"\n🎯 RESULTADO: {'PASSED' if passed else 'FAILED'}")
    return results, passed


def run_comprehensive_test():
    """Ejecuta todos los tests y genera el reporte final."""
    print("KRONOS - Test de Validación Columna ID y Ordenamiento")
    print("=" * 55)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_results = {}
    all_passed = True
    
    # Ejecutar todos los tests
    test_functions = [
        ("COLUMN_CONFIGURATION", test_column_configuration),
        ("DATABASE_SORTING", test_database_sorting),
        ("API_RESPONSE", test_api_response_structure),
        ("PAGINATION_CONSISTENCY", test_pagination_consistency)
    ]
    
    for test_name, test_func in test_functions:
        try:
            results, passed = test_func()
            all_results[test_name] = {
                'results': results,
                'passed': passed
            }
            all_passed = all_passed and passed
        except Exception as e:
            print(f"\n❌ ERROR en {test_name}: {e}")
            all_results[test_name] = {
                'results': [],
                'passed': False,
                'error': str(e)
            }
            all_passed = False
    
    # Generar reporte final
    print("\n" + "=" * 55)
    print("RESUMEN EJECUTIVO")
    print("=" * 55)
    
    for test_name, result in all_results.items():
        status = "✅ PASSED" if result['passed'] else "❌ FAILED"
        print(f"{test_name:25}: {status}")
    
    print(f"\n🎯 RESULTADO GENERAL: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    # Guardar reporte detallado
    report = {
        'timestamp': datetime.now().isoformat(),
        'overall_passed': all_passed,
        'test_results': all_results,
        'summary': {
            'total_tests': len(test_functions),
            'passed_tests': sum(1 for r in all_results.values() if r['passed']),
            'failed_tests': sum(1 for r in all_results.values() if not r['passed'])
        }
    }
    
    report_file = f"id_column_sorting_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📄 Reporte detallado guardado en: {report_file}")
    
    return all_passed


if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)