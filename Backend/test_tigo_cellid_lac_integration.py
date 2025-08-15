"""
Test de Integración - Funcionalidad Cell ID y LAC para TIGO
===========================================================
Prueba completa de la funcionalidad de extracción y conversión de Cell ID y LAC
desde archivos de TIGO, usando el formato CELDA_ORIGEN_TRUNCADA.

Author: KRONOS Development Team
Date: 2025-08-14
"""

import os
import sys
import uuid
from datetime import datetime

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db_connection
from services.file_processor_service import FileProcessorService
from services.operator_data_service import get_operator_sheet_data
from utils.cell_id_converter import extract_cellid_lac_from_celda_origen


def test_tigo_conversion_function():
    """Prueba la función de conversión específica para TIGO"""
    print("=== TEST: CONVERSION TIGO ===")
    
    # Valores del archivo real de TIGO
    test_cases = [
        ("010006CC", {"cellid_decimal": 65542, "lac_decimal": 204}),
        ("030006CC", {"cellid_decimal": 196614, "lac_decimal": 204}), 
        ("020006CC", {"cellid_decimal": 131078, "lac_decimal": 204}),
        ("0001D799", {"cellid_decimal": 471, "lac_decimal": 153}),
        ("0001AF5D", {"cellid_decimal": 431, "lac_decimal": 93}),
    ]
    
    all_passed = True
    
    for input_val, expected in test_cases:
        result = extract_cellid_lac_from_celda_origen(input_val, "TIGO")
        passed = result == expected
        all_passed &= passed
        
        status = "PASS" if passed else "FAIL"
        print(f"{status}: {input_val} -> Cell ID: {result['cellid_decimal']}, LAC: {result['lac_decimal']}")
        if not passed:
            print(f"   Esperado: {expected}")
    
    print(f"Resultado función conversión: {'PASS' if all_passed else 'FAIL'}")
    return all_passed


def create_test_mission():
    """Crea una misión de prueba"""
    mission_id = str(uuid.uuid4())
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO missions (
                id, code, name, description, status, start_date, 
                end_date, created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            mission_id,
            f"TIGO-TEST-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "Test Cell ID LAC TIGO",
            "Prueba de funcionalidad Cell ID y LAC para archivos TIGO",
            "En Progreso",
            "2024-01-01",
            "2024-12-31",
            "admin",
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        
    print(f"Mision creada: {mission_id}")
    return mission_id


def test_tigo_file_processing(mission_id):
    """Prueba el procesamiento del archivo TIGO con Cell ID y LAC"""
    print("\n=== TEST: PROCESAMIENTO ARCHIVO TIGO ===")
    
    file_path = r"C:\Soluciones\BGC\claude\KNSOft\datatest\Tigo\Formato Excel\Reporte TIGO.xlsx"
    
    if not os.path.exists(file_path):
        print(f"Archivo no encontrado: {file_path}")
        return False, None
    
    print(f"Archivo encontrado: {os.path.basename(file_path)}")
    
    try:
        # Generar IDs únicos
        file_upload_id = str(uuid.uuid4())
        file_name = os.path.basename(file_path)
        
        print(f"File Upload ID: {file_upload_id}")
        
        # Leer archivo y calcular checksum
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
        
        import hashlib
        file_checksum = hashlib.sha256(file_bytes).hexdigest()  # SHA-256 para 64 caracteres
        file_size = len(file_bytes)
        
        # Crear registro en operator_data_sheets primero (requerido por FOREIGN KEY)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO operator_data_sheets (
                    id, mission_id, file_name, file_size_bytes, 
                    file_checksum, file_type, operator, operator_file_format,
                    processing_status, uploaded_by, uploaded_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                file_upload_id,
                mission_id,
                file_name,
                file_size,
                file_checksum,
                'CALL_DATA',
                'TIGO',
                'LLAMADAS_UNIFICADAS',
                'PROCESSING',
                'test_user',
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            conn.commit()
        
        print("Registro operator_data_sheets creado exitosamente")
        
        # Crear instancia del procesador
        processor = FileProcessorService()
        
        # Procesar archivo TIGO
        print("Iniciando procesamiento TIGO...")
        result = processor.process_tigo_llamadas_unificadas(
            file_bytes, file_name, file_upload_id, mission_id
        )
        
        if result['success']:
            processed_records = result.get('processed_records', 0)
            failed_records = result.get('failed_records', 0)
            
            print(f"Procesamiento exitoso!")
            print(f"Registros procesados: {processed_records}")
            print(f"Registros fallidos: {failed_records}")
            
            # Actualizar estado a COMPLETED
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE operator_data_sheets 
                    SET processing_status = 'COMPLETED', updated_at = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), file_upload_id))
                conn.commit()
            
            return True, file_upload_id
        else:
            print(f"Error en procesamiento: {result.get('error', 'Error desconocido')}")
            
            # Actualizar estado a FAILED
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE operator_data_sheets 
                    SET processing_status = 'FAILED', updated_at = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), file_upload_id))
                conn.commit()
            
            return False, None
            
    except Exception as e:
        print(f"Excepción durante procesamiento: {e}")
        
        # Actualizar estado a ERROR si existe el registro
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE operator_data_sheets 
                    SET processing_status = 'ERROR', updated_at = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), file_upload_id))
                conn.commit()
        except:
            pass
        
        return False, None


