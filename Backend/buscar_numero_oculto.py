#!/usr/bin/env python3
"""
BÚSQUEDA ESPECÍFICA - Encontrar 3104277553 con formatos alternativos
=================================================================
Boris: 3104277553 llamando al 3224274851 en celda 53591 -> 52453
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sqlite3

def buscar_numero_oculto():
    print("BÚSQUEDA DE NÚMERO CON FORMATOS ALTERNATIVOS")
    print("=" * 55)
    
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kronos.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Buscar llamadas donde 3224274851 es el destino EN celda 53591 
    print("1. Llamadas hacia 3224274851 en celda 53591:")
    print("-" * 40)
    
    query = """
        SELECT 
            numero_origen, numero_destino, numero_objetivo,
            celda_origen, celda_destino, celda_objetivo,
            fecha_hora_llamada
        FROM operator_call_data
        WHERE (numero_destino LIKE '%3224274851%' OR numero_objetivo LIKE '%3224274851%')
        AND (celda_origen = '53591' OR celda_destino = '53591' OR celda_objetivo = '53591')
        ORDER BY fecha_hora_llamada
    """
    
    cursor = conn.execute(query)
    records = cursor.fetchall()
    
    print(f"Registros encontrados: {len(records)}")
    
    for record in records:
        print(f"  Fecha: {record['fecha_hora_llamada']}")
        print(f"  Origen: {record['numero_origen']}")
        print(f"  Destino: {record['numero_destino']}")
        print(f"  Celdas: origen={record['celda_origen']}, destino={record['celda_destino']}")
        
        # Analizar si el origen podría ser 3104277553 en otro formato
        origen = record['numero_origen']
        if origen:
            # Quitar todos los caracteres no numéricos
            digits_only = ''.join(filter(str.isdigit, origen))
            
            # Buscar la secuencia 3104277553 en el número
            if '3104277553' in digits_only:
                print(f"    *** ENCONTRADO: {origen} contiene 3104277553 ***")
            elif digits_only.endswith('3104277553'):
                print(f"    *** POSIBLE: {origen} termina en 3104277553 ***")
            elif '104277553' in digits_only:
                print(f"    *** PARCIAL: {origen} contiene 104277553 ***")
        print()
    
    # 2. Buscar actividad en celda 53591 en el período relevante
    print("2. Toda la actividad en celda 53591:")
    print("-" * 35)
    
    activity_query = """
        SELECT 
            numero_origen, numero_destino,
            celda_origen, celda_destino, celda_objetivo,
            fecha_hora_llamada
        FROM operator_call_data
        WHERE celda_origen = '53591'
        AND fecha_hora_llamada BETWEEN '2021-05-20 10:00:00' AND '2021-05-20 11:00:00'
        ORDER BY fecha_hora_llamada
        LIMIT 20
    """
    
    cursor = conn.execute(activity_query)
    activity_records = cursor.fetchall()
    
    print(f"Actividad en celda 53591 (10:00-11:00): {len(activity_records)} registros")
    
    for record in activity_records:
        origen = record['numero_origen']
        destino = record['numero_destino']
        
        print(f"  {record['fecha_hora_llamada']}: {origen} -> {destino}")
        
        # Buscar coincidencias con patrones del número buscado
        for numero in [origen, destino]:
            if numero:
                digits = ''.join(filter(str.isdigit, numero))
                
                # Verificar diferentes patrones
                patterns = ['3104277553', '104277553', '4277553', '277553']
                for pattern in patterns:
                    if pattern in digits:
                        print(f"    *** PATRÓN {pattern} encontrado en {numero} ***")
    
    # 3. Verificar llamadas con destino a celda 52453
    print("\n3. Actividad con destino a celda 52453:")
    print("-" * 40)
    
    dest_query = """
        SELECT 
            numero_origen, numero_destino,
            celda_origen, celda_destino,
            fecha_hora_llamada
        FROM operator_call_data
        WHERE celda_destino = '52453'
        AND fecha_hora_llamada BETWEEN '2021-05-20 10:00:00' AND '2021-05-20 12:00:00'
        ORDER BY fecha_hora_llamada
        LIMIT 10
    """
    
    cursor = conn.execute(dest_query)
    dest_records = cursor.fetchall()
    
    print(f"Llamadas con destino celda 52453: {len(dest_records)}")
    
    for record in dest_records:
        print(f"  {record['fecha_hora_llamada']}: {record['numero_origen']} -> {record['numero_destino']}")
        print(f"    Celdas: {record['celda_origen']} -> {record['celda_destino']}")
        
        # Verificar si hay números que contengan 3224274851
        for numero in [record['numero_origen'], record['numero_destino']]:
            if numero and '3224274851' in numero:
                print(f"    *** DESTINO CORRECTO: {numero} ***")
    
    conn.close()

if __name__ == "__main__":
    buscar_numero_oculto()