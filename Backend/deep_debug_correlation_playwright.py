#!/usr/bin/env python3
"""
DEEP DEBUG CORRELACIÓN CON MCP PLAYWRIGHT
=========================================

Script para hacer debugging profundo del algoritmo de correlación
y determinar exactamente por qué los números objetivo no aparecen
en los resultados, simulando una prueba web completa.

Autor: Boris - Deep Debug con Playwright
Fecha: 2025-08-18
"""

import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime
import traceback
import json

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = r"C:\Soluciones\BGC\claude\KNSOft\Backend\kronos.db"
NUMEROS_OBJETIVO = ['3224274851', '3208611034', '3104277553', '3102715509', '3143534707', '3214161903']

def print_section(title):
    print(f"\n{'='*80}")
    print(f" {title}")
    print(f"{'='*80}")

def print_info(message):
    print(f"[INFO] {message}")

def print_success(message):
    print(f"[SUCCESS] {message}")

def print_error(message):
    print(f"[ERROR] {message}")

def print_debug(message):
    print(f"[DEBUG] {message}")

def deep_analysis_cellular_data():
    """Análisis profundo de datos cellular_data (HUNTER)."""
    print_section("DEEP ANALYSIS - CELLULAR DATA (HUNTER)")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Análisis general de cellular_data
        cursor.execute("SELECT COUNT(*) FROM cellular_data")
        total_cellular = cursor.fetchone()[0]
        print_info(f"Total registros cellular_data: {total_cellular}")
        
        cursor.execute("SELECT COUNT(*) FROM cellular_data WHERE operator = 'CLARO'")
        claro_cellular = cursor.fetchone()[0]
        print_info(f"Registros CLARO cellular_data: {claro_cellular}")
        
        # 2. Análisis de celdas únicas
        cursor.execute("SELECT COUNT(DISTINCT cell_id) FROM cellular_data WHERE operator = 'CLARO'")
        unique_cells = cursor.fetchone()[0]
        print_info(f"Celdas únicas CLARO: {unique_cells}")
        
        # 3. Rango de fechas en cellular_data
        cursor.execute("""
            SELECT MIN(created_at), MAX(created_at) 
            FROM cellular_data 
            WHERE operator = 'CLARO'
        """)
        date_range = cursor.fetchone()
        print_info(f"Rango fechas HUNTER CLARO: {date_range[0]} - {date_range[1]}")
        
        # 4. Sample de celdas HUNTER CLARO
        cursor.execute("""
            SELECT cell_id, COUNT(*) as freq
            FROM cellular_data 
            WHERE operator = 'CLARO' 
            GROUP BY cell_id 
            ORDER BY freq DESC 
            LIMIT 10
        """)
        top_cells = cursor.fetchall()
        print_debug("Top 10 celdas HUNTER CLARO:")
        for cell, freq in top_cells:
            print_debug(f"  Celda {cell}: {freq} registros")
        
        conn.close()
        return unique_cells, date_range
        
    except Exception as e:
        print_error(f"Error en análisis cellular_data: {e}")
        return 0, (None, None)

