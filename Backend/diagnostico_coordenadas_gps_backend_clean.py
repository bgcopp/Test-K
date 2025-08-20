#!/usr/bin/env python3
"""
DIAGNOSTICO CRITICO: Investigacion Backend - Coordenadas GPS Missing en KRONOS
===============================================================================

PROBLEMA REPORTADO POR BORIS:
- Las coordenadas GPS de HUNTER no aparecen en el frontend de KRONOS
- TableCorrelationModal.tsx muestra "N/A" en lugar de coordenadas validas
- Identificado por agente de datos: cell_ids HUNTER vs CLARO no correlacionan

OBJETIVO:
Analizar exactamente que esta retornando get_call_interactions() y por que
las coordenadas GPS estan llegando como NULL/undefined al frontend.

FECHA: 2025-08-20
INVESTIGADOR: Backend Engineer - Claude Code
===============================================================================
"""

import sqlite3
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List

# Configurar path para imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def get_db_connection():
    """Obtiene conexion directa a la base de datos SQLite"""
    db_path = current_dir / 'kronos.db'
    return sqlite3.connect(str(db_path))

def analyze_cell_id_correlation():
    """
    Analisis 1: Correlacion entre cell_ids de HUNTER vs Operadoras
    """
    print("=" * 80)
    print("ANALISIS 1: CORRELACION CELL_IDS HUNTER vs OPERADORAS")
    print("=" * 80)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Obtener sample de cell_ids de HUNTER (cellular_data)
        print("\nCELL_IDs de HUNTER (cellular_data):")
        cursor.execute("SELECT DISTINCT cell_id FROM cellular_data LIMIT 10")
        hunter_cells = cursor.fetchall()
        print(f"Sample de celdas HUNTER: {[cell[0] for cell in hunter_cells]}")
        
        # Obtener sample de cell_ids de operadoras (operator_call_data)
        print("\nCELL_IDs de OPERADORAS (operator_call_data):")
        cursor.execute("SELECT DISTINCT celda_origen FROM operator_call_data WHERE celda_origen IS NOT NULL LIMIT 10")
        operator_cells_origen = cursor.fetchall()
        print(f"Sample celdas origen operadoras: {[cell[0] for cell in operator_cells_origen]}")
        
        cursor.execute("SELECT DISTINCT celda_destino FROM operator_call_data WHERE celda_destino IS NOT NULL LIMIT 10")
        operator_cells_destino = cursor.fetchall()
        print(f"Sample celdas destino operadoras: {[cell[0] for cell in operator_cells_destino]}")
        
        # Verificar si hay interseccion
        print("\nVERIFICANDO INTERSECCION:")
        cursor.execute("""
        SELECT COUNT(*) as interseccion_count
        FROM cellular_data cd
        INNER JOIN operator_call_data ocd ON (cd.cell_id = ocd.celda_origen OR cd.cell_id = ocd.celda_destino)
        """)
        intersection_count = cursor.fetchone()[0]
        print(f"Interseccion encontrada: {intersection_count} registros")
        
        if intersection_count == 0:
            print("PROBLEMA CRITICO: NO HAY INTERSECCION ENTRE CELL_IDs HUNTER Y OPERADORAS")
            print("    Esto explica por que lat_hunter/lon_hunter siempre son NULL")
        
        return intersection_count > 0

