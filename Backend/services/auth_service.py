"""
KRONOS Authentication Service
===============================================================================
Servicio de autenticación que maneja login, verificación de credenciales,
validación de sesiones y gestión de contraseñas.

Características principales:
- Autenticación segura con bcrypt
- Validación de credenciales contra base de datos
- Gestión de estados de sesión
- Logging de intentos de login
- Protección contra ataques de fuerza bruta (futuro)
===============================================================================
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import bcrypt
from sqlalchemy.exc import SQLAlchemyError

from database.connection import get_database_manager
from database.models import User, Role
from utils.validators import validate_email, validate_password_strength

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Excepción personalizada para errores de autenticación"""
    pass


class AuthService:
    """Servicio de autenticación y autorización"""
    
    def __init__(self):
        self._current_user: Optional[Dict[str, Any]] = None
    
    @property
    def db_manager(self):
        """Obtiene el database manager de manera lazy para asegurar que esté inicializado"""
        return get_database_manager()
    
    def login(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """
        Autentica un usuario con email y contraseña
        
        Args:
            credentials: {"email": "...", "password": "..."}
            
        Returns:
            Dict con status y datos del usuario autenticado
            
        Raises:
            AuthenticationError: Si las credenciales son inválidas
        """
        try:
            email = credentials.get('email', '').strip()
            password = credentials.get('password', '')
            
            # Validaciones básicas
            if not email or not password:
                raise AuthenticationError("Email y contraseña son requeridos")
            
            if not validate_email(email):
                raise AuthenticationError("Formato de email inválido")
            
            # Buscar usuario en base de datos
            with self.db_manager.get_session() as session:
                user = session.query(User).filter(
                    User.email == email,
                    User.status == 'active'
                ).first()
                
                if not user:
                    logger.warning(f"Intento de login con email inexistente: {email}")
                    raise AuthenticationError("Credenciales inválidas")
                
                # Verificar contraseña con bcrypt
                if not self._verify_password(password, user.password_hash):
                    logger.warning(f"Intento de login con contraseña incorrecta para: {email}")
                    raise AuthenticationError("Credenciales inválidas")
                
                # Actualizar fecha de último login
                user.last_login = datetime.now()
                session.commit()
                
                # Obtener datos del rol
                role_data = user.role.to_dict() if user.role else None
                
                # Preparar datos del usuario para la respuesta
                user_data = user.to_dict()
                user_data['roleId'] = user.role_id  # Mapear para compatibilidad frontend
                
                self._current_user = {
                    'user': user_data,
                    'role': role_data,
                    'login_time': datetime.now().isoformat()
                }
                
                logger.info(f"Login exitoso para usuario: {email}")
                return {"status": "ok"}
                
        except AuthenticationError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos en login: {e}")
            raise AuthenticationError("Error interno del servidor")
        except Exception as e:
            logger.error(f"Error inesperado en login: {e}")
            raise AuthenticationError("Error interno del servidor")
    
    def logout(self) -> Dict[str, str]:
        """
        Cierra la sesión del usuario actual
        
        Returns:
            Dict confirmando el cierre de sesión
        """
        if self._current_user:
            email = self._current_user['user']['email']
            logger.info(f"Logout exitoso para usuario: {email}")
            
        self._current_user = None
        return {"status": "ok"}
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Retorna los datos del usuario autenticado actualmente"""
        return self._current_user
    
    def is_authenticated(self) -> bool:
        """Verifica si hay un usuario autenticado"""
        return self._current_user is not None
    
    def change_password(self, user_id: str, current_password: str, new_password: str) -> Dict[str, str]:
        """
        Cambia la contraseña de un usuario
        
        Args:
            user_id: ID del usuario
            current_password: Contraseña actual
            new_password: Nueva contraseña
            
        Returns:
            Dict con status del cambio
            
        Raises:
            AuthenticationError: Si hay errores en el proceso
        """
        try:
            # Validar nueva contraseña
            if not validate_password_strength(new_password):
                raise AuthenticationError("La nueva contraseña no cumple con los requisitos de seguridad")
            
            with self.db_manager.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                
                if not user:
                    raise AuthenticationError("Usuario no encontrado")
                
                # Verificar contraseña actual
                if not self._verify_password(current_password, user.password_hash):
                    raise AuthenticationError("Contraseña actual incorrecta")
                
                # Hashear nueva contraseña
                new_hash = self._hash_password(new_password)
                user.password_hash = new_hash
                session.commit()
                
                logger.info(f"Contraseña cambiada exitosamente para usuario: {user.email}")
                return {"status": "ok"}
                
        except AuthenticationError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos cambiando contraseña: {e}")
            raise AuthenticationError("Error interno del servidor")
        except Exception as e:
            logger.error(f"Error inesperado cambiando contraseña: {e}")
            raise AuthenticationError("Error interno del servidor")
    
    def reset_password(self, email: str, new_password: str) -> Dict[str, str]:
        """
        Resetea la contraseña de un usuario (solo para administradores)
        
        Args:
            email: Email del usuario
            new_password: Nueva contraseña
            
        Returns:
            Dict con status del reset
            
        Raises:
            AuthenticationError: Si hay errores en el proceso
        """
        try:
            # Validar nueva contraseña
            if not validate_password_strength(new_password):
                raise AuthenticationError("La nueva contraseña no cumple con los requisitos de seguridad")
            
            with self.db_manager.get_session() as session:
                user = session.query(User).filter(User.email == email).first()
                
                if not user:
                    raise AuthenticationError("Usuario no encontrado")
                
                # Hashear nueva contraseña
                new_hash = self._hash_password(new_password)
                user.password_hash = new_hash
                session.commit()
                
                logger.info(f"Contraseña reseteada exitosamente para usuario: {email}")
                return {"status": "ok"}
                
        except AuthenticationError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos reseteando contraseña: {e}")
            raise AuthenticationError("Error interno del servidor")
        except Exception as e:
            logger.error(f"Error inesperado reseteando contraseña: {e}")
            raise AuthenticationError("Error interno del servidor")
    
    def has_permission(self, resource: str, action: str) -> bool:
        """
        Verifica si el usuario actual tiene un permiso específico
        
        Args:
            resource: Recurso a verificar (users, roles, missions, etc.)
            action: Acción a verificar (create, read, update, delete, execute)
            
        Returns:
            True si tiene el permiso
        """
        if not self.is_authenticated():
            return False
        
        try:
            user_data = self._current_user['user']
            role_data = self._current_user['role']
            
            if not role_data:
                return False
            
            permissions = role_data.get('permissions', {})
            resource_perms = permissions.get(resource, {})
            
            return resource_perms.get(action, False)
            
        except Exception as e:
            logger.error(f"Error verificando permisos: {e}")
            return False
    
    def require_permission(self, resource: str, action: str) -> None:
        """
        Requiere un permiso específico, lanza excepción si no lo tiene
        
        Args:
            resource: Recurso requerido
            action: Acción requerida
            
        Raises:
            AuthenticationError: Si no tiene el permiso
        """
        if not self.has_permission(resource, action):
            raise AuthenticationError(f"No tiene permisos para {action} en {resource}")
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """
        Verifica una contraseña contra su hash
        
        Args:
            password: Contraseña en texto plano
            password_hash: Hash bcrypt almacenado
            
        Returns:
            True si la contraseña coincide
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error verificando contraseña: {e}")
            return False
    
    def _hash_password(self, password: str) -> str:
        """
        Hashea una contraseña usando bcrypt
        
        Args:
            password: Contraseña en texto plano
            
        Returns:
            Hash bcrypt como string
        """
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


# Instancia global del servicio de autenticación
auth_service = AuthService()


def get_auth_service() -> AuthService:
    """Retorna la instancia del servicio de autenticación"""
    return auth_service


def require_auth(func):
    """
    Decorador que requiere autenticación para ejecutar una función
    
    Usage:
        @require_auth
        def some_protected_function():
            pass
    """
    def wrapper(*args, **kwargs):
        if not auth_service.is_authenticated():
            raise AuthenticationError("Autenticación requerida")
        return func(*args, **kwargs)
    return wrapper


def require_permission(resource: str, action: str):
    """
    Decorador que requiere un permiso específico
    
    Usage:
        @require_permission('users', 'create')
        def create_user_function():
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            auth_service.require_permission(resource, action)
            return func(*args, **kwargs)
        return wrapper
    return decorator