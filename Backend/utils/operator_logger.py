"""
KRONOS - Sistema de Logging Especializado para Operadores
========================================================

Este módulo proporciona un sistema de logging especializado para el procesamiento
de datos de operadores celulares, con características avanzadas de auditoría,
performance monitoring y integración con la base de datos.

Características principales:
- Logging jerárquico con múltiples niveles
- Integración directa con la tabla file_processing_logs
- Métricas de performance automáticas
- Formateo estructurado para análisis
- Rotación automática de logs
- Contexto de procesamiento por archivo

Niveles de logging:
- DEBUG: Información detallada para desarrollo
- INFO: Eventos normales del sistema
- WARNING: Situaciones que requieren atención
- ERROR: Errores recuperables
- CRITICAL: Errores que requieren intervención inmediata

Autor: Sistema KRONOS
Versión: 1.0.0
"""

import logging
import logging.handlers
import json
import time
import threading
import traceback
import psutil
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys

# Agregar el directorio padre al path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db_connection


class OperatorLoggerFormatter(logging.Formatter):
    """
    Formateador personalizado para logs de operadores con información contextual.
    """
    
    def __init__(self):
        super().__init__()
        self.default_format = (
            "%(asctime)s | %(levelname)-8s | %(name)s | "
            "%(funcName)s:%(lineno)d | %(message)s"
        )
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Formatea el registro de log con información contextual adicional.
        
        Args:
            record (logging.LogRecord): Registro a formatear
            
        Returns:
            str: Log formateado
        """
        # Formatear timestamp en formato ISO
        record.asctime = datetime.fromtimestamp(
            record.created, tz=timezone.utc
        ).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + 'Z'
        
        # Agregar información de contexto si está disponible
        context_info = []
        
        if hasattr(record, 'file_upload_id'):
            context_info.append(f"FileID:{record.file_upload_id[:8]}")
        
        if hasattr(record, 'operator'):
            context_info.append(f"Op:{record.operator}")
        
        if hasattr(record, 'processing_step'):
            context_info.append(f"Step:{record.processing_step}")
        
        if hasattr(record, 'records_processed'):
            context_info.append(f"Proc:{record.records_processed}")
        
        # Agregar contexto al mensaje
        base_message = record.getMessage()
        if context_info:
            context_str = " | ".join(context_info)
            record.msg = f"[{context_str}] {base_message}"
        
        # Usar formato base
        return super().format(record)


class DatabaseLogHandler(logging.Handler):
    """
    Handler personalizado que escribe logs directamente a la base de datos.
    """
    
    def __init__(self, min_level: int = logging.INFO):
        super().__init__(level=min_level)
        self._db_queue = []
        self._db_lock = threading.Lock()
        self._batch_size = 10
        self._flush_interval = 5.0  # segundos
        self._last_flush = time.time()
    
    def emit(self, record: logging.LogRecord) -> None:
        """
        Emite un log a la cola de base de datos.
        
        Args:
            record (logging.LogRecord): Registro a escribir
        """
        try:
            # Crear entrada para la base de datos
            log_entry = {
                'file_upload_id': getattr(record, 'file_upload_id', None),
                'log_level': record.levelname,
                'log_message': record.getMessage(),
                'log_details': self._extract_log_details(record),
                'processing_step': getattr(record, 'processing_step', 'GENERAL'),
                'record_number': getattr(record, 'record_number', None),
                'error_code': getattr(record, 'error_code', None),
                'execution_time_ms': getattr(record, 'execution_time_ms', None),
                'memory_usage_mb': self._get_current_memory_usage(),
                'logged_at': datetime.fromtimestamp(record.created, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Agregar a cola thread-safe
            with self._db_lock:
                self._db_queue.append(log_entry)
                
                # Flush si es necesario
                if (len(self._db_queue) >= self._batch_size or 
                    time.time() - self._last_flush > self._flush_interval or
                    record.levelno >= logging.ERROR):
                    self._flush_to_db()
        
        except Exception:
            # No fallar si no se puede escribir a DB, usar logging estándar como fallback
            pass
    
    def _extract_log_details(self, record: logging.LogRecord) -> Optional[str]:
        """
        Extrae detalles adicionales del registro para almacenar como JSON.
        
        Args:
            record (logging.LogRecord): Registro de log
            
        Returns:
            Optional[str]: JSON con detalles o None
        """
        details = {}
        
        # Agregar información de excepción si existe
        if record.exc_info:
            details['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Agregar atributos personalizados
        custom_attrs = {}
        for attr in dir(record):
            if not attr.startswith('_') and attr not in [
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'lineno', 'funcName', 'created',
                'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'message', 'exc_info', 'exc_text',
                'stack_info', 'getMessage'
            ]:
                try:
                    value = getattr(record, attr)
                    if value is not None and not callable(value):
                        custom_attrs[attr] = value
                except:
                    pass
        
        if custom_attrs:
            details['custom_attributes'] = custom_attrs
        
        # Agregar información del sistema
        details['system_info'] = {
            'thread_id': record.thread,
            'thread_name': record.threadName,
            'process_id': record.process,
            'module': record.module,
            'function': record.funcName,
            'line_number': record.lineno
        }
        
        return json.dumps(details, default=str) if details else None
    
    def _get_current_memory_usage(self) -> float:
        """
        Obtiene el uso actual de memoria en MB.
        
        Returns:
            float: Memoria utilizada en MB
        """
        try:
            process = psutil.Process()
            return round(process.memory_info().rss / 1024 / 1024, 2)
        except:
            return 0.0
    
    def _flush_to_db(self) -> None:
        """
        Escribe los logs acumulados a la base de datos.
        """
        if not self._db_queue:
            return
        
        entries_to_write = self._db_queue[:]
        self._db_queue.clear()
        self._last_flush = time.time()
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                for entry in entries_to_write:
                    # Solo escribir si tenemos file_upload_id (logs de procesamiento)
                    if entry['file_upload_id']:
                        cursor.execute("""
                            INSERT INTO file_processing_logs (
                                file_upload_id, log_level, log_message, log_details,
                                processing_step, record_number, error_code,
                                execution_time_ms, memory_usage_mb, logged_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            entry['file_upload_id'],
                            entry['log_level'],
                            entry['log_message'],
                            entry['log_details'],
                            entry['processing_step'],
                            entry['record_number'],
                            entry['error_code'],
                            entry['execution_time_ms'],
                            entry['memory_usage_mb'],
                            entry['logged_at']
                        ))
                
                conn.commit()
        
        except Exception as e:
            # Si falla escribir a DB, no hacer nada (logs van a archivo)
            pass
    
    def flush(self) -> None:
        """Forza el flush de logs pendientes."""
        with self._db_lock:
            self._flush_to_db()
    
    def close(self) -> None:
        """Cierra el handler y hace flush final."""
        self.flush()
        super().close()


