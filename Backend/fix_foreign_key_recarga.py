"""
Arreglar problema de foreign key y recargar archivo
"""

import sys
import os
import sqlite3
import uuid

# Agregar el directorio de servicios al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.file_processor_service import FileProcessorService

def fix_and_reload():
    """Arreglar foreign key y recargar"""
    
    print("=== FIX FOREIGN KEY Y RECARGA ===")
    
    db_path = os.path.join(os.path.dirname(__file__), 'kronos.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Verificar estructura de claves foráneas
    print("=== VERIFICANDO FOREIGN KEYS ===")
    
    cursor.execute("PRAGMA foreign_key_list(operator_call_data)")
    fkeys = cursor.fetchall()
    
    print(f"Foreign keys en operator_call_data: {len(fkeys)}")
    for fkey in fkeys:
        print(f"  {fkey}")
    
    # 2. Pre-insertar el registro del archivo en operator_data_sheets
    print("\n=== PRE-INSERTANDO REGISTRO DE ARCHIVO ===")
    
    file_upload_id = str(uuid.uuid4())
    mission_id = "mission_MPFRBNsb"
    file_name = "1-225211_LLAMADAS_SALIENTES_POR_CELDA_545613_0.xlsx"
    
    # Verificar que la misión existe
    cursor.execute("SELECT id FROM missions WHERE id = ?", (mission_id,))
    mission_exists = cursor.fetchone()
    
    if not mission_exists:
        print(f"Creando misión {mission_id}")
        cursor.execute("""
            INSERT INTO missions (id, code, name, description, status, start_date, created_by) 
            VALUES (?, 'TEST', 'Test Mission', 'Test mission for reload', 'ACTIVE', '2025-08-18', 'admin')
        """, (mission_id,))
    
    # Insertar registro del archivo
    cursor.execute("""
        INSERT INTO operator_data_sheets (
            id, mission_id, file_name, file_size_bytes, file_checksum,
            file_type, operator, operator_file_format, processing_status,
            records_processed, records_failed, uploaded_by, uploaded_at,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), datetime('now'))
    """, (
        file_upload_id, mission_id, file_name, 49643, 'test-checksum',
        'CALL_DATA', 'CLARO', 'CLARO_CALL_DATA_XLSX', 'PROCESSING',
        0, 0, 'admin'
    ))
    
    conn.commit()
    print(f"Pre-insertado archivo con ID: {file_upload_id}")
    
    # 3. Procesar el archivo manualmente
    print("\n=== PROCESANDO ARCHIVO MANUALMENTE ===")
    
    archivo_path = r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\1-225211_LLAMADAS_SALIENTES_POR_CELDA_545613_0.xlsx"
    
    try:
        with open(archivo_path, 'rb') as f:
            file_bytes = f.read()
        
        processor = FileProcessorService()
        
        # Usar el ID pre-insertado
        result = processor.process_claro_llamadas_salientes(
            file_bytes=file_bytes,
            file_name=file_name,
            file_upload_id=file_upload_id,  # Usar el ID ya insertado
            mission_id=mission_id
        )
        
        print("RESULTADO:")
        if result.get('success', False):
            print(f"EXITOSO - Procesados: {result.get('processedRecords', 0)}")
            print(f"Fallidos: {result.get('records_failed', 0)}")
        else:
            print(f"FALLO - Error: {result.get('error', 'Desconocido')}")
        
        # Actualizar el registro del archivo con los resultados
        cursor.execute("""
            UPDATE operator_data_sheets 
            SET processing_status = ?, records_processed = ?, records_failed = ?,
                processing_end_time = datetime('now')
            WHERE id = ?
        """, (
            'COMPLETED' if result.get('success', False) else 'FAILED',
            result.get('processedRecords', 0),
            result.get('records_failed', 0),
            file_upload_id
        ))
        
        conn.commit()
        
    except Exception as e:
        print(f"ERROR: {e}")
        # Marcar como fallido
        cursor.execute("""
            UPDATE operator_data_sheets 
            SET processing_status = 'FAILED', error_details = ?
            WHERE id = ?
        """, (str(e), file_upload_id))
        conn.commit()
        return
    
    # 4. Verificar resultado
    print("\n=== VERIFICACION FINAL ===")
    
    cursor.execute("""
        SELECT id, numero_origen, numero_destino, celda_origen, celda_destino 
        FROM operator_call_data 
        WHERE numero_origen = '3104277553' OR numero_destino = '3104277553'
    """)
    
    records = cursor.fetchall()
    
    print(f"Registros con 3104277553: {len(records)}")
    
    for record in records:
        id_rec, origen, destino, celda_orig, celda_dest = record
        print(f"  ENCONTRADO: {origen} -> {destino} | Celdas: {celda_orig} -> {celda_dest}")
    
    conn.close()
    
    print("PROCESO COMPLETADO")

if __name__ == "__main__":
    fix_and_reload()