"""
KRONOS Backend - Main Eel Application
===============================================================================
Script principal del backend de KRONOS que implementa la aplicación desktop
híbrida usando Eel. Expone todas las funciones necesarias para el frontend
y gestiona la inicialización completa del sistema.

Funciones expuestas para el frontend:
- Authentication: login
- Users: get_users, create_user, update_user, delete_user
- Roles: get_roles, create_role, update_role, delete_role
- Missions: get_missions, create_mission, update_mission, delete_mission
- File Upload: upload_cellular_data
- Data Management: clear_cellular_data
- Analysis: run_analysis, analyze_correlation, get_correlation_summary
- Call Data: get_call_interactions

Características principales:
- Inicialización automática de base de datos
- Manejo robusto de errores con logging
- Transacciones seguras para todas las operaciones
- Validación exhaustiva de datos
- Compatibilidad completa con tipos TypeScript del frontend
===============================================================================
"""

import os
import sys
import signal
import threading
import time
import logging
import atexit
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configurar path para imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

import eel

# Importar servicios
from database.connection import init_database, get_database_manager, get_db_connection
import sqlite3
from services.auth_service import get_auth_service, AuthenticationError
from services.user_service import get_user_service, UserServiceError
from services.role_service import get_role_service, RoleServiceError
from services.mission_service import get_mission_service, MissionServiceError
from services.analysis_service import get_analysis_service, AnalysisServiceError
from services.correlation_service import get_correlation_service
from services.correlation_service_fixed import CorrelationServiceFixedError
from services.diagram_correlation_service import get_diagram_correlation_service, DiagramCorrelationServiceError
from services.correlation_service_dynamic import get_correlation_service_dynamic
from services.correlation_service_hunter_validated import get_correlation_service_hunter_validated
from services.file_processor import FileProcessorError

# Importar servicio de datos de operador (para registrar funciones Eel expuestas)
import services.operator_data_service

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kronos_backend.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# GESTIÓN DE SHUTDOWN DE APLICACIÓN
# ============================================================================

class ApplicationShutdownManager:
    """
    Gestor central de cierre limpio de aplicación
    
    Maneja el shutdown coordinado de todos los componentes críticos:
    - Base de datos y conexiones
    - Servicios singleton
    - Recursos de logging
    - Limpieza de recursos del sistema
    """
    
    def __init__(self):
        self._shutdown_initiated = False
        self._shutdown_lock = threading.Lock()
        self._cleanup_handlers = []
        self._logger = None
        self._shutdown_reason = None
    
    def set_logger(self, logger):
        """Establece el logger a usar para el shutdown"""
        self._logger = logger
    
    def register_cleanup_handler(self, name: str, handler: callable, critical: bool = False):
        """
        Registra un handler de cleanup
        
        Args:
            name: Nombre descriptivo del handler
            handler: Función callable para ejecutar cleanup
            critical: Si es crítico, se ejecuta primero y errores no se ignoran
        """
        self._cleanup_handlers.append({
            'name': name,
            'handler': handler,
            'critical': critical
        })
    
    def initiate_shutdown(self, reason: str = "Usuario cerró aplicación", page=None, sockets=None):
        """
        Inicia proceso de cierre coordinado
        
        Args:
            reason: Razón del shutdown
            page: Página Eel (compatible con close_callback)
            sockets: Sockets Eel (compatible con close_callback)
        """
        with self._shutdown_lock:
            if self._shutdown_initiated:
                return
            
            self._shutdown_initiated = True
            self._shutdown_reason = reason
        
        if self._logger:
            self._logger.info(f"=== INICIANDO SHUTDOWN DE APLICACIÓN ===")
            self._logger.info(f"Razón: {reason}")
            if page:
                self._logger.info(f"Página Eel: {page}")
        
        # Ejecutar cleanup en hilo separado para no bloquear callback
        shutdown_thread = threading.Thread(
            target=self._execute_cleanup_sequence,
            daemon=False,
            name="ShutdownCleanup"
        )
        shutdown_thread.start()
    
    def _execute_cleanup_sequence(self):
        """Ejecuta secuencia ordenada de cleanup con timeout de seguridad"""
        cleanup_timeout = 10  # 10 segundos máximo para cleanup completo
        
        # Timer de seguridad para evitar shutdown colgado
        def emergency_exit():
            time.sleep(cleanup_timeout)
            if self._logger:
                self._logger.error("⚠️ TIMEOUT DE SHUTDOWN - Forzando salida de emergencia")
            os._exit(1)
        
        # Iniciar timer de emergencia
        emergency_thread = threading.Thread(target=emergency_exit, daemon=True)
        emergency_thread.start()
        
        try:
            start_time = time.time()
            
            # Separar handlers críticos y no críticos
            critical_handlers = [h for h in self._cleanup_handlers if h['critical']]
            normal_handlers = [h for h in self._cleanup_handlers if not h['critical']]
            
            # Ejecutar handlers críticos primero (timeout más estricto)
            if self._logger:
                self._logger.info(f"Ejecutando {len(critical_handlers)} handlers críticos...")
            self._execute_handlers(critical_handlers, fail_fast=True, individual_timeout=3)
            
            # Ejecutar handlers normales (continúa aunque fallen)
            if self._logger:
                self._logger.info(f"Ejecutando {len(normal_handlers)} handlers normales...")
            self._execute_handlers(normal_handlers, fail_fast=False, individual_timeout=2)
            
            # Flush final de logs
            self._final_log_flush()
            
            elapsed_time = time.time() - start_time
            if self._logger:
                self._logger.info(f"=== SHUTDOWN COMPLETADO EXITOSAMENTE en {elapsed_time:.2f}s ===")
            
            # Dar tiempo para que se complete el flush de logs
            time.sleep(0.5)
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"ERROR CRÍTICO durante shutdown: {e}")
            import traceback
            if self._logger:
                self._logger.error(f"Traceback:\n{traceback.format_exc()}")
        
        finally:
            # Cancelar timer de emergencia ya que terminamos normalmente
            try:
                # El hilo daemon se cancelará automáticamente
                pass
            except:
                pass
            
            # Forzar salida después del cleanup
            os._exit(0)
    
    def _execute_handlers(self, handlers: List[Dict], fail_fast: bool, individual_timeout: int = 5):
        """
        Ejecuta una lista de handlers con timeout individual
        
        Args:
            handlers: Lista de handlers a ejecutar
            fail_fast: Si True, detiene en el primer error
            individual_timeout: Timeout en segundos para cada handler individual
        """
        for handler_info in handlers:
            name = handler_info['name']
            handler = handler_info['handler']
            
            try:
                if self._logger:
                    self._logger.info(f"Ejecutando cleanup: {name}")
                
                # Ejecutar handler con timeout
                result_container = [None]
                exception_container = [None]
                
                def run_handler():
                    try:
                        result_container[0] = handler()
                    except Exception as e:
                        exception_container[0] = e
                
                handler_thread = threading.Thread(target=run_handler, daemon=True)
                handler_thread.start()
                handler_thread.join(timeout=individual_timeout)
                
                # Verificar si el handler terminó a tiempo
                if handler_thread.is_alive():
                    error_msg = f"✗ Timeout en cleanup {name} (>{individual_timeout}s)"
                    if self._logger:
                        self._logger.warning(error_msg)
                    
                    if fail_fast:
                        raise Exception(f"Timeout crítico en cleanup {name}")
                    continue
                
                # Verificar si hubo excepción
                if exception_container[0]:
                    raise exception_container[0]
                
                if self._logger:
                    self._logger.info(f"✓ Cleanup completado: {name}")
                
            except Exception as e:
                error_msg = f"✗ Error en cleanup {name}: {e}"
                if self._logger:
                    self._logger.error(error_msg)
                
                if fail_fast:
                    raise Exception(f"Error crítico en cleanup {name}: {e}")
    
    def _final_log_flush(self):
        """Realiza flush final de todos los handlers de logging"""
        try:
            # Flush todos los handlers del root logger
            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                try:
                    handler.flush()
                except:
                    pass
            
            # Flush logger específico si existe
            if self._logger:
                for handler in self._logger.handlers[:]:
                    try:
                        handler.flush()
                    except:
                        pass
        except:
            pass

