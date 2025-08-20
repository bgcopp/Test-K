#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANÁLISIS DE RELACIÓN ENTRE DATOS HUNTER Y LLAMADAS TELEFÓNICAS
Boris - Análisis de estructura y relaciones para consultas SQL optimizadas
"""

import sqlite3
import json
from datetime import datetime

def analizar_relacion_hunter_llamadas():
    """
    Analiza la relación entre cellular_data (HUNTER) y operator_call_data (LLAMADAS)
    para determinar la estrategia de JOIN óptima
    """
    print("=" * 80)
    print("ANÁLISIS DE RELACIÓN HUNTER-LLAMADAS")
    print("=" * 80)
    
    conn = sqlite3.connect("kronos.db")
    cursor = conn.cursor()
    
    # 1. ANÁLISIS DETALLADO DE TABLA CELLULAR_DATA (HUNTER)
    print("\n1. ANÁLISIS TABLA CELLULAR_DATA (HUNTER)")
    print("-" * 50)
    
    cursor.execute("SELECT COUNT(*) FROM cellular_data")
    hunter_count = cursor.fetchone()[0]
    print(f"Total registros HUNTER: {hunter_count}")
    
    # Estructura y muestra de datos HUNTER
    cursor.execute("SELECT * FROM cellular_data LIMIT 3")
    hunter_samples = cursor.fetchall()
    print("\nMuestra de datos HUNTER:")
    for i, sample in enumerate(hunter_samples, 1):
        print(f"  Registro {i}: {sample}")
    
    # Análisis de cell_id en HUNTER
    cursor.execute("SELECT DISTINCT cell_id FROM cellular_data WHERE cell_id IS NOT NULL ORDER BY cell_id LIMIT 10")
    hunter_cell_ids = cursor.fetchall()
    print(f"\nPrimeros 10 cell_id únicos en HUNTER: {[c[0] for c in hunter_cell_ids]}")
    
    # Análisis de puntos únicos
    cursor.execute("SELECT DISTINCT punto FROM cellular_data WHERE punto IS NOT NULL ORDER BY punto")
    hunter_puntos = cursor.fetchall()
    print(f"Puntos únicos en HUNTER: {[p[0] for p in hunter_puntos]}")
    
    # 2. ANÁLISIS DETALLADO DE TABLA OPERATOR_CALL_DATA (LLAMADAS)
    print("\n\n2. ANÁLISIS TABLA OPERATOR_CALL_DATA (LLAMADAS)")
    print("-" * 50)
    
    cursor.execute("SELECT COUNT(*) FROM operator_call_data")
    call_count = cursor.fetchone()[0]
    print(f"Total registros LLAMADAS: {call_count}")
    
    # Estructura y muestra de datos LLAMADAS
    cursor.execute("SELECT * FROM operator_call_data LIMIT 3")
    call_samples = cursor.fetchall()
    print("\nMuestra de datos LLAMADAS:")
    for i, sample in enumerate(call_samples, 1):
        print(f"  Registro {i}: {sample}")
    
    # Análisis de celdas en LLAMADAS
    cursor.execute("SELECT DISTINCT celda_origen FROM operator_call_data WHERE celda_origen IS NOT NULL ORDER BY celda_origen LIMIT 10")
    call_celda_origen = cursor.fetchall()
    print(f"\nPrimeros 10 celda_origen únicos en LLAMADAS: {[c[0] for c in call_celda_origen]}")
    
    cursor.execute("SELECT DISTINCT celda_destino FROM operator_call_data WHERE celda_destino IS NOT NULL ORDER BY celda_destino LIMIT 10")
    call_celda_destino = cursor.fetchall()
    print(f"Primeros 10 celda_destino únicos en LLAMADAS: {[c[0] for c in call_celda_destino]}")
    
    # 3. ANÁLISIS DE COINCIDENCIAS ENTRE CELL_ID Y CELDAS
    print("\n\n3. ANÁLISIS DE COINCIDENCIAS")
    print("-" * 50)
    
    # Verificar coincidencias entre cell_id (HUNTER) y celda_origen (LLAMADAS)
    cursor.execute("""
        SELECT COUNT(*) 
        FROM cellular_data cd 
        INNER JOIN operator_call_data ocd ON cd.cell_id = ocd.celda_origen
    """)
    matches_origen = cursor.fetchone()[0]
    print(f"Coincidencias cell_id <-> celda_origen: {matches_origen}")
    
    # Verificar coincidencias entre cell_id (HUNTER) y celda_destino (LLAMADAS)
    cursor.execute("""
        SELECT COUNT(*) 
        FROM cellular_data cd 
        INNER JOIN operator_call_data ocd ON cd.cell_id = ocd.celda_destino
    """)
    matches_destino = cursor.fetchone()[0]
    print(f"Coincidencias cell_id <-> celda_destino: {matches_destino}")
    
    # 4. EJEMPLOS DE COINCIDENCIAS REALES
    print("\n\n4. EJEMPLOS DE COINCIDENCIAS REALES")
    print("-" * 50)
    
    if matches_origen > 0:
        print("COINCIDENCIAS CON CELDA_ORIGEN:")
        cursor.execute("""
            SELECT 
                cd.punto,
                cd.cell_id,
                cd.lat,
                cd.lon,
                cd.operator as hunter_operator,
                ocd.numero_origen,
                ocd.numero_destino,
                ocd.celda_origen,
                ocd.operator as call_operator
            FROM cellular_data cd 
            INNER JOIN operator_call_data ocd ON cd.cell_id = ocd.celda_origen
            LIMIT 5
        """)
        ejemplos_origen = cursor.fetchall()
        for i, ejemplo in enumerate(ejemplos_origen, 1):
            print(f"  Ejemplo {i}: Punto={ejemplo[0]}, Cell_ID={ejemplo[1]}, Hunter_Op={ejemplo[4]}, Call_Op={ejemplo[8]}")
    
    if matches_destino > 0:
        print("\nCOINCIDENCIAS CON CELDA_DESTINO:")
        cursor.execute("""
            SELECT 
                cd.punto,
                cd.cell_id,
                cd.lat,
                cd.lon,
                cd.operator as hunter_operator,
                ocd.numero_origen,
                ocd.numero_destino,
                ocd.celda_destino,
                ocd.operator as call_operator
            FROM cellular_data cd 
            INNER JOIN operator_call_data ocd ON cd.cell_id = ocd.celda_destino
            LIMIT 5
        """)
        ejemplos_destino = cursor.fetchall()
        for i, ejemplo in enumerate(ejemplos_destino, 1):
            print(f"  Ejemplo {i}: Punto={ejemplo[0]}, Cell_ID={ejemplo[1]}, Hunter_Op={ejemplo[4]}, Call_Op={ejemplo[8]}")
    
    # 5. ANÁLISIS DE FORMATOS DE CELL_ID
    print("\n\n5. ANÁLISIS DE FORMATOS DE CELL_ID")
    print("-" * 50)
    
    # Tipos de datos en cell_id (HUNTER)
    cursor.execute("SELECT DISTINCT typeof(cell_id), COUNT(*) FROM cellular_data GROUP BY typeof(cell_id)")
    hunter_cell_types = cursor.fetchall()
    print(f"Tipos de datos en cell_id (HUNTER): {hunter_cell_types}")
    
    # Tipos de datos en celda_origen/destino (LLAMADAS)
    cursor.execute("SELECT DISTINCT typeof(celda_origen), COUNT(*) FROM operator_call_data GROUP BY typeof(celda_origen)")
    call_origen_types = cursor.fetchall()
    print(f"Tipos de datos en celda_origen (LLAMADAS): {call_origen_types}")
    
    cursor.execute("SELECT DISTINCT typeof(celda_destino), COUNT(*) FROM operator_call_data GROUP BY typeof(celda_destino)")
    call_destino_types = cursor.fetchall()
    print(f"Tipos de datos en celda_destino (LLAMADAS): {call_destino_types}")
    
    # 6. CONSULTAS SQL OPTIMIZADAS PROPUESTAS
    print("\n\n6. CONSULTAS SQL OPTIMIZADAS PROPUESTAS")
    print("-" * 50)
    
    consultas_optimizadas = {
        "consulta_origen": """
