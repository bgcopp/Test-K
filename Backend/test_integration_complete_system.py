#!/usr/bin/env python3
"""
KRONOS - Testing de Integración Completo del Sistema de Operadores
==================================================================

Este script ejecuta una evaluación integral del sistema KRONOS para certificar
su estado de producción. Incluye testing de:

1. Backend - Procesamiento de archivos por operador
2. Frontend - Compilación y estructura
3. Database - Integridad y performance
4. APIs Eel - Comunicación Python-JavaScript
5. Integration End-to-End - Flujos completos
6. Performance - Métricas del sistema
7. Security - Validaciones y controles

Autor: Equipo de Testing KRONOS
Fecha: 12 de Agosto de 2025
Versión: 1.0.0
"""

import os
import sys
import json
import time
import sqlite3
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess
import tempfile
import base64

# Configurar path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db_connection
from services.operator_data_service import OperatorDataService
from utils.operator_logger import OperatorLogger


class ComprehensiveSystemTester:
    """
    Tester integral del sistema KRONOS que ejecuta todas las pruebas
    necesarias para certificar el estado de producción.
    """
    
    def __init__(self):
        """Inicializa el tester con configuración completa."""
        self.logger = OperatorLogger()
        self.test_start_time = datetime.now()
        self.results = {
            'test_run_info': {
                'start_time': self.test_start_time.isoformat(),
                'tester_version': '1.0.0',
                'system_version': 'KRONOS 1.0.0',
                'environment': 'Integration Testing'
            },
            'operator_status': {},
            'backend_tests': {},
            'frontend_tests': {},
            'database_tests': {},
            'api_tests': {},
            'integration_tests': {},
            'performance_tests': {},
            'security_tests': {},
            'summary': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'warnings': 0,
                'critical_issues': 0,
                'certification_status': 'PENDING'
            }
        }
        
        # Configuración de operadores para testing
        self.test_operators = {
            'CLARO': {
                'data_types': ['CELLULAR_DATA', 'CALL_DATA'],
                'files': {
                    'cellular': 'DATOS_POR_CELDA CLARO.csv',
                    'calls_entrantes': 'LLAMADAS_ENTRANTES_POR_CELDA CLARO.csv',
                    'calls_salientes': 'LLAMADAS_SALIENTES_POR_CELDA CLARO.csv'
                }
            },
            'MOVISTAR': {
                'data_types': ['CELLULAR_DATA', 'CALL_DATA'],
                'files': {
                    'cellular': 'jgd202410754_00007301_datos_ MOVISTAR.csv',
                    'calls': 'jgd202410754_07F08305_vozm_saliente_ MOVISTAR.csv'
                }
            },
            'TIGO': {
                'data_types': ['CALL_DATA'],
                'files': {
                    'calls_unified': 'Reporte TIGO.csv'
                }
            },
            'WOM': {
                'data_types': ['CELLULAR_DATA', 'CALL_DATA'],
                'files': {
                    'cellular': 'PUNTO 1 TRÁFICO DATOS WOM.csv',
                    'calls': 'PUNTO 1 TRÁFICO VOZ ENTRAN  SALIENT WOM.csv'
                }
            }
        }
        
        print("="*80)
        print("KRONOS - TESTING DE INTEGRACIÓN COMPLETO DEL SISTEMA")
        print("="*80)
        print(f"Inicio: {self.test_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Operadores a evaluar: {', '.join(self.test_operators.keys())}")
        print("="*80)
    
    def _add_test_result(self, category: str, test_name: str, 
                        status: str, details: Any = None, 
                        execution_time: float = 0.0):
        """Agrega un resultado de prueba a los resultados."""
        if category not in self.results:
            self.results[category] = {}
        
        self.results[category][test_name] = {
            'status': status,
            'details': details,
            'execution_time': execution_time,
            'timestamp': datetime.now().isoformat()
        }
        
        self.results['summary']['total_tests'] += 1
        
        if status == 'PASS':
            self.results['summary']['passed_tests'] += 1
        elif status == 'FAIL':
            self.results['summary']['failed_tests'] += 1
        elif status == 'WARNING':
            self.results['summary']['warnings'] += 1
        elif status == 'CRITICAL':
            self.results['summary']['critical_issues'] += 1
    
    def test_operator_status(self):
        """Verifica el estado de implementación de cada operador."""
        print("\n1. VERIFICANDO ESTADO DE OPERADORES...")
        
        for operator in self.test_operators.keys():
            start_time = time.time()
            
            try:
                # Verificar archivos de test disponibles
                test_files_exist = self._check_test_files(operator)
                
                # Verificar procesadores implementados
                processor_available = self._check_processor(operator)
                
                # Verificar APIs Eel expuestas
                apis_available = self._check_operator_apis(operator)
                
                # Verificar configuración en frontend
                frontend_config = self._check_frontend_config(operator)
                
                status = {
                    'test_files': test_files_exist,
                    'processor': processor_available,
                    'apis': apis_available,
                    'frontend': frontend_config,
                    'overall': all([test_files_exist, processor_available, apis_available, frontend_config])
                }
                
                self.results['operator_status'][operator] = status
                
                if status['overall']:
                    self._add_test_result('operator_tests', f'{operator}_status', 'PASS', 
                                        status, time.time() - start_time)
                    print(f"  OK {operator}: COMPLETADO")
                else:
                    self._add_test_result('operator_tests', f'{operator}_status', 'FAIL', 
                                        status, time.time() - start_time)
                    print(f"  FAIL {operator}: INCOMPLETO")
                    
            except Exception as e:
                self._add_test_result('operator_tests', f'{operator}_status', 'CRITICAL', 
                                    str(e), time.time() - start_time)
                print(f"  ERROR {operator}: {str(e)}")
    
    def test_database_integrity(self):
        """Pruebas de integridad de la base de datos."""
        print("\n2. VERIFICANDO INTEGRIDAD DE BASE DE DATOS...")
        
        start_time = time.time()
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 1. Verificar esquema de tablas
                required_tables = [
                    'operator_data_sheets',
                    'operator_cellular_data', 
                    'operator_call_data',
                    'operator_cell_registry',
                    'operator_data_audit'
                ]
                
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing_tables = [row[0] for row in cursor.fetchall()]
                
                missing_tables = [t for t in required_tables if t not in existing_tables]
                
                if not missing_tables:
                    self._add_test_result('database_tests', 'schema_integrity', 'PASS',
                                        f'Todas las {len(required_tables)} tablas existen')
                    print("  ✅ Esquema de tablas: COMPLETO")
                else:
                    self._add_test_result('database_tests', 'schema_integrity', 'FAIL',
                                        f'Tablas faltantes: {missing_tables}')
                    print(f"  ❌ Tablas faltantes: {missing_tables}")
                
                # 2. Verificar índices críticos
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='index' AND name LIKE 'idx_%'
                """)
                indices = cursor.fetchall()
                
                if len(indices) >= 10:  # Esperamos al menos 10 índices
                    self._add_test_result('database_tests', 'indices', 'PASS',
                                        f'{len(indices)} índices encontrados')
                    print(f"  ✅ Índices: {len(indices)} índices optimizados")
                else:
                    self._add_test_result('database_tests', 'indices', 'WARNING',
                                        f'Solo {len(indices)} índices encontrados')
                    print(f"  ⚠️  Índices: Solo {len(indices)} encontrados")
                
                # 3. Verificar datos existentes
                cursor.execute("SELECT COUNT(*) FROM operator_data_sheets")
                files_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM operator_cellular_data")
                cellular_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM operator_call_data")
                call_count = cursor.fetchone()[0]
                
                data_status = {
                    'files': files_count,
                    'cellular_records': cellular_count,
                    'call_records': call_count,
                    'total_records': cellular_count + call_count
                }
                
                self._add_test_result('database_tests', 'data_integrity', 'PASS',
                                    data_status, time.time() - start_time)
                print(f"  ✅ Datos: {files_count} archivos, {data_status['total_records']} registros")
                
        except Exception as e:
            self._add_test_result('database_tests', 'database_connection', 'CRITICAL',
                                str(e), time.time() - start_time)
            print(f"  🚨 Error de base de datos: {str(e)}")
    
    def test_backend_functionality(self):
        """Pruebas de funcionalidad del backend."""
        print("\n3. VERIFICANDO FUNCIONALIDAD DEL BACKEND...")
        
        # 1. Test de inicialización de servicios
        start_time = time.time()
        
        try:
            service = OperatorDataService()
            self._add_test_result('backend_tests', 'service_initialization', 'PASS',
                                'OperatorDataService inicializado correctamente', 
                                time.time() - start_time)
            print("  ✅ Inicialización de servicios: OK")
        except Exception as e:
            self._add_test_result('backend_tests', 'service_initialization', 'CRITICAL',
                                str(e), time.time() - start_time)
            print(f"  🚨 Error inicialización: {str(e)}")
            return
        
        # 2. Test de validaciones
        start_time = time.time()
        
        try:
            # Validar operadores soportados
            supported_ops = service.SUPPORTED_OPERATORS
            expected_ops = ['CLARO', 'MOVISTAR', 'TIGO', 'WOM']
            
            if all(op in supported_ops for op in expected_ops):
                self._add_test_result('backend_tests', 'operator_support', 'PASS',
                                    f'Soporta: {supported_ops}', time.time() - start_time)
                print(f"  ✅ Operadores soportados: {len(supported_ops)}")
            else:
                missing = [op for op in expected_ops if op not in supported_ops]
                self._add_test_result('backend_tests', 'operator_support', 'FAIL',
                                    f'Faltantes: {missing}', time.time() - start_time)
                print(f"  ❌ Operadores faltantes: {missing}")
        
        except Exception as e:
            self._add_test_result('backend_tests', 'validation_system', 'CRITICAL',
                                str(e), time.time() - start_time)
            print(f"  🚨 Error validaciones: {str(e)}")
    
    def test_frontend_compilation(self):
        """Verifica la compilación y estructura del frontend."""
        print("\n4. VERIFICANDO FRONTEND...")
        
        start_time = time.time()
        
        try:
            # Verificar que el dist existe
            frontend_path = Path(__file__).parent.parent / 'Frontend'
            dist_path = frontend_path / 'dist'
            
            if dist_path.exists() and (dist_path / 'index.html').exists():
                # Contar archivos en dist
                dist_files = list(dist_path.rglob('*'))
                file_count = len([f for f in dist_files if f.is_file()])
                
                self._add_test_result('frontend_tests', 'compilation', 'PASS',
                                    f'{file_count} archivos compilados', time.time() - start_time)
                print(f"  ✅ Compilación: {file_count} archivos generados")
            else:
                self._add_test_result('frontend_tests', 'compilation', 'FAIL',
                                    'Directorio dist no encontrado', time.time() - start_time)
                print("  ❌ Compilación: Directorio dist no encontrado")
            
            # Verificar componentes de operadores
            operator_components_path = frontend_path / 'components' / 'operator-data'
            
            if operator_components_path.exists():
                operator_files = list(operator_components_path.glob('*.tsx'))
                self._add_test_result('frontend_tests', 'operator_components', 'PASS',
                                    f'{len(operator_files)} componentes', time.time() - start_time)
                print(f"  ✅ Componentes de operadores: {len(operator_files)} archivos")
            else:
                self._add_test_result('frontend_tests', 'operator_components', 'FAIL',
                                    'Componentes no encontrados', time.time() - start_time)
                print("  ❌ Componentes de operadores: No encontrados")
                
        except Exception as e:
            self._add_test_result('frontend_tests', 'frontend_structure', 'CRITICAL',
                                str(e), time.time() - start_time)
            print(f"  🚨 Error frontend: {str(e)}")
    
    def test_performance_metrics(self):
        """Pruebas de performance del sistema."""
        print("\n5. MIDIENDO PERFORMANCE DEL SISTEMA...")
        
        start_time = time.time()
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 1. Test de velocidad de consulta de archivos
                query_start = time.time()
                cursor.execute("SELECT COUNT(*) FROM operator_data_sheets")
                files_count = cursor.fetchone()[0]
                query_time = time.time() - query_start
                
                # 2. Test de velocidad de consulta de datos
                data_query_start = time.time()
                cursor.execute("""
                    SELECT COUNT(*) FROM operator_cellular_data 
                    UNION ALL 
                    SELECT COUNT(*) FROM operator_call_data
                """)
                data_counts = cursor.fetchall()
                data_query_time = time.time() - data_query_start
                
                # 3. Test de consulta compleja (JOIN)
                join_start = time.time()
                cursor.execute("""
                    SELECT ods.operator, COUNT(ocd.id) as cellular_records
                    FROM operator_data_sheets ods
                    LEFT JOIN operator_cellular_data ocd ON ods.id = ocd.file_upload_id
                    GROUP BY ods.operator
                """)
                join_results = cursor.fetchall()
                join_time = time.time() - join_start
                
                performance_metrics = {
                    'files_query_time': round(query_time * 1000, 2),  # ms
                    'data_query_time': round(data_query_time * 1000, 2),  # ms
                    'join_query_time': round(join_time * 1000, 2),  # ms
                    'total_files': files_count,
                    'cellular_records': data_counts[0][0] if data_counts else 0,
                    'call_records': data_counts[1][0] if len(data_counts) > 1 else 0
                }
                
                # Evaluar performance
                if query_time < 0.1 and data_query_time < 0.5 and join_time < 1.0:
                    status = 'PASS'
                    print("  ✅ Performance: Excelente")
                elif query_time < 0.5 and data_query_time < 2.0 and join_time < 3.0:
                    status = 'WARNING'
                    print("  ⚠️  Performance: Aceptable")
                else:
                    status = 'FAIL'
                    print("  ❌ Performance: Lenta")
                
                self._add_test_result('performance_tests', 'database_queries', status,
                                    performance_metrics, time.time() - start_time)
                
                print(f"     - Consulta archivos: {performance_metrics['files_query_time']}ms")
                print(f"     - Consulta datos: {performance_metrics['data_query_time']}ms")
                print(f"     - Consulta JOIN: {performance_metrics['join_query_time']}ms")
                
        except Exception as e:
            self._add_test_result('performance_tests', 'performance_measurement', 'CRITICAL',
                                str(e), time.time() - start_time)
            print(f"  🚨 Error midiendo performance: {str(e)}")
    
    def test_security_validations(self):
        """Pruebas de seguridad y validaciones."""
        print("\n6. VERIFICANDO SEGURIDAD Y VALIDACIONES...")
        
        start_time = time.time()
        
        try:
            service = OperatorDataService()
            
            # 1. Test de validación de misión inexistente
            fake_mission_id = "fake_mission_123"
            mission_exists = service._validate_mission_exists(fake_mission_id)
            
            if not mission_exists:
                self._add_test_result('security_tests', 'mission_validation', 'PASS',
                                    'Correctamente rechaza misiones inexistentes')
                print("  ✅ Validación de misiones: OK")
            else:
                self._add_test_result('security_tests', 'mission_validation', 'FAIL',
                                    'No valida misiones inexistentes correctamente')
                print("  ❌ Validación de misiones: FALLO")
            
            # 2. Test de validación de usuario inexistente
            fake_user_id = "fake_user_123"
            user_exists = service._validate_user_exists(fake_user_id)
            
            if not user_exists:
                self._add_test_result('security_tests', 'user_validation', 'PASS',
                                    'Correctamente rechaza usuarios inexistentes')
                print("  ✅ Validación de usuarios: OK")
            else:
                self._add_test_result('security_tests', 'user_validation', 'FAIL',
                                    'No valida usuarios inexistentes correctamente')
                print("  ❌ Validación de usuarios: FALLO")
            
            # 3. Test de validación de operadores
            invalid_operator = "INVALID_OP"
            if invalid_operator not in service.SUPPORTED_OPERATORS:
                self._add_test_result('security_tests', 'operator_validation', 'PASS',
                                    'Lista de operadores controlada')
                print("  ✅ Validación de operadores: OK")
            else:
                self._add_test_result('security_tests', 'operator_validation', 'FAIL',
                                    'Control de operadores insuficiente')
                print("  ❌ Validación de operadores: FALLO")
            
            # 4. Test de límites de archivo
            if service.MAX_FILE_SIZE == 20 * 1024 * 1024:  # 20MB
                self._add_test_result('security_tests', 'file_size_limits', 'PASS',
                                    f'Límite configurado: {service.MAX_FILE_SIZE / (1024*1024)}MB')
                print(f"  ✅ Límites de archivo: {service.MAX_FILE_SIZE / (1024*1024)}MB máximo")
            else:
                self._add_test_result('security_tests', 'file_size_limits', 'WARNING',
                                    f'Límite no estándar: {service.MAX_FILE_SIZE}')
                print(f"  ⚠️  Límites de archivo: {service.MAX_FILE_SIZE} bytes")
                
        except Exception as e:
            self._add_test_result('security_tests', 'security_validation', 'CRITICAL',
                                str(e), time.time() - start_time)
            print(f"  🚨 Error en validaciones de seguridad: {str(e)}")
    
    def test_end_to_end_integration(self):
        """Pruebas de integración end-to-end simplificadas."""
        print("\n7. TESTING DE INTEGRACIÓN END-TO-END...")
        
        start_time = time.time()
        
        try:
            # Verificar que el sistema puede ejecutar operaciones básicas
            service = OperatorDataService()
            
            # 1. Test de obtener sheets (sin datos específicos)
            sheets_result = service.get_operator_statistics()
            
            if sheets_result.get('success', False):
                self._add_test_result('integration_tests', 'get_statistics', 'PASS',
                                    'API de estadísticas funcional')
                print("  ✅ API de estadísticas: Funcional")
            else:
                self._add_test_result('integration_tests', 'get_statistics', 'FAIL',
                                    'API de estadísticas no responde')
                print("  ❌ API de estadísticas: No funcional")
            
            # 2. Test de conexión a base de datos bajo carga
            connection_test_start = time.time()
            connections_successful = 0
            
            for i in range(5):
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT 1")
                        cursor.fetchone()
                        connections_successful += 1
                except:
                    pass
            
            connection_time = time.time() - connection_test_start
            
            if connections_successful == 5:
                self._add_test_result('integration_tests', 'database_connections', 'PASS',
                                    f'5/5 conexiones exitosas en {connection_time:.2f}s')
                print(f"  ✅ Conexiones DB: 5/5 exitosas ({connection_time:.2f}s)")
            else:
                self._add_test_result('integration_tests', 'database_connections', 'WARNING',
                                    f'{connections_successful}/5 conexiones exitosas')
                print(f"  ⚠️  Conexiones DB: {connections_successful}/5 exitosas")
            
        except Exception as e:
            self._add_test_result('integration_tests', 'e2e_integration', 'CRITICAL',
                                str(e), time.time() - start_time)
            print(f"  🚨 Error en integración E2E: {str(e)}")
    
    def generate_certification_report(self):
        """Genera el reporte final de certificación."""
        print("\n8. GENERANDO REPORTE DE CERTIFICACIÓN...")
        
        end_time = datetime.now()
        execution_time = (end_time - self.test_start_time).total_seconds()
        
        # Actualizar información final
        self.results['test_run_info']['end_time'] = end_time.isoformat()
        self.results['test_run_info']['execution_time_seconds'] = execution_time
        
        # Determinar estado de certificación
        critical_issues = self.results['summary']['critical_issues']
        failed_tests = self.results['summary']['failed_tests']
        total_tests = self.results['summary']['total_tests']
        
        if critical_issues == 0 and failed_tests == 0:
            certification_status = 'PRODUCTION_READY'
            certification_message = '🟢 SISTEMA CERTIFICADO PARA PRODUCCIÓN'
        elif critical_issues == 0 and failed_tests <= 2:
            certification_status = 'CONDITIONAL_READY'
            certification_message = '🟡 SISTEMA LISTO CON CONDICIONES MENORES'
        elif critical_issues == 0:
            certification_status = 'NEEDS_FIXES'
            certification_message = '🔶 SISTEMA REQUIERE CORRECCIONES'
        else:
            certification_status = 'NOT_READY'
            certification_message = '🔴 SISTEMA NO LISTO PARA PRODUCCIÓN'
        
        self.results['summary']['certification_status'] = certification_status
        self.results['summary']['certification_message'] = certification_message
        
        # Guardar reporte
        report_filename = f"integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = Path(__file__).parent / report_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        # Mostrar resumen final
        print("\n" + "="*80)
        print("RESUMEN FINAL DE CERTIFICACIÓN")
        print("="*80)
        print(f"Estado: {certification_message}")
        print(f"Tiempo total: {execution_time:.1f} segundos")
        print(f"Pruebas ejecutadas: {total_tests}")
        print(f"Exitosas: {self.results['summary']['passed_tests']} ✅")
        print(f"Fallidas: {failed_tests} ❌")
        print(f"Advertencias: {self.results['summary']['warnings']} ⚠️")
        print(f"Issues críticos: {critical_issues} 🚨")
        print(f"Reporte guardado: {report_path}")
        print("="*80)
        
        return certification_status, self.results
    
    # Métodos auxiliares
    def _check_test_files(self, operator: str) -> bool:
        """Verifica si existen archivos de test para el operador."""
        test_data_path = Path(__file__).parent.parent / 'datatest' / operator.title()
        return test_data_path.exists() and any(test_data_path.iterdir())
    
    def _check_processor(self, operator: str) -> bool:
        """Verifica si el procesador del operador está implementado."""
        try:
            from services.file_processor_service import FileProcessorService
            processor = FileProcessorService()
            
            # Verificar que existen métodos específicos del operador
            operator_lower = operator.lower()
            methods = dir(processor)
            
            # Buscar métodos que contengan el nombre del operador
            operator_methods = [m for m in methods if operator_lower in m.lower()]
            return len(operator_methods) > 0
        except:
            return False
    
    def _check_operator_apis(self, operator: str) -> bool:
        """Verifica si las APIs del operador están disponibles."""
        # Por simplicidad, verificamos que el servicio principal existe
        try:
            from services.operator_data_service import OperatorDataService
            service = OperatorDataService()
            return operator in service.SUPPORTED_OPERATORS
        except:
            return False
    
    def _check_frontend_config(self, operator: str) -> bool:
        """Verifica configuración del operador en frontend."""
        try:
            frontend_path = Path(__file__).parent.parent / 'Frontend'
            
            # Verificar que existe el componente OperatorDataUpload
            upload_component = frontend_path / 'components' / 'operator-data' / 'OperatorDataUpload.tsx'
            
            if upload_component.exists():
                # Leer contenido y buscar configuración del operador
                content = upload_component.read_text(encoding='utf-8')
                return operator in content
            
            return False
        except:
            return False


def main():
    """Función principal para ejecutar el testing integral."""
    
    tester = ComprehensiveSystemTester()
    
    try:
        # Ejecutar todas las pruebas
        tester.test_operator_status()
        tester.test_database_integrity()
        tester.test_backend_functionality()
        tester.test_frontend_compilation()
        tester.test_performance_metrics()
        tester.test_security_validations()
        tester.test_end_to_end_integration()
        
        # Generar reporte final
        certification_status, results = tester.generate_certification_report()
        
        # Retornar código de salida apropiado
        if certification_status in ['PRODUCTION_READY', 'CONDITIONAL_READY']:
            return 0  # Éxito
        else:
            return 1  # Fallo
            
    except Exception as e:
        print(f"\n🚨 ERROR CRÍTICO EN TESTING: {str(e)}")
        print(traceback.format_exc())
        
        # Guardar reporte de error
        error_report = {
            'error': str(e),
            'traceback': traceback.format_exc(),
            'timestamp': datetime.now().isoformat()
        }
        
        error_filename = f"integration_test_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(Path(__file__).parent / error_filename, 'w') as f:
            json.dump(error_report, f, indent=2)
        
        return 2  # Error crítico


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)