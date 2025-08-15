"""
KRONOS - Servicio Principal de Datos de Operadores Celulares
==========================================================

Este módulo proporciona las funciones principales expuestas vía Eel para la gestión
de datos de operadores celulares. Implementa un patrón de servicio robusto con:

- Funciones Eel expuestas para comunicación JavaScript-Python
- Manejo transaccional de archivos
- Validación rigurosa de entrada
- Logging detallado para auditoría
- Soporte para todos los operadores (CLARO, MOVISTAR, TIGO, WOM)

Autor: Sistema KRONOS
Versión: 1.0.0
"""

import eel
import uuid
import hashlib
import base64
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import traceback
from pathlib import Path
import sys
import os

# Agregar el directorio padre al path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db_connection
from services.file_processor_service import FileProcessorService
from services.data_normalizer_service import DataNormalizerService  
from utils.operator_logger import OperatorLogger


def _ensure_eel_serializable(response_dict):
    """
    Asegura que la respuesta sea compatible con la serialización Eel Python-JavaScript.
    
    Args:
        response_dict: Diccionario de respuesta a serializar
        
    Returns:
        dict: Respuesta con tipos garantizados para serialización
    """
    safe_response = {}
    for key, value in response_dict.items():
        if isinstance(value, str):
            safe_response[key] = str(value)
        elif isinstance(value, bool):
            safe_response[key] = bool(value)
        elif isinstance(value, (int, float)):
            safe_response[key] = int(value) if isinstance(value, int) else float(value)
        elif isinstance(value, list):
            safe_response[key] = list(value)  # Asegurar que es una lista Python estándar
        elif value is None:
            safe_response[key] = None
        else:
            safe_response[key] = str(value)  # Fallback a string
    return safe_response


