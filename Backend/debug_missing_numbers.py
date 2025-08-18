#!/usr/bin/env python3
"""
ANÁLISIS PROFUNDO - Números faltantes en correlación
====================================================
Investigar por qué estos números no aparecen en resultados:
3224274851, 3208611034, 3104277553, 3102715509, 3143534707

Boris solicitó análisis detallado y plan de ajustes.
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, List, Any

# Lista de números a investigar
MISSING_NUMBERS = [
    '3224274851', '3208611034', '3104277553', 
    '3102715509', '3143534707'
]

def get_db_connection():
    """Obtener conexión a la base de datos."""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kronos.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def normalize_phone_number(number: str) -> str:
    """Normalizar número como lo hace el algoritmo de correlación."""
    if not number:
        return ""
    
    # Limpiar el número (solo dígitos)
    clean_number = ''.join(filter(str.isdigit, str(number)))
    
    # Si el número comienza con 57 (Colombia) y tiene más de 10 dígitos,
    # remover el prefijo 57 para comparación
    if clean_number.startswith('57') and len(clean_number) > 10:
        normalized = clean_number[2:]  # Remover los primeros 2 dígitos (57)
        return normalized
    
    return clean_number

def analyze_missing_numbers():
    """Análisis profundo de números faltantes."""
    print("=" * 80)
    print("ANÁLISIS PROFUNDO - NÚMEROS FALTANTES EN CORRELACIÓN")
    print("=" * 80)
    print(f"Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Números a investigar: {MISSING_NUMBERS}")
    print("=" * 80)
    
    analysis_report = {
        'timestamp': datetime.now().isoformat(),
        'missing_numbers': MISSING_NUMBERS,
        'analysis_results': {}
    }
    
    with get_db_connection() as conn:
        # PASO 1: Verificar si los números existen en las tablas
        print("\n1. VERIFICACIÓN DE EXISTENCIA EN TABLAS")
        print("-" * 50)
        
        for number in MISSING_NUMBERS:
            print(f"\nAnalizando número: {number}")
            
            number_analysis = {
                'original_number': number,
                'normalized_number': normalize_phone_number(number),
                'found_in_tables': {},
                'total_occurrences': 0,
                'cell_associations': []
            }
            
            # Buscar en operator_call_data
            call_query = """
                SELECT 
                    id, mission_id, operator, fecha_hora_llamada,
                    numero_origen, numero_destino, numero_objetivo,
                    celda_origen, celda_destino, celda_objetivo, cellid_decimal
                FROM operator_call_data 
                WHERE numero_origen = ? OR numero_destino = ? OR numero_objetivo = ?
                   OR numero_origen = ? OR numero_destino = ? OR numero_objetivo = ?
            """
            
            # Buscar tanto el número original como el normalizado
            normalized = normalize_phone_number(number)
            cursor = conn.execute(call_query, (number, number, number, normalized, normalized, normalized))
            call_results = cursor.fetchall()
            
            number_analysis['found_in_tables']['operator_call_data'] = len(call_results)
            number_analysis['total_occurrences'] += len(call_results)
            
            print(f"  operator_call_data: {len(call_results)} registros")
            
            # Analizar celdas asociadas
            for row in call_results:
                cells = []
                if row['celda_origen']: cells.append(str(row['celda_origen']))
                if row['celda_destino']: cells.append(str(row['celda_destino']))
                if row['celda_objetivo']: cells.append(str(row['celda_objetivo']))
                if row['cellid_decimal']: cells.append(str(row['cellid_decimal']))
                
                number_analysis['cell_associations'].extend(cells)
                
                print(f"    ID: {row['id']}, Misión: {row['mission_id']}, Operador: {row['operator']}")
                print(f"    Fecha: {row['fecha_hora_llamada']}")
                print(f"    Números: orig={row['numero_origen']}, dest={row['numero_destino']}, obj={row['numero_objetivo']}")
                print(f"    Celdas: orig={row['celda_origen']}, dest={row['celda_destino']}, obj={row['celda_objetivo']}, decimal={row['cellid_decimal']}")
            
            # Buscar en operator_cellular_data
            cellular_query = """
                SELECT 
                    id, mission_id, operator, fecha_hora_inicio,
                    numero_telefono, celda_id, lac_tac
                FROM operator_cellular_data 
                WHERE numero_telefono = ? OR numero_telefono = ?
            """
            
            cursor = conn.execute(cellular_query, (number, normalized))
            cellular_results = cursor.fetchall()
            
            number_analysis['found_in_tables']['operator_cellular_data'] = len(cellular_results)
            number_analysis['total_occurrences'] += len(cellular_results)
            
            print(f"  operator_cellular_data: {len(cellular_results)} registros")
            
            for row in cellular_results:
                if row['celda_id']:
                    number_analysis['cell_associations'].append(str(row['celda_id']))
                
                print(f"    ID: {row['id']}, Misión: {row['mission_id']}, Operador: {row['operator']}")
                print(f"    Fecha: {row['fecha_hora_inicio']}")
                print(f"    Número: {row['numero_telefono']}, Celda: {row['celda_id']}")
            
            # Eliminar celdas duplicadas
            number_analysis['unique_cells'] = list(set(number_analysis['cell_associations']))
            
            print(f"  TOTAL REGISTROS: {number_analysis['total_occurrences']}")
            print(f"  CELDAS ASOCIADAS: {len(number_analysis['unique_cells'])} únicas: {number_analysis['unique_cells']}")
            
            analysis_report['analysis_results'][number] = number_analysis
        
        # PASO 2: Verificar si las celdas asociadas existen en HUNTER
        print("\n\n2. VERIFICACIÓN DE CELDAS EN DATOS HUNTER")
        print("-" * 50)
        
        # Obtener todas las celdas HUNTER
        hunter_query = "SELECT DISTINCT cell_id FROM cellular_data WHERE cell_id IS NOT NULL"
        cursor = conn.execute(hunter_query)
        hunter_cells = set(str(row['cell_id']) for row in cursor.fetchall())
        
        print(f"Total celdas HUNTER en base de datos: {len(hunter_cells)}")
        print(f"Primeras 10 celdas HUNTER: {list(hunter_cells)[:10]}")
        
        for number in MISSING_NUMBERS:
            number_data = analysis_report['analysis_results'][number]
            associated_cells = number_data['unique_cells']
            
            print(f"\nNúmero {number}:")
            print(f"  Celdas asociadas al número: {associated_cells}")
            
            matching_cells = []
            for cell in associated_cells:
                if cell in hunter_cells:
                    matching_cells.append(cell)
            
            number_data['hunter_cell_matches'] = matching_cells
            number_data['should_appear_in_correlation'] = len(matching_cells) > 0
            
            print(f"  Coincidencias con HUNTER: {matching_cells}")
            print(f"  ¿DEBERÍA aparecer en correlación?: {'SÍ' if len(matching_cells) > 0 else 'NO'}")
            
            if len(matching_cells) == 0:
                print(f"  ❌ PROBLEMA: Número encontrado pero sin celdas coincidentes con HUNTER")
            else:
                print(f"  ⚠️  PROBLEMA: Número DEBERÍA aparecer pero no está en resultados")
        
        # PASO 3: Verificar misiones activas
        print("\n\n3. VERIFICACIÓN DE MISIONES")
        print("-" * 50)
        
        mission_query = "SELECT id, name, created_at FROM missions ORDER BY created_at DESC LIMIT 5"
        cursor = conn.execute(mission_query)
        missions = cursor.fetchall()
        
        print("Misiones recientes:")
        for mission in missions:
            print(f"  ID: {mission['id']}, Nombre: {mission['name']}, Creada: {mission['created_at']}")
        
        # PASO 4: Verificar rangos de fecha típicos
        print("\n\n4. VERIFICACIÓN DE RANGOS DE FECHA")
        print("-" * 50)
        
        date_query = """
            SELECT 
                MIN(fecha_hora_llamada) as min_call_date,
                MAX(fecha_hora_llamada) as max_call_date
            FROM operator_call_data
        """
        cursor = conn.execute(date_query)
        date_range = cursor.fetchone()
        
        print(f"Rango de fechas en operator_call_data:")
        print(f"  Mínima: {date_range['min_call_date']}")
        print(f"  Máxima: {date_range['max_call_date']}")
        
        cellular_date_query = """
            SELECT 
                MIN(fecha_hora_inicio) as min_cellular_date,
                MAX(fecha_hora_inicio) as max_cellular_date
            FROM operator_cellular_data
        """
        cursor = conn.execute(cellular_date_query)
        cellular_date_range = cursor.fetchone()
        
        print(f"Rango de fechas en operator_cellular_data:")
        print(f"  Mínima: {cellular_date_range['min_cellular_date']}")
        print(f"  Máxima: {cellular_date_range['max_cellular_date']}")
        
        hunter_date_query = """
            SELECT 
                MIN(created_at) as min_hunter_date,
                MAX(created_at) as max_hunter_date
            FROM cellular_data
        """
        cursor = conn.execute(hunter_date_query)
        hunter_date_range = cursor.fetchone()
        
        print(f"Rango de fechas en cellular_data (HUNTER):")
        print(f"  Mínima: {hunter_date_range['min_hunter_date']}")
        print(f"  Máxima: {hunter_date_range['max_hunter_date']}")
    
    # PASO 5: Generar reporte
    print("\n\n5. RESUMEN Y DIAGNÓSTICO")
    print("-" * 50)
    
    problems_found = []
    
    for number, data in analysis_report['analysis_results'].items():
        if data['total_occurrences'] == 0:
            problems_found.append(f"❌ {number}: No existe en ninguna tabla")
        elif not data['should_appear_in_correlation']:
            problems_found.append(f"⚠️  {number}: Existe pero sin celdas coincidentes con HUNTER")
        else:
            problems_found.append(f"🔍 {number}: DEBERÍA aparecer - verificar algoritmo")
    
    print("PROBLEMAS IDENTIFICADOS:")
    for problem in problems_found:
        print(f"  {problem}")
    
    # Guardar reporte
    report_file = f"missing_numbers_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_report, f, indent=2, ensure_ascii=False)
    
    print(f"\nReporte detallado guardado en: {report_file}")
    
    return analysis_report

if __name__ == "__main__":
    analysis_report = analyze_missing_numbers()