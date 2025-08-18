#!/usr/bin/env python3
"""
DEBUG DETALLADO - Verificar origen y destino de llamadas
=======================================================
Boris indica que 3224274851 aparece como:
- Receptor en celda 51438
- Originador en celda 56124
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.correlation_analysis_service import CorrelationAnalysisService
import logging

logging.basicConfig(level=logging.WARNING)

def verificar_origen_destino():
    service = CorrelationAnalysisService()
    
    print("DEBUG DETALLADO - Origen y Destino de Llamadas")
    print("=" * 60)
    
    mission_id = "mission_MPFRBNsb"
    start_date = "2021-05-20 10:00:00"
    end_date = "2021-05-20 14:45:00"  # Período extendido
    
    target_number = "3224274851"
    target_with_prefix = f"57{target_number}"
    
    print(f"Analizando número: {target_number} (formato: {target_with_prefix})")
    print(f"Período: {start_date} a {end_date}")
    print()
    
    with service.get_db_connection() as conn:
        # Búsqueda detallada por campo específico
        detailed_query = """
            SELECT 
                numero_origen, numero_destino, numero_objetivo,
                celda_origen, celda_destino, celda_objetivo, cellid_decimal,
                fecha_hora_llamada, operator,
                CASE 
                    WHEN numero_origen = ? THEN 'ORIGINADOR'
                    WHEN numero_destino = ? THEN 'RECEPTOR' 
                    WHEN numero_objetivo = ? THEN 'OBJETIVO'
                    ELSE 'OTRO'
                END as rol_numero
            FROM operator_call_data
            WHERE mission_id = ?
            AND fecha_hora_llamada BETWEEN ? AND ?
            AND (numero_origen = ? OR numero_destino = ? OR numero_objetivo = ?)
            ORDER BY fecha_hora_llamada
        """
        
        cursor = conn.execute(detailed_query, (
            target_with_prefix, target_with_prefix, target_with_prefix,
            mission_id, start_date, end_date,
            target_with_prefix, target_with_prefix, target_with_prefix
        ))
        
        records = cursor.fetchall()
        
        print(f"Registros encontrados: {len(records)}")
        print("-" * 50)
        
        all_cells = set()
        role_cell_mapping = {}
        
        for i, record in enumerate(records, 1):
            print(f"Registro {i}:")
            print(f"  Fecha: {record[7]}")
            print(f"  Operador: {record[8]}")
            print(f"  Rol del número: {record[9]}")
            print(f"  Números:")
            print(f"    Origen: {record[0]}")
            print(f"    Destino: {record[1]}")
            print(f"    Objetivo: {record[2]}")
            print(f"  Celdas:")
            print(f"    Origen: {record[3]}")
            print(f"    Destino: {record[4]}")
            print(f"    Objetivo: {record[5]}")
            print(f"    Decimal: {record[6]}")
            
            # Mapear rol a celdas
            rol = record[9]
            if rol == 'ORIGINADOR' and record[3]:  # celda_origen
                cell = str(record[3])
                all_cells.add(cell)
                role_cell_mapping[f"{rol}-{cell}"] = f"Originador en celda {cell}"
            elif rol == 'RECEPTOR' and record[4]:  # celda_destino
                cell = str(record[4])
                all_cells.add(cell)
                role_cell_mapping[f"{rol}-{cell}"] = f"Receptor en celda {cell}"
            elif rol == 'OBJETIVO' and record[5]:  # celda_objetivo
                cell = str(record[5])
                all_cells.add(cell)
                role_cell_mapping[f"{rol}-{cell}"] = f"Objetivo en celda {cell}"
            
            # También agregar todas las celdas asociadas
            for cell_field in [record[3], record[4], record[5], record[6]]:
                if cell_field:
                    all_cells.add(str(cell_field))
            
            print()
        
        print("RESUMEN DE CELDAS ASOCIADAS:")
        print("-" * 30)
        print(f"Todas las celdas: {sorted(list(all_cells))}")
        print()
        
        print("MAPEO ROL-CELDA:")
        print("-" * 20)
        for role_cell, description in role_cell_mapping.items():
            print(f"  {description}")
        print()
        
        # Verificar coincidencias con HUNTER
        hunter_query = """
            SELECT DISTINCT cell_id
            FROM cellular_data
            WHERE mission_id = ?
            AND created_at BETWEEN ? AND ?
            AND cell_id IS NOT NULL
        """
        
        cursor = conn.execute(hunter_query, (mission_id, start_date, end_date))
        hunter_cells = set(str(row[0]) for row in cursor.fetchall())
        
        print(f"Celdas HUNTER en período: {sorted(list(hunter_cells))}")
        
        # Calcular coincidencias
        coincidencias = all_cells.intersection(hunter_cells)
        print(f"Coincidencias encontradas: {sorted(list(coincidencias))}")
        
        # Verificar qué roles específicos tienen coincidencias
        print("\nCOINCIDENCIAS POR ROL:")
        print("-" * 25)
        
        for role_cell, description in role_cell_mapping.items():
            rol, cell = role_cell.split('-', 1)
            if cell in hunter_cells:
                print(f"  ✅ {description} -> COINCIDE con HUNTER")
            else:
                print(f"  ❌ {description} -> NO coincide con HUNTER")
        
        print(f"\nCONCLUSIÓN:")
        if coincidencias:
            print(f"El número DEBERÍA aparecer con {len(coincidencias)} coincidencia(s)")
            print(f"Celdas coincidentes: {sorted(list(coincidencias))}")
        else:
            print(f"El número NO debería aparecer (sin coincidencias)")

if __name__ == "__main__":
    verificar_origen_destino()