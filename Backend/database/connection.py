"""
KRONOS Database Connection Manager
===============================================================================
Gestiona la conexión a la base de datos SQLite y proporciona funciones de
inicialización, configuración y mantenimiento.

Características principales:
- Conexión singleton para SQLite
- Inicialización automática de esquema si no existe
- Carga de datos iniciales en primera ejecución
- Configuración optimizada de SQLite para rendimiento
- Manejo robusto de errores y transacciones
- Funciones de utilidad para mantenimiento
===============================================================================
"""

import os
import sqlite3
import logging
from pathlib import Path
from typing import Optional
from contextlib import contextmanager
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import bcrypt
import json

from .models import Base, User, Role, Mission, get_all_models

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de la base de datos
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'kronos.db')
DEFAULT_SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')
DEFAULT_INITIAL_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'initial_data.sql')


class DatabaseManager:
    """Gestor de conexión y operaciones de base de datos"""
    
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = os.path.abspath(db_path)
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
        self._initialized = False
        
    def initialize(self, force_recreate: bool = False) -> None:
        """
        Inicializa la base de datos y crea las conexiones necesarias
        
        Args:
            force_recreate: Si True, elimina la BD existente y la recrea
        """
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Si force_recreate, eliminar DB existente
            if force_recreate and os.path.exists(self.db_path):
                os.remove(self.db_path)
                logger.info(f"Base de datos eliminada: {self.db_path}")
            
            # Verificar si es una nueva instalación
            is_new_database = not os.path.exists(self.db_path)
            
            # Crear engine y configurar SQLite
            self.engine = create_engine(
                f'sqlite:///{self.db_path}',
                echo=False,  # Cambiar a True para debug SQL
                pool_pre_ping=True,
                # pool_recycle removido - no necesario para SQLite file-based
                connect_args={
                    'check_same_thread': False,
                    'timeout': 20
                }
            )
            
            # Configurar eventos SQLite
            self._setup_sqlite_events()
            
            # Crear SessionMaker
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Inicializar esquema y datos según sea necesario
            if is_new_database:
                logger.info("Nueva base de datos detectada. Inicializando esquema y datos...")
                self._create_schema()
                self._load_initial_data()
                logger.info("Base de datos nueva inicializada exitosamente")
            else:
                logger.info(f"Conectado a base de datos existente: {self.db_path}")
                # Asegurar que el esquema esté actualizado
                self._ensure_schema_exists()
                # Verificar y reparar datos faltantes
                self._ensure_initial_data_exists()
            
            # Verificar integridad final de la base de datos
            self._verify_database_integrity()
            
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Error al inicializar la base de datos: {e}")
            raise
    
    def _setup_sqlite_events(self) -> None:
        """Configura eventos SQLite para optimización"""
        
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Configura pragmas SQLite para mejor rendimiento y integridad"""
            cursor = dbapi_connection.cursor()
            
            # Configuraciones críticas de SQLite
            pragmas = [
                "PRAGMA foreign_keys=ON",              # Habilitar foreign keys
                "PRAGMA journal_mode=WAL",             # Write-Ahead Logging
                "PRAGMA synchronous=NORMAL",           # Balance seguridad/velocidad
                "PRAGMA cache_size=10000",             # 10MB cache
                "PRAGMA temp_store=MEMORY",            # Temporales en memoria
                "PRAGMA mmap_size=268435456",          # 256MB memory mapping
                "PRAGMA optimize"                       # Optimizar estadísticas
            ]
            
            for pragma in pragmas:
                try:
                    cursor.execute(pragma)
                except sqlite3.Error as e:
                    logger.warning(f"No se pudo aplicar pragma '{pragma}': {e}")
            
            cursor.close()
    
    def _create_schema(self) -> None:
        """Crea el esquema de la base de datos desde schema.sql"""
        try:
            # Crear todas las tablas definidas en los modelos
            Base.metadata.create_all(self.engine)
            logger.info("Esquema de base de datos creado exitosamente")
            
        except Exception as e:
            logger.error(f"Error al crear esquema: {e}")
            raise
    
    def _ensure_schema_exists(self) -> None:
        """Asegura que el esquema exista y esté actualizado en BD existente"""
        try:
            # Verificar que el esquema esté actualizado
            Base.metadata.create_all(self.engine)
            logger.info("Esquema verificado y actualizado")
            
        except Exception as e:
            logger.error(f"Error al verificar esquema: {e}")
            raise
    
    def _ensure_initial_data_exists(self) -> None:
        """Verifica y carga datos iniciales si faltan en BD existente"""
        try:
            session = self.SessionLocal()
            try:
                # Verificar roles
                role_count = session.query(Role).count()
                user_count = session.query(User).count()
                
                if role_count == 0:
                    logger.info("Datos iniciales faltantes detectados. Iniciando auto-reparación...")
                    self._create_initial_roles(session)
                    logger.info("Roles iniciales restaurados")
                
                if user_count == 0:
                    logger.info("Usuarios iniciales faltantes. Restaurando...")
                    self._create_initial_users(session)
                    logger.info("Usuarios iniciales restaurados")
                
                # Verificar misiones de ejemplo solo si no existen
                mission_count = session.query(Mission).count()
                if mission_count == 0:
                    logger.info("Misiones de ejemplo faltantes. Restaurando...")
                    self._create_initial_missions(session)
                    logger.info("Misiones de ejemplo restauradas")
                
                session.commit()
                
                if role_count == 0 or user_count == 0 or mission_count == 0:
                    logger.info("Auto-reparación completada exitosamente")
                
            except Exception as e:
                session.rollback()
                logger.error(f"Error en auto-reparación: {e}")
                raise
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error verificando datos iniciales: {e}")
            raise
    
    def _load_initial_data(self) -> None:
        """Carga los datos iniciales en la base de datos"""
        try:
            session = self.SessionLocal()
            try:
                # Verificar si ya existen datos
                if session.query(Role).count() > 0:
                    logger.info("Datos iniciales ya existen, omitiendo carga")
                    return
                
                # Crear datos iniciales usando Python (más confiable que SQL)
                self._create_initial_roles(session)
                self._create_initial_users(session)
                self._create_initial_missions(session)
                
                session.commit()
                logger.info("Datos iniciales cargados exitosamente")
            except Exception as e:
                session.rollback()
                raise
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error al cargar datos iniciales: {e}")
            raise
    
    def _create_initial_roles(self, session: Session) -> None:
        """Crea los roles iniciales"""
        roles_data = [
            {
                'id': '1',
                'name': 'Super Administrador',
                'permissions': {
                    "users": {"create": True, "read": True, "update": True, "delete": True},
                    "roles": {"create": True, "read": True, "update": True, "delete": True},
                    "missions": {"create": True, "read": True, "update": True, "delete": True},
                    "dashboard": {"read": True},
                    "targetAnalysis": {"execute": True}
                }
            },
            {
                'id': '2',
                'name': 'Editor de Misiones',
                'permissions': {
                    "users": {"create": False, "read": True, "update": False, "delete": False},
                    "roles": {"create": False, "read": True, "update": False, "delete": False},
                    "missions": {"create": True, "read": True, "update": True, "delete": False},
                    "dashboard": {"read": True},
                    "targetAnalysis": {"execute": True}
                }
            },
            {
                'id': '3',
                'name': 'Visualizador',
                'permissions': {
                    "users": {"create": False, "read": True, "update": False, "delete": False},
                    "roles": {"create": False, "read": True, "update": False, "delete": False},
                    "missions": {"create": False, "read": True, "update": False, "delete": False},
                    "dashboard": {"read": True},
                    "targetAnalysis": {"execute": False}
                }
            }
        ]
        
        for role_data in roles_data:
            role = Role(
                id=role_data['id'],
                name=role_data['name'],
                permissions=json.dumps(role_data['permissions'])
            )
            session.add(role)
    
    def _create_initial_users(self, session: Session) -> None:
        """Crea los usuarios iniciales con passwords hasheados"""
        # Password por defecto para todos los usuarios de ejemplo
        default_password = "password"
        password_hash = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        users_data = [
            {
                'id': 'admin',
                'name': 'Administrador KRONOS',
                'email': 'admin@example.com',
                'role_id': '1',
                'status': 'active',
                'avatar': 'https://picsum.photos/seed/admin/100/100'
            },
            {
                'id': 'u1',
                'name': 'Alice Johnson',
                'email': 'alice.j@example.com',
                'role_id': '1',
                'status': 'active',
                'avatar': 'https://picsum.photos/seed/alice/100/100'
            },
            {
                'id': 'u2',
                'name': 'Bob Williams',
                'email': 'bob.w@example.com',
                'role_id': '2',
                'status': 'active',
                'avatar': 'https://picsum.photos/seed/bob/100/100'
            },
            {
                'id': 'u3',
                'name': 'Charlie Brown',
                'email': 'charlie.b@example.com',
                'role_id': '3',
                'status': 'inactive',
                'avatar': 'https://picsum.photos/seed/charlie/100/100'
            },
            {
                'id': 'u4',
                'name': 'Diana Prince',
                'email': 'diana.p@example.com',
                'role_id': '2',
                'status': 'active',
                'avatar': 'https://picsum.photos/seed/diana/100/100'
            },
            {
                'id': 'u5',
                'name': 'Ethan Hunt',
                'email': 'ethan.h@example.com',
                'role_id': '3',
                'status': 'active',
                'avatar': 'https://picsum.photos/seed/ethan/100/100'
            }
        ]
        
        for user_data in users_data:
            user = User(
                id=user_data['id'],
                name=user_data['name'],
                email=user_data['email'],
                password_hash=password_hash,
                role_id=user_data['role_id'],
                status=user_data['status'],
                avatar=user_data['avatar']
            )
            session.add(user)
    
    def _create_initial_missions(self, session: Session) -> None:
        """Crea las misiones iniciales"""
        missions_data = [
            {
                'id': 'm1',
                'code': 'PX-001',
                'name': 'Proyecto Fénix',
                'description': 'Investigar anomalías de rayos cósmicos en la galaxia de Andrómeda.',
                'status': 'En Progreso',
                'start_date': '2023-01-15',
                'end_date': '2024-12-31',
                'created_by': 'u1'
            },
            {
                'id': 'm2',
                'code': 'DD-002',
                'name': 'Operación Inmersión Profunda',
                'description': 'Explorar la Fosa de las Marianas en busca de nuevas especies biológicas.',
                'status': 'Completada',
                'start_date': '2022-05-20',
                'end_date': '2023-05-19',
                'created_by': 'u1'
            },
            {
                'id': 'm3',
                'code': 'AS-003',
                'name': 'Centinela del Ártico',
                'description': 'Monitorear las tasas de derretimiento de los casquetes polares y el impacto climático.',
                'status': 'Planificación',
                'start_date': '2025-02-01',
                'end_date': '2026-02-01',
                'created_by': 'u2'
            },
            {
                'id': 'm4',
                'code': 'PC-004',
                'name': 'Proyecto Quimera',
                'description': 'Investigación genética de extremófilos para la colonización espacial.',
                'status': 'Cancelada',
                'start_date': '2023-08-01',
                'end_date': '2024-08-01',
                'created_by': 'u4'
            }
        ]
        
        for mission_data in missions_data:
            mission = Mission(**mission_data)
            session.add(mission)
    
    def _verify_database_integrity(self) -> None:
        """Verifica la integridad final de la base de datos"""
        try:
            session = self.SessionLocal()
            try:
                # Verificar que existan las tablas principales con datos
                role_count = session.query(Role).count()
                user_count = session.query(User).count()
                mission_count = session.query(Mission).count()
                
                if role_count == 0 or user_count == 0:
                    # Esto no debería pasar después de la auto-reparación
                    error_msg = f"CRÍTICO: Base de datos sin datos esenciales después de reparación (roles: {role_count}, usuarios: {user_count})"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                
                logger.info(f"✓ Integridad de base de datos verificada exitosamente:")
                logger.info(f"  - {role_count} roles disponibles")
                logger.info(f"  - {user_count} usuarios registrados")
                logger.info(f"  - {mission_count} misiones de ejemplo")
                logger.info("Sistema listo para operación")
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"ERROR CRÍTICO en verificación final de integridad: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """Context manager para obtener una sesión de base de datos"""
        if not self._initialized:
            raise ValueError("DatabaseManager no ha sido inicializado")
        
        session = self.SessionLocal()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Error en transacción de base de datos: {e}")
            raise
        finally:
            session.close()
    
    def get_engine(self) -> Engine:
        """Retorna el engine de SQLAlchemy"""
        if not self._initialized:
            raise ValueError("DatabaseManager no ha sido inicializado")
        return self.engine
    
    def execute_sql(self, sql: str, params: Optional[dict] = None) -> None:
        """Ejecuta SQL raw de manera segura"""
        try:
            with self.get_session() as session:
                session.execute(text(sql), params or {})
                session.commit()
        except Exception as e:
            logger.error(f"Error ejecutando SQL: {e}")
            raise
    
    def backup_database(self, backup_path: str) -> None:
        """Crea un backup de la base de datos"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Backup creado: {backup_path}")
        except Exception as e:
            logger.error(f"Error creando backup: {e}")
            raise
    
    def vacuum_database(self) -> None:
        """Optimiza la base de datos"""
        try:
            self.execute_sql("VACUUM")
            self.execute_sql("ANALYZE")
            logger.info("Base de datos optimizada")
        except Exception as e:
            logger.error(f"Error optimizando base de datos: {e}")
            raise
    
    def close(self) -> None:
        """Cierra las conexiones de base de datos"""
        if self.engine:
            self.engine.dispose()
            self._initialized = False
            logger.info("Conexiones de base de datos cerradas")


