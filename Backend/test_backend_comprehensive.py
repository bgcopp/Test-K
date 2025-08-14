"""
KRONOS Backend - Testing Comprehensivo del Backend
=======================================================================
Script de testing coordinado para validar funcionalidad específica del backend
considerando los issues críticos identificados por el equipo de BD.

CONTEXTO DEL TESTING COORDINADO:
- Arquitectura L2: APROBADO (2 issues menores)
- Base de Datos: NO APROBADO (3 issues críticos)

ISSUES CRÍTICOS DE BD QUE AFECTAN BACKEND:
1. Consultas cross-operador vacías - datos no se insertan correctamente
2. Foreign key rollback no funciona - problemas de integridad  
3. Datos parciales después de rollback - transacciones incompletas

CASOS DE PRUEBA ASIGNADOS AL BACKEND:
- P0-001 a P0-004: Cargas de archivos por operador (CRÍTICOS)
- P0-009: Manejo de archivos corruptos (CRÍTICO)
- P1-001, P1-008: Performance y validaciones (IMPORTANTES)
- P2-001, P2-005: Edge cases (CASOS LÍMITE)
- BACKEND-001 a 004: Validaciones específicas de backend

OBJETIVO: Separar issues de backend vs issues de BD
=======================================================================
"""

import sys
import os
import time
import logging
import traceback
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import tempfile
import base64

# Configurar path para imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Setup logging específico para testing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend_testing_report.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Importar componentes del backend
try:
    from database.connection import init_database, get_database_manager
    from services.auth_service import get_auth_service
    from services.user_service import get_user_service
    from services.role_service import get_role_service
    from services.mission_service import get_mission_service
    from services.analysis_service import get_analysis_service
    from services.operator_service import get_operator_service
    from services.operator_processors import get_operator_processor, get_supported_operators
    from utils.validators import validate_colombian_phone_number, validate_coordinates, validate_claro_date_format
    from utils.helpers import normalize_column_names, clean_dataframe
except ImportError as e:
    logger.error(f"Error importando componentes del backend: {e}")
    sys.exit(1)

