#!/usr/bin/env python3
"""
KRONOS - Test de Validacion de Paginacion con Ordenamiento ID
=============================================================

Este script valida especificamente que la paginacion mantiene 
el ordenamiento correcto por ID ASC a traves de multiples paginas.

Cambios Validados:
1. ORDER BY id ASC en lugar de fechas (lineas 1167 y 1183)
2. Consistencia de ordenamiento en paginacion
3. Sin solapamiento entre paginas
4. Orden secuencial de IDs entre paginas

Autor: Sistema KRONOS
Fecha: 2025-08-14
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.operator_data_service import get_operator_sheet_data
from database.connection import get_db_connection

def find_suitable_file_for_pagination():
    """Encuentra un archivo con suficientes registros para testear paginacion."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Buscar archivos con al menos 15 registros para poder testear 3 paginas
        cursor.execute("""
            WITH file_counts AS (
                SELECT ods.id, ods.file_type, ods.operator, ods.file_name,
                       CASE WHEN ods.file_type = 'CELLULAR_DATA' THEN 
                           (SELECT COUNT(*) FROM operator_cellular_data WHERE file_upload_id = ods.id)
                       ELSE
                           (SELECT COUNT(*) FROM operator_call_data WHERE file_upload_id = ods.id)
                       END as record_count
                FROM operator_data_sheets ods
                WHERE processing_status = 'COMPLETED'
            )
            SELECT id, file_type, operator, file_name, record_count
            FROM file_counts
            WHERE record_count >= 15
            ORDER BY record_count DESC
            LIMIT 3
        """)
        
        files = cursor.fetchall()
        
        print(f"Archivos encontrados para testeo de paginacion:")
        for i, (file_id, file_type, operator, file_name, count) in enumerate(files, 1):
            print(f"  {i}. {operator} - {file_type}: {count} registros ({file_name[:50]}...)")
        
        return files[0] if files else None

