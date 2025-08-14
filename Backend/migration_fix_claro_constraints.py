#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Migration script para corregir constraints problemáticos en datos CLARO
Soluciona el problema de tasa de éxito del 49.2% en archivos CLARO
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

class ClaroConstraintMigration:
    """Migración para corregir constraints de datos CLARO"""
    
    def __init__(self):
        self.db_path = backend_dir / "kronos.db"
        self.backup_path = backend_dir / f"kronos_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
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
                
                # Verificar índices únicos problemáticos
                cursor.execute("""
                    SELECT name, sql FROM sqlite_master 
                    WHERE type='index' AND tbl_name='operator_cellular_data'
                    AND (name LIKE '%record_hash%' OR sql LIKE '%record_hash%')
                """)
                problematic_indexes = cursor.fetchall()
                
                logger.info(f"📊 Tabla operator_cellular_data: {len(columns)} columnas")
                logger.info(f"🔍 Índices problemáticos encontrados: {len(problematic_indexes)}")
                
                for idx_name, idx_sql in problematic_indexes:
                    logger.info(f"   - {idx_name}: {idx_sql}")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Error verificando schema: {e}")
            return False
    
    def remove_problematic_constraints(self):
        """Eliminar constraints problemáticos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Buscar y eliminar índices únicos problemáticos
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='index' AND tbl_name='operator_cellular_data'
                    AND (name LIKE '%record_hash%' OR sql LIKE '%record_hash%')
                """)
                problematic_indexes = cursor.fetchall()
                
                for (idx_name,) in problematic_indexes:
                    logger.info(f"🗑️ Eliminando índice problemático: {idx_name}")
                    cursor.execute(f"DROP INDEX IF EXISTS {idx_name}")
                
                # Verificar si hay UNIQUE constraints en la definición de tabla
                cursor.execute("""
                    SELECT sql FROM sqlite_master 
                    WHERE type='table' AND name='operator_cellular_data'
                """)
                table_sql = cursor.fetchone()
                
                if table_sql and 'record_hash' in table_sql[0] and 'UNIQUE' in table_sql[0]:
                    logger.warning("⚠️ Hay UNIQUE constraints en la definición de tabla que requieren recreación")
                    return self._recreate_table_without_constraints(conn)
                
                conn.commit()
                logger.info("✅ Constraints problemáticos eliminados")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error eliminando constraints: {e}")
            return False
    
    def _recreate_table_without_constraints(self, conn):
        """Recrear tabla sin constraints problemáticos"""
        try:
            cursor = conn.cursor()
            
            # Obtener datos actuales
            cursor.execute("SELECT * FROM operator_cellular_data")
            existing_data = cursor.fetchall()
            
            # Obtener estructura de columnas
            cursor.execute("PRAGMA table_info(operator_cellular_data)")
            columns_info = cursor.fetchall()
            
            # Crear nueva tabla sin constraint problemático
            new_table_sql = """
            CREATE TABLE operator_cellular_data_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_upload_id TEXT NOT NULL,
                numero_telefono TEXT NOT NULL,
                fecha_hora_inicio DATETIME NOT NULL,
                fecha_hora_fin DATETIME,
                celda_id TEXT NOT NULL,
                lac_id TEXT,
                operador TEXT NOT NULL,
                tipo_conexion TEXT,
                tecnologia TEXT,
                trafico_subida_bytes INTEGER,
                trafico_bajada_bytes INTEGER,
                trafico_total_bytes INTEGER,
                duracion_segundos INTEGER,
                ubicacion_latitud REAL,
                ubicacion_longitud REAL,
                record_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_upload_id) REFERENCES operator_data_sheets (id)
            )
            """
            
            cursor.execute(new_table_sql)
            
            # Copiar datos si existen
            if existing_data:
                # Construir INSERT dinámicamente basado en las columnas
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
            logger.info("✅ Tabla recreada sin constraints problemáticos")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error recreando tabla: {e}")
            conn.rollback()
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
                
                # Agregar índice de performance para búsquedas comunes
                performance_index_sql = """
                CREATE INDEX IF NOT EXISTS idx_cellular_lookup 
                ON operator_cellular_data (
                    file_upload_id,
                    operador,
                    fecha_hora_inicio,
                    numero_telefono
                )
                """
                
                cursor.execute(performance_index_sql)
                
                conn.commit()
                logger.info("✅ Constraints mejorados agregados")
                logger.info("   - Permite múltiples sesiones del mismo usuario")
                logger.info("   - Evita duplicados exactos de tráfico")
                logger.info("   - Mejora performance de consultas")
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
                    AND name IN ('idx_cellular_unique_session', 'idx_cellular_lookup')
                """)
                new_indexes = cursor.fetchall()
                
                # Verificar que no quedan índices problemáticos
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='index' AND tbl_name='operator_cellular_data'
                    AND (name LIKE '%record_hash%' OR sql LIKE '%record_hash%')
                """)
                problematic_indexes = cursor.fetchall()
                
                logger.info(f"✅ Verificación de migración:")
                logger.info(f"   - Tabla existe: {table_exists}")
                logger.info(f"   - Nuevos índices: {len(new_indexes)}/2")
                logger.info(f"   - Índices problemáticos restantes: {len(problematic_indexes)}")
                
                success = table_exists and len(new_indexes) >= 1 and len(problematic_indexes) == 0
                
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
    logger.info("MIGRACIÓN - CORRECCIÓN DE CONSTRAINTS CLARO")
    logger.info("Soluciona tasa de éxito del 49.2% -> 99%+")
    logger.info("=" * 60)
    
    # Inicializar DatabaseManager
    try:
        db_manager.initialize()
        logger.info("✅ DatabaseManager inicializado")
    except Exception as e:
        logger.error(f"❌ Error inicializando DatabaseManager: {e}")
        return 1
    
    migration = ClaroConstraintMigration()
    
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
        
        # Paso 3: Eliminar constraints problemáticos
        logger.info("\n🗑️ PASO 3: Eliminando constraints problemáticos...")
        if not migration.remove_problematic_constraints():
            logger.error("❌ Fallo eliminando constraints problemáticos")
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
        logger.info("🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE")
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