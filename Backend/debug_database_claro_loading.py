#!/usr/bin/env python3
"""
Script para VERIFICAR qué números se cargan realmente en la base de datos
y encontrar el problema crítico de números faltantes en CLARO.

Autor: Sistema KRONOS - Verificación crítica de DB
"""

import sqlite3
import pandas as pd
import sys
import os
from pathlib import Path

# Añadir el path del backend para importar servicios
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import get_db_connection

def verify_claro_database_loading():
    """Verifica qué números están realmente en la base de datos después de la carga"""
    
    print("=" * 80)
    print("VERIFICACION CRITICA: NUMEROS CLARO EN BASE DE DATOS")
    print("=" * 80)
    
    # Números objetivo que DEBEN aparecer
    target_numbers = ['3224274851', '3208611034', '3104277553', '3102715509', '3143534707', '3214161903']
    
    try:
        with get_db_connection() as conn:
            # === VERIFICAR DATOS DE LLAMADAS ===
            print("\n1. VERIFICANDO DATOS DE LLAMADAS EN BD:")
            print("-" * 50)
            
            # Contar total de registros de llamadas CLARO
            cursor = conn.execute("""
                SELECT COUNT(*) 
                FROM call_data 
                WHERE operator = 'CLARO'
            """)
            total_claro_calls = cursor.fetchone()[0]
            print(f"   Total registros CLARO en call_data: {total_claro_calls}")
            
            # Buscar números objetivo en call_data
            print("\n   Buscando números objetivo en call_data:")
            for target in target_numbers:
                # Buscar como número origen
                cursor = conn.execute("""
                    SELECT COUNT(*) 
                    FROM call_data 
                    WHERE operator = 'CLARO' 
                    AND numero_origen = ?
                """, (target,))
                count_origen = cursor.fetchone()[0]
                
                # Buscar como número destino
                cursor = conn.execute("""
                    SELECT COUNT(*) 
                    FROM call_data 
                    WHERE operator = 'CLARO' 
                    AND numero_destino = ?
                """, (target,))
                count_destino = cursor.fetchone()[0]
                
                # Buscar con prefijo 57
                target_with_57 = f"57{target}"
                cursor = conn.execute("""
                    SELECT COUNT(*) 
                    FROM call_data 
                    WHERE operator = 'CLARO' 
                    AND (numero_origen = ? OR numero_destino = ?)
                """, (target_with_57, target_with_57))
                count_with_57 = cursor.fetchone()[0]
                
                total_found = count_origen + count_destino + count_with_57
                print(f"     {target}: origen={count_origen}, destino={count_destino}, con_57={count_with_57}, total={total_found}")
                
                if total_found == 0:
                    print(f"       ❌ NUMERO OBJETIVO NO ENCONTRADO EN BD: {target}")
                else:
                    print(f"       ✅ Número encontrado en BD")
            
            # === VERIFICAR DATOS CELULARES ===
            print("\n2. VERIFICANDO DATOS CELULARES EN BD:")
            print("-" * 50)
            
            # Contar total de registros celulares CLARO
            cursor = conn.execute("""
                SELECT COUNT(*) 
                FROM cellular_data 
                WHERE operator = 'CLARO'
            """)
            total_claro_cellular = cursor.fetchone()[0]
            print(f"   Total registros CLARO en cellular_data: {total_claro_cellular}")
            
            # Buscar números objetivo en cellular_data
            print("\n   Buscando números objetivo en cellular_data:")
            for target in target_numbers:
                # Buscar sin prefijo
                cursor = conn.execute("""
                    SELECT COUNT(*) 
                    FROM cellular_data 
                    WHERE operator = 'CLARO' 
                    AND numero_telefono = ?
                """, (target,))
                count_normal = cursor.fetchone()[0]
                
                # Buscar con prefijo 57
                target_with_57 = f"57{target}"
                cursor = conn.execute("""
                    SELECT COUNT(*) 
                    FROM cellular_data 
                    WHERE operator = 'CLARO' 
                    AND numero_telefono = ?
                """, (target_with_57,))
                count_with_57 = cursor.fetchone()[0]
                
                total_found = count_normal + count_with_57
                print(f"     {target}: normal={count_normal}, con_57={count_with_57}, total={total_found}")
                
                if total_found == 0:
                    print(f"       ❌ NUMERO OBJETIVO NO ENCONTRADO EN BD: {target}")
                else:
                    print(f"       ✅ Número encontrado en BD")
            
            # === ANALIZAR PATRONES DE NÚMEROS EN BD ===
            print("\n3. ANALIZANDO PATRONES DE NUMEROS EN BD:")
            print("-" * 50)
            
            # Patrones en call_data
            print("   Patrones en call_data CLARO:")
            cursor = conn.execute("""
                SELECT 
                    SUM(CASE WHEN numero_origen LIKE '57%' THEN 1 ELSE 0 END) as origen_con_57,
                    SUM(CASE WHEN numero_origen LIKE '3%' AND numero_origen NOT LIKE '57%' THEN 1 ELSE 0 END) as origen_sin_57,
                    SUM(CASE WHEN numero_destino LIKE '57%' THEN 1 ELSE 0 END) as destino_con_57,
                    SUM(CASE WHEN numero_destino LIKE '3%' AND numero_destino NOT LIKE '57%' THEN 1 ELSE 0 END) as destino_sin_57
                FROM call_data 
                WHERE operator = 'CLARO'
            """)
            patterns = cursor.fetchone()
            print(f"     Números origen con 57: {patterns[0]}")
            print(f"     Números origen sin 57: {patterns[1]}")
            print(f"     Números destino con 57: {patterns[2]}")
            print(f"     Números destino sin 57: {patterns[3]}")
            
            # Patrones en cellular_data
            print("\\n   Patrones en cellular_data CLARO:")
            cursor = conn.execute("""
                SELECT 
                    SUM(CASE WHEN numero_telefono LIKE '57%' THEN 1 ELSE 0 END) as con_57,
                    SUM(CASE WHEN numero_telefono LIKE '3%' AND numero_telefono NOT LIKE '57%' THEN 1 ELSE 0 END) as sin_57
                FROM cellular_data 
                WHERE operator = 'CLARO'
            """)
            patterns = cursor.fetchone()
            print(f"     Números telefono con 57: {patterns[0]}")
            print(f"     Números telefono sin 57: {patterns[1]}")
            
            # === MUESTRAS DE NÚMEROS EN BD ===
            print("\\n4. MUESTRAS DE NUMEROS EN BD:")
            print("-" * 50)
            
            print("   Ejemplos de números en call_data CLARO:")
            cursor = conn.execute("""
                SELECT DISTINCT numero_origen 
                FROM call_data 
                WHERE operator = 'CLARO' 
                LIMIT 10
            """)
            ejemplos_origen = [row[0] for row in cursor.fetchall()]
            print(f"     Números origen: {ejemplos_origen}")
            
            cursor = conn.execute("""
                SELECT DISTINCT numero_destino 
                FROM call_data 
                WHERE operator = 'CLARO' 
                LIMIT 10
            """)
            ejemplos_destino = [row[0] for row in cursor.fetchall()]
            print(f"     Números destino: {ejemplos_destino}")
            
            print("\\n   Ejemplos de números en cellular_data CLARO:")
            cursor = conn.execute("""
                SELECT DISTINCT numero_telefono 
                FROM cellular_data 
                WHERE operator = 'CLARO' 
                LIMIT 10
            """)
            ejemplos_cellular = [row[0] for row in cursor.fetchall()]
            print(f"     Números telefono: {ejemplos_cellular}")
            
            # === BUSCAR NÚMEROS SIMILARES ===
            print("\\n5. BUSCANDO NUMEROS SIMILARES A OBJETIVOS:")
            print("-" * 50)
            
            for target in target_numbers:
                # Buscar números que empiecen con los primeros 6 dígitos
                prefix = target[:6]
                
                print(f"\\n   Buscando números similares a {target} (prefijo {prefix}):")
                
                # En call_data
                cursor = conn.execute("""
                    SELECT DISTINCT numero_origen 
                    FROM call_data 
                    WHERE operator = 'CLARO' 
                    AND (numero_origen LIKE ? OR numero_origen LIKE ?)
                    LIMIT 5
                """, (f"{prefix}%", f"57{prefix}%"))
                similares_origen = [row[0] for row in cursor.fetchall()]
                
                cursor = conn.execute("""
                    SELECT DISTINCT numero_destino 
                    FROM call_data 
                    WHERE operator = 'CLARO' 
                    AND (numero_destino LIKE ? OR numero_destino LIKE ?)
                    LIMIT 5
                """, (f"{prefix}%", f"57{prefix}%"))
                similares_destino = [row[0] for row in cursor.fetchall()]
                
                # En cellular_data
                cursor = conn.execute("""
                    SELECT DISTINCT numero_telefono 
                    FROM cellular_data 
                    WHERE operator = 'CLARO' 
                    AND (numero_telefono LIKE ? OR numero_telefono LIKE ?)
                    LIMIT 5
                """, (f"{prefix}%", f"57{prefix}%"))
                similares_cellular = [row[0] for row in cursor.fetchall()]
                
                todos_similares = list(set(similares_origen + similares_destino + similares_cellular))
                
                if todos_similares:
                    print(f"     Números similares encontrados: {todos_similares}")
                    # Verificar si alguno coincide exactamente
                    for similar in todos_similares:
                        if similar == target or similar == f"57{target}":
                            print(f"       ✅ COINCIDENCIA EXACTA: {similar}")
                else:
                    print(f"     ❌ NO SE ENCONTRARON NÚMEROS SIMILARES")
                    
    except Exception as e:
        print(f"ERROR conectando a la base de datos: {str(e)}")
        return
    
    print("\\n" + "=" * 80)
    print("VERIFICACION COMPLETADA")
    print("=" * 80)

if __name__ == "__main__":
    verify_claro_database_loading()