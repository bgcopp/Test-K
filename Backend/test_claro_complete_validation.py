"""
Test de validación completa para carga de archivos CLARO
Verifica que TODOS los números objetivo se procesen correctamente
Boris - KRONOS L2 Analysis
"""

import sys
import os
import sqlite3
import pandas as pd
from datetime import datetime
import json
import base64
from pathlib import Path

# Agregar el directorio padre al path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.file_processor_service import FileProcessorService
from services.operator_data_service import OperatorDataService
from services.data_normalizer_service import DataNormalizerService
from utils.operator_logger import OperatorLogger

def create_test_claro_files():
    """Crea archivos de prueba CLARO con los números objetivo"""
    
    # Números objetivo de Boris
    target_numbers = [
        '3224274851', '3208611034', '3104277553', 
        '3102715509', '3143534707', '3214161903'
    ]
    
    print("\n=== CREANDO ARCHIVOS DE PRUEBA CLARO ===")
    
    # Crear archivo de llamadas salientes
    salientes_data = []
    for i, target in enumerate(target_numbers):
        # Crear llamadas donde el target es originador
        salientes_data.append({
            'tipo': 'CDR_SALIENTE',
            'originador': target,
            'receptor': f'310{5000000 + i}',
            'fecha_hora': f'12/08/2024 10:{i:02d}:00',
            'duracion': str(60 + i * 10),
            'celda_inicio_llamada': f'CELL_{i}_START',
            'celda_final_llamada': f'CELL_{i}_END'
        })
        
        # Crear llamadas donde el target es receptor
        salientes_data.append({
            'tipo': 'CDR_SALIENTE',
            'originador': f'320{4000000 + i}',
            'receptor': target,
            'fecha_hora': f'12/08/2024 11:{i:02d}:00',
            'duracion': str(120 + i * 5),
            'celda_inicio_llamada': f'CELL_{i}_A',
            'celda_final_llamada': f'CELL_{i}_B'
        })
    
    # Agregar el caso específico reportado por Boris
    salientes_data.append({
        'tipo': 'CDR_SALIENTE',
        'originador': '3104277553',
        'receptor': '3224274851',
        'fecha_hora': '12/08/2024 23:13:20',
        'duracion': '0',
        'celda_inicio_llamada': 'CELL_BORIS_1',
        'celda_final_llamada': 'CELL_BORIS_2'
    })
    
    df_salientes = pd.DataFrame(salientes_data)
    salientes_path = 'test_claro_salientes.csv'
    df_salientes.to_csv(salientes_path, index=False)
    print(f"   Archivo creado: {salientes_path} ({len(df_salientes)} registros)")
    
    # Crear archivo de llamadas entrantes
    entrantes_data = []
    for i, target in enumerate(target_numbers):
        entrantes_data.append({
            'tipo': 'CDR_ENTRANTE',
            'originador': f'315{6000000 + i}',
            'receptor': target,
            'fecha_hora': f'13/08/2024 09:{i:02d}:00',
            'duracion': str(180 + i * 15),
            'celda_inicio_llamada': f'CELL_IN_{i}',
            'celda_final_llamada': f'CELL_IN_{i}_END'
        })
    
    df_entrantes = pd.DataFrame(entrantes_data)
    entrantes_path = 'test_claro_entrantes.csv'
    df_entrantes.to_csv(entrantes_path, index=False)
    print(f"   Archivo creado: {entrantes_path} ({len(df_entrantes)} registros)")
    
    return salientes_path, entrantes_path