class OperatorDataService:
    """
    Servicio principal para gestión de datos de operadores celulares.
    
    Implementa el patrón Repository con servicios especializados para
    procesamiento de archivos y normalización de datos.
    """
    
    def __init__(self):
        """Inicializa el servicio con dependencias."""
        self.file_processor = FileProcessorService()
        self.data_normalizer = DataNormalizerService()
        self.logger = OperatorLogger()
        # Verificar y aplicar migración de schema si es necesario
        self._ensure_schema_migration()
        
        # Configuración de operadores soportados
        self.SUPPORTED_OPERATORS = ['CLARO', 'MOVISTAR', 'TIGO', 'WOM']
        self.SUPPORTED_FILE_TYPES = ['CELLULAR_DATA', 'CALL_DATA']
        
        # Límites de archivo (20MB en bytes)
        self.MAX_FILE_SIZE = 20 * 1024 * 1024
        
        self.logger.info("OperatorDataService inicializado correctamente")
    
    def _get_column_configuration(self, operator: str, file_type: str) -> Dict[str, Any]:
        """
        Retorna la configuración de columnas específica para el operador y tipo de archivo.
        
        Args:
            operator: Nombre del operador (CLARO, MOVISTAR, TIGO, WOM)
            file_type: Tipo de archivo (CELLULAR_DATA, CALL_DATA)
        
        Returns:
            Dict con configuración de columnas, query SELECT y mapeo para frontend
        """
        
        if file_type == 'CALL_DATA':
            if operator == 'TIGO':
                return {
                    'columns': [
                        'id', 'numero_origen', 'numero_destino', 'fecha_hora_llamada', 
                        'duracion_segundos', 'celda_origen', 'cellid_decimal', 'lac_decimal', 
                        'tecnologia', 'tipo_llamada', 'latitud_origen', 'longitud_origen'
                    ],
                    'select_query': """
                        SELECT 
                            id, numero_origen, numero_destino, fecha_hora_llamada,
                            duracion_segundos, celda_origen, cellid_decimal, lac_decimal,
                            tecnologia, tipo_llamada, latitud_origen, longitud_origen, created_at
                        FROM operator_call_data
                    """,
                    'display_names': {
                        'id': 'ID',
                        'numero_origen': 'Número A',
                        'numero_destino': 'Número Marcado', 
                        'fecha_hora_llamada': 'Fecha/Hora',
                        'duracion_segundos': 'Duración (seg)',
                        'celda_origen': 'Celda Origen',
                        'cellid_decimal': 'Cell ID (Dec)',
                        'lac_decimal': 'LAC (Dec)',
                        'tecnologia': 'Tecnología',
                        'tipo_llamada': 'Dirección',
                        'latitud_origen': 'Latitud',
                        'longitud_origen': 'Longitud'
                    }
                }
            
            elif operator == 'CLARO':
                return {
                    'columns': [
                        'id', 'numero_origen', 'numero_destino', 'fecha_hora_llamada',
                        'duracion_segundos', 'celda_origen', 'celda_destino', 'tipo_llamada'
                    ],
                    'select_query': """
                        SELECT 
                            id, numero_origen, numero_destino, fecha_hora_llamada,
                            duracion_segundos, celda_origen, celda_destino, tipo_llamada,
                            created_at
                        FROM operator_call_data
                    """,
                    'display_names': {
                        'id': 'ID',
                        'numero_origen': 'Número Origen',
                        'numero_destino': 'Número Destino',
                        'fecha_hora_llamada': 'Fecha/Hora',
                        'duracion_segundos': 'Duración (seg)',
                        'celda_origen': 'Celda Origen',
                        'celda_destino': 'Celda Destino',
                        'tipo_llamada': 'Tipo Llamada'
                    }
                }
            
            elif operator == 'MOVISTAR':
                return {
                    'columns': [
                        'id', 'numero_origen', 'numero_destino', 'fecha_hora_llamada',
                        'duracion_segundos', 'celda_origen', 'cellid_decimal', 'lac_decimal', 'tipo_llamada'
                    ],
                    'select_query': """
                        SELECT 
                            id, numero_origen, numero_destino, fecha_hora_llamada,
                            duracion_segundos, celda_origen, cellid_decimal, lac_decimal, tipo_llamada, created_at
                        FROM operator_call_data
                    """,
                    'display_names': {
                        'id': 'ID',
                        'numero_origen': 'Número que Contesta',
                        'numero_destino': 'Número que Marca',
                        'fecha_hora_llamada': 'Fecha/Hora',
                        'duracion_segundos': 'Duración (seg)',
                        'celda_origen': 'Celda Origen',
                        'cellid_decimal': 'Cell ID (Dec)',
                        'lac_decimal': 'LAC (Dec)',
                        'tipo_llamada': 'Tipo'
                    }
                }
        
        elif file_type == 'CELLULAR_DATA':
            if operator == 'CLARO':
                return {
                    'columns': [
                        'id', 'numero_telefono', 'fecha_hora_inicio', 'celda_id', 
                        'lac_tac', 'tipo_conexion'
                    ],
                    'select_query': """
                        SELECT 
                            id, numero_telefono, fecha_hora_inicio, celda_id,
                            lac_tac, tipo_conexion, created_at
                        FROM operator_cellular_data
                    """,
                    'display_names': {
                        'id': 'ID',
                        'numero_telefono': 'Número',
                        'fecha_hora_inicio': 'Fecha Tráfico',
                        'celda_id': 'Celda',
                        'lac_tac': 'LAC',
                        'tipo_conexion': 'Tipo CDR'
                    }
                }
            
            elif operator == 'MOVISTAR':
                return {
                    'columns': [
                        'id', 'numero_telefono', 'fecha_hora_inicio', 'fecha_hora_fin',
                        'celda_id', 'trafico_subida_bytes', 'trafico_bajada_bytes',
                        'latitud', 'longitud', 'tecnologia'
                    ],
                    'select_query': """
                        SELECT 
                            id, numero_telefono, fecha_hora_inicio, fecha_hora_fin,
                            celda_id, trafico_subida_bytes, trafico_bajada_bytes,
                            latitud, longitud, tecnologia, created_at
                        FROM operator_cellular_data
                    """,
                    'display_names': {
                        'id': 'ID',
                        'numero_telefono': 'Número que Navega',
                        'fecha_hora_inicio': 'Inicio Sesión',
                        'fecha_hora_fin': 'Fin Sesión',
                        'celda_id': 'Celda',
                        'trafico_subida_bytes': 'Tráfico Subida',
                        'trafico_bajada_bytes': 'Tráfico Bajada',
                        'latitud': 'Latitud',
                        'longitud': 'Longitud',
                        'tecnologia': 'Tecnología'
                    }
                }
        
        # Fallback para operadores no configurados
        if file_type == 'CALL_DATA':
            return {
                'columns': [
                    'id', 'numero_origen', 'numero_destino', 'fecha_hora_llamada',
                    'duracion_segundos', 'celda_origen', 'cellid_decimal', 'lac_decimal', 'tipo_llamada'
                ],
                'select_query': """
                    SELECT 
                        id, numero_origen, numero_destino, fecha_hora_llamada,
                        duracion_segundos, celda_origen, cellid_decimal, lac_decimal, tipo_llamada, created_at
                    FROM operator_call_data
                """,
                'display_names': {
                    'id': 'ID',
                    'numero_origen': 'Número Origen',
                    'numero_destino': 'Número Destino',
                    'fecha_hora_llamada': 'Fecha/Hora',
                    'duracion_segundos': 'Duración (seg)',
                    'celda_origen': 'Celda',
                    'cellid_decimal': 'Cell ID (Dec)',
                    'lac_decimal': 'LAC (Dec)',
                    'tipo_llamada': 'Tipo'
                }
            }
        else:  # CELLULAR_DATA fallback
            return {
                'columns': [
                    'id', 'numero_telefono', 'fecha_hora_inicio', 'celda_id',
                    'lac_tac', 'tecnologia'
                ],
                'select_query': """
                    SELECT 
                        id, numero_telefono, fecha_hora_inicio, celda_id,
                        lac_tac, tecnologia, created_at
                    FROM operator_cellular_data
                """,
                'display_names': {
                    'id': 'ID',
                    'numero_telefono': 'Teléfono',
                    'fecha_hora_inicio': 'Timestamp',
                    'celda_id': 'Cell ID',
                    'lac_tac': 'LAC',
                    'tecnologia': 'Tecnología'
                }
            }
    
    def _ensure_schema_migration(self):
        """
        Verifica si necesita aplicar la migración para permitir duplicados por misión.
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Verificar si la tabla tiene el constraint antiguo (UNIQUE global)
                cursor.execute("""
                    SELECT sql FROM sqlite_master 
                    WHERE type='table' AND name='operator_data_sheets'
                """)
                
                table_sql = cursor.fetchone()
                if table_sql and 'file_checksum TEXT NOT NULL UNIQUE' in table_sql[0]:
                    self.logger.info("Aplicando migración: cambiar validación duplicados de global a por misión")
                    self._apply_duplicate_per_mission_migration(conn)
                    self.logger.info("Migración completada exitosamente")
                else:
                    self.logger.debug("Schema ya está actualizado para validación por misión")
                    
        except Exception as e:
            self.logger.error(f"Error verificando migración de schema: {str(e)}")
            # No fallar el servicio por problemas de migración
    
    def _apply_duplicate_per_mission_migration(self, conn):
        """
        Aplica la migración para cambiar el constraint de duplicados.
        """
        cursor = conn.cursor()
        
        # Ejecutar la migración paso a paso
        migration_steps = [
            # Crear tabla temporal con nuevo constraint
            """
            CREATE TABLE operator_data_sheets_new (
                id TEXT PRIMARY KEY NOT NULL,
                mission_id TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_size_bytes INTEGER NOT NULL,
                file_checksum TEXT NOT NULL,
                file_type TEXT NOT NULL,
                operator TEXT NOT NULL,
                operator_file_format TEXT NOT NULL,
                processing_status TEXT NOT NULL DEFAULT 'PENDING',
                records_processed INTEGER DEFAULT 0,
                records_failed INTEGER DEFAULT 0,
                processing_start_time DATETIME,
                processing_end_time DATETIME,
                processing_duration_seconds INTEGER,
                error_details TEXT,
                uploaded_by TEXT NOT NULL,
                uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                CHECK (processing_status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')),
                CHECK (file_type IN ('CELLULAR_DATA', 'CALL_DATA')),
                CHECK (operator IN ('CLARO', 'MOVISTAR', 'TIGO', 'WOM')),
                CHECK (file_size_bytes > 0),
                CHECK (records_processed >= 0),
                CHECK (records_failed >= 0),
                CHECK (length(trim(file_name)) > 0),
                CHECK (length(trim(file_checksum)) = 64),
                CHECK (length(trim(uploaded_by)) > 0),
                UNIQUE (file_checksum, mission_id),
                FOREIGN KEY (mission_id) REFERENCES missions(id) ON DELETE CASCADE
            )
            """,
            
            # Copiar datos existentes
            """
            INSERT INTO operator_data_sheets_new 
            SELECT * FROM operator_data_sheets
            """,
            
            # Eliminar tabla antigua
            "DROP TABLE operator_data_sheets",
            
            # Renombrar tabla nueva
            "ALTER TABLE operator_data_sheets_new RENAME TO operator_data_sheets",
            
            # Recrear índices principales
            "CREATE INDEX idx_operator_sheets_mission_operator ON operator_data_sheets(mission_id, operator)",
            "CREATE INDEX idx_operator_sheets_checksum ON operator_data_sheets(file_checksum)",
            "CREATE INDEX idx_operator_sheets_status ON operator_data_sheets(processing_status)",
            "CREATE INDEX idx_operator_sheets_upload_time ON operator_data_sheets(uploaded_at)",
            "CREATE INDEX idx_operator_sheets_mission_checksum ON operator_data_sheets(mission_id, file_checksum)"
        ]
        
        for step in migration_steps:
            cursor.execute(step)
        
        conn.commit()
    
    def _validate_mission_exists(self, mission_id: str) -> bool:
        """Valida que la misión existe en la base de datos."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM missions WHERE id = ?", (mission_id,))
                return cursor.fetchone() is not None
        except Exception as e:
            self.logger.error(f"Error validando misión {mission_id}: {str(e)}")
            return False
    
    def _validate_user_exists(self, user_id: str) -> bool:
        """Valida que el usuario existe en la base de datos."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
                return cursor.fetchone() is not None
        except Exception as e:
            self.logger.error(f"Error validando usuario {user_id}: {str(e)}")
            return False
    
    def _calculate_file_checksum(self, file_data: bytes) -> str:
        """Calcula el checksum SHA256 del archivo."""
        return hashlib.sha256(file_data).hexdigest()
    
    def _check_file_duplicate(self, checksum: str, mission_id: str) -> bool:
        """
        Verifica si un archivo con el mismo checksum ya existe exitosamente en la misma misión.
        Permite reprocesamiento de archivos que fallaron anteriormente.
        
        Args:
            checksum: SHA256 checksum del archivo
            mission_id: ID de la misión donde se quiere cargar el archivo
            
        Returns:
            bool: True si el archivo ya existe exitosamente en esta misión, False en caso contrario
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, processing_status FROM operator_data_sheets WHERE file_checksum = ? AND mission_id = ?",
                    (checksum, mission_id)
                )
                result = cursor.fetchone()
                
                if result:
                    existing_id, existing_status = result
                    
                    # Solo bloquear si el procesamiento fue exitoso o está en progreso
                    if existing_status in ['COMPLETED', 'PROCESSING']:
                        self.logger.warning(f"Archivo duplicado detectado en misión {mission_id}: checksum {checksum[:8]}... (estado: {existing_status})")
                        return True
                    
                    # Si el archivo falló anteriormente, permitir reprocesamiento
                    elif existing_status in ['FAILED', 'ERROR']:
                        self.logger.info(f"Archivo falló anteriormente ({existing_status}), eliminando registro para reprocesar: {existing_id}")
                        
                        # Eliminar datos asociados al procesamiento anterior
                        cursor.execute("DELETE FROM operator_call_data WHERE file_upload_id = ?", (existing_id,))
                        deleted_calls = cursor.rowcount
                        
                        cursor.execute("DELETE FROM operator_data_sheets WHERE id = ?", (existing_id,))
                        deleted_sheet = cursor.rowcount
                        
                        conn.commit()
                        
                        self.logger.info(f"Limpieza completada: {deleted_calls} llamadas, {deleted_sheet} hoja eliminadas")
                        return False  # Permitir reprocesamiento
                
                return False  # No existe, permitir procesamiento
                
        except Exception as e:
            self.logger.error(f"Error verificando duplicado: {str(e)}")
            return False
    
    def _create_file_record(self, file_info: Dict[str, Any]) -> str:
        """Crea el registro inicial del archivo en operator_data_sheets."""
        file_upload_id = str(uuid.uuid4())
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO operator_data_sheets (
                        id, mission_id, file_name, file_size_bytes, 
                        file_checksum, file_type, operator, operator_file_format,
                        processing_status, uploaded_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    file_upload_id,
                    file_info['mission_id'],
                    file_info['file_name'],
                    file_info['file_size'],
                    file_info['checksum'],
                    file_info['file_type'],
                    file_info['operator'],
                    file_info['format'],
                    'PENDING',
                    file_info['user_id']
                ))
                conn.commit()
                
                self.logger.info(
                    f"Registro de archivo creado: {file_upload_id}",
                    extra={'file_name': file_info['file_name'], 'operator': file_info['operator']}
                )
                
                return file_upload_id
                
        except Exception as e:
            self.logger.error(f"Error creando registro de archivo: {str(e)}")
            raise
    
    def _update_processing_status(self, file_upload_id: str, status: str, 
                                error_details: Optional[str] = None):
        """Actualiza el estado de procesamiento del archivo."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                if status == 'PROCESSING':
                    cursor.execute("""
                        UPDATE operator_data_sheets 
                        SET processing_status = ?, processing_start_time = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (status, file_upload_id))
                
                elif status in ['COMPLETED', 'FAILED']:
                    cursor.execute("""
                        UPDATE operator_data_sheets 
                        SET processing_status = ?, 
                            processing_end_time = CURRENT_TIMESTAMP,
                            processing_duration_seconds = 
                                (julianday(CURRENT_TIMESTAMP) - julianday(processing_start_time)) * 86400,
                            error_details = ?
                        WHERE id = ?
                    """, (status, error_details, file_upload_id))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error actualizando estado {status}: {str(e)}")
            raise


