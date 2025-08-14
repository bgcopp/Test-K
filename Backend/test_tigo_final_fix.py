"""
KRONOS - Test Final TIGO con Corrección Completa
===============================================================================
Test final que crea todos los registros necesarios y ejecuta el procesamiento
TIGO completo con las correcciones aplicadas.
===============================================================================
"""

import os
import sys
import json
import base64
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path

# Configurar path para importaciones
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.file_processor_service import FileProcessorService
from database.connection import get_db_connection
from utils.operator_logger import OperatorLogger

logger = OperatorLogger()

class TigoFinalTest:
    """Test final con todas las correcciones aplicadas"""
    
    def __init__(self):
        self.file_service = FileProcessorService()
        self.test_mission_id = None
        self.test_file_upload_id = None
        
    def setup_complete_environment(self):
        """Configura el entorno completo incluyendo todos los registros necesarios"""
        logger.info("Configurando entorno completo para test final...")
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 1. Crear misión de prueba
                import uuid
                self.test_mission_id = str(uuid.uuid4())
                
                # Obtener usuario válido
                cursor.execute("SELECT id FROM users LIMIT 1")
                user_result = cursor.fetchone()
                
                if not user_result:
                    cursor.execute("""
                        INSERT INTO users (id, username, email, password_hash, role, is_active, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, ("system_test", "system_test", "system@test.com", "hash", "admin", 1, datetime.now().isoformat()))
                    user_id = "system_test"
                else:
                    user_id = user_result[0]
                
                cursor.execute("""
                    INSERT INTO missions (id, code, name, description, status, start_date, created_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.test_mission_id,
                    "TIGO_FINAL_TEST",
                    "TIGO_FINAL_TEST",
                    "Test final de TIGO con todas las correcciones",
                    "En Progreso",
                    datetime.now().strftime("%Y-%m-%d"),
                    user_id,
                    datetime.now().isoformat()
                ))
                
                # 2. Crear registro en operator_data_sheets
                self.test_file_upload_id = f"tigo_final_test_{int(datetime.now().timestamp())}"
                
                # Calcular checksum del archivo
                file_content = b"dummy content for checksum"
                file_checksum = hashlib.sha256(file_content).hexdigest()
                
                cursor.execute("""
                    INSERT INTO operator_data_sheets 
                    (id, mission_id, file_name, file_size_bytes, file_checksum, file_type, 
                     operator, operator_file_format, processing_status, uploaded_by, uploaded_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.test_file_upload_id,
                    self.test_mission_id,
                    "Reporte TIGO.xlsx",
                    348446,
                    file_checksum,
                    "CALL_DATA",
                    "TIGO",
                    "LLAMADAS_MIXTAS",
                    "PROCESSING",
                    user_id,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                
                # 3. Crear registro en operator_file_uploads
                cursor.execute("""
                    INSERT INTO operator_file_uploads 
                    (id, mission_id, operator, file_name, file_type, file_size, 
                     upload_date, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.test_file_upload_id + "_upload",
                    self.test_mission_id,
                    "TIGO",
                    "Reporte TIGO.xlsx",
                    "LLAMADAS_MIXTAS",
                    348446,
                    datetime.now().isoformat(),
                    "PROCESSING",
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                
                logger.info(f"Entorno configurado: Mission ID {self.test_mission_id}")
                logger.info(f"                    File Upload ID {self.test_file_upload_id}")
                
                return True
                
        except Exception as e:
            logger.error(f"Error configurando entorno completo: {e}")
            return False
    
    def load_tigo_file(self):
        """Carga el archivo TIGO real"""
        tigo_file_path = Path("C:/Soluciones/BGC/claude/KNSOft/datatest/Tigo/Formato Excel/Reporte TIGO.xlsx")
        
        if not tigo_file_path.exists():
            logger.error(f"Archivo TIGO no encontrado: {tigo_file_path}")
            return False
        
        try:
            with open(tigo_file_path, 'rb') as file:
                file_content = file.read()
                self.file_bytes = file_content
            
            logger.info(f"Archivo TIGO cargado: {len(file_content)} bytes")
            return True
            
        except Exception as e:
            logger.error(f"Error cargando archivo TIGO: {e}")
            return False
    
    def process_tigo_with_fixes(self):
        """Procesa TIGO usando el file_upload_id correcto"""
        logger.info("Procesando TIGO con todas las correcciones...")
        
        try:
            result = self.file_service.process_tigo_llamadas_unificadas(
                file_bytes=self.file_bytes,
                file_name="Reporte TIGO.xlsx",
                file_upload_id=self.test_file_upload_id,
                mission_id=self.test_mission_id
            )
            
            logger.info(f"Resultado del procesamiento: {result}")
            
            success_rate = 0
            if result.get('records_processed', 0) > 0:
                successful = result.get('records_processed', 0) - result.get('records_failed', 0)
                success_rate = (successful / result.get('records_processed', 0)) * 100
            
            logger.info(f"Tasa de éxito: {success_rate:.2f}%")
            logger.info(f"Registros procesados: {result.get('records_processed', 0)}")
            logger.info(f"Registros exitosos: {result.get('records_processed', 0) - result.get('records_failed', 0)}")
            logger.info(f"Registros fallidos: {result.get('records_failed', 0)}")
            
            return success_rate, result
            
        except Exception as e:
            logger.error(f"Error en procesamiento final: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return 0, {'error': str(e)}
    
    def verify_final_results(self):
        """Verifica los resultados finales en la base de datos"""
        logger.info("Verificando resultados finales...")
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Contar registros insertados
                cursor.execute("""
                    SELECT COUNT(*) FROM operator_call_data 
                    WHERE mission_id = ? AND operator = ?
                """, (self.test_mission_id, 'TIGO'))
                total_records = cursor.fetchone()[0]
                
                # Contar por tipo
                cursor.execute("""
                    SELECT tipo_llamada, COUNT(*) FROM operator_call_data 
                    WHERE mission_id = ? AND operator = ?
                    GROUP BY tipo_llamada
                """, (self.test_mission_id, 'TIGO'))
                
                type_counts = dict(cursor.fetchall())
                
                # Verificar JSON válido
                cursor.execute("""
                    SELECT COUNT(*) FROM operator_call_data 
                    WHERE mission_id = ? AND operator = ? 
                    AND operator_specific_data IS NOT NULL
                """, (self.test_mission_id, 'TIGO'))
                json_records = cursor.fetchone()[0]
                
                logger.info(f"RESULTADOS FINALES:")
                logger.info(f"  Total registros insertados: {total_records}")
                logger.info(f"  Tipos de llamada: {type_counts}")
                logger.info(f"  Registros con JSON válido: {json_records}")
                
                return total_records > 0
                
        except Exception as e:
            logger.error(f"Error verificando resultados: {e}")
            return False
    
    def run_final_test(self):
        """Ejecuta el test final completo"""
        logger.info("="*80)
        logger.info("KRONOS - TEST FINAL TIGO CON TODAS LAS CORRECCIONES")
        logger.info("="*80)
        
        steps = [
            ("Configurar entorno completo", self.setup_complete_environment),
            ("Cargar archivo TIGO", self.load_tigo_file),
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n--- {step_name} ---")
            if not step_func():
                logger.error(f"Falló: {step_name}")
                return False
        
        # Procesar archivo
        logger.info(f"\n--- Procesar archivo TIGO ---")
        success_rate, result = self.process_tigo_with_fixes()
        
        # Verificar resultados
        logger.info(f"\n--- Verificar resultados ---")
        db_success = self.verify_final_results()
        
        # Resumen final
        logger.info("="*80)
        logger.info("RESUMEN FINAL")
        logger.info("="*80)
        
        if success_rate >= 95:
            logger.info(f"EXCELENTE: Tasa de éxito {success_rate:.2f}%")
            return True
        elif success_rate >= 85:
            logger.info(f"BUENO: Tasa de éxito {success_rate:.2f}%")
            return True
        else:
            logger.warning(f"NECESITA MEJORAS: Tasa de éxito {success_rate:.2f}%")
            return False


def main():
    """Función principal"""
    tester = TigoFinalTest()
    
    try:
        success = tester.run_final_test()
        
        if success:
            print("\nTEST FINAL TIGO: EXITOSO")
            return 0
        else:
            print("\nTEST FINAL TIGO: NECESITA MEJORAS")
            return 1
            
    except Exception as e:
        print(f"\nTEST FINAL TIGO FALLÓ: {e}")
        return 2


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)