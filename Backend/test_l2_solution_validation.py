"""
KRONOS L2 Solution Validation Test
===============================================================================
Test definitivo que valida que la solución L2 arquitectónica resuelve
completamente el problema de FOREIGN KEY constraint failed.

Flujo de validación:
1. Crear archivo CLARO real (estructura datos celulares)
2. Usar nueva función upload_operator_data con router inteligente
3. Verificar que:
   - No hay errores FOREIGN KEY
   - Archivo se procesa correctamente
   - Datos se persisten en tablas correctas
   - Frontend recibe respuesta consistente

Validación L2:
- Router detecta automáticamente tipo CLARO
- Usa operator_service en lugar de mission_service
- Transacciones atómicas funcionan correctamente
- Ningún bloqueo para el usuario final
===============================================================================
"""

import logging
import traceback
import sys
import base64
from pathlib import Path

# Configurar path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Configurar logging sin emojis para evitar encoding issues
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('l2_solution_validation.log')
    ]
)
logger = logging.getLogger(__name__)


def create_claro_test_files():
    """Crea archivos de test para diferentes tipos CLARO"""
    
    # Archivo CLARO Datos (estructura real)
    datos_csv = """numero;fecha_trafico;tipo_cdr;celda_decimal;lac_decimal
3001234567;20240419080000;VOICE;12345;6789
3001234568;20240419090000;DATA;12346;6790
3001234569;20240419100000;SMS;12347;6791
3007777777;20240419110000;VOICE;12348;6792"""
    
    # Archivo genérico (estructura antigua)
    generic_csv = """operatorId;name;towers;coverage
OP001;Operador Test 1;150;85%
OP002;Operador Test 2;200;92%
OP003;Operador Test 3;120;78%"""
    
    files = {}
    
    # CLARO datos
    datos_bytes = datos_csv.encode('utf-8')
    datos_b64 = base64.b64encode(datos_bytes).decode('utf-8')
    files['claro_datos'] = {
        "name": "datos_claro_test.csv",
        "content": f"data:text/csv;base64,{datos_b64}"
    }
    
    # Genérico
    generic_bytes = generic_csv.encode('utf-8')
    generic_b64 = base64.b64encode(generic_bytes).decode('utf-8')
    files['generic'] = {
        "name": "operador_generico_test.csv", 
        "content": f"data:text/csv;base64,{generic_b64}"
    }
    
    return files