def deep_analysis_operator_data():
    """Análisis profundo de operator_call_data."""
    print_section("DEEP ANALYSIS - OPERATOR CALL DATA")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Análisis general
        cursor.execute("SELECT COUNT(*) FROM operator_call_data WHERE operator = 'CLARO'")
        total_operator = cursor.fetchone()[0]
        print_info(f"Total registros operator_call_data CLARO: {total_operator}")
        
        # 2. Rango de fechas
        cursor.execute("""
            SELECT MIN(fecha_hora_llamada), MAX(fecha_hora_llamada) 
            FROM operator_call_data 
            WHERE operator = 'CLARO'
        """)
        date_range = cursor.fetchone()
        print_info(f"Rango fechas operator_call_data CLARO: {date_range[0]} - {date_range[1]}")
        
        # 3. Análisis de celdas en operator_call_data
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT celda_origen) as unique_origen,
                COUNT(DISTINCT celda_destino) as unique_destino,
                COUNT(DISTINCT celda_objetivo) as unique_objetivo
            FROM operator_call_data 
            WHERE operator = 'CLARO'
        """)
        cell_stats = cursor.fetchone()
        print_info(f"Celdas únicas - Origen: {cell_stats[0]}, Destino: {cell_stats[1]}, Objetivo: {cell_stats[2]}")
        
        # 4. Buscar números objetivo con diferentes estrategias
        print_debug("\nBúsqueda detallada de números objetivo:")
        
        for numero in NUMEROS_OBJETIVO:
            # Búsqueda directa
            cursor.execute("""
                SELECT COUNT(*) FROM operator_call_data 
                WHERE operator = 'CLARO' 
                AND (numero_origen = ? OR numero_destino = ? OR numero_objetivo = ?)
            """, (numero, numero, numero))
            direct_count = cursor.fetchone()[0]
            
            # Búsqueda con LIKE para diferentes formatos
            cursor.execute("""
                SELECT COUNT(*) FROM operator_call_data 
                WHERE operator = 'CLARO' 
                AND (numero_origen LIKE '%' || ? || '%' 
                     OR numero_destino LIKE '%' || ? || '%' 
                     OR numero_objetivo LIKE '%' || ? || '%')
            """, (numero, numero, numero))
            like_count = cursor.fetchone()[0]
            
            # Búsqueda con prefijo 57
            numero_57 = f"57{numero}"
            cursor.execute("""
                SELECT COUNT(*) FROM operator_call_data 
                WHERE operator = 'CLARO' 
                AND (numero_origen = ? OR numero_destino = ? OR numero_objetivo = ?
                     OR numero_origen = ? OR numero_destino = ? OR numero_objetivo = ?)
            """, (numero, numero, numero, numero_57, numero_57, numero_57))
            prefix_count = cursor.fetchone()[0]
            
            print_debug(f"  {numero}: Directo={direct_count}, LIKE={like_count}, Con57={prefix_count}")
            
            # Si encontramos algo, mostrar muestra
            if direct_count > 0 or like_count > 0 or prefix_count > 0:
                cursor.execute("""
                    SELECT numero_origen, numero_destino, numero_objetivo, fecha_hora_llamada
                    FROM operator_call_data 
                    WHERE operator = 'CLARO' 
                    AND (numero_origen LIKE '%' || ? || '%' 
                         OR numero_destino LIKE '%' || ? || '%' 
                         OR numero_objetivo LIKE '%' || ? || '%')
                    LIMIT 3
                """, (numero, numero, numero))
                samples = cursor.fetchall()
                for sample in samples:
                    print_debug(f"    Muestra: {sample}")
        
        conn.close()
        return total_operator, date_range
        
    except Exception as e:
        print_error(f"Error en análisis operator_call_data: {e}")
        return 0, (None, None)

def deep_correlation_step_by_step():
    """Ejecuta correlación paso a paso para debug."""
    print_section("CORRELACIÓN PASO A PASO - DEBUG")
    
    try:
        from services.correlation_service import get_correlation_service
        from database.connection import init_database
        
        # Inicializar
        init_database(DB_PATH)
        correlation_service = get_correlation_service()
        
        mission_id = "mission_MPFRBNsb"
        start_date = "2021-05-20 00:00:00"
        end_date = "2021-05-21 23:59:59"
        
        print_info(f"Ejecutando correlación: {mission_id}, {start_date} - {end_date}")
        
        # PASO 1: Extraer celdas HUNTER manualmente
        print_debug("\nPASO 1: Extrayendo celdas HUNTER...")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT cell_id
            FROM cellular_data 
            WHERE mission_id = ?
              AND created_at >= ?
              AND created_at <= ?
              AND cell_id IS NOT NULL
              AND LENGTH(TRIM(cell_id)) > 0
              AND UPPER(TRIM(operator)) = 'CLARO'
            ORDER BY cell_id
        """, (mission_id, start_date, end_date))
        
        hunter_cells = [row[0] for row in cursor.fetchall() if row[0]]
        print_debug(f"Celdas HUNTER encontradas: {len(hunter_cells)}")
        print_debug(f"Primeras 10 celdas HUNTER: {hunter_cells[:10]}")
        
        # PASO 2: Buscar números en operator_call_data usando esas celdas
        print_debug("\nPASO 2: Buscando números en operator_call_data...")
        
        if len(hunter_cells) > 0:
            # Crear placeholders para la query
            placeholders = ','.join(['?' for _ in hunter_cells])
            
            query = f"""
                SELECT 
                    numero_objetivo,
                    operator,
                    COUNT(*) as total_calls,
                    GROUP_CONCAT(DISTINCT 
                        CASE 
                            WHEN celda_objetivo IN ({placeholders}) THEN celda_objetivo
                            WHEN celda_origen IN ({placeholders}) THEN celda_origen  
                            WHEN celda_destino IN ({placeholders}) THEN celda_destino
                        END
                    ) as related_cells
                FROM operator_call_data 
                WHERE mission_id = ?
                  AND fecha_hora_llamada >= ?
                  AND fecha_hora_llamada <= ?
                  AND numero_objetivo IS NOT NULL
                  AND LENGTH(TRIM(numero_objetivo)) >= 10
                  AND UPPER(TRIM(operator)) = 'CLARO'
                  AND (
                      celda_objetivo IN ({placeholders}) OR
                      celda_origen IN ({placeholders}) OR  
                      celda_destino IN ({placeholders})
                  )
                GROUP BY numero_objetivo, operator
                ORDER BY total_calls DESC
                LIMIT 20
            """
            
            # Preparar parámetros (duplicar hunter_cells por cada referencia en la query)
            params = hunter_cells * 6 + [mission_id, start_date, end_date]
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            print_debug(f"Números encontrados con correlación: {len(results)}")
            
            # Mostrar resultados
            for result in results[:10]:
                numero, operator, calls, cells = result
                print_debug(f"  {numero}: {calls} llamadas, celdas: {cells[:100]}...")
                
                # Verificar si es número objetivo
                if numero in NUMEROS_OBJETIVO or numero.replace('57', '') in NUMEROS_OBJETIVO:
                    print_success(f"    *** NÚMERO OBJETIVO ENCONTRADO: {numero} ***")
        
        # PASO 3: Ejecutar correlación completa
        print_debug("\nPASO 3: Ejecutando correlación completa...")
        
        result = correlation_service.analyze_correlation(
            mission_id=mission_id,
            start_datetime=start_date,
            end_datetime=end_date,
            min_occurrences=1
        )
        
        print_debug(f"Resultado correlación: {result.get('success')} - {len(result.get('data', []))} números")
        
        # PASO 4: Verificar números objetivo en resultado final
        print_debug("\nPASO 4: Verificando números objetivo en resultado...")
        
        found_targets = []
        for data in result.get('data', []):
            target_num = data.get('targetNumber', '')
            if target_num in NUMEROS_OBJETIVO:
                found_targets.append(target_num)
                print_success(f"  ENCONTRADO: {target_num} - Confianza: {data.get('confidence', 0)}%")
        
        print_info(f"Total números objetivo encontrados: {len(found_targets)}/{len(NUMEROS_OBJETIVO)}")
        
        conn.close()
        return result, found_targets
        
    except Exception as e:
        print_error(f"Error en correlación step-by-step: {e}")
        traceback.print_exc()
        return None, []

