#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DIAGNÓSTICO GPS HUNTER - ANÁLISIS SIMPLIFICADO
Author: Claude Code Assistant para Boris
Date: 2025-08-20
"""

import sqlite3
import sys

def diagnose_gps_correlation():
    """
    Diagnóstico simplificado del problema GPS
    """
    print("=" * 60)
    print("DIAGNOSTICO GPS HUNTER - KRONOS")
    print("=" * 60)
    
    conn = sqlite3.connect('kronos.db')
    cursor = conn.cursor()
    
    try:
        # 1. Verificar datos GPS en cellular_data
        print("1. VERIFICACION DATOS GPS:")
        print("-" * 30)
        
        cursor.execute("SELECT COUNT(*) FROM cellular_data WHERE lat IS NOT NULL AND lon IS NOT NULL")
        gps_count = cursor.fetchone()[0]
        print(f"Registros con GPS en cellular_data: {gps_count}")
        
        cursor.execute("SELECT cell_id, lat, lon FROM cellular_data LIMIT 5")
        gps_samples = cursor.fetchall()
        print("Muestra datos GPS:")
        for row in gps_samples:
            print(f"  Cell: {row[0]} -> GPS: ({row[1]}, {row[2]})")
        
        # 2. Verificar estructura operator_call_data
        print("\n2. VERIFICACION OPERATOR_CALL_DATA:")
        print("-" * 30)
        
        cursor.execute("PRAGMA table_info(operator_call_data)")
        operator_cols = cursor.fetchall()
        
        cell_fields = []
        for col in operator_cols:
            if 'cell' in col[1].lower():
                cell_fields.append(col[1])
        
        print(f"Campos CELL encontrados: {cell_fields}")
        
        # 3. Probar correlación con cellid_decimal
        print("\n3. PRUEBA CORRELACION:")
        print("-" * 30)
        
        if 'cellid_decimal' in [col[1] for col in operator_cols]:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM operator_call_data ocd
                INNER JOIN cellular_data cd ON CAST(cd.cell_id AS INTEGER) = ocd.cellid_decimal
                WHERE cd.lat IS NOT NULL
            """)
            
            correlation_count = cursor.fetchone()[0]
            print(f"Correlaciones exitosas: {correlation_count}")
            
            if correlation_count > 0:
                cursor.execute("""
                    SELECT ocd.numero_origen, ocd.numero_destino, cd.cell_id, cd.lat, cd.lon
                    FROM operator_call_data ocd
                    INNER JOIN cellular_data cd ON CAST(cd.cell_id AS INTEGER) = ocd.cellid_decimal
                    WHERE cd.lat IS NOT NULL
                    LIMIT 3
                """)
                
                examples = cursor.fetchall()
                print("Ejemplos correlacion exitosa:")
                for ex in examples:
                    print(f"  {ex[0]} -> {ex[1]} | Cell: {ex[2]} | GPS: ({ex[3]}, {ex[4]})")
            else:
                print("NO HAY CORRELACIONES EXITOSAS")
                
                # Investigar por qué no correlaciona
                cursor.execute("SELECT DISTINCT cellid_decimal FROM operator_call_data WHERE cellid_decimal IS NOT NULL LIMIT 5")
                operator_cells = cursor.fetchall()
                print("Muestras cellid_decimal:")
                for cell in operator_cells:
                    print(f"  {cell[0]}")
                
                cursor.execute("SELECT DISTINCT cell_id FROM cellular_data LIMIT 5")
                cellular_cells = cursor.fetchall()
                print("Muestras cell_id cellular_data:")
                for cell in cellular_cells:
                    print(f"  {cell[0]}")
        
        # 4. Verificar consulta actual del backend
        print("\n4. SIMULACION CONSULTA BACKEND:")
        print("-" * 30)
        
        # Buscar el archivo del servicio de correlación
        try:
            # Simular consulta que debería usar el backend
            test_query = """
                SELECT 
                    ocd.numero_origen,
                    ocd.numero_destino,
                    ocd.cellid_decimal,
                    cd.lat,
                    cd.lon
                FROM operator_call_data ocd
                LEFT JOIN cellular_data cd ON CAST(cd.cell_id AS INTEGER) = ocd.cellid_decimal
                LIMIT 5
            """
            
            cursor.execute(test_query)
            results = cursor.fetchall()
            
            print("Resultados simulacion:")
            for row in results:
                if row[3] is not None and row[4] is not None:
                    print(f"  EXITOSO: {row[0]} -> {row[1]} | GPS: ({row[3]}, {row[4]})")
                else:
                    print(f"  SIN GPS: {row[0]} -> {row[1]} | Cell: {row[2]} | GPS: None")
                    
        except Exception as e:
            print(f"Error en simulacion: {e}")
    
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    diagnose_gps_correlation()