def test_file_processing():
    """Prueba el procesamiento completo de archivos"""
    
    print("\n" + "="*80)
    print("TEST DE VALIDACIÓN COMPLETA - CARGA CLARO")
    print("="*80)
    
    # Crear archivos de prueba
    salientes_path, entrantes_path = create_test_claro_files()
    
    # Inicializar servicio
    processor = FileProcessorService()
    
    # Procesar archivo de salientes
    print("\n=== PROCESANDO ARCHIVO DE SALIENTES ===")
    
    with open(salientes_path, 'rb') as f:
        file_bytes = f.read()
    
    result_salientes = processor.process_claro_llamadas_salientes(
        file_bytes=file_bytes,
        file_name='test_claro_salientes.csv',
        file_upload_id='TEST_UPLOAD_SALIENTES_001',
        mission_id='TEST_MISSION_L2'
    )
    
    print(f"Resultado: {json.dumps(result_salientes, indent=2)}")
    
    # Procesar archivo de entrantes
    print("\n=== PROCESANDO ARCHIVO DE ENTRANTES ===")
    
    with open(entrantes_path, 'rb') as f:
        file_bytes = f.read()
    
    result_entrantes = processor.process_claro_llamadas_entrantes(
        file_bytes=file_bytes,
        file_name='test_claro_entrantes.csv',
        file_upload_id='TEST_UPLOAD_ENTRANTES_001',
        mission_id='TEST_MISSION_L2'
    )
    
    print(f"Resultado: {json.dumps(result_entrantes, indent=2)}")
    
    # Verificar en base de datos
    print("\n=== VERIFICACIÓN EN BASE DE DATOS ===")
    
    target_numbers = [
        '3224274851', '3208611034', '3104277553', 
        '3102715509', '3143534707', '3214161903'
    ]
    
    try:
        conn = sqlite3.connect('kronos.db')
        cursor = conn.cursor()
        
        for number in target_numbers:
            # Buscar sin prefijo
            cursor.execute("""
                SELECT COUNT(*) as total,
                       COUNT(DISTINCT tipo_llamada) as tipos,
                       MIN(fecha_hora_llamada) as primera,
                       MAX(fecha_hora_llamada) as ultima
                FROM operator_call_data
                WHERE numero_origen = ? OR numero_destino = ? OR numero_objetivo = ?
            """, (number, number, number))
            
            result = cursor.fetchone()
            
            print(f"\nNúmero: {number}")
            print(f"  - Registros totales: {result[0]}")
            print(f"  - Tipos de llamada: {result[1]}")
            
            if result[0] > 0:
                print(f"  - Primera llamada: {result[2]}")
                print(f"  - Última llamada: {result[3]}")
                
                # Detalles específicos
                cursor.execute("""
                    SELECT tipo_llamada, COUNT(*) as cantidad
                    FROM operator_call_data
                    WHERE numero_origen = ? OR numero_destino = ? OR numero_objetivo = ?
                    GROUP BY tipo_llamada
                """, (number, number, number))
                
                detalles = cursor.fetchall()
                for tipo, cantidad in detalles:
                    print(f"    - {tipo}: {cantidad} registros")
            else:
                print("  *** ADVERTENCIA: NÚMERO NO ENCONTRADO EN BD ***")
        
        # Verificar el caso específico de Boris
        print("\n=== CASO ESPECÍFICO 3104277553 -> 3224274851 ===")
        cursor.execute("""
            SELECT * FROM operator_call_data
            WHERE numero_origen = '3104277553' AND numero_destino = '3224274851'
        """)
        
        caso_boris = cursor.fetchall()
        print(f"Registros encontrados: {len(caso_boris)}")
        
        if caso_boris:
            print("ÉXITO: El caso reportado por Boris se cargó correctamente")
        else:
            print("ERROR: El caso de Boris NO se cargó")
        
        conn.close()
        
    except Exception as e:
        print(f"ERROR consultando BD: {e}")
    
    # Limpiar archivos de prueba
    try:
        os.remove(salientes_path)
        os.remove(entrantes_path)
        print("\n=== Archivos de prueba eliminados ===")
    except:
        pass
    
    print("\n" + "="*80)
    print("RESUMEN DE VALIDACIÓN")
    print("="*80)
    
    success_count = 0
    for number in target_numbers:
        # Verificación rápida final
        conn = sqlite3.connect('kronos.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM operator_call_data
            WHERE numero_origen = ? OR numero_destino = ? OR numero_objetivo = ?
        """, (number, number, number))
        count = cursor.fetchone()[0]
        conn.close()
        
        if count > 0:
            success_count += 1
            status = "OK"
        else:
            status = "FALTA"
        
        print(f"  {number}: {status} ({count} registros)")
    
    print(f"\nNúmeros cargados: {success_count}/{len(target_numbers)}")
    
    if success_count == len(target_numbers):
        print("\n*** ÉXITO TOTAL: TODOS LOS NÚMEROS SE CARGARON CORRECTAMENTE ***")
    else:
        print(f"\n*** ADVERTENCIA: {len(target_numbers) - success_count} NÚMEROS NO SE CARGARON ***")

if __name__ == "__main__":
    test_file_processing()