"""
Debug específico del error FOREIGN KEY constraint failed
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import get_db_connection
import pandas as pd

def debug_foreign_key_error():
    """Debug del error de foreign key con información detallada"""
    
    print("=== DEBUG: Foreign Key Error Analysis ===")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Verificar estado de foreign keys
        cursor.execute("PRAGMA foreign_keys")
        fk_status = cursor.fetchone()[0]
        print(f"Foreign keys habilitadas: {fk_status}")
        
        # 2. Crear registros padre
        test_file_id = "debug-fk-test-123"
        test_checksum = "b" * 64  # SHA256 válido
        
        # Verificar que existe la misión
        cursor.execute("SELECT id, name FROM missions WHERE id = 'm1'")
        mission = cursor.fetchone()
        if mission:
            print(f"Mision encontrada: {mission}")
        else:
            print("ERROR: Mision m1 no existe")
            return
        
        # Crear registro en operator_data_sheets
        cursor.execute("""
            INSERT OR REPLACE INTO operator_data_sheets (
                id, mission_id, file_name, file_size_bytes, 
                file_checksum, file_type, operator, operator_file_format,
                processing_status, uploaded_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_file_id, "m1", "debug_test.csv", 1000,
            test_checksum, "CELLULAR_DATA", "CLARO", 
            "CLARO_CELLULAR_DATA_CSV", "PROCESSING", "debug_user"
        ))
        conn.commit()
        print(f"Registro padre creado: {test_file_id}")
        
        # 3. Verificar que el registro padre existe
        cursor.execute("SELECT id, mission_id FROM operator_data_sheets WHERE id = ?", (test_file_id,))
        parent_record = cursor.fetchone()
        if parent_record:
            print(f"Registro padre confirmado: {parent_record}")
        else:
            print("ERROR: No se pudo crear registro padre")
            return
        
        # 4. Intentar INSERT directo en operator_cellular_data
        print("Intentando INSERT directo...")
        try:
            cursor.execute("""
                INSERT INTO operator_cellular_data (
                    file_upload_id, mission_id, operator, numero_telefono,
                    fecha_hora_inicio, celda_id, lac_tac, trafico_subida_bytes,
                    trafico_bajada_bytes, tecnologia, tipo_conexion, record_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                test_file_id,           # file_upload_id
                "m1",                   # mission_id
                "CLARO",                # operator
                "573205487611",         # numero_telefono
                "2024-04-19 08:00:00",  # fecha_hora_inicio
                "175462",               # celda_id
                "100",                  # lac_tac
                0,                      # trafico_subida_bytes
                0,                      # trafico_bajada_bytes
                "LTE",                  # tecnologia
                "DATOS",                # tipo_conexion
                "test_hash_123"         # record_hash
            ))
            
            print("SUCCESS: INSERT directo funcionó")
            
            # Verificar que se insertó
            cursor.execute("SELECT COUNT(*) FROM operator_cellular_data WHERE file_upload_id = ?", (test_file_id,))
            count = cursor.fetchone()[0]
            print(f"Registros insertados: {count}")
            
        except Exception as e:
            print(f"ERROR en INSERT directo: {e}")
            
            # Verificar específicamente cada FK
            print("Verificando foreign keys individualmente...")
            
            # FK 1: file_upload_id
            cursor.execute("SELECT id FROM operator_data_sheets WHERE id = ?", (test_file_id,))
            fk1_exists = cursor.fetchone()
            print(f"FK1 (file_upload_id) existe: {fk1_exists is not None}")
            
            # FK 2: mission_id  
            cursor.execute("SELECT id FROM missions WHERE id = ?", ("m1",))
            fk2_exists = cursor.fetchone()
            print(f"FK2 (mission_id) existe: {fk2_exists is not None}")
            
        finally:
            # Limpiar
            cursor.execute("DELETE FROM operator_cellular_data WHERE file_upload_id = ?", (test_file_id,))
            cursor.execute("DELETE FROM operator_data_sheets WHERE id = ?", (test_file_id,))
            conn.commit()
            print("Datos de prueba limpiados")

if __name__ == "__main__":
    debug_foreign_key_error()