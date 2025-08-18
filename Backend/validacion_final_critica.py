#!/usr/bin/env python3
"""
VALIDACIÓN FINAL CRÍTICA - KRONOS CORRELATION SYSTEM
===============================================================================
TEST DEFINITIVO para confirmar que TODOS los 6 números objetivo aparecen 
correctamente en la correlación KRONOS.

NÚMEROS OBJETIVO QUE DEBEN APARECER TODOS (SIN EXCEPCIÓN):
- 3224274851 ✅
- 3208611034 ✅  
- 3104277553 ✅ (recién recuperado)
- 3102715509 ✅
- 3143534707 ✅ (problema original resuelto)
- 3214161903 ✅

CRITERIO DE ÉXITO ABSOLUTO:
- ❌ Si falta aunque sea 1 número → FALLÓ
- ✅ Si aparecen todos los 6 números → ÉXITO TOTAL

Autor: Claude Code para Boris
Fecha: 2025-08-18
Versión: FINAL CRITICAL VALIDATION
===============================================================================
"""

import sys
import os
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Set
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

# Agregar el directorio Backend al path para importaciones
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import get_database_manager, DatabaseManager
from services.correlation_service_fixed import get_correlation_service_fixed

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# NÚMEROS OBJETIVO CRÍTICOS - DEBE ESTAR 100% COMPLETO
TARGET_NUMBERS_CRITICAL = {
    '3224274851',
    '3208611034', 
    '3104277553',  # ⚠️ RECIÉN RECUPERADO
    '3102715509',
    '3143534707',  # ⚠️ PROBLEMA ORIGINAL
    '3214161903'
}

class CriticalValidationResults:
    """Clase para almacenar y reportar resultados de validación crítica"""
    
    def __init__(self):
        self.start_time = time.time()
        self.db_integrity_results = {}
        self.correlation_results = {}
        self.performance_metrics = {}
        self.regression_results = {}
        self.final_status = "PENDIENTE"
        self.critical_issues = []
        self.success_confirmations = []
        
    def add_critical_issue(self, issue: str):
        """Agrega un problema crítico"""
        self.critical_issues.append(f"❌ CRÍTICO: {issue}")
        logger.error(f"CRÍTICO: {issue}")
        
    def add_success_confirmation(self, confirmation: str):
        """Agrega una confirmación de éxito"""
        self.success_confirmations.append(f"✅ ÉXITO: {confirmation}")
        logger.info(f"ÉXITO: {confirmation}")
        
    def set_final_status(self, success: bool):
        """Establece el estado final"""
        self.final_status = "ÉXITO TOTAL" if success else "FALLÓ"
        
    def generate_final_report(self) -> Dict[str, Any]:
        """Genera reporte final de validación"""
        total_time = time.time() - self.start_time
        
        return {
            'validationTimestamp': datetime.now().isoformat(),
            'totalExecutionTime': round(total_time, 3),
            'finalStatus': self.final_status,
            'targetNumbersRequired': list(TARGET_NUMBERS_CRITICAL),
            'targetNumbersCount': len(TARGET_NUMBERS_CRITICAL),
            'dbIntegrityResults': self.db_integrity_results,
            'correlationResults': self.correlation_results,
            'performanceMetrics': self.performance_metrics,
            'regressionResults': self.regression_results,
            'criticalIssues': self.critical_issues,
            'successConfirmations': self.success_confirmations,
            'testsPassed': len(self.success_confirmations),
            'testsFailed': len(self.critical_issues)
        }


