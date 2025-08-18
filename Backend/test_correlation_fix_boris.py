#!/usr/bin/env python3
"""
PRUEBA URGENTE: Verificación del algoritmo de correlación corregido para Boris
===============================================================================

Este script verifica que el algoritmo corregido detecte correctamente los números
objetivo de Boris correlacionando por Cell IDs (NO buscando números en HUNTER).

NÚMEROS OBJETIVO BORIS:
- 3224274851, 3208611034, 3104277553, 3102715509, 3143534707, 3214161903

ALGORITMO CORREGIDO:
1. Extraer Cell IDs únicos de datos HUNTER (scanner)
2. Extraer números + Cell IDs de operator_call_data
3. Correlacionar por Cell ID coincidente
4. Retornar números que usaron celdas que también están en HUNTER
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.correlation_analysis_service import CorrelationAnalysisService
import logging
import json

# Configurar logging detallado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_correlation_fix():
    """Prueba el algoritmo de correlación corregido"""
    
    print("=" * 80)
    print("PRUEBA ALGORITMO DE CORRELACIÓN CORREGIDO PARA BORIS")
    print("=" * 80)
    
    # Inicializar servicio
    service = CorrelationAnalysisService()
    
    # Parámetros de prueba
    mission_id = "mission_MPFRBNsb"  # Misión disponible en la BD
    start_date = "2021-05-20 00:00:00"  # Período con datos conocidos
    end_date = "2021-05-20 23:59:59"
    min_coincidences = 1  # Mínimo para detectar cualquier coincidencia
    
    print(f"Misión: {mission_id}")
    print(f"Período: {start_date} a {end_date}")
    print(f"Min coincidencias: {min_coincidences}")
    print()
    
    # Ejecutar análisis
    print("EJECUTANDO ANÁLISIS DE CORRELACIÓN...")
    result = service.analyze_correlation(
        mission_id=mission_id,
        start_date=start_date,
        end_date=end_date,
        min_coincidences=min_coincidences
    )
    
    print()
    print("=" * 80)
    print("RESULTADOS DEL ANÁLISIS")
    print("=" * 80)
    
    if result['success']:
        data = result['data']
        stats = result['statistics']
        
        print(f"✓ Análisis completado exitosamente")
        print(f"✓ Tiempo de procesamiento: {result['processing_time_seconds']} segundos")
        print(f"✓ Números correlacionados: {len(data)}")
        print()
        
        # Mostrar estadísticas
        print("ESTADÍSTICAS:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        print()
        
        # Verificar números objetivo de Boris
        target_numbers = ['3224274851', '3208611034', '3104277553', '3102715509', '3143534707', '3214161903']
        print("VERIFICACIÓN NÚMEROS OBJETIVO BORIS:")
        
        found_targets = []
        for item in data:
            numero_celular = item['numero_celular']
            numero_original = item.get('numero_original', numero_celular)
            
            # Normalizar y comparar
            for target in target_numbers:
                target_norm = service._normalize_phone_number(target)
                if numero_celular == target_norm:
                    found_targets.append({
                        'objetivo': target,
                        'encontrado_como': numero_original,
                        'coincidencias': item['total_coincidencias'],
                        'celdas': item.get('celdas_coincidentes', []),
                        'operadores': item.get('operadores', [])
                    })
                    break
        
        if found_targets:
            print(f"✓ ÉXITO: {len(found_targets)} números objetivo detectados:")
            for target in found_targets:
                print(f"  • {target['objetivo']} ({target['encontrado_como']})")
                print(f"    Celdas coincidentes: {target['coincidencias']}")
                print(f"    Cell IDs: {target['celdas']}")
                print(f"    Operadores: {target['operadores']}")
                print()
        else:
            print("✗ PROBLEMA: No se detectaron números objetivo")
            print("  Verificando primeros resultados encontrados:")
            for i, item in enumerate(data[:5], 1):
                print(f"  {i}. {item.get('numero_original', item['numero_celular'])} -> {item['total_coincidencias']} celdas")
        
        # Mostrar top 10 resultados
        print()
        print("TOP 10 NÚMEROS CON MÁS COINCIDENCIAS:")
        for i, item in enumerate(data[:10], 1):
            numero_orig = item.get('numero_original', item['numero_celular'])
            print(f"  {i:2d}. {numero_orig} -> {item['total_coincidencias']} celdas ({item.get('operadores', [])})")
        
        # Guardar resultados detallados
        output_file = "test_correlation_fix_boris_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n✓ Resultados guardados en: {output_file}")
        
    else:
        print(f"✗ Error en el análisis: {result.get('error', 'Error desconocido')}")
    
    print()
    print("=" * 80)

if __name__ == "__main__":
    try:
        test_correlation_fix()
    except Exception as e:
        logger.error(f"Error en la prueba: {e}", exc_info=True)
        print(f"\n✗ ERROR: {e}")