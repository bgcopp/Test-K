"""
KRONOS - Diagram Correlation Service
===============================================================================
SERVICIO ESPECIALIZADO PARA DIAGRAMA DE CORRELACIÓN INTERACTIVO
===============================================================================

Este servicio genera datos estructurados para el diagrama de red de comunicaciones
que muestra las interacciones de un número objetivo filtradas por celdas HUNTER.

FUNCIONALIDADES PRINCIPALES:
1. Obtener red de comunicaciones de un número objetivo específico
2. Filtrar por celdas donde estuvo presente según datos HUNTER
3. Generar estructura de nodos (números) y aristas (comunicaciones)
4. Calcular estadísticas de interacción y metadatos geográficos
5. Optimizar para renderizado en frontend con D3.js

ARQUITECTURA:
- Consultas SQL optimizadas con índices existentes
- Cache inteligente para consultas repetidas
- Límites de rendimiento para prevenir sobrecarga del frontend
- Estructura JSON compatible con bibliotecas de visualización

Autor: Claude Code para Boris
Fecha: 2025-08-18
Versión: 1.0.0 - Implementación inicial
===============================================================================
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Set, Tuple, Optional
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from collections import defaultdict, Counter

from database.connection import get_database_manager

logger = logging.getLogger(__name__)


class DiagramCorrelationServiceError(Exception):
    """Excepción personalizada para errores del servicio de diagrama"""
    pass


# Configuración de límites de rendimiento
DIAGRAM_LIMITS = {
    'max_nodes': 100,           # Máximo nodos en el diagrama
    'max_edges': 500,           # Máximo aristas en el diagrama
    'max_time_range_days': 365, # Máximo rango temporal (1 año)
    'pagination_size': 50       # Tamaño de página para comunicaciones
}


class DiagramCorrelationService:
    """
    Servicio especializado para generar datos del diagrama de correlación
    
    Funcionalidades:
    1. Obtener red de comunicaciones de un número objetivo
    2. Filtrar por celdas HUNTER reales
    3. Generar estructura de nodos y aristas para frontend
    4. Calcular estadísticas de interacción
    """
    
    def __init__(self):
        self.db_manager = get_database_manager()
        self._cache = {}  # Cache en memoria para sesión
        self._cache_timeout = 300  # 5 minutos
        
    def get_correlation_diagram_data(self, 
                                   mission_id: str, 
                                   numero_objetivo: str,
                                   start_datetime: str,
                                   end_datetime: str,
                                   filtros: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Genera datos completos para el diagrama de correlación
        
        Args:
            mission_id: ID de la misión
            numero_objetivo: Número telefónico objetivo
            start_datetime: Inicio período (YYYY-MM-DD HH:MM:SS)
            end_datetime: Fin período (YYYY-MM-DD HH:MM:SS)
            filtros: Filtros opcionales (tipo_trafico, operador, etc.)
            
        Returns:
            Dict con nodos, aristas y metadatos para el diagrama
        """
        start_time = time.time()
        filtros = filtros or {}
        
        try:
            logger.info(f"=== GENERANDO DIAGRAMA DE CORRELACIÓN ===")
            logger.info(f"Número objetivo: {numero_objetivo}")
            logger.info(f"Misión: {mission_id}")
            logger.info(f"Período: {start_datetime} - {end_datetime}")
            
            # Validar rango temporal
            if not self._validate_time_range(start_datetime, end_datetime):
                raise DiagramCorrelationServiceError(
                    f"Rango temporal excede el máximo permitido ({DIAGRAM_LIMITS['max_time_range_days']} días)"
                )
            
            # Verificar cache
            cache_key = f"{mission_id}_{numero_objetivo}_{start_datetime}_{end_datetime}_{hash(str(filtros))}"
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                logger.info("Datos del diagrama obtenidos desde cache")
                return cached_result
            
            with self.db_manager.get_session() as session:
                # 1. Obtener red de comunicaciones
                network_data = self._build_communication_network(
                    session, mission_id, numero_objetivo, start_datetime, end_datetime, filtros
                )
                
                if not network_data['comunicaciones']:
                    return {
                        'success': True,
                        'message': 'No se encontraron comunicaciones en el período especificado',
                        'numero_objetivo': numero_objetivo,
                        'periodo': {'inicio': start_datetime, 'fin': end_datetime},
                        'nodos': [],
                        'aristas': [],
                        'celdas_hunter': [],
                        'estadisticas': {},
                        'processing_time': time.time() - start_time
                    }
                
                # 2. Aplicar límites de rendimiento
                limited_data = self._apply_diagram_limits(network_data['comunicaciones'])
                
                # 3. Generar nodos y aristas
                nodos = self._generate_nodes(limited_data['comunicaciones'], numero_objetivo)
                aristas = self._generate_edges(limited_data['comunicaciones'], numero_objetivo)
                
                # 4. Obtener metadatos de celdas HUNTER
                cell_ids = set()
                for comm in limited_data['comunicaciones']:
                    if comm.get('celda_origen'):
                        cell_ids.add(comm['celda_origen'])
                    if comm.get('celda_destino'):
                        cell_ids.add(comm['celda_destino'])
                
                celdas_hunter = self._get_hunter_cells_metadata(session, mission_id, cell_ids)
                
                # 5. Calcular estadísticas
                estadisticas = self._calculate_statistics(limited_data['comunicaciones'], numero_objetivo)
                
                # 6. Construir resultado final
                result = {
                    'success': True,
                    'numero_objetivo': numero_objetivo,
                    'periodo': {'inicio': start_datetime, 'fin': end_datetime},
                    'nodos': nodos,
                    'aristas': aristas,
                    'celdas_hunter': celdas_hunter,
                    'estadisticas': estadisticas,
                    'metadata': {
                        'total_comunicaciones_originales': len(network_data['comunicaciones']),
                        'comunicaciones_mostradas': len(limited_data['comunicaciones']),
                        'truncated': limited_data['truncated'],
                        'hunter_cells_used': len(celdas_hunter)
                    },
                    'processing_time': time.time() - start_time
                }
                
                # 7. Guardar en cache
                self._save_to_cache(cache_key, result)
                
                logger.info(f"Diagrama generado - Nodos: {len(nodos)}, Aristas: {len(aristas)}")
                return result
                
        except Exception as e:
            logger.error(f"Error generando diagrama de correlación: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'numero_objetivo': numero_objetivo,
                'nodos': [],
                'aristas': [],
                'celdas_hunter': [],
                'estadisticas': {},
                'processing_time': time.time() - start_time
            }
    
    def _build_communication_network(self, session, mission_id: str, numero_objetivo: str,
                                   start_datetime: str, end_datetime: str, 
                                   filtros: Dict[str, Any]) -> Dict[str, Any]:
        """
        Construye la red de comunicaciones usando la consulta SQL especializada
        """
        try:
            # Construir filtros adicionales
            filtro_sql = ""
            filtro_params = {
                'mission_id': mission_id,
                'numero_objetivo': numero_objetivo,
                'start_date': start_datetime.split(' ')[0],
                'end_date': end_datetime.split(' ')[0]
            }
            
            if filtros.get('tipo_trafico') and filtros['tipo_trafico'] != 'TODOS':
                filtro_sql += " AND ocd.tipo_trafico = :tipo_trafico"
                filtro_params['tipo_trafico'] = filtros['tipo_trafico']
                
            if filtros.get('operador') and filtros['operador'] != 'TODOS':
                filtro_sql += " AND ocd.operator = :operador"
                filtro_params['operador'] = filtros['operador']
            
            # Query principal CORREGIDA: SOLO llamadas directas del número objetivo
            # CORRECCIÓN BORIS 2025-08-18: Eliminar filtrado por celdas HUNTER que causa inflación
            query = text(f"""
                WITH target_communications AS (
                    -- NUEVA LÓGICA: Buscar ÚNICAMENTE llamadas donde el número objetivo participó directamente
                    -- No filtrar por celdas HUNTER para evitar mostrar números que no interactuaron directamente
                    SELECT DISTINCT
                        ocd.numero_origen,
                        ocd.numero_destino,
                        ocd.numero_objetivo,
                        ocd.celda_origen,
                        ocd.celda_destino,
                        ocd.fecha_hora_llamada,
                        ocd.duracion_segundos,
                        ocd.tipo_llamada,
                        ocd.tipo_trafico,
                        ocd.estado_llamada,
                        ocd.tecnologia,
                        ocd.operator,
                        
                        -- Identificar dirección relativa al objetivo
                        CASE 
                            WHEN ocd.numero_origen = :numero_objetivo THEN 'SALIENTE'
                            WHEN ocd.numero_destino = :numero_objetivo THEN 'ENTRANTE'
                            ELSE 'UNKNOWN'
                        END as direccion_objetivo,
                        
                        -- Identificar el otro participante (número que interactuó directamente)
                        CASE 
                            WHEN ocd.numero_origen = :numero_objetivo THEN ocd.numero_destino
                            WHEN ocd.numero_destino = :numero_objetivo THEN ocd.numero_origen
                            ELSE NULL
                        END as numero_contacto
                        
                    FROM operator_call_data ocd
                    WHERE ocd.mission_id = :mission_id
                      -- FILTRO PRINCIPAL: Solo llamadas donde el número objetivo participó directamente
                      AND (ocd.numero_origen = :numero_objetivo OR ocd.numero_destino = :numero_objetivo)
                      AND DATE(ocd.fecha_hora_llamada) BETWEEN :start_date AND :end_date
                      AND ocd.celda_origen IS NOT NULL 
                      AND ocd.celda_destino IS NOT NULL
                      -- Opcional: Validar que las celdas existen en datos HUNTER
                      AND EXISTS (
                          SELECT 1 FROM cellular_data cd 
                          WHERE cd.mission_id = :mission_id 
                          AND (cd.cell_id = ocd.celda_origen OR cd.cell_id = ocd.celda_destino)
                      )
                      {filtro_sql}
                )
                
                -- Resultado final: SOLO interacciones directas del número objetivo
                SELECT 
                    tc.*
                FROM target_communications tc
                ORDER BY tc.fecha_hora_llamada DESC
                LIMIT 50
            """)
            
            result = session.execute(query, filtro_params)
            comunicaciones = []
            
            for row in result.fetchall():
                comunicaciones.append({
                    'numero_origen': row.numero_origen,
                    'numero_destino': row.numero_destino,
                    'numero_objetivo': row.numero_objetivo,
                    'celda_origen': row.celda_origen,
                    'celda_destino': row.celda_destino,
                    'fecha_hora_llamada': row.fecha_hora_llamada.isoformat() if hasattr(row.fecha_hora_llamada, 'isoformat') and row.fecha_hora_llamada else str(row.fecha_hora_llamada) if row.fecha_hora_llamada else None,
                    'duracion_segundos': row.duracion_segundos or 0,
                    'tipo_llamada': row.tipo_llamada,
                    'tipo_trafico': row.tipo_trafico,
                    'estado_llamada': row.estado_llamada,
                    'tecnologia': row.tecnologia,
                    'operator': row.operator,
                    'direccion_objetivo': row.direccion_objetivo,
                    'numero_contacto': row.numero_contacto
                })
            
            logger.info(f"=== CORRECCIÓN BORIS: RESULTADO DE CONSULTA DIRECTA ===")
            logger.info(f"Comunicaciones directas encontradas: {len(comunicaciones)}")
            
            # Log de debug para las primeras comunicaciones
            for i, comm in enumerate(comunicaciones[:5]):  # Solo las primeras 5
                logger.info(f"  {i+1}. {comm['numero_origen']} → {comm['numero_destino']} | Celda: {comm['celda_origen']}→{comm['celda_destino']} | {comm['fecha_hora_llamada']}")
            
            if len(comunicaciones) > 5:
                logger.info(f"  ... y {len(comunicaciones) - 5} comunicaciones más")
            
            # Contar contactos únicos
            contactos_unicos = set()
            for comm in comunicaciones:
                if comm.get('numero_contacto'):
                    contactos_unicos.add(comm['numero_contacto'])
            
            logger.info(f"Números únicos que interactuaron directamente con {numero_objetivo}: {len(contactos_unicos)}")
            logger.info(f"Lista de contactos únicos: {list(contactos_unicos)}")
            logger.info(f"=== FIN CORRECCIÓN - INFLACIÓN ELIMINADA ===")
            
            return {'comunicaciones': comunicaciones}
            
        except Exception as e:
            logger.error(f"Error construyendo red de comunicaciones: {e}")
            return {'comunicaciones': []}
    
    def _generate_nodes(self, comunicaciones: List[Dict], numero_objetivo: str) -> List[Dict]:
        """
        Genera nodos del diagrama (objetivo + contactos)
        """
        try:
            nodos = {}
            contacto_stats = defaultdict(lambda: {
                'total_comunicaciones': 0,
                'llamadas_voz': 0,
                'mensajes_sms': 0,
                'sesiones_datos': 0,
                'duracion_total': 0,
                'primera_comunicacion': None,
                'ultima_comunicacion': None,
                'operadores': set()
            })
            
            # Procesar estadísticas por contacto
            for comm in comunicaciones:
                contacto = comm.get('numero_contacto')
                if not contacto:
                    continue
                    
                stats = contacto_stats[contacto]
                stats['total_comunicaciones'] += 1
                stats['operadores'].add(comm.get('operator', 'UNKNOWN'))
                
                if comm.get('tipo_trafico') == 'VOZ':
                    stats['llamadas_voz'] += 1
                elif comm.get('tipo_trafico') == 'SMS':
                    stats['mensajes_sms'] += 1
                elif comm.get('tipo_trafico') == 'DATOS':
                    stats['sesiones_datos'] += 1
                    
                stats['duracion_total'] += comm.get('duracion_segundos', 0)
                
                fecha_comm = comm.get('fecha_hora_llamada')
                if fecha_comm:
                    if not stats['primera_comunicacion'] or fecha_comm < stats['primera_comunicacion']:
                        stats['primera_comunicacion'] = fecha_comm
                    if not stats['ultima_comunicacion'] or fecha_comm > stats['ultima_comunicacion']:
                        stats['ultima_comunicacion'] = fecha_comm
            
            # Generar nodo objetivo
            objetivo_stats = sum(stats['total_comunicaciones'] for stats in contacto_stats.values())
            nodos[numero_objetivo] = {
                'id': numero_objetivo,
                'tipo': 'objetivo',
                'numero': numero_objetivo,
                'operador': 'MULTIPLE' if len(set(comm.get('operator', '') for comm in comunicaciones)) > 1 
                           else next((comm.get('operator', 'UNKNOWN') for comm in comunicaciones), 'UNKNOWN'),
                'nivel_actividad': self._calculate_activity_level(objetivo_stats),
                'total_comunicaciones': objetivo_stats,
                'metadata': {
                    'es_numero_objetivo': True,
                    'primera_comunicacion': min((comm.get('fecha_hora_llamada') for comm in comunicaciones), default=None),
                    'ultima_comunicacion': max((comm.get('fecha_hora_llamada') for comm in comunicaciones), default=None)
                }
            }
            
            # Generar nodos de contactos
            for contacto, stats in contacto_stats.items():
                if len(nodos) >= DIAGRAM_LIMITS['max_nodes'] - 1:  # -1 para el objetivo
                    break
                    
                nodos[contacto] = {
                    'id': contacto,
                    'tipo': 'contacto',
                    'numero': contacto,
                    'operador': list(stats['operadores'])[0] if len(stats['operadores']) == 1 else 'MULTIPLE',
                    'nivel_actividad': self._calculate_activity_level(stats['total_comunicaciones']),
                    'total_comunicaciones': stats['total_comunicaciones'],
                    'metadata': {
                        'es_numero_objetivo': False,
                        'primera_comunicacion': stats['primera_comunicacion'],
                        'ultima_comunicacion': stats['ultima_comunicacion'],
                        'llamadas_voz': stats['llamadas_voz'],
                        'mensajes_sms': stats['mensajes_sms'],
                        'sesiones_datos': stats['sesiones_datos'],
                        'duracion_total_segundos': stats['duracion_total']
                    }
                }
            
            return list(nodos.values())
            
        except Exception as e:
            logger.error(f"Error generando nodos: {e}")
            return []
    
    def _generate_edges(self, comunicaciones: List[Dict], numero_objetivo: str) -> List[Dict]:
        """
        Genera aristas del diagrama (comunicaciones)
        """
        try:
            aristas = []
            
            for i, comm in enumerate(comunicaciones):
                if len(aristas) >= DIAGRAM_LIMITS['max_edges']:
                    break
                
                # Determinar origen y destino para el diagrama
                if comm.get('direccion_objetivo') == 'SALIENTE':
                    origen_diagrama = numero_objetivo
                    destino_diagrama = comm.get('numero_contacto')
                elif comm.get('direccion_objetivo') == 'ENTRANTE':
                    origen_diagrama = comm.get('numero_contacto')
                    destino_diagrama = numero_objetivo
                else:
                    continue  # Skip comunicaciones sin dirección clara
                
                if not destino_diagrama:
                    continue
                
                arista = {
                    'id': f"comm_{i}",
                    'origen': origen_diagrama,
                    'destino': destino_diagrama,
                    'tipo_comunicacion': comm.get('tipo_trafico', 'UNKNOWN'),
                    'direccion': comm.get('direccion_objetivo', 'UNKNOWN'),
                    'timestamp': comm.get('fecha_hora_llamada'),
                    'duracion_segundos': comm.get('duracion_segundos', 0),
                    'estado': comm.get('estado_llamada', 'UNKNOWN'),
                    'tecnologia': comm.get('tecnologia', 'UNKNOWN'),
                    'operador': comm.get('operator', 'UNKNOWN'),
                    'celda_origen': comm.get('celda_origen'),
                    'celda_destino': comm.get('celda_destino'),
                    'metadata': {
                        'es_correlacion_hunter': True,  # Por definición, ya filtradas por HUNTER
                        'numero_origen_original': comm.get('numero_origen'),
                        'numero_destino_original': comm.get('numero_destino')
                    }
                }
                
                aristas.append(arista)
            
            logger.info(f"Generadas {len(aristas)} aristas para el diagrama")
            return aristas
            
        except Exception as e:
            logger.error(f"Error generando aristas: {e}")
            return []
    
    def _get_hunter_cells_metadata(self, session, mission_id: str, cell_ids: Set[str]) -> List[Dict]:
        """
        Obtiene metadatos de celdas HUNTER para correlación geográfica
        """
        try:
            if not cell_ids:
                return []
            
            # Convertir a lista para SQL
            cell_ids_list = list(cell_ids)
            cell_ids_str = ','.join([f"'{cell}'" for cell in cell_ids_list])
            
            query = text(f"""
                SELECT 
                    cd.cell_id,
                    cd.operator,
                    cd.tecnologia,
                    cd.lat,
                    cd.lon,
                    cd.rssi,
                    cd.punto,
                    cd.mnc_mcc,
                    cd.lac_tac,
                    cd.enb,
                    cd.channel,
                    
                    -- Contar comunicaciones que pasaron por esta celda
                    COUNT(DISTINCT ocd1.id) as comunicaciones_como_origen,
                    COUNT(DISTINCT ocd2.id) as comunicaciones_como_destino
                    
                FROM cellular_data cd
                LEFT JOIN operator_call_data ocd1 ON (
                    cd.cell_id = ocd1.celda_origen AND 
                    cd.mission_id = ocd1.mission_id
                )
                LEFT JOIN operator_call_data ocd2 ON (
                    cd.cell_id = ocd2.celda_destino AND 
                    cd.mission_id = ocd2.mission_id
                )
                
                WHERE cd.mission_id = :mission_id
                  AND cd.cell_id IN ({cell_ids_str})
                
                GROUP BY cd.cell_id, cd.operator, cd.tecnologia, cd.lat, cd.lon, 
                         cd.rssi, cd.punto, cd.mnc_mcc, cd.lac_tac, cd.enb, cd.channel
                
                ORDER BY (COUNT(DISTINCT ocd1.id) + COUNT(DISTINCT ocd2.id)) DESC, cd.rssi DESC
            """)
            
            result = session.execute(query, {'mission_id': mission_id})
            celdas_hunter = []
            
            for row in result.fetchall():
                celda = {
                    'cell_id': row.cell_id,
                    'operador': row.operator,
                    'tecnologia': row.tecnologia,
                    'lat': float(row.lat) if row.lat is not None else None,
                    'lon': float(row.lon) if row.lon is not None else None,
                    'rssi': row.rssi,
                    'punto_medicion': row.punto,
                    'mnc_mcc': row.mnc_mcc,
                    'lac_tac': row.lac_tac,
                    'enb': row.enb,
                    'channel': row.channel,
                    'comunicaciones_origen': row.comunicaciones_como_origen or 0,
                    'comunicaciones_destino': row.comunicaciones_como_destino or 0,
                    'total_actividad': (row.comunicaciones_como_origen or 0) + (row.comunicaciones_como_destino or 0)
                }
                celdas_hunter.append(celda)
            
            logger.info(f"Obtenidos metadatos de {len(celdas_hunter)} celdas HUNTER")
            return celdas_hunter
            
        except Exception as e:
            logger.error(f"Error obteniendo metadatos de celdas HUNTER: {e}")
            return []
    
    def _calculate_statistics(self, comunicaciones: List[Dict], numero_objetivo: str) -> Dict[str, Any]:
        """
        Calcula estadísticas del diagrama
        """
        try:
            if not comunicaciones:
                return {}
            
            # Contadores básicos
            contactos_unicos = set()
            tipos_trafico = Counter()
            operadores = Counter()
            estados = Counter()
            tecnologias = Counter()
            celdas_involucradas = set()
            duracion_total = 0
            
            for comm in comunicaciones:
                if comm.get('numero_contacto'):
                    contactos_unicos.add(comm['numero_contacto'])
                tipos_trafico[comm.get('tipo_trafico', 'UNKNOWN')] += 1
                operadores[comm.get('operator', 'UNKNOWN')] += 1
                estados[comm.get('estado_llamada', 'UNKNOWN')] += 1
                tecnologias[comm.get('tecnologia', 'UNKNOWN')] += 1
                duracion_total += comm.get('duracion_segundos', 0)
                
                if comm.get('celda_origen'):
                    celdas_involucradas.add(comm['celda_origen'])
                if comm.get('celda_destino'):
                    celdas_involucradas.add(comm['celda_destino'])
            
            # Estadísticas temporales
            fechas = [comm.get('fecha_hora_llamada') for comm in comunicaciones if comm.get('fecha_hora_llamada')]
            primera_comunicacion = min(fechas) if fechas else None
            ultima_comunicacion = max(fechas) if fechas else None
            
            return {
                'total_comunicaciones': len(comunicaciones),
                'contactos_unicos': len(contactos_unicos),
                'celdas_hunter_involucradas': len(celdas_involucradas),
                'duracion_total_segundos': duracion_total,
                'duracion_total_minutos': round(duracion_total / 60.0, 2),
                'primera_comunicacion': primera_comunicacion,
                'ultima_comunicacion': ultima_comunicacion,
                'tipos_trafico': dict(tipos_trafico),
                'operadores': dict(operadores),
                'estados_llamada': dict(estados),
                'tecnologias': dict(tecnologias),
                'promedio_duracion_segundos': round(duracion_total / len(comunicaciones), 2) if comunicaciones else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculando estadísticas: {e}")
            return {}
    
    def _calculate_activity_level(self, total_comunicaciones: int) -> str:
        """Calcula nivel de actividad basado en número de comunicaciones"""
        if total_comunicaciones >= 50:
            return 'ALTO'
        elif total_comunicaciones >= 10:
            return 'MEDIO'
        else:
            return 'BAJO'
    
    def _apply_diagram_limits(self, comunicaciones: List[Dict]) -> Dict[str, Any]:
        """
        Aplica límites de rendimiento al diagrama
        """
        truncated = False
        
        if len(comunicaciones) > DIAGRAM_LIMITS['max_edges']:
            logger.warning(f"Limitando comunicaciones de {len(comunicaciones)} a {DIAGRAM_LIMITS['max_edges']}")
            # Tomar las más recientes
            comunicaciones_sorted = sorted(comunicaciones, 
                                         key=lambda x: x.get('fecha_hora_llamada', ''), 
                                         reverse=True)
            comunicaciones = comunicaciones_sorted[:DIAGRAM_LIMITS['max_edges']]
            truncated = True
        
        return {
            'comunicaciones': comunicaciones,
            'truncated': truncated,
            'total_original': len(comunicaciones)
        }
    
    def _validate_time_range(self, start_datetime: str, end_datetime: str) -> bool:
        """Valida que el rango temporal no exceda los límites"""
        try:
            start = datetime.fromisoformat(start_datetime.replace(' ', 'T'))
            end = datetime.fromisoformat(end_datetime.replace(' ', 'T'))
            delta = end - start
            return delta.days <= DIAGRAM_LIMITS['max_time_range_days']
        except:
            return True  # Si hay error de parsing, permitir continuar
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Obtiene datos del cache si están disponibles y vigentes"""
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_timeout:
                return cached_data
            else:
                # Cache expirado, eliminar
                del self._cache[cache_key]
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Guarda datos en cache con timestamp"""
        self._cache[cache_key] = (data, time.time())
        
        # Limpiar cache antiguo si hay muchas entradas
        if len(self._cache) > 50:
            current_time = time.time()
            expired_keys = [
                key for key, (_, timestamp) in self._cache.items()
                if current_time - timestamp > self._cache_timeout
            ]
            for key in expired_keys:
                del self._cache[key]


def get_diagram_correlation_service() -> DiagramCorrelationService:
    """
    Factory function para obtener instancia del servicio de diagrama
    """
    return DiagramCorrelationService()


# Función de prueba
if __name__ == "__main__":
    # Configurar logging para pruebas
    logging.basicConfig(level=logging.INFO)
    
    # Crear instancia del servicio
    service = get_diagram_correlation_service()
    
    # Prueba con datos de ejemplo
    result = service.get_correlation_diagram_data(
        mission_id="mission_MPFRBNsb",
        numero_objetivo="3143534707",
        start_datetime="2021-01-01 00:00:00",
        end_datetime="2021-12-31 23:59:59"
    )
    
    print(f"Resultado de prueba:")
    print(f"- Success: {result['success']}")
    print(f"- Nodos: {len(result['nodos'])}")
    print(f"- Aristas: {len(result['aristas'])}")
    print(f"- Tiempo: {result['processing_time']:.3f}s")