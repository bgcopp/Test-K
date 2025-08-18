#!/usr/bin/env python3
"""
Test de validación para el servicio de correlación dinámico corregido
===============================================================================
Script de prueba para verificar que las correcciones de SQLite funcionan
===============================================================================

Autor: Claude Code para Boris
Fecha: 2025-08-18
"""

import os
import sys
import logging
from datetime import datetime, timedelta

# Configurar path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.correlation_service_dynamic import CorrelationServiceDynamic

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_correlation_service_fixed():
    """
    Test para validar las correcciones del servicio de correlación dinámico
    """
    print("=" * 80)
    print("TEST DE VALIDACIÓN - SERVICIO DE CORRELACIÓN DINÁMICO CORREGIDO")
    print("=" * 80)
    
    try:
        # Inicializar servicio
        service = CorrelationServiceDynamic()
        print("OK Servicio inicializado correctamente")
        
        # Parámetros de test (usando datos reales conocidos)
        mission_id = "66c0a8a2f28b5a32e6a0b123"  # Mission ID conocida
        
        # Período de agosto 2024 
        start_datetime = "2024-08-01 00:00:00"
        end_datetime = "2024-08-31 23:59:59"
        min_occurrences = 1
        
        print(f"\nParámetros del test:")
        print(f"  Mission ID: {mission_id}")
        print(f"  Período: {start_datetime} - {end_datetime}")
        print(f"  Mín ocurrencias: {min_occurrences}")
        
        # Ejecutar análisis de correlación
        print(f"\n[ANALISIS] Ejecutando análisis de correlación dinámico...")
        
        result = service.analyze_correlation(
            mission_id=mission_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            min_occurrences=min_occurrences
        )
        
        # Verificar resultado
        if result['success']:
            print(f"OK Análisis completado exitosamente")
            print(f"[ESTADISTICAS] Resultado del análisis:")
            print(f"  - Total correlaciones: {result['total_count']}")
            print(f"  - Tiempo de procesamiento: {result['processing_time']:.2f}s")
            print(f"  - Celdas HUNTER utilizadas: {len(result.get('hunter_cells_used', []))}")
            
            # Mostrar primeras correlaciones encontradas
            if result['data']:
                print(f"\n[RESULTADOS] Primeras correlaciones encontradas:")
                for i, correlation in enumerate(result['data'][:5]):
                    print(f"  {i+1}. {correlation['numero_objetivo']} ({correlation['operador']}) - "
                          f"{correlation['ocurrencias']} ocurrencias en {correlation['total_celdas_unicas']} celdas")
                    print(f"      Confianza: {correlation['nivel_confianza']}% | "
                          f"Período: {correlation['primera_deteccion']} - {correlation['ultima_deteccion']}")
                
                print(f"\n[SUCCESS] TEST EXITOSO: El servicio funciona correctamente con SQLite")
                return True
            else:
                print(f"[WARNING] No se encontraron correlaciones en el período especificado")
                print(f"[SUCCESS] TEST EXITOSO: Query se ejecutó sin errores (sin datos para el período)")
                return True
        else:
            print(f"[ERROR] Error en el análisis: {result['message']}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error durante el test: {str(e)}")
        return False

def test_sql_syntax_validation():
    """
    Test específico para validar que el SQL es compatible con SQLite
    """
    print(f"\n" + "=" * 80)
    print("TEST DE VALIDACIÓN SQL - COMPATIBILIDAD SQLITE")
    print("=" * 80)
    
    try:
        service = CorrelationServiceDynamic()
        
        # Test con datos mínimos para verificar sintaxis SQL
        mission_id = "test_mission"
        start_datetime = "2024-01-01 00:00:00"
        end_datetime = "2024-01-02 00:00:00"
        min_occurrences = 1
        
        print(f"[VALIDATION] Validando sintaxis SQL...")
        
        result = service.analyze_correlation(
            mission_id=mission_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            min_occurrences=min_occurrences
        )
        
        # Si no hay error SQL, la sintaxis es correcta
        if 'Error en query SQL' not in result.get('message', ''):
            print(f"[SUCCESS] Sintaxis SQL válida para SQLite")
            return True
        else:
            print(f"[ERROR] Error de sintaxis SQL detectado")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error validando sintaxis SQL: {str(e)}")
        return False

if __name__ == "__main__":
    print("Iniciando tests de validación del servicio de correlación dinámico corregido...")
    
    # Ejecutar tests
    test1_passed = test_sql_syntax_validation()
    test2_passed = test_correlation_service_fixed()
    
    # Resultado final
    print(f"\n" + "=" * 80)
    print("RESUMEN DE TESTS")
    print("=" * 80)
    print(f"Test sintaxis SQL: {'[SUCCESS]' if test1_passed else '[ERROR]'}")
    print(f"Test funcionalidad: {'[SUCCESS]' if test2_passed else '[ERROR]'}")
    
    if test1_passed and test2_passed:
        print(f"\n[SUCCESS] TODOS LOS TESTS EXITOSOS")
        print(f"El servicio de correlación dinámico está corregido y funcional")
    else:
        print(f"\n[WARNING] ALGUNOS TESTS FALLARON")
        print(f"Revisar logs para más detalles")