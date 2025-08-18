#!/usr/bin/env python3
"""
DEBUG - Verificar coincidencias de celdas con HUNTER
==================================================
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.correlation_analysis_service import CorrelationAnalysisService
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)

def debug_cell_matches():
    service = CorrelationAnalysisService()
    
    print("DEBUG: Verificacion de coincidencias celdas HUNTER")
    print("=" * 60)
    
    mission_id = "mission_MPFRBNsb"
    start_date = "2021-05-20 10:00:00"
    end_date = "2021-05-20 13:30:00"
    
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
        
        print(f"CELDAS HUNTER encontradas: {len(hunter_cells)}")
        print(f"Celdas: {sorted(list(hunter_cells))}")
        print()
        
        # 2. Verificar celdas asociadas a numeros objetivo
        target_numbers = ['3224274851', '3208611034', '3102715509', '3143534707']
        
        for target in target_numbers:
            # Buscar con prefijo 57
            target_with_prefix = f"57{target}"
            
            print(f"Analizando {target} (formato base: {target_with_prefix}):")
            
            # Buscar en operator_call_data
            call_query = """
                SELECT DISTINCT celda_origen, celda_destino, celda_objetivo, cellid_decimal
                FROM operator_call_data
                WHERE mission_id = ?
                AND fecha_hora_llamada BETWEEN ? AND ?
                AND (numero_origen = ? OR numero_destino = ? OR numero_objetivo = ?)
            """
            
            cursor = conn.execute(call_query, (
                mission_id, start_date, end_date,
                target_with_prefix, target_with_prefix, target_with_prefix
            ))
            
            operator_cells = set()
            for row in cursor.fetchall():
                for cell_field in row:
                    if cell_field:
                        operator_cells.add(str(cell_field))
            
            print(f"  Celdas asociadas al numero: {sorted(list(operator_cells))}")
            
            # Verificar coincidencias
            matching_cells = operator_cells.intersection(hunter_cells)
            print(f"  Coincidencias con HUNTER: {sorted(list(matching_cells))}")
            
            if matching_cells:
                print(f"  RESULTADO: DEBERIA aparecer en correlacion ({len(matching_cells)} celdas)")
            else:
                print(f"  RESULTADO: NO deberia aparecer (sin coincidencias)")
            print()

if __name__ == "__main__":
    debug_cell_matches()