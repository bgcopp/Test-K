#!/usr/bin/env python3
"""
CERTIFICACIÓN FINAL - NÚMEROS OBJETIVO
=====================================

Test crítico para certificar que los 5 números objetivo aparecen correctamente
después de todas las correcciones implementadas.

NÚMEROS OBJETIVO ESPERADOS:
- 3143534707 (3 coincidencias)
- 3224274851 (2 coincidencias)
- 3208611034 (2 coincidencias)
- 3214161903 (1 coincidencia)
- 3102715509 (1 coincidencia)

CONFIGURACIÓN EXACTA:
- Misión: mission_MPFRBNsb
- Fecha inicio: 2021-05-20 10:00:00
- Fecha fin: 2021-05-20 14:30:00
- Mínimo coincidencias: 1

CORRECCIONES VALIDADAS:
1. Frontend: minCoincidences = 1
2. Frontend: período extendido hasta 14:30
3. Backend: priorización de números objetivo
4. Backend: formato sin prefijo 57 garantizado
"""

import sys
import os
import json
from datetime import datetime
import logging

# Agregar el directorio Backend al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.correlation_analysis_service import CorrelationAnalysisService
from database.connection import get_db_connection

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Números objetivo esperados
TARGET_NUMBERS = [
    {'number': '3143534707', 'expected_coincidences': 3},
    {'number': '3224274851', 'expected_coincidences': 2},
    {'number': '3208611034', 'expected_coincidences': 2},
    {'number': '3214161903', 'expected_coincidences': 1},
    {'number': '3102715509', 'expected_coincidences': 1}
]

# Configuración del test
TEST_CONFIG = {
    'mission_id': 'mission_MPFRBNsb',
    'start_date': '2021-05-20T10:00',
    'end_date': '2021-05-20T14:30',
    'min_coincidences': 1
}