def analyze_specific_endpoint_query(mission_id="mission_MPFRBNsb", target_number="3113330727", 
                                   start_datetime="2021-01-01 00:00:00", 
                                   end_datetime="2024-12-31 23:59:59"):
    """
    Analisis 2: Ejecutar la misma consulta exacta que get_call_interactions()
    """
    print("\n" + "=" * 80)
    print("ANALISIS 2: CONSULTA EXACTA DE get_call_interactions()")
    print("=" * 80)
    
    print(f"Parametros de prueba:")
    print(f"  - mission_id: {mission_id}")
    print(f"  - target_number: {target_number}")
    print(f"  - start_datetime: {start_datetime}")
    print(f"  - end_datetime: {end_datetime}")
    
    # Esta es la misma consulta SQL de main.py lineas 1070-1106
    query = """
    SELECT 
        ocd.numero_origen as originador,
        ocd.numero_destino as receptor,
        ocd.fecha_hora_llamada as fecha_hora, 
        ocd.duracion_segundos as duracion,
        ocd.operator as operador,
        ocd.celda_origen,
        ocd.celda_destino,
        ocd.latitud_origen,
        ocd.longitud_origen,
        ocd.latitud_destino,
        ocd.longitud_destino,
        cd_origen.punto as punto_hunter_origen,
        cd_origen.lat as lat_hunter_origen,
        cd_origen.lon as lon_hunter_origen,
        cd_destino.punto as punto_hunter_destino,
        cd_destino.lat as lat_hunter_destino,
        cd_destino.lon as lon_hunter_destino,
        -- CAMPOS UNIFICADOS HUNTER (CORRECCION BORIS): Prioriza destino sobre origen
        COALESCE(cd_destino.punto, cd_origen.punto) as punto_hunter,
        COALESCE(cd_destino.lat, cd_origen.lat) as lat_hunter,
        COALESCE(cd_destino.lon, cd_origen.lon) as lon_hunter,
        -- Metadatos adicionales para debugging
        CASE 
            WHEN cd_destino.punto IS NOT NULL THEN 'destino'
            WHEN cd_origen.punto IS NOT NULL THEN 'origen' 
            ELSE 'ninguno'
        END as hunter_source
    FROM operator_call_data ocd
    LEFT JOIN cellular_data cd_origen ON (cd_origen.cell_id = ocd.celda_origen AND cd_origen.mission_id = ocd.mission_id)
    LEFT JOIN cellular_data cd_destino ON (cd_destino.cell_id = ocd.celda_destino AND cd_destino.mission_id = ocd.mission_id)
    WHERE ocd.mission_id = ?
      AND (ocd.numero_origen = ? OR ocd.numero_destino = ?)
      AND ocd.fecha_hora_llamada BETWEEN ? AND ?  
    ORDER BY ocd.fecha_hora_llamada DESC
    LIMIT 5
    """
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Ejecutar consulta con parametros
        cursor.execute(query, (mission_id, target_number, target_number, start_datetime, end_datetime))
        rows = cursor.fetchall()
        
        if not rows:
            print("NO SE ENCONTRARON RESULTADOS")
            print("    Verificando si hay datos en las tablas...")
            
            # Verificar datos en operator_call_data
            cursor.execute("SELECT COUNT(*) FROM operator_call_data WHERE mission_id = ?", (mission_id,))
            operator_count = cursor.fetchone()[0]
            print(f"    - operator_call_data: {operator_count} registros")
            
            # Verificar datos en cellular_data  
            cursor.execute("SELECT COUNT(*) FROM cellular_data WHERE mission_id = ?", (mission_id,))
            cellular_count = cursor.fetchone()[0]
            print(f"    - cellular_data: {cellular_count} registros")
            
            return []
        
        # Analizar resultados
        column_names = [description[0] for description in cursor.description]
        results = []
        
        print(f"\nENCONTRADOS {len(rows)} REGISTROS:")
        for i, row in enumerate(rows):
            result = dict(zip(column_names, row))
            results.append(result)
            
            print(f"\n--- REGISTRO {i+1} ---")
            print(f"Llamada: {result['originador']} -> {result['receptor']}")
            print(f"Fecha: {result['fecha_hora']}")
            print(f"Operador: {result['operador']}")
            print(f"Celdas: origen={result['celda_origen']}, destino={result['celda_destino']}")
            
            # ANALISIS CRITICO: Coordenadas HUNTER
            print(f"COORDENADAS HUNTER:")
            print(f"  - punto_hunter_origen: {result['punto_hunter_origen']}")
            print(f"  - lat_hunter_origen: {result['lat_hunter_origen']}")
            print(f"  - lon_hunter_origen: {result['lon_hunter_origen']}")
            print(f"  - punto_hunter_destino: {result['punto_hunter_destino']}")
            print(f"  - lat_hunter_destino: {result['lat_hunter_destino']}")
            print(f"  - lon_hunter_destino: {result['lon_hunter_destino']}")
            print(f"  - UNIFICADO punto_hunter: {result['punto_hunter']}")
            print(f"  - UNIFICADO lat_hunter: {result['lat_hunter']}")
            print(f"  - UNIFICADO lon_hunter: {result['lon_hunter']}")
            print(f"  - hunter_source: {result['hunter_source']}")
            
            # Diagnostico especifico
            if result['lat_hunter'] is None and result['lon_hunter'] is None:
                print("  PROBLEMA: lat_hunter/lon_hunter son NULL")
                print("      Esto confirma el problema reportado por Boris")
            else:
                print("  GPS HUNTER valido encontrado")
    
    return results