def test_1_database_integrity(results: CriticalValidationResults) -> bool:
    """
    PRUEBA 1: INTEGRIDAD DE BASE DE DATOS
    Verificar que los 6 números objetivo existen en operator_call_data
    """
    logger.info("=" * 80)
    logger.info("EJECUTANDO PRUEBA 1: INTEGRIDAD DE BASE DE DATOS")
    logger.info("=" * 80)
    
    try:
        db_manager = get_database_manager()
        
        with db_manager.get_session() as session:
            integrity_results = {
                'numbersFound': [],
                'numbersMissing': [],
                'numberDetails': {},
                'totalCalls': 0
            }
            
            for target_number in TARGET_NUMBERS_CRITICAL:
                # Buscar número con variaciones (con/sin prefijo 57)
                numbers_to_search = [target_number]
                if not target_number.startswith('57') and len(target_number) == 10:
                    numbers_to_search.append('57' + target_number)
                elif target_number.startswith('57') and len(target_number) == 12:
                    numbers_to_search.append(target_number[2:])
                
                found = False
                total_calls_for_number = 0
                found_as = None
                first_seen = None
                
                for search_variation in numbers_to_search:
                    query = text("""
                        SELECT 
                            COUNT(*) as call_count,
                            MIN(fecha_hora_llamada) as first_call,
                            MAX(fecha_hora_llamada) as last_call,
                            COUNT(DISTINCT operator) as operators,
                            COUNT(DISTINCT mission_id) as missions
                        FROM operator_call_data 
                        WHERE numero_objetivo = :number
                    """)
                    
                    result = session.execute(query, {'number': search_variation}).fetchone()
                    
                    if result and result[0] > 0:
                        found = True
                        total_calls_for_number = result[0]
                        found_as = search_variation
                        first_seen = result[1]
                        
                        integrity_results['numberDetails'][target_number] = {
                            'found': True,
                            'foundAs': found_as,
                            'callCount': total_calls_for_number,
                            'firstSeen': first_seen,
                            'lastSeen': result[2],
                            'operatorCount': result[3],
                            'missionCount': result[4]
                        }
                        break
                
                if found:
                    integrity_results['numbersFound'].append(target_number)
                    integrity_results['totalCalls'] += total_calls_for_number
                    results.add_success_confirmation(f"Número {target_number} encontrado como {found_as} con {total_calls_for_number} llamadas")
                else:
                    integrity_results['numbersMissing'].append(target_number)
                    integrity_results['numberDetails'][target_number] = {
                        'found': False,
                        'foundAs': None,
                        'callCount': 0,
                        'reason': 'No encontrado en base de datos'
                    }
                    results.add_critical_issue(f"Número {target_number} NO ENCONTRADO en operator_call_data")
            
            # Almacenar resultados
            results.db_integrity_results = integrity_results
            
            # Validación crítica
            if len(integrity_results['numbersMissing']) == 0:
                results.add_success_confirmation(f"INTEGRIDAD BD: Todos los {len(TARGET_NUMBERS_CRITICAL)} números objetivo están en la base de datos")
                return True
            else:
                results.add_critical_issue(f"INTEGRIDAD BD: Faltan {len(integrity_results['numbersMissing'])} números objetivo en la base de datos")
                return False
                
    except Exception as e:
        results.add_critical_issue(f"Error en prueba de integridad BD: {e}")
        return False


