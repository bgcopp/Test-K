"""
MIGRACIÓN: Agregar campo file_record_id a la tabla cellular_data

Esta migración agrega el campo file_record_id para almacenar el ID original
del archivo fuente (ej: columna "Id" de SCANHUNTER.xlsx).

Esto permite:
1. Mostrar el ID del archivo en lugar del autoincremental de la BD
2. Ordenar por el ID original del archivo (ASC: 0, 12, 32)
3. Mantener la trazabilidad del origen de cada registro

Autor: Sistema KRONOS
Fecha: 2025-08-14
"""

import sqlite3
import os
import sys
from datetime import datetime

def run_migration():
    """Ejecuta la migración para agregar file_record_id a cellular_data"""
    
    db_path = os.path.join(os.path.dirname(__file__), 'kronos.db')
    
    print(f"=== MIGRACIÓN: Agregar file_record_id a cellular_data ===")
    print(f"Base de datos: {db_path}")
    print(f"Fecha: {datetime.now().isoformat()}")
    print()
    
    if not os.path.exists(db_path):
        print(f"ERROR: Base de datos no encontrada en {db_path}")
        return False
    
    # Crear respaldo antes de la migración
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"[OK] Respaldo creado: {backup_path}")
    except Exception as e:
        print(f"[WARN] Error creando respaldo: {e}")
        print("Continuando sin respaldo...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='cellular_data'
        """)
        
        if not cursor.fetchone():
            print("ERROR: Tabla cellular_data no existe")
            return False
        
        # Verificar si el campo ya existe
        cursor.execute("PRAGMA table_info(cellular_data)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'file_record_id' in columns:
            print("[OK] Campo file_record_id ya existe, migración no necesaria")
            return True
        
        print("[PROCESO] Agregando campo file_record_id...")
        
        # Agregar la nueva columna
        cursor.execute("""
            ALTER TABLE cellular_data 
            ADD COLUMN file_record_id INTEGER
        """)
        
        print("[OK] Campo file_record_id agregado exitosamente")
        
        # Crear el índice para el nuevo campo
        print("[PROCESO] Creando índices...")
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cellular_file_record_id 
            ON cellular_data(file_record_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cellular_mission_file_record 
            ON cellular_data(mission_id, file_record_id)
        """)
        
        print("[OK] Índices creados exitosamente")
        
        # Verificar el resultado
        cursor.execute("PRAGMA table_info(cellular_data)")
        columns = cursor.fetchall()
        
        print("\n[INFO] Estructura final de cellular_data:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})" + (" [NUEVO]" if col[1] == 'file_record_id' else ""))
        
        # Contar registros existentes
        cursor.execute("SELECT COUNT(*) FROM cellular_data")
        record_count = cursor.fetchone()[0]
        
        print(f"\n[INFO] Registros existentes: {record_count}")
        if record_count > 0:
            print("   [WARN] Los registros existentes tendrán file_record_id = NULL")
            print("   [INFO] Recomendación: Re-procesar archivos SCANHUNTER para poblar este campo")
        
        conn.commit()
        conn.close()
        
        print("\n[SUCCESS] MIGRACIÓN COMPLETADA EXITOSAMENTE")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] ERROR EN MIGRACIÓN: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def verify_migration():
    """Verifica que la migración se haya aplicado correctamente"""
    
    db_path = os.path.join(os.path.dirname(__file__), 'kronos.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar que el campo existe
        cursor.execute("PRAGMA table_info(cellular_data)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'file_record_id' not in columns:
            print("[ERROR] VERIFICACIÓN FALLÓ: Campo file_record_id no existe")
            return False
        
        # Verificar índices
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name IN ('idx_cellular_file_record_id', 'idx_cellular_mission_file_record')
        """)
        
        indices = [row[0] for row in cursor.fetchall()]
        expected_indices = ['idx_cellular_file_record_id', 'idx_cellular_mission_file_record']
        
        for idx in expected_indices:
            if idx not in indices:
                print(f"[WARN] Índice faltante: {idx}")
            else:
                print(f"[OK] Índice encontrado: {idx}")
        
        conn.close()
        print("[SUCCESS] VERIFICACIÓN EXITOSA")
        return True
        
    except Exception as e:
        print(f"[ERROR] ERROR EN VERIFICACIÓN: {e}")
        return False

if __name__ == "__main__":
    print("KRONOS - Migración de Base de Datos")
    print("===================================")
    
    if len(sys.argv) > 1 and sys.argv[1] == 'verify':
        verify_migration()
    else:
        success = run_migration()
        if success:
            verify_migration()
        else:
            sys.exit(1)