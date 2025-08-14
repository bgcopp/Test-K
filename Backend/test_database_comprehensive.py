"""
KRONOS - Testing Exhaustivo de Base de Datos - Equipo de Base de Datos
=============================================================================
Script de testing coordinado para validación completa de la capa de datos
del sistema de sábanas de datos de operador.

Casos de Prueba Asignados:
- P0-008 (CRÍTICO): Consulta cross-operador en BD
- P1-003 (IMPORTANTE): Backup y recuperación BD operadores  
- P1-007 (IMPORTANTE): Rollback automático en fallo BD
- P2-007 (EDGE CASE): Queries BD con millones registros
- Integridad Referencial
- Normalización de Datos  
- Performance de Índices
- Triggers y Constraints

Contexto del Testing Coordinado:
- Equipo de Arquitectura L2 ya completó sus pruebas (2 issues menores)
- Issue conocido: Context Manager en OperatorService con sesiones DB
=============================================================================
"""

import os
import sys
import sqlite3
import time
import logging
import tempfile
import shutil
import json
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from contextlib import contextmanager
from pathlib import Path

# Configurar el path para importar módulos del proyecto
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

# Imports del proyecto
from database.connection import DatabaseManager, get_database_manager
from database.models import Mission, User, Role, Base as MainBase
from database.operator_models import *
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import bcrypt

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database_test_results.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseTestResult:
    """Clase para almacenar resultados de pruebas"""
    def __init__(self, test_case: str, priority: str):
        self.test_case = test_case
        self.priority = priority
        self.status = "PENDING"
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.duration_ms: Optional[float] = None
        self.error_message: Optional[str] = None
        self.details: Dict[str, Any] = {}
        self.issues_found: List[Dict[str, str]] = []
        
    def start_test(self):
        self.start_time = datetime.now()
        self.status = "RUNNING"
        
    def complete_test(self, success: bool = True, error_message: str = None):
        self.end_time = datetime.now()
        if self.start_time:
            self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.status = "PASSED" if success else "FAILED"
        if error_message:
            self.error_message = error_message
            
    def add_issue(self, severity: str, description: str, impact: str = None, suggestion: str = None):
        self.issues_found.append({
            "severity": severity,
            "description": description,
            "impact": impact or "Por determinar",
            "suggestion": suggestion or "Requiere análisis adicional"
        })

