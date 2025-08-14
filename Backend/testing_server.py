"""
KRONOS Testing Server - Simplified for Playwright Testing
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any

# Configurar path para imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

import eel

# Importar servicios
from database.connection import init_database
from services.auth_service import get_auth_service
from services.user_service import get_user_service
from services.role_service import get_role_service
from services.mission_service import get_mission_service
from services.analysis_service import get_analysis_service
from services.operator_data_service import upload_operator_data, get_operator_sheets

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

logger = logging.getLogger(__name__)

def setup_database():
    """Inicializar base de datos"""
    try:
        init_database()
        logger.info("Base de datos inicializada exitosamente")
        return True
    except Exception as e:
        logger.error(f"Error inicializando base de datos: {str(e)}")
        return False

def setup_eel_functions():
    """Configurar funciones Eel"""
    
    # === AUTHENTICATION ===
    @eel.expose
    def login(email: str, password: str) -> Dict[str, Any]:
        try:
            auth_service = get_auth_service()
            result = auth_service.authenticate(email, password)
            logger.info(f"Login exitoso para: {email}")
            return result
        except Exception as e:
            logger.error(f"Error en login: {str(e)}")
            return {'success': False, 'error': str(e)}

    # === USERS ===
    @eel.expose
    def get_users() -> Dict[str, Any]:
        try:
            user_service = get_user_service()
            users = user_service.get_all_users()
            logger.info(f"Recuperados {len(users)} usuarios")
            return {'success': True, 'data': users}
        except Exception as e:
            logger.error(f"Error obteniendo usuarios: {str(e)}")
            return {'success': False, 'error': str(e)}

    # === ROLES ===
    @eel.expose
    def get_roles() -> Dict[str, Any]:
        try:
            role_service = get_role_service()
            roles = role_service.get_all_roles()
            logger.info(f"Recuperados {len(roles)} roles")
            return {'success': True, 'data': roles}
        except Exception as e:
            logger.error(f"Error obteniendo roles: {str(e)}")
            return {'success': False, 'error': str(e)}

    # === MISSIONS ===
    @eel.expose
    def get_missions() -> Dict[str, Any]:
        try:
            mission_service = get_mission_service()
            missions = mission_service.get_all_missions()
            logger.info(f"Recuperadas {len(missions)} misiones")
            return {'success': True, 'data': missions}
        except Exception as e:
            logger.error(f"Error obteniendo misiones: {str(e)}")
            return {'success': False, 'error': str(e)}

    # === OPERATOR DATA ===
    # Las funciones de operator_data_service ya están definidas y se exponen automáticamente

    logger.info("Funciones Eel configuradas exitosamente")

if __name__ == "__main__":
    logger.info("=== INICIANDO KRONOS TESTING SERVER ===")
    
    # Configurar base de datos
    if not setup_database():
        sys.exit(1)
    
    # Configurar funciones Eel
    setup_eel_functions()
    
    # Inicializar Eel
    frontend_path = current_dir.parent / "Frontend" / "dist"
    eel.init(str(frontend_path))
    logger.info(f"Eel inicializado con path: {frontend_path}")
    
    logger.info("=== TESTING SERVER LISTO ===")
    
    # Iniciar servidor
    try:
        eel.start('index.html', size=(1200, 800), port=8080, block=True)
    except Exception as e:
        logger.error(f"Error iniciando servidor: {str(e)}")
        sys.exit(1)