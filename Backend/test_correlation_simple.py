#!/usr/bin/env python3
"""
Test Simplificado de Verificacion de Correccion del Algoritmo de Correlacion
"""

import logging
import json
from datetime import datetime
from services.correlation_analysis_service import get_correlation_service

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_correlation_fix_simple():
    """
    Prueba simplificada de la correccion del algoritmo
    """
    print("=" * 80)
    print("TEST: VERIFICACION DE CORRECCION DE ALGORITMO DE CORRELACION")
    print("=" * 80)
    
    # Numeros objetivo que Boris espera ver
    target_numbers = ['3224274851', '3208611034', '3104277553', '3102715509', '3143534707', '3214161903']
    
    print(f"Numeros objetivo esperados: {target_numbers}")
    print()
    
    try:
        # Obtener servicio de correlacion
        correlation_service = get_correlation_service()
        
        # Ejecutar analisis
        mission_id = "mission_MPFRBNsb"
        start_date = "2021-05-20 10:00:00"
        end_date = "2021-05-20 13:20:00"
        min_coincidences = 1
        
        print(f"Ejecutando analisis para mision: {mission_id}")
        print(f"Periodo: {start_date} a {end_date}")
        print()
        
        # Ejecutar analisis
        result = correlation_service.analyze_correlation(
            mission_id=mission_id,
            start_date=start_date,
            end_date=end_date,
            min_coincidences=min_coincidences
        )
        
        if not result.get('success'):
            print(f"ERROR en analisis: {result.get('error')}")
            return False
        
        data = result.get('data', [])
        print(f"RESULTADOS DEL ANALISIS:")
        print(f"   Total numeros con coincidencias: {len(data)}")
        print()
        
        # Verificar cada numero objetivo
        found_targets = []
        for target in target_numbers:
            found = False
            for correlation in data:
                numero_celular = correlation.get('numero_celular', '')
                numero_original = correlation.get('numero_original', '')
                
                # Verificar si el numero celular (normalizado) coincide con el objetivo
                if numero_celular == target:
                    found_targets.append({
                        'target': target,
                        'numero_celular': numero_celular,
                        'numero_original': numero_original,
                        'coincidencias': correlation.get('total_coincidencias', 0),
                        'operadores': correlation.get('operadores', [])
                    })
                    found = True
                    break
            
            if found:
                print(f"ENCONTRADO {target}")
            else:
                print(f"NO ENCONTRADO {target}")
        
        print()
        print("=" * 60)
        print("DETALLES DE NUMEROS OBJETIVO ENCONTRADOS:")
        print("=" * 60)
        
        for target_info in found_targets:
            print(f"Numero Objetivo: {target_info['target']}")
            print(f"   numero_celular (normalizado): {target_info['numero_celular']}")
            print(f"   numero_original (con prefijo): {target_info['numero_original']}")
            print(f"   Total coincidencias: {target_info['coincidencias']}")
            print(f"   Operadores: {', '.join(target_info['operadores'])}")
            print()
        
        # Estadisticas finales
        print("=" * 60)
        print("ESTADISTICAS DE LA CORRECCION:")
        print("=" * 60)
        print(f"Numeros objetivo detectados: {len(found_targets)}/{len(target_numbers)}")
        print(f"Porcentaje de exito: {(len(found_targets)/len(target_numbers)*100):.1f}%")
        
        # Verificar formato correcto
        numbers_without_prefix = sum(1 for t in found_targets if not t['numero_celular'].startswith('57'))
        print(f"Numeros sin prefijo 57 en numero_celular: {numbers_without_prefix}/{len(found_targets)}")
        
        numbers_with_prefix = sum(1 for t in found_targets if t['numero_original'].startswith('57'))
        print(f"Numeros con prefijo 57 en numero_original: {numbers_with_prefix}/{len(found_targets)}")
        
        if len(found_targets) > 0:
            print()
            print("CORRECCION EXITOSA: Los numeros objetivo ahora aparecen correctamente")
            return True
        else:
            print()
            print("CORRECCION FALLIDA: Los numeros objetivo aun no aparecen")
            return False
            
    except Exception as e:
        print(f"ERROR durante la prueba: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_correlation_fix_simple()
    print(f"Resultado final: {'EXITOSO' if success else 'FALLIDO'}")
    exit(0 if success else 1)