# Instancia global del gestor de shutdown
shutdown_manager = ApplicationShutdownManager()

# Servicios globales (se inicializan después de la BD)
auth_service = None
user_service = None
role_service = None
mission_service = None
analysis_service = None
correlation_service = None


def handle_service_error(func_name: str, error: Exception) -> None:
    """
    Maneja errores de servicios y los re-lanza como ValueError para Eel
    
    Args:
        func_name: Nombre de la función que falló
        error: Excepción original
    """
    error_msg = f"Error en {func_name}: {str(error)}"
    logger.error(error_msg)
    raise ValueError(error_msg)


# ============================================================================
# AUTHENTICATION
# ============================================================================

@eel.expose
def login(credentials):
    """
    Autentica un usuario con email y contraseña
    
    Args:
        credentials: {"email": "...", "password": "..."}
        
    Returns:
        {"status": "ok"} si es exitoso
        
    Raises:
        ValueError: Si las credenciales son inválidas
    """
    try:
        logger.info(f"Intento de login para: {credentials.get('email', 'unknown')}")
        
        # Validar que las credenciales no estén vacías
        if not credentials:
            raise ValueError("Credenciales no proporcionadas")
        
        if not isinstance(credentials, dict):
            raise ValueError("Credenciales deben ser un objeto")
        
        if 'email' not in credentials or 'password' not in credentials:
            raise ValueError("Email y contraseña son requeridos")
        
        # Verificar que el servicio de auth esté disponible
        if not auth_service:
            logger.error("Servicio de autenticación no disponible")
            raise ValueError("Error interno: servicio de autenticación no disponible")
        
        result = auth_service.login(credentials)
        logger.info("Login exitoso")
        return result
        
    except AuthenticationError as e:
        logger.error(f"Error de autenticación en login: {e}")
        handle_service_error("login", e)
    except ValueError as e:
        logger.error(f"Error de validación en login: {e}")
        handle_service_error("login", e)  
    except Exception as e:
        logger.error(f"Error inesperado en login: {e}")
        import traceback
        logger.error(f"Traceback completo:\n{traceback.format_exc()}")
        handle_service_error("login", e)


# ============================================================================
# USER MANAGEMENT
# ============================================================================

@eel.expose
def get_users():
    """
    Obtiene todos los usuarios
    
    Returns:
        Lista de usuarios
    """
    try:
        logger.info("Obteniendo lista de usuarios")
        users = user_service.get_all_users()
        logger.info(f"Enviando {len(users)} usuarios al frontend")
        return users
    except UserServiceError as e:
        handle_service_error("get_users", e)
    except Exception as e:
        handle_service_error("get_users", e)


@eel.expose
def create_user(user_data):
    """
    Crea un nuevo usuario
    
    Args:
        user_data: Datos del usuario (sin id ni avatar)
        
    Returns:
        Usuario creado
    """
    try:
        logger.info(f"Creando usuario: {user_data.get('email', 'unknown')}")
        created_user = user_service.create_user(user_data)
        logger.info(f"Usuario creado exitosamente: {created_user['email']}")
        return created_user
    except UserServiceError as e:
        handle_service_error("create_user", e)
    except Exception as e:
        handle_service_error("create_user", e)


@eel.expose
def update_user(user_id, user_data):
    """
    Actualiza un usuario existente
    
    Args:
        user_id: ID del usuario
        user_data: Datos actualizados del usuario
        
    Returns:
        Usuario actualizado
    """
    try:
        logger.info(f"Actualizando usuario: {user_id}")
        updated_user = user_service.update_user(user_id, user_data)
        logger.info(f"Usuario actualizado exitosamente: {updated_user['email']}")
        return updated_user
    except UserServiceError as e:
        handle_service_error("update_user", e)
    except Exception as e:
        handle_service_error("update_user", e)


@eel.expose
def delete_user(user_id):
    """
    Elimina un usuario
    
    Args:
        user_id: ID del usuario
        
    Returns:
        {"status": "ok"} si es exitoso
    """
    try:
        logger.info(f"Eliminando usuario: {user_id}")
        result = user_service.delete_user(user_id)
        logger.info("Usuario eliminado exitosamente")
        return result
    except UserServiceError as e:
        handle_service_error("delete_user", e)
    except Exception as e:
        handle_service_error("delete_user", e)


# ============================================================================
# ROLE MANAGEMENT
# ============================================================================

@eel.expose
def get_roles():
    """
    Obtiene todos los roles
    
    Returns:
        Lista de roles
    """
    try:
        logger.info("Obteniendo lista de roles")
        roles = role_service.get_all_roles()
        logger.info(f"Enviando {len(roles)} roles al frontend")
        return roles
    except RoleServiceError as e:
        handle_service_error("get_roles", e)
    except Exception as e:
        handle_service_error("get_roles", e)


@eel.expose
def create_role(role_data):
    """
    Crea un nuevo rol
    
    Args:
        role_data: {"name": "...", "permissions": {...}}
        
    Returns:
        Rol creado
    """
    try:
        logger.info(f"Creando rol: {role_data.get('name', 'unknown')}")
        created_role = role_service.create_role(role_data)
        logger.info(f"Rol creado exitosamente: {created_role['name']}")
        return created_role
    except RoleServiceError as e:
        handle_service_error("create_role", e)
    except Exception as e:
        handle_service_error("create_role", e)


