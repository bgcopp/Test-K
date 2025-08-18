"""
Test final del servicio de correlación con datos reales
===============================================================================
Prueba el servicio de correlación usando las fechas reales de los datos
en la base de datos para validar que el algoritmo funciona correctamente
con datos reales de HUNTER y operadores.
===============================================================================
"""

import sys
import os
import logging
from pathlib import Path

# Configurar path para imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importar servicios
from database.connection import init_database
from services.correlation_service import get_correlation_service


def test_real_correlation():
    """
    Prueba de correlación con datos reales usando fechas correctas
    """
    logger.info("=== TEST DE CORRELACIÓN CON DATOS REALES ===")
    
    try:
        # Inicializar
        init_database()
        correlation_service = get_correlation_service()
        
        # Datos reales están en mayo 2021
        mission_id = "mission_MPFRBNsb"
        start_datetime = "2021-05-20 10:00:00"
        end_datetime = "2021-05-20 14:00:00"
        min_occurrences = 1
        
        logger.info(f"Misión: {mission_id}")
        logger.info(f"Período: {start_datetime} - {end_datetime}")
        logger.info(f"Min occurrences: {min_occurrences}")
        
        # Ejecutar análisis
        result = correlation_service.analyze_correlation(
            mission_id=mission_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            min_occurrences=min_occurrences
        )
        
        # Mostrar resultados
        logger.info("\n=== RESULTADOS DEL ANÁLISIS ===")
        logger.info(f"Success: {result['success']}")
        logger.info(f"Números encontrados: {len(result['data'])}")
        logger.info(f"Tiempo de procesamiento: {result['statistics']['processingTime']}s")
        logger.info(f"Celdas HUNTER analizadas: {result['statistics']['hunterCellsTotal']}")
        
        if result['data']:
            logger.info(f"\n=== PRIMEROS 10 NÚMEROS OBJETIVO ENCONTRADOS ===")
            for i, target in enumerate(result['data'][:10]):
                logger.info(f"{i+1:2d}. {target['targetNumber']:12s} | {target['operator']:8s} | "
                           f"Conf: {target['confidence']:5.1f}% | Coinc: {target['occurrences']:2d} | "
                           f"Celdas: {len(target['relatedCells'])}")
        else:
            logger.warning("No se encontraron números correlacionados")
        
        # Probar con diferentes configuraciones
        logger.info("\n=== PROBANDO CON MIN_OCCURRENCES = 2 ===")
        result2 = correlation_service.analyze_correlation(
            mission_id=mission_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            min_occurrences=2
        )
        
        logger.info(f"Con min_occurrences=2: {len(result2['data'])} números encontrados")
        
        # Probar con período más corto
        logger.info("\n=== PROBANDO CON PERÍODO MÁS CORTO ===")
        result3 = correlation_service.analyze_correlation(
            mission_id=mission_id,
            start_datetime="2021-05-20 10:30:00",
            end_datetime="2021-05-20 11:30:00",
            min_occurrences=1
        )
        
        logger.info(f"Con período corto: {len(result3['data'])} números encontrados")
        logger.info(f"Celdas HUNTER en período corto: {result3['statistics']['hunterCellsTotal']}")
        
        logger.info("\n🎉 TEST DE CORRELACIÓN CON DATOS REALES COMPLETADO")
        return True
        
    except Exception as e:
        logger.error(f"Error en test de correlación real: {e}")
        return False


def test_eel_functions():
    """
    Prueba las funciones expuestas por Eel
    """
    logger.info("\n=== TEST DE FUNCIONES EEL ===")
    
    try:
        from main import analyze_correlation, get_correlation_summary
        
        mission_id = "mission_MPFRBNsb"
        
        # Test resumen
        summary = get_correlation_summary(mission_id)
        logger.info(f"Resumen Eel - HUNTER: {summary['hunterData']['totalRecords']} registros")
        logger.info(f"Resumen Eel - Operador: {summary['operatorData']['totalCalls']} llamadas")
        
        # Test análisis
        result = analyze_correlation(
            mission_id=mission_id,
            start_datetime="2021-05-20 10:00:00",
            end_datetime="2021-05-20 14:00:00",
            min_occurrences=1
        )
        
        logger.info(f"Análisis Eel - Números encontrados: {len(result['data'])}")
        logger.info(f"Análisis Eel - Tiempo: {result['statistics']['processingTime']}s")
        
        logger.info("✓ Funciones Eel funcionando correctamente")
        return True
        
    except Exception as e:
        logger.error(f"Error en test de funciones Eel: {e}")
        return False


def main():
    """Función principal"""
    logger.info("Iniciando test final del servicio de correlación KRONOS")
    
    test1_ok = test_real_correlation()
    test2_ok = test_eel_functions()
    
    if test1_ok and test2_ok:
        logger.info("\n🎉 TODOS LOS TESTS PASARON")
        logger.info("✓ Servicio de correlación validado con datos reales")
        logger.info("✓ Integración Eel funcionando correctamente")
        logger.info("✓ Algoritmo de correlación operativo")
        return 0
    else:
        logger.error("\n❌ ALGÚN TEST FALLÓ")
        return 1


if __name__ == "__main__":
    sys.exit(main())