# ==============================================================================
# FUNCIONES EEL EXPUESTAS - Interfaz JavaScript-Python
# ==============================================================================

@eel.expose
def upload_operator_data(file_data: str, file_name: str, mission_id: str, 
                        operator: str, file_type: str, user_id: str) -> Dict[str, Any]:
    """
    Procesa la carga de un archivo de datos de operador celular.
    
    Args:
        file_data (str): Archivo codificado en Base64
        file_name (str): Nombre original del archivo
        mission_id (str): ID de la misión asociada
        operator (str): Operador celular ('CLARO', 'MOVISTAR', 'TIGO', 'WOM')
        file_type (str): Tipo de datos ('CELLULAR_DATA', 'CALL_DATA')
        user_id (str): ID del usuario que sube el archivo
    
    Returns:
        Dict[str, Any]: Resultado del procesamiento con estado y detalles
    """
    service = OperatorDataService()
    
    try:
        service.logger.info(
            f"Iniciando carga de archivo {file_name}",
            extra={
                'operator': operator,
                'file_type': file_type,
                'mission_id': mission_id,
                'user_id': user_id
            }
        )
        
        # === VALIDACIÓN DE ENTRADA ===
        
        # Validar parámetros requeridos
        if not all([file_data, file_name, mission_id, operator, file_type, user_id]):
            error_msg = 'Todos los parámetros son requeridos'
            response = {
                'success': False,
                'error': error_msg,
                'error_code': 'MISSING_PARAMETERS',
                'processedRecords': 0,
                'warnings': [],
                'errors': [error_msg]
            }
            return _ensure_eel_serializable(response)
        
        # Validar operador soportado
        if operator.upper() not in service.SUPPORTED_OPERATORS:
            error_msg = f'Operador no soportado: {operator}. Soportados: {", ".join(service.SUPPORTED_OPERATORS)}'
            response = {
                'success': False,
                'error': error_msg,
                'error_code': 'UNSUPPORTED_OPERATOR',
                'processedRecords': 0,
                'warnings': [],
                'errors': [error_msg]
            }
            return _ensure_eel_serializable(response)
        
        # Validar tipo de archivo
        if file_type not in service.SUPPORTED_FILE_TYPES:
            error_msg = f'Tipo de archivo no soportado: {file_type}'
            response = {
                'success': False,
                'error': error_msg,
                'error_code': 'UNSUPPORTED_FILE_TYPE',
                'processedRecords': 0,
                'warnings': [],
                'errors': [error_msg]
            }
            return _ensure_eel_serializable(response)
        
        # Validar que la misión existe
        if not service._validate_mission_exists(mission_id):
            error_msg = f'La misión {mission_id} no existe'
            response = {
                'success': False,
                'error': error_msg,
                'error_code': 'MISSION_NOT_FOUND',
                'processedRecords': 0,
                'warnings': [],
                'errors': [error_msg]
            }
            return _ensure_eel_serializable(response)
        
        # Validar que el usuario existe
        if not service._validate_user_exists(user_id):
            error_msg = f'El usuario {user_id} no existe'
            response = {
                'success': False,
                'error': error_msg,
                'error_code': 'USER_NOT_FOUND',
                'processedRecords': 0,
                'warnings': [],
                'errors': [error_msg]
            }
            return _ensure_eel_serializable(response)
        
        # === PROCESAMIENTO DEL ARCHIVO ===
        
        # Decodificar archivo Base64
        try:
            file_bytes = base64.b64decode(file_data)
        except Exception as e:
            service.logger.error(f"Error decodificando Base64: {str(e)}")
            error_msg = 'Error decodificando archivo Base64'
            response = {
                'success': False,
                'error': error_msg,
                'error_code': 'INVALID_BASE64',
                'processedRecords': 0,
                'warnings': [],
                'errors': [error_msg]
            }
            return _ensure_eel_serializable(response)
        
        # Validar tamaño de archivo
        file_size = len(file_bytes)
        if file_size > service.MAX_FILE_SIZE:
            error_msg = f'Archivo demasiado grande: {file_size / 1024 / 1024:.1f}MB. Máximo: {service.MAX_FILE_SIZE / 1024 / 1024}MB'
            response = {
                'success': False,
                'error': error_msg,
                'error_code': 'FILE_TOO_LARGE',
                'processedRecords': 0,
                'warnings': [],
                'errors': [error_msg]
            }
            return _ensure_eel_serializable(response)
        
        # Calcular checksum y verificar duplicados en la misma misión
        file_checksum = service._calculate_file_checksum(file_bytes)
        if service._check_file_duplicate(file_checksum, mission_id):
            error_msg = f'Este archivo ya ha sido procesado anteriormente en esta misión'
            response = {
                'success': False,
                'error': error_msg,
                'error_code': 'DUPLICATE_FILE',
                'processedRecords': 0,
                'warnings': [],
                'errors': [error_msg]
            }
            return _ensure_eel_serializable(response)
        
        # Determinar formato de archivo basado en extensión
        file_extension = Path(file_name).suffix.lower()
        if file_extension not in ['.csv', '.xlsx']:
            error_msg = f'Formato de archivo no soportado: {file_extension}. Use CSV o XLSX'
            response = {
                'success': False,
                'error': error_msg,
                'error_code': 'UNSUPPORTED_FORMAT',
                'processedRecords': 0,
                'warnings': [],
                'errors': [error_msg]
            }
            return _ensure_eel_serializable(response)
        
        # Crear información del archivo
        file_info = {
            'mission_id': mission_id,
            'file_name': file_name,
            'file_size': file_size,
            'checksum': file_checksum,
            'file_type': file_type,
            'operator': operator.upper(),
            'format': f"{operator.upper()}_{file_type}_{file_extension[1:].upper()}",
            'user_id': user_id
        }
        
        # Crear registro inicial en base de datos
        file_upload_id = service._create_file_record(file_info)
        
        # === PROCESAMIENTO ESPECÍFICO POR OPERADOR ===
        
        try:
            # Actualizar estado a PROCESSING
            service._update_processing_status(file_upload_id, 'PROCESSING')
            
            processing_result = None
            
            if operator.upper() == 'CLARO' and file_type == 'CELLULAR_DATA':
                # Procesar datos celulares de CLARO
                processing_result = service.file_processor.process_claro_data_por_celda(
                    file_bytes=file_bytes,
                    file_name=file_name,
                    file_upload_id=file_upload_id,
                    mission_id=mission_id
                )
            
            elif operator.upper() == 'CLARO' and file_type == 'CALL_DATA':
                # Procesar datos de llamadas de CLARO (detecta automáticamente el subtipo)
                # Determinar subtipo basado en el nombre del archivo o contenido
                if 'ENTRANTE' in file_name.upper() or 'ENTRADA' in file_name.upper():
                    processing_result = service.file_processor.process_claro_llamadas_entrantes(
                        file_bytes=file_bytes,
                        file_name=file_name,
                        file_upload_id=file_upload_id,
                        mission_id=mission_id
                    )
                elif 'SALIENTE' in file_name.upper() or 'SALIDA' in file_name.upper():
                    processing_result = service.file_processor.process_claro_llamadas_salientes(
                        file_bytes=file_bytes,
                        file_name=file_name,
                        file_upload_id=file_upload_id,
                        mission_id=mission_id
                    )
                else:
                    # Intentar detectar automáticamente por el contenido
                    # Leer una muestra del archivo para detectar el tipo
                    try:
                        # Detectar tipo basado en el contenido del archivo
                        if file_name.lower().endswith('.csv'):
                            # Leer las primeras líneas para detectar CDR_ENTRANTE vs CDR_SALIENTE
                            df_sample = service.file_processor._read_csv_robust(file_bytes[:10000], delimiter=',')  # Muestra de 10KB
                            if len(df_sample) > 0 and 'tipo' in df_sample.columns:
                                tipos_encontrados = df_sample['tipo'].astype(str).str.upper().unique()
                                if any('CDR_SALIENTE' in tipo for tipo in tipos_encontrados):
                                    processing_result = service.file_processor.process_claro_llamadas_salientes(
                                        file_bytes=file_bytes,
                                        file_name=file_name,
                                        file_upload_id=file_upload_id,
                                        mission_id=mission_id
                                    )
                                else:
                                    # Por defecto, usar entrantes
                                    processing_result = service.file_processor.process_claro_llamadas_entrantes(
                                        file_bytes=file_bytes,
                                        file_name=file_name,
                                        file_upload_id=file_upload_id,
                                        mission_id=mission_id
                                    )
                            else:
                                # Si no se puede detectar, usar entrantes por defecto
                                processing_result = service.file_processor.process_claro_llamadas_entrantes(
                                    file_bytes=file_bytes,
                                    file_name=file_name,
                                    file_upload_id=file_upload_id,
                                    mission_id=mission_id
                                )
                        else:
                            # Para XLSX u otros, usar entrantes por defecto
                            processing_result = service.file_processor.process_claro_llamadas_entrantes(
                                file_bytes=file_bytes,
                                file_name=file_name,
                                file_upload_id=file_upload_id,
                                mission_id=mission_id
                            )
                    except Exception as detection_error:
                        service.logger.warning(f"Error en detección automática de tipo de llamada: {detection_error}")
                        # Fallback: usar entrantes por defecto
                        processing_result = service.file_processor.process_claro_llamadas_entrantes(
                            file_bytes=file_bytes,
                            file_name=file_name,
                            file_upload_id=file_upload_id,
                            mission_id=mission_id
                        )
            
            elif operator.upper() == 'MOVISTAR' and file_type == 'CELLULAR_DATA':
                # Procesar datos celulares de MOVISTAR
                processing_result = service.file_processor.process_movistar_datos_por_celda(
                    file_bytes=file_bytes,
                    file_name=file_name,
                    file_upload_id=file_upload_id,
                    mission_id=mission_id
                )
            
            elif operator.upper() == 'MOVISTAR' and file_type == 'CALL_DATA':
                # Procesar datos de llamadas de MOVISTAR
                # MOVISTAR típicamente tiene archivos de llamadas salientes
                if 'saliente' in file_name.lower() or 'vozm' in file_name.lower():
                    processing_result = service.file_processor.process_movistar_llamadas_salientes(
                        file_bytes=file_bytes,
                        file_name=file_name,
                        file_upload_id=file_upload_id,
                        mission_id=mission_id
                    )
                else:
                    # Detectar automáticamente basado en contenido
                    try:
                        # Leer muestra para detectar estructura
                        if file_name.lower().endswith('.csv'):
                            df_sample = service.file_processor._read_csv_robust(file_bytes[:10000], delimiter=',')
                            if len(df_sample) > 0:
                                columns = df_sample.columns.str.lower().tolist()
                                # Si contiene campos de llamadas MOVISTAR, procesar como llamadas
                                if 'numero_que_contesta' in columns and 'numero_que_marca' in columns:
                                    processing_result = service.file_processor.process_movistar_llamadas_salientes(
                                        file_bytes=file_bytes,
                                        file_name=file_name,
                                        file_upload_id=file_upload_id,
                                        mission_id=mission_id
                                    )
                                else:
                                    # Si no se reconoce la estructura, error
                                    error_msg = 'Estructura de archivo MOVISTAR no reconocida'
                                    service._update_processing_status(
                                        file_upload_id,
                                        'FAILED',
                                        error_msg
                                    )
                                    response = {
                                        'success': False,
                                        'error': error_msg,
                                        'error_code': 'UNRECOGNIZED_STRUCTURE',
                                        'sheetId': file_upload_id,
                                        'processedRecords': 0,
                                        'warnings': [],
                                        'errors': [error_msg]
                                    }
                                    return _ensure_eel_serializable(response)
                            else:
                                error_msg = 'No se pudo leer el archivo MOVISTAR'
                                service._update_processing_status(
                                    file_upload_id,
                                    'FAILED',
                                    error_msg
                                )
                                response = {
                                    'success': False,
                                    'error': error_msg,
                                    'error_code': 'FILE_READ_ERROR',
                                    'sheetId': file_upload_id,
                                    'processedRecords': 0,
                                    'warnings': [],
                                    'errors': [error_msg]
                                }
                                return _ensure_eel_serializable(response)
                        else:
                            # Para XLSX, usar salientes por defecto
                            processing_result = service.file_processor.process_movistar_llamadas_salientes(
                                file_bytes=file_bytes,
                                file_name=file_name,
                                file_upload_id=file_upload_id,
                                mission_id=mission_id
                            )
                    except Exception as detection_error:
                        service.logger.warning(f"Error en detección automática MOVISTAR: {detection_error}")
                        # Fallback: usar salientes por defecto
                        processing_result = service.file_processor.process_movistar_llamadas_salientes(
                            file_bytes=file_bytes,
                            file_name=file_name,
                            file_upload_id=file_upload_id,
                            mission_id=mission_id
                        )
            
            elif operator.upper() == 'TIGO' and file_type == 'CALL_DATA':
                # Procesar datos de llamadas unificadas TIGO
                # TIGO maneja llamadas entrantes y salientes en un solo archivo
                # diferenciadas por el campo DIRECCION ('O' = SALIENTE, 'I' = ENTRANTE)
                processing_result = service.file_processor.process_tigo_llamadas_unificadas(
                    file_bytes=file_bytes,
                    file_name=file_name,
                    file_upload_id=file_upload_id,
                    mission_id=mission_id
                )
            
            elif operator.upper() == 'TIGO' and file_type == 'CELLULAR_DATA':
                # TIGO no maneja datos celulares por separado
                # Todo está incluido en las llamadas unificadas
                service._update_processing_status(
                    file_upload_id,
                    'FAILED', 
                    'TIGO no maneja datos celulares separados. Use CALL_DATA para llamadas unificadas.'
                )
                response = {
                    'success': False,
                    'error': 'TIGO no maneja datos celulares separados. Use CALL_DATA para llamadas unificadas.',
                    'error_code': 'INVALID_FILE_TYPE_FOR_OPERATOR',
                    'sheetId': file_upload_id
                }
                return _ensure_eel_serializable(response)
            
            elif operator.upper() == 'WOM' and file_type == 'CELLULAR_DATA':
                # Procesar datos celulares de WOM
                processing_result = service.file_processor.process_wom_datos_por_celda(
                    file_bytes=file_bytes,
                    file_name=file_name,
                    file_upload_id=file_upload_id,
                    mission_id=mission_id
                )
            
            elif operator.upper() == 'WOM' and file_type == 'CALL_DATA':
                # Procesar datos de llamadas unificadas WOM (entrantes y salientes)
                # WOM maneja llamadas entrantes y salientes en un solo archivo,
                # diferenciadas por el campo SENTIDO ('ENTRANTE'/'SALIENTE')
                processing_result = service.file_processor.process_wom_llamadas_entrantes(
                    file_bytes=file_bytes,
                    file_name=file_name,
                    file_upload_id=file_upload_id,
                    mission_id=mission_id
                )
            
            else:
                # Placeholder para otros operadores/tipos no implementados
                error_msg = f'Procesamiento para {operator} {file_type} no implementado aún'
                service._update_processing_status(
                    file_upload_id, 
                    'FAILED',
                    error_msg
                )
                response = {
                    'success': False,
                    'error': error_msg,
                    'error_code': 'NOT_IMPLEMENTED',
                    'sheetId': file_upload_id,
                    'processedRecords': 0,
                    'warnings': [],
                    'errors': [error_msg]
                }
                return _ensure_eel_serializable(response)
            
            # Evaluar resultado del procesamiento
            if processing_result and processing_result.get('success', False):
                service._update_processing_status(file_upload_id, 'COMPLETED')
                
                service.logger.info(
                    f"Archivo procesado exitosamente: {file_name}",
                    extra={
                        'records_processed': processing_result.get('records_processed', 0),
                        'records_failed': processing_result.get('records_failed', 0)
                    }
                )
                
                # Construir respuesta de éxito
                success_response = {
                    'success': True,
                    'message': 'Archivo procesado exitosamente',
                    'sheetId': file_upload_id,
                    'processedRecords': processing_result.get('records_processed', 0),
                    'warnings': processing_result.get('warnings', []),
                    'errors': processing_result.get('errors', [])
                }
                
                # Asegurar compatibilidad con serialización Eel
                safe_response = _ensure_eel_serializable(success_response)
                service.logger.info(f"SUCCESS RESPONSE STRUCTURE: {safe_response}")
                return safe_response
            
            else:
                error_msg = processing_result.get('error', 'Error desconocido en el procesamiento') if processing_result else 'No se pudo procesar el archivo'
                service._update_processing_status(file_upload_id, 'FAILED', error_msg)
                
                # Construir respuesta de error
                error_response = {
                    'success': False,
                    'error': error_msg,
                    'error_code': 'PROCESSING_FAILED',
                    'sheetId': file_upload_id,
                    'processedRecords': 0,
                    'warnings': [],
                    'errors': [error_msg]
                }
                
                # Asegurar compatibilidad con serialización Eel
                safe_response = _ensure_eel_serializable(error_response)
                service.logger.error(f"ERROR RESPONSE STRUCTURE: {safe_response}")
                return safe_response
        
        except Exception as e:
            # Error durante el procesamiento
            error_msg = f"Error crítico durante procesamiento: {str(e)}"
            service.logger.error(error_msg, exc_info=True)
            
            try:
                service._update_processing_status(file_upload_id, 'FAILED', error_msg)
            except:
                pass  # No fallar si no podemos actualizar el estado
            
            response = {
                'success': False,
                'error': error_msg,
                'error_code': 'CRITICAL_ERROR',
                'sheetId': file_upload_id,
                'processedRecords': 0,
                'warnings': [],
                'errors': [error_msg]
            }
            return _ensure_eel_serializable(response)
    
    except Exception as e:
        # Error crítico antes de crear registro
        service.logger.error(f"Error crítico en upload_operator_data: {str(e)}", exc_info=True)
        error_msg = f"Error crítico del sistema: {str(e)}"
        response = {
            'success': False,
            'error': error_msg,
            'error_code': 'SYSTEM_ERROR',
            'processedRecords': 0,
            'warnings': [],
            'errors': [error_msg]
        }
        return _ensure_eel_serializable(response)


