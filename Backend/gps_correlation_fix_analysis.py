#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DIAGNÓSTICO CRÍTICO: PROBLEMA DE CORRELACIÓN GPS HUNTER
Análisis específico del problema de correlación entre cellular_data y operator_call_data
Author: Claude Code Assistant para Boris
Date: 2025-08-20
"""

import sqlite3
import pandas as pd
import json
from datetime import datetime

def diagnose_correlation_problem():
    """
    Diagnostica el problema específico de correlación GPS
    """
    print("=" * 80)
    print("DIAGNÓSTICO CRÍTICO: PROBLEMA CORRELACIÓN GPS HUNTER")
    print("=" * 80)
    print(f"Fecha análisis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Conectar a la base de datos
    conn = sqlite3.connect('kronos.db')
    cursor = conn.cursor()
    
    try:
        # 1. VERIFICAR ESTRUCTURA REAL DE AMBAS TABLAS
        print("1. VERIFICACIÓN DE ESTRUCTURAS DE TABLA:")
        print("-" * 50)
        
        # Cellular data
        cursor.execute("PRAGMA table_info(cellular_data)")
        cellular_columns = cursor.fetchall()
        print("CELLULAR_DATA:")
        for col in cellular_columns:
            if 'cell' in col[1].lower() or 'lat' in col[1].lower() or 'lon' in col[1].lower():
                print(f"  ★ {col[1]} ({col[2]})")
            else:
                print(f"    {col[1]} ({col[2]})")
        
        print("\nOPERATOR_CALL_DATA:")
        cursor.execute("PRAGMA table_info(operator_call_data)")
        operator_columns = cursor.fetchall()
        for col in operator_columns:
            if 'cell' in col[1].lower() or 'lat' in col[1].lower() or 'lon' in col[1].lower():
                print(f"  ★ {col[1]} ({col[2]})")
            else:
                print(f"    {col[1]} ({col[2]})")
        
        # 2. IDENTIFICAR CAMPOS DE CORRELACIÓN DISPONIBLES
        print("\n2. ANÁLISIS DE CAMPOS DE CORRELACIÓN:")
        print("-" * 50)
        
        cellular_cell_fields = []
        operator_cell_fields = []
        
        for col in cellular_columns:
            if 'cell' in col[1].lower():
                cellular_cell_fields.append(col[1])
        
        for col in operator_columns:
            if 'cell' in col[1].lower():
                operator_cell_fields.append(col[1])
        
        print(f"Campos CELL en cellular_data: {cellular_cell_fields}")
        print(f"Campos CELL en operator_call_data: {operator_cell_fields}")
        
        # 3. ANÁLISIS DE VALORES EN CAMPOS CELL
        print("\n3. ANÁLISIS DE VALORES CELL:")
        print("-" * 50)
        
        # Cellular data cell_id values
        cursor.execute("SELECT DISTINCT cell_id FROM cellular_data ORDER BY cell_id LIMIT 10")
        cellular_cell_samples = cursor.fetchall()
        print("Muestra cell_id en cellular_data:")
        for cell in cellular_cell_samples:
            print(f"  {cell[0]}")
        
        # Operator call data cell values
        for cell_field in operator_cell_fields:
            cursor.execute(f"SELECT DISTINCT {cell_field} FROM operator_call_data WHERE {cell_field} IS NOT NULL ORDER BY {cell_field} LIMIT 5")
            operator_cell_samples = cursor.fetchall()
            print(f"\nMuestra {cell_field} en operator_call_data:")
            for cell in operator_cell_samples:
                print(f"  {cell[0]}")
        
        # 4. BUSCAR POSIBLES CORRELACIONES
        print("\n4. BÚSQUEDA DE CORRELACIONES POSIBLES:")
        print("-" * 50)
        
        # Intentar correlacionar por diferentes campos
        for operator_field in operator_cell_fields:
            try:
                cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM cellular_data cd
                    INNER JOIN operator_call_data ocd ON cd.cell_id = ocd.{operator_field}
                """)
                
                correlation_count = cursor.fetchone()[0]
                print(f"Correlación cellular_data.cell_id ↔ operator_call_data.{operator_field}: {correlation_count} registros")
                
                if correlation_count > 0:
                    # Mostrar ejemplo de correlación exitosa
                    cursor.execute(f"""
                        SELECT cd.cell_id, cd.lat, cd.lon, ocd.{operator_field}
                        FROM cellular_data cd
                        INNER JOIN operator_call_data ocd ON cd.cell_id = ocd.{operator_field}
                        LIMIT 3
                    """)
                    
                    examples = cursor.fetchall()
                    print(f"  Ejemplos de correlación exitosa:")
                    for ex in examples:
                        print(f"    cell_id: {ex[0]} → lat: {ex[1]}, lon: {ex[2]} (via {operator_field}: {ex[3]})")
                        
            except Exception as e:
                print(f"Error al correlacionar con {operator_field}: {e}")
        
        # 5. VERIFICAR SI HAY cellid_decimal
        print("\n5. ANÁLISIS ESPECÍFICO cellid_decimal:")
        print("-" * 50)
        
        try:
            cursor.execute("SELECT DISTINCT cellid_decimal FROM operator_call_data WHERE cellid_decimal IS NOT NULL LIMIT 10")
            cellid_decimal_samples = cursor.fetchall()
            print("Muestras cellid_decimal en operator_call_data:")
            for cell in cellid_decimal_samples:
                print(f"  {cell[0]}")
            
            # Intentar correlación directa
            cursor.execute("""
                SELECT COUNT(*) 
                FROM cellular_data cd
                INNER JOIN operator_call_data ocd ON CAST(cd.cell_id AS INTEGER) = ocd.cellid_decimal
            """)
            
            direct_correlation = cursor.fetchone()[0]
            print(f"\nCorrelación directa cellular_data.cell_id ↔ operator_call_data.cellid_decimal: {direct_correlation}")
            
            if direct_correlation > 0:
                cursor.execute("""
                    SELECT cd.cell_id, cd.lat, cd.lon, ocd.cellid_decimal, ocd.numero_origen, ocd.numero_destino
                    FROM cellular_data cd
                    INNER JOIN operator_call_data ocd ON CAST(cd.cell_id AS INTEGER) = ocd.cellid_decimal
                    LIMIT 5
                """)
                
                successful_examples = cursor.fetchall()
                print("CORRELACIÓN EXITOSA - Ejemplos:")
                for ex in successful_examples:
                    print(f"  ★ HUNTER cell_id: {ex[0]} → GPS: ({ex[1]}, {ex[2]}) ← Call: {ex[4]} → {ex[5]}")
                    
        except Exception as e:
            print(f"Error en análisis cellid_decimal: {e}")
        
        # 6. REVISAR CONSULTA ACTUAL DEL BACKEND
        print("\n6. SIMULACIÓN CONSULTA BACKEND ACTUAL:")
        print("-" * 50)
        
        # Simular la consulta que debería estar usando el backend
        try:
            simulated_query = """
                SELECT 
                    ocd.numero_origen as caller_id,
                    ocd.numero_destino as target_id,
                    ocd.cellid_decimal,
                    cd.lat as lat_hunter,
                    cd.lon as lon_hunter,
                    cd.punto as punto_hunter
                FROM operator_call_data ocd
                LEFT JOIN cellular_data cd ON CAST(cd.cell_id AS INTEGER) = ocd.cellid_decimal
                WHERE ocd.mission_id = (SELECT mission_id FROM operator_call_data LIMIT 1)
                LIMIT 5
            """
            
            cursor.execute(simulated_query)
            simulated_results = cursor.fetchall()
            
            print("Resultados simulación consulta backend:")
            for row in simulated_results:
                print(f"  Origen: {row[0]} → Destino: {row[1]}")
                print(f"  Cell: {row[2]} → GPS: ({row[3]}, {row[4]}) Punto: {row[5]}")
                print()
            
        except Exception as e:
            print(f"Error en simulación consulta backend: {e}")
            
        # 7. DIAGNÓSTICO FINAL
        print("\n7. DIAGNÓSTICO FINAL:")
        print("-" * 50)
        
        # Verificar si el problema está en el backend o en los datos
        cursor.execute("SELECT COUNT(*) FROM cellular_data WHERE lat IS NOT NULL AND lon IS NOT NULL")
        valid_gps_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM operator_call_data WHERE cellid_decimal IS NOT NULL")
        valid_cellid_count = cursor.fetchone()[0]
        
        print(f"✓ Registros cellular_data con GPS válido: {valid_gps_count}")
        print(f"✓ Registros operator_call_data con cellid_decimal: {valid_cellid_count}")
        
        # Test final de correlación
        cursor.execute("""
            SELECT COUNT(*) 
            FROM operator_call_data ocd
            LEFT JOIN cellular_data cd ON CAST(cd.cell_id AS INTEGER) = ocd.cellid_decimal
            WHERE cd.lat IS NOT NULL AND cd.lon IS NOT NULL
        """)
        
        final_correlation_count = cursor.fetchone()[0]
        print(f"✓ Correlaciones exitosas con GPS: {final_correlation_count}")
        
        if final_correlation_count == 0:
            print("\n🚨 PROBLEMA IDENTIFICADO: No hay correlación entre las tablas")
            print("   Posibles causas:")
            print("   - Campo de correlación incorrecto en el backend")
            print("   - Formato de datos incompatible")
            print("   - Consulta SQL incorrecta")
        else:
            print(f"\n✅ DATOS DISPONIBLES: {final_correlation_count} registros correlacionables")
            print("   El problema está en la consulta del backend o en el frontend")
    
    except Exception as e:
        print(f"ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()
    
    print("\n" + "=" * 80)
    print("DIAGNÓSTICO COMPLETADO")
    print("=" * 80)

if __name__ == "__main__":
    diagnose_correlation_problem()