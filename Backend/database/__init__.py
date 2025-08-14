"""
KRONOS Database Module
===============================================================================
Módulo de base de datos del backend de KRONOS.
Expone modelos, conexión y funciones de gestión de BD.
"""

from database.connection import (
    init_database,
    get_database_manager,
    get_db_session,
    verify_user_credentials,
    hash_password,
    DatabaseManager
)

from database.models import (
    Base,
    BaseModel,
    Role,
    User,
    Mission,
    CellularData,
    TargetRecord,
    get_all_models,
    create_all_tables,
    drop_all_tables
)

__all__ = [
    # Connection
    'init_database',
    'get_database_manager',
    'get_db_session',
    'verify_user_credentials',
    'hash_password',
    'DatabaseManager',
    
    # Models
    'Base',
    'BaseModel',
    'Role',
    'User',
    'Mission',
    'CellularData',
    'TargetRecord',
    'get_all_models',
    'create_all_tables',
    'drop_all_tables'
]