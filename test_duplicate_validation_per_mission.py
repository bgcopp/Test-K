#!/usr/bin/env python3
"""
KRONOS - Test de Validación de Duplicados por Misión
====================================================

Este script prueba exhaustivamente la nueva lógica de validación de archivos duplicados
que ahora opera por misión en lugar de globalmente.

Casos de prueba:
1. Migración automática de schema
2. Archivo duplicado en la misma misión (debe fallar)
3. Mismo archivo en misiones diferentes (debe funcionar)
4. Archivos diferentes en la misma misión (debe funcionar)
5. Verificación de constraints de base de datos
6. Mensajes de error específicos por misión

Fecha: 2025-08-13
Autor: Testing Engineer - Claude Code
"""

import os
import sys
import json
import base64
import hashlib
import sqlite3
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

# Agregar el directorio Backend al path
backend_path = os.path.join(os.path.dirname(__file__), 'Backend')
sys.path.insert(0, backend_path)

# Imports del sistema KRONOS
from database.connection import get_db_connection
from services.operator_data_service import upload_operator_data, OperatorDataService

class DuplicateValidationTester:
    """
    Clase principal para testing de validación de duplicados por misión.
    """
    
    def __init__(self):
        self.test_results = []
        self.test_db_path = None
        self.setup_test_environment()
        
    def setup_test_environment(self):
        """Configura el entorno de testing con base de datos temporal."""
        # Crear directorio temporal para testing
        self.temp_dir = tempfile.mkdtemp(prefix='kronos_test_duplicates_')
        self.test_db_path = os.path.join(self.temp_dir, 'test_duplicates.db')
        
        # Configurar variable de entorno para usar BD de testing
        os.environ['KRONOS_DB_PATH'] = self.test_db_path
        
        print(f"[CONFIG] Entorno de testing configurado:")
        print(f"   BD Testing: {self.test_db_path}")
        print(f"   Directorio temporal: {self.temp_dir}")
        
        # Inicializar base de datos con schema básico
        self.init_test_database()
        
    def init_test_database(self):
        """Inicializa la base de datos de testing con datos mínimos."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Crear tablas básicas (missions, users, roles)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS roles (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL UNIQUE,
                        permissions TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        email TEXT NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL,
                        role_id TEXT NOT NULL,
                        status TEXT DEFAULT 'active',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (role_id) REFERENCES roles(id)
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS missions (
                        id TEXT PRIMARY KEY,
                        code TEXT NOT NULL UNIQUE,
                        name TEXT NOT NULL,
                        description TEXT,
                        status TEXT DEFAULT 'Planificación',
                        start_date DATE NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Crear tabla operator_data_sheets con constraint ANTIGUO (global unique)
                # para simular estado pre-migración
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS operator_data_sheets (
                        id TEXT PRIMARY KEY NOT NULL,
                        mission_id TEXT NOT NULL,
                        file_name TEXT NOT NULL,
                        file_size_bytes INTEGER NOT NULL,
                        file_checksum TEXT NOT NULL UNIQUE,  -- CONSTRAINT ANTIGUO
                        file_type TEXT NOT NULL,
                        operator TEXT NOT NULL,
                        operator_file_format TEXT NOT NULL DEFAULT 'CLARO_CELLULAR_DATA_CSV',
                        processing_status TEXT NOT NULL DEFAULT 'PENDING',
                        processing_start_time TIMESTAMP,
                        processing_end_time TIMESTAMP,
                        records_processed INTEGER DEFAULT 0,
                        records_failed INTEGER DEFAULT 0,
                        error_details TEXT,
                        uploaded_by TEXT NOT NULL,
                        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CHECK (processing_status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')),
                        CHECK (file_type IN ('CELLULAR_DATA', 'CALL_DATA')),
                        CHECK (operator IN ('CLARO', 'MOVISTAR', 'TIGO', 'WOM')),
                        FOREIGN KEY (mission_id) REFERENCES missions(id) ON DELETE CASCADE
                    )
                """)
                
                # Crear datos de testing
                test_role_id = 'role-admin-test'
                test_user_id = 'user-test-001'
                test_mission_a_id = 'mission-test-a'
                test_mission_b_id = 'mission-test-b'
                
                cursor.execute("""
                    INSERT OR IGNORE INTO roles (id, name, permissions) 
                    VALUES (?, 'Admin Test', '{}')
                """, (test_role_id,))
                
                cursor.execute("""
                    INSERT OR IGNORE INTO users (id, name, email, password_hash, role_id) 
                    VALUES (?, 'Usuario Test', 'test@kronos.com', 'hash_placeholder', ?)
                """, (test_user_id, test_role_id))
                
                cursor.execute("""
                    INSERT OR IGNORE INTO missions (id, code, name, start_date) 
                    VALUES (?, 'MISSION-A', 'Misión Test A', '2025-01-01')
                """, (test_mission_a_id,))
                
                cursor.execute("""
                    INSERT OR IGNORE INTO missions (id, code, name, start_date) 
                    VALUES (?, 'MISSION-B', 'Misión Test B', '2025-01-01')
                """, (test_mission_b_id,))
                
                conn.commit()
                
                # Guardar IDs para testing
                self.test_user_id = test_user_id
                self.test_mission_a_id = test_mission_a_id
                self.test_mission_b_id = test_mission_b_id
                
                print("[OK] Base de datos de testing inicializada")
                
        except Exception as e:
            print(f"[ERROR] Error inicializando BD de testing: {e}")
            raise
    
    def create_test_file_data(self, content_variant="default"):
        """Crea datos de archivo de testing en formato CSV."""
        if content_variant == "default":
            csv_content = """numero_telefono,fecha_hora_inicio,fecha_hora_fin,celda_id,lac_tac,trafico_subida_bytes,trafico_bajada_bytes
573001234567,2025-01-01 10:00:00,2025-01-01 10:05:00,CLARO_CELL_001,1001,1024000,2048000
573001234568,2025-01-01 11:00:00,2025-01-01 11:03:00,CLARO_CELL_002,1002,512000,1024000
573001234569,2025-01-01 12:00:00,2025-01-01 12:07:00,CLARO_CELL_003,1003,2048000,4096000"""
        elif content_variant == "different":
            csv_content = """numero_telefono,fecha_hora_inicio,fecha_hora_fin,celda_id,lac_tac,trafico_subida_bytes,trafico_bajada_bytes
573009876543,2025-01-02 14:00:00,2025-01-02 14:05:00,CLARO_CELL_004,1004,3072000,6144000
573009876544,2025-01-02 15:00:00,2025-01-02 15:03:00,CLARO_CELL_005,1005,1536000,3072000"""
        else:
            raise ValueError(f"Variante de contenido no válida: {content_variant}")
        
        # Codificar en Base64
        file_bytes = csv_content.encode('utf-8')
        file_base64 = base64.b64encode(file_bytes).decode('utf-8')
        
        # Calcular checksum para verificación
        checksum = hashlib.sha256(file_bytes).hexdigest()
        
        return {
            'file_data': file_base64,
            'file_bytes': file_bytes,
            'checksum': checksum,
            'size': len(file_bytes)
        }
    
    def run_test(self, test_name, test_function):
        """Ejecuta un test individual y registra el resultado."""
        print(f"\n[TEST] Ejecutando: {test_name}")
        print("=" * 60)
        
        try:
            start_time = datetime.now()
            result = test_function()
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            test_result = {
                'test_name': test_name,
                'status': 'PASSED' if result['success'] else 'FAILED',
                'duration_seconds': duration,
                'details': result,
                'timestamp': start_time.isoformat()
            }
            
            self.test_results.append(test_result)
            
            if result['success']:
                print(f"[PASS] {test_name} - PASSED ({duration:.2f}s)")
            else:
                print(f"[FAIL] {test_name} - FAILED ({duration:.2f}s)")
                print(f"   Error: {result.get('error', 'Unknown error')}")
                
            return result
            
        except Exception as e:
            error_result = {
                'test_name': test_name,
                'status': 'ERROR',
                'duration_seconds': 0,
                'details': {'success': False, 'error': str(e)},
                'timestamp': datetime.now().isoformat()
            }
            self.test_results.append(error_result)
            print(f"[ERROR] {test_name} - ERROR: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_1_schema_migration(self):
        """Test 1: Verificar migración automática de schema."""
        try:
            # Verificar estado inicial (constraint global)
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT sql FROM sqlite_master 
                    WHERE type='table' AND name='operator_data_sheets'
                """)
                
                initial_schema = cursor.fetchone()[0]
                has_global_unique = 'file_checksum TEXT NOT NULL UNIQUE' in initial_schema
            
            if not has_global_unique:
                return {
                    'success': False,
                    'error': 'Estado inicial incorrecto: no se encontró constraint global'
                }
            
            # Inicializar servicio (debe ejecutar migración)
            service = OperatorDataService()
            
            # Verificar estado post-migración
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT sql FROM sqlite_master 
                    WHERE type='table' AND name='operator_data_sheets'
                """)
                
                migrated_schema = cursor.fetchone()[0]
                has_mission_unique = 'UNIQUE (file_checksum, mission_id)' in migrated_schema
                has_global_unique_after = 'file_checksum TEXT NOT NULL UNIQUE' in migrated_schema
            
            return {
                'success': has_mission_unique and not has_global_unique_after,
                'details': {
                    'initial_global_unique': has_global_unique,
                    'final_mission_unique': has_mission_unique,
                    'final_global_unique': has_global_unique_after,
                    'migration_applied': has_mission_unique and not has_global_unique_after
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_2_duplicate_same_mission(self):
        """Test 2: Archivo duplicado en la misma misión (debe fallar)."""
        try:
            file_data = self.create_test_file_data("default")
            
            # Primera carga (debe funcionar)
            result1 = upload_operator_data(
                file_data=file_data['file_data'],
                file_name='test_claro_datos_celda_duplicate.csv',
                mission_id=self.test_mission_a_id,
                operator='CLARO',
                file_type='CELLULAR_DATA',
                user_id=self.test_user_id
            )
            
            if not result1.get('success'):
                return {
                    'success': False,
                    'error': f'Primera carga falló: {result1.get("error")}'
                }
            
            # Segunda carga del MISMO archivo en la MISMA misión (debe fallar)
            result2 = upload_operator_data(
                file_data=file_data['file_data'],
                file_name='test_claro_datos_celda_duplicate_2.csv',  # Nombre diferente, contenido igual
                mission_id=self.test_mission_a_id,
                operator='CLARO',
                file_type='CELLULAR_DATA',
                user_id=self.test_user_id
            )
            
            # Verificar que falló correctamente
            duplicate_detected = not result2.get('success') and 'ya ha sido procesado anteriormente en esta misión' in result2.get('error', '')
            
            return {
                'success': duplicate_detected,
                'details': {
                    'first_upload_success': result1.get('success'),
                    'second_upload_failed': not result2.get('success'),
                    'error_message': result2.get('error'),
                    'error_code': result2.get('error_code'),
                    'duplicate_correctly_detected': duplicate_detected
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_3_same_file_different_missions(self):
        """Test 3: Mismo archivo en misiones diferentes (debe funcionar)."""
        try:
            file_data = self.create_test_file_data("default")
            
            # Carga en Misión A
            result_a = upload_operator_data(
                file_data=file_data['file_data'],
                file_name='test_claro_datos_cross_mission.csv',
                mission_id=self.test_mission_a_id,
                operator='CLARO',
                file_type='CELLULAR_DATA',
                user_id=self.test_user_id
            )
            
            # Carga del MISMO archivo en Misión B (debe funcionar)
            result_b = upload_operator_data(
                file_data=file_data['file_data'],
                file_name='test_claro_datos_cross_mission.csv',
                mission_id=self.test_mission_b_id,
                operator='CLARO',
                file_type='CELLULAR_DATA',
                user_id=self.test_user_id
            )
            
            both_succeeded = result_a.get('success') and result_b.get('success')
            
            return {
                'success': both_succeeded,
                'details': {
                    'mission_a_success': result_a.get('success'),
                    'mission_a_error': result_a.get('error'),
                    'mission_b_success': result_b.get('success'),
                    'mission_b_error': result_b.get('error'),
                    'both_missions_succeeded': both_succeeded
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_4_different_files_same_mission(self):
        """Test 4: Archivos diferentes en la misma misión (debe funcionar)."""
        try:
            file_data_1 = self.create_test_file_data("default")
            file_data_2 = self.create_test_file_data("different")
            
            # Cargar primer archivo
            result_1 = upload_operator_data(
                file_data=file_data_1['file_data'],
                file_name='test_claro_datos_file_1.csv',
                mission_id=self.test_mission_a_id,
                operator='CLARO',
                file_type='CELLULAR_DATA',
                user_id=self.test_user_id
            )
            
            # Cargar segundo archivo (contenido diferente)
            result_2 = upload_operator_data(
                file_data=file_data_2['file_data'],
                file_name='test_claro_datos_file_2.csv',
                mission_id=self.test_mission_a_id,
                operator='CLARO',
                file_type='CELLULAR_DATA',
                user_id=self.test_user_id
            )
            
            both_succeeded = result_1.get('success') and result_2.get('success')
            
            return {
                'success': both_succeeded,
                'details': {
                    'file_1_success': result_1.get('success'),
                    'file_1_error': result_1.get('error'),
                    'file_2_success': result_2.get('success'),
                    'file_2_error': result_2.get('error'),
                    'different_checksums': file_data_1['checksum'] != file_data_2['checksum'],
                    'both_files_succeeded': both_succeeded
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_5_database_constraint_enforcement(self):
        """Test 5: Verificar enforcement del constraint en base de datos."""
        try:
            file_data = self.create_test_file_data("default")
            
            # Insertar registro directamente en BD
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Primer registro
                cursor.execute("""
                    INSERT INTO operator_data_sheets (
                        id, mission_id, file_name, file_size_bytes, file_checksum,
                        file_type, operator, uploaded_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    'test-sheet-1', self.test_mission_a_id, 'test_file_1.csv',
                    1000, file_data['checksum'], 'CELLULAR_DATA', 'CLARO', self.test_user_id
                ))
                
                conn.commit()
                
                # Intentar insertar duplicado en MISMA misión (debe fallar)
                constraint_enforced = False
                try:
                    cursor.execute("""
                        INSERT INTO operator_data_sheets (
                            id, mission_id, file_name, file_size_bytes, file_checksum,
                            file_type, operator, uploaded_by
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        'test-sheet-2', self.test_mission_a_id, 'test_file_2.csv',
                        1000, file_data['checksum'], 'CELLULAR_DATA', 'CLARO', self.test_user_id
                    ))
                    conn.commit()
                except sqlite3.IntegrityError as e:
                    constraint_enforced = 'UNIQUE constraint failed' in str(e)
                
                # Intentar insertar MISMO checksum en DIFERENTE misión (debe funcionar)
                different_mission_allowed = False
                try:
                    cursor.execute("""
                        INSERT INTO operator_data_sheets (
                            id, mission_id, file_name, file_size_bytes, file_checksum,
                            file_type, operator, uploaded_by
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        'test-sheet-3', self.test_mission_b_id, 'test_file_3.csv',
                        1000, file_data['checksum'], 'CELLULAR_DATA', 'CLARO', self.test_user_id
                    ))
                    conn.commit()
                    different_mission_allowed = True
                except sqlite3.IntegrityError:
                    different_mission_allowed = False
            
            return {
                'success': constraint_enforced and different_mission_allowed,
                'details': {
                    'constraint_prevents_same_mission_duplicate': constraint_enforced,
                    'constraint_allows_different_mission_duplicate': different_mission_allowed
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_6_error_message_specificity(self):
        """Test 6: Validar mensajes de error específicos por misión."""
        try:
            file_data = self.create_test_file_data("default")
            
            # Cargar archivo en misión A
            result1 = upload_operator_data(
                file_data=file_data['file_data'],
                file_name='test_error_message.csv',
                mission_id=self.test_mission_a_id,
                operator='CLARO',
                file_type='CELLULAR_DATA',
                user_id=self.test_user_id
            )
            
            if not result1.get('success'):
                return {
                    'success': False,
                    'error': f'Setup falló: {result1.get("error")}'
                }
            
            # Intentar cargar duplicado en misión A
            result2 = upload_operator_data(
                file_data=file_data['file_data'],
                file_name='test_error_message_duplicate.csv',
                mission_id=self.test_mission_a_id,
                operator='CLARO',
                file_type='CELLULAR_DATA',
                user_id=self.test_user_id
            )
            
            error_message = result2.get('error', '')
            has_mission_specific_text = 'en esta misión' in error_message
            has_duplicate_code = result2.get('error_code') == 'DUPLICATE_FILE'
            
            return {
                'success': has_mission_specific_text and has_duplicate_code,
                'details': {
                    'error_message': error_message,
                    'error_code': result2.get('error_code'),
                    'contains_mission_specific_text': has_mission_specific_text,
                    'has_correct_error_code': has_duplicate_code
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_test_report(self):
        """Genera reporte completo de testing."""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASSED'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAILED'])
        error_tests = len([r for r in self.test_results if r['status'] == 'ERROR'])
        
        report = {
            'test_execution': {
                'timestamp': datetime.now().isoformat(),
                'environment': {
                    'test_db_path': self.test_db_path,
                    'temp_directory': self.temp_dir,
                    'python_version': sys.version,
                    'test_mission_a': self.test_mission_a_id,
                    'test_mission_b': self.test_mission_b_id
                }
            },
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'errors': error_tests,
                'success_rate': round((passed_tests / total_tests) * 100, 1) if total_tests > 0 else 0
            },
            'test_results': self.test_results,
            'conclusion': {
                'migration_functionality': None,
                'duplicate_validation': None,
                'cross_mission_support': None,
                'overall_assessment': None
            }
        }
        
        # Evaluar conclusiones específicas
        migration_test = next((r for r in self.test_results if 'schema_migration' in r['test_name']), None)
        if migration_test:
            report['conclusion']['migration_functionality'] = 'PASSED' if migration_test['status'] == 'PASSED' else 'FAILED'
        
        duplicate_tests = [r for r in self.test_results if 'duplicate' in r['test_name'].lower()]
        if duplicate_tests:
            all_duplicate_passed = all(r['status'] == 'PASSED' for r in duplicate_tests)
            report['conclusion']['duplicate_validation'] = 'PASSED' if all_duplicate_passed else 'FAILED'
        
        cross_mission_test = next((r for r in self.test_results if 'different_missions' in r['test_name']), None)
        if cross_mission_test:
            report['conclusion']['cross_mission_support'] = 'PASSED' if cross_mission_test['status'] == 'PASSED' else 'FAILED'
        
        # Evaluación general
        if passed_tests == total_tests:
            report['conclusion']['overall_assessment'] = 'ALL_TESTS_PASSED'
        elif passed_tests >= total_tests * 0.8:
            report['conclusion']['overall_assessment'] = 'MOSTLY_SUCCESSFUL'
        elif passed_tests >= total_tests * 0.5:
            report['conclusion']['overall_assessment'] = 'PARTIAL_SUCCESS'
        else:
            report['conclusion']['overall_assessment'] = 'MAJOR_ISSUES'
        
        return report
    
    def cleanup(self):
        """Limpia el entorno de testing."""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                print(f"[CLEANUP] Directorio temporal limpiado: {self.temp_dir}")
            
            # Remover variable de entorno
            if 'KRONOS_DB_PATH' in os.environ:
                del os.environ['KRONOS_DB_PATH']
                
        except Exception as e:
            print(f"[WARNING] Error en limpieza: {e}")
    
    def run_all_tests(self):
        """Ejecuta toda la suite de testing."""
        print("[START] INICIANDO TESTING DE VALIDACION DE DUPLICADOS POR MISION")
        print("=" * 80)
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Entorno: {self.temp_dir}")
        print()
        
        # Ejecutar todos los tests
        tests = [
            ("Test 1: Migración Automática de Schema", self.test_1_schema_migration),
            ("Test 2: Duplicado en Misma Misión", self.test_2_duplicate_same_mission),
            ("Test 3: Mismo Archivo en Misiones Diferentes", self.test_3_same_file_different_missions),
            ("Test 4: Archivos Diferentes en Misma Misión", self.test_4_different_files_same_mission),
            ("Test 5: Enforcement de Constraint en BD", self.test_5_database_constraint_enforcement),
            ("Test 6: Especificidad de Mensajes de Error", self.test_6_error_message_specificity)
        ]
        
        for test_name, test_function in tests:
            self.run_test(test_name, test_function)
        
        # Generar reporte
        report = self.generate_test_report()
        
        # Mostrar resumen
        print("\n" + "=" * 80)
        print("[SUMMARY] RESUMEN DE TESTING")
        print("=" * 80)
        print(f"Total de Tests: {report['summary']['total_tests']}")
        print(f"Aprobados: {report['summary']['passed']} [PASS]")
        print(f"Fallidos: {report['summary']['failed']} [FAIL]")
        print(f"Errores: {report['summary']['errors']} [ERROR]")
        print(f"Tasa de Éxito: {report['summary']['success_rate']}%")
        print()
        
        # Conclusiones específicas
        print("[CONCLUSIONS] CONCLUSIONES ESPECIFICAS:")
        for key, value in report['conclusion'].items():
            if value:
                status_icon = "[OK]" if value == "PASSED" or "SUCCESS" in value else "[FAIL]"
                print(f"   {key.replace('_', ' ').title()}: {value} {status_icon}")
        
        return report


def main():
    """Función principal de testing."""
    tester = None
    
    try:
        tester = DuplicateValidationTester()
        
        # Actualizar status del todo
        print("[TODO] Actualizando lista de tareas...")
        
        # Ejecutar todos los tests
        report = tester.run_all_tests()
        
        # Guardar reporte
        report_filename = f"duplicate_validation_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = os.path.join(os.path.dirname(__file__), report_filename)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n[REPORT] Reporte guardado en: {report_path}")
        
        # Resultado final
        if report['summary']['success_rate'] >= 100:
            print("\n[SUCCESS] TODOS LOS TESTS PASARON - IMPLEMENTACION EXITOSA")
            return 0
        elif report['summary']['success_rate'] >= 80:
            print("\n[WARNING] MAYORIA DE TESTS PASARON - REVISAR ISSUES MENORES")
            return 1
        else:
            print("\n[CRITICAL] TESTS CRITICOS FALLARON - REVISAR IMPLEMENTACION")
            return 2
            
    except Exception as e:
        print(f"\n[CRITICAL ERROR] ERROR CRITICO EN TESTING: {e}")
        import traceback
        traceback.print_exc()
        return 3
        
    finally:
        if tester:
            tester.cleanup()


if __name__ == "__main__":
    sys.exit(main())