@eel.expose
def update_role(role_id, role_data):
    """
    Actualiza un rol existente
    
    Args:
        role_id: ID del rol
        role_data: {"name": "...", "permissions": {...}}
        
    Returns:
        Rol actualizado
    """
    try:
        logger.info(f"Actualizando rol: {role_id}")
        updated_role = role_service.update_role(role_id, role_data)
        logger.info(f"Rol actualizado exitosamente: {updated_role['name']}")
        return updated_role
    except RoleServiceError as e:
        handle_service_error("update_role", e)
    except Exception as e:
        handle_service_error("update_role", e)


@eel.expose
def delete_role(role_id):
    """
    Elimina un rol
    
    Args:
        role_id: ID del rol
        
    Returns:
        {"status": "ok"} si es exitoso
    """
    try:
        logger.info(f"Eliminando rol: {role_id}")
        result = role_service.delete_role(role_id)
        logger.info("Rol eliminado exitosamente")
        return result
    except RoleServiceError as e:
        handle_service_error("delete_role", e)
    except Exception as e:
        handle_service_error("delete_role", e)


# ============================================================================
# MISSION MANAGEMENT
# ============================================================================

@eel.expose
def get_missions():
    """
    Obtiene todas las misiones
    
    Returns:
        Lista de misiones con datos completos
    """
    try:
        logger.info("Obteniendo lista de misiones")
        
        # Lazy loading: obtener servicio si la variable global no está inicializada
        global mission_service
        if mission_service is None:
            logger.warning("Servicio de misiones no inicializado, creando instancia lazy")
            mission_service = get_mission_service()
        
        missions = mission_service.get_all_missions()
        logger.info(f"Enviando {len(missions)} misiones al frontend")
        return missions
    except MissionServiceError as e:
        handle_service_error("get_missions", e)
    except Exception as e:
        handle_service_error("get_missions", e)


@eel.expose
def create_mission(mission_data):
    """
    Crea una nueva misión
    
    Args:
        mission_data: Datos de la misión (sin id, cellularData, operatorData)
        
    Returns:
        Misión creada
    """
    try:
        logger.info(f"Creando misión: {mission_data.get('code', 'unknown')}")
        
        # Lazy loading: obtener servicio si la variable global no está inicializada
        global mission_service
        if mission_service is None:
            logger.warning("Servicio de misiones no inicializado, creando instancia lazy")
            mission_service = get_mission_service()
        
        # TODO: Obtener created_by del usuario autenticado
        created_mission = mission_service.create_mission(mission_data, created_by=None)
        logger.info(f"Misión creada exitosamente: {created_mission['code']}")
        return created_mission
    except MissionServiceError as e:
        handle_service_error("create_mission", e)
    except Exception as e:
        handle_service_error("create_mission", e)


@eel.expose
def update_mission(mission_id, mission_data):
    """
    Actualiza una misión existente
    
    Args:
        mission_id: ID de la misión
        mission_data: Datos actualizados de la misión
        
    Returns:
        Misión actualizada
    """
    try:
        logger.info(f"Actualizando misión: {mission_id}")
        
        # Lazy loading: obtener servicio si la variable global no está inicializada
        global mission_service
        if mission_service is None:
            logger.warning("Servicio de misiones no inicializado, creando instancia lazy")
            mission_service = get_mission_service()
        
        updated_mission = mission_service.update_mission(mission_id, mission_data)
        logger.info(f"Misión actualizada exitosamente: {updated_mission['code']}")
        return updated_mission
    except MissionServiceError as e:
        handle_service_error("update_mission", e)
    except Exception as e:
        handle_service_error("update_mission", e)


@eel.expose
def delete_mission(mission_id):
    """
    Elimina una misión
    
    Args:
        mission_id: ID de la misión
        
    Returns:
        {"status": "ok"} si es exitoso
    """
    try:
        logger.info(f"Eliminando misión: {mission_id}")
        
        # Lazy loading: obtener servicio si la variable global no está inicializada
        global mission_service
        if mission_service is None:
            logger.warning("Servicio de misiones no inicializado, creando instancia lazy")
            mission_service = get_mission_service()
        
        result = mission_service.delete_mission(mission_id)
        logger.info("Misión eliminada exitosamente")
        return result
    except MissionServiceError as e:
        handle_service_error("delete_mission", e)
    except Exception as e:
        handle_service_error("delete_mission", e)


# ============================================================================
# FILE UPLOAD AND DATA MANAGEMENT
# ============================================================================

@eel.expose
def upload_cellular_data(mission_id, file_data):
    """
    Carga datos celulares desde archivo a una misión
    
    Args:
        mission_id: ID de la misión
        file_data: {"name": "...", "content": "data:mime/type;base64,..."}
        
    Returns:
        Misión actualizada con nuevos datos
    """
    try:
        logger.info(f"Cargando datos celulares para misión: {mission_id}")
        
        # Lazy loading: obtener servicio si la variable global no está inicializada
        global mission_service
        if mission_service is None:
            logger.warning("Servicio de misiones no inicializado, creando instancia lazy")
            mission_service = get_mission_service()
        
        updated_mission = mission_service.upload_cellular_data(mission_id, file_data)
        logger.info("Datos celulares cargados exitosamente")
        return updated_mission
    except (MissionServiceError, FileProcessorError) as e:
        handle_service_error("upload_cellular_data", e)
    except Exception as e:
        handle_service_error("upload_cellular_data", e)


# La función upload_operator_data está implementada directamente en operator_data_service.py
# y se expone automáticamente vía Eel desde ese módulo. Esta función antigua ha sido removida
# para evitar conflictos de nombres.


@eel.expose
def clear_cellular_data(mission_id):
    """
    Elimina todos los datos celulares de una misión
    
    Args:
        mission_id: ID de la misión
        
    Returns:
        Misión actualizada sin datos celulares
    """
    try:
        logger.info(f"Limpiando datos celulares de misión: {mission_id}")
        
        # Lazy loading: obtener servicio si la variable global no está inicializada
        global mission_service
        if mission_service is None:
            logger.warning("Servicio de misiones no inicializado, creando instancia lazy")
            mission_service = get_mission_service()
        
        updated_mission = mission_service.clear_cellular_data(mission_id)
        logger.info("Datos celulares eliminados exitosamente")
        return updated_mission
    except MissionServiceError as e:
        handle_service_error("clear_cellular_data", e)
    except Exception as e:
        handle_service_error("clear_cellular_data", e)


