"""
Test de Regresión - Algoritmo Original vs Corregido
==================================================
Valida que el algoritmo corregido mantiene todas las funcionalidades 
del original y además recupera el número crítico 3143534707.

Boris - Testing Engineer
Fecha: 2025-08-18
"""

import time
import json
from datetime import datetime
from database.connection import init_database, get_database_manager
from services.correlation_service import CorrelationService
from services.correlation_service_fixed import get_correlation_service_fixed


class CorrelationRegressionValidator:
    """Validador de regresión entre algoritmos de correlación"""
    
    def __init__(self):
        self.target_numbers_critical = [
            '3224274851', '3208611034', '3104277553', 
            '3102715509', '3143534707', '3214161903'
        ]
        self.mission_id = 'mission_MPFRBNsb'
        self.test_period_start = '2021-05-20 10:00:00'
        self.test_period_end = '2021-05-20 13:59:59'
    
    def run_regression_tests(self):
        """Ejecuta suite completa de pruebas de regresión"""
        print("="*80)
        print("INICIANDO PRUEBAS DE REGRESIÓN - ALGORITMO CORRELACIÓN")
        print("="*80)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'test_suite': 'correlation_regression_validation',
            'original_algorithm_results': {},
            'fixed_algorithm_results': {},
            'regression_analysis': {},
            'critical_findings': {}
        }
        
        try:
            # Inicializar base de datos
            init_database()
            
            # Test 1: Algoritmo Original
            print("\nEJECUTANDO: Algoritmo Original (CorrelationService)")
            original_results = self._test_original_algorithm()
            results['original_algorithm_results'] = original_results
            
            # Test 2: Algoritmo Corregido
            print("\nEJECUTANDO: Algoritmo Corregido (CorrelationServiceFixed)")
            fixed_results = self._test_fixed_algorithm()
            results['fixed_algorithm_results'] = fixed_results
            
            # Test 3: Análisis de Regresión
            print("\nEJECUTANDO: Analisis de Regresion Comparativo")
            regression_analysis = self._analyze_regression(original_results, fixed_results)
            results['regression_analysis'] = regression_analysis
            
            # Test 4: Hallazgos Críticos
            critical_findings = self._evaluate_critical_findings(original_results, fixed_results)
            results['critical_findings'] = critical_findings
            
            # Evaluación final
            results['overall_regression_passed'] = self._evaluate_regression_success(regression_analysis, critical_findings)
            
            print("\n" + "="*80)
            print("RESULTADOS DE REGRESIÓN:")
            self._print_summary(results)
            
            return results
            
        except Exception as e:
            results['error'] = str(e)
            results['overall_regression_passed'] = False
            print(f"ERROR EN PRUEBAS DE REGRESION: {e}")
            return results
    
    def _test_original_algorithm(self):
        """Prueba el algoritmo de correlación original"""
        try:
            # Crear instancia directa del servicio original (sin factory)
            original_service = CorrelationService()
            
            start_time = time.time()
            
            # Ejecutar análisis con período real de datos
            original_result = original_service.analyze_correlation(
                mission_id=self.mission_id,
                start_datetime=self.test_period_start,
                end_datetime=self.test_period_end,
                min_occurrences=1
            )
            
            duration = time.time() - start_time
            
            # Analizar números encontrados
            found_numbers = set()
            target_numbers_found = {}
            
            for result in original_result.get('data', []):
                target_number = result.get('targetNumber', '')
                found_numbers.add(target_number)
                
                if target_number in self.target_numbers_critical:
                    target_numbers_found[target_number] = {
                        'confidence': result.get('confidence', 0),
                        'total_calls': result.get('totalCalls', 0),
                        'occurrences': result.get('occurrences', 0)
                    }
            
            return {
                'success': original_result.get('success', False),
                'execution_time': round(duration, 3),
                'total_numbers_found': len(found_numbers),
                'target_numbers_found': len(target_numbers_found),
                'critical_3143534707_found': '3143534707' in found_numbers,
                'missing_targets': list(set(self.target_numbers_critical) - found_numbers),
                'target_details': target_numbers_found,
                'algorithm_version': 'original',
                'full_statistics': original_result.get('statistics', {})
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'algorithm_version': 'original'
            }
    
    def _test_fixed_algorithm(self):
        """Prueba el algoritmo de correlación corregido"""
        try:
            # Obtener instancia del servicio corregido
            fixed_service = get_correlation_service_fixed()
            
            start_time = time.time()
            
            # Ejecutar análisis con mismo período
            fixed_result = fixed_service.analyze_correlation(
                mission_id=self.mission_id,
                start_datetime=self.test_period_start,
                end_datetime=self.test_period_end,
                min_occurrences=1
            )
            
            duration = time.time() - start_time
            
            # Analizar números encontrados
            found_numbers = set()
            target_numbers_found = {}
            strategies_used = {}
            
            for result in fixed_result.get('data', []):
                target_number = result.get('targetNumber', '')
                found_numbers.add(target_number)
                
                strategy = result.get('detectionStrategy', 'Unknown')
                strategies_used[strategy] = strategies_used.get(strategy, 0) + 1
                
                if target_number in self.target_numbers_critical:
                    target_numbers_found[target_number] = {
                        'confidence': result.get('confidence', 0),
                        'total_calls': result.get('totalCalls', 0),
                        'strategy': strategy,
                        'cells_used': result.get('uniqueHunterCells', 0)
                    }
            
            return {
                'success': fixed_result.get('success', False),
                'execution_time': round(duration, 3),
                'total_numbers_found': len(found_numbers),
                'target_numbers_found': len(target_numbers_found),
                'critical_3143534707_found': '3143534707' in found_numbers,
                'missing_targets': list(set(self.target_numbers_critical) - found_numbers),
                'target_details': target_numbers_found,
                'strategies_used': strategies_used,
                'algorithm_version': 'fixed',
                'full_statistics': fixed_result.get('statistics', {})
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'algorithm_version': 'fixed'
            }
    
    def _analyze_regression(self, original_results, fixed_results):
        """Analiza regresión comparando ambos algoritmos"""
        analysis = {
            'performance_comparison': {},
            'functionality_regression': {},
            'improvement_metrics': {}
        }
        
        # Comparación de rendimiento
        if original_results.get('success') and fixed_results.get('success'):
            analysis['performance_comparison'] = {
                'original_time': original_results.get('execution_time', 0),
                'fixed_time': fixed_results.get('execution_time', 0),
                'performance_regression': fixed_results.get('execution_time', 0) > original_results.get('execution_time', 0) * 2,
                'time_difference': fixed_results.get('execution_time', 0) - original_results.get('execution_time', 0)
            }
            
            # Regresión funcional
            analysis['functionality_regression'] = {
                'numbers_lost': original_results.get('total_numbers_found', 0) > fixed_results.get('total_numbers_found', 0),
                'original_found': original_results.get('total_numbers_found', 0),
                'fixed_found': fixed_results.get('total_numbers_found', 0),
                'net_difference': fixed_results.get('total_numbers_found', 0) - original_results.get('total_numbers_found', 0)
            }
            
            # Métricas de mejora
            analysis['improvement_metrics'] = {
                'critical_number_recovered': fixed_results.get('critical_3143534707_found', False) and not original_results.get('critical_3143534707_found', False),
                'target_numbers_improvement': fixed_results.get('target_numbers_found', 0) - original_results.get('target_numbers_found', 0),
                'strategies_implemented': len(fixed_results.get('strategies_used', {})) > 1
            }
        
        return analysis
    
    def _evaluate_critical_findings(self, original_results, fixed_results):
        """Evalúa hallazgos críticos de la regresión"""
        findings = {
            'critical_number_3143534707': {
                'original_found': original_results.get('critical_3143534707_found', False),
                'fixed_found': fixed_results.get('critical_3143534707_found', False),
                'issue_resolved': fixed_results.get('critical_3143534707_found', False)
            },
            'target_numbers_analysis': {
                'original_missing': original_results.get('missing_targets', []),
                'fixed_missing': fixed_results.get('missing_targets', []),
                'recovered_numbers': list(set(original_results.get('missing_targets', [])) - set(fixed_results.get('missing_targets', []))),
                'lost_numbers': list(set(fixed_results.get('missing_targets', [])) - set(original_results.get('missing_targets', [])))
            },
            'algorithm_reliability': {
                'original_success': original_results.get('success', False),
                'fixed_success': fixed_results.get('success', False),
                'improvement_achieved': fixed_results.get('success', False) and fixed_results.get('target_numbers_found', 0) > original_results.get('target_numbers_found', 0)
            }
        }
        
        return findings
    
    def _evaluate_regression_success(self, regression_analysis, critical_findings):
        """Evalúa si la regresión fue exitosa"""
        criteria = [
            # No debe haber regresión funcional severa
            not regression_analysis.get('functionality_regression', {}).get('numbers_lost', True),
            
            # No debe haber regresión de rendimiento severa (> 2x tiempo)
            not regression_analysis.get('performance_comparison', {}).get('performance_regression', True),
            
            # Debe resolver el problema crítico del 3143534707
            critical_findings.get('critical_number_3143534707', {}).get('issue_resolved', False),
            
            # El algoritmo corregido debe ser exitoso
            critical_findings.get('algorithm_reliability', {}).get('fixed_success', False)
        ]
        
        return all(criteria)
    
    def _print_summary(self, results):
        """Imprime resumen de resultados"""
        print(f"Algoritmo Original: {results['original_algorithm_results'].get('success', False)}")
        print(f"Algoritmo Corregido: {results['fixed_algorithm_results'].get('success', False)}")
        print(f"3143534707 Recuperado: {results['critical_findings'].get('critical_number_3143534707', {}).get('issue_resolved', False)}")
        print(f"Regresion Exitosa: {results.get('overall_regression_passed', False)}")
        
        if results.get('regression_analysis', {}).get('improvement_metrics', {}):
            improvement = results['regression_analysis']['improvement_metrics']
            print(f"Numeros Objetivo Mejorados: +{improvement.get('target_numbers_improvement', 0)}")


def main():
    """Función principal de ejecución"""
    validator = CorrelationRegressionValidator()
    results = validator.run_regression_tests()
    
    # Guardar resultados
    output_file = f"correlation_regression_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nResultados guardados en: {output_file}")
    return results


if __name__ == "__main__":
    main()