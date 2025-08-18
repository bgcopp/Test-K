#!/usr/bin/env python3
"""
VALIDACIÓN DE FILTRADO POR OPERADOR
===================================

Test específico para validar que el nuevo filtrado por operador funciona correctamente
después de implementar las correcciones del agente de revisión de código.

OBJETIVOS:
1. Verificar que el filtrado por operador está funcionando
2. Confirmar que se detectan los números objetivo con filtrado
3. Validar que las correlaciones solo se hacen dentro del mismo operador
4. Comprobar que el rendimiento es aceptable

CONFIGURACIÓN:
- Misión: mission_MPFRBNsb
- Fecha inicio: 2021-05-20 10:00:00  
- Fecha fin: 2021-05-20 14:30:00
- Mínimo coincidencias: 1
"""

import sys
import os
import json
import time
from datetime import datetime

# Agregar el directorio Backend al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.correlation_analysis_service import CorrelationAnalysisService

# Números objetivo esperados
TARGET_NUMBERS = [
    '3143534707', '3224274851', '3208611034', 
    '3214161903', '3102715509'
]

# Configuración del test
TEST_CONFIG = {
    'mission_id': 'mission_MPFRBNsb',
    'start_date': '2021-05-20 10:00:00',
    'end_date': '2021-05-20 14:30:00',
    'min_coincidences': 1
}