@eel.expose
def get_operator_sheets(mission_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Obtiene la lista de archivos de datos de operadores.
    
    Args:
        mission_id (Optional[str]): ID de misión para filtrar (None = todos)
    
    Returns:
        Dict[str, Any]: Lista de archivos con metadata
    """
    service = OperatorDataService()
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if mission_id:
                # Validar que la misión existe
                if not service._validate_mission_exists(mission_id):
                    return {
                        'success': False,
                        'error': f'La misión {mission_id} no existe',
                        'error_code': 'MISSION_NOT_FOUND'
                    }
                
                cursor.execute("""
                    SELECT 
                        ods.id, ods.mission_id, ods.file_name, ods.file_size_bytes,
                        ods.file_type, ods.operator, ods.operator_file_format,
                        ods.processing_status, ods.records_processed, ods.records_failed,
                        ods.processing_duration_seconds, ods.error_details,
                        ods.uploaded_by, ods.uploaded_at, ods.processing_start_time,
                        ods.processing_end_time,
                        u.name as uploaded_by_username,
                        m.name as mission_name
                    FROM operator_data_sheets ods
                    LEFT JOIN users u ON ods.uploaded_by = u.id
                    LEFT JOIN missions m ON ods.mission_id = m.id
                    WHERE ods.mission_id = ?
                    ORDER BY ods.uploaded_at DESC
                """, (mission_id,))
            
            else:
                cursor.execute("""
                    SELECT 
                        ods.id, ods.mission_id, ods.file_name, ods.file_size_bytes,
                        ods.file_type, ods.operator, ods.operator_file_format,
                        ods.processing_status, ods.records_processed, ods.records_failed,
                        ods.processing_duration_seconds, ods.error_details,
                        ods.uploaded_by, ods.uploaded_at, ods.processing_start_time,
                        ods.processing_end_time,
                        u.name as uploaded_by_username,
                        m.name as mission_name
                    FROM operator_data_sheets ods
                    LEFT JOIN users u ON ods.uploaded_by = u.id
                    LEFT JOIN missions m ON ods.mission_id = m.id
                    ORDER BY ods.uploaded_at DESC
                """)
            
            rows = cursor.fetchall()
            
            # Convertir resultados a formato dictionary
            sheets = []
            for row in rows:
                sheet_data = {
                    'id': row[0],
                    'mission_id': row[1],
                    'file_name': row[2],
                    'file_size_bytes': row[3],
                    'file_type': row[4],
                    'operator': row[5],
                    'operator_file_format': row[6],
                    'processing_status': row[7],
                    'records_processed': row[8] or 0,
                    'records_failed': row[9] or 0,
                    'processing_duration_seconds': row[10],
                    'error_details': row[11],
                    'uploaded_by': row[12],
                    'uploaded_at': row[13],
                    'processing_start_time': row[14],
                    'processing_end_time': row[15],
                    'uploaded_by_username': row[16],
                    'mission_name': row[17],
                    
                    # Campos calculados
                    'file_size_mb': round(row[3] / 1024 / 1024, 2) if row[3] else 0,
                    'success_rate': None
                }
                
                # Calcular tasa de éxito si hay registros procesados
                if row[8] and (row[8] + (row[9] or 0)) > 0:
                    total_records = row[8] + (row[9] or 0)
                    sheet_data['success_rate'] = round((row[8] / total_records) * 100, 1)
                
                sheets.append(sheet_data)
            
            return {
                'success': True,
                'data': sheets,
                'total_count': len(sheets)
            }
    
    except Exception as e:
        service.logger.error(f"Error obteniendo archivos de operadores: {str(e)}")
        return {
            'success': False,
            'error': f"Error obteniendo datos: {str(e)}",
            'error_code': 'QUERY_ERROR'
        }


@eel.expose
def get_operator_sheet_data(file_upload_id: str, page: int = 1, 
                          page_size: int = 50) -> Dict[str, Any]:
    """
    Obtiene los datos procesados de un archivo específico.
    
    Args:
        file_upload_id (str): ID del archivo cargado
        page (int): Número de página (empieza en 1)
        page_size (int): Registros por página (máximo 5000)
    
    Returns:
        Dict[str, Any]: Datos del archivo con paginación
    """
    service = OperatorDataService()
    
    try:
        # Convertir page/page_size a limit/offset
        if page_size > 5000:
            page_size = 5000
        if page < 1:
            page = 1
            
        limit = page_size
        offset = (page - 1) * page_size
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Obtener información del archivo
            cursor.execute("""
                SELECT file_type, operator, file_name, processing_status,
                       records_processed, records_failed
                FROM operator_data_sheets 
                WHERE id = ?
            """, (file_upload_id,))
            
            file_info = cursor.fetchone()
            if not file_info:
                return {
                    'success': False,
                    'error': f'Archivo no encontrado: {file_upload_id}',
                    'error_code': 'FILE_NOT_FOUND'
                }
            
            file_type, operator, file_name = file_info[0], file_info[1], file_info[2]
            processing_status, records_processed, records_failed = file_info[3], file_info[4], file_info[5]
            
            # Definir columnas según operador y tipo de archivo
            column_config = service._get_column_configuration(operator, file_type)
            
            # Obtener datos según el tipo de archivo usando configuración dinámica
            if file_type == 'CELLULAR_DATA':
                # Primero obtener conteo total
                cursor.execute("""
                    SELECT COUNT(*) FROM operator_cellular_data 
                    WHERE file_upload_id = ?
                """, (file_upload_id,))
                total_count = cursor.fetchone()[0]
                
                # Construir query dinámico basado en configuración
                select_query = column_config['select_query'] + """
                    WHERE file_upload_id = ?
                    ORDER BY id ASC
                    LIMIT ? OFFSET ?
                """
                cursor.execute(select_query, (file_upload_id, limit, offset))
                
            elif file_type == 'CALL_DATA':
                # Primero obtener conteo total
                cursor.execute("""
                    SELECT COUNT(*) FROM operator_call_data 
                    WHERE file_upload_id = ?
                """, (file_upload_id,))
                total_count = cursor.fetchone()[0]
                
                # Construir query dinámico basado en configuración
                select_query = column_config['select_query'] + """
                    WHERE file_upload_id = ?
                    ORDER BY id ASC
                    LIMIT ? OFFSET ?
                """
                cursor.execute(select_query, (file_upload_id, limit, offset))
            
            else:
                return {
                    'success': False,
                    'error': f'Tipo de archivo no soportado: {file_type}',
                    'error_code': 'UNSUPPORTED_FILE_TYPE'
                }
            
            # Convertir resultados (ahora el cursor tiene los datos correctos)
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            
            data = []
            for row in rows:
                record = dict(zip(columns, row))
                data.append(record)
            
            return {
                'success': True,
                'data': data,
                'total': total_count,
                'hasMore': (offset + limit) < total_count,
                'columns': column_config['columns'],
                'displayNames': column_config['display_names'],
                'metadata': {
                    'sheetId': file_upload_id,
                    'file_name': file_name,
                    'operator': operator,
                    'file_type': file_type,
                    'processing_status': processing_status,
                    'records_processed': records_processed,
                    'records_failed': records_failed,
                    'page': page,
                    'page_size': page_size,
                    'limit': limit,
                    'offset': offset
                }
            }
    
    except Exception as e:
        service.logger.error(f"Error obteniendo datos del archivo {file_upload_id}: {str(e)}")
        return {
            'success': False,
            'error': f"Error obteniendo datos: {str(e)}",
            'error_code': 'QUERY_ERROR'
        }


@eel.expose
def delete_operator_sheet(file_upload_id: str, user_id: str) -> Dict[str, Any]:
    """
    Elimina un archivo de datos de operador y todos sus datos asociados.
    
    ATENCIÓN: Esta operación es irreversible y eliminará:
    - El registro del archivo en operator_data_sheets
    - Todos los datos celulares/llamadas asociados
    - Los logs de procesamiento
    - Los registros de auditoría
    
    Args:
        file_upload_id (str): ID del archivo a eliminar
        user_id (str): ID del usuario que solicita la eliminación
    
    Returns:
        Dict[str, Any]: Resultado de la eliminación
    """
    service = OperatorDataService()
    
    try:
        # Validar que el usuario existe
        if not service._validate_user_exists(user_id):
            return {
                'success': False,
                'error': f'El usuario {user_id} no existe',
                'error_code': 'USER_NOT_FOUND'
            }
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar que el archivo existe y obtener información
            cursor.execute("""
                SELECT file_name, operator, file_type, processing_status, records_processed
                FROM operator_data_sheets 
                WHERE id = ?
            """, (file_upload_id,))
            
            file_info = cursor.fetchone()
            if not file_info:
                return {
                    'success': False,
                    'error': f'Archivo no encontrado: {file_upload_id}',
                    'error_code': 'FILE_NOT_FOUND'
                }
            
            file_name, operator, file_type, processing_status, records_processed = file_info
            
            # Log de la eliminación antes de ejecutar
            service.logger.warning(
                f"ELIMINACIÓN de archivo: {file_name}",
                extra={
                    'file_upload_id': file_upload_id,
                    'operator': operator,
                    'file_type': file_type,
                    'records_processed': records_processed,
                    'deleted_by': user_id
                }
            )
            
            # Eliminar archivo (CASCADE eliminará datos relacionados)
            cursor.execute("DELETE FROM operator_data_sheets WHERE id = ?", (file_upload_id,))
            
            deleted_count = cursor.rowcount
            if deleted_count == 0:
                return {
                    'success': False,
                    'error': 'No se pudo eliminar el archivo',
                    'error_code': 'DELETE_FAILED'
                }
            
            conn.commit()
            
            service.logger.info(
                f"Archivo eliminado exitosamente: {file_name}",
                extra={'records_affected': records_processed or 0}
            )
            
            return {
                'success': True,
                'message': f'Archivo "{file_name}" eliminado exitosamente',
                'file_name': file_name,
                'records_deleted': records_processed or 0
            }
    
    except Exception as e:
        service.logger.error(f"Error eliminando archivo {file_upload_id}: {str(e)}")
        return {
            'success': False,
            'error': f"Error eliminando archivo: {str(e)}",
            'error_code': 'DELETE_ERROR'
        }


# ==============================================================================
# FUNCIONES DE UTILIDAD PARA TESTING Y MANTENIMIENTO
# ==============================================================================

@eel.expose
def get_operator_statistics(mission_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Obtiene estadísticas consolidadas de los datos de operadores.
    
    Args:
        mission_id (Optional[str]): ID de misión para filtrar (None = todos)
    
    Returns:
        Dict[str, Any]: Estadísticas consolidadas con totales y por operador
    """
    service = OperatorDataService()
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            base_query = """
                SELECT 
                    operator,
                    COUNT(*) as total_files,
                    SUM(records_processed) as total_records,
                    SUM(records_failed) as total_failed,
                    SUM(file_size_bytes) as total_bytes,
                    AVG(processing_duration_seconds) as avg_processing_time,
                    COUNT(CASE WHEN processing_status = 'COMPLETED' THEN 1 END) as completed_files,
                    COUNT(CASE WHEN processing_status = 'FAILED' THEN 1 END) as failed_files
                FROM operator_data_sheets 
            """
            
            if mission_id:
                cursor.execute(base_query + "WHERE mission_id = ? GROUP BY operator", (mission_id,))
            else:
                cursor.execute(base_query + "GROUP BY operator")
            
            stats = {}
            total_stats = {
                'total_files': 0, 'total_records': 0, 'total_failed': 0,
                'total_bytes': 0, 'completed_files': 0, 'failed_files': 0
            }
            
            for row in cursor.fetchall():
                operator = row[0]
                stats[operator] = {
                    'total_files': row[1] or 0,
                    'total_records': row[2] or 0,
                    'total_failed': row[3] or 0,
                    'total_bytes': row[4] or 0,
                    'avg_processing_time': round(row[5], 2) if row[5] else 0,
                    'completed_files': row[6] or 0,
                    'failed_files': row[7] or 0,
                    'success_rate': 0
                }
                
                # Calcular tasa de éxito
                if stats[operator]['total_files'] > 0:
                    stats[operator]['success_rate'] = round(
                        (stats[operator]['completed_files'] / stats[operator]['total_files']) * 100, 1
                    )
                
                # Acumular totales
                for key in total_stats:
                    total_stats[key] += stats[operator][key.replace('avg_', 'total_').replace('success_', 'completed_')]
            
            # Calcular tasa de éxito total
            if total_stats['total_files'] > 0:
                total_stats['success_rate'] = round(
                    (total_stats['completed_files'] / total_stats['total_files']) * 100, 1
                )
            else:
                total_stats['success_rate'] = 0
            
            return {
                'success': True,
                'statistics': stats,
                'totals': total_stats,
                'mission_id': mission_id
            }
    
    except Exception as e:
        service.logger.error(f"Error obteniendo estadísticas: {str(e)}")
        return {
            'success': False,
            'error': f"Error obteniendo estadísticas: {str(e)}"
        }


if __name__ == "__main__":
    # Código de testing básico
    service = OperatorDataService()
    print("OperatorDataService inicializado correctamente")
    
    # Test de estadísticas
    stats = get_operator_statistics()
    print(f"Estadísticas: {stats}")