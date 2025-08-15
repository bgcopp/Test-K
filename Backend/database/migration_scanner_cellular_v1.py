"""
KRONOS Database Migration - Scanner Cellular Data v1.0
====================================================================
Migración para implementar el nuevo schema optimizado de datos de
scanner celular con soporte completo para formato SCANHUNTER.

IMPORTANTE: Esta migración es REVERSIBLE y mantiene compatibilidad
con el sistema existente.

Características de la migración:
- Crea nueva tabla scanner_cellular_data optimizada
- Migra datos existentes de cellular_data (si existen)
- Implementa índices optimizados
- Crea vistas de compatibilidad
- Mantiene triggers de auditoría
- Soporte para rollback completo
====================================================================
"""

import sqlite3
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import hashlib

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ScannerCellularMigrationV1:
    """
    Migración principal para schema de scanner cellular data
    """
    
    def __init__(self, db_path: str):
        """
        Inicializa la migración
        
        Args:
            db_path: Ruta a la base de datos SQLite
        """
        self.db_path = db_path
        self.migration_id = "scanner_cellular_v1"
        self.migration_date = datetime.now().isoformat()
        self.backup_path = None
        
    def execute(self, create_backup: bool = True) -> bool:
        """
        Ejecuta la migración completa
        
        Args:
            create_backup: Si crear backup antes de la migración
            
        Returns:
            True si la migración fue exitosa
        """
        try:
            logger.info(f"Iniciando migración {self.migration_id}")
            
            # Verificar estado actual
            if not self._check_preconditions():
                logger.error("Precondiciones de migración no cumplidas")
                return False
            
            # Crear backup si se solicita
            if create_backup:
                self._create_backup()
            
            # Ejecutar pasos de migración
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = OFF")
                
                # Paso 1: Crear nueva tabla optimizada
                self._create_scanner_cellular_table(conn)
                
                # Paso 2: Migrar datos existentes
                self._migrate_existing_data(conn)
                
                # Paso 3: Crear índices optimizados
                self._create_optimized_indexes(conn)
                
                # Paso 4: Crear vistas de compatibilidad
                self._create_compatibility_views(conn)
                
                # Paso 5: Crear triggers de mantenimiento
                self._create_maintenance_triggers(conn)
                
                # Paso 6: Crear tabla de operadores
                self._create_operators_table(conn)
                
                # Paso 7: Registrar migración
                self._register_migration(conn)
                
                conn.execute("PRAGMA foreign_keys = ON")
                conn.commit()
            
            logger.info(f"Migración {self.migration_id} completada exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error en migración {self.migration_id}: {str(e)}")
            if create_backup and self.backup_path:
                logger.info(f"Restaurando backup desde {self.backup_path}")
                self._restore_backup()
            return False
    
    def rollback(self) -> bool:
        """
        Revierte la migración
        
        Returns:
            True si el rollback fue exitoso
        """
        try:
            logger.info(f"Iniciando rollback de migración {self.migration_id}")
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = OFF")
                
                # Eliminar objetos creados por la migración
                self._drop_migration_objects(conn)
                
                # Remover registro de migración
                conn.execute("""
                    DELETE FROM migration_history 
                    WHERE migration_id = ?
                """, (self.migration_id,))
                
                conn.execute("PRAGMA foreign_keys = ON")
                conn.commit()
            
            logger.info(f"Rollback de migración {self.migration_id} completado")
            return True
            
        except Exception as e:
            logger.error(f"Error en rollback de migración {self.migration_id}: {str(e)}")
            return False
    
    def _check_preconditions(self) -> bool:
        """Verifica que se cumplan las precondiciones para la migración"""
        try:
            if not os.path.exists(self.db_path):
                logger.error(f"Base de datos no existe: {self.db_path}")
                return False
            
            with sqlite3.connect(self.db_path) as conn:
                # Verificar que no exista ya la nueva tabla
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='scanner_cellular_data'
                """)
                
                if cursor.fetchone():
                    logger.warning("Tabla scanner_cellular_data ya existe")
                    return False
                
                # Verificar que exista tabla missions
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='missions'
                """)
                
                if not cursor.fetchone():
                    logger.error("Tabla missions requerida no existe")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error verificando precondiciones: {str(e)}")
            return False
    
    def _create_backup(self) -> None:
        """Crea backup de la base de datos"""
        self.backup_path = f"{self.db_path}.backup_{self.migration_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with open(self.db_path, 'rb') as src, open(self.backup_path, 'wb') as dst:
            dst.write(src.read())
        
        logger.info(f"Backup creado en: {self.backup_path}")
    
    def _restore_backup(self) -> None:
        """Restaura backup de la base de datos"""
        if self.backup_path and os.path.exists(self.backup_path):
            with open(self.backup_path, 'rb') as src, open(self.db_path, 'wb') as dst:
                dst.write(src.read())
            logger.info("Backup restaurado exitosamente")
    
    def _create_scanner_cellular_table(self, conn: sqlite3.Connection) -> None:
        """Crea la nueva tabla optimizada para scanner cellular data"""
        logger.info("Creando tabla scanner_cellular_data")
        
        conn.execute("""
            CREATE TABLE scanner_cellular_data (
                -- Identificación única
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mission_id TEXT NOT NULL,
                
                -- Información del punto de medición
                punto TEXT NOT NULL CHECK (length(trim(punto)) > 0),
                measurement_sequence INTEGER,
                
                -- Coordenadas geográficas
                latitude REAL NOT NULL CHECK (latitude >= -90.0 AND latitude <= 90.0),
                longitude REAL NOT NULL CHECK (longitude >= -180.0 AND longitude <= 180.0),
                coordinate_precision INTEGER DEFAULT 6,
                
                -- Información de red celular
                mnc_mcc TEXT NOT NULL CHECK (length(mnc_mcc) >= 5 AND mnc_mcc GLOB '[0-9]*'),
                operator_name TEXT NOT NULL CHECK (length(trim(operator_name)) > 0),
                operator_code TEXT,
                
                -- Métricas de señal
                rssi_dbm INTEGER NOT NULL CHECK (rssi_dbm <= 0 AND rssi_dbm >= -150),
                signal_quality TEXT GENERATED ALWAYS AS (
                    CASE 
                        WHEN rssi_dbm >= -70 THEN 'Excelente'
                        WHEN rssi_dbm >= -85 THEN 'Buena' 
                        WHEN rssi_dbm >= -100 THEN 'Regular'
                        ELSE 'Mala'
                    END
                ) STORED,
                
                -- Información técnica de celda
                technology TEXT NOT NULL CHECK (
                    technology IN ('GSM', 'UMTS', '3G', 'LTE', '4G', '5G NR', '5G', 'UNKNOWN')
                ),
                cell_id TEXT NOT NULL CHECK (length(trim(cell_id)) > 0),
                lac_tac TEXT CHECK (lac_tac IS NULL OR length(trim(lac_tac)) > 0),
                enb_id TEXT CHECK (enb_id IS NULL OR length(trim(enb_id)) > 0),
                
                -- Información de canal/frecuencia
                channel TEXT CHECK (channel IS NULL OR length(trim(channel)) > 0),
                frequency_band TEXT,
                
                -- Metadatos de medición
                comentario TEXT,
                measurement_timestamp DATETIME,
                
                -- Auditoría y procesamiento
                file_source TEXT,
                processing_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                data_hash TEXT,
                is_validated BOOLEAN DEFAULT 0,
                validation_errors TEXT,
                
                -- Relaciones
                FOREIGN KEY (mission_id) REFERENCES missions(id) ON DELETE CASCADE
            )
        """)
    
    def _migrate_existing_data(self, conn: sqlite3.Connection) -> None:
        """Migra datos existentes de cellular_data a scanner_cellular_data"""
        logger.info("Verificando datos existentes para migrar")
        
        # Verificar si existe tabla cellular_data con datos
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='cellular_data'
        """)
        
        if not cursor.fetchone():
            logger.info("No existe tabla cellular_data - omitiendo migración de datos")
            return
        
        cursor = conn.execute("SELECT COUNT(*) FROM cellular_data")
        count = cursor.fetchone()[0]
        
        if count == 0:
            logger.info("Tabla cellular_data vacía - omitiendo migración")
            return
        
        logger.info(f"Migrando {count} registros de cellular_data")
        
        # Mapear datos de tabla anterior a nueva estructura
        conn.execute("""
            INSERT INTO scanner_cellular_data (
                mission_id, punto, latitude, longitude, mnc_mcc, operator_name,
                rssi_dbm, technology, cell_id, lac_tac, enb_id, comentario, 
                channel, processing_timestamp, is_validated
            )
            SELECT 
                mission_id,
                COALESCE(punto, 'MIGRATED_' || id) as punto,
                CAST(lat as REAL) as latitude,
                CAST(lon as REAL) as longitude,
                COALESCE(mnc_mcc, '732000') as mnc_mcc,
                COALESCE(operator, 'UNKNOWN') as operator_name,
                rssi as rssi_dbm,
                COALESCE(tecnologia, 'UNKNOWN') as technology,
                cell_id,
                lac_tac,
                enb,
                comentario,
                channel,
                created_at as processing_timestamp,
                1 as is_validated
            FROM cellular_data
            WHERE mission_id IS NOT NULL
        """)
        
        migrated_count = conn.execute("SELECT changes()").fetchone()[0]
        logger.info(f"Migrados {migrated_count} registros exitosamente")
    
    def _create_optimized_indexes(self, conn: sqlite3.Connection) -> None:
        """Crea índices optimizados para consultas frecuentes"""
        logger.info("Creando índices optimizados")
        
        indexes = [
            # Índices primarios
            ("idx_scanner_cellular_mission", "scanner_cellular_data", ["mission_id"]),
            ("idx_scanner_cellular_coverage_analysis", "scanner_cellular_data", 
             ["mission_id", "operator_name", "technology", "rssi_dbm", "latitude", "longitude"]),
            ("idx_scanner_cellular_operator_tech", "scanner_cellular_data", 
             ["mission_id", "operator_name", "technology"]),
            
            # Índices secundarios
            ("idx_scanner_cellular_coordinates", "scanner_cellular_data", ["latitude", "longitude"]),
            ("idx_scanner_cellular_signal_analysis", "scanner_cellular_data", 
             ["mission_id", "rssi_dbm", "technology"]),
            ("idx_scanner_cellular_cell_lookup", "scanner_cellular_data", ["cell_id", "operator_name"]),
            
            # Índices de soporte
            ("idx_scanner_cellular_punto", "scanner_cellular_data", ["mission_id", "punto"]),
            ("idx_scanner_cellular_lac_tac", "scanner_cellular_data", ["lac_tac", "technology"]),
            ("idx_scanner_cellular_deduplication", "scanner_cellular_data", ["data_hash"]),
        ]
        
        for index_name, table_name, columns in indexes:
            columns_str = ", ".join(columns)
            conn.execute(f"""
                CREATE INDEX IF NOT EXISTS {index_name} 
                ON {table_name}({columns_str})
            """)
            logger.info(f"Índice creado: {index_name}")
    
    def _create_compatibility_views(self, conn: sqlite3.Connection) -> None:
        """Crea vistas para mantener compatibilidad con código existente"""
        logger.info("Creando vistas de compatibilidad")
        
        # Vista para análisis de cobertura
        conn.execute("""
            CREATE VIEW IF NOT EXISTS vw_scanner_coverage_summary AS
            SELECT 
                mission_id,
                operator_name,
                technology,
                COUNT(*) as total_measurements,
                AVG(rssi_dbm) as avg_rssi,
                MIN(rssi_dbm) as min_rssi,
                MAX(rssi_dbm) as max_rssi,
                COUNT(DISTINCT punto) as unique_points,
                COUNT(DISTINCT cell_id) as unique_cells,
                SUM(CASE WHEN rssi_dbm >= -85 THEN 1 ELSE 0 END) as good_signal_count,
                SUM(CASE WHEN rssi_dbm < -100 THEN 1 ELSE 0 END) as poor_signal_count,
                MIN(latitude) as min_lat,
                MAX(latitude) as max_lat,
                MIN(longitude) as min_lon,
                MAX(longitude) as max_lon
            FROM scanner_cellular_data
            WHERE is_validated = 1
            GROUP BY mission_id, operator_name, technology
        """)
        
        # Vista para detección de anomalías
        conn.execute("""
            CREATE VIEW IF NOT EXISTS vw_scanner_anomalies AS
            SELECT 
                scd.*,
                'RSSI_ANOMALY' as anomaly_type,
                'RSSI value outside expected range' as anomaly_description
            FROM scanner_cellular_data scd
            WHERE scd.rssi_dbm > -30 OR scd.rssi_dbm < -120
            
            UNION ALL
            
            SELECT 
                scd.*,
                'DUPLICATE_MEASUREMENT' as anomaly_type,
                'Potential duplicate measurement detected' as anomaly_description
            FROM scanner_cellular_data scd
            WHERE EXISTS (
                SELECT 1 FROM scanner_cellular_data scd2 
                WHERE scd2.id != scd.id 
                AND scd2.mission_id = scd.mission_id
                AND scd2.punto = scd.punto
                AND scd2.cell_id = scd.cell_id
                AND ABS(scd2.latitude - scd.latitude) < 0.0001
                AND ABS(scd2.longitude - scd.longitude) < 0.0001
            )
        """)
        
        # Vista para estadísticas de misión
        conn.execute("""
            CREATE VIEW IF NOT EXISTS vw_mission_scanner_stats AS
            SELECT 
                m.id as mission_id,
                m.name as mission_name,
                COUNT(scd.id) as total_measurements,
                COUNT(DISTINCT scd.operator_name) as operators_count,
                COUNT(DISTINCT scd.technology) as technologies_count,
                COUNT(DISTINCT scd.punto) as measurement_points,
                AVG(scd.rssi_dbm) as avg_signal_strength,
                MIN(scd.processing_timestamp) as first_upload,
                MAX(scd.processing_timestamp) as last_upload
            FROM missions m
            LEFT JOIN scanner_cellular_data scd ON m.id = scd.mission_id
            GROUP BY m.id, m.name
        """)
    
    def _create_maintenance_triggers(self, conn: sqlite3.Connection) -> None:
        """Crea triggers para mantenimiento automático"""
        logger.info("Creando triggers de mantenimiento")
        
        # Trigger para generar hash automáticamente
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS trg_scanner_cellular_data_hash
                AFTER INSERT ON scanner_cellular_data
                FOR EACH ROW
            BEGIN
                UPDATE scanner_cellular_data 
                SET data_hash = hex(
                    printf('%s|%s|%s|%s|%s|%s|%s|%s', 
                        NEW.mission_id, NEW.punto, NEW.latitude, NEW.longitude, 
                        NEW.cell_id, NEW.operator_name, NEW.rssi_dbm, NEW.technology
                    )
                ) 
                WHERE id = NEW.id;
            END
        """)
        
        # Trigger para actualizar timestamp de procesamiento
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS trg_scanner_cellular_data_processing_time
                AFTER UPDATE ON scanner_cellular_data
                FOR EACH ROW
            BEGIN
                UPDATE scanner_cellular_data 
                SET processing_timestamp = CURRENT_TIMESTAMP 
                WHERE id = NEW.id;
            END
        """)
    
    def _create_operators_table(self, conn: sqlite3.Connection) -> None:
        """Crea tabla de configuración de operadores"""
        logger.info("Creando tabla de operadores")
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cellular_operators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operator_name TEXT NOT NULL UNIQUE,
                mnc_codes TEXT NOT NULL,
                country_code TEXT DEFAULT '732',
                frequency_bands TEXT,
                technologies TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insertar operadores colombianos
        operators = [
            ('CLARO', '["101", "102", "103", "123"]', '["850", "1900", "1700", "2600"]', '["GSM", "UMTS", "LTE", "5G"]'),
            ('MOVISTAR', '["111", "123"]', '["850", "1900", "1700"]', '["GSM", "UMTS", "LTE"]'),
            ('TIGO', '["103", "111"]', '["850", "1900", "1700"]', '["GSM", "UMTS", "LTE"]'),
            ('WOM', '["130"]', '["1700", "2600"]', '["LTE", "5G"]'),
            ('PARTNERS', '["154"]', '["1900"]', '["LTE"]'),
            ('ETB', '["103"]', '["1700"]', '["LTE"]'),
        ]
        
        for name, mnc_codes, freq_bands, technologies in operators:
            conn.execute("""
                INSERT OR IGNORE INTO cellular_operators 
                (operator_name, mnc_codes, frequency_bands, technologies) 
                VALUES (?, ?, ?, ?)
            """, (name, mnc_codes, freq_bands, technologies))
    
    def _register_migration(self, conn: sqlite3.Connection) -> None:
        """Registra la migración en el historial"""
        logger.info("Registrando migración en historial")
        
        # Crear tabla de historial de migraciones si no existe
        conn.execute("""
            CREATE TABLE IF NOT EXISTS migration_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                migration_id TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                executed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                execution_time_seconds REAL,
                success BOOLEAN DEFAULT 1,
                rollback_available BOOLEAN DEFAULT 1,
                metadata TEXT
            )
        """)
        
        metadata = {
            "version": "1.0",
            "backup_path": self.backup_path,
            "objects_created": [
                "scanner_cellular_data",
                "cellular_operators",
                "vw_scanner_coverage_summary",
                "vw_scanner_anomalies",
                "vw_mission_scanner_stats",
                "trg_scanner_cellular_data_hash",
                "trg_scanner_cellular_data_processing_time"
            ]
        }
        
        conn.execute("""
            INSERT INTO migration_history 
            (migration_id, description, metadata)
            VALUES (?, ?, ?)
        """, (
            self.migration_id,
            "Implementación de schema optimizado para datos de scanner celular SCANHUNTER",
            json.dumps(metadata)
        ))
    
    def _drop_migration_objects(self, conn: sqlite3.Connection) -> None:
        """Elimina objetos creados por la migración"""
        logger.info("Eliminando objetos de la migración")
        
        objects_to_drop = [
            ("TRIGGER", "trg_scanner_cellular_data_processing_time"),
            ("TRIGGER", "trg_scanner_cellular_data_hash"),
            ("VIEW", "vw_mission_scanner_stats"),
            ("VIEW", "vw_scanner_anomalies"),
            ("VIEW", "vw_scanner_coverage_summary"),
            ("TABLE", "cellular_operators"),
            ("TABLE", "scanner_cellular_data"),
        ]
        
        for obj_type, obj_name in objects_to_drop:
            try:
                conn.execute(f"DROP {obj_type} IF EXISTS {obj_name}")
                logger.info(f"Eliminado {obj_type}: {obj_name}")
            except Exception as e:
                logger.warning(f"Error eliminando {obj_type} {obj_name}: {str(e)}")


def main():
    """Función principal para ejecutar la migración"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migración Scanner Cellular Data v1.0")
    parser.add_argument("db_path", help="Ruta a la base de datos SQLite")
    parser.add_argument("--no-backup", action="store_true", help="No crear backup")
    parser.add_argument("--rollback", action="store_true", help="Ejecutar rollback")
    
    args = parser.parse_args()
    
    migration = ScannerCellularMigrationV1(args.db_path)
    
    if args.rollback:
        success = migration.rollback()
    else:
        success = migration.execute(create_backup=not args.no_backup)
    
    if success:
        logger.info("Operación completada exitosamente")
        exit(0)
    else:
        logger.error("Operación falló")
        exit(1)


if __name__ == "__main__":
    main()