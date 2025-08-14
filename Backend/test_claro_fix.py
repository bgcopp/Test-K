"""
TEST DE LA CORRECCIÓN DEL PROBLEMA CLARO
==========================================
Script para probar la corrección del problema de foreign key constraint.
"""

import os
import sys
import logging
import traceback
import base64
import uuid
from pathlib import Path

# Configurar path para imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Configurar logging simple
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('claro_fix_test.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

from database.connection import init_database, get_database_manager
from database.models import Mission
from services.operator_processors.claro_processor import ClaroProcessor
from database.operator_models import OperatorFileUpload


def create_test_mission():
    """Crear misión de testing válida"""
    try:
        db_manager = get_database_manager()
        with db_manager.get_session() as session:
            mission_id = "test-mission-claro-fix"
            
            # Verificar si ya existe
            existing = session.query(Mission).filter_by(id=mission_id).first()
            if existing:
                logger.info(f"Misión de testing ya existe: {mission_id}")
                return mission_id
            
            # Crear nueva misión con fechas requeridas
            from datetime import datetime, date
            mission = Mission(
                id=mission_id,
                code="TEST-CLARO-FIX",
                name="Test Corrección CLARO",
                description="Misión para probar la corrección del problema CLARO",
                status="En Progreso",
                start_date=date(2025, 1, 1),
                end_date=date(2025, 12, 31),
                created_by="admin"
            )
            
            session.add(mission)
            session.commit()
            
            logger.info(f"Misión de testing creada: {mission_id}")
            return mission_id
            
    except Exception as e:
        logger.error(f"Error creando misión de testing: {e}")
        return None


def prepare_test_file():
    """Preparar archivo de testing"""
    test_data_dir = Path(current_dir) / '..' / 'datatest' / 'Claro'
    test_file_path = test_data_dir / 'DATOS_POR_CELDA CLARO_MANUAL_FIX.csv'
    
    if not test_file_path.exists():
        logger.error(f"Archivo de testing no encontrado: {test_file_path}")
        return None
    
    try:
        # Leer archivo y convertir a formato esperado
        with open(test_file_path, 'rb') as f:
            file_bytes = f.read()
        
        file_data = {
            'name': test_file_path.name,
            'content': f'data:text/csv;base64,{base64.b64encode(file_bytes).decode("utf-8")}',
            'size': len(file_bytes),
            'type': 'text/csv'
        }
        
        logger.info(f"Archivo preparado: {test_file_path.name} ({len(file_bytes):,} bytes)")
        return file_data
        
    except Exception as e:
        logger.error(f"Error preparando archivo: {e}")
        return None


def test_corrected_processing():
    """Probar el procesamiento corregido"""
    logger.info("="*60)
    logger.info("PROBANDO CORRECCIÓN DEL PROBLEMA CLARO")
    logger.info("="*60)
    
    try:
        # Inicializar BD
        logger.info("1. Inicializando base de datos...")
        init_database(force_recreate=False)
        db_manager = get_database_manager()
        
        # Crear misión de testing
        logger.info("2. Creando misión de testing válida...")
        mission_id = create_test_mission()
        if not mission_id:
            logger.error("No se pudo crear la misión de testing")
            return False
        
        # Preparar archivo
        logger.info("3. Preparando archivo de testing...")
        file_data = prepare_test_file()
        if not file_data:
            logger.error("No se pudo preparar el archivo de testing")
            return False
        
        # Procesar con corrección
        logger.info("4. Procesando archivo con corrección aplicada...")
        processor = ClaroProcessor()
        
        try:
            result = processor.process_file(file_data, "DATOS", mission_id)
            
            if result.get('success'):
                logger.info("[ÉXITO] Procesamiento completado exitosamente!")
                logger.info(f"  - Registros procesados: {result.get('records_processed')}")
                logger.info(f"  - File upload ID: {result.get('file_upload_id')}")
                
                # Verificar persistencia
                logger.info("5. Verificando persistencia en BD...")
                with db_manager.get_session() as session:
                    upload = session.query(OperatorFileUpload).filter_by(
                        id=result.get('file_upload_id')
                    ).first()
                    
                    if upload:
                        logger.info(f"  - Upload encontrado con estado: {upload.upload_status}")
                        logger.info(f"  - Registros: {upload.records_count}")
                        
                        if upload.upload_status == 'completed':
                            logger.info("[ÉXITO TOTAL] La corrección funciona perfectamente!")
                            return True
                        else:
                            logger.error(f"[PROBLEMA] Upload no completado: {upload.upload_status}")
                            return False
                    else:
                        logger.error("[PROBLEMA] Upload no encontrado en BD")
                        return False
            else:
                logger.error("[FALLO] El procesamiento no fue exitoso")
                return False
                
        except Exception as e:
            logger.error(f"[FALLO] Error en procesamiento: {e}")
            logger.error(traceback.format_exc())
            return False
        
    except Exception as e:
        logger.error(f"Error general: {e}")
        logger.error(traceback.format_exc())
        return False
    
    finally:
        try:
            db_manager.close()
        except:
            pass


if __name__ == "__main__":
    success = test_corrected_processing()
    
    if success:
        logger.info("\n" + "="*60)
        logger.info("✅ CORRECCIÓN EXITOSA - EL PROBLEMA HA SIDO RESUELTO")
        logger.info("="*60)
        sys.exit(0)
    else:
        logger.error("\n" + "="*60)
        logger.error("❌ LA CORRECCIÓN REQUIERE AJUSTES ADICIONALES")
        logger.error("="*60)
        sys.exit(1)