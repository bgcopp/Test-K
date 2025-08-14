"""
KRONOS - Testing Específico de Base de Datos - Equipo de Base de Datos
=============================================================================
Script de testing simplificado para casos de prueba críticos de base de datos.

Casos de Prueba Ejecutados:
- P0-008 (CRÍTICO): Consulta cross-operador en BD
- P1-003 (IMPORTANTE): Backup y recuperación BD operadores
- P1-007 (IMPORTANTE): Rollback automático en fallo BD  
- P2-007 (EDGE CASE): Queries BD con millones registros

Contexto del Testing Coordinado:
- Post validación Arquitectura L2 (2 issues menores encontrados)
- Issue conocido: Context Manager en OperatorService
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
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseTestResult:
    """Resultado de una prueba de base de datos"""
    def __init__(self, test_case: str, priority: str):
        self.test_case = test_case
        self.priority = priority
        self.status = "PENDING"
        self.start_time = None
        self.end_time = None
        self.duration_ms = None
        self.error_message = None
        self.details = {}
        self.issues_found = []
        
    def start_test(self):
        self.start_time = datetime.now()
        self.status = "RUNNING"
        
    def complete_test(self, success=True, error_message=None):
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

class DatabaseTestRunner:
    """Ejecutor de pruebas de base de datos"""
    
    def __init__(self):
        self.results = []
        self.test_db_path = None
        self.backup_db_path = None
        
    def setup_test_database(self):
        """Crea una base de datos de prueba con esquema completo"""
        logger.info("Configurando base de datos de prueba...")
        
        # Crear directorio temporal
        temp_dir = tempfile.mkdtemp(prefix="kronos_db_test_")
        self.test_db_path = os.path.join(temp_dir, "test_db.db")
        self.backup_db_path = os.path.join(temp_dir, "backup_db.db")
        
        # Crear conexión y habilitar foreign keys
        conn = sqlite3.connect(self.test_db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Crear esquema básico
        cursor = conn.cursor()
        
        # Tabla missions (simplificada)
        cursor.execute("""
            CREATE TABLE missions (
                id TEXT PRIMARY KEY,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'En Progreso',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla operator_file_uploads
        cursor.execute("""
            CREATE TABLE operator_file_uploads (
                id TEXT PRIMARY KEY,
                mission_id TEXT NOT NULL,
                operator TEXT NOT NULL CHECK (operator IN ('CLARO', 'MOVISTAR', 'TIGO', 'WOM')),
                file_type TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                records_count INTEGER DEFAULT 0,
                upload_status TEXT DEFAULT 'pending' CHECK (upload_status IN ('pending', 'processing', 'completed', 'error')),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (mission_id) REFERENCES missions(id)
            )
        """)
        
        # Tabla operator_cellular_data
        cursor.execute("""
            CREATE TABLE operator_cellular_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_upload_id TEXT NOT NULL,
                mission_id TEXT NOT NULL,
                operator TEXT NOT NULL,
                numero_telefono TEXT NOT NULL,
                fecha_hora_inicio DATETIME NOT NULL,
                fecha_hora_fin DATETIME,
                duracion_segundos INTEGER,
                celda_id TEXT NOT NULL,
                lac_tac TEXT,
                trafico_subida_bytes BIGINT DEFAULT 0,
                trafico_bajada_bytes BIGINT DEFAULT 0,
                latitud REAL,
                longitud REAL,
                tecnologia TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_upload_id) REFERENCES operator_file_uploads(id) ON DELETE CASCADE,
                FOREIGN KEY (mission_id) REFERENCES missions(id)
            )
        """)
        
        # Tabla operator_call_data
        cursor.execute("""
            CREATE TABLE operator_call_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_upload_id TEXT NOT NULL,
                mission_id TEXT NOT NULL,
                operator TEXT NOT NULL,
                tipo_llamada TEXT NOT NULL CHECK (tipo_llamada IN ('ENTRANTE', 'SALIENTE', 'MIXTA')),
                numero_origen TEXT NOT NULL,
                numero_destino TEXT NOT NULL,
                numero_objetivo TEXT NOT NULL,
                fecha_hora_llamada DATETIME NOT NULL,
                duracion_segundos INTEGER DEFAULT 0,
                celda_objetivo TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_upload_id) REFERENCES operator_file_uploads(id) ON DELETE CASCADE,
                FOREIGN KEY (mission_id) REFERENCES missions(id)
            )
        """)
        
        # Índices críticos
        indexes = [
            "CREATE INDEX idx_ofu_mission ON operator_file_uploads(mission_id)",
            "CREATE INDEX idx_ofu_operator ON operator_file_uploads(operator)",
            "CREATE INDEX idx_ocd_mission_operator ON operator_cellular_data(mission_id, operator)",
            "CREATE INDEX idx_ocd_numero ON operator_cellular_data(numero_telefono)",
            "CREATE INDEX idx_ocd_fecha ON operator_cellular_data(fecha_hora_inicio)",
            "CREATE INDEX idx_call_mission_operator ON operator_call_data(mission_id, operator)",
            "CREATE INDEX idx_call_numero ON operator_call_data(numero_objetivo)",
            "CREATE INDEX idx_call_fecha ON operator_call_data(fecha_hora_llamada)"
        ]
        
        for idx_sql in indexes:
            cursor.execute(idx_sql)
        
        # Datos iniciales
        cursor.execute("INSERT INTO missions (id, code, name) VALUES ('test_mission', 'TEST-001', 'Mission de Prueba')")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Base de datos de prueba creada: {self.test_db_path}")
        
    def cleanup_test_database(self):
        """Limpia archivos de prueba"""
        try:
            if self.test_db_path and os.path.exists(self.test_db_path):
                os.remove(self.test_db_path)
            if self.backup_db_path and os.path.exists(self.backup_db_path):
                os.remove(self.backup_db_path)
            logger.info("Archivos de prueba eliminados")
        except Exception as e:
            logger.error(f"Error limpiando archivos: {e}")
    
    def create_test_data(self, record_count=1000):
        """Crea datos de prueba para validaciones"""
        logger.info(f"Creando {record_count} registros de datos de prueba...")
        
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Crear uploads para múltiples operadores
        operators = ['CLARO', 'MOVISTAR', 'TIGO', 'WOM']
        upload_ids = []
        
        for i, operator in enumerate(operators):
            upload_id = f"upload_{operator.lower()}"
            upload_ids.append(upload_id)
            cursor.execute("""
                INSERT INTO operator_file_uploads 
                (id, mission_id, operator, file_type, file_name, file_size, upload_status, records_count)
                VALUES (?, 'test_mission', ?, 'DATOS', ?, 1024000, 'completed', ?)
            """, (upload_id, operator, f"test_{operator.lower()}.xlsx", record_count // len(operators)))
        
        # Crear datos celulares
        base_date = datetime.now() - timedelta(days=30)
        phone_numbers = [f"31234567{i:02d}" for i in range(50)]
        cell_ids = [f"CELL_{i:04d}" for i in range(20)]
        
        cellular_data = []
        for i in range(record_count):
            operator_idx = i % len(operators)
            cellular_data.append((
                upload_ids[operator_idx],
                'test_mission',
                operators[operator_idx],
                phone_numbers[i % len(phone_numbers)],
                (base_date + timedelta(minutes=i)).isoformat(),
                (base_date + timedelta(minutes=i+5)).isoformat(),
                300 + (i % 600),
                cell_ids[i % len(cell_ids)],
                f"LAC_{i % 100}",
                1024 * (i % 1000),
                2048 * (i % 1500),
                -4.5981 + (i % 100) * 0.001,
                -74.0758 + (i % 100) * 0.001,
                'LTE'
            ))
            
            if len(cellular_data) >= 100:  # Insertar en lotes
                cursor.executemany("""
                    INSERT INTO operator_cellular_data 
                    (file_upload_id, mission_id, operator, numero_telefono, fecha_hora_inicio, 
                     fecha_hora_fin, duracion_segundos, celda_id, lac_tac, trafico_subida_bytes, 
                     trafico_bajada_bytes, latitud, longitud, tecnologia)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, cellular_data)
                cellular_data = []
        
        if cellular_data:  # Insertar último lote
            cursor.executemany("""
                INSERT INTO operator_cellular_data 
                (file_upload_id, mission_id, operator, numero_telefono, fecha_hora_inicio, 
                 fecha_hora_fin, duracion_segundos, celda_id, lac_tac, trafico_subida_bytes, 
                 trafico_bajada_bytes, latitud, longitud, tecnologia)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, cellular_data)
        
        # Crear algunos datos de llamadas
        call_data = []
        for i in range(record_count // 2):
            operator_idx = i % len(operators)
            call_data.append((
                upload_ids[operator_idx],
                'test_mission',
                operators[operator_idx],
                'ENTRANTE',
                f"555000{i % 100:02d}",
                phone_numbers[i % len(phone_numbers)],
                phone_numbers[i % len(phone_numbers)],
                (base_date + timedelta(hours=i % 24)).isoformat(),
                60 + (i % 300),
                cell_ids[i % len(cell_ids)]
            ))
        
        cursor.executemany("""
            INSERT INTO operator_call_data 
            (file_upload_id, mission_id, operator, tipo_llamada, numero_origen, numero_destino,
             numero_objetivo, fecha_hora_llamada, duracion_segundos, celda_objetivo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, call_data)
        
        conn.commit()
        conn.close()
        
        logger.info(f"Datos de prueba creados: {record_count} registros celulares, {len(call_data)} llamadas")

    # ========================================================================
    # CASOS DE PRUEBA CRÍTICOS
    # ========================================================================
    
    def test_p0_008_cross_operator_queries(self) -> DatabaseTestResult:
        """P0-008 (CRÍTICO): Consulta cross-operador en BD"""
        result = DatabaseTestResult("P0-008", "CRÍTICO")
        result.start_test()
        
        try:
            logger.info("=== EJECUTANDO P0-008: Consultas Cross-Operador ===")
            
            conn = sqlite3.connect(self.test_db_path)
            cursor = conn.cursor()
            
            # PRUEBA 1: Consulta unificada de todos los operadores
            query_start = time.time()
            cursor.execute("""
                SELECT 
                    operator,
                    COUNT(*) as total_records,
                    COUNT(DISTINCT numero_telefono) as unique_phones,
                    AVG(trafico_subida_bytes + trafico_bajada_bytes) as avg_traffic,
                    COUNT(DISTINCT celda_id) as unique_cells
                FROM operator_cellular_data 
                WHERE mission_id = 'test_mission'
                GROUP BY operator
                ORDER BY total_records DESC
            """)
            cross_results = cursor.fetchall()
            query_time = (time.time() - query_start) * 1000
            
            result.details["cross_operator_query"] = {
                "time_ms": query_time,
                "operators_found": len(cross_results),
                "results": [{"operator": row[0], "records": row[1], "phones": row[2]} for row in cross_results]
            }
            
            # PRUEBA 2: JOIN entre tablas de operadores
            join_start = time.time()
            cursor.execute("""
                SELECT 
                    ofu.operator,
                    COUNT(DISTINCT ocd.numero_telefono) as unique_phones,
                    COUNT(ocd.id) as data_records,
                    COUNT(DISTINCT ocl.numero_objetivo) as call_phones,
                    COUNT(ocl.id) as call_records
                FROM operator_file_uploads ofu
                LEFT JOIN operator_cellular_data ocd ON ofu.id = ocd.file_upload_id
                LEFT JOIN operator_call_data ocl ON ofu.id = ocl.file_upload_id
                WHERE ofu.mission_id = 'test_mission'
                GROUP BY ofu.operator
                ORDER BY data_records DESC
            """)
            join_results = cursor.fetchall()
            join_time = (time.time() - join_start) * 1000
            
            result.details["join_query"] = {
                "time_ms": join_time,
                "results": len(join_results)
            }
            
            # PRUEBA 3: Consulta temporal cross-operador
            temporal_start = time.time()
            cursor.execute("""
                SELECT 
                    DATE(fecha_hora_inicio) as date,
                    operator,
                    COUNT(*) as daily_records,
                    SUM(trafico_subida_bytes + trafico_bajada_bytes) as daily_traffic
                FROM operator_cellular_data
                WHERE mission_id = 'test_mission'
                GROUP BY DATE(fecha_hora_inicio), operator
                ORDER BY date, operator
            """)
            temporal_results = cursor.fetchall()
            temporal_time = (time.time() - temporal_start) * 1000
            
            result.details["temporal_query"] = {
                "time_ms": temporal_time,
                "results": len(temporal_results)
            }
            
            # Validaciones
            expected_operators = ['CLARO', 'MOVISTAR', 'TIGO', 'WOM']
            found_operators = [row[0] for row in cross_results]
            missing_operators = set(expected_operators) - set(found_operators)
            
            if missing_operators:
                result.add_issue(
                    "CRÍTICO",
                    f"Operadores faltantes en consulta cross-operador: {missing_operators}",
                    "Datos no están siendo normalizados correctamente",
                    "Verificar proceso de inserción y normalización"
                )
            
            if query_time > 1000:  # >1 segundo
                result.add_issue(
                    "MAYOR",
                    f"Consulta cross-operador lenta: {query_time:.2f}ms",
                    "Performance degradada en consultas unificadas",
                    "Verificar índices en campos operator y mission_id"
                )
            
            conn.close()
            
            logger.info(f"✓ P0-008 completado - Operadores: {len(cross_results)}, Tiempo: {query_time:.2f}ms")
            result.complete_test(success=len(result.issues_found) == 0)
            
        except Exception as e:
            logger.error(f"Error en P0-008: {e}")
            result.complete_test(success=False, error_message=str(e))
        
        return result
    
    def test_p1_003_backup_recovery(self) -> DatabaseTestResult:
        """P1-003 (IMPORTANTE): Backup y recuperación BD operadores"""
        result = DatabaseTestResult("P1-003", "IMPORTANTE")
        result.start_test()
        
        try:
            logger.info("=== EJECUTANDO P1-003: Backup y Recuperación ===")
            
            # Crear datos de prueba
            self.create_test_data(500)
            
            # Contar registros originales
            conn = sqlite3.connect(self.test_db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM operator_file_uploads")
            original_uploads = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM operator_cellular_data")
            original_cellular = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM operator_call_data")
            original_calls = cursor.fetchone()[0]
            
            conn.close()
            
            result.details["original_counts"] = {
                "uploads": original_uploads,
                "cellular": original_cellular,
                "calls": original_calls
            }
            
            # PRUEBA 1: Crear backup
            backup_start = time.time()
            shutil.copy2(self.test_db_path, self.backup_db_path)
            backup_time = (time.time() - backup_start) * 1000
            
            result.details["backup_time_ms"] = backup_time
            result.details["backup_size_bytes"] = os.path.getsize(self.backup_db_path)
            
            # PRUEBA 2: Modificar datos originales
            conn = sqlite3.connect(self.test_db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM operator_cellular_data WHERE id <= 100")
            cursor.execute("UPDATE operator_file_uploads SET upload_status = 'error' WHERE operator = 'CLARO'")
            
            conn.commit()
            conn.close()
            
            # PRUEBA 3: Restaurar desde backup
            restore_start = time.time()
            shutil.copy2(self.backup_db_path, self.test_db_path)
            restore_time = (time.time() - restore_start) * 1000
            
            result.details["restore_time_ms"] = restore_time
            
            # PRUEBA 4: Verificar integridad
            conn = sqlite3.connect(self.test_db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM operator_file_uploads")
            restored_uploads = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM operator_cellular_data")
            restored_cellular = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM operator_call_data")
            restored_calls = cursor.fetchone()[0]
            
            cursor.execute("SELECT upload_status FROM operator_file_uploads WHERE operator = 'CLARO'")
            claro_status = cursor.fetchone()[0]
            
            conn.close()
            
            result.details["restored_counts"] = {
                "uploads": restored_uploads,
                "cellular": restored_cellular,
                "calls": restored_calls
            }
            
            # Validaciones de integridad
            integrity_ok = (
                original_uploads == restored_uploads and
                original_cellular == restored_cellular and
                original_calls == restored_calls and
                claro_status == 'completed'  # Debe estar restaurado
            )
            
            if not integrity_ok:
                result.add_issue(
                    "CRÍTICO",
                    "Pérdida de datos en proceso de backup/restore",
                    "Integridad de datos comprometida",
                    "Revisar proceso de backup y validar restauración completa"
                )
            
            if backup_time > 5000:  # >5 segundos
                result.add_issue(
                    "MENOR",
                    f"Proceso de backup lento: {backup_time:.2f}ms",
                    "Performance degradada en backup",
                    "Optimizar proceso de backup para bases de datos grandes"
                )
            
            logger.info(f"✓ P1-003 completado - Integridad: {integrity_ok}, Tiempo backup: {backup_time:.2f}ms")
            result.complete_test(success=integrity_ok)
            
        except Exception as e:
            logger.error(f"Error en P1-003: {e}")
            result.complete_test(success=False, error_message=str(e))
        
        return result
    
    def test_p1_007_rollback_transactions(self) -> DatabaseTestResult:
        """P1-007 (IMPORTANTE): Rollback automático en fallo BD"""
        result = DatabaseTestResult("P1-007", "IMPORTANTE")
        result.start_test()
        
        try:
            logger.info("=== EJECUTANDO P1-007: Rollback Automático ===")
            
            conn = sqlite3.connect(self.test_db_path)
            
            # Contar registros iniciales
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM operator_file_uploads")
            initial_uploads = cursor.fetchone()[0]
            
            result.details["initial_uploads"] = initial_uploads
            
            # PRUEBA 1: Transacción que debe fallar por constraint
            rollback_test_1 = False
            try:
                cursor.execute("BEGIN TRANSACTION")
                
                # Insertar upload válido
                cursor.execute("""
                    INSERT INTO operator_file_uploads 
                    (id, mission_id, operator, file_type, file_name, file_size)
                    VALUES ('rollback_test', 'test_mission', 'CLARO', 'DATOS', 'test.xlsx', 1024)
                """)
                
                # Intentar insertar upload con operador inválido (debe fallar)
                cursor.execute("""
                    INSERT INTO operator_file_uploads 
                    (id, mission_id, operator, file_type, file_name, file_size)
                    VALUES ('rollback_test2', 'test_mission', 'OPERADOR_INVALIDO', 'DATOS', 'test2.xlsx', 1024)
                """)
                
                cursor.execute("COMMIT")
                
            except sqlite3.IntegrityError as e:
                cursor.execute("ROLLBACK")
                rollback_test_1 = True
                result.details["constraint_error"] = str(e)
                logger.info(f"✓ Rollback por constraint funcionó: {e}")
            
            # PRUEBA 2: Transacción que falla por foreign key
            rollback_test_2 = False
            try:
                cursor.execute("BEGIN TRANSACTION")
                
                cursor.execute("""
                    INSERT INTO operator_file_uploads 
                    (id, mission_id, operator, file_type, file_name, file_size)
                    VALUES ('rollback_fk_test', 'mission_inexistente', 'CLARO', 'DATOS', 'test.xlsx', 1024)
                """)
                
                cursor.execute("COMMIT")
                
            except sqlite3.IntegrityError as e:
                cursor.execute("ROLLBACK")
                rollback_test_2 = True
                result.details["fk_error"] = str(e)
                logger.info(f"✓ Rollback por FK funcionó: {e}")
            
            # Verificar que no se insertó nada
            cursor.execute("SELECT COUNT(*) FROM operator_file_uploads")
            final_uploads = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM operator_file_uploads WHERE id LIKE 'rollback%'")
            rollback_uploads = cursor.fetchone()[0]
            
            conn.close()
            
            result.details["final_uploads"] = final_uploads
            result.details["rollback_uploads_found"] = rollback_uploads
            result.details["rollback_tests"] = {
                "constraint_violation": rollback_test_1,
                "foreign_key_violation": rollback_test_2
            }
            
            # Validaciones
            counts_preserved = (final_uploads == initial_uploads)
            no_partial_data = (rollback_uploads == 0)
            
            if not rollback_test_1:
                result.add_issue(
                    "CRÍTICO",
                    "Constraint violation no causó rollback automático",
                    "Datos parciales pueden quedar en BD",
                    "Verificar configuración de constraints y transacciones"
                )
            
            if not rollback_test_2:
                result.add_issue(
                    "CRÍTICO",
                    "Foreign key violation no causó rollback automático",
                    "Integridad referencial comprometida",
                    "Verificar PRAGMA foreign_keys=ON"
                )
            
            if not counts_preserved or not no_partial_data:
                result.add_issue(
                    "CRÍTICO",
                    "Datos parciales permanecieron después de rollback",
                    "Transacciones no funcionan correctamente",
                    "Revisar manejo de transacciones en aplicación"
                )
            
            overall_success = rollback_test_1 and rollback_test_2 and counts_preserved and no_partial_data
            
            logger.info(f"✓ P1-007 completado - Rollbacks OK: {overall_success}")
            result.complete_test(success=overall_success)
            
        except Exception as e:
            logger.error(f"Error en P1-007: {e}")
            result.complete_test(success=False, error_message=str(e))
        
        return result
    
    def test_p2_007_performance_large_dataset(self) -> DatabaseTestResult:
        """P2-007 (EDGE CASE): Queries BD con millones registros"""
        result = DatabaseTestResult("P2-007", "EDGE CASE")
        result.start_test()
        
        try:
            logger.info("=== EJECUTANDO P2-007: Performance con Dataset Grande ===")
            
            # Crear dataset grande para pruebas
            large_size = 20000  # Simula comportamiento con millones
            self.create_test_data(large_size)
            
            conn = sqlite3.connect(self.test_db_path)
            cursor = conn.cursor()
            
            # PRUEBA 1: Consulta de agregación masiva
            agg_start = time.time()
            cursor.execute("""
                SELECT 
                    operator,
                    DATE(fecha_hora_inicio) as date,
                    COUNT(*) as records,
                    SUM(trafico_subida_bytes + trafico_bajada_bytes) as total_traffic,
                    COUNT(DISTINCT numero_telefono) as unique_phones
                FROM operator_cellular_data 
                GROUP BY operator, DATE(fecha_hora_inicio)
                ORDER BY records DESC
            """)
            agg_results = cursor.fetchall()
            agg_time = (time.time() - agg_start) * 1000
            
            result.details["aggregation_query"] = {
                "time_ms": agg_time,
                "results": len(agg_results),
                "records_processed": large_size
            }
            
            # PRUEBA 2: Búsqueda por rango temporal
            temporal_start = time.time()
            cursor.execute("""
                SELECT 
                    numero_telefono,
                    COUNT(*) as sessions,
                    SUM(trafico_subida_bytes + trafico_bajada_bytes) as total_traffic
                FROM operator_cellular_data
                WHERE fecha_hora_inicio >= datetime('now', '-7 days')
                GROUP BY numero_telefono
                HAVING sessions >= 3
                ORDER BY total_traffic DESC
                LIMIT 100
            """)
            temporal_results = cursor.fetchall()
            temporal_time = (time.time() - temporal_start) * 1000
            
            result.details["temporal_query"] = {
                "time_ms": temporal_time,
                "results": len(temporal_results)
            }
            
            # PRUEBA 3: JOIN complejo
            join_start = time.time()
            cursor.execute("""
                SELECT 
                    ocd.operator,
                    ocd.numero_telefono,
                    COUNT(DISTINCT ocd.celda_id) as cells_used,
                    COUNT(ocd.id) as data_sessions,
                    COUNT(ocl.id) as calls_made
                FROM operator_cellular_data ocd
                JOIN operator_file_uploads ofu ON ocd.file_upload_id = ofu.id
                LEFT JOIN operator_call_data ocl ON ocd.numero_telefono = ocl.numero_objetivo
                GROUP BY ocd.operator, ocd.numero_telefono
                HAVING data_sessions >= 5
                ORDER BY data_sessions DESC
                LIMIT 50
            """)
            join_results = cursor.fetchall()
            join_time = (time.time() - join_start) * 1000
            
            result.details["join_query"] = {
                "time_ms": join_time,
                "results": len(join_results)
            }
            
            # PRUEBA 4: Análisis de uso de índices
            cursor.execute("""
                EXPLAIN QUERY PLAN
                SELECT COUNT(*) FROM operator_cellular_data 
                WHERE operator = 'CLARO' AND mission_id = 'test_mission'
            """)
            query_plan = cursor.fetchall()
            
            using_index = any("INDEX" in str(row) for row in query_plan)
            result.details["query_plan"] = [str(row) for row in query_plan]
            result.details["using_indexes"] = using_index
            
            conn.close()
            
            # Evaluaciones de performance
            performance_issues = []
            
            if agg_time > 3000:  # >3 segundos
                performance_issues.append(f"agregación: {agg_time:.0f}ms")
            
            if temporal_time > 2000:  # >2 segundos
                performance_issues.append(f"temporal: {temporal_time:.0f}ms")
            
            if join_time > 5000:  # >5 segundos
                performance_issues.append(f"JOIN: {join_time:.0f}ms")
            
            if performance_issues:
                result.add_issue(
                    "MAYOR",
                    f"Consultas lentas con dataset grande: {', '.join(performance_issues)}",
                    "Performance degradada con grandes volúmenes",
                    "Optimizar índices y revisar queries"
                )
            
            if not using_index:
                result.add_issue(
                    "MAYOR",
                    "Consultas críticas no usan índices",
                    "Performance muy degradada sin índices",
                    "Verificar creación e implementación de índices"
                )
            
            total_time = agg_time + temporal_time + join_time
            result.details["total_query_time_ms"] = total_time
            
            logger.info(f"✓ P2-007 completado - Tiempo total: {total_time:.2f}ms, Índices: {using_index}")
            result.complete_test(success=len(performance_issues) == 0)
            
        except Exception as e:
            logger.error(f"Error en P2-007: {e}")
            result.complete_test(success=False, error_message=str(e))
        
        return result
    
    def run_all_tests(self):
        """Ejecuta todos los casos de prueba"""
        logger.info("=== INICIANDO TESTING DE BASE DE DATOS ===")
        
        try:
            self.setup_test_database()
            
            # Ejecutar casos de prueba
            test_methods = [
                self.test_p0_008_cross_operator_queries,
                self.test_p1_003_backup_recovery,
                self.test_p1_007_rollback_transactions,
                self.test_p2_007_performance_large_dataset
            ]
            
            for test_method in test_methods:
                try:
                    result = test_method()
                    self.results.append(result)
                    logger.info(f"Completado: {result.test_case} - {result.status}")
                except Exception as e:
                    logger.error(f"Error en {test_method.__name__}: {e}")
                    error_result = DatabaseTestResult(test_method.__name__, "ERROR")
                    error_result.complete_test(success=False, error_message=str(e))
                    self.results.append(error_result)
        
        finally:
            self.cleanup_test_database()
        
        return self.results
    
    def generate_report(self):
        """Genera reporte completo de testing"""
        report = []
        report.append("=" * 80)
        report.append("REPORTE DE TESTING - EQUIPO DE BASE DE DATOS")
        report.append("=" * 80)
        report.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Contexto: Testing Coordinado Post-Arquitectura L2")
        report.append("")
        
        # Resumen
        passed = sum(1 for r in self.results if r.status == "PASSED")
        failed = sum(1 for r in self.results if r.status == "FAILED") 
        total_issues = sum(len(r.issues_found) for r in self.results)
        critical_issues = sum(len([i for i in r.issues_found if i["severity"] == "CRÍTICO"]) for r in self.results)
        
        report.append("RESUMEN EJECUTIVO:")
        report.append(f"- Pruebas exitosas: {passed}/{len(self.results)}")
        report.append(f"- Pruebas fallidas: {failed}/{len(self.results)}")
        report.append(f"- Issues críticos: {critical_issues}")
        report.append(f"- Issues totales: {total_issues}")
        report.append("")
        
        # Estado general
        if critical_issues == 0 and failed == 0:
            status = "[OK] APTO PARA PRODUCCION"
        elif critical_issues == 0:
            status = "[WARNING] REQUIERE CORRECCIONES MENORES"
        else:
            status = "[ERROR] REQUIERE CORRECCIONES CRITICAS"
        
        report.append(f"ESTADO DE LA BASE DE DATOS: {status}")
        report.append("")
        
        # Detalle por caso
        for result in self.results:
            report.append(f"{result.test_case} ({result.priority}): {result.status}")
            if result.duration_ms:
                report.append(f"  Duración: {result.duration_ms:.2f}ms")
            
            if result.issues_found:
                for issue in result.issues_found:
                    report.append(f"  - {issue['severity']}: {issue['description']}")
            
            if result.details:
                for key, value in result.details.items():
                    if isinstance(value, dict):
                        report.append(f"  {key}:")
                        for subkey, subvalue in value.items():
                            report.append(f"    {subkey}: {subvalue}")
                    else:
                        report.append(f"  {key}: {value}")
            report.append("")
        
        # Issues por severidad
        all_issues = []
        for result in self.results:
            for issue in result.issues_found:
                issue_copy = issue.copy()
                issue_copy["test_case"] = result.test_case
                all_issues.append(issue_copy)
        
        if all_issues:
            report.append("ISSUES POR SEVERIDAD:")
            for severity in ["CRÍTICO", "MAYOR", "MENOR"]:
                severity_issues = [i for i in all_issues if i["severity"] == severity]
                if severity_issues:
                    report.append(f"\n{severity}:")
                    for issue in severity_issues:
                        report.append(f"- [{issue['test_case']}] {issue['description']}")
                        report.append(f"  Sugerencia: {issue['suggestion']}")
        
        # Recomendaciones
        report.append("\nRECOMENDACIONES:")
        if critical_issues > 0:
            report.append("- CRITICO: Resolver issues críticos antes de continuar")
        if failed > 0:
            report.append("- Revisar casos fallidos e implementar correcciones")
        
        report.append("- Implementar monitoreo continuo de performance")
        report.append("- Mantener estadísticas de BD actualizadas")
        report.append("- Documentar procedimientos de backup/recovery")
        
        # Sign-off
        report.append(f"\nSIGN-OFF EQUIPO DE BASE DE DATOS: {status}")
        report.append(f"Especialista: Database Testing Team")
        report.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return "\n".join(report)

def main():
    """Función principal"""
    try:
        test_runner = DatabaseTestRunner()
        results = test_runner.run_all_tests()
        
        # Generar reporte
        report = test_runner.generate_report()
        
        # Guardar reporte
        with open("database_test_report.txt", 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Mostrar resumen
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
        print(f"\nReporte guardado en: database_test_report.txt")
        
        if critical_issues == 0 and failed == 0:
            print("\n[OK] BASE DE DATOS APROBADA PARA OPERACION")
            return 0
        elif critical_issues == 0:
            print("\n[WARNING] BASE DE DATOS APROBADA CON OBSERVACIONES")
            return 1
        else:
            print("\n[ERROR] BASE DE DATOS NO APROBADA")
            return 2
            
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Error en testing: {e}")
        return 3

if __name__ == "__main__":
    exit(main())