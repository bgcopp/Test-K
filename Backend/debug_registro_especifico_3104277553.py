"""
Simulación específica del procesamiento del registro 3104277553
Para identificar exactamente por qué falló durante el procesamiento ETL
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Agregar el directorio de servicios al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.data_normalizer_service import DataNormalizerService
from services.file_processor_service import FileProcessorService

def simulate_3104277553_processing():
    """
    Simular el procesamiento específico del registro de 3104277553
    según los datos conocidos del análisis de Excel
    """
    
    print("=== SIMULACIÓN PROCESAMIENTO REGISTRO 3104277553 ===")
    print("=" * 60)
    
    # Datos del registro según análisis previo
    registro_excel = {
        'originador': '3104277553',
        'receptor': '3224274851',
        'celda_inicio': '53591',
        'celda_final': '52453',
        'fecha_hora': '2021-05-20 10:09:58',
        'tipo': 'SALIENTE'
    }
    
    print("DATOS DEL REGISTRO EN EXCEL:")
    for key, value in registro_excel.items():
        print(f"  - {key}: {value}")
    
    # Inicializar servicios
    data_normalizer = DataNormalizerService()
    file_processor = FileProcessorService()
    
    # === PASO 1: VALIDACIÓN ===
    print("\n=== PASO 1: VALIDACIÓN ===")
    
    try:
        is_valid, errors = file_processor._validate_claro_call_record(
            registro_excel, 'SALIENTE'
        )
        
        print(f"¿Es válido?: {is_valid}")
        
        if errors:
            print("Errores de validación:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("No hay errores de validación")
            
        if not is_valid:
            print("❌ EL REGISTRO FALLÓ EN LA VALIDACIÓN")
            print("   Esta es probablemente la causa por la que no se cargó a la BD")
            return
            
    except Exception as e:
        print(f"Error en validación: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # === PASO 2: NORMALIZACIÓN ===
    print("\n=== PASO 2: NORMALIZACIÓN ===")
    
    try:
        file_upload_id = "test-file-id"
        mission_id = "test-mission-id"
        
        normalized_data = data_normalizer.normalize_claro_call_data_salientes(
            registro_excel, file_upload_id, mission_id
        )
        
        if normalized_data:
            print("✅ NORMALIZACIÓN EXITOSA")
            print("Datos normalizados:")
            for key, value in normalized_data.items():
                print(f"  - {key}: {value}")
        else:
            print("❌ NORMALIZACIÓN FALLÓ")
            print("   El registro fue rechazado durante la normalización")
            return
            
    except Exception as e:
        print(f"Error en normalización: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # === PASO 3: ANÁLISIS DE CAMPOS ESPECÍFICOS ===
    print("\n=== PASO 3: ANÁLISIS DE CAMPOS ESPECÍFICOS ===")
    
    # Verificar normalización de números
    try:
        numero_origen_normalizado = data_normalizer._normalize_phone_number('3104277553')
        numero_destino_normalizado = data_normalizer._normalize_phone_number('3224274851')
        
        print(f"Número origen normalizado: '{numero_origen_normalizado}'")
        print(f"Número destino normalizado: '{numero_destino_normalizado}'")
        
        if not numero_origen_normalizado:
            print("❌ NÚMERO ORIGEN se normalizó a vacío")
        if not numero_destino_normalizado:
            print("❌ NÚMERO DESTINO se normalizó a vacío")
            
    except Exception as e:
        print(f"Error normalizando números: {e}")
    
    # === PASO 4: SIMULACIÓN CON DIFERENTES FORMATOS ===
    print("\n=== PASO 4: PRUEBA CON FORMATOS ALTERNATIVOS ===")
    
    # Probar diferentes variaciones del registro
    variaciones = [
        {
            'descripcion': 'Formato original',
            'datos': registro_excel
        },
        {
            'descripcion': 'Sin tipo especificado',
            'datos': {**registro_excel, 'tipo': ''}
        },
        {
            'descripcion': 'Fecha en formato diferente',
            'datos': {**registro_excel, 'fecha_hora': '20210520100958'}
        },
        {
            'descripcion': 'Campos con espacios',
            'datos': {
                'originador': ' 3104277553 ',
                'receptor': ' 3224274851 ',
                'celda_inicio': ' 53591 ',
                'celda_final': ' 52453 ',
                'fecha_hora': ' 2021-05-20 10:09:58 ',
                'tipo': ' SALIENTE '
            }
        }
    ]
    
    for variacion in variaciones:
        print(f"\n--- {variacion['descripcion']} ---")
        
        try:
            # Validación
            is_valid, errors = file_processor._validate_claro_call_record(
                variacion['datos'], 'SALIENTE'
            )
            
            print(f"Validación: {'✅ VÁLIDO' if is_valid else '❌ INVÁLIDO'}")
            
            if errors:
                for error in errors:
                    print(f"  Error: {error}")
            
            # Normalización solo si es válido
            if is_valid:
                normalized = data_normalizer.normalize_claro_call_data_salientes(
                    variacion['datos'], file_upload_id, mission_id
                )
                
                print(f"Normalización: {'✅ EXITOSA' if normalized else '❌ FALLÓ'}")
                
                if normalized:
                    print(f"  - Origen: {normalized.get('numero_origen', 'N/A')}")
                    print(f"  - Destino: {normalized.get('numero_destino', 'N/A')}")
                    print(f"  - Celda origen: {normalized.get('celda_origen', 'N/A')}")
            
        except Exception as e:
            print(f"Error procesando variación: {e}")
    
    print("\n" + "=" * 60)
    print("SIMULACIÓN COMPLETADA")

if __name__ == "__main__":
    simulate_3104277553_processing()