"""
KRONOS - Test con Archivos Reales de MOVISTAR
===============================================================================
Prueba del procesador MOVISTAR con los archivos reales disponibles:
- jgd202410754_00007301_datos_ MOVISTAR.csv
- jgd202410754_07F08305_vozm_saliente_ MOVISTAR.csv

Verifica:
1. Lectura correcta de archivos reales
2. Validación de estructura
3. Procesamiento de registros reales
4. Mapeo a tablas unificadas
===============================================================================
"""

import sys
import pandas as pd
from pathlib import Path

# Configurar path para imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from services.operator_processors.movistar_processor import MovistarProcessor


def test_movistar_real_files():
    """Prueba archivos reales de MOVISTAR"""
    print("="*80)
    print("KRONOS - PRUEBA CON ARCHIVOS REALES MOVISTAR")
    print("="*80)
    
    processor = MovistarProcessor()
    
    # Rutas de archivos reales
    files_dir = Path("../archivos/CeldasDiferenteOperador/mov")
    datos_file = files_dir / "jgd202410754_00007301_datos_ MOVISTAR.csv"
    llamadas_file = files_dir / "jgd202410754_07F08305_vozm_saliente_ MOVISTAR.csv"
    
    print(f"Directorio de archivos: {files_dir.absolute()}")
    print(f"Archivo de datos: {datos_file.name}")
    print(f"Archivo de llamadas: {llamadas_file.name}")
    print()
    
    # Probar archivo de datos
    if datos_file.exists():
        print("ANALIZANDO ARCHIVO DE DATOS MOVISTAR:")
        print("-" * 50)
        
        try:
            # Leer archivo con encoding detection
            try:
                df_datos = pd.read_csv(datos_file, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    df_datos = pd.read_csv(datos_file, encoding='latin-1')
                except UnicodeDecodeError:
                    df_datos = pd.read_csv(datos_file, encoding='cp1252')
            print(f"[OK] Archivo leido exitosamente")
            print(f"Filas: {len(df_datos)}")
            print(f"Columnas: {len(df_datos.columns)}")
            print(f"Columnas: {list(df_datos.columns)}")
            
            # Mostrar muestra de datos
            print(f"\nMuestra de datos (primeras 3 filas):")
            print(df_datos.head(3).to_string())
            
            # Probar validación de estructura
            print(f"\nValidando estructura de datos...")
            validation_result = processor._validate_datos_structure(df_datos)
            
            if validation_result['is_valid']:
                print("[OK] Estructura de datos VALIDA")
                print(f"Columnas mapeadas: {validation_result['mapped_columns']}")
            else:
                print("[ERROR] Estructura de datos INVALIDA")
                print(f"Columnas faltantes: {validation_result['missing_columns']}")
            
            # Probar limpieza de datos
            print(f"\nLimpiando datos...")
            df_clean = processor._clean_datos_dataframe(df_datos)
            print(f"Filas despues de limpieza: {len(df_clean)}")
            
            # Probar validación de registros individuales
            print(f"\nValidando registros individuales (muestra de 3)...")
            success_count = 0
            for i, (index, row) in enumerate(df_clean.head(3).iterrows()):
                try:
                    from utils.validators import validate_movistar_datos_record
                    
                    row_dict = {
                        'numero_que_navega': row.get('numero_que_navega'),
                        'ruta_entrante': row.get('ruta_entrante'),
                        'celda': row.get('celda'),
                        'trafico_de_subida': row.get('trafico_de_subida'),
                        'trafico_de_bajada': row.get('trafico_de_bajada'),
                        'fecha_hora_inicio_sesion': row.get('fecha_hora_inicio_sesion'),
                        'duracion': row.get('duracion'),
                        'tipo_tecnologia': row.get('tipo_tecnologia'),
                        'fecha_hora_fin_sesion': row.get('fecha_hora_fin_sesion'),
                        'departamento': row.get('departamento'),
                        'localidad': row.get('localidad'),
                        'region': row.get('region'),
                        'latitud_n': row.get('latitud_n'),
                        'longitud_w': row.get('longitud_w'),
                        'proveedor': row.get('proveedor'),
                        'tecnologia': row.get('tecnologia'),
                        'descripcion': row.get('descripcion'),
                        'direccion': row.get('direccion'),
                        'celda_': row.get('celda_')
                    }
                    
                    validated = validate_movistar_datos_record(row_dict)
                    print(f"[OK] Registro {i+1}: {validated['numero_que_navega']} - {validated['tecnologia']}")
                    success_count += 1
                    
                except Exception as e:
                    print(f"[ERROR] Registro {i+1}: {str(e)}")
            
            print(f"Registros validados exitosamente: {success_count}/3")
            
        except Exception as e:
            print(f"[ERROR] Error procesando archivo de datos: {e}")
    else:
        print(f"[ERROR] Archivo de datos no encontrado: {datos_file}")
    
    print("\n" + "="*80)
    
    # Probar archivo de llamadas
    if llamadas_file.exists():
        print("ANALIZANDO ARCHIVO DE LLAMADAS MOVISTAR:")
        print("-" * 50)
        
        try:
            # Leer archivo
            df_llamadas = pd.read_csv(llamadas_file)
            print(f"[OK] Archivo leido exitosamente")
            print(f"Filas: {len(df_llamadas)}")
            print(f"Columnas: {len(df_llamadas.columns)}")
            print(f"Columnas: {list(df_llamadas.columns)}")
            
            # Mostrar muestra de datos
            print(f"\nMuestra de llamadas (primeras 3 filas):")
            print(df_llamadas.head(3).to_string())
            
            # Probar validación de estructura
            print(f"\nValidando estructura de llamadas...")
            validation_result = processor._validate_llamadas_structure(df_llamadas)
            
            if validation_result['is_valid']:
                print("[OK] Estructura de llamadas VALIDA")
                print(f"Columnas mapeadas: {validation_result['mapped_columns']}")
            else:
                print("[ERROR] Estructura de llamadas INVALIDA")
                print(f"Columnas faltantes: {validation_result['missing_columns']}")
            
            # Probar limpieza de datos
            print(f"\nLimpiando datos de llamadas...")
            df_clean = processor._clean_llamadas_dataframe(df_llamadas)
            print(f"Filas despues de limpieza: {len(df_clean)}")
            
            # Probar validación de registros individuales
            print(f"\nValidando registros de llamadas individuales (muestra de 3)...")
            success_count = 0
            for i, (index, row) in enumerate(df_clean.head(3).iterrows()):
                try:
                    from utils.validators import validate_movistar_llamadas_record
                    
                    row_dict = {
                        'numero_que_contesta': row.get('numero_que_contesta'),
                        'serial_destino': row.get('serial_destino'),
                        'numero_que_marca': row.get('numero_que_marca'),
                        'serial_origen': row.get('serial_origen'),
                        'duracion': row.get('duracion'),
                        'ruta_entrante': row.get('ruta_entrante'),
                        'numero_marcado': row.get('numero_marcado'),
                        'ruta_saliente': row.get('ruta_saliente'),
                        'transferencia': row.get('transferencia'),
                        'fecha_hora_inicio_llamada': row.get('fecha_hora_inicio_llamada'),
                        'fecha_hora_fin_llamada': row.get('fecha_hora_fin_llamada'),
                        'switch': row.get('switch'),
                        'celda_origen': row.get('celda_origen'),
                        'celda_destino': row.get('celda_destino'),
                        'departamento': row.get('departamento'),
                        'localidad': row.get('localidad'),
                        'region': row.get('region'),
                        'latitud_n': row.get('latitud_n'),
                        'longitud_w': row.get('longitud_w'),
                        'proveedor': row.get('proveedor'),
                        'tecnologia': row.get('tecnologia'),
                        'descripcion': row.get('descripcion'),
                        'direccion': row.get('direccion'),
                        'celda': row.get('celda'),
                        'azimut': row.get('azimut')
                    }
                    
                    validated = validate_movistar_llamadas_record(row_dict)
                    print(f"[OK] Llamada {i+1}: {validated['numero_que_marca']} -> {validated['numero_que_contesta']} ({validated['duracion']}s)")
                    success_count += 1
                    
                except Exception as e:
                    print(f"[ERROR] Llamada {i+1}: {str(e)}")
            
            print(f"Llamadas validadas exitosamente: {success_count}/3")
            
        except Exception as e:
            print(f"[ERROR] Error procesando archivo de llamadas: {e}")
    else:
        print(f"[ERROR] Archivo de llamadas no encontrado: {llamadas_file}")
    
    print("\n" + "="*80)
    print("PRUEBA CON ARCHIVOS REALES MOVISTAR COMPLETADA")
    print("="*80)


if __name__ == '__main__':
    test_movistar_real_files()