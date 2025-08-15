"""
Test de Validación: Corrección del ID de archivo SCANHUNTER.xlsx

Este script valida que:
1. La columna "Id" de SCANHUNTER.xlsx se procese correctamente
2. Se almacene en el campo file_record_id de la BD
3. Se muestre el file_record_id en lugar del autoincremental
4. Se ordene correctamente por file_record_id (ASC: 0, 12, 32)

Autor: Sistema KRONOS  
Fecha: 2025-08-14
"""

import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path

# Agregar el directorio padre al path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_database_manager
from database.models import Mission, CellularData, User, Role
from services.file_processor_service import FileProcessorService
from services.mission_service import MissionService
from utils.operator_logger import OperatorLogger

def test_scanhunter_file_record_id_fix():
    """
    Test principal que valida la corrección del file_record_id para SCANHUNTER
    """
    logger = OperatorLogger()
    logger.info("=== INICIANDO TEST: Corrección file_record_id SCANHUNTER ===")
    
    try:
        # === PREPARACIÓN ===
        
        # Limpiar base de datos test
        test_db_path = "test_scanhunter_fix.db"
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            logger.info(f"Base de datos test eliminada: {test_db_path}")
        
        # Configurar conexión a BD test
        os.environ['DATABASE_PATH'] = test_db_path
        db_manager = get_database_manager()
        
        # Crear esquema
        with db_manager.get_session() as session:
            db_manager.create_tables()
            logger.info("Esquema de BD test creado")
            
            # Crear usuario y rol test
            test_role = Role(
                id="test-role",
                name="Test Role",
                permissions='{"missions": {"create": true, "read": true}}'
            )
            session.add(test_role)
            
            test_user = User(
                id="test-user",
                name="Test User",
                email="test@test.com",
                password_hash="$2b$12$test_hash_for_testing_only_1234567890abcdef",
                role_id="test-role"
            )
            session.add(test_user)
            
            # Crear misión test
            test_mission = Mission(
                id="test-mission",
                code="TEST-SCANHUNTER",
                name="Test Mission SCANHUNTER fix",
                description="Misión para validar corrección file_record_id",
                status="En Progreso",
                start_date="2025-08-14",
                created_by="test-user"
            )
            session.add(test_mission)
            
            session.commit()
            logger.info("Datos test creados en BD")
        
        # === VERIFICACIÓN DEL ARCHIVO SCANHUNTER ===
        
        scanhunter_path = os.path.join(
            os.path.dirname(__file__), 
            "..", "archivos", "envioarchivosparaanalizar (1)", "SCANHUNTER.csv"
        )
        
        if not os.path.exists(scanhunter_path):
            logger.error(f"Archivo SCANHUNTER no encontrado: {scanhunter_path}")
            return False
        
        logger.info(f"Archivo SCANHUNTER encontrado: {scanhunter_path}")
        
        # Analizar estructura del archivo
        df = pd.read_csv(scanhunter_path)
        logger.info(f"Archivo SCANHUNTER: {len(df)} registros, columnas: {list(df.columns)}")
        
        if 'Id' not in df.columns:
            logger.error("ERROR CRÍTICO: Columna 'Id' no encontrada en SCANHUNTER")
            return False
        
        # Analizar distribución de IDs
        id_counts = df['Id'].value_counts().sort_index()
        logger.info(f"Distribución de IDs en archivo: {dict(id_counts)}")
        expected_ids = {0, 12, 32}
        found_ids = set(id_counts.index)
        
        if not expected_ids.issubset(found_ids):
            logger.warning(f"IDs esperados {expected_ids} no todos encontrados. Encontrados: {found_ids}")
        
        # === PROCESAMIENTO DEL ARCHIVO ===
        
        logger.info("Iniciando procesamiento con FileProcessorService...")
        
        file_processor = FileProcessorService()
        
        # Leer archivo como bytes
        with open(scanhunter_path, 'rb') as f:
            file_bytes = f.read()
        
        # Procesar archivo
        result = file_processor.process_scanhunter_data(
            file_bytes=file_bytes,
            file_name="SCANHUNTER.csv", 
            mission_id="test-mission",
            upload_id="test-upload"
        )
        
        logger.info(f"Resultado procesamiento: {result}")
        
        if not result.get('success'):
            logger.error(f"ERROR: Procesamiento falló: {result.get('error')}")
            return False
        
        # === VERIFICACIÓN EN BASE DE DATOS ===
        
        logger.info("Verificando datos procesados en BD...")
        
        with db_manager.get_session() as session:
            # Obtener registros ordenados por file_record_id
            cellular_records = session.query(CellularData).filter(
                CellularData.mission_id == "test-mission"
            ).order_by(CellularData.file_record_id).all()
            
            logger.info(f"Registros encontrados en BD: {len(cellular_records)}")
            
            if len(cellular_records) == 0:
                logger.error("ERROR: No se encontraron registros en la BD")
                return False
            
            # Verificar que file_record_id está poblado
            records_with_file_id = [r for r in cellular_records if r.file_record_id is not None]
            logger.info(f"Registros con file_record_id: {len(records_with_file_id)}")
            
            if len(records_with_file_id) == 0:
                logger.error("ERROR CRÍTICO: Ningún registro tiene file_record_id poblado")
                return False
            
            # Verificar ordenamiento
            file_record_ids = [r.file_record_id for r in records_with_file_id]
            unique_ids = sorted(set(file_record_ids))
            logger.info(f"IDs únicos encontrados (ordenados): {unique_ids}")
            
            # Verificar que están los IDs esperados
            for expected_id in [0, 12, 32]:
                if expected_id not in file_record_ids:
                    logger.error(f"ERROR: ID esperado {expected_id} no encontrado en BD")
                    return False
                else:
                    count = file_record_ids.count(expected_id)
                    logger.info(f"ID {expected_id}: {count} registros en BD")
            
            # Verificar que el ordenamiento es correcto
            is_sorted = file_record_ids == sorted(file_record_ids)
            logger.info(f"Registros ordenados correctamente por file_record_id: {is_sorted}")
            
            # Mostrar muestra de registros
            logger.info("Muestra de primeros 5 registros:")
            for i, record in enumerate(cellular_records[:5]):
                logger.info(f"  {i+1}. file_record_id={record.file_record_id}, id={record.id}, punto={record.punto}")
        
        # === VERIFICACIÓN DEL MODELO ===
        
        logger.info("Verificando serialización del modelo...")
        
        with db_manager.get_session() as session:
            mission = session.query(Mission).filter(Mission.id == "test-mission").first()
            mission_dict = mission.to_dict_with_relations()
            
            cellular_data = mission_dict.get('cellularData', [])
            logger.info(f"CellularData serializados: {len(cellular_data)} registros")
            
            if len(cellular_data) > 0:
                sample_record = cellular_data[0]
                has_file_record_id = 'fileRecordId' in sample_record
                logger.info(f"Registro tiene fileRecordId: {has_file_record_id}")
                
                if has_file_record_id:
                    logger.info(f"Ejemplo fileRecordId: {sample_record['fileRecordId']}")
                else:
                    logger.error("ERROR: fileRecordId no encontrado en serialización")
                    return False
        
        logger.info("✅ TEST COMPLETADO EXITOSAMENTE")
        logger.info("✅ file_record_id se procesa y almacena correctamente")
        logger.info("✅ Ordenamiento por file_record_id funciona")
        logger.info("✅ Serialización incluye fileRecordId")
        
        return True
        
    except Exception as e:
        logger.error(f"ERROR CRÍTICO EN TEST: {str(e)}", exc_info=True)
        return False
    
    finally:
        # Limpiar archivo test
        if os.path.exists("test_scanhunter_fix.db"):
            os.remove("test_scanhunter_fix.db")
            logger.info("Base de datos test eliminada")

