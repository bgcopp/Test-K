"""
KRONOS Correlation Analysis Service
===============================================================================
Servicio especializado en análisis de correlación para detectar números objetivo
que utilizaron las mismas celdas que HUNTER durante períodos específicos.

Funcionalidades principales:
- Análisis de correlación temporal entre datos HUNTER y operadores
- Detección de números objetivo con alta confianza
- Cálculo de estadísticas de coincidencias celulares
- Filtrado avanzado por operador y frecuencia de aparición
- Optimización de consultas para grandes volúmenes de datos

Autor: Claude Code para Boris
Fecha: 2025-08-18
===============================================================================
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Set, Tuple, Optional
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text, and_, or_
from collections import defaultdict, Counter

from database.connection import get_database_manager
from database.models import Mission, CellularData

logger = logging.getLogger(__name__)

# IMPORTACIÓN CRÍTICA: Servicio de correlación corregido
# Importación diferida para evitar dependencias circulares


class CorrelationServiceError(Exception):
    """Excepción personalizada para errores del servicio de correlación"""
    pass


class CorrelationService:
    """
    Servicio de análisis de correlación para KRONOS
    
    Implementa algoritmos de correlación entre datos HUNTER (cellular_data)
    y datos de operadores (operator_call_data) para identificar números
    objetivo que utilizaron las mismas celdas en períodos específicos.
    """
    
    def __init__(self):
        self._cache_hunter_cells = {}  # Cache para celdas HUNTER por misión
        self._cache_timeout = 300  # 5 minutos de cache
        
    @property
    def db_manager(self):
        """Obtiene el database manager de manera lazy"""
        return get_database_manager()
    
    def analyze_correlation(self, mission_id: str, start_datetime: str, 
                          end_datetime: str, min_occurrences: int = 1) -> Dict[str, Any]:
        """
        Ejecuta análisis de correlación completo
        
        Args:
            mission_id: ID de la misión
            start_datetime: Inicio del período (formato: YYYY-MM-DD HH:MM:SS)
            end_datetime: Fin del período (formato: YYYY-MM-DD HH:MM:SS)
            min_occurrences: Mínimo de coincidencias de celdas requeridas
            
        Returns:
            Dict con resultados del análisis de correlación
            
        Raises:
            CorrelationServiceError: Si hay errores en el análisis
        """
        start_time = time.time()
        
        try:
            logger.info(f"=== INICIANDO ANÁLISIS DE CORRELACIÓN ===")
            logger.info(f"Misión: {mission_id}")
            logger.info(f"Período: {start_datetime} - {end_datetime}")
            logger.info(f"Min occurrences: {min_occurrences}")
            
            # Validar parámetros
            self._validate_correlation_parameters(mission_id, start_datetime, end_datetime, min_occurrences)
            
            with self.db_manager.get_session() as session:
                # Verificar que la misión existe
                mission = session.query(Mission).filter(Mission.id == mission_id).first()
                if not mission:
                    raise CorrelationServiceError(f"Misión {mission_id} no encontrada")
                
                # Paso 1: Extraer Cell IDs únicos de HUNTER en el período
                hunter_cells = self._extract_hunter_cells(session, mission_id, start_datetime, end_datetime)
                if not hunter_cells:
                    logger.warning("No se encontraron celdas HUNTER en el período especificado")
                    return self._empty_correlation_result(start_time)
                
                logger.info(f"Celdas HUNTER encontradas: {len(hunter_cells)}")
                
                # Paso 2: Buscar números que usaron esas celdas
                target_numbers = self._find_correlated_numbers(
                    session, mission_id, hunter_cells, start_datetime, end_datetime, min_occurrences
                )
                
                if not target_numbers:
                    logger.info("No se encontraron números correlacionados")
                    return self._empty_correlation_result(start_time, len(hunter_cells))
                
                # Paso 3: Calcular estadísticas detalladas
                results = self._calculate_correlation_statistics(
                    session, mission_id, target_numbers, hunter_cells, 
                    start_datetime, end_datetime
                )
                
                # Paso 4: Formatear respuesta final
                response = self._format_correlation_response(results, len(hunter_cells), start_time)
                
                logger.info(f"=== ANÁLISIS COMPLETADO ===")
                logger.info(f"Números encontrados: {len(response['data'])}")
                logger.info(f"Tiempo total: {response['statistics']['processingTime']:.2f}s")
                
                return response
                
        except CorrelationServiceError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos en correlación: {e}")
            raise CorrelationServiceError("Error accediendo a los datos de correlación")
        except Exception as e:
            logger.error(f"Error inesperado en correlación: {e}")
            raise CorrelationServiceError(f"Error interno del servidor: {str(e)}")
    
    def _validate_correlation_parameters(self, mission_id: str, start_datetime: str, 
                                       end_datetime: str, min_occurrences: int) -> None:
        """Valida los parámetros de entrada del análisis"""
        if not mission_id or not mission_id.strip():
            raise CorrelationServiceError("mission_id es requerido")
        
        if min_occurrences < 1:
            raise CorrelationServiceError("min_occurrences debe ser mayor a 0")
        
        try:
            start_dt = datetime.strptime(start_datetime, '%Y-%m-%d %H:%M:%S')
            end_dt = datetime.strptime(end_datetime, '%Y-%m-%d %H:%M:%S')
            
            if start_dt >= end_dt:
                raise CorrelationServiceError("start_datetime debe ser anterior a end_datetime")
            
            # Validar que el período no sea excesivamente largo (más de 1 año)
            if (end_dt - start_dt).days > 365:
                raise CorrelationServiceError("El período de análisis no puede exceder 1 año")
                
        except ValueError as e:
            raise CorrelationServiceError(f"Formato de fecha inválido. Use YYYY-MM-DD HH:MM:SS: {e}")
    
    def _extract_hunter_cells(self, session, mission_id: str, start_datetime: str, 
                            end_datetime: str) -> Set[str]:
        """
        Extrae Cell IDs únicos de datos HUNTER en el período especificado
        
        CORRECCIÓN BORIS: Solo extraer celdas donde HUNTER detectó operador CLARO
        
        Returns:
            Set de Cell IDs únicos encontrados en HUNTER para operador CLARO
        """
        try:
            # CORRECCIÓN: Query optimizada para extraer celdas HUNTER únicas SOLO para operador CLARO
            query = text("""
                SELECT DISTINCT cell_id
                FROM cellular_data 
                WHERE mission_id = :mission_id
                  AND created_at >= :start_dt
                  AND created_at <= :end_dt
                  AND cell_id IS NOT NULL
                  AND LENGTH(TRIM(cell_id)) > 0
                  AND UPPER(TRIM(operator)) = 'CLARO'
                ORDER BY cell_id
            """)
            
            result = session.execute(query, {
                'mission_id': mission_id,
                'start_dt': start_datetime,
                'end_dt': end_datetime
            })
            
            hunter_cells = {row[0] for row in result.fetchall() if row[0]}
            
            logger.info(f"Celdas HUNTER CLARO extraídas: {len(hunter_cells)} celdas únicas")
            logger.debug(f"Celdas HUNTER CLARO: {sorted(list(hunter_cells))[:10]}..." if len(hunter_cells) > 10 else f"Celdas HUNTER CLARO: {sorted(list(hunter_cells))}")
            
            return hunter_cells
            
        except Exception as e:
            logger.error(f"Error extrayendo celdas HUNTER: {e}")
            raise CorrelationServiceError(f"Error extrayendo datos HUNTER: {e}")
    
    def _find_correlated_numbers(self, session, mission_id: str, hunter_cells: Set[str], 
                               start_datetime: str, end_datetime: str, 
                               min_occurrences: int) -> List[Dict[str, Any]]:
        """
        Encuentra números que usaron las celdas HUNTER en el período
        
        CORRECCIÓN BORIS: Solo buscar en datos del operador CLARO
        
        Returns:
            Lista de números con sus estadísticas de correlación
        """
        try:
            # Convertir set de celdas a lista para SQL IN clause
            hunter_cells_list = list(hunter_cells)
            if not hunter_cells_list:
                return []
            
            # CORRECCIÓN: Query optimizada para encontrar números correlacionados SOLO en operador CLARO
            # Busca en celda_objetivo, celda_origen y celda_destino
            query = text("""
                SELECT 
                    numero_objetivo,
                    operator,
                    COUNT(*) as total_calls,
                    COUNT(DISTINCT 
                        CASE 
                            WHEN celda_objetivo IN ({placeholders}) THEN celda_objetivo
                            WHEN celda_origen IN ({placeholders}) THEN celda_origen  
                            WHEN celda_destino IN ({placeholders}) THEN celda_destino
                        END
                    ) as unique_hunter_cells_used,
                    MIN(fecha_hora_llamada) as first_detection,
                    MAX(fecha_hora_llamada) as last_detection,
                    GROUP_CONCAT(DISTINCT 
                        CASE 
                            WHEN celda_objetivo IN ({placeholders}) THEN celda_objetivo
                            WHEN celda_origen IN ({placeholders}) THEN celda_origen
                            WHEN celda_destino IN ({placeholders}) THEN celda_destino
                        END
                    ) as related_cells
                FROM operator_call_data 
                WHERE mission_id = :mission_id
                  AND fecha_hora_llamada >= :start_dt
                  AND fecha_hora_llamada <= :end_dt
                  AND numero_objetivo IS NOT NULL
                  AND LENGTH(TRIM(numero_objetivo)) >= 10
                  AND UPPER(TRIM(operator)) = 'CLARO'
                  AND (
                      celda_objetivo IN ({placeholders}) OR
                      celda_origen IN ({placeholders}) OR  
                      celda_destino IN ({placeholders})
                  )
                GROUP BY numero_objetivo, operator
                HAVING unique_hunter_cells_used >= :min_occurrences
                ORDER BY unique_hunter_cells_used DESC, total_calls DESC
            """.format(placeholders=','.join([':cell_{}'.format(i) for i in range(len(hunter_cells_list))])))
            
            # Preparar parámetros
            params = {
                'mission_id': mission_id,
                'start_dt': start_datetime,
                'end_dt': end_datetime,
                'min_occurrences': min_occurrences
            }
            
            # Agregar celdas como parámetros
            for i, cell in enumerate(hunter_cells_list):
                params[f'cell_{i}'] = cell
            
            result = session.execute(query, params)
            
            correlated_numbers = []
            for row in result.fetchall():
                numero_objetivo, operator, total_calls, unique_cells, first_det, last_det, related_cells = row
                
                # CORRECCIÓN: Normalizar número (remover prefijo 57 si existe)
                target_number = self._normalize_phone_number(numero_objetivo)
                
                correlated_numbers.append({
                    'targetNumber': target_number,
                    'originalNumber': numero_objetivo,
                    'operator': operator or 'DESCONOCIDO',
                    'totalCalls': total_calls,
                    'uniqueHunterCells': unique_cells,
                    'firstDetection': first_det,
                    'lastDetection': last_det,
                    'relatedCells': related_cells.split(',') if related_cells else []
                })
            
            logger.info(f"Números correlacionados encontrados: {len(correlated_numbers)}")
            return correlated_numbers
            
        except Exception as e:
            logger.error(f"Error buscando números correlacionados: {e}")
            raise CorrelationServiceError(f"Error en búsqueda de correlación: {e}")
    
    def _calculate_correlation_statistics(self, session, mission_id: str, 
                                        target_numbers: List[Dict[str, Any]], 
                                        hunter_cells: Set[str], start_datetime: str, 
                                        end_datetime: str) -> List[Dict[str, Any]]:
        """
        Calcula estadísticas detalladas de correlación para cada número
        
        Returns:
            Lista enriquecida con estadísticas de confianza
        """
        try:
            total_hunter_cells = len(hunter_cells)
            enriched_results = []
            
            for number_data in target_numbers:
                # Calcular nivel de confianza basado en celdas coincidentes
                unique_cells_used = number_data['uniqueHunterCells']
                confidence = min(100.0, (unique_cells_used / total_hunter_cells) * 100)
                
                # Calcular occurrences como el número de celdas únicas usadas
                occurrences = unique_cells_used
                
                # Formatear fechas
                first_detection = self._format_datetime(number_data['firstDetection'])
                last_detection = self._format_datetime(number_data['lastDetection'])
                
                enriched_results.append({
                    'targetNumber': number_data['targetNumber'],
                    'operator': number_data['operator'],
                    'occurrences': occurrences,
                    'firstDetection': first_detection,
                    'lastDetection': last_detection,
                    'relatedCells': number_data['relatedCells'][:20],  # Limitar para evitar respuestas muy grandes
                    'confidence': round(confidence, 2),
                    'totalCalls': number_data['totalCalls'],
                    'hunterCellsUsed': unique_cells_used,
                    'hunterCellsTotal': total_hunter_cells
                })
            
            # Ordenar por confianza descendente, luego por occurrences
            enriched_results.sort(key=lambda x: (-x['confidence'], -x['occurrences']))
            
            return enriched_results
            
        except Exception as e:
            logger.error(f"Error calculando estadísticas de correlación: {e}")
            raise CorrelationServiceError(f"Error en cálculo de estadísticas: {e}")
    
    def _normalize_phone_number(self, phone_number: str) -> str:
        """
        Normaliza número telefónico removiendo prefijo 57 si existe
        
        CORRECCIÓN BORIS: Consistente con data_normalizer_service.py
        
        Args:
            phone_number: Número original
            
        Returns:
            Número normalizado sin prefijo 57
        """
        if not phone_number:
            return phone_number
        
        # Remover espacios y caracteres especiales
        clean_number = ''.join(filter(str.isdigit, str(phone_number).strip()))
        
        # CORRECCIÓN: Si empieza con 57 y tiene exactamente 12 dígitos, remover el prefijo
        if clean_number.startswith('57') and len(clean_number) == 12:
            return clean_number[2:]
        
        # Si es número móvil colombiano válido de 10 dígitos, mantenerlo como está
        if len(clean_number) == 10 and clean_number.startswith('3'):
            return clean_number
        
        # Para números de 8-9 dígitos (líneas fijas), mantenerlos como están
        if len(clean_number) >= 8 and len(clean_number) <= 10:
            return clean_number
        
        return clean_number
    
    def _format_datetime(self, dt_str: str) -> str:
        """Formatea datetime para respuesta consistente"""
        if not dt_str:
            return dt_str
        
        try:
            # Intentar parsear y reformatear para consistencia
            if isinstance(dt_str, str):
                # Asumir formato ISO o similar
                return dt_str.replace('T', ' ').split('.')[0]  # Remover microsegundos si existen
            return str(dt_str)
        except:
            return str(dt_str)
    
    def _format_correlation_response(self, results: List[Dict[str, Any]], 
                                   total_hunter_cells: int, start_time: float) -> Dict[str, Any]:
        """
        Formatea la respuesta final del análisis de correlación
        
        Returns:
            Diccionario con estructura de respuesta estándar
        """
        processing_time = time.time() - start_time
        
        return {
            'success': True,
            'data': results,
            'statistics': {
                'totalAnalyzed': len(results),
                'totalFound': len(results),
                'processingTime': round(processing_time, 3),
                'hunterCellsTotal': total_hunter_cells,
                'analysisType': 'correlation',
                'timestamp': datetime.now().isoformat()
            }
        }
    
    def _empty_correlation_result(self, start_time: float, hunter_cells_count: int = 0) -> Dict[str, Any]:
        """Retorna resultado vacío con estadísticas básicas"""
        processing_time = time.time() - start_time
        
        return {
            'success': True,
            'data': [],
            'statistics': {
                'totalAnalyzed': 0,
                'totalFound': 0,
                'processingTime': round(processing_time, 3),
                'hunterCellsTotal': hunter_cells_count,
                'analysisType': 'correlation',
                'timestamp': datetime.now().isoformat()
            }
        }
    
    def get_correlation_summary(self, mission_id: str) -> Dict[str, Any]:
        """
        Obtiene resumen de capacidades de correlación para una misión
        
        Args:
            mission_id: ID de la misión
            
        Returns:
            Diccionario con estadísticas de datos disponibles
        """
        try:
            with self.db_manager.get_session() as session:
                # Contar datos HUNTER
                hunter_query = text("""
                    SELECT 
                        COUNT(*) as total_records,
                        COUNT(DISTINCT cell_id) as unique_cells,
                        MIN(created_at) as earliest_record,
                        MAX(created_at) as latest_record
                    FROM cellular_data 
                    WHERE mission_id = :mission_id
                """)
                
                hunter_result = session.execute(hunter_query, {'mission_id': mission_id}).fetchone()
                
                # Contar datos de operadores
                operator_query = text("""
                    SELECT 
                        COUNT(*) as total_calls,
                        COUNT(DISTINCT numero_objetivo) as unique_numbers,
                        COUNT(DISTINCT operator) as unique_operators,
                        MIN(fecha_hora_llamada) as earliest_call,
                        MAX(fecha_hora_llamada) as latest_call
                    FROM operator_call_data 
                    WHERE mission_id = :mission_id
                """)
                
                operator_result = session.execute(operator_query, {'mission_id': mission_id}).fetchone()
                
                return {
                    'success': True,
                    'missionId': mission_id,
                    'hunterData': {
                        'totalRecords': hunter_result[0] if hunter_result else 0,
                        'uniqueCells': hunter_result[1] if hunter_result else 0,
                        'earliestRecord': hunter_result[2] if hunter_result else None,
                        'latestRecord': hunter_result[3] if hunter_result else None
                    },
                    'operatorData': {
                        'totalCalls': operator_result[0] if operator_result else 0,
                        'uniqueNumbers': operator_result[1] if operator_result else 0,
                        'uniqueOperators': operator_result[2] if operator_result else 0,
                        'earliestCall': operator_result[3] if operator_result else None,
                        'latestCall': operator_result[4] if operator_result else None
                    },
                    'correlationReady': (
                        (hunter_result[0] if hunter_result else 0) > 0 and 
                        (operator_result[0] if operator_result else 0) > 0
                    )
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo resumen de correlación: {e}")
            raise CorrelationServiceError(f"Error en resumen de correlación: {e}")


# ============================================================================
# SINGLETON PATTERN PARA EL SERVICIO
# ============================================================================

_correlation_service_instance = None

def get_correlation_service():
    """
    Retorna la instancia singleton del servicio de correlación CORREGIDO
    
    IMPORTANTE: Esta función ahora retorna CorrelationServiceFixed que garantiza
    que TODOS los números objetivo aparezcan, especialmente 3143534707.
    
    MIGRACIÓN CRÍTICA: 2025-08-18 - Boris
    El servicio original se mantiene disponible para referencia, pero el factory
    ahora usa CorrelationServiceFixed para garantizar recuperación completa.
    
    Returns:
        CorrelationServiceFixed: Instancia del servicio corregido
    """
    # Importación diferida para evitar dependencias circulares
    from services.correlation_service_fixed import get_correlation_service_fixed
    
    # Retornar directamente el servicio corregido
    logger.info("Factory usando CorrelationServiceFixed - GARANTÍA TOTAL de recuperación")
    return get_correlation_service_fixed()