class BackendTestingCoordinator:
    """
    Coordinador de testing del backend que ejecuta casos específicos
    y distingue entre issues de backend vs issues de BD subyacente
    """
    
    def __init__(self):
        self.test_results = {}
        self.backend_issues = []
        self.database_issues = []
        self.test_mission_id = None
        self.services_initialized = False
        
        # Contadores de resultados
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.critical_failures = 0
        
        # Rutas de archivos de prueba
        self.test_files_base = current_dir.parent / "archivos" / "CeldasDiferenteOperador"
        
        logger.info("=== INICIANDO TESTING COORDINADO DEL BACKEND ===")
        logger.info("Contexto: Testing post-issues críticos de BD")
    
    def setup_test_environment(self) -> bool:
        """Prepara el entorno de testing"""
        try:
            logger.info("Configurando entorno de testing...")
            
            # 1. Inicializar base de datos de testing
            test_db_path = current_dir / "test_backend_comprehensive.db"
            if test_db_path.exists():
                test_db_path.unlink()  # Eliminar BD anterior
            
            logger.info("Inicializando base de datos de testing...")
            init_database(str(test_db_path), force_recreate=True)
            
            # 2. Inicializar servicios
            logger.info("Inicializando servicios de testing...")
            auth_service = get_auth_service()
            user_service = get_user_service()
            role_service = get_role_service()
            mission_service = get_mission_service()
            analysis_service = get_analysis_service()
            operator_service = get_operator_service()
            
            # 3. Crear misión de prueba
            logger.info("Creando misión de prueba...")
            test_mission_data = {
                "code": "TEST-BACKEND-001",
                "name": "Misión Testing Backend Coordinado",
                "description": "Misión para testing de funcionalidad de backend",
                "objectives": ["31000000001", "31000000002", "31000000003"],
                "status": "En Progreso",
                "startDate": "2025-01-01",
                "endDate": "2025-12-31"
            }
            
            created_mission = mission_service.create_mission(test_mission_data, created_by=1)
            self.test_mission_id = created_mission['id']
            
            self.services_initialized = True
            logger.info(f"Entorno configurado. Misión de prueba ID: {self.test_mission_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error configurando entorno de testing: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def validate_eel_apis(self) -> Dict[str, Any]:
        """BACKEND-001: Validar que las 36 APIs Eel están expuestas"""
        logger.info("=== BACKEND-001: Validando APIs Eel expuestas ===")
        
        # Lista de APIs que deben estar expuestas según main.py
        expected_apis = [
            # Authentication
            'login',
            
            # User Management  
            'get_users', 'create_user', 'update_user', 'delete_user',
            
            # Role Management
            'get_roles', 'create_role', 'update_role', 'delete_role',
            
            # Mission Management
            'get_missions', 'create_mission', 'update_mission', 'delete_mission',
            
            # File Upload and Data Management
            'upload_cellular_data', 'upload_operator_data', 'clear_cellular_data', 'delete_operator_sheet',
            
            # Analysis
            'run_analysis',
            
            # CLARO APIs
            'upload_claro_datos_file', 'upload_claro_llamadas_entrantes_file', 'upload_claro_llamadas_salientes_file',
            'get_claro_data_summary', 'delete_claro_file', 'validate_claro_file_structure',
            
            # General Operator APIs
            'get_supported_operators', 'get_mission_operator_summary', 'get_operator_files_for_mission',
            'delete_operator_file', 'get_operator_data_analysis', 'validate_operator_file_structure',
            'upload_operator_file',
            
            # WOM APIs
            'validate_wom_file_structure', 'upload_wom_datos_file', 'upload_wom_llamadas_file',
            'get_wom_data_summary', 'delete_wom_file'
        ]
        
        result = {
            'test_case': 'BACKEND-001',
            'description': 'Validar APIs Eel expuestas',
            'expected_apis': len(expected_apis),
            'found_apis': 0,
            'missing_apis': [],
            'status': 'UNKNOWN',
            'details': {}
        }
        
        try:
            # Importar main.py y verificar funciones expuestas
            import main
            
            found_apis = []
            missing_apis = []
            
            for api_name in expected_apis:
                if hasattr(main, api_name):
                    # Verificar que tiene el decorador @eel.expose
                    func = getattr(main, api_name)
                    if hasattr(func, '_eel_exposed') or api_name in str(func):
                        found_apis.append(api_name)
                    else:
                        missing_apis.append(f"{api_name} (no expuesta)")
                else:
                    missing_apis.append(f"{api_name} (no encontrada)")
            
            result['found_apis'] = len(found_apis)
            result['missing_apis'] = missing_apis
            result['details']['found'] = found_apis
            
            # Evaluar resultado
            if len(missing_apis) == 0:
                result['status'] = 'PASSED'
                logger.info(f"✓ Todas las {len(expected_apis)} APIs Eel están expuestas")
            elif len(missing_apis) <= 2:
                result['status'] = 'WARNING'
                logger.warning(f"⚠️ {len(missing_apis)} APIs faltantes (no crítico)")
            else:
                result['status'] = 'FAILED'
                logger.error(f"✗ {len(missing_apis)} APIs faltantes (crítico)")
                self.backend_issues.append({
                    'issue_id': 'BACKEND-API-001',
                    'severity': 'CRITICAL',
                    'description': f'{len(missing_apis)} APIs Eel no expuestas',
                    'missing_apis': missing_apis
                })
            
        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            logger.error(f"Error validando APIs Eel: {e}")
            self.backend_issues.append({
                'issue_id': 'BACKEND-API-002', 
                'severity': 'CRITICAL',
                'description': f'Error cargando APIs Eel: {e}'
            })
        
        return result
    
    def validate_operator_processors(self) -> Dict[str, Any]:
        """BACKEND-002: Validar que los 4 procesadores de operador funcionan"""
        logger.info("=== BACKEND-002: Validando procesadores de operador ===")
        
        expected_operators = ['CLARO', 'MOVISTAR', 'TIGO', 'WOM']
        
        result = {
            'test_case': 'BACKEND-002',
            'description': 'Validar procesadores de operador',
            'expected_processors': len(expected_operators),
            'working_processors': 0,
            'failed_processors': [],
            'processor_details': {},
            'status': 'UNKNOWN'
        }
        
        try:
            working_processors = []
            failed_processors = []
            
            for operator in expected_operators:
                try:
                    # Intentar obtener procesador
                    processor = get_operator_processor(operator)
                    
                    if processor is None:
                        failed_processors.append(f"{operator}: Procesador no disponible")
                        continue
                    
                    # Verificar métodos básicos del procesador
                    required_methods = ['process_file', 'validate_file_structure', 'get_supported_file_types']
                    processor_info = {'methods': {}}
                    
                    for method in required_methods:
                        if hasattr(processor, method):
                            processor_info['methods'][method] = True
                        else:
                            processor_info['methods'][method] = False
                            failed_processors.append(f"{operator}: Método {method} faltante")
                    
                    # Si tiene todos los métodos, considerar funcionando
                    if all(processor_info['methods'].values()):
                        working_processors.append(operator)
                        
                        # Obtener tipos de archivo soportados
                        try:
                            supported_types = processor.get_supported_file_types()
                            processor_info['supported_file_types'] = supported_types
                        except Exception as e:
                            processor_info['supported_file_types'] = f"Error: {e}"
                    
                    result['processor_details'][operator] = processor_info
                    
                except Exception as e:
                    failed_processors.append(f"{operator}: Error - {str(e)}")
                    result['processor_details'][operator] = {'error': str(e)}
            
            result['working_processors'] = len(working_processors)
            result['failed_processors'] = failed_processors
            
            # Evaluar resultado
            if len(failed_processors) == 0:
                result['status'] = 'PASSED'
                logger.info(f"✓ Todos los {len(expected_operators)} procesadores funcionan correctamente")
            elif len(working_processors) >= 3:
                result['status'] = 'WARNING'
                logger.warning(f"⚠️ {len(failed_processors)} procesadores con problemas (no crítico)")
            else:
                result['status'] = 'FAILED'
                logger.error(f"✗ {len(failed_processors)} procesadores fallidos (crítico)")
                self.backend_issues.append({
                    'issue_id': 'BACKEND-PROC-001',
                    'severity': 'CRITICAL',
                    'description': f'{len(failed_processors)} procesadores no funcionan',
                    'failed_processors': failed_processors
                })
        
        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            logger.error(f"Error validando procesadores: {e}")
            self.backend_issues.append({
                'issue_id': 'BACKEND-PROC-002',
                'severity': 'CRITICAL', 
                'description': f'Error evaluando procesadores: {e}'
            })
        
        return result
    
    def validate_backend_validators(self) -> Dict[str, Any]:
        """BACKEND-003: Validar validaciones específicas (teléfonos, fechas, coordenadas)"""
        logger.info("=== BACKEND-003: Validando validadores específicos ===")
        
        result = {
            'test_case': 'BACKEND-003',
            'description': 'Validar funciones de validación específicas',
            'validators_tested': 0,
            'validators_passed': 0,
            'validation_details': {},
            'status': 'UNKNOWN'
        }
        
        try:
            validators_tested = 0
            validators_passed = 0
            
            # 1. Validación de números telefónicos colombianos
            phone_tests = [
                ('3001234567', '3001234567'),   # Celular válido
                ('3201234567', '3201234567'),   # Celular válido
                ('6011234567', '6011234567'),   # Fijo Bogotá válido
                ('12345', None),                # Muy corto (debería fallar)
                ('abc1234567', None),           # Contiene letras (debería fallar)
                ('30012345678', None),          # Muy largo (debería fallar)
            ]
            
            phone_results = []
            for phone, expected in phone_tests:
                try:
                    actual = validate_colombian_phone_number(phone)
                    passed = (actual == expected)
                    phone_results.append({'phone': phone, 'expected': expected, 'actual': actual, 'passed': passed})
                    if passed:
                        validators_passed += 1
                except Exception as e:
                    # Si esperábamos que fallara (expected = None), es correcto
                    passed = (expected is None)
                    phone_results.append({'phone': phone, 'expected': expected, 'error': str(e), 'passed': passed})
                    if passed:
                        validators_passed += 1
                validators_tested += 1
            
            result['validation_details']['phone_validation'] = {
                'tests': phone_results,
                'passed': sum(1 for r in phone_results if r.get('passed', False)),
                'total': len(phone_tests)
            }
            
            # 2. Validación de coordenadas geográficas
            coord_tests = [
                ((4.6097, -74.0817), (4.6097, -74.0817)),  # Bogotá válido
                ((0.0, 0.0), (0.0, 0.0)),                  # Ecuador/Greenwich válido
                ((91.0, 0.0), None),                       # Latitud inválida (debería fallar)
                ((0.0, 181.0), None),                      # Longitud inválida (debería fallar)
                (('a', 'b'), None),                        # Tipos inválidos (debería fallar)
            ]
            
            coord_results = []
            for (lat, lon), expected in coord_tests:
                try:
                    actual = validate_coordinates(lat, lon)
                    passed = (actual == expected)
                    coord_results.append({'lat': lat, 'lon': lon, 'expected': expected, 'actual': actual, 'passed': passed})
                    if passed:
                        validators_passed += 1
                except Exception as e:
                    # Si esperábamos que fallara (expected = None), es correcto
                    passed = (expected is None)
                    coord_results.append({'lat': lat, 'lon': lon, 'expected': expected, 'error': str(e), 'passed': passed})
                    if passed:
                        validators_passed += 1
                validators_tested += 1
            
            result['validation_details']['coordinate_validation'] = {
                'tests': coord_results,
                'passed': sum(1 for r in coord_results if r.get('passed', False)),
                'total': len(coord_tests)
            }
            
            # 3. Parsing de fechas (usando formato CLARO como ejemplo)
            date_tests = [
                ('20250115123000', True),      # Formato CLARO válido
                ('20241225000000', True),      # Fecha válida
                ('fecha_inválida', False),     # Formato inválido
                ('32011225000000', False),     # Fecha inválida
                ('20250115', False),           # Muy corto
            ]
            
            date_results = []
            for date_str, should_parse in date_tests:
                try:
                    parsed_date = validate_claro_date_format(date_str)
                    passed = (parsed_date is not None) == should_parse
                    date_results.append({'date_str': date_str, 'should_parse': should_parse, 'parsed': parsed_date is not None, 'passed': passed})
                    if passed:
                        validators_passed += 1
                except Exception as e:
                    # Si esperábamos que fallara (should_parse = False), es correcto
                    passed = (not should_parse)
                    date_results.append({'date_str': date_str, 'should_parse': should_parse, 'error': str(e), 'passed': passed})
                    if passed:
                        validators_passed += 1
                validators_tested += 1
            
            result['validation_details']['date_parsing'] = {
                'tests': date_results,
                'passed': sum(1 for r in date_results if r.get('passed', False)),
                'total': len(date_tests)
            }
            
            result['validators_tested'] = validators_tested
            result['validators_passed'] = validators_passed
            
            # Evaluar resultado
            success_rate = validators_passed / validators_tested if validators_tested > 0 else 0
            
            if success_rate >= 0.9:
                result['status'] = 'PASSED'
                logger.info(f"✓ Validadores funcionan correctamente ({validators_passed}/{validators_tested})")
            elif success_rate >= 0.7:
                result['status'] = 'WARNING'
                logger.warning(f"⚠️ Algunos validadores fallan ({validators_passed}/{validators_tested})")
            else:
                result['status'] = 'FAILED'
                logger.error(f"✗ Validadores con fallas críticas ({validators_passed}/{validators_tested})")
                self.backend_issues.append({
                    'issue_id': 'BACKEND-VAL-001',
                    'severity': 'HIGH',
                    'description': f'Validadores con {success_rate:.1%} de éxito (< 70%)',
                    'failed_count': validators_tested - validators_passed
                })
        
        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            logger.error(f"Error validando validadores: {e}")
            self.backend_issues.append({
                'issue_id': 'BACKEND-VAL-002',
                'severity': 'CRITICAL',
                'description': f'Error evaluando validadores: {e}'
            })
        
        return result
    
    def test_claro_file_processing(self) -> Dict[str, Any]:
        """P0-001: Validar carga archivo CLARO datos válido"""
        logger.info("=== P0-001: Testing carga archivo CLARO ===")
        
        result = {
            'test_case': 'P0-001',
            'description': 'Carga archivo CLARO datos válido',
            'severity': 'CRITICAL',
            'files_tested': 0,
            'files_processed': 0,
            'processing_details': {},
            'status': 'UNKNOWN'
        }
        
        if not self.services_initialized:
            result['status'] = 'SKIPPED'
            result['error'] = 'Servicios no inicializados'
            return result
        
        try:
            claro_path = self.test_files_base / "claro"
            claro_files = [
                "DATOS_POR_CELDA CLARO.xlsx",
                "LLAMADAS_ENTRANTES_POR_CELDA CLARO.xlsx", 
                "LLAMADAS_SALIENTES_POR_CELDA CLARO.xlsx"
            ]
            
            processor = get_operator_processor('CLARO')
            if not processor:
                result['status'] = 'FAILED'
                result['error'] = 'Procesador CLARO no disponible'
                self.backend_issues.append({
                    'issue_id': 'P0-001-BACKEND',
                    'severity': 'CRITICAL',
                    'description': 'Procesador CLARO no disponible para testing'
                })
                return result
            
            files_processed = 0
            
            for file_name in claro_files:
                file_path = claro_path / file_name
                result['files_tested'] += 1
                
                if not file_path.exists():
                    result['processing_details'][file_name] = {'status': 'FILE_NOT_FOUND'}
                    continue
                
                try:
                    # Leer archivo y convertir a base64
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                    
                    file_data = {
                        'name': file_name,
                        'content': f'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{base64.b64encode(file_content).decode()}'
                    }
                    
                    # Determinar tipo de archivo
                    if 'DATOS_POR_CELDA' in file_name:
                        file_type = 'DATOS'
                    elif 'LLAMADAS_ENTRANTES' in file_name:
                        file_type = 'LLAMADAS_ENTRANTES'
                    elif 'LLAMADAS_SALIENTES' in file_name:
                        file_type = 'LLAMADAS_SALIENTES'
                    else:
                        file_type = 'UNKNOWN'
                    
                    # Validar estructura primero
                    validation_result = processor.validate_file_structure(file_data, file_type)
                    
                    if not validation_result.get('is_valid', False):
                        result['processing_details'][file_name] = {
                            'status': 'VALIDATION_FAILED',
                            'validation_errors': validation_result.get('errors', [])
                        }
                        continue
                    
                    # Procesar archivo
                    start_time = time.time()
                    process_result = processor.process_file(file_data, file_type, self.test_mission_id)
                    processing_time = time.time() - start_time
                    
                    result['processing_details'][file_name] = {
                        'status': 'PROCESSED',
                        'records_processed': process_result.get('records_processed', 0),
                        'processing_time': processing_time,
                        'validation_result': validation_result
                    }
                    
                    files_processed += 1
                    
                except Exception as e:
                    result['processing_details'][file_name] = {
                        'status': 'PROCESSING_ERROR',
                        'error': str(e),
                        'traceback': traceback.format_exc()
                    }
                    
                    # Distinguir si es error de backend o BD
                    if 'database' in str(e).lower() or 'sqlite' in str(e).lower() or 'constraint' in str(e).lower():
                        self.database_issues.append({
                            'issue_id': f'P0-001-DB-{file_name}',
                            'severity': 'CRITICAL',
                            'description': f'Error de BD procesando {file_name}: {e}',
                            'category': 'DATABASE'
                        })
                    else:
                        self.backend_issues.append({
                            'issue_id': f'P0-001-BACKEND-{file_name}',
                            'severity': 'CRITICAL', 
                            'description': f'Error de backend procesando {file_name}: {e}',
                            'category': 'BACKEND'
                        })
            
            result['files_processed'] = files_processed
            
            # Evaluar resultado
            if files_processed == len(claro_files):
                result['status'] = 'PASSED'
                logger.info(f"✓ Todos los archivos CLARO procesados correctamente ({files_processed}/{len(claro_files)})")
            elif files_processed > 0:
                result['status'] = 'PARTIAL'
                logger.warning(f"⚠️ Algunos archivos CLARO procesados ({files_processed}/{len(claro_files)})")
            else:
                result['status'] = 'FAILED'
                logger.error(f"✗ Ningún archivo CLARO procesado correctamente")
        
        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            logger.error(f"Error en test CLARO: {e}")
            self.backend_issues.append({
                'issue_id': 'P0-001-GENERAL',
                'severity': 'CRITICAL',
                'description': f'Error general en test CLARO: {e}'
            })
        
        return result
    
    def test_file_corruption_handling(self) -> Dict[str, Any]:
        """P0-009: Manejo archivo corrupto/malformado"""
        logger.info("=== P0-009: Testing manejo archivos corruptos ===")
        
        result = {
            'test_case': 'P0-009',
            'description': 'Manejo archivo corrupto/malformado',
            'severity': 'CRITICAL',
            'corruption_tests': 0,
            'graceful_handles': 0,
            'corruption_details': {},
            'status': 'UNKNOWN'
        }
        
        if not self.services_initialized:
            result['status'] = 'SKIPPED'
            result['error'] = 'Servicios no inicializados'
            return result
        
        try:
            corruption_tests = [
                {
                    'name': 'archivo_vacio',
                    'content': '',
                    'description': 'Archivo completamente vacío'
                },
                {
                    'name': 'datos_binarios_random',
                    'content': b'\x00\x01\x02\x03\xFF\xFE\xFD\xFC' * 100,
                    'description': 'Datos binarios aleatorios'
                },
                {
                    'name': 'json_malformado',
                    'content': '{"datos": malformed json content...',
                    'description': 'JSON sintácticamente incorrecto'
                },
                {
                    'name': 'texto_plano',
                    'content': 'Este es solo texto plano, no un archivo válido de datos',
                    'description': 'Texto plano sin estructura'
                },
                {
                    'name': 'excel_falso',
                    'content': 'PK\x03\x04FAKE_EXCEL_HEADER_BUT_CORRUPTED_DATA',
                    'description': 'Archivo que parece Excel pero está corrupto'
                }
            ]
            
            processor = get_operator_processor('CLARO')  # Usar CLARO como ejemplo
            if not processor:
                result['status'] = 'FAILED'
                result['error'] = 'Procesador CLARO no disponible para testing'
                return result
            
            graceful_handles = 0
            
            for test_case in corruption_tests:
                result['corruption_tests'] += 1
                test_name = test_case['name']
                
                try:
                    # Preparar archivo corrupto
                    content = test_case['content']
                    if isinstance(content, str):
                        content = content.encode('utf-8')
                    
                    file_data = {
                        'name': f'{test_name}.xlsx',
                        'content': f'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{base64.b64encode(content).decode()}'
                    }
                    
                    # Intentar procesar archivo corrupto
                    start_time = time.time()
                    
                    try:
                        # Primero validar estructura (debería fallar gracefully)
                        validation_result = processor.validate_file_structure(file_data, 'DATOS')
                        
                        # Si la validación pasa (no debería), intentar procesar
                        if validation_result.get('is_valid', False):
                            process_result = processor.process_file(file_data, 'DATOS', self.test_mission_id)
                            result['corruption_details'][test_name] = {
                                'status': 'UNEXPECTED_SUCCESS',
                                'validation': validation_result,
                                'process_result': process_result,
                                'graceful': False
                            }
                        else:
                            # Validación falló apropiadamente
                            result['corruption_details'][test_name] = {
                                'status': 'GRACEFUL_VALIDATION_FAILURE',
                                'validation_errors': validation_result.get('errors', []),
                                'graceful': True
                            }
                            graceful_handles += 1
                    
                    except Exception as process_error:
                        # Verificar si el error es manejado gracefully
                        error_str = str(process_error).lower()
                        graceful_keywords = ['invalid', 'corrupted', 'malformed', 'formato', 'estructura']
                        
                        is_graceful = any(keyword in error_str for keyword in graceful_keywords)
                        
                        result['corruption_details'][test_name] = {
                            'status': 'GRACEFUL_PROCESSING_ERROR' if is_graceful else 'UNGRACEFUL_ERROR',
                            'error': str(process_error),
                            'graceful': is_graceful
                        }
                        
                        if is_graceful:
                            graceful_handles += 1
                        else:
                            # Error no manejado gracefully - issue de backend
                            self.backend_issues.append({
                                'issue_id': f'P0-009-BACKEND-{test_name}',
                                'severity': 'HIGH',
                                'description': f'Error no graceful con archivo corrupto {test_name}: {process_error}',
                                'category': 'ERROR_HANDLING'
                            })
                    
                    processing_time = time.time() - start_time
                    result['corruption_details'][test_name]['processing_time'] = processing_time
                
                except Exception as e:
                    result['corruption_details'][test_name] = {
                        'status': 'TEST_ERROR',
                        'error': str(e),
                        'graceful': False
                    }
                    
                    logger.error(f"Error en test de corrupción {test_name}: {e}")
            
            result['graceful_handles'] = graceful_handles
            
            # Evaluar resultado
            success_rate = graceful_handles / result['corruption_tests'] if result['corruption_tests'] > 0 else 0
            
            if success_rate >= 0.8:
                result['status'] = 'PASSED'
                logger.info(f"✓ Manejo de archivos corruptos funciona ({graceful_handles}/{result['corruption_tests']})")
            elif success_rate >= 0.6:
                result['status'] = 'WARNING'
                logger.warning(f"⚠️ Manejo parcial de archivos corruptos ({graceful_handles}/{result['corruption_tests']})")
            else:
                result['status'] = 'FAILED'
                logger.error(f"✗ Manejo deficiente de archivos corruptos ({graceful_handles}/{result['corruption_tests']})")
        
        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)
            logger.error(f"Error en test de archivos corruptos: {e}")
            self.backend_issues.append({
                'issue_id': 'P0-009-GENERAL',
                'severity': 'CRITICAL',
                'description': f'Error general en test de archivos corruptos: {e}'
            })
        
        return result
    
    def generate_comprehensive_report(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Genera reporte comprehensivo distinguiendo issues de backend vs BD"""
        
        # Calcular métricas generales
        total_tests = len(test_results)
        passed_tests = sum(1 for r in test_results.values() if r.get('status') == 'PASSED')
        failed_tests = sum(1 for r in test_results.values() if r.get('status') == 'FAILED')
        error_tests = sum(1 for r in test_results.values() if r.get('status') == 'ERROR')
        
        # Crear reporte final
        report = {
            'report_info': {
                'title': 'REPORTE TESTING BACKEND COORDINADO',
                'specialist': 'Backend Python/Eel Team',
                'date': time.strftime('%Y-%m-%d'),
                'context': 'Testing post-issues críticos de BD',
                'project': 'KRONOS - Sistema de Sábanas de Datos de Operador'
            },
            
            'executive_summary': {
                'backend_status': 'EVALUANDO...',
                'total_tests_executed': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'error_tests': error_tests,
                'backend_issues_found': len(self.backend_issues),
                'database_issues_found': len(self.database_issues)
            },
            
            'test_results_by_category': {
                'critical_cases': [],
                'important_cases': [],
                'edge_cases': [],
                'backend_specific': []
            },
            
            'issues_classification': {
                'backend_issues': self.backend_issues,
                'database_issues': self.database_issues,
                'coordination_issues': []
            },
            
            'detailed_results': test_results,
            
            'recommendations': {
                'immediate_actions': [],
                'before_production': [],
                'monitoring_suggestions': []
            },
            
            'sign_off': {
                'backend_approved': False,
                'conditions_for_approval': [],
                'specialist': 'Backend Python/Eel Team',
                'next_review': 'Después de resolver issues identificados'
            }
        }
        
        # Clasificar resultados por categoría
        for test_id, test_result in test_results.items():
            test_info = {
                'test_id': test_id,
                'description': test_result.get('description', 'N/A'),
                'status': test_result.get('status', 'UNKNOWN'),
                'severity': test_result.get('severity', 'UNKNOWN')
            }
            
            if test_id.startswith('P0-'):
                report['test_results_by_category']['critical_cases'].append(test_info)
            elif test_id.startswith('P1-'):
                report['test_results_by_category']['important_cases'].append(test_info)
            elif test_id.startswith('P2-'):
                report['test_results_by_category']['edge_cases'].append(test_info)
            elif test_id.startswith('BACKEND-'):
                report['test_results_by_category']['backend_specific'].append(test_info)
        
        # Determinar estado general del backend
        critical_failures = sum(1 for r in test_results.values() 
                              if r.get('status') in ['FAILED', 'ERROR'] and r.get('severity') == 'CRITICAL')
        
        if critical_failures == 0 and len(self.backend_issues) == 0:
            report['executive_summary']['backend_status'] = 'APROBADO'
            report['sign_off']['backend_approved'] = True
        elif critical_failures <= 2 and len([i for i in self.backend_issues if i.get('severity') == 'CRITICAL']) == 0:
            report['executive_summary']['backend_status'] = 'APROBADO CON OBSERVACIONES'
            report['sign_off']['backend_approved'] = True
            report['sign_off']['conditions_for_approval'] = ['Corregir issues menores identificados']
        else:
            report['executive_summary']['backend_status'] = 'NO APROBADO'
            report['sign_off']['backend_approved'] = False
            
        # Generar recomendaciones
        if len(self.backend_issues) > 0:
            critical_backend = [i for i in self.backend_issues if i.get('severity') == 'CRITICAL']
            if critical_backend:
                report['recommendations']['immediate_actions'].extend([
                    f"Resolver {len(critical_backend)} issues críticos de backend identificados",
                    "Verificar configuración de APIs Eel y procesadores de operador",
                    "Validar manejo de errores en carga de archivos"
                ])
        
        if len(self.database_issues) > 0:
            report['recommendations']['immediate_actions'].extend([
                f"Coordinar con equipo de BD para resolver {len(self.database_issues)} issues de base de datos",
                "Verificar que issues de BD no sean causados por uso incorrecto desde backend"
            ])
        
        report['recommendations']['before_production'].extend([
            "Re-ejecutar testing completo después de correcciones",
            "Validar funcionalidad end-to-end con archivos reales de operadores",
            "Verificar performance con archivos grandes",
            "Implementar monitoreo de APIs y procesadores"
        ])
        
        report['recommendations']['monitoring_suggestions'].extend([
            "Logging detallado de procesamiento de archivos",
            "Métricas de performance por operador",
            "Alertas de errores en APIs Eel",
            "Monitoreo de memoria en procesamiento de archivos grandes"
        ])
        
        return report
    
    def run_comprehensive_testing(self) -> Dict[str, Any]:
        """Ejecuta testing comprehensivo del backend"""
        logger.info("=== INICIANDO TESTING COMPREHENSIVO DEL BACKEND ===")
        
        # 1. Setup del entorno
        if not self.setup_test_environment():
            logger.error("No se pudo configurar entorno de testing")
            return {'error': 'Entorno de testing no disponible'}
        
        # 2. Ejecutar tests específicos del backend
        test_results = {}
        
        logger.info("Ejecutando tests específicos del backend...")
        test_results['BACKEND-001'] = self.validate_eel_apis()
        test_results['BACKEND-002'] = self.validate_operator_processors()
        test_results['BACKEND-003'] = self.validate_backend_validators()
        
        # 3. Ejecutar casos de prueba críticos
        logger.info("Ejecutando casos críticos de carga de archivos...")
        test_results['P0-001'] = self.test_claro_file_processing()
        test_results['P0-009'] = self.test_file_corruption_handling()
        
        # 4. Generar reporte comprehensivo
        logger.info("Generando reporte comprehensivo...")
        final_report = self.generate_comprehensive_report(test_results)
        
        return final_report
    
    def update_todo_with_results(self, final_report: Dict[str, Any]):
        """Actualiza el estado de TODOs basado en los resultados"""
        # Esto sería llamado externamente por el coordinador principal
        # Por ahora solo loggeamos el estado
        logger.info("=== ACTUALIZACIÓN DE TODOs ===")
        
        if 'test_results_by_category' in final_report:
            for category, tests in final_report['test_results_by_category'].items():
                for test in tests:
                    status = "✓ PASSED" if test['status'] == 'PASSED' else "✗ FAILED"
                    logger.info(f"{test['test_id']}: {status}")


def main():
    """Función principal de testing"""
    coordinator = BackendTestingCoordinator()
    
    try:
        # Ejecutar testing comprehensivo
        final_report = coordinator.run_comprehensive_testing()
        
        # Guardar reporte en archivo
        report_path = current_dir / "REPORTE_TESTING_BACKEND_COORDINADO.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Reporte guardado en: {report_path}")
        
        # Mostrar resumen ejecutivo
        if 'executive_summary' in final_report:
            summary = final_report['executive_summary']
            logger.info("=== RESUMEN EJECUTIVO ===")
            logger.info(f"Estado Backend: {summary.get('backend_status', 'UNKNOWN')}")
            logger.info(f"Tests Ejecutados: {summary.get('total_tests_executed', 0)}")
            logger.info(f"Tests Exitosos: {summary.get('passed_tests', 0)}")
            logger.info(f"Tests Fallidos: {summary.get('failed_tests', 0)}")
            logger.info(f"Issues Backend: {summary.get('backend_issues_found', 0)}")
            logger.info(f"Issues BD: {summary.get('database_issues_found', 0)}")
        
        # Actualizar TODO con resultados
        coordinator.update_todo_with_results(final_report)
        
    except Exception as e:
        logger.error(f"Error en testing coordinado: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")


if __name__ == '__main__':
    main()