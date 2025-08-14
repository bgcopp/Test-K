"""
KRONOS - Demostracion Simple de TIGO
===============================================================================
Script simplificado para demostrar el procesamiento de TIGO
===============================================================================
"""

import sys
import os
import base64
import json
from datetime import datetime

# Configurar path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.operator_processors.tigo_processor import TigoProcessor


def load_tigo_file():
    """Carga el archivo de TIGO"""
    tigo_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'archivos', 'CeldasDiferenteOperador', 'tigo', 'Reporte TIGO.csv'
    )
    
    if not os.path.exists(tigo_path):
        print(f"ERROR: Archivo no encontrado: {tigo_path}")
        return None
    
    with open(tigo_path, 'rb') as f:
        content = f.read()
    
    return {
        'name': 'Reporte TIGO.csv',
        'content': f'data:text/csv;base64,{base64.b64encode(content).decode()}',
        'size': len(content)
    }


def demo_validation():
    """Demuestra validacion"""
    print("1. VALIDACION DE ESTRUCTURA")
    print("-" * 40)
    
    file_data = load_tigo_file()
    if not file_data:
        return False
    
    processor = TigoProcessor()
    result = processor.validate_file_structure(file_data, 'LLAMADAS_MIXTAS')
    
    print(f"Archivo: {file_data['name']}")
    print(f"Tamaño: {file_data['size']:,} bytes")
    print(f"Valido: {result['is_valid']}")
    print(f"Columnas: {len(result['mapped_columns'])}")
    
    return result['is_valid']


def demo_processing():
    """Demuestra procesamiento"""
    print("\n2. PROCESAMIENTO DE DATOS")
    print("-" * 40)
    
    file_data = load_tigo_file()
    if not file_data:
        return False
    
    try:
        import pandas as pd
        from io import StringIO
        from utils.helpers import decode_base64_file
        
        processor = TigoProcessor()
        
        # Decodificar archivo
        file_bytes, filename, mime_type = decode_base64_file(file_data)
        csv_content = file_bytes.decode('utf-8')
        df = pd.read_csv(StringIO(csv_content))
        
        print(f"Registros totales: {len(df)}")
        
        # Normalizar y limpiar
        df_norm = processor._normalize_column_names(df, processor.LLAMADAS_COLUMN_MAPPING)
        df_clean = processor._clean_llamadas_dataframe(df_norm)
        
        print(f"Registros limpios: {len(df_clean)}")
        
        # Analizar direcciones
        if 'direccion_tipo' in df_clean.columns:
            dirs = df_clean['direccion_tipo'].value_counts()
            print("Distribucion de llamadas:")
            for dir_val, count in dirs.items():
                tipo = "SALIENTES" if dir_val == 'O' else "ENTRANTES"
                print(f"  {tipo}: {count:,}")
        
        # Mostrar ejemplo
        print("\nEjemplo de registro:")
        if len(df_clean) > 0:
            row = df_clean.iloc[0]
            print(f"  Numero: {row.get('numero_a', 'N/A')}")
            print(f"  Direccion: {row.get('direccion_tipo', 'N/A')}")
            print(f"  Fecha: {row.get('fecha_hora_origen', 'N/A')}")
            print(f"  Celda: {row.get('celda_origen_truncada', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def demo_features():
    """Demuestra caracteristicas especificas"""
    print("\n3. CARACTERISTICAS ESPECIFICAS TIGO")
    print("-" * 40)
    
    # Validadores
    from utils.validators import (
        validate_tigo_datetime_format,
        validate_tigo_coordinates,
        validate_tigo_direction_field
    )
    
    # 1. Fechas
    print("Fechas TIGO:")
    try:
        fecha = validate_tigo_datetime_format("28/02/2025 01:20:19")
        print(f"  OK: 28/02/2025 01:20:19 -> {fecha}")
    except Exception as e:
        print(f"  ERROR: {e}")
    
    # 2. Coordenadas
    print("Coordenadas TIGO:")
    try:
        lat, lon = validate_tigo_coordinates("-74,074989", "4,64958")
        print(f"  OK: (-74,074989, 4,64958) -> ({lat:.6f}, {lon:.6f})")
    except Exception as e:
        print(f"  ERROR: {e}")
    
    # 3. Direccion
    print("Campo direccion:")
    for dir_val in ['O', 'I']:
        try:
            result = validate_tigo_direction_field(dir_val)
            print(f"  OK: '{dir_val}' -> '{result}'")
        except Exception as e:
            print(f"  ERROR: {e}")


def main():
    """Funcion principal"""
    print("DEMOSTRACION TIGO - KRONOS")
    print("=" * 50)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Version: TIGO Processor v1.0")
    print()
    
    try:
        # 1. Validacion
        validation_ok = demo_validation()
        
        if validation_ok:
            # 2. Procesamiento
            processing_ok = demo_processing()
            
            # 3. Caracteristicas
            demo_features()
            
            if processing_ok:
                print("\n" + "=" * 50)
                print("DEMOSTRACION COMPLETADA EXITOSAMENTE")
                print("La implementacion de TIGO esta lista!")
            else:
                print("\nDEMOSTRACION PARCIALMENTE COMPLETADA")
        else:
            print("\nDEMOSTRACION FALLIDA - Validacion fallo")
            
    except Exception as e:
        print(f"\nERROR EN DEMOSTRACION: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()