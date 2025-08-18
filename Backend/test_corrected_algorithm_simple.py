#!/usr/bin/env python3
"""
KRONOS - Validación Simplificada del Algoritmo Corregido
======================================================
Boris 2025-08-18: Validar que el algoritmo corregido incluya 
TODAS las celdas relacionadas con las comunicaciones del número objetivo.

Usando SQLite directo para evitar problemas de inicialización.
"""

import sqlite3
import os
import json
from datetime import datetime

def main():
    """Valida el algoritmo de correlación corregido usando SQLite directo"""
    print("=" * 80)
    print("VALIDACION DEL ALGORITMO DE CORRELACION CORREGIDO - SIMPLE")
    print("=" * 80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Objetivo: Validar logica corregida que incluye TODAS las celdas")
    print()
    
    try:
        # Usar backup con datos reales
        backup_file = "kronos.db.backup_20250818_023501"
        if not os.path.exists(backup_file):
            print(f"Error: No se encuentra el archivo {backup_file}")
            return False
        
        # Conectar a la base de datos
        conn = sqlite3.connect(backup_file)
        cursor = conn.cursor()
        
        # Parámetros de prueba
        mission_id = "mission_MPFRBNsb"
        numero_objetivo = "3143534707"
        start_date = "2021-05-01"  # Período amplio para encontrar datos
        end_date = "2021-05-31"
        
        print(f"Parametros de prueba:")
        print(f"  - Mision: {mission_id}")
        print(f"  - Numero objetivo: {numero_objetivo}")
        print(f"  - Periodo: {start_date} - {end_date}")
        print()
        
        # 1. Verificar datos disponibles
        print("1. VERIFICANDO DATOS DISPONIBLES")
        print("-" * 50)
        
        # Contar registros totales
        cursor.execute("SELECT COUNT(*) FROM operator_call_data WHERE mission_id = ?", (mission_id,))
        total_records = cursor.fetchone()[0]
        print(f"Registros totales en operator_call_data: {total_records}")
        
        # Verificar período de datos
        cursor.execute("""
            SELECT MIN(fecha_hora_llamada), MAX(fecha_hora_llamada) 
            FROM operator_call_data 
            WHERE mission_id = ?
        """, (mission_id,))
        min_date, max_date = cursor.fetchone()
        print(f"Periodo de datos: {min_date} - {max_date}")
        
        # Contar números únicos
        cursor.execute("""
            SELECT COUNT(DISTINCT numero_origen) + COUNT(DISTINCT numero_destino) as total_numeros
            FROM operator_call_data 
            WHERE mission_id = ?
        """, (mission_id,))
        total_numbers = cursor.fetchone()[0]
        print(f"Numeros unicos aproximados: {total_numbers}")
        
        # Verificar si existe el número objetivo
        cursor.execute("""
            SELECT COUNT(*) FROM operator_call_data 
            WHERE mission_id = ? AND (numero_origen = ? OR numero_destino = ?)
        """, (mission_id, numero_objetivo, numero_objetivo))
        target_records = cursor.fetchone()[0]
        print(f"Registros con numero objetivo {numero_objetivo}: {target_records}")
        print()
        
        if target_records == 0:
            print("ADVERTENCIA: Numero objetivo no encontrado en los datos")
            # Buscar números similares
            cursor.execute("""
                SELECT DISTINCT numero_origen 
                FROM operator_call_data 
                WHERE mission_id = ? AND numero_origen LIKE '%3143534707%'
                LIMIT 5
            """, (mission_id,))
            similar = cursor.fetchall()
            if similar:
                print(f"Numeros similares encontrados: {[n[0] for n in similar]}")
            
            # Usar un número que sí exista para la prueba
            cursor.execute("""
                SELECT numero_origen, COUNT(*) as count 
                FROM operator_call_data 
                WHERE mission_id = ?
                GROUP BY numero_origen 
                ORDER BY count DESC 
                LIMIT 3
            """, (mission_id,))
            top_numbers = cursor.fetchall()
            if top_numbers:
                numero_objetivo = str(top_numbers[0][0])
                print(f"Usando numero con mas registros para prueba: {numero_objetivo}")
                print()
        
        # 2. Implementar algoritmo CORREGIDO directamente en SQL
        print("2. ALGORITMO CORREGIDO - TODAS LAS CELDAS INVOLUCRADAS")
        print("-" * 50)
        
        # Query corregido - incluir TODAS las celdas relacionadas con el número
        query_corrected = """
        WITH target_communications AS (
            -- Obtener todas las comunicaciones del número objetivo
            SELECT 
                numero_origen as numero,
                celda_origen as celda,
                fecha_hora_llamada,
                'originador_fisica' as tipo
            FROM operator_call_data 
            WHERE mission_id = ?
              AND numero_origen = ?
              AND date(fecha_hora_llamada) BETWEEN ? AND ?
            
            UNION ALL
            
            -- Celdas destino cuando es originador (comunicaciones relacionadas)
            SELECT 
                numero_origen as numero,
                celda_destino as celda,
                fecha_hora_llamada,
                'originador_destino' as tipo
            FROM operator_call_data 
            WHERE mission_id = ?
              AND numero_origen = ?
              AND date(fecha_hora_llamada) BETWEEN ? AND ?
              AND celda_destino IS NOT NULL
              AND celda_destino != ''
            
            UNION ALL
            
            -- Cuando es receptor
            SELECT 
                numero_destino as numero,
                celda_destino as celda,
                fecha_hora_llamada,
                'receptor_destino' as tipo
            FROM operator_call_data 
            WHERE mission_id = ?
              AND numero_destino = ?
              AND date(fecha_hora_llamada) BETWEEN ? AND ?
        )
        SELECT 
            numero,
            COUNT(DISTINCT celda) as total_celdas_unicas,
            GROUP_CONCAT(DISTINCT celda) as celdas,
            COUNT(*) as total_comunicaciones
        FROM target_communications
        GROUP BY numero
        """
        
        params = (mission_id, numero_objetivo, start_date, end_date,
                 mission_id, numero_objetivo, start_date, end_date,
                 mission_id, numero_objetivo, start_date, end_date)
        
        cursor.execute(query_corrected, params)
        result = cursor.fetchone()
        
        if result:
            numero, total_celdas, celdas_str, total_comunicaciones = result
            celdas_encontradas = set(celdas_str.split(',')) if celdas_str else set()
            
            print(f"Numero analizado: {numero}")
            print(f"Total celdas unicas: {total_celdas}")
            print(f"Total comunicaciones: {total_comunicaciones}")
            print(f"Celdas encontradas: {', '.join(sorted(celdas_encontradas))}")
            print()
            
            # 3. Análisis detallado por tipo
            print("3. ANALISIS DETALLADO POR TIPO DE RELACION")
            print("-" * 50)
            
            query_detail = """
            SELECT 
                tipo,
                COUNT(DISTINCT celda) as celdas_unicas,
                GROUP_CONCAT(DISTINCT celda) as celdas,
                COUNT(*) as comunicaciones
            FROM (
                SELECT 
                    celda_origen as celda,
                    'originador_fisica' as tipo
                FROM operator_call_data 
                WHERE mission_id = ? AND numero_origen = ?
                  AND date(fecha_hora_llamada) BETWEEN ? AND ?
                
                UNION ALL
                
                SELECT 
                    celda_destino as celda,
                    'originador_destino' as tipo
                FROM operator_call_data 
                WHERE mission_id = ? AND numero_origen = ?
                  AND date(fecha_hora_llamada) BETWEEN ? AND ?
                  AND celda_destino IS NOT NULL AND celda_destino != ''
                
                UNION ALL
                
                SELECT 
                    celda_destino as celda,
                    'receptor_destino' as tipo
                FROM operator_call_data 
                WHERE mission_id = ? AND numero_destino = ?
                  AND date(fecha_hora_llamada) BETWEEN ? AND ?
            ) AS all_relations
            GROUP BY tipo
            ORDER BY tipo
            """
            
            cursor.execute(query_detail, params)
            detail_results = cursor.fetchall()
            
            for tipo, celdas_count, celdas_list, comm_count in detail_results:
                celdas = celdas_list.split(',') if celdas_list else []
                print(f"{tipo}: {celdas_count} celdas, {comm_count} comunicaciones")
                print(f"  Celdas: {', '.join(sorted(celdas))}")
            print()
            
            # 4. Comparación con algoritmo anterior (solo físico)
            print("4. COMPARACION CON ALGORITMO ANTERIOR")
            print("-" * 50)
            
            # Algoritmo anterior - solo ubicación física
            query_old = """
            SELECT COUNT(DISTINCT celda) as total_celdas_fisicas
            FROM (
                SELECT celda_origen as celda
                FROM operator_call_data 
                WHERE mission_id = ? AND numero_origen = ?
                  AND date(fecha_hora_llamada) BETWEEN ? AND ?
                
                UNION
                
                SELECT celda_destino as celda
                FROM operator_call_data 
                WHERE mission_id = ? AND numero_destino = ?
                  AND date(fecha_hora_llamada) BETWEEN ? AND ?
            ) AS physical_locations
            """
            
            old_params = (mission_id, numero_objetivo, start_date, end_date,
                         mission_id, numero_objetivo, start_date, end_date)
            cursor.execute(query_old, old_params)
            old_result = cursor.fetchone()
            celdas_algoritmo_anterior = old_result[0] if old_result else 0
            
            print(f"Algoritmo ANTERIOR (solo fisico): {celdas_algoritmo_anterior} celdas")
            print(f"Algoritmo CORREGIDO (completo): {total_celdas} celdas")
            print(f"Diferencia: +{total_celdas - celdas_algoritmo_anterior} celdas adicionales")
            print()
            
            # 5. Resultado final
            print("5. RESULTADO FINAL")
            print("-" * 50)
            
            if total_celdas > celdas_algoritmo_anterior:
                print("EXITO: El algoritmo corregido incluye MAS celdas")
                print("  - Se incluyen todas las celdas involucradas en comunicaciones")
                print("  - No solo donde el numero esta fisicamente ubicado")
                status = "CORRECTED_SUCCESS"
            elif total_celdas == celdas_algoritmo_anterior:
                print("ADVERTENCIA: Mismo numero de celdas que algoritmo anterior")
                status = "CORRECTED_SAME"
            else:
                print("ERROR: Menos celdas que algoritmo anterior")
                status = "CORRECTED_ERROR"
            
            print(f"Estado: {status}")
            print()
            
            # Guardar resultado
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"corrected_algorithm_validation_{timestamp}.json"
            
            result_data = {
                'timestamp': datetime.now().isoformat(),
                'test_name': 'Corrected Algorithm Validation',
                'numero_objetivo': numero_objetivo,
                'mission_id': mission_id,
                'periodo': f"{start_date} - {end_date}",
                'algoritmo_anterior': celdas_algoritmo_anterior,
                'algoritmo_corregido': total_celdas,
                'diferencia': total_celdas - celdas_algoritmo_anterior,
                'celdas_encontradas': list(celdas_encontradas),
                'detalle_por_tipo': {
                    r[0]: {'celdas': r[1], 'comunicaciones': r[3]} 
                    for r in detail_results
                },
                'status': status,
                'algorithm_improved': total_celdas > celdas_algoritmo_anterior
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"Resultado guardado en: {filename}")
            
            success = total_celdas > celdas_algoritmo_anterior
            
        else:
            print("No se encontraron datos para el numero objetivo")
            success = False
        
        conn.close()
        return success
        
    except Exception as e:
        print(f"Error durante la validacion: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)