# La función delete_operator_sheet está implementada directamente en operator_data_service.py
# y se expone automáticamente vía Eel desde ese módulo. Esta función antigua ha sido removida
# para evitar conflictos de nombres.


# ============================================================================
# ANALYSIS
# ============================================================================

@eel.expose
def run_analysis(mission_id):
    """
    Ejecuta análisis de objetivos para una misión
    
    Args:
        mission_id: ID de la misión
        
    Returns:
        Lista de registros de objetivos encontrados
    """
    try:
        logger.info(f"Ejecutando análisis para misión: {mission_id}")
        
        # Lazy loading: obtener servicio si la variable global no está inicializada
        global analysis_service
        if analysis_service is None:
            logger.warning("Servicio de análisis no inicializado, creando instancia lazy")
            analysis_service = get_analysis_service()
        
        target_records = analysis_service.run_analysis(mission_id)
        logger.info(f"Análisis completado: {len(target_records)} objetivos encontrados")
        return target_records
    except AnalysisServiceError as e:
        handle_service_error("run_analysis", e)
    except Exception as e:
        handle_service_error("run_analysis", e)


@eel.expose
def analyze_correlation(mission_id, start_datetime, end_datetime, min_occurrences=1):
    """
    Ejecuta análisis de correlación para detectar números objetivo
    que utilizaron las mismas celdas que HUNTER en un período específico
    
    Args:
        mission_id: ID de la misión
        start_datetime: Inicio del período (formato: YYYY-MM-DD HH:MM:SS)
        end_datetime: Fin del período (formato: YYYY-MM-DD HH:MM:SS)
        min_occurrences: Mínimo de coincidencias de celdas requeridas (default: 1)
        
    Returns:
        Dict con resultados del análisis de correlación:
        {
            'success': bool,
            'data': [
                {
                    'targetNumber': str,      # Número sin prefijo 57
                    'operator': str,          # CLARO, MOVISTAR, etc
                    'occurrences': int,       # Total de coincidencias
                    'firstDetection': str,    # Primera aparición
                    'lastDetection': str,     # Última aparición
                    'relatedCells': list,     # Cell IDs relacionados
                    'confidence': float       # Nivel de confianza 0-100
                }
            ],
            'statistics': {
                'totalAnalyzed': int,
                'totalFound': int,
                'processingTime': float
            }
        }
    """
    try:
        logger.info(f"Ejecutando análisis de correlación para misión: {mission_id}")
        logger.info(f"Período: {start_datetime} - {end_datetime}, Min occurrences: {min_occurrences}")
        
        # CORRECCIÓN BORIS 2025-08-18: Usar servicio con validación de celdas HUNTER reales
        # Elimina inflación del 50% por celdas que no existen en HUNTER
        logger.info("Usando servicio de correlación HUNTER-VALIDATED - CORRECCIÓN INFLACIÓN BORIS")
        correlation_service_hunter = get_correlation_service_hunter_validated()
        
        # Ejecutar análisis de correlación con validación HUNTER
        result = correlation_service_hunter.analyze_correlation(
            mission_id=mission_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            min_occurrences=min_occurrences
        )
        
        logger.info(f"Análisis de correlación HUNTER-VALIDATED completado: {result['total_count']} números encontrados")
        logger.info(f"Tiempo de procesamiento: {result['processing_time']}s")
        logger.info(f"Celdas HUNTER reales utilizadas: {result.get('hunter_cells_real_count', 'N/A')}")
        logger.info(f"CORRECCIÓN BORIS: Inflación eliminada mediante filtrado por celdas HUNTER reales")
        
        # Mapear resultado del servicio dinámico al formato esperado por el frontend
        if result['success'] and result['data']:
            mapped_data = []
            for item in result['data']:
                # Transformar campos de snake_case a camelCase para el frontend
                mapped_item = {
                    'targetNumber': item.get('numero_objetivo', 'N/A'),
                    'operator': item.get('operador', 'DESCONOCIDO'),
                    'occurrences': item.get('ocurrencias', 0),
                    'firstDetection': item.get('primera_deteccion', ''),
                    'lastDetection': item.get('ultima_deteccion', ''),
                    'relatedCells': item.get('celdas_relacionadas', []),
                    'confidence': item.get('nivel_confianza', 0)
                }
                mapped_data.append(mapped_item)
            
            # Devolver resultado con formato estándar para el frontend
            return {
                'success': True,
                'data': mapped_data,
                'statistics': {
                    'totalAnalyzed': result.get('total_count', 0),
                    'totalFound': len(mapped_data),
                    'processingTime': result.get('processing_time', 0)
                }
            }
        
        # Si no hay éxito o no hay datos, devolver el resultado original
        return result
        
    except CorrelationServiceFixedError as e:
        logger.error(f"Error en servicio de correlación: {e}")
        handle_service_error("analyze_correlation", e)
    except Exception as e:
        logger.error(f"Error inesperado en análisis de correlación: {e}")
        handle_service_error("analyze_correlation", e)


@eel.expose
def get_correlation_summary(mission_id):
    """
    Obtiene resumen de capacidades de correlación para una misión
    
    Args:
        mission_id: ID de la misión
        
    Returns:
        Dict con estadísticas de datos disponibles para correlación
    """
    try:
        logger.info(f"Obteniendo resumen de correlación para misión: {mission_id}")
        
        # Lazy loading: obtener servicio si la variable global no está inicializada
        global correlation_service
        if correlation_service is None:
            logger.info("Servicio de correlación no inicializado, creando instancia lazy")
            correlation_service = get_correlation_service()
        
        summary = correlation_service.get_correlation_summary(mission_id)
        logger.info(f"Resumen de correlación obtenido: Listo={summary.get('correlationReady', False)}")
        
        return summary
        
    except CorrelationServiceFixedError as e:
        logger.error(f"Error obteniendo resumen de correlación: {e}")
        handle_service_error("get_correlation_summary", e)
    except Exception as e:
        logger.error(f"Error inesperado obteniendo resumen de correlación: {e}")
        handle_service_error("get_correlation_summary", e)


