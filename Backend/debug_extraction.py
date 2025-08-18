#!/usr/bin/env python3
"""
Debug específico de la extracción de datos de operadores
"""

import sqlite3
from services.correlation_analysis_service import CorrelationAnalysisService

def debug_extraction():
    """Debug de la extracción paso a paso"""
    
    service = CorrelationAnalysisService()
    
    mission_id = "mission_MPFRBNsb"
    start_date = "2021-05-20 10:00:00"
    end_date = "2021-05-20 13:20:00"
    
    print("=== DEBUG DE EXTRACCION DE DATOS ===")
    
    with service.get_db_connection() as conn:
        # Simular la consulta exacta de _extract_operator_numbers_with_cells
        call_query = """
            SELECT 
                numero_origen,
                numero_destino,
                numero_objetivo,
                operator,
                fecha_hora_llamada,
                celda_origen,
                celda_destino,
                celda_objetivo,
                cellid_decimal,
                lac_decimal
            FROM operator_call_data
            WHERE mission_id = ?
            AND fecha_hora_llamada BETWEEN ? AND ?
        """
        
        cursor = conn.execute(call_query, (mission_id, start_date, end_date))
        call_rows = cursor.fetchall()
        
        print(f"Total registros de operator_call_data: {len(call_rows)}")
        
        # Filtrar solo registros que contengan 3143534707
        target_rows = []
        for row in call_rows:
            numero_origen = row[0]
            numero_destino = row[1] 
            numero_objetivo = row[2]
            
            if ('3143534707' in str(numero_origen) or 
                '3143534707' in str(numero_destino) or 
                '3143534707' in str(numero_objetivo)):
                target_rows.append(row)
        
        print(f"Registros con 3143534707: {len(target_rows)}")
        print()
        
        # Procesar cada registro como lo hace el algoritmo
        processed_records = []
        for row in target_rows:
            numero_origen = row[0]
            numero_destino = row[1] 
            numero_objetivo = row[2]
            operator = row[3]
            fecha_hora_llamada = row[4]
            celda_origen = row[5]
            celda_destino = row[6]
            celda_objetivo = row[7]
            cellid_decimal = row[8]
            lac_decimal = row[9]
            
            print(f"Procesando registro:")
            print(f"  Fecha: {fecha_hora_llamada}")
            print(f"  Origen: {numero_origen}, Destino: {numero_destino}, Objetivo: {numero_objetivo}")
            print(f"  Celdas: Origen={celda_origen}, Destino={celda_destino}, Objetivo={celda_objetivo}")
            
            # Simular el procesamiento del algoritmo
            number_cell_pairs = [
                (numero_origen, celda_origen, 'origen'),
                (numero_destino, celda_destino, 'destino'),
                (numero_objetivo, celda_objetivo, 'objetivo')
            ]
            
            for number, cell_id, field_type in number_cell_pairs:
                if number and service._is_valid_phone_number(number) and cell_id:
                    normalized = service._normalize_phone_number(number)
                    print(f"    Procesando: {number} -> {normalized}, cell_id={cell_id}, tipo={field_type}")
                    
                    if normalized == '3143534707':
                        processed_records.append({
                            'numero_telefono': normalized,
                            'numero_original': number,
                            'cell_id': str(cell_id).strip(),
                            'field_type': field_type
                        })
                        print(f"      *** AGREGADO para 3143534707 ***")
            print()
        
        print(f"=== RESUMEN DE REGISTROS PROCESADOS PARA 3143534707 ===")
        for i, record in enumerate(processed_records):
            print(f"Registro {i+1}: cell_id={record['cell_id']}, tipo={record['field_type']}")

if __name__ == "__main__":
    debug_extraction()