def test_2_correlation_algorithm(results: CriticalValidationResults) -> bool:
    """
    PRUEBA 2: ALGORITMO DE CORRELACIÓN COMPLETO
    Ejecutar correlation_service_fixed.analyze_correlation()
    """
    logger.info("=" * 80)
    logger.info("EJECUTANDO PRUEBA 2: ALGORITMO DE CORRELACIÓN COMPLETO")
    logger.info("=" * 80)
    
    try:
        correlation_service = get_correlation_service_fixed()
        
        # Parámetros de prueba (período amplio para garantizar cobertura)
        test_mission_id = "mission_MPFRBNsb"  # Misión existente válida
        start_datetime = "2024-08-01 00:00:00"
        end_datetime = "2024-08-31 23:59:59"
        min_occurrences = 1
        
        logger.info(f"Ejecutando correlación con parámetros:")
        logger.info(f"  - Misión: {test_mission_id}")
        logger.info(f"  - Período: {start_datetime} - {end_datetime}")
        logger.info(f"  - Min occurrences: {min_occurrences}")
        
        # Ejecutar análisis de correlación
        start_correlation_time = time.time()
        correlation_response = correlation_service.analyze_correlation(
            mission_id=test_mission_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            min_occurrences=min_occurrences
        )
        correlation_time = time.time() - start_correlation_time
        
        # Analizar resultados
        if not correlation_response.get('success', False):
            results.add_critical_issue("El algoritmo de correlación falló")
            return False
        
        correlation_data = correlation_response.get('data', [])
        statistics = correlation_response.get('statistics', {})
        
        # Extraer números encontrados
        found_target_numbers = set()
        correlation_details = {}
        
        for result in correlation_data:
            target_number = result.get('targetNumber')
            if target_number in TARGET_NUMBERS_CRITICAL:
                found_target_numbers.add(target_number)
                correlation_details[target_number] = {
                    'strategy': result.get('detectionStrategy'),
                    'confidence': result.get('confidence'),
                    'totalCalls': result.get('totalCalls'),
                    'uniqueHunterCells': result.get('uniqueHunterCells'),
                    'firstDetection': result.get('firstDetection'),
                    'lastDetection': result.get('lastDetection')
                }
        
        # Almacenar resultados de correlación
        results.correlation_results = {
            'executionTime': correlation_time,
            'totalNumbersFound': len(correlation_data),
            'targetNumbersFound': len(found_target_numbers),
            'targetNumbersRequired': len(TARGET_NUMBERS_CRITICAL),
            'foundTargetNumbers': list(found_target_numbers),
            'missingTargetNumbers': list(TARGET_NUMBERS_CRITICAL - found_target_numbers),
            'correlationDetails': correlation_details,
            'algorithmStatistics': statistics,
            'fullResponse': correlation_response
        }
        
        # Almacenar métricas de rendimiento
        results.performance_metrics = {
            'correlationExecutionTime': correlation_time,
            'numbersProcessed': len(correlation_data),
            'performanceRating': 'EXCELENTE' if correlation_time < 1.0 else 'BUENO' if correlation_time < 3.0 else 'MEJORABLE'
        }
        
        # Validaciones críticas específicas
        missing_targets = TARGET_NUMBERS_CRITICAL - found_target_numbers
        
        if len(missing_targets) == 0:
            results.add_success_confirmation(f"CORRELACIÓN: Todos los {len(TARGET_NUMBERS_CRITICAL)} números objetivo encontrados")
            results.add_success_confirmation(f"RENDIMIENTO: Tiempo de ejecución {correlation_time:.3f}s")
            return True
        else:
            results.add_critical_issue(f"CORRELACIÓN: Faltan {len(missing_targets)} números objetivo: {missing_targets}")
            return False
            
    except Exception as e:
        results.add_critical_issue(f"Error en algoritmo de correlación: {e}")
        return False


def test_3_specific_numbers_validation(results: CriticalValidationResults) -> bool:
    """
    PRUEBA 3: VALIDACIÓN ESPECÍFICA DE NÚMEROS CRÍTICOS
    Confirmar específicamente 3104277553 y 3143534707
    """
    logger.info("=" * 80)
    logger.info("EJECUTANDO PRUEBA 3: VALIDACIÓN ESPECÍFICA DE NÚMEROS CRÍTICOS")
    logger.info("=" * 80)
    
    critical_numbers = ['3104277553', '3143534707']
    
    try:
        correlation_details = results.correlation_results.get('correlationDetails', {})
        found_critical_numbers = results.correlation_results.get('foundTargetNumbers', [])
        
        validation_success = True
        
        for critical_number in critical_numbers:
            if critical_number in found_critical_numbers:
                details = correlation_details.get(critical_number, {})
                results.add_success_confirmation(
                    f"CRÍTICO: {critical_number} encontrado con estrategia {details.get('strategy', 'N/A')} "
                    f"y confianza {details.get('confidence', 'N/A')}%"
                )
            else:
                results.add_critical_issue(f"CRÍTICO: {critical_number} NO ENCONTRADO en correlación")
                validation_success = False
        
        return validation_success
        
    except Exception as e:
        results.add_critical_issue(f"Error en validación específica: {e}")
        return False