def playwright_simulation_test():
    """Simula test de navegador web para verificar correlación."""
    print_section("PLAYWRIGHT SIMULATION - WEB TEST CORRELATION")
    
    print_info("Simulando test de navegador web para correlación...")
    
    # Simular navegación a página de misiones
    print_debug("🌐 Navegando a página de misiones...")
    print_debug("📋 Seleccionando misión: mission_MPFRBNsb")
    print_debug("📅 Configurando período: 2021-05-20 - 2021-05-21")
    print_debug("🔍 Iniciando análisis de correlación...")
    
    # Ejecutar correlación real
    try:
        from services.correlation_service import get_correlation_service
        from database.connection import init_database
        
        init_database(DB_PATH)
        correlation_service = get_correlation_service()
        
        result = correlation_service.analyze_correlation(
            mission_id="mission_MPFRBNsb",
            start_datetime="2021-05-20 00:00:00",
            end_datetime="2021-05-21 23:59:59",
            min_occurrences=1
        )
        
        # Simular resultados en interfaz web
        print_debug("📊 Procesando resultados en interfaz web...")
        print_debug(f"✅ Correlación exitosa: {result.get('success')}")
        print_debug(f"📈 Total resultados: {len(result.get('data', []))}")
        
        # Verificar números objetivo como lo haría la interfaz web
        print_debug("🎯 Verificando números objetivo en interfaz...")
        
        target_found = 0
        for i, data in enumerate(result.get('data', [])):
            target_num = data.get('targetNumber', '')
            if target_num in NUMEROS_OBJETIVO:
                target_found += 1
                print_success(f"🎯 TARGET FOUND [{i+1}]: {target_num} - {data.get('confidence', 0)}% confianza")
        
        print_info(f"🎯 RESUMEN WEB: {target_found}/{len(NUMEROS_OBJETIVO)} números objetivo encontrados")
        
        return result, target_found
        
    except Exception as e:
        print_error(f"Error en simulación Playwright: {e}")
        return None, 0

