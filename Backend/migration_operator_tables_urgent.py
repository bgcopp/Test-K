#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIGRATION URGENTE: Agregar Tablas de Datos de Operadores
========================================================

Este script crea las tablas faltantes para el módulo de datos de operadores:
- operator_data_sheets
- operator_cellular_data
- operator_call_data
- file_processing_logs
- operator_data_audit
- operator_cell_registry

PROBLEMA RESUELTO:
- Error: "no such table: operator_data_sheets" en dashboard
- Dashboard broken por tablas faltantes

EJECUCIÓN:
python migration_operator_tables_urgent.py

AUTOR: System Migration
FECHA: 2025-08-14
URGENCIA: CRÍTICA
"""

import sqlite3
import os
import sys
from datetime import datetime
import hashlib
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration_operator_tables.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class OperatorTablesMigration:
    """Migración urgente para crear tablas de datos de operadores"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def create_backup(self) -> bool:
        """Crear backup de la base de datos antes de la migración"""
        try:
            logger.info(f"Creando backup: {self.backup_path}")
            
            # Conectar a BD original
            source = sqlite3.connect(self.db_path)
            backup = sqlite3.connect(self.backup_path)
            
            # Crear backup completo
            source.backup(backup)
            
            backup.close()
            source.close()
            
            logger.info("✓ Backup creado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"✗ Error creando backup: {e}")
            return False
    
    def check_existing_tables(self, conn: sqlite3.Connection) -> dict:
        """Verificar qué tablas ya existen"""
        cursor = conn.cursor()
        
        # Lista de tablas que debemos crear
        required_tables = [
            'operator_data_sheets',
            'operator_cellular_data', 
            'operator_call_data',
            'file_processing_logs',
            'operator_data_audit',
            'operator_cell_registry'
        ]
        
        existing_tables = {}
        
        for table in required_tables:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?", 
                (table,)
            )
            existing_tables[table] = cursor.fetchone() is not None
            
        return existing_tables
    
    def ensure_system_user(self, conn: sqlite3.Connection) -> bool:
        """Asegurar que existe el usuario 'system' para foreign keys"""
        try:
            cursor = conn.cursor()
            
            # Verificar si existe el usuario system
            cursor.execute("SELECT id FROM users WHERE id = 'system'")
            if cursor.fetchone():
                logger.info("✓ Usuario 'system' ya existe")
                return True
            
            # Crear usuario system
            cursor.execute("""
                INSERT INTO users (id, username, email, role_id, is_active, created_at)
                VALUES (
                    'system',
                    'system',
                    'system@kronos.internal',
                    (SELECT id FROM roles LIMIT 1),
                    1,
                    CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            logger.info("✓ Usuario 'system' creado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"✗ Error creando usuario system: {e}")
            return False
    
    def create_operator_data_sheets(self, conn: sqlite3.Connection) -> bool:
        """Crear tabla operator_data_sheets"""
        try:
            cursor = conn.cursor()
            
            sql = """
            CREATE TABLE operator_data_sheets (
                -- Identificación primaria
                id TEXT PRIMARY KEY NOT NULL,
                mission_id TEXT NOT NULL,
                
                -- Información del archivo
                file_name TEXT NOT NULL,
                file_size_bytes INTEGER NOT NULL,
                file_checksum TEXT NOT NULL UNIQUE,        -- SHA256 para prevenir duplicados
                file_type TEXT NOT NULL,                   -- 'CELLULAR_DATA' | 'CALL_DATA'
                
                -- Información del operador
                operator TEXT NOT NULL,                    -- 'CLARO' | 'MOVISTAR' | 'TIGO' | 'WOM'
                operator_file_format TEXT NOT NULL,       -- Formato específico del archivo
                
                -- Estado de procesamiento
                processing_status TEXT NOT NULL DEFAULT 'PENDING', -- 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'
                records_processed INTEGER DEFAULT 0,
                records_failed INTEGER DEFAULT 0,
                processing_start_time DATETIME,
                processing_end_time DATETIME,
                processing_duration_seconds INTEGER,
                error_details TEXT,
                
                -- Auditoría
                uploaded_by TEXT NOT NULL,
                uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                -- Relaciones
                FOREIGN KEY (mission_id) REFERENCES missions(id) ON DELETE CASCADE,
                FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE RESTRICT,
                
                -- Validaciones
                CHECK (length(trim(file_name)) > 0),
                CHECK (file_size_bytes > 0 AND file_size_bytes <= 20971520), -- Max 20MB
                CHECK (length(file_checksum) = 64), -- SHA256 hex length
                CHECK (file_type IN ('CELLULAR_DATA', 'CALL_DATA')),
                CHECK (operator IN ('CLARO', 'MOVISTAR', 'TIGO', 'WOM')),
                CHECK (processing_status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')),
                CHECK (records_processed >= 0),
                CHECK (records_failed >= 0),
                CHECK (processing_start_time IS NULL OR processing_end_time IS NULL OR processing_start_time <= processing_end_time)
            );
            """
            
            cursor.execute(sql)
            
            # Crear índices
            indices = [
                "CREATE INDEX idx_operator_sheets_mission_operator ON operator_data_sheets(mission_id, operator);",
                "CREATE INDEX idx_operator_sheets_checksum ON operator_data_sheets(file_checksum);",
                "CREATE INDEX idx_operator_sheets_status ON operator_data_sheets(processing_status);",
                "CREATE INDEX idx_operator_sheets_upload_time ON operator_data_sheets(uploaded_at);",
                "CREATE INDEX idx_operator_sheets_processing_time ON operator_data_sheets(processing_start_time, processing_end_time);"
            ]
            
            for index in indices:
                cursor.execute(index)
            
            # Crear trigger para updated_at
            trigger = """
            CREATE TRIGGER trg_operator_sheets_updated_at
                AFTER UPDATE ON operator_data_sheets
                FOR EACH ROW
                WHEN NEW.updated_at = OLD.updated_at
            BEGIN
                UPDATE operator_data_sheets 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE id = NEW.id;
            END;
            """
            cursor.execute(trigger)
            
            logger.info("✓ Tabla operator_data_sheets creada exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"✗ Error creando operator_data_sheets: {e}")
            return False
    
    def create_operator_cellular_data(self, conn: sqlite3.Connection) -> bool:
        """Crear tabla operator_cellular_data"""
        try:
            cursor = conn.cursor()
            
            sql = """
            CREATE TABLE operator_cellular_data (
                -- Identificación
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_upload_id TEXT NOT NULL,
                mission_id TEXT NOT NULL,
                
                -- Datos normalizados comunes
                operator TEXT NOT NULL,
                numero_telefono TEXT NOT NULL,
                
                -- Información temporal
                fecha_hora_inicio DATETIME NOT NULL,
                fecha_hora_fin DATETIME,
                duracion_segundos INTEGER,
                
                -- Información de celda
                celda_id TEXT NOT NULL,
                lac_tac TEXT,                              -- Location Area Code / Tracking Area Code
                
                -- Datos de tráfico (en bytes)
                trafico_subida_bytes BIGINT DEFAULT 0,
                trafico_bajada_bytes BIGINT DEFAULT 0,
                trafico_total_bytes BIGINT GENERATED ALWAYS AS (trafico_subida_bytes + trafico_bajada_bytes) STORED,
                
                -- Información geográfica
                latitud REAL,
                longitud REAL,
                
                -- Información técnica
                tecnologia TEXT DEFAULT 'UNKNOWN',          -- 'GSM', '3G', 'LTE', '5G', etc.
                tipo_conexion TEXT DEFAULT 'DATOS',         -- 'DATOS', 'SMS', 'MMS'
                calidad_senal INTEGER,                      -- RSSI en dBm (valores negativos)
                
                -- Campos específicos del operador (JSON)
                operator_specific_data TEXT,               -- JSON con campos únicos por operador
                
                -- Control de duplicados y auditoría
                record_hash TEXT NOT NULL,                 -- Hash único para detectar duplicados
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                -- Relaciones
                FOREIGN KEY (file_upload_id) REFERENCES operator_data_sheets(id) ON DELETE CASCADE,
                FOREIGN KEY (mission_id) REFERENCES missions(id) ON DELETE CASCADE,
                
                -- Validaciones geográficas y técnicas
                CHECK (latitud IS NULL OR (latitud >= -90.0 AND latitud <= 90.0)),
                CHECK (longitud IS NULL OR (longitud >= -180.0 AND longitud <= 180.0)),
                CHECK (duracion_segundos IS NULL OR duracion_segundos >= 0),
                CHECK (trafico_subida_bytes >= 0),
                CHECK (trafico_bajada_bytes >= 0),
                CHECK (calidad_senal IS NULL OR calidad_senal <= 0), -- dBm values son negativos
                
                -- Validaciones de formato
                CHECK (length(trim(numero_telefono)) >= 10),
                CHECK (numero_telefono GLOB '[0-9]*'),
                CHECK (length(trim(celda_id)) > 0),
                CHECK (length(trim(operator)) > 0),
                CHECK (tecnologia IN ('GSM', '2G', 'UMTS', '3G', 'LTE', '4G', '5G NR', '5G', 'UNKNOWN')),
                CHECK (tipo_conexion IN ('DATOS', 'SMS', 'MMS')),
                CHECK (operator_specific_data IS NULL OR json_valid(operator_specific_data) = 1),
                
                -- Constraint único para prevenir duplicados exactos
                UNIQUE (file_upload_id, record_hash)
            );
            """
            
            cursor.execute(sql)
            
            # Crear índices optimizados
            indices = [
                "CREATE INDEX idx_cellular_mission_operator ON operator_cellular_data(mission_id, operator);",
                "CREATE INDEX idx_cellular_numero_telefono ON operator_cellular_data(numero_telefono);",
                "CREATE INDEX idx_cellular_numero_mission ON operator_cellular_data(numero_telefono, mission_id);",
                "CREATE INDEX idx_cellular_fecha_hora ON operator_cellular_data(fecha_hora_inicio);",
                "CREATE INDEX idx_cellular_celda_id ON operator_cellular_data(celda_id);",
                "CREATE INDEX idx_cellular_trafico_total ON operator_cellular_data(trafico_total_bytes);",
                "CREATE INDEX idx_cellular_tecnologia ON operator_cellular_data(tecnologia);",
                "CREATE INDEX idx_cellular_geolocation ON operator_cellular_data(latitud, longitud) WHERE latitud IS NOT NULL AND longitud IS NOT NULL;",
                "CREATE INDEX idx_cellular_numero_fecha ON operator_cellular_data(numero_telefono, fecha_hora_inicio);",
                "CREATE INDEX idx_cellular_celda_fecha ON operator_cellular_data(celda_id, fecha_hora_inicio);",
                "CREATE INDEX idx_cellular_operator_fecha ON operator_cellular_data(operator, fecha_hora_inicio);"
            ]
            
            for index in indices:
                cursor.execute(index)
            
            logger.info("✓ Tabla operator_cellular_data creada exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"✗ Error creando operator_cellular_data: {e}")
            return False
    
    def create_operator_call_data(self, conn: sqlite3.Connection) -> bool:
        """Crear tabla operator_call_data"""
        try:
            cursor = conn.cursor()
            
            sql = """
            CREATE TABLE operator_call_data (
                -- Identificación
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_upload_id TEXT NOT NULL,
                mission_id TEXT NOT NULL,
                
                -- Datos normalizados comunes
                operator TEXT NOT NULL,
                tipo_llamada TEXT NOT NULL,               -- 'ENTRANTE', 'SALIENTE', 'MIXTA'
                
                -- Números involucrados
                numero_origen TEXT NOT NULL,
                numero_destino TEXT NOT NULL,
                numero_objetivo TEXT NOT NULL,            -- El número de interés investigativo
                
                -- Información temporal
                fecha_hora_llamada DATETIME NOT NULL,
                duracion_segundos INTEGER DEFAULT 0,
                
                -- Información de celdas
                celda_origen TEXT,
                celda_destino TEXT,
                celda_objetivo TEXT,                      -- Celda del número objetivo
                
                -- Información geográfica
                latitud_origen REAL,
                longitud_origen REAL,
                latitud_destino REAL,
                longitud_destino REAL,
                
                -- Información técnica
                tecnologia TEXT DEFAULT 'UNKNOWN',
                tipo_trafico TEXT DEFAULT 'VOZ',          -- 'VOZ', 'SMS', 'MMS', 'DATOS'
                estado_llamada TEXT DEFAULT 'COMPLETADA', -- 'COMPLETADA', 'NO_CONTESTADA', 'OCUPADO', 'ERROR'
                
                -- Campos específicos del operador (JSON)
                operator_specific_data TEXT,
                
                -- Control de duplicados y auditoría
                record_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                -- Relaciones
                FOREIGN KEY (file_upload_id) REFERENCES operator_data_sheets(id) ON DELETE CASCADE,
                FOREIGN KEY (mission_id) REFERENCES missions(id) ON DELETE CASCADE,
                
                -- Validaciones
                CHECK (tipo_llamada IN ('ENTRANTE', 'SALIENTE', 'MIXTA')),
                CHECK (duracion_segundos >= 0),
                CHECK (length(trim(numero_origen)) >= 7),
                CHECK (length(trim(numero_destino)) >= 7),
                CHECK (length(trim(numero_objetivo)) >= 7),
                CHECK (numero_origen GLOB '[0-9]*'),
                CHECK (numero_destino GLOB '[0-9]*'),
                CHECK (numero_objetivo GLOB '[0-9]*'),
                
                -- Validaciones geográficas
                CHECK (latitud_origen IS NULL OR (latitud_origen >= -90.0 AND latitud_origen <= 90.0)),
                CHECK (longitud_origen IS NULL OR (longitud_origen >= -180.0 AND longitud_origen <= 180.0)),
                CHECK (latitud_destino IS NULL OR (latitud_destino >= -90.0 AND latitud_destino <= 90.0)),
                CHECK (longitud_destino IS NULL OR (longitud_destino >= -180.0 AND longitud_destino <= 180.0)),
                
                -- Validaciones técnicas
                CHECK (tecnologia IN ('GSM', '2G', 'UMTS', '3G', 'LTE', '4G', '5G NR', '5G', 'UNKNOWN')),
                CHECK (tipo_trafico IN ('VOZ', 'SMS', 'MMS', 'DATOS')),
                CHECK (estado_llamada IN ('COMPLETADA', 'NO_CONTESTADA', 'OCUPADO', 'ERROR', 'TRANSFERIDA')),
                CHECK (operator_specific_data IS NULL OR json_valid(operator_specific_data) = 1),
                
                -- Constraint único para prevenir duplicados
                UNIQUE (file_upload_id, record_hash)
            );
            """
            
            cursor.execute(sql)
            
            # Crear índices
            indices = [
                "CREATE INDEX idx_calls_mission_operator ON operator_call_data(mission_id, operator);",
                "CREATE INDEX idx_calls_numero_objetivo ON operator_call_data(numero_objetivo);",
                "CREATE INDEX idx_calls_numero_origen ON operator_call_data(numero_origen);",
                "CREATE INDEX idx_calls_numero_destino ON operator_call_data(numero_destino);",
                "CREATE INDEX idx_calls_objetivo_mission ON operator_call_data(numero_objetivo, mission_id);",
                "CREATE INDEX idx_calls_fecha_hora ON operator_call_data(fecha_hora_llamada);",
                "CREATE INDEX idx_calls_duracion ON operator_call_data(duracion_segundos);",
                "CREATE INDEX idx_calls_tipo ON operator_call_data(tipo_llamada);",
                "CREATE INDEX idx_calls_celda_origen ON operator_call_data(celda_origen);",
                "CREATE INDEX idx_calls_objetivo_fecha ON operator_call_data(numero_objetivo, fecha_hora_llamada);",
                "CREATE INDEX idx_calls_origen_destino ON operator_call_data(numero_origen, numero_destino);",
                "CREATE INDEX idx_calls_tipo_fecha ON operator_call_data(tipo_llamada, fecha_hora_llamada);"
            ]
            
            for index in indices:
                cursor.execute(index)
                
            logger.info("✓ Tabla operator_call_data creada exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"✗ Error creando operator_call_data: {e}")
            return False
    
    def create_supporting_tables(self, conn: sqlite3.Connection) -> bool:
        """Crear tablas de soporte adicionales"""
        try:
            cursor = conn.cursor()
            
            # Tabla file_processing_logs
            cursor.execute("""
            CREATE TABLE file_processing_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_upload_id TEXT NOT NULL,
                
                -- Información del log
                log_level TEXT NOT NULL,                  -- 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
                log_message TEXT NOT NULL,
                log_details TEXT,                         -- JSON con detalles adicionales
                
                -- Contexto del procesamiento
                processing_step TEXT NOT NULL,           -- 'VALIDATION', 'PARSING', 'TRANSFORMATION', 'INSERTION', 'CLEANUP'
                record_number INTEGER,                   -- Número de registro que causó el log (si aplica)
                error_code TEXT,                         -- Código de error específico
                
                -- Información de performance
                execution_time_ms INTEGER,               -- Tiempo de ejecución del paso
                memory_usage_mb REAL,                    -- Uso de memoria durante el procesamiento
                
                -- Timestamp
                logged_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                -- Relaciones
                FOREIGN KEY (file_upload_id) REFERENCES operator_data_sheets(id) ON DELETE CASCADE,
                
                -- Validaciones
                CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
                CHECK (length(trim(log_message)) > 0),
                CHECK (length(trim(processing_step)) > 0),
                CHECK (record_number IS NULL OR record_number > 0),
                CHECK (execution_time_ms IS NULL OR execution_time_ms >= 0),
                CHECK (memory_usage_mb IS NULL OR memory_usage_mb >= 0),
                CHECK (log_details IS NULL OR json_valid(log_details) = 1)
            );
            """)
            
            # Tabla operator_data_audit
            cursor.execute("""
            CREATE TABLE operator_data_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                
                -- Identificación del registro auditado
                table_name TEXT NOT NULL,                -- 'operator_cellular_data' | 'operator_call_data'
                record_id INTEGER NOT NULL,             -- ID del registro modificado
                
                -- Información de la operación
                operation_type TEXT NOT NULL,           -- 'INSERT', 'UPDATE', 'DELETE'
                field_name TEXT,                        -- Campo modificado (para UPDATE)
                old_value TEXT,                         -- Valor anterior (para UPDATE/DELETE)
                new_value TEXT,                         -- Valor nuevo (para INSERT/UPDATE)
                
                -- Contexto de la modificación
                modified_by TEXT NOT NULL,              -- Usuario que realizó el cambio
                modification_reason TEXT,               -- Razón del cambio
                batch_operation_id TEXT,                -- ID de operación en lote (si aplica)
                
                -- Información adicional
                user_agent TEXT,                        -- Cliente que realizó la operación
                ip_address TEXT,                        -- IP de origen
                session_id TEXT,                        -- ID de sesión
                
                -- Timestamp
                audited_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                -- Relaciones
                FOREIGN KEY (modified_by) REFERENCES users(id) ON DELETE RESTRICT,
                
                -- Validaciones
                CHECK (table_name IN ('operator_cellular_data', 'operator_call_data', 'operator_data_sheets')),
                CHECK (operation_type IN ('INSERT', 'UPDATE', 'DELETE')),
                CHECK (record_id > 0),
                CHECK (length(trim(modified_by)) > 0)
            );
            """)
            
            # Tabla operator_cell_registry
            cursor.execute("""
            CREATE TABLE operator_cell_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                
                -- Identificación de celda
                operator TEXT NOT NULL,
                celda_id TEXT NOT NULL,
                lac_tac TEXT,
                
                -- Información geográfica
                latitud REAL,
                longitud REAL,
                ciudad TEXT,
                departamento TEXT,
                
                -- Información técnica
                tecnologia_predominante TEXT,           -- Tecnología más usada en esta celda
                frecuencia_uso INTEGER DEFAULT 1,      -- Cantidad de veces vista
                calidad_promedio_senal REAL,          -- RSSI promedio en dBm
                
                -- Estadísticas agregadas
                trafico_promedio_mb_dia REAL,         -- Tráfico promedio por día
                usuarios_unicos_dia INTEGER,          -- Usuarios únicos por día promedio
                llamadas_promedio_dia INTEGER,        -- Llamadas promedio por día
                
                -- Metadatos
                primera_deteccion DATETIME,           -- Primera vez que se vio esta celda
                ultima_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                -- Validaciones
                CHECK (operator IN ('CLARO', 'MOVISTAR', 'TIGO', 'WOM')),
                CHECK (length(trim(celda_id)) > 0),
                CHECK (latitud IS NULL OR (latitud >= -90.0 AND latitud <= 90.0)),
                CHECK (longitud IS NULL OR (longitud >= -180.0 AND longitud <= 180.0)),
                CHECK (frecuencia_uso > 0),
                CHECK (calidad_promedio_senal IS NULL OR calidad_promedio_senal <= 0),
                CHECK (trafico_promedio_mb_dia IS NULL OR trafico_promedio_mb_dia >= 0),
                CHECK (usuarios_unicos_dia IS NULL OR usuarios_unicos_dia >= 0),
                CHECK (llamadas_promedio_dia IS NULL OR llamadas_promedio_dia >= 0),
                
                -- Constraint único por operador y celda
                UNIQUE (operator, celda_id)
            );
            """)
            
            # Crear índices para las nuevas tablas
            indices = [
                # file_processing_logs
                "CREATE INDEX idx_logs_file_upload ON file_processing_logs(file_upload_id);",
                "CREATE INDEX idx_logs_level_time ON file_processing_logs(log_level, logged_at);",
                "CREATE INDEX idx_logs_step ON file_processing_logs(processing_step);",
                "CREATE INDEX idx_logs_error_code ON file_processing_logs(error_code) WHERE error_code IS NOT NULL;",
                
                # operator_data_audit
                "CREATE INDEX idx_audit_table_record ON operator_data_audit(table_name, record_id);",
                "CREATE INDEX idx_audit_modified_by ON operator_data_audit(modified_by);",
                "CREATE INDEX idx_audit_time ON operator_data_audit(audited_at);",
                "CREATE INDEX idx_audit_operation ON operator_data_audit(operation_type);",
                "CREATE INDEX idx_audit_batch ON operator_data_audit(batch_operation_id) WHERE batch_operation_id IS NOT NULL;",
                
                # operator_cell_registry
                "CREATE INDEX idx_cell_registry_operator_celda ON operator_cell_registry(operator, celda_id);",
                "CREATE INDEX idx_cell_registry_geolocation ON operator_cell_registry(latitud, longitud) WHERE latitud IS NOT NULL AND longitud IS NOT NULL;",
                "CREATE INDEX idx_cell_registry_frecuencia ON operator_cell_registry(frecuencia_uso);",
                "CREATE INDEX idx_cell_registry_tecnologia ON operator_cell_registry(tecnologia_predominante);",
                "CREATE INDEX idx_cell_registry_ciudad ON operator_cell_registry(ciudad);"
            ]
            
            for index in indices:
                cursor.execute(index)
                
            logger.info("✓ Tablas de soporte creadas exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"✗ Error creando tablas de soporte: {e}")
            return False
    
    def create_triggers(self, conn: sqlite3.Connection) -> bool:
        """Crear triggers para auditoría y mantenimiento"""
        try:
            cursor = conn.cursor()
            
            # Trigger para auditoría de operator_cellular_data
            cursor.execute("""
            CREATE TRIGGER trg_cellular_data_audit_insert
                AFTER INSERT ON operator_cellular_data
                FOR EACH ROW
            BEGIN
                INSERT INTO operator_data_audit (
                    table_name, record_id, operation_type,
                    modified_by, audited_at
                ) VALUES (
                    'operator_cellular_data', NEW.id, 'INSERT',
                    'SYSTEM', CURRENT_TIMESTAMP
                );
            END;
            """)
            
            # Trigger para mantener estadísticas en operator_data_sheets
            cursor.execute("""
            CREATE TRIGGER trg_update_processing_stats_cellular
                AFTER INSERT ON operator_cellular_data
                FOR EACH ROW
            BEGIN
                UPDATE operator_data_sheets 
                SET records_processed = records_processed + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = NEW.file_upload_id;
            END;
            """)
            
            cursor.execute("""
            CREATE TRIGGER trg_update_processing_stats_calls
                AFTER INSERT ON operator_call_data
                FOR EACH ROW
            BEGIN
                UPDATE operator_data_sheets 
                SET records_processed = records_processed + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = NEW.file_upload_id;
            END;
            """)
            
            logger.info("✓ Triggers creados exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"✗ Error creando triggers: {e}")
            return False
    
    def run_migration(self) -> bool:
        """Ejecutar migración completa"""
        try:
            logger.info("🚀 INICIANDO MIGRACIÓN URGENTE DE TABLAS DE OPERADORES")
            logger.info("=" * 60)
            
            # Verificar que existe la base de datos
            if not os.path.exists(self.db_path):
                logger.error(f"✗ Base de datos no encontrada: {self.db_path}")
                return False
            
            # Crear backup
            if not self.create_backup():
                return False
            
            # Conectar a la base de datos
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON;")
            
            try:
                # Verificar tablas existentes
                existing_tables = self.check_existing_tables(conn)
                logger.info("\n📋 ESTADO DE TABLAS:")
                for table, exists in existing_tables.items():
                    status = "✓ EXISTS" if exists else "✗ MISSING"
                    logger.info(f"  {table}: {status}")
                
                # Asegurar que existe usuario system
                if not self.ensure_system_user(conn):
                    return False
                
                # Crear tablas que faltan
                success = True
                
                if not existing_tables['operator_data_sheets']:
                    success &= self.create_operator_data_sheets(conn)
                else:
                    logger.info("⏭ operator_data_sheets ya existe, omitiendo")
                
                if not existing_tables['operator_cellular_data']:
                    success &= self.create_operator_cellular_data(conn)
                else:
                    logger.info("⏭ operator_cellular_data ya existe, omitiendo")
                
                if not existing_tables['operator_call_data']:
                    success &= self.create_operator_call_data(conn)
                else:
                    logger.info("⏭ operator_call_data ya existe, omitiendo")
                
                if not existing_tables['file_processing_logs'] or not existing_tables['operator_data_audit'] or not existing_tables['operator_cell_registry']:
                    success &= self.create_supporting_tables(conn)
                else:
                    logger.info("⏭ Tablas de soporte ya existen, omitiendo")
                
                # Crear triggers
                success &= self.create_triggers(conn)
                
                if success:
                    conn.commit()
                    logger.info("\n✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
                    logger.info("🎯 Dashboard debería funcionar ahora sin errores")
                    return True
                else:
                    conn.rollback()
                    logger.error("\n❌ MIGRACIÓN FALLÓ - Rollback ejecutado")
                    return False
                    
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"\n💥 ERROR CRÍTICO EN MIGRACIÓN: {e}")
            return False

def main():
    """Punto de entrada principal"""
    db_path = "kronos.db"
    
    if not os.path.exists(db_path):
        print(f"❌ ERROR: Base de datos no encontrada: {db_path}")
        print("   Asegúrate de estar en el directorio Backend/")
        sys.exit(1)
    
    migration = OperatorTablesMigration(db_path)
    
    if migration.run_migration():
        print("\n🎉 MIGRACIÓN URGENTE COMPLETADA")
        print("📊 Las tablas de operadores han sido creadas")
        print("💻 El dashboard debería funcionar correctamente ahora")
        sys.exit(0)
    else:
        print("\n💀 MIGRACIÓN FALLÓ")
        print("📞 Contacta al equipo de desarrollo")
        sys.exit(1)

if __name__ == "__main__":
    main()