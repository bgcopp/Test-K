#!/usr/bin/env python3
"""
Database Validator for KRONOS CLARO E2E Tests
===============================================

Script especializado para validación de base de datos SQLite
desde tests de Playwright. Proporciona validaciones específicas
para números objetivo CLARO y genera reportes JSON.

Uso:
    python database-validator.py --action validate_targets
    python database-validator.py --action validate_claro_data
    python database-validator.py --action generate_report

Author: Boris - KRONOS Testing Team
"""

import sys
import sqlite3
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

class KronosDatabaseValidator:
    """Validador de base de datos KRONOS para tests E2E"""
    
    def __init__(self, db_path: str = None):
        """
        Inicializar validador
        
        Args:
            db_path: Ruta a la base de datos SQLite. Por defecto busca en Backend/
        """
        if db_path is None:
            # Buscar base de datos en directorio Backend
            backend_path = Path(__file__).parent.parent / 'Backend'
            self.db_path = backend_path / 'kronos.db'
        else:
            self.db_path = Path(db_path)
            
        self.target_numbers = [
            '3224274851', '3208611034', '3104277553', 
            '3102715509', '3143534707', '3214161903'
        ]
        
        self.critical_numbers = ['3104277553', '3224274851']
        
    def validate_database_exists(self) -> Dict[str, Any]:
        """Validar que la base de datos existe y es accesible"""
        result = {
            'test': 'database_exists',
            'status': 'FAILED',
            'message': '',
            'details': {}
        }
        
        try:
            if not self.db_path.exists():
                result['message'] = f'Base de datos no existe: {self.db_path}'
                return result
                
            # Intentar conexión
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Verificar tabla operator_call_data
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='operator_call_data'
            """)
            
            table_exists = cursor.fetchone() is not None
            
            if table_exists:
                # Contar registros
                cursor.execute("SELECT COUNT(*) FROM operator_call_data")
                total_records = cursor.fetchone()[0]
                
                result['status'] = 'PASSED'
                result['message'] = f'Base de datos válida con {total_records} registros'
                result['details'] = {
                    'db_path': str(self.db_path),
                    'table_exists': True,
                    'total_records': total_records
                }
            else:
                result['message'] = 'Tabla operator_call_data no existe'
                result['details'] = {'table_exists': False}
            
            conn.close()
            
        except Exception as e:
            result['message'] = f'Error accediendo a BD: {str(e)}'
            result['details'] = {'error': str(e)}
            
        return result
    
    def validate_target_numbers(self) -> Dict[str, Any]:
        """Validar que los números objetivo están en la base de datos"""
        result = {
            'test': 'target_numbers_validation',
            'status': 'FAILED',
            'message': '',
            'details': {},
            'target_results': {}
        }
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            total_found = 0
            
            for number in self.target_numbers:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(DISTINCT file_upload_id) as files,
                        COUNT(CASE WHEN tipo_llamada = 'ENTRANTE' THEN 1 END) as entrantes,
                        COUNT(CASE WHEN tipo_llamada = 'SALIENTE' THEN 1 END) as salientes,
                        MIN(fecha_hora_llamada) as primera,
                        MAX(fecha_hora_llamada) as ultima
                    FROM operator_call_data
                    WHERE numero_origen = ? OR numero_destino = ? OR numero_objetivo = ?
                """, (number, number, number))
                
                row = cursor.fetchone()
                
                number_result = {
                    'total_records': row[0],
                    'unique_files': row[1],
                    'incoming_calls': row[2],
                    'outgoing_calls': row[3],
                    'first_call': row[4],
                    'last_call': row[5],
                    'found': row[0] > 0
                }
                
                result['target_results'][number] = number_result
                
                if row[0] > 0:
                    total_found += 1
            
            # Validar números críticos
            critical_found = sum(1 for num in self.critical_numbers 
                               if result['target_results'][num]['found'])
            
            result['details'] = {
                'total_targets': len(self.target_numbers),
                'targets_found': total_found,
                'critical_targets': len(self.critical_numbers),
                'critical_found': critical_found,
                'coverage_percentage': (total_found / len(self.target_numbers)) * 100
            }
            
            # Determinar estado
            if critical_found == len(self.critical_numbers):
                result['status'] = 'PASSED'
                result['message'] = f'Todos los números críticos encontrados. Cobertura: {result["details"]["coverage_percentage"]:.1f}%'
            else:
                result['message'] = f'Solo {critical_found}/{len(self.critical_numbers)} números críticos encontrados'
            
            conn.close()
            
        except Exception as e:
            result['message'] = f'Error validando números objetivo: {str(e)}'
            result['details'] = {'error': str(e)}
            
        return result
    
    def validate_claro_data(self) -> Dict[str, Any]:
        """Validar integridad de datos CLARO específicamente"""
        result = {
            'test': 'claro_data_validation',
            'status': 'FAILED',
            'message': '',
            'details': {}
        }
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Validaciones específicas para CLARO
            validations = [
                {
                    'name': 'claro_records',
                    'query': "SELECT COUNT(*) FROM operator_call_data WHERE UPPER(operator) LIKE '%CLARO%'",
                    'expected_min': 1
                },
                {
                    'name': 'valid_dates',
                    'query': "SELECT COUNT(*) FROM operator_call_data WHERE fecha_hora_llamada IS NOT NULL AND fecha_hora_llamada != ''",
                    'expected_min': 1
                },
                {
                    'name': 'valid_durations',
                    'query': "SELECT COUNT(*) FROM operator_call_data WHERE duracion_segundos >= 0",
                    'expected_min': 1
                },
                {
                    'name': 'valid_cells',
                    'query': """SELECT COUNT(*) FROM operator_call_data 
                            WHERE (celda_origen IS NOT NULL AND celda_origen != '') 
                               OR (celda_destino IS NOT NULL AND celda_destino != '')""",
                    'expected_min': 1
                },
                {
                    'name': 'distinct_file_uploads',
                    'query': "SELECT COUNT(DISTINCT file_upload_id) FROM operator_call_data WHERE UPPER(operator) LIKE '%CLARO%'",
                    'expected_min': 1
                }
            ]
            
            validation_results = {}
            all_passed = True
            
            for validation in validations:
                cursor.execute(validation['query'])
                count = cursor.fetchone()[0]
                
                passed = count >= validation['expected_min']
                if not passed:
                    all_passed = False
                
                validation_results[validation['name']] = {
                    'count': count,
                    'expected_min': validation['expected_min'],
                    'passed': passed
                }
            
            result['details'] = validation_results
            
            if all_passed:
                result['status'] = 'PASSED'
                result['message'] = 'Todas las validaciones de datos CLARO pasaron'
            else:
                failed_validations = [name for name, res in validation_results.items() if not res['passed']]
                result['message'] = f'Validaciones fallidas: {", ".join(failed_validations)}'
            
            conn.close()
            
        except Exception as e:
            result['message'] = f'Error validando datos CLARO: {str(e)}'
            result['details'] = {'error': str(e)}
            
        return result
    
    def validate_boris_case(self) -> Dict[str, Any]:
        """Validar el caso específico reportado por Boris: 3104277553 → 3224274851"""
        result = {
            'test': 'boris_case_validation',
            'status': 'FAILED',
            'message': '',
            'details': {}
        }
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Buscar comunicación específica entre números críticos
            cursor.execute("""
                SELECT 
                    id, operator, tipo_llamada, numero_origen, numero_destino,
                    fecha_hora_llamada, duracion_segundos, celda_origen, celda_destino
                FROM operator_call_data
                WHERE (numero_origen = '3104277553' AND numero_destino = '3224274851')
                   OR (numero_origen = '3224274851' AND numero_destino = '3104277553')
                ORDER BY fecha_hora_llamada DESC
                LIMIT 5
            """)
            
            records = cursor.fetchall()
            
            result['details'] = {
                'records_found': len(records),
                'communications': []
            }
            
            for record in records:
                communication = {
                    'id': record[0],
                    'operator': record[1],
                    'call_type': record[2],
                    'origin': record[3],
                    'destination': record[4],
                    'datetime': record[5],
                    'duration': record[6],
                    'origin_cell': record[7],
                    'destination_cell': record[8]
                }
                result['details']['communications'].append(communication)
            
            if len(records) > 0:
                result['status'] = 'PASSED'
                result['message'] = f'Caso Boris validado: {len(records)} comunicaciones encontradas'
            else:
                result['message'] = 'Caso Boris NO encontrado: sin comunicaciones entre 3104277553 y 3224274851'
            
            conn.close()
            
        except Exception as e:
            result['message'] = f'Error validando caso Boris: {str(e)}'
            result['details'] = {'error': str(e)}
            
        return result
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generar reporte comprehensivo de validación"""
        timestamp = datetime.now()
        
        report = {
            'report_type': 'KRONOS_DATABASE_VALIDATION',
            'timestamp': timestamp.isoformat(),
            'database_path': str(self.db_path),
            'target_numbers': self.target_numbers,
            'critical_numbers': self.critical_numbers,
            'validations': {},
            'summary': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'overall_status': 'UNKNOWN'
            }
        }
        
        # Ejecutar todas las validaciones
        validations = [
            ('database_exists', self.validate_database_exists),
            ('target_numbers', self.validate_target_numbers),
            ('claro_data', self.validate_claro_data),
            ('boris_case', self.validate_boris_case)
        ]
        
        for validation_name, validation_func in validations:
            try:
                validation_result = validation_func()
                report['validations'][validation_name] = validation_result
                
                report['summary']['total_tests'] += 1
                if validation_result['status'] == 'PASSED':
                    report['summary']['passed_tests'] += 1
                else:
                    report['summary']['failed_tests'] += 1
                    
            except Exception as e:
                report['validations'][validation_name] = {
                    'test': validation_name,
                    'status': 'ERROR',
                    'message': f'Error ejecutando validación: {str(e)}',
                    'details': {'error': str(e)}
                }
                report['summary']['total_tests'] += 1
                report['summary']['failed_tests'] += 1
        
        # Determinar estado general
        if report['summary']['failed_tests'] == 0:
            report['summary']['overall_status'] = 'PASSED'
        elif report['summary']['passed_tests'] > report['summary']['failed_tests']:
            report['summary']['overall_status'] = 'MOSTLY_PASSED'
        else:
            report['summary']['overall_status'] = 'FAILED'
        
        return report

def main():
    """Función principal de línea de comandos"""
    parser = argparse.ArgumentParser(description='KRONOS Database Validator for E2E Tests')
    parser.add_argument('--action', 
                       choices=['validate_targets', 'validate_claro_data', 'validate_boris_case', 'generate_report'],
                       required=True,
                       help='Acción de validación a ejecutar')
    parser.add_argument('--db-path', 
                       help='Ruta a la base de datos SQLite')
    parser.add_argument('--output', 
                       help='Archivo de salida para reporte JSON')
    
    args = parser.parse_args()
    
    # Inicializar validador
    validator = KronosDatabaseValidator(args.db_path)
    
    # Ejecutar acción solicitada
    if args.action == 'validate_targets':
        result = validator.validate_target_numbers()
    elif args.action == 'validate_claro_data':
        result = validator.validate_claro_data()
    elif args.action == 'validate_boris_case':
        result = validator.validate_boris_case()
    elif args.action == 'generate_report':
        result = validator.generate_comprehensive_report()
    
    # Mostrar resultado en consola
    print("="*80)
    print(f"KRONOS DATABASE VALIDATION - {args.action.upper()}")
    print("="*80)
    print(f"Status: {result.get('status', result.get('summary', {}).get('overall_status', 'UNKNOWN'))}")
    print(f"Message: {result.get('message', 'Comprehensive report generated')}")
    print("="*80)
    
    # Guardar resultado
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path(f'validation_result_{args.action}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"Resultado guardado en: {output_path}")
    
    # Exit code basado en el resultado
    if args.action == 'generate_report':
        exit_code = 0 if result['summary']['overall_status'] in ['PASSED', 'MOSTLY_PASSED'] else 1
    else:
        exit_code = 0 if result['status'] == 'PASSED' else 1
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()