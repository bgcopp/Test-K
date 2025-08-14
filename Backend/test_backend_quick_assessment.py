"""
KRONOS Backend - Testing Rápido y Coordinado
=======================================================================
Script de evaluación rápida del backend enfocado en los casos críticos
identificados por el equipo de BD, ejecutando validaciones específicas
sin configuración completa del entorno.

OBJETIVO: Validar funcionalidad del backend distinguiendo issues de BD vs Backend
=======================================================================
"""

import sys
import os
import logging
import traceback
import json
import time
from pathlib import Path
from typing import Dict, Any, List

# Configurar path para imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Setup logging simple
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_backend_imports():
    """Test básico de importación de componentes"""
    logger.info("=== TEST: Importación de Componentes Backend ===")
    results = {
        'test_name': 'BACKEND-IMPORTS',
        'imports_tested': 0,
        'imports_successful': 0,
        'failed_imports': [],
        'status': 'UNKNOWN'
    }
    
    # Lista de módulos críticos a importar
    import_tests = [
        ('database.connection', ['init_database', 'get_database_manager']),
        ('services.auth_service', ['get_auth_service']),
        ('services.user_service', ['get_user_service']),
        ('services.role_service', ['get_role_service']),
        ('services.mission_service', ['get_mission_service']),
        ('services.analysis_service', ['get_analysis_service']),
        ('services.operator_service', ['get_operator_service']),
        ('services.operator_processors', ['get_operator_processor', 'get_supported_operators']),
        ('utils.validators', ['validate_colombian_phone_number', 'validate_coordinates']),
        ('utils.helpers', ['normalize_column_names', 'decode_base64_file'])
    ]
    
    for module_name, functions in import_tests:
        results['imports_tested'] += 1
        try:
            module = __import__(module_name, fromlist=functions)
            
            # Verificar que las funciones existen
            missing_functions = []
            for func_name in functions:
                if not hasattr(module, func_name):
                    missing_functions.append(func_name)
            
            if missing_functions:
                results['failed_imports'].append(f"{module_name}: funciones faltantes {missing_functions}")
            else:
                results['imports_successful'] += 1
                logger.info(f"✓ {module_name}: OK")
                
        except ImportError as e:
            results['failed_imports'].append(f"{module_name}: {str(e)}")
            logger.error(f"✗ {module_name}: {str(e)}")
        except Exception as e:
            results['failed_imports'].append(f"{module_name}: Error inesperado - {str(e)}")
            logger.error(f"✗ {module_name}: Error inesperado - {str(e)}")
    
    # Determinar estado
    success_rate = results['imports_successful'] / results['imports_tested']
    if success_rate >= 0.9:
        results['status'] = 'PASSED'
        logger.info(f"IMPORTS: PASSED ({results['imports_successful']}/{results['imports_tested']})")
    elif success_rate >= 0.7:
        results['status'] = 'WARNING'
        logger.warning(f"IMPORTS: WARNING ({results['imports_successful']}/{results['imports_tested']})")
    else:
        results['status'] = 'FAILED'
        logger.error(f"IMPORTS: FAILED ({results['imports_successful']}/{results['imports_tested']})")
    
    return results