def verify_tigo_cellid_lac_data(file_upload_id):
    """Verifica los datos de Cell ID y LAC procesados para TIGO"""
    print(f"\n=== TEST: VERIFICACION DATOS TIGO ===")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Estadísticas generales
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(DISTINCT celda_origen) as unique_celdas,
                    COUNT(cellid_decimal) as with_cellid,
                    COUNT(lac_decimal) as with_lac,
                    MIN(cellid_decimal) as min_cellid,
                    MAX(cellid_decimal) as max_cellid,
                    MIN(lac_decimal) as min_lac,
                    MAX(lac_decimal) as max_lac
                FROM operator_call_data 
                WHERE file_upload_id = ? 
                AND operator = 'TIGO'
            """, (file_upload_id,))
            
            stats = cursor.fetchone()
            
            if stats:
                total, unique_celdas, with_cellid, with_lac = stats[:4]
                min_cellid, max_cellid, min_lac, max_lac = stats[4:]
                
                print(f"Total registros TIGO: {total}")
                print(f"Celdas únicas: {unique_celdas}")
                print(f"Con Cell ID: {with_cellid}")
                print(f"Con LAC: {with_lac}")
                print(f"Cell ID rango: {min_cellid} - {max_cellid}")
                print(f"LAC rango: {min_lac} - {max_lac}")
                
                if total > 0:
                    conversion_rate = (with_cellid / total * 100)
                    print(f"Tasa conversión: {conversion_rate:.1f}%")
                    
                    # Verificar algunas conversiones específicas
                    cursor.execute("""
                        SELECT celda_origen, cellid_decimal, lac_decimal, COUNT(*) as count
                        FROM operator_call_data 
                        WHERE file_upload_id = ?
                        AND cellid_decimal IS NOT NULL 
                        AND lac_decimal IS NOT NULL
                        GROUP BY celda_origen, cellid_decimal, lac_decimal
                        ORDER BY count DESC
                        LIMIT 5
                    """, (file_upload_id,))
                    
                    samples = cursor.fetchall()
                    print(f"\nConversiones más frecuentes:")
                    for sample in samples:
                        celda, cellid, lac, count = sample
                        print(f"  {celda} -> Cell ID: {cellid}, LAC: {lac} ({count} registros)")
                    
                    return conversion_rate > 90  # Esperamos al menos 90% de conversión
                
            return False
            
    except Exception as e:
        print(f"Error en verificación: {e}")
        return False


def test_tigo_api_response(file_upload_id):
    """Prueba la respuesta de la API con las nuevas columnas para TIGO"""
    print(f"\n=== TEST: API TIGO CON NUEVAS COLUMNAS ===")
    
    try:
        # Obtener datos a través de la API
        response = get_operator_sheet_data(file_upload_id, page=1, page_size=5)
        
        if not response.get('success'):
            print(f"API falló: {response.get('error')}")
            return False
        
        data = response.get('data', [])
        columns = response.get('columns', [])
        display_names = response.get('displayNames', {})
        
        print(f"API exitosa: {len(data)} registros obtenidos")
        print(f"Columnas disponibles: {len(columns)}")
        
        # Verificar que las nuevas columnas están presentes
        has_cellid = 'cellid_decimal' in columns
        has_lac = 'lac_decimal' in columns
        
        print(f"Columna cellid_decimal: {'SI' if has_cellid else 'NO'}")
        print(f"Columna lac_decimal: {'SI' if has_lac else 'NO'}")
        
        if has_cellid:
            cellid_display = display_names.get('cellid_decimal', 'N/A')
            print(f"  Display name: '{cellid_display}'")
        
        if has_lac:
            lac_display = display_names.get('lac_decimal', 'N/A')
            print(f"  Display name: '{lac_display}'")
        
        # Mostrar muestra de datos
        if data:
            print(f"\nMuestra de datos TIGO:")
            for i, record in enumerate(data[:3], 1):
                celda_origen = record.get('celda_origen', 'N/A')
                cellid = record.get('cellid_decimal', 'N/A')
                lac = record.get('lac_decimal', 'N/A')
                numero_origen = record.get('numero_origen', 'N/A')
                tipo_llamada = record.get('tipo_llamada', 'N/A')
                
                print(f"  {i}. {numero_origen} ({tipo_llamada})")
                print(f"     Celda: {celda_origen} -> Cell ID: {cellid}, LAC: {lac}")
        
        return has_cellid and has_lac
        
    except Exception as e:
        print(f"Error en API: {e}")
        return False


def cleanup_test_data(mission_id, file_upload_id):
    """Limpia los datos de prueba"""
    print(f"\n=== LIMPIEZA DATOS PRUEBA ===")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Eliminar datos de llamadas
            cursor.execute("DELETE FROM operator_call_data WHERE file_upload_id = ?", (file_upload_id,))
            call_deleted = cursor.rowcount
            
            # Eliminar hoja de datos
            cursor.execute("DELETE FROM operator_data_sheets WHERE id = ?", (file_upload_id,))
            sheet_deleted = cursor.rowcount
            
            # Eliminar misión
            cursor.execute("DELETE FROM missions WHERE id = ?", (mission_id,))
            mission_deleted = cursor.rowcount
            
            conn.commit()
            
            print(f"Eliminado: {call_deleted} registros, {sheet_deleted} hoja, {mission_deleted} mision")
            
    except Exception as e:
        print(f"Error en limpieza: {e}")


def main():
    """Función principal del test"""
    print("KRONOS - Test Integración Cell ID y LAC para TIGO")
    print("=" * 48)
    
    # Test 1: Función de conversión
    conversion_ok = test_tigo_conversion_function()
    
    # Crear misión
    mission_id = create_test_mission()
    
    try:
        # Test 2: Procesamiento de archivo
        processing_ok, file_upload_id = test_tigo_file_processing(mission_id)
        
        if processing_ok and file_upload_id:
            # Test 3: Verificación de datos
            data_ok = verify_tigo_cellid_lac_data(file_upload_id)
            
            # Test 4: Respuesta API
            api_ok = test_tigo_api_response(file_upload_id)
            
            # Resultado final
            all_tests_ok = conversion_ok and processing_ok and data_ok and api_ok
            
            print(f"\n{'='*48}")
            print("RESULTADOS:")
            print(f"Conversión TIGO: {'PASS' if conversion_ok else 'FAIL'}")
            print(f"Procesamiento archivo: {'PASS' if processing_ok else 'FAIL'}")
            print(f"Verificación datos: {'PASS' if data_ok else 'FAIL'}")
            print(f"API con nuevos campos: {'PASS' if api_ok else 'FAIL'}")
            print(f"RESULTADO FINAL: {'EXITOSO' if all_tests_ok else 'CON ERRORES'}")
            
            if all_tests_ok:
                print("\nLa funcionalidad Cell ID y LAC para TIGO está funcionando!")
            
            # Preguntar si limpiar
            response = input(f"\n¿Limpiar datos de prueba? (s/N): ").strip().lower()
            if response == 's':
                cleanup_test_data(mission_id, file_upload_id)
                print("Datos eliminados.")
            else:
                print(f"Datos conservados:")
                print(f"  Mission ID: {mission_id}")
                print(f"  File Upload ID: {file_upload_id}")
        
        else:
            cleanup_test_data(mission_id, None)
            print("Prueba fallida en procesamiento")
            
    except Exception as e:
        print(f"Error durante pruebas: {e}")
        cleanup_test_data(mission_id, None)


if __name__ == "__main__":
    main()