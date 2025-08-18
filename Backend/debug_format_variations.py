#!/usr/bin/env python3
"""
ANALISIS DE VARIACIONES DE FORMATO - Numeros faltantes
======================================================
Buscar variaciones de formato de los numeros objetivo
"""

import sqlite3
import os
from typing import List

# Lista de numeros objetivo
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

def generate_format_variations(number: str) -> List[str]:
    """Generar variaciones de formato para un numero."""
    variations = []
    
    # Formato original
    variations.append(number)
    
    # Con prefijo 57 (Colombia)
    variations.append(f"57{number}")
    
    # Con +57
    variations.append(f"+57{number}")
    
    # Con +57 y espacio
    variations.append(f"+57 {number}")
    
    # Sin el primer digito (por si es prefijo)
    if len(number) > 9:
        variations.append(number[1:])
    
    # Con guiones
    if len(number) >= 10:
        variations.append(f"{number[:3]}-{number[3:6]}-{number[6:]}")
        variations.append(f"{number[:3]} {number[3:6]} {number[6:]}")
    
    # Como entero (sin ceros a la izquierda)
    variations.append(str(int(number)))
    
    return variations

def search_format_variations():
    """Buscar todas las variaciones de formato."""
    print("ANALISIS DE VARIACIONES DE FORMATO")
    print("=" * 50)
    
    with get_db_connection() as conn:
        for number in MISSING_NUMBERS:
            print(f"\nAnalizando variaciones para: {number}")
            
            variations = generate_format_variations(number)
            found_variations = []
            
            for variation in variations:
                # Buscar en operator_call_data
                call_query = """
                    SELECT COUNT(*) as count
                    FROM operator_call_data 
                    WHERE numero_origen LIKE ? OR numero_destino LIKE ? OR numero_objetivo LIKE ?
                """
                
                # Buscar exacto y con wildcards
                search_patterns = [variation, f"%{variation}%", f"{variation}%", f"%{variation}"]
                
                for pattern in search_patterns:
                    cursor = conn.execute(call_query, (pattern, pattern, pattern))
                    result = cursor.fetchone()
                    
                    if result['count'] > 0:
                        found_variations.append({
                            'variation': variation,
                            'pattern': pattern,
                            'count': result['count'],
                            'table': 'operator_call_data'
                        })
                
                # Buscar en operator_cellular_data
                cellular_query = """
                    SELECT COUNT(*) as count
                    FROM operator_cellular_data 
                    WHERE numero_telefono LIKE ?
                """
                
                for pattern in search_patterns:
                    cursor = conn.execute(cellular_query, (pattern,))
                    result = cursor.fetchone()
                    
                    if result['count'] > 0:
                        found_variations.append({
                            'variation': variation,
                            'pattern': pattern,
                            'count': result['count'],
                            'table': 'operator_cellular_data'
                        })
            
            if found_variations:
                print(f"  ENCONTRADO en variaciones:")
                for var in found_variations:
                    print(f"    {var['variation']} (patron: {var['pattern']}) -> {var['count']} en {var['table']}")
            else:
                print(f"  NO ENCONTRADO en ninguna variacion")

def check_partial_matches():
    """Buscar coincidencias parciales."""
    print(f"\n\nANALISIS DE COINCIDENCIAS PARCIALES")
    print("=" * 50)
    
    with get_db_connection() as conn:
        for number in MISSING_NUMBERS:
            print(f"\nBuscando coincidencias parciales para: {number}")
            
            # Buscar por ultimos 7 digitos (numero local)
            last_7 = number[-7:]
            last_8 = number[-8:]
            first_3 = number[:3]
            
            patterns_to_check = [
                (f"%{last_7}", f"ultimos 7 digitos: {last_7}"),
                (f"%{last_8}", f"ultimos 8 digitos: {last_8}"),
                (f"{first_3}%", f"primeros 3 digitos: {first_3}")
            ]
            
            for pattern, description in patterns_to_check:
                query = """
                    SELECT numero_origen, numero_destino, numero_objetivo, operator, fecha_hora_llamada
                    FROM operator_call_data 
                    WHERE numero_origen LIKE ? OR numero_destino LIKE ? OR numero_objetivo LIKE ?
                    LIMIT 3
                """
                
                cursor = conn.execute(query, (pattern, pattern, pattern))
                matches = cursor.fetchall()
                
                if matches:
                    print(f"  Coincidencias por {description}:")
                    for match in matches:
                        nums = [match['numero_origen'], match['numero_destino'], match['numero_objetivo']]
                        matching_nums = [n for n in nums if n and pattern.replace('%', '') in str(n)]
                        print(f"    Numeros: {matching_nums}, Operador: {match['operator']}, Fecha: {match['fecha_hora_llamada']}")

if __name__ == "__main__":
    search_format_variations()
    check_partial_matches()