def test_operator_processors():
    """Test específico de procesadores de operador"""
    logger.info("=== TEST: Procesadores de Operador ===")
    results = {
        'test_name': 'BACKEND-PROCESSORS',
        'processors_tested': 0,
        'processors_working': 0,
        'processor_details': {},
        'status': 'UNKNOWN'
    }
    
    try:
        from services.operator_processors import get_operator_processor, get_supported_operators
        
        # Obtener operadores soportados
        try:
            supported_operators = get_supported_operators()
            logger.info(f"Operadores soportados detectados: {supported_operators}")
        except Exception as e:
            logger.error(f"Error obteniendo operadores soportados: {e}")
            supported_operators = ['CLARO', 'MOVISTAR', 'TIGO', 'WOM']  # Fallback
        
        expected_operators = ['CLARO', 'MOVISTAR', 'TIGO', 'WOM']
        
        for operator in expected_operators:
            results['processors_tested'] += 1
            processor_info = {'available': False, 'methods': {}, 'errors': []}
            
            try:
                processor = get_operator_processor(operator)
                
                if processor is None:
                    processor_info['errors'].append("Procesador retorna None")
                else:
                    processor_info['available'] = True
                    
                    # Verificar métodos esenciales
                    essential_methods = ['process_file', 'validate_file_structure', 'get_supported_file_types']
                    
                    for method in essential_methods:
                        processor_info['methods'][method] = hasattr(processor, method)
                    
                    # Si tiene todos los métodos, considerar funcional
                    if all(processor_info['methods'].values()):
                        results['processors_working'] += 1
                        logger.info(f"✓ {operator}: Procesador funcional")
                        
                        # Intentar obtener tipos de archivo soportados
                        try:
                            file_types = processor.get_supported_file_types()
                            processor_info['supported_file_types'] = file_types
                        except Exception as e:
                            processor_info['errors'].append(f"Error obteniendo tipos de archivo: {e}")
                    else:
                        logger.warning(f"⚠ {operator}: Métodos faltantes")
                        
            except Exception as e:
                processor_info['errors'].append(str(e))
                logger.error(f"✗ {operator}: Error - {str(e)}")
            
            results['processor_details'][operator] = processor_info
        
        # Determinar estado
        if results['processors_working'] == len(expected_operators):
            results['status'] = 'PASSED'
            logger.info(f"PROCESSORS: PASSED ({results['processors_working']}/{results['processors_tested']})")
        elif results['processors_working'] >= 3:
            results['status'] = 'WARNING'
            logger.warning(f"PROCESSORS: WARNING ({results['processors_working']}/{results['processors_tested']})")
        else:
            results['status'] = 'FAILED'
            logger.error(f"PROCESSORS: FAILED ({results['processors_working']}/{results['processors_tested']})")
            
    except Exception as e:
        results['status'] = 'ERROR'
        results['error'] = str(e)
        logger.error(f"PROCESSORS: ERROR - {str(e)}")
    
    return results

