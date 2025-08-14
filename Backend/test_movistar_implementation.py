"""
KRONOS - Test Comprensivo para Implementación MOVISTAR
====================================================

Script de testing específico para validar el funcionamiento completo
del sistema de procesamiento de archivos del operador MOVISTAR.

Características del test:
- Validación de estructura de archivos reales
- Procesamiento de datos celulares
- Procesamiento de llamadas salientes
- Normalización de datos
- Inserción en base de datos
- Verificación de integridad

Autor: Sistema KRONOS
Versión: 1.0.0
"""

import sys
import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.file_processor_service import FileProcessorService
from services.data_normalizer_service import DataNormalizerService
from services.operator_data_service import OperatorDataService
from database.connection import get_db_connection
from utils.operator_logger import OperatorLogger


class MovistarImplementationTester:
    """
    Clase para testing comprensivo de la implementación MOVISTAR.
    """
    
    def __init__(self):
        """Inicializa el tester con dependencias."""
        self.file_processor = FileProcessorService()
        self.data_normalizer = DataNormalizerService()
        self.operator_service = OperatorDataService()
        self.logger = OperatorLogger()
        
        # Configuración de archivos de prueba
        self.test_files = {
            'datos_celulares': 'datatest/Movistar/jgd202410754_00007301_datos_ MOVISTAR.csv',
            'llamadas_salientes': 'datatest/Movistar/jgd202410754_07F08305_vozm_saliente_ MOVISTAR.csv'
        }
        
        # IDs de prueba
        self.test_mission_id = 'test-movistar-mission'
        self.test_user_id = 'test-user'
        
        # Contadores y resultados
        self.results = {
            'tests_passed': 0,
            'tests_failed': 0,
            'errors': []
        }
        
        print("✓ MovistarImplementationTester inicializado")
    
    def _log_test_result(self, test_name: str, success: bool, details: Optional[str] = None):
        """Log resultado de un test."""
        if success:
            self.results['tests_passed'] += 1
            status = "✓ PASSED"
            print(f"{status}: {test_name}")
        else:
            self.results['tests_failed'] += 1
            status = "✗ FAILED"
            print(f"{status}: {test_name}")
            if details:
                print(f"   Error: {details}")
                self.results['errors'].append(f"{test_name}: {details}")
    
    def test_file_accessibility(self) -> bool:
        """Test 1: Verificar que los archivos de prueba existen y son accesibles."""
        print("\n=== Test 1: Accesibilidad de Archivos ===")
        
        all_accessible = True
        
        for file_type, file_path in self.test_files.items():
            full_path = Path(file_path)
            if not full_path.exists():
                self._log_test_result(f"Archivo {file_type} existe", False, f"No encontrado: {full_path}")
                all_accessible = False
            else:
                file_size = full_path.stat().st_size
                self._log_test_result(f"Archivo {file_type} existe", True, f"Tamaño: {file_size} bytes")
        
        return all_accessible
    
    def test_file_structure_validation(self) -> bool:
        """Test 2: Validar estructura de archivos MOVISTAR."""
        print("\n=== Test 2: Validación de Estructura ===")
        
        all_valid = True
        
        # Test datos celulares
        try:
            with open(self.test_files['datos_celulares'], 'rb') as f:
                file_bytes = f.read()
            
            df = self.file_processor._read_csv_robust(file_bytes, delimiter=',')
            is_valid, errors = self.file_processor._validate_movistar_cellular_columns(df)
            
            self._log_test_result("Estructura datos celulares", is_valid, "; ".join(errors) if errors else None)
            if not is_valid:
                all_valid = False
                
        except Exception as e:
            self._log_test_result("Estructura datos celulares", False, str(e))
            all_valid = False
        
        # Test llamadas salientes
        try:
            with open(self.test_files['llamadas_salientes'], 'rb') as f:
                file_bytes = f.read()
            
            df = self.file_processor._read_csv_robust(file_bytes, delimiter=',')
            is_valid, errors = self.file_processor._validate_movistar_call_columns(df)
            
            self._log_test_result("Estructura llamadas salientes", is_valid, "; ".join(errors) if errors else None)
            if not is_valid:
                all_valid = False
                
        except Exception as e:
            self._log_test_result("Estructura llamadas salientes", False, str(e))
            all_valid = False
        
        return all_valid
    
    def test_data_cleaning(self) -> bool:
        """Test 3: Validar limpieza de datos."""
        print("\n=== Test 3: Limpieza de Datos ===")
        
        all_clean = True
        
        # Test limpieza datos celulares
        try:
            with open(self.test_files['datos_celulares'], 'rb') as f:
                file_bytes = f.read()
            
            df_raw = self.file_processor._read_csv_robust(file_bytes, delimiter=',')
            df_clean = self.file_processor._clean_movistar_cellular_data(df_raw)
            
            cleaning_success = len(df_clean) > 0 and len(df_clean) <= len(df_raw)
            self._log_test_result(
                "Limpieza datos celulares", 
                cleaning_success,
                f"Registros originales: {len(df_raw)}, limpios: {len(df_clean)}"
            )
            if not cleaning_success:
                all_clean = False
                
        except Exception as e:
            self._log_test_result("Limpieza datos celulares", False, str(e))
            all_clean = False
        
        # Test limpieza llamadas
        try:
            with open(self.test_files['llamadas_salientes'], 'rb') as f:
                file_bytes = f.read()
            
            df_raw = self.file_processor._read_csv_robust(file_bytes, delimiter=',')
            df_clean = self.file_processor._clean_movistar_call_data(df_raw)
            
            cleaning_success = len(df_clean) > 0 and len(df_clean) <= len(df_raw)
            self._log_test_result(
                "Limpieza llamadas salientes", 
                cleaning_success,
                f"Registros originales: {len(df_raw)}, limpios: {len(df_clean)}"
            )
            if not cleaning_success:
                all_clean = False
                
        except Exception as e:
            self._log_test_result("Limpieza llamadas salientes", False, str(e))
            all_clean = False
        
        return all_clean
    
    def test_data_normalization(self) -> bool:
        """Test 4: Validar normalización de datos."""
        print("\n=== Test 4: Normalización de Datos ===")
        
        all_normalized = True
        
        # Test normalización datos celulares
        try:
            with open(self.test_files['datos_celulares'], 'rb') as f:
                file_bytes = f.read()
            
            df = self.file_processor._read_csv_robust(file_bytes, delimiter=',')
            df_clean = self.file_processor._clean_movistar_cellular_data(df)
            
            if len(df_clean) > 0:
                # Tomar una muestra de registros para normalizar
                sample_records = df_clean.head(3).to_dict('records')
                normalized_count = 0
                
                for i, record in enumerate(sample_records):
                    normalized = self.data_normalizer.normalize_movistar_cellular_data(
                        record, f"test-file-{i}", self.test_mission_id
                    )
                    if normalized:
                        normalized_count += 1
                
                normalization_success = normalized_count == len(sample_records)
                self._log_test_result(
                    "Normalización datos celulares", 
                    normalization_success,
                    f"Normalizados: {normalized_count}/{len(sample_records)}"
                )
                if not normalization_success:
                    all_normalized = False
            else:
                self._log_test_result("Normalización datos celulares", False, "No hay registros limpios para normalizar")
                all_normalized = False
                
        except Exception as e:
            self._log_test_result("Normalización datos celulares", False, str(e))
            all_normalized = False
        
        # Test normalización llamadas
        try:
            with open(self.test_files['llamadas_salientes'], 'rb') as f:
                file_bytes = f.read()
            
            df = self.file_processor._read_csv_robust(file_bytes, delimiter=',')
            df_clean = self.file_processor._clean_movistar_call_data(df)
            
            if len(df_clean) > 0:
                # Tomar una muestra de registros para normalizar
                sample_records = df_clean.head(3).to_dict('records')
                normalized_count = 0
                
                for i, record in enumerate(sample_records):
                    normalized = self.data_normalizer.normalize_movistar_call_data_salientes(
                        record, f"test-file-call-{i}", self.test_mission_id
                    )
                    if normalized:
                        normalized_count += 1
                
                normalization_success = normalized_count == len(sample_records)
                self._log_test_result(
                    "Normalización llamadas salientes", 
                    normalization_success,
                    f"Normalizados: {normalized_count}/{len(sample_records)}"
                )
                if not normalization_success:
                    all_normalized = False
            else:
                self._log_test_result("Normalización llamadas salientes", False, "No hay registros limpios para normalizar")
                all_normalized = False
                
        except Exception as e:
            self._log_test_result("Normalización llamadas salientes", False, str(e))
            all_normalized = False
        
        return all_normalized
    
    def test_full_processing(self) -> bool:
        """Test 5: Validar procesamiento completo de archivos."""
        print("\n=== Test 5: Procesamiento Completo ===")
        
        all_processed = True
        
        # Test procesamiento datos celulares
        try:
            with open(self.test_files['datos_celulares'], 'rb') as f:
                file_bytes = f.read()
            
            file_name = Path(self.test_files['datos_celulares']).name
            result = self.file_processor.process_movistar_datos_por_celda(
                file_bytes, file_name, 'test-cellular-upload', self.test_mission_id
            )
            
            processing_success = result.get('success', False)
            records_processed = result.get('records_processed', 0)
            
            self._log_test_result(
                "Procesamiento completo datos celulares", 
                processing_success,
                f"Registros procesados: {records_processed}"
            )
            if not processing_success:
                all_processed = False
                
        except Exception as e:
            self._log_test_result("Procesamiento completo datos celulares", False, str(e))
            all_processed = False
        
        # Test procesamiento llamadas salientes
        try:
            with open(self.test_files['llamadas_salientes'], 'rb') as f:
                file_bytes = f.read()
            
            file_name = Path(self.test_files['llamadas_salientes']).name
            result = self.file_processor.process_movistar_llamadas_salientes(
                file_bytes, file_name, 'test-calls-upload', self.test_mission_id
            )
            
            processing_success = result.get('success', False)
            records_processed = result.get('records_processed', 0)
            
            self._log_test_result(
                "Procesamiento completo llamadas salientes", 
                processing_success,
                f"Registros procesados: {records_processed}"
            )
            if not processing_success:
                all_processed = False
                
        except Exception as e:
            self._log_test_result("Procesamiento completo llamadas salientes", False, str(e))
            all_processed = False
        
        return all_processed
    
    def test_database_integrity(self) -> bool:
        """Test 6: Verificar integridad de datos en base de datos."""
        print("\n=== Test 6: Integridad de Base de Datos ===")
        
        integrity_ok = True
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Verificar datos celulares insertados
                cursor.execute("""
                    SELECT COUNT(*) FROM operator_cellular_data 
                    WHERE operator = 'MOVISTAR' AND mission_id = ?
                """, (self.test_mission_id,))
                
                cellular_count = cursor.fetchone()[0]
                cellular_success = cellular_count > 0
                
                self._log_test_result(
                    "Datos celulares en DB", 
                    cellular_success,
                    f"Registros encontrados: {cellular_count}"
                )
                if not cellular_success:
                    integrity_ok = False
                
                # Verificar llamadas insertadas
                cursor.execute("""
                    SELECT COUNT(*) FROM operator_call_data 
                    WHERE operator = 'MOVISTAR' AND mission_id = ?
                """, (self.test_mission_id,))
                
                call_count = cursor.fetchone()[0]
                call_success = call_count > 0
                
                self._log_test_result(
                    "Datos de llamadas en DB", 
                    call_success,
                    f"Registros encontrados: {call_count}"
                )
                if not call_success:
                    integrity_ok = False
                
                # Verificar integridad de datos específicos MOVISTAR
                cursor.execute("""
                    SELECT COUNT(*) FROM operator_cellular_data 
                    WHERE operator = 'MOVISTAR' AND tecnologia IN ('LTE', '3G', 'GSM')
                """)
                
                tech_valid_count = cursor.fetchone()[0]
                tech_success = tech_valid_count > 0
                
                self._log_test_result(
                    "Tecnologías válidas", 
                    tech_success,
                    f"Registros con tecnología válida: {tech_valid_count}"
                )
                if not tech_success:
                    integrity_ok = False
                    
        except Exception as e:
            self._log_test_result("Verificación DB", False, str(e))
            integrity_ok = False
        
        return integrity_ok
    
    def cleanup_test_data(self):
        """Limpiar datos de prueba de la base de datos."""
        print("\n=== Limpieza de Datos de Prueba ===")
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Eliminar datos de prueba
                cursor.execute("""
                    DELETE FROM operator_cellular_data 
                    WHERE mission_id = ? OR file_upload_id LIKE 'test-%'
                """, (self.test_mission_id,))
                
                cellular_deleted = cursor.rowcount
                
                cursor.execute("""
                    DELETE FROM operator_call_data 
                    WHERE mission_id = ? OR file_upload_id LIKE 'test-%'
                """, (self.test_mission_id,))
                
                call_deleted = cursor.rowcount
                
                conn.commit()
                
                print(f"✓ Limpieza completada: {cellular_deleted} registros celulares, {call_deleted} registros de llamadas eliminados")
                
        except Exception as e:
            print(f"✗ Error en limpieza: {e}")
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Ejecutar todos los tests comprensivos."""
        print("\n" + "="*60)
        print("KRONOS - Test Comprensivo Implementación MOVISTAR")
        print("="*60)
        
        start_time = datetime.now()
        
        # Ejecutar tests en secuencia
        tests = [
            ("Accesibilidad de archivos", self.test_file_accessibility),
            ("Validación de estructura", self.test_file_structure_validation),
            ("Limpieza de datos", self.test_data_cleaning),
            ("Normalización de datos", self.test_data_normalization),
            ("Procesamiento completo", self.test_full_processing),
            ("Integridad de base de datos", self.test_database_integrity),
        ]
        
        overall_success = True
        for test_name, test_func in tests:
            try:
                success = test_func()
                if not success:
                    overall_success = False
            except Exception as e:
                self._log_test_result(test_name, False, f"Excepción: {str(e)}")
                overall_success = False
        
        # Limpiar datos de prueba
        self.cleanup_test_data()
        
        # Generar reporte final
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        report = {
            'success': overall_success,
            'tests_passed': self.results['tests_passed'],
            'tests_failed': self.results['tests_failed'],
            'total_tests': self.results['tests_passed'] + self.results['tests_failed'],
            'duration_seconds': duration,
            'errors': self.results['errors'],
            'timestamp': end_time.isoformat()
        }
        
        # Mostrar resumen final
        print("\n" + "="*60)
        print("RESUMEN FINAL")
        print("="*60)
        print(f"Estado general: {'✓ ÉXITO' if overall_success else '✗ FALLÓ'}")
        print(f"Tests pasados: {self.results['tests_passed']}")
        print(f"Tests fallidos: {self.results['tests_failed']}")
        print(f"Duración: {duration:.2f} segundos")
        
        if self.results['errors']:
            print(f"\nErrores encontrados ({len(self.results['errors'])}):")
            for error in self.results['errors'][:5]:  # Mostrar solo los primeros 5
                print(f"  - {error}")
            if len(self.results['errors']) > 5:
                print(f"  ... y {len(self.results['errors']) - 5} más")
        
        return report


def main():
    """Función principal de testing."""
    tester = MovistarImplementationTester()
    
    # Ejecutar todos los tests
    report = tester.run_all_tests()
    
    # Guardar reporte
    report_path = f"test_movistar_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\nReporte guardado en: {report_path}")
    
    # Exit code basado en el éxito
    return 0 if report['success'] else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
        self.assertEqual(validate_traffic_bytes(""), 0)
        
        # Tráfico inválido - negativo
        with self.assertRaises(ValidationError) as cm:
            validate_traffic_bytes(-1000)
        self.assertIn("no puede ser negativo", str(cm.exception))
        
        # Tráfico inválido - excede límite
        with self.assertRaises(ValidationError) as cm:
            validate_traffic_bytes(999999999999999)
        self.assertIn("límite máximo", str(cm.exception))
    
    def test_validate_movistar_technology(self):
        """Prueba validación de tecnología MOVISTAR"""
        # Tecnologías válidas
        self.assertEqual(validate_movistar_technology("LTE"), "LTE")
        self.assertEqual(validate_movistar_technology("3g"), "3G")
        self.assertEqual(validate_movistar_technology("5G"), "5G")
        
        # Tecnología inválida
        with self.assertRaises(ValidationError) as cm:
            validate_movistar_technology("INVALID_TECH")
        self.assertIn("debe ser uno de", str(cm.exception))
    
    def test_validate_movistar_provider(self):
        """Prueba validación de proveedor MOVISTAR"""
        # Proveedores válidos
        self.assertEqual(validate_movistar_provider("HUAWEI"), "HUAWEI")
        self.assertEqual(validate_movistar_provider("ericsson"), "ERICSSON")
        self.assertEqual(validate_movistar_provider("Nokia"), "NOKIA")
        
        # Proveedor válido pero no en lista predefinida
        self.assertEqual(validate_movistar_provider("CISCO"), "CISCO")
        
        # Proveedor inválido - muy largo
        with self.assertRaises(ValidationError) as cm:
            validate_movistar_provider("A" * 51)
        self.assertIn("no puede exceder 50 caracteres", str(cm.exception))
    
    def test_validate_movistar_datos_record(self):
        """Prueba validación completa de registro de datos MOVISTAR"""
        # Registro válido
        valid_record = {
            'numero_que_navega': '14014891373',
            'ruta_entrante': '01',
            'celda': '000073',
            'trafico_de_subida': 11438,
            'trafico_de_bajada': 12320,
            'fecha_hora_inicio_sesion': '20240419080341',
            'duracion': 5297,
            'tipo_tecnologia': '6',
            'fecha_hora_fin_sesion': '20240419093158',
            'departamento': 'BOGOTA D.C',
            'localidad': 'BOGOTA, D.C.',
            'region': 'BOGOTA',
            'latitud_n': 4.6305,
            'longitud_w': -74.0966,
            'proveedor': 'HUAWEI',
            'tecnologia': 'LTE',
            'descripcion': 'BOG0115 - CENTRO NARIÑO',
            'direccion': 'Diagonal 22 A # 43-65',
            'celda_': '000073-01'
        }
        
        result = validate_movistar_datos_record(valid_record)
        self.assertEqual(result['numero_que_navega'], '14014891373')
        self.assertEqual(result['tecnologia'], 'LTE')
        self.assertEqual(result['proveedor'], 'HUAWEI')
        self.assertIsInstance(result['fecha_hora_inicio_sesion'], datetime)
    
    def test_validate_movistar_llamadas_record(self):
        """Prueba validación completa de registro de llamadas MOVISTAR"""
        # Registro válido
        valid_record = {
            'numero_que_contesta': '3002398578',
            'serial_destino': '',
            'numero_que_marca': '3015468323',
            'serial_origen': '',
            'duracion': 25,
            'ruta_entrante': 33541,
            'numero_marcado': '3002398578',
            'ruta_saliente': 5,
            'transferencia': '',
            'fecha_hora_inicio_llamada': '20240418140744',
            'fecha_hora_fin_llamada': '20240418140809',
            'switch': '3160043001',
            'celda_origen': '07F083-05',
            'celda_destino': '',
            'departamento': 'BOGOTA D.C',
            'localidad': 'BOGOTA, D.C.',
            'region': 'BOGOTA',
            'latitud_n': 4.71573,
            'longitud_w': -74.1057,
            'proveedor': 'HUAWEI',
            'tecnologia': 'LTE',
            'descripcion': 'BOCHICA NORTE BOGOTA',
            'direccion': 'CALLE 86 BIS # 96G - 27 INTERIOR 101',
            'celda': '07F083-05',
            'azimut': 160
        }
        
        result = validate_movistar_llamadas_record(valid_record)
        self.assertEqual(result['numero_que_contesta'], '3002398578')
        self.assertEqual(result['numero_que_marca'], '3015468323')
        self.assertEqual(result['tecnologia'], 'LTE')
        self.assertEqual(result['azimut'], 160)


class TestMovistarProcessor(unittest.TestCase):
    """Pruebas para MovistarProcessor"""
    
    def setUp(self):
        self.processor = MovistarProcessor()
    
    def test_initialization(self):
        """Prueba inicialización del procesador"""
        self.assertEqual(self.processor.operator, 'MOVISTAR')
        
        file_types = self.processor.get_supported_file_types()
        self.assertIn('DATOS', file_types)
        self.assertIn('LLAMADAS_SALIENTES', file_types)
        self.assertNotIn('LLAMADAS_ENTRANTES', file_types)  # MOVISTAR solo tiene salientes
    
    def test_column_mapping(self):
        """Prueba mapeo de columnas específico de MOVISTAR"""
        # Crear DataFrame de prueba con columnas variadas
        test_data = {
            'numero_que_navega': ['14014891373'],
            'celda': ['000073'],
            'trafico_de_subida': [11438],
            'trafico_de_bajada': [12320],
            'latitud_n': [4.6305],
            'longitud_w': [-74.0966],
            'tecnologia': ['LTE']
        }
        df = pd.DataFrame(test_data)
        
        # Normalizar usando mapeo DATOS
        df_normalized = self.processor._normalize_column_names(df, self.processor.DATOS_COLUMN_MAPPING)
        
        # Verificar que las columnas se mantienen correctas
        expected_columns = ['numero_que_navega', 'celda', 'trafico_de_subida', 
                          'trafico_de_bajada', 'latitud_n', 'longitud_w', 'tecnologia']
        for col in expected_columns:
            self.assertIn(col, df_normalized.columns)
    
    def test_validate_datos_structure(self):
        """Prueba validación de estructura de datos MOVISTAR"""
        # DataFrame válido
        valid_data = {
            'numero_que_navega': ['14014891373'],
            'celda': ['000073'],
            'trafico_de_subida': [11438],
            'trafico_de_bajada': [12320],
            'fecha_hora_inicio_sesion': ['20240419080341'],
            'latitud_n': [4.6305],
            'longitud_w': [-74.0966],
            'tecnologia': ['LTE']
        }
        df_valid = pd.DataFrame(valid_data)
        
        result = self.processor._validate_datos_structure(df_valid)
        self.assertTrue(result['is_valid'])
        self.assertEqual(result['validation_type'], 'datos_movistar')
        self.assertEqual(len(result['missing_columns']), 0)
        
        # DataFrame inválido - falta columna requerida
        invalid_data = {
            'numero_que_navega': ['14014891373'],
            'celda': ['000073']
            # Faltan columnas requeridas
        }
        df_invalid = pd.DataFrame(invalid_data)
        
        result = self.processor._validate_llamadas_structure(df_invalid)
        self.assertFalse(result['is_valid'])
        self.assertGreater(len(result['missing_columns']), 0)
    
    def test_clean_data_methods(self):
        """Prueba métodos de limpieza de datos"""
        # Datos de prueba con valores problemáticos
        test_data = {
            'numero_que_navega': ['14014891373', None, ''],
            'celda': ['000073', 'ABC123', None],
            'trafico_de_subida': [11438, 'invalid', None],
            'latitud_n': [4.6305, 'invalid', None],
            'fecha_hora_inicio_sesion': ['20240419080341', None, 'invalid']
        }
        df_dirty = pd.DataFrame(test_data)
        
        # Limpiar datos
        df_clean = self.processor._clean_datos_dataframe(df_dirty)
        
        # Verificar que se eliminaron filas con datos críticos faltantes
        self.assertLess(len(df_clean), len(df_dirty))
        
        # Verificar que los datos numéricos se convirtieron correctamente
        self.assertTrue(pd.api.types.is_numeric_dtype(df_clean['trafico_de_subida']))


class TestMovistarIntegration(unittest.TestCase):
    """Pruebas de integración para MOVISTAR"""
    
    def test_operator_registry(self):
        """Prueba registro de MOVISTAR en el sistema"""
        # Verificar que MOVISTAR está soportado
        self.assertTrue(is_operator_supported('MOVISTAR'))
        
        # Obtener procesador
        processor = get_operator_processor('MOVISTAR')
        self.assertIsNotNone(processor)
        self.assertIsInstance(processor, MovistarProcessor)
        self.assertEqual(processor.operator, 'MOVISTAR')
    
    def test_operator_service_integration(self):
        """Prueba integración con OperatorService"""
        service = get_operator_service()
        
        # Obtener información de operadores soportados
        operators_info = service.get_supported_operators_info()
        
        # Verificar que MOVISTAR está incluido
        movistar_found = False
        for op_info in operators_info:
            if op_info['name'] == 'MOVISTAR':
                movistar_found = True
                self.assertTrue(op_info['is_available'])
                self.assertIn('DATOS', op_info['supported_file_types'])
                self.assertIn('LLAMADAS_SALIENTES', op_info['supported_file_types'])
                break
        
        self.assertTrue(movistar_found, "MOVISTAR no encontrado en operadores soportados")
    
    @patch('services.operator_processors.movistar_processor.get_database_manager')
    def test_specific_methods_exist(self, mock_db):
        """Prueba que los métodos específicos de MOVISTAR existen"""
        processor = MovistarProcessor()
        
        # Verificar métodos específicos
        self.assertTrue(hasattr(processor, 'get_movistar_data_summary'))
        self.assertTrue(hasattr(processor, 'delete_movistar_file'))
        self.assertTrue(callable(getattr(processor, 'get_movistar_data_summary')))
        self.assertTrue(callable(getattr(processor, 'delete_movistar_file')))


class TestMovistarSpecificFeatures(unittest.TestCase):
    """Pruebas para características específicas de MOVISTAR"""
    
    def test_geolocation_support(self):
        """Prueba soporte de geolocalización"""
        processor = MovistarProcessor()
        
        # Crear datos de prueba con coordenadas
        test_row = pd.Series({
            'latitud_n': 4.6305,
            'longitud_w': -74.0966,
            'tecnologia': 'LTE',
            'proveedor': 'HUAWEI'
        })
        
        # Construir datos específicos
        specific_data = processor._build_movistar_specific_data(test_row, 'datos')
        
        # Verificar que incluye información de geolocalización
        import json
        data_dict = json.loads(specific_data)
        self.assertTrue(data_dict['has_geolocation'])
        self.assertEqual(data_dict['operator'], 'MOVISTAR')
    
    def test_only_outgoing_calls(self):
        """Prueba que MOVISTAR solo maneja llamadas salientes"""
        processor = MovistarProcessor()
        file_types = processor.get_supported_file_types()
        
        # Verificar que solo hay LLAMADAS_SALIENTES
        self.assertIn('LLAMADAS_SALIENTES', file_types)
        self.assertNotIn('LLAMADAS_ENTRANTES', file_types)
    
    def test_traffic_separation(self):
        """Prueba separación de tráfico de subida y bajada"""
        # Datos de prueba
        record = {
            'numero_que_navega': '14014891373',
            'celda': '000073',
            'trafico_de_subida': 11438,
            'trafico_de_bajada': 12320,
            'fecha_hora_inicio_sesion': '20240419080341',
            'departamento': 'BOGOTA D.C',
            'localidad': 'BOGOTA, D.C.',
            'region': 'BOGOTA',
            'latitud_n': 4.6305,
            'longitud_w': -74.0966,
            'proveedor': 'HUAWEI',
            'tecnologia': 'LTE'
        }
        
        validated = validate_movistar_datos_record(record)
        
        # Verificar que se mantienen ambos tráficos
        self.assertEqual(validated['trafico_de_subida'], 11438)
        self.assertEqual(validated['trafico_de_bajada'], 12320)
        self.assertNotEqual(validated['trafico_de_subida'], validated['trafico_de_bajada'])


def run_movistar_tests():
    """Ejecuta todas las pruebas de MOVISTAR"""
    print("="*80)
    print("KRONOS - PRUEBAS DE IMPLEMENTACIÓN MOVISTAR")
    print("="*80)
    
    # Crear suite de pruebas
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Agregar clases de prueba
    test_classes = [
        TestMovistarValidators,
        TestMovistarProcessor, 
        TestMovistarIntegration,
        TestMovistarSpecificFeatures
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Ejecutar pruebas
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Resumen
    print("\n" + "="*80)
    print("RESUMEN DE PRUEBAS MOVISTAR")
    print("="*80)
    print(f"Total de pruebas ejecutadas: {result.testsRun}")
    print(f"Pruebas exitosas: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Pruebas fallidas: {len(result.failures)}")
    print(f"Errores: {len(result.errors)}")
    
    if result.failures:
        print("\nFALLOS:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORES:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_movistar_tests()
    sys.exit(0 if success else 1)