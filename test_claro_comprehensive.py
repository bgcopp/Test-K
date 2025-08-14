#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KRONOS - Testing Comprensivo para Implementación CLARO
=====================================================

Este script ejecuta tests exhaustivos del sistema CLARO implementado,
validando todos los componentes críticos desde backend hasta integración.

Testing Scope:
1. Backend Services (operator_data_service, file_processor_service, data_normalizer_service)
2. Database Schema y Performance
3. File Processing con archivos reales
4. Data Validation y Normalization  
5. Error Handling y Edge Cases
6. Performance Metrics
7. Integration Testing

Autor: Sistema KRONOS Testing
Versión: 1.0.0
"""

import os
import sys
import json
import sqlite3
import time
import hashlib
import base64
import traceback
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from contextlib import contextmanager

# Add backend to path
backend_path = Path(__file__).parent / "Backend"
sys.path.insert(0, str(backend_path))

# Set console encoding for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

@contextmanager
def get_db_connection():
    """Simple SQLite connection context manager for testing"""
    db_path = os.path.join(backend_path, 'kronos.db')
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()

# Import services
try:
    from services.operator_data_service import OperatorDataService, upload_operator_data, get_operator_sheets
    from services.file_processor_service import FileProcessorService
    from services.data_normalizer_service import DataNormalizerService, validate_normalized_data
    from utils.operator_logger import OperatorLogger
except ImportError as e:
    print(f"Error importando servicios: {e}")
    sys.exit(1)


class ClaroTestingSuite:
    """Suite comprensiva de testing para implementación CLARO"""
    
    def __init__(self):
        self.logger = OperatorLogger()
        self.results = {
            'test_start_time': datetime.now().isoformat(),
            'tests_executed': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'critical_issues': [],
            'major_issues': [],
            'minor_issues': [],
            'performance_metrics': {},
            'test_details': []
        }
        
        # Test data paths
        self.test_data_dir = Path(__file__).parent / "datatest" / "Claro"
        self.csv_file = self.test_data_dir / "DATOS_POR_CELDA CLARO.csv"
        self.xlsx_file = self.test_data_dir / "formato excel" / "DATOS_POR_CELDA CLARO.xlsx"
        
        print("🚀 KRONOS CLARO Testing Suite Iniciado")
        print(f"📊 Archivos de prueba: {self.test_data_dir}")
        print(f"📄 CSV: {self.csv_file.exists()}")
        print(f"📄 XLSX: {self.xlsx_file.exists()}")
        print("-" * 80)
    
    def log_test_result(self, test_name: str, status: str, details: Dict[str, Any], 
                       duration: float = 0.0, issue_type: Optional[str] = None):
        """Log del resultado de un test individual"""
        self.results['tests_executed'] += 1
        
        if status == 'PASS':
            self.results['tests_passed'] += 1
        else:
            self.results['tests_failed'] += 1
            
            # Clasificar issues
            if issue_type == 'critical':
                self.results['critical_issues'].append({
                    'test': test_name,
                    'details': details,
                    'timestamp': datetime.now().isoformat()
                })
            elif issue_type == 'major':
                self.results['major_issues'].append({
                    'test': test_name,
                    'details': details,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                self.results['minor_issues'].append({
                    'test': test_name,
                    'details': details,
                    'timestamp': datetime.now().isoformat()
                })
        
        self.results['test_details'].append({
            'test_name': test_name,
            'status': status,
            'duration_seconds': duration,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
        status_emoji = "✅" if status == 'PASS' else "❌"
        print(f"{status_emoji} {test_name}: {status} ({duration:.2f}s)")
        if status != 'PASS' and details.get('error'):
            print(f"   └─ Error: {details['error']}")
    
    # =========================================================================
    # DATABASE TESTING
    # =========================================================================
    
    def test_database_schema(self) -> None:
        """Test 1: Verificar que el schema de base de datos esté configurado correctamente"""
        start_time = time.time()
        test_name = "Database Schema Validation"
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Verificar tablas principales
                required_tables = [
                    'operator_data_sheets',
                    'operator_cellular_data', 
                    'operator_call_data',
                    'file_processing_logs',
                    'operator_data_audit',
                    'operator_cell_registry'
                ]
                
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing_tables = [row[0] for row in cursor.fetchall()]
                
                missing_tables = [t for t in required_tables if t not in existing_tables]
                
                if missing_tables:
                    self.log_test_result(
                        test_name, 'FAIL',
                        {'error': f'Tablas faltantes: {missing_tables}', 'existing_tables': existing_tables},
                        time.time() - start_time, 'critical'
                    )
                    return
                
                # Verificar índices críticos
                cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
                indexes = [row[0] for row in cursor.fetchall()]
                
                critical_indexes = [
                    'idx_cellular_numero_telefono',
                    'idx_cellular_mission_operator',
                    'idx_operator_sheets_checksum'
                ]
                
                missing_indexes = [idx for idx in critical_indexes if idx not in indexes]
                
                # Verificar constraints
                cursor.execute("PRAGMA foreign_keys")
                fk_enabled = cursor.fetchone()[0]
                
                details = {
                    'tables_found': len(existing_tables),
                    'tables_required': len(required_tables),
                    'indexes_found': len(indexes),
                    'missing_indexes': missing_indexes,
                    'foreign_keys_enabled': bool(fk_enabled)
                }
                
                if missing_indexes or not fk_enabled:
                    self.log_test_result(
                        test_name, 'FAIL', 
                        {**details, 'error': f'Indexes faltantes: {missing_indexes}, FK enabled: {fk_enabled}'},
                        time.time() - start_time, 'major'
                    )
                else:
                    self.log_test_result(test_name, 'PASS', details, time.time() - start_time)
                    
        except Exception as e:
            self.log_test_result(
                test_name, 'FAIL',
                {'error': str(e), 'traceback': traceback.format_exc()},
                time.time() - start_time, 'critical'
            )
    
    def test_database_performance(self) -> None:
        """Test 2: Verificar performance de consultas críticas"""
        start_time = time.time()
        test_name = "Database Performance"
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                performance_tests = []
                
                # Test 1: Insert simple
                insert_start = time.time()
                test_sheet_id = f"test-{int(time.time())}"
                cursor.execute("""
                    INSERT INTO operator_data_sheets (
                        id, mission_id, file_name, file_size_bytes, file_checksum,
                        file_type, operator, operator_file_format, uploaded_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    test_sheet_id, 'test-mission', 'test.csv', 1024,
                    hashlib.sha256(b'test').hexdigest(), 'CELLULAR_DATA', 
                    'CLARO', 'CLARO_CELLULAR_DATA_CSV', 'test-user'
                ))
                insert_time = time.time() - insert_start
                performance_tests.append(('Insert operator_data_sheets', insert_time))
                
                # Test 2: Select con índice
                select_start = time.time()
                cursor.execute("SELECT * FROM operator_data_sheets WHERE id = ?", (test_sheet_id,))
                result = cursor.fetchone()
                select_time = time.time() - select_start
                performance_tests.append(('Select by ID', select_time))
                
                # Test 3: Join complejo
                join_start = time.time()
                cursor.execute("""
                    SELECT ods.*, COUNT(ocd.id) as record_count
                    FROM operator_data_sheets ods
                    LEFT JOIN operator_cellular_data ocd ON ods.id = ocd.file_upload_id
                    WHERE ods.operator = 'CLARO'
                    GROUP BY ods.id
                    LIMIT 10
                """)
                join_results = cursor.fetchall()
                join_time = time.time() - join_start
                performance_tests.append(('Complex JOIN query', join_time))
                
                # Limpiar datos de prueba
                cursor.execute("DELETE FROM operator_data_sheets WHERE id = ?", (test_sheet_id,))
                conn.commit()
                
                # Evaluar performance
                slow_queries = [(name, t) for name, t in performance_tests if t > 0.1]
                
                details = {
                    'performance_tests': [{'query': name, 'time_seconds': t} for name, t in performance_tests],
                    'slow_queries': slow_queries,
                    'avg_query_time': sum(t for _, t in performance_tests) / len(performance_tests)
                }
                
                if slow_queries:
                    self.log_test_result(
                        test_name, 'FAIL',
                        {**details, 'error': f'Consultas lentas detectadas: {slow_queries}'},
                        time.time() - start_time, 'major'
                    )
                else:
                    self.log_test_result(test_name, 'PASS', details, time.time() - start_time)
                    
        except Exception as e:
            self.log_test_result(
                test_name, 'FAIL',
                {'error': str(e), 'traceback': traceback.format_exc()},
                time.time() - start_time, 'critical'
            )
    
    # =========================================================================
    # BACKEND SERVICES TESTING  
    # =========================================================================
    
    def test_data_normalizer_service(self) -> None:
        """Test 3: Verificar servicio de normalización de datos"""
        start_time = time.time()
        test_name = "Data Normalizer Service"
        
        try:
            normalizer = DataNormalizerService()
            
            # Test data CLARO típica
            test_records = [
                {
                    'numero': '573205487611',
                    'fecha_trafico': '20240419080000',
                    'tipo_cdr': 'DATOS',
                    'celda_decimal': '175462',
                    'lac_decimal': '20010'
                },
                {
                    'numero': '57 312 345 6789',  # Con espacios
                    'fecha_trafico': '20240419080001',
                    'tipo_cdr': 'datos',  # lowercase
                    'celda_decimal': '175463',
                    'lac_decimal': ''  # vacío
                },
                {
                    'numero': '3123456789',  # Sin código país
                    'fecha_trafico': '20240419080002',
                    'tipo_cdr': 'VOZ',
                    'celda_decimal': '175464',
                    'lac_decimal': '20011'
                }
            ]
            
            normalization_results = []
            
            for i, record in enumerate(test_records):
                normalized = normalizer.normalize_claro_cellular_data(
                    record, f'test-file-{i}', 'test-mission'
                )
                
                if normalized:
                    # Validar datos normalizados
                    validation_errors = validate_normalized_data(normalized)
                    normalization_results.append({
                        'record_index': i,
                        'original': record,
                        'normalized': normalized,
                        'validation_errors': validation_errors,
                        'success': len(validation_errors) == 0
                    })
                else:
                    normalization_results.append({
                        'record_index': i,
                        'original': record,
                        'normalized': None,
                        'success': False,
                        'error': 'Normalización falló'
                    })
            
            # Evaluar resultados
            successful = sum(1 for r in normalization_results if r['success'])
            failed = len(normalization_results) - successful
            
            details = {
                'total_records': len(test_records),
                'successful_normalizations': successful,
                'failed_normalizations': failed,
                'results': normalization_results
            }
            
            if failed > 0:
                self.log_test_result(
                    test_name, 'FAIL',
                    {**details, 'error': f'{failed} normalizaciones fallaron'},
                    time.time() - start_time, 'major'
                )
            else:
                self.log_test_result(test_name, 'PASS', details, time.time() - start_time)
                
        except Exception as e:
            self.log_test_result(
                test_name, 'FAIL',
                {'error': str(e), 'traceback': traceback.format_exc()},
                time.time() - start_time, 'critical'
            )
    
    def test_file_processor_service(self) -> None:
        """Test 4: Verificar servicio de procesamiento de archivos"""
        start_time = time.time()
        test_name = "File Processor Service"
        
        try:
            processor = FileProcessorService()
            
            # Test encoding detection
            test_data_utf8 = "número,fecha_trafico,tipo_cdr\n573123456789,20240419080000,DATOS\n".encode('utf-8')
            test_data_latin1 = "número,fecha_trafico,tipo_cdr\n573123456789,20240419080000,DATOS\n".encode('latin-1')
            
            encoding_utf8 = processor._detect_encoding(test_data_utf8)
            encoding_latin1 = processor._detect_encoding(test_data_latin1)
            
            # Test CSV reading
            try:
                df_utf8 = processor._read_csv_robust(test_data_utf8, delimiter=',')
                csv_read_success = len(df_utf8) > 0
            except Exception as e:
                csv_read_success = False
                csv_error = str(e)
            
            # Test validation
            if csv_read_success:
                is_valid, errors = processor._validate_claro_cellular_columns(df_utf8)
                validation_success = is_valid
            else:
                validation_success = False
                errors = ['CSV reading failed']
            
            details = {
                'encoding_detection_utf8': encoding_utf8,
                'encoding_detection_latin1': encoding_latin1,
                'csv_read_success': csv_read_success,
                'validation_success': validation_success,
                'validation_errors': errors if not validation_success else []
            }
            
            if not csv_read_success or not validation_success:
                self.log_test_result(
                    test_name, 'FAIL',
                    {**details, 'error': 'CSV processing o validación falló'},
                    time.time() - start_time, 'major'
                )
            else:
                self.log_test_result(test_name, 'PASS', details, time.time() - start_time)
                
        except Exception as e:
            self.log_test_result(
                test_name, 'FAIL',
                {'error': str(e), 'traceback': traceback.format_exc()},
                time.time() - start_time, 'critical'
            )
    
    # =========================================================================
    # INTEGRATION TESTING
    # =========================================================================
    
    def test_real_file_processing_csv(self) -> None:
        """Test 5: Procesar archivo CSV real de CLARO"""
        start_time = time.time()
        test_name = "Real CSV File Processing"
        
        if not self.csv_file.exists():
            self.log_test_result(
                test_name, 'SKIP',
                {'error': f'Archivo CSV no encontrado: {self.csv_file}'},
                time.time() - start_time, 'minor'
            )
            return
        
        try:
            # Leer archivo real
            with open(self.csv_file, 'rb') as f:
                file_bytes = f.read()
            
            file_size_mb = len(file_bytes) / (1024 * 1024)
            
            # Encoded en base64 para simular upload
            file_data_b64 = base64.b64encode(file_bytes).decode('utf-8')
            
            # Crear IDs de prueba únicos
            test_mission_id = f"test-mission-{int(time.time())}"
            test_user_id = f"test-user-{int(time.time())}"
            
            # Crear misión y usuario de prueba  
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Crear usuario de prueba
                cursor.execute("""
                    INSERT OR IGNORE INTO users (id, username, password_hash, role_id, email)
                    VALUES (?, ?, ?, ?, ?)
                """, (test_user_id, 'test-user', 'hash', 'role1', 'test@test.com'))
                
                # Crear misión de prueba
                cursor.execute("""
                    INSERT OR IGNORE INTO missions (id, name, description, created_by, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (test_mission_id, 'Test Mission', 'Test', test_user_id, 'active'))
                
                conn.commit()
            
            # Procesar archivo usando el servicio completo
            processing_start = time.time()
            result = upload_operator_data(
                file_data_b64,
                self.csv_file.name,
                test_mission_id,
                'CLARO',
                'CELLULAR_DATA',
                test_user_id
            )
            processing_time = time.time() - processing_start
            
            # Limpiar datos de prueba
            if result.get('file_upload_id'):
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM operator_data_sheets WHERE id = ?", 
                                 (result['file_upload_id'],))
                    cursor.execute("DELETE FROM missions WHERE id = ?", (test_mission_id,))
                    cursor.execute("DELETE FROM users WHERE id = ?", (test_user_id,))
                    conn.commit()
            
            details = {
                'file_size_mb': round(file_size_mb, 2),
                'processing_time_seconds': round(processing_time, 2),
                'processing_success': result.get('success', False),
                'records_processed': result.get('records_processed', 0),
                'records_failed': result.get('records_failed', 0),
                'error': result.get('error') if not result.get('success') else None
            }
            
            # Store performance metrics
            self.results['performance_metrics']['csv_processing'] = details
            
            if not result.get('success'):
                self.log_test_result(
                    test_name, 'FAIL',
                    {**details, 'error': result.get('error', 'Unknown error')},
                    time.time() - start_time, 'critical'
                )
            else:
                self.log_test_result(test_name, 'PASS', details, time.time() - start_time)
                
        except Exception as e:
            self.log_test_result(
                test_name, 'FAIL',
                {'error': str(e), 'traceback': traceback.format_exc()},
                time.time() - start_time, 'critical'
            )
    
    def test_real_file_processing_xlsx(self) -> None:
        """Test 6: Procesar archivo XLSX real de CLARO"""
        start_time = time.time()
        test_name = "Real XLSX File Processing"
        
        if not self.xlsx_file.exists():
            self.log_test_result(
                test_name, 'SKIP',
                {'error': f'Archivo XLSX no encontrado: {self.xlsx_file}'},
                time.time() - start_time, 'minor'
            )
            return
        
        try:
            # Similar al test CSV pero con archivo Excel
            with open(self.xlsx_file, 'rb') as f:
                file_bytes = f.read()
            
            file_size_mb = len(file_bytes) / (1024 * 1024)
            file_data_b64 = base64.b64encode(file_bytes).decode('utf-8')
            
            test_mission_id = f"test-mission-xlsx-{int(time.time())}"
            test_user_id = f"test-user-xlsx-{int(time.time())}"
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO users (id, username, password_hash, role_id, email)
                    VALUES (?, ?, ?, ?, ?)
                """, (test_user_id, 'test-user', 'hash', 'role1', 'test@test.com'))
                cursor.execute("""
                    INSERT OR IGNORE INTO missions (id, name, description, created_by, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (test_mission_id, 'Test Mission XLSX', 'Test', test_user_id, 'active'))
                conn.commit()
            
            processing_start = time.time()
            result = upload_operator_data(
                file_data_b64,
                self.xlsx_file.name,
                test_mission_id,
                'CLARO',
                'CELLULAR_DATA',
                test_user_id
            )
            processing_time = time.time() - processing_start
            
            # Limpiar
            if result.get('file_upload_id'):
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM operator_data_sheets WHERE id = ?", 
                                 (result['file_upload_id'],))
                    cursor.execute("DELETE FROM missions WHERE id = ?", (test_mission_id,))
                    cursor.execute("DELETE FROM users WHERE id = ?", (test_user_id,))
                    conn.commit()
            
            details = {
                'file_size_mb': round(file_size_mb, 2),
                'processing_time_seconds': round(processing_time, 2),
                'processing_success': result.get('success', False),
                'records_processed': result.get('records_processed', 0),
                'records_failed': result.get('records_failed', 0)
            }
            
            self.results['performance_metrics']['xlsx_processing'] = details
            
            if not result.get('success'):
                self.log_test_result(
                    test_name, 'FAIL',
                    {**details, 'error': result.get('error', 'Unknown error')},
                    time.time() - start_time, 'critical'
                )
            else:
                self.log_test_result(test_name, 'PASS', details, time.time() - start_time)
                
        except Exception as e:
            self.log_test_result(
                test_name, 'FAIL',
                {'error': str(e), 'traceback': traceback.format_exc()},
                time.time() - start_time, 'critical'
            )
    
    # =========================================================================
    # ERROR HANDLING & EDGE CASES
    # =========================================================================
    
    def test_error_handling(self) -> None:
        """Test 7: Verificar manejo de errores y casos extremos"""
        start_time = time.time()
        test_name = "Error Handling & Edge Cases"
        
        try:
            error_tests = []
            
            # Test 1: Archivo muy grande (simulado)
            large_file_data = base64.b64encode(b'x' * (25 * 1024 * 1024)).decode('utf-8')  # 25MB
            result1 = upload_operator_data(large_file_data, 'large.csv', 'test', 'CLARO', 'CELLULAR_DATA', 'test')
            error_tests.append({
                'test': 'Large file rejection',
                'success': not result1.get('success'),
                'error_code': result1.get('error_code'),
                'expected_code': 'FILE_TOO_LARGE'
            })
            
            # Test 2: Formato inválido
            result2 = upload_operator_data('invalid_b64', 'test.txt', 'test', 'CLARO', 'CELLULAR_DATA', 'test')
            error_tests.append({
                'test': 'Invalid format rejection',
                'success': not result2.get('success'),
                'error_code': result2.get('error_code')
            })
            
            # Test 3: Operador no soportado
            valid_data = base64.b64encode(b'test,data\n123,456').decode('utf-8')
            result3 = upload_operator_data(valid_data, 'test.csv', 'test', 'INVALID_OP', 'CELLULAR_DATA', 'test')
            error_tests.append({
                'test': 'Invalid operator rejection',
                'success': not result3.get('success'),
                'error_code': result3.get('error_code'),
                'expected_code': 'UNSUPPORTED_OPERATOR'
            })
            
            # Test 4: Parámetros faltantes
            result4 = upload_operator_data('', '', '', '', '', '')
            error_tests.append({
                'test': 'Missing parameters rejection',
                'success': not result4.get('success'),
                'error_code': result4.get('error_code'),
                'expected_code': 'MISSING_PARAMETERS'
            })
            
            passed_tests = sum(1 for test in error_tests if test['success'])
            
            details = {
                'error_tests': error_tests,
                'passed_tests': passed_tests,
                'total_tests': len(error_tests)
            }
            
            if passed_tests != len(error_tests):
                self.log_test_result(
                    test_name, 'FAIL',
                    {**details, 'error': f'Solo {passed_tests}/{len(error_tests)} tests de error pasaron'},
                    time.time() - start_time, 'major'
                )
            else:
                self.log_test_result(test_name, 'PASS', details, time.time() - start_time)
                
        except Exception as e:
            self.log_test_result(
                test_name, 'FAIL',
                {'error': str(e), 'traceback': traceback.format_exc()},
                time.time() - start_time, 'critical'
            )
    
    def test_duplicate_detection(self) -> None:
        """Test 8: Verificar detección de duplicados"""
        start_time = time.time()
        test_name = "Duplicate Detection"
        
        try:
            # Crear archivo de prueba pequeño
            test_csv_content = """numero,fecha_trafico,tipo_cdr,celda_decimal,lac_decimal
573205487611,20240419080000,DATOS,175462,20010
573133934909,20240419080001,DATOS,175462,20010"""
            
            file_bytes = test_csv_content.encode('utf-8')
            file_data_b64 = base64.b64encode(file_bytes).decode('utf-8')
            
            test_mission_id = f"test-mission-dup-{int(time.time())}"
            test_user_id = f"test-user-dup-{int(time.time())}"
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO users (id, username, password_hash, role_id, email)
                    VALUES (?, ?, ?, ?, ?)
                """, (test_user_id, 'test-user', 'hash', 'role1', 'test@test.com'))
                cursor.execute("""
                    INSERT OR IGNORE INTO missions (id, name, description, created_by, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (test_mission_id, 'Test Mission Dup', 'Test', test_user_id, 'active'))
                conn.commit()
            
            # Primera carga - debe ser exitosa
            result1 = upload_operator_data(
                file_data_b64, 'test_dup.csv', test_mission_id, 'CLARO', 'CELLULAR_DATA', test_user_id
            )
            
            # Segunda carga del mismo archivo - debe ser rechazada por duplicado
            result2 = upload_operator_data(
                file_data_b64, 'test_dup.csv', test_mission_id, 'CLARO', 'CELLULAR_DATA', test_user_id
            )
            
            # Limpiar
            with get_db_connection() as conn:
                cursor = conn.cursor()
                if result1.get('file_upload_id'):
                    cursor.execute("DELETE FROM operator_data_sheets WHERE id = ?", 
                                 (result1['file_upload_id'],))
                cursor.execute("DELETE FROM missions WHERE id = ?", (test_mission_id,))
                cursor.execute("DELETE FROM users WHERE id = ?", (test_user_id,))
                conn.commit()
            
            details = {
                'first_upload_success': result1.get('success', False),
                'second_upload_rejected': not result2.get('success', True),
                'duplicate_error_code': result2.get('error_code'),
                'expected_error_code': 'DUPLICATE_FILE'
            }
            
            success = (result1.get('success') and 
                      not result2.get('success') and 
                      result2.get('error_code') == 'DUPLICATE_FILE')
            
            if not success:
                self.log_test_result(
                    test_name, 'FAIL',
                    {**details, 'error': 'Detección de duplicados no funcionó correctamente'},
                    time.time() - start_time, 'major'
                )
            else:
                self.log_test_result(test_name, 'PASS', details, time.time() - start_time)
                
        except Exception as e:
            self.log_test_result(
                test_name, 'FAIL',
                {'error': str(e), 'traceback': traceback.format_exc()},
                time.time() - start_time, 'critical'
            )
    
    # =========================================================================
    # MAIN EXECUTION
    # =========================================================================
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Ejecutar toda la suite de testing"""
        print("🔬 Iniciando Testing Suite Completa para CLARO...")
        print("-" * 80)
        
        # Database Tests
        print("\n📊 DATABASE TESTING")
        self.test_database_schema()
        self.test_database_performance()
        
        # Backend Services Tests
        print("\n⚙️ BACKEND SERVICES TESTING")
        self.test_data_normalizer_service()
        self.test_file_processor_service()
        
        # Integration Tests
        print("\n🔗 INTEGRATION TESTING")
        self.test_real_file_processing_csv()
        self.test_real_file_processing_xlsx()
        
        # Error Handling & Edge Cases
        print("\n🛡️ ERROR HANDLING & EDGE CASES")
        self.test_error_handling()
        self.test_duplicate_detection()
        
        # Finalizar resultados
        self.results['test_end_time'] = datetime.now().isoformat()
        self.results['total_duration'] = (
            datetime.fromisoformat(self.results['test_end_time']) - 
            datetime.fromisoformat(self.results['test_start_time'])
        ).total_seconds()
        
        self.results['success_rate'] = (
            (self.results['tests_passed'] / self.results['tests_executed']) * 100
            if self.results['tests_executed'] > 0 else 0
        )
        
        return self.results


def main():
    """Función principal de testing"""
    suite = ClaroTestingSuite()
    
    try:
        results = suite.run_all_tests()
        
        # Generar reporte
        print("\n" + "=" * 80)
        print("📋 RESUMEN DE TESTING CLARO")
        print("=" * 80)
        print(f"Tests Ejecutados: {results['tests_executed']}")
        print(f"Tests Pasados: {results['tests_passed']}")
        print(f"Tests Fallidos: {results['tests_failed']}")
        print(f"Tasa de Éxito: {results['success_rate']:.1f}%")
        print(f"Duración Total: {results['total_duration']:.2f} segundos")
        
        if results['critical_issues']:
            print(f"\n🚨 ISSUES CRÍTICOS: {len(results['critical_issues'])}")
            for issue in results['critical_issues']:
                print(f"  - {issue['test']}: {issue['details'].get('error', 'N/A')}")
        
        if results['major_issues']:
            print(f"\n⚠️ ISSUES MAYORES: {len(results['major_issues'])}")
            for issue in results['major_issues']:
                print(f"  - {issue['test']}: {issue['details'].get('error', 'N/A')}")
        
        if results['minor_issues']:
            print(f"\n💡 ISSUES MENORES: {len(results['minor_issues'])}")
        
        # Performance metrics
        if results['performance_metrics']:
            print(f"\n⚡ MÉTRICAS DE PERFORMANCE:")
            for metric, data in results['performance_metrics'].items():
                print(f"  - {metric}: {data}")
        
        # Guardar reporte completo
        report_path = Path(__file__).parent / f"claro_testing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 Reporte completo guardado en: {report_path}")
        
        # Exit code basado en resultados
        if results['critical_issues']:
            print("\n❌ TESTING FALLÓ - Issues críticos encontrados")
            return 1
        elif results['major_issues']:
            print("\n⚠️ TESTING PASÓ CON ADVERTENCIAS - Issues mayores encontrados") 
            return 0
        else:
            print("\n✅ TESTING COMPLETADO EXITOSAMENTE")
            return 0
            
    except Exception as e:
        print(f"\n💥 ERROR CRÍTICO EN TESTING SUITE: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())