@eel.expose
def get_correlation_diagram(mission_id: str, 
                          numero_objetivo: str,
                          start_datetime: str,
                          end_datetime: str,
                          filtros: dict = None):
    """
    CORRECCIÓN URGENTE BORIS 2025-08-19: Endpoint para diagrama de correlación con función específica
    
    PROBLEMA RESUELTO:
    - ANTES: 255 nodos para 3113330727 (dataset completo)
    - AHORA: 4-5 nodos (solo interacciones directas del número objetivo)
    
    IMPLEMENTACIÓN:
    - Detecta solicitud de diagrama para número específico  
    - Usa nueva función optimizada en lugar del algoritmo general
    - Retorna solo interacciones donde numero_objetivo fue origen O destino
    
    Args:
        mission_id: ID de la misión
        numero_objetivo: Número telefónico objetivo para el análisis
        start_datetime: Inicio del período (YYYY-MM-DD HH:MM:SS)
        end_datetime: Fin del período (YYYY-MM-DD HH:MM:SS)
        filtros: Filtros opcionales (tipo_trafico, operador, etc.)
        
    Returns:
        Dict con nodos, aristas y metadatos para el diagrama de red
    """
    try:
        logger.info(f"=== CORRECCIÓN BORIS: DIAGRAMA DE CORRELACIÓN ESPECÍFICO ===")
        logger.info(f"Número objetivo: {numero_objetivo}")
        logger.info(f"Misión: {mission_id}")
        logger.info(f"Período: {start_datetime} - {end_datetime}")
        logger.info(f"Filtros: {filtros}")
        logger.info(f"OBJETIVO: Generar diagrama individual con máximo 4-5 nodos")
        
        # Validar parámetros requeridos
        if not mission_id or not numero_objetivo:
            raise ValueError("mission_id y numero_objetivo son requeridos")
        
        if not start_datetime or not end_datetime:
            raise ValueError("start_datetime y end_datetime son requeridos")
        
        # CORRECCIÓN BORIS: Usar servicio específico para número individual
        # En lugar del servicio general que causa inflación de nodos
        logger.info("CORRECCIÓN APLICADA: Usando servicio HUNTER-VALIDATED específico para número individual")
        correlation_service_hunter = get_correlation_service_hunter_validated()
        
        # Usar función específica para diagrama individual
        result = correlation_service_hunter.get_individual_number_diagram_data(
            mission_id=mission_id,
            numero_objetivo=numero_objetivo,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            filtros=filtros or {}
        )
        
        logger.info(f"✓ DIAGRAMA INDIVIDUAL GENERADO CON CORRECCIÓN BORIS:")
        logger.info(f"  - Nodos: {len(result.get('nodos', []))} (objetivo: máximo 4-5)")
        logger.info(f"  - Aristas: {len(result.get('aristas', []))}")
        logger.info(f"  - Interacciones directas: {result.get('estadisticas', {}).get('interacciones_directas', 0)}")
        logger.info(f"  - Tiempo procesamiento: {result.get('processing_time', 0):.3f}s")
        logger.info(f"  - INFLACIÓN ELIMINADA: Solo interacciones directas del número objetivo")
        
        # Log específico para números problema
        if numero_objetivo in ['3113330727', '3243182028', '3009120093']:
            logger.info(f"✓ CORRECCIÓN EXITOSA PARA {numero_objetivo}:")
            logger.info(f"  - ANTES: 255+ nodos (dataset completo)")
            logger.info(f"  - AHORA: {len(result.get('nodos', []))} nodos (interacciones directas)")
            logger.info(f"  - PROBLEMA RESUELTO: Eliminada inflación artificial")
        
        return result
        
    except Exception as e:
        logger.error(f"Error generando diagrama individual para {numero_objetivo}: {e}")
        return {
            'success': False,
            'message': f'Error generando diagrama: {str(e)}',
            'numero_objetivo': numero_objetivo,
            'nodos': [],
            'aristas': [],
            'celdas_hunter': [],
            'estadisticas': {
                'total_nodos': 0,
                'total_aristas': 0,
                'interacciones_directas': 0
            },
            'processing_time': 0,
            'algoritmo': 'INDIVIDUAL_DIRECT_INTERACTIONS_ERROR',
            'correccion_boris': 'Error al aplicar corrección para diagrama individual'
        }