# ============================================================================
# INSTANCIA GLOBAL Y FUNCIONES DE UTILIDAD
# ============================================================================

# Instancia global del gestor de base de datos
db_manager = DatabaseManager()


def init_database(db_path: str = DEFAULT_DB_PATH, force_recreate: bool = False) -> None:
    """Inicializa la base de datos global"""
    global db_manager
    if db_path != DEFAULT_DB_PATH:
        db_manager = DatabaseManager(db_path)
    db_manager.initialize(force_recreate=force_recreate)


def get_db_session():
    """Generador para obtener sesiones de base de datos (para dependency injection)"""
    with db_manager.get_session() as session:
        yield session


def get_database_manager() -> DatabaseManager:
    """Retorna la instancia del gestor de base de datos"""
    return db_manager


# ============================================================================
# FUNCIONES DE UTILIDAD PARA EEL
# ============================================================================

def verify_user_credentials(email: str, password: str) -> bool:
    """
    Verifica las credenciales de un usuario
    
    Args:
        email: Email del usuario
        password: Contraseña en texto plano
        
    Returns:
        True si las credenciales son válidas
    """
    try:
        with db_manager.get_session() as session:
            user = session.query(User).filter(User.email == email, User.status == 'active').first()
            
            if not user:
                return False
            
            # Verificar password con bcrypt
            # NOTA: password_hash ya es un string, pero bcrypt.checkpw necesita bytes
            return bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8'))
            
    except Exception as e:
        logger.error(f"Error verificando credenciales: {e}")
        return False


def hash_password(password: str) -> str:
    """Hashea una contraseña usando bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


@contextmanager  
def get_db_connection():
    """
    Context manager para obtener conexión SQLite directa para operator services
    
    Esta función proporciona una conexión SQLite simple para uso en los servicios
    de operadores que necesitan acceso directo a la base de datos.
    """
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'kronos.db')
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()