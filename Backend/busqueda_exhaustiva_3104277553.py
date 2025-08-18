#!/usr/bin/env python3
"""
BÚSQUEDA EXHAUSTIVA - Encontrar 3104277553 en cualquier formato
=============================================================
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sqlite3
import logging

logging.basicConfig(level=logging.WARNING)

def busqueda_exhaustiva():
    print("BÚSQUEDA EXHAUSTIVA - Número 3104277553")
    print("=" * 50)
    
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kronos.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Secuencias de dígitos a buscar
    search_sequences = [
        '3104277553',  # Completo
        '104277553',   # Sin primer 3
        '4277553',     # Últimos 7
        '277553',      # Últimos 6
        '31042',       # Primeros 5
    ]
    
    print("Buscando secuencias de dígitos en todas las columnas...")
    print()
    
    try:
        # 1. Búsqueda en operator_call_data
        print("1. BÚSQUEDA EN OPERATOR_CALL_DATA:")
        print("-" * 35)
        
        for sequence in search_sequences:
            total_found = 0
            
            # Buscar en cada campo numérico
            number_fields = ['numero_origen', 'numero_destino', 'numero_objetivo']
            
            for field in number_fields:
                query = f"""
                    SELECT 
                        {field} as numero_encontrado,
                        fecha_hora_llamada,
                        mission_id,
                        celda_origen, celda_destino, celda_objetivo
                    FROM operator_call_data 
                    WHERE {field} LIKE '%{sequence}%'
                    ORDER BY fecha_hora_llamada
                    LIMIT 10
                """
                
                cursor = conn.execute(query)
                records = cursor.fetchall()
                
                if records:
                    print(f"  Secuencia '{sequence}' en campo '{field}': {len(records)} registros")
                    for record in records[:3]:  # Solo primeros 3
                        print(f"    {record['numero_encontrado']} - {record['fecha_hora_llamada']}")
                        print(f"    Celdas: {record['celda_origen']}, {record['celda_destino']}, {record['celda_objetivo']}")
                    total_found += len(records)
            
            if total_found == 0:
                print(f"  Secuencia '{sequence}': NO ENCONTRADA")
            print()
        
        # 2. Búsqueda en operator_cellular_data
        print("2. BÚSQUEDA EN OPERATOR_CELLULAR_DATA:")
        print("-" * 35)
        
        for sequence in search_sequences:
            query = f"""
                SELECT 
                    numero_telefono,
                    fecha_hora_inicio,
                    mission_id,
                    celda_id
                FROM operator_cellular_data 
                WHERE numero_telefono LIKE '%{sequence}%'
                ORDER BY fecha_hora_inicio
                LIMIT 10
            """
            
            cursor = conn.execute(query)
            records = cursor.fetchall()
            
            if records:
                print(f"  Secuencia '{sequence}': {len(records)} registros")
                for record in records[:3]:
                    print(f"    {record['numero_telefono']} - {record['fecha_hora_inicio']}")
                    print(f"    Celda: {record['celda_id']}")
            else:
                print(f"  Secuencia '{sequence}': NO ENCONTRADA")
        
        print()
        
        # 3. Verificar estructura de tablas
        print("3. VERIFICACIÓN DE ESTRUCTURA DE TABLAS:")
        print("-" * 40)
        
        # Mostrar esquema de operator_call_data
        cursor = conn.execute("PRAGMA table_info(operator_call_data)")
        call_columns = cursor.fetchall()
        
        print("Columnas en operator_call_data:")
        for col in call_columns:
            print(f"  {col['name']} ({col['type']})")
        
        print()
        
        # Mostrar esquema de operator_cellular_data
        cursor = conn.execute("PRAGMA table_info(operator_cellular_data)")
        cellular_columns = cursor.fetchall()
        
        print("Columnas en operator_cellular_data:")
        for col in cellular_columns:
            print(f"  {col['name']} ({col['type']})")
        
        print()
        
        # 4. Buscar en celdas también
        print("4. BÚSQUEDA EN CAMPOS DE CELDAS:")
        print("-" * 30)
        
        cell_fields = ['celda_origen', 'celda_destino', 'celda_objetivo', 'cellid_decimal']
        
        for sequence in ['53591', '52453']:  # Celdas mencionadas por Boris
            for field in cell_fields:
                query = f"""
                    SELECT 
                        numero_origen, numero_destino, numero_objetivo,
                        {field} as celda_encontrada,
                        fecha_hora_llamada
                    FROM operator_call_data 
                    WHERE {field} = '{sequence}'
                    ORDER BY fecha_hora_llamada
                    LIMIT 5
                """
                
                cursor = conn.execute(query)
                records = cursor.fetchall()
                
                if records:
                    print(f"  Celda '{sequence}' en campo '{field}': {len(records)} registros")
                    for record in records:
                        print(f"    Números: {record['numero_origen']}, {record['numero_destino']}, {record['numero_objetivo']}")
                        print(f"    Fecha: {record['fecha_hora_llamada']}")
        
        # 5. Mostrar algunos números de ejemplo para comparar formato
        print("\n5. NÚMEROS DE EJEMPLO EN BASE DE DATOS:")
        print("-" * 40)
        
        cursor = conn.execute("""
            SELECT DISTINCT numero_origen 
            FROM operator_call_data 
            WHERE numero_origen IS NOT NULL 
            ORDER BY numero_origen 
            LIMIT 10
        """)
        
        sample_numbers = cursor.fetchall()
        print("Primeros 10 números origen:")
        for num in sample_numbers:
            print(f"  {num['numero_origen']}")
    
    except Exception as e:
        print(f"Error en búsqueda: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    busqueda_exhaustiva()