class OperatorLogger:
    """
    Logger especializado para operaciones de procesamiento de datos de operadores.
    
    Proporciona logging tanto a archivos como a base de datos, con contexto
    específico para cada operación de procesamiento.
    """
    
    def __init__(self, name: str = 'operator_processor'):
        """
        Inicializa el logger con configuración especializada.
        
        Args:
            name (str): Nombre del logger
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Inicializar contexto de procesamiento
        self._current_context = {}
        
        # Evitar configuración duplicada
        if self.logger.handlers:
            return
        
        # Crear directorio de logs si no existe
        self.log_dir = Path('logs')
        self.log_dir.mkdir(exist_ok=True)
        
        # Configurar handlers
        self._setup_file_handler()
        self._setup_console_handler()
        self._setup_database_handler()
        
        self.info("OperatorLogger inicializado correctamente")
    
    def _setup_file_handler(self) -> None:
        """Configura el handler para archivos con rotación."""
        log_file = self.log_dir / 'operator_processing.log'
        
        # Handler con rotación automática
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB por archivo
            backupCount=5,  # Mantener 5 archivos de respaldo
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(OperatorLoggerFormatter())
        
        self.logger.addHandler(file_handler)
    
    def _setup_console_handler(self) -> None:
        """Configura el handler para salida de consola."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)  # Solo INFO+ en consola
        console_handler.setFormatter(OperatorLoggerFormatter())
        
        self.logger.addHandler(console_handler)
    
    def _setup_database_handler(self) -> None:
        """Configura el handler para base de datos."""
        try:
            db_handler = DatabaseLogHandler(min_level=logging.INFO)
            self.logger.addHandler(db_handler)
        except Exception as e:
            self.logger.warning(f"No se pudo configurar DatabaseLogHandler: {e}")
    
    def set_context(self, **kwargs) -> None:
        """
        Establece el contexto actual para todos los logs siguientes.
        
        Args:
            **kwargs: Pares clave-valor del contexto
        """
        self._current_context.update(kwargs)
    
    def clear_context(self) -> None:
        """Limpia el contexto actual."""
        self._current_context.clear()
    
    def _log_with_context(self, level: int, message: str, **kwargs) -> None:
        """
        Registra un mensaje con contexto adicional.
        
        Args:
            level (int): Nivel de logging
            message (str): Mensaje a registrar
            **kwargs: Información contextual adicional
        """
        # Combinar contexto actual con kwargs
        full_context = {**self._current_context, **kwargs}
        
        # Extraer exc_info antes de crear extra
        exc_info = full_context.pop('exc_info', False)
        
        # Crear registro con información extra
        extra = {
            'execution_time_ms': full_context.pop('execution_time_ms', None),
            'memory_usage_mb': full_context.pop('memory_usage_mb', None),
            'error_code': full_context.pop('error_code', None),
            **full_context
        }
        
        # Llamar al logger con exc_info como parámetro separado
        self.logger.log(level, message, extra=extra, exc_info=exc_info)
    
    def debug(self, message: str, **kwargs) -> None:
        """
        Registra un mensaje de DEBUG.
        
        Args:
            message (str): Mensaje a registrar
            **kwargs: Contexto adicional
        """
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """
        Registra un mensaje de INFO.
        
        Args:
            message (str): Mensaje a registrar
            **kwargs: Contexto adicional
        """
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """
        Registra un mensaje de WARNING.
        
        Args:
            message (str): Mensaje a registrar
            **kwargs: Contexto adicional
        """
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """
        Registra un mensaje de ERROR.
        
        Args:
            message (str): Mensaje a registrar
            exc_info (bool): Incluir información de excepción
            **kwargs: Contexto adicional
        """
        if exc_info:
            kwargs['exc_info'] = True
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """
        Registra un mensaje de CRITICAL.
        
        Args:
            message (str): Mensaje a registrar
            exc_info (bool): Incluir información de excepción
            **kwargs: Contexto adicional
        """
        if exc_info:
            kwargs['exc_info'] = True
        self._log_with_context(logging.CRITICAL, message, **kwargs)
    
    def log_processing_start(self, file_name: str, file_upload_id: str, 
                           operator: str, file_size: int) -> None:
        """
        Registra el inicio de procesamiento de un archivo.
        
        Args:
            file_name (str): Nombre del archivo
            file_upload_id (str): ID único del archivo
            operator (str): Operador celular
            file_size (int): Tamaño del archivo en bytes
        """
        self.set_context(
            file_upload_id=file_upload_id,
            operator=operator,
            processing_step='START'
        )
        
        self.info(
            f"Iniciando procesamiento de archivo: {file_name}",
            extra={
                'file_name': file_name,
                'file_size_bytes': file_size,
                'file_size_mb': round(file_size / 1024 / 1024, 2)
            }
        )
    
    def log_processing_progress(self, processed: int, failed: int, 
                              total: Optional[int] = None) -> None:
        """
        Registra el progreso del procesamiento.
        
        Args:
            processed (int): Registros procesados exitosamente
            failed (int): Registros que fallaron
            total (Optional[int]): Total de registros (si se conoce)
        """
        progress_msg = f"Progreso: {processed} procesados, {failed} fallidos"
        if total:
            progress_msg += f" de {total} ({(processed/total)*100:.1f}%)"
        
        self.info(
            progress_msg,
            extra={
                'records_processed': processed,
                'records_failed': failed,
                'total_records': total,
                'processing_step': 'PROGRESS'
            }
        )
    
    def log_processing_end(self, success: bool, total_processed: int, 
                         total_failed: int, processing_time: float) -> None:
        """
        Registra el fin del procesamiento de un archivo.
        
        Args:
            success (bool): Si el procesamiento fue exitoso
            total_processed (int): Total de registros procesados
            total_failed (int): Total de registros fallidos
            processing_time (float): Tiempo de procesamiento en segundos
        """
        status = "COMPLETADO" if success else "FALLIDO"
        success_rate = (total_processed / (total_processed + total_failed)) * 100 if (total_processed + total_failed) > 0 else 0
        
        log_method = self.info if success else self.error
        log_method(
            f"Procesamiento {status}: {total_processed} exitosos, {total_failed} fallidos ({success_rate:.1f}% éxito) en {processing_time:.2f}s",
            extra={
                'records_processed': total_processed,
                'records_failed': total_failed,
                'success_rate': success_rate,
                'processing_time_seconds': processing_time,
                'processing_step': 'END',
                'execution_time_ms': int(processing_time * 1000)
            }
        )
        
        # Limpiar contexto al final
        self.clear_context()
    
    def log_validation_error(self, record_number: int, errors: List[str], 
                           record_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Registra errores de validación de un registro específico.
        
        Args:
            record_number (int): Número del registro con error
            errors (List[str]): Lista de errores encontrados
            record_data (Optional[Dict[str, Any]]): Datos del registro (opcional)
        """
        self.warning(
            f"Error de validación en registro {record_number}: {'; '.join(errors)}",
            extra={
                'record_number': record_number,
                'validation_errors': errors,
                'record_data': json.dumps(record_data, default=str) if record_data else None,
                'processing_step': 'VALIDATION',
                'error_code': 'VALIDATION_ERROR'
            }
        )
    
    def log_database_operation(self, operation: str, records_affected: int, 
                             execution_time: float) -> None:
        """
        Registra operaciones de base de datos.
        
        Args:
            operation (str): Tipo de operación (INSERT, UPDATE, DELETE)
            records_affected (int): Número de registros afectados
            execution_time (float): Tiempo de ejecución en segundos
        """
        self.debug(
            f"Operación DB {operation}: {records_affected} registros en {execution_time:.3f}s",
            extra={
                'db_operation': operation,
                'records_affected': records_affected,
                'execution_time_ms': int(execution_time * 1000),
                'processing_step': 'DATABASE'
            }
        )
    
    def flush_logs(self) -> None:
        """Fuerza el flush de todos los handlers."""
        for handler in self.logger.handlers:
            if hasattr(handler, 'flush'):
                handler.flush()


# ==============================================================================
# UTILIDADES DE LOGGING
# ==============================================================================

class LoggingContext:
    """Context manager para logging con contexto automático."""
    
    def __init__(self, logger: OperatorLogger, **context):
        self.logger = logger
        self.context = context
        self.start_time = None
    
    def __enter__(self) -> OperatorLogger:
        self.logger.set_context(**self.context)
        self.start_time = time.time()
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            execution_time = time.time() - self.start_time
            self.logger.set_context(execution_time_ms=int(execution_time * 1000))
        
        if exc_type:
            self.logger.error(
                f"Excepción en contexto: {exc_val}",
                exc_info=True,
                error_code=exc_type.__name__
            )
        
        self.logger.clear_context()


def get_performance_metrics() -> Dict[str, Any]:
    """
    Obtiene métricas de performance del sistema.
    
    Returns:
        Dict[str, Any]: Métricas del sistema
    """
    try:
        process = psutil.Process()
        
        return {
            'memory_usage_mb': round(process.memory_info().rss / 1024 / 1024, 2),
            'cpu_percent': process.cpu_percent(),
            'open_files': len(process.open_files()),
            'threads': process.num_threads(),
            'uptime_seconds': time.time() - process.create_time()
        }
    except:
        return {}


if __name__ == "__main__":
    # Código de testing básico
    logger = OperatorLogger('test')
    
    # Test de contexto
    with LoggingContext(logger, file_upload_id='test-123', operator='CLARO'):
        logger.info("Mensaje de prueba con contexto")
        time.sleep(0.1)  # Simular trabajo
    
    # Test de diferentes niveles
    logger.debug("Mensaje debug")
    logger.info("Mensaje info")
    logger.warning("Mensaje warning")
    logger.error("Mensaje error")
    
    # Test de métricas
    metrics = get_performance_metrics()
    logger.info(f"Métricas del sistema: {metrics}")
    
    # Flush final
    logger.flush_logs()
    
    print("OperatorLogger testing completado")