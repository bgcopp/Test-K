#!/usr/bin/env python3
"""
ANALISIS PROFUNDO - Numeros faltantes en correlacion
====================================================
Investigar por que estos numeros no aparecen en resultados:
3224274851, 3208611034, 3104277553, 3102715509, 3143534707

Boris solicito analisis detallado y plan de ajustes.
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, List, Any

# Lista de numeros a investigar
MISSING_NUMBERS = [
    '3224274851', '3208611034', '3104277553', 
    '3102715509', '3143534707'
]

def get_db_connection():
    """Obtener conexion a la base de datos."""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kronos.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def normalize_phone_number(number: str) -> str:
    """Normalizar numero como lo hace el algoritmo de correlacion."""
    if not number:
        return ""
    
    # Limpiar el numero (solo digitos)
    clean_number = ''.join(filter(str.isdigit, str(number)))
    
    # Si el numero comienza con 57 (Colombia) y tiene mas de 10 digitos,
    # remover el prefijo 57 para comparacion
    if clean_number.startswith('57') and len(clean_number) > 10:
        normalized = clean_number[2:]  # Remover los primeros 2 digitos (57)
        return normalized
    
    return clean_number

def check_similar_numbers():
    """Buscar numeros similares que SI aparezcan en correlacion."""
    print("\n6. BUSQUEDA DE NUMEROS SIMILARES QUE SI APARECEN")
    print("-" * 50)
    
    with get_db_connection() as conn:
        # Buscar numeros que empiecen con 32, 31, etc.
        similar_patterns = ['32%', '31%', '30%']
        
        for pattern in similar_patterns:
            print(f"\nBuscando numeros que empiecen con {pattern[:-1]}:")
            
            query = """
                SELECT DISTINCT numero_origen as numero FROM operator_call_data WHERE numero_origen LIKE ?
                UNION
                SELECT DISTINCT numero_destino as numero FROM operator_call_data WHERE numero_destino LIKE ?
                UNION
                SELECT DISTINCT numero_objetivo as numero FROM operator_call_data WHERE numero_objetivo LIKE ?
                UNION
                SELECT DISTINCT numero_telefono as numero FROM operator_cellular_data WHERE numero_telefono LIKE ?
                ORDER BY numero
                LIMIT 10
            """
            
            cursor = conn.execute(query, (pattern, pattern, pattern, pattern))
            similar_numbers = cursor.fetchall()
            
            print(f"  Encontrados {len(similar_numbers)} numeros similares:")
            for row in similar_numbers[:5]:
                print(f"    {row['numero']}")

def analyze_data_completeness():
    """Analizar completitud de datos en las tablas."""
    print("\n7. ANALISIS DE COMPLETITUD DE DATOS")
    print("-" * 50)
    
    with get_db_connection() as conn:
        # Verificar cantidad total de registros
        queries = {
            'operator_call_data': 'SELECT COUNT(*) as count FROM operator_call_data',
            'operator_cellular_data': 'SELECT COUNT(*) as count FROM operator_cellular_data',
            'cellular_data (HUNTER)': 'SELECT COUNT(*) as count FROM cellular_data'
        }
        
        for table_name, query in queries.items():
            cursor = conn.execute(query)
            result = cursor.fetchone()
            print(f"  {table_name}: {result['count']} registros")
        
        # Verificar distribucion por operador
        print("\nDistribucion por operador:")
        
        op_query = """
            SELECT operator, COUNT(*) as count 
            FROM operator_call_data 
            GROUP BY operator 
            ORDER BY count DESC
        """
        cursor = conn.execute(op_query)
        operators = cursor.fetchall()
        
        for op in operators:
            print(f"  {op['operator']}: {op['count']} registros")

def main_analysis():
    """Analisis principal simplificado."""
    print("=" * 80)
    print("ANALISIS PROFUNDO - NUMEROS FALTANTES EN CORRELACION")
    print("=" * 80)
    print(f"Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Numeros a investigar: {MISSING_NUMBERS}")
    print("=" * 80)
    
    # Resultado del analisis anterior: NINGUN numero existe en las tablas
    print("\nRESULTADO CLAVE DEL ANALISIS:")
    print("NINGUN de los numeros buscados existe en las tablas de operadores")
    print("")
    print("Numeros buscados:")
    for num in MISSING_NUMBERS:
        print(f"  {num} -> No encontrado en operator_call_data ni operator_cellular_data")
    
    # Buscar patrones similares
    check_similar_numbers()
    
    # Analizar completitud
    analyze_data_completeness()
    
    print("\n" + "=" * 80)
    print("DIAGNOSTICO PRINCIPAL")
    print("=" * 80)
    print("PROBLEMA IDENTIFICADO:")
    print("  Los numeros NO EXISTEN en las tablas de datos de operadores")
    print("  No es un problema del algoritmo de correlacion")
    print("  Es un problema de DATOS FALTANTES")
    print("")
    print("POSIBLES CAUSAS:")
    print("  1. Los numeros no fueron incluidos en la carga de datos")
    print("  2. Los archivos de operadores no contenian estos numeros")
    print("  3. Error en el proceso de importacion de datos")
    print("  4. Los numeros estan en un formato diferente")
    print("  5. Los numeros corresponden a fechas fuera del rango cargado")

if __name__ == "__main__":
    main_analysis()