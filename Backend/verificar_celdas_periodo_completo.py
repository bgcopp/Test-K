#!/usr/bin/env python3
"""
VERIFICAR - Celdas esperadas en período completo de HUNTER
========================================================
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.correlation_analysis_service import CorrelationAnalysisService
import logging

logging.basicConfig(level=logging.WARNING)

def verificar_celdas_periodo_completo():
    service = CorrelationAnalysisService()
    
    print("VERIFICACION DE CELDAS EN TODO EL DATASET HUNTER")
    print("=" * 60)
    
    mission_id = "mission_MPFRBNsb"
    celdas_esperadas = ['53591', '52453', '56124']
    
    with service.get_db_connection() as conn:
        # 1. Verificar rango completo de fechas en HUNTER
        date_range_query = """
            SELECT 
                MIN(created_at) as min_date,
                MAX(created_at) as max_date,
                COUNT(*) as total_records
            FROM cellular_data 
            WHERE mission_id = ?
        """
        cursor = conn.execute(date_range_query, (mission_id,))
        date_info = cursor.fetchone()
        
        print(f"Rango completo de datos HUNTER:")
        print(f"  Fecha minima: {date_info[0]}")
        print(f"  Fecha maxima: {date_info[1]}")
        print(f"  Total registros: {date_info[2]}")
        print()
        
        # 2. Buscar celdas esperadas en todo el dataset
        print(f"Buscando celdas esperadas: {celdas_esperadas}")
        print("-" * 40)
        
        for celda in celdas_esperadas:
            search_query = """
                SELECT 
                    COUNT(*) as count,
                    MIN(created_at) as first_occurrence,
                    MAX(created_at) as last_occurrence
                FROM cellular_data
                WHERE mission_id = ?
                AND cell_id = ?
            """
            
            cursor = conn.execute(search_query, (mission_id, celda))
            result = cursor.fetchone()
            
            print(f"Celda {celda}:")
            if result[0] > 0:
                print(f"  ENCONTRADA: {result[0]} registros")
                print(f"  Primera aparicion: {result[1]}")
                print(f"  Ultima aparicion: {result[2]}")
            else:
                print(f"  NO ENCONTRADA en datos HUNTER")
            print()
        
        # 3. Verificar qué celdas están disponibles en el período de análisis
        analysis_start = "2021-05-20 10:00:00"
        analysis_end = "2021-05-20 13:30:00"
        
        print(f"Celdas disponibles en período de análisis ({analysis_start} a {analysis_end}):")
        
        period_query = """
            SELECT DISTINCT cell_id, COUNT(*) as count
            FROM cellular_data
            WHERE mission_id = ?
            AND created_at BETWEEN ? AND ?
            AND cell_id IS NOT NULL
            GROUP BY cell_id
            ORDER BY cell_id
        """
        
        cursor = conn.execute(period_query, (mission_id, analysis_start, analysis_end))
        period_cells = cursor.fetchall()
        
        print(f"Total celdas en período: {len(period_cells)}")
        for cell_info in period_cells:
            print(f"  {cell_info[0]}: {cell_info[1]} registros")
        
        # 4. Sugerencia de período alternativo
        print(f"\nSUGERENCIA:")
        print(f"Las celdas {celdas_esperadas} no están en el período analizado.")
        print(f"Posibles soluciones:")
        print(f"  1. Ampliar el rango de fechas de análisis")
        print(f"  2. Verificar si las celdas están en otros períodos")
        print(f"  3. Confirmar que las celdas esperadas son correctas")

if __name__ == "__main__":
    verificar_celdas_periodo_completo()