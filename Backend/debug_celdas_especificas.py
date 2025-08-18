#!/usr/bin/env python3
"""
DEBUG PROFUNDO - Verificar celdas específicas de Boris
=====================================================
Boris indica que estos números DEBERÍAN aparecer:
- 3104277553: celdas 53591, 52453
- 3102715509: celda 56124  
- 3224274851: celda 53591
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.correlation_analysis_service import CorrelationAnalysisService
import logging

logging.basicConfig(level=logging.INFO)

def verificar_celdas_especificas():
    service = CorrelationAnalysisService()
    
    print("DEBUG PROFUNDO - Verificación de celdas específicas")
    print("=" * 60)
    
    mission_id = "mission_MPFRBNsb"
    start_date = "2021-05-20 10:00:00"
    end_date = "2021-05-20 13:30:00"
    
    # Información proporcionada por Boris
    expected_matches = {
        '3104277553': ['53591', '52453'],
        '3102715509': ['56124'],
        '3224274851': ['53591']
    }
    
    with service.get_db_connection() as conn:
        # 1. Verificar qué celdas tiene HUNTER en el período
        print("1. CELDAS HUNTER EN EL PERÍODO:")
        print("-" * 40)
        
        hunter_query = """
            SELECT DISTINCT cell_id, COUNT(*) as count
            FROM cellular_data 
            WHERE mission_id = ? 
            AND created_at BETWEEN ? AND ?
            AND cell_id IS NOT NULL
            GROUP BY cell_id
            ORDER BY cell_id
        """
        cursor = conn.execute(hunter_query, (mission_id, start_date, end_date))
        hunter_cells_data = cursor.fetchall()
        hunter_cells = set(str(row[0]) for row in hunter_cells_data)
        
        print(f"Total celdas HUNTER: {len(hunter_cells)}")
        for row in hunter_cells_data:
            print(f"  Celda {row[0]}: {row[1]} registros")
        print()
        
        # 2. Verificar las celdas esperadas por Boris
        print("2. VERIFICACIÓN DE CELDAS ESPERADAS:")
        print("-" * 40)
        
        for number, expected_cells in expected_matches.items():
            print(f"\nNúmero: {number}")
            print(f"Celdas esperadas por Boris: {expected_cells}")
            
            # Verificar si las celdas esperadas están en HUNTER
            missing_from_hunter = []
            present_in_hunter = []
            
            for expected_cell in expected_cells:
                if expected_cell in hunter_cells:
                    present_in_hunter.append(expected_cell)
                else:
                    missing_from_hunter.append(expected_cell)
            
            print(f"  Celdas presentes en HUNTER: {present_in_hunter}")
            print(f"  Celdas AUSENTES en HUNTER: {missing_from_hunter}")
            
            if missing_from_hunter:
                print(f"  ❌ PROBLEMA: Celdas {missing_from_hunter} no están en datos HUNTER del período")
        
        # 3. Verificar registros específicos en operator_call_data
        print("\n3. VERIFICACIÓN EN OPERATOR_CALL_DATA:")
        print("-" * 40)
        
        for number, expected_cells in expected_matches.items():
            number_with_prefix = f"57{number}"
            
            print(f"\nBuscando {number} (como {number_with_prefix}):")
            
            # Buscar registros específicos
            detailed_query = """
                SELECT 
                    numero_origen, numero_destino, numero_objetivo,
                    celda_origen, celda_destino, celda_objetivo, cellid_decimal,
                    fecha_hora_llamada, operator
                FROM operator_call_data
                WHERE mission_id = ?
                AND fecha_hora_llamada BETWEEN ? AND ?
                AND (numero_origen = ? OR numero_destino = ? OR numero_objetivo = ?)
                ORDER BY fecha_hora_llamada
            """
            
            cursor = conn.execute(detailed_query, (
                mission_id, start_date, end_date,
                number_with_prefix, number_with_prefix, number_with_prefix
            ))
            
            records = cursor.fetchall()
            print(f"  Registros encontrados: {len(records)}")
            
            if records:
                all_cells = set()
                for record in records:
                    cells_in_record = []
                    if record[3]: cells_in_record.append(str(record[3]))  # celda_origen
                    if record[4]: cells_in_record.append(str(record[4]))  # celda_destino  
                    if record[5]: cells_in_record.append(str(record[5]))  # celda_objetivo
                    if record[6]: cells_in_record.append(str(record[6]))  # cellid_decimal
                    
                    all_cells.update(cells_in_record)
                    
                    print(f"    Fecha: {record[7]}, Operador: {record[8]}")
                    print(f"    Números: orig={record[0]}, dest={record[1]}, obj={record[2]}")
                    print(f"    Celdas: orig={record[3]}, dest={record[4]}, obj={record[5]}, decimal={record[6]}")
                
                print(f"  Todas las celdas asociadas: {sorted(list(all_cells))}")
                
                # Verificar coincidencias con celdas esperadas
                expected_set = set(expected_cells)
                found_set = all_cells
                matches = expected_set.intersection(found_set)
                missing = expected_set - found_set
                
                print(f"  Celdas esperadas encontradas: {sorted(list(matches))}")
                if missing:
                    print(f"  Celdas esperadas NO encontradas: {sorted(list(missing))}")
                
                # Verificar si las encontradas están en HUNTER
                hunter_matches = matches.intersection(hunter_cells)
                print(f"  Coincidencias con HUNTER: {sorted(list(hunter_matches))}")
                
                if hunter_matches:
                    print(f"  ✅ DEBERÍA aparecer en correlación")
                else:
                    print(f"  ❌ NO debería aparecer (sin coincidencias HUNTER)")
            else:
                print(f"  ❌ NÚMERO NO ENCONTRADO en operator_call_data")

if __name__ == "__main__":
    verificar_celdas_especificas()