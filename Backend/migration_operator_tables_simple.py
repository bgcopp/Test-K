#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIGRATION URGENTE: Agregar Tablas de Datos de Operadores
========================================================

Script simplificado para crear las tablas faltantes de operadores.
Resuelve el error: "no such table: operator_data_sheets"

EJECUCIÓN:
python migration_operator_tables_simple.py
"""

import sqlite3
import os
import sys
from datetime import datetime

def create_backup(db_path):
    """Crear backup de la base de datos"""
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        source = sqlite3.connect(db_path)
        backup = sqlite3.connect(backup_path)
        source.backup(backup)
        backup.close()
        source.close()
        print(f"BACKUP CREADO: {backup_path}")
        return True
    except Exception as e:
        print(f"ERROR CREANDO BACKUP: {e}")
        return False

def ensure_system_user(conn):
    """Asegurar que existe el usuario 'system'"""
    try:
        cursor = conn.cursor()
        
        # Verificar si existe
        cursor.execute("SELECT id FROM users WHERE id = 'system'")
        if cursor.fetchone():
            print("Usuario 'system' ya existe")
            return True
        
        # Crear usuario system (usando los campos correctos)
        cursor.execute("""
            INSERT INTO users (id, name, email, password_hash, role_id, status, created_at)
            VALUES (
                'system',
                'System User',
                'system@kronos.internal',
                '$2b$12$system_generated_hash_for_kronos_operator_data_processing_module',
                (SELECT id FROM roles LIMIT 1),
                'active',
                CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        print("Usuario 'system' creado")
        return True
        
    except Exception as e:
        print(f"ERROR CREANDO USUARIO SYSTEM: {e}")
        return False

def create_operator_data_sheets(conn):
    """Crear tabla operator_data_sheets"""
    try:
        cursor = conn.cursor()
        
        sql = """
        CREATE TABLE operator_data_sheets (
            id TEXT PRIMARY KEY NOT NULL,
            mission_id TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_size_bytes INTEGER NOT NULL,
            file_checksum TEXT NOT NULL UNIQUE,
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
            
            FOREIGN KEY (mission_id) REFERENCES missions(id) ON DELETE CASCADE,
            FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE RESTRICT,
            
            CHECK (length(trim(file_name)) > 0),
            CHECK (file_size_bytes > 0 AND file_size_bytes <= 20971520),
            CHECK (length(file_checksum) = 64),
            CHECK (file_type IN ('CELLULAR_DATA', 'CALL_DATA')),
            CHECK (operator IN ('CLARO', 'MOVISTAR', 'TIGO', 'WOM')),
            CHECK (processing_status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')),
            CHECK (records_processed >= 0),
            CHECK (records_failed >= 0)
        );
        """
        
        cursor.execute(sql)
        
        # Crear índices básicos
        try:
            cursor.execute("CREATE INDEX idx_operator_sheets_mission_operator ON operator_data_sheets(mission_id, operator);")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("CREATE INDEX idx_operator_sheets_checksum ON operator_data_sheets(file_checksum);")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("CREATE INDEX idx_operator_sheets_status ON operator_data_sheets(processing_status);")
        except sqlite3.OperationalError:
            pass
        
        print("Tabla operator_data_sheets creada")
        return True
        
    except Exception as e:
        print(f"ERROR CREANDO operator_data_sheets: {e}")
        return False

def create_operator_cellular_data(conn):
    """Crear tabla operator_cellular_data"""
    try:
        cursor = conn.cursor()
        
        sql = """
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
            trafico_total_bytes BIGINT GENERATED ALWAYS AS (trafico_subida_bytes + trafico_bajada_bytes) STORED,
            latitud REAL,
            longitud REAL,
            tecnologia TEXT DEFAULT 'UNKNOWN',
            tipo_conexion TEXT DEFAULT 'DATOS',
            calidad_senal INTEGER,
            operator_specific_data TEXT,
            record_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (file_upload_id) REFERENCES operator_data_sheets(id) ON DELETE CASCADE,
            FOREIGN KEY (mission_id) REFERENCES missions(id) ON DELETE CASCADE,
            
            CHECK (latitud IS NULL OR (latitud >= -90.0 AND latitud <= 90.0)),
            CHECK (longitud IS NULL OR (longitud >= -180.0 AND longitud <= 180.0)),
            CHECK (duracion_segundos IS NULL OR duracion_segundos >= 0),
            CHECK (trafico_subida_bytes >= 0),
            CHECK (trafico_bajada_bytes >= 0),
            CHECK (length(trim(numero_telefono)) >= 10),
            CHECK (numero_telefono GLOB '[0-9]*'),
            CHECK (length(trim(celda_id)) > 0),
            CHECK (tecnologia IN ('GSM', '2G', 'UMTS', '3G', 'LTE', '4G', '5G NR', '5G', 'UNKNOWN')),
            CHECK (tipo_conexion IN ('DATOS', 'SMS', 'MMS')),
            
            UNIQUE (file_upload_id, record_hash)
        );
        """
        
        cursor.execute(sql)
        
        # Crear índices esenciales
        try:
            cursor.execute("CREATE INDEX idx_cellular_mission_operator ON operator_cellular_data(mission_id, operator);")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("CREATE INDEX idx_cellular_numero_telefono ON operator_cellular_data(numero_telefono);")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("CREATE INDEX idx_cellular_fecha_hora ON operator_cellular_data(fecha_hora_inicio);")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("CREATE INDEX idx_cellular_celda_id ON operator_cellular_data(celda_id);")
        except sqlite3.OperationalError:
            pass
        
        print("Tabla operator_cellular_data creada")
        return True
        
    except Exception as e:
        print(f"ERROR CREANDO operator_cellular_data: {e}")
        return False

def create_operator_call_data(conn):
    """Crear tabla operator_call_data"""
    try:
        cursor = conn.cursor()
        
        sql = """
        CREATE TABLE operator_call_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_upload_id TEXT NOT NULL,
            mission_id TEXT NOT NULL,
            operator TEXT NOT NULL,
            tipo_llamada TEXT NOT NULL,
            numero_origen TEXT NOT NULL,
            numero_destino TEXT NOT NULL,
            numero_objetivo TEXT NOT NULL,
            fecha_hora_llamada DATETIME NOT NULL,
            duracion_segundos INTEGER DEFAULT 0,
            celda_origen TEXT,
            celda_destino TEXT,
            celda_objetivo TEXT,
            latitud_origen REAL,
            longitud_origen REAL,
            latitud_destino REAL,
            longitud_destino REAL,
            tecnologia TEXT DEFAULT 'UNKNOWN',
            tipo_trafico TEXT DEFAULT 'VOZ',
            estado_llamada TEXT DEFAULT 'COMPLETADA',
            operator_specific_data TEXT,
            record_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (file_upload_id) REFERENCES operator_data_sheets(id) ON DELETE CASCADE,
            FOREIGN KEY (mission_id) REFERENCES missions(id) ON DELETE CASCADE,
            
            CHECK (tipo_llamada IN ('ENTRANTE', 'SALIENTE', 'MIXTA')),
            CHECK (duracion_segundos >= 0),
            CHECK (length(trim(numero_origen)) >= 7),
            CHECK (length(trim(numero_destino)) >= 7),
            CHECK (length(trim(numero_objetivo)) >= 7),
            CHECK (numero_origen GLOB '[0-9]*'),
            CHECK (numero_destino GLOB '[0-9]*'),
            CHECK (numero_objetivo GLOB '[0-9]*'),
            CHECK (tecnologia IN ('GSM', '2G', 'UMTS', '3G', 'LTE', '4G', '5G NR', '5G', 'UNKNOWN')),
            CHECK (tipo_trafico IN ('VOZ', 'SMS', 'MMS', 'DATOS')),
            CHECK (estado_llamada IN ('COMPLETADA', 'NO_CONTESTADA', 'OCUPADO', 'ERROR', 'TRANSFERIDA')),
            
            UNIQUE (file_upload_id, record_hash)
        );
        """
        
        cursor.execute(sql)
        
        # Crear índices esenciales
        try:
            cursor.execute("CREATE INDEX idx_calls_mission_operator ON operator_call_data(mission_id, operator);")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("CREATE INDEX idx_calls_numero_objetivo ON operator_call_data(numero_objetivo);")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("CREATE INDEX idx_calls_fecha_hora ON operator_call_data(fecha_hora_llamada);")
        except sqlite3.OperationalError:
            pass
        
        print("Tabla operator_call_data creada")
        return True
        
    except Exception as e:
        print(f"ERROR CREANDO operator_call_data: {e}")
        return False

def main():
    """Función principal"""
    db_path = "kronos.db"
    
    if not os.path.exists(db_path):
        print(f"ERROR: Base de datos no encontrada: {db_path}")
        sys.exit(1)
    
    print("INICIANDO MIGRACION URGENTE")
    print("=" * 40)
    
    # Crear backup
    if not create_backup(db_path):
        print("ERROR: No se pudo crear backup")
        sys.exit(1)
    
    # Conectar a la base de datos
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    
    try:
        # Verificar tablas existentes
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='operator_data_sheets'")
        if cursor.fetchone():
            print("operator_data_sheets ya existe")
        else:
            print("Creando operator_data_sheets...")
            if not ensure_system_user(conn):
                raise Exception("No se pudo crear usuario system")
            if not create_operator_data_sheets(conn):
                raise Exception("No se pudo crear operator_data_sheets")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='operator_cellular_data'")
        if cursor.fetchone():
            print("operator_cellular_data ya existe")
        else:
            print("Creando operator_cellular_data...")
            if not create_operator_cellular_data(conn):
                raise Exception("No se pudo crear operator_cellular_data")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='operator_call_data'")
        if cursor.fetchone():
            print("operator_call_data ya existe")
        else:
            print("Creando operator_call_data...")
            if not create_operator_call_data(conn):
                raise Exception("No se pudo crear operator_call_data")
        
        conn.commit()
        print("\nMIGRACION COMPLETADA EXITOSAMENTE")
        print("Las tablas de operadores han sido creadas")
        print("El dashboard deberia funcionar ahora")
        
    except Exception as e:
        conn.rollback()
        print(f"\nERROR EN MIGRACION: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()