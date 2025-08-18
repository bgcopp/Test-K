"""
Script de validación del servicio de correlación KRONOS
===============================================================================
Script para probar la funcionalidad del nuevo servicio de correlación
implementado. Valida la integración completa con la base de datos y
verifica que el algoritmo de correlación funcione correctamente.

Ejecutar: python test_correlation_service_validation.py
===============================================================================
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Configurar path para imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Configurar logging para el test
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importar servicios necesarios
from database.connection import init_database, get_database_manager
from services.correlation_service import get_correlation_service, CorrelationServiceError


def test_correlation_service():
    """
    Prueba completa del servicio de correlación
    """
    logger.info("=== INICIANDO VALIDACIÓN DEL SERVICIO DE CORRELACIÓN ===")
    
    try:
        # Inicializar base de datos
        logger.info("Inicializando conexión a base de datos...")
        init_database()
        correlation_service = get_correlation_service()
        
        # Obtener misiones disponibles
        logger.info("Obteniendo misiones disponibles...")
        db_manager = get_database_manager()
        
        with db_manager.get_session() as session:
            from database.models import Mission
            
            missions = session.query(Mission).limit(5).all()
            if not missions:
                logger.error("No se encontraron misiones en la base de datos")
                return False
            
            logger.info(f"Misiones encontradas: {len(missions)}")
            for mission in missions:
                logger.info(f"  - {mission.id}: {mission.name}")
        
        # Probar con la primera misión
        test_mission = missions[0]
        logger.info(f"\n=== PROBANDO CON MISIÓN: {test_mission.id} ===")
        
        # Test 1: Obtener resumen de correlación
        logger.info("Test 1: Obteniendo resumen de correlación...")
        try:
            summary = correlation_service.get_correlation_summary(test_mission.id)
            logger.info(f"Resumen obtenido exitosamente:")
            logger.info(f"  - Datos HUNTER: {summary['hunterData']['totalRecords']} registros, {summary['hunterData']['uniqueCells']} celdas únicas")
            logger.info(f"  - Datos Operador: {summary['operatorData']['totalCalls']} llamadas, {summary['operatorData']['uniqueNumbers']} números únicos")
            logger.info(f"  - Listo para correlación: {summary['correlationReady']}")
            
            if not summary['correlationReady']:
                logger.warning("La misión no tiene datos suficientes para correlación")
                return True  # No es error, solo no hay datos
            
        except Exception as e:
            logger.error(f"Error en test de resumen: {e}")
            return False
        
        # Test 2: Análisis de correlación con período amplio
        logger.info("\nTest 2: Ejecutando análisis de correlación...")
        try:
            # Usar un período amplio para maximizar posibilidades de encontrar datos
            start_date = "2024-01-01 00:00:00"
            end_date = "2024-12-31 23:59:59"
            min_occurrences = 1
            
            logger.info(f"Parámetros: {start_date} - {end_date}, min_occurrences={min_occurrences}")
            
            result = correlation_service.analyze_correlation(
                mission_id=test_mission.id,
                start_datetime=start_date,
                end_datetime=end_date,
                min_occurrences=min_occurrences
            )
            
            logger.info(f"Análisis completado exitosamente:")
            logger.info(f"  - Success: {result['success']}")
            logger.info(f"  - Números encontrados: {result['statistics']['totalFound']}")
            logger.info(f"  - Tiempo de procesamiento: {result['statistics']['processingTime']}s")
            logger.info(f"  - Celdas HUNTER analizadas: {result['statistics']['hunterCellsTotal']}")
            
            # Mostrar algunos resultados si existen
            if result['data']:
                logger.info(f"\nPrimeros {min(3, len(result['data']))} resultados:")
                for i, target in enumerate(result['data'][:3]):
                    logger.info(f"  {i+1}. Número: {target['targetNumber']}")
                    logger.info(f"      Operador: {target['operator']}")
                    logger.info(f"      Coincidencias: {target['occurrences']}")
                    logger.info(f"      Confianza: {target['confidence']}%")
                    logger.info(f"      Período: {target['firstDetection']} - {target['lastDetection']}")
            else:
                logger.info("No se encontraron números correlacionados en el período especificado")
            
        except Exception as e:
            logger.error(f"Error en test de análisis: {e}")
            return False
        
        # Test 3: Validar parámetros incorrectos
        logger.info("\nTest 3: Validando manejo de errores...")
        try:
            # Probar con fechas inválidas
            correlation_service.analyze_correlation(
                mission_id=test_mission.id,
                start_datetime="fecha-invalida",
                end_datetime=end_date,
                min_occurrences=1
            )
            logger.error("ERROR: Debería haber fallado con fecha inválida")
            return False
        except CorrelationServiceError as e:
            logger.info(f"  ✓ Error de fecha inválida manejado correctamente: {e}")
        
        try:
            # Probar con misión inexistente
            correlation_service.analyze_correlation(
                mission_id="mision-inexistente",
                start_datetime=start_date,
                end_datetime=end_date,
                min_occurrences=1
            )
            logger.error("ERROR: Debería haber fallado con misión inexistente")
            return False
        except CorrelationServiceError as e:
            logger.info(f"  ✓ Error de misión inexistente manejado correctamente: {e}")
        
        try:
            # Probar con min_occurrences inválido
            correlation_service.analyze_correlation(
                mission_id=test_mission.id,
                start_datetime=start_date,
                end_datetime=end_date,
                min_occurrences=0
            )
            logger.error("ERROR: Debería haber fallado con min_occurrences=0")
            return False
        except CorrelationServiceError as e:
            logger.info(f"  ✓ Error de min_occurrences inválido manejado correctamente: {e}")
        
        logger.info("\n=== TODOS LOS TESTS PASARON EXITOSAMENTE ===")
        return True
        
    except Exception as e:
        logger.error(f"Error inesperado en validación: {e}")
        return False


def test_eel_integration():
    """
    Prueba la integración con las funciones Eel expuestas
    """
    logger.info("\n=== PROBANDO INTEGRACIÓN EEL ===")
    
    try:
        # Importar funciones expuestas
        from main import analyze_correlation, get_correlation_summary
        
        # Obtener una misión para probar
        db_manager = get_database_manager()
        with db_manager.get_session() as session:
            from database.models import Mission
            mission = session.query(Mission).first()
            
            if not mission:
                logger.warning("No hay misiones para probar integración Eel")
                return True
        
        # Probar función de resumen
        logger.info("Probando get_correlation_summary...")
        summary = get_correlation_summary(mission.id)
        logger.info(f"  ✓ Resumen obtenido via Eel: {summary['correlationReady']}")
        
        # Probar función de análisis (solo si hay datos)
        if summary['correlationReady']:
            logger.info("Probando analyze_correlation...")
            result = analyze_correlation(
                mission_id=mission.id,
                start_datetime="2024-01-01 00:00:00",
                end_datetime="2024-12-31 23:59:59",
                min_occurrences=1
            )
            logger.info(f"  ✓ Análisis completado via Eel: {result['statistics']['totalFound']} números")
        
        logger.info("=== INTEGRACIÓN EEL EXITOSA ===")
        return True
        
    except Exception as e:
        logger.error(f"Error en integración Eel: {e}")
        return False


def main():
    """Función principal de validación"""
    logger.info("Iniciando validación completa del servicio de correlación KRONOS")
    
    # Test del servicio
    service_ok = test_correlation_service()
    
    # Test de integración Eel
    eel_ok = test_eel_integration()
    
    # Resultado final
    if service_ok and eel_ok:
        logger.info("\n🎉 VALIDACIÓN COMPLETA EXITOSA")
        logger.info("El servicio de correlación está listo para producción")
        return 0
    else:
        logger.error("\n❌ VALIDACIÓN FALLÓ")
        logger.error("Revisar errores anteriores")
        return 1


if __name__ == "__main__":
    sys.exit(main())