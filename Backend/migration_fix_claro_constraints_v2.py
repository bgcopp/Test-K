#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Migration script v2 para corregir constraints problemáticos en datos CLARO
Soluciona el problema de tasa de éxito del 49.2% en archivos CLARO
VERSIÓN CORREGIDA para el schema actual
"""

import sys
import os
import sqlite3
from pathlib import Path
from datetime import datetime
import logging

# Agregar el directorio Backend al path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from database.connection import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClaroConstraintMigrationV2:
    """Migración para corregir constraints de datos CLARO - Versión 2"""
    
    def __init__(self):
        self.db_path = backend_dir / "kronos.db"
        self.backup_path = backend_dir / f"kronos_backup_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
    def create_backup(self):
        """Crear backup de la base de datos"""
        try:
            import shutil
            shutil.copy2(self.db_path, self.backup_path)
            logger.info(f"✅ Backup creado: {self.backup_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Error creando backup: {e}")
            return False
    
    def check_current_schema(self):
        """Verificar estado actual del schema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar si existe la tabla operator_cellular_data
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='operator_cellular_data'
                """)
                table_exists = cursor.fetchone() is not None
                
                if not table_exists:
                    logger.warning("⚠️ Tabla operator_cellular_data no existe")
                    return False
                
                # Verificar constraints actuales
                cursor.execute("PRAGMA table_info(operator_cellular_data)")
                columns = cursor.fetchall()
                
                # Verificar definición de tabla para constraint problemático
                cursor.execute("""
                    SELECT sql FROM sqlite_master 
                    WHERE type='table' AND name='operator_cellular_data'
                """)
                table_sql = cursor.fetchone()
                
                logger.info(f"📊 Tabla operator_cellular_data: {len(columns)} columnas")
                
                has_problematic_constraint = False
                if table_sql and 'UNIQUE (file_upload_id, record_hash)' in table_sql[0]:
                    has_problematic_constraint = True
                    logger.info("🔍 Constraint problemático encontrado: UNIQUE (file_upload_id, record_hash)")
                else:
                    logger.info("✅ No se encontró el constraint problemático")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Error verificando schema: {e}")
            return False
    
    def recreate_table_without_problematic_constraint(self):
        """Recrear tabla eliminando el constraint problemático"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Obtener datos actuales
                cursor.execute("SELECT * FROM operator_cellular_data")
                existing_data = cursor.fetchall()
                
                # Obtener estructura de columnas
                cursor.execute("PRAGMA table_info(operator_cellular_data)")
                columns_info = cursor.fetchall()
                
                logger.info(f"📦 Preparando migración de {len(existing_data)} registros")
                
                # Crear nueva tabla sin constraint problemático pero con constraint mejorado
                new_table_sql = """
                CREATE TABLE operator_cellular_data_new (
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
                    CHECK (operator_specific_data IS NULL OR json_valid(operator_specific_data) = 1)
                    
                    -- NO incluir el constraint problemático UNIQUE (file_upload_id, record_hash)
                )
                """
                
                cursor.execute(new_table_sql)
                logger.info("✅ Tabla nueva creada sin constraint problemático")
                
                # Copiar datos si existen
                if existing_data:
                    # Construir INSERT dinámicamente basado en las columnas (excluyendo id)
                    column_names = [col[1] for col in columns_info if col[1] != 'id']
                    placeholders = ','.join(['?' for _ in column_names])
                    insert_sql = f"""
                        INSERT INTO operator_cellular_data_new ({','.join(column_names)})
                        SELECT {','.join(column_names)} FROM operator_cellular_data
                    """
                    cursor.execute(insert_sql)
                    logger.info(f"📦 Copiados {len(existing_data)} registros a nueva tabla")
                
                # Eliminar tabla antigua y renombrar nueva
                cursor.execute("DROP TABLE operator_cellular_data")
                cursor.execute("ALTER TABLE operator_cellular_data_new RENAME TO operator_cellular_data")
                
                conn.commit()
                logger.info("✅ Tabla recreada sin constraint problemático")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error recreando tabla: {e}")
            return False
    
    def add_improved_constraints(self):
        """Agregar constraints mejorados para datos celulares"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Agregar índice único mejorado para datos celulares
                # Permite múltiples sesiones del mismo usuario, pero evita duplicados exactos
                improved_constraint_sql = """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_cellular_unique_session 
                ON operator_cellular_data (
                    file_upload_id, 
                    numero_telefono, 
                    fecha_hora_inicio, 
                    celda_id,
                    COALESCE(trafico_subida_bytes, 0),
                    COALESCE(trafico_bajada_bytes, 0)
                )
                """
                
                cursor.execute(improved_constraint_sql)
                
                # Recrear índices de performance que se perdieron
                performance_indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_cellular_numero_telefono ON operator_cellular_data(numero_telefono)",
                    "CREATE INDEX IF NOT EXISTS idx_cellular_numero_mission ON operator_cellular_data(numero_telefono, mission_id)",
                    "CREATE INDEX IF NOT EXISTS idx_cellular_fecha_hora ON operator_cellular_data(fecha_hora_inicio)",
                    "CREATE INDEX IF NOT EXISTS idx_cellular_celda_id ON operator_cellular_data(celda_id)",
                    "CREATE INDEX IF NOT EXISTS idx_cellular_trafico_total ON operator_cellular_data(trafico_total_bytes)",
                    "CREATE INDEX IF NOT EXISTS idx_cellular_geolocation ON operator_cellular_data(latitud, longitud) WHERE latitud IS NOT NULL AND longitud IS NOT NULL",
                    "CREATE INDEX IF NOT EXISTS idx_cellular_numero_fecha ON operator_cellular_data(numero_telefono, fecha_hora_inicio)",
                    "CREATE INDEX IF NOT EXISTS idx_cellular_celda_fecha ON operator_cellular_data(celda_id, fecha_hora_inicio)",
                    "CREATE INDEX IF NOT EXISTS idx_cellular_operator_fecha ON operator_cellular_data(operator, fecha_hora_inicio)"
                ]
                
                for idx_sql in performance_indexes:
                    cursor.execute(idx_sql)
                
                conn.commit()
                logger.info("✅ Constraints mejorados agregados")
                logger.info("   - Permite múltiples sesiones del mismo usuario/celda/tiempo")
                logger.info("   - Evita duplicados exactos incluyendo tráfico")
                logger.info("   - Recrea todos los índices de performance")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error agregando constraints mejorados: {e}")
            return False
    
    def verify_migration(self):
        """Verificar que la migración fue exitosa"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar que la tabla existe
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='operator_cellular_data'
                """)
                table_exists = cursor.fetchone() is not None
                
                if not table_exists:
                    logger.error("❌ Tabla operator_cellular_data no existe después de migración")
                    return False
                
                # Verificar nuevos índices
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='index' AND tbl_name='operator_cellular_data'
                    AND name = 'idx_cellular_unique_session'
                """)
                new_unique_index = cursor.fetchone() is not None
                
                # Verificar que NO queda el constraint problemático
                cursor.execute("""
                    SELECT sql FROM sqlite_master 
                    WHERE type='table' AND name='operator_cellular_data'
                """)
                table_sql = cursor.fetchone()
                
                has_old_constraint = False
                if table_sql and 'UNIQUE (file_upload_id, record_hash)' in table_sql[0]:
                    has_old_constraint = True
                
                # Contar registros para verificar integridad
                cursor.execute("SELECT COUNT(*) FROM operator_cellular_data")
                record_count = cursor.fetchone()[0]
                
                logger.info(f"✅ Verificación de migración:")
                logger.info(f"   - Tabla existe: {table_exists}")
                logger.info(f"   - Nuevo índice único: {new_unique_index}")
                logger.info(f"   - Constraint problemático eliminado: {not has_old_constraint}")
                logger.info(f"   - Registros preservados: {record_count}")
                
                success = table_exists and new_unique_index and not has_old_constraint
                
                if success:
                    logger.info("🎉 Migración completada exitosamente")
                else:
                    logger.error("❌ Migración falló verificación")
                
                return success
                
        except Exception as e:
            logger.error(f"❌ Error verificando migración: {e}")
            return False
    
    def rollback(self):
        """Rollback a backup si algo falla"""
        try:
            if self.backup_path.exists():
                import shutil
                shutil.copy2(self.backup_path, self.db_path)
                logger.info(f"🔄 Rollback completado desde: {self.backup_path}")
                return True
            else:
                logger.error("❌ No se encontró backup para rollback")
                return False
        except Exception as e:
            logger.error(f"❌ Error en rollback: {e}")
            return False

