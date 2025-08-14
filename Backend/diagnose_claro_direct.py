"""
DIAGNÓSTICO DIRECTO - Procesamiento CLARO
==================================================
Script directo para diagnosticar el problema específico de procesamiento CLARO.
Evita dependencies complejas y va directo al problema.
"""

import os
import sys
import logging
import traceback
import base64
from pathlib import Path

# Configurar path para imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Configurar logging simple
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('claro_direct_diagnosis.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

from database.connection import init_database, get_database_manager
from services.operator_processors.claro_processor import ClaroProcessor
from database.operator_models import OperatorFileUpload, OperatorCellularData, OperatorCallData


def setup_database():
    """Configurar base de datos"""
    try:
        logger.info("Inicializando base de datos...")
        init_database(force_recreate=False)
        db_manager = get_database_manager()
        logger.info("Base de datos inicializada correctamente")
        return db_manager
    except Exception as e:
        logger.error(f"Error inicializando BD: {e}")
        logger.error(traceback.format_exc())
        return None


def prepare_test_file():
    """Preparar archivo de testing CLARO más pequeño"""
    test_data_dir = Path(current_dir) / '..' / 'datatest' / 'Claro'
    test_file_path = test_data_dir / 'DATOS_POR_CELDA CLARO_MANUAL_FIX.csv'
    
    if not test_file_path.exists():
        logger.error(f"Archivo de testing no encontrado: {test_file_path}")
        return None
    
    try:
        # Leer archivo y convertir a base64
        with open(test_file_path, 'rb') as f:
            file_bytes = f.read()
        
        # Crear estructura de datos compatible - formato data URL esperado
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
        logger.error(traceback.format_exc())
        return None


def test_claro_processing():
    """Test directo del procesamiento CLARO"""
    logger.info("="*60)
    logger.info("INICIANDO DIAGNÓSTICO DIRECTO CLARO")
    logger.info("="*60)
    
    # Setup
    db_manager = setup_database()
    if not db_manager:
        return False
        
    file_data = prepare_test_file()
    if not file_data:
        return False
    
    # Crear procesador CLARO directamente
    logger.info("Creando procesador CLARO...")
    processor = ClaroProcessor()
    
    test_mission_id = "test-direct-mission-001"
    file_type = "DATOS"
    
    try:
        # ETAPA 1: Validar estructura
        logger.info("\nETAPA 1: Validando estructura...")
        validation_result = processor.validate_file_structure(file_data, file_type)
        
        if not validation_result.get('is_valid'):
            logger.error(f"VALIDACIÓN FALLIDA: {validation_result.get('error')}")
            return False
            
        logger.info("[OK] Validación exitosa")
        logger.info(f"  - Columnas: {len(validation_result.get('original_columns', []))}")
        logger.info(f"  - Filas muestra: {validation_result.get('sample_rows', 0)}")
        
        # ETAPA 2: Verificar estado inicial BD
        logger.info("\nETAPA 2: Verificando estado inicial BD...")
        initial_uploads = count_uploads(db_manager, test_mission_id)
        initial_cellular = count_cellular_data(db_manager, test_mission_id)
        
        logger.info(f"  - Uploads iniciales: {initial_uploads}")
        logger.info(f"  - Datos celulares iniciales: {initial_cellular}")
        
        # ETAPA 3: Procesar archivo paso a paso
        logger.info("\nETAPA 3: Procesando archivo...")
        logger.info("  Iniciando process_file...")
        
        # DIAGNÓSTICO CRÍTICO: Interceptar en puntos clave
        try:
            processing_result = processor.process_file(file_data, file_type, test_mission_id)
            
            logger.info("[OK] process_file completado sin excepción")
            logger.info(f"  - Success: {processing_result.get('success')}")
            logger.info(f"  - Records processed: {processing_result.get('records_processed')}")
            logger.info(f"  - File upload ID: {processing_result.get('file_upload_id')}")
            
        except Exception as proc_error:
            logger.error(f"[FAIL] Error en process_file: {proc_error}")
            logger.error(traceback.format_exc())
            return False
        
        # ETAPA 4: Verificar persistencia inmediata
        logger.info("\nETAPA 4: Verificando persistencia...")
        final_uploads = count_uploads(db_manager, test_mission_id)
        final_cellular = count_cellular_data(db_manager, test_mission_id)
        
        logger.info(f"  - Uploads finales: {final_uploads} (incremento: {final_uploads - initial_uploads})")
        logger.info(f"  - Datos celulares finales: {final_cellular} (incremento: {final_cellular - initial_cellular})")
        
        # ETAPA 5: Verificar detalles del upload específico
        if processing_result.get('file_upload_id'):
            logger.info("\nETAPA 5: Verificando detalles del upload...")
            upload_details = get_upload_details(db_manager, processing_result['file_upload_id'])
            
            if upload_details:
                logger.info(f"  - Estado: {upload_details.get('upload_status')}")
                logger.info(f"  - Records count: {upload_details.get('records_count')}")
                logger.info(f"  - Error message: {upload_details.get('error_message')}")
                logger.info(f"  - Created at: {upload_details.get('created_at')}")
                logger.info(f"  - Processed at: {upload_details.get('processed_at')}")
                
                # ANÁLISIS CRÍTICO
                if processing_result.get('success') and upload_details.get('upload_status') != 'completed':
                    logger.error("\n" + "="*60)
                    logger.error("DISCREPANCIA CRÍTICA DETECTADA:")
                    logger.error("- process_file retorna success=True")
                    logger.error(f"- Pero upload_status = '{upload_details.get('upload_status')}'")
                    logger.error(f"- Error message: '{upload_details.get('error_message')}'")
                    logger.error("ESTO INDICA FALLA EN TRANSACCIÓN O COMMIT")
                    logger.error("="*60)
                    return False
                elif upload_details.get('upload_status') == 'completed':
                    logger.info("[OK] Upload completado correctamente")
                else:
                    logger.warning(f"Upload en estado: {upload_details.get('upload_status')}")
            else:
                logger.error("[FAIL] No se pudo obtener detalles del upload")
                return False
        else:
            logger.error("[FAIL] No se generó file_upload_id")
            return False
        
        # RESUMEN FINAL
        logger.info("\n" + "="*60)
        logger.info("RESUMEN DEL DIAGNÓSTICO:")
        logger.info(f"  - Validación: [OK]")
        logger.info(f"  - Procesamiento: [OK]")
        logger.info(f"  - Persistencia BD: [OK]" if final_uploads > initial_uploads else "[FAIL]")
        logger.info(f"  - Estado upload: [{upload_details.get('upload_status', 'UNKNOWN')}]")
        logger.info(f"  - Registros procesados: {processing_result.get('records_processed', 0)}")
        
        success = (
            processing_result.get('success') and 
            final_uploads > initial_uploads and 
            upload_details and 
            upload_details.get('upload_status') == 'completed'
        )
        
        if success:
            logger.info("\n[ÉXITO] Procesamiento completado sin problemas críticos")
        else:
            logger.error("\n[FALLA] Se detectaron problemas críticos en el procesamiento")
        
        logger.info("="*60)
        return success
        
    except Exception as e:
        logger.error(f"Error general en diagnóstico: {e}")
        logger.error(traceback.format_exc())
        return False
    
    finally:
        try:
            db_manager.close()
        except:
            pass


def count_uploads(db_manager, mission_id):
    """Contar uploads"""
    try:
        with db_manager.get_session() as session:
            return session.query(OperatorFileUpload).filter_by(
                mission_id=mission_id, operator='CLARO'
            ).count()
    except:
        return -1


def count_cellular_data(db_manager, mission_id):
    """Contar datos celulares"""
    try:
        with db_manager.get_session() as session:
            return session.query(OperatorCellularData).filter_by(
                mission_id=mission_id, operator='CLARO'
            ).count()
    except:
        return -1


def get_upload_details(db_manager, upload_id):
    """Obtener detalles de upload"""
    try:
        with db_manager.get_session() as session:
            upload = session.query(OperatorFileUpload).filter_by(id=upload_id).first()
            if upload:
                return {
                    'upload_status': upload.upload_status,
                    'records_count': upload.records_count,
                    'error_message': upload.error_message,
                    'created_at': upload.created_at,
                    'processed_at': upload.processed_at
                }
    except Exception as e:
        logger.error(f"Error obteniendo detalles: {e}")
    return None


if __name__ == "__main__":
    try:
        success = test_claro_processing()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Diagnóstico interrumpido por usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error crítico: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)