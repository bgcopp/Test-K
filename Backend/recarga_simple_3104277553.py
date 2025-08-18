"""
Recarga simple del archivo que contiene 3104277553
"""

import sys
import os
import sqlite3

# Agregar el directorio de servicios al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.file_processor_service import FileProcessorService

def recargar_simple():
    """Recarga simple del archivo"""
    
    print("=== RECARGA SIMPLE ARCHIVO 3104277553 ===")
    
    # Archivo específico
    archivo_path = r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\1-225211_LLAMADAS_SALIENTES_POR_CELDA_545613_0.xlsx"
    
    print(f"Archivo: {os.path.basename(archivo_path)}")
    
    if not os.path.exists(archivo_path):
        print(f"ERROR: No se encuentra el archivo {archivo_path}")
        return
    
    # 1. Limpiar registros existentes
    print("\n=== LIMPIANDO REGISTROS EXISTENTES ===")
    
    db_path = os.path.join(os.path.dirname(__file__), 'kronos.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Buscar el archivo anterior
    cursor.execute("""
        SELECT id, records_processed, records_failed 
        FROM operator_data_sheets 
        WHERE file_name LIKE '%545613%'
    """)
    
    file_info = cursor.fetchone()
    
    if file_info:
        file_id, old_processed, old_failed = file_info
        print(f"Archivo encontrado: {file_id}")
        print(f"Procesados anteriormente: {old_processed}")
        print(f"Fallidos anteriormente: {old_failed}")
        
        # Eliminar datos
        cursor.execute("DELETE FROM operator_call_data WHERE file_upload_id = ?", (file_id,))
        deleted_count = cursor.rowcount
        print(f"Eliminados {deleted_count} registros")
        
        # Eliminar registro del archivo
        cursor.execute("DELETE FROM operator_data_sheets WHERE id = ?", (file_id,))
        print("Eliminado registro de procesamiento")
        
        conn.commit()
    
    conn.close()
    
    # 2. Recargar archivo
    print("\n=== RECARGANDO ARCHIVO ===")
    
    try:
        with open(archivo_path, 'rb') as f:
            file_bytes = f.read()
        
        file_name = os.path.basename(archivo_path)
        
        processor = FileProcessorService()
        
        result = processor.process_claro_llamadas_salientes(
            file_bytes=file_bytes,
            file_name=file_name,
            file_upload_id=f"recarga-{file_name}",
            mission_id="mission_MPFRBNsb"
        )
        
        print("RESULTADO:")
        if result.get('success', False):
            print(f"EXITOSA - Procesados: {result.get('processedRecords', 0)}")
            print(f"Fallidos: {result.get('records_failed', 0)}")
        else:
            print(f"FALLO - Error: {result.get('error', 'Desconocido')}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        return
    
    # 3. Verificar resultado
    print("\n=== VERIFICACION ===")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Buscar 3104277553
    cursor.execute("""
        SELECT id, numero_origen, numero_destino, celda_origen, celda_destino 
        FROM operator_call_data 
        WHERE numero_origen = '3104277553' OR numero_destino = '3104277553'
    """)
    
    records = cursor.fetchall()
    
    print(f"Registros con 3104277553: {len(records)}")
    
    for record in records:
        id_rec, origen, destino, celda_orig, celda_dest = record
        print(f"  ID: {id_rec} | {origen} -> {destino} | Celdas: {celda_orig} -> {celda_dest}")
    
    # Verificar celda 53591
    cursor.execute("""
        SELECT COUNT(*) 
        FROM operator_call_data 
        WHERE celda_origen = '53591' OR celda_destino = '53591'
    """)
    
    cell_count = cursor.fetchone()[0]
    print(f"Registros con celda 53591: {cell_count}")
    
    conn.close()
    
    print("\nRECARGA COMPLETADA")

if __name__ == "__main__":
    recargar_simple()