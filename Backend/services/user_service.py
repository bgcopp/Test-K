"""
KRONOS User Service
===============================================================================
Servicio para gestión completa de usuarios incluyendo operaciones CRUD,
validaciones, gestión de contraseñas y verificación de permisos.

Características principales:
- Operaciones CRUD completas para usuarios
- Validación exhaustiva de datos
- Gestión segura de contraseñas con bcrypt
- Verificación de unicidad de email
- Mapeo automático entre BD y frontend
- Logging detallado de operaciones
- Manejo robusto de errores
===============================================================================
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import joinedload
import bcrypt

from database.connection import get_database_manager
from database.models import User, Role
from utils.validators import validate_user_data, ValidationError
from utils.helpers import (
    generate_user_id, 
    map_user_to_frontend,
    get_current_timestamp
)

logger = logging.getLogger(__name__)


class UserServiceError(Exception):
    """Excepción personalizada para errores del servicio de usuarios"""
    pass


class UserService:
    """Servicio de gestión de usuarios"""
    
    def __init__(self):
        self.db_manager = None
    
    def _get_db_manager(self):
        """Obtiene el DB manager de forma lazy"""
        if self.db_manager is None:
            self.db_manager = get_database_manager()
        return self.db_manager
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los usuarios con sus roles
        
        Returns:
            Lista de diccionarios con datos de usuarios
            
        Raises:
            UserServiceError: Si hay error accediendo a los datos
        """
        try:
            with self._get_db_manager().get_session() as session:
                # Cargar usuarios con roles en una consulta
                users = session.query(User).options(
                    joinedload(User.role)
                ).order_by(User.name).all()
                
                result = []
                for user in users:
                    user_dict = map_user_to_frontend(user.to_dict())
                    result.append(user_dict)
                
                logger.info(f"Recuperados {len(result)} usuarios")
                return result
                
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos obteniendo usuarios: {e}")
            raise UserServiceError("Error accediendo a los datos de usuarios")
        except Exception as e:
            logger.error(f"Error inesperado obteniendo usuarios: {e}")
            raise UserServiceError("Error interno del servidor")
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un usuario por su ID
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Diccionario con datos del usuario o None si no existe
            
        Raises:
            UserServiceError: Si hay error accediendo a los datos
        """
        try:
            with self._get_db_manager().get_session() as session:
                user = session.query(User).options(
                    joinedload(User.role)
                ).filter(User.id == user_id).first()
                
                if user:
                    return map_user_to_frontend(user.to_dict())
                return None
                
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos obteniendo usuario {user_id}: {e}")
            raise UserServiceError("Error accediendo a los datos del usuario")
        except Exception as e:
            logger.error(f"Error inesperado obteniendo usuario {user_id}: {e}")
            raise UserServiceError("Error interno del servidor")
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un usuario por su email
        
        Args:
            email: Email del usuario
            
        Returns:
            Diccionario con datos del usuario o None si no existe
        """
        try:
            with self._get_db_manager().get_session() as session:
                user = session.query(User).options(
                    joinedload(User.role)
                ).filter(User.email == email.lower().strip()).first()
                
                if user:
                    return map_user_to_frontend(user.to_dict())
                return None
                
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos obteniendo usuario por email {email}: {e}")
            raise UserServiceError("Error accediendo a los datos del usuario")
        except Exception as e:
            logger.error(f"Error inesperado obteniendo usuario por email {email}: {e}")
            raise UserServiceError("Error interno del servidor")
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un nuevo usuario
        
        Args:
            user_data: Datos del usuario a crear
            
        Returns:
            Diccionario con datos del usuario creado
            
        Raises:
            UserServiceError: Si hay errores en la creación
        """
        try:
            # Validar datos
            validated_data = validate_user_data(user_data, is_update=False)
            
            with self._get_db_manager().get_session() as session:
                # Verificar que el email no esté en uso
                existing_user = session.query(User).filter(
                    User.email == validated_data['email']
                ).first()
                
                if existing_user:
                    raise UserServiceError("El email ya está registrado")
                
                # Verificar que el rol existe
                role = session.query(Role).filter(
                    Role.id == validated_data['role_id']
                ).first()
                
                if not role:
                    raise UserServiceError("El rol especificado no existe")
                
                # Generar ID único
                user_id = generate_user_id()
                
                # Hashear contraseña por defecto
                default_password = user_data.get('password', 'password')
                password_hash = self._hash_password(default_password)
                
                # Crear usuario
                new_user = User(
                    id=user_id,
                    name=validated_data['name'],
                    email=validated_data['email'],
                    password_hash=password_hash,
                    role_id=validated_data['role_id'],
                    status=validated_data.get('status', 'active'),
                    avatar=validated_data.get('avatar', f'https://picsum.photos/seed/{user_id}/100/100')
                )
                
                session.add(new_user)
                session.flush()  # Para obtener el ID generado
                
                # Cargar el usuario con su rol
                created_user = session.query(User).options(
                    joinedload(User.role)
                ).filter(User.id == user_id).first()
                
                session.commit()
                
                result = map_user_to_frontend(created_user.to_dict())
                logger.info(f"Usuario creado exitosamente: {validated_data['email']}")
                
                return result
                
        except ValidationError as e:
            logger.warning(f"Error de validación creando usuario: {e}")
            raise UserServiceError(str(e))
        except UserServiceError:
            raise
        except IntegrityError as e:
            logger.error(f"Error de integridad creando usuario: {e}")
            raise UserServiceError("El email ya está registrado")
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos creando usuario: {e}")
            raise UserServiceError("Error guardando el usuario")
        except Exception as e:
            logger.error(f"Error inesperado creando usuario: {e}")
            raise UserServiceError("Error interno del servidor")
    
    def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza un usuario existente
        
        Args:
            user_id: ID del usuario a actualizar
            user_data: Datos actualizados del usuario
            
        Returns:
            Diccionario con datos del usuario actualizado
            
        Raises:
            UserServiceError: Si hay errores en la actualización
        """
        try:
            # Validar datos para actualización
            validated_data = validate_user_data(user_data, is_update=True)
            
            with self._get_db_manager().get_session() as session:
                # Buscar usuario
                user = session.query(User).filter(User.id == user_id).first()
                
                if not user:
                    raise UserServiceError("Usuario no encontrado")
                
                # Si se actualiza email, verificar que no esté en uso
                if 'email' in validated_data:
                    existing_user = session.query(User).filter(
                        User.email == validated_data['email'],
                        User.id != user_id
                    ).first()
                    
                    if existing_user:
                        raise UserServiceError("El email ya está registrado")
                
                # Si se actualiza rol, verificar que existe
                if 'role_id' in validated_data:
                    role = session.query(Role).filter(
                        Role.id == validated_data['role_id']
                    ).first()
                    
                    if not role:
                        raise UserServiceError("El rol especificado no existe")
                
                # Actualizar campos
                for field, value in validated_data.items():
                    setattr(user, field, value)
                
                # Actualizar contraseña si se proporciona
                if 'password' in user_data:
                    user.password_hash = self._hash_password(user_data['password'])
                
                session.flush()
                
                # Cargar usuario actualizado con su rol
                updated_user = session.query(User).options(
                    joinedload(User.role)
                ).filter(User.id == user_id).first()
                
                session.commit()
                
                result = map_user_to_frontend(updated_user.to_dict())
                logger.info(f"Usuario actualizado exitosamente: {user.email}")
                
                return result
                
        except ValidationError as e:
            logger.warning(f"Error de validación actualizando usuario: {e}")
            raise UserServiceError(str(e))
        except UserServiceError:
            raise
        except IntegrityError as e:
            logger.error(f"Error de integridad actualizando usuario: {e}")
            raise UserServiceError("El email ya está registrado")
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos actualizando usuario: {e}")
            raise UserServiceError("Error guardando los cambios")
        except Exception as e:
            logger.error(f"Error inesperado actualizando usuario: {e}")
            raise UserServiceError("Error interno del servidor")
    
    def delete_user(self, user_id: str) -> Dict[str, str]:
        """
        Elimina un usuario
        
        Args:
            user_id: ID del usuario a eliminar
            
        Returns:
            Diccionario confirmando la eliminación
            
        Raises:
            UserServiceError: Si hay errores en la eliminación
        """
        try:
            with self._get_db_manager().get_session() as session:
                # Buscar usuario
                user = session.query(User).filter(User.id == user_id).first()
                
                if not user:
                    raise UserServiceError("Usuario no encontrado")
                
                # Verificar que no sea el último admin (opcional)
                if user.role and user.role.name == 'Super Administrador':
                    admin_count = session.query(User).join(Role).filter(
                        Role.name == 'Super Administrador',
                        User.status == 'active'
                    ).count()
                    
                    if admin_count <= 1:
                        raise UserServiceError("No se puede eliminar el último administrador")
                
                user_email = user.email
                session.delete(user)
                session.commit()
                
                logger.info(f"Usuario eliminado exitosamente: {user_email}")
                return {"status": "ok"}
                
        except UserServiceError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos eliminando usuario: {e}")
            raise UserServiceError("Error eliminando el usuario")
        except Exception as e:
            logger.error(f"Error inesperado eliminando usuario: {e}")
            raise UserServiceError("Error interno del servidor")
    
    def change_user_status(self, user_id: str, status: str) -> Dict[str, Any]:
        """
        Cambia el status de un usuario
        
        Args:
            user_id: ID del usuario
            status: Nuevo status ('active' o 'inactive')
            
        Returns:
            Diccionario con datos del usuario actualizado
            
        Raises:
            UserServiceError: Si hay errores en el cambio
        """
        try:
            if status not in ['active', 'inactive']:
                raise UserServiceError("Status inválido")
            
            with self._get_db_manager().get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                
                if not user:
                    raise UserServiceError("Usuario no encontrado")
                
                # Si se inactiva un admin, verificar que no sea el último
                if status == 'inactive' and user.role and user.role.name == 'Super Administrador':
                    active_admin_count = session.query(User).join(Role).filter(
                        Role.name == 'Super Administrador',
                        User.status == 'active',
                        User.id != user_id
                    ).count()
                    
                    if active_admin_count < 1:
                        raise UserServiceError("No se puede inactivar el último administrador activo")
                
                user.status = status
                session.commit()
                
                result = map_user_to_frontend(user.to_dict())
                logger.info(f"Status de usuario cambiado a {status}: {user.email}")
                
                return result
                
        except UserServiceError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos cambiando status de usuario: {e}")
            raise UserServiceError("Error actualizando el status")
        except Exception as e:
            logger.error(f"Error inesperado cambiando status de usuario: {e}")
            raise UserServiceError("Error interno del servidor")
    
    def reset_user_password(self, user_id: str, new_password: str = "password") -> Dict[str, str]:
        """
        Resetea la contraseña de un usuario
        
        Args:
            user_id: ID del usuario
            new_password: Nueva contraseña (por defecto "password")
            
        Returns:
            Diccionario confirmando el reset
            
        Raises:
            UserServiceError: Si hay errores en el reset
        """
        try:
            with self._get_db_manager().get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                
                if not user:
                    raise UserServiceError("Usuario no encontrado")
                
                user.password_hash = self._hash_password(new_password)
                session.commit()
                
                logger.info(f"Contraseña reseteada para usuario: {user.email}")
                return {"status": "ok"}
                
        except UserServiceError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos reseteando contraseña: {e}")
            raise UserServiceError("Error reseteando la contraseña")
        except Exception as e:
            logger.error(f"Error inesperado reseteando contraseña: {e}")
            raise UserServiceError("Error interno del servidor")
    
    def get_users_by_role(self, role_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene usuarios por rol
        
        Args:
            role_id: ID del rol
            
        Returns:
            Lista de usuarios con ese rol
        """
        try:
            with self._get_db_manager().get_session() as session:
                users = session.query(User).options(
                    joinedload(User.role)
                ).filter(User.role_id == role_id).order_by(User.name).all()
                
                result = []
                for user in users:
                    user_dict = map_user_to_frontend(user.to_dict())
                    result.append(user_dict)
                
                return result
                
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo usuarios por rol {role_id}: {e}")
            raise UserServiceError("Error accediendo a los datos")
        except Exception as e:
            logger.error(f"Error inesperado obteniendo usuarios por rol: {e}")
            raise UserServiceError("Error interno del servidor")
    
    def search_users(self, query: str) -> List[Dict[str, Any]]:
        """
        Busca usuarios por nombre o email
        
        Args:
            query: Término de búsqueda
            
        Returns:
            Lista de usuarios que coinciden
        """
        try:
            with self._get_db_manager().get_session() as session:
                search_term = f"%{query.lower()}%"
                
                users = session.query(User).options(
                    joinedload(User.role)
                ).filter(
                    (User.name.ilike(search_term)) |
                    (User.email.ilike(search_term))
                ).order_by(User.name).all()
                
                result = []
                for user in users:
                    user_dict = map_user_to_frontend(user.to_dict())
                    result.append(user_dict)
                
                return result
                
        except SQLAlchemyError as e:
            logger.error(f"Error buscando usuarios: {e}")
            raise UserServiceError("Error en la búsqueda")
        except Exception as e:
            logger.error(f"Error inesperado buscando usuarios: {e}")
            raise UserServiceError("Error interno del servidor")
    
    def _hash_password(self, password: str) -> str:
        """
        Hashea una contraseña usando bcrypt
        
        Args:
            password: Contraseña en texto plano
            
        Returns:
            Hash de la contraseña
        """
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


# Instancia global del servicio
user_service = UserService()


def get_user_service() -> UserService:
    """Retorna la instancia del servicio de usuarios"""
    return user_service