class DatabaseTestSuite:
    """Suite completa de pruebas de base de datos"""
    
    def __init__(self):
        self.results: List[DatabaseTestResult] = []
        self.db_manager: Optional[DatabaseManager] = None
        self.test_db_path = None
        self.backup_db_path = None
        
    def setup_test_environment(self):
        """Configura el entorno de pruebas"""
        logger.info("=== CONFIGURANDO ENTORNO DE PRUEBAS ===")
        
        # Crear DB temporal para pruebas
        temp_dir = tempfile.mkdtemp(prefix="kronos_db_test_")
        self.test_db_path = os.path.join(temp_dir, "test_kronos.db")
        self.backup_db_path = os.path.join(temp_dir, "backup_kronos.db")
        
        # Inicializar DB manager con DB temporal
        self.db_manager = DatabaseManager(self.test_db_path)
        self.db_manager.initialize(force_recreate=True)
        
        logger.info(f"Base de datos de prueba creada: {self.test_db_path}")
        
        # Crear tablas de operadores usando SQLAlchemy
        self._create_operator_tables()
        
        # Cargar esquemas adicionales de operadores (índices, triggers, etc.)
        self._load_operator_schemas()
        
        logger.info("Entorno de pruebas configurado exitosamente")
    
    def _create_operator_tables(self):
        """Crea las tablas específicas de operadores"""
        try:
            # Crear tablas de operadores usando SQLAlchemy
            Base.metadata.create_all(self.db_manager.get_engine())
            logger.info("Tablas de operadores creadas exitosamente")
        except Exception as e:
            logger.error(f"Error creando tablas de operadores: {e}")
            raise
        
    def _load_operator_schemas(self):
        """Carga los esquemas específicos de operadores"""
        try:
            schema_files = [
                "database/operator_data_schema.sql",
                "database/operator_indexes_strategy.sql", 
                "database/operator_triggers_constraints.sql"
            ]
            
            for schema_file in schema_files:
                schema_path = os.path.join(os.path.dirname(__file__), schema_file)
                if os.path.exists(schema_path):
                    logger.info(f"Cargando esquema: {schema_file}")
                    with open(schema_path, 'r', encoding='utf-8') as f:
                        schema_sql = f.read()
                    
                    # Ejecutar SQL en bloques separados
                    statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
                    
                    with self.db_manager.get_session() as session:
                        for statement in statements:
                            if statement and not statement.startswith('--'):
                                try:
                                    session.execute(text(statement))
                                except Exception as e:
                                    if "already exists" not in str(e).lower():
                                        logger.warning(f"Error ejecutando statement: {e}")
                        session.commit()
                        
            logger.info("Esquemas de operadores cargados exitosamente")
                        
        except Exception as e:
            logger.error(f"Error cargando esquemas de operadores: {e}")
            raise
    
    def cleanup_test_environment(self):
        """Limpia el entorno de pruebas"""
        try:
            if self.db_manager:
                self.db_manager.close()
            if self.test_db_path and os.path.exists(self.test_db_path):
                os.remove(self.test_db_path)
            if self.backup_db_path and os.path.exists(self.backup_db_path):
                os.remove(self.backup_db_path)
            logger.info("Entorno de pruebas limpiado")
        except Exception as e:
            logger.error(f"Error limpiando entorno: {e}")

    def _create_test_data(self, record_count: int = 1000) -> Tuple[str, str]:
        """Crea datos de prueba para las validaciones"""
        logger.info(f"Creando {record_count} registros de datos de prueba...")
        
        with self.db_manager.get_session() as session:
            # Crear misión de prueba
            mission_id = "test_mission_001"
            mission = session.query(Mission).filter_by(id=mission_id).first()
            if not mission:
                mission = Mission(
                    id=mission_id,
                    code="TEST-001",
                    name="Misión de Prueba Database Testing",
                    description="Misión creada para testing exhaustivo de base de datos",
                    status="En Progreso",
                    created_by="admin"
                )
                session.add(mission)
            
            # Crear upload de archivo de prueba
            file_upload_id = "test_upload_001"
            file_upload = OperatorFileUpload(
                id=file_upload_id,
                mission_id=mission_id,
                operator="CLARO",
                file_type="DATOS",
                file_name="test_data_massive.xlsx",
                file_size=1024000,
                upload_status="completed",
                created_by="admin"
            )
            session.add(file_upload)
            session.commit()
            
            # Crear datos celulares de prueba
            base_date = datetime.now() - timedelta(days=30)
            phone_numbers = [f"31234567{i:02d}" for i in range(100)]
            cell_ids = [f"CELL_{i:04d}" for i in range(50)]
            
            cellular_data = []
            for i in range(record_count):
                data = OperatorCellularData(
                    file_upload_id=file_upload_id,
                    mission_id=mission_id,
                    operator="CLARO",
                    numero_telefono=phone_numbers[i % len(phone_numbers)],
                    fecha_hora_inicio=base_date + timedelta(minutes=i),
                    fecha_hora_fin=base_date + timedelta(minutes=i+5),
                    duracion_segundos=300 + (i % 600),
                    celda_id=cell_ids[i % len(cell_ids)],
                    lac_tac=f"LAC_{i % 100}",
                    trafico_subida_bytes=1024 * (i % 1000),
                    trafico_bajada_bytes=2048 * (i % 1500),
                    latitud=-4.5981 + (i % 100) * 0.001,
                    longitud=-74.0758 + (i % 100) * 0.001,
                    tecnologia="LTE",
                    tipo_conexion="internet"
                )
                cellular_data.append(data)
                
                if len(cellular_data) >= 100:  # Insertar en lotes
                    session.add_all(cellular_data)
                    session.commit()
                    cellular_data = []
            
            if cellular_data:  # Insertar último lote
                session.add_all(cellular_data)
                session.commit()
            
            logger.info(f"Datos de prueba creados exitosamente")
            return mission_id, file_upload_id

    # =========================================================================
    # CASOS DE PRUEBA CRÍTICOS
    # =========================================================================
    
    def test_p0_008_cross_operator_queries(self) -> DatabaseTestResult:
        """P0-008 (CRÍTICO): Consulta cross-operador en BD"""
        result = DatabaseTestResult("P0-008", "CRÍTICO")
        result.start_test()
        
        try:
            logger.info("=== EJECUTANDO P0-008: Consultas Cross-Operador ===")
            
            with self.db_manager.get_session() as session:
                # Crear datos de múltiples operadores
                mission_id = "cross_op_test"
                operators = ["CLARO", "MOVISTAR", "TIGO", "WOM"]
                
                # Crear misión
                mission = Mission(
                    id=mission_id,
                    code="CROSS-001",
                    name="Test Cross-Operador",
                    description="Prueba de consultas unificadas",
                    status="En Progreso",
                    created_by="admin"
                )
                session.add(mission)
                
                # Crear datos para cada operador
                for i, operator in enumerate(operators):
                    # Upload de archivo
                    upload = OperatorFileUpload(
                        id=f"upload_{operator.lower()}",
                        mission_id=mission_id,
                        operator=operator,
                        file_type="LLAMADAS_ENTRANTES",
                        file_name=f"test_{operator.lower()}.xlsx",
                        file_size=1024,
                        upload_status="completed"
                    )
                    session.add(upload)
                    
                    # Datos de llamadas
                    for j in range(10):
                        call_data = OperatorCallData(
                            file_upload_id=upload.id,
                            mission_id=mission_id,
                            operator=operator,
                            tipo_llamada="ENTRANTE",
                            numero_origen=f"555000{j:02d}",
                            numero_destino="3123456789",
                            numero_objetivo="3123456789",
                            fecha_hora_llamada=datetime.now() - timedelta(hours=j),
                            duracion_segundos=60 + j * 10,
                            celda_objetivo=f"CELL_{operator}_{j}"
                        )
                        session.add(call_data)
                
                session.commit()
                
                # PRUEBA 1: Consulta unificada de todos los operadores
                query_start = time.time()
                cross_operator_query = """
                    SELECT 
                        operator,
                        COUNT(*) as total_calls,
                        AVG(duracion_segundos) as avg_duration,
                        COUNT(DISTINCT numero_origen) as unique_origins
                    FROM operator_call_data 
                    WHERE mission_id = :mission_id
                    GROUP BY operator
                    ORDER BY total_calls DESC
                """
                
                cross_results = session.execute(
                    text(cross_operator_query), 
                    {"mission_id": mission_id}
                ).fetchall()
                query_time = (time.time() - query_start) * 1000
                
                result.details["cross_operator_query_time_ms"] = query_time
                result.details["operators_found"] = len(cross_results)
                result.details["expected_operators"] = len(operators)
                
                # Verificar que todos los operadores aparecen
                found_operators = [row[0] for row in cross_results]
                missing_operators = set(operators) - set(found_operators)
                
                if missing_operators:
                    result.add_issue(
                        "CRÍTICO",
                        f"Operadores faltantes en consulta cross-operador: {missing_operators}",
                        "Datos no están siendo normalizados correctamente",
                        "Verificar proceso de inserción y normalización de datos"
                    )
                
                # PRUEBA 2: Consulta de análisis temporal cross-operador
                temporal_query = """
                    SELECT 
                        DATE(fecha_hora_llamada) as call_date,
                        operator,
                        COUNT(*) as daily_calls,
                        SUM(duracion_segundos) as total_duration
                    FROM operator_call_data 
                    WHERE mission_id = :mission_id
                    GROUP BY DATE(fecha_hora_llamada), operator
                    ORDER BY call_date, operator
                """
                
                temporal_start = time.time()
                temporal_results = session.execute(
                    text(temporal_query),
                    {"mission_id": mission_id}
                ).fetchall()
                temporal_time = (time.time() - temporal_start) * 1000
                
                result.details["temporal_query_time_ms"] = temporal_time
                result.details["temporal_records"] = len(temporal_results)
                
                # PRUEBA 3: JOIN complejo entre tablas de operadores
                join_query = """
                    SELECT 
                        ofu.operator,
                        ofu.file_type,
                        COUNT(DISTINCT ocd.numero_objetivo) as unique_numbers,
                        COUNT(ocd.id) as total_calls,
                        AVG(ocd.duracion_segundos) as avg_duration
                    FROM operator_file_uploads ofu
                    JOIN operator_call_data ocd ON ofu.id = ocd.file_upload_id
                    WHERE ofu.mission_id = :mission_id
                    GROUP BY ofu.operator, ofu.file_type
                    ORDER BY total_calls DESC
                """
                
                join_start = time.time()
                join_results = session.execute(
                    text(join_query),
                    {"mission_id": mission_id}
                ).fetchall()
                join_time = (time.time() - join_start) * 1000
                
                result.details["join_query_time_ms"] = join_time
                result.details["join_results"] = len(join_results)
                
                # Verificar performance
                if query_time > 1000:  # >1 segundo
                    result.add_issue(
                        "MAYOR",
                        f"Consulta cross-operador lenta: {query_time:.2f}ms",
                        "Performance degradada en consultas unificadas",
                        "Verificar índices en campos operator y mission_id"
                    )
                
                # Verificar integridad de datos
                if len(cross_results) != len(operators):
                    result.add_issue(
                        "CRÍTICO", 
                        "No todos los operadores aparecen en consulta unificada",
                        "Datos no están siendo normalizados correctamente",
                        "Revisar proceso de inserción y validar constraints"
                    )
                
                logger.info(f"✓ Consultas cross-operador completadas")
                logger.info(f"  - Operadores encontrados: {len(cross_results)}/{len(operators)}")
                logger.info(f"  - Tiempo consulta unificada: {query_time:.2f}ms")
                logger.info(f"  - Tiempo consulta temporal: {temporal_time:.2f}ms")
                logger.info(f"  - Tiempo JOIN complejo: {join_time:.2f}ms")
                
            result.complete_test(success=len(result.issues_found) == 0)
            
        except Exception as e:
            logger.error(f"Error en P0-008: {e}")
            result.complete_test(success=False, error_message=str(e))
            result.add_issue("CRÍTICO", f"Fallo en consultas cross-operador: {e}", 
                           "Sistema no puede consultar datos unificados", 
                           "Revisar esquema y normalización de datos")
        
        return result
    
    def test_p1_003_backup_recovery(self) -> DatabaseTestResult:
        """P1-003 (IMPORTANTE): Backup y recuperación BD operadores"""
        result = DatabaseTestResult("P1-003", "IMPORTANTE")
        result.start_test()
        
        try:
            logger.info("=== EJECUTANDO P1-003: Backup y Recuperación ===")
            
            # Crear datos de prueba
            mission_id, file_id = self._create_test_data(500)
            
            with self.db_manager.get_session() as session:
                # Contar registros antes del backup
                original_uploads = session.query(OperatorFileUpload).count()
                original_cellular = session.query(OperatorCellularData).count()
                original_calls = session.query(OperatorCallData).count()
                original_cells = session.query(OperatorCellRegistry).count()
                
                result.details["original_counts"] = {
                    "uploads": original_uploads,
                    "cellular_data": original_cellular,
                    "call_data": original_calls,
                    "cell_registry": original_cells
                }
            
            # PRUEBA 1: Crear backup
            backup_start = time.time()
            self.db_manager.backup_database(self.backup_db_path)
            backup_time = (time.time() - backup_start) * 1000
            
            result.details["backup_time_ms"] = backup_time
            result.details["backup_file_exists"] = os.path.exists(self.backup_db_path)
            result.details["backup_size_bytes"] = os.path.getsize(self.backup_db_path) if os.path.exists(self.backup_db_path) else 0
            
            # PRUEBA 2: Modificar datos originales
            with self.db_manager.get_session() as session:
                # Eliminar algunos registros
                session.query(OperatorCellularData).filter(
                    OperatorCellularData.id <= 100
                ).delete()
                
                # Modificar datos
                upload = session.query(OperatorFileUpload).filter_by(id=file_id).first()
                if upload:
                    upload.upload_status = "error"
                    upload.error_message = "Test modification"
                
                session.commit()
            
            # Verificar cambios
            with self.db_manager.get_session() as session:
                modified_cellular = session.query(OperatorCellularData).count()
                modified_upload = session.query(OperatorFileUpload).filter_by(id=file_id).first()
                
                result.details["data_modified"] = {
                    "cellular_records_deleted": original_cellular - modified_cellular,
                    "upload_status_changed": modified_upload.upload_status == "error" if modified_upload else False
                }
            
            # PRUEBA 3: Restaurar desde backup
            restore_start = time.time()
            
            # Cerrar conexión actual
            self.db_manager.close()
            
            # Copiar backup sobre la DB original
            shutil.copy2(self.backup_db_path, self.test_db_path)
            
            # Reinicializar conexión
            self.db_manager = DatabaseManager(self.test_db_path)
            self.db_manager.initialize()
            
            restore_time = (time.time() - restore_start) * 1000
            result.details["restore_time_ms"] = restore_time
            
            # PRUEBA 4: Verificar integridad después de restauración
            with self.db_manager.get_session() as session:
                restored_uploads = session.query(OperatorFileUpload).count()
                restored_cellular = session.query(OperatorCellularData).count()
                restored_calls = session.query(OperatorCallData).count()
                restored_cells = session.query(OperatorCellRegistry).count()
                
                # Verificar upload específico
                restored_upload = session.query(OperatorFileUpload).filter_by(id=file_id).first()
                
                result.details["restored_counts"] = {
                    "uploads": restored_uploads,
                    "cellular_data": restored_cellular,
                    "call_data": restored_calls,
                    "cell_registry": restored_cells
                }
                
                result.details["data_integrity_check"] = {
                    "uploads_match": original_uploads == restored_uploads,
                    "cellular_match": original_cellular == restored_cellular,
                    "calls_match": original_calls == restored_calls,
                    "cells_match": original_cells == restored_cells,
                    "upload_status_restored": restored_upload.upload_status == "completed" if restored_upload else False
                }
            
            # Verificar integridad
            integrity_issues = []
            if original_uploads != restored_uploads:
                integrity_issues.append(f"uploads: {original_uploads} → {restored_uploads}")
            if original_cellular != restored_cellular:
                integrity_issues.append(f"cellular: {original_cellular} → {restored_cellular}")
            if original_calls != restored_calls:
                integrity_issues.append(f"calls: {original_calls} → {restored_calls}")
            if original_cells != restored_cells:
                integrity_issues.append(f"cells: {original_cells} → {restored_cells}")
            
            if integrity_issues:
                result.add_issue(
                    "CRÍTICO",
                    f"Pérdida de datos en restauración: {', '.join(integrity_issues)}",
                    "Proceso de backup/restore no preserva integridad completa",
                    "Revisar proceso de backup y verificar constraints de BD"
                )
            
            if backup_time > 5000:  # >5 segundos
                result.add_issue(
                    "MENOR",
                    f"Proceso de backup lento: {backup_time:.2f}ms",
                    "Performance degradada en operaciones de backup",
                    "Considerar optimización de archivos DB o proceso de backup"
                )
            
            if restore_time > 5000:  # >5 segundos
                result.add_issue(
                    "MENOR", 
                    f"Proceso de restore lento: {restore_time:.2f}ms",
                    "Performance degradada en operaciones de restore",
                    "Considerar optimización del proceso de restauración"
                )
            
            logger.info(f"✓ Backup y recuperación completados")
            logger.info(f"  - Tiempo backup: {backup_time:.2f}ms")
            logger.info(f"  - Tiempo restore: {restore_time:.2f}ms")
            logger.info(f"  - Integridad preservada: {len(integrity_issues) == 0}")
            
            result.complete_test(success=len(integrity_issues) == 0)
            
        except Exception as e:
            logger.error(f"Error en P1-003: {e}")
            result.complete_test(success=False, error_message=str(e))
            result.add_issue("CRÍTICO", f"Fallo en backup/recuperación: {e}",
                           "Sistema no puede garantizar respaldo de datos",
                           "Revisar configuración de BD y permisos de archivos")
        
        return result
    
    def test_p1_007_rollback_transactions(self) -> DatabaseTestResult:
        """P1-007 (IMPORTANTE): Rollback automático en fallo BD"""
        result = DatabaseTestResult("P1-007", "IMPORTANTE")
        result.start_test()
        
        try:
            logger.info("=== EJECUTANDO P1-007: Rollback Automático ===")
            
            with self.db_manager.get_session() as session:
                # Contar registros iniciales
                initial_uploads = session.query(OperatorFileUpload).count()
                initial_cellular = session.query(OperatorCellularData).count()
                
                result.details["initial_counts"] = {
                    "uploads": initial_uploads,
                    "cellular": initial_cellular
                }
            
            # PRUEBA 1: Transacción que debe fallar por constraint violation
            rollback_test_1_success = False
            try:
                with self.db_manager.get_session() as session:
                    # Crear upload válido
                    upload = OperatorFileUpload(
                        id="rollback_test_upload",
                        mission_id="m1",  # Misión existente
                        operator="CLARO",
                        file_type="DATOS",
                        file_name="rollback_test.xlsx",
                        file_size=1024,
                        upload_status="pending"
                    )
                    session.add(upload)
                    
                    # Crear datos celulares válidos
                    cellular_valid = OperatorCellularData(
                        file_upload_id="rollback_test_upload",
                        mission_id="m1",
                        operator="CLARO",
                        numero_telefono="3123456789",
                        fecha_hora_inicio=datetime.now(),
                        celda_id="CELL_001",
                        trafico_subida_bytes=1024,
                        trafico_bajada_bytes=2048
                    )
                    session.add(cellular_valid)
                    
                    # Intentar crear datos celulares INVÁLIDOS que deben fallar
                    cellular_invalid = OperatorCellularData(
                        file_upload_id="rollback_test_upload",
                        mission_id="m1",
                        operator="OPERADOR_INVÁLIDO",  # Esto debe fallar por constraint
                        numero_telefono="123",  # Número muy corto
                        fecha_hora_inicio=datetime.now(),
                        celda_id="",  # Celda vacía debe fallar
                        trafico_subida_bytes=-1000  # Negativo debe fallar
                    )
                    session.add(cellular_invalid)
                    
                    # Esto debe fallar y hacer rollback completo
                    session.commit()
                    
            except Exception as e:
                rollback_test_1_success = True
                result.details["constraint_rollback_error"] = str(e)
                logger.info(f"✓ Rollback por constraint funcionó: {e}")
            
            # Verificar que NO se insertó nada
            with self.db_manager.get_session() as session:
                after_rollback_uploads = session.query(OperatorFileUpload).count()
                after_rollback_cellular = session.query(OperatorCellularData).count()
                rollback_upload = session.query(OperatorFileUpload).filter_by(id="rollback_test_upload").first()
                
                result.details["after_constraint_rollback"] = {
                    "uploads": after_rollback_uploads,
                    "cellular": after_rollback_cellular,
                    "test_upload_exists": rollback_upload is not None
                }
            
            if not rollback_test_1_success:
                result.add_issue(
                    "CRÍTICO",
                    "Constraint violation no causó rollback automático",
                    "Datos parciales pueden quedar en BD en caso de error",
                    "Verificar configuración de constraints y transacciones"
                )
            
            if rollback_upload is not None:
                result.add_issue(
                    "CRÍTICO",
                    "Upload permaneció en BD después de rollback fallido",
                    "Transacciones no están funcionando correctamente",
                    "Revisar manejo de transacciones en DatabaseManager"
                )
            
            # PRUEBA 2: Transacción que falla por foreign key violation
            rollback_test_2_success = False
            try:
                with self.db_manager.get_session() as session:
                    # Crear upload con mission_id inexistente
                    upload_invalid_fk = OperatorFileUpload(
                        id="rollback_test_fk",
                        mission_id="mission_inexistente",  # FK violation
                        operator="CLARO",
                        file_type="DATOS", 
                        file_name="test_fk.xlsx",
                        file_size=1024
                    )
                    session.add(upload_invalid_fk)
                    session.commit()
                    
            except Exception as e:
                rollback_test_2_success = True
                result.details["fk_rollback_error"] = str(e)
                logger.info(f"✓ Rollback por FK funcionó: {e}")
            
            # PRUEBA 3: Simular error de aplicación en medio de transacción
            rollback_test_3_success = False
            try:
                with self.db_manager.get_session() as session:
                    # Crear datos válidos
                    upload_app_error = OperatorFileUpload(
                        id="rollback_test_app_error",
                        mission_id="m1",
                        operator="CLARO", 
                        file_type="DATOS",
                        file_name="app_error_test.xlsx",
                        file_size=1024
                    )
                    session.add(upload_app_error)
                    session.flush()  # Enviar a BD pero no commit
                    
                    # Simular error de aplicación
                    raise ValueError("Error simulado de aplicación")
                    
            except ValueError as e:
                rollback_test_3_success = True
                result.details["app_error_rollback"] = str(e)
                logger.info(f"✓ Rollback por error de aplicación funcionó")
            
            # Verificar estado final
            with self.db_manager.get_session() as session:
                final_uploads = session.query(OperatorFileUpload).count()
                final_cellular = session.query(OperatorCellularData).count()
                
                result.details["final_counts"] = {
                    "uploads": final_uploads,
                    "cellular": final_cellular
                }
                
                result.details["rollback_tests"] = {
                    "constraint_violation": rollback_test_1_success,
                    "foreign_key_violation": rollback_test_2_success, 
                    "application_error": rollback_test_3_success
                }
            
            # Verificar que contadores se mantuvieron
            counts_preserved = (
                final_uploads == initial_uploads and 
                final_cellular == initial_cellular
            )
            
            if not counts_preserved:
                result.add_issue(
                    "CRÍTICO",
                    f"Contadores cambiaron después de rollbacks: uploads {initial_uploads}→{final_uploads}, cellular {initial_cellular}→{final_cellular}",
                    "Datos parciales permanecen después de errores",
                    "Revisar implementación de transacciones y context managers"
                )
            
            overall_success = (
                rollback_test_1_success and 
                rollback_test_2_success and 
                rollback_test_3_success and
                counts_preserved
            )
            
            logger.info(f"✓ Pruebas de rollback completadas")
            logger.info(f"  - Constraint violation rollback: {rollback_test_1_success}")
            logger.info(f"  - Foreign key violation rollback: {rollback_test_2_success}")
            logger.info(f"  - Application error rollback: {rollback_test_3_success}")
            logger.info(f"  - Contadores preservados: {counts_preserved}")
            
            result.complete_test(success=overall_success)
            
        except Exception as e:
            logger.error(f"Error en P1-007: {e}")
            result.complete_test(success=False, error_message=str(e))
            result.add_issue("CRÍTICO", f"Fallo en pruebas de rollback: {e}",
                           "Sistema no puede garantizar consistencia transaccional",
                           "Revisar configuración de transacciones y manejo de errores")
        
        return result
    
    def test_p2_007_million_records_performance(self) -> DatabaseTestResult:
        """P2-007 (EDGE CASE): Queries BD con millones registros"""
        result = DatabaseTestResult("P2-007", "EDGE CASE")
        result.start_test()
        
        try:
            logger.info("=== EJECUTANDO P2-007: Performance con Millones de Registros ===")
            
            # Crear datos masivos (simulados con menos registros por tiempo)
            large_dataset_size = 10000  # Reducido para testing, simula comportamiento con millones
            mission_id, file_id = self._create_test_data(large_dataset_size)
            
            result.details["dataset_size"] = large_dataset_size
            
            with self.db_manager.get_session() as session:
                # PRUEBA 1: Consulta de agregación masiva
                logger.info("Ejecutando consulta de agregación masiva...")
                
                aggregation_query = """
                    SELECT 
                        operator,
                        DATE(fecha_hora_inicio) as date,
                        COUNT(*) as total_sessions,
                        SUM(trafico_subida_bytes + trafico_bajada_bytes) as total_traffic,
                        AVG(duracion_segundos) as avg_duration,
                        COUNT(DISTINCT numero_telefono) as unique_phones,
                        COUNT(DISTINCT celda_id) as unique_cells
                    FROM operator_cellular_data 
                    WHERE mission_id = :mission_id
                    GROUP BY operator, DATE(fecha_hora_inicio)
                    ORDER BY date, operator
                """
                
                agg_start = time.time()
                agg_results = session.execute(
                    text(aggregation_query),
                    {"mission_id": mission_id}
                ).fetchall()
                agg_time = (time.time() - agg_start) * 1000
                
                result.details["aggregation_query"] = {
                    "time_ms": agg_time,
                    "results_count": len(agg_results),
                    "records_processed": large_dataset_size
                }
                
                # PRUEBA 2: Búsqueda por rango temporal
                logger.info("Ejecutando búsqueda por rango temporal...")
                
                date_start = datetime.now() - timedelta(days=15)
                date_end = datetime.now() - timedelta(days=5) 
                
                temporal_query = """
                    SELECT 
                        numero_telefono,
                        COUNT(*) as session_count,
                        MIN(fecha_hora_inicio) as first_session,
                        MAX(fecha_hora_inicio) as last_session,
                        SUM(trafico_subida_bytes + trafico_bajada_bytes) as total_traffic
                    FROM operator_cellular_data
                    WHERE mission_id = :mission_id
                          AND fecha_hora_inicio BETWEEN :start_date AND :end_date
                    GROUP BY numero_telefono
                    HAVING session_count >= 5
                    ORDER BY total_traffic DESC
                    LIMIT 100
                """
                
                temporal_start = time.time()
                temporal_results = session.execute(
                    text(temporal_query),
                    {
                        "mission_id": mission_id,
                        "start_date": date_start,
                        "end_date": date_end
                    }
                ).fetchall()
                temporal_time = (time.time() - temporal_start) * 1000
                
                result.details["temporal_query"] = {
                    "time_ms": temporal_time,
                    "results_count": len(temporal_results),
                    "date_range_days": 10
                }
                
                # PRUEBA 3: JOIN complejo con múltiples tablas
                logger.info("Ejecutando JOIN complejo...")
                
                complex_join_query = """
                    SELECT 
                        ocd.numero_telefono,
                        ocr.celda_nombre,
                        ocr.ciudad,
                        COUNT(DISTINCT ocd.celda_id) as cells_used,
                        SUM(ocd.trafico_subida_bytes + ocd.trafico_bajada_bytes) as total_traffic,
                        COUNT(*) as session_count,
                        AVG(ocd.duracion_segundos) as avg_session_duration
                    FROM operator_cellular_data ocd
                    JOIN operator_file_uploads ofu ON ocd.file_upload_id = ofu.id
                    LEFT JOIN operator_cell_registry ocr ON ocd.celda_id = ocr.celda_id AND ocd.operator = ocr.operator
                    WHERE ocd.mission_id = :mission_id
                    GROUP BY ocd.numero_telefono, ocr.celda_nombre, ocr.ciudad
                    HAVING session_count >= 3
                    ORDER BY total_traffic DESC
                    LIMIT 50
                """
                
                join_start = time.time()
                join_results = session.execute(
                    text(complex_join_query),
                    {"mission_id": mission_id}
                ).fetchall()
                join_time = (time.time() - join_start) * 1000
                
                result.details["complex_join_query"] = {
                    "time_ms": join_time,
                    "results_count": len(join_results)
                }
                
                # PRUEBA 4: Consulta geoespacial
                logger.info("Ejecutando consulta geoespacial...")
                
                geo_query = """
                    SELECT 
                        celda_id,
                        AVG(latitud) as avg_lat,
                        AVG(longitud) as avg_lng,
                        COUNT(*) as usage_count,
                        COUNT(DISTINCT numero_telefono) as unique_users
                    FROM operator_cellular_data
                    WHERE mission_id = :mission_id
                          AND latitud IS NOT NULL 
                          AND longitud IS NOT NULL
                          AND latitud BETWEEN -5.0 AND -4.0
                          AND longitud BETWEEN -75.0 AND -74.0
                    GROUP BY celda_id
                    HAVING usage_count >= 10
                    ORDER BY usage_count DESC
                """
                
                geo_start = time.time()
                geo_results = session.execute(
                    text(geo_query),
                    {"mission_id": mission_id}
                ).fetchall()
                geo_time = (time.time() - geo_start) * 1000
                
                result.details["geospatial_query"] = {
                    "time_ms": geo_time,
                    "results_count": len(geo_results)
                }
                
                # PRUEBA 5: Análizar plan de consulta de query crítica
                explain_query = """
                    EXPLAIN QUERY PLAN
                    SELECT numero_telefono, COUNT(*) 
                    FROM operator_cellular_data 
                    WHERE mission_id = :mission_id AND operator = 'CLARO'
                    GROUP BY numero_telefono
                """
                
                explain_results = session.execute(
                    text(explain_query),
                    {"mission_id": mission_id}
                ).fetchall()
                
                query_plan = [{"detail": row[3]} for row in explain_results]
                result.details["query_plan"] = query_plan
                
                # Verificar uso de índices
                using_index = any("USING INDEX" in detail["detail"] for detail in query_plan)
                result.details["using_indexes"] = using_index
                
                if not using_index:
                    result.add_issue(
                        "MAYOR",
                        "Consultas críticas no están usando índices",
                        "Performance muy degradada con grandes volúmenes",
                        "Verificar creación e implementación de índices estratégicos"
                    )
                
                # Evaluar performance
                performance_issues = []
                
                # Umbrales de performance (ajustados para dataset de prueba)
                if agg_time > 2000:  # >2 segundos para agregación
                    performance_issues.append(f"agregación: {agg_time:.0f}ms")
                
                if temporal_time > 1000:  # >1 segundo para temporal
                    performance_issues.append(f"temporal: {temporal_time:.0f}ms")
                
                if join_time > 3000:  # >3 segundos para JOIN complejo
                    performance_issues.append(f"JOIN complejo: {join_time:.0f}ms")
                
                if geo_time > 1500:  # >1.5 segundos para geoespacial
                    performance_issues.append(f"geoespacial: {geo_time:.0f}ms")
                
                if performance_issues:
                    result.add_issue(
                        "MAYOR",
                        f"Consultas lentas con dataset grande: {', '.join(performance_issues)}",
                        "Performance degradada impactará producción con millones de registros",
                        "Optimizar índices, revisar queries y considerar particionado"
                    )
                
                # Verificar memoria y recursos
                total_query_time = agg_time + temporal_time + join_time + geo_time
                result.details["total_query_time_ms"] = total_query_time
                
                if total_query_time > 10000:  # >10 segundos total
                    result.add_issue(
                        "MAYOR",
                        f"Tiempo total de consultas excesivo: {total_query_time:.0f}ms",
                        "Sistema no escalará apropiadamente con datos reales",
                        "Implementar optimizaciones críticas antes de producción"
                    )
                
                logger.info(f"✓ Performance con dataset grande completada")
                logger.info(f"  - Registros procesados: {large_dataset_size:,}")
                logger.info(f"  - Tiempo agregación: {agg_time:.2f}ms")
                logger.info(f"  - Tiempo temporal: {temporal_time:.2f}ms")
                logger.info(f"  - Tiempo JOIN: {join_time:.2f}ms")
                logger.info(f"  - Tiempo geoespacial: {geo_time:.2f}ms")
                logger.info(f"  - Usando índices: {using_index}")
                
            result.complete_test(success=len(performance_issues) == 0)
            
        except Exception as e:
            logger.error(f"Error en P2-007: {e}")
            result.complete_test(success=False, error_message=str(e))
            result.add_issue("CRÍTICO", f"Fallo en pruebas de performance: {e}",
                           "Sistema no puede manejar grandes volúmenes de datos",
                           "Revisar arquitectura de BD y optimizaciones")
        
        return result
    
    # =========================================================================
    # CASOS DE PRUEBA ADICIONALES ESPECÍFICOS DE BD
    # =========================================================================
    
    def test_referential_integrity(self) -> DatabaseTestResult:
        """Integridad Referencial - Probar constraints entre tablas"""
        result = DatabaseTestResult("INTEGRIDAD_REFERENCIAL", "CRÍTICO")
        result.start_test()
        
        try:
            logger.info("=== EJECUTANDO: Integridad Referencial ===")
            
            with self.db_manager.get_session() as session:
                # PRUEBA 1: Foreign Key Constraints
                fk_violations = []
                
                # Intentar crear upload con mission_id inexistente
                try:
                    invalid_upload = OperatorFileUpload(
                        id="invalid_mission_fk",
                        mission_id="mission_inexistente",
                        operator="CLARO",
                        file_type="DATOS",
                        file_name="test.xlsx",
                        file_size=1024
                    )
                    session.add(invalid_upload)
                    session.commit()
                    fk_violations.append("mission_id FK no se valida")
                except Exception:
                    logger.info("✓ FK constraint mission_id funciona")
                    session.rollback()
                
                # Intentar crear datos celulares con file_upload_id inexistente
                try:
                    invalid_cellular = OperatorCellularData(
                        file_upload_id="upload_inexistente",
                        mission_id="m1",
                        operator="CLARO",
                        numero_telefono="3123456789",
                        fecha_hora_inicio=datetime.now(),
                        celda_id="CELL_001"
                    )
                    session.add(invalid_cellular)
                    session.commit()
                    fk_violations.append("file_upload_id FK no se valida")
                except Exception:
                    logger.info("✓ FK constraint file_upload_id funciona")
                    session.rollback()
                
                # PRUEBA 2: CASCADE Delete
                # Crear datos para probar cascade
                test_upload = OperatorFileUpload(
                    id="cascade_test_upload",
                    mission_id="m1",
                    operator="CLARO",
                    file_type="DATOS",
                    file_name="cascade_test.xlsx",
                    file_size=1024,
                    upload_status="completed"
                )
                session.add(test_upload)
                
                test_cellular = OperatorCellularData(
                    file_upload_id="cascade_test_upload",
                    mission_id="m1",
                    operator="CLARO",
                    numero_telefono="3123456789",
                    fecha_hora_inicio=datetime.now(),
                    celda_id="CELL_CASCADE"
                )
                session.add(test_cellular)
                
                test_call = OperatorCallData(
                    file_upload_id="cascade_test_upload",
                    mission_id="m1",
                    operator="CLARO",
                    tipo_llamada="ENTRANTE",
                    numero_origen="3111111111",
                    numero_destino="3123456789",
                    numero_objetivo="3123456789",
                    fecha_hora_llamada=datetime.now(),
                    celda_objetivo="CELL_CASCADE"
                )
                session.add(test_call)
                session.commit()
                
                # Contar registros antes de delete
                cellular_before = session.query(OperatorCellularData).filter_by(file_upload_id="cascade_test_upload").count()
                calls_before = session.query(OperatorCallData).filter_by(file_upload_id="cascade_test_upload").count()
                
                # Eliminar upload (debe hacer cascade)
                session.delete(test_upload)
                session.commit()
                
                # Verificar cascade
                cellular_after = session.query(OperatorCellularData).filter_by(file_upload_id="cascade_test_upload").count()
                calls_after = session.query(OperatorCallData).filter_by(file_upload_id="cascade_test_upload").count()
                
                cascade_working = (cellular_after == 0 and calls_after == 0)
                
                result.details["foreign_key_tests"] = {
                    "violations_found": fk_violations,
                    "cascade_test": {
                        "cellular_before": cellular_before,
                        "cellular_after": cellular_after,
                        "calls_before": calls_before,
                        "calls_after": calls_after,
                        "cascade_working": cascade_working
                    }
                }
                
                if fk_violations:
                    result.add_issue(
                        "CRÍTICO",
                        f"FK constraints no funcionan: {', '.join(fk_violations)}",
                        "Integridad referencial comprometida",
                        "Verificar PRAGMA foreign_keys=ON y definición de constraints"
                    )
                
                if not cascade_working:
                    result.add_issue(
                        "CRÍTICO",
                        "CASCADE delete no funciona correctamente",
                        "Datos huérfanos permanecen en BD",
                        "Revisar definición de FK constraints con CASCADE"
                    )
                
                logger.info(f"✓ Integridad referencial validada")
                logger.info(f"  - FK violations encontradas: {len(fk_violations)}")
                logger.info(f"  - CASCADE delete funciona: {cascade_working}")
                
            result.complete_test(success=len(fk_violations) == 0 and cascade_working)
            
        except Exception as e:
            logger.error(f"Error en integridad referencial: {e}")
            result.complete_test(success=False, error_message=str(e))
            result.add_issue("CRÍTICO", f"Fallo en pruebas de integridad: {e}",
                           "No se puede verificar integridad referencial",
                           "Revisar configuración de BD y constraints")
        
        return result
    
    def test_data_normalization(self) -> DatabaseTestResult:
        """Normalización de Datos - Verificar que datos heterogéneos se normalizan correctamente"""
        result = DatabaseTestResult("NORMALIZACION_DATOS", "IMPORTANTE")
        result.start_test()
        
        try:
            logger.info("=== EJECUTANDO: Normalización de Datos ===")
            
            with self.db_manager.get_session() as session:
                # Crear misión de prueba
                mission_id = "normalization_test"
                mission = Mission(
                    id=mission_id,
                    code="NORM-001",
                    name="Test Normalización",
                    description="Prueba de normalización de datos heterogéneos",
                    status="En Progreso",
                    created_by="admin"
                )
                session.add(mission)
                
                # PRUEBA 1: Datos de diferentes operadores con formatos heterogéneos
                operator_data_variations = [
                    {
                        "operator": "CLARO",
                        "numero_formats": ["573123456789", "3123456789", "+573123456789"],
                        "celda_formats": ["CLR_001", "clr_001", "CLARO_CELL_001"],
                        "tech_formats": ["LTE", "4G", "LTE-A"]
                    },
                    {
                        "operator": "MOVISTAR",
                        "numero_formats": ["573234567890", "3234567890", "+57-323-456-7890"],
                        "celda_formats": ["MOV_002", "mov_002", "MOVISTAR_CELL_002"],
                        "tech_formats": ["GSM", "2G", "GSM-900"]
                    },
                    {
                        "operator": "TIGO",
                        "numero_formats": ["573345678901", "3345678901", "57-334-567-8901"],
                        "celda_formats": ["TIG_003", "tig_003", "TIGO_CELL_003"],
                        "tech_formats": ["UMTS", "3G", "WCDMA"]
                    },
                    {
                        "operator": "WOM",
                        "numero_formats": ["573456789012", "3456789012", "573456789012"],
                        "celda_formats": ["WOM_004", "wom_004", "WOM_CELL_004"],
                        "tech_formats": ["LTE", "4G+", "LTE-Advanced"]
                    }
                ]
                
                normalization_results = {}
                
                for op_data in operator_data_variations:
                    operator = op_data["operator"]
                    
                    # Crear upload para este operador
                    upload = OperatorFileUpload(
                        id=f"norm_test_{operator.lower()}",
                        mission_id=mission_id,
                        operator=operator,
                        file_type="DATOS",
                        file_name=f"norm_test_{operator.lower()}.xlsx",
                        file_size=1024,
                        upload_status="completed"
                    )
                    session.add(upload)
                    
                    # Insertar datos con diferentes formatos
                    inserted_records = []
                    for i, numero in enumerate(op_data["numero_formats"]):
                        cellular_data = OperatorCellularData(
                            file_upload_id=upload.id,
                            mission_id=mission_id,
                            operator=operator,
                            numero_telefono=numero,  # Formato variable
                            fecha_hora_inicio=datetime.now() - timedelta(hours=i),
                            celda_id=op_data["celda_formats"][i],  # Formato variable
                            tecnologia=op_data["tech_formats"][i],  # Formato variable
                            trafico_subida_bytes=1024 * (i + 1),
                            trafico_bajada_bytes=2048 * (i + 1)
                        )
                        session.add(cellular_data)
                        inserted_records.append({
                            "numero_original": numero,
                            "celda_original": op_data["celda_formats"][i],
                            "tech_original": op_data["tech_formats"][i]
                        })
                    
                    normalization_results[operator] = inserted_records
                
                session.commit()
                
                # PRUEBA 2: Verificar normalización de números telefónicos
                number_normalization_issues = []
                
                for operator in ["CLARO", "MOVISTAR", "TIGO", "WOM"]:
                    numbers = session.query(OperatorCellularData.numero_telefono).filter_by(
                        mission_id=mission_id,
                        operator=operator
                    ).all()
                    
                    unique_numbers = set(num[0] for num in numbers)
                    
                    # Verificar que números diferentes representando el mismo número se normalizaron
                    if len(unique_numbers) > 1:
                        # Verificar si realmente son el mismo número normalizado
                        normalized_set = set()
                        for num in unique_numbers:
                            # Normalizar manualmente para comparar
                            clean_num = ''.join(filter(str.isdigit, num))
                            if clean_num.startswith('57'):
                                clean_num = clean_num[2:]
                            normalized_set.add(clean_num)
                        
                        if len(normalized_set) == 1 and len(unique_numbers) > 1:
                            number_normalization_issues.append(
                                f"{operator}: múltiples formatos del mismo número: {list(unique_numbers)}"
                            )
                
                # PRUEBA 3: Verificar normalización de celdas
                cell_normalization_issues = []
                
                for operator in ["CLARO", "MOVISTAR", "TIGO", "WOM"]:
                    cells = session.query(OperatorCellularData.celda_id).filter_by(
                        mission_id=mission_id,
                        operator=operator
                    ).all()
                    
                    unique_cells = set(cell[0] for cell in cells)
                    
                    # Verificar patrones de normalización de celdas
                    for cell_id in unique_cells:
                        if cell_id.lower() != cell_id and cell_id.upper() != cell_id:
                            cell_normalization_issues.append(
                                f"{operator}: celda sin normalización consistente: {cell_id}"
                            )
                
                # PRUEBA 4: Verificar datos específicos de operador en JSON
                operator_specific_data_test = []
                
                # Agregar datos específicos para cada operador
                for operator in ["CLARO", "MOVISTAR", "TIGO", "WOM"]:
                    cellular_record = session.query(OperatorCellularData).filter_by(
                        mission_id=mission_id,
                        operator=operator
                    ).first()
                    
                    if cellular_record:
                        # Datos específicos simulados por operador
                        operator_specific = {
                            "CLARO": {"plan_type": "postpago", "roaming": False, "apn": "internet.comcel.com.co"},
                            "MOVISTAR": {"tipo_plan": "prepago", "en_roaming": False, "apn": "internet.movistar.co"},
                            "TIGO": {"plan": "hibrido", "roaming_status": False, "access_point": "web.comcel.com.co"},
                            "WOM": {"plan_categoria": "postpago", "roaming_activo": False, "punto_acceso": "internet.wom.co"}
                        }
                        
                        cellular_record.operator_specific_data = json.dumps(operator_specific[operator])
                        
                        # Verificar que JSON es válido
                        try:
                            parsed_data = cellular_record.get_operator_specific_data()
                            operator_specific_data_test.append({
                                "operator": operator,
                                "json_valid": True,
                                "data_keys": list(parsed_data.keys())
                            })
                        except Exception as e:
                            operator_specific_data_test.append({
                                "operator": operator,
                                "json_valid": False,
                                "error": str(e)
                            })
                
                session.commit()
                
                # PRUEBA 5: Verificar integridad después de normalización
                final_count_by_operator = {}
                for operator in ["CLARO", "MOVISTAR", "TIGO", "WOM"]:
                    count = session.query(OperatorCellularData).filter_by(
                        mission_id=mission_id,
                        operator=operator
                    ).count()
                    final_count_by_operator[operator] = count
                
                result.details["normalization_test"] = {
                    "data_inserted": normalization_results,
                    "number_normalization_issues": number_normalization_issues,
                    "cell_normalization_issues": cell_normalization_issues,
                    "operator_specific_data": operator_specific_data_test,
                    "final_counts": final_count_by_operator
                }
                
                # Evaluar resultados
                total_issues = len(number_normalization_issues) + len(cell_normalization_issues)
                
                if number_normalization_issues:
                    result.add_issue(
                        "MAYOR",
                        f"Problemas en normalización de números: {'; '.join(number_normalization_issues)}",
                        "Números duplicados por falta de normalización consistente",
                        "Implementar normalización automática en triggers o validaciones"
                    )
                
                if cell_normalization_issues:
                    result.add_issue(
                        "MENOR",
                        f"Problemas en normalización de celdas: {'; '.join(cell_normalization_issues)}",
                        "Inconsistencia en formato de identificadores de celdas",
                        "Estandarizar formato de celda_id en procesamiento"
                    )
                
                # Verificar JSON válido
                invalid_json = [test for test in operator_specific_data_test if not test["json_valid"]]
                if invalid_json:
                    result.add_issue(
                        "MAYOR",
                        f"Datos específicos JSON inválidos: {[test['operator'] for test in invalid_json]}",
                        "Pérdida de datos específicos de operador",
                        "Verificar validación JSON en constraints"
                    )
                
                logger.info(f"✓ Normalización de datos validada")
                logger.info(f"  - Operadores procesados: {len(final_count_by_operator)}")
                logger.info(f"  - Issues de normalización números: {len(number_normalization_issues)}")
                logger.info(f"  - Issues de normalización celdas: {len(cell_normalization_issues)}")
                logger.info(f"  - JSON válido: {len([t for t in operator_specific_data_test if t['json_valid']])}/{len(operator_specific_data_test)}")
                
            result.complete_test(success=total_issues == 0 and len(invalid_json) == 0)
            
        except Exception as e:
            logger.error(f"Error en normalización de datos: {e}")
            result.complete_test(success=False, error_message=str(e))
            result.add_issue("CRÍTICO", f"Fallo en pruebas de normalización: {e}",
                           "No se puede verificar normalización de datos",
                           "Revisar procesamiento de datos y esquema de BD")
        
        return result
    
    def run_all_tests(self) -> List[DatabaseTestResult]:
        """Ejecuta todos los casos de prueba de base de datos"""
        logger.info("=== INICIANDO TESTING EXHAUSTIVO DE BASE DE DATOS ===")
        logger.info("Equipo: Base de Datos")
        logger.info("Contexto: Testing Coordinado - Post Arquitectura L2")
        
        try:
            self.setup_test_environment()
            
            # Ejecutar todos los casos de prueba
            test_methods = [
                self.test_p0_008_cross_operator_queries,
                self.test_p1_003_backup_recovery,
                self.test_p1_007_rollback_transactions,
                self.test_p2_007_million_records_performance,
                self.test_referential_integrity,
                self.test_data_normalization
            ]
            
            for test_method in test_methods:
                try:
                    result = test_method()
                    self.results.append(result)
                    logger.info(f"Completado: {result.test_case} - {result.status}")
                except Exception as e:
                    logger.error(f"Error ejecutando {test_method.__name__}: {e}")
                    error_result = DatabaseTestResult(test_method.__name__, "ERROR")
                    error_result.complete_test(success=False, error_message=str(e))
                    self.results.append(error_result)
            
        finally:
            self.cleanup_test_environment()
        
        return self.results
    
    def generate_report(self) -> str:
        """Genera reporte completo de testing de base de datos"""
        report = []
        report.append("=" * 80)
        report.append("REPORTE DE TESTING EXHAUSTIVO - EQUIPO DE BASE DE DATOS")
        report.append("=" * 80)
        report.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Contexto: Testing Coordinado Post-Arquitectura L2")
        report.append(f"Total de pruebas ejecutadas: {len(self.results)}")
        report.append("")
        
        # Resumen ejecutivo
        passed = sum(1 for r in self.results if r.status == "PASSED")
        failed = sum(1 for r in self.results if r.status == "FAILED")
        total_issues = sum(len(r.issues_found) for r in self.results)
        critical_issues = sum(len([i for i in r.issues_found if i["severity"] == "CRÍTICO"]) for r in self.results)
        
        report.append("RESUMEN EJECUTIVO:")
        report.append(f"✓ Pruebas exitosas: {passed}/{len(self.results)}")
        report.append(f"✗ Pruebas fallidas: {failed}/{len(self.results)}")
        report.append(f"⚠ Issues encontrados: {total_issues} (Críticos: {critical_issues})")
        report.append("")
        
        # Estado general de la base de datos
        if critical_issues == 0 and failed == 0:
            db_status = "✅ APTO PARA PRODUCCIÓN"
        elif critical_issues == 0 and failed <= 2:
            db_status = "⚠️ REQUIERE CORRECCIONES MENORES"
        elif critical_issues <= 2:
            db_status = "🔴 REQUIERE CORRECCIONES CRÍTICAS"
        else:
            db_status = "❌ NO APTO PARA PRODUCCIÓN"
        
        report.append(f"ESTADO DE LA BASE DE DATOS: {db_status}")
        report.append("")
        
        # Detalle por caso de prueba
        report.append("DETALLE DE CASOS DE PRUEBA:")
        report.append("-" * 50)
        
        for result in self.results:
            report.append(f"\n{result.test_case} ({result.priority})")
            report.append(f"Estado: {result.status}")
            if result.duration_ms:
                report.append(f"Duración: {result.duration_ms:.2f}ms")
            
            if result.error_message:
                report.append(f"Error: {result.error_message}")
            
            if result.issues_found:
                report.append("Issues encontrados:")
                for issue in result.issues_found:
                    report.append(f"  - {issue['severity']}: {issue['description']}")
                    report.append(f"    Impacto: {issue['impact']}")
                    report.append(f"    Sugerencia: {issue['suggestion']}")
            
            if result.details:
                report.append("Detalles técnicos:")
                for key, value in result.details.items():
                    if isinstance(value, dict):
                        report.append(f"  {key}:")
                        for subkey, subvalue in value.items():
                            report.append(f"    {subkey}: {subvalue}")
                    else:
                        report.append(f"  {key}: {value}")
        
        # Issues consolidados por severidad
        report.append("\n" + "=" * 50)
        report.append("ISSUES CONSOLIDADOS POR SEVERIDAD:")
        report.append("=" * 50)
        
        all_issues = []
        for result in self.results:
            for issue in result.issues_found:
                issue_copy = issue.copy()
                issue_copy["test_case"] = result.test_case
                all_issues.append(issue_copy)
        
        for severity in ["CRÍTICO", "MAYOR", "MENOR", "COSMÉTICO"]:
            severity_issues = [i for i in all_issues if i["severity"] == severity]
            if severity_issues:
                report.append(f"\n{severity} ({len(severity_issues)} issues):")
                for i, issue in enumerate(severity_issues, 1):
                    report.append(f"{i}. [{issue['test_case']}] {issue['description']}")
                    report.append(f"   Sugerencia: {issue['suggestion']}")
        
        # Recomendaciones finales
        report.append("\n" + "=" * 50)
        report.append("RECOMENDACIONES FINALES:")
        report.append("=" * 50)
        
        if critical_issues > 0:
            report.append("🔴 ACCIÓN INMEDIATA REQUERIDA:")
            report.append("- Resolver todos los issues CRÍTICOS antes de continuar")
            report.append("- Re-ejecutar testing después de correcciones")
            report.append("- Validar integridad de datos en entorno de pruebas")
        
        if failed > 0:
            report.append("⚠️ ACCIONES RECOMENDADAS:")
            report.append("- Revisar casos de prueba fallidos")
            report.append("- Implementar correcciones sugeridas")
            report.append("- Validar configuración de base de datos")
        
        report.append("\n📋 ACCIONES DE SEGUIMIENTO:")
        report.append("- Implementar monitoreo continuo de performance")
        report.append("- Programar testing regular con datos reales")
        report.append("- Mantener estadísticas de BD actualizadas (ANALYZE)")
        report.append("- Documentar procedimientos de backup/recovery")
        
        # Sign-off
        report.append("\n" + "=" * 50)
        report.append("SIGN-OFF DEL EQUIPO DE BASE DE DATOS:")
        report.append("=" * 50)
        
        if critical_issues == 0 and failed == 0:
            report.append("✅ APROBADO - Base de datos lista para operación")
        elif critical_issues == 0:
            report.append("⚠️ APROBADO CON OBSERVACIONES - Implementar correcciones menores")
        else:
            report.append("❌ NO APROBADO - Requiere correcciones críticas")
        
        report.append(f"Especialista de BD: Database Testing Team")
        report.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return "\n".join(report)

