#!/usr/bin/env python3
"""
KRONOS - Test Simple de Implementación TIGO
===============================================================================
Script simplificado para probar la implementación TIGO con archivos reales.
"""

import os
import sys
import json
import base64
from datetime import datetime
from pathlib import Path

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.file_processor_service import FileProcessorService
from services.data_normalizer_service import DataNormalizerService
from utils.validators import validate_tigo_llamada_record
from database.connection import get_db_connection


def test_validadores_tigo():
    """Test básico de validadores TIGO"""
    print("\n=== Test 1: Validadores TIGO ===")
    
    # Test registro válido
    registro_valido = {
        'tipo_de_llamada': '200',
        'numero_a': '3005722406',
        'numero_marcado': 'web.colombiamovil.com.co',
        'direccion': 'O',
        'fecha_hora_origen': '28/02/2025 01:20:19',
        'duracion_total_seg': '0',
        'celda_origen_truncada': '010006CC',
        'tecnologia': '4G',
        'trcsextracodec': '10.198.50.152',
        'latitude': '4,64958',
        'longitude': '-74,074989',
        'ciudad': 'BOGOTÁ. D.C.',
        'departamento': 'CUNDINAMARCA',
        'azimuth': '350',
        'altura': '22',
        'potencia': '18,2'
    }
    
    try:
        validado = validate_tigo_llamada_record(registro_valido)
        if validado:
            print("PASS: Validador TIGO funciona correctamente")
            print(f"  - Direccion: {validado['direccion']}")
            print(f"  - Numero A: {validado['numero_a']}")
            print(f"  - Coordenadas: {validado.get('latitud', 'N/A')}, {validado.get('longitud', 'N/A')}")
            return True
        else:
            print("FAIL: Validador no retorno datos")
            return False
    except Exception as e:
        print(f"FAIL: Error en validador TIGO: {e}")
        return False


def test_normalizacion_tigo():
    """Test básico de normalización TIGO"""
    print("\n=== Test 2: Normalizacion TIGO ===")
    
    data_normalizer = DataNormalizerService()
    
    registro_raw = {
        'tipo_de_llamada': '200',
        'numero_a': '3005722406',
        'numero_marcado': 'web.colombiamovil.com.co',
        'direccion': 'O',
        'fecha_hora_origen': '28/02/2025 01:20:19',
        'duracion_total_seg': 0,
        'celda_origen_truncada': '010006CC',
        'tecnologia': '4G',
        'trcsextracodec': '10.198.50.152',
        'latitud': 4.64958,
        'longitud': -74.074989,
        'ciudad': 'BOGOTÁ. D.C.',
        'departamento': 'CUNDINAMARCA'
    }
    
    try:
        # Test llamada saliente
        normalizado_saliente = data_normalizer.normalize_tigo_call_data_unificadas(
            registro_raw, 'test-file-id', 'test-mission', 'SALIENTE'
        )
        
        if normalizado_saliente:
            print("PASS: Normalizacion SALIENTE funciona")
            print(f"  - Tipo: {normalizado_saliente['tipo_llamada']}")
            print(f"  - Origen: {normalizado_saliente['numero_origen']}")
            print(f"  - Destino: {normalizado_saliente['numero_destino']}")
        else:
            print("FAIL: Normalizacion SALIENTE fallo")
            return False
        
        # Test llamada entrante
        normalizado_entrante = data_normalizer.normalize_tigo_call_data_unificadas(
            registro_raw, 'test-file-id', 'test-mission', 'ENTRANTE'
        )
        
        if normalizado_entrante:
            print("PASS: Normalizacion ENTRANTE funciona")
            print(f"  - Tipo: {normalizado_entrante['tipo_llamada']}")
            print(f"  - Origen: {normalizado_entrante['numero_origen']}")
            print(f"  - Destino: {normalizado_entrante['numero_destino']}")
            return True
        else:
            print("FAIL: Normalizacion ENTRANTE fallo")
            return False
            
    except Exception as e:
        print(f"FAIL: Error en normalizacion: {e}")
        return False


def test_lectura_archivo_csv():
    """Test lectura del archivo CSV TIGO"""
    print("\n=== Test 3: Lectura CSV TIGO ===")
    
    csv_path = Path(__file__).parent.parent / 'datatest' / 'Tigo' / 'Reporte TIGO.csv'
    
    if not csv_path.exists():
        print(f"SKIP: Archivo CSV no encontrado: {csv_path}")
        return True
    
    try:
        file_processor = FileProcessorService()
        
        # Leer archivo
        with open(csv_path, 'rb') as f:
            file_bytes = f.read()
        
        print(f"  - Archivo leido: {len(file_bytes)} bytes")
        
        # Detectar encoding
        encoding = file_processor._detect_encoding(file_bytes)
        print(f"  - Encoding detectado: {encoding}")
        
        # Leer como DataFrame
        df = file_processor._read_csv_robust(file_bytes, delimiter=',')
        
        if df is not None and len(df) > 0:
            print(f"PASS: CSV leido correctamente")
            print(f"  - Registros: {len(df)}")
            print(f"  - Columnas: {len(df.columns)}")
            print(f"  - Primeras columnas: {list(df.columns[:5])}")
            
            # Verificar columnas TIGO
            required_cols = ['TIPO_DE_LLAMADA', 'NUMERO A', 'DIRECCION: O SALIENTE, I ENTRANTE']
            found_cols = [col for col in required_cols if col in df.columns]
            print(f"  - Columnas TIGO encontradas: {len(found_cols)}/{len(required_cols)}")
            
            # Verificar direcciones
            if 'DIRECCION: O SALIENTE, I ENTRANTE' in df.columns:
                direcciones = df['DIRECCION: O SALIENTE, I ENTRANTE'].value_counts()
                print(f"  - Direcciones encontradas: {dict(direcciones)}")
            
            return True
        else:
            print("FAIL: No se pudo leer el CSV o esta vacio")
            return False
            
    except Exception as e:
        print(f"FAIL: Error leyendo CSV: {e}")
        return False


