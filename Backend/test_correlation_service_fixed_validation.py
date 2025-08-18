#!/usr/bin/env python3
"""
VALIDACIÓN CRÍTICA DEL SERVICIO DE CORRELACIÓN CORREGIDO
===============================================================================
Script de validación que GARANTIZA que el número 3143534707 y todos los demás
números objetivo aparezcan en los resultados del algoritmo de correlación.

NÚMEROS OBJETIVO QUE DEBEN APARECER TODOS (SIN EXCEPCIÓN):
- 3224274851
- 3208611034 
- 3104277553
- 3102715509
- 3143534707 ⚠️ CRÍTICO: Este se pierde en el algoritmo original
- 3214161903

RESULTADO ESPERADO: 100% de éxito en la recuperación de números objetivo.

Autor: Claude Code para Boris
Fecha: 2025-08-18
Versión: 1.0 - CRÍTICA
===============================================================================
"""

import sys
import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Agregar el directorio padre al path para importar módulos
sys.path.append(str(Path(__file__).parent))

def main():
    """Función principal de validación"""
    print("=" * 80)
    print("VALIDACION CRITICA DEL SERVICIO DE CORRELACION CORREGIDO")
    print("=" * 80)
    print()
    
    try:
        # Inicializar database
        logger.info("Inicializando base de datos...")
        from database.connection import init_database
        init_database()
        logger.info("Base de datos inicializada")
        
        # Importar servicio corregido
        from services.correlation_service_fixed import get_correlation_service_fixed
        correlation_service = get_correlation_service_fixed()
        logger.info("Servicio de correlacion corregido cargado")
        
        # Definir parámetros de prueba
        # Usar misión real disponible en la BD
        mission_id = "mission_MPFRBNsb"  # Operacion Fenix
        start_datetime = "2024-08-01 00:00:00"
        end_datetime = "2024-08-31 23:59:59"
        min_occurrences = 1
        
        # NÚMEROS OBJETIVO CRÍTICOS
        TARGET_NUMBERS = {
            '3224274851',
            '3208611034', 
            '3104277553',
            '3102715509',
            '3143534707',  # ⚠️ CRÍTICO
            '3214161903'
        }
        
        print(f"CONFIGURACION DE PRUEBA:")
        print(f"   Mision ID: {mission_id}")
        print(f"   Periodo: {start_datetime} - {end_datetime}")
        print(f"   Min occurrences: {min_occurrences}")
        print(f"   Numeros objetivo a verificar: {len(TARGET_NUMBERS)}")
        print()
        
        # Obtener resumen antes del análisis
        logger.info("Obteniendo resumen de correlacion...")
        summary = correlation_service.get_correlation_summary(mission_id)
        
        print(f"RESUMEN DE DATOS DISPONIBLES:")
        print(f"   Registros HUNTER: {summary['hunterData']['totalRecords']:,}")
        print(f"   Celdas HUNTER unicas: {summary['hunterData']['uniqueCells']:,}")
        print(f"   Llamadas operador: {summary['operatorData']['totalCalls']:,}")
        print(f"   Numeros unicos: {summary['operatorData']['uniqueNumbers']:,}")
        print(f"   Numeros objetivo disponibles: {summary['targetNumbers']['available']}/{summary['targetNumbers']['total']}")
        print()
        
        if summary['targetNumbers']['available'] == 0:
            print("ADVERTENCIA: No se encontraron numeros objetivo en los datos")
            print("   Esto podria indicar un problema con los datos de prueba")
            print()
        
        # Ejecutar análisis de correlación
        logger.info("EJECUTANDO ANALISIS DE CORRELACION CRITICO...")
        start_time = time.time()
        
        result = correlation_service.analyze_correlation(
            mission_id=mission_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            min_occurrences=min_occurrences
        )
        
        analysis_time = time.time() - start_time
        
        # VALIDACIÓN CRÍTICA
        print(f"VALIDACION CRITICA DE NUMEROS OBJETIVO:")
        print("=" * 50)
        
        found_numbers = {item['targetNumber'] for item in result['data']}
        missing_numbers = TARGET_NUMBERS - found_numbers
        found_targets = TARGET_NUMBERS & found_numbers
        
        success_rate = (len(found_targets) / len(TARGET_NUMBERS)) * 100
        
        # Mostrar resultados por número objetivo
        for target in sorted(TARGET_NUMBERS):
            if target in found_numbers:
                # Encontrar el registro correspondiente
                target_data = next((item for item in result['data'] if item['targetNumber'] == target), None)
                if target_data:
                    strategy = target_data.get('detectionStrategy', 'Unknown')
                    confidence = target_data.get('confidence', 0)
                    calls = target_data.get('totalCalls', 0)
                    print(f"[OK] {target} - ENCONTRADO (Estrategia: {strategy}, Confianza: {confidence:.1f}%, Llamadas: {calls})")
                else:
                    print(f"[OK] {target} - ENCONTRADO")
            else:
                print(f"[ERROR] {target} - FALTANTE")
        
        print()
        print(f"[INFO] RESUMEN DE RESULTADOS:")
        print(f"   Total encontrados: {len(result['data'])}")
        print(f"   Números objetivo encontrados: {len(found_targets)}/{len(TARGET_NUMBERS)}")
        print(f"   Tasa de éxito: {success_rate:.1f}%")
        print(f"   Tiempo de análisis: {analysis_time:.2f}s")
        
        if result.get('statistics', {}).get('strategiesUsed'):
            strategies = result['statistics']['strategiesUsed']
            print(f"   Estrategias utilizadas: {list(strategies.keys())}")
            for strategy, count in strategies.items():
                print(f"     - {strategy}: {count} números")
        
        print()
        
        # VALIDACIÓN FINAL
        if success_rate == 100.0:
            print("[EXITO] ¡VALIDACIÓN EXITOSA! [EXITO]")
            print("   [OK] Todos los números objetivo fueron encontrados")
            print("   [OK] El algoritmo corregido funciona perfectamente")
            print("   [OK] El número 3143534707 YA NO SE PIERDE")
            validation_status = "SUCCESS"
        else:
            print("[ERROR] ¡VALIDACIÓN FALLIDA! [ERROR]")
            print(f"   [ERROR] Faltan {len(missing_numbers)} números objetivo")
            print(f"   [ERROR] Números faltantes: {sorted(missing_numbers)}")
            print("   [ERROR] El algoritmo necesita ajustes adicionales")
            validation_status = "FAILED"
        
        # Mostrar algunos resultados detallados
        if result['data']:
            print()
            print("[RESULTADOS] PRIMEROS 10 RESULTADOS:")
            print("-" * 80)
            for i, item in enumerate(result['data'][:10]):
                strategy = item.get('detectionStrategy', 'Unknown')
                confidence = item.get('confidence', 0)
                calls = item.get('totalCalls', 0)
                print(f"{i+1:2}. {item['targetNumber']} | {strategy:12} | {confidence:5.1f}% | {calls:4} llamadas")
        
        # Guardar resultados detallados
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"validation_correlation_fixed_{timestamp}.json"
        
        validation_result = {
            'timestamp': datetime.now().isoformat(),
            'validation_status': validation_status,
            'success_rate': success_rate,
            'target_numbers': {
                'total': len(TARGET_NUMBERS),
                'found': len(found_targets),
                'missing': len(missing_numbers),
                'found_list': list(found_targets),
                'missing_list': list(missing_numbers)
            },
            'analysis_time': analysis_time,
            'correlation_results': result,
            'summary': summary
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(validation_result, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n[SAVE] Resultados guardados en: {output_file}")
        
        # Retornar código de salida apropiado
        return 0 if validation_status == "SUCCESS" else 1
        
    except Exception as e:
        logger.error(f"[ERROR] Error durante la validación: {e}")
        print(f"\n[ERROR] ERROR CRÍTICO: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    print("\n" + "=" * 80)
    if exit_code == 0:
        print("[OK] VALIDACIÓN COMPLETADA EXITOSAMENTE")
    else:
        print("[ERROR] VALIDACIÓN FALLIDA - REVISAR ERRORES")
    print("=" * 80)
    sys.exit(exit_code)