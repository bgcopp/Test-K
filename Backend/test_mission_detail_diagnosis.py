"""
DIAGNÓSTICO L2 - Análisis de Falla en Detalle de Misiones KRONOS
================================================================

Este script realiza un análisis exhaustivo del flujo de datos para identificar
el punto exacto de falla cuando se accede a los detalles de una misión.

Prueba sistemáticamente:
1. Inicialización de base de datos
2. Disponibilidad de servicios
3. Consulta de misiones
4. Funciones Eel expuestas
5. Consulta de hojas de operador
6. Mapeo de datos para frontend

Autor: Claude L2 Analysis
Fecha: 2025-01-12
"""

import os
import sys
import logging
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configurar path para imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Configurar logging detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('mission_detail_diagnosis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_database_initialization():
    """Prueba 1: Verificar inicialización de base de datos"""
    try:
        logger.info("=== PRUEBA 1: INICIALIZACIÓN DE BASE DE DATOS ===")
        
        from database.connection import init_database, get_database_manager
        
        # Ruta de base de datos
        db_path = os.path.join(current_dir, 'kronos.db')
        logger.info(f"Probando base de datos en: {db_path}")
        
        # Verificar si el archivo existe
        if os.path.exists(db_path):
            logger.info("✓ Archivo de base de datos existe")
        else:
            logger.warning("⚠ Archivo de base de datos no existe - se creará")
        
        # Intentar inicializar
        init_database(db_path, force_recreate=False)
        logger.info("✓ Base de datos inicializada correctamente")
        
        # Verificar database manager
        db_manager = get_database_manager()
        if db_manager and db_manager._initialized:
            logger.info("✓ Database manager disponible e inicializado")
        else:
            logger.error("✗ Database manager no disponible")
            return False
        
        # Probar conexión
        with db_manager.get_session() as session:
            result = session.execute("SELECT 1").fetchone()
            logger.info("✓ Conexión de base de datos funcional")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error en inicialización de BD: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_services_initialization():
    """Prueba 2: Verificar inicialización de servicios"""
    try:
        logger.info("=== PRUEBA 2: INICIALIZACIÓN DE SERVICIOS ===")
        
        from services.mission_service import get_mission_service
        from services.operator_data_service import OperatorDataService
        
        # Test Mission Service
        mission_service = get_mission_service()
        if mission_service:
            logger.info("✓ Mission Service disponible")
        else:
            logger.error("✗ Mission Service no disponible")
            return False
        
        # Test Operator Data Service
        operator_service = OperatorDataService()
        if operator_service:
            logger.info("✓ Operator Data Service disponible")
        else:
            logger.error("✗ Operator Data Service no disponible")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error en inicialización de servicios: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_mission_queries():
    """Prueba 3: Verificar consultas de misiones"""
    try:
        logger.info("=== PRUEBA 3: CONSULTAS DE MISIONES ===")
        
        from services.mission_service import get_mission_service
        
        mission_service = get_mission_service()
        
        # Obtener todas las misiones
        missions = mission_service.get_all_missions()
        logger.info(f"✓ Obtenidas {len(missions)} misiones")
        
        if missions:
            # Probar obtener misión específica
            first_mission = missions[0]
            mission_id = first_mission['id']
            logger.info(f"Probando misión específica: {mission_id}")
            
            specific_mission = mission_service.get_mission_by_id(mission_id)
            if specific_mission:
                logger.info("✓ Consulta de misión específica exitosa")
                logger.debug(f"Datos de misión: {specific_mission.keys()}")
            else:
                logger.error("✗ No se pudo obtener misión específica")
                return False
        else:
            logger.warning("⚠ No hay misiones en la base de datos")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error en consultas de misiones: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_eel_functions():
    """Prueba 4: Verificar funciones Eel expuestas"""
    try:
        logger.info("=== PRUEBA 4: FUNCIONES EEL EXPUESTAS ===")
        
        # Test funciones desde main.py
        from main import get_missions
        
        logger.info("Probando get_missions()...")
        missions = get_missions()
        logger.info(f"✓ get_missions() retornó {len(missions)} misiones")
        
        # Test funciones desde operator_data_service
        from services.operator_data_service import get_operator_sheets
        
        if missions:
            mission_id = missions[0]['id']
            logger.info(f"Probando get_operator_sheets({mission_id})...")
            sheets_result = get_operator_sheets(mission_id)
            
            if isinstance(sheets_result, dict) and 'success' in sheets_result:
                if sheets_result['success']:
                    logger.info(f"✓ get_operator_sheets() exitoso - {len(sheets_result.get('data', []))} hojas")
                else:
                    logger.warning(f"⚠ get_operator_sheets() falló: {sheets_result.get('error', 'Error desconocido')}")
            else:
                logger.info(f"✓ get_operator_sheets() retornó formato legacy: {type(sheets_result)}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error en funciones Eel: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_operator_data_flow():
    """Prueba 5: Verificar flujo completo de datos de operador"""
    try:
        logger.info("=== PRUEBA 5: FLUJO DE DATOS DE OPERADOR ===")
        
        from services.mission_service import get_mission_service
        from services.operator_data_service import get_operator_sheets
        
        mission_service = get_mission_service()
        missions = mission_service.get_all_missions()
        
        if not missions:
            logger.warning("⚠ No hay misiones para probar")
            return True
        
        mission_id = missions[0]['id']
        logger.info(f"Probando flujo con misión: {mission_id}")
        
        # Test 1: Consulta directa a base de datos
        logger.info("Test 1: Consulta directa a BD")
        from database.connection import get_db_connection
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM operator_data_sheets 
                WHERE mission_id = ?
            """, (mission_id,))
            
            count = cursor.fetchone()[0]
            logger.info(f"✓ Consulta directa BD: {count} hojas de operador para misión {mission_id}")
        
        # Test 2: A través de servicio
        logger.info("Test 2: A través de servicio")
        sheets_result = get_operator_sheets(mission_id)
        
        if isinstance(sheets_result, dict):
            if sheets_result.get('success'):
                sheets = sheets_result.get('data', [])
                logger.info(f"✓ Servicio retornó {len(sheets)} hojas")
                
                # Detalles de cada hoja
                for i, sheet in enumerate(sheets):
                    logger.debug(f"  Hoja {i+1}: {sheet.get('file_name', 'N/A')} - {sheet.get('operator', 'N/A')} - {sheet.get('processing_status', 'N/A')}")
            else:
                logger.warning(f"⚠ Servicio falló: {sheets_result.get('error', 'Error desconocido')}")
        else:
            logger.warning(f"⚠ Formato de respuesta inesperado: {type(sheets_result)}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error en flujo de datos de operador: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_frontend_compatibility():
    """Prueba 6: Verificar compatibilidad con frontend"""
    try:
        logger.info("=== PRUEBA 6: COMPATIBILIDAD CON FRONTEND ===")
        
        from services.mission_service import get_mission_service
        from services.operator_data_service import get_operator_sheets
        
        mission_service = get_mission_service()
        missions = mission_service.get_all_missions()
        
        if not missions:
            logger.warning("⚠ No hay misiones para probar")
            return True
        
        # Test estructura de misión
        mission = missions[0]
        required_fields = ['id', 'code', 'name', 'description', 'status']
        
        logger.info("Verificando estructura de misión...")
        for field in required_fields:
            if field in mission:
                logger.debug(f"✓ Campo '{field}': {type(mission[field])}")
            else:
                logger.error(f"✗ Campo faltante: '{field}'")
                return False
        
        # Test estructura de hojas de operador
        mission_id = mission['id']
        sheets_result = get_operator_sheets(mission_id)
        
        if isinstance(sheets_result, dict) and sheets_result.get('success'):
            sheets = sheets_result.get('data', [])
            if sheets:
                sheet = sheets[0]
                expected_sheet_fields = ['id', 'file_name', 'operator', 'processing_status']
                
                logger.info("Verificando estructura de hoja de operador...")
                for field in expected_sheet_fields:
                    if field in sheet:
                        logger.debug(f"✓ Campo hoja '{field}': {type(sheet[field])}")
                    else:
                        logger.error(f"✗ Campo hoja faltante: '{field}'")
                        return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error en compatibilidad frontend: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def run_comprehensive_diagnosis():
    """Ejecuta diagnóstico completo del sistema"""
    
    logger.info("KRONOS - DIAGNÓSTICO COMPLETO L2")
    logger.info("=" * 50)
    
    tests = [
        ("Inicialización Base de Datos", test_database_initialization),
        ("Inicialización Servicios", test_services_initialization),
        ("Consultas de Misiones", test_mission_queries),
        ("Funciones Eel Expuestas", test_eel_functions),
        ("Flujo Datos Operador", test_operator_data_flow),
        ("Compatibilidad Frontend", test_frontend_compatibility)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"Ejecutando: {test_name}")
        try:
            result = test_func()
            results[test_name] = result
            logger.info(f"{'✓ PASSED' if result else '✗ FAILED'}: {test_name}")
        except Exception as e:
            results[test_name] = False
            logger.error(f"✗ CRITICAL FAILURE: {test_name} - {e}")
        
        logger.info("-" * 30)
    
    # Resumen final
    logger.info("RESUMEN FINAL")
    logger.info("=" * 50)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        logger.info(f"{status}: {test_name}")
    
    logger.info("-" * 30)
    logger.info(f"TOTAL: {passed}/{total} pruebas exitosas")
    
    if passed == total:
        logger.info("🎉 SISTEMA OPERATIVO - No se detectaron fallas críticas")
        return True
    else:
        logger.error("🚨 SISTEMA CON FALLAS - Revisar logs para detalles")
        return False

if __name__ == "__main__":
    try:
        success = run_comprehensive_diagnosis()
        
        if success:
            logger.info("Diagnóstico completado exitosamente")
            sys.exit(0)
        else:
            logger.error("Diagnóstico detectó fallas críticas")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("Diagnóstico interrumpido por usuario")
        sys.exit(2)
    except Exception as e:
        logger.error(f"Error crítico en diagnóstico: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(3)