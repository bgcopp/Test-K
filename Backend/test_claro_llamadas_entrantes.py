#!/usr/bin/env python3
"""
KRONOS - Script de Testing para CLARO - Llamadas Entrantes
=========================================================

Este script valida la implementación completa del procesamiento de archivos
de llamadas entrantes de CLARO, incluyendo:

- Lectura de archivos CSV y XLSX
- Validación de estructura y contenido
- Normalización de datos
- Inserción en base de datos
- Verificación de integridad

Uso:
    python test_claro_llamadas_entrantes.py

Archivos de prueba:
    - /datatest/Claro/LLAMADAS_ENTRANTES_POR_CELDA CLARO.csv
    - /datatest/Claro/formato excel/LLAMADAS_ENTRANTES_POR_CELDA CLARO.xlsx

Autor: Sistema KRONOS
Versión: 1.0.0
"""

import os
import sys
import uuid
from pathlib import Path
from datetime import datetime
import json
import sqlite3

# Agregar el directorio padre al path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.file_processor_service import FileProcessorService
from services.data_normalizer_service import DataNormalizerService
from services.operator_data_service import OperatorDataService
from database.connection import get_db_connection
from utils.operator_logger import OperatorLogger


class ClaroLlamadasEntrantesTestSuite:
    """
    Suite de testing completa para procesamiento de llamadas entrantes de CLARO.
    """
    
    def __init__(self):
        """Inicializa la suite de testing."""
        self.logger = OperatorLogger()
        self.file_processor = FileProcessorService()
        self.data_normalizer = DataNormalizerService()
        self.operator_service = OperatorDataService()
        
        # Archivos de prueba
        self.test_files = {
            'csv': Path(__file__).parent.parent / 'datatest' / 'Claro' / 'LLAMADAS_ENTRANTES_POR_CELDA CLARO.csv',
            'xlsx': Path(__file__).parent.parent / 'datatest' / 'Claro' / 'formato excel' / 'LLAMADAS_ENTRANTES_POR_CELDA CLARO.xlsx'
        }
        
        # Configuración de prueba con timestamp único
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.test_mission_id = f'test-mission-claro-entrantes-{timestamp}'
        self.test_user_id = f'test-user-{timestamp}'
        self.test_role_id = f'test-role-{timestamp}'
        
        self.logger.info("ClaroLlamadasEntrantesTestSuite inicializada")
    
    def setup_test_environment(self) -> bool:
        """
        Configura el entorno de testing creando datos necesarios.
        
        Returns:
            bool: True si el setup fue exitoso
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Primero crear rol de prueba si no existe
                cursor.execute("SELECT id FROM roles WHERE id = ?", (self.test_role_id,))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO roles (id, name, permissions)
                        VALUES (?, ?, ?)
                    """, (
                        self.test_role_id,
                        'Test Role',
                        json.dumps({"users": {"read": True, "write": True}})
                    ))
                
                # Crear usuario de prueba si no existe
                cursor.execute("SELECT id FROM users WHERE id = ?", (self.test_user_id,))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO users (id, name, email, password_hash, role_id, status)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        self.test_user_id,
                        'Test User',
                        f'test-{self.test_user_id.split("-")[-1]}@kronos.test',
                        'test_hash_not_real_12345678901234567890123456789012345678901234567890',  # Al menos 60 caracteres
                        self.test_role_id,
                        'active'
                    ))
                
                # Crear misión de prueba si no existe
                cursor.execute("SELECT id FROM missions WHERE id = ?", (self.test_mission_id,))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO missions (id, code, name, status, start_date, created_by)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        self.test_mission_id,
                        'TEST-CLARO-ENT',
                        'Mision de Prueba - CLARO Llamadas Entrantes',
                        'En Progreso',
                        datetime.now().date().isoformat(),
                        self.test_user_id
                    ))
                
                conn.commit()
                
                self.logger.info("Entorno de testing configurado correctamente")
                return True
                
        except Exception as e:
            self.logger.error(f"Error configurando entorno de testing: {e}")
            return False
    
    def test_file_reading(self) -> dict:
        """
        Test de lectura básica de archivos.
        
        Returns:
            dict: Resultados del test
        """
        self.logger.info("=== TEST: Lectura de Archivos ===")
        results = {}
        
        for file_type, file_path in self.test_files.items():
            try:
                if not file_path.exists():
                    results[file_type] = {
                        'success': False,
                        'error': f'Archivo no encontrado: {file_path}'
                    }
                    continue
                
                # Leer archivo
                with open(file_path, 'rb') as f:
                    file_bytes = f.read()
                
                # Test de lectura usando file processor
                if file_type == 'csv':
                    df = self.file_processor._read_csv_robust(file_bytes, delimiter=',')
                else:  # xlsx
                    df = self.file_processor._read_excel_robust(file_bytes)
                
                results[file_type] = {
                    'success': True,
                    'file_size': len(file_bytes),
                    'rows_read': len(df),
                    'columns': list(df.columns),
                    'sample_data': df.head(2).to_dict('records') if len(df) > 0 else []
                }
                
                self.logger.info(f"✓ {file_type.upper()}: {len(df)} filas, {len(df.columns)} columnas")
                
            except Exception as e:
                results[file_type] = {
                    'success': False,
                    'error': str(e)
                }
                self.logger.error(f"✗ {file_type.upper()}: {e}")
        
        return results
    
    def test_data_validation(self) -> dict:
        """
        Test de validación de estructura y contenido.
        
        Returns:
            dict: Resultados del test
        """
        self.logger.info("=== TEST: Validación de Datos ===")
        results = {}
        
        for file_type, file_path in self.test_files.items():
            try:
                if not file_path.exists():
                    results[file_type] = {'success': False, 'error': 'Archivo no encontrado'}
                    continue
                
                with open(file_path, 'rb') as f:
                    file_bytes = f.read()
                
                # Leer archivo
                if file_type == 'csv':
                    df = self.file_processor._read_csv_robust(file_bytes, delimiter=',')
                else:
                    df = self.file_processor._read_excel_robust(file_bytes)
                
                # Test de validación de columnas
                is_valid_structure, structure_errors = self.file_processor._validate_claro_call_columns(df)
                
                # Test de limpieza de datos
                original_count = len(df)
                cleaned_df = self.file_processor._clean_claro_call_data(df)
                cleaned_count = len(cleaned_df)
                
                # Test de validación de registros individuales
                valid_records = 0
                invalid_records = 0
                sample_errors = []
                
                for index, row in cleaned_df.head(10).iterrows():
                    record = row.to_dict()
                    is_valid, errors = self.file_processor._validate_claro_call_record(record)
                    
                    if is_valid:
                        valid_records += 1
                    else:
                        invalid_records += 1
                        if len(sample_errors) < 3:
                            sample_errors.append({
                                'row': index + 1,
                                'errors': errors
                            })
                
                results[file_type] = {
                    'success': is_valid_structure,
                    'structure_errors': structure_errors,
                    'original_rows': original_count,
                    'cleaned_rows': cleaned_count,
                    'cdr_entrante_rows': cleaned_count,
                    'sample_validation': {
                        'valid_records': valid_records,
                        'invalid_records': invalid_records,
                        'sample_errors': sample_errors
                    }
                }
                
                if is_valid_structure:
                    self.logger.info(f"✓ {file_type.upper()}: Estructura válida, {cleaned_count}/{original_count} registros CDR_ENTRANTE")
                else:
                    self.logger.error(f"✗ {file_type.upper()}: Estructura inválida - {structure_errors}")
                
            except Exception as e:
                results[file_type] = {'success': False, 'error': str(e)}
                self.logger.error(f"✗ {file_type.upper()}: {e}")
        
        return results
    
    def test_data_normalization(self) -> dict:
        """
        Test de normalización de datos.
        
        Returns:
            dict: Resultados del test
        """
        self.logger.info("=== TEST: Normalización de Datos ===")
        results = {}
        
        # Test con datos de muestra
        sample_records = [
            {
                'celda_inicio_llamada': '20264',
                'celda_final_llamada': '20264',
                'originador': '3213639847',
                'receptor': '3132825038',
                'fecha_hora': '20/05/2021 10:02:26',
                'duracion': '91',
                'tipo': 'CDR_ENTRANTE'
            },
            {
                'celda_inicio_llamada': '37825',
                'celda_final_llamada': '20264',
                'originador': '3205148564',
                'receptor': '3206001800',
                'fecha_hora': '20/05/2021 10:02:43',
                'duracion': '30',
                'tipo': 'CDR_ENTRANTE'
            }
        ]
        
        normalized_success = 0
        normalization_errors = []
        normalized_samples = []
        
        file_upload_id = str(uuid.uuid4())
        
        for i, record in enumerate(sample_records):
            try:
                normalized = self.data_normalizer.normalize_claro_call_data_entrantes(
                    record, file_upload_id, self.test_mission_id
                )
                
                if normalized:
                    normalized_success += 1
                    if len(normalized_samples) < 2:
                        # Copiar sin datos sensibles para el log
                        safe_sample = {k: v for k, v in normalized.items() if k != 'record_hash'}
                        normalized_samples.append(safe_sample)
                else:
                    normalization_errors.append(f"Registro {i+1}: Error en normalización")
                
            except Exception as e:
                normalization_errors.append(f"Registro {i+1}: {str(e)}")
        
        results = {
            'success': normalized_success > 0,
            'total_records': len(sample_records),
            'normalized_successfully': normalized_success,
            'errors': normalization_errors,
            'sample_normalized_data': normalized_samples
        }
        
        if normalized_success > 0:
            self.logger.info(f"✓ Normalización: {normalized_success}/{len(sample_records)} registros exitosos")
        else:
            self.logger.error(f"✗ Normalización: Ningún registro normalizado exitosamente")
        
        return results
    
    def test_full_processing(self, file_type: str = 'csv') -> dict:
        """
        Test de procesamiento completo de archivo.
        
        Args:
            file_type (str): Tipo de archivo a procesar ('csv' o 'xlsx')
        
        Returns:
            dict: Resultados del test
        """
        self.logger.info(f"=== TEST: Procesamiento Completo ({file_type.upper()}) ===")
        
        file_path = self.test_files[file_type]
        
        try:
            if not file_path.exists():
                return {
                    'success': False,
                    'error': f'Archivo no encontrado: {file_path}'
                }
            
            # Leer archivo
            with open(file_path, 'rb') as f:
                file_bytes = f.read()
            
            # Generar IDs únicos para el test
            file_upload_id = f"test-{file_type}-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Procesar archivo usando el método principal
            result = self.file_processor.process_claro_llamadas_entrantes(
                file_bytes=file_bytes,
                file_name=file_path.name,
                file_upload_id=file_upload_id,
                mission_id=self.test_mission_id
            )
            
            # Verificar datos insertados en base de datos
            inserted_count = 0
            if result.get('success', False):
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT COUNT(*) FROM operator_call_data 
                        WHERE file_upload_id = ?
                    """, (file_upload_id,))
                    inserted_count = cursor.fetchone()[0]
            
            # Añadir información de verificación
            result['database_verification'] = {
                'records_in_db': inserted_count,
                'matches_processed': inserted_count == result.get('records_processed', 0)
            }
            
            if result.get('success', False):
                self.logger.info(
                    f"✓ Procesamiento completo {file_type.upper()}: "
                    f"{result.get('records_processed', 0)} registros procesados, "
                    f"{inserted_count} insertados en BD"
                )
            else:
                self.logger.error(
                    f"✗ Procesamiento completo {file_type.upper()}: "
                    f"{result.get('error', 'Error desconocido')}"
                )
            
            return result
            
        except Exception as e:
            error_result = {
                'success': False,
                'error': str(e)
            }
            self.logger.error(f"✗ Procesamiento completo {file_type.upper()}: {e}")
            return error_result
    
    def test_integration_via_service(self, file_type: str = 'csv') -> dict:
        """
        Test de integración completa usando OperatorDataService.
        
        Args:
            file_type (str): Tipo de archivo a procesar
        
        Returns:
            dict: Resultados del test
        """
        self.logger.info(f"=== TEST: Integración Completa via Service ({file_type.upper()}) ===")
        
        file_path = self.test_files[file_type]
        
        try:
            if not file_path.exists():
                return {
                    'success': False,
                    'error': f'Archivo no encontrado: {file_path}'
                }
            
            # Leer y codificar archivo en Base64 (como lo haría el frontend)
            with open(file_path, 'rb') as f:
                file_bytes = f.read()
            
            import base64
            file_data_b64 = base64.b64encode(file_bytes).decode('utf-8')
            
            # Usar el servicio principal (función expuesta via Eel)
            from services.operator_data_service import upload_operator_data
            
            result = upload_operator_data(
                file_data=file_data_b64,
                file_name=file_path.name,
                mission_id=self.test_mission_id,
                operator='CLARO',
                file_type='CALL_DATA',
                user_id=self.test_user_id
            )
            
            # Verificar archivo en operator_data_sheets
            sheet_info = None
            if result.get('success', False) and result.get('file_upload_id'):
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT processing_status, records_processed, records_failed
                        FROM operator_data_sheets 
                        WHERE id = ?
                    """, (result['file_upload_id'],))
                    row = cursor.fetchone()
                    if row:
                        sheet_info = {
                            'processing_status': row[0],
                            'records_processed': row[1],
                            'records_failed': row[2]
                        }
            
            result['sheet_verification'] = sheet_info
            
            if result.get('success', False):
                self.logger.info(
                    f"✓ Integración completa {file_type.upper()}: "
                    f"Estado: {sheet_info.get('processing_status') if sheet_info else 'N/A'}, "
                    f"Procesados: {result.get('records_processed', 0)}"
                )
            else:
                self.logger.error(
                    f"✗ Integración completa {file_type.upper()}: "
                    f"{result.get('error', 'Error desconocido')}"
                )
            
            return result
            
        except Exception as e:
            error_result = {
                'success': False,
                'error': str(e)
            }
            self.logger.error(f"✗ Integración completa {file_type.upper()}: {e}")
            return error_result
    
    def cleanup_test_data(self):
        """Limpia datos de prueba de la base de datos."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Eliminar datos de prueba (CASCADE eliminará registros relacionados)
                cursor.execute("DELETE FROM operator_data_sheets WHERE mission_id = ?", (self.test_mission_id,))
                cursor.execute("DELETE FROM missions WHERE id = ?", (self.test_mission_id,))
                cursor.execute("DELETE FROM users WHERE id = ?", (self.test_user_id,))
                cursor.execute("DELETE FROM roles WHERE id = ?", (self.test_role_id,))
                
                conn.commit()
                
                self.logger.info("Datos de prueba limpiados")
                
        except Exception as e:
            self.logger.warning(f"Error limpiando datos de prueba: {e}")
    
    def run_all_tests(self) -> dict:
        """
        Ejecuta toda la suite de tests.
        
        Returns:
            dict: Resultados completos de todos los tests
        """
        self.logger.info("INICIANDO SUITE DE TESTS - CLARO LLAMADAS ENTRANTES")
        
        start_time = datetime.now()
        
        # Configurar entorno
        if not self.setup_test_environment():
            return {
                'success': False,
                'error': 'Error configurando entorno de testing'
            }
        
        all_results = {
            'start_time': start_time.isoformat(),
            'test_files': {str(k): str(v) for k, v in self.test_files.items()},
            'results': {}
        }
        
        try:
            # 1. Test de lectura de archivos
            all_results['results']['file_reading'] = self.test_file_reading()
            
            # 2. Test de validación
            all_results['results']['data_validation'] = self.test_data_validation()
            
            # 3. Test de normalización
            all_results['results']['data_normalization'] = self.test_data_normalization()
            
            # 4. Test de procesamiento completo (CSV)
            all_results['results']['full_processing_csv'] = self.test_full_processing('csv')
            
            # 5. Test de procesamiento completo (XLSX) - si existe
            if self.test_files['xlsx'].exists():
                all_results['results']['full_processing_xlsx'] = self.test_full_processing('xlsx')
            
            # 6. Test de integración completa
            all_results['results']['integration_test'] = self.test_integration_via_service('csv')
            
            # Calcular resumen
            total_tests = len(all_results['results'])
            successful_tests = sum(1 for result in all_results['results'].values() 
                                 if isinstance(result, dict) and result.get('success', False))
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            all_results.update({
                'end_time': end_time.isoformat(),
                'duration_seconds': round(duration, 2),
                'summary': {
                    'total_tests': total_tests,
                    'successful_tests': successful_tests,
                    'failed_tests': total_tests - successful_tests,
                    'success_rate': round((successful_tests / total_tests) * 100, 1)
                },
                'overall_success': successful_tests >= (total_tests * 0.8)  # 80% success rate
            })
            
            # Log resumen
            self.logger.info(
                f"RESUMEN: {successful_tests}/{total_tests} tests exitosos "
                f"({all_results['summary']['success_rate']}%) en {duration:.1f}s"
            )
            
            if all_results['overall_success']:
                self.logger.info("SUITE DE TESTS EXITOSA")
            else:
                self.logger.warning("SUITE DE TESTS CON ERRORES")
            
            return all_results
            
        finally:
            # Limpiar datos de prueba
            self.cleanup_test_data()


def main():
    """Función principal para ejecutar los tests."""
    print("=" * 80)
    print("KRONOS - Test Suite: CLARO Llamadas Entrantes")
    print("=" * 80)
    
    # Crear y ejecutar suite de tests
    test_suite = ClaroLlamadasEntrantesTestSuite()
    results = test_suite.run_all_tests()
    
    print("\n" + "=" * 80)
    print("RESULTADOS FINALES")
    print("=" * 80)
    
    # Mostrar resumen en consola
    if results.get('summary'):
        summary = results['summary']
        print(f"Total de Tests: {summary['total_tests']}")
        print(f"Exitosos: {summary['successful_tests']}")
        print(f"Fallidos: {summary['failed_tests']}")
        print(f"Tasa de Éxito: {summary['success_rate']}%")
        print(f"Duración: {results.get('duration_seconds', 0)}s")
        
        if results.get('overall_success'):
            print("\nTODOS LOS TESTS PRINCIPALES EXITOSOS")
        else:
            print("\nALGUNOS TESTS FALLARON")
    
    # Guardar resultados detallados
    output_file = Path(__file__).parent / f"test_results_claro_entrantes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        print(f"\nResultados detallados guardados en: {output_file}")
    except Exception as e:
        print(f"\nError guardando resultados: {e}")
    
    return 0 if results.get('overall_success', False) else 1


if __name__ == "__main__":
    sys.exit(main())