"""
Debug simple del registro 3104277553 sin caracteres especiales
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Agregar el directorio de servicios al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.data_normalizer_service import DataNormalizerService
from services.file_processor_service import FileProcessorService

def debug_3104277553_simple():
    """Debug simple del procesamiento"""
    
    print("=== DEBUG REGISTRO 3104277553 ===")
    
    # Datos del registro
    registro = {
        'originador': '3104277553',
        'receptor': '3224274851',
        'celda_inicio': '53591',
        'celda_final': '52453',
        'fecha_hora': '2021-05-20 10:09:58',
        'tipo': 'SALIENTE'
    }
    
    print("Datos del registro:")
    for key, value in registro.items():
        print(f"  {key}: {value}")
    
    # Servicios
    data_normalizer = DataNormalizerService()
    file_processor = FileProcessorService()
    
    # VALIDACIÓN
    print("\n=== VALIDACION ===")
    is_valid, errors = file_processor._validate_claro_call_record(
        registro, 'SALIENTE'
    )
    
    print(f"Es valido: {is_valid}")
    if errors:
        print("Errores:")
        for error in errors:
            print(f"  - {error}")
    
    # NORMALIZACIÓN
    print("\n=== NORMALIZACION ===")
    try:
        normalized_data = data_normalizer.normalize_claro_call_data_salientes(
            registro, "test-file-id", "test-mission-id"
        )
        
        if normalized_data:
            print("NORMALIZACION EXITOSA")
            print("Datos normalizados:")
            for key, value in normalized_data.items():
                print(f"  {key}: {value}")
        else:
            print("NORMALIZACION FALLO - retorno None")
            
    except Exception as e:
        print(f"Error en normalizacion: {e}")
        import traceback
        traceback.print_exc()
    
    # ANÁLISIS DE NÚMEROS
    print("\n=== ANALISIS NUMEROS ===")
    try:
        origen_norm = data_normalizer._normalize_phone_number('3104277553')
        destino_norm = data_normalizer._normalize_phone_number('3224274851')
        
        print(f"3104277553 normalizado: '{origen_norm}'")
        print(f"3224274851 normalizado: '{destino_norm}'")
        
        print(f"Origen vacio: {not origen_norm}")
        print(f"Destino vacio: {not destino_norm}")
        
    except Exception as e:
        print(f"Error normalizando numeros: {e}")

if __name__ == "__main__":
    debug_3104277553_simple()