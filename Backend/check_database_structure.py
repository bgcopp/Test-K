#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificar estructura de la base de datos para encontrar los datos correctos
"""

import sqlite3
import sys

def check_database_structure():
    print("VERIFICANDO ESTRUCTURA DE BASE DE DATOS")
    print("=" * 50)
    
    conn = sqlite3.connect("kronos.db")
    cursor = conn.cursor()
    
    # Obtener todas las tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in cursor.fetchall()]
    
    print(f"Tablas encontradas: {tables}")
    
    # Analizar cada tabla para encontrar datos relevantes
    for table in tables:
        if table.startswith('sqlite_'):
            continue
            
        print(f"\n--- TABLA: {table} ---")
        
        # Obtener estructura de la tabla
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        print("Columnas:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Obtener conteo de registros
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"Total registros: {count}")
        
        # Si tiene columnas relacionadas con números telefónicos, mostrar muestra
        column_names = [col[1].lower() for col in columns]
        phone_related = ['origen', 'destino', 'numero', 'telefono', 'phone', 'number']
        
        if any(phone_col in column_names for phone_col in phone_related):
            print("TABLA RELEVANTE PARA NÚMEROS TELEFÓNICOS")
            
            # Buscar el número específico
            target_number = "3113330727"
            
            # Intentar diferentes nombres de columnas
            search_columns = []
            for col in columns:
                col_name = col[1].lower()
                if any(phone_col in col_name for phone_col in phone_related):
                    search_columns.append(col[1])
            
            if search_columns:
                print(f"Buscando {target_number} en columnas: {search_columns}")
                
                for search_col in search_columns:
                    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {search_col} = ?", (target_number,))
                    found_count = cursor.fetchone()[0]
                    if found_count > 0:
                        print(f"  ENCONTRADO en {search_col}: {found_count} registros")
                        
                        # Mostrar algunos registros de ejemplo
                        cursor.execute(f"SELECT * FROM {table} WHERE {search_col} = ? LIMIT 3", (target_number,))
                        samples = cursor.fetchall()
                        print("  Ejemplos:")
                        for sample in samples:
                            print(f"    {sample}")
    
    conn.close()

if __name__ == "__main__":
    check_database_structure()