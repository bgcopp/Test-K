#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KRONOS - Testing Focalizado para CLARO
======================================

Test minimalista que se enfoca en los componentes críticos
sin dependencias complejas del sistema completo.
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

# Set console encoding for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

# Add backend to path
backend_path = Path(__file__).parent / "Backend"
sys.path.insert(0, str(backend_path))

class ClaroTestingSuiteFocused:
    """Suite de testing focalizada en CLARO sin dependencias complejas"""
    
    def __init__(self):
        self.results = {
            'test_start_time': datetime.now().isoformat(),
            'tests_executed': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'issues': [],
            'performance_metrics': {},
            'test_details': []
        }
        
        # Test data paths
        self.test_data_dir = Path(__file__).parent / "datatest" / "Claro"
        self.csv_file = self.test_data_dir / "DATOS_POR_CELDA CLARO.csv"
        self.xlsx_file = self.test_data_dir / "formato excel" / "DATOS_POR_CELDA CLARO.xlsx"
        
        print("🚀 KRONOS CLARO Testing Suite Focalizado Iniciado")
        print(f"📊 Archivos de prueba: {self.test_data_dir}")
        print(f"📄 CSV: {self.csv_file.exists()}")
        print(f"📄 XLSX: {self.xlsx_file.exists()}")
        print("-" * 80)
    
    def log_test_result(self, test_name: str, status: str, details: Dict[str, Any], 
                       duration: float = 0.0):
        """Log del resultado de un test individual"""
        self.results['tests_executed'] += 1
        
        if status == 'PASS':
            self.results['tests_passed'] += 1
        else:
            self.results['tests_failed'] += 1
            self.results['issues'].append({
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
    
    def test_database_exists(self):
        """Test 1: Verificar que la base de datos existe"""
        start_time = time.time()
        test_name = "Database Existence"
        
        try:
            db_path = backend_path / 'kronos.db'
            
            if not db_path.exists():
                self.log_test_result(
                    test_name, 'FAIL',
                    {'error': f'Base de datos no encontrada: {db_path}'},
                    time.time() - start_time
                )
                return
            
            # Test basic connection
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
            
            details = {
                'db_path': str(db_path),
                'db_size_mb': round(db_path.stat().st_size / (1024 * 1024), 2),
                'tables_found': len(tables),
                'tables': tables[:10]  # Primeras 10 tablas
            }
            
            self.log_test_result(test_name, 'PASS', details, time.time() - start_time)
            
        except Exception as e:
            self.log_test_result(
                test_name, 'FAIL',
                {'error': str(e), 'traceback': traceback.format_exc()},
                time.time() - start_time
            )
    
    def test_operator_schema_exists(self):
        """Test 2: Verificar que las tablas de operadores existen"""
        start_time = time.time()
        test_name = "Operator Schema"
        
        try:
            db_path = backend_path / 'kronos.db'
            
            required_tables = [
                'operator_data_sheets',
                'operator_cellular_data', 
                'operator_call_data'
            ]
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing_tables = [row[0] for row in cursor.fetchall()]
                
                missing_tables = [t for t in required_tables if t not in existing_tables]
                
                # Check schema for existing tables
                table_schemas = {}
                for table in required_tables:
                    if table in existing_tables:
                        cursor.execute(f"PRAGMA table_info({table})")
                        columns = cursor.fetchall()
                        table_schemas[table] = [col[1] for col in columns]  # Column names
            
            details = {
                'required_tables': required_tables,
                'existing_tables': existing_tables,
                'missing_tables': missing_tables,
                'table_schemas': table_schemas
            }
            
            if missing_tables:
                self.log_test_result(
                    test_name, 'FAIL',
                    {**details, 'error': f'Tablas faltantes: {missing_tables}'},
                    time.time() - start_time
                )
            else:
                self.log_test_result(test_name, 'PASS', details, time.time() - start_time)
                
        except Exception as e:
            self.log_test_result(
                test_name, 'FAIL',
                {'error': str(e), 'traceback': traceback.format_exc()},
                time.time() - start_time
            )
    
    def test_file_processor_import(self):
        """Test 3: Verificar que los servicios se puedan importar"""
        start_time = time.time()
        test_name = "Service Imports"
        
        try:
            imports_status = {}
            
            # Test file processor
            try:
                from services.file_processor_service import FileProcessorService
                processor = FileProcessorService()
                imports_status['FileProcessorService'] = 'OK'
            except Exception as e:
                imports_status['FileProcessorService'] = str(e)
            
            # Test data normalizer
            try:
                from services.data_normalizer_service import DataNormalizerService
                normalizer = DataNormalizerService()
                imports_status['DataNormalizerService'] = 'OK'
            except Exception as e:
                imports_status['DataNormalizerService'] = str(e)
            
            # Test logger
            try:
                from utils.operator_logger import OperatorLogger
                logger = OperatorLogger()
                imports_status['OperatorLogger'] = 'OK'
            except Exception as e:
                imports_status['OperatorLogger'] = str(e)
            
            details = {'imports': imports_status}
            
            failed_imports = [name for name, status in imports_status.items() if status != 'OK']
            
            if failed_imports:
                self.log_test_result(
                    test_name, 'FAIL',
                    {**details, 'error': f'Imports fallidos: {failed_imports}'},
                    time.time() - start_time
                )
            else:
                self.log_test_result(test_name, 'PASS', details, time.time() - start_time)
                
        except Exception as e:
            self.log_test_result(
                test_name, 'FAIL',
                {'error': str(e), 'traceback': traceback.format_exc()},
                time.time() - start_time
            )
    
    def test_data_normalizer_basic(self):
        """Test 4: Testing básico del normalizador de datos"""
        start_time = time.time()
        test_name = "Data Normalizer Basic"
        
        try:
            from services.data_normalizer_service import DataNormalizerService
            normalizer = DataNormalizerService()
            
            # Test data CLARO
            test_record = {
                'numero': '573205487611',
                'fecha_trafico': '20240419080000',
                'tipo_cdr': 'DATOS',
                'celda_decimal': '175462',
                'lac_decimal': '20010'
            }
            
            # Test normalización
            normalized = normalizer.normalize_claro_cellular_data(
                test_record, 'test-file-id', 'test-mission-id'
            )
            
            details = {
                'original_record': test_record,
                'normalized_success': normalized is not None,
                'normalized_fields': list(normalized.keys()) if normalized else [],
                'has_record_hash': 'record_hash' in (normalized or {}),
                'has_normalized_phone': 'numero_telefono' in (normalized or {}),
                'has_datetime': 'fecha_hora_inicio' in (normalized or {})
            }
            
            if not normalized:
                self.log_test_result(
                    test_name, 'FAIL',
                    {**details, 'error': 'Normalización retornó None'},
                    time.time() - start_time
                )
            else:
                self.log_test_result(test_name, 'PASS', details, time.time() - start_time)
                
        except Exception as e:
            self.log_test_result(
                test_name, 'FAIL',
                {'error': str(e), 'traceback': traceback.format_exc()},
                time.time() - start_time
            )
    
    def test_file_processor_basic(self):
        """Test 5: Testing básico del procesador de archivos"""
        start_time = time.time()
        test_name = "File Processor Basic"
        
        try:
            from services.file_processor_service import FileProcessorService
            processor = FileProcessorService()
            
            # Test encoding detection
            test_data = "numero,fecha_trafico,tipo_cdr\n573123456789,20240419080000,DATOS\n".encode('utf-8')
            encoding = processor._detect_encoding(test_data)
            
            # Test CSV reading
            df = processor._read_csv_robust(test_data, delimiter=',')
            
            # Test validation
            is_valid, errors = processor._validate_claro_cellular_columns(df)
            
            details = {
                'encoding_detected': encoding,
                'csv_rows_read': len(df) if df is not None else 0,
                'csv_columns': list(df.columns) if df is not None else [],
                'validation_success': is_valid,
                'validation_errors': errors
            }
            
            if not is_valid or len(df) == 0:
                self.log_test_result(
                    test_name, 'FAIL',
                    {**details, 'error': f'Validación falló: {errors}'},
                    time.time() - start_time
                )
            else:
                self.log_test_result(test_name, 'PASS', details, time.time() - start_time)
                
        except Exception as e:
            self.log_test_result(
                test_name, 'FAIL',
                {'error': str(e), 'traceback': traceback.format_exc()},
                time.time() - start_time
            )
    
    def test_real_csv_file_structure(self):
        """Test 6: Analizar estructura de archivo CSV real"""
        start_time = time.time()
        test_name = "Real CSV File Structure"
        
        if not self.csv_file.exists():
            self.log_test_result(
                test_name, 'SKIP',
                {'error': f'Archivo CSV no encontrado: {self.csv_file}'},
                time.time() - start_time
            )
            return
        
        try:
            from services.file_processor_service import FileProcessorService
            processor = FileProcessorService()
            
            # Read file
            with open(self.csv_file, 'rb') as f:
                file_bytes = f.read()
            
            file_size_mb = len(file_bytes) / (1024 * 1024)
            
            # Test encoding
            encoding = processor._detect_encoding(file_bytes)
            
            # Test CSV parsing (first 1000 lines for speed)
            limited_bytes = b'\n'.join(file_bytes.split(b'\n')[:1000])
            df = processor._read_csv_robust(limited_bytes, delimiter=',')
            
            # Test validation
            is_valid, errors = processor._validate_claro_cellular_columns(df)
            
            # Get data sample
            sample_data = []
            if df is not None and len(df) > 0:
                sample_data = df.head(3).to_dict('records')
            
            details = {
                'file_size_mb': round(file_size_mb, 2),
                'encoding_detected': encoding,
                'sample_rows_read': len(df) if df is not None else 0,
                'columns_found': list(df.columns) if df is not None else [],
                'validation_success': is_valid,
                'validation_errors': errors,
                'sample_data': sample_data
            }
            
            # Store performance metrics
            self.results['performance_metrics']['csv_analysis'] = {
                'file_size_mb': file_size_mb,
                'processing_time': time.time() - start_time,
                'encoding': encoding,
                'validation_success': is_valid
            }
            
            if not is_valid:
                self.log_test_result(
                    test_name, 'FAIL',
                    {**details, 'error': f'Estructura inválida: {errors}'},
                    time.time() - start_time
                )
            else:
                self.log_test_result(test_name, 'PASS', details, time.time() - start_time)
                
        except Exception as e:
            self.log_test_result(
                test_name, 'FAIL',
                {'error': str(e), 'traceback': traceback.format_exc()},
                time.time() - start_time
            )
    
    def test_excel_file_structure(self):
        """Test 7: Analizar estructura de archivo Excel real"""
        start_time = time.time()
        test_name = "Real Excel File Structure"
        
        if not self.xlsx_file.exists():
            self.log_test_result(
                test_name, 'SKIP',
                {'error': f'Archivo Excel no encontrado: {self.xlsx_file}'},
                time.time() - start_time
            )
            return
        
        try:
            from services.file_processor_service import FileProcessorService
            processor = FileProcessorService()
            
            # Read file
            with open(self.xlsx_file, 'rb') as f:
                file_bytes = f.read()
            
            file_size_mb = len(file_bytes) / (1024 * 1024)
            
            # Test Excel parsing
            df = processor._read_excel_robust(file_bytes)
            
            # Test validation
            is_valid, errors = processor._validate_claro_cellular_columns(df)
            
            # Get data sample
            sample_data = []
            if df is not None and len(df) > 0:
                sample_data = df.head(3).to_dict('records')
            
            details = {
                'file_size_mb': round(file_size_mb, 2),
                'rows_read': len(df) if df is not None else 0,
                'columns_found': list(df.columns) if df is not None else [],
                'validation_success': is_valid,
                'validation_errors': errors,
                'sample_data': sample_data
            }
            
            # Store performance metrics
            self.results['performance_metrics']['excel_analysis'] = {
                'file_size_mb': file_size_mb,
                'processing_time': time.time() - start_time,
                'validation_success': is_valid
            }
            
            if not is_valid:
                self.log_test_result(
                    test_name, 'FAIL',
                    {**details, 'error': f'Estructura inválida: {errors}'},
                    time.time() - start_time
                )
            else:
                self.log_test_result(test_name, 'PASS', details, time.time() - start_time)
                
        except Exception as e:
            self.log_test_result(
                test_name, 'FAIL',
                {'error': str(e), 'traceback': traceback.format_exc()},
                time.time() - start_time
            )
    
    def test_frontend_components_exist(self):
        """Test 8: Verificar que los componentes de frontend existen"""
        start_time = time.time()
        test_name = "Frontend Components"
        
        try:
            frontend_path = Path(__file__).parent / "Frontend"
            
            expected_components = [
                "components/operator-data/OperatorDataUpload.tsx",
                "components/operator-data/OperatorSheetsManager.tsx",
                "services/api.ts",
                "types.ts"
            ]
            
            component_status = {}
            for component in expected_components:
                file_path = frontend_path / component
                component_status[component] = {
                    'exists': file_path.exists(),
                    'size_kb': round(file_path.stat().st_size / 1024, 2) if file_path.exists() else 0
                }
            
            missing_components = [comp for comp, status in component_status.items() if not status['exists']]
            
            details = {
                'frontend_path': str(frontend_path),
                'expected_components': expected_components,
                'component_status': component_status,
                'missing_components': missing_components
            }
            
            if missing_components:
                self.log_test_result(
                    test_name, 'FAIL',
                    {**details, 'error': f'Componentes faltantes: {missing_components}'},
                    time.time() - start_time
                )
            else:
                self.log_test_result(test_name, 'PASS', details, time.time() - start_time)
                
        except Exception as e:
            self.log_test_result(
                test_name, 'FAIL',
                {'error': str(e), 'traceback': traceback.format_exc()},
                time.time() - start_time
            )
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Ejecutar todos los tests"""
        print("🔬 Iniciando Testing Suite Focalizada para CLARO...")
        print("-" * 80)
        
        # Core System Tests
        print("\n📊 SISTEMA CORE")
        self.test_database_exists()
        self.test_operator_schema_exists()
        
        # Service Tests
        print("\n⚙️ SERVICIOS BACKEND")
        self.test_file_processor_import()
        self.test_data_normalizer_basic()
        self.test_file_processor_basic()
        
        # File Tests
        print("\n📄 ANÁLISIS DE ARCHIVOS")
        self.test_real_csv_file_structure()
        self.test_excel_file_structure()
        
        # Frontend Tests
        print("\n🎨 FRONTEND")
        self.test_frontend_components_exist()
        
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
    suite = ClaroTestingSuiteFocused()
    
    try:
        results = suite.run_all_tests()
        
        # Generar reporte
        print("\n" + "=" * 80)
        print("📋 RESUMEN DE TESTING CLARO (FOCALIZADO)")
        print("=" * 80)
        print(f"Tests Ejecutados: {results['tests_executed']}")
        print(f"Tests Pasados: {results['tests_passed']}")
        print(f"Tests Fallidos: {results['tests_failed']}")
        print(f"Tasa de Éxito: {results['success_rate']:.1f}%")
        print(f"Duración Total: {results['total_duration']:.2f} segundos")
        
        if results['issues']:
            print(f"\n⚠️ ISSUES ENCONTRADOS: {len(results['issues'])}")
            for issue in results['issues']:
                print(f"  - {issue['test']}: {issue['details'].get('error', 'N/A')}")
        
        # Performance metrics
        if results['performance_metrics']:
            print(f"\n⚡ MÉTRICAS DE PERFORMANCE:")
            for metric, data in results['performance_metrics'].items():
                print(f"  - {metric}: {data}")
        
        # Guardar reporte
        report_path = Path(__file__).parent / f"claro_focused_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 Reporte guardado en: {report_path}")
        
        # Exit code basado en resultados
        if results['tests_failed'] > 0:
            print("\n⚠️ ALGUNOS TESTS FALLARON")
            return 1
        else:
            print("\n✅ TODOS LOS TESTS PASARON")
            return 0
            
    except Exception as e:
        print(f"\n💥 ERROR CRÍTICO EN TESTING SUITE: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())