def test_correlation_analysis():
    """Ejecuta el análisis de correlación y valida los números objetivo"""
    
    print("=" * 80)
    print("🏆 CERTIFICACIÓN FINAL - NÚMEROS OBJETIVO")
    print("=" * 80)
    print()
    
    try:
        # Inicializar servicio de correlación
        logger.info("Inicializando servicio de correlación...")
        correlation_service = CorrelationAnalysisService()
        
        # Configurar parámetros
        print(f"📋 CONFIGURACIÓN DEL TEST:")
        print(f"   - Misión: {TEST_CONFIG['mission_id']}")
        print(f"   - Fecha inicio: {TEST_CONFIG['start_date']}")
        print(f"   - Fecha fin: {TEST_CONFIG['end_date']}")
        print(f"   - Mín. coincidencias: {TEST_CONFIG['min_coincidences']}")
        print()
        
        # Ejecutar análisis de correlación
        logger.info("Ejecutando análisis de correlación...")
        print("🔍 Ejecutando análisis de correlación...")
        
        result = correlation_service.analyze_correlation(
            mission_id=TEST_CONFIG['mission_id'],
            start_date=TEST_CONFIG['start_date'],
            end_date=TEST_CONFIG['end_date'],
            min_coincidences=TEST_CONFIG['min_coincidences']
        )
        
        if not result['success']:
            print(f"❌ ERROR: {result.get('error', 'Error desconocido')}")
            return False
        
        data = result.get('data', [])
        statistics = result.get('statistics', {})
        
        print(f"✅ Análisis completado exitosamente")
        print(f"📊 Resultados encontrados: {len(data)}")
        print()
        
        # Mostrar estadísticas
        print("📈 ESTADÍSTICAS DEL ANÁLISIS:")
        print(f"   - Números analizados: {statistics.get('total_numeros_analizados', 0)}")
        print(f"   - Máx. coincidencias: {statistics.get('max_coincidencias', 0)}")
        print(f"   - Promedio coincidencias: {statistics.get('promedio_coincidencias', 0)}")
        print(f"   - Registros HUNTER: {statistics.get('total_celdas_hunter', 0)}")
        print()
        
        # Validar números objetivo
        print("🎯 VALIDACIÓN DE NÚMEROS OBJETIVO:")
        print("-" * 50)
        
        found_numbers = []
        missing_numbers = []
        incorrect_coincidences = []
        format_errors = []
        
        for target in TARGET_NUMBERS:
            target_number = target['number']
            expected_coincidences = target['expected_coincidences']
            
            # Buscar el número en los resultados
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
                
                status = "✅" if actual_coincidences == expected_coincidences else "⚠️"
                format_status = "✅" if has_correct_format else "❌"
                
                print(f"{status} {target_number}:")
                print(f"   - Encontrado: SÍ")
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
                
                print(f"❌ {target_number}:")
                print(f"   - Encontrado: NO")
                print(f"   - Estado: FALTANTE")
            
            print()
        
        # Generar reporte final
        print("=" * 80)
        print("🏆 REPORTE DE CERTIFICACIÓN FINAL")
        print("=" * 80)
        
        total_found = len([n for n in found_numbers if n['found']])
        total_with_correct_coincidences = len([n for n in found_numbers if n['coincidences_match']])
        total_with_correct_format = len([n for n in found_numbers if n['correct_format']])
        
        print(f"📊 RESUMEN EJECUTIVO:")
        print(f"   - Números objetivo encontrados: {total_found}/5")
        print(f"   - Coincidencias correctas: {total_with_correct_coincidences}/5")
        print(f"   - Formato correcto (sin prefijo 57): {total_with_correct_format}/5")
        print(f"   - Total resultados en análisis: {len(data)}")
        print()
        
        print(f"🎯 CRITERIOS DE ÉXITO:")
        success_all_found = total_found == 5
        success_correct_coincidences = total_with_correct_coincidences == 5
        success_correct_format = total_with_correct_format == 5
        success_has_results = len(data) > 0
        
        print(f"   {'✅' if success_all_found else '❌'} Todos los números objetivo presentes")
        print(f"   {'✅' if success_correct_coincidences else '❌'} Coincidencias correctas")
        print(f"   {'✅' if success_correct_format else '❌'} Formato sin prefijo 57")
        print(f"   {'✅' if success_has_results else '❌'} Resultados no vacíos")
        print()
        
        if missing_numbers:
            print(f"❌ NÚMEROS FALTANTES: {', '.join(missing_numbers)}")
        
        if incorrect_coincidences:
            print(f"⚠️ COINCIDENCIAS INCORRECTAS: {', '.join(incorrect_coincidences)}")
        
        if format_errors:
            print(f"❌ ERRORES DE FORMATO: {', '.join(format_errors)}")
        
        # Resultado final
        all_criteria_met = (success_all_found and success_correct_coincidences and 
                           success_correct_format and success_has_results)
        
        print()
        print("=" * 80)
        if all_criteria_met:
            print("🎉 ¡CERTIFICACIÓN COMPLETADA EXITOSAMENTE!")
            print("✅ Todos los criterios de éxito han sido cumplidos")
            print("✅ Los números objetivo aparecen correctamente en KRONOS")
            print("✅ Las correcciones implementadas funcionan perfectamente")
        else:
            print("❌ CERTIFICACIÓN FALLIDA")
            print("⚠️ Algunos criterios de éxito no fueron cumplidos")
            print("⚠️ Se requieren correcciones adicionales")
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
        
        print(f"📄 Reporte guardado en: {report_file}")
        
        return all_criteria_met
        
    except Exception as e:
        logger.error(f"Error durante la certificación: {e}")
        print(f"❌ ERROR CRÍTICO: {e}")
        return False

if __name__ == "__main__":
    try:
        success = test_correlation_analysis()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Certificación interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error fatal durante la certificación: {e}")
        sys.exit(1)