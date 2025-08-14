#!/usr/bin/env python3
"""
KRONOS - Testing de Integración Simplificado del Sistema de Operadores
=====================================================================

Script simplificado para certificar el estado de producción del sistema KRONOS.
Versión sin emojis para compatibilidad con Windows.

Autor: Equipo de Testing KRONOS
Fecha: 12 de Agosto de 2025
"""

import os
import sys
import json
import time
import sqlite3
from datetime import datetime
from pathlib import Path

# Configurar path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db_connection
from services.operator_data_service import OperatorDataService


class SimpleSystemTester:
    """Tester simplificado del sistema KRONOS."""
    
    def __init__(self):
        self.test_start_time = datetime.now()
        self.results = {
            'start_time': self.test_start_time.isoformat(),
            'tests': {},
            'summary': {
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'warnings': 0,
                'critical': 0
            }
        }
        
        print("="*80)
        print("KRONOS - TESTING DE INTEGRACIÓN COMPLETO DEL SISTEMA")
        print("="*80)
        print(f"Inicio: {self.test_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
    
    def add_result(self, test_name: str, status: str, details: str = ""):
        """Agrega resultado de prueba."""
        self.results['tests'][test_name] = {
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        
        self.results['summary']['total_tests'] += 1
        
        if status == 'PASS':
            self.results['summary']['passed'] += 1
        elif status == 'FAIL':
            self.results['summary']['failed'] += 1
        elif status == 'WARNING':
            self.results['summary']['warnings'] += 1
        elif status == 'CRITICAL':
            self.results['summary']['critical'] += 1
    
    def test_database(self):
        """Test de base de datos."""
        print("\\n1. VERIFICANDO BASE DE DATOS...")
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Verificar tablas principales
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                required_tables = [
                    'operator_data_sheets',
                    'operator_cellular_data', 
                    'operator_call_data'
                ]
                
                missing = [t for t in required_tables if t not in tables]
                
                if not missing:
                    self.add_result('database_tables', 'PASS', f'{len(tables)} tablas encontradas')
                    print(f"   OK: {len(tables)} tablas en base de datos")
                else:
                    self.add_result('database_tables', 'FAIL', f'Faltantes: {missing}')
                    print(f"   FAIL: Tablas faltantes: {missing}")
                
                # Verificar datos
                cursor.execute("SELECT COUNT(*) FROM operator_data_sheets")
                files_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM operator_cellular_data")
                cellular_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM operator_call_data")
                call_count = cursor.fetchone()[0]
                
                total_records = cellular_count + call_count
                
                if total_records > 0:
                    self.add_result('database_data', 'PASS', 
                                  f'{files_count} archivos, {total_records} registros')
                    print(f"   OK: {files_count} archivos procesados, {total_records} registros")
                else:
                    self.add_result('database_data', 'WARNING', 'No hay datos de prueba')
                    print("   WARNING: No hay datos de prueba en el sistema")
                
        except Exception as e:
            self.add_result('database_connection', 'CRITICAL', str(e))
            print(f"   CRITICAL: Error de base de datos: {str(e)}")
    
    def test_operators(self):
        """Test de operadores."""
        print("\\n2. VERIFICANDO OPERADORES...")
        
        try:
            service = OperatorDataService()
            
            expected_operators = ['CLARO', 'MOVISTAR', 'TIGO', 'WOM']
            supported_operators = service.SUPPORTED_OPERATORS
            
            for operator in expected_operators:
                if operator in supported_operators:
                    self.add_result(f'operator_{operator.lower()}', 'PASS', 'Operador soportado')
                    print(f"   OK: {operator} - Implementado")
                else:
                    self.add_result(f'operator_{operator.lower()}', 'FAIL', 'Operador no soportado')
                    print(f"   FAIL: {operator} - No implementado")
            
            # Verificar archivos de test
            test_data_path = Path(__file__).parent.parent / 'datatest'
            
            if test_data_path.exists():
                test_dirs = [d.name for d in test_data_path.iterdir() if d.is_dir()]
                available_test_data = [d for d in expected_operators if d.title() in test_dirs or d.lower() in test_dirs]
                
                self.add_result('test_data_availability', 'PASS', 
                              f'Datos de prueba para: {available_test_data}')
                print(f"   OK: Datos de prueba disponibles para: {available_test_data}")
            else:
                self.add_result('test_data_availability', 'WARNING', 'Directorio datatest no encontrado')
                print("   WARNING: Directorio datatest no encontrado")
        
        except Exception as e:
            self.add_result('operators_system', 'CRITICAL', str(e))
            print(f"   CRITICAL: Error en sistema de operadores: {str(e)}")
    
    def test_frontend(self):
        """Test de frontend."""
        print("\\n3. VERIFICANDO FRONTEND...")
        
        try:
            frontend_path = Path(__file__).parent.parent / 'Frontend'
            
            # Verificar compilación
            dist_path = frontend_path / 'dist'
            
            if dist_path.exists() and (dist_path / 'index.html').exists():
                dist_files = list(dist_path.rglob('*'))
                file_count = len([f for f in dist_files if f.is_file()])
                
                self.add_result('frontend_compilation', 'PASS', f'{file_count} archivos compilados')
                print(f"   OK: Frontend compilado - {file_count} archivos")
            else:
                self.add_result('frontend_compilation', 'FAIL', 'Directorio dist no encontrado')
                print("   FAIL: Frontend no compilado")
            
            # Verificar componentes de operadores
            operator_components = frontend_path / 'components' / 'operator-data'
            
            if operator_components.exists():
                component_files = list(operator_components.glob('*.tsx'))
                self.add_result('operator_components', 'PASS', f'{len(component_files)} componentes')
                print(f"   OK: {len(component_files)} componentes de operadores")
            else:
                self.add_result('operator_components', 'FAIL', 'Componentes no encontrados')
                print("   FAIL: Componentes de operadores no encontrados")
        
        except Exception as e:
            self.add_result('frontend_system', 'CRITICAL', str(e))
            print(f"   CRITICAL: Error en frontend: {str(e)}")
    
    def test_performance(self):
        """Test de performance."""
        print("\\n4. VERIFICANDO PERFORMANCE...")
        
        try:
            start_time = time.time()
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Test de consulta simple
                query_start = time.time()
                cursor.execute("SELECT COUNT(*) FROM operator_data_sheets")
                files_count = cursor.fetchone()[0]
                query_time = time.time() - query_start
                
                # Test de consulta compleja
                join_start = time.time()
                cursor.execute("""
                    SELECT ods.operator, COUNT(ocd.id) as cellular_records
                    FROM operator_data_sheets ods
                    LEFT JOIN operator_cellular_data ocd ON ods.id = ocd.file_upload_id
                    GROUP BY ods.operator
                """)
                join_results = cursor.fetchall()
                join_time = time.time() - join_start
                
                if query_time < 0.1 and join_time < 1.0:
                    status = 'PASS'
                    message = 'Performance excelente'
                elif query_time < 0.5 and join_time < 3.0:
                    status = 'WARNING'
                    message = 'Performance aceptable'
                else:
                    status = 'FAIL'
                    message = 'Performance lenta'
                
                details = f'Consulta simple: {query_time*1000:.1f}ms, JOIN: {join_time*1000:.1f}ms'
                self.add_result('performance_database', status, details)
                print(f"   {status}: {message} ({details})")
        
        except Exception as e:
            self.add_result('performance_system', 'CRITICAL', str(e))
            print(f"   CRITICAL: Error midiendo performance: {str(e)}")
    
    def test_security(self):
        """Test de seguridad."""
        print("\\n5. VERIFICANDO SEGURIDAD...")
        
        try:
            service = OperatorDataService()
            
            # Test de validaciones
            fake_mission = service._validate_mission_exists("fake_mission_123")
            fake_user = service._validate_user_exists("fake_user_123")
            
            if not fake_mission and not fake_user:
                self.add_result('security_validations', 'PASS', 'Validaciones funcionando')
                print("   OK: Validaciones de seguridad funcionando")
            else:
                self.add_result('security_validations', 'FAIL', 'Validaciones no funcionan')
                print("   FAIL: Validaciones de seguridad no funcionan")
            
            # Test de límites
            max_size = service.MAX_FILE_SIZE
            expected_size = 20 * 1024 * 1024  # 20MB
            
            if max_size == expected_size:
                self.add_result('security_limits', 'PASS', f'Límite: {max_size/1024/1024}MB')
                print(f"   OK: Límite de archivo configurado: {max_size/1024/1024}MB")
            else:
                self.add_result('security_limits', 'WARNING', f'Límite no estándar: {max_size}')
                print(f"   WARNING: Límite no estándar: {max_size}")
        
        except Exception as e:
            self.add_result('security_system', 'CRITICAL', str(e))
            print(f"   CRITICAL: Error en validaciones de seguridad: {str(e)}")
    
    def generate_report(self):
        """Genera reporte final."""
        print("\\n6. GENERANDO REPORTE FINAL...")
        
        end_time = datetime.now()
        execution_time = (end_time - self.test_start_time).total_seconds()
        
        self.results['end_time'] = end_time.isoformat()
        self.results['execution_time_seconds'] = execution_time
        
        # Determinar certificación
        summary = self.results['summary']
        
        if summary['critical'] == 0 and summary['failed'] == 0:
            certification = 'PRODUCTION_READY'
            message = 'SISTEMA CERTIFICADO PARA PRODUCCIÓN'
        elif summary['critical'] == 0 and summary['failed'] <= 2:
            certification = 'CONDITIONAL_READY'
            message = 'SISTEMA LISTO CON CONDICIONES MENORES'
        elif summary['critical'] == 0:
            certification = 'NEEDS_FIXES'
            message = 'SISTEMA REQUIERE CORRECCIONES'
        else:
            certification = 'NOT_READY'
            message = 'SISTEMA NO LISTO PARA PRODUCCIÓN'
        
        self.results['certification'] = {
            'status': certification,
            'message': message
        }
        
        # Guardar reporte
        report_filename = f"integration_simple_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = Path(__file__).parent / report_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        # Mostrar resumen
        print("\\n" + "="*80)
        print("RESUMEN FINAL DE CERTIFICACIÓN")
        print("="*80)
        print(f"Estado: {message}")
        print(f"Tiempo total: {execution_time:.1f} segundos")
        print(f"Pruebas totales: {summary['total_tests']}")
        print(f"Exitosas: {summary['passed']}")
        print(f"Fallidas: {summary['failed']}")
        print(f"Advertencias: {summary['warnings']}")
        print(f"Críticas: {summary['critical']}")
        print(f"Reporte guardado: {report_path}")
        print("="*80)
        
        return certification, self.results


def main():
    """Función principal."""
    tester = SimpleSystemTester()
    
    try:
        tester.test_database()
        tester.test_operators()
        tester.test_frontend()
        tester.test_performance()
        tester.test_security()
        certification, results = tester.generate_report()
        
        if certification in ['PRODUCTION_READY', 'CONDITIONAL_READY']:
            return 0
        else:
            return 1
    
    except Exception as e:
        print(f"\\nERROR CRÍTICO: {str(e)}")
        return 2


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)