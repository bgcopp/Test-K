"""
Recarga específica del archivo que contiene 3104277553 con la corrección aplicada
"""

import sys
import os
import sqlite3

# Agregar el directorio de servicios al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.file_processor_service import FileProcessorService

def recargar_archivo_3104277553():
    """
    Recargar el archivo específico que contiene el número 3104277553
    """
    
    print("=== RECARGA ARCHIVO 3104277553 CON CORRECCIÓN APLICADA ===")
    print("=" * 70)
    
    # Ruta del archivo específico que contiene el número
    archivo_path = r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\1-225211_LLAMADAS_SALIENTES_POR_CELDA_545613_0.xlsx"
    
    print(f"Archivo a recargar: {os.path.basename(archivo_path)}")
    
    if not os.path.exists(archivo_path):
        print(f"❌ ERROR: No se encuentra el archivo {archivo_path}")
        return
    
    # 1. Eliminar registros existentes de este archivo de la base de datos
    print("\n=== PASO 1: LIMPIAR REGISTROS EXISTENTES ===")
    
    db_path = os.path.join(os.path.dirname(__file__), 'kronos.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Obtener el ID del archivo procesado anteriormente
    cursor.execute("""
        SELECT id, records_processed, records_failed 
        FROM operator_data_sheets 
        WHERE file_name LIKE '%545613%'
    """)
    
    file_info = cursor.fetchone()
    
    if file_info:
        file_id, old_processed, old_failed = file_info
        print(f"Archivo anterior encontrado: ID {file_id}")
        print(f"  - Registros procesados anteriormente: {old_processed}")
        print(f"  - Registros fallidos anteriormente: {old_failed}")
        
        # Eliminar registros de datos de llamadas de este archivo
        cursor.execute("DELETE FROM operator_call_data WHERE file_upload_id = ?", (file_id,))
        deleted_count = cursor.rowcount
        print(f"✅ Eliminados {deleted_count} registros de operator_call_data")
        
        # Eliminar el registro del archivo para que pueda ser reprocesado
        cursor.execute("DELETE FROM operator_data_sheets WHERE id = ?", (file_id,))
        print(f"✅ Eliminado registro de procesamiento anterior")
        
        conn.commit()
    else:
        print("No se encontró procesamiento anterior del archivo")
    
    conn.close()
    
    # 2. Recargar el archivo con la corrección aplicada
    print("\n=== PASO 2: RECARGAR ARCHIVO CON CORRECCIÓN ===")
    
    try:
        # Leer el archivo
        with open(archivo_path, 'rb') as f:
            file_bytes = f.read()
        
        file_name = os.path.basename(archivo_path)
        
        # Inicializar el procesador
        processor = FileProcessorService()
        
        # Procesar como archivo CLARO de llamadas salientes
        result = processor.process_claro_llamadas_salientes(
            file_bytes=file_bytes,
            file_name=file_name,
            file_upload_id=f"recarga-{file_name}",
            mission_id="mission_MPFRBNsb"  # Usar la misma misión
        )
        
        print("RESULTADO DE LA RECARGA:")
        if result.get('success', False):
            print(f"✅ RECARGA EXITOSA")
            print(f"  - Registros procesados: {result.get('processedRecords', 0)}")
            print(f"  - Registros fallidos: {result.get('records_failed', 0)}")
            print(f"  - Tasa de éxito: {result.get('success_rate', 0)}%")
        else:
            print(f"❌ RECARGA FALLÓ")
            print(f"  - Error: {result.get('error', 'Error desconocido')}")
            print(f"  - Registros procesados: {result.get('processedRecords', 0)}")
            
    except Exception as e:
        print(f"❌ ERROR durante la recarga: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. Verificar que el número 3104277553 ahora esté en la base de datos
    print("\n=== PASO 3: VERIFICACIÓN POST-RECARGA ===")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Buscar el número específico
    cursor.execute("""
        SELECT id, numero_origen, numero_destino, celda_origen, celda_destino, 
               fecha_hora_llamada, operator
        FROM operator_call_data 
        WHERE numero_origen = '3104277553' OR numero_destino = '3104277553'
    """)
    
    records = cursor.fetchall()
    
    print(f"Registros encontrados con número 3104277553: {len(records)}")
    
    if records:
        print("Detalles de registros encontrados:")
        for record in records:
            id_rec, origen, destino, celda_orig, celda_dest, fecha, operador = record
            print(f"  - ID: {id_rec}")
            print(f"    Origen: {origen} -> Destino: {destino}")
            print(f"    Celda origen: {celda_orig} -> Celda destino: {celda_dest}")
            print(f"    Fecha: {fecha}")
            print(f"    Operador: {operador}")
            print()
    else:
        print("❌ Aún no se encontraron registros con 3104277553")
    
    # Verificar registros con celda 53591
    cursor.execute("""
        SELECT COUNT(*) 
        FROM operator_call_data 
        WHERE celda_origen = '53591' OR celda_destino = '53591'
    """)
    
    cell_count = cursor.fetchone()[0]
    print(f"Registros totales con celda 53591: {cell_count}")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("RECARGA COMPLETADA")

if __name__ == "__main__":
    recargar_archivo_3104277553()