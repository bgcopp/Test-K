#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para crear las tablas WOM faltantes en la base de datos.
"""

import sqlite3
import os

def create_wom_tables():
    """Crea las tablas necesarias para WOM"""
    
    db_path = 'kronos.db'
    
    # SQL para crear tabla wom_cellular_data
    create_wom_cellular_data = """
    CREATE TABLE IF NOT EXISTS wom_cellular_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_upload_id VARCHAR NOT NULL,
        mission_id VARCHAR NOT NULL,
        source_sheet VARCHAR,
        operador_tecnologia VARCHAR,
        bts_id INTEGER,
        tac INTEGER,
        cell_id_voz INTEGER,
        sector INTEGER,
        fecha_hora_inicio DATETIME,
        fecha_hora_fin DATETIME,
        operador_ran VARCHAR,
        numero_origen VARCHAR,
        duracion_seg INTEGER,
        up_data_bytes BIGINT,
        down_data_bytes BIGINT,
        imsi VARCHAR,
        imei VARCHAR,
        nombre_antena VARCHAR,
        direccion TEXT,
        latitud REAL,
        longitud REAL,
        localidad VARCHAR,
        ciudad VARCHAR,
        departamento VARCHAR,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (file_upload_id) REFERENCES operator_data_sheets (id),
        FOREIGN KEY (mission_id) REFERENCES missions (id)
    )
    """
    
    # SQL para crear tabla wom_call_data
    create_wom_call_data = """
    CREATE TABLE IF NOT EXISTS wom_call_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_upload_id VARCHAR NOT NULL,
        mission_id VARCHAR NOT NULL,
        source_sheet VARCHAR,
        call_direction VARCHAR,
        operador_tecnologia VARCHAR,
        bts_id INTEGER,
        tac INTEGER,
        cell_id_voz INTEGER,
        sector INTEGER,
        numero_origen VARCHAR,
        numero_destino VARCHAR,
        fecha_hora_inicio DATETIME,
        fecha_hora_fin DATETIME,
        duracion_seg INTEGER,
        operador_ran_origen VARCHAR,
        nombre_antena VARCHAR,
        direccion TEXT,
        latitud REAL,
        longitud REAL,
        localidad VARCHAR,
        ciudad VARCHAR,
        departamento VARCHAR,
        sentido VARCHAR,
        imsi VARCHAR,
        imei VARCHAR,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (file_upload_id) REFERENCES operator_data_sheets (id),
        FOREIGN KEY (mission_id) REFERENCES missions (id)
    )
    """
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            print("Creando tabla wom_cellular_data...")
            cursor.execute(create_wom_cellular_data)
            
            print("Creando tabla wom_call_data...")
            cursor.execute(create_wom_call_data)
            
            # Crear índices para mejor performance
            print("Creando índices...")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_wom_cellular_file_upload ON wom_cellular_data (file_upload_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_wom_cellular_mission ON wom_cellular_data (mission_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_wom_cellular_numero ON wom_cellular_data (numero_origen)")
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_wom_call_file_upload ON wom_call_data (file_upload_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_wom_call_mission ON wom_call_data (mission_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_wom_call_numero ON wom_call_data (numero_origen)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_wom_call_direction ON wom_call_data (call_direction)")
            
            conn.commit()
            print("[OK] Tablas WOM creadas exitosamente")
            
    except Exception as e:
        print(f"[ERROR] Error creando tablas WOM: {e}")
        raise

if __name__ == "__main__":
    print("=" * 60)
    print("CREACIÓN DE TABLAS WOM")
    print("=" * 60)
    
    create_wom_tables()
    
    print("\n" + "=" * 60)
    print("COMPLETADO")
    print("=" * 60)