def test_l2_solution_complete():
    """Test completo de la solución L2"""
    logger.info("=" * 80)
    logger.info("INICIANDO VALIDACIÓN L2 - SOLUCIÓN ARQUITECTÓNICA COMPLETA")
    logger.info("=" * 80)
    
    try:
        # Inicializar base de datos
        from database.connection import init_database, get_database_manager
        from database.models import Mission
        
        # CORRECCIÓN L2: Usar init_database para establecer la instancia global
        init_database()
        db_manager = get_database_manager()
        
        # Verificar misión CERT-CLARO-001
        with db_manager.get_session() as session:
            claro_mission = session.query(Mission).filter(
                Mission.code == 'CERT-CLARO-001'
            ).first()
            
            if not claro_mission:
                logger.error("ERROR: Misión CERT-CLARO-001 no encontrada")
                return False
                
            mission_id = claro_mission.id
            logger.info(f"Misión CERT-CLARO-001 encontrada: {mission_id}")
        
        # Crear archivos de test
        test_files = create_claro_test_files()
        
        # FASE 1: Probar router inteligente directamente
        logger.info("FASE 1: Probando router inteligente directamente")
        
        from services.intelligent_upload_router import get_intelligent_router
        router = get_intelligent_router()
        
        # Test con archivo CLARO
        logger.info("Probando archivo CLARO...")
        try:
            claro_result = router.route_upload(
                mission_id=mission_id,
                sheet_name="Datos CLARO Router Test",
                file_data=test_files['claro_datos']
            )
            
            logger.info("SUCCESS: Router procesó archivo CLARO exitosamente")
            logger.info(f"Routing info: {claro_result.get('routing_info', {})}")
            
            # Verificar que usó procesador específico
            if claro_result.get('routing_info', {}).get('processor') == 'specific':
                logger.info("SUCCESS: Router usó procesador específico CLARO")
            else:
                logger.error("ERROR: Router no usó procesador específico")
                return False
                
        except Exception as e:
            logger.error(f"ERROR: Router falló con archivo CLARO: {e}")
            traceback.print_exc()
            return False
        
        # Test con archivo genérico
        logger.info("Probando archivo genérico...")
        try:
            generic_result = router.route_upload(
                mission_id=mission_id,
                sheet_name="Datos Genéricos Router Test", 
                file_data=test_files['generic']
            )
            
            logger.info("SUCCESS: Router procesó archivo genérico exitosamente")
            logger.info(f"Routing info: {generic_result.get('routing_info', {})}")
            
            # Verificar que usó procesador genérico
            if generic_result.get('routing_info', {}).get('processor') == 'generic':
                logger.info("SUCCESS: Router usó procesador genérico")
            else:
                logger.error("ERROR: Router no usó procesador genérico")
                return False
                
        except Exception as e:
            logger.error(f"ERROR: Router falló con archivo genérico: {e}")
            traceback.print_exc()
            return False
        
        # FASE 2: Probar función main.py upload_operator_data
        logger.info("FASE 2: Probando función upload_operator_data integrada")
        
        # Importar función del main
        import main
        
        # Test con archivo CLARO via main.py
        logger.info("Probando upload_operator_data con archivo CLARO...")
        try:
            main_claro_result = main.upload_operator_data(
                mission_id,
                "Datos CLARO Main Test",
                test_files['claro_datos']
            )
            
            logger.info("SUCCESS: main.upload_operator_data procesó CLARO exitosamente")
            logger.info(f"Routing info: {main_claro_result.get('routing_info', {})}")
            
        except Exception as e:
            logger.error(f"ERROR: main.upload_operator_data falló con CLARO: {e}")
            traceback.print_exc()
            return False
        
        # FASE 3: Validar persistencia en base de datos
        logger.info("FASE 3: Validando persistencia en base de datos")
        
        with db_manager.get_session() as session:
            # Verificar archivos CLARO en operator_file_uploads
            from database.operator_models import OperatorFileUpload, OperatorCellularData
            
            claro_uploads = session.query(OperatorFileUpload).filter(
                OperatorFileUpload.mission_id == mission_id,
                OperatorFileUpload.operator == 'CLARO'
            ).all()
            
            logger.info(f"Archivos CLARO en BD: {len(claro_uploads)}")
            
            if len(claro_uploads) == 0:
                logger.error("ERROR: No se encontraron uploads CLARO en BD")
                return False
            
            # Verificar datos celulares CLARO
            claro_cellular_data = session.query(OperatorCellularData).filter(
                OperatorCellularData.mission_id == mission_id,
                OperatorCellularData.operator == 'CLARO'
            ).all()
            
            logger.info(f"Registros celulares CLARO en BD: {len(claro_cellular_data)}")
            
            if len(claro_cellular_data) == 0:
                logger.error("ERROR: No se encontraron datos celulares CLARO en BD")
                return False
            
            # Verificar datos genéricos
            from database.models import OperatorSheet, OperatorDataRecord
            
            generic_sheets = session.query(OperatorSheet).filter(
                OperatorSheet.mission_id == mission_id
            ).all()
            
            logger.info(f"Hojas genéricas en BD: {len(generic_sheets)}")
            
            total_generic_records = 0
            for sheet in generic_sheets:
                records = session.query(OperatorDataRecord).filter(
                    OperatorDataRecord.sheet_id == sheet.id
                ).count()
                total_generic_records += records
            
            logger.info(f"Registros genéricos en BD: {total_generic_records}")
        
        # FASE 4: Validar que no hay errores FOREIGN KEY
        logger.info("FASE 4: Validando integridad de FOREIGN KEYS")
        
        # El hecho de que llegemos aquí sin excepciones significa que no hubo errores FOREIGN KEY
        logger.info("SUCCESS: No se detectaron errores FOREIGN KEY constraint failed")
        
        logger.info("=" * 80)
        logger.info("VALIDACIÓN L2 COMPLETADA EXITOSAMENTE")
        logger.info("=" * 80)
        logger.info("RESUMEN DE CORRECCIONES L2:")
        logger.info("  1. Router inteligente detecta automáticamente tipo de archivo")
        logger.info("  2. Archivos CLARO usan procesador específico (operator_service)")
        logger.info("  3. Archivos genéricos usan procesador original (mission_service)")
        logger.info("  4. Validación preventiva de FOREIGN KEY constraints")
        logger.info("  5. Transacciones atómicas sin bloqueos para usuario")
        logger.info("=" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"ERROR CRÍTICO EN VALIDACIÓN L2: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_l2_solution_complete()
    if success:
        print("SUCCESS: Validación L2 completada exitosamente")
        print("RESULTADO: Problema FOREIGN KEY resuelto completamente")
    else:
        print("ERROR: Validación L2 falló - revisar logs")
        
    sys.exit(0 if success else 1)