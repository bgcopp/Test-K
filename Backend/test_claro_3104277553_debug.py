"""
Test específico para debug del número 3104277553 en carga CLARO
Objetivo: Identificar por qué este número no llega a la base de datos
Boris - Análisis L2 KRONOS
"""

import sys
import os
import sqlite3
import pandas as pd
from datetime import datetime
import json

# Agregar el directorio padre al path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.file_processor_service import FileProcessorService
from services.data_normalizer_service import DataNormalizerService
from utils.operator_logger import OperatorLogger

def analyze_specific_number():
    """Analiza el procesamiento del número 3104277553"""
    
    print("\n" + "="*80)
    print("ANÁLISIS L2: DEBUG NÚMERO 3104277553 EN CARGA CLARO")
    print("="*80)
    
    # Inicializar servicios
    processor = FileProcessorService()
    normalizer = DataNormalizerService()
    logger = OperatorLogger()
    
    # Crear registro de prueba simulando el archivo real
    test_record = {
        'originador': '3104277553',
        'receptor': '3224274851',
        'fecha_hora': '12/08/2024 23:13:20',
        'duracion': '0',
        'tipo': 'CDR_SALIENTE',
        'celda_inicio_llamada': '12345',
        'celda_final_llamada': '67890'
    }
    
    print("\n1. REGISTRO DE PRUEBA:")
    print(json.dumps(test_record, indent=2))
    
    # === PASO 1: VALIDACIÓN ===
    print("\n2. VALIDACIÓN DEL REGISTRO:")
    is_valid, errors = processor._validate_claro_call_record(test_record, 'SALIENTE')
    print(f"   - ¿Es válido?: {is_valid}")
    if errors:
        print(f"   - Errores: {errors}")
    
    # === PASO 2: NORMALIZACIÓN DE NÚMEROS ===
    print("\n3. NORMALIZACIÓN DE NÚMEROS:")
    
    # Probar normalización del originador
    numero_origen_raw = test_record['originador']
    numero_origen_norm = normalizer._normalize_phone_number(numero_origen_raw)
    print(f"   - Originador raw: {numero_origen_raw}")
    print(f"   - Originador normalizado: {numero_origen_norm}")
    
    # Probar normalización del receptor
    numero_destino_raw = test_record['receptor']
    numero_destino_norm = normalizer._normalize_phone_number(numero_destino_raw)
    print(f"   - Receptor raw: {numero_destino_raw}")
    print(f"   - Receptor normalizado: {numero_destino_norm}")
    
    # === PASO 3: NORMALIZACIÓN COMPLETA ===
    print("\n4. NORMALIZACIÓN COMPLETA DEL REGISTRO:")
    normalized = normalizer.normalize_claro_call_data_salientes(
        test_record,
        file_upload_id='TEST_FILE_001',
        mission_id='TEST_MISSION_001'
    )
    
    if normalized:
        print("   - Normalización EXITOSA")
        print(f"   - Número origen final: {normalized.get('numero_origen')}")
        print(f"   - Número destino final: {normalized.get('numero_destino')}")
        print(f"   - Número objetivo: {normalized.get('numero_objetivo')}")
        print(f"   - Hash del registro: {normalized.get('record_hash')}")
    else:
        print("   - ERROR: La normalización falló")
    
    # === PASO 4: VERIFICAR BASE DE DATOS ===
    print("\n5. VERIFICACIÓN EN BASE DE DATOS:")
    try:
        conn = sqlite3.connect('kronos.db')
        cursor = conn.cursor()
        
        # Buscar el número en operator_call_data
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT file_upload_id) as archivos,
                   MIN(fecha_hora_llamada) as primera_llamada,
                   MAX(fecha_hora_llamada) as ultima_llamada
            FROM operator_call_data
            WHERE numero_origen = ? OR numero_destino = ? OR numero_objetivo = ?
        """, ('3104277553', '3104277553', '3104277553'))
        
        result = cursor.fetchone()
        print(f"   - Registros encontrados: {result[0]}")
        print(f"   - Archivos únicos: {result[1]}")
        if result[0] > 0:
            print(f"   - Primera llamada: {result[2]}")
            print(f"   - Última llamada: {result[3]}")
        
        # Buscar con prefijo 57
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM operator_call_data
            WHERE numero_origen = ? OR numero_destino = ? OR numero_objetivo = ?
        """, ('573104277553', '573104277553', '573104277553'))
        
        result_57 = cursor.fetchone()
        print(f"   - Registros con prefijo 57: {result_57[0]}")
        
        conn.close()
        
    except Exception as e:
        print(f"   - ERROR consultando BD: {e}")
    
    # === PASO 5: PROCESAR ARCHIVO REAL ===
    print("\n6. PROCESAMIENTO DE ARCHIVO REAL:")
    
    # Buscar archivo de salientes en el directorio
    salientes_path = None
    for root, dirs, files in os.walk('.'):
        for file in files:
            if 'saliente' in file.lower() and file.endswith('.csv'):
                salientes_path = os.path.join(root, file)
                break
        if salientes_path:
            break
    
    if salientes_path:
        print(f"   - Archivo encontrado: {salientes_path}")
        
        try:
            # Leer archivo y buscar el número
            df = pd.read_csv(salientes_path, encoding='utf-8', delimiter=',')
            
            # Buscar el número específico
            mask_origen = df['originador'].astype(str) == '3104277553'
            mask_receptor = df['receptor'].astype(str) == '3104277553'
            
            registros = df[mask_origen | mask_receptor]
            
            print(f"   - Registros con el número en archivo: {len(registros)}")
            
            if len(registros) > 0:
                print("\n   REGISTROS ENCONTRADOS EN ARCHIVO:")
                for idx, row in registros.iterrows():
                    print(f"   Fila {idx + 1}:")
                    print(f"     - Originador: {row['originador']}")
                    print(f"     - Receptor: {row['receptor']}")
                    print(f"     - Fecha: {row['fecha_hora']}")
                    print(f"     - Tipo: {row['tipo']}")
                    
        except Exception as e:
            print(f"   - ERROR leyendo archivo: {e}")
    else:
        print("   - No se encontró archivo de salientes")
    
    # === PASO 6: SIMULAR INSERCIÓN ===
    print("\n7. SIMULACIÓN DE INSERCIÓN EN BD:")
    if normalized:
        try:
            conn = sqlite3.connect('kronos_test.db')
            cursor = conn.cursor()
            
            # Crear tabla si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS operator_call_data_test (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_upload_id TEXT,
                    mission_id TEXT,
                    numero_origen TEXT,
                    numero_destino TEXT,
                    numero_objetivo TEXT,
                    fecha_hora_llamada TEXT,
                    record_hash TEXT
                )
            """)
            
            # Insertar registro
            cursor.execute("""
                INSERT INTO operator_call_data_test (
                    file_upload_id, mission_id, numero_origen,
                    numero_destino, numero_objetivo, fecha_hora_llamada,
                    record_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                normalized['file_upload_id'],
                normalized['mission_id'],
                normalized['numero_origen'],
                normalized['numero_destino'],
                normalized['numero_objetivo'],
                normalized['fecha_hora_llamada'],
                normalized['record_hash']
            ))
            
            conn.commit()
            print("   - Inserción EXITOSA en BD de prueba")
            
            # Verificar inserción
            cursor.execute("""
                SELECT * FROM operator_call_data_test
                WHERE numero_origen = ? OR numero_destino = ?
            """, ('3104277553', '3104277553'))
            
            test_result = cursor.fetchone()
            if test_result:
                print("   - Registro verificado en BD de prueba")
            else:
                print("   - ERROR: Registro no encontrado después de inserción")
            
            conn.close()
            
        except Exception as e:
            print(f"   - ERROR en inserción de prueba: {e}")
    
    print("\n" + "="*80)
    print("CONCLUSIÓN DEL ANÁLISIS")
    print("="*80)
    
    if normalized:
        print("\n✓ El registro SE PUEDE normalizar correctamente")
        print("✓ Los números se procesan sin problemas")
        print("\nPOSIBLES CAUSAS DEL PROBLEMA:")
        print("1. Duplicados: El hash del registro ya existe en BD")
        print("2. Transacciones no confirmadas: rollback por error en otro registro")
        print("3. Filtrado por validación adicional no detectada")
        print("4. Error en chunk processing que aborta antes de procesar este registro")
    else:
        print("\n✗ El registro NO se puede normalizar")
        print("REVISAR: Logs de normalización para identificar el error específico")

if __name__ == "__main__":
    analyze_specific_number()