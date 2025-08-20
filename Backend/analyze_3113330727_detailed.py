#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANALISIS DETALLADO DEL NUMERO 3113330727
=========================================

Analizar el numero especifico en la tabla operator_call_data
para encontrar exactamente cuantas interacciones tiene.
"""

import sqlite3
import json
from datetime import datetime

def analyze_target_number():
    print("ANALIZANDO NUMERO 3113330727 EN TABLA operator_call_data")
    print("=" * 60)
    
    target_number = "3113330727"
    conn = sqlite3.connect("kronos.db")
    cursor = conn.cursor()
    
    # 1. Buscar como numero_origen
    cursor.execute("""
        SELECT COUNT(*) FROM operator_call_data 
        WHERE numero_origen = ?
    """, (target_number,))
    origen_count = cursor.fetchone()[0]
    
    # 2. Buscar como numero_destino
    cursor.execute("""
        SELECT COUNT(*) FROM operator_call_data 
        WHERE numero_destino = ?
    """, (target_number,))
    destino_count = cursor.fetchone()[0]
    
    # 3. Buscar como numero_objetivo
    cursor.execute("""
        SELECT COUNT(*) FROM operator_call_data 
        WHERE numero_objetivo = ?
    """, (target_number,))
    objetivo_count = cursor.fetchone()[0]
    
    print(f"RESULTADOS PARA {target_number}:")
    print(f"- Como numero_origen: {origen_count}")
    print(f"- Como numero_destino: {destino_count}")
    print(f"- Como numero_objetivo: {objetivo_count}")
    
    # 4. Obtener destinos unicos cuando es origen
    cursor.execute("""
        SELECT DISTINCT numero_destino FROM operator_call_data 
        WHERE numero_origen = ?
    """, (target_number,))
    destinos_unicos = cursor.fetchall()
    
    # 5. Obtener origenes unicos cuando es destino
    cursor.execute("""
        SELECT DISTINCT numero_origen FROM operator_call_data 
        WHERE numero_destino = ?
    """, (target_number,))
    origenes_unicos = cursor.fetchall()
    
    print(f"\nINTERACCIONES UNICAS:")
    print(f"- Destinos unicos (cuando es origen): {len(destinos_unicos)}")
    print(f"- Origenes unicos (cuando es destino): {len(origenes_unicos)}")
    
    # 6. Crear conjunto de todos los numeros relacionados
    all_related_numbers = set()
    
    for destino in destinos_unicos:
        all_related_numbers.add(destino[0])
    
    for origen in origenes_unicos:
        all_related_numbers.add(origen[0])
    
    # Incluir el numero objetivo mismo
    all_related_numbers.add(target_number)
    
    total_unique_nodes = len(all_related_numbers)
    
    print(f"\nTOTAL DE NODOS UNICOS ESPERADOS: {total_unique_nodes}")
    print(f"NODOS REPORTADOS EN UI: 255")
    print(f"DIFERENCIA: {255 - total_unique_nodes}")
    
    # 7. Mostrar los primeros numeros relacionados
    print(f"\nPrimeros 20 numeros relacionados:")
    related_list = list(all_related_numbers)[:20]
    for i, numero in enumerate(related_list, 1):
        print(f"  {i}. {numero}")
    
    # 8. Analizar por operador si esta disponible
    cursor.execute("""
        SELECT operator, COUNT(*) FROM operator_call_data 
        WHERE numero_origen = ? OR numero_destino = ? OR numero_objetivo = ?
        GROUP BY operator
    """, (target_number, target_number, target_number))
    
    por_operador = cursor.fetchall()
    print(f"\nDISTRIBUCION POR OPERADOR:")
    for operador, count in por_operador:
        print(f"  {operador}: {count} registros")
    
    # 9. Analizar por periodo de tiempo
    cursor.execute("""
        SELECT DATE(fecha_hora_llamada) as fecha, COUNT(*) as llamadas
        FROM operator_call_data 
        WHERE numero_origen = ? OR numero_destino = ? OR numero_objetivo = ?
        GROUP BY DATE(fecha_hora_llamada)
        ORDER BY llamadas DESC
        LIMIT 10
    """, (target_number, target_number, target_number))
    
    por_fecha = cursor.fetchall()
    print(f"\nACTIVIDAD POR FECHA (Top 10):")
    for fecha, llamadas in por_fecha:
        print(f"  {fecha}: {llamadas} llamadas")
    
    # 10. Verificar si hay duplicados o registros anomalos
    cursor.execute("""
        SELECT numero_origen, numero_destino, COUNT(*) as repeticiones
        FROM operator_call_data 
        WHERE numero_origen = ? OR numero_destino = ?
        GROUP BY numero_origen, numero_destino
        HAVING COUNT(*) > 10
        ORDER BY repeticiones DESC
        LIMIT 10
    """, (target_number, target_number))
    
    duplicados = cursor.fetchall()
    if duplicados:
        print(f"\nPOSIBLES DUPLICADOS (>10 repeticiones):")
        for origen, destino, rep in duplicados:
            print(f"  {origen} -> {destino}: {rep} repeticiones")
    else:
        print(f"\nNo se encontraron duplicados significativos")
    
    # 11. Guardar resultados detallados
    resultados = {
        "numero_objetivo": target_number,
        "fecha_analisis": datetime.now().isoformat(),
        "conteos": {
            "como_origen": origen_count,
            "como_destino": destino_count,
            "como_objetivo": objetivo_count
        },
        "nodos_unicos": {
            "destinos_cuando_origen": len(destinos_unicos),
            "origenes_cuando_destino": len(origenes_unicos),
            "total_nodos_esperados": total_unique_nodes
        },
        "metricas_problema": {
            "nodos_esperados": total_unique_nodes,
            "nodos_reportados_ui": 255,
            "diferencia": 255 - total_unique_nodes
        },
        "distribucion_operador": dict(por_operador),
        "actividad_por_fecha": dict(por_fecha),
        "numeros_relacionados": list(all_related_numbers),
        "duplicados_detectados": duplicados
    }
    
    # Guardar en archivo JSON
    with open(f"analisis_detallado_{target_number}.json", 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    
    print(f"\nAnalisis guardado en: analisis_detallado_{target_number}.json")
    
    # 12. DIAGNOSTICO FINAL
    print(f"\n" + "="*60)
    print("DIAGNOSTICO FINAL:")
    print("="*60)
    
    if total_unique_nodes < 255:
        print(f"PROBLEMA IDENTIFICADO:")
        print(f"- La base de datos tiene {total_unique_nodes} nodos unicos")
        print(f"- La UI muestra 255 nodos")
        print(f"- Se estan agregando {255 - total_unique_nodes} nodos extra")
        print(f"\nPOSIBLES CAUSAS:")
        print(f"1. El servicio de correlacion esta incluyendo datos de otros numeros")
        print(f"2. El frontend esta duplicando nodos durante la transformacion")
        print(f"3. Se estan incluyendo nodos de referencia o auxiliares")
        print(f"4. Hay un error en el filtrado de datos")
    else:
        print(f"Los datos de la base parecen correctos")
        print(f"El problema podria estar en el filtrado o transformacion")
    
    conn.close()
    return resultados

if __name__ == "__main__":
    analyze_target_number()