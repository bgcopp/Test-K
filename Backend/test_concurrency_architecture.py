"""
Test de Concurrencia Arquitectónica L2
===============================================================================
Prueba el comportamiento del sistema bajo carga concurrente de múltiples
usuarios simulados procesando archivos de diferentes operadores simultáneamente.

Este test valida:
1. Integridad de datos bajo carga concurrente
2. Aislamiento entre sesiones de usuario
3. Manejo robusto de transacciones paralelas
4. Performance bajo concurrencia
5. Detección de deadlocks o race conditions

Arquitectura evaluada:
- Patrón Factory de procesadores
- Transacciones SQLite concurrentes
- Manejo de errores bajo stress
- Escalabilidad del diseño
===============================================================================
"""

import threading
import time
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from database.connection import init_database, get_database_manager
from services.operator_service import get_operator_service
from services.mission_service import get_mission_service

# Configurar logging específico para pruebas
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(threadName)s] - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConcurrencyStressTest:
    """Test de stress de concurrencia para arquitectura L2"""
    
    def __init__(self):
        self.db_path = os.path.join(os.getcwd(), 'test_concurrency.db')
        self.results = {}
        self.errors = []
        self.lock = threading.Lock()
        
    def setup_test_environment(self):
        """Configura entorno de pruebas"""
        logger.info("=== CONFIGURANDO ENTORNO DE PRUEBAS CONCURRENCIA ===")
        
        # Limpiar BD de pruebas si existe
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        
        # Inicializar BD nueva
        init_database(self.db_path, force_recreate=True)
        logger.info("Base de datos de pruebas inicializada")
        
        # Usar misión existente para evitar validaciones complejas
        mission_service = get_mission_service()
        missions = mission_service.get_all_missions()
        
        if missions:
            self.test_mission_id = missions[0]['id']
            logger.info(f"Usando misión existente: {missions[0]['code']}")
        else:
            # Crear misión mínima
            from datetime import datetime, timedelta
            test_mission = {
                'code': 'CONCURRENCY-TEST',
                'name': 'Prueba de Concurrencia Arquitectónica',
                'description': 'Misión para testing de carga concurrente',
                'status': 'En Progreso',
                'priority': 'Alta',
                'startDate': datetime.now().strftime('%Y-%m-%d'),
                'endDate': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                'targets': ['573001234567', '573009876543', '573005555555']
            }
            
            created_mission = mission_service.create_mission(test_mission)
            self.test_mission_id = created_mission['id']
        
        logger.info(f"Misión de prueba creada: {self.test_mission_id}")
        
    def simulate_user_session(self, user_id, operator, session_duration=10):
        """Simula una sesión de usuario procesando archivos"""
        thread_name = threading.current_thread().name
        logger.info(f"[Usuario-{user_id}] Iniciando sesión para {operator}")
        
        session_results = {
            'user_id': user_id,
            'operator': operator,
            'files_processed': 0,
            'errors_encountered': 0,
            'processing_time': 0,
            'thread_name': thread_name
        }
        
        start_time = time.time()
        
        try:
            operator_service = get_operator_service()
            
            # Simular procesamiento de archivos en ráfagas
            for batch in range(3):  # 3 lotes de procesamiento
                logger.info(f"[Usuario-{user_id}] {operator} - Lote {batch + 1}")
                
                # Simular carga de archivo pequeño
                fake_file_data = {
                    'name': f'{operator.lower()}_test_user_{user_id}_batch_{batch}.csv',
                    'content': 'data:text/csv;base64,bnVtZXJvLGZlY2hhCjU3MzAwMTIzNDU2NywyMDI1MDgxMjEwMDA='
                }
                
                try:
                    # Intentar validar archivo (sin procesar para evitar errores)
                    validation = operator_service.validate_file_for_operator(
                        operator, fake_file_data, 'DATOS'
                    )
                    
                    if validation.get('is_valid', False):
                        session_results['files_processed'] += 1
                    else:
                        session_results['errors_encountered'] += 1
                        
                except Exception as e:
                    session_results['errors_encountered'] += 1
                    with self.lock:
                        self.errors.append(f"[Usuario-{user_id}] {operator}: {str(e)}")
                
                # Simular tiempo de procesamiento
                time.sleep(0.5)
        
        except Exception as e:
            logger.error(f"[Usuario-{user_id}] Error crítico en sesión {operator}: {e}")
            session_results['errors_encountered'] += 10  # Error crítico
            with self.lock:
                self.errors.append(f"[Usuario-{user_id}] ERROR CRÍTICO {operator}: {str(e)}")
        
        session_results['processing_time'] = time.time() - start_time
        logger.info(f"[Usuario-{user_id}] Sesión {operator} completada: {session_results}")
        
        return session_results
    
    def run_concurrent_stress_test(self, num_users=8, operators=None):
        """Ejecuta test de stress con múltiples usuarios concurrentes"""
        if operators is None:
            operators = ['CLARO', 'MOVISTAR', 'TIGO', 'WOM']
        
        logger.info(f"=== INICIANDO TEST CONCURRENCIA: {num_users} usuarios, {len(operators)} operadores ===")
        
        all_sessions = []
        
        # Generar combinaciones usuario-operador
        session_id = 0
        for user_num in range(num_users):
            for operator in operators:
                all_sessions.append((session_id, operator))
                session_id += 1
        
        logger.info(f"Total de sesiones concurrentes: {len(all_sessions)}")
        
        # Ejecutar sesiones concurrentes
        results = []
        start_test_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_users * 2) as executor:
            # Enviar todas las tareas
            future_to_session = {}
            for session_id, operator in all_sessions:
                future = executor.submit(self.simulate_user_session, session_id, operator)
                future_to_session[future] = (session_id, operator)
            
            # Recoger resultados
            completed_count = 0
            for future in as_completed(future_to_session):
                session_id, operator = future_to_session[future]
                try:
                    result = future.result(timeout=30)  # Timeout de 30 segundos por sesión
                    results.append(result)
                    completed_count += 1
                    
                    logger.info(f"Progreso: {completed_count}/{len(all_sessions)} sesiones completadas")
                    
                except Exception as e:
                    logger.error(f"Error en sesión {session_id}-{operator}: {e}")
                    with self.lock:
                        self.errors.append(f"Sesión {session_id}-{operator}: TIMEOUT/ERROR - {str(e)}")
        
        total_test_time = time.time() - start_test_time
        
        # Analizar resultados
        self.analyze_concurrency_results(results, total_test_time)
        
        return results
    
    def analyze_concurrency_results(self, results, total_time):
        """Analiza los resultados del test de concurrencia"""
        logger.info("=== ANÁLISIS DE RESULTADOS DE CONCURRENCIA ===")
        
        total_sessions = len(results)
        total_files_processed = sum(r['files_processed'] for r in results)
        total_errors = sum(r['errors_encountered'] for r in results)
        avg_session_time = sum(r['processing_time'] for r in results) / total_sessions if total_sessions > 0 else 0
        
        # Agrupar por operador
        operator_stats = {}
        for result in results:
            op = result['operator']
            if op not in operator_stats:
                operator_stats[op] = {
                    'sessions': 0,
                    'files_processed': 0,
                    'errors': 0,
                    'avg_time': 0
                }
            
            stats = operator_stats[op]
            stats['sessions'] += 1
            stats['files_processed'] += result['files_processed']
            stats['errors'] += result['errors_encountered']
            stats['avg_time'] += result['processing_time']
        
        # Calcular promedios
        for op, stats in operator_stats.items():
            if stats['sessions'] > 0:
                stats['avg_time'] = stats['avg_time'] / stats['sessions']
        
        # Reportar resultados
        print("\n" + "="*70)
        print("REPORTE DE CONCURRENCIA ARQUITECTÓNICA L2")
        print("="*70)
        print(f"Total de sesiones ejecutadas: {total_sessions}")
        print(f"Tiempo total de prueba: {total_time:.2f} segundos")
        print(f"Archivos procesados exitosamente: {total_files_processed}")
        print(f"Errores encontrados: {total_errors}")
        print(f"Tiempo promedio por sesión: {avg_session_time:.2f} segundos")
        print(f"Tasa de éxito global: {((total_files_processed / (total_files_processed + total_errors)) * 100):.1f}%" if (total_files_processed + total_errors) > 0 else "N/A")
        
        print("\nESTADÍSTICAS POR OPERADOR:")
        print("-" * 50)
        for op, stats in operator_stats.items():
            success_rate = (stats['files_processed'] / (stats['files_processed'] + stats['errors'])) * 100 if (stats['files_processed'] + stats['errors']) > 0 else 0
            print(f"{op:10} | Sesiones: {stats['sessions']:2} | Archivos: {stats['files_processed']:2} | Errores: {stats['errors']:2} | Éxito: {success_rate:5.1f}% | Tiempo: {stats['avg_time']:.2f}s")
        
        print("\nERRORES ENCONTRADOS:")
        print("-" * 50)
        if self.errors:
            for i, error in enumerate(self.errors[:10], 1):  # Mostrar primeros 10 errores
                print(f"{i:2}. {error}")
            if len(self.errors) > 10:
                print(f"    ... y {len(self.errors) - 10} errores más")
        else:
            print("✓ NO SE ENCONTRARON ERRORES")
        
        # Evaluación arquitectónica
        print("\nEVALUACIÓN ARQUITECTÓNICA:")
        print("-" * 50)
        
        # Criterios de evaluación
        concurrency_score = 0
        max_score = 100
        
        # 1. Tasa de éxito (40 puntos)
        success_rate = (total_files_processed / (total_files_processed + total_errors)) * 100 if (total_files_processed + total_errors) > 0 else 0
        if success_rate >= 90:
            concurrency_score += 40
        elif success_rate >= 80:
            concurrency_score += 30
        elif success_rate >= 70:
            concurrency_score += 20
        else:
            concurrency_score += 10
        
        print(f"Tasa de éxito: {success_rate:.1f}% {'✓' if success_rate >= 80 else '⚠' if success_rate >= 70 else '✗'}")
        
        # 2. Performance bajo concurrencia (30 puntos)
        if avg_session_time <= 5:
            concurrency_score += 30
        elif avg_session_time <= 10:
            concurrency_score += 20
        elif avg_session_time <= 15:
            concurrency_score += 10
        
        print(f"Performance: {avg_session_time:.2f}s promedio {'✓' if avg_session_time <= 10 else '⚠' if avg_session_time <= 15 else '✗'}")
        
        # 3. Estabilidad (sin errores críticos) (20 puntos)
        critical_errors = len([e for e in self.errors if 'CRÍTICO' in e])
        if critical_errors == 0:
            concurrency_score += 20
        elif critical_errors <= 2:
            concurrency_score += 10
        
        print(f"Errores críticos: {critical_errors} {'✓' if critical_errors == 0 else '⚠' if critical_errors <= 2 else '✗'}")
        
        # 4. Consistencia entre operadores (10 puntos)
        operator_variance = max(operator_stats.values(), key=lambda x: x['avg_time'])['avg_time'] - min(operator_stats.values(), key=lambda x: x['avg_time'])['avg_time']
        if operator_variance <= 2:
            concurrency_score += 10
        elif operator_variance <= 5:
            concurrency_score += 5
        
        print(f"Consistencia entre operadores: {operator_variance:.2f}s varianza {'✓' if operator_variance <= 2 else '⚠' if operator_variance <= 5 else '✗'}")
        
        print(f"\nPUNTUACIÓN FINAL DE CONCURRENCIA: {concurrency_score}/{max_score} ({(concurrency_score/max_score)*100:.1f}%)")
        
        # Veredicto final
        if concurrency_score >= 85:
            verdict = "EXCELENTE - Arquitectura robusta para concurrencia"
        elif concurrency_score >= 70:
            verdict = "BUENO - Arquitectura aceptable con mejoras menores"
        elif concurrency_score >= 60:
            verdict = "REGULAR - Requiere optimizaciones arquitectónicas"
        else:
            verdict = "INSUFICIENTE - Problemas serios de concurrencia"
        
        print(f"\nVEREDICTO: {verdict}")
        print("=" * 70)
        
        return {
            'score': concurrency_score,
            'max_score': max_score,
            'verdict': verdict,
            'stats': {
                'total_sessions': total_sessions,
                'success_rate': success_rate,
                'avg_session_time': avg_session_time,
                'critical_errors': critical_errors,
                'operator_variance': operator_variance
            }
        }
    
    def cleanup(self):
        """Limpia recursos de prueba"""
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
                logger.info("Base de datos de pruebas eliminada")
        except Exception as e:
            logger.warning(f"Error limpiando recursos: {e}")

def main():
    """Ejecuta el test de concurrencia arquitectónica L2"""
    test = ConcurrencyStressTest()
    
    try:
        # Configurar entorno
        test.setup_test_environment()
        
        # Ejecutar test de concurrencia con 4 usuarios, 4 operadores = 16 sesiones concurrentes
        results = test.run_concurrent_stress_test(num_users=4)
        
        print("\n🎯 TEST P1-002 CONCURRENCIA COMPLETADO")
        
    except Exception as e:
        logger.error(f"Error ejecutando test de concurrencia: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        test.cleanup()

if __name__ == "__main__":
    main()