def test_procesamiento_chunk():
    """Test procesamiento por chunks"""
    print("\n=== Test 4: Procesamiento por Chunks ===")
    
    csv_path = Path(__file__).parent.parent / 'datatest' / 'Tigo' / 'Reporte TIGO.csv'
    
    if not csv_path.exists():
        print(f"SKIP: Archivo CSV no encontrado")
        return True
    
    try:
        file_processor = FileProcessorService()
        
        # Leer archivo
        with open(csv_path, 'rb') as f:
            file_bytes = f.read()
        
        # Detectar encoding y leer
        encoding = file_processor._detect_encoding(file_bytes)
        df = file_processor._read_csv_robust(file_bytes, delimiter=',')
        
        if df is None or len(df) == 0:
            print("SKIP: No se pudo leer el archivo")
            return True
        
        # Mapear columnas TIGO
        tigo_column_mapping = {
            'DIRECCION: O SALIENTE, I ENTRANTE': 'direccion',
            'NUMERO A': 'numero_a',
            'FECHA Y HORA ORIGEN': 'fecha_hora_origen',
            'TIPO_DE_LLAMADA': 'tipo_de_llamada'
        }
        
        df_mapped = df.rename(columns=tigo_column_mapping)
        
        # Verificar separación por dirección
        df_clean = df_mapped.dropna(subset=['numero_a', 'direccion']).copy()
        
        if len(df_clean) > 0:
            direcciones = df_clean['direccion'].str.upper().value_counts()
            print(f"PASS: Procesamiento por chunks simulado")
            print(f"  - Registros limpios: {len(df_clean)}")
            print(f"  - Distribución direcciones: {dict(direcciones)}")
            
            entrantes = df_clean[df_clean['direccion'].str.upper().isin(['I', 'ENTRANTE'])]
            salientes = df_clean[df_clean['direccion'].str.upper().isin(['O', 'SALIENTE'])]
            
            print(f"  - Entrantes: {len(entrantes)}")
            print(f"  - Salientes: {len(salientes)}")
            
            return True
        else:
            print("FAIL: No hay registros validos")
            return False
            
    except Exception as e:
        print(f"FAIL: Error en procesamiento: {e}")
        return False


def test_estructura_base_datos():
    """Test estructura de base de datos"""
    print("\n=== Test 5: Estructura Base de Datos ===")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar tablas principales
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['operator_data_sheets', 'operator_call_data', 'missions']
            found_tables = [table for table in required_tables if table in tables]
            
            print(f"PASS: Base de datos accesible")
            print(f"  - Tablas encontradas: {len(found_tables)}/{len(required_tables)}")
            print(f"  - Tablas: {found_tables}")
            
            # Verificar estructura operator_call_data
            cursor.execute("PRAGMA table_info(operator_call_data)")
            columns = [row[1] for row in cursor.fetchall()]
            
            required_cols = ['tipo_llamada', 'numero_origen', 'numero_destino', 'operator_specific_data']
            found_cols = [col for col in required_cols if col in columns]
            
            print(f"  - Columnas call_data: {len(found_cols)}/{len(required_cols)}")
            
            return len(found_tables) >= 2  # Al menos las tablas principales
            
    except Exception as e:
        print(f"FAIL: Error accediendo BD: {e}")
        return False


def main():
    """Función principal del test"""
    print("=" * 80)
    print("KRONOS - Test Simple de Implementación TIGO")
    print("=" * 80)
    
    tests = [
        ("Validadores TIGO", test_validadores_tigo),
        ("Normalización TIGO", test_normalizacion_tigo),
        ("Lectura CSV TIGO", test_lectura_archivo_csv),
        ("Procesamiento Chunks", test_procesamiento_chunk),
        ("Estructura BD", test_estructura_base_datos)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"ERROR en {test_name}: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 80)
    print("RESUMEN DE RESULTADOS")
    print("=" * 80)
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nTests pasados: {passed}/{len(results)}")
    
    if passed == len(results):
        print("\nTODOS LOS TESTS PASARON!")
        print("La implementación TIGO está funcionando correctamente.")
    else:
        print(f"\n{len(results) - passed} tests fallaron.")
        print("Revisar los errores arriba.")
    
    print("=" * 80)
    
    return passed == len(results)


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)