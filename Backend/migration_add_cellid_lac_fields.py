"""
KRONOS Database Migration - Agregar campos Cell ID y LAC
========================================================
Migración para agregar campos cellid_decimal y lac_decimal a la tabla 
operator_call_data para soporte de extracción desde celda_origen de Movistar.

Author: KRONOS Development Team
Date: 2025-08-14
"""

import sqlite3
import logging
import sys
from datetime import datetime
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_backup(db_path: str) -> str:
    """
    Crea respaldo de la base de datos antes de la migración.
    
    Returns:
        str: Ruta del archivo de respaldo
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"
    
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        logger.info(f"Respaldo creado: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Error creando respaldo: {e}")
        raise


def check_existing_columns(conn: sqlite3.Connection) -> dict:
    """
    Verifica si las columnas ya existen en la tabla.
    
    Returns:
        dict: Estado de las columnas
    """
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(operator_call_data)")
    columns = cursor.fetchall()
    
    column_names = [col[1] for col in columns]
    
    status = {
        'cellid_decimal_exists': 'cellid_decimal' in column_names,
        'lac_decimal_exists': 'lac_decimal' in column_names,
        'celda_origen_exists': 'celda_origen' in column_names
    }
    
    logger.info(f"Estado de columnas: {status}")
    return status


def add_cellid_lac_columns(conn: sqlite3.Connection) -> None:
    """
    Agrega las columnas cellid_decimal y lac_decimal a operator_call_data.
    """
    cursor = conn.cursor()
    
    try:
        # Agregar columna cellid_decimal
        logger.info("Agregando columna cellid_decimal...")
        cursor.execute("""
            ALTER TABLE operator_call_data 
            ADD COLUMN cellid_decimal INTEGER
        """)
        
        # Agregar columna lac_decimal
        logger.info("Agregando columna lac_decimal...")
        cursor.execute("""
            ALTER TABLE operator_call_data 
            ADD COLUMN lac_decimal INTEGER
        """)
        
        conn.commit()
        logger.info("Columnas agregadas exitosamente")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            logger.warning(f"Columna ya existe: {e}")
        else:
            logger.error(f"Error SQL agregando columnas: {e}")
            raise
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        raise


def populate_cellid_lac_from_existing_data(conn: sqlite3.Connection) -> None:
    """
    Puebla las nuevas columnas con datos extraídos de celda_origen existente.
    """
    cursor = conn.cursor()
    
    # Importar utilidad de conversión
    sys.path.append('.')
    from utils.cell_id_converter import extract_cellid_lac_from_celda_origen
    
    logger.info("Extrayendo datos de celda_origen existente...")
    
    # Obtener registros con celda_origen no nulos
    cursor.execute("""
        SELECT id, celda_origen 
        FROM operator_call_data 
        WHERE celda_origen IS NOT NULL 
        AND celda_origen != ''
        AND celda_origen != 'null'
    """)
    
    records = cursor.fetchall()
    logger.info(f"Procesando {len(records)} registros con celda_origen")
    
    updated_count = 0
    error_count = 0
    
    for record_id, celda_origen in records:
        try:
            # Extraer cellid y lac
            result = extract_cellid_lac_from_celda_origen(celda_origen)
            
            if result['cellid_decimal'] is not None and result['lac_decimal'] is not None:
                # Actualizar registro
                cursor.execute("""
                    UPDATE operator_call_data 
                    SET cellid_decimal = ?, lac_decimal = ?
                    WHERE id = ?
                """, (result['cellid_decimal'], result['lac_decimal'], record_id))
                
                updated_count += 1
                
                if updated_count % 100 == 0:
                    logger.info(f"Procesados {updated_count} registros...")
            else:
                error_count += 1
                logger.debug(f"No se pudo convertir celda_origen: {celda_origen}")
                
        except Exception as e:
            error_count += 1
            logger.error(f"Error procesando registro {record_id} ({celda_origen}): {e}")
    
    conn.commit()
    logger.info(f"Migración de datos completada: {updated_count} actualizados, {error_count} errores")


def create_indexes(conn: sqlite3.Connection) -> None:
    """
    Crea índices para las nuevas columnas para mejorar rendimiento.
    """
    cursor = conn.cursor()
    
    try:
        logger.info("Creando índices para nuevas columnas...")
        
        # Índice para cellid_decimal
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_operator_call_data_cellid_decimal 
            ON operator_call_data(cellid_decimal)
        """)
        
        # Índice para lac_decimal
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_operator_call_data_lac_decimal 
            ON operator_call_data(lac_decimal)
        """)
        
        # Índice compuesto para consultas que usen ambos campos
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_operator_call_data_cellid_lac 
            ON operator_call_data(cellid_decimal, lac_decimal)
        """)
        
        conn.commit()
        logger.info("Índices creados exitosamente")
        
    except Exception as e:
        logger.error(f"Error creando índices: {e}")
        raise


def verify_migration(conn: sqlite3.Connection) -> dict:
    """
    Verifica que la migración se completó correctamente.
    
    Returns:
        dict: Estadísticas de verificación
    """
    cursor = conn.cursor()
    
    # Verificar estructura de tabla
    cursor.execute("PRAGMA table_info(operator_call_data)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    # Contar registros con datos poblados
    cursor.execute("""
        SELECT 
            COUNT(*) as total_records,
            COUNT(celda_origen) as records_with_celda_origen,
            COUNT(cellid_decimal) as records_with_cellid,
            COUNT(lac_decimal) as records_with_lac
        FROM operator_call_data
    """)
    
    stats = cursor.fetchone()
    
    verification = {
        'cellid_decimal_column_exists': 'cellid_decimal' in column_names,
        'lac_decimal_column_exists': 'lac_decimal' in column_names,
        'total_records': stats[0],
        'records_with_celda_origen': stats[1],
        'records_with_cellid': stats[2],
        'records_with_lac': stats[3]
    }
    
    logger.info(f"Verificación de migración: {verification}")
    return verification


def main():
    """
    Función principal para ejecutar la migración.
    """
    db_path = "kronos.db"
    
    if not Path(db_path).exists():
        logger.error(f"Base de datos no encontrada: {db_path}")
        return False
    
    try:
        # Crear respaldo
        backup_path = create_backup(db_path)
        
        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        
        # Verificar estado inicial
        initial_status = check_existing_columns(conn)
        
        if initial_status['cellid_decimal_exists'] and initial_status['lac_decimal_exists']:
            logger.info("Las columnas ya existen. Verificando datos...")
            verification = verify_migration(conn)
            conn.close()
            return True
        
        # Ejecutar migración
        logger.info("Iniciando migración de base de datos...")
        
        # Agregar columnas
        add_cellid_lac_columns(conn)
        
        # Poblar datos desde registros existentes
        if initial_status['celda_origen_exists']:
            populate_cellid_lac_from_existing_data(conn)
        
        # Crear índices
        create_indexes(conn)
        
        # Verificar migración
        verification = verify_migration(conn)
        
        # Cerrar conexión
        conn.close()
        
        logger.info("Migración completada exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"Error durante la migración: {e}")
        return False


if __name__ == "__main__":
    success = main()
    if success:
        logger.info("✅ Migración ejecutada exitosamente")
    else:
        logger.error("❌ Migración falló")
        sys.exit(1)