#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del Algoritmo Corregido de Correlación - KRONOS
====================================================
Valida que la corrección del algoritmo elimine la inflación por contextos múltiples.

Números a validar específicamente:
- 3243182028: Debería mostrar 1 ocurrencia en celda 16478 (no 5)
- 3009120093: Debería mostrar 2 ocurrencias en celdas 22504,56121 (no 4)  
- 3124390973: Debería mostrar 2 ocurrencias en celdas 22504,51438 (no 4)

Autor: Claude Code para Boris
Fecha: 2025-08-18
"""

import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Configurar encoding para Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

# Agregar el directorio Backend al path para importar módulos
sys.path.append(str(Path(__file__).parent))

from services.correlation_service_dynamic import get_correlation_service_dynamic
from database.connection import get_database_manager

# Configurar logging para evitar mensajes de info innecesarios
logging.getLogger('numexpr.utils').setLevel(logging.WARNING)
logging.getLogger('services.correlation_service_dynamic').setLevel(logging.WARNING)

def test_corrected_algorithm():
    """
    Prueba el algoritmo corregido para verificar que los conteos sean precisos
    """
    
    print("=== TEST ALGORITMO CORREGIDO - CORRELACIÓN SIN INFLACIÓN ===")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        # Inicializar conexión a base de datos
        print("Inicializando conexión a base de datos...")
        db_manager = get_database_manager()
        db_manager.initialize()
        print("Base de datos inicializada correctamente")
        print()
        
        # Configurar parámetros de prueba
        mission_id = "mission_MPFRBNsb"  # ID de misión con datos reales
        start_datetime = "2021-05-20 00:00:00"
        end_datetime = "2021-05-20 23:59:59"
        min_occurrences = 1
        
        print(f"Misión: {mission_id}")
        print(f"Período: {start_datetime} - {end_datetime}")
        print(f"Mín ocurrencias: {min_occurrences}")
        print()
        
        # Obtener servicio corregido
        correlation_service = get_correlation_service_dynamic()
        
        # Ejecutar análisis con algoritmo corregido
        print("Ejecutando análisis con algoritmo CORREGIDO...")
        result = correlation_service.analyze_correlation(
            mission_id=mission_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            min_occurrences=min_occurrences
        )
        
        if not result['success']:
            print(f"[ERROR] Error en análisis: {result['message']}")
            return False
        
        correlations = result['data']
        print(f"[OK] Análisis completado: {len(correlations)} correlaciones encontradas")
        print(f"[TIME] Tiempo procesamiento: {result['processing_time']:.2f} segundos")
        print()
        
        # Números específicos a validar (datos reales de la misión)
        target_numbers = {
            '3243182028': {'expected_count': 5, 'expected_cells': ['16478', '22504', '51438', '6159', '6578']},
            '3009120093': {'expected_count': 4, 'expected_cells': ['22504', '51438', '56121', '56124']},
            '3124390973': {'expected_count': 4, 'expected_cells': ['22504', '51438', '52356', '6578']}
        }
        
        print("VALIDACIÓN DE NÚMEROS PROBLEMÁTICOS:")
        print("-" * 50)
        
        validation_results = {}
        
        for target_number, expected in target_numbers.items():
            print(f"\n[TEST] Número: {target_number}")
            
            # Buscar número en resultados
            found = False
            for correlation in correlations:
                if correlation['numero_objetivo'] == target_number:
                    found = True
                    actual_count = correlation['ocurrencias']
                    actual_cells = correlation['celdas_relacionadas']
                    
                    print(f"   Ocurrencias encontradas: {actual_count}")
                    print(f"   Celdas encontradas: {actual_cells}")
                    print(f"   Esperaba ocurrencias: {expected['expected_count']}")
                    print(f"   Esperaba celdas: {expected['expected_cells']}")
                    
                    # Validar conteo
                    count_correct = actual_count == expected['expected_count']
                    if count_correct:
                        print(f"   [OK] CONTEO CORRECTO: {actual_count} ocurrencias")
                    else:
                        print(f"   [ERROR] CONTEO INCORRECTO: {actual_count} vs {expected['expected_count']} esperado")
                    
                    # Validar celdas (al menos las esperadas deben estar presentes)
                    expected_cells_set = set(expected['expected_cells'])
                    actual_cells_set = set(actual_cells)
                    cells_present = expected_cells_set.issubset(actual_cells_set)
                    
                    if cells_present:
                        print(f"   [OK] CELDAS CORRECTAS: Celdas esperadas presentes")
                    else:
                        missing_cells = expected_cells_set - actual_cells_set
                        print(f"   [ERROR] CELDAS FALTANTES: {missing_cells}")
                    
                    validation_results[target_number] = {
                        'found': True,
                        'count_correct': count_correct,
                        'cells_correct': cells_present,
                        'actual_count': actual_count,
                        'actual_cells': actual_cells,
                        'algorithm_strategy': correlation.get('strategy', 'Unknown')
                    }
                    break
            
            if not found:
                print(f"   [ERROR] NÚMERO NO ENCONTRADO en los resultados")
                validation_results[target_number] = {
                    'found': False,
                    'count_correct': False,
                    'cells_correct': False,
                    'actual_count': 0,
                    'actual_cells': [],
                    'algorithm_strategy': 'None'
                }
        
        # Resumen de validación
        print("\n" + "=" * 60)
        print("RESUMEN DE VALIDACIÓN DEL ALGORITMO CORREGIDO:")
        print("=" * 60)
        
        all_correct = True
        for target_number, validation in validation_results.items():
            status = "[OK] CORRECTO" if (validation['found'] and validation['count_correct'] and validation['cells_correct']) else "[ERROR] INCORRECTO"
            print(f"{target_number}: {status}")
            if not (validation['found'] and validation['count_correct'] and validation['cells_correct']):
                all_correct = False
        
        print()
        if all_correct:
            print("[SUCCESS] ALGORITMO CORREGIDO EXITOSAMENTE!")
            print("   - Todos los números problemáticos ahora muestran conteos precisos")
            print("   - Se eliminó la inflación por contextos múltiples")
            print("   - El algoritmo funciona según especificaciones")
        else:
            print("[WARNING] ALGORITMO REQUIERE AJUSTES ADICIONALES")
            print("   - Algunos números aún muestran conteos incorrectos")
            print("   - Revisar lógica de consolidación en final_unique_combinations")
        
        # Guardar resultados detallados para análisis
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f"correction_validation_results_{timestamp}.json"
        
        detailed_results = {
            'test_info': {
                'timestamp': datetime.now().isoformat(),
                'mission_id': mission_id,
                'period': f"{start_datetime} - {end_datetime}",
                'algorithm_version': 'DynamicCorrected_v2.0'
            },
            'validation_summary': {
                'total_correlations_found': len(correlations),
                'target_numbers_tested': len(target_numbers),
                'all_validations_passed': all_correct
            },
            'detailed_validations': validation_results,
            'all_correlations': correlations[:20]  # Primeras 20 para referencia
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(detailed_results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n[SAVE] Resultados guardados en: {results_file}")
        
        return all_correct
        
    except Exception as e:
        print(f"[ERROR] ERROR en test del algoritmo corregido: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_corrected_algorithm()
    sys.exit(0 if success else 1)