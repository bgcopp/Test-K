#!/usr/bin/env python3
"""
CERTIFICACION FINAL - NUMEROS OBJETIVO
=====================================

Test critico para certificar que los 5 numeros objetivo aparecen correctamente
despues de todas las correcciones implementadas.

NUMEROS OBJETIVO ESPERADOS:
- 3143534707 (3 coincidencias)
- 3224274851 (2 coincidencias)
- 3208611034 (2 coincidencias)
- 3214161903 (1 coincidencia)
- 3102715509 (1 coincidencia)

CONFIGURACION EXACTA:
- Mision: mission_MPFRBNsb
- Fecha inicio: 2021-05-20 10:00:00
- Fecha fin: 2021-05-20 14:30:00
- Minimo coincidencias: 1
"""

import sys
import os
import json
from datetime import datetime
import logging

# Agregar el directorio Backend al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.correlation_analysis_service import CorrelationAnalysisService

# Configuracion de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Numeros objetivo esperados
TARGET_NUMBERS = [
    {'number': '3143534707', 'expected_coincidences': 3},
    {'number': '3224274851', 'expected_coincidences': 2},
    {'number': '3208611034', 'expected_coincidences': 2},
    {'number': '3214161903', 'expected_coincidences': 1},
    {'number': '3102715509', 'expected_coincidences': 1}
]

# Configuracion del test
TEST_CONFIG = {
    'mission_id': 'mission_MPFRBNsb',
    'start_date': '2021-05-20 10:00:00',
    'end_date': '2021-05-20 14:30:00',
    'min_coincidences': 1
}

