"""
Test Simple - Funcionalidad Cell ID y LAC para Movistar
=======================================================
Prueba basica de la funcionalidad de extraccion y conversion de Cell ID y LAC
desde archivos de Movistar.

Author: KRONOS Development Team  
Date: 2025-08-14
"""

import os
import sys
import sqlite3
from datetime import datetime

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db_connection
from services.file_processor_service import FileProcessorService
from services.operator_data_service import get_operator_sheet_data
from utils.cell_id_converter import extract_cellid_lac_from_celda_origen


def test_conversion():
    """Prueba la funcion de conversion"""
    print("\n=== TEST: CONVERSION CELL ID Y LAC ===")
    
    # Test con valor del archivo real
    result = extract_cellid_lac_from_celda_origen("07F083-05")
    expected_cellid = 520323  # 07F083 en hex
    expected_lac = 5          # 05 en hex
    
    print(f"Entrada: 07F083-05")
    print(f"Cell ID: {result['cellid_decimal']} (esperado: {expected_cellid})")
    print(f"LAC: {result['lac_decimal']} (esperado: {expected_lac})")
    
    cellid_ok = result['cellid_decimal'] == expected_cellid
    lac_ok = result['lac_decimal'] == expected_lac
    
    print(f"Conversion OK: {cellid_ok and lac_ok}")
    return cellid_ok and lac_ok


def test_database_columns():
    """Verifica que las columnas esten en la base de datos"""
    print("\n=== TEST: COLUMNAS EN BASE DE DATOS ===")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(operator_call_data)")
        columns = cursor.fetchall()
        
        column_names = [col[1] for col in columns]
        has_cellid = 'cellid_decimal' in column_names
        has_lac = 'lac_decimal' in column_names
        
        print(f"Columna cellid_decimal: {'SI' if has_cellid else 'NO'}")
        print(f"Columna lac_decimal: {'SI' if has_lac else 'NO'}")
        
        return has_cellid and has_lac


def test_existing_data():
    """Verifica los datos existentes en la base de datos"""
    print("\n=== TEST: DATOS EXISTENTES ===")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Contar registros con datos convertidos
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(cellid_decimal) as with_cellid,
                COUNT(lac_decimal) as with_lac
            FROM operator_call_data 
            WHERE operator = 'MOVISTAR'
        """)
        
        stats = cursor.fetchone()
        if stats:
            total, with_cellid, with_lac = stats
            print(f"Total registros MOVISTAR: {total}")
            print(f"Con cellid_decimal: {with_cellid}")
            print(f"Con lac_decimal: {with_lac}")
            
            if total > 0:
                conversion_rate = (with_cellid / total * 100)
                print(f"Tasa de conversion: {conversion_rate:.1f}%")
                
                # Mostrar algunas muestras
                cursor.execute("""
                    SELECT celda_origen, cellid_decimal, lac_decimal 
                    FROM operator_call_data 
                    WHERE operator = 'MOVISTAR' 
                    AND cellid_decimal IS NOT NULL 
                    LIMIT 3
                """)
                
                samples = cursor.fetchall()
                print("\nMuestras:")
                for sample in samples:
                    print(f"  {sample[0]} -> Cell ID: {sample[1]}, LAC: {sample[2]}")
                
                return conversion_rate > 0
        
        return False


def test_api_response():
    """Prueba la respuesta de la API"""
    print("\n=== TEST: RESPUESTA API ===")
    
    # Buscar un archivo MOVISTAR existente
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM operator_data_sheets 
            WHERE operator = 'MOVISTAR' 
            AND file_type = 'CALL_DATA'
            LIMIT 1
        """)
        
        file_record = cursor.fetchone()
        if not file_record:
            print("No hay archivos MOVISTAR para probar")
            return False
        
        file_upload_id = file_record[0]
        print(f"Probando con archivo: {file_upload_id}")
        
        # Obtener datos via API
        response = get_operator_sheet_data(file_upload_id, page=1, page_size=3)
        
        if response.get('success'):
            columns = response.get('columns', [])
            display_names = response.get('displayNames', {})
            data = response.get('data', [])
            
            has_cellid = 'cellid_decimal' in columns
            has_lac = 'lac_decimal' in columns
            
            print(f"API exitosa: SI")
            print(f"Columna cellid_decimal en respuesta: {'SI' if has_cellid else 'NO'}")
            print(f"Columna lac_decimal en respuesta: {'SI' if has_lac else 'NO'}")
            
            if data:
                record = data[0]
                cellid_val = record.get('cellid_decimal')
                lac_val = record.get('lac_decimal')
                celda_val = record.get('celda_origen')
                
                print(f"Ejemplo: {celda_val} -> Cell ID: {cellid_val}, LAC: {lac_val}")
            
            return has_cellid and has_lac
        else:
            print(f"API fallo: {response.get('error')}")
            return False


def main():
    """Funcion principal"""
    print("KRONOS - Test Simple Cell ID y LAC para Movistar")
    print("=" * 50)
    
    # Ejecutar tests
    test1 = test_conversion()
    test2 = test_database_columns()
    test3 = test_existing_data()
    test4 = test_api_response()
    
    # Resultado
    all_ok = test1 and test2 and test3 and test4
    
    print("\n" + "=" * 50)
    print("RESULTADOS:")
    print(f"Conversion: {'PASS' if test1 else 'FAIL'}")
    print(f"Columnas BD: {'PASS' if test2 else 'FAIL'}")
    print(f"Datos existentes: {'PASS' if test3 else 'FAIL'}")
    print(f"API: {'PASS' if test4 else 'FAIL'}")
    print(f"\nFINAL: {'TODAS LAS PRUEBAS PASARON' if all_ok else 'ALGUNAS PRUEBAS FALLARON'}")


if __name__ == "__main__":
    main()