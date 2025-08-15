"""
Test de Integración - Funcionalidad Cell ID y LAC para Movistar
==============================================================
Prueba completa de la funcionalidad de extracción y conversión de Cell ID y LAC
desde archivos de Movistar, validando todo el flujo desde el procesamiento 
hasta la visualización.

Author: KRONOS Development Team
Date: 2025-08-14
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Any

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db_connection
from services.file_processor_service import FileProcessorService
from services.operator_data_service import get_operator_sheet_data
from utils.cell_id_converter import extract_cellid_lac_from_celda_origen


def setup_test_environment():
    """Configura el entorno de prueba"""
    print("=== CONFIGURACION DEL ENTORNO DE PRUEBA ===")
    
    # Verificar que la base de datos tiene las nuevas columnas
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(operator_call_data)")
        columns = cursor.fetchall()
        
        column_names = [col[1] for col in columns]
        has_cellid = 'cellid_decimal' in column_names
        has_lac = 'lac_decimal' in column_names
        
        print(f"OK Base de datos disponible")
        print(f"OK Columna cellid_decimal: {'SI' if has_cellid else 'NO'}")
        print(f"OK Columna lac_decimal: {'SI' if has_lac else 'NO'}")
        
        if not (has_cellid and has_lac):
            print("ERROR Las columnas cellid_decimal y lac_decimal no existen")
            print("   Ejecute migration_add_cellid_lac_fields.py primero")
            return False
    
    return True


def test_cell_id_converter():
    """Prueba la función de conversión de Cell ID y LAC"""
    print("\n=== TEST: CONVERSION CELL ID Y LAC ===")
    
    test_cases = [
        ("07F083-05", {"cellid_decimal": 520323, "lac_decimal": 5}),
        ("ABC123-FF", {"cellid_decimal": 11256099, "lac_decimal": 255}),
        ("000001-00", {"cellid_decimal": 1, "lac_decimal": 0}),
        ("FFFFFF-FFFF", {"cellid_decimal": 16777215, "lac_decimal": 65535}),
        ("invalid", {"cellid_decimal": None, "lac_decimal": None}),
        ("", {"cellid_decimal": None, "lac_decimal": None}),
    ]
    
    all_passed = True
    
    for input_val, expected in test_cases:
        result = extract_cellid_lac_from_celda_origen(input_val)
        passed = result == expected
        all_passed &= passed
        
        status = "OK" if passed else "ERROR"
        print(f"{status} {input_val} -> {result}")
        if not passed:
            print(f"   Esperado: {expected}")
    
    print(f"\nResultado: {'PASSED' if all_passed else 'FAILED'}")
    return all_passed


def test_movistar_file_processing():
    """Prueba el procesamiento del archivo de Movistar"""
    print("\n=== TEST: PROCESAMIENTO ARCHIVO MOVISTAR ===")
    
    file_path = r"C:\Soluciones\BGC\claude\KNSOft\datatest\Movistar\Formato Excel\jgd202410754_07F08305_vozm_saliente_ MOVISTAR.xlsx"
    
    if not os.path.exists(file_path):
        print(f"ERROR Archivo de prueba no encontrado: {file_path}")
        return False
    
    print(f"✓ Archivo de prueba encontrado: {os.path.basename(file_path)}")
    
    try:
        # Crear instancia del procesador
        processor = FileProcessorService()
        
        # Generar IDs únicos para la prueba
        test_mission_id = f"test_mission_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        file_upload_id = f"test_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Leer archivo
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
        
        file_name = os.path.basename(file_path)
        
        print(f"✓ Iniciando procesamiento...")
        print(f"  Mission ID: {test_mission_id}")
        print(f"  File Upload ID: {file_upload_id}")
        
        # Procesar archivo
        result = processor.process_movistar_llamadas_salientes(
            file_bytes, file_name, file_upload_id, test_mission_id
        )
        
        if result['success']:
            processed_records = result.get('processed_records', 0)
            failed_records = result.get('failed_records', 0)
            
            print(f"✓ Procesamiento exitoso")
            print(f"  Registros procesados: {processed_records}")
            print(f"  Registros fallidos: {failed_records}")
            
            # Verificar que se insertaron datos con cellid_decimal y lac_decimal
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        celda_origen, cellid_decimal, lac_decimal,
                        COUNT(*) as count
                    FROM operator_call_data 
                    WHERE file_upload_id = ? 
                    AND cellid_decimal IS NOT NULL 
                    AND lac_decimal IS NOT NULL
                    GROUP BY celda_origen, cellid_decimal, lac_decimal
                    LIMIT 5
                """, (file_upload_id,))
                
                converted_samples = cursor.fetchall()
                
                print(f"\n✓ Muestras de conversión exitosa:")
                for sample in converted_samples:
                    print(f"  {sample[0]} -> Cell ID: {sample[1]}, LAC: {sample[2]} ({sample[3]} registros)")
            
            return True, file_upload_id
        else:
            print(f"❌ Error en procesamiento: {result.get('error', 'Error desconocido')}")
            return False, None
            
    except Exception as e:
        print(f"❌ Excepción durante procesamiento: {e}")
        return False, None