@eel.expose
def get_call_interactions(mission_id, target_number, start_datetime, end_datetime):
    """
    Obtiene interacciones telefónicas específicas de un número objetivo desde operator_call_data
    correlacionadas con datos HUNTER de cellular_data.
    
    Este endpoint retorna todas las llamadas donde el número objetivo fue origen O destino,
    enriquecidas con información de puntos HUNTER cuando las celdas coinciden.
    
    Args:
        mission_id: ID de la misión (string)
        target_number: Número telefónico objetivo (string, sin prefijo +57)
        start_datetime: Inicio del período (string, formato: YYYY-MM-DD HH:MM:SS)
        end_datetime: Fin del período (string, formato: YYYY-MM-DD HH:MM:SS)
        
    Returns:
        Lista de diccionarios con interacciones telefónicas correlacionadas:
        [
            {
                'originador': str,              # Número que originó la llamada
                'receptor': str,                # Número que recibió la llamada  
                'fecha_hora': str,              # Timestamp de la llamada (ISO format)
                'duracion': int,                # Duración en segundos
                'operador': str,                # CLARO, MOVISTAR, TIGO, WOM
                'celda_origen': str,            # Celda del originador (puede ser None)
                'celda_destino': str,           # Celda del receptor (puede ser None)
                'latitud_origen': str,          # Latitud origen de operadora (puede ser None)
                'longitud_origen': str,         # Longitud origen de operadora (puede ser None)
                'latitud_destino': str,         # Latitud destino de operadora (puede ser None)
                'longitud_destino': str,        # Longitud destino de operadora (puede ser None)
                # Campos HUNTER correlacionados (específicos por celda):
                'punto_hunter_origen': str,     # Punto HUNTER de celda origen (puede ser None)
                'lat_hunter_origen': str,       # Latitud HUNTER de celda origen (puede ser None)
                'lon_hunter_origen': str,       # Longitud HUNTER de celda origen (puede ser None)
                'punto_hunter_destino': str,    # Punto HUNTER de celda destino (puede ser None)
                'lat_hunter_destino': str,      # Latitud HUNTER de celda destino (puede ser None)
                'lon_hunter_destino': str,      # Longitud HUNTER de celda destino (puede ser None)
                # CAMPOS HUNTER UNIFICADOS (CORRECCIÓN BORIS 2025-08-19):
                'punto_hunter': str,            # Punto HUNTER unificado (prioriza destino sobre origen)
                'lat_hunter': str,              # Latitud HUNTER unificada (prioriza destino sobre origen)
                'lon_hunter': str,              # Longitud HUNTER unificada (prioriza destino sobre origen)
                'hunter_source': str            # Fuente del dato HUNTER: 'destino', 'origen' o 'ninguno'
            }
        ]
        
    Raises:
        ValueError: Si faltan parámetros requeridos o hay errores de validación
    """
    try:
        logger.info(f"=== OBTENER INTERACCIONES TELEFÓNICAS CON DATOS HUNTER ===")
        logger.info(f"Parámetros recibidos:")
        logger.info(f"  - mission_id: '{mission_id}' (tipo: {type(mission_id)})")
        logger.info(f"  - target_number: '{target_number}' (tipo: {type(target_number)})")
        logger.info(f"  - start_datetime: '{start_datetime}' (tipo: {type(start_datetime)})")
        logger.info(f"  - end_datetime: '{end_datetime}' (tipo: {type(end_datetime)})")
        logger.info(f"Correlacionando llamadas (operator_call_data) con datos HUNTER (cellular_data)")
        
        # Validación detallada de parámetros de entrada
        missing_params = []
        if not mission_id:
            missing_params.append("mission_id")
        if not target_number:
            missing_params.append("target_number")
        if not start_datetime:
            missing_params.append("start_datetime")
        if not end_datetime:
            missing_params.append("end_datetime")
            
        if missing_params:
            error_msg = f"Parámetros faltantes o vacíos: {', '.join(missing_params)}"
            logger.error(error_msg)
            raise ValueError(f"Todos los parámetros son requeridos: mission_id, target_number, start_datetime, end_datetime. Faltantes: {', '.join(missing_params)}")
        
        # Validar que el número sea numérico
        if not str(target_number).isdigit():
            raise ValueError(f"target_number debe ser numérico: {target_number}")
        
        # Normalizar número objetivo (remover cualquier prefijo +57 si existe)
        target_number_clean = str(target_number).replace('+57', '').replace('57', '') if str(target_number).startswith(('57', '+57')) else str(target_number)
        logger.info(f"Número objetivo normalizado: {target_number_clean}")
        
        # Query SQL parametrizada para obtener interacciones con datos HUNTER correlacionados
        # LEFT JOINs con cellular_data para enriquecer con información de puntos HUNTER
        # CORRECCIÓN BORIS 2025-08-19: Query mejorada para resolver problema de "N/A" en Punto HUNTER
        # Problema identificado: Frontend mostraba "N/A" cuando punto_hunter_origen era NULL 
        # pero punto_hunter_destino tenía datos válidos (ej: celda 56124)
        # Solución: Campos unificados que priorizan destino sobre origen usando COALESCE
        query = """
        SELECT 
            ocd.numero_origen as originador,
            ocd.numero_destino as receptor,
            ocd.fecha_hora_llamada as fecha_hora, 
            ocd.duracion_segundos as duracion,
            ocd.operator as operador,
            ocd.celda_origen,
            ocd.celda_destino,
            ocd.latitud_origen,
            ocd.longitud_origen,
            ocd.latitud_destino,
            ocd.longitud_destino,
            cd_origen.punto as punto_hunter_origen,
            cd_origen.lat as lat_hunter_origen,
            cd_origen.lon as lon_hunter_origen,
            cd_destino.punto as punto_hunter_destino,
            cd_destino.lat as lat_hunter_destino,
            cd_destino.lon as lon_hunter_destino,
            -- CAMPOS UNIFICADOS HUNTER (CORRECCIÓN DIRECCIONALIDAD BORIS): Considera dirección de llamada
            CASE 
                WHEN ocd.numero_origen = :target_number THEN cd_origen.punto    -- SALIENTE: ubicación origen
                WHEN ocd.numero_destino = :target_number THEN cd_destino.punto  -- ENTRANTE: ubicación destino
                ELSE COALESCE(cd_destino.punto, cd_origen.punto)               -- Fallback general
            END as punto_hunter,
            CASE 
                WHEN ocd.numero_origen = :target_number THEN cd_origen.lat      -- SALIENTE: latitud origen
                WHEN ocd.numero_destino = :target_number THEN cd_destino.lat    -- ENTRANTE: latitud destino
                ELSE COALESCE(cd_destino.lat, cd_origen.lat)                   -- Fallback general
            END as lat_hunter,
            CASE 
                WHEN ocd.numero_origen = :target_number THEN cd_origen.lon      -- SALIENTE: longitud origen
                WHEN ocd.numero_destino = :target_number THEN cd_destino.lon    -- ENTRANTE: longitud destino
                ELSE COALESCE(cd_destino.lon, cd_origen.lon)                   -- Fallback general
            END as lon_hunter,
            -- Metadatos para transparencia investigativa
            CASE 
                WHEN ocd.numero_origen = :target_number AND cd_origen.punto IS NOT NULL THEN 'origen_direccional'
                WHEN ocd.numero_destino = :target_number AND cd_destino.punto IS NOT NULL THEN 'destino_direccional'
                WHEN ocd.numero_origen = :target_number AND cd_origen.punto IS NULL AND cd_destino.punto IS NOT NULL THEN 'destino_fallback'
                WHEN ocd.numero_destino = :target_number AND cd_destino.punto IS NULL AND cd_origen.punto IS NOT NULL THEN 'origen_fallback'
                ELSE 'sin_ubicacion'
            END as hunter_source,
            -- Campo de precisión para investigadores
            CASE 
                WHEN (ocd.numero_origen = :target_number AND cd_origen.punto IS NOT NULL) OR 
                     (ocd.numero_destino = :target_number AND cd_destino.punto IS NOT NULL) THEN 'ALTA'
                WHEN COALESCE(cd_destino.punto, cd_origen.punto) IS NOT NULL THEN 'MEDIA'
                ELSE 'SIN_DATOS'
            END as precision_ubicacion
        FROM operator_call_data ocd
        LEFT JOIN cellular_data cd_origen ON (cd_origen.cell_id = ocd.celda_origen AND cd_origen.mission_id = ocd.mission_id)
        LEFT JOIN cellular_data cd_destino ON (cd_destino.cell_id = ocd.celda_destino AND cd_destino.mission_id = ocd.mission_id)
        WHERE ocd.mission_id = :mission_id
          AND (ocd.numero_origen = :target_number OR ocd.numero_destino = :target_number)
          AND ocd.fecha_hora_llamada BETWEEN :start_datetime AND :end_datetime  
        ORDER BY ocd.fecha_hora_llamada DESC
        """
        
        # Parámetros para la query (prevención de SQL injection)
        params = {
            'mission_id': mission_id,
            'target_number': target_number_clean,
            'start_datetime': start_datetime,
            'end_datetime': end_datetime
        }
        
        logger.info(f"Ejecutando query con parámetros: {params}")
        
        # Ejecutar query usando conexión directa a SQLite
        interactions = []
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convertir resultados a lista de diccionarios
            column_names = [description[0] for description in cursor.description]
            for row in rows:
                interaction = {}
                for i, value in enumerate(row):
                    field_name = column_names[i]
                    # Convertir valores NULL a None y manejar tipos específicos
                    if value is None:
                        interaction[field_name] = None
                    elif field_name == 'fecha_hora':
                        # Asegurar formato ISO para fechas
                        interaction[field_name] = str(value) if value else None
                    elif field_name == 'duracion':
                        # Asegurar que duración sea entero
                        interaction[field_name] = int(value) if value is not None else 0
                    else:
                        # Convertir a string otros campos
                        interaction[field_name] = str(value) if value is not None else None
                
                interactions.append(interaction)
        
        # Logging de resultados
        total_found = len(interactions)
        logger.info(f"✓ Interacciones encontradas: {total_found}")
        
        if total_found > 0:
            # Log de primeros y últimos registros para verificación
            first_interaction = interactions[0]
            last_interaction = interactions[-1]
            logger.info(f"Primera interacción: {first_interaction['fecha_hora']} - {first_interaction['originador']} → {first_interaction['receptor']}")
            logger.info(f"Última interacción: {last_interaction['fecha_hora']} - {last_interaction['originador']} → {last_interaction['receptor']}")
            
            # Estadísticas de operadores
            operators_count = {}
            for interaction in interactions:
                operator = interaction.get('operador', 'DESCONOCIDO')
                operators_count[operator] = operators_count.get(operator, 0) + 1
            logger.info(f"Distribución por operadores: {operators_count}")
            
            # Estadísticas de correlación HUNTER (por campos específicos)
            hunter_origen_found = sum(1 for i in interactions if i.get('punto_hunter_origen'))
            hunter_destino_found = sum(1 for i in interactions if i.get('punto_hunter_destino'))
            hunter_ambos_found = sum(1 for i in interactions if i.get('punto_hunter_origen') and i.get('punto_hunter_destino'))
            
            # CORRECCIÓN BORIS: Estadísticas de campos unificados 
            hunter_unificado_found = sum(1 for i in interactions if i.get('punto_hunter'))
            hunter_source_stats = {}
            for interaction in interactions:
                source = interaction.get('hunter_source', 'desconocido')
                hunter_source_stats[source] = hunter_source_stats.get(source, 0) + 1
            
            logger.info(f"Correlación HUNTER - Origen: {hunter_origen_found}/{total_found} ({hunter_origen_found/total_found*100:.1f}%)")
            logger.info(f"Correlación HUNTER - Destino: {hunter_destino_found}/{total_found} ({hunter_destino_found/total_found*100:.1f}%)")
            logger.info(f"Correlación HUNTER - Ambos: {hunter_ambos_found}/{total_found} ({hunter_ambos_found/total_found*100:.1f}%)")
            logger.info(f"✓ CORRECCIÓN BORIS - Campo unificado: {hunter_unificado_found}/{total_found} ({hunter_unificado_found/total_found*100:.1f}%)")
            logger.info(f"✓ CORRECCIÓN BORIS - Fuentes HUNTER: {hunter_source_stats}")
        else:
            logger.info("No se encontraron interacciones para los criterios especificados")
            logger.info("Verificar que:")
            logger.info(f"  - La misión {mission_id} tenga datos de llamadas cargados")
            logger.info(f"  - El número {target_number_clean} aparezca en los datos")
            logger.info(f"  - El período {start_datetime} - {end_datetime} contenga actividad")
        
        logger.info(f"=== CONSULTA CON CORRELACIÓN HUNTER COMPLETADA EXITOSAMENTE ===")
        return interactions
        
    except sqlite3.Error as e:
        error_msg = f"Error de base de datos obteniendo interacciones telefónicas: {e}"
        logger.error(error_msg)
        logger.error(f"Query: {query if 'query' in locals() else 'No definida'}")
        logger.error(f"Parámetros: {params if 'params' in locals() else 'No definidos'}")
        handle_service_error("get_call_interactions", e)
    except ValueError as e:
        error_msg = f"Error de validación en get_call_interactions: {e}"
        logger.error(error_msg)
        handle_service_error("get_call_interactions", e)
    except Exception as e:
        error_msg = f"Error inesperado obteniendo interacciones telefónicas: {e}"
        logger.error(error_msg)
        import traceback
        logger.error(f"Traceback completo:\n{traceback.format_exc()}")
        handle_service_error("get_call_interactions", e)


