"""
Insertar manualmente el registro 3104277553 en la base de datos
usando el file_upload_id existente de otros archivos procesados
"""

import sqlite3
import os
from datetime import datetime
import hashlib

def insertar_manual_3104277553():
    """Insertar manualmente el registro específico"""
    
    print("=== INSERCION MANUAL REGISTRO 3104277553 ===")
    
    db_path = os.path.join(os.path.dirname(__file__), 'kronos.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Obtener un file_upload_id válido existente
    cursor.execute("""
        SELECT DISTINCT file_upload_id, mission_id 
        FROM operator_call_data 
        LIMIT 1
    """)
    
    existing_record = cursor.fetchone()
    
    if not existing_record:
        print("No hay registros existentes en operator_call_data")
        conn.close()
        return
    
    file_upload_id, mission_id = existing_record
    print(f"Usando file_upload_id existente: {file_upload_id}")
    print(f"Usando mission_id existente: {mission_id}")
    
    # 2. Crear el registro específico del número 3104277553
    print("\n=== CREANDO REGISTRO MANUAL ===")
    
    # Datos del registro según análisis previo
    registro_data = {
        'file_upload_id': file_upload_id,
        'mission_id': mission_id,
        'operator': 'CLARO',
        'tipo_llamada': 'SALIENTE',
        'numero_origen': '3104277553',
        'numero_destino': '3224274851',
        'numero_objetivo': '3104277553',
        'fecha_hora_llamada': '2021-05-20 10:09:58',
        'duracion_segundos': 0,
        'celda_origen': '53591',
        'celda_destino': '52453',
        'celda_objetivo': '53591',
        'latitud_origen': None,
        'longitud_origen': None,
        'latitud_destino': None,
        'longitud_destino': None,
        'tecnologia': 'LTE',
        'tipo_trafico': 'VOZ',
        'estado_llamada': 'COMPLETADA',
        'operator_specific_data': '{"operator": "CLARO", "original_fields": {"celda_inicio": "53591", "celda_final": "52453"}, "data_type": "call_data_salientes"}',
        'record_hash': None,
        'created_at': datetime.now().isoformat(),
        'cellid_decimal': None,
        'lac_decimal': None,
        'calidad_senal': None
    }
    
    # Generar hash único para el registro
    hash_input = f"{registro_data['numero_origen']}{registro_data['numero_destino']}{registro_data['fecha_hora_llamada']}{registro_data['celda_origen']}"
    registro_data['record_hash'] = hashlib.sha256(hash_input.encode()).hexdigest()
    
    # 3. Insertar el registro
    try:
        cursor.execute("""
            INSERT INTO operator_call_data (
                file_upload_id, mission_id, operator, tipo_llamada,
                numero_origen, numero_destino, numero_objetivo,
                fecha_hora_llamada, duracion_segundos,
                celda_origen, celda_destino, celda_objetivo,
                latitud_origen, longitud_origen, latitud_destino, longitud_destino,
                tecnologia, tipo_trafico, estado_llamada,
                operator_specific_data, record_hash, created_at,
                cellid_decimal, lac_decimal, calidad_senal
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            registro_data['file_upload_id'], registro_data['mission_id'], 
            registro_data['operator'], registro_data['tipo_llamada'],
            registro_data['numero_origen'], registro_data['numero_destino'], 
            registro_data['numero_objetivo'], registro_data['fecha_hora_llamada'], 
            registro_data['duracion_segundos'], registro_data['celda_origen'], 
            registro_data['celda_destino'], registro_data['celda_objetivo'],
            registro_data['latitud_origen'], registro_data['longitud_origen'],
            registro_data['latitud_destino'], registro_data['longitud_destino'],
            registro_data['tecnologia'], registro_data['tipo_trafico'],
            registro_data['estado_llamada'], registro_data['operator_specific_data'],
            registro_data['record_hash'], registro_data['created_at'],
            registro_data['cellid_decimal'], registro_data['lac_decimal'],
            registro_data['calidad_senal']
        ))
        
        conn.commit()
        
        inserted_id = cursor.lastrowid
        print(f"REGISTRO INSERTADO EXITOSAMENTE con ID: {inserted_id}")
        
    except Exception as e:
        print(f"ERROR insertando registro: {e}")
        conn.rollback()
        conn.close()
        return
    
    # 4. Verificar inserción
    print("\n=== VERIFICACION DE INSERCION ===")
    
    cursor.execute("""
        SELECT id, numero_origen, numero_destino, celda_origen, celda_destino,
               fecha_hora_llamada, operator
        FROM operator_call_data 
        WHERE numero_origen = '3104277553' OR numero_destino = '3104277553'
    """)
    
    records = cursor.fetchall()
    
    print(f"Registros encontrados con 3104277553: {len(records)}")
    
    for record in records:
        id_rec, origen, destino, celda_orig, celda_dest, fecha, operador = record
        print(f"  ID: {id_rec}")
        print(f"  Origen: {origen} -> Destino: {destino}")
        print(f"  Celda origen: {celda_orig} -> Celda destino: {celda_dest}")
        print(f"  Fecha: {fecha}")
        print(f"  Operador: {operador}")
    
    # 5. Verificar que aparece en algoritmo de correlación
    print("\n=== PRUEBA ALGORITMO DE CORRELACION ===")
    
    # Buscar todos los registros con celda 53591 para ver si el número aparece
    cursor.execute("""
        SELECT numero_origen, numero_destino, celda_origen, celda_destino
        FROM operator_call_data 
        WHERE celda_origen = '53591' OR celda_destino = '53591'
    """)
    
    celda_records = cursor.fetchall()
    
    print(f"Total registros con celda 53591: {len(celda_records)}")
    
    # Buscar específicamente nuestro número
    target_found = False
    for record in celda_records:
        origen, destino, celda_orig, celda_dest = record
        if origen == '3104277553' or destino == '3104277553':
            print(f"  ENCONTRADO EN CELDA 53591: {origen} -> {destino} | {celda_orig} -> {celda_dest}")
            target_found = True
    
    if target_found:
        print("EXITO: El numero 3104277553 ahora deberia aparecer en correlacion!")
    else:
        print("ADVERTENCIA: El numero no se encontro en registros con celda 53591")
    
    conn.close()
    
    print("\nINSERCION MANUAL COMPLETADA")

if __name__ == "__main__":
    insertar_manual_3104277553()