#!/usr/bin/env python3
"""
PRUEBA - Análisis con período extendido para incluir celda 56124
==============================================================
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.correlation_analysis_service import CorrelationAnalysisService
import logging

logging.basicConfig(level=logging.WARNING)

def test_periodo_extendido():
    service = CorrelationAnalysisService()
    
    print("PRUEBA CON PERIODO EXTENDIDO")
    print("=" * 40)
    
    mission_id = "mission_MPFRBNsb"
    # Extender hasta 14:45 para incluir celda 56124
    start_date = "2021-05-20 10:00:00"
    end_date = "2021-05-20 14:45:00"  # Extendido
    min_coincidences = 1
    
    print(f"Período extendido: {start_date} a {end_date}")
    print()
    
    # Ejecutar análisis
    result = service.analyze_correlation(
        mission_id=mission_id,
        start_date=start_date,
        end_date=end_date,
        min_coincidences=min_coincidences
    )
    
    if result.get('success'):
        print(f"Análisis exitoso: {len(result['data'])} números con coincidencias")
        
        # Buscar números objetivo específicos
        target_numbers = ['3102715509', '3224274851', '3104277553']
        
        print("\nVerificación de números objetivo:")
        print("-" * 30)
        
        found_count = 0
        
        for target in target_numbers:
            found = False
            for item in result['data']:
                if item['numero_celular'] == target:
                    found = True
                    found_count += 1
                    print(f"ENCONTRADO: {target}")
                    print(f"  Coincidencias: {item['total_coincidencias']}")
                    print(f"  Celdas: {list(item['celdas_detalle'].keys())}")
                    break
            
            if not found:
                print(f"NO ENCONTRADO: {target}")
        
        print(f"\nResultado: {found_count} de {len(target_numbers)} encontrados")
        
        if found_count > 0:
            print("✅ PROBLEMA PARCIALMENTE RESUELTO con período extendido")
        else:
            print("❌ Aún hay problemas que investigar")
    
    else:
        print(f"Error: {result.get('error')}")

if __name__ == "__main__":
    test_periodo_extendido()