def test_api_response(file_upload_id: str):
    """Prueba la respuesta de la API con las nuevas columnas"""
    print("\n=== TEST: RESPUESTA API CON NUEVAS COLUMNAS ===")
    
    try:
        # Obtener datos a través de la API
        response = get_operator_sheet_data(file_upload_id, page=1, page_size=5)
        
        if not response.get('success'):
            print(f"❌ API falló: {response.get('error')}")
            return False
        
        data = response.get('data', [])
        columns = response.get('columns', [])
        display_names = response.get('displayNames', {})
        
        print(f"✓ API respondió exitosamente")
        print(f"  Total registros: {response.get('total', 0)}")
        print(f"  Registros en página: {len(data)}")
        
        # Verificar que las nuevas columnas están presentes
        has_cellid = 'cellid_decimal' in columns
        has_lac = 'lac_decimal' in columns
        
        print(f"  ✓ Columna cellid_decimal en respuesta: {'SI' if has_cellid else 'NO'}")
        print(f"  ✓ Columna lac_decimal en respuesta: {'SI' if has_lac else 'NO'}")
        
        # Verificar display names
        cellid_display = display_names.get('cellid_decimal', 'N/A')
        lac_display = display_names.get('lac_decimal', 'N/A')
        
        print(f"  Display name cellid_decimal: '{cellid_display}'")
        print(f"  Display name lac_decimal: '{lac_display}'")
        
        # Mostrar muestra de datos
        if data:
            print(f"\n✓ Muestra de datos convertidos:")
            for i, record in enumerate(data[:3], 1):
                celda_origen = record.get('celda_origen', 'N/A')
                cellid = record.get('cellid_decimal', 'N/A')
                lac = record.get('lac_decimal', 'N/A')
                print(f"  Registro {i}: {celda_origen} -> Cell ID: {cellid}, LAC: {lac}")
        
        return has_cellid and has_lac
        
    except Exception as e:
        print(f"❌ Error en API: {e}")
        return False


