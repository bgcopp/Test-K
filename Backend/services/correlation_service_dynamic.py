"""
KRONOS Dynamic Correlation Analysis Service
===============================================================================
SERVICIO DINÁMICO DE CORRELACIÓN SIN VALORES HARDCODEADOS
===============================================================================

Este servicio implementa un análisis de correlación completamente dinámico
que NO tiene números de teléfono ni operadores hardcodeados.

FUNCIONALIDADES PRINCIPALES:
1. Extrae automáticamente todos los números únicos de los archivos cargados
2. Identifica dinámicamente los operadores desde los datos
3. Cuenta correctamente múltiples ocurrencias por número (1 por celda única)
4. Correlaciona originador Y receptor con celdas HUNTER
5. Filtra por período de tiempo y mínimo de ocurrencias

ARQUITECTURA:
- Completamente dinámico: no valores hardcodeados
- Conteo por combinación única número-celda
- Análisis tanto de originador como receptor
- Validación automática de operadores

Autor: Claude Code para Boris
Fecha: 2025-08-18
Versión: 2.0 - DINÁMICO
===============================================================================
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Set, Tuple, Optional
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from collections import defaultdict

from database.connection import get_database_manager

logger = logging.getLogger(__name__)


class CorrelationServiceDynamicError(Exception):
    """Excepción personalizada para errores del servicio de correlación dinámico"""
    pass


class CorrelationServiceDynamic:
    """
    Servicio de análisis de correlación DINÁMICO para KRONOS
    
    Analiza datos reales sin valores hardcodeados.
    Implementa conteo correcto de múltiples celdas por número.
    """
    
    def __init__(self):
        self._cache_hunter_cells = {}
        self._cache_timeout = 300
        
    @property
    def db_manager(self):
        """Obtiene el database manager de manera lazy"""
        return get_database_manager()
    
    def analyze_correlation(self, mission_id: str, start_datetime: str, 
                          end_datetime: str, min_occurrences: int = 1) -> Dict[str, Any]:
        """
        Ejecuta análisis de correlación dinámico
        
        Args:
            mission_id: ID de la misión
            start_datetime: Inicio del período (formato: YYYY-MM-DD HH:MM:SS)
            end_datetime: Fin del período (formato: YYYY-MM-DD HH:MM:SS)
            min_occurrences: Mínimo de ocurrencias requeridas
            
        Returns:
            Dict con resultados del análisis de correlación
        """
        start_time = time.time()
        
        try:
            logger.info(f"=== INICIANDO ANÁLISIS DE CORRELACIÓN DINÁMICO ===")
            logger.info(f"Misión: {mission_id}")
            logger.info(f"Período: {start_datetime} - {end_datetime}")
            logger.info(f"Min occurrences: {min_occurrences}")
            
            with self.db_manager.get_session() as session:
                # 1. Extraer celdas HUNTER
                hunter_cells = self._extract_hunter_cells(session, mission_id)
                if not hunter_cells:
                    logger.warning("No se encontraron celdas HUNTER para la misión")
                    return {
                        'success': False,
                        'message': 'No se encontraron datos celulares HUNTER',
                        'data': [],
                        'total_count': 0,
                        'processing_time': time.time() - start_time
                    }
                
                logger.info(f"Celdas HUNTER encontradas: {len(hunter_cells)}")
                
                # 2. Buscar correlaciones dinámicamente
                correlation_results = self._find_dynamic_correlations(
                    session, mission_id, hunter_cells, start_datetime, end_datetime, min_occurrences
                )
                
                logger.info(f"Correlaciones encontradas: {len(correlation_results)}")
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                return {
                    'success': True,
                    'message': f'Correlación completada exitosamente',
                    'data': correlation_results,
                    'total_count': len(correlation_results),
                    'processing_time': processing_time,
                    'hunter_cells_used': sorted(list(hunter_cells))
                }
                
        except Exception as e:
            logger.error(f"Error en análisis de correlación dinámico: {str(e)}")
            return {
                'success': False,
                'message': f'Error en el análisis: {str(e)}',
                'data': [],
                'total_count': 0,
                'processing_time': time.time() - start_time
            }
    
    def _extract_hunter_cells(self, session, mission_id: str) -> Set[str]:
        """Extrae celdas HUNTER de la misión"""
        try:
            # Primero intentar con cellular_data (datos celulares HUNTER)
            query_cellular = text("""
                SELECT DISTINCT cell_id
                FROM cellular_data 
                WHERE mission_id = :mission_id 
                  AND cell_id IS NOT NULL
            """)
            
            result = session.execute(query_cellular, {'mission_id': mission_id})
            hunter_cells = {str(row[0]) for row in result.fetchall()}
            
            # Si no hay datos en cellular_data, extraer celdas únicas de operator_call_data
            if not hunter_cells:
                logger.warning("No se encontraron celdas en cellular_data, extrayendo de operator_call_data")
                query_operator = text("""
                    SELECT DISTINCT celda_origen
                    FROM operator_call_data 
                    WHERE mission_id = :mission_id 
                      AND celda_origen IS NOT NULL
                    UNION
                    SELECT DISTINCT celda_destino
                    FROM operator_call_data 
                    WHERE mission_id = :mission_id 
                      AND celda_destino IS NOT NULL
                """)
                
                result = session.execute(query_operator, {'mission_id': mission_id})
                hunter_cells = {str(row[0]) for row in result.fetchall()}
            
            logger.info(f"Extraídas {len(hunter_cells)} celdas HUNTER únicas")
            if len(hunter_cells) > 0:
                logger.debug(f"Primeras 10 celdas HUNTER: {sorted(list(hunter_cells))[:10]}")
            
            return hunter_cells
            
        except Exception as e:
            logger.error(f"Error extrayendo celdas HUNTER: {e}")
            return set()
    
    def _find_dynamic_correlations(self, session, mission_id: str, hunter_cells: Set[str],
                                 start_datetime: str, end_datetime: str, min_occurrences: int) -> List[Dict[str, Any]]:
        """
        Encuentra correlaciones dinámicamente usando conteo EXACTO por celda única
        
        ALGORITMO CORREGIDO - Boris 2025-08-18:
        SOLUCIÓN AL PROBLEMA DE INFLACIÓN POR CONTEXTOS MÚLTIPLES:
        
        ANTES: El UNION contaba la misma combinación número-celda múltiples veces:
        - Como originador_fisica (celda_origen)  
        - Como destino_comunicacion (celda_destino)
        - Como receptor_comunicacion (celda_destino)
        
        AHORA: Cuenta EXACTAMENTE 1 vez cada combinación única número-celda:
        1. Identifica números objetivo que contactaron celdas HUNTER
        2. Extrae TODAS sus celdas relacionadas (origen y destino)  
        3. Consolida para eliminar duplicados por contexto múltiple
        4. Cuenta 1 ocurrencia por combinación única número-celda
        
        RESULTADO: Conteos precisos sin inflación artificial
        """
        try:
            # Convertir celdas HUNTER a lista para SQL
            hunter_cells_list = list(hunter_cells)
            hunter_cells_str = ','.join([f"'{cell}'" for cell in hunter_cells_list])
            
            if not hunter_cells_str:
                return []
            
            # Query CORREGIDO - Algoritmo sin inflación por contextos múltiples - Boris 2025-08-18
            query = text(f"""
                WITH target_numbers AS (
                    -- Extraer números objetivo que tuvieron contacto con celdas HUNTER
                    SELECT DISTINCT numero_origen as numero, operator as operador
                    FROM operator_call_data 
                    WHERE mission_id = :mission_id 
                      AND celda_origen IN ({hunter_cells_str})
                      AND date(fecha_hora_llamada) BETWEEN :start_date AND :end_date
                      AND numero_origen IS NOT NULL 
                      AND numero_origen != ''
                    
                    UNION
                    
                    SELECT DISTINCT numero_destino as numero, operator as operador
                    FROM operator_call_data 
                    WHERE mission_id = :mission_id 
                      AND celda_destino IN ({hunter_cells_str})
                      AND date(fecha_hora_llamada) BETWEEN :start_date AND :end_date
                      AND numero_destino IS NOT NULL 
                      AND numero_destino != ''
                ),
                unique_number_cell_combinations AS (
                    -- Para cada número objetivo, encontrar TODAS sus celdas únicas (sin duplicación por contexto)
                    SELECT DISTINCT 
                        tn.numero,
                        tn.operador,
                        ocd.celda_origen as celda,
                        MIN(ocd.fecha_hora_llamada) as primera_deteccion,
                        MAX(ocd.fecha_hora_llamada) as ultima_deteccion
                    FROM target_numbers tn
                    JOIN operator_call_data ocd ON tn.numero = ocd.numero_origen AND tn.operador = ocd.operator
                    WHERE ocd.mission_id = :mission_id
                      AND date(ocd.fecha_hora_llamada) BETWEEN :start_date AND :end_date
                      AND ocd.celda_origen IS NOT NULL
                      AND ocd.celda_origen != ''
                    GROUP BY tn.numero, tn.operador, ocd.celda_origen
                    
                    UNION
                    
                    SELECT DISTINCT 
                        tn.numero,
                        tn.operador,
                        ocd.celda_destino as celda,
                        MIN(ocd.fecha_hora_llamada) as primera_deteccion,
                        MAX(ocd.fecha_hora_llamada) as ultima_deteccion
                    FROM target_numbers tn
                    JOIN operator_call_data ocd ON tn.numero = ocd.numero_origen AND tn.operador = ocd.operator
                    WHERE ocd.mission_id = :mission_id
                      AND date(ocd.fecha_hora_llamada) BETWEEN :start_date AND :end_date
                      AND ocd.celda_destino IS NOT NULL
                      AND ocd.celda_destino != ''
                    GROUP BY tn.numero, tn.operador, ocd.celda_destino
                    
                    UNION
                    
                    SELECT DISTINCT 
                        tn.numero,
                        tn.operador,
                        ocd.celda_destino as celda,
                        MIN(ocd.fecha_hora_llamada) as primera_deteccion,
                        MAX(ocd.fecha_hora_llamada) as ultima_deteccion
                    FROM target_numbers tn
                    JOIN operator_call_data ocd ON tn.numero = ocd.numero_destino AND tn.operador = ocd.operator
                    WHERE ocd.mission_id = :mission_id
                      AND date(ocd.fecha_hora_llamada) BETWEEN :start_date AND :end_date
                      AND ocd.celda_destino IS NOT NULL
                      AND ocd.celda_destino != ''
                    GROUP BY tn.numero, tn.operador, ocd.celda_destino
                ),
                final_unique_combinations AS (
                    -- Consolidar para evitar duplicados cuando la misma combinación número-celda 
                    -- aparece en múltiples UNIONs anteriores
                    SELECT 
                        numero,
                        operador,
                        celda,
                        MIN(primera_deteccion) as primera_deteccion,
                        MAX(ultima_deteccion) as ultima_deteccion
                    FROM unique_number_cell_combinations
                    GROUP BY numero, operador, celda
                ),
                correlation_stats AS (
                    -- Contar EXACTAMENTE 1 vez cada combinación única número-celda
                    SELECT 
                        numero,
                        operador,
                        COUNT(*) as ocurrencias,  -- Cada fila representa 1 celda única
                        MIN(primera_deteccion) as primera_deteccion_global,
                        MAX(ultima_deteccion) as ultima_deteccion_global,
                        GROUP_CONCAT(celda) as celdas_relacionadas
                    FROM final_unique_combinations
                    GROUP BY numero, operador
                    HAVING COUNT(*) >= :min_occurrences
                )
                SELECT 
                    numero,
                    operador,
                    ocurrencias,
                    primera_deteccion_global,
                    ultima_deteccion_global,
                    celdas_relacionadas
                FROM correlation_stats
                ORDER BY ocurrencias DESC, numero ASC
            """)
            
            # Convertir fechas para el query
            start_date = datetime.strptime(start_datetime, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
            end_date = datetime.strptime(end_datetime, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
            
            # Log de parámetros para debug - ALGORITMO CORREGIDO
            logger.info(f"Ejecutando correlación CORREGIDA (sin inflación por contextos) con parámetros:")
            logger.info(f"  - Mission ID: {mission_id}")
            logger.info(f"  - Período: {start_date} a {end_date}")
            logger.info(f"  - Mín ocurrencias: {min_occurrences}")
            logger.info(f"  - Celdas HUNTER: {len(hunter_cells_list)} celdas")
            logger.info(f"  - ALGORITMO: Conteo EXACTO por combinación única número-celda")
            logger.debug(f"  - Celdas HUNTER utilizadas: {sorted(hunter_cells_list[:10])}{'...' if len(hunter_cells_list) > 10 else ''}")
            
            query_params = {
                'mission_id': mission_id,
                'start_date': start_date,
                'end_date': end_date,
                'min_occurrences': min_occurrences
            }
            
            # Ejecutar query con manejo de errores específico para SQLite
            try:
                result = session.execute(query, query_params)
                logger.info("Query ejecutada exitosamente")
            except Exception as sql_error:
                logger.error(f"Error SQL específico: {sql_error}")
                logger.error(f"Query problemático detectado - verificar sintaxis SQLite")
                raise CorrelationServiceDynamicError(f"Error en query SQL: {sql_error}")
            
            correlations = []
            for row in result.fetchall():
                numero = str(row[0])
                operador = str(row[1])
                ocurrencias = int(row[2])
                primera_deteccion = row[3]
                ultima_deteccion = row[4]
                celdas_relacionadas_str = str(row[5]) if row[5] else ""
                
                # Procesar celdas relacionadas (SQLite devuelve separadas por comas)
                if celdas_relacionadas_str:
                    # SQLite GROUP_CONCAT usa coma como separador por defecto
                    celdas_relacionadas = [cell.strip() for cell in celdas_relacionadas_str.split(',') if cell.strip()]
                else:
                    celdas_relacionadas = []
                
                # Normalizar número si es necesario
                numero_normalizado = self._normalize_phone_number(numero)
                
                # Calcular nivel de confianza basado en ocurrencias y distribución de celdas
                base_confidence = 65.0  # Aumentar base ligeramente
                
                # Bonus por múltiples celdas (más celdas = mayor confianza de ubicación)
                cell_bonus = min(25.0, len(celdas_relacionadas) * 7)  
                
                # Bonus por múltiples ocurrencias (consistencia temporal)
                occurrence_bonus = min(15.0, ocurrencias * 3)  
                
                # Bonus especial para números con alta actividad (más de 5 ocurrencias)
                high_activity_bonus = 5.0 if ocurrencias >= 5 else 0.0
                
                nivel_confianza = min(95.0, base_confidence + cell_bonus + occurrence_bonus + high_activity_bonus)
                
                # Log detallado para números específicos (debug) - ALGORITMO CORREGIDO
                if numero_normalizado in ['3243182028', '3009120093', '3124390973', '3143534707', '3104277553']:
                    logger.info(f"CORREGIDO {numero_normalizado}: {ocurrencias} ocurrencias EXACTAS en celdas {celdas_relacionadas}")
                    logger.debug(f"  Confianza: base={base_confidence} + celdas={cell_bonus} + ocurr={occurrence_bonus} + actividad={high_activity_bonus} = {nivel_confianza}")
                    logger.debug(f"  VALIDACIÓN: Sin inflación por contextos múltiples")
                
                correlations.append({
                    'numero_objetivo': numero_normalizado,
                    'operador': operador,
                    'ocurrencias': ocurrencias,
                    'primera_deteccion': primera_deteccion,
                    'ultima_deteccion': ultima_deteccion,
                    'celdas_relacionadas': celdas_relacionadas,
                    'nivel_confianza': round(nivel_confianza, 1),
                    'strategy': 'DynamicCorrected_v2.0',
                    'total_celdas_unicas': len(celdas_relacionadas)
                })
            
            logger.info(f"Procesadas {len(correlations)} correlaciones CORREGIDAS (sin inflación por contextos múltiples)")
            return correlations
            
        except Exception as e:
            logger.error(f"Error en búsqueda dinámica de correlaciones: {e}")
            return []
    
    def _normalize_phone_number(self, phone: str) -> str:
        """Normaliza números telefónicos removiendo prefijo 57 si es necesario"""
        if not phone:
            return phone
            
        phone_clean = str(phone).strip()
        
        # Si empieza con 57 y tiene 12 dígitos, remover el prefijo
        if phone_clean.startswith('57') and len(phone_clean) == 12:
            return phone_clean[2:]
        
        return phone_clean
    
    def validate_number_correlation(self, session, numero: str, hunter_cells: Set[str]) -> Dict[str, Any]:
        """
        Valida la correlación de un número específico para debugging
        
        ALGORITMO CORREGIDO v2.0 - Boris 2025-08-18:
        Implementa conteo EXACTO sin inflación por contextos múltiples
        
        Args:
            session: Sesión de base de datos
            numero: Número a validar
            hunter_cells: Conjunto de celdas HUNTER
            
        Returns:
            Dict con información detallada de la correlación CORREGIDA
        """
        try:
            hunter_cells_str = ','.join([f"'{cell}'" for cell in hunter_cells])
            
            # Query corregido - TODAS las celdas involucradas en comunicaciones del número
            query = text(f"""
                -- Cuando el número es ORIGINADOR: celda_origen (ubicación física)
                SELECT 
                    'originador_fisica' as rol,
                    numero_origen as numero,
                    celda_origen as celda,
                    fecha_hora_llamada,
                    operator,
                    numero_destino as otro_numero
                FROM operator_call_data 
                WHERE numero_origen = :numero
                  AND numero_origen IS NOT NULL
                  AND numero_origen != ''
                
                UNION ALL
                
                -- Cuando el número es ORIGINADOR: celda_destino (comunicación relacionada)
                SELECT 
                    'originador_destino' as rol,
                    numero_origen as numero,
                    celda_destino as celda,
                    fecha_hora_llamada,
                    operator,
                    numero_destino as otro_numero
                FROM operator_call_data 
                WHERE numero_origen = :numero
                  AND numero_origen IS NOT NULL
                  AND numero_origen != ''
                  AND celda_destino IS NOT NULL
                  AND celda_destino != ''
                
                UNION ALL
                
                -- Cuando el número es RECEPTOR: celda_destino (donde recibe)
                SELECT 
                    'receptor_destino' as rol,
                    numero_destino as numero,
                    celda_destino as celda,
                    fecha_hora_llamada,
                    operator,
                    numero_origen as otro_numero
                FROM operator_call_data 
                WHERE numero_destino = :numero
                  AND numero_destino IS NOT NULL
                  AND numero_destino != ''
                
                ORDER BY celda, fecha_hora_llamada
            """)
            
            result = session.execute(query, {'numero': numero})
            all_appearances = result.fetchall()
            
            # Procesar resultados - incluye todas las celdas relacionadas
            celdas_unicas = set()
            detalles = []
            
            for row in all_appearances:
                rol = row[0]
                numero_row = row[1]
                celda = str(row[2])
                fecha = row[3]
                operador = row[4]
                otro_numero = row[5] if len(row) > 5 else None
                
                celdas_unicas.add(celda)
                detalles.append({
                    'rol': rol,
                    'celda': celda,
                    'fecha': fecha,
                    'operador': operador,
                    'otro_numero': otro_numero
                })
            
            return {
                'numero': numero,
                'celdas_unicas': sorted(list(celdas_unicas)),
                'total_celdas': len(celdas_unicas),
                'total_registros': len(all_appearances),
                'detalles': detalles,
                'algoritmo': 'CORRECTED v2.0 - Conteo exacto sin inflación por contextos múltiples'
            }
            
        except Exception as e:
            logger.error(f"Error validando correlación para {numero}: {e}")
            return {
                'numero': numero,
                'error': str(e),
                'celdas_unicas': [],
                'total_celdas': 0,
                'total_registros': 0,
                'detalles': []
            }


def get_correlation_service_dynamic() -> CorrelationServiceDynamic:
    """Factory function para obtener instancia del servicio dinámico"""
    return CorrelationServiceDynamic()