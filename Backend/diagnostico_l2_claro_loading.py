#!/usr/bin/env python3
"""
DIAGNÓSTICO L2 - PROBLEMA DE CARGA CLARO
=============================================

Script de diagnóstico exhaustivo para identificar el punto exacto 
de falla en la carga de archivos CLARO a la base de datos.

Autor: Boris - Solución L2 
Fecha: 2025-08-18
"""

import os
import sys
import pandas as pd
import sqlite3
import json
from pathlib import Path
from datetime import datetime
import traceback

# Agregar el directorio padre al path para importar servicios
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuración de archivos de prueba
TEST_FILES = [
    r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\1-225211_LLAMADAS_ENTRANTES_POR_CELDA_545612_0.xlsx",
    r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\1-225211_LLAMADAS_SALIENTES_POR_CELDA_545613_0.xlsx",
    r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\2-225211_LLAMADAS_ENTRANTES_POR_CELDA_545614_0.xlsx",
    r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\2-225211_LLAMADAS_SALIENTES_POR_CELDA_545615_0.xlsx"
]

DB_PATH = r"C:\Soluciones\BGC\claude\KNSOft\Backend\kronos.db"

def print_section(title):
    """Imprime una sección del diagnóstico."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_error(message):
    """Imprime un mensaje de error."""
    print(f"[ERROR] {message}")

def print_warning(message):
    """Imprime un mensaje de advertencia."""
    print(f"[WARNING] {message}")

def print_info(message):
    """Imprime un mensaje informativo."""
    print(f"[INFO] {message}")

def print_success(message):
    """Imprime un mensaje de éxito."""
    print(f"[SUCCESS] {message}")

def analyze_excel_structure(file_path):
    """Analiza la estructura de un archivo Excel CLARO."""
    print_section(f"ANÁLISIS DE ESTRUCTURA: {os.path.basename(file_path)}")
    
    if not os.path.exists(file_path):
        print_error(f"Archivo no encontrado: {file_path}")
        return None
    
    try:
        # Leer archivo Excel
        df = pd.read_excel(file_path)
        
        print_info(f"Archivo leído exitosamente")
        print_info(f"Registros: {len(df)}")
        print_info(f"Columnas: {len(df.columns)}")
        
        print(f"\nColumnas encontradas:")
        for i, col in enumerate(df.columns):
            print(f"  {i+1}. '{col}' (tipo: {df[col].dtype})")
        
        print(f"\nPrimeros 3 registros:")
        for i in range(min(3, len(df))):
            print(f"  Registro {i+1}:")
            for col in df.columns:
                value = df.iloc[i][col]
                print(f"    {col}: {value} ({type(value).__name__})")
        
        # Verificar columnas esperadas por KRONOS
        expected_columns = ['celda_inicio_llamada', 'celda_final_llamada', 'originador', 'receptor', 'fecha_hora', 'duracion', 'tipo']
        
        print(f"\nVERIFICACIÓN DE COLUMNAS ESPERADAS:")
        df_columns_lower = [col.lower().strip() for col in df.columns]
        
        for expected in expected_columns:
            if expected in df_columns_lower:
                print_success(f"Columna '{expected}' encontrada")
            else:
                print_error(f"Columna '{expected}' NO encontrada")
        
        # Verificar tipos de llamada
        if 'tipo' in df_columns_lower:
            tipo_col_name = df.columns[df_columns_lower.index('tipo')]
            tipos_unicos = df[tipo_col_name].value_counts()
            print(f"\nTIPOS DE LLAMADA encontrados:")
            for tipo, count in tipos_unicos.items():
                print(f"  {tipo}: {count} registros")
        
        return df
        
    except Exception as e:
        print_error(f"Error leyendo archivo: {e}")
        traceback.print_exc()
        return None

def check_database_status():
    """Verifica el estado actual de la base de datos."""
    print_section("ESTADO ACTUAL DE LA BASE DE DATOS")
    
    if not os.path.exists(DB_PATH):
        print_error(f"Base de datos no encontrada: {DB_PATH}")
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar tabla operator_call_data
        cursor.execute("SELECT COUNT(*) FROM operator_call_data")
        call_data_count = cursor.fetchone()[0]
        print_info(f"Registros en operator_call_data: {call_data_count}")
        
        if call_data_count == 0:
            print_error("PROBLEMA CRITICO: operator_call_data esta vacia")
        else:
            print_success(f"operator_call_data tiene {call_data_count} registros")
            
            # Verificar operadores
            cursor.execute("SELECT operator, COUNT(*) FROM operator_call_data GROUP BY operator")
            operators = cursor.fetchall()
            print(f"\nOperadores en operator_call_data:")
            for op, count in operators:
                print(f"  {op}: {count} registros")
        
        # Verificar tabla cellular_data
        cursor.execute("SELECT COUNT(*) FROM cellular_data WHERE operator = 'CLARO'")
        cellular_claro_count = cursor.fetchone()[0]
        print_info(f"Registros CLARO en cellular_data: {cellular_claro_count}")
        
        # Verificar tabla de archivos cargados
        cursor.execute("SELECT * FROM operator_data_sheets WHERE operator = 'CLARO' ORDER BY created_at DESC LIMIT 5")
        sheets = cursor.fetchall()
        print(f"\nÚltimos 5 archivos CLARO cargados:")
        for sheet in sheets:
            print(f"  ID: {sheet[0]}, File: {sheet[2]}, Records: {sheet[4]}, Created: {sheet[6]}")
        
        conn.close()
        
    except Exception as e:
        print_error(f"Error accediendo a la base de datos: {e}")
        traceback.print_exc()

def test_file_processor_integration():
    """Prueba la integración con el file processor."""
    print_section("PRUEBA DE INTEGRACIÓN FILE PROCESSOR")
    
    try:
        from services.file_processor_service import FileProcessorService
        from services.data_normalizer_service import DataNormalizerService
        
        print_info("Servicios importados exitosamente")
        
        # Inicializar servicios (CORRECCIÓN L2: FileProcessorService no acepta parámetros)
        processor = FileProcessorService()  # Ya inicializa DataNormalizerService internamente
        
        print_info("Servicios inicializados exitosamente")
        
        # Probar con el primer archivo
        test_file = TEST_FILES[0]
        if not os.path.exists(test_file):
            print_error(f"Archivo de prueba no encontrado: {test_file}")
            return
        
        print_info(f"Probando procesamiento con: {os.path.basename(test_file)}")
        
        # Leer archivo
        with open(test_file, 'rb') as f:
            file_bytes = f.read()
        
        # Simular procesamiento
        file_upload_id = f"test_l2_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        mission_id = "test_mission_l2"
        
        print_info(f"Iniciando procesamiento...")
        print_info(f"File Upload ID: {file_upload_id}")
        print_info(f"Mission ID: {mission_id}")
        
        # Procesar según el tipo de archivo
        if "ENTRANTES" in test_file.upper():
            result = processor.process_claro_llamadas_entrantes(
                file_bytes, os.path.basename(test_file), file_upload_id, mission_id
            )
        elif "SALIENTES" in test_file.upper():
            result = processor.process_claro_llamadas_salientes(
                file_bytes, os.path.basename(test_file), file_upload_id, mission_id
            )
        else:
            result = processor.process_claro_data_por_celda(
                file_bytes, os.path.basename(test_file), file_upload_id, mission_id
            )
        
        print(f"\nRESULTADO DEL PROCESAMIENTO:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get('success'):
            print_success("Procesamiento exitoso")
        else:
            print_error(f"Procesamiento falló: {result.get('error', 'Error desconocido')}")
        
        return result
        
    except ImportError as e:
        print_error(f"Error importando servicios: {e}")
        traceback.print_exc()
    except Exception as e:
        print_error(f"Error en la prueba de integración: {e}")
        traceback.print_exc()

def check_database_after_processing():
    """Verifica el estado de la BD después del procesamiento."""
    print_section("VERIFICACIÓN POST-PROCESAMIENTO")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar nuevos registros
        cursor.execute("SELECT COUNT(*) FROM operator_call_data")
        total_count = cursor.fetchone()[0]
        print_info(f"Total registros en operator_call_data: {total_count}")
        
        cursor.execute("SELECT COUNT(*) FROM operator_call_data WHERE operator = 'CLARO'")
        claro_count = cursor.fetchone()[0]
        print_info(f"Registros CLARO en operator_call_data: {claro_count}")
        
        if claro_count > 0:
            print_success(f"PROBLEMA RESUELTO: Se cargaron {claro_count} registros CLARO")
            
            # Verificar números objetivo
            target_numbers = ['3224274851', '3208611034', '3104277553', '3102715509', '3143534707', '3214161903']
            
            print(f"\nVERIFICACIÓN DE NÚMEROS OBJETIVO:")
            for number in target_numbers:
                cursor.execute("""
                    SELECT COUNT(*) FROM operator_call_data 
                    WHERE operator = 'CLARO' 
                    AND (numero_origen = ? OR numero_destino = ? OR numero_objetivo = ?)
                """, (number, number, number))
                count = cursor.fetchone()[0]
                if count > 0:
                    print_success(f"Número {number}: {count} registros encontrados")
                else:
                    print_warning(f"Número {number}: NO encontrado")
        else:
            print_error("PROBLEMA PERSISTE: No hay registros CLARO cargados")
        
        conn.close()
        
    except Exception as e:
        print_error(f"Error verificando BD post-procesamiento: {e}")
        traceback.print_exc()

def generate_diagnostic_report():
    """Genera un reporte completo del diagnóstico."""
    print_section("GENERACIÓN DE REPORTE DIAGNÓSTICO")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "diagnostic_type": "L2 - CLARO Loading Issue",
        "test_files": TEST_FILES,
        "database_path": DB_PATH,
        "analysis_results": {}
    }
    
    # Analizar cada archivo
    for file_path in TEST_FILES:
        if os.path.exists(file_path):
            file_name = os.path.basename(file_path)
            try:
                df = pd.read_excel(file_path)
                report["analysis_results"][file_name] = {
                    "exists": True,
                    "records": len(df),
                    "columns": list(df.columns),
                    "sample_data": df.head(2).to_dict('records') if len(df) > 0 else []
                }
            except Exception as e:
                report["analysis_results"][file_name] = {
                    "exists": True,
                    "error": str(e)
                }
        else:
            file_name = os.path.basename(file_path)
            report["analysis_results"][file_name] = {
                "exists": False
            }
    
    # Guardar reporte
    report_path = f"diagnostico_l2_claro_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print_success(f"Reporte guardado en: {report_path}")
    return report_path

def main():
    """Función principal del diagnóstico L2."""
    print_section("DIAGNÓSTICO L2 - PROBLEMA CARGA CLARO")
    print("Iniciando análisis exhaustivo del problema de carga de archivos CLARO...")
    print(f"Timestamp: {datetime.now()}")
    
    # FASE 1: Verificar estado inicial de BD
    check_database_status()
    
    # FASE 2: Analizar estructura de archivos
    for file_path in TEST_FILES:
        if os.path.exists(file_path):
            analyze_excel_structure(file_path)
        else:
            print_warning(f"Archivo no encontrado: {file_path}")
    
    # FASE 3: Probar integración con file processor
    processing_result = test_file_processor_integration()
    
    # FASE 4: Verificar BD después del procesamiento
    check_database_after_processing()
    
    # FASE 5: Generar reporte
    report_path = generate_diagnostic_report()
    
    print_section("DIAGNÓSTICO L2 COMPLETADO")
    print_info("Análisis exhaustivo completado")
    print_info(f"Reporte disponible en: {report_path}")
    
    if processing_result and processing_result.get('success'):
        print_success("DIAGNOSTICO: El problema parece estar resuelto")
    else:
        print_error("DIAGNOSTICO: El problema persiste - se requiere intervencion adicional")

if __name__ == "__main__":
    main()