"""
KRONOS Role Service
===============================================================================
Servicio para gestión completa de roles incluyendo operaciones CRUD,
validación de permisos, verificación de dependencias con usuarios
y manejo de roles del sistema.

Características principales:
- Operaciones CRUD completas para roles
- Validación exhaustiva de estructura de permisos
- Verificación de dependencias antes de eliminación
- Protección de roles críticos del sistema
- Mapeo automático entre BD y frontend
- Logging detallado de operaciones
- Manejo robusto de errores
===============================================================================
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import joinedload
import json

from database.connection import get_database_manager
from database.models import Role, User
from utils.validators import validate_role_data, ValidationError
from utils.helpers import generate_role_id, get_current_timestamp

logger = logging.getLogger(__name__)


class RoleServiceError(Exception):
    """Excepción personalizada para errores del servicio de roles"""
    pass


class RoleService:
    """Servicio de gestión de roles"""
    
    # Roles protegidos que no se pueden eliminar
    PROTECTED_ROLES = {'Super Administrador'}
    
    def __init__(self):
        self.db_manager = None
    
    def _get_db_manager(self):
        """Obtiene el DB manager de forma lazy"""
        if self.db_manager is None:
            self.db_manager = get_database_manager()
        return self.db_manager
    
    def get_all_roles(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los roles con conteo de usuarios asignados
        
        Returns:
            Lista de diccionarios con datos de roles
            
        Raises:
            RoleServiceError: Si hay error accediendo a los datos
        """
        try:
            with self._get_db_manager().get_session() as session:
                roles = session.query(Role).order_by(Role.name).all()
                
                result = []
                for role in roles:
                    role_dict = role.to_dict()
                    
                    # Agregar conteo de usuarios
                    user_count = session.query(User).filter(User.role_id == role.id).count()
                    role_dict['userCount'] = user_count
                    
                    result.append(role_dict)
                
                logger.info(f"Recuperados {len(result)} roles")
                return result
                
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos obteniendo roles: {e}")
            raise RoleServiceError("Error accediendo a los datos de roles")
        except Exception as e:
            logger.error(f"Error inesperado obteniendo roles: {e}")
            raise RoleServiceError("Error interno del servidor")
    
    def get_role_by_id(self, role_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un rol por su ID
        
        Args:
            role_id: ID del rol
            
        Returns:
            Diccionario con datos del rol o None si no existe
            
        Raises:
            RoleServiceError: Si hay error accediendo a los datos
        """
        try:
            with self._get_db_manager().get_session() as session:
                role = session.query(Role).filter(Role.id == role_id).first()
                
                if role:
                    role_dict = role.to_dict()
                    
                    # Agregar conteo de usuarios
                    user_count = session.query(User).filter(User.role_id == role.id).count()
                    role_dict['userCount'] = user_count
                    
                    return role_dict
                return None
                
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos obteniendo rol {role_id}: {e}")
            raise RoleServiceError("Error accediendo a los datos del rol")
        except Exception as e:
            logger.error(f"Error inesperado obteniendo rol {role_id}: {e}")
            raise RoleServiceError("Error interno del servidor")
    
    def create_role(self, role_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un nuevo rol
        
        Args:
            role_data: Datos del rol a crear {"name": "...", "permissions": {...}}
            
        Returns:
            Diccionario con datos del rol creado
            
        Raises:
            RoleServiceError: Si hay errores en la creación
        """
        try:
            # Validar datos
            validated_data = validate_role_data(role_data, is_update=False)
            
            with self.db_manager.get_session() as session:
                # Verificar que el nombre no esté en uso
                existing_role = session.query(Role).filter(
                    Role.name == validated_data['name']
                ).first()
                
                if existing_role:
                    raise RoleServiceError("Ya existe un rol con ese nombre")
                
                # Generar ID único
                role_id = generate_role_id()
                
                # Crear rol
                new_role = Role(
                    id=role_id,
                    name=validated_data['name'],
                    permissions=json.dumps(validated_data['permissions'])
                )
                
                session.add(new_role)
                session.flush()
                
                # Obtener el rol creado con su diccionario completo
                created_role = session.query(Role).filter(Role.id == role_id).first()
                session.commit()
                
                result = created_role.to_dict()
                result['userCount'] = 0  # Nuevo rol no tiene usuarios asignados
                
                logger.info(f"Rol creado exitosamente: {validated_data['name']}")
                return result
                
        except ValidationError as e:
            logger.warning(f"Error de validación creando rol: {e}")
            raise RoleServiceError(str(e))
        except RoleServiceError:
            raise
        except IntegrityError as e:
            logger.error(f"Error de integridad creando rol: {e}")
            raise RoleServiceError("Ya existe un rol con ese nombre")
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos creando rol: {e}")
            raise RoleServiceError("Error guardando el rol")
        except Exception as e:
            logger.error(f"Error inesperado creando rol: {e}")
            raise RoleServiceError("Error interno del servidor")
    
    def update_role(self, role_id: str, role_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza un rol existente
        
        Args:
            role_id: ID del rol a actualizar
            role_data: Datos actualizados del rol
            
        Returns:
            Diccionario con datos del rol actualizado
            
        Raises:
            RoleServiceError: Si hay errores en la actualización
        """
        try:
            # Validar datos para actualización
            validated_data = validate_role_data(role_data, is_update=True)
            
            with self.db_manager.get_session() as session:
                # Buscar rol
                role = session.query(Role).filter(Role.id == role_id).first()
                
                if not role:
                    raise RoleServiceError("Rol no encontrado")
                
                # Verificar si es un rol protegido y se intenta cambiar nombre crítico
                if (role.name in self.PROTECTED_ROLES and 
                    'name' in validated_data and 
                    validated_data['name'] not in self.PROTECTED_ROLES):
                    raise RoleServiceError("No se puede modificar el nombre de este rol del sistema")
                
                # Si se actualiza nombre, verificar que no esté en uso
                if 'name' in validated_data:
                    existing_role = session.query(Role).filter(
                        Role.name == validated_data['name'],
                        Role.id != role_id
                    ).first()
                    
                    if existing_role:
                        raise RoleServiceError("Ya existe un rol con ese nombre")
                
                # Actualizar campos
                if 'name' in validated_data:
                    role.name = validated_data['name']
                
                if 'permissions' in validated_data:
                    role.permissions = json.dumps(validated_data['permissions'])
                
                session.flush()
                
                # Obtener rol actualizado
                updated_role = session.query(Role).filter(Role.id == role_id).first()
                session.commit()
                
                result = updated_role.to_dict()
                # Agregar conteo de usuarios
                user_count = session.query(User).filter(User.role_id == role_id).count()
                result['userCount'] = user_count
                
                logger.info(f"Rol actualizado exitosamente: {role.name}")
                return result
                
        except ValidationError as e:
            logger.warning(f"Error de validación actualizando rol: {e}")
            raise RoleServiceError(str(e))
        except RoleServiceError:
            raise
        except IntegrityError as e:
            logger.error(f"Error de integridad actualizando rol: {e}")
            raise RoleServiceError("Ya existe un rol con ese nombre")
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos actualizando rol: {e}")
            raise RoleServiceError("Error guardando los cambios")
        except Exception as e:
            logger.error(f"Error inesperado actualizando rol: {e}")
            raise RoleServiceError("Error interno del servidor")
    
    def delete_role(self, role_id: str) -> Dict[str, str]:
        """
        Elimina un rol
        
        Args:
            role_id: ID del rol a eliminar
            
        Returns:
            Diccionario confirmando la eliminación
            
        Raises:
            RoleServiceError: Si hay errores en la eliminación
        """
        try:
            with self._get_db_manager().get_session() as session:
                # Buscar rol
                role = session.query(Role).filter(Role.id == role_id).first()
                
                if not role:
                    raise RoleServiceError("Rol no encontrado")
                
                # Verificar que no sea un rol protegido
                if role.name in self.PROTECTED_ROLES:
                    raise RoleServiceError("No se puede eliminar este rol del sistema")
                
                # Verificar que no tenga usuarios asignados
                user_count = session.query(User).filter(User.role_id == role_id).count()
                if user_count > 0:
                    raise RoleServiceError(f"No se puede eliminar el rol porque tiene {user_count} usuario(s) asignado(s)")
                
                role_name = role.name
                session.delete(role)
                session.commit()
                
                logger.info(f"Rol eliminado exitosamente: {role_name}")
                return {"status": "ok"}
                
        except RoleServiceError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos eliminando rol: {e}")
            raise RoleServiceError("Error eliminando el rol")
        except Exception as e:
            logger.error(f"Error inesperado eliminando rol: {e}")
            raise RoleServiceError("Error interno del servidor")
    
    def get_role_permissions(self, role_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene los permisos de un rol específico
        
        Args:
            role_id: ID del rol
            
        Returns:
            Diccionario con los permisos o None si no existe
        """
        try:
            with self._get_db_manager().get_session() as session:
                role = session.query(Role).filter(Role.id == role_id).first()
                
                if role:
                    return role.get_permissions_dict()
                return None
                
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo permisos del rol {role_id}: {e}")
            raise RoleServiceError("Error accediendo a los permisos")
        except Exception as e:
            logger.error(f"Error inesperado obteniendo permisos del rol: {e}")
            raise RoleServiceError("Error interno del servidor")
    
    def update_role_permissions(self, role_id: str, permissions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza solo los permisos de un rol
        
        Args:
            role_id: ID del rol
            permissions: Nueva estructura de permisos
            
        Returns:
            Diccionario con datos del rol actualizado
        """
        return self.update_role(role_id, {'permissions': permissions})
    
    def get_users_with_role(self, role_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene lista de usuarios que tienen un rol específico
        
        Args:
            role_id: ID del rol
            
        Returns:
            Lista de usuarios con ese rol
        """
        try:
            with self._get_db_manager().get_session() as session:
                users = session.query(User).filter(
                    User.role_id == role_id
                ).order_by(User.name).all()
                
                result = []
                for user in users:
                    user_dict = user.to_dict()
                    result.append(user_dict)
                
                return result
                
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo usuarios del rol {role_id}: {e}")
            raise RoleServiceError("Error accediendo a los datos")
        except Exception as e:
            logger.error(f"Error inesperado obteniendo usuarios del rol: {e}")
            raise RoleServiceError("Error interno del servidor")
    
    def duplicate_role(self, role_id: str, new_name: str) -> Dict[str, Any]:
        """
        Duplica un rol existente con un nuevo nombre
        
        Args:
            role_id: ID del rol a duplicar
            new_name: Nombre para el nuevo rol
            
        Returns:
            Diccionario con datos del rol duplicado
        """
        try:
            with self._get_db_manager().get_session() as session:
                # Buscar rol original
                original_role = session.query(Role).filter(Role.id == role_id).first()
                
                if not original_role:
                    raise RoleServiceError("Rol original no encontrado")
                
                # Verificar que el nuevo nombre no esté en uso
                existing_role = session.query(Role).filter(Role.name == new_name).first()
                if existing_role:
                    raise RoleServiceError("Ya existe un rol con ese nombre")
                
                # Crear el rol duplicado
                role_data = {
                    'name': new_name,
                    'permissions': original_role.get_permissions_dict()
                }
                
                return self.create_role(role_data)
                
        except RoleServiceError:
            raise
        except Exception as e:
            logger.error(f"Error duplicando rol: {e}")
            raise RoleServiceError("Error duplicando el rol")
    
    def get_default_permissions(self) -> Dict[str, Any]:
        """
        Retorna estructura de permisos por defecto para nuevos roles
        
        Returns:
            Diccionario con permisos básicos
        """
        return {
            "users": {
                "create": False,
                "read": True,
                "update": False,
                "delete": False
            },
            "roles": {
                "create": False,
                "read": True,
                "update": False,
                "delete": False
            },
            "missions": {
                "create": False,
                "read": True,
                "update": False,
                "delete": False
            },
            "dashboard": {
                "read": True
            },
            "targetAnalysis": {
                "execute": False
            }
        }
    
    def validate_permissions_structure(self, permissions: Dict[str, Any]) -> bool:
        """
        Valida que una estructura de permisos sea correcta
        
        Args:
            permissions: Estructura de permisos a validar
            
        Returns:
            True si es válida
        """
        try:
            from utils.validators import validate_permissions_structure
            validate_permissions_structure(permissions)
            return True
        except ValidationError:
            return False


# Instancia global del servicio
role_service = RoleService()


def get_role_service() -> RoleService:
    """Retorna la instancia del servicio de roles"""
    return role_service