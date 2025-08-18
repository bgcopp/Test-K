#!/usr/bin/env python3
"""
Testing de Validación de Números Objetivo de Boris
===============================================

Prueba específica para validar que el algoritmo de correlación dinámico
encuentra correctamente los números objetivo especificados por Boris,
particularmente 3143534707 que debe mostrar 4 ocurrencias en celdas específicas.

Autor: Claude Code (Testing Engineer)
Fecha: 2025-08-18
"""

import sys
import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime

# Agregar el directorio Backend al path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.correlation_service_dynamic import get_correlation_service_dynamic

def test_boris_target_numbers():
    """
    Valida los números objetivo específicos de Boris
    """
    print("=" * 60)
    print("TESTING DE NUMEROS OBJETIVO DE BORIS")
    print("=" * 60)
    
    # Números objetivo especificados por Boris
    target_numbers = [
        "3143534707",  # Debe mostrar 4 ocurrencias: celdas 53591, 51438, 56124, 51203
        "3224274851",
        "3208611034", 
        "3104277553",
        "3102715509"
    ]
    
    # Celdas esperadas para 3143534707
    expected_cells_3143534707 = ["53591", "51438", "56124", "51203"]
    
    try:
        # Configurar parámetros de correlación
        mission_id = "mission_MPFRBNsb"
        start_datetime = "2021-05-20 10:00:00"
        end_datetime = "2021-05-20 14:30:00"
        min_occurrences = 1
        
        print(f"Mision: {mission_id}")
        print(f"Periodo: {start_datetime} - {end_datetime}")
        print(f"Min ocurrencias: {min_occurrences}")
        print()
        
        # Ejecutar análisis de correlación dinámico
        service = get_correlation_service_dynamic()
        results = service.execute_correlation_analysis(
            mission_id=mission_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            min_occurrences=min_occurrences
        )
        
        if not results['success']:
            raise Exception(f"Error en análisis: {results.get('error', 'Error desconocido')}")
        
        correlations = results['data']
        total_found = len(correlations)
        
        print(f"Analisis completado exitosamente")
        print(f"Total correlaciones encontradas: {total_found}")
        print()
        
        # Crear diccionario para búsqueda rápida por número
        correlations_by_number = {}
        for correlation in correlations:
            number = correlation.get('numero_completo')
            cell_id = correlation.get('cell_id')
            
            if number not in correlations_by_number:
                correlations_by_number[number] = []
            correlations_by_number[number].append(correlation)
        
        # Validar cada número objetivo
        validation_results = {}
        
        for target_number in target_numbers:
            print(f"Validando numero objetivo: {target_number}")
            
            if target_number in correlations_by_number:
                occurrences = correlations_by_number[target_number]
                cell_ids = [str(occ.get('cell_id')) for occ in occurrences]
                unique_cells = list(set(cell_ids))
                
                print(f"   Encontrado con {len(occurrences)} ocurrencias")
                print(f"   Celdas: {unique_cells}")
                
                # Validación especial para 3143534707
                if target_number == "3143534707":
                    print(f"   VALIDACION ESPECIAL para {target_number}:")
                    print(f"   Celdas esperadas: {expected_cells_3143534707}")
                    
                    # Verificar que todas las celdas esperadas estén presentes
                    cells_found = set(unique_cells)
                    cells_expected = set(expected_cells_3143534707)
                    
                    if cells_expected.issubset(cells_found):
                        print(f"   EXITO: Todas las celdas esperadas encontradas")
                        validation_results[target_number] = {
                            'status': 'SUCCESS',
                            'occurrences': len(occurrences),
                            'cells_found': unique_cells,
                            'all_expected_cells_found': True
                        }
                    else:
                        missing_cells = cells_expected - cells_found
                        print(f"   FALLO: Celdas faltantes: {list(missing_cells)}")
                        validation_results[target_number] = {
                            'status': 'PARTIAL',
                            'occurrences': len(occurrences),
                            'cells_found': unique_cells,
                            'missing_cells': list(missing_cells),
                            'all_expected_cells_found': False
                        }
                else:
                    validation_results[target_number] = {
                        'status': 'FOUND',
                        'occurrences': len(occurrences),
                        'cells_found': unique_cells
                    }
            else:
                print(f"   NO encontrado en los resultados")
                validation_results[target_number] = {
                    'status': 'NOT_FOUND',
                    'occurrences': 0,
                    'cells_found': []
                }
            
            print()
        
        # Resumen de validación
        print("=" * 60)
        print("RESUMEN DE VALIDACION")
        print("=" * 60)
        
        success_count = 0
        for number, result in validation_results.items():
            status = result['status']
            occurrences = result['occurrences']
            
            if status in ['SUCCESS', 'FOUND']:
                success_count += 1
                print(f"OK {number}: {occurrences} ocurrencias - {status}")
            else:
                print(f"FAIL {number}: {occurrences} ocurrencias - {status}")
        
        print()
        print(f"Tasa de exito: {success_count}/{len(target_numbers)} ({(success_count/len(target_numbers)*100):.1f}%)")
        
        # Guardar resultados en archivo JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"boris_target_numbers_validation_{timestamp}.json"
        
        output_data = {
            'timestamp': timestamp,
            'mission_id': mission_id,
            'period': f"{start_datetime} - {end_datetime}",
            'total_correlations_found': total_found,
            'target_numbers_tested': target_numbers,
            'validation_results': validation_results,
            'success_rate': f"{(success_count/len(target_numbers)*100):.1f}%",
            'algorithm_status': 'DYNAMIC_NO_HARDCODED_VALUES'
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"Resultados guardados en: {output_file}")
        
        # Determinar resultado final
        if success_count == len(target_numbers):
            print("\nTODOS LOS NUMEROS OBJETIVO VALIDADOS EXITOSAMENTE")
            return True
        else:
            print(f"\n{len(target_numbers) - success_count} numeros no validados completamente")
            return False
        
    except Exception as e:
        print(f"Error durante la validacion: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_database_records():
    """
    Verifica que la base de datos contiene los registros esperados
    """
    print("\n" + "=" * 60)
    print("VERIFICACION DE BASE DE DATOS")
    print("=" * 60)
    
    try:
        db_path = "kronos.db"
        if not os.path.exists(db_path):
            print(f"Base de datos no encontrada: {db_path}")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar tabla de datos de operador celular (CLARO)
        cursor.execute("SELECT COUNT(*) FROM operator_cellular_data")
        claro_count = cursor.fetchone()[0]
        print(f"Registros operator_cellular_data: {claro_count}")
        
        # Verificar tabla de datos celulares (HUNTER)
        cursor.execute("SELECT COUNT(*) FROM cellular_data WHERE mission_id = 'mission_MPFRBNsb'")
        hunter_count = cursor.fetchone()[0]
        print(f"Registros cellular_data (HUNTER): {hunter_count}")
        
        # Verificar que existen números objetivo específicos en ambas tablas
        target_numbers = ["3143534707", "3224274851", "3208611034", "3104277553", "3102715509"]
        
        for number in target_numbers:
            # Buscar en call_data (número_origen, número_destino, número_objetivo)
            cursor.execute("""SELECT COUNT(*) FROM operator_call_data 
                             WHERE numero_origen = ? OR numero_destino = ? OR numero_objetivo = ?""", 
                          (number, number, number))
            call_count = cursor.fetchone()[0]
            
            # Buscar en cellular_data (numero_telefono)
            cursor.execute("SELECT COUNT(*) FROM operator_cellular_data WHERE numero_telefono = ?", (number,))
            cellular_count = cursor.fetchone()[0]
            
            total_count = call_count + cellular_count
            print(f"Numero {number}: {total_count} registros (calls: {call_count}, cellular: {cellular_count})")
        
        conn.close()
        
        if claro_count >= 3391 and hunter_count > 0:
            print("Base de datos verificada exitosamente")
            return True
        else:
            print("Base de datos no tiene los datos esperados")
            return False
        
    except Exception as e:
        print(f"Error verificando base de datos: {e}")
        return False

if __name__ == "__main__":
    print("INICIANDO TESTING DE VALIDACION BORIS")
    print("Testing Engineer: Claude Code")
    print("Fecha:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    # Verificar base de datos primero
    db_ok = verify_database_records()
    
    if db_ok:
        # Ejecutar validación de números objetivo
        validation_ok = test_boris_target_numbers()
        
        if validation_ok:
            print("\nTESTING COMPLETO: EXITO TOTAL")
            sys.exit(0)
        else:
            print("\nTESTING COMPLETO: VALIDACION PARCIAL")
            sys.exit(1)
    else:
        print("\nTESTING FALLIDO: PROBLEMAS DE BASE DE DATOS")
        sys.exit(2)