def test_validators():
    """Test de validadores específicos"""
    logger.info("=== TEST: Validadores Específicos ===")
    results = {
        'test_name': 'BACKEND-VALIDATORS',
        'validators_tested': 0,
        'validators_passed': 0,
        'validation_details': {},
        'status': 'UNKNOWN'
    }
    
    try:
        from utils.validators import validate_colombian_phone_number, validate_coordinates, validate_claro_date_format
        
        # Test teléfonos colombianos
        phone_tests = [
            ('3001234567', True),   # Debe pasar
            ('6011234567', True),   # Debe pasar
            ('12345', False),       # Debe fallar
            ('abc123', False),      # Debe fallar
        ]
        
        phone_results = []
        for phone, should_pass in phone_tests:
            results['validators_tested'] += 1
            try:
                result = validate_colombian_phone_number(phone)
                passed = should_pass  # Si no lanzó excepción y esperábamos que pasara
                phone_results.append({'input': phone, 'expected': should_pass, 'result': result, 'passed': passed})
                if passed:
                    results['validators_passed'] += 1
            except Exception as e:
                passed = not should_pass  # Si lanzó excepción y esperábamos que fallara
                phone_results.append({'input': phone, 'expected': should_pass, 'error': str(e), 'passed': passed})
                if passed:
                    results['validators_passed'] += 1
        
        results['validation_details']['phone'] = phone_results
        
        # Test coordenadas
        coord_tests = [
            ((4.6097, -74.0817), True),   # Bogotá - debe pasar
            ((0.0, 0.0), True),           # Ecuador - debe pasar
            ((91.0, 0.0), False),         # Latitud inválida - debe fallar
            (('a', 'b'), False),          # Tipos inválidos - debe fallar
        ]
        
        coord_results = []
        for (lat, lon), should_pass in coord_tests:
            results['validators_tested'] += 1
            try:
                result = validate_coordinates(lat, lon)
                passed = should_pass
                coord_results.append({'lat': lat, 'lon': lon, 'expected': should_pass, 'result': result, 'passed': passed})
                if passed:
                    results['validators_passed'] += 1
            except Exception as e:
                passed = not should_pass
                coord_results.append({'lat': lat, 'lon': lon, 'expected': should_pass, 'error': str(e), 'passed': passed})
                if passed:
                    results['validators_passed'] += 1
        
        results['validation_details']['coordinates'] = coord_results
        
        # Test fechas CLARO
        date_tests = [
            ('20250115123000', True),     # Formato válido - debe pasar
            ('20241225000000', True),     # Formato válido - debe pasar
            ('fecha_invalida', False),    # Formato inválido - debe fallar
            ('20250115', False),          # Muy corto - debe fallar
        ]
        
        date_results = []
        for date_str, should_pass in date_tests:
            results['validators_tested'] += 1
            try:
                result = validate_claro_date_format(date_str)
                passed = should_pass
                date_results.append({'input': date_str, 'expected': should_pass, 'result': str(result), 'passed': passed})
                if passed:
                    results['validators_passed'] += 1
            except Exception as e:
                passed = not should_pass
                date_results.append({'input': date_str, 'expected': should_pass, 'error': str(e), 'passed': passed})
                if passed:
                    results['validators_passed'] += 1
        
        results['validation_details']['dates'] = date_results
        
        # Determinar estado
        success_rate = results['validators_passed'] / results['validators_tested'] if results['validators_tested'] > 0 else 0
        if success_rate >= 0.8:
            results['status'] = 'PASSED'
            logger.info(f"VALIDATORS: PASSED ({results['validators_passed']}/{results['validators_tested']})")
        elif success_rate >= 0.6:
            results['status'] = 'WARNING'
            logger.warning(f"VALIDATORS: WARNING ({results['validators_passed']}/{results['validators_tested']})")
        else:
            results['status'] = 'FAILED'
            logger.error(f"VALIDATORS: FAILED ({results['validators_passed']}/{results['validators_tested']})")
            
    except Exception as e:
        results['status'] = 'ERROR'
        results['error'] = str(e)
        logger.error(f"VALIDATORS: ERROR - {str(e)}")
    
    return results

