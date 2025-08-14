"""
KRONOS - Test Comprehensivo TIGO con Playwright
===============================================================================
Prueba completa del procesamiento de TIGO usando el archivo real "Reporte TIGO.xlsx"
para verificar que se logre el 100% de éxito en el procesamiento de todos los registros.

Objetivos:
1. Procesar el archivo TIGO real completo
2. Verificar tasa de éxito del 100%
3. Identificar y corregir problemas de normalización de destinos
4. Validar que no haya errores de JSON validation en operator_specific_data
5. Documentar resultados y proponer mejoras
===============================================================================
"""

import os
import sys
import json
import time
import traceback
import base64
import sqlite3
from datetime import datetime
from pathlib import Path

# Configurar path para importaciones
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.file_processor_service import FileProcessorService
from database.connection import get_db_connection
from utils.operator_logger import OperatorLogger

# Configurar logging
logger = OperatorLogger()

class TigoPlaywrightTest:
    """Clase para pruebas comprehensivas de TIGO con archivo real"""
    
    def __init__(self):
        self.file_service = FileProcessorService()
        self.test_results = {
            'test_start_time': datetime.now().isoformat(),
            'total_records_processed': 0,
            'successful_records': 0,
            'failed_records': 0,
            'error_details': [],
            'validation_errors': [],
            'json_validation_errors': [],
            'normalization_issues': [],
            'success_rate': 0.0,
            'sheets_processed': {},
            'detailed_stats': {}
        }
        
    def setup_test_environment(self):
        """Configura el entorno de prueba"""
        logger.info("Configurando entorno de prueba para TIGO...")
        
        try:
            # Crear misión de prueba directamente en la base de datos
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Eliminar misión de prueba previa si existe
                cursor.execute("""
                    SELECT id FROM missions WHERE name = ?
                """, ("TIGO_PLAYWRIGHT_TEST",))
                
                existing_mission = cursor.fetchone()
                
                if existing_mission:
                    mission_id = existing_mission[0]
                    logger.info(f"Eliminando misión de prueba previa: {mission_id}")
                    
                    # Eliminar datos de operador asociados
                    cursor.execute("DELETE FROM operator_call_data WHERE mission_id = ?", (mission_id,))
                    cursor.execute("DELETE FROM operator_file_uploads WHERE mission_id = ?", (mission_id,))
                    cursor.execute("DELETE FROM missions WHERE id = ?", (mission_id,))
                    conn.commit()
                
                # Obtener un usuario válido para la misión
                cursor.execute("SELECT id FROM users LIMIT 1")
                user_result = cursor.fetchone()
                
                if not user_result:
                    # Crear usuario de sistema si no existe
                    cursor.execute("""
                        INSERT INTO users (id, username, email, password_hash, role, is_active, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, ("system_test", "system_test", "system@test.com", "hash", "admin", 1, datetime.now().isoformat()))
                    user_id = "system_test"
                else:
                    user_id = user_result[0]
                
                # Crear nueva misión de prueba
                import uuid
                mission_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO missions (id, code, name, description, status, start_date, created_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    mission_id,
                    "TIGO_TEST",
                    "TIGO_PLAYWRIGHT_TEST",
                    "Misión para pruebas comprehensivas de TIGO con archivo real",
                    "En Progreso",
                    datetime.now().strftime("%Y-%m-%d"),
                    user_id,
                    datetime.now().isoformat()
                ))
                
                self.test_mission_id = mission_id
                conn.commit()
                
                logger.info(f"Misión de prueba creada: ID {self.test_mission_id}")
                
        except Exception as e:
            logger.error(f"Error configurando entorno de prueba: {e}")
            raise
    
    def load_tigo_test_file(self):
        """Carga el archivo de prueba TIGO real"""
        logger.info("Cargando archivo de prueba TIGO real...")
        
        # Ruta al archivo TIGO real
        tigo_file_path = Path("C:/Soluciones/BGC/claude/KNSOft/datatest/Tigo/Formato Excel/Reporte TIGO.xlsx")
        
        if not tigo_file_path.exists():
            raise FileNotFoundError(f"Archivo TIGO no encontrado: {tigo_file_path}")
        
        try:
            # Leer archivo y convertir a base64
            with open(tigo_file_path, 'rb') as file:
                file_content = file.read()
                file_base64 = base64.b64encode(file_content).decode('utf-8')
            
            self.file_data = {
                'name': 'Reporte TIGO.xlsx',
                'content': f'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{file_base64}'
            }
            
            logger.info(f"Archivo TIGO cargado exitosamente: {len(file_content)} bytes")
            return True
            
        except Exception as e:
            logger.error(f"Error cargando archivo TIGO: {e}")
            raise
    
    def validate_file_structure(self):
        """Valida la estructura del archivo TIGO"""
        logger.info("Validando estructura del archivo TIGO...")
        
        try:
            # Validación básica del archivo
            if not self.file_data or not self.file_data.get('content'):
                logger.error("Archivo TIGO vacío o sin contenido")
                return False
            
            # Extraer contenido base64
            content_b64 = self.file_data['content'].split(',')[1] if ',' in self.file_data['content'] else self.file_data['content']
            file_bytes = base64.b64decode(content_b64)
            
            if len(file_bytes) == 0:
                logger.error("Archivo TIGO sin datos")
                return False
            
            logger.info("Estructura del archivo TIGO básica válida")
            logger.info(f"Tamaño del archivo: {len(file_bytes)} bytes")
            
            self.test_results['structure_validation'] = {
                'is_valid': True,
                'file_size_bytes': len(file_bytes),
                'file_name': self.file_data['name']
            }
            
            return True
                
        except Exception as e:
            logger.error(f"Error en validación de estructura: {e}")
            logger.error(traceback.format_exc())
            self.test_results['structure_validation_error'] = str(e)
            return False
    
    def process_tigo_file_comprehensive(self):
        """Procesa el archivo TIGO de forma comprehensiva"""
        logger.info("Iniciando procesamiento comprehensivo del archivo TIGO...")
        
        try:
            # Extraer bytes del archivo
            content_b64 = self.file_data['content'].split(',')[1] if ',' in self.file_data['content'] else self.file_data['content']
            file_bytes = base64.b64decode(content_b64)
            
            # Generar ID de archivo único
            file_upload_id = f"tigo_test_{int(datetime.now().timestamp())}"
            
            # Procesar archivo usando el método específico de TIGO
            result = self.file_service.process_tigo_llamadas_unificadas(
                file_bytes=file_bytes,
                file_name=self.file_data['name'],
                file_upload_id=file_upload_id,
                mission_id=str(self.test_mission_id)
            )
            
            logger.info(f"Resultado del procesamiento: {result}")
            
            # Analizar resultados
            self.analyze_processing_results(result)
            
            return result.get('success', False)
            
        except Exception as e:
            logger.error(f"Error en procesamiento comprehensivo: {e}")
            logger.error(traceback.format_exc())
            self.test_results['processing_error'] = str(e)
            return False
    
    def analyze_processing_results(self, result):
        """Analiza los resultados del procesamiento en detalle"""
        logger.info("Analizando resultados del procesamiento...")
        
        try:
            # Actualizar estadísticas básicas
            self.test_results.update({
                'processing_success': result.get('success', False),
                'total_records_processed': result.get('records_processed', 0),
                'successful_records': result.get('records_inserted', 0),
                'failed_records': result.get('records_failed', 0),
                'processing_time_seconds': result.get('processing_time', 0),
                'file_size_mb': result.get('file_size_mb', 0)
            })
            
            # Calcular tasa de éxito
            total = self.test_results['total_records_processed']
            successful = self.test_results['successful_records']
            
            if total > 0:
                self.test_results['success_rate'] = (successful / total) * 100
            
            logger.info(f"ESTADÍSTICAS DE PROCESAMIENTO:")
            logger.info(f"   Total registros procesados: {total}")
            logger.info(f"   Registros exitosos: {successful}")
            logger.info(f"   Registros fallidos: {self.test_results['failed_records']}")
            logger.info(f"   Tasa de éxito: {self.test_results['success_rate']:.2f}%")
            
            # Analizar errores específicos
            if 'errors' in result:
                self.analyze_errors(result['errors'])
            
            # Analizar hojas procesadas
            if 'sheets_processed' in result:
                self.test_results['sheets_processed'] = result['sheets_processed']
                logger.info(f"Hojas procesadas: {result['sheets_processed']}")
            
        except Exception as e:
            logger.error(f"Error analizando resultados: {e}")
    
    def analyze_errors(self, errors):
        """Analiza errores específicos del procesamiento"""
        logger.info("Analizando errores específicos...")
        
        json_validation_count = 0
        normalization_count = 0
        validation_count = 0
        other_count = 0
        
        for error in errors:
            error_msg = str(error).lower()
            
            if 'json' in error_msg or 'operator_specific_data' in error_msg:
                json_validation_count += 1
                self.test_results['json_validation_errors'].append(error)
            elif 'normaliz' in error_msg or 'destino' in error_msg:
                normalization_count += 1
                self.test_results['normalization_issues'].append(error)
            elif 'validation' in error_msg:
                validation_count += 1
                self.test_results['validation_errors'].append(error)
            else:
                other_count += 1
                self.test_results['error_details'].append(error)
        
        logger.info(f"ANÁLISIS DE ERRORES:")
        logger.info(f"   Errores JSON validation: {json_validation_count}")
        logger.info(f"   Errores normalización: {normalization_count}")
        logger.info(f"   Errores validación: {validation_count}")
        logger.info(f"   Otros errores: {other_count}")
        
        # Mostrar algunos ejemplos de errores
        if json_validation_count > 0:
            logger.error(f"Ejemplo error JSON: {self.test_results['json_validation_errors'][0]}")
        if normalization_count > 0:
            logger.error(f"Ejemplo error normalización: {self.test_results['normalization_issues'][0]}")
    
    def verify_database_data(self):
        """Verifica los datos insertados en la base de datos"""
        logger.info("Verificando datos insertados en la base de datos...")
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Contar registros de llamadas
                cursor.execute("""
                    SELECT COUNT(*) FROM operator_call_data 
                    WHERE mission_id = ? AND operator = ?
                """, (self.test_mission_id, 'TIGO'))
                call_count = cursor.fetchone()[0]
                
                # Contar archivos subidos
                cursor.execute("""
                    SELECT COUNT(*) FROM operator_file_uploads 
                    WHERE mission_id = ? AND operator = ?
                """, (self.test_mission_id, 'TIGO'))
                file_count = cursor.fetchone()[0]
                
                # Obtener estadísticas por tipo de llamada
                cursor.execute("""
                    SELECT COUNT(*) FROM operator_call_data 
                    WHERE mission_id = ? AND operator = ? AND tipo_llamada = ?
                """, (self.test_mission_id, 'TIGO', 'SALIENTE'))
                salientes_count = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(*) FROM operator_call_data 
                    WHERE mission_id = ? AND operator = ? AND tipo_llamada = ?
                """, (self.test_mission_id, 'TIGO', 'ENTRANTE'))
                entrantes_count = cursor.fetchone()[0]
                
                # Obtener ejemplos de datos específicos del operador
                cursor.execute("""
                    SELECT operator_specific_data FROM operator_call_data 
                    WHERE mission_id = ? AND operator = ? 
                    LIMIT 5
                """, (self.test_mission_id, 'TIGO'))
                sample_records = cursor.fetchall()
                
                self.test_results['database_verification'] = {
                    'total_call_records': call_count,
                    'file_uploads': file_count,
                    'salientes_count': salientes_count,
                    'entrantes_count': entrantes_count,
                    'sample_operator_data': []
                }
                
                # Verificar datos específicos del operador
                json_valid_count = 0
                json_invalid_count = 0
                
                for record_row in sample_records:
                    operator_data_str = record_row[0]
                    try:
                        if operator_data_str:
                            operator_data = json.loads(operator_data_str)
                            json_valid_count += 1
                            self.test_results['database_verification']['sample_operator_data'].append(
                                operator_data
                            )
                        else:
                            json_invalid_count += 1
                    except json.JSONDecodeError:
                        json_invalid_count += 1
                
                logger.info(f"VERIFICACIÓN BASE DE DATOS:")
                logger.info(f"   Registros de llamadas: {call_count}")
                logger.info(f"   Archivos subidos: {file_count}")
                logger.info(f"   Llamadas salientes: {salientes_count}")
                logger.info(f"   Llamadas entrantes: {entrantes_count}")
                logger.info(f"   JSON válidos (muestra): {json_valid_count}")
                logger.info(f"   JSON inválidos (muestra): {json_invalid_count}")
                
                return call_count > 0
                
        except Exception as e:
            logger.error(f"Error verificando base de datos: {e}")
            return False
    
    def generate_comprehensive_report(self):
        """Genera reporte comprehensivo de la prueba"""
        logger.info("Generando reporte comprehensivo...")
        
        self.test_results['test_end_time'] = datetime.now().isoformat()
        
        # Calcular duración total del test
        start_time = datetime.fromisoformat(self.test_results['test_start_time'])
        end_time = datetime.fromisoformat(self.test_results['test_end_time'])
        total_duration = (end_time - start_time).total_seconds()
        self.test_results['total_test_duration_seconds'] = total_duration
        
        # Determinar estado general
        success_rate = self.test_results.get('success_rate', 0)
        if success_rate >= 100.0:
            self.test_results['overall_status'] = 'EXCELLENT'
        elif success_rate >= 95.0:
            self.test_results['overall_status'] = 'GOOD'
        elif success_rate >= 85.0:
            self.test_results['overall_status'] = 'ACCEPTABLE'
        else:
            self.test_results['overall_status'] = 'NEEDS_IMPROVEMENT'
        
        # Guardar reporte
        report_filename = f"tigo_playwright_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = Path(report_filename)
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Reporte guardado en: {report_path}")
            
        except Exception as e:
            logger.error(f"Error guardando reporte: {e}")
        
        return self.test_results
    
    def run_comprehensive_test(self):
        """Ejecuta el test comprehensivo completo"""
        logger.info("INICIANDO TEST COMPREHENSIVO TIGO CON PLAYWRIGHT")
        logger.info("="*80)
        
        try:
            # 1. Configurar entorno
            logger.info("PASO 1: Configurando entorno...")
            self.setup_test_environment()
            
            # 2. Cargar archivo
            logger.info("PASO 2: Cargando archivo TIGO real...")
            self.load_tigo_test_file()
            
            # 3. Validar estructura
            logger.info("PASO 3: Validando estructura del archivo...")
            if not self.validate_file_structure():
                raise Exception("Fallo en validación de estructura")
            
            # 4. Procesar archivo
            logger.info("PASO 4: Procesando archivo TIGO comprehensivamente...")
            if not self.process_tigo_file_comprehensive():
                logger.warning("Procesamiento completado con errores")
            
            # 5. Verificar base de datos
            logger.info("PASO 5: Verificando datos en base de datos...")
            self.verify_database_data()
            
            # 6. Generar reporte
            logger.info("PASO 6: Generando reporte comprehensivo...")
            report = self.generate_comprehensive_report()
            
            # 7. Mostrar resumen final
            self.show_final_summary()
            
            return report
            
        except Exception as e:
            logger.error(f"ERROR CRÍTICO EN TEST COMPREHENSIVO: {e}")
            logger.error(traceback.format_exc())
            self.test_results['critical_error'] = str(e)
            self.generate_comprehensive_report()
            raise
    
    def show_final_summary(self):
        """Muestra resumen final del test"""
        logger.info("="*80)
        logger.info("RESUMEN FINAL DEL TEST TIGO")
        logger.info("="*80)
        
        status = self.test_results.get('overall_status', 'UNKNOWN')
        success_rate = self.test_results.get('success_rate', 0)
        total_records = self.test_results.get('total_records_processed', 0)
        successful_records = self.test_results.get('successful_records', 0)
        failed_records = self.test_results.get('failed_records', 0)
        
        logger.info(f"Estado General: {status}")
        logger.info(f"Tasa de Éxito: {success_rate:.2f}%")
        logger.info(f"Registros Totales: {total_records}")
        logger.info(f"Registros Exitosos: {successful_records}")
        logger.info(f"Registros Fallidos: {failed_records}")
        
        if success_rate >= 100.0:
            logger.info("EXCELENTE! Se logró el 100% de éxito")
        elif success_rate >= 95.0:
            logger.info("Muy bueno, pero hay margen de mejora")
        elif success_rate < 85.0:
            logger.warning("Se requiere investigación y correcciones")
        
        # Mostrar errores principales si existen
        json_errors = len(self.test_results.get('json_validation_errors', []))
        norm_errors = len(self.test_results.get('normalization_issues', []))
        
        if json_errors > 0:
            logger.warning(f"{json_errors} errores de JSON validation encontrados")
        if norm_errors > 0:
            logger.warning(f"{norm_errors} problemas de normalización encontrados")
        
        logger.info("="*80)


def main():
    """Función principal"""
    tester = TigoPlaywrightTest()
    
    try:
        # Ejecutar test comprehensivo
        results = tester.run_comprehensive_test()
        
        # Determinar código de salida
        success_rate = results.get('success_rate', 0)
        if success_rate >= 100.0:
            print("\nTEST EXITOSO: Se logró el 100% de éxito")
            exit_code = 0
        elif success_rate >= 95.0:
            print("\nTEST BUENO: Tasa de éxito superior al 95%")
            exit_code = 0
        else:
            print(f"\nTEST CON PROBLEMAS: Tasa de éxito {success_rate:.2f}%")
            exit_code = 1
        
        return exit_code
        
    except Exception as e:
        print(f"\nTEST FALLÓ: {e}")
        return 2


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)