def main():
    """Función principal de migración"""
    logger.info("=" * 60)
    logger.info("MIGRACIÓN V2 - CORRECCIÓN DE CONSTRAINTS CLARO")
    logger.info("Soluciona tasa de éxito del 49.2% -> 99%+")
    logger.info("=" * 60)
    
    # Inicializar DatabaseManager
    try:
        db_manager.initialize()
        logger.info("✅ DatabaseManager inicializado")
    except Exception as e:
        logger.error(f"❌ Error inicializando DatabaseManager: {e}")
        return 1
    
    migration = ClaroConstraintMigrationV2()
    
    try:
        # Paso 1: Verificar estado actual
        logger.info("\n📋 PASO 1: Verificando estado actual...")
        if not migration.check_current_schema():
            logger.error("❌ Fallo verificación de schema actual")
            return 1
        
        # Paso 2: Crear backup
        logger.info("\n💾 PASO 2: Creando backup...")
        if not migration.create_backup():
            logger.error("❌ Fallo creación de backup")
            return 1
        
        # Paso 3: Recrear tabla sin constraint problemático
        logger.info("\n🔧 PASO 3: Recreando tabla sin constraint problemático...")
        if not migration.recreate_table_without_problematic_constraint():
            logger.error("❌ Fallo recreando tabla")
            logger.info("🔄 Iniciando rollback...")
            migration.rollback()
            return 1
        
        # Paso 4: Agregar constraints mejorados
        logger.info("\n✨ PASO 4: Agregando constraints mejorados...")
        if not migration.add_improved_constraints():
            logger.error("❌ Fallo agregando constraints mejorados")
            logger.info("🔄 Iniciando rollback...")
            migration.rollback()
            return 1
        
        # Paso 5: Verificar migración
        logger.info("\n🔍 PASO 5: Verificando migración...")
        if not migration.verify_migration():
            logger.error("❌ Fallo verificación de migración")
            logger.info("🔄 Iniciando rollback...")
            migration.rollback()
            return 1
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 MIGRACIÓN V2 COMPLETADA EXITOSAMENTE")
        logger.info("Archivos CLARO deberían tener 99%+ tasa de éxito ahora")
        logger.info(f"Backup disponible en: {migration.backup_path}")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error inesperado durante migración: {e}")
        logger.info("🔄 Iniciando rollback...")
        migration.rollback()
        return 1

if __name__ == "__main__":
    sys.exit(main())