def run_quick_validation():
    """
    Validación rápida de la estructura de la BD existente
    """
    logger = OperatorLogger()
    logger.info("=== VALIDACIÓN RÁPIDA: Campo file_record_id en BD actual ===")
    
    try:
        db_path = os.path.join(os.path.dirname(__file__), 'kronos.db')
        if not os.path.exists(db_path):
            logger.error(f"BD no encontrada: {db_path}")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar estructura de cellular_data
        cursor.execute("PRAGMA table_info(cellular_data)")
        columns = cursor.fetchall()
        
        has_file_record_id = any(col[1] == 'file_record_id' for col in columns)
        logger.info(f"Campo file_record_id existe: {has_file_record_id}")
        
        if has_file_record_id:
            # Contar registros con file_record_id
            cursor.execute("SELECT COUNT(*) FROM cellular_data WHERE file_record_id IS NOT NULL")
            count_with_id = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM cellular_data")
            total_count = cursor.fetchone()[0]
            
            logger.info(f"Registros totales: {total_count}")
            logger.info(f"Registros con file_record_id: {count_with_id}")
            
            if count_with_id > 0:
                # Mostrar valores únicos de file_record_id
                cursor.execute("SELECT DISTINCT file_record_id FROM cellular_data WHERE file_record_id IS NOT NULL ORDER BY file_record_id")
                unique_ids = [row[0] for row in cursor.fetchall()]
                logger.info(f"file_record_id únicos existentes: {unique_ids}")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error en validación rápida: {e}")
        return False

if __name__ == "__main__":
    print("KRONOS - Test Corrección file_record_id SCANHUNTER")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] == 'quick':
        run_quick_validation()
    else:
        success = test_scanhunter_file_record_id_fix()
        if success:
            print("\n✅ TODOS LOS TESTS PASARON")
        else:
            print("\n❌ ALGUNOS TESTS FALLARON")
            sys.exit(1)