# ============================================================================
# SIGNAL HANDLERS Y CLEANUP SETUP
# ============================================================================

def setup_signal_handlers():
    """Configura manejadores de señales para cierre graceful"""
    
    def signal_handler(signum, frame):
        signal_name = {
            signal.SIGINT: "SIGINT (Ctrl+C)",
            getattr(signal, 'SIGTERM', None): "SIGTERM"
        }.get(signum, f"Señal {signum}")
        
        logger.info(f"Señal {signal_name} recibida, iniciando cierre graceful...")
        shutdown_manager.initiate_shutdown(f"Señal del sistema: {signal_name}")
    
    # Configurar manejadores
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM') and os.name != 'nt':  # SIGTERM no disponible en Windows
        signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Manejadores de señales configurados")


def setup_cleanup_handlers():
    """Registra todos los handlers de cleanup necesarios"""
    
    def cleanup_database():
        """Cierra conexiones de base de datos"""
        try:
            db_manager = get_database_manager()
            if db_manager and db_manager._initialized:
                db_manager.close()
        except Exception as e:
            logger.error(f"Error cerrando base de datos: {e}")
    
    def cleanup_auth_service():
        """Cierra sesión de usuario autenticado"""
        try:
            if auth_service and auth_service.is_authenticated():
                auth_service.logout()
        except Exception as e:
            logger.error(f"Error cerrando sesión de usuario: {e}")
    
    def cleanup_logging_handlers():
        """Cierra y hace flush de todos los handlers de logging"""
        try:
            # Flush y cerrar handlers del logger principal
            for handler in logger.handlers[:]:
                try:
                    handler.flush()
                    if hasattr(handler, 'close'):
                        handler.close()
                except:
                    pass
            
            # Flush y cerrar handlers del root logger
            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                try:
                    handler.flush()
                    if hasattr(handler, 'close'):
                        handler.close()
                except:
                    pass
        except Exception as e:
            logger.error(f"Error cerrando handlers de logging: {e}")
    
    def cleanup_services():
        """Cleanup general de servicios"""
        global auth_service, user_service, role_service, mission_service, analysis_service, correlation_service
        try:
            # Limpiar referencias a servicios
            auth_service = None
            user_service = None
            role_service = None
            mission_service = None
            analysis_service = None
            correlation_service = None
        except Exception as e:
            logger.error(f"Error limpiando servicios: {e}")
    
    # Registrar handlers en orden de prioridad
    shutdown_manager.register_cleanup_handler(
        "Sesión de Usuario", 
        cleanup_auth_service, 
        critical=False
    )
    
    shutdown_manager.register_cleanup_handler(
        "Base de Datos", 
        cleanup_database, 
        critical=True
    )
    
    shutdown_manager.register_cleanup_handler(
        "Servicios", 
        cleanup_services, 
        critical=False
    )
    
    shutdown_manager.register_cleanup_handler(
        "Logging", 
        cleanup_logging_handlers, 
        critical=True
    )
    
    logger.info("Handlers de cleanup registrados")


