"""
Test de un solo registro para identificar el problema exacto
Boris - KRONOS L2 Debug
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.file_processor_service import FileProcessorService
from services.data_normalizer_service import DataNormalizerService
import sqlite3
from datetime import datetime

def test_single_record():
    print("\n=== TEST DE REGISTRO ÚNICO ===")
    
    # Inicializar servicios
    processor = FileProcessorService()
    normalizer = DataNormalizerService()
    
    # Registro de prueba simple
    test_record = {
        'tipo': 'CDR_SALIENTE',
        'originador': '3104277553',
        'receptor': '3224274851',
        'fecha_hora': '12/08/2024 23:13:20',
        'duracion': '120',
        'celda_inicio_llamada': '12345',  # Numérico
        'celda_final_llamada': '67890'    # Numérico
    }
    
    print(f"\nRegistro de prueba: {test_record}")
    
    # Paso 1: Validación
    print("\n1. VALIDACIÓN:")
    is_valid, errors = processor._validate_claro_call_record(test_record, 'SALIENTE')
    print(f"   Válido: {is_valid}")
    if errors:
        print(f"   Errores: {errors}")
    
    if not is_valid:
        print("\n   *** FALLO EN VALIDACIÓN ***")
        return
    
    # Paso 2: Normalización
    print("\n2. NORMALIZACIÓN:")
    normalized = normalizer.normalize_claro_call_data_salientes(
        test_record,
        file_upload_id='TEST_001',
        mission_id='MISSION_001'
    )
    
    if not normalized:
        print("   *** FALLO EN NORMALIZACIÓN ***")
        return
    
    print(f"   Número origen: {normalized['numero_origen']}")
    print(f"   Número destino: {normalized['numero_destino']}")
    print(f"   Número objetivo: {normalized['numero_objetivo']}")
    print(f"   Hash: {normalized['record_hash']}")
    
    # Paso 3: Inserción en BD
    print("\n3. INSERCIÓN EN BD:")
    try:
        conn = sqlite3.connect('kronos.db')
        cursor = conn.cursor()
        
        # Intentar insertar
        cursor.execute("""
            INSERT INTO operator_call_data (
                file_upload_id, mission_id, operator, tipo_llamada,
                numero_origen, numero_destino, numero_objetivo,
                fecha_hora_llamada, duracion_segundos,
                celda_origen, celda_destino, celda_objetivo,
                latitud_origen, longitud_origen, latitud_destino, longitud_destino,
                tecnologia, tipo_trafico, estado_llamada,
                operator_specific_data, record_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            normalized['file_upload_id'],
            normalized['mission_id'],
            normalized['operator'],
            normalized['tipo_llamada'],
            normalized['numero_origen'],
            normalized['numero_destino'],
            normalized['numero_objetivo'],
            normalized['fecha_hora_llamada'],
            normalized['duracion_segundos'],
            normalized['celda_origen'],
            normalized['celda_destino'],
            normalized['celda_objetivo'],
            normalized['latitud_origen'],
            normalized['longitud_origen'],
            normalized['latitud_destino'],
            normalized['longitud_destino'],
            normalized['tecnologia'],
            normalized['tipo_trafico'],
            normalized['estado_llamada'],
            normalized['operator_specific_data'],
            normalized['record_hash']
        ))
        
        conn.commit()
        print("   [OK] Insercion exitosa")
        
        # Verificar
        cursor.execute("""
            SELECT * FROM operator_call_data
            WHERE numero_origen = ? AND numero_destino = ?
            ORDER BY id DESC LIMIT 1
        """, (normalized['numero_origen'], normalized['numero_destino']))
        
        result = cursor.fetchone()
        if result:
            print(f"   [OK] Registro verificado en BD (ID: {result[0]})")
        else:
            print("   [ERROR] Registro NO encontrado despues de insercion")
        
        conn.close()
        
    except Exception as e:
        print(f"   [ERROR] Error en insercion: {e}")
    
    print("\n=== FIN DEL TEST ===")

if __name__ == "__main__":
    test_single_record()