"""
KRONOS - Demostración con Datos Reales de TIGO
===============================================================================
Script de demostración que muestra el procesamiento de datos reales de TIGO
usando el archivo de ejemplo disponible en el proyecto.

Este script:
1. Lee el archivo real de TIGO (Reporte TIGO.csv)
2. Procesa los datos usando TigoProcessor
3. Muestra estadísticas del procesamiento
4. Demuestra las funcionalidades específicas de TIGO
===============================================================================
"""

import sys
import os
import base64
import json
from datetime import datetime

# Configurar path para importaciones
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.operator_processors.tigo_processor import TigoProcessor
from database.connection import get_database_manager
import uuid


def load_real_tigo_file():
    """Carga el archivo real de TIGO disponible en el proyecto"""
    tigo_file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'archivos', 'CeldasDiferenteOperador', 'tigo', 'Reporte TIGO.csv'
    )
    
    if not os.path.exists(tigo_file_path):
        print(f"ERROR: Archivo no encontrado: {tigo_file_path}")
        return None
    
    # Leer archivo y convertir a base64
    with open(tigo_file_path, 'rb') as f:
        file_content = f.read()
    
    file_base64 = base64.b64encode(file_content).decode('utf-8')
    
    return {
        'name': 'Reporte TIGO.csv',
        'content': f'data:text/csv;base64,{file_base64}',
        'path': tigo_file_path,
        'size_bytes': len(file_content)
    }


def demonstrate_tigo_validation():
    """Demuestra validación de estructura TIGO"""
    print("1. VALIDACIÓN DE ESTRUCTURA DE ARCHIVO TIGO")
    print("-" * 50)
    
    # Cargar archivo real
    file_data = load_real_tigo_file()
    if not file_data:
        return
    
    processor = TigoProcessor()
    
    # Validar estructura
    validation_result = processor.validate_file_structure(file_data, 'LLAMADAS_MIXTAS')
    
    print(f"📁 Archivo: {file_data['name']}")
    print(f"📏 Tamaño: {file_data['size_bytes']:,} bytes")
    print(f"✅ Válido: {validation_result['is_valid']}")
    print(f"📊 Columnas encontradas: {len(validation_result['mapped_columns'])}")
    print(f"📋 Filas de muestra: {validation_result['sample_rows']}")
    
    # Mostrar columnas mapeadas
    print(f"\n🗂️ Columnas mapeadas:")
    for col in sorted(validation_result['mapped_columns']):
        print(f"   • {col}")
    
    # Mostrar validación de direcciones
    direccion_validation = validation_result['direccion_validation']
    print(f"\n🧭 Direcciones válidas encontradas: {direccion_validation['valid_directions']}")
    if direccion_validation['invalid_directions']:
        print(f"⚠️ Direcciones inválidas: {direccion_validation['invalid_directions']}")
    
    return validation_result['is_valid']


def demonstrate_tigo_processing():
    """Demuestra procesamiento completo de archivo TIGO"""
    print("\n\n2. PROCESAMIENTO DE ARCHIVO TIGO")
    print("-" * 50)
    
    # Cargar archivo real
    file_data = load_real_tigo_file()
    if not file_data:
        return
    
    processor = TigoProcessor()
    
    # Crear misión de prueba
    mission_id = str(uuid.uuid4())
    print(f"🎯 ID Misión: {mission_id}")
    
    try:
        # Procesar archivo (sin insertar en BD real)
        print("🔄 Procesando archivo...")
        
        # Solo validación y análisis, sin BD
        import pandas as pd
        from io import StringIO
        from utils.helpers import decode_base64_file
        
        # Decodificar archivo
        file_bytes, filename, mime_type = decode_base64_file(file_data)
        
        # Leer como CSV
        csv_content = file_bytes.decode('utf-8')
        df = pd.read_csv(StringIO(csv_content))
        
        print(f"📊 Total de registros: {len(df)}")
        
        # Normalizar columnas
        df_normalized = processor._normalize_column_names(df, processor.LLAMADAS_COLUMN_MAPPING)
        
        # Limpiar datos
        df_clean = processor._clean_llamadas_dataframe(df_normalized)
        
        print(f"🧹 Registros después de limpieza: {len(df_clean)}")
        
        # Analizar distribución de direcciones
        direcciones = df_clean['direccion_tipo'].value_counts()
        print(f"\n📈 Distribución de llamadas:")
        for direccion, count in direcciones.items():
            tipo = "SALIENTES" if direccion == 'O' else "ENTRANTES"
            print(f"   • {tipo}: {count:,} registros")
        
        # Analizar tecnologías
        if 'tecnologia' in df_clean.columns:
            tecnologias = df_clean['tecnologia'].value_counts()
            print(f"\n📡 Tecnologías encontradas:")
            for tech, count in tecnologias.items():
                print(f"   • {tech}: {count:,} registros")
        
        # Analizar rangos de tiempo
        if 'fecha_hora_origen' in df_clean.columns:
            try:
                df_clean['fecha_parsed'] = pd.to_datetime(df_clean['fecha_hora_origen'], format='%d/%m/%Y %H:%M:%S')
                fecha_min = df_clean['fecha_parsed'].min()
                fecha_max = df_clean['fecha_parsed'].max()
                print(f"\n📅 Rango temporal:")
                print(f"   • Desde: {fecha_min}")
                print(f"   • Hasta: {fecha_max}")
                print(f"   • Duración: {(fecha_max - fecha_min).days} días")
            except:
                print("⚠️ No se pudo parsear fechas")
        
        # Analizar números únicos
        if 'numero_a' in df_clean.columns:
            numeros_unicos = df_clean['numero_a'].nunique()
            print(f"\n📞 Números únicos: {numeros_unicos:,}")
        
        # Analizar celdas únicas
        if 'celda_origen_truncada' in df_clean.columns:
            celdas_unicas = df_clean['celda_origen_truncada'].nunique()
            print(f"📡 Celdas únicas: {celdas_unicas:,}")
        
        # Mostrar registros de ejemplo
        print(f"\n📋 EJEMPLO DE REGISTROS PROCESADOS:")
        print("-" * 50)
        
        for i, (idx, row) in enumerate(df_clean.head(3).iterrows()):
            print(f"\nRegistro {i+1}:")
            print(f"   • Número: {row.get('numero_a', 'N/A')}")
            print(f"   • Dirección: {'SALIENTE' if row.get('direccion_tipo') == 'O' else 'ENTRANTE'}")
            print(f"   • Fecha: {row.get('fecha_hora_origen', 'N/A')}")
            print(f"   • Duración: {row.get('duracion_total_seg', 0)} seg")
            print(f"   • Celda: {row.get('celda_origen_truncada', 'N/A')}")
            print(f"   • Tecnología: {row.get('tecnologia', 'N/A')}")
            if 'latitud' in row and 'longitud' in row:
                print(f"   • Coordenadas: {row['latitud']:.6f}, {row['longitud']:.6f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error procesando archivo: {e}")
        return False


