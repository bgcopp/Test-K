#!/usr/bin/env python3
"""
Verificar datos existentes en kronos.db
Boris 2025-08-18
"""

import sqlite3
import sys
import os

def main():
    db_path = "kronos.db"
    
    if not os.path.exists(db_path):
        print(f"Base de datos {db_path} no existe")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar tablas disponibles
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print("Tablas disponibles:")
        for table in sorted(tables):
            print(f"  - {table}")
        
        # Verificar misiones
        if 'missions' in tables:
            cursor.execute("SELECT id, name FROM missions")
            missions = cursor.fetchall()
            print(f"\nMisiones ({len(missions)}):")
            for mission_id, name in missions:
                print(f"  - {mission_id}: {name}")
        
        # Verificar datos de operador
        operator_tables = [t for t in tables if 'operator' in t.lower() or 'call' in t.lower()]
        print(f"\nTablas relacionadas con operadores: {operator_tables}")
        
        for table in operator_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  - {table}: {count} registros")
                
                if count > 0:
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = [col[1] for col in cursor.fetchall()]
                    print(f"    Columnas: {', '.join(columns[:5])}{'...' if len(columns) > 5 else ''}")
            except Exception as e:
                print(f"  - {table}: Error - {e}")
        
        # Verificar datos celulares
        if 'cellular_data' in tables:
            cursor.execute("SELECT COUNT(*) FROM cellular_data")
            count = cursor.fetchone()[0]
            print(f"\nDatos celulares: {count} registros")
            
            if count > 0:
                cursor.execute("SELECT DISTINCT mission_id FROM cellular_data LIMIT 5")
                mission_ids = [row[0] for row in cursor.fetchall()]
                print(f"  Misiones con datos celulares: {mission_ids}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error verificando datos: {e}")

if __name__ == "__main__":
    main()