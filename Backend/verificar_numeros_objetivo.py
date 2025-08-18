#!/usr/bin/env python3
"""
VERIFICACION RAPIDA - Numeros objetivo en resultados
===================================================
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.correlation_analysis_service import CorrelationAnalysisService
import logging

# Reducir logging para ver solo resultados importantes
logging.basicConfig(level=logging.WARNING)

def verificar_numeros():
    service = CorrelationAnalysisService()
    
    # Parametros del analisis
    mission_id = "mission_MPFRBNsb"
    start_date = "2021-05-20 10:00:00"
    end_date = "2021-05-20 13:30:00"
    min_coincidences = 1
    
    print("VERIFICACION DE NUMEROS OBJETIVO DE BORIS")
    print("=" * 50)
    print(f"Mision: {mission_id}")
    print(f"Periodo: {start_date} a {end_date}")
    print()
    
    # Ejecutar analisis
    result = service.analyze_correlation(
        mission_id=mission_id,
        start_date=start_date,
        end_date=end_date,
        min_coincidences=min_coincidences
    )
    
    if result.get('success'):
        total_results = len(result['data'])
        print(f"ANALISIS EXITOSO: {total_results} numeros con coincidencias")
        print()
        
        # Numeros objetivo de Boris
        target_numbers = ['3224274851', '3208611034', '3104277553', '3102715509', '3143534707']
        
        print("RESULTADO DE NUMEROS OBJETIVO:")
        print("-" * 40)
        
        found_count = 0
        
        for target in target_numbers:
            found = False
            for item in result['data']:
                if item['numero_celular'] == target:
                    found = True
                    found_count += 1
                    coincidencias = item['total_coincidencias']
                    celdas = list(item['celdas_detalle'].keys())
                    operadores = item['operadores']
                    
                    print(f"ENCONTRADO: {target}")
                    print(f"  Coincidencias: {coincidencias}")
                    print(f"  Celdas: {celdas}")
                    print(f"  Operadores: {operadores}")
                    print()
                    break
            
            if not found:
                print(f"NO ENCONTRADO: {target}")
        
        print(f"RESUMEN FINAL:")
        print(f"  Encontrados: {found_count} de {len(target_numbers)} numeros objetivo")
        print(f"  Porcentaje exito: {(found_count/len(target_numbers)*100):.1f}%")
        
        if found_count >= 4:
            print("  RESULTADO: EXCELENTE - Ajustes Fase 1 funcionan correctamente")
        elif found_count >= 2:
            print("  RESULTADO: BUENO - Mejora significativa detectada")
        else:
            print("  RESULTADO: Requiere ajustes adicionales")
    
    else:
        print(f"ERROR EN ANALISIS: {result.get('error', 'Error desconocido')}")

if __name__ == "__main__":
    verificar_numeros()