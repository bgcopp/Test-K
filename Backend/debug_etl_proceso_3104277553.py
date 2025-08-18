"""
Análisis específico del proceso ETL para el número 3104277553
Verificar por qué no se cargó a la base de datos si existe en Excel
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime

def debug_etl_3104277553():
    """Analizar el proceso ETL específico del número 3104277553"""
    
    print("=== DEBUG PROCESO ETL - NÚMERO 3104277553 ===")
    print("=" * 60)
    
    # 1. Información del archivo Excel según análisis previo
    excel_info = {
        'file': '1-225211_LLAMADAS_SALIENTES_POR_CELDA_545613_0.xlsx',
        'sheet': 'XDR',
        'row': 310,
        'role': 'originador',
        'cell': '53591',
        'originador': '3104277553',
        'receptor': '3224274851',
        'celda_inicio': '53591',
        'celda_final': '52453',
        'fecha_hora': '2021-05-20 10:09:58'
    }
    
    print("INFORMACIÓN DEL EXCEL (análisis previo):")
    for key, value in excel_info.items():
        print(f"  - {key}: {value}")
    
    # 2. Conectar a base de datos
    db_path = os.path.join(os.path.dirname(__file__), 'kronos.db')
    conn = sqlite3.connect(db_path)
    
    # 3. Verificar información del procesamiento del archivo
    print("\n=== INFORMACIÓN DE PROCESAMIENTO ===")
    
    query_file_processing = """
    SELECT 
        id, file_name, file_size_bytes, processing_status,
        records_processed, records_failed, processing_start_time,
        processing_end_time, error_details
    FROM operator_data_sheets 
    WHERE file_name LIKE '%545613%'
    """
    
    df_processing = pd.read_sql_query(query_file_processing, conn)
    
    if len(df_processing) > 0:
        proc_info = df_processing.iloc[0]
        print(f"Archivo procesado: {proc_info['file_name']}")
        print(f"Estado: {proc_info['processing_status']}")
        print(f"Registros procesados: {proc_info['records_processed']}")
        print(f"Registros fallidos: {proc_info['records_failed']}")
        print(f"Tiempo inicio: {proc_info['processing_start_time']}")
        print(f"Tiempo fin: {proc_info['processing_end_time']}")
        
        if proc_info['error_details']:
            print(f"Detalles de errores: {proc_info['error_details']}")
        
        file_upload_id = proc_info['id']
        
        # 4. Buscar registros específicos relacionados con este archivo
        print(f"\n=== REGISTROS EN BASE DE DATOS DEL ARCHIVO {file_upload_id} ===")
        
        query_file_records = """
        SELECT 
            id, numero_origen, numero_destino, celda_origen, celda_destino,
            fecha_hora_llamada, operator, tipo_llamada
        FROM operator_call_data 
        WHERE file_upload_id = ?
        ORDER BY id
        """
        
        df_records = pd.read_sql_query(query_file_records, conn, params=[file_upload_id])
        print(f"Total de registros cargados para este archivo: {len(df_records)}")
        
        # 5. Buscar específicamente registros con celda 53591
        print(f"\n=== REGISTROS CON CELDA 53591 ===")
        
        records_53591 = df_records[
            (df_records['celda_origen'] == '53591') | 
            (df_records['celda_destino'] == '53591')
        ]
        
        print(f"Registros con celda 53591: {len(records_53591)}")
        
        if len(records_53591) > 0:
            print("Detalles de registros con celda 53591:")
            for idx, record in records_53591.iterrows():
                print(f"  - ID: {record['id']}")
                print(f"    Origen: {record['numero_origen']}, Destino: {record['numero_destino']}")
                print(f"    Celda origen: {record['celda_origen']}, Celda destino: {record['celda_destino']}")
                print(f"    Fecha: {record['fecha_hora_llamada']}")
                print()
        
        # 6. Buscar cualquier registro que involucre los números del caso
        print(f"\n=== REGISTROS QUE INVOLUCREN NÚMEROS DEL CASO ===")
        
        target_numbers = ['3104277553', '3224274851']
        
        for number in target_numbers:
            records_with_number = df_records[
                (df_records['numero_origen'] == number) | 
                (df_records['numero_destino'] == number)
            ]
            
            print(f"Registros con número {number}: {len(records_with_number)}")
            
            if len(records_with_number) > 0:
                for idx, record in records_with_number.iterrows():
                    print(f"  - ID: {record['id']}")
                    print(f"    Origen: {record['numero_origen']} -> Destino: {record['numero_destino']}")
                    print(f"    Celda origen: {record['celda_origen']} -> Celda destino: {record['celda_destino']}")
                    print(f"    Fecha: {record['fecha_hora_llamada']}")
        
        # 7. Mostrar algunos ejemplos de registros procesados para comparar formato
        print(f"\n=== MUESTRA DE REGISTROS PROCESADOS (primeros 5) ===")
        
        sample_records = df_records.head()
        
        for idx, record in sample_records.iterrows():
            print(f"Registro {idx + 1}:")
            print(f"  - Origen: {record['numero_origen']} -> Destino: {record['numero_destino']}")
            print(f"  - Celda origen: {record['celda_origen']} -> Celda destino: {record['celda_destino']}")
            print(f"  - Fecha: {record['fecha_hora_llamada']}")
            print(f"  - Operador: {record['operator']}")
            print()
    
    else:
        print("❌ No se encontró información de procesamiento del archivo")
    
    conn.close()
    
    print("=" * 60)
    print("DEBUG ETL COMPLETADO")

if __name__ == "__main__":
    debug_etl_3104277553()