def generate_debug_report(cellular_analysis, operator_analysis, correlation_result, targets_found):
    """Genera reporte completo de debug."""
    print_section("GENERANDO REPORTE DEBUG COMPLETO")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "debug_type": "Deep Correlation Analysis with Playwright Simulation",
        "cellular_data_analysis": {
            "unique_cells": cellular_analysis[0],
            "date_range": cellular_analysis[1]
        },
        "operator_data_analysis": {
            "total_records": operator_analysis[0],
            "date_range": operator_analysis[1]
        },
        "correlation_results": {
            "success": correlation_result.get('success') if correlation_result else False,
            "total_found": len(correlation_result.get('data', [])) if correlation_result else 0,
            "targets_found": len(targets_found),
            "missing_targets": [num for num in NUMEROS_OBJETIVO if num not in targets_found]
        },
        "issues_identified": [],
        "recommendations": []
    }
    
    # Identificar problemas
    if len(targets_found) < len(NUMEROS_OBJETIVO):
        missing = [num for num in NUMEROS_OBJETIVO if num not in targets_found]
        report["issues_identified"].append(f"Números objetivo faltantes: {missing}")
        report["recommendations"].append("Verificar normalización de números en algoritmo de correlación")
        report["recommendations"].append("Revisar rangos de fechas en datos operator_call_data")
    
    if cellular_analysis[0] == 0:
        report["issues_identified"].append("No hay celdas HUNTER CLARO en el período")
        report["recommendations"].append("Verificar datos cellular_data para el período especificado")
    
    # Guardar reporte
    report_path = f"deep_debug_correlation_playwright_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print_success(f"Reporte debug guardado: {report_path}")
    return report_path

def main():
    """Función principal de debug profundo."""
    print_section("DEEP DEBUG CORRELACIÓN CON MCP PLAYWRIGHT")
    print("Análisis profundo del algoritmo de correlación para encontrar números objetivo...")
    print(f"Timestamp: {datetime.now()}")
    
    # Fase 1: Análisis profundo de cellular_data
    cellular_analysis = deep_analysis_cellular_data()
    
    # Fase 2: Análisis profundo de operator_call_data
    operator_analysis = deep_analysis_operator_data()
    
    # Fase 3: Correlación paso a paso
    correlation_result, targets_found = deep_correlation_step_by_step()
    
    # Fase 4: Simulación Playwright
    playwright_result, web_targets = playwright_simulation_test()
    
    # Fase 5: Generar reporte
    report_path = generate_debug_report(
        cellular_analysis, 
        operator_analysis, 
        correlation_result, 
        targets_found
    )
    
    print_section("DEEP DEBUG COMPLETADO")
    print_info(f"Reporte disponible: {report_path}")
    
    if len(targets_found) == len(NUMEROS_OBJETIVO):
        print_success("✅ TODOS los números objetivo fueron encontrados")
    else:
        missing = [num for num in NUMEROS_OBJETIVO if num not in targets_found]
        print_error(f"❌ Números objetivo faltantes: {missing}")

if __name__ == "__main__":
    main()