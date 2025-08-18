#!/usr/bin/env python3
"""
DEBUG ESPECÍFICO - Número 3104277553
===================================
Boris confirma que este número existe en los datos:
- En celda 53591 llamando al 3224274851 
- Destino en celda 52453

Investigar por qué no aparece en extracción.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.correlation_analysis_service import CorrelationAnalysisService
import logging

logging.basicConfig(level=logging.WARNING)

def debug_numero_especifico():
    service = CorrelationAnalysisService()
    
    print("DEBUG ESPECÍFICO - Número 3104277553")
    print("=" * 50)
    
    mission_id = "mission_MPFRBNsb"
    target_number = "3104277553"
    
    # Probar diferentes formatos
    search_variants = [
        target_number,           # 3104277553
        f"57{target_number}",    # 573104277553
        f"+57{target_number}",   # +573104277553
        target_number[1:],       # 104277553 (sin primer dígito)
    ]
    
    print(f"Buscando número: {target_number}")
    print(f"Variantes a probar: {search_variants}")
    print()
    
    with service.get_db_connection() as conn:
        # 1. Búsqueda exhaustiva sin filtro de fecha
        print("1. BÚSQUEDA EXHAUSTIVA SIN FILTRO DE FECHA:")
        print("-" * 45)
        
        for variant in search_variants:
            search_query = """
                SELECT 
                    numero_origen, numero_destino, numero_objetivo,
                    celda_origen, celda_destino, celda_objetivo, cellid_decimal,
                    fecha_hora_llamada, operator, mission_id,
                    CASE 
                        WHEN numero_origen = ? THEN 'ORIGINADOR'
                        WHEN numero_destino = ? THEN 'RECEPTOR' 
                        WHEN numero_objetivo = ? THEN 'OBJETIVO'
                        ELSE 'OTRO'
                    END as rol_numero
                FROM operator_call_data
                WHERE numero_origen = ? OR numero_destino = ? OR numero_objetivo = ?
                ORDER BY fecha_hora_llamada
            """
            
            cursor = conn.execute(search_query, (
                variant, variant, variant, variant, variant, variant
            ))
            
            records = cursor.fetchall()
            
            print(f"Variante '{variant}': {len(records)} registros")
            
            if records:
                print(f"  ENCONTRADO! Detalles:")
                for record in records:
                    print(f"    Fecha: {record[7]}")
                    print(f"    Misión: {record[9]}")
                    print(f"    Rol: {record[10]}")
                    print(f"    Origen: {record[0]} -> Destino: {record[1]}")
                    print(f"    Celdas: origen={record[3]}, destino={record[4]}, objetivo={record[5]}")
                    print()
            else:
                print(f"  No encontrado")
            print()
        
        # 2. Búsqueda con LIKE para coincidencias parciales
        print("2. BÚSQUEDA CON COINCIDENCIAS PARCIALES:")
        print("-" * 40)
        
        # Buscar números que contengan los últimos 7 dígitos
        last_7_digits = target_number[-7:]  # 4277553
        last_8_digits = target_number[-8:]  # 04277553
        
        partial_patterns = [
            f"%{last_7_digits}",   # Termina en 4277553
            f"%{last_8_digits}",   # Termina en 04277553
            f"%{target_number}%",  # Contiene 3104277553
        ]
        
        for pattern in partial_patterns:
            like_query = """
                SELECT 
                    numero_origen, numero_destino, numero_objetivo,
                    celda_origen, celda_destino, celda_objetivo,
                    fecha_hora_llamada, operator
                FROM operator_call_data
                WHERE numero_origen LIKE ? OR numero_destino LIKE ? OR numero_objetivo LIKE ?
                ORDER BY fecha_hora_llamada
                LIMIT 10
            """
            
            cursor = conn.execute(like_query, (pattern, pattern, pattern))
            partial_records = cursor.fetchall()
            
            print(f"Patrón '{pattern}': {len(partial_records)} registros")
            
            if partial_records:
                for record in partial_records[:3]:  # Solo primeros 3
                    print(f"    {record[7]}: origen={record[0]}, destino={record[1]}")
                    print(f"    Celdas: {record[3]}, {record[4]}, {record[5]}")
        
        print()
        
        # 3. Búsqueda específica de la llamada mencionada por Boris
        print("3. BÚSQUEDA ESPECÍFICA DE LLAMADA A 3224274851:")
        print("-" * 45)
        
        # Buscar llamadas donde 3224274851 sea el destino
        target_call_query = """
            SELECT 
                numero_origen, numero_destino, numero_objetivo,
                celda_origen, celda_destino, celda_objetivo,
                fecha_hora_llamada, operator
            FROM operator_call_data
            WHERE numero_destino LIKE '%3224274851%'
            OR numero_objetivo LIKE '%3224274851%'
            ORDER BY fecha_hora_llamada
        """
        
        cursor = conn.execute(target_call_query)
        call_records = cursor.fetchall()
        
        print(f"Llamadas hacia 3224274851: {len(call_records)} registros")
        
        for record in call_records:
            origen = record[0]
            print(f"  Fecha: {record[6]}")
            print(f"  Origen: {origen} -> Destino: {record[1]}")
            print(f"  Celdas: origen={record[3]}, destino={record[4]}")
            
            # Verificar si el origen contiene parte del número buscado
            if origen and ('3104277553' in origen or '104277553' in origen):
                print(f"    *** POSIBLE COINCIDENCIA: {origen} ***")
            print()
        
        # 4. Verificar problemas de validación
        print("4. VERIFICACIÓN DE VALIDACIÓN DE NÚMEROS:")
        print("-" * 40)
        
        for variant in search_variants:
            is_valid = service._is_valid_phone_number(variant)
            normalized = service._normalize_phone_number(variant)
            variations = service._get_number_variations(variant)
            
            print(f"Variante: {variant}")
            print(f"  ¿Válido?: {is_valid}")
            print(f"  Normalizado: {normalized}")
            print(f"  Variaciones: {variations}")
            print()

if __name__ == "__main__":
    debug_numero_especifico()