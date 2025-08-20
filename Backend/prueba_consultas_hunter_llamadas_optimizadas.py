#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRUEBA DE CONSULTAS OPTIMIZADAS HUNTER-LLAMADAS
Boris - Validación de consultas SQL para relacionar datos HUNTER con llamadas telefónicas
"""

import sqlite3
import json
import time
from datetime import datetime

def ejecutar_consultas_optimizadas():
    """
    Ejecuta y valida las consultas SQL optimizadas para relacionar HUNTER con LLAMADAS
    """
    print("=" * 80)
    print("PRUEBA DE CONSULTAS OPTIMIZADAS HUNTER-LLAMADAS")
    print("=" * 80)
    
    conn = sqlite3.connect("kronos.db")
    cursor = conn.cursor()
    
    # Obtener mission_id para las pruebas
    cursor.execute("SELECT DISTINCT mission_id FROM cellular_data LIMIT 1")
    mission_id = cursor.fetchone()[0]
    print(f"Mission ID para pruebas: {mission_id}")
    
    resultados = {}
    
    # ==================================================
    # CONSULTA 1: RELACIÓN POR CELDA_ORIGEN
    # ==================================================
    print("\n1. CONSULTA POR CELDA_ORIGEN")
    print("-" * 50)
    
    consulta_origen = """
    SELECT 
        cd.punto AS punto_hunter,
        cd.lat AS lat_hunter,
        cd.lon AS lon_hunter,
        cd.cell_id,
        cd.operator AS operador_hunter,
        cd.tecnologia AS tech_hunter,
        ocd.numero_origen,
        ocd.numero_destino,
        ocd.fecha_hora_llamada,
        ocd.duracion_segundos,
        ocd.celda_origen,
        ocd.operator AS operador_llamada,
        ocd.tecnologia AS tech_llamada
    FROM cellular_data cd
    INNER JOIN operator_call_data ocd ON cd.cell_id = ocd.celda_origen
    WHERE cd.mission_id = ? AND ocd.mission_id = ?
    ORDER BY ocd.fecha_hora_llamada DESC
    LIMIT 10;
    """
    
    start_time = time.time()
    cursor.execute(consulta_origen, (mission_id, mission_id))
    resultados_origen = cursor.fetchall()
    tiempo_origen = time.time() - start_time
    
    print(f"Registros encontrados: {len(resultados_origen)}")
    print(f"Tiempo de ejecución: {tiempo_origen:.4f} segundos")
    
    if resultados_origen:
        print("\nPrimeros 3 resultados:")
        for i, resultado in enumerate(resultados_origen[:3], 1):
            print(f"  {i}. Punto: {resultado[0]}")
            print(f"     Cell_ID: {resultado[3]} -> Celda_Origen: {resultado[10]}")
            print(f"     Llamada: {resultado[6]} -> {resultado[7]}")
            print(f"     Fecha: {resultado[8]}")
            print()
    
    resultados['consulta_origen'] = {
        'registros': len(resultados_origen),
        'tiempo_segundos': tiempo_origen,
        'muestra': resultados_origen[:3] if resultados_origen else []
    }
    
    # ==================================================
    # CONSULTA 2: RELACIÓN POR CELDA_DESTINO
    # ==================================================
    print("\n2. CONSULTA POR CELDA_DESTINO")
    print("-" * 50)
    
    consulta_destino = """
    SELECT 
        cd.punto AS punto_hunter,
        cd.lat AS lat_hunter,
        cd.lon AS lon_hunter,
        cd.cell_id,
        cd.operator AS operador_hunter,
        cd.tecnologia AS tech_hunter,
        ocd.numero_origen,
        ocd.numero_destino,
        ocd.fecha_hora_llamada,
        ocd.duracion_segundos,
        ocd.celda_destino,
        ocd.operator AS operador_llamada,
        ocd.tecnologia AS tech_llamada
    FROM cellular_data cd
    INNER JOIN operator_call_data ocd ON cd.cell_id = ocd.celda_destino
    WHERE cd.mission_id = ? AND ocd.mission_id = ?
    ORDER BY ocd.fecha_hora_llamada DESC
    LIMIT 10;
    """
    
    start_time = time.time()
    cursor.execute(consulta_destino, (mission_id, mission_id))
    resultados_destino = cursor.fetchall()
    tiempo_destino = time.time() - start_time
    
    print(f"Registros encontrados: {len(resultados_destino)}")
    print(f"Tiempo de ejecución: {tiempo_destino:.4f} segundos")
    
    if resultados_destino:
        print("\nPrimeros 3 resultados:")
        for i, resultado in enumerate(resultados_destino[:3], 1):
            print(f"  {i}. Punto: {resultado[0]}")
            print(f"     Cell_ID: {resultado[3]} -> Celda_Destino: {resultado[10]}")
            print(f"     Llamada: {resultado[6]} -> {resultado[7]}")
            print(f"     Fecha: {resultado[8]}")
            print()
    
    resultados['consulta_destino'] = {
        'registros': len(resultados_destino),
        'tiempo_segundos': tiempo_destino,
        'muestra': resultados_destino[:3] if resultados_destino else []
    }
    
    # ==================================================
    # CONSULTA 3: UNIÓN COMPLETA (ORIGEN + DESTINO)
    # ==================================================
    print("\n3. CONSULTA UNIÓN COMPLETA")
    print("-" * 50)
    
    consulta_completa = """
    SELECT 
        cd.punto AS punto_hunter,
        cd.lat AS lat_hunter,
        cd.lon AS lon_hunter,
        cd.cell_id,
        cd.operator AS operador_hunter,
        cd.tecnologia AS tech_hunter,
        ocd.numero_origen,
        ocd.numero_destino,
        ocd.fecha_hora_llamada,
        ocd.duracion_segundos,
        CASE 
            WHEN cd.cell_id = ocd.celda_origen THEN ocd.celda_origen
            WHEN cd.cell_id = ocd.celda_destino THEN ocd.celda_destino
        END AS celda_coincidente,
        CASE 
            WHEN cd.cell_id = ocd.celda_origen THEN 'ORIGEN'
            WHEN cd.cell_id = ocd.celda_destino THEN 'DESTINO'
        END AS tipo_coincidencia,
        ocd.operator AS operador_llamada,
        ocd.tecnologia AS tech_llamada
    FROM cellular_data cd
    INNER JOIN operator_call_data ocd ON (
        cd.cell_id = ocd.celda_origen OR cd.cell_id = ocd.celda_destino
    )
    WHERE cd.mission_id = ? AND ocd.mission_id = ?
    ORDER BY ocd.fecha_hora_llamada DESC
    LIMIT 15;
    """
    
    start_time = time.time()
    cursor.execute(consulta_completa, (mission_id, mission_id))
    resultados_completa = cursor.fetchall()
    tiempo_completa = time.time() - start_time
    
    print(f"Registros encontrados: {len(resultados_completa)}")
    print(f"Tiempo de ejecución: {tiempo_completa:.4f} segundos")
    
    if resultados_completa:
        print("\nPrimeros 5 resultados:")
        for i, resultado in enumerate(resultados_completa[:5], 1):
            print(f"  {i}. Punto: {resultado[0]}")
            print(f"     Cell_ID: {resultado[3]} -> Celda: {resultado[10]} ({resultado[11]})")
            print(f"     Llamada: {resultado[6]} -> {resultado[7]}")
            print(f"     Fecha: {resultado[8]}")
            print()
    
    resultados['consulta_completa'] = {
        'registros': len(resultados_completa),
        'tiempo_segundos': tiempo_completa,
        'muestra': resultados_completa[:5] if resultados_completa else []
    }
    
    # ==================================================
    # CONSULTA 4: ANÁLISIS POR PUNTO HUNTER
    # ==================================================
    print("\n4. ANÁLISIS POR PUNTO HUNTER")
    print("-" * 50)
    
    consulta_por_punto = """
    SELECT 
        cd.punto,
        COUNT(DISTINCT cd.cell_id) as celdas_hunter,
        COUNT(ocd.id) as llamadas_relacionadas,
        COUNT(DISTINCT ocd.numero_origen) as numeros_origen_unicos,
        COUNT(DISTINCT ocd.numero_destino) as numeros_destino_unicos,
        MIN(ocd.fecha_hora_llamada) as primera_llamada,
        MAX(ocd.fecha_hora_llamada) as ultima_llamada
    FROM cellular_data cd
    INNER JOIN operator_call_data ocd ON (
        cd.cell_id = ocd.celda_origen OR cd.cell_id = ocd.celda_destino
    )
    WHERE cd.mission_id = ? AND ocd.mission_id = ?
    GROUP BY cd.punto
    ORDER BY llamadas_relacionadas DESC;
    """
    
    start_time = time.time()
    cursor.execute(consulta_por_punto, (mission_id, mission_id))
    resultados_por_punto = cursor.fetchall()
    tiempo_por_punto = time.time() - start_time
    
    print(f"Puntos con actividad: {len(resultados_por_punto)}")
    print(f"Tiempo de ejecución: {tiempo_por_punto:.4f} segundos")
    
    if resultados_por_punto:
        print("\nResumen por punto:")
        for punto_data in resultados_por_punto:
            print(f"  Punto: {punto_data[0]}")
            print(f"    Celdas HUNTER: {punto_data[1]}")
            print(f"    Llamadas relacionadas: {punto_data[2]}")
            print(f"    Números origen únicos: {punto_data[3]}")
            print(f"    Números destino únicos: {punto_data[4]}")
            print(f"    Período: {punto_data[5]} a {punto_data[6]}")
            print()
    
    resultados['analisis_por_punto'] = {
        'puntos_activos': len(resultados_por_punto),
        'tiempo_segundos': tiempo_por_punto,
        'datos': resultados_por_punto
    }
    
    # ==================================================
    # CONSULTA 5: BÚSQUEDA ESPECÍFICA POR CELL_ID
    # ==================================================
    print("\n5. BÚSQUEDA ESPECÍFICA POR CELL_ID")
    print("-" * 50)
    
    # Obtener un cell_id específico para la prueba
    cursor.execute("SELECT cell_id FROM cellular_data WHERE cell_id IS NOT NULL LIMIT 1")
    test_cell_id = cursor.fetchone()[0]
    
    consulta_especifica = """
    SELECT 
        'HUNTER' as fuente,
        cd.punto,
        cd.lat,
        cd.lon,
        cd.cell_id,
        cd.operator,
        cd.tecnologia,
        NULL as numero_origen,
        NULL as numero_destino,
        NULL as fecha_llamada
    FROM cellular_data cd
    WHERE cd.cell_id = ?
    
    UNION ALL
    
    SELECT 
        'LLAMADA_ORIGEN' as fuente,
        NULL as punto,
        ocd.latitud_origen as lat,
        ocd.longitud_origen as lon,
        ocd.celda_origen as cell_id,
        ocd.operator,
        ocd.tecnologia,
        ocd.numero_origen,
        ocd.numero_destino,
        ocd.fecha_hora_llamada
    FROM operator_call_data ocd
    WHERE ocd.celda_origen = ?
    
    UNION ALL
    
    SELECT 
        'LLAMADA_DESTINO' as fuente,
        NULL as punto,
        ocd.latitud_destino as lat,
        ocd.longitud_destino as lon,
        ocd.celda_destino as cell_id,
        ocd.operator,
        ocd.tecnologia,
        ocd.numero_origen,
        ocd.numero_destino,
        ocd.fecha_hora_llamada
    FROM operator_call_data ocd
    WHERE ocd.celda_destino = ?
    
    ORDER BY fuente, fecha_llamada DESC;
    """
    
    start_time = time.time()
    cursor.execute(consulta_especifica, (test_cell_id, test_cell_id, test_cell_id))
    resultados_especifica = cursor.fetchall()
    tiempo_especifica = time.time() - start_time
    
    print(f"Cell_ID analizado: {test_cell_id}")
    print(f"Registros encontrados: {len(resultados_especifica)}")
    print(f"Tiempo de ejecución: {tiempo_especifica:.4f} segundos")
    
    if resultados_especifica:
        for fuente in ['HUNTER', 'LLAMADA_ORIGEN', 'LLAMADA_DESTINO']:
            fuente_data = [r for r in resultados_especifica if r[0] == fuente]
            if fuente_data:
                print(f"\n  {fuente}: {len(fuente_data)} registros")
                if fuente == 'HUNTER':
                    for data in fuente_data[:2]:
                        print(f"    Punto: {data[1]} - Operador: {data[5]}")
                else:
                    for data in fuente_data[:3]:
                        print(f"    Llamada: {data[7]} -> {data[8]} ({data[9]})")
    
    resultados['busqueda_especifica'] = {
        'cell_id_analizado': test_cell_id,
        'registros': len(resultados_especifica),
        'tiempo_segundos': tiempo_especifica
    }
    
    # ==================================================
    # VERIFICAR ÍNDICES CREADOS
    # ==================================================
    print("\n6. VERIFICACIÓN DE ÍNDICES")
    print("-" * 50)
    
    cursor.execute("""
        SELECT 
            name as indice_nombre,
            tbl_name as tabla
        FROM sqlite_master 
        WHERE type = 'index' 
            AND tbl_name IN ('cellular_data', 'operator_call_data')
            AND name LIKE 'idx_%'
        ORDER BY tbl_name, name;
    """)
    
    indices = cursor.fetchall()
    print(f"Índices creados: {len(indices)}")
    for indice in indices:
        print(f"  - {indice[0]} (tabla: {indice[1]})")
    
    # ==================================================
    # GUARDAR REPORTE
    # ==================================================
    reporte_final = {
        'timestamp': datetime.now().isoformat(),
        'mission_id': mission_id,
        'resultados_consultas': resultados,
        'indices_optimizacion': len(indices),
        'resumen': {
            'hunter_registros': 58,  # Del análisis anterior
            'llamadas_registros': 3392,  # Del análisis anterior
            'total_coincidencias_origen': resultados['consulta_origen']['registros'],
            'total_coincidencias_destino': resultados['consulta_destino']['registros'],
            'total_coincidencias_completas': resultados['consulta_completa']['registros'],
            'puntos_con_actividad': resultados['analisis_por_punto']['puntos_activos']
        }
    }
    
    nombre_reporte = f"prueba_consultas_hunter_llamadas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(nombre_reporte, "w", encoding="utf-8") as f:
        json.dump(reporte_final, f, indent=2, ensure_ascii=False)
    
    print(f"\n\nReporte guardado en: {nombre_reporte}")
    
    conn.close()
    return reporte_final

if __name__ == "__main__":
    reporte = ejecutar_consultas_optimizadas()
    print("\n" + "=" * 80)
    print("PRUEBA DE CONSULTAS COMPLETADA")
    print("=" * 80)