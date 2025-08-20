#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INVESTIGACIÓN CRÍTICA: DIAGNÓSTICO GPS HUNTER - KRONOS
Análisis específico de coordenadas GPS en tabla cellular_data
Author: Claude Code Assistant para Boris
Date: 2025-08-20
"""

import sqlite3
import pandas as pd
import json
from datetime import datetime

def analyze_gps_data():
    """
    Análisis exhaustivo de datos GPS en cellular_data
    """
    print("=" * 80)
    print("INVESTIGACIÓN CRÍTICA: COORDENADAS GPS HUNTER - KRONOS")
    print("=" * 80)
    print(f"Fecha análisis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Conectar a la base de datos
    conn = sqlite3.connect('kronos.db')
    cursor = conn.cursor()
    
    try:
        # 1. ANÁLISIS DE ESTRUCTURA DE TABLA cellular_data
        print("1. ESTRUCTURA DE TABLA cellular_data:")
        print("-" * 50)
        
        cursor.execute("PRAGMA table_info(cellular_data)")
        columns = cursor.fetchall()
        
        print("Columnas encontradas:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]}) - NotNull: {bool(col[3])} - Default: {col[4]}")
        
        # Verificar si existen columnas GPS específicas
        gps_columns = []
        for col in columns:
            col_name = col[1].lower()
            if any(term in col_name for term in ['lat', 'lon', 'gps', 'coord']):
                gps_columns.append(col[1])
        
        print(f"\nColumnas relacionadas con GPS encontradas: {gps_columns}")
        print()
        
        # 2. CONTEO TOTAL DE REGISTROS
        print("2. ANÁLISIS DE REGISTROS:")
        print("-" * 50)
        
        cursor.execute("SELECT COUNT(*) FROM cellular_data")
        total_records = cursor.fetchone()[0]
        print(f"Total de registros en cellular_data: {total_records}")
        
        # 3. ANÁLISIS ESPECÍFICO DE COORDENADAS GPS
        if gps_columns:
            for gps_col in gps_columns:
                cursor.execute(f"SELECT COUNT(*) FROM cellular_data WHERE {gps_col} IS NOT NULL AND {gps_col} != ''")
                non_null_count = cursor.fetchone()[0]
                print(f"Registros con {gps_col} válido: {non_null_count}")
        
        # 4. MUESTRA DE DATOS GPS REALES
        print("\n3. MUESTRA DE DATOS GPS REALES:")
        print("-" * 50)
        
        # Buscar todas las columnas que podrían contener coordenadas
        all_columns = [col[1] for col in columns]
        gps_query_columns = []
        
        for col in all_columns:
            if any(term in col.lower() for term in ['lat', 'lon', 'coord', 'gps']):
                gps_query_columns.append(col)
        
        if gps_query_columns:
            query_cols = ", ".join(gps_query_columns)
            cursor.execute(f"""
                SELECT cell_id, {query_cols}
                FROM cellular_data 
                WHERE ({" IS NOT NULL OR ".join(gps_query_columns)} IS NOT NULL)
                LIMIT 10
            """)
            
            sample_data = cursor.fetchall()
            print("Muestra de registros con coordenadas GPS:")
            for row in sample_data:
                print(f"  Cell ID: {row[0]} - GPS Data: {row[1:]}")
        
        # 5. ANÁLISIS DE CORRELACIÓN CON operator_call_data
        print("\n4. ANÁLISIS DE CORRELACIÓN TABLES:")
        print("-" * 50)
        
        # Verificar estructura de operator_call_data
        cursor.execute("PRAGMA table_info(operator_call_data)")
        operator_columns = cursor.fetchall()
        
        print("Columnas en operator_call_data:")
        for col in operator_columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Verificar correlación por cell_id
        cursor.execute("""
            SELECT COUNT(*) 
            FROM cellular_data cd
            INNER JOIN operator_call_data ocd ON cd.cell_id = ocd.cell_id
        """)
        
        correlated_records = cursor.fetchone()[0]
        print(f"\nRegistros correlacionados entre ambas tablas: {correlated_records}")
        
        # 6. SIMULACIÓN DE CONSULTA get_call_interactions
        print("\n5. SIMULACIÓN CONSULTA get_call_interactions:")
        print("-" * 50)
        
        # Intentar reproducir la consulta que debería retornar GPS
        test_query = """
            SELECT 
                ocd.caller_id,
                ocd.target_id,
                ocd.cell_id,
                cd.latitude,
                cd.longitude,
                cd.lat,
                cd.lon
            FROM operator_call_data ocd
            LEFT JOIN cellular_data cd ON ocd.cell_id = cd.cell_id
            LIMIT 5
        """
        
        try:
            cursor.execute(test_query)
            test_results = cursor.fetchall()
            
            print("Resultados de consulta simulada:")
            for row in test_results:
                print(f"  Caller: {row[0]}, Target: {row[1]}, Cell: {row[2]}")
                print(f"  GPS: lat={row[3]}, lon={row[4]}, lat2={row[5]}, lon2={row[6]}")
        except Exception as e:
            print(f"Error en consulta simulada: {e}")
            
            # Intentar con nombres alternativos de columnas
            cursor.execute("SELECT name FROM pragma_table_info('cellular_data') WHERE name LIKE '%lat%' OR name LIKE '%lon%'")
            potential_gps_cols = cursor.fetchall()
            print(f"Columnas potenciales GPS: {[col[0] for col in potential_gps_cols]}")
        
        # 7. VERIFICACIÓN DE VALORES ESPECÍFICOS
        print("\n6. VERIFICACIÓN VALORES ESPECÍFICOS:")
        print("-" * 50)
        
        # Buscar registros con valores GPS no nulos
        cursor.execute("SELECT name FROM pragma_table_info('cellular_data')")
        all_cellular_columns = [row[0] for row in cursor.fetchall()]
        
        gps_related = [col for col in all_cellular_columns if any(term in col.lower() for term in ['lat', 'lon', 'coord', 'gps'])]
        
        if gps_related:
            for col in gps_related:
                cursor.execute(f"""
                    SELECT {col}, COUNT(*) as count
                    FROM cellular_data 
                    WHERE {col} IS NOT NULL AND {col} != '' AND {col} != '0'
                    GROUP BY {col}
                    ORDER BY count DESC
                    LIMIT 5
                """)
                
                values = cursor.fetchall()
                print(f"\nValores más frecuentes en {col}:")
                for val, count in values:
                    print(f"  {val}: {count} registros")
    
    except Exception as e:
        print(f"ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()
    
    print("\n" + "=" * 80)
    print("INVESTIGACIÓN COMPLETADA")
    print("=" * 80)

if __name__ == "__main__":
    analyze_gps_data()