def test_pagination_consistency(file_info):
    """Test completo de consistencia de paginacion."""
    file_id, file_type, operator, file_name, total_records = file_info
    
    print(f"\n=== TESTING PAGINACION ===")
    print(f"Archivo: {operator} - {file_type}")
    print(f"Total registros: {total_records}")
    print(f"Archivo ID: {file_id}")
    
    # Configuracion de paginacion
    page_size = 5
    num_pages_to_test = min(3, (total_records + page_size - 1) // page_size)
    
    print(f"Paginas a testear: {num_pages_to_test} (page_size={page_size})")
    
    all_ids = []
    all_data = []
    page_results = []
    
    # Obtener multiples paginas
    for page_num in range(1, num_pages_to_test + 1):
        print(f"\n--- Pagina {page_num} ---")
        
        try:
            response = get_operator_sheet_data(file_id, page=page_num, page_size=page_size)
            
            if not response.get('success'):
                raise Exception(f"API failed: {response.get('error', 'Unknown error')}")
            
            page_data = response.get('data', [])
            page_ids = [record.get('id') for record in page_data if 'id' in record]
            
            print(f"  Registros obtenidos: {len(page_data)}")
            print(f"  IDs: {page_ids}")
            
            # Validaciones por pagina
            ids_sorted = page_ids == sorted(page_ids)
            print(f"  IDs ordenados ASC: {ids_sorted}")
            
            # Guardar datos para validacion cruzada
            all_ids.extend(page_ids)
            all_data.extend(page_data)
            
            page_results.append({
                'page': page_num,
                'ids': page_ids,
                'count': len(page_data),
                'sorted': ids_sorted,
                'has_metadata': 'metadata' in response,
                'has_columns': 'columns' in response,
                'has_display_names': 'displayNames' in response
            })
            
        except Exception as e:
            print(f"  [ERROR] Error en pagina {page_num}: {e}")
            page_results.append({
                'page': page_num,
                'error': str(e),
                'sorted': False
            })
    
    # Validaciones generales
    print(f"\n=== VALIDACIONES GENERALES ===")
    
    # 1. Todos los IDs estan ordenados globalmente
    global_sorted = all_ids == sorted(all_ids)
    print(f"Todos los IDs ordenados globalmente: {global_sorted}")
    print(f"IDs obtenidos: {all_ids}")
    
    # 2. No hay duplicados
    no_duplicates = len(all_ids) == len(set(all_ids))
    print(f"Sin duplicados: {no_duplicates}")
    
    # 3. Continuidad entre paginas (sin gaps inesperados en secuencia)
    if len(page_results) >= 2:
        page1_max = max(page_results[0]['ids']) if page_results[0].get('ids') else 0
        page2_min = min(page_results[1]['ids']) if page_results[1].get('ids') else 0
        proper_sequence = page1_max < page2_min
        print(f"Secuencia correcta entre paginas 1-2: {proper_sequence}")
        
        if len(page_results) >= 3:
            page2_max = max(page_results[1]['ids']) if page_results[1].get('ids') else 0
            page3_min = min(page_results[2]['ids']) if page_results[2].get('ids') else 0
            proper_sequence_23 = page2_max < page3_min
            print(f"Secuencia correcta entre paginas 2-3: {proper_sequence_23}")
    
    # 4. Metadatos consistentes
    all_have_metadata = all(result.get('has_metadata', False) for result in page_results if 'error' not in result)
    print(f"Todas las paginas tienen metadata: {all_have_metadata}")
    
    # 5. Configuracion de columnas consistente
    all_have_columns = all(result.get('has_columns', False) for result in page_results if 'error' not in result)
    all_have_display_names = all(result.get('has_display_names', False) for result in page_results if 'error' not in result)
    print(f"Todas las paginas tienen columns: {all_have_columns}")
    print(f"Todas las paginas tienen displayNames: {all_have_display_names}")
    
    # Resultado final
    all_page_tests_passed = all(result.get('sorted', False) for result in page_results)
    
    overall_passed = (
        global_sorted and 
        no_duplicates and 
        all_page_tests_passed and
        all_have_metadata and 
        all_have_columns and
        all_have_display_names
    )
    
    print(f"\n[RESULTADO PAGINACION]: {'PASSED' if overall_passed else 'FAILED'}")
    
    return {
        'file_info': file_info,
        'page_results': page_results,
        'global_sorted': global_sorted,
        'no_duplicates': no_duplicates,
        'all_page_tests_passed': all_page_tests_passed,
        'metadata_consistent': all_have_metadata,
        'columns_consistent': all_have_columns,
        'display_names_consistent': all_have_display_names,
        'overall_passed': overall_passed,
        'total_ids_tested': len(all_ids),
        'all_ids': all_ids
    }

def test_edge_cases():
    """Test casos edge de paginacion."""
    print(f"\n=== TEST CASOS EDGE ===")
    
    # Obtener cualquier archivo para tests edge
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, file_type, operator 
            FROM operator_data_sheets 
            WHERE processing_status = 'COMPLETED'
            LIMIT 1
        """)
        file_info = cursor.fetchone()
    
    if not file_info:
        print("No hay archivos para testear casos edge")
        return {'passed': True, 'reason': 'No data available'}
    
    file_id = file_info[0]
    results = []
    
    # Test 1: Pagina vacia (page muy grande)
    try:
        response = get_operator_sheet_data(file_id, page=9999, page_size=10)
        empty_page_ok = response.get('success', False) and len(response.get('data', [])) == 0
        print(f"Pagina vacia manejada correctamente: {empty_page_ok}")
        results.append(empty_page_ok)
    except Exception as e:
        print(f"Error en pagina vacia: {e}")
        results.append(False)
    
    # Test 2: Page size muy grande
    try:
        response = get_operator_sheet_data(file_id, page=1, page_size=10000)
        large_page_size_ok = response.get('success', False)
        print(f"Page size grande manejado correctamente: {large_page_size_ok}")
        results.append(large_page_size_ok)
    except Exception as e:
        print(f"Error en page size grande: {e}")
        results.append(False)
    
    # Test 3: Parametros invalidos
    try:
        response = get_operator_sheet_data(file_id, page=0, page_size=5)  # page 0 deberia convertirse a 1
        invalid_params_handled = response.get('success', False)
        print(f"Parametros invalidos manejados: {invalid_params_handled}")
        results.append(invalid_params_handled)
    except Exception as e:
        print(f"Error en parametros invalidos: {e}")
        results.append(False)
    
    all_passed = all(results)
    print(f"[RESULTADO EDGE CASES]: {'PASSED' if all_passed else 'FAILED'}")
    
    return {'passed': all_passed, 'individual_results': results}

def run_pagination_test():
    """Ejecuta el test completo de paginacion."""
    print("KRONOS - Test de Paginacion con Ordenamiento ID")
    print("=" * 50)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Encontrar archivo adecuado
    suitable_file = find_suitable_file_for_pagination()
    
    if not suitable_file:
        print("\n[ERROR] No se encontraron archivos con suficientes registros para testear paginacion")
        return False
    
    # 2. Test principal de paginacion
    pagination_result = test_pagination_consistency(suitable_file)
    
    # 3. Test de casos edge
    edge_case_result = test_edge_cases()
    
    # 4. Resumen final
    print(f"\n{'='*50}")
    print("RESUMEN FINAL - PAGINACION")
    print(f"{'='*50}")
    
    print(f"Test Principal Paginacion: {'PASSED' if pagination_result['overall_passed'] else 'FAILED'}")
    print(f"Test Casos Edge:          {'PASSED' if edge_case_result['passed'] else 'FAILED'}")
    
    overall_success = pagination_result['overall_passed'] and edge_case_result['passed']
    print(f"\n[RESULTADO GENERAL]: {'ALL TESTS PASSED' if overall_success else 'SOME TESTS FAILED'}")
    
    # Detalles especificos de la validacion
    if pagination_result['overall_passed']:
        print(f"\n[DETALLES EXITOSOS]:")
        print(f"  - IDs ordenados globalmente: {pagination_result['global_sorted']}")
        print(f"  - Sin duplicados: {pagination_result['no_duplicates']}")
        print(f"  - Paginas individuales ordenadas: {pagination_result['all_page_tests_passed']}")
        print(f"  - Metadata consistente: {pagination_result['metadata_consistent']}")
        print(f"  - Total IDs testeados: {pagination_result['total_ids_tested']}")
        print(f"  - Rango de IDs: {min(pagination_result['all_ids'])} - {max(pagination_result['all_ids'])}")
    
    return overall_success

if __name__ == "__main__":
    success = run_pagination_test()
    sys.exit(0 if success else 1)