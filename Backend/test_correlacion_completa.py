#!/usr/bin/env python3
"""
PRUEBA CORRELACIÓN COMPLETA - Con ajustes Fase 1
===============================================
Verificar que los números objetivo aparezcan en análisis completo
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.correlation_analysis_service import CorrelationAnalysisService
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)

def test_full_correlation():
    """Probar análisis de correlación completo."""
    print("PRUEBA: Análisis de correlación completo con ajustes Fase 1")
    print("=" * 70)
    
    service = CorrelationAnalysisService()
    
    # Parámetros del análisis
    mission_id = "mission_MPFRBNsb"
    start_date = "2021-05-20 10:00:00"
    end_date = "2021-05-20 13:30:00"
    min_coincidences = 1  # Mínimo para ver todos los resultados
    
    print(f"Misión: {mission_id}")
    print(f"Fecha inicio: {start_date}")
    print(f"Fecha fin: {end_date}")
    print(f"Coincidencias mínimas: {min_coincidences}")
    print()
    
    # Ejecutar análisis
    result = service.analyze_correlation(
        mission_id=mission_id,
        start_date=start_date,
        end_date=end_date,
        min_coincidences=min_coincidences
    )
    
    if result.get('success'):
        print("✅ ANÁLISIS EXITOSO")
        print(f"Total resultados: {len(result['data'])}")
        print()
        
        # Buscar números objetivo de Boris
        target_numbers = ['3224274851', '3208611034', '3104277553', '3102715509', '3143534707']
        
        print("VERIFICACIÓN DE NÚMEROS OBJETIVO:")
        print("-" * 40)
        
        found_targets = 0
        
        for target in target_numbers:
            found = False
            for item in result['data']:
                if item['numero_celular'] == target:
                    found = True
                    found_targets += 1
                    print(f"✅ {target} -> {item['total_coincidencias']} coincidencias")
                    print(f"   Celdas: {list(item['celdas_detalle'].keys())}")
                    print(f"   Operadores: {item['operadores']}")
                    break
            
            if not found:
                print(f"❌ {target} -> NO encontrado en resultados")
        
        print()
        print(f"RESUMEN: {found_targets} de {len(target_numbers)} números objetivo encontrados")
        
        # Mostrar top 5 resultados
        print(f"\nTOP 5 RESULTADOS:")
        print("-" * 30)
        
        for i, item in enumerate(result['data'][:5]):
            print(f"{i+1}. {item['numero_celular']} -> {item['total_coincidencias']} coincidencias")
    
    else:
        print("❌ ERROR EN ANÁLISIS:")
        print(f"   {result.get('error', 'Error desconocido')}")

if __name__ == "__main__":
    test_full_correlation()