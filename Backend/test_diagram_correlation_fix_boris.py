#!/usr/bin/env python3
"""
PRUEBA ESPECÍFICA PARA CORRECCIÓN BORIS - DIAGRAMA DE CORRELACIÓN
===============================================================================
Script para validar que la corrección del diagrama de correlación funciona
correctamente y muestra SOLO las interacciones directas del número objetivo.

PROBLEMA ORIGINAL:
- Número 3113330727 mostraba 255 nodos (inflación por celdas compartidas)
- El algoritmo buscaba "números que usaron las mismas celdas que HUNTER"

CORRECCIÓN IMPLEMENTADA:
- Buscar SOLO llamadas donde 3113330727 fue origen O destino
- Resultado esperado: máximo 3-5 nodos (contactos directos)

FECHA: 2025-08-18
AUTOR: Claude Code para Boris
===============================================================================
"""

import os
import sys
import logging
import json
from datetime import datetime

# Configurar path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from database.connection import init_database, get_database_manager
from services.diagram_correlation_service import get_diagram_correlation_service

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_diagram_correlation_fix():
    """
    Prueba específica para validar la corrección del diagrama de correlación
    """
    try:
        logger.info("=== INICIANDO PRUEBA DE CORRECCIÓN DE DIAGRAMA ===")
        
        # Inicializar base de datos
        db_path = os.path.join(current_dir, 'kronos.db')
        init_database(db_path, force_recreate=False)
        
        # Obtener servicio
        diagram_service = get_diagram_correlation_service()
        
        # Parámetros de prueba
        mission_id = "mission_MPFRBNsb"
        numero_objetivo = "3113330727"  # Número específico del problema
        start_datetime = "2021-05-01 00:00:00"
        end_datetime = "2021-05-31 23:59:59"
        
        logger.info(f"Misión: {mission_id}")
        logger.info(f"Número objetivo: {numero_objetivo}")
        logger.info(f"Período: {start_datetime} - {end_datetime}")
        
        # Ejecutar análisis
        logger.info("Ejecutando análisis de diagrama...")
        start_time = datetime.now()
        
        result = diagram_service.get_correlation_diagram_data(
            mission_id=mission_id,
            numero_objetivo=numero_objetivo,
            start_datetime=start_datetime,
            end_datetime=end_datetime
        )
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Validar resultado
        logger.info("=== RESULTADO DE LA CORRECCIÓN ===")
        logger.info(f"Success: {result.get('success', False)}")
        logger.info(f"Nodos encontrados: {len(result.get('nodos', []))}")
        logger.info(f"Aristas encontradas: {len(result.get('aristas', []))}")
        logger.info(f"Tiempo procesamiento: {processing_time:.3f}s")
        
        # Análisis detallado de nodos
        nodos = result.get('nodos', [])
        if nodos:
            logger.info("=== ANÁLISIS DE NODOS ===")
            nodo_objetivo = None
            contactos = []
            
            for nodo in nodos:
                if nodo.get('tipo') == 'objetivo':
                    nodo_objetivo = nodo
                    logger.info(f"OBJETIVO: {nodo['numero']} - {nodo['total_comunicaciones']} comunicaciones")
                else:
                    contactos.append(nodo)
                    logger.info(f"CONTACTO: {nodo['numero']} - {nodo['total_comunicaciones']} comunicaciones")
            
            logger.info(f"Total contactos directos: {len(contactos)}")
            
            # Análisis de aristas
            aristas = result.get('aristas', [])
            if aristas:
                logger.info("=== ANÁLISIS DE COMUNICACIONES ===")
                tipos_trafico = {}
                direcciones = {}
                
                for arista in aristas:
                    tipo = arista.get('tipo_comunicacion', 'UNKNOWN')
                    direccion = arista.get('direccion', 'UNKNOWN')
                    
                    tipos_trafico[tipo] = tipos_trafico.get(tipo, 0) + 1
                    direcciones[direccion] = direcciones.get(direccion, 0) + 1
                
                logger.info(f"Tipos de tráfico: {tipos_trafico}")
                logger.info(f"Direcciones: {direcciones}")
        
        # Estadísticas
        estadisticas = result.get('estadisticas', {})
        if estadisticas:
            logger.info("=== ESTADÍSTICAS ===")
            logger.info(f"Total comunicaciones: {estadisticas.get('total_comunicaciones', 0)}")
            logger.info(f"Contactos únicos: {estadisticas.get('contactos_unicos', 0)}")
            logger.info(f"Celdas HUNTER involucradas: {estadisticas.get('celdas_hunter_involucradas', 0)}")
        
        # Validación de la corrección
        logger.info("=== VALIDACIÓN DE CORRECCIÓN ===")
        total_nodos = len(result.get('nodos', []))
        
        if total_nodos <= 10:  # Máximo esperado después de la corrección
            logger.info("✅ CORRECCIÓN EXITOSA: Número de nodos dentro del rango esperado")
            validation_status = "EXITOSA"
        elif total_nodos <= 50:
            logger.warning("⚠️ CORRECCIÓN PARCIAL: Nodos reducidos pero aún pueden optimizarse")
            validation_status = "PARCIAL"
        else:
            logger.error("❌ CORRECCIÓN FALLIDA: Demasiados nodos, posible inflación persistente")
            validation_status = "FALLIDA"
        
        # Crear reporte de resultado
        report = {
            'fecha_prueba': datetime.now().isoformat(),
            'numero_objetivo': numero_objetivo,
            'mision': mission_id,
            'periodo': f"{start_datetime} - {end_datetime}",
            'resultado_correccion': {
                'status': validation_status,
                'nodos_encontrados': total_nodos,
                'aristas_encontradas': len(result.get('aristas', [])),
                'tiempo_procesamiento': processing_time,
                'success': result.get('success', False)
            },
            'analisis_detallado': {
                'nodos': result.get('nodos', []),
                'estadisticas': estadisticas,
                'metadata': result.get('metadata', {})
            }
        }
        
        # Guardar reporte
        report_file = f"diagram_correlation_fix_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Reporte guardado en: {report_file}")
        
        return validation_status == "EXITOSA"
        
    except Exception as e:
        logger.error(f"Error en prueba de diagrama: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    logger.info("INICIANDO PRUEBA DE CORRECCIÓN BORIS - DIAGRAMA DE CORRELACIÓN")
    
    success = test_diagram_correlation_fix()
    
    if success:
        logger.info("🎉 PRUEBA COMPLETADA EXITOSAMENTE - CORRECCIÓN VALIDADA")
        sys.exit(0)
    else:
        logger.error("💥 PRUEBA FALLIDA - REVISAR CORRECCIÓN")
        sys.exit(1)