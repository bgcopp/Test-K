#!/usr/bin/env python3
"""
TESTING EXHAUSTIVO - Carga de Archivos CLARO
===========================================
Sistema de testing completo para validar que el algoritmo de carga
de archivos CLARO funcione al 100% sin pérdida de datos.

Autor: Testing Engineer - Sistema KRONOS
"""

import pytest
import pandas as pd
import os
import sys
import sqlite3
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime
import json

# Agregar paths del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar logging para testing
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClaroLoadingTestSuite:
    """
    Suite de testing exhaustiva para validar carga de archivos CLARO.
    
    OBJETIVOS:
    1. Garantizar carga del 100% de registros
    2. Validar preservación de números objetivo
    3. Verificar remoción correcta de prefijo 57
    4. Detectar pérdidas de datos en cualquier etapa
    """
    
    # Archivos de prueba disponibles
    TEST_FILES = {
        'entrantes_1': r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\1-225211_LLAMADAS_ENTRANTES_POR_CELDA_545612_0.xlsx",
        'salientes_1': r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\1-225211_LLAMADAS_SALIENTES_POR_CELDA_545613_0.xlsx",
        'entrantes_2': r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\2-225211_LLAMADAS_ENTRANTES_POR_CELDA_545614_0.xlsx",
        'salientes_2': r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\2-225211_LLAMADAS_SALIENTES_POR_CELDA_545615_0.xlsx",
        'hunter': r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\SCANHUNTER.xlsx",
        'numeros_base': r"C:\Soluciones\BGC\claude\KNSOft\datatest\Claro\numerosbase.xlsx"
    }
    
    # Números objetivo que DEBEN aparecer
    TARGET_NUMBERS = [
        '3224274851', '3208611034', '3104277553', 
        '3102715509', '3143534707', '3214161903'
    ]
    
    def __init__(self):
        self.test_results = {}
        self.db_path = os.path.join(os.path.dirname(__file__), 'kronos.db')
        logger.info("ClaroLoadingTestSuite inicializado")
    
    def test_01_validate_test_files_exist(self) -> Dict[str, Any]:
        """
        Test 1: Validar que todos los archivos de prueba existen.
        """
        logger.info("TEST 1: Validando existencia de archivos de prueba")
        
        results = {
            'test_name': 'validate_test_files_exist',
            'status': 'PASS',
            'files_found': {},
            'files_missing': [],
            'critical_error': None
        }
        
        for file_key, file_path in self.TEST_FILES.items():
            exists = os.path.exists(file_path)
            results['files_found'][file_key] = {
                'path': file_path,
                'exists': exists,
                'size_mb': os.path.getsize(file_path) / (1024*1024) if exists else 0
            }
            
            if not exists:
                results['files_missing'].append(file_key)
                results['status'] = 'FAIL'
        
        if results['files_missing']:
            results['critical_error'] = f"Archivos faltantes: {results['files_missing']}"
        
        logger.info(f"TEST 1 RESULTADO: {results['status']}")
        return results
    
    def test_02_analyze_raw_file_content(self) -> Dict[str, Any]:
        """
        Test 2: Analizar contenido crudo de archivos para entender estructura.
        """
        logger.info("TEST 2: Analizando contenido crudo de archivos")
        
        results = {
            'test_name': 'analyze_raw_file_content',
            'status': 'PASS',
            'file_analysis': {},
            'target_numbers_found': {},
            'total_records_available': 0
        }
        
        for file_key, file_path in self.TEST_FILES.items():
            if not os.path.exists(file_path) or file_key == 'numeros_base':
                continue
                
            try:
                logger.info(f"Analizando archivo: {file_key}")
                
                # Leer archivo Excel
                if file_path.endswith('.xlsx'):
                    df = pd.read_excel(file_path)
                else:
                    df = pd.read_csv(file_path)
                
                # Análisis básico
                analysis = {
                    'total_rows': len(df),
                    'columns': list(df.columns),
                    'sample_data': df.head(3).to_dict('records') if len(df) > 0 else [],
                    'has_originador': 'originador' in df.columns,
                    'has_receptor': 'receptor' in df.columns,
                    'has_fecha': any(col for col in df.columns if 'fecha' in col.lower()),
                    'target_numbers_analysis': {}
                }
                
                # Buscar números objetivo en datos crudos
                if analysis['has_originador'] and analysis['has_receptor']:
                    for target in self.TARGET_NUMBERS:
                        # Buscar en originador
                        orig_matches = df['originador'].astype(str).str.contains(target, na=False).sum()
                        # Buscar en receptor  
                        recv_matches = df['receptor'].astype(str).str.contains(target, na=False).sum()
                        
                        total_matches = orig_matches + recv_matches
                        
                        analysis['target_numbers_analysis'][target] = {
                            'found_as_originador': orig_matches,
                            'found_as_receptor': recv_matches,
                            'total_appearances': total_matches
                        }
                        
                        if total_matches > 0:
                            if target not in results['target_numbers_found']:
                                results['target_numbers_found'][target] = []
                            results['target_numbers_found'][target].append(file_key)
                
                results['file_analysis'][file_key] = analysis
                results['total_records_available'] += analysis['total_rows']
                
            except Exception as e:
                logger.error(f"Error analizando {file_key}: {e}")
                results['status'] = 'FAIL'
                results['file_analysis'][file_key] = {'error': str(e)}
        
        # Resumen de números objetivo encontrados
        found_targets = len(results['target_numbers_found'])
        total_targets = len(self.TARGET_NUMBERS)
        
        logger.info(f"Números objetivo encontrados en archivos: {found_targets}/{total_targets}")
        logger.info(f"Total registros disponibles: {results['total_records_available']}")
        
        if found_targets < total_targets:
            missing = set(self.TARGET_NUMBERS) - set(results['target_numbers_found'].keys())
            logger.warning(f"Números objetivo NO encontrados en archivos: {missing}")
        
        return results
    
    def test_03_validate_number_base_reference(self) -> Dict[str, Any]:
        """
        Test 3: Validar archivo de números base como referencia.
        """
        logger.info("TEST 3: Validando archivo de números base")
        
        results = {
            'test_name': 'validate_number_base_reference',
            'status': 'PASS',
            'base_numbers': [],
            'base_analysis': {},
            'target_numbers_in_base': {}
        }
        
        try:
            base_file = self.TEST_FILES['numeros_base']
            
            if os.path.exists(base_file):
                df_base = pd.read_excel(base_file)
                
                # Extraer todos los números del archivo base
                numbers_found = set()
                for col in df_base.columns:
                    if df_base[col].dtype == 'object' or df_base[col].dtype == 'int64':
                        for value in df_base[col].dropna():
                            value_str = str(value).strip()
                            if len(value_str) >= 8 and value_str.isdigit():
                                numbers_found.add(value_str)
                
                results['base_numbers'] = list(numbers_found)
                results['base_analysis'] = {
                    'total_rows': len(df_base),
                    'columns': list(df_base.columns),
                    'unique_numbers_found': len(numbers_found)
                }
                
                # Verificar números objetivo en base
                for target in self.TARGET_NUMBERS:
                    # Buscar número con y sin prefijo 57
                    found_exact = target in numbers_found
                    found_with_prefix = f"57{target}" in numbers_found
                    
                    results['target_numbers_in_base'][target] = {
                        'found_exact': found_exact,
                        'found_with_prefix': found_with_prefix,
                        'found_any': found_exact or found_with_prefix
                    }
                
                logger.info(f"Archivo base cargado: {len(numbers_found)} números únicos")
            else:
                results['status'] = 'FAIL'
                results['error'] = "Archivo números base no encontrado"
                
        except Exception as e:
            logger.error(f"Error validando números base: {e}")
            results['status'] = 'FAIL'
            results['error'] = str(e)
        
        return results
    
    def test_04_simulate_claro_loading_process(self) -> Dict[str, Any]:
        """
        Test 4: Simular proceso completo de carga CLARO.
        """
        logger.info("TEST 4: Simulando proceso completo de carga CLARO")
        
        results = {
            'test_name': 'simulate_claro_loading_process',
            'status': 'PASS',
            'file_processing_results': {},
            'total_records_processed': 0,
            'total_records_loaded': 0,
            'target_numbers_processed': {},
            'processing_errors': []
        }
        
        try:
            # Importar el procesador CLARO existente o crear uno simplificado
            from services.file_processor_service import FileProcessorService
            processor = FileProcessorService()
            
            # Procesar cada archivo CLARO
            claro_files = [k for k in self.TEST_FILES.keys() if k.startswith(('entrantes', 'salientes'))]
            
            for file_key in claro_files:
                file_path = self.TEST_FILES[file_key]
                
                if not os.path.exists(file_path):
                    continue
                
                logger.info(f"Procesando archivo: {file_key}")
                
                try:
                    # Simular carga usando el servicio existente
                    # (Esto dependerá de la implementación actual)
                    
                    # Por ahora, hacer análisis directo del archivo
                    df = pd.read_excel(file_path)
                    
                    # Simular limpieza de números (remoción prefijo 57)
                    def clean_number(num):
                        if pd.isna(num):
                            return ''
                        num_str = str(num).strip()
                        # Remover prefijo 57 si existe
                        if num_str.startswith('57') and len(num_str) > 10:
                            return num_str[2:]
                        return num_str
                    
                    df['originador_clean'] = df['originador'].apply(clean_number)
                    df['receptor_clean'] = df['receptor'].apply(clean_number)
                    
                    # Contar registros válidos
                    valid_records = df[
                        (df['originador_clean'] != '') & 
                        (df['receptor_clean'] != '') &
                        (df['originador_clean'] != 'nan') &
                        (df['receptor_clean'] != 'nan')
                    ]
                    
                    # Buscar números objetivo en datos procesados
                    target_found_in_file = {}
                    for target in self.TARGET_NUMBERS:
                        orig_count = (valid_records['originador_clean'] == target).sum()
                        recv_count = (valid_records['receptor_clean'] == target).sum()
                        total_count = orig_count + recv_count
                        
                        target_found_in_file[target] = {
                            'as_originador': orig_count,
                            'as_receptor': recv_count,
                            'total': total_count
                        }
                        
                        if total_count > 0:
                            if target not in results['target_numbers_processed']:
                                results['target_numbers_processed'][target] = []
                            results['target_numbers_processed'][target].append(file_key)
                    
                    file_result = {
                        'total_raw_records': len(df),
                        'valid_records_after_processing': len(valid_records),
                        'processing_success_rate': (len(valid_records) / len(df)) * 100,
                        'target_numbers_found': target_found_in_file
                    }
                    
                    results['file_processing_results'][file_key] = file_result
                    results['total_records_processed'] += len(df)
                    results['total_records_loaded'] += len(valid_records)
                    
                except Exception as e:
                    error_msg = f"Error procesando {file_key}: {str(e)}"
                    results['processing_errors'].append(error_msg)
                    logger.error(error_msg)
            
            # Calcular tasa de éxito general
            overall_success_rate = (results['total_records_loaded'] / results['total_records_processed']) * 100 if results['total_records_processed'] > 0 else 0
            
            # Verificar si encontramos todos los números objetivo
            found_targets = len(results['target_numbers_processed'])
            total_targets = len(self.TARGET_NUMBERS)
            
            if found_targets < total_targets:
                results['status'] = 'PARTIAL'
                missing = set(self.TARGET_NUMBERS) - set(results['target_numbers_processed'].keys())
                logger.warning(f"Números objetivo NO procesados: {missing}")
            
            logger.info(f"Procesamiento simulado - Tasa éxito: {overall_success_rate:.1f}%")
            logger.info(f"Números objetivo procesados: {found_targets}/{total_targets}")
            
        except Exception as e:
            logger.error(f"Error en simulación de carga: {e}")
            results['status'] = 'FAIL'
            results['error'] = str(e)
        
        return results
    
    def test_05_validate_database_final_state(self) -> Dict[str, Any]:
        """
        Test 5: Validar estado final de la base de datos después de carga.
        """
        logger.info("TEST 5: Validando estado final de base de datos")
        
        results = {
            'test_name': 'validate_database_final_state',
            'status': 'PASS',
            'database_analysis': {},
            'target_numbers_in_db': {},
            'data_integrity_check': {}
        }
        
        try:
            if not os.path.exists(self.db_path):
                results['status'] = 'FAIL'
                results['error'] = "Base de datos no encontrada"
                return results
            
            with sqlite3.connect(self.db_path) as conn:
                # Analizar tabla operator_call_data
                cursor = conn.execute("SELECT COUNT(*) FROM operator_call_data")
                total_call_records = cursor.fetchone()[0]
                
                # Analizar tabla cellular_data (HUNTER)
                cursor = conn.execute("SELECT COUNT(*) FROM cellular_data")
                total_hunter_records = cursor.fetchone()[0]
                
                results['database_analysis'] = {
                    'total_call_records': total_call_records,
                    'total_hunter_records': total_hunter_records,
                    'tables_analyzed': ['operator_call_data', 'cellular_data']
                }
                
                # Buscar números objetivo en base de datos
                for target in self.TARGET_NUMBERS:
                    # Buscar en operator_call_data
                    query = """
                        SELECT COUNT(*) FROM operator_call_data 
                        WHERE numero_origen LIKE ? OR numero_destino LIKE ? OR numero_objetivo LIKE ?
                    """
                    
                    # Buscar tanto con prefijo como sin prefijo
                    patterns = [f"%{target}%", f"%57{target}%"]
                    
                    total_found = 0
                    for pattern in patterns:
                        cursor = conn.execute(query, (pattern, pattern, pattern))
                        count = cursor.fetchone()[0]
                        total_found += count
                    
                    results['target_numbers_in_db'][target] = {
                        'found_in_operator_call_data': total_found > 0,
                        'total_occurrences': total_found
                    }
                
                # Verificar integridad de datos
                # 1. Verificar que no haya registros con números vacíos
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM operator_call_data 
                    WHERE numero_origen IS NULL OR numero_origen = '' 
                    OR numero_destino IS NULL OR numero_destino = ''
                """)
                empty_number_records = cursor.fetchone()[0]
                
                # 2. Verificar distribución de operadores
                cursor = conn.execute("""
                    SELECT operator, COUNT(*) as count 
                    FROM operator_call_data 
                    GROUP BY operator
                """)
                operator_distribution = dict(cursor.fetchall())
                
                results['data_integrity_check'] = {
                    'records_with_empty_numbers': empty_number_records,
                    'operator_distribution': operator_distribution,
                    'data_quality_score': (total_call_records - empty_number_records) / total_call_records * 100 if total_call_records > 0 else 0
                }
                
                # Determinar estado general
                found_targets = sum(1 for target_data in results['target_numbers_in_db'].values() if target_data['found_in_operator_call_data'])
                total_targets = len(self.TARGET_NUMBERS)
                
                if found_targets < total_targets:
                    results['status'] = 'FAIL'
                    missing = [target for target, data in results['target_numbers_in_db'].items() if not data['found_in_operator_call_data']]
                    logger.error(f"Números objetivo NO encontrados en DB: {missing}")
                
                logger.info(f"Estado DB - Registros: {total_call_records}, Números objetivo: {found_targets}/{total_targets}")
                
        except Exception as e:
            logger.error(f"Error validando base de datos: {e}")
            results['status'] = 'FAIL'
            results['error'] = str(e)
        
        return results
    
    def run_complete_test_suite(self) -> Dict[str, Any]:
        """
        Ejecutar suite completa de testing.
        """
        logger.info("=" * 80)
        logger.info("INICIANDO SUITE COMPLETA DE TESTING - CARGA CLARO")
        logger.info("=" * 80)
        
        # Ejecutar todos los tests
        tests_to_run = [
            self.test_01_validate_test_files_exist,
            self.test_02_analyze_raw_file_content,
            self.test_03_validate_number_base_reference,
            self.test_04_simulate_claro_loading_process,
            self.test_05_validate_database_final_state
        ]
        
        suite_results = {
            'suite_start_time': datetime.now().isoformat(),
            'tests_executed': [],
            'tests_passed': 0,
            'tests_failed': 0,
            'overall_status': 'PASS',
            'critical_issues': [],
            'recommendations': []
        }
        
        for test_func in tests_to_run:
            try:
                logger.info(f"\nEjecutando: {test_func.__name__}")
                test_result = test_func()
                
                suite_results['tests_executed'].append(test_result)
                
                if test_result['status'] == 'PASS':
                    suite_results['tests_passed'] += 1
                else:
                    suite_results['tests_failed'] += 1
                    if test_result['status'] == 'FAIL':
                        suite_results['overall_status'] = 'FAIL'
                        if 'error' in test_result:
                            suite_results['critical_issues'].append(test_result['error'])
                
                logger.info(f"Resultado: {test_result['status']}")
                
            except Exception as e:
                error_msg = f"Error ejecutando {test_func.__name__}: {str(e)}"
                logger.error(error_msg)
                suite_results['tests_failed'] += 1
                suite_results['overall_status'] = 'FAIL'
                suite_results['critical_issues'].append(error_msg)
        
        # Generar recomendaciones
        if suite_results['overall_status'] != 'PASS':
            suite_results['recommendations'].extend([
                "1. Verificar que todos los archivos de prueba estén disponibles",
                "2. Revisar algoritmo de carga CLARO para garantizar 100% de registros",
                "3. Validar que remoción de prefijo 57 funcione correctamente",
                "4. Implementar logging detallado en proceso de carga",
                "5. Crear validaciones de integridad de datos post-carga"
            ])
        
        suite_results['suite_end_time'] = datetime.now().isoformat()
        
        # Guardar resultados detallados
        results_file = f"claro_testing_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(suite_results, f, indent=2, ensure_ascii=False)
        
        logger.info("=" * 80)
        logger.info(f"SUITE COMPLETADA - Estado: {suite_results['overall_status']}")
        logger.info(f"Tests pasados: {suite_results['tests_passed']}")
        logger.info(f"Tests fallidos: {suite_results['tests_failed']}")
        logger.info(f"Resultados guardados en: {results_file}")
        logger.info("=" * 80)
        
        return suite_results

def main():
    """Función principal para ejecutar testing."""
    test_suite = ClaroLoadingTestSuite()
    results = test_suite.run_complete_test_suite()
    
    # Imprimir resumen final
    print("\n" + "="*60)
    print("RESUMEN FINAL DEL TESTING")
    print("="*60)
    print(f"Estado general: {results['overall_status']}")
    print(f"Tests ejecutados: {len(results['tests_executed'])}")
    print(f"Tests exitosos: {results['tests_passed']}")
    print(f"Tests fallidos: {results['tests_failed']}")
    
    if results['critical_issues']:
        print(f"\nProblemas críticos encontrados:")
        for issue in results['critical_issues']:
            print(f"  - {issue}")
    
    if results['recommendations']:
        print(f"\nRecomendaciones:")
        for rec in results['recommendations']:
            print(f"  {rec}")
    
    return results['overall_status'] == 'PASS'

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)