-- CONSULTA 1: Relacionar HUNTER con LLAMADAS por celda_origen
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
ORDER BY ocd.fecha_hora_llamada DESC;
""",
        "consulta_destino": """
-- CONSULTA 2: Relacionar HUNTER con LLAMADAS por celda_destino
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
ORDER BY ocd.fecha_hora_llamada DESC;
""",
        "consulta_completa": """
-- CONSULTA 3: Unión completa (origen + destino)
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
ORDER BY ocd.fecha_hora_llamada DESC;
"""
    }
    
    for nombre, consulta in consultas_optimizadas.items():
        print(f"\n{nombre.upper()}:")
        print(consulta)
    
    # 7. RECOMENDACIONES DE OPTIMIZACIÓN
    print("\n\n7. RECOMENDACIONES DE OPTIMIZACIÓN")
    print("-" * 50)
    
    recomendaciones = [
        "1. Crear índices en las columnas de JOIN:",
        "   CREATE INDEX idx_cellular_data_cell_id ON cellular_data(cell_id);",
        "   CREATE INDEX idx_operator_call_data_celda_origen ON operator_call_data(celda_origen);",
        "   CREATE INDEX idx_operator_call_data_celda_destino ON operator_call_data(celda_destino);",
        "",
        "2. Considerar índices compuestos para consultas frecuentes:",
        "   CREATE INDEX idx_cellular_data_mission_cell ON cellular_data(mission_id, cell_id);",
        "   CREATE INDEX idx_operator_call_data_mission_origen ON operator_call_data(mission_id, celda_origen);",
        "",
        "3. Para consultas con filtros de fecha/tiempo:",
        "   CREATE INDEX idx_operator_call_data_fecha ON operator_call_data(fecha_hora_llamada);",
        "",
        "4. Verificar consistencia de tipos de datos entre cell_id y celda_origen/destino",
        "5. Considerar normalización si hay redundancia de datos geográficos"
    ]
    
    for rec in recomendaciones:
        print(rec)
    
    # 8. GENERAR REPORTE JSON
    reporte = {
        "timestamp": datetime.now().isoformat(),
        "analisis": "Relación HUNTER-LLAMADAS",
        "estadisticas": {
            "hunter_registros": hunter_count,
            "llamadas_registros": call_count,
            "coincidencias_origen": matches_origen,
            "coincidencias_destino": matches_destino
        },
        "esquemas": {
            "hunter_campos_clave": ["punto", "cell_id", "lat", "lon", "operator", "tecnologia"],
            "llamadas_campos_clave": ["numero_origen", "numero_destino", "celda_origen", "celda_destino", "operator", "tecnologia"]
        },
        "relaciones_detectadas": {
            "cell_id_celda_origen": matches_origen > 0,
            "cell_id_celda_destino": matches_destino > 0
        },
        "consultas_optimizadas": consultas_optimizadas
    }
    
    with open(f"analisis_hunter_llamadas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w", encoding="utf-8") as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)
    
    print(f"\n\nReporte guardado en: analisis_hunter_llamadas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    conn.close()
    return reporte

if __name__ == "__main__":
    reporte = analizar_relacion_hunter_llamadas()
    print("\n" + "=" * 80)
    print("ANÁLISIS COMPLETADO")
    print("=" * 80)