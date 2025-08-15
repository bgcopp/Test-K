#!/usr/bin/env python3
"""
Script para migrar datos existentes de cellular_data con file_record_id NULL
Asigna valores de file_record_id basados en el índice dentro de cada misión
"""

import sqlite3
import sys
from pathlib import Path

def migrate_cellular_data():
    """Migra datos de cellular_data existentes para agregar file_record_id"""
    
    # Path a la base de datos
    current_dir = Path(__file__).parent
    db_path = current_dir / 'kronos.db'
    
    if not db_path.exists():
        print(f"ERROR: Base de datos no encontrada: {db_path}")
        return False
    
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("Verificando datos existentes sin file_record_id...")
        
        # Verificar datos existentes sin file_record_id
        cursor.execute("""
            SELECT COUNT(*) 
            FROM cellular_data 
            WHERE file_record_id IS NULL
        """)
        null_count = cursor.fetchone()[0]
        
        print(f"Registros con file_record_id NULL: {null_count}")
        
        if null_count == 0:
            print("EXITO: No hay registros que migrar")
            conn.close()
            return True
        
        # Obtener todos los registros agrupados por misión
        cursor.execute("""
            SELECT id, mission_id 
            FROM cellular_data 
            WHERE file_record_id IS NULL
            ORDER BY mission_id, id
        """)
        records = cursor.fetchall()
        
        print(f"PROCESO: Migrando {len(records)} registros...")
        
        # Agrupar por misión y asignar file_record_id secuencial
        mission_counters = {}
        updates = []
        
        for record_id, mission_id in records:
            if mission_id not in mission_counters:
                mission_counters[mission_id] = 0
            
            file_record_id = mission_counters[mission_id]
            updates.append((file_record_id, record_id))
            mission_counters[mission_id] += 1
        
        # Ejecutar updates
        cursor.executemany("""
            UPDATE cellular_data 
            SET file_record_id = ? 
            WHERE id = ?
        """, updates)
        
        # Commit cambios
        conn.commit()
        
        # Verificar resultados
        cursor.execute("""
            SELECT COUNT(*) 
            FROM cellular_data 
            WHERE file_record_id IS NOT NULL
        """)
        updated_count = cursor.fetchone()[0]
        
        print(f"EXITO: Migracion completada")
        print(f"STATS: Registros actualizados: {len(updates)}")
        print(f"STATS: Total con file_record_id: {updated_count}")
        
        # Mostrar estadísticas por misión
        cursor.execute("""
            SELECT mission_id, COUNT(*) as count, MIN(file_record_id) as min_id, MAX(file_record_id) as max_id
            FROM cellular_data 
            WHERE file_record_id IS NOT NULL
            GROUP BY mission_id
        """)
        
        mission_stats = cursor.fetchall()
        print("\nEstadisticas por mision:")
        for mission_id, count, min_id, max_id in mission_stats:
            print(f"  Mision {mission_id}: {count} registros (IDs: {min_id}-{max_id})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"ERROR: Error durante migracion: {e}")
        if 'conn' in locals():
            conn.close()
        return False

if __name__ == '__main__':
    print("INICIO: Iniciando migracion de cellular_data...")
    success = migrate_cellular_data()
    
    if success:
        print("\nEXITO: Migracion completada exitosamente")
        sys.exit(0)
    else:
        print("\nERROR: Migracion fallo")
        sys.exit(1)