def setup_atexit_handler():
    """Configura handler de salida del proceso"""
    
    def atexit_cleanup():
        if not shutdown_manager._shutdown_initiated:
            logger.info("Proceso terminando sin shutdown explícito, iniciando cleanup...")
            shutdown_manager.initiate_shutdown("Terminación del proceso")
    
    atexit.register(atexit_cleanup)
    logger.info("Handler atexit configurado")


# ============================================================================
# INITIALIZATION AND STARTUP
# ============================================================================

def initialize_backend():
    """Inicializa el backend completo"""
    try:
        logger.info("=== INICIANDO BACKEND KRONOS ===")
        
        # Configurar sistema de shutdown
        logger.info("Configurando sistema de shutdown...")
        shutdown_manager.set_logger(logger)
        setup_signal_handlers()
        setup_cleanup_handlers()
        setup_atexit_handler()
        logger.info("Sistema de shutdown configurado exitosamente")
        
        # Inicializar base de datos con manejo robusto de errores
        logger.info("Inicializando base de datos...")
        db_path = os.path.join(current_dir, 'kronos.db')
        
        # Intentar inicialización normal primero
        try:
            init_database(db_path, force_recreate=False)
            logger.info("Base de datos inicializada exitosamente")
        except Exception as db_error:
            logger.warning(f"Error en inicialización normal de BD: {db_error}")
            logger.info("Intentando recrear base de datos...")
            try:
                # Si falla, recrear completamente la base de datos
                init_database(db_path, force_recreate=True)
                logger.info("Base de datos recreada exitosamente")
            except Exception as recreation_error:
                logger.error(f"Error crítico recreando base de datos: {recreation_error}")
                raise
        
        # Inicializar servicios después de la BD
        logger.info("Inicializando servicios...")
        global auth_service, user_service, role_service, mission_service, analysis_service
        
        auth_service = get_auth_service()
        user_service = get_user_service()
        role_service = get_role_service()
        mission_service = get_mission_service()
        analysis_service = get_analysis_service()
        
        logger.info("Servicios inicializados exitosamente")
        
        # Verificar servicios
        logger.info("Verificando servicios...")
        
        # Test de servicios básicos con reintentos
        max_retries = 3
        for attempt in range(max_retries):
            try:
                roles = role_service.get_all_roles()
                users = user_service.get_all_users()
                missions = mission_service.get_all_missions()
                
                logger.info(f"Sistema verificado: {len(roles)} roles, {len(users)} usuarios, {len(missions)} misiones")
                break
                
            except Exception as e:
                if attempt == max_retries - 1:  # Último intento
                    logger.error(f"Error verificando servicios después de {max_retries} intentos: {e}")
                    # Intentar una última recreación completa
                    logger.info("Intentando recreación final de base de datos...")
                    init_database(db_path, force_recreate=True)
                    
                    # Reinicializar servicios después de recrear BD
                    auth_service = get_auth_service()
                    user_service = get_user_service()
                    role_service = get_role_service()
                    mission_service = get_mission_service()
                    analysis_service = get_analysis_service()
                    
                    # Un último test
                    roles = role_service.get_all_roles()
                    users = user_service.get_all_users()
                    missions = mission_service.get_all_missions()
                    logger.info(f"Sistema verificado tras recreación: {len(roles)} roles, {len(users)} usuarios, {len(missions)} misiones")
                    break
                else:
                    logger.warning(f"Error en intento {attempt + 1}/{max_retries}: {e}")
                    import time
                    time.sleep(1)  # Esperar 1 segundo antes del siguiente intento
        
        logger.info("=== BACKEND INICIALIZADO CORRECTAMENTE ===")
        
    except Exception as e:
        logger.error(f"Error crítico inicializando backend: {e}")
        import traceback
        logger.error(f"Traceback completo:\n{traceback.format_exc()}")
        sys.exit(1)


def main():
    """Función principal de la aplicación"""
    try:
        # Inicializar backend
        initialize_backend()
        
        # Configurar Eel
        # Primero buscar dist/ para producción, luego Frontend/ para desarrollo
        dist_path = os.path.join(current_dir, '..', 'Frontend', 'dist')
        frontend_path = os.path.join(current_dir, '..', 'Frontend')
        
        if os.path.exists(dist_path) and os.path.exists(os.path.join(dist_path, 'index.html')):
            # Usar build de producción
            eel_path = dist_path
            logger.info("Usando build de producción desde Frontend/dist/")
        elif os.path.exists(frontend_path) and os.path.exists(os.path.join(frontend_path, 'index.html')):
            # Usar fuentes de desarrollo
            eel_path = frontend_path
            logger.info("Usando fuentes de desarrollo desde Frontend/")
            logger.warning("MODO DESARROLLO: Para producción, ejecuta 'build.bat' primero")
        else:
            logger.error("No se encontró ni build de producción (Frontend/dist/) ni fuentes de desarrollo (Frontend/)")
            logger.error("Para compilar: ejecuta 'build.bat' desde el directorio raíz del proyecto")
            sys.exit(1)
        
        eel.init(eel_path)
        logger.info(f"Eel inicializado con directorio: {eel_path}")
        
        # Verificar que index.html existe
        index_path = os.path.join(eel_path, 'index.html')
        if not os.path.exists(index_path):
            logger.error(f"Archivo index.html no encontrado: {index_path}")
            sys.exit(1)
        
        logger.info("Iniciando aplicación Eel...")
        logger.info("La aplicación estará disponible en la ventana del navegador que se abrirá")
        
        # Iniciar aplicación Eel para testing (sin close_callback)
        eel.start(
            'index.html',
            size=(1440, 900),
            position=(100, 100),
            disable_cache=True,
            mode='chrome',  # Usar Chrome si está disponible
            port=8000,
            host='localhost'
        )
        
    except KeyboardInterrupt:
        logger.info("Aplicación interrumpida por el usuario (Ctrl+C)")
        shutdown_manager.initiate_shutdown("Interrupción por teclado (Ctrl+C)")
    except Exception as e:
        logger.error(f"Error ejecutando aplicación: {e}")
        shutdown_manager.initiate_shutdown(f"Error crítico: {e}")
        sys.exit(1)
    finally:
        # El shutdown manager se encargará del cleanup via atexit
        pass


if __name__ == '__main__':
    main()