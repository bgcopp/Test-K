"""
KRONOS Analysis Service - FUNCIONALIDAD REDUCIDA
===============================================================================
Servicio de análisis simplificado después de eliminar funcionalidad de operadores.
El análisis original cruzaba datos celulares con datos de operador para encontrar
coincidencias, pero esa funcionalidad ha sido eliminada.

Estado actual:
- Sin análisis de cruce de datos
- Solo limpieza de análisis previos
- Retorna listas vacías de objetivos
===============================================================================
"""

import logging
from typing import Dict, Any, List
from sqlalchemy.exc import SQLAlchemyError

from database.connection import get_database_manager
from database.models import Mission, CellularData, TargetRecord

logger = logging.getLogger(__name__)


class AnalysisServiceError(Exception):
    """Excepción personalizada para errores del servicio de análisis"""
    pass


class AnalysisService:
    """Servicio de análisis de objetivos (funcionalidad reducida)"""
    
    def __init__(self):
        pass
    
    @property
    def db_manager(self):
        """Obtiene el database manager de manera lazy para asegurar que esté inicializado"""
        return get_database_manager()
    
    def run_analysis(self, mission_id: str) -> List[Dict[str, Any]]:
        """
        Funcionalidad de análisis simplificada (sin datos de operador)
        
        Args:
            mission_id: ID de la misión
            
        Returns:
            Lista vacía (funcionalidad de análisis de operadores eliminada)
            
        Raises:
            AnalysisServiceError: Si hay errores en el análisis
        """
        try:
            logger.info(f"Análisis solicitado para misión {mission_id} - funcionalidad de operadores eliminada")
            
            with self.db_manager.get_session() as session:
                # Verificar que la misión existe
                mission = session.query(Mission).filter(Mission.id == mission_id).first()
                if not mission:
                    raise AnalysisServiceError("Misión no encontrada")
                
                # Verificar si hay datos celulares
                cellular_count = session.query(CellularData).filter(
                    CellularData.mission_id == mission_id
                ).count()
                
                # Limpiar análisis previos si existen
                deleted_count = session.query(TargetRecord).filter(
                    TargetRecord.mission_id == mission_id
                ).delete()
                
                session.commit()
                
                logger.info(f"Análisis completado para misión {mission_id}:")
                logger.info(f"- {cellular_count} registros celulares disponibles")
                logger.info(f"- {deleted_count} registros de análisis previo eliminados")
                logger.warning("- Sin análisis de operadores (funcionalidad eliminada)")
                
                return []
                
        except AnalysisServiceError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos en análisis: {e}")
            raise AnalysisServiceError("Error accediendo a los datos de análisis")
        except Exception as e:
            logger.error(f"Error inesperado en análisis: {e}")
            raise AnalysisServiceError("Error interno del servidor")
    
    def get_analysis_stats(self, mission_id: str) -> Dict[str, Any]:
        """
        Obtiene estadísticas de análisis para una misión
        
        Args:
            mission_id: ID de la misión
            
        Returns:
            Diccionario con estadísticas básicas
        """
        try:
            with self.db_manager.get_session() as session:
                mission = session.query(Mission).filter(Mission.id == mission_id).first()
                if not mission:
                    raise AnalysisServiceError("Misión no encontrada")
                
                cellular_count = session.query(CellularData).filter(
                    CellularData.mission_id == mission_id
                ).count()
                
                target_count = session.query(TargetRecord).filter(
                    TargetRecord.mission_id == mission_id
                ).count()
                
                return {
                    'cellularRecordsAvailable': cellular_count,
                    'operatorRecordsProcessed': 0,  # Funcionalidad eliminada
                    'targetRecordsFound': target_count,
                    'analysisStatus': 'disabled' if cellular_count == 0 else 'ready',
                    'operatorAnalysisEnabled': False
                }
                
        except AnalysisServiceError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo estadísticas de análisis: {e}")
            raise AnalysisServiceError("Error accediendo a las estadísticas")
        except Exception as e:
            logger.error(f"Error inesperado obteniendo estadísticas: {e}")
            raise AnalysisServiceError("Error interno del servidor")


# Instancia global del servicio
analysis_service = AnalysisService()


def get_analysis_service() -> AnalysisService:
    """Retorna la instancia del servicio de análisis"""
    return analysis_service