def test_data_validation(file_upload_id: str):
    """Valida la consistencia de los datos convertidos"""
    print("\n=== TEST: VALIDACION DE DATOS ===")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Estadísticas generales
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(celda_origen) as with_celda_origen,
                    COUNT(cellid_decimal) as with_cellid,
                    COUNT(lac_decimal) as with_lac
                FROM operator_call_data 
                WHERE file_upload_id = ?
            """, (file_upload_id,))
            
            stats = cursor.fetchone()
            total, with_celda, with_cellid, with_lac = stats
            
            print(f"✓ Estadísticas de conversión:")
            print(f"  Total registros: {total}")
            print(f"  Con celda_origen: {with_celda}")
            print(f"  Con cellid_decimal: {with_cellid}")
            print(f"  Con lac_decimal: {with_lac}")
            
            # Verificar consistencia
            conversion_rate = (with_cellid / with_celda * 100) if with_celda > 0 else 0
            print(f"  Tasa de conversión: {conversion_rate:.1f}%")
            
            # Verificar algunos valores específicos
            cursor.execute("""
                SELECT celda_origen, cellid_decimal, lac_decimal
                FROM operator_call_data 
                WHERE file_upload_id = ? 
                AND celda_origen = '07F083-05'
                LIMIT 1
            """, (file_upload_id,))
            
            specific_test = cursor.fetchone()
            if specific_test:
                celda, cellid, lac = specific_test
                expected_cellid = 520323  # 07F083 en hex = 520323 en decimal
                expected_lac = 5          # 05 en hex = 5 en decimal
                
                cellid_correct = cellid == expected_cellid
                lac_correct = lac == expected_lac
                
                print(f"\n✓ Verificación de conversión específica:")
                print(f"  {celda} -> Cell ID: {cellid} ({'✓' if cellid_correct else '❌'} esperado: {expected_cellid})")
                print(f"  {celda} -> LAC: {lac} ({'✓' if lac_correct else '❌'} esperado: {expected_lac})")
                
                return conversion_rate > 95 and cellid_correct and lac_correct
            
            return conversion_rate > 95
            
    except Exception as e:
        print(f"❌ Error en validación: {e}")
        return False


def cleanup_test_data(file_upload_id: str):
    """Limpia los datos de prueba"""
    print(f"\n=== LIMPIEZA DE DATOS DE PRUEBA ===")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Eliminar datos de prueba
            cursor.execute("DELETE FROM operator_call_data WHERE file_upload_id = ?", (file_upload_id,))
            deleted_call_data = cursor.rowcount
            
            cursor.execute("DELETE FROM operator_data_sheets WHERE id = ?", (file_upload_id,))
            deleted_sheets = cursor.rowcount
            
            conn.commit()
            
            print(f"✓ Limpieza completada:")
            print(f"  Registros de llamadas eliminados: {deleted_call_data}")
            print(f"  Hojas de datos eliminadas: {deleted_sheets}")
            
    except Exception as e:
        print(f"❌ Error en limpieza: {e}")


def main():
    """Función principal del test"""
    print("KRONOS - Test de Integración Cell ID y LAC para Movistar")
    print("=" * 60)
    
    # Setup
    if not setup_test_environment():
        print("\n❌ PRUEBAS FALLARON - Entorno no configurado correctamente")
        return
    
    # Test 1: Función de conversión
    converter_ok = test_cell_id_converter()
    
    # Test 2: Procesamiento de archivo
    processing_ok, file_upload_id = test_movistar_file_processing()
    
    if processing_ok and file_upload_id:
        # Test 3: Respuesta API
        api_ok = test_api_response(file_upload_id)
        
        # Test 4: Validación de datos
        validation_ok = test_data_validation(file_upload_id)
        
        # Limpieza
        cleanup_test_data(file_upload_id)
        
        # Resultado final
        all_tests_ok = converter_ok and processing_ok and api_ok and validation_ok
        
        print("\n" + "=" * 60)
        print(f"RESULTADO FINAL: {'✓ TODAS LAS PRUEBAS PASARON' if all_tests_ok else '❌ ALGUNAS PRUEBAS FALLARON'}")
        print(f"✓ Conversión Cell ID/LAC: {'PASS' if converter_ok else 'FAIL'}")
        print(f"✓ Procesamiento archivo: {'PASS' if processing_ok else 'FAIL'}")
        print(f"✓ Respuesta API: {'PASS' if api_ok else 'FAIL'}")
        print(f"✓ Validación datos: {'PASS' if validation_ok else 'FAIL'}")
        
        if all_tests_ok:
            print("\n🎉 La funcionalidad Cell ID y LAC está completamente implementada y funcionando!")
        else:
            print("\n⚠️  Algunas pruebas fallaron. Revisar la implementación.")
    
    else:
        print("\n❌ PRUEBAS FALLARON - No se pudo procesar el archivo de prueba")


if __name__ == "__main__":
    main()