def test_operator_filtering():
    """Ejecuta test completo del filtrado por operador"""
    
    print("=" * 80)
    print("🧪 VALIDACIÓN DE FILTRADO POR OPERADOR")
    print("=" * 80)
    print()
    
    try:
        # Inicializar servicio
        start_time = time.time()
        service = CorrelationAnalysisService()
        
        print("📋 CONFIGURACIÓN DEL TEST:")
        print(f"   - Misión: {TEST_CONFIG['mission_id']}")
        print(f"   - Fecha inicio: {TEST_CONFIG['start_date']}")
        print(f"   - Fecha fin: {TEST_CONFIG['end_date']}")
        print(f"   - Min. coincidencias: {TEST_CONFIG['min_coincidences']}")
        print()
        
        # Ejecutar análisis con filtrado por operador
        print("🔍 Ejecutando análisis CON filtrado por operador...")
        
        result = service.analyze_correlation(
            mission_id=TEST_CONFIG['mission_id'],
            start_date=TEST_CONFIG['start_date'],
            end_date=TEST_CONFIG['end_date'],
            min_coincidences=TEST_CONFIG['min_coincidences']
        )
        
        processing_time = time.time() - start_time
        
        if not result['success']:
            print(f"❌ ERROR: {result.get('error', 'Error desconocido')}")
            return False
        
        # Obtener correlaciones (con nuevo formato)
        correlations = result.get('correlations', [])
        statistics = result.get('statistics', {})
        
        print(f"✅ Análisis completado en {processing_time:.2f} segundos")
        print(f"📊 Correlaciones encontradas: {len(correlations)}")
        print()
        
        # Verificar estadísticas
        print("📈 ESTADÍSTICAS DEL ANÁLISIS:")
        print(f"   - Números analizados: {statistics.get('total_numeros_analizados', 0)}")
        print(f"   - Máx. coincidencias: {statistics.get('max_coincidencias', 0)}")
        print(f"   - Promedio coincidencias: {statistics.get('promedio_coincidencias', 0):.2f}")
        print(f"   - Registros HUNTER: {statistics.get('total_celdas_hunter', 0)}")
        print()
        
        # Verificar que el filtrado por operador se aplicó
        print("🔍 VERIFICACIÓN DE FILTRADO POR OPERADOR:")
        
        # Contar operadores únicos en resultados
        operators_in_results = set()
        operator_counts = {}
        
        for corr in correlations:
            operators = corr.get('operadores', [])
            for op in operators:
                operators_in_results.add(op)
                operator_counts[op] = operator_counts.get(op, 0) + 1
        
        print(f"   - Operadores detectados: {sorted(list(operators_in_results))}")
        for op, count in sorted(operator_counts.items()):
            print(f"   - {op}: {count} números correlacionados")
        
        # Verificar que hay filtrado por operador en los resultados
        has_operator_filtering = any(
            corr.get('filtrado_por_operador', False) for corr in correlations
        )
        print(f"   - Filtrado por operador aplicado: {'✅ SÍ' if has_operator_filtering else '❌ NO'}")
        print()
        
        # Validar números objetivo
        print("🎯 VALIDACIÓN DE NÚMEROS OBJETIVO:")
        print("-" * 50)
        
        found_targets = []
        missing_targets = []
        
        for target in TARGET_NUMBERS:
            found = False
            for corr in correlations:
                if corr.get('numero_celular') == target:
                    found_targets.append({
                        'numero': target,
                        'coincidencias': corr.get('total_coincidencias', 0),
                        'operadores': corr.get('operadores', []),
                        'celdas': len(corr.get('celdas_coincidentes', []))
                    })
                    found = True
                    break
            
            if not found:
                missing_targets.append(target)
        
        # Mostrar resultados
        for target in found_targets:
            ops_str = ', '.join(target['operadores'])
            print(f"✅ {target['numero']}: {target['coincidencias']} coincidencias ({ops_str})")
        
        for target in missing_targets:
            print(f"❌ {target}: NO ENCONTRADO")
        
        print()
        
        # Generar reporte final
        print("=" * 80)
        print("🏆 REPORTE FINAL DE VALIDACIÓN")
        print("=" * 80)
        
        success_all_found = len(found_targets) == len(TARGET_NUMBERS)
        success_has_results = len(correlations) > 0
        success_has_filtering = has_operator_filtering
        success_performance = processing_time < 30.0  # Menos de 30 segundos
        
        print("📊 CRITERIOS DE ÉXITO:")
        print(f"   {'✅' if success_all_found else '❌'} Todos los números objetivo encontrados ({len(found_targets)}/{len(TARGET_NUMBERS)})")
        print(f"   {'✅' if success_has_results else '❌'} Resultados no vacíos ({len(correlations)} correlaciones)")
        print(f"   {'✅' if success_has_filtering else '❌'} Filtrado por operador aplicado")
        print(f"   {'✅' if success_performance else '❌'} Rendimiento aceptable ({processing_time:.2f}s)")
        print()
        
        if missing_targets:
            print(f"❌ NÚMEROS FALTANTES: {', '.join(missing_targets)}")
        
        # Resultado final
        all_criteria_met = (success_all_found and success_has_results and 
                           success_has_filtering and success_performance)
        
        print()
        print("=" * 80)
        if all_criteria_met:
            print("🎉 ¡VALIDACIÓN COMPLETADA EXITOSAMENTE!")
            print("✅ El filtrado por operador funciona correctamente")
            print("✅ Todos los números objetivo aparecen en resultados")
            print("✅ Las correcciones del code reviewer fueron exitosas")
            print("✅ LISTO PARA PRUEBA PLAYWRIGHT")
        else:
            print("❌ VALIDACIÓN FALLIDA")
            print("⚠️ Algunos criterios no fueron cumplidos")
            print("⚠️ Se requieren correcciones adicionales")
        print("=" * 80)
        
        # Guardar reporte
        report = {
            'timestamp': datetime.now().isoformat(),
            'test_config': TEST_CONFIG,
            'target_numbers': TARGET_NUMBERS,
            'processing_time_seconds': processing_time,
            'results': {
                'total_correlations': len(correlations),
                'targets_found': len(found_targets),
                'targets_missing': len(missing_targets),
                'operators_detected': sorted(list(operators_in_results)),
                'operator_filtering_applied': has_operator_filtering,
                'all_criteria_met': all_criteria_met
            },
            'found_targets': found_targets,
            'missing_targets': missing_targets,
            'statistics': statistics
        }
        
        report_file = f"operator_filtering_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Reporte guardado en: {report_file}")
        
        return all_criteria_met
        
    except Exception as e:
        print(f"❌ ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = test_operator_filtering()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error fatal durante la validación: {e}")
        sys.exit(1)