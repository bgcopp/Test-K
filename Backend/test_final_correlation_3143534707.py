#!/usr/bin/env python3
"""
Test final del servicio de correlación dinámico para el número 3143534707
Validación completa de la corrección del algoritmo
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import init_database, get_database_manager
from services.correlation_service_dynamic import get_correlation_service_dynamic
import logging
import json

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Inicializar base de datos
init_database()

def test_correlation_3143534707():
    """Test final del número 3143534707"""
    
    numero_objetivo = "3143534707"
    celdas_esperadas_correctas = ["53591", "51438", "56124"]  # Corregidas según análisis
    
    logger.info(f"=== TEST FINAL CORRELACIÓN {numero_objetivo} ===")
    
    # Parámetros de prueba (usar mission_id real de la BD)
    mission_id = "mission_MPFRBNsb"
    start_datetime = "2021-05-01 00:00:00"
    end_datetime = "2021-05-31 23:59:59"
    min_occurrences = 1
    
    # Obtener servicio de correlación dinámico
    correlation_service = get_correlation_service_dynamic()
    
    # Ejecutar análisis de correlación
    logger.info(f"Ejecutando análisis de correlación...")
    result = correlation_service.analyze_correlation(
        mission_id=mission_id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        min_occurrences=min_occurrences
    )
    
    if not result['success']:
        logger.error(f"Error en análisis: {result['message']}")
        return False
    
    logger.info(f"Análisis completado exitosamente:")
    logger.info(f"  - Total correlaciones: {result['total_count']}")
    logger.info(f"  - Tiempo procesamiento: {result['processing_time']:.2f}s")
    logger.info(f"  - Celdas HUNTER utilizadas: {len(result['hunter_cells_used'])}")
    
    # Buscar el número específico en los resultados
    numero_encontrado = None
    for correlation in result['data']:
        if correlation['numero_objetivo'] == numero_objetivo:
            numero_encontrado = correlation
            break
    
    if numero_encontrado:
        logger.info(f"✅ NÚMERO {numero_objetivo} ENCONTRADO:")
        logger.info(f"  - Operador: {numero_encontrado['operador']}")
        logger.info(f"  - Ocurrencias: {numero_encontrado['ocurrencias']}")
        logger.info(f"  - Celdas relacionadas: {numero_encontrado['celdas_relacionadas']}")
        logger.info(f"  - Primera detección: {numero_encontrado['primera_deteccion']}")
        logger.info(f"  - Última detección: {numero_encontrado['ultima_deteccion']}")
        logger.info(f"  - Nivel confianza: {numero_encontrado['nivel_confianza']}%")
        logger.info(f"  - Total celdas únicas: {numero_encontrado['total_celdas_unicas']}")
        
        # Validar celdas encontradas
        celdas_encontradas = sorted(numero_encontrado['celdas_relacionadas'])
        celdas_esperadas_sorted = sorted(celdas_esperadas_correctas)
        
        logger.info(f"\n--- VALIDACIÓN ---")
        logger.info(f"Celdas esperadas: {celdas_esperadas_sorted}")
        logger.info(f"Celdas encontradas: {celdas_encontradas}")
        
        if celdas_encontradas == celdas_esperadas_sorted:
            logger.info("✅ CORRELACIÓN CORRECTA - Todas las celdas coinciden")
            
            # Validar conteo de ocurrencias (debe ser 3: una por cada celda única)
            if numero_encontrado['ocurrencias'] == 3:
                logger.info("✅ CONTEO DE OCURRENCIAS CORRECTO")
            else:
                logger.error(f"❌ CONTEO INCORRECTO - Esperadas 3, encontradas {numero_encontrado['ocurrencias']}")
                return False
                
            # Validar que el nivel de confianza sea razonable
            if numero_encontrado['nivel_confianza'] >= 70.0:
                logger.info("✅ NIVEL DE CONFIANZA ADECUADO")
            else:
                logger.warning(f"⚠️ NIVEL DE CONFIANZA BAJO: {numero_encontrado['nivel_confianza']}%")
            
            return True
            
        else:
            logger.error("❌ CORRELACIÓN INCORRECTA - Discrepancia en celdas")
            
            faltantes = set(celdas_esperadas_correctas) - set(celdas_encontradas)
            extras = set(celdas_encontradas) - set(celdas_esperadas_correctas)
            
            if faltantes:
                logger.error(f"  Celdas FALTANTES: {list(faltantes)}")
            if extras:
                logger.error(f"  Celdas EXTRA: {list(extras)}")
            
            return False
    
    else:
        logger.error(f"❌ NÚMERO {numero_objetivo} NO ENCONTRADO en los resultados")
        logger.info(f"Primeros 5 resultados encontrados:")
        for i, correlation in enumerate(result['data'][:5]):
            logger.info(f"  {i+1}. {correlation['numero_objetivo']} - {correlation['ocurrencias']} ocurrencias")
        return False

def test_detailed_validation():
    """Test de validación detallada usando el método de validación específico"""
    
    numero_objetivo = "3143534707"
    logger.info(f"\n=== VALIDACIÓN DETALLADA {numero_objetivo} ===")
    
    correlation_service = get_correlation_service_dynamic()
    
    with get_database_manager().get_session() as session:
        # Obtener celdas HUNTER
        hunter_cells = correlation_service._extract_hunter_cells(session, "mission_MPFRBNsb")
        
        # Validar número específico
        validation = correlation_service.validate_number_correlation(
            session, numero_objetivo, hunter_cells
        )
        
        logger.info(f"Validación detallada:")
        logger.info(f"  - Número: {validation['numero']}")
        logger.info(f"  - Total celdas únicas: {validation['total_celdas']}")
        logger.info(f"  - Total registros: {validation['total_registros']}")
        logger.info(f"  - Celdas encontradas: {validation['celdas_unicas']}")
        
        if validation.get('error'):
            logger.error(f"  - Error: {validation['error']}")
            return False
        
        logger.info(f"\nDetalles por registro:")
        for i, detalle in enumerate(validation['detalles'][:10]):  # Mostrar máximo 10
            logger.info(f"  {i+1}. {detalle['rol']} en celda {detalle['celda']} - {detalle['fecha']} ({detalle['operador']})")
        
        return validation['total_celdas'] == 3

if __name__ == "__main__":
    logger.info("Iniciando test final de correlación...")
    
    # Test principal
    success_main = test_correlation_3143534707()
    
    # Test de validación detallada
    success_validation = test_detailed_validation()
    
    # Resultado final
    if success_main and success_validation:
        logger.info("\n🎉 TEST COMPLETADO EXITOSAMENTE")
        logger.info("El algoritmo de correlación está funcionando correctamente")
        logger.info("El número 3143534707 se correlaciona correctamente con 3 celdas únicas")
    else:
        logger.error("\n❌ TEST FALLIDO")
        if not success_main:
            logger.error("- Fallo en test principal de correlación")
        if not success_validation:
            logger.error("- Fallo en validación detallada")
    
    logger.info("\n=== FIN DEL TEST ===")