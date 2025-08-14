#!/usr/bin/env python3
"""
KRONOS - Validación Completa de Correcciones CLARO
================================================================

Este script valida exhaustivamente las dos correcciones críticas
implementadas para resolver el problema de carga de archivos CLARO:

FIX 1: Corrección de IDs de tipos de documento en frontend
FIX 2: Corrección de nombres de campos en respuesta del backend

Autor: Sistema KRONOS - Testing Engineer
Fecha: 2025-08-12
Objetivo: Certificación final de resolución completa del problema CLARO
"""

import sys
import os
import json
import base64
import sqlite3
from datetime import datetime
from pathlib import Path
import traceback
import logging

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import get_db_connection, init_database
from services.operator_data_service import upload_operator_data

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('claro_fix_validation_comprehensive.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ClaroFixValidator:
    """Validador completo de correcciones CLARO"""
    
    def __init__(self):
        """Inicializa el validador con datos de prueba"""
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'test_summary': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'critical_fixes_validated': []
            },
            'frontend_fix_validation': {},
            'backend_fix_validation': {},
            'integration_tests': {},
            'regression_tests': {},
            'certification_status': 'PENDING'
        }
        
        # Datos de prueba CLARO simulados
        self.claro_cellular_data = """numero,fecha_trafico,tipo_cdr,celda_decimal,lac_decimal
573001234567,2024-08-01 10:15:30,DATA,12345,678
573007654321,2024-08-01 10:20:45,DATA,12346,679
573009876543,2024-08-01 10:25:15,DATA,12347,680"""

        self.claro_call_data = """celda_inicio_llamada,celda_final_llamada,originador,receptor,fecha_hora,duracion,tipo
12345,12346,573001234567,573007654321,2024-08-01 14:30:15,120,SALIENTE
12347,12348,573007654321,573009876543,2024-08-01 14:35:20,95,ENTRANTE
12349,12350,573009876543,573001234567,2024-08-01 14:40:10,180,SALIENTE"""
        
        self.setup_test_environment()
    
    def setup_test_environment(self):
        """Configura el entorno de pruebas"""
        try:
            # Inicializar base de datos de prueba
            current_dir = Path(__file__).parent
            test_db_path = current_dir / 'test_claro_fix_validation.db'
            
            if test_db_path.exists():
                test_db_path.unlink()
            
            init_database(str(test_db_path), force_recreate=True)
            
            # Insertar datos de prueba necesarios
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Insertar usuario de prueba (usando hash bcrypt válido)
                cursor.execute("""
                    INSERT INTO users (id, email, name, password_hash, role_id, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, ('test-user-123', 'test@claro.com', 'Test User', 
                      '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj5HzGR3fP4a', 
                      '1', 'active', datetime.now().isoformat()))
                
                # Insertar misión de prueba
                cursor.execute("""
                    INSERT INTO missions (id, code, name, description, status, start_date, created_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, ('test-mission-claro', 'TEST-CLARO', 'Test Mission CLARO', 'Mission for CLARO testing', 
                      'Planificación', '2024-08-01', 'test-user-123', datetime.now().isoformat()))
                
                conn.commit()
            
            logger.info("✓ Entorno de pruebas configurado correctamente")
            
        except Exception as e:
            logger.error(f"Error configurando entorno de pruebas: {e}")
            raise
    
    def validate_frontend_document_types(self):
        """
        Valida que los tipos de documentos en frontend usen IDs correctos
        FIX 1: CELLULAR_DATA y CALL_DATA en lugar de IDs en español
        """
        logger.info("\n=== VALIDANDO FIX 1: IDs de Tipos de Documento Frontend ===")
        
        try:
            # Leer el archivo OperatorDataUpload.tsx
            frontend_file = Path(__file__).parent.parent / 'Frontend' / 'components' / 'operator-data' / 'OperatorDataUpload.tsx'
            
            with open(frontend_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificar que CLARO tenga los IDs correctos
            has_cellular_data = "id: 'CELLULAR_DATA'" in content
            has_call_data = "id: 'CALL_DATA'" in content
            
            # Verificar que NO tenga IDs en español
            no_spanish_ids = "id: 'DATOS_CELULARES'" not in content and "id: 'DATOS_LLAMADAS'" not in content
            
            fix1_validated = has_cellular_data and has_call_data and no_spanish_ids
            
            self.test_results['frontend_fix_validation'] = {
                'fix_id': 'FIX-1-FRONTEND-DOCUMENT-TYPES',
                'description': 'Corrección de IDs de tipos de documento en frontend',
                'validated': fix1_validated,
                'details': {
                    'has_cellular_data_id': has_cellular_data,
                    'has_call_data_id': has_call_data,
                    'no_spanish_ids': no_spanish_ids
                }
            }
            
            if fix1_validated:
                logger.info("✓ FIX 1 VALIDADO: IDs de documentos correctos en frontend")
                self.test_results['test_summary']['critical_fixes_validated'].append('FIX-1-FRONTEND')
            else:
                logger.error("✗ FIX 1 FALLÓ: IDs de documentos incorrectos en frontend")
            
            self.test_results['test_summary']['total_tests'] += 1
            if fix1_validated:
                self.test_results['test_summary']['passed_tests'] += 1
            else:
                self.test_results['test_summary']['failed_tests'] += 1
                
        except Exception as e:
            logger.error(f"✗ Error validando frontend fix: {e}")
            self.test_results['frontend_fix_validation'] = {
                'validated': False,
                'error': str(e)
            }
            self.test_results['test_summary']['total_tests'] += 1
            self.test_results['test_summary']['failed_tests'] += 1
    
    def validate_backend_response_fields(self):
        """
        Valida que el backend retorne los campos correctos
        FIX 2: sheetId y processedRecords en lugar de file_upload_id y records_processed
        """
        logger.info("\n=== VALIDANDO FIX 2: Campos de Respuesta Backend ===")
        
        try:
            # Crear archivo CSV de prueba
            csv_data = self.claro_cellular_data
            csv_base64 = base64.b64encode(csv_data.encode('utf-8')).decode('utf-8')
            
            # Realizar upload usando la función real
            result = upload_operator_data(
                file_data=csv_base64,
                file_name='test_claro_cellular.csv',
                mission_id='test-mission-claro',
                operator='CLARO',
                file_type='CELLULAR_DATA',
                user_id='test-user-123'
            )
            
            # Validar estructura de respuesta
            has_success = 'success' in result
            has_sheet_id = 'sheetId' in result and result.get('sheetId') is not None
            has_processed_records = 'processedRecords' in result and isinstance(result.get('processedRecords'), int)
            has_warnings = 'warnings' in result and isinstance(result.get('warnings'), list)
            has_errors = 'errors' in result and isinstance(result.get('errors'), list)
            
            # Verificar que NO tenga los campos antiguos
            no_old_fields = 'file_upload_id' not in result and 'records_processed' not in result
            
            fix2_validated = (has_success and has_sheet_id and has_processed_records and 
                            has_warnings and has_errors and no_old_fields and result.get('success'))
            
            self.test_results['backend_fix_validation'] = {
                'fix_id': 'FIX-2-BACKEND-RESPONSE-FIELDS',
                'description': 'Corrección de nombres de campos en respuesta del backend',
                'validated': fix2_validated,
                'response_received': result,
                'details': {
                    'has_success': has_success,
                    'has_sheet_id': has_sheet_id,
                    'has_processed_records': has_processed_records,
                    'has_warnings': has_warnings,
                    'has_errors': has_errors,
                    'no_old_fields': no_old_fields,
                    'upload_successful': result.get('success', False),
                    'processed_count': result.get('processedRecords', 0)
                }
            }
            
            if fix2_validated:
                logger.info("✓ FIX 2 VALIDADO: Campos de respuesta correctos en backend")
                logger.info(f"  - sheetId: {result.get('sheetId')}")
                logger.info(f"  - processedRecords: {result.get('processedRecords')}")
                self.test_results['test_summary']['critical_fixes_validated'].append('FIX-2-BACKEND')
            else:
                logger.error("✗ FIX 2 FALLÓ: Campos de respuesta incorrectos en backend")
                logger.error(f"  - Respuesta recibida: {result}")
            
            self.test_results['test_summary']['total_tests'] += 1
            if fix2_validated:
                self.test_results['test_summary']['passed_tests'] += 1
            else:
                self.test_results['test_summary']['failed_tests'] += 1
                
        except Exception as e:
            logger.error(f"✗ Error validando backend fix: {e}")
            self.test_results['backend_fix_validation'] = {
                'validated': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            self.test_results['test_summary']['total_tests'] += 1
            self.test_results['test_summary']['failed_tests'] += 1
    
    def test_claro_cellular_data_integration(self):
        """Prueba completa de integración para CELLULAR_DATA de CLARO"""
        logger.info("\n=== PRUEBA INTEGRACIÓN: CLARO CELLULAR_DATA ===")
        
        try:
            csv_data = self.claro_cellular_data
            csv_base64 = base64.b64encode(csv_data.encode('utf-8')).decode('utf-8')
            
            result = upload_operator_data(
                file_data=csv_base64,
                file_name='claro_cellular_integration_test.csv',
                mission_id='test-mission-claro',
                operator='CLARO',
                file_type='CELLULAR_DATA',
                user_id='test-user-123'
            )
            
            # Validaciones específicas
            test_passed = (
                result.get('success') == True and
                result.get('processedRecords') == 3 and  # 3 registros en datos de prueba
                result.get('sheetId') is not None and
                isinstance(result.get('warnings'), list) and
                isinstance(result.get('errors'), list)
            )
            
            self.test_results['integration_tests']['claro_cellular_data'] = {
                'test_name': 'CLARO CELLULAR_DATA Integration',
                'passed': test_passed,
                'result': result,
                'expected_records': 3,
                'actual_records': result.get('processedRecords', 0)
            }
            
            if test_passed:
                logger.info("✓ CLARO CELLULAR_DATA integración exitosa")
                logger.info(f"  - Registros procesados: {result.get('processedRecords')}")
            else:
                logger.error("✗ CLARO CELLULAR_DATA integración falló")
            
            self.test_results['test_summary']['total_tests'] += 1
            if test_passed:
                self.test_results['test_summary']['passed_tests'] += 1
            else:
                self.test_results['test_summary']['failed_tests'] += 1
                
        except Exception as e:
            logger.error(f"✗ Error en prueba CELLULAR_DATA: {e}")
            self.test_results['integration_tests']['claro_cellular_data'] = {
                'passed': False,
                'error': str(e)
            }
            self.test_results['test_summary']['total_tests'] += 1
            self.test_results['test_summary']['failed_tests'] += 1
    
    def test_claro_call_data_integration(self):
        """Prueba completa de integración para CALL_DATA de CLARO"""
        logger.info("\n=== PRUEBA INTEGRACIÓN: CLARO CALL_DATA ===")
        
        try:
            csv_data = self.claro_call_data
            csv_base64 = base64.b64encode(csv_data.encode('utf-8')).decode('utf-8')
            
            result = upload_operator_data(
                file_data=csv_base64,
                file_name='claro_call_data_integration_test.csv',
                mission_id='test-mission-claro',
                operator='CLARO',
                file_type='CALL_DATA',
                user_id='test-user-123'
            )
            
            # Validaciones específicas
            test_passed = (
                result.get('success') == True and
                result.get('processedRecords') == 3 and  # 3 registros en datos de prueba
                result.get('sheetId') is not None and
                isinstance(result.get('warnings'), list) and
                isinstance(result.get('errors'), list)
            )
            
            self.test_results['integration_tests']['claro_call_data'] = {
                'test_name': 'CLARO CALL_DATA Integration',
                'passed': test_passed,
                'result': result,
                'expected_records': 3,
                'actual_records': result.get('processedRecords', 0)
            }
            
            if test_passed:
                logger.info("✓ CLARO CALL_DATA integración exitosa")
                logger.info(f"  - Registros procesados: {result.get('processedRecords')}")
            else:
                logger.error("✗ CLARO CALL_DATA integración falló")
            
            self.test_results['test_summary']['total_tests'] += 1
            if test_passed:
                self.test_results['test_summary']['passed_tests'] += 1
            else:
                self.test_results['test_summary']['failed_tests'] += 1
                
        except Exception as e:
            logger.error(f"✗ Error en prueba CALL_DATA: {e}")
            self.test_results['integration_tests']['claro_call_data'] = {
                'passed': False,
                'error': str(e)
            }
            self.test_results['test_summary']['total_tests'] += 1
            self.test_results['test_summary']['failed_tests'] += 1
    
    def test_regression_other_operators(self):
        """Pruebas de regresión para otros operadores"""
        logger.info("\n=== PRUEBAS DE REGRESIÓN: OTROS OPERADORES ===")
        
        # Datos de prueba para otros operadores
        movistar_data = """numero_que_navega,ruta_entrante,celda,trafico_de_subida,trafico_de_bajada,fecha_hora_inicio_sesion,duracion,tipo_tecnologia,departamento,localidad,latitud_n,longitud_w
573001234567,http://example.com,12345,1024,2048,2024-08-01 10:15:30,300,4G,BOGOTA,CHAPINERO,4.60971,-74.08175"""
        
        operators_to_test = [
            ('MOVISTAR', 'CELLULAR_DATA', movistar_data, 'movistar_test.csv'),
        ]
        
        regression_results = {}
        
        for operator, file_type, data, filename in operators_to_test:
            try:
                logger.info(f"Probando {operator} - {file_type}")
                
                csv_base64 = base64.b64encode(data.encode('utf-8')).decode('utf-8')
                
                result = upload_operator_data(
                    file_data=csv_base64,
                    file_name=filename,
                    mission_id='test-mission-claro',
                    operator=operator,
                    file_type=file_type,
                    user_id='test-user-123'
                )
                
                test_passed = (
                    result.get('success') == True and
                    result.get('sheetId') is not None and
                    'processedRecords' in result
                )
                
                regression_results[f"{operator}_{file_type}"] = {
                    'passed': test_passed,
                    'result': result
                }
                
                if test_passed:
                    logger.info(f"✓ {operator} {file_type} - OK")
                else:
                    logger.error(f"✗ {operator} {file_type} - FALLÓ")
                
                self.test_results['test_summary']['total_tests'] += 1
                if test_passed:
                    self.test_results['test_summary']['passed_tests'] += 1
                else:
                    self.test_results['test_summary']['failed_tests'] += 1
                    
            except Exception as e:
                logger.error(f"✗ Error probando {operator}: {e}")
                regression_results[f"{operator}_{file_type}"] = {
                    'passed': False,
                    'error': str(e)
                }
                self.test_results['test_summary']['total_tests'] += 1
                self.test_results['test_summary']['failed_tests'] += 1
        
        self.test_results['regression_tests'] = regression_results
    
    def generate_certification_report(self):
        """Genera el reporte de certificación final"""
        logger.info("\n=== GENERANDO REPORTE DE CERTIFICACIÓN ===")
        
        # Determinar estado de certificación
        total_tests = self.test_results['test_summary']['total_tests']
        passed_tests = self.test_results['test_summary']['passed_tests']
        critical_fixes = len(self.test_results['test_summary']['critical_fixes_validated'])
        
        if critical_fixes == 2 and passed_tests == total_tests:
            certification_status = 'CERTIFICADO'
            status_icon = '✅'
        elif critical_fixes == 2:
            certification_status = 'CERTIFICADO_CON_OBSERVACIONES'
            status_icon = '⚠️'
        else:
            certification_status = 'NO_CERTIFICADO'
            status_icon = '❌'
        
        self.test_results['certification_status'] = certification_status
        
        # Guardar reporte completo
        report_file = f'CLARO_FIX_VALIDATION_REPORT_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        # Imprimir resumen
        logger.info(f"\n{'='*60}")
        logger.info(f"{status_icon} CERTIFICACIÓN CLARO: {certification_status}")
        logger.info(f"{'='*60}")
        logger.info(f"Pruebas totales: {total_tests}")
        logger.info(f"Pruebas exitosas: {passed_tests}")
        logger.info(f"Pruebas fallidas: {total_tests - passed_tests}")
        logger.info(f"Correcciones críticas validadas: {critical_fixes}/2")
        logger.info(f"Reporte completo: {report_file}")
        
        if certification_status == 'CERTIFICADO':
            logger.info("\n🎉 AMBAS CORRECCIONES VALIDADAS EXITOSAMENTE")
            logger.info("✓ FIX 1: IDs de tipos de documento corregidos")
            logger.info("✓ FIX 2: Campos de respuesta backend corregidos")
            logger.info("✓ El problema reportado por el usuario está RESUELTO")
        
        return report_file
    
    def run_all_tests(self):
        """Ejecuta todas las pruebas de validación"""
        logger.info("INICIANDO VALIDACIÓN COMPLETA DE CORRECCIONES CLARO")
        logger.info("=" * 60)
        
        try:
            # Ejecutar todas las validaciones
            self.validate_frontend_document_types()
            self.validate_backend_response_fields()
            self.test_claro_cellular_data_integration()
            self.test_claro_call_data_integration()
            self.test_regression_other_operators()
            
            # Generar reporte final
            report_file = self.generate_certification_report()
            
            return report_file
            
        except Exception as e:
            logger.error(f"Error en ejecución de pruebas: {e}")
            logger.error(traceback.format_exc())
            return None

def main():
    """Función principal"""
    try:
        validator = ClaroFixValidator()
        report_file = validator.run_all_tests()
        
        if report_file:
            print(f"\nValidacion completada. Reporte generado: {report_file}")
            return 0
        else:
            print("\nError en validacion")
            return 1
            
    except Exception as e:
        print(f"Error critico: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())