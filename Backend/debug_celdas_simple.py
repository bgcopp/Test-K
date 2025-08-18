#!/usr/bin/env python3
"""
DEBUG SIMPLE - Verificar celdas específicas de Boris
===================================================
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.correlation_analysis_service import CorrelationAnalysisService
import logging

logging.basicConfig(level=logging.WARNING)

def verificar_problema():
    service = CorrelationAnalysisService()
    
    print("VERIFICACION DE CELDAS ESPECIFICAS")
    print("=" * 50)
    
    mission_id = "mission_MPFRBNsb"
    start_date = "2021-05-20 10:00:00"
    end_date = "2021-05-20 13:30:00"
    
    # Información de Boris
    expected_matches = {
        '3104277553': ['53591', '52453'],
        '3102715509': ['56124'],
        '3224274851': ['53591']
    }
    
    with service.get_db_connection() as conn:
        # 1. Obtener celdas HUNTER
        hunter_query = """
            SELECT DISTINCT cell_id
            FROM cellular_data 
            WHERE mission_id = ? 
            AND created_at BETWEEN ? AND ?
            AND cell_id IS NOT NULL
        """
        cursor = conn.execute(hunter_query, (mission_id, start_date, end_date))
        hunter_cells = set(str(row[0]) for row in cursor.fetchall())
        
        print(f"Celdas HUNTER en periodo: {sorted(list(hunter_cells))}")
        print()
        
        # 2. Verificar cada número
        for number, expected_cells in expected_matches.items():
            number_with_prefix = f"57{number}"
            
            print(f"Numero: {number} (buscando como {number_with_prefix})")
            print(f"Celdas esperadas: {expected_cells}")
            
            # Verificar si celdas esperadas están en HUNTER
            celdas_en_hunter = []
            celdas_no_en_hunter = []
            
            for celda in expected_cells:
                if celda in hunter_cells:
                    celdas_en_hunter.append(celda)
                else:
                    celdas_no_en_hunter.append(celda)
            
            print(f"Celdas esperadas EN HUNTER: {celdas_en_hunter}")
            print(f"Celdas esperadas NO en HUNTER: {celdas_no_en_hunter}")
            
            # Buscar el número en operator_call_data
            search_query = """
                SELECT COUNT(*) as count
                FROM operator_call_data
                WHERE mission_id = ?
                AND fecha_hora_llamada BETWEEN ? AND ?
                AND (numero_origen = ? OR numero_destino = ? OR numero_objetivo = ?)
            """
            
            cursor = conn.execute(search_query, (
                mission_id, start_date, end_date,
                number_with_prefix, number_with_prefix, number_with_prefix
            ))
            
            count = cursor.fetchone()[0]
            print(f"Registros encontrados en operator_call_data: {count}")
            
            if count > 0 and celdas_en_hunter:
                print("CONCLUSION: DEBERIA aparecer en correlacion")
            elif count > 0 and not celdas_en_hunter:
                print("CONCLUSION: NO deberia aparecer (celdas esperadas no estan en HUNTER)")
            else:
                print("CONCLUSION: Numero no encontrado en datos")
            
            print("-" * 30)

if __name__ == "__main__":
    verificar_problema()