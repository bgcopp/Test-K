"""
KRONOS Mission Service
===============================================================================
Servicio completo para gestión de misiones incluyendo operaciones CRUD,
manejo de datos celulares y de operador, procesamiento de archivos
y gestión de hojas de datos.

Características principales:
- Operaciones CRUD completas para misiones
- Carga y gestión de datos celulares desde archivos
- Carga y gestión de datos de operador con múltiples hojas
- Limpieza y eliminación de datos asociados
- Validación exhaustiva de datos
- Mapeo automático entre BD y frontend
- Transacciones atomicas para integridad
- Logging detallado de operaciones
===============================================================================
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import joinedload

from database.connection import get_database_manager
from database.models import (
    Mission, CellularData, TargetRecord
)
from utils.validators import validate_mission_data, ValidationError
from utils.helpers import (
    generate_mission_id,
    map_mission_to_frontend,
    map_cellular_record_to_frontend
)
from .file_processor import get_file_processor, FileProcessorError

logger = logging.getLogger(__name__)


class MissionServiceError(Exception):
    """Excepción personalizada para errores del servicio de misiones"""
    pass


class MissionService:
    """Servicio de gestión de misiones"""
    
    def __init__(self):
        self.db_manager = None
        self.file_processor = get_file_processor()
    
    def _get_db_manager(self):
        """Obtiene el DB manager de forma lazy"""
        if self.db_manager is None:
            try:
                self.db_manager = get_database_manager()
                # Verificar si está inicializado
                if not self.db_manager._initialized:
                    # Inicializar si no está inicializado
                    import os
                    from pathlib import Path
                    current_dir = Path(__file__).parent.parent
                    db_path = os.path.join(current_dir, 'kronos.db')
                    
                    from database.connection import init_database
                    init_database(db_path, force_recreate=False)
                    self.db_manager = get_database_manager()
            except Exception as e:
                logger.error(f"Error inicializando DB manager: {e}")
                # Intentar inicialización desde cero
                import os
                from pathlib import Path
                current_dir = Path(__file__).parent.parent
                db_path = os.path.join(current_dir, 'kronos.db')
                
                from database.connection import init_database
                init_database(db_path, force_recreate=False)
                self.db_manager = get_database_manager()
        return self.db_manager
    
    def get_all_missions(self) -> List[Dict[str, Any]]:
        """
        Obtiene todas las misiones con datos completos
        
        Returns:
            Lista de diccionarios con datos de misiones
            
        Raises:
            MissionServiceError: Si hay error accediendo a los datos
        """
        try:
            with self._get_db_manager().get_session() as session:
                # Cargar misiones con todos los datos relacionados
                missions = session.query(Mission).options(
                    joinedload(Mission.cellular_data),
                    joinedload(Mission.creator)
                ).order_by(Mission.created_at.desc()).all()
                
                result = []
                for mission in missions:
                    mission_dict = mission.to_dict_with_relations()
                    result.append(mission_dict)
                
                logger.info(f"Recuperadas {len(result)} misiones")
                return result
                
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos obteniendo misiones: {e}")
            raise MissionServiceError("Error accediendo a los datos de misiones")
        except Exception as e:
            logger.error(f"Error inesperado obteniendo misiones: {e}")
            raise MissionServiceError("Error interno del servidor")
    
    def get_mission_by_id(self, mission_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene una misión por su ID con todos los datos
        
        Args:
            mission_id: ID de la misión
            
        Returns:
            Diccionario con datos de la misión o None si no existe
        """
        try:
            with self._get_db_manager().get_session() as session:
                mission = session.query(Mission).options(
                    joinedload(Mission.cellular_data),
                    joinedload(Mission.creator)
                ).filter(Mission.id == mission_id).first()
                
                if mission:
                    return mission.to_dict_with_relations()
                return None
                
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos obteniendo misión {mission_id}: {e}")
            raise MissionServiceError("Error accediendo a los datos de la misión")
        except Exception as e:
            logger.error(f"Error inesperado obteniendo misión {mission_id}: {e}")
            raise MissionServiceError("Error interno del servidor")
    
    def create_mission(self, mission_data: Dict[str, Any], created_by: Optional[str] = None) -> Dict[str, Any]:
        """
        Crea una nueva misión
        
        Args:
            mission_data: Datos de la misión
            created_by: ID del usuario que crea la misión
            
        Returns:
            Diccionario con datos de la misión creada
        """
        try:
            # Validar datos
            validated_data = validate_mission_data(mission_data, is_update=False)
            
            with self.db_manager.get_session() as session:
                # Verificar que el código no esté en uso
                existing_mission = session.query(Mission).filter(
                    Mission.code == validated_data['code']
                ).first()
                
                if existing_mission:
                    raise MissionServiceError("Ya existe una misión con ese código")
                
                # Generar ID único
                mission_id = generate_mission_id()
                
                # Crear misión
                new_mission = Mission(
                    id=mission_id,
                    code=validated_data['code'],
                    name=validated_data['name'],
                    description=validated_data.get('description', ''),
                    status=validated_data.get('status', 'Planificación'),
                    start_date=validated_data['start_date'],
                    end_date=validated_data.get('end_date'),
                    created_by=created_by
                )
                
                session.add(new_mission)
                session.flush()
                
                # Cargar misión creada con datos completos
                created_mission = session.query(Mission).options(
                    joinedload(Mission.cellular_data),
                    joinedload(Mission.creator)
                ).filter(Mission.id == mission_id).first()
                
                session.commit()
                
                result = created_mission.to_dict_with_relations()
                logger.info(f"Misión creada exitosamente: {validated_data['code']}")
                
                return result
                
        except ValidationError as e:
            logger.warning(f"Error de validación creando misión: {e}")
            raise MissionServiceError(str(e))
        except MissionServiceError:
            raise
        except IntegrityError as e:
            logger.error(f"Error de integridad creando misión: {e}")
            raise MissionServiceError("Ya existe una misión con ese código")
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos creando misión: {e}")
            raise MissionServiceError("Error guardando la misión")
        except Exception as e:
            logger.error(f"Error inesperado creando misión: {e}")
            raise MissionServiceError("Error interno del servidor")
    
    def create_mission_with_id(self, mission_id: str, mission_data: Dict[str, Any], created_by: Optional[str] = None) -> Dict[str, Any]:
        """
        Crea una nueva misión con un ID específico (para testing)
        
        Args:
            mission_id: ID específico para la misión
            mission_data: Datos de la misión
            created_by: ID del usuario que crea la misión
            
        Returns:
            Diccionario con datos de la misión creada
        """
        try:
            # Validar datos básicos sin validación estricta para testing
            if not mission_data.get('code'):
                raise MissionServiceError("Código de misión requerido")
            if not mission_data.get('name'):
                raise MissionServiceError("Nombre de misión requerido")
            
            with self._get_db_manager().get_session() as session:
                # Verificar que el ID no esté en uso
                existing_mission_by_id = session.query(Mission).filter(
                    Mission.id == mission_id
                ).first()
                
                if existing_mission_by_id:
                    logger.info(f"Misión con ID {mission_id} ya existe, saltando creación")
                    return existing_mission_by_id.to_dict_with_relations()
                
                # Verificar que el código no esté en uso
                existing_mission_by_code = session.query(Mission).filter(
                    Mission.code == mission_data['code']
                ).first()
                
                if existing_mission_by_code:
                    logger.info(f"Misión con código {mission_data['code']} ya existe, saltando creación")
                    return existing_mission_by_code.to_dict_with_relations()
                
                # Crear misión con ID específico
                new_mission = Mission(
                    id=mission_id,
                    code=mission_data['code'],
                    name=mission_data['name'],
                    description=mission_data.get('description', ''),
                    status=mission_data.get('status', 'active'),
                    priority=mission_data.get('priority', 'medium'),
                    start_date=mission_data.get('start_date'),
                    end_date=mission_data.get('end_date'),
                    created_by=created_by
                )
                
                session.add(new_mission)
                session.flush()
                
                # Cargar misión creada con datos completos
                created_mission = session.query(Mission).options(
                    joinedload(Mission.cellular_data),
                    joinedload(Mission.creator)
                ).filter(Mission.id == mission_id).first()
                
                session.commit()
                
                result = created_mission.to_dict_with_relations()
                logger.info(f"Misión creada exitosamente con ID específico: {mission_data['code']} ({mission_id})")
                
                return result
                
        except MissionServiceError:
            raise
        except IntegrityError as e:
            logger.error(f"Error de integridad creando misión con ID: {e}")
            raise MissionServiceError("Ya existe una misión con ese ID o código")
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos creando misión con ID: {e}")
            raise MissionServiceError("Error guardando la misión")
        except Exception as e:
            logger.error(f"Error inesperado creando misión con ID: {e}")
            raise MissionServiceError("Error interno del servidor")
    
    def update_mission(self, mission_id: str, mission_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza una misión existente
        
        Args:
            mission_id: ID de la misión
            mission_data: Datos actualizados
            
        Returns:
            Diccionario con datos de la misión actualizada
        """
        try:
            # Validar datos para actualización
            validated_data = validate_mission_data(mission_data, is_update=True)
            
            with self.db_manager.get_session() as session:
                # Buscar misión
                mission = session.query(Mission).filter(Mission.id == mission_id).first()
                
                if not mission:
                    raise MissionServiceError("Misión no encontrada")
                
                # Si se actualiza código, verificar que no esté en uso
                if 'code' in validated_data:
                    existing_mission = session.query(Mission).filter(
                        Mission.code == validated_data['code'],
                        Mission.id != mission_id
                    ).first()
                    
                    if existing_mission:
                        raise MissionServiceError("Ya existe una misión con ese código")
                
                # Actualizar campos
                for field, value in validated_data.items():
                    setattr(mission, field, value)
                
                session.flush()
                
                # Cargar misión actualizada
                updated_mission = session.query(Mission).options(
                    joinedload(Mission.cellular_data),
                    joinedload(Mission.creator)
                ).filter(Mission.id == mission_id).first()
                
                session.commit()
                
                result = updated_mission.to_dict_with_relations()
                logger.info(f"Misión actualizada exitosamente: {mission.code}")
                
                return result
                
        except ValidationError as e:
            logger.warning(f"Error de validación actualizando misión: {e}")
            raise MissionServiceError(str(e))
        except MissionServiceError:
            raise
        except IntegrityError as e:
            logger.error(f"Error de integridad actualizando misión: {e}")
            raise MissionServiceError("Ya existe una misión con ese código")
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos actualizando misión: {e}")
            raise MissionServiceError("Error guardando los cambios")
        except Exception as e:
            logger.error(f"Error inesperado actualizando misión: {e}")
            raise MissionServiceError("Error interno del servidor")
    
    def delete_mission(self, mission_id: str) -> Dict[str, str]:
        """
        Elimina una misión y todos sus datos asociados
        
        Args:
            mission_id: ID de la misión
            
        Returns:
            Diccionario confirmando la eliminación
        """
        try:
            with self._get_db_manager().get_session() as session:
                # Buscar misión
                mission = session.query(Mission).filter(Mission.id == mission_id).first()
                
                if not mission:
                    raise MissionServiceError("Misión no encontrada")
                
                mission_code = mission.code
                
                # Eliminar (cascada automática por la configuración en modelos)
                session.delete(mission)
                session.commit()
                
                logger.info(f"Misión eliminada exitosamente: {mission_code}")
                return {"status": "ok"}
                
        except MissionServiceError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos eliminando misión: {e}")
            raise MissionServiceError("Error eliminando la misión")
        except Exception as e:
            logger.error(f"Error inesperado eliminando misión: {e}")
            raise MissionServiceError("Error interno del servidor")
    
    def upload_cellular_data(self, mission_id: str, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Carga datos celulares desde archivo a una misión
        
        Args:
            mission_id: ID de la misión
            file_data: Datos del archivo {"name": "...", "content": "..."}
            
        Returns:
            Diccionario con la misión actualizada
        """
        try:
            logger.info(f"Iniciando carga de datos celulares para misión {mission_id}")
            
            # Procesar archivo
            cellular_records = self.file_processor.process_cellular_file(file_data)
            
            with self.db_manager.get_session() as session:
                # Verificar que la misión existe
                mission = session.query(Mission).filter(Mission.id == mission_id).first()
                if not mission:
                    raise MissionServiceError("Misión no encontrada")
                
                # Limpiar datos celulares existentes
                session.query(CellularData).filter(
                    CellularData.mission_id == mission_id
                ).delete()
                
                # Insertar nuevos datos con todos los campos SCANHUNTER
                for record in cellular_records:
                    cellular_data = CellularData(
                        mission_id=mission_id,
                        file_record_id=record.get('file_record_id'),  # ID original del archivo SCANHUNTER
                        punto=record['punto'],
                        lat=record['lat'],
                        lon=record['lon'],
                        mnc_mcc=record['mnc_mcc'],
                        operator=record['operator'],
                        rssi=record['rssi'],
                        tecnologia=record['tecnologia'],
                        cell_id=record['cell_id'],
                        lac_tac=record.get('lac_tac'),
                        enb=record.get('enb'),
                        channel=record.get('channel'),
                        comentario=record.get('comentario')
                    )
                    session.add(cellular_data)
                
                session.flush()
                
                # Cargar misión actualizada con relaciones
                updated_mission = session.query(Mission).options(
                    joinedload(Mission.cellular_data),
                    joinedload(Mission.creator)
                ).filter(Mission.id == mission_id).first()
                
                session.commit()
                
                result = updated_mission.to_dict_with_relations()
                logger.info(f"Datos celulares cargados: {len(cellular_records)} registros")
                
                return result
                
        except FileProcessorError as e:
            logger.warning(f"Error procesando archivo celular: {e}")
            raise MissionServiceError(str(e))
        except MissionServiceError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos cargando datos celulares: {e}")
            raise MissionServiceError("Error guardando los datos celulares")
        except Exception as e:
            logger.error(f"Error inesperado cargando datos celulares: {e}")
            raise MissionServiceError("Error interno del servidor")
    
    def upload_operator_data(self, mission_id: str, sheet_name: str, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Funcionalidad de carga de datos de operador eliminada
        
        Args:
            mission_id: ID de la misión
            sheet_name: Nombre de la hoja de datos
            file_data: Datos del archivo
            
        Returns:
            Diccionario con la misión actualizada
        """
        # Funcionalidad de operadores eliminada - solo retornar misión actual
        try:
            with self._get_db_manager().get_session() as session:
                mission = session.query(Mission).options(
                    joinedload(Mission.cellular_data),
                    joinedload(Mission.creator)
                ).filter(Mission.id == mission_id).first()
                
                if not mission:
                    raise MissionServiceError("Misión no encontrada")
                
                result = mission.to_dict_with_relations()
                logger.warning(f"Upload de operador solicitado para misión {mission_id} pero funcionalidad eliminada")
                
                return result
                
        except MissionServiceError:
            raise
        except Exception as e:
            logger.error(f"Error accediendo a misión: {e}")
            raise MissionServiceError("Error interno del servidor")
    
    def clear_cellular_data(self, mission_id: str) -> Dict[str, Any]:
        """
        Elimina todos los datos celulares de una misión
        
        Args:
            mission_id: ID de la misión
            
        Returns:
            Diccionario con la misión actualizada
        """
        try:
            with self._get_db_manager().get_session() as session:
                # Verificar que la misión existe
                mission = session.query(Mission).filter(Mission.id == mission_id).first()
                if not mission:
                    raise MissionServiceError("Misión no encontrada")
                
                # Eliminar datos celulares
                deleted_count = session.query(CellularData).filter(
                    CellularData.mission_id == mission_id
                ).delete()
                
                # También limpiar análisis existentes ya que dependen de datos celulares
                session.query(TargetRecord).filter(
                    TargetRecord.mission_id == mission_id
                ).delete()
                
                session.flush()
                
                # Cargar misión actualizada
                updated_mission = session.query(Mission).options(
                    joinedload(Mission.cellular_data),
                    joinedload(Mission.creator)
                ).filter(Mission.id == mission_id).first()
                
                session.commit()
                
                result = updated_mission.to_dict_with_relations()
                logger.info(f"Datos celulares eliminados: {deleted_count} registros de misión {mission.code}")
                
                return result
                
        except MissionServiceError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos limpiando datos celulares: {e}")
            raise MissionServiceError("Error eliminando los datos celulares")
        except Exception as e:
            logger.error(f"Error inesperado limpiando datos celulares: {e}")
            raise MissionServiceError("Error interno del servidor")
    
    def delete_operator_sheet(self, mission_id: str, sheet_id: str) -> Dict[str, Any]:
        """
        Funcionalidad de eliminación de hojas de operador eliminada
        
        Args:
            mission_id: ID de la misión
            sheet_id: ID de la hoja a eliminar
            
        Returns:
            Diccionario con la misión actualizada
        """
        # Funcionalidad de operadores eliminada - solo retornar misión actual
        try:
            with self._get_db_manager().get_session() as session:
                mission = session.query(Mission).options(
                    joinedload(Mission.cellular_data),
                    joinedload(Mission.creator)
                ).filter(Mission.id == mission_id).first()
                
                if not mission:
                    raise MissionServiceError("Misión no encontrada")
                
                result = mission.to_dict_with_relations()
                logger.warning(f"Eliminación de hoja operador solicitada para misión {mission_id} pero funcionalidad eliminada")
                
                return result
                
        except MissionServiceError:
            raise
        except Exception as e:
            logger.error(f"Error accediendo a misión: {e}")
            raise MissionServiceError("Error interno del servidor")
    
    def get_mission_stats(self, mission_id: str) -> Dict[str, Any]:
        """
        Obtiene estadísticas de una misión
        
        Args:
            mission_id: ID de la misión
            
        Returns:
            Diccionario con estadísticas
        """
        try:
            with self._get_db_manager().get_session() as session:
                mission = session.query(Mission).filter(Mission.id == mission_id).first()
                if not mission:
                    raise MissionServiceError("Misión no encontrada")
                
                cellular_count = session.query(CellularData).filter(
                    CellularData.mission_id == mission_id
                ).count()
                
                target_records_count = session.query(TargetRecord).filter(
                    TargetRecord.mission_id == mission_id
                ).count()
                
                return {
                    'cellularRecordsCount': cellular_count,
                    'operatorSheetsCount': 0,  # Funcionalidad eliminada
                    'operatorRecordsCount': 0,  # Funcionalidad eliminada
                    'targetRecordsCount': target_records_count
                }
                
        except MissionServiceError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo estadísticas de misión: {e}")
            raise MissionServiceError("Error accediendo a las estadísticas")
        except Exception as e:
            logger.error(f"Error inesperado obteniendo estadísticas: {e}")
            raise MissionServiceError("Error interno del servidor")


# Instancia global del servicio
mission_service = MissionService()


def get_mission_service() -> MissionService:
    """Retorna la instancia del servicio de misiones"""
    return mission_service