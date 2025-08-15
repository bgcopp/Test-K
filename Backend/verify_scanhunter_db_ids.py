#!/usr/bin/env python3
"""
Verificar los valores de ID en la base de datos para SCANHUNTER
Comparar con los valores reales del archivo Excel
"""

import sqlite3
import json
from datetime import datetime

def verify_scanhunter_db_ids():
    """Verifica los IDs en la base de datos vs archivo Excel"""
    
    db_path = "kronos.db"
    
    print("=== VERIFICACION DE IDS EN BASE DE DATOS vs EXCEL ===")
    print(f"Base de datos: {db_path}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Valores esperados del archivo Excel
    expected_ids = [0, 12, 32]
    expected_counts = {0: 17, 12: 15, 32: 26}
    expected_total = 58
    
    print("VALORES ESPERADOS DEL ARCHIVO EXCEL:")
    print(f"  IDs únicos: {expected_ids}")
    print(f"  Total registros: {expected_total}")
    for id_val, count in expected_counts.items():
        print(f"  ID {id_val}: {count} registros")
    
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cellular_data'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("\nERROR: La tabla 'cellular_data' no existe en la base de datos")
            conn.close()
            return
        
        # Obtener información de la tabla
        cursor.execute("SELECT COUNT(*) FROM cellular_data")
        total_db_records = cursor.fetchone()[0]
        
        print(f"\nVALORES EN LA BASE DE DATOS:")
        print(f"  Total registros en DB: {total_db_records}")
        
        # Obtener IDs únicos
        cursor.execute("SELECT DISTINCT file_record_id FROM cellular_data ORDER BY file_record_id")
        db_unique_ids = [row[0] for row in cursor.fetchall()]
        
        print(f"  IDs únicos en DB: {db_unique_ids}")
        
        # Contar registros por ID
        cursor.execute("""
            SELECT file_record_id, COUNT(*) 
            FROM cellular_data 
            GROUP BY file_record_id 
            ORDER BY file_record_id
        """)
        db_id_counts = dict(cursor.fetchall())
        
        print("  Distribución por ID en DB:")
        for id_val, count in db_id_counts.items():
            print(f"    ID {id_val}: {count} registros")
        
        # Comparación
        print(f"\nCOMPARACION:")
        print("-" * 40)
        
        # Total de registros
        if total_db_records == expected_total:
            print(f"[OK] Total registros: CORRECTO ({total_db_records})")
        else:
            print(f"[ERROR] Total registros: INCORRECTO (DB: {total_db_records}, Esperado: {expected_total})")
        
        # Filtrar valores None de db_unique_ids
        db_unique_ids_clean = [x for x in db_unique_ids if x is not None]
        
        # IDs únicos
        if set(db_unique_ids_clean) == set(expected_ids):
            print(f"[OK] IDs únicos: CORRECTO ({db_unique_ids_clean})")
        else:
            print(f"[ERROR] IDs únicos: INCORRECTO")
            print(f"    DB tiene: {db_unique_ids_clean}")
            print(f"    Esperado: {expected_ids}")
            print(f"    Faltantes: {set(expected_ids) - set(db_unique_ids_clean)}")
            print(f"    Extras: {set(db_unique_ids_clean) - set(expected_ids)}")
        
        # Conteos por ID
        counts_match = True
        for expected_id, expected_count in expected_counts.items():
            db_count = db_id_counts.get(expected_id, 0)
            if db_count == expected_count:
                print(f"[OK] ID {expected_id}: CORRECTO ({db_count} registros)")
            else:
                print(f"[ERROR] ID {expected_id}: INCORRECTO (DB: {db_count}, Esperado: {expected_count})")
                counts_match = False
        
        # Mostrar algunos registros de ejemplo
        print(f"\nEJEMPLOS DE REGISTROS EN DB:")
        print("-" * 40)
        cursor.execute("""
            SELECT file_record_id, punto, lat, lon 
            FROM cellular_data 
            ORDER BY file_record_id 
            LIMIT 10
        """)
        
        for row in cursor.fetchall():
            print(f"  ID: {row[0]}, Punto: {str(row[1])[:30]}..., Lat: {row[2]}, Lon: {row[3]}")
        
        # Conclusión
        print(f"\nCONCLUSION:")
        print("-" * 40)
        if set(db_unique_ids_clean) == set(expected_ids) and counts_match:
            print("[OK] Los datos en la base de datos coinciden con el archivo Excel")
        else:
            print("[ERROR] PROBLEMA DETECTADO: Los datos en la base de datos NO coinciden con el archivo Excel")
            print("  Necesitas ejecutar una migración para corregir los file_record_id")
            print(f"  Registros con file_record_id NULL: {db_id_counts.get(None, 0)}")
            print(f"  Esto sugiere cargas duplicadas o problemas en el procesamiento")
        
        conn.close()
        
    except Exception as e:
        print(f"ERROR al verificar la base de datos: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_scanhunter_db_ids()