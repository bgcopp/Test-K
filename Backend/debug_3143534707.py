#!/usr/bin/env python3
"""
Debug específico para el número 3143534707
"""

import logging
from services.correlation_analysis_service import CorrelationAnalysisService

# Configurar logging detallado
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def debug_3143534707():
    """Debug específico para 3143534707"""
    
    service = CorrelationAnalysisService()
    
    mission_id = "mission_MPFRBNsb"
    start_date = "2021-05-20 10:00:00"
    end_date = "2021-05-20 13:20:00"
    
    print("=== DEBUG ESPECIFICO PARA 3143534707 ===")
    
    with service.get_db_connection() as conn:
        # 1. Verificar Cell IDs de HUNTER
        hunter_cell_ids = service._extract_hunter_cell_ids(conn, mission_id, start_date, end_date)
        print(f"Cell IDs HUNTER: {sorted(list(hunter_cell_ids.keys()))}")
        print()
        
        # 2. Extraer datos de operadores
        operator_data = service._extract_operator_numbers_with_cells(conn, mission_id, start_date, end_date)
        
        # 3. Filtrar solo registros de 3143534707
        target_records = [r for r in operator_data if r['numero_telefono'] == '3143534707']
        print(f"Registros de 3143534707 en operator_data: {len(target_records)}")
        
        for i, record in enumerate(target_records):
            print(f"  Registro {i+1}: cell_id={record['cell_id']}, field_type={record['field_type']}")
            print(f"    numero_original={record['numero_original']}")
            print(f"    cell_id en HUNTER? {'SI' if record['cell_id'] in hunter_cell_ids else 'NO'}")
        print()
        
        # 4. Ejecutar correlación paso a paso
        correlations = service._correlate_by_cell_ids(hunter_cell_ids, operator_data)
        
        # 5. Buscar 3143534707 en correlaciones
        target_correlation = None
        for correlation in correlations:
            if correlation['numero_celular'] == '3143534707':
                target_correlation = correlation
                break
        
        if target_correlation:
            print("ENCONTRADO en correlaciones:")
            print(f"  numero_celular: {target_correlation['numero_celular']}")
            print(f"  numero_original: {target_correlation['numero_original']}")
            print(f"  total_coincidencias: {target_correlation['total_coincidencias']}")
            print(f"  celdas_coincidentes: {target_correlation['celdas_coincidentes']}")
        else:
            print("NO ENCONTRADO en correlaciones - ESTE ES EL PROBLEMA")
            
            # Debug: verificar qué está pasando en la correlación
            print()
            print("=== DEBUG DE CORRELACION ===")
            hunter_cell_set = set(hunter_cell_ids.keys())
            
            for record in target_records:
                cell_id = record['cell_id']
                numero = record['numero_telefono']
                print(f"Procesando: numero={numero}, cell_id={cell_id}")
                print(f"  cell_id en hunter_cell_set? {cell_id in hunter_cell_set}")
                
                if cell_id in hunter_cell_set:
                    print(f"  DEBERIA agregarse a correlations[{numero}]")
                else:
                    print(f"  NO se agrega porque cell_id no está en HUNTER")

if __name__ == "__main__":
    debug_3143534707()