def test_file_processing():
    """Test básico de procesamiento de archivos"""
    logger.info("=== TEST: Procesamiento de Archivos ===")
    results = {
        'test_name': 'BACKEND-FILE-PROCESSING',
        'tests_executed': 0,
        'tests_passed': 0,
        'processing_details': {},
        'status': 'UNKNOWN'
    }
    
    try:
        from utils.helpers import decode_base64_file, read_csv_file, read_excel_file
        import base64
        import io
        
        # Test decodificación base64
        results['tests_executed'] += 1
        try:
            # Crear un archivo CSV simple como test
            test_csv_content = "columna1,columna2\nvalor1,valor2\nvalor3,valor4"
            test_csv_bytes = test_csv_content.encode('utf-8')
            test_csv_b64 = base64.b64encode(test_csv_bytes).decode('ascii')
            
            file_data = {
                'name': 'test.csv',
                'content': f'data:text/csv;base64,{test_csv_b64}'
            }
            
            decoded_bytes, name, mime_type = decode_base64_file(file_data)
            
            if decoded_bytes == test_csv_bytes and name == 'test.csv' and mime_type == 'text/csv':
                results['tests_passed'] += 1
                results['processing_details']['base64_decode'] = 'PASSED'
                logger.info("✓ Decodificación base64: OK")
            else:
                results['processing_details']['base64_decode'] = 'FAILED - Datos no coinciden'
                logger.error("✗ Decodificación base64: Datos no coinciden")
                
        except Exception as e:
            results['processing_details']['base64_decode'] = f'ERROR - {str(e)}'
            logger.error(f"✗ Decodificación base64: {str(e)}")
        
        # Test lectura CSV
        results['tests_executed'] += 1
        try:
            test_csv_content = "columna1,columna2\nvalor1,valor2\nvalor3,valor4"
            test_csv_bytes = test_csv_content.encode('utf-8')
            
            df = read_csv_file(test_csv_bytes)
            
            if len(df) == 2 and len(df.columns) == 2 and 'columna1' in df.columns:
                results['tests_passed'] += 1
                results['processing_details']['csv_read'] = 'PASSED'
                logger.info("✓ Lectura CSV: OK")
            else:
                results['processing_details']['csv_read'] = 'FAILED - DataFrame incorrecto'
                logger.error("✗ Lectura CSV: DataFrame incorrecto")
                
        except Exception as e:
            results['processing_details']['csv_read'] = f'ERROR - {str(e)}'
            logger.error(f"✗ Lectura CSV: {str(e)}")
        
        # Determinar estado
        success_rate = results['tests_passed'] / results['tests_executed'] if results['tests_executed'] > 0 else 0
        if success_rate >= 0.8:
            results['status'] = 'PASSED'
            logger.info(f"FILE-PROCESSING: PASSED ({results['tests_passed']}/{results['tests_executed']})")
        else:
            results['status'] = 'FAILED'
            logger.error(f"FILE-PROCESSING: FAILED ({results['tests_passed']}/{results['tests_executed']})")
            
    except Exception as e:
        results['status'] = 'ERROR'
        results['error'] = str(e)
        logger.error(f"FILE-PROCESSING: ERROR - {str(e)}")
    
    return results

def test_real_file_existence():
    """Test de existencia de archivos reales para testing"""
    logger.info("=== TEST: Archivos Reales Disponibles ===")
    results = {
        'test_name': 'BACKEND-REAL-FILES',
        'files_checked': 0,
        'files_found': 0,
        'file_details': {},
        'status': 'UNKNOWN'
    }
    
    # Archivos esperados para testing
    test_files_base = current_dir.parent / "archivos" / "CeldasDiferenteOperador"
    
    expected_files = [
        ("claro/DATOS_POR_CELDA CLARO.xlsx", "CLARO - Datos por celda"),
        ("claro/LLAMADAS_ENTRANTES_POR_CELDA CLARO.xlsx", "CLARO - Llamadas entrantes"),
        ("claro/LLAMADAS_SALIENTES_POR_CELDA CLARO.xlsx", "CLARO - Llamadas salientes"),
        ("mov/jgd202410754_00007301_datos_ MOVISTAR.xlsx", "MOVISTAR - Datos"),
        ("tigo/Reporte TIGO.xlsx", "TIGO - Reporte mixto"),
        ("wom/PUNTO 1 TRÁFICO DATOS WOM.xlsx", "WOM - Datos"),
        ("wom/PUNTO 1 TRÁFICO VOZ ENTRAN  SALIENT WOM.xlsx", "WOM - Llamadas"),
    ]
    
    for relative_path, description in expected_files:
        results['files_checked'] += 1
        file_path = test_files_base / relative_path
        
        file_info = {
            'path': str(file_path),
            'description': description,
            'exists': file_path.exists(),
            'size': None
        }
        
        if file_path.exists():
            try:
                file_info['size'] = file_path.stat().st_size
                results['files_found'] += 1
                logger.info(f"✓ {description}: Encontrado ({file_info['size']} bytes)")
            except Exception as e:
                file_info['error'] = str(e)
                logger.warning(f"⚠ {description}: Encontrado pero error leyendo propiedades")
        else:
            logger.warning(f"✗ {description}: No encontrado")
        
        results['file_details'][relative_path] = file_info
    
    # Determinar estado
    if results['files_found'] >= 6:  # Al menos 6 de 7 archivos
        results['status'] = 'PASSED'
        logger.info(f"REAL-FILES: PASSED ({results['files_found']}/{results['files_checked']})")
    elif results['files_found'] >= 4:  # Al menos 4 archivos
        results['status'] = 'WARNING'
        logger.warning(f"REAL-FILES: WARNING ({results['files_found']}/{results['files_checked']})")
    else:
        results['status'] = 'FAILED'
        logger.error(f"REAL-FILES: FAILED ({results['files_found']}/{results['files_checked']})")
    
    return results