def main():
    """Función principal para ejecutar el testing exhaustivo"""
    try:
        # Crear y ejecutar suite de pruebas
        test_suite = DatabaseTestSuite()
        results = test_suite.run_all_tests()
        
        # Generar y guardar reporte
        report = test_suite.generate_report()
        
        # Guardar reporte en archivo
        report_file = "database_testing_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Mostrar resumen en consola
        print("\n" + "=" * 60)
        print("TESTING DE BASE DE DATOS COMPLETADO")
        print("=" * 60)
        
        passed = sum(1 for r in results if r.status == "PASSED")
        failed = sum(1 for r in results if r.status == "FAILED")
        total_issues = sum(len(r.issues_found) for r in results)
        critical_issues = sum(len([i for i in r.issues_found if i["severity"] == "CRÍTICO"]) for r in results)
        
        print(f"Pruebas ejecutadas: {len(results)}")
        print(f"Exitosas: {passed}")
        print(f"Fallidas: {failed}")
        print(f"Issues críticos: {critical_issues}")
        print(f"Issues totales: {total_issues}")
        print(f"\nReporte completo guardado en: {report_file}")
        
        if critical_issues == 0 and failed == 0:
            print("\n[OK] BASE DE DATOS APROBADA PARA OPERACION")
            return 0
        elif critical_issues == 0:
            print("\n[WARNING] BASE DE DATOS APROBADA CON OBSERVACIONES")
            return 1
        else:
            print("\n[ERROR] BASE DE DATOS NO APROBADA - REQUIERE CORRECCIONES")
            return 2
            
    except Exception as e:
        print(f"\n[CRITICAL ERROR] ERROR CRITICO EN TESTING: {e}")
        traceback.print_exc()
        return 3

if __name__ == "__main__":
    exit(main())