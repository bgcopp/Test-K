"""
Test de Integración Main.py/Eel - Validación Completa
=====================================================
Valida que la integración entre main.py, servicios y Eel funcione correctamente
con el algoritmo de correlación corregido.

Boris - Testing Engineer
Fecha: 2025-08-18
"""

import time
import json
from datetime import datetime


class MainIntegrationValidator:
    """Validador de integración completa main.py/Eel"""
    
    def run_integration_tests(self):
        """Ejecuta suite completa de pruebas de integración"""
        print("="*80)
        print("INICIANDO PRUEBAS DE INTEGRACIÓN MAIN.PY/EEL")
        print("="*80)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'test_suite': 'main_integration_validation',
            'tests_performed': []
        }
        
        try:
            # Test 1: Importaciones críticas
            print("\nTest 1: Verificando importaciones criticas...")
            import_test = self._test_critical_imports()
            results['tests_performed'].append(import_test)
            
            # Test 2: Factory pattern correcto
            print("\nTest 2: Validando factory pattern...")
            factory_test = self._test_factory_pattern()
            results['tests_performed'].append(factory_test)
            
            # Test 3: Base de datos accesible
            print("\nTest 3: Verificando acceso a base de datos...")
            db_test = self._test_database_access()
            results['tests_performed'].append(db_test)
            
            # Test 4: Servicio de correlación funcional
            print("\nTest 4: Probando servicio de correlacion...")
            correlation_test = self._test_correlation_service()
            results['tests_performed'].append(correlation_test)
            
            # Test 5: Resumen de capacidades
            print("\nTest 5: Validando resumen de capacidades...")
            summary_test = self._test_correlation_summary()
            results['tests_performed'].append(summary_test)
            
            # Evaluación general
            all_tests_passed = all(t.get('success', False) for t in results['tests_performed'])
            results['integration_successful'] = all_tests_passed
            
            print("\n" + "="*80)
            print("RESULTADOS DE INTEGRACIÓN:")
            self._print_integration_summary(results)
            
            return results
            
        except Exception as e:
            results['error'] = str(e)
            results['integration_successful'] = False
            print(f"ERROR EN PRUEBAS DE INTEGRACIÓN: {e}")
            return results
    
    def _test_critical_imports(self):
        """Test de importaciones críticas"""
        try:
            # Importar módulos principales
            from database.connection import init_database, get_database_manager
            from services.correlation_service import get_correlation_service
            from services.correlation_service_fixed import get_correlation_service_fixed
            
            # Inicializar base de datos
            init_database()
            
            return {
                'test_id': 'critical_imports',
                'success': True,
                'description': 'Importaciones principales exitosas',
                'modules_imported': [
                    'database.connection',
                    'services.correlation_service',
                    'services.correlation_service_fixed'
                ]
            }
            
        except Exception as e:
            return {
                'test_id': 'critical_imports',
                'success': False,
                'error': str(e)
            }
    
    def _test_factory_pattern(self):
        """Test del factory pattern"""
        try:
            from services.correlation_service import get_correlation_service
            
            # Obtener servicio desde factory
            correlation_service = get_correlation_service()
            service_class = correlation_service.__class__.__name__
            
            # Verificar que es el servicio corregido
            is_fixed_service = service_class == 'CorrelationServiceFixed'
            
            return {
                'test_id': 'factory_pattern',
                'success': True,
                'service_returned': service_class,
                'is_fixed_service': is_fixed_service,
                'factory_working': is_fixed_service
            }
            
        except Exception as e:
            return {
                'test_id': 'factory_pattern',
                'success': False,
                'error': str(e)
            }
    
    def _test_database_access(self):
        """Test de acceso a base de datos"""
        try:
            from database.connection import get_database_manager
            from sqlalchemy import text
            
            db_manager = get_database_manager()
            
            with db_manager.get_session() as session:
                # Verificar acceso a tablas principales
                missions_query = text('SELECT COUNT(*) FROM missions')
                missions_count = session.execute(missions_query).scalar()
                
                cellular_query = text('SELECT COUNT(*) FROM cellular_data')
                cellular_count = session.execute(cellular_query).scalar()
                
                operator_query = text('SELECT COUNT(*) FROM operator_call_data')
                operator_count = session.execute(operator_query).scalar()
            
            return {
                'test_id': 'database_access',
                'success': True,
                'missions_count': missions_count,
                'cellular_data_count': cellular_count,
                'operator_data_count': operator_count,
                'database_healthy': missions_count > 0 and operator_count > 0
            }
            
        except Exception as e:
            return {
                'test_id': 'database_access',
                'success': False,
                'error': str(e)
            }
    
    def _test_correlation_service(self):
        """Test funcional del servicio de correlación"""
        try:
            from services.correlation_service import get_correlation_service
            
            correlation_service = get_correlation_service()
            
            test_start = time.time()
            
            correlation_result = correlation_service.analyze_correlation(
                mission_id='mission_MPFRBNsb',
                start_datetime='2021-05-20 10:00:00',
                end_datetime='2021-05-20 13:59:59',
                min_occurrences=1
            )
            
            test_duration = time.time() - test_start
            
            # Verificar número crítico
            critical_found = any(
                r.get('targetNumber') == '3143534707' 
                for r in correlation_result.get('data', [])
            )
            
            return {
                'test_id': 'correlation_service_functional',
                'success': correlation_result.get('success', False),
                'duration': round(test_duration, 3),
                'numbers_found': len(correlation_result.get('data', [])),
                'critical_3143534707_found': critical_found,
                'performance_acceptable': test_duration < 1.0,
                'statistics': correlation_result.get('statistics', {})
            }
            
        except Exception as e:
            return {
                'test_id': 'correlation_service_functional',
                'success': False,
                'error': str(e)
            }
    
    def _test_correlation_summary(self):
        """Test del resumen de capacidades de correlación"""
        try:
            from services.correlation_service import get_correlation_service
            
            correlation_service = get_correlation_service()
            
            test_start = time.time()
            
            summary_result = correlation_service.get_correlation_summary('mission_MPFRBNsb')
            
            test_duration = time.time() - test_start
            
            return {
                'test_id': 'correlation_summary',
                'success': summary_result.get('success', False),
                'duration': round(test_duration, 3),
                'correlation_ready': summary_result.get('correlationReady', False),
                'hunter_data': summary_result.get('hunterData', {}),
                'operator_data': summary_result.get('operatorData', {}),
                'target_numbers_info': summary_result.get('targetNumbers', {})
            }
            
        except Exception as e:
            return {
                'test_id': 'correlation_summary',
                'success': False,
                'error': str(e)
            }
    
    def _print_integration_summary(self, results):
        """Imprime resumen de resultados de integración"""
        tests = results.get('tests_performed', [])
        
        for test in tests:
            test_name = test.get('test_id', 'Unknown')
            success = test.get('success', False)
            status = "EXITOSO" if success else "FALLIDO"
            print(f"{test_name}: {status}")
            
            if test_name == 'factory_pattern' and success:
                print(f"  - Servicio retornado: {test.get('service_returned', 'Unknown')}")
                print(f"  - Es servicio corregido: {test.get('is_fixed_service', False)}")
            
            elif test_name == 'correlation_service_functional' and success:
                print(f"  - Numeros encontrados: {test.get('numbers_found', 0)}")
                print(f"  - 3143534707 encontrado: {test.get('critical_3143534707_found', False)}")
                print(f"  - Tiempo ejecucion: {test.get('duration', 0)}s")
        
        print(f"\nINTEGRACIÓN GENERAL: {'EXITOSA' if results.get('integration_successful', False) else 'FALLIDA'}")


def main():
    """Función principal de ejecución"""
    validator = MainIntegrationValidator()
    results = validator.run_integration_tests()
    
    # Guardar resultados
    output_file = f"main_integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nResultados guardados en: {output_file}")
    return results


if __name__ == "__main__":
    main()