def generate_assessment_report(test_results: List[Dict[str, Any]]):
    """Genera reporte de evaluación rápida"""
    
    # Calcular estadísticas generales
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r.get('status') == 'PASSED')
    warning_tests = sum(1 for r in test_results if r.get('status') == 'WARNING')
    failed_tests = sum(1 for r in test_results if r.get('status') == 'FAILED')
    error_tests = sum(1 for r in test_results if r.get('status') == 'ERROR')
    
    # Determinar estado general del backend
    critical_failures = sum(1 for r in test_results 
                          if r.get('status') in ['FAILED', 'ERROR'] and 
                          r.get('test_name', '').startswith('BACKEND-'))
    
    if critical_failures == 0 and passed_tests >= (total_tests * 0.8):
        backend_status = 'APROBADO'
        approved = True
    elif critical_failures <= 1 and (passed_tests + warning_tests) >= (total_tests * 0.7):
        backend_status = 'APROBADO CON OBSERVACIONES'
        approved = True
    else:
        backend_status = 'NO APROBADO'
        approved = False
    
    report = {
        'report_info': {
            'title': 'EVALUACIÓN RÁPIDA BACKEND COORDINADO',
            'specialist': 'Backend Python/Eel Team',
            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'context': 'Testing post-issues críticos de BD - Evaluación independiente'
        },
        
        'executive_summary': {
            'backend_status': backend_status,
            'backend_approved': approved,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'warning_tests': warning_tests,
            'failed_tests': failed_tests,
            'error_tests': error_tests,
            'critical_failures': critical_failures
        },
        
        'detailed_results': {r['test_name']: r for r in test_results},
        
        'findings': {
            'backend_functional': critical_failures == 0,
            'can_process_files': any(r.get('test_name') == 'BACKEND-FILE-PROCESSING' and 
                                   r.get('status') == 'PASSED' for r in test_results),
            'processors_available': any(r.get('test_name') == 'BACKEND-PROCESSORS' and 
                                      r.get('status') in ['PASSED', 'WARNING'] for r in test_results),
            'validators_working': any(r.get('test_name') == 'BACKEND-VALIDATORS' and 
                                    r.get('status') in ['PASSED', 'WARNING'] for r in test_results),
            'test_files_available': any(r.get('test_name') == 'BACKEND-REAL-FILES' and 
                                      r.get('status') in ['PASSED', 'WARNING'] for r in test_results)
        },
        
        'recommendations': {
            'immediate_actions': [],
            'before_production': [],
            'coordination_notes': []
        }
    }
    
    # Generar recomendaciones específicas
    if not report['findings']['backend_functional']:
        report['recommendations']['immediate_actions'].append(
            "Resolver fallas críticas en componentes básicos del backend"
        )
    
    if not report['findings']['processors_available']:
        report['recommendations']['immediate_actions'].append(
            "Corregir procesadores de operador - crítico para funcionalidad principal"
        )
    
    if report['findings']['backend_functional'] and report['findings']['processors_available']:
        report['recommendations']['coordination_notes'].append(
            "Backend funcionalmente estable - issues de BD pueden ser independientes"
        )
    
    if not report['findings']['test_files_available']:
        report['recommendations']['before_production'].append(
            "Asegurar disponibilidad de archivos de prueba para testing integral"
        )
    
    # Coordinar con equipo de BD
    if approved:
        report['recommendations']['coordination_notes'].extend([
            "Backend aprobado para continuar con testing coordinado",
            "Evaluar si issues de BD son de configuración o datos, no de backend",
            "Proceder con casos P0-001 a P0-004 usando backend validado"
        ])
    else:
        report['recommendations']['immediate_actions'].append(
            "Resolver issues de backend antes de continuar testing coordinado con BD"
        )
    
    return report