def analyze_join_effectiveness():
    """
    Analisis 3: Efectividad de los JOINs por mision
    """
    print("\n" + "=" * 80)
    print("ANALISIS 3: EFECTIVIDAD DE JOINS POR MISION")
    print("=" * 80)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Verificar misiones disponibles
        cursor.execute("SELECT DISTINCT mission_id FROM operator_call_data")
        missions = cursor.fetchall()
        print(f"Misiones con datos de llamadas: {[m[0] for m in missions]}")
        
        cursor.execute("SELECT DISTINCT mission_id FROM cellular_data")
        hunter_missions = cursor.fetchall()
        print(f"Misiones con datos HUNTER: {[m[0] for m in hunter_missions]}")
        
        # Para cada mision, analizar efectividad del JOIN
        for mission_tuple in missions:
            mission_id = mission_tuple[0]
            print(f"\n--- MISION {mission_id} ---")
            
            # Total de llamadas
            cursor.execute("SELECT COUNT(*) FROM operator_call_data WHERE mission_id = ?", (mission_id,))
            total_calls = cursor.fetchone()[0]
            
            # Llamadas con correlacion HUNTER (cualquiera)
            cursor.execute("""
            SELECT COUNT(*) 
            FROM operator_call_data ocd
            WHERE ocd.mission_id = ?
              AND (
                EXISTS (SELECT 1 FROM cellular_data cd WHERE cd.cell_id = ocd.celda_origen AND cd.mission_id = ocd.mission_id)
                OR 
                EXISTS (SELECT 1 FROM cellular_data cd WHERE cd.cell_id = ocd.celda_destino AND cd.mission_id = ocd.mission_id)
              )
            """, (mission_id,))
            calls_with_hunter = cursor.fetchone()[0]
            
            percentage = (calls_with_hunter / total_calls * 100) if total_calls > 0 else 0
            print(f"  Total llamadas: {total_calls}")
            print(f"  Con correlacion HUNTER: {calls_with_hunter} ({percentage:.1f}%)")
            
            if percentage == 0:
                print("  CORRELACION 0% - Cell IDs no coinciden")
            elif percentage < 10:
                print("  CORRELACION BAJA - Pocos cell IDs coinciden")
            else:
                print("  Correlacion aceptable")

def analyze_sample_cell_ids():
    """
    Analisis 4: Muestra especifica de cell_ids para entender el problema
    """
    print("\n" + "=" * 80)
    print("ANALISIS 4: MUESTRA ESPECIFICA DE CELL_IDs")
    print("=" * 80)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Sample especifico de HUNTER para mision correcta
        print("\nHUNTER cell_ids (mission_MPFRBNsb):")
        cursor.execute("SELECT cell_id, punto, lat, lon FROM cellular_data WHERE mission_id = 'mission_MPFRBNsb' LIMIT 5")
        hunter_sample = cursor.fetchall()
        for cell_id, punto, lat, lon in hunter_sample:
            print(f"  {cell_id} -> {punto} ({lat}, {lon})")
        
        # Sample especifico de operadoras para mision correcta
        print("\nOPERADORA cell_ids (mission_MPFRBNsb):")
        cursor.execute("""
        SELECT DISTINCT celda_origen, operator 
        FROM operator_call_data 
        WHERE mission_id = 'mission_MPFRBNsb' AND celda_origen IS NOT NULL 
        LIMIT 5
        """)
        operator_sample = cursor.fetchall()
        for celda, operator in operator_sample:
            print(f"  {celda} -> {operator}")
        
        # Buscar cualquier coincidencia exacta
        print("\nCOINCIDENCIAS EXACTAS:")
        cursor.execute("""
        SELECT cd.cell_id, cd.punto, ocd.operator
        FROM cellular_data cd
        INNER JOIN operator_call_data ocd ON cd.cell_id = ocd.celda_origen
        WHERE cd.mission_id = 'mission_MPFRBNsb' AND ocd.mission_id = 'mission_MPFRBNsb'
        LIMIT 3
        """)
        matches = cursor.fetchall()
        if matches:
            for cell_id, punto, operator in matches:
                print(f"  Coincidencia: {cell_id} -> {punto} ({operator})")
        else:
            print("  NO HAY COINCIDENCIAS EXACTAS")
            print("      Esto confirma que los cell_ids no correlacionan")

