"""
Test para verificar que la corrección del error FOREIGN KEY constraint failed funciona
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import get_db_connection
from services.file_processor_service import FileProcessorService
import pandas as pd

def test_foreign_key_fix():
    """Prueba la corrección de foreign keys en CLARO data processing"""
    
    print("=== TEST: Foreign Key Fix for CLARO Data Processing ===")
    
    # 1. Verificar que hay misiones disponibles
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM missions LIMIT 3")
        missions = cursor.fetchall()
        
        if not missions:
            print("ERROR: No hay misiones en la base de datos")
            return False
        
        print(f"Misiones disponibles: {missions}")
        mission_id = missions[0][0]
        
        # 2. Crear un registro de prueba en operator_data_sheets
        test_file_id = "test-foreign-key-fix-12345"
        # Generar un checksum de 64 caracteres válido (SHA256)
        test_checksum = "a" * 64  # Simular un SHA256 hash
        cursor.execute("""
            INSERT OR REPLACE INTO operator_data_sheets (
                id, mission_id, file_name, file_size_bytes, 
                file_checksum, file_type, operator, operator_file_format,
                processing_status, uploaded_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_file_id, mission_id, "test_fix.csv", 1000,
            test_checksum, "CELLULAR_DATA", "CLARO", 
            "CLARO_CELLULAR_DATA_CSV", "PROCESSING", "test_user"
        ))
        conn.commit()
        print(f"Registro de prueba creado: {test_file_id}")
    
    # 3. Crear DataFrame de prueba
    test_data = pd.DataFrame({
        'numero': ['573205487611', '573205487612'],
        'fecha_trafico': ['20240419080000', '20240419080001'],
        'tipo_cdr': ['DATOS', 'DATOS'],
        'celda_decimal': ['175462', '175463'],
        'lac_decimal': ['100', '101']
    })
    
    print(f"DataFrame de prueba creado: {len(test_data)} registros")
    
    # 4. Probar el procesamiento con la corrección
    processor = FileProcessorService()
    
    try:
        result = processor._process_claro_cellular_chunk(
            test_data, test_file_id, mission_id, 1
        )
        
        if result.get('success'):
            print(f"SUCCESS: Chunk procesado exitosamente")
            print(f"   Registros procesados: {result.get('records_processed', 0)}")
            print(f"   Registros fallidos: {result.get('records_failed', 0)}")
            
            # Verificar que se insertaron datos
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM operator_cellular_data WHERE file_upload_id = ?", 
                              (test_file_id,))
                count = cursor.fetchone()[0]
                print(f"   Registros en BD: {count}")
                
                if count > 0:
                    print("SUCCESS: Los datos se insertaron correctamente en la base de datos")
                    return True
                else:
                    print("WARNING: No se insertaron datos en la base de datos")
                    return False
        else:
            print(f"FAILED: {result.get('error', 'Error desconocido')}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False
        
    finally:
        # Limpiar datos de prueba
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM operator_cellular_data WHERE file_upload_id = ?", (test_file_id,))
            cursor.execute("DELETE FROM operator_data_sheets WHERE id = ?", (test_file_id,))
            conn.commit()
            print("Datos de prueba limpiados")

if __name__ == "__main__":
    success = test_foreign_key_fix()
    if success:
        print("\nRESULTADO: La corrección del error FOREIGN KEY funciona correctamente!")
    else:
        print("\nRESULTADO: La corrección NO resolvió el problema")