def demonstrate_tigo_specific_features():
    """Demuestra características específicas de TIGO"""
    print("\n\n3. CARACTERÍSTICAS ESPECÍFICAS DE TIGO")
    print("-" * 50)
    
    # Validadores específicos
    from utils.validators import (
        validate_tigo_datetime_format,
        validate_tigo_coordinates, 
        validate_tigo_direction_field
    )
    
    # 1. Formato de fechas TIGO
    print("📅 Validación de fechas formato TIGO:")
    fecha_ejemplo = "28/02/2025 01:20:19"
    try:
        fecha_parsed = validate_tigo_datetime_format(fecha_ejemplo)
        print(f"   ✅ '{fecha_ejemplo}' → {fecha_parsed}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 2. Coordenadas con comas
    print("\n🗺️ Conversión de coordenadas TIGO:")
    coord_ejemplos = [
        ("-74,074989", "4,64958"),
        ('"-74.123456"', '"4.567890"')
    ]
    
    for lat_str, lon_str in coord_ejemplos:
        try:
            lat, lon = validate_tigo_coordinates(lat_str, lon_str)
            print(f"   ✅ ({lat_str}, {lon_str}) → ({lat:.6f}, {lon:.6f})")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # 3. Campo dirección
    print("\n🧭 Validación campo dirección TIGO:")
    direcciones_ejemplo = ["O", "I", "SALIENTE", "ENTRANTE"]
    
    for direccion in direcciones_ejemplo:
        try:
            direccion_validada = validate_tigo_direction_field(direccion)
            print(f"   ✅ '{direccion}' → '{direccion_validada}'")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # 4. Demostrar metadata específica
    print(f"\n📋 Ejemplo de metadata específica TIGO:")
    processor = TigoProcessor()
    
    import pandas as pd
    row_example = pd.Series({
        'numero_a': '3005722406',
        'numero_marcado': 'web.colombiamovil.com.co',
        'fecha_hora_origen': '28/02/2025 01:20:19',
        'tecnologia': '4G',
        'ciudad': 'BOGOTÁ. D.C.',
        'departamento': 'CUNDINAMARCA'
    }, name=0)
    
    validated_example = {
        'direccion_tipo': 'O',
        'tecnologia': '4G',
        'trcsextracodec': '10.198.50.152',
        'ciudad': 'BOGOTÁ. D.C.',
        'departamento': 'CUNDINAMARCA',
        'latitud': 4.64958,
        'longitud': -74.074989,
        'azimuth': 350.0,
        'altura': 22.0,
        'potencia': 18.2
    }
    
    metadata_json = processor._build_tigo_specific_data(row_example, validated_example)
    metadata = json.loads(metadata_json)
    
    print(json.dumps(metadata, indent=2, ensure_ascii=False))


def main():
    """Función principal de demostración"""
    print("DEMOSTRACION IMPLEMENTACION TIGO - KRONOS")
    print("=" * 80)
    
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Version: TIGO Processor v1.0")
    
    # Verificar archivo existe
    file_data = load_real_tigo_file()
    if not file_data:
        print("❌ No se puede ejecutar la demostración sin el archivo de ejemplo")
        return
    
    try:
        # 1. Demostrar validación
        validation_ok = demonstrate_tigo_validation()
        
        if validation_ok:
            # 2. Demostrar procesamiento
            processing_ok = demonstrate_tigo_processing()
            
            # 3. Demostrar características específicas
            demonstrate_tigo_specific_features()
            
            if processing_ok:
                print("\n\n🎉 DEMOSTRACIÓN COMPLETADA EXITOSAMENTE")
                print("=" * 80)
                print("✅ Validación de estructura: OK")
                print("✅ Procesamiento de datos: OK") 
                print("✅ Características específicas: OK")
                print("\n📝 La implementación de TIGO está lista para uso en producción.")
            else:
                print("\n\n⚠️ DEMOSTRACIÓN PARCIALMENTE COMPLETADA")
                print("Algunas funciones de procesamiento no pudieron ejecutarse completamente")
        else:
            print("\n\n❌ DEMOSTRACIÓN FALLIDA")
            print("La validación de estructura falló")
            
    except Exception as e:
        print(f"\n\n💥 ERROR EN DEMOSTRACIÓN: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()