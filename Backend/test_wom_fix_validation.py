"""
Test de Validación - Solución WOM Column calidad_senal
======================================================
Prueba automatizada para validar que la solución implementada para el problema
de la columna calidad_senal en WOM funciona correctamente.

Autor: KRONOS Development Team  
Fecha: 2025-08-15
"""

import os
import sys
import uuid
import sqlite3
from datetime import datetime

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db_connection
from services.file_processor_service import FileProcessorService
from services.operator_data_service import get_operator_sheet_data


def test_calidad_senal_column_exists():
    """Verifica que la columna calidad_senal existe en operator_call_data"""
    print("=== TEST: VERIFICACIÓN COLUMNA calidad_senal ===")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(operator_call_data)")
            columns = cursor.fetchall()
            
            # Buscar la columna calidad_senal
            calidad_senal_found = False
            for col in columns:
                if col[1] == 'calidad_senal':  # col[1] es el nombre de la columna
                    calidad_senal_found = True
                    print(f"OK Columna 'calidad_senal' encontrada: {col}")
                    break
            
            if not calidad_senal_found:
                print("ERROR Columna 'calidad_senal' NO encontrada")
                return False
            
            print("OK Columna calidad_senal existe en la tabla operator_call_data")
            return True
            
    except Exception as e:
        print(f"ERROR verificando columna: {e}")
        return False


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
            f"WOM-FIX-TEST-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "Test WOM Fix calidad_senal",
            "Prueba de validación para solución WOM calidad_senal",
            "En Progreso",
            "2024-01-01",
            "2024-12-31",
            "admin",
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        
    print(f"OK Mision de prueba creada: {mission_id}")
    return mission_id


def test_wom_file_processing_with_fix(mission_id):
    """Prueba el procesamiento del archivo WOM con la solución implementada"""
    print("\n=== TEST: PROCESAMIENTO WOM CON SOLUCIÓN ===")
    
    file_path = r"C:\Soluciones\BGC\claude\KNSOft\datatest\wom\Formato excel\PUNTO 1 TRÁFICO VOZ ENTRAN  SALIENT WOM.xlsx"
    
    if not os.path.exists(file_path):
        print(f"ERROR Archivo no encontrado: {file_path}")
        return False, None
    
    print(f"OK Archivo encontrado: {os.path.basename(file_path)}")
    
    try:
        # Generar IDs únicos
        file_upload_id = str(uuid.uuid4())
        file_name = os.path.basename(file_path)
        
        print(f"INFO File Upload ID: {file_upload_id}")
        
        # Leer archivo y calcular checksum
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
        
        import hashlib
        file_checksum = hashlib.sha256(file_bytes).hexdigest()
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
                'WOM',
                'LLAMADAS_UNIFICADAS',
                'PROCESSING',
                'test_user',
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            conn.commit()
        
        print("OK Registro operator_data_sheets creado exitosamente")
        
        # Crear instancia del procesador
        processor = FileProcessorService()
        
        # Procesar archivo WOM
        print("INFO Iniciando procesamiento WOM...")
        result = processor.process_wom_llamadas_entrantes(
            file_bytes, file_name, file_upload_id, mission_id
        )
        
        if result['success']:
            processed_records = result.get('processed_records', 0)
            failed_records = result.get('failed_records', 0)
            
            print(f"OK Procesamiento exitoso!")
            print(f"INFO Registros procesados: {processed_records}")
            print(f"WARN Registros fallidos: {failed_records}")
            
            # Actualizar estado a COMPLETED
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE operator_data_sheets 
                    SET processing_status = 'COMPLETED', 
                        records_processed = ?,
                        records_failed = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (processed_records, failed_records, datetime.now().isoformat(), file_upload_id))
                conn.commit()
            
            return True, file_upload_id, processed_records
        else:
            print(f"ERROR Error en procesamiento: {result.get('error', 'Error desconocido')}")
            
            # Actualizar estado a FAILED
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE operator_data_sheets 
                    SET processing_status = 'FAILED', updated_at = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), file_upload_id))
                conn.commit()
            
            return False, file_upload_id, 0
            
    except Exception as e:
        print(f"ERROR Excepcion durante procesamiento: {e}")
        return False, None, 0


