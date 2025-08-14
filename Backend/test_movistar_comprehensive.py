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
        
        print("[OK] MovistarImplementationTester inicializado")
    
    def _log_test_result(self, test_name: str, success: bool, details: Optional[str] = None):
        """Log resultado de un test."""
        if success:
            self.results['tests_passed'] += 1
            status = "[PASS]"
            print(f"{status}: {test_name}")
        else:
            self.results['tests_failed'] += 1
            status = "[FAIL]"
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
                
                print(f"[OK] Limpieza completada: {cellular_deleted} registros celulares, {call_deleted} registros de llamadas eliminados")
                
        except Exception as e:
            print(f"[ERROR] Error en limpieza: {e}")
    
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
        print(f"Estado general: {'[EXITO]' if overall_success else '[FALLO]'}")
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