def generate_diagnostic_report():
    """
    Genera reporte tecnico completo
    """
    print("\n" + "=" * 80)
    print("REPORTE TECNICO FINAL")
    print("=" * 80)
    
    has_correlation = analyze_cell_id_correlation()
    sample_results = analyze_specific_endpoint_query()
    
    print("\nDIAGNOSTICO FINAL:")
    print("-" * 40)
    
    if not has_correlation:
        print("PROBLEMA CONFIRMADO: Cell IDs HUNTER vs OPERADORAS no correlacionan")
        print("   - cellular_data.cell_id != operator_call_data.celda_origen/celda_destino")
        print("   - Los LEFT JOINs siempre retornan NULL para coordenadas HUNTER")
        print("   - Frontend recibe lat_hunter=None, lon_hunter=None")
        print("   - formatCoordinates() muestra 'N/A' como era esperado")
    
    print("\nDATOS ESPECIFICOS QUE RETORNA get_call_interactions():")
    if sample_results:
        for i, result in enumerate(sample_results[:2]):  # Solo primeros 2
            print(f"   Registro {i+1}:")
            print(f"     lat_hunter: {result['lat_hunter']} (tipo: {type(result['lat_hunter'])})")
            print(f"     lon_hunter: {result['lon_hunter']} (tipo: {type(result['lon_hunter'])})")
            print(f"     punto_hunter: {result['punto_hunter']}")
            print(f"     hunter_source: {result['hunter_source']}")
    
    print("\nPROPUESTA DE SOLUCION:")
    print("   1. Crear tabla de mapeo cell_id_hunter <-> cell_id_operadora")
    print("   2. Implementar algoritmo de correlacion geografica (distancia)")
    print("   3. Modificar consulta SQL para usar tabla de mapeo")
    print("   4. Validar que coordenadas lleguen correctamente al frontend")
    
    # Guardar reporte JSON
    report = {
        "timestamp": "2025-08-20",
        "problema_confirmado": not has_correlation,
        "coordenadas_hunter_nulls": all(r['lat_hunter'] is None for r in sample_results),
        "sample_data": sample_results[:3] if sample_results else [],
        "conclusion": "Cell IDs HUNTER no correlacionan con Cell IDs operadoras - JOINs fallan",
        "solucion_recomendada": "Implementar tabla de mapeo o correlacion geografica"
    }
    
    report_path = current_dir / 'diagnostico_coordenadas_gps_reporte.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\nReporte guardado en: {report_path}")

def main():
    """
    Funcion principal de diagnostico
    """
    print("DIAGNOSTICO BACKEND: Coordenadas GPS Missing en KRONOS")
    print("Problema reportado por Boris: Frontend muestra 'N/A' en lugar de GPS")
    print("Objetivo: Identificar exactamente que retorna get_call_interactions()")
    print("=" * 80)
    
    try:
        # Verificar que la base de datos existe
        db_path = current_dir / 'kronos.db'
        if not db_path.exists():
            print(f"ERROR: Base de datos no encontrada: {db_path}")
            return
        
        print(f"Base de datos encontrada: {db_path}")
        
        # Ejecutar analisis completo
        analyze_cell_id_correlation()
        analyze_specific_endpoint_query()
        analyze_join_effectiveness()
        analyze_sample_cell_ids()
        generate_diagnostic_report()
        
    except Exception as e:
        print(f"ERROR durante diagnostico: {e}")
        import traceback
        print(f"Traceback:\n{traceback.format_exc()}")

if __name__ == "__main__":
    main()