def test_4_regression_testing(results: CriticalValidationResults) -> bool:
    """
    PRUEBA 4: TESTING DE REGRESIÓN
    Ejecutar correlación múltiples veces para verificar consistencia
    """
    logger.info("=" * 80)
    logger.info("EJECUTANDO PRUEBA 4: TESTING DE REGRESIÓN")
    logger.info("=" * 80)
    
    try:
        correlation_service = get_correlation_service_fixed()
        
        regression_results = {
            'executionCount': 3,
            'executionTimes': [],
            'resultConsistency': True,
            'executionDetails': []
        }
        
        # Ejecutar 3 veces la correlación
        consistent_results = []
        
        for i in range(3):
            logger.info(f"Ejecución de regresión #{i+1}/3")
            
            start_time = time.time()
            response = correlation_service.analyze_correlation(
                mission_id="mission_MPFRBNsb",
                start_datetime="2024-08-15 00:00:00",
                end_datetime="2024-08-20 23:59:59",
                min_occurrences=1
            )
            execution_time = time.time() - start_time
            
            regression_results['executionTimes'].append(execution_time)
            
            # Extraer números objetivo encontrados
            found_numbers = set()
            for result in response.get('data', []):
                if result.get('targetNumber') in TARGET_NUMBERS_CRITICAL:
                    found_numbers.add(result.get('targetNumber'))
            
            consistent_results.append(found_numbers)
            
            regression_results['executionDetails'].append({
                'execution': i+1,
                'time': execution_time,
                'targetNumbersFound': len(found_numbers),
                'foundNumbers': list(found_numbers)
            })
        
        # Verificar consistencia
        first_result = consistent_results[0]
        for result in consistent_results[1:]:
            if result != first_result:
                regression_results['resultConsistency'] = False
                results.add_critical_issue("REGRESIÓN: Resultados inconsistentes entre ejecuciones")
                break
        
        if regression_results['resultConsistency']:
            avg_time = sum(regression_results['executionTimes']) / len(regression_results['executionTimes'])
            results.add_success_confirmation(f"REGRESIÓN: Resultados consistentes en {len(regression_results['executionTimes'])} ejecuciones")
            results.add_success_confirmation(f"RENDIMIENTO: Tiempo promedio {avg_time:.3f}s")
        
        results.regression_results = regression_results
        return regression_results['resultConsistency']
        
    except Exception as e:
        results.add_critical_issue(f"Error en testing de regresión: {e}")
        return False


def save_validation_report(results: CriticalValidationResults):
    """Guarda el reporte final de validación"""
    try:
        report = results.generate_final_report()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"validacion_final_critica_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"REPORTE GUARDADO: {filename}")
        return filename
        
    except Exception as e:
        logger.error(f"Error guardando reporte: {e}")
        return None


def main():
    """
    FUNCIÓN PRINCIPAL DE VALIDACIÓN CRÍTICA
    Ejecuta todas las pruebas en secuencia y determina el éxito total
    """
    print("=" * 80)
    print("INICIANDO VALIDACIÓN FINAL CRÍTICA - KRONOS CORRELATION SYSTEM")
    print("=" * 80)
    print()
    
    # INICIALIZAR BASE DE DATOS
    try:
        from database.connection import init_database
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kronos.db')
        init_database(db_path)
        logger.info(f"Base de datos inicializada: {db_path}")
    except Exception as e:
        logger.error(f"Error inicializando base de datos: {e}")
        print(f"ERROR CRÍTICO: No se pudo inicializar la base de datos: {e}")
        return False
    
    results = CriticalValidationResults()
    
    # Ejecutar todas las pruebas
    test_results = []
    
    test_results.append(test_1_database_integrity(results))
    test_results.append(test_2_correlation_algorithm(results))
    test_results.append(test_3_specific_numbers_validation(results))
    test_results.append(test_4_regression_testing(results))
    
    # Determinar éxito total
    all_tests_passed = all(test_results)
    results.set_final_status(all_tests_passed)
    
    # Generar reporte final
    print("\n" + "=" * 80)
    print("RESULTADOS FINALES DE VALIDACIÓN CRÍTICA")
    print("=" * 80)
    
    final_report = results.generate_final_report()
    
    print(f"ESTADO FINAL: {final_report['finalStatus']}")
    print(f"TIEMPO TOTAL: {final_report['totalExecutionTime']:.3f}s")
    print(f"PRUEBAS EXITOSAS: {final_report['testsPassed']}")
    print(f"PRUEBAS FALLIDAS: {final_report['testsFailed']}")
    print()
    
    if final_report['finalStatus'] == "ÉXITO TOTAL":
        print("*** VALIDACIÓN EXITOSA! Todos los números objetivo están presentes.")
        print(f"Números objetivo encontrados: {len(final_report['correlationResults'].get('foundTargetNumbers', []))}/{final_report['targetNumbersCount']}")
        print("*** El sistema KRONOS está funcionando perfectamente.")
    else:
        print("*** VALIDACIÓN FALLIDA: Se encontraron problemas críticos.")
        print("*** Se requiere intervención inmediata para resolver los issues.")
    
    # Guardar reporte
    report_file = save_validation_report(results)
    if report_file:
        print(f"Reporte detallado guardado en: {report_file}")
    
    print("\n" + "=" * 80)
    print("VALIDACIÓN FINAL CRÍTICA COMPLETADA")
    print("=" * 80)
    
    return all_tests_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)