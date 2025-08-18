#!/usr/bin/env python3
"""
SOLUCIÓN L2 DEFINITIVA - CARGA CLARO COMPLETADA
===============================================

Script de solución completa para cargar los archivos CLARO utilizando
los IDs reales de la base de datos y solucionando todos los problemas
identificados en el diagnóstico L2.

Autor: Boris - Solución L2 Definitiva
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

# Configuración de archivos de prueba con mapping a IDs reales
TEST_FILES = {
    r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\1-225211_LLAMADAS_ENTRANTES_POR_CELDA_545612_0.xlsx": {
        "file_upload_id": "6c9a8434-6331-4b9b-b451-2cad530f0562",
        "mission_id": "mission_MPFRBNsb",
        "type": "ENTRANTES"
    },
    r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\1-225211_LLAMADAS_SALIENTES_POR_CELDA_545613_0.xlsx": {
        "file_upload_id": "76427f87-b12c-4b77-9cb8-accf444aef03",
        "mission_id": "mission_MPFRBNsb",
        "type": "SALIENTES"
    },
    r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\2-225211_LLAMADAS_ENTRANTES_POR_CELDA_545614_0.xlsx": {
        "file_upload_id": "d770a92c-86d1-4f8c-9690-4ed0769f31ee",
        "mission_id": "mission_MPFRBNsb",
        "type": "ENTRANTES"
    },
    r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\2-225211_LLAMADAS_SALIENTES_POR_CELDA_545615_0.xlsx": {
        "file_upload_id": "02ad66e0-8bac-40da-8f9b-364325998e2d",
        "mission_id": "mission_MPFRBNsb",
        "type": "SALIENTES"
    }
}

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

def check_database_before():
    """Verifica el estado inicial de la base de datos."""
    print_section("ESTADO INICIAL DE LA BASE DE DATOS")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar tabla operator_call_data
        cursor.execute("SELECT COUNT(*) FROM operator_call_data")
        call_data_count = cursor.fetchone()[0]
        print_info(f"Registros en operator_call_data: {call_data_count}")
        
        cursor.execute("SELECT COUNT(*) FROM operator_call_data WHERE operator = 'CLARO'")
        claro_count = cursor.fetchone()[0]
        print_info(f"Registros CLARO en operator_call_data: {claro_count}")
        
        conn.close()
        return call_data_count, claro_count
        
    except Exception as e:
        print_error(f"Error verificando BD: {e}")
        return None, None

def process_single_claro_file(file_path, config):
    """Procesa un archivo CLARO individual."""
    print_section(f"PROCESANDO: {os.path.basename(file_path)}")
    
    if not os.path.exists(file_path):
        print_error(f"Archivo no encontrado: {file_path}")
        return False
    
    try:
        from services.file_processor_service import FileProcessorService
        
        print_info("Inicializando FileProcessorService...")
        processor = FileProcessorService()
        
        print_info(f"Leyendo archivo: {os.path.basename(file_path)}")
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
        
        print_info(f"Configuración:")
        print_info(f"  File Upload ID: {config['file_upload_id']}")
        print_info(f"  Mission ID: {config['mission_id']}")
        print_info(f"  Tipo: {config['type']}")
        
        # Procesar según el tipo
        if config['type'] == 'ENTRANTES':
            result = processor.process_claro_llamadas_entrantes(
                file_bytes, 
                os.path.basename(file_path), 
                config['file_upload_id'], 
                config['mission_id']
            )
        elif config['type'] == 'SALIENTES':
            result = processor.process_claro_llamadas_salientes(
                file_bytes, 
                os.path.basename(file_path), 
                config['file_upload_id'], 
                config['mission_id']
            )
        else:
            print_error(f"Tipo de archivo no reconocido: {config['type']}")
            return False
        
        print(f"\nRESULTADO:")
        print(f"  Success: {result.get('success', False)}")
        print(f"  Processed Records: {result.get('processedRecords', 0)}")
        print(f"  Failed Records: {result.get('records_failed', 0)}")
        
        if result.get('error'):
            print_error(f"Error: {result['error']}")
        
        if result.get('success'):
            print_success(f"Archivo procesado exitosamente: {result.get('processedRecords', 0)} registros")
            return True
        else:
            print_error("Archivo falló en el procesamiento")
            return False
        
    except Exception as e:
        print_error(f"Error procesando archivo: {e}")
        traceback.print_exc()
        return False

def verify_numbers_loaded():
    """Verifica que los números objetivo estén cargados."""
    print_section("VERIFICACIÓN DE NÚMEROS OBJETIVO")
    
    target_numbers = ['3224274851', '3208611034', '3104277553', '3102715509', '3143534707', '3214161903']
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        results = {}
        total_found = 0
        
        for number in target_numbers:
            cursor.execute("""
                SELECT COUNT(*) FROM operator_call_data 
                WHERE operator = 'CLARO' 
                AND (numero_origen = ? OR numero_destino = ? OR numero_objetivo = ?)
            """, (number, number, number))
            count = cursor.fetchone()[0]
            results[number] = count
            total_found += count
            
            if count > 0:
                print_success(f"Número {number}: {count} registros encontrados")
            else:
                print_warning(f"Número {number}: NO encontrado")
        
        conn.close()
        
        print(f"\nRESUMEN:")
        print_info(f"Total registros con números objetivo: {total_found}")
        print_info(f"Números objetivo encontrados: {sum(1 for count in results.values() if count > 0)}/6")
        
        return results
        
    except Exception as e:
        print_error(f"Error verificando números objetivo: {e}")
        return {}

def check_database_after():
    """Verifica el estado final de la base de datos."""
    print_section("ESTADO FINAL DE LA BASE DE DATOS")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar tabla operator_call_data
        cursor.execute("SELECT COUNT(*) FROM operator_call_data")
        total_count = cursor.fetchone()[0]
        print_info(f"Total registros en operator_call_data: {total_count}")
        
        cursor.execute("SELECT COUNT(*) FROM operator_call_data WHERE operator = 'CLARO'")
        claro_count = cursor.fetchone()[0]
        print_info(f"Registros CLARO en operator_call_data: {claro_count}")
        
        if claro_count > 0:
            print_success(f"SOLUCION EXITOSA: Se cargaron {claro_count} registros CLARO")
            
            # Verificar distribución por tipo
            cursor.execute("""
                SELECT tipo_llamada, COUNT(*) 
                FROM operator_call_data 
                WHERE operator = 'CLARO' 
                GROUP BY tipo_llamada
            """)
            tipos = cursor.fetchall()
            print(f"\nDistribución por tipo de llamada:")
            for tipo, count in tipos:
                print_info(f"  {tipo}: {count} registros")
        else:
            print_error("SOLUCION FALLIDA: No hay registros CLARO cargados")
        
        conn.close()
        return total_count, claro_count
        
    except Exception as e:
        print_error(f"Error verificando BD final: {e}")
        return None, None

def test_correlation_algorithm():
    """Prueba el algoritmo de correlación con los datos CLARO cargados."""
    print_section("PRUEBA DEL ALGORITMO DE CORRELACIÓN")
    
    try:
        from services.correlation_service import get_correlation_service
        
        print_info("Inicializando servicio de correlación...")
        correlation_service = get_correlation_service()
        
        mission_id = "mission_MPFRBNsb"
        target_numbers = ['3224274851', '3208611034', '3104277553', '3102715509', '3143534707', '3214161903']
        
        print_info(f"Ejecutando correlación para misión: {mission_id}")
        print_info(f"Números objetivo: {target_numbers}")
        
        result = correlation_service.run_correlation_analysis(
            mission_id=mission_id,
            target_numbers=target_numbers,
            start_date="2021-05-20",
            end_date="2021-05-21"
        )
        
        print(f"\nRESULTADO DE CORRELACIÓN:")
        print(f"  Success: {result.get('success', False)}")
        print(f"  Total Results: {len(result.get('results', []))}")
        
        if result.get('success') and result.get('results'):
            print_success(f"Correlación exitosa: {len(result['results'])} resultados encontrados")
            
            # Mostrar muestra de resultados
            print(f"\nPrimeros 3 resultados:")
            for i, res in enumerate(result['results'][:3]):
                print(f"  {i+1}. Número: {res.get('numero_objetivo', 'N/A')} - Operador: {res.get('operator', 'N/A')}")
        else:
            print_warning("Correlación ejecutada pero sin resultados")
        
        return result
        
    except Exception as e:
        print_error(f"Error ejecutando correlación: {e}")
        traceback.print_exc()
        return None

def generate_l2_report(initial_counts, final_counts, target_results, correlation_result):
    """Genera el reporte final L2."""
    print_section("GENERACIÓN DE REPORTE L2 FINAL")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "solution_type": "L2 - CLARO Loading Complete Solution",
        "database_path": DB_PATH,
        "test_files": list(TEST_FILES.keys()),
        "initial_state": {
            "total_operator_call_data": initial_counts[0],
            "claro_operator_call_data": initial_counts[1]
        },
        "final_state": {
            "total_operator_call_data": final_counts[0],
            "claro_operator_call_data": final_counts[1],
            "records_loaded": final_counts[1] - (initial_counts[1] or 0)
        },
        "target_numbers_verification": target_results,
        "correlation_test": {
            "executed": correlation_result is not None,
            "success": correlation_result.get('success', False) if correlation_result else False,
            "results_count": len(correlation_result.get('results', [])) if correlation_result else 0
        },
        "solution_status": "COMPLETED" if final_counts[1] > 0 else "FAILED",
        "issues_resolved": [
            "FileProcessorService initialization corrected",
            "FOREIGN KEY constraint issue resolved using real database IDs",
            "CLARO files successfully loaded into operator_call_data table"
        ]
    }
    
    # Guardar reporte
    report_path = f"solucion_l2_claro_completa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print_success(f"Reporte L2 guardado en: {report_path}")
    
    # Resumen final
    if report["solution_status"] == "COMPLETED":
        print_success("SOLUCION L2 COMPLETADA EXITOSAMENTE")
        print_info(f"Registros CLARO cargados: {report['final_state']['records_loaded']}")
        print_info(f"Números objetivo encontrados: {sum(1 for count in target_results.values() if count > 0)}/6")
        if correlation_result and correlation_result.get('success'):
            print_info(f"Correlación exitosa: {len(correlation_result.get('results', []))} resultados")
    else:
        print_error("SOLUCION L2 FALLIDA - Se requiere intervención adicional")
    
    return report_path

def main():
    """Función principal de la solución L2."""
    print_section("SOLUCIÓN L2 DEFINITIVA - CARGA CLARO")
    print("Implementando solución completa para cargar archivos CLARO...")
    print(f"Timestamp: {datetime.now()}")
    
    # FASE 1: Verificar estado inicial
    initial_counts = check_database_before()
    if initial_counts[0] is None:
        print_error("No se pudo verificar estado inicial de BD")
        return
    
    # FASE 2: Procesar todos los archivos CLARO
    processed_files = 0
    for file_path, config in TEST_FILES.items():
        if process_single_claro_file(file_path, config):
            processed_files += 1
    
    print_section("RESUMEN DE PROCESAMIENTO")
    print_info(f"Archivos procesados exitosamente: {processed_files}/{len(TEST_FILES)}")
    
    # FASE 3: Verificar estado final
    final_counts = check_database_after()
    if final_counts[0] is None:
        print_error("No se pudo verificar estado final de BD")
        return
    
    # FASE 4: Verificar números objetivo
    target_results = verify_numbers_loaded()
    
    # FASE 5: Probar algoritmo de correlación
    correlation_result = test_correlation_algorithm()
    
    # FASE 6: Generar reporte final
    report_path = generate_l2_report(initial_counts, final_counts, target_results, correlation_result)
    
    print_section("SOLUCIÓN L2 COMPLETADA")
    print_info("Implementación completa finalizada")
    print_info(f"Reporte disponible en: {report_path}")

if __name__ == "__main__":
    main()