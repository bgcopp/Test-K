"""
KRONOS L2 Analysis - FOREIGN KEY Constraint Error Diagnosis
===============================================================================
Test especializado para reproducir y diagnosticar el error exacto:
"FOREIGN KEY constraint failed" durante upload de archivos de operador.

Este test L2 reproduce el flujo completo que causa el problema:
1. Archivo procesa exitosamente al 100%
2. Error ocurre durante la persistencia en BD
3. Usuario ve progreso completo seguido de error

Análisis crítico:
- ¿El problema es en mission_service.upload_operator_data?
- ¿O es en el procesador específico de CLARO?
- ¿La misión CERT-CLARO-001 está correctamente referenciada?
===============================================================================
"""

import logging
import traceback
from pathlib import Path
import sys
import base64

# Configurar path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Configurar logging detallado para diagnóstico L2
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('l2_foreign_key_diagnosis.log')
    ]
)
logger = logging.getLogger(__name__)


def create_minimal_claro_file():
    """Crea archivo CLARO mínimo para testing"""
    # CSV simple con estructura CLARO válida
    csv_content = """numero;fecha_trafico;tipo_cdr;celda_decimal;lac_decimal
3001234567;20240419080000;VOICE;12345;6789
3001234568;20240419090000;DATA;12346;6790
3001234569;20240419100000;SMS;12347;6791"""
    
    # Codificar en base64
    csv_bytes = csv_content.encode('utf-8')
    base64_content = base64.b64encode(csv_bytes).decode('utf-8')
    
    return {
        "name": "datos_claro_test.csv",
        "content": f"data:text/csv;base64,{base64_content}"
    }


def test_l2_foreign_key_diagnosis():
    """
    Test L2 para diagnosticar error FOREIGN KEY específico
    """
    logger.info("="*80)
    logger.info("INICIANDO DIAGNÓSTICO L2 - FOREIGN KEY CONSTRAINT FAILED")
    logger.info("="*80)
    
    try:
        # Fase 1: Verificar estado actual de la base de datos
        logger.info("FASE 1: Verificando estado actual de base de datos")
        
        from database.connection import DatabaseManager
        from database.models import Mission
        
        # CORRECCIÓN CRÍTICA: Inicializar database manager
        db_manager = DatabaseManager()
        db_manager.initialize()
        
        with db_manager.get_session() as session:
            # Verificar que CERT-CLARO-001 existe
            claro_mission = session.query(Mission).filter(
                Mission.code == 'CERT-CLARO-001'
            ).first()
            
            if claro_mission:
                logger.info(f"✅ CERT-CLARO-001 ENCONTRADA:")
                logger.info(f"  - ID: {claro_mission.id}")
                logger.info(f"  - Nombre: {claro_mission.name}")
                logger.info(f"  - Status: {claro_mission.status}")
                mission_id = claro_mission.id
            else:
                logger.error("ERROR: CERT-CLARO-001 NO ENCONTRADA")
                return False
        
        # Fase 2: Probar el flujo que falla
        logger.info("FASE 2: Reproduciendo flujo que causa FOREIGN KEY error")
        
        # Crear archivo de prueba
        file_data = create_minimal_claro_file()
        logger.info(f"Archivo de prueba creado: {file_data['name']}")
        
        # Intentar upload usando mission_service
        logger.info("Intentando upload_operator_data via mission_service...")
        
        from services.mission_service import get_mission_service
        mission_service = get_mission_service()
        
        # Esta es la llamada que debe fallar con FOREIGN KEY constraint
        try:
            result = mission_service.upload_operator_data(
                mission_id=mission_id,
                sheet_name="Datos CLARO Test",
                file_data=file_data
            )
            logger.info("✅ Upload exitoso!")
            logger.info(f"Resultado: {result}")
            
        except Exception as upload_error:
            logger.error("ERROR EN UPLOAD_OPERATOR_DATA:")
            logger.error(f"Error: {upload_error}")
            logger.error("STACK TRACE COMPLETO:")
            traceback.print_exc()
            
            # Analizar el tipo específico de error
            error_str = str(upload_error)
            if "FOREIGN KEY constraint failed" in error_str:
                logger.error("CONFIRMADO: Error FOREIGN KEY constraint failed")
                
                # Fase 3: Diagnóstico profundo de la causa raíz
                logger.info("FASE 3: Diagnóstico profundo de causa raíz")
                
                # Verificar si el problema es en el procesador de operador
                logger.info("Probando procesador de operador directamente...")
                
                try:
                    from services.operator_service import get_operator_service
                    operator_service = get_operator_service()
                    
                    # Probar validación
                    validation = operator_service.validate_file_for_operator(
                        'CLARO', file_data, 'DATOS'
                    )
                    logger.info(f"Validación: {validation}")
                    
                    # Probar procesamiento directo
                    process_result = operator_service.process_file_for_operator(
                        'CLARO', file_data, 'DATOS', mission_id
                    )
                    logger.info(f"Procesamiento directo exitoso: {process_result}")
                    
                except Exception as operator_error:
                    logger.error(f"ERROR EN OPERATOR SERVICE: {operator_error}")
                    traceback.print_exc()
                    
                    # El problema está en operator service vs mission service
                    logger.error("ANÁLISIS L2:")
                    logger.error("  - mission_service.upload_operator_data FALLA")
                    logger.error("  - operator_service puede funcionar correctamente") 
                    logger.error("  - PROBLEMA: Inconsistencia arquitectónica")
                    
                    return False
                
            else:
                logger.error(f"Tipo de error diferente: {error_str}")
                return False
        
        # Fase 4: Verificar integridad post-upload
        logger.info("FASE 4: Verificando integridad post-upload")
        
        with db_manager.get_session() as session:
            # Contar registros de operador
            from database.operator_models import OperatorFileUpload
            uploads = session.query(OperatorFileUpload).filter(
                OperatorFileUpload.mission_id == mission_id,
                OperatorFileUpload.operator == 'CLARO'
            ).all()
            
            logger.info(f"Archivos CLARO en BD: {len(uploads)}")
            for upload in uploads:
                logger.info(f"  - {upload.file_name}: {upload.records_count} registros, status: {upload.upload_status}")
        
        logger.info("="*80)
        logger.info("DIAGNÓSTICO L2 COMPLETADO EXITOSAMENTE")
        logger.info("="*80)
        
        return True
        
    except Exception as e:
        logger.error(f"ERROR CRÍTICO EN DIAGNÓSTICO L2: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_l2_foreign_key_diagnosis()
    if success:
        print("Diagnóstico L2 completado exitosamente")
    else:
        print("Diagnóstico L2 falló - revisar logs para detalles")
    
    sys.exit(0 if success else 1)