def test_correlation_analysis():
    """Ejecuta el analisis de correlacion y valida los numeros objetivo"""
    
    print("=" * 80)
    print("CERTIFICACION FINAL - NUMEROS OBJETIVO")
    print("=" * 80)
    print()
    
    try:
        # Inicializar servicio de correlacion
        logger.info("Inicializando servicio de correlacion...")
        correlation_service = CorrelationAnalysisService()
        
        # Configurar parametros
        print("CONFIGURACION DEL TEST:")
        print(f"   - Mision: {TEST_CONFIG['mission_id']}")
        print(f"   - Fecha inicio: {TEST_CONFIG['start_date']}")
        print(f"   - Fecha fin: {TEST_CONFIG['end_date']}")
        print(f"   - Min. coincidencias: {TEST_CONFIG['min_coincidences']}")
        print()
        
        # Ejecutar analisis de correlacion
        logger.info("Ejecutando analisis de correlacion...")
        print("Ejecutando analisis de correlacion...")
        
        result = correlation_service.analyze_correlation(
            mission_id=TEST_CONFIG['mission_id'],
            start_date=TEST_CONFIG['start_date'],
            end_date=TEST_CONFIG['end_date'],
            min_coincidences=TEST_CONFIG['min_coincidences']
        )
        
        if not result['success']:
            print(f"ERROR: {result.get('error', 'Error desconocido')}")
            return False
        
        data = result.get('data', [])
        statistics = result.get('statistics', {})
        
        print(f"Analisis completado exitosamente")
        print(f"Resultados encontrados: {len(data)}")
        print()
        
        # Mostrar estadisticas
        print("ESTADISTICAS DEL ANALISIS:")
        print(f"   - Numeros analizados: {statistics.get('total_numeros_analizados', 0)}")
        print(f"   - Max. coincidencias: {statistics.get('max_coincidencias', 0)}")
        print(f"   - Promedio coincidencias: {statistics.get('promedio_coincidencias', 0)}")
        print(f"   - Registros HUNTER: {statistics.get('total_celdas_hunter', 0)}")
        print()
        
        # Validar numeros objetivo
        print("VALIDACION DE NUMEROS OBJETIVO:")
        print("-" * 50)
        
        found_numbers = []
        missing_numbers = []
        incorrect_coincidences = []
        format_errors = []
        
        for target in TARGET_NUMBERS:
            target_number = target['number']
            expected_coincidences = target['expected_coincidences']
            
            # Buscar el numero en los resultados
            found_result = None
            for item in data:
                if str(item.get('numero_celular', '')).strip() == target_number:
                    found_result = item
                    break
            
            if found_result:
                actual_coincidences = found_result.get('total_coincidencias', 0)
                numero_formato = str(found_result.get('numero_celular', '')).strip()
                
                # Verificar formato (sin prefijo 57)
                has_correct_format = not numero_formato.startswith('57')
                
                found_numbers.append({
                    'number': target_number,
                    'found': True,
                    'expected_coincidences': expected_coincidences,
                    'actual_coincidences': actual_coincidences,
                    'coincidences_match': actual_coincidences == expected_coincidences,
                    'correct_format': has_correct_format,
                    'format_value': numero_formato
                })
                
                status = "OK" if actual_coincidences == expected_coincidences else "WARN"
                format_status = "OK" if has_correct_format else "ERROR"
                
                print(f"[{status}] {target_number}:")
                print(f"   - Encontrado: SI")
                print(f"   - Formato correcto: {format_status} ({numero_formato})")
                print(f"   - Coincidencias: {actual_coincidences}/{expected_coincidences}")
                print(f"   - Operadores: {', '.join(found_result.get('operadores', []))}")
                
                if actual_coincidences != expected_coincidences:
                    incorrect_coincidences.append(target_number)
                
                if not has_correct_format:
                    format_errors.append(target_number)
                    
            else:
                missing_numbers.append(target_number)
                found_numbers.append({
                    'number': target_number,
                    'found': False,
                    'expected_coincidences': expected_coincidences,
                    'actual_coincidences': 0,
                    'coincidences_match': False,
                    'correct_format': False,
                    'format_value': 'N/A'
                })
                
                print(f"[MISSING] {target_number}:")
                print(f"   - Encontrado: NO")
                print(f"   - Estado: FALTANTE")
            
            print()
        
        # Generar reporte final
        print("=" * 80)
        print("REPORTE DE CERTIFICACION FINAL")
        print("=" * 80)
        
        total_found = len([n for n in found_numbers if n['found']])
        total_with_correct_coincidences = len([n for n in found_numbers if n['coincidences_match']])
        total_with_correct_format = len([n for n in found_numbers if n['correct_format']])
        
        print("RESUMEN EJECUTIVO:")
        print(f"   - Numeros objetivo encontrados: {total_found}/5")
        print(f"   - Coincidencias correctas: {total_with_correct_coincidences}/5")
        print(f"   - Formato correcto (sin prefijo 57): {total_with_correct_format}/5")
        print(f"   - Total resultados en analisis: {len(data)}")
        print()
        
        print("CRITERIOS DE EXITO:")
        success_all_found = total_found == 5
        success_correct_coincidences = total_with_correct_coincidences == 5
        success_correct_format = total_with_correct_format == 5
        success_has_results = len(data) > 0
        
        print(f"   [{'OK' if success_all_found else 'FAIL'}] Todos los numeros objetivo presentes")
        print(f"   [{'OK' if success_correct_coincidences else 'FAIL'}] Coincidencias correctas")
        print(f"   [{'OK' if success_correct_format else 'FAIL'}] Formato sin prefijo 57")
        print(f"   [{'OK' if success_has_results else 'FAIL'}] Resultados no vacios")
        print()
        
        if missing_numbers:
            print(f"NUMEROS FALTANTES: {', '.join(missing_numbers)}")
        
        if incorrect_coincidences:
            print(f"COINCIDENCIAS INCORRECTAS: {', '.join(incorrect_coincidences)}")
        
        if format_errors:
            print(f"ERRORES DE FORMATO: {', '.join(format_errors)}")
        
        # Resultado final
        all_criteria_met = (success_all_found and success_correct_coincidences and 
                           success_correct_format and success_has_results)
        
        print()
        print("=" * 80)
        if all_criteria_met:
            print("*** CERTIFICACION COMPLETADA EXITOSAMENTE ***")
            print("Todos los criterios de exito han sido cumplidos")
            print("Los numeros objetivo aparecen correctamente en KRONOS")
            print("Las correcciones implementadas funcionan perfectamente")
        else:
            print("*** CERTIFICACION FALLIDA ***")
            print("Algunos criterios de exito no fueron cumplidos")
            print("Se requieren correcciones adicionales")
        print("=" * 80)
        
        # Guardar reporte en JSON
        report = {
            'timestamp': datetime.now().isoformat(),
            'test_config': TEST_CONFIG,
            'target_numbers': TARGET_NUMBERS,
            'results': {
                'total_found': total_found,
                'total_with_correct_coincidences': total_with_correct_coincidences,
                'total_with_correct_format': total_with_correct_format,
                'total_results': len(data),
                'all_criteria_met': all_criteria_met
            },
            'detailed_results': found_numbers,
            'statistics': statistics,
            'missing_numbers': missing_numbers,
            'incorrect_coincidences': incorrect_coincidences,
            'format_errors': format_errors
        }
        
        report_file = f"certificacion_final_numeros_objetivo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"Reporte guardado en: {report_file}")
        
        return all_criteria_met
        
    except Exception as e:
        logger.error(f"Error durante la certificacion: {e}")
        print(f"ERROR CRITICO: {e}")
        return False

if __name__ == "__main__":
    try:
        success = test_correlation_analysis()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nCertificacion interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\nError fatal durante la certificacion: {e}")
        sys.exit(1)