def verify_wom_data_inserted(file_upload_id):
    """Verifica que los datos WOM se insertaron correctamente en la base de datos"""
    print(f"\n=== TEST: VERIFICACIÓN DATOS INSERTADOS ===")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Contar registros insertados
            cursor.execute("""
                SELECT COUNT(*) as total,
                       COUNT(calidad_senal) as with_calidad_senal,
                       COUNT(CASE WHEN calidad_senal IS NOT NULL THEN 1 END) as calidad_senal_not_null
                FROM operator_call_data 
                WHERE file_upload_id = ? AND operator = 'WOM'
            """, (file_upload_id,))
            
            stats = cursor.fetchone()
            
            if stats:
                total, with_calidad_senal, calidad_senal_not_null = stats
                
                print(f"📊 Total registros WOM: {total}")
                print(f"📊 Con campo calidad_senal: {with_calidad_senal}")
                print(f"📊 calidad_senal no nulo: {calidad_senal_not_null}")
                
                if total > 0:
                    # Mostrar algunos registros de ejemplo
                    cursor.execute("""
                        SELECT numero_origen, numero_destino, calidad_senal, celda_origen
                        FROM operator_call_data 
                        WHERE file_upload_id = ? AND operator = 'WOM'
                        LIMIT 3
                    """, (file_upload_id,))
                    
                    samples = cursor.fetchall()
                    print(f"\n📋 Muestra de datos insertados:")
                    for sample in samples:
                        origen, destino, calidad, celda = sample
                        print(f"  {origen} -> {destino} | Calidad: {calidad} | Celda: {celda}")
                    
                    return total > 0
                
            return False
            
    except Exception as e:
        print(f"❌ Error en verificación: {e}")
        return False


def cleanup_test_data(mission_id, file_upload_id):
    """Limpia los datos de prueba"""
    print(f"\n=== LIMPIEZA DATOS PRUEBA ===")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            call_deleted = 0
            sheet_deleted = 0
            mission_deleted = 0
            
            if file_upload_id:
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
            
            print(f"🗑️ Eliminado: {call_deleted} registros llamadas, {sheet_deleted} hoja, {mission_deleted} misión")
            
    except Exception as e:
        print(f"❌ Error en limpieza: {e}")


def main():
    """Función principal del test"""
    print("KRONOS - Test Validación Solución WOM calidad_senal")
    print("=" * 52)
    
    # Test 1: Verificar que la columna existe
    column_ok = test_calidad_senal_column_exists()
    
    if not column_ok:
        print("\n❌ FALLO CRÍTICO: La columna calidad_senal no existe")
        print("   Ejecutar: ALTER TABLE operator_call_data ADD COLUMN calidad_senal INTEGER;")
        return
    
    # Test 2: Crear misión de prueba
    mission_id = create_test_mission()
    
    try:
        # Test 3: Procesamiento de archivo WOM
        processing_ok, file_upload_id, processed_count = test_wom_file_processing_with_fix(mission_id)
        
        # Test 4: Verificación de datos insertados
        data_ok = False
        if processing_ok and file_upload_id and processed_count > 0:
            data_ok = verify_wom_data_inserted(file_upload_id)
        
        # Resultados finales
        print(f"\n{'='*52}")
        print("RESULTADOS FINALES:")
        print(f"✅ Columna calidad_senal: {'EXISTE' if column_ok else 'FALTA'}")
        print(f"{'✅' if processing_ok else '❌'} Procesamiento WOM: {'EXITOSO' if processing_ok else 'FALLIDO'}")
        print(f"{'✅' if data_ok else '❌'} Datos insertados: {'CORRECTOS' if data_ok else 'INCORRECTOS'}")
        print(f"📊 Registros procesados: {processed_count}")
        
        success = column_ok and processing_ok and data_ok
        print(f"\n🎯 RESULTADO GENERAL: {'ÉXITO - PROBLEMA SOLUCIONADO' if success else 'FALLO - REVISAR IMPLEMENTACIÓN'}")
        
        if success:
            print("\n🎉 La solución para WOM funciona correctamente!")
            print("   ✅ El archivo WOM ahora procesa registros exitosamente")
            print("   ✅ La columna calidad_senal permite la inserción correcta")
        
        # Preguntar si limpiar
        response = input(f"\n¿Limpiar datos de prueba? (s/N): ").strip().lower()
        if response == 's':
            cleanup_test_data(mission_id, file_upload_id)
            print("🗑️ Datos eliminados.")
        else:
            print(f"💾 Datos conservados:")
            print(f"  Mission ID: {mission_id}")
            if file_upload_id:
                print(f"  File Upload ID: {file_upload_id}")
        
    except Exception as e:
        print(f"❌ Error durante pruebas: {e}")
        cleanup_test_data(mission_id, None)


if __name__ == "__main__":
    main()