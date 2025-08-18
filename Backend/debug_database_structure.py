#!/usr/bin/env python3
"""
Script para verificar la estructura de la base de datos y entender dónde se almacenan los datos CLARO.

Autor: Sistema KRONOS - Verificación de estructura DB
"""

import sqlite3
import sys
import os

# Añadir el path del backend para importar servicios
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import get_db_connection

def verify_database_structure():
    """Verifica la estructura de la base de datos para entender dónde buscar los datos CLARO"""
    
    print("=" * 80)
    print("VERIFICACION DE ESTRUCTURA DE BASE DE DATOS")
    print("=" * 80)
    
    try:
        with get_db_connection() as conn:
            # === LISTAR TODAS LAS TABLAS ===
            print("\n1. TABLAS EXISTENTES EN LA BASE DE DATOS:")
            print("-" * 50)
            
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                ORDER BY name
            """)
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                print(f"   - {table_name}")
                
                # Contar registros en cada tabla
                try:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    print(f"     Registros: {count}")
                except Exception as e:
                    print(f"     Error contando registros: {e}")
            
            # === BUSCAR TABLAS RELACIONADAS CON CLARO ===
            print("\n2. BUSCANDO DATOS RELACIONADOS CON CLARO:")
            print("-" * 50)
            
            # Verificar cada tabla para datos de CLARO
            for table in tables:
                table_name = table[0]
                print(f"\n   Analizando tabla: {table_name}")
                
                # Obtener estructura de la tabla
                cursor = conn.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                print(f"     Columnas: {column_names}")
                
                # Buscar columnas que podrían contener datos de operador
                operator_columns = [col for col in column_names if 'operator' in col.lower()]
                if operator_columns:
                    print(f"     Columnas de operador detectadas: {operator_columns}")
                    
                    # Verificar si hay datos de CLARO
                    for op_col in operator_columns:
                        try:
                            cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {op_col} = 'CLARO'")
                            claro_count = cursor.fetchone()[0]
                            print(f"       Registros CLARO en {op_col}: {claro_count}")
                            
                            if claro_count > 0:
                                # Obtener ejemplos de datos
                                cursor = conn.execute(f"SELECT * FROM {table_name} WHERE {op_col} = 'CLARO' LIMIT 3")
                                ejemplos = cursor.fetchall()
                                print(f"       Ejemplos de registros CLARO:")
                                for i, ejemplo in enumerate(ejemplos, 1):
                                    print(f"         Registro {i}: {dict(zip(column_names, ejemplo))}")
                        
                        except Exception as e:
                            print(f"       Error buscando CLARO en {op_col}: {e}")
                
                # Buscar columnas que podrían contener números telefónicos
                phone_columns = [col for col in column_names if any(keyword in col.lower() for keyword in ['numero', 'phone', 'telefono', 'origen', 'destino', 'originador', 'receptor'])]
                if phone_columns:
                    print(f"     Columnas de números detectadas: {phone_columns}")
                    
                    # Si hay pocos registros, mostrar algunos ejemplos
                    try:
                        cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                        total_count = cursor.fetchone()[0]
                        
                        if total_count > 0 and total_count <= 1000:  # Solo para tablas pequeñas
                            print(f"     Ejemplos de números en tabla {table_name}:")
                            for phone_col in phone_columns[:2]:  # Solo primeras 2 columnas
                                cursor = conn.execute(f"SELECT DISTINCT {phone_col} FROM {table_name} WHERE {phone_col} IS NOT NULL LIMIT 5")
                                examples = cursor.fetchall()
                                phone_examples = [row[0] for row in examples]
                                print(f"       {phone_col}: {phone_examples}")
                    
                    except Exception as e:
                        print(f"       Error obteniendo ejemplos: {e}")
            
            # === BUSCAR NÚMEROS OBJETIVO EN TODAS LAS TABLAS ===
            print("\n3. BUSCANDO NUMEROS OBJETIVO EN TODAS LAS TABLAS:")
            print("-" * 50)
            
            target_numbers = ['3224274851', '3208611034', '3104277553', '3102715509', '3143534707', '3214161903']
            
            for target in target_numbers:
                print(f"\n   Buscando número: {target}")
                target_variations = [target, f"57{target}", f"+57{target}"]
                
                found_in_tables = []
                
                for table in tables:
                    table_name = table[0]
                    
                    # Obtener columnas de la tabla
                    cursor = conn.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    
                    for col_info in columns:
                        col_name = col_info[1]
                        col_type = col_info[2]
                        
                        # Solo buscar en columnas que podrían contener números
                        if any(keyword in col_name.lower() for keyword in ['numero', 'phone', 'telefono', 'origen', 'destino', 'originador', 'receptor']) or 'TEXT' in col_type.upper():
                            try:
                                for variation in target_variations:
                                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {col_name} = ?", (variation,))
                                    count = cursor.fetchone()[0]
                                    
                                    if count > 0:
                                        found_in_tables.append(f"{table_name}.{col_name} ({variation}): {count}")
                            
                            except Exception as e:
                                # Ignorar errores de búsqueda en columnas incompatibles
                                pass
                
                if found_in_tables:
                    print(f"     OK - ENCONTRADO EN: {found_in_tables}")
                else:
                    print(f"     ERROR - NO ENCONTRADO EN NINGUNA TABLA")
                    
    except Exception as e:
        print(f"ERROR conectando a la base de datos: {str(e)}")
        return
    
    print("\n" + "=" * 80)
    print("VERIFICACION DE ESTRUCTURA COMPLETADA")
    print("=" * 80)

if __name__ == "__main__":
    verify_database_structure()