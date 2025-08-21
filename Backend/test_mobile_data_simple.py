#!/usr/bin/env python3
"""
Test Simple - Validacion Correccion Error SQL operator_cellular_data
CORRECCION BORIS 2025-08-20: ocd.operador -> ocd.operator as operador
"""

import sqlite3
import os

def main():
    print("=" * 50)
    print("TEST VALIDACION CORRECCION SQL")
    print("=" * 50)
    
    db_path = "kronos.db"
    if not os.path.exists(db_path):
        print("Base de datos no encontrada:", db_path)
        return 1
    
    # Test: Query corregida funciona sin error
    query = """
    SELECT 
        ocd.numero_telefono,
        ocd.operator as operador,
        ocd.celda_id
    FROM operator_cellular_data ocd
    WHERE ocd.mission_id = ? 
    LIMIT 1
    """
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, ['test'])
            print("EXITO: Query ejecutada sin errores")
            print("Campo 'operator' existe y es accesible")
            return 0
            
    except sqlite3.OperationalError as e:
        if "no such column: ocd.operador" in str(e):
            print("ERROR: Correccion no aplicada correctamente")
            print("Aun usa campo inexistente 'operador'")
        elif "no such column" in str(e):
            print("ERROR SQL:", e)
        else:
            print("Otro error SQL:", e)
        return 1
        
    except Exception as e:
        print("Error inesperado:", e)
        return 1

if __name__ == '__main__':
    exit(main())