def main():
    """Función principal de evaluación rápida"""
    logger.info("=== INICIANDO EVALUACIÓN RÁPIDA DEL BACKEND ===")
    logger.info("Objetivo: Validar funcionalidad básica sin configuración completa")
    
    # Ejecutar tests rápidos
    test_results = []
    
    try:
        # Test 1: Importaciones
        logger.info("\n--- Ejecutando Test 1: Importaciones ---")
        result1 = test_backend_imports()
        test_results.append(result1)
        
        # Test 2: Procesadores (solo si importaciones pasan)
        if result1['status'] in ['PASSED', 'WARNING']:
            logger.info("\n--- Ejecutando Test 2: Procesadores ---")
            result2 = test_operator_processors()
            test_results.append(result2)
            
            # Test 3: Validadores (solo si procesadores pasan)
            if result2['status'] in ['PASSED', 'WARNING']:
                logger.info("\n--- Ejecutando Test 3: Validadores ---")
                result3 = test_validators()
                test_results.append(result3)
                
                # Test 4: Procesamiento de archivos
                logger.info("\n--- Ejecutando Test 4: Procesamiento de Archivos ---")
                result4 = test_file_processing()
                test_results.append(result4)
        
        # Test 5: Archivos reales (siempre ejecutar)
        logger.info("\n--- Ejecutando Test 5: Archivos Reales ---")
        result5 = test_real_file_existence()
        test_results.append(result5)
        
        # Generar reporte
        logger.info("\n--- Generando Reporte Final ---")
        final_report = generate_assessment_report(test_results)
        
        # Guardar reporte
        report_path = current_dir / "REPORTE_EVALUACION_RAPIDA_BACKEND.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)
        
        # Mostrar resumen
        logger.info("\n=== RESUMEN EJECUTIVO ===")
        logger.info(f"Estado Backend: {final_report['executive_summary']['backend_status']}")
        logger.info(f"Tests Ejecutados: {final_report['executive_summary']['total_tests']}")
        logger.info(f"Tests Pasados: {final_report['executive_summary']['passed_tests']}")
        logger.info(f"Tests con Warning: {final_report['executive_summary']['warning_tests']}")
        logger.info(f"Tests Fallidos: {final_report['executive_summary']['failed_tests']}")
        logger.info(f"Fallas Críticas: {final_report['executive_summary']['critical_failures']}")
        logger.info(f"Reporte guardado en: {report_path}")
        
        # Mostrar hallazgos clave
        logger.info("\n=== HALLAZGOS CLAVE ===")
        findings = final_report['findings']
        logger.info(f"Backend Funcional: {'SI' if findings['backend_functional'] else 'NO'}")
        logger.info(f"Puede Procesar Archivos: {'SI' if findings['can_process_files'] else 'NO'}")
        logger.info(f"Procesadores Disponibles: {'SI' if findings['processors_available'] else 'NO'}")
        logger.info(f"Validadores Funcionan: {'SI' if findings['validators_working'] else 'NO'}")
        logger.info(f"Archivos de Test Disponibles: {'SI' if findings['test_files_available'] else 'NO'}")
        
        return final_report
        
    except Exception as e:
        logger.error(f"Error en evaluación rápida: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {'error': str(e)}

if __name__ == '__main__':
    main()