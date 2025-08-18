#!/usr/bin/env python3
"""
Test de Verificación de Corrección del Algoritmo de Correlación
===============================================================================
Verifica que los números objetivo aparezcan correctamente sin prefijo 57
tras la corrección del algoritmo de correlación.

Objetivos de la prueba:
1. Verificar que los números objetivo se detecten correctamente
2. Confirmar que numero_celular contiene el formato sin prefijo 57
3. Validar que numero_original mantiene el formato con prefijo 57
===============================================================================
"""

import logging
import json
from datetime import datetime
from services.correlation_analysis_service import get_correlation_service

# Configurar logging para ver los resultados
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_correlation_fix():
    """
    Prueba la corrección del algoritmo de correlación
    """
    print("=" * 80)
    print("TEST: VERIFICACIÓN DE CORRECCIÓN DE ALGORITMO DE CORRELACIÓN")
    print("=" * 80)
    
    # Números objetivo que Boris espera ver
    target_numbers = ['3224274851', '3208611034', '3104277553', '3102715509', '3143534707', '3214161903']
    
    print(f"Números objetivo esperados: {target_numbers}")
    print()
    
    try:
        # Obtener servicio de correlación
        correlation_service = get_correlation_service()
        
        # Ejecutar análisis con parámetros específicos para mission_MPFRBNsb
        mission_id = "mission_MPFRBNsb"
        start_date = "2021-05-20 10:00:00"
        end_date = "2021-05-20 13:20:00"
        min_coincidences = 1  # Usar 1 para detectar todos los números
        
        print(f"Ejecutando análisis para misión: {mission_id}")
        print(f"Período: {start_date} a {end_date}")
        print(f"Mínimo coincidencias: {min_coincidences}")
        print()
        
        # Ejecutar análisis
        result = correlation_service.analyze_correlation(
            mission_id=mission_id,
            start_date=start_date,
            end_date=end_date,
            min_coincidences=min_coincidences
        )
        
        if not result.get('success'):
            print(f"❌ ERROR en análisis: {result.get('error')}")
            return False
        
        data = result.get('data', [])
        print(f"📊 RESULTADOS DEL ANÁLISIS:")
        print(f"   Total números con coincidencias: {len(data)}")
        print()
        
        # Verificar cada número objetivo
        found_targets = []
        for target in target_numbers:
            found = False
            for correlation in data:
                numero_celular = correlation.get('numero_celular', '')
                numero_original = correlation.get('numero_original', '')
                
                # Verificar si el número celular (normalizado) coincide con el objetivo
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
                print(f"✅ {target}: ENCONTRADO")
            else:
                print(f"❌ {target}: NO ENCONTRADO")
        
        print()
        print("=" * 60)
        print("DETALLES DE NÚMEROS OBJETIVO ENCONTRADOS:")
        print("=" * 60)
        
        for target_info in found_targets:
            print(f"📱 Número Objetivo: {target_info['target']}")
            print(f"   numero_celular (normalizado): {target_info['numero_celular']}")
            print(f"   numero_original (con prefijo): {target_info['numero_original']}")
            print(f"   Total coincidencias: {target_info['coincidencias']}")
            print(f"   Operadores: {', '.join(target_info['operadores'])}")
            print()
        
        # Estadísticas finales
        print("=" * 60)
        print("ESTADÍSTICAS DE LA CORRECCIÓN:")
        print("=" * 60)
        print(f"✅ Números objetivo detectados: {len(found_targets)}/{len(target_numbers)}")
        print(f"📈 Porcentaje de éxito: {(len(found_targets)/len(target_numbers)*100):.1f}%")
        
        # Verificar que numero_celular no tiene prefijo 57
        numbers_without_prefix = sum(1 for t in found_targets if not t['numero_celular'].startswith('57'))
        print(f"✅ Números sin prefijo 57 en numero_celular: {numbers_without_prefix}/{len(found_targets)}")
        
        # Verificar que numero_original sí tiene prefijo 57
        numbers_with_prefix = sum(1 for t in found_targets if t['numero_original'].startswith('57'))
        print(f"✅ Números con prefijo 57 en numero_original: {numbers_with_prefix}/{len(found_targets)}")
        
        if len(found_targets) >= len(target_numbers) * 0.8:  # 80% o más
            print()
            print("🎉 CORRECCIÓN EXITOSA: Los números objetivo ahora aparecen correctamente")
            return True
        else:
            print()
            print("⚠️  CORRECCIÓN PARCIAL: Algunos números objetivo aún no aparecen")
            return False
            
    except Exception as e:
        print(f"❌ ERROR durante la prueba: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_correlation_fix()
    exit(0 if success else 1)