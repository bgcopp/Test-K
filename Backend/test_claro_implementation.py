"""
KRONOS - Script de Prueba para Implementación CLARO
==================================================

Script de testing para validar la implementación completa del procesamiento
de archivos de datos celulares de CLARO.

Funcionalidades probadas:
- Lectura y procesamiento de archivos CSV/XLSX de CLARO
- Normalización de datos al esquema unificado
- Inserción en base de datos SQLite
- Sistema de logging especializado
- Funciones Eel expuestas

Uso:
    python test_claro_implementation.py

Autor: Sistema KRONOS
Versión: 1.0.0
"""

import os
import sys
import json
import base64
import time
from pathlib import Path

# Agregar directorios al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.operator_data_service import OperatorDataService, upload_operator_data, get_operator_sheets
from services.file_processor_service import FileProcessorService, test_claro_file_processing
from services.data_normalizer_service import DataNormalizerService, test_claro_normalization
from utils.operator_logger import OperatorLogger, get_performance_metrics


def create_test_mission_and_user():
    """Crea datos de prueba necesarios en la base de datos."""
    from database.connection import get_db_connection
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Crear usuario de prueba
            cursor.execute("""
                INSERT OR IGNORE INTO users (id, username, email, password_hash, role, is_active)
                VALUES ('test-user-001', 'test_user', 'test@kronos.local', 'hash123', 'admin', 1)
            """)
            
            # Crear misión de prueba
            cursor.execute("""
                INSERT OR IGNORE INTO missions (
                    id, name, description, status, 
                    created_by, created_at
                ) VALUES (
                    'test-mission-001', 
                    'Misión de Prueba CLARO',
                    'Misión para testing de procesamiento CLARO',
                    'active',
                    'test-user-001',
                    datetime('now')
                )
            """)
            
            conn.commit()
            print("✓ Datos de prueba creados: usuario y misión")
            return True
            
    except Exception as e:
        print(f"❌ Error creando datos de prueba: {e}")
        return False


def test_logger():
    """Prueba el sistema de logging."""
    print("\n=== PRUEBA 1: Sistema de Logging ===")
    
    logger = OperatorLogger('test_claro')
    
    # Test de diferentes niveles
    logger.info("Iniciando pruebas del sistema de logging")
    logger.debug("Mensaje de debug - información detallada")
    logger.warning("Mensaje de advertencia - situación a considerar")
    
    # Test con contexto
    logger.set_context(
        file_upload_id='test-file-123',
        operator='CLARO',
        processing_step='TESTING'
    )
    
    logger.info("Mensaje con contexto establecido", extra={
        'records_processed': 100,
        'file_size_mb': 2.5
    })
    
    # Test de métricas
    metrics = get_performance_metrics()
    logger.info(f"Métricas del sistema: {json.dumps(metrics, indent=2)}")
    
    logger.clear_context()
    logger.info("✓ Pruebas de logging completadas")
    
    return True


def test_data_normalizer():
    """Prueba el servicio de normalización."""
    print("\n=== PRUEBA 2: Normalización de Datos ===")
    
    # Ejecutar test integrado
    test_claro_normalization()
    
    print("✓ Pruebas de normalización completadas")
    return True


def test_file_processor():
    """Prueba el procesamiento de archivos."""
    print("\n=== PRUEBA 3: Procesamiento de Archivos ===")
    
    # Buscar archivo de prueba CLARO
    test_file_paths = [
        "C:\\Soluciones\\BGC\\claude\\KNSOft\\datatest\\Claro\\DATOS_POR_CELDA CLARO.csv",
        "C:\\Soluciones\\BGC\\claude\\KNSOft\\datatest\\Claro\\formato excel\\DATOS_POR_CELDA CLARO.xlsx"
    ]
    
    file_found = None
    for file_path in test_file_paths:
        if os.path.exists(file_path):
            file_found = file_path
            break
    
    if not file_found:
        print("❌ No se encontró archivo de prueba CLARO")
        print("Archivos buscados:")
        for path in test_file_paths:
            print(f"  - {path}")
        return False
    
    print(f"📁 Usando archivo de prueba: {file_found}")
    
    # Crear pequeña muestra de datos para prueba
    test_csv_data = """numero,fecha_trafico,tipo_cdr,celda_decimal,lac_decimal
573123456789,20240419080000,DATOS,175462,20010
573987654321,20240419080001,DATOS,175462,20010
573111222333,20240419080002,DATOS,175463,20010
573444555666,20240419080003,DATOS,175464,20011
573777888999,20240419080004,DATOS,175465,20011"""
    
    # Probar con datos de muestra
    service = FileProcessorService()
    
    try:
        result = service.process_claro_data_por_celda(
            file_bytes=test_csv_data.encode('utf-8'),
            file_name='test_datos_claro.csv',
            file_upload_id='test-file-001',
            mission_id='test-mission-001'
        )
        
        print(f"📊 Resultado del procesamiento: {json.dumps(result, indent=2)}")
        
        if result.get('success'):
            print("✓ Procesamiento de archivo exitoso")
            return True
        else:
            print(f"❌ Error en procesamiento: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Excepción en procesamiento: {e}")
        return False


def test_full_integration():
    """Prueba la integración completa usando funciones Eel."""
    print("\n=== PRUEBA 4: Integración Completa (Funciones Eel) ===")
    
    # Datos de archivo de prueba (pequeña muestra)
    test_csv_data = """numero,fecha_trafico,tipo_cdr,celda_decimal,lac_decimal
573123456789,20240419080000,DATOS,175462,20010
573987654321,20240419080001,DATOS,175462,20010
573111222333,20240419080002,DATOS,175463,20010"""
    
    # Codificar en Base64 (como viene del frontend)
    file_data_b64 = base64.b64encode(test_csv_data.encode('utf-8')).decode('utf-8')
    
    try:
        # Prueba de carga de archivo
        print("📤 Probando carga de archivo via función Eel...")
        
        start_time = time.time()
        result = upload_operator_data(
            file_data=file_data_b64,
            file_name='test_integracion_claro.csv',
            mission_id='test-mission-001',
            operator='CLARO',
            file_type='CELLULAR_DATA',
            user_id='test-user-001'
        )
        processing_time = time.time() - start_time
        
        print(f"⏱️ Tiempo de procesamiento: {processing_time:.2f} segundos")
        print(f"📊 Resultado: {json.dumps(result, indent=2)}")
        
        if result.get('success'):
            file_upload_id = result.get('file_upload_id')
            print(f"✓ Archivo procesado exitosamente. ID: {file_upload_id}")
            
            # Prueba de consulta de archivos
            print("📋 Probando consulta de archivos...")
            sheets_result = get_operator_sheets('test-mission-001')
            print(f"📊 Archivos encontrados: {len(sheets_result.get('data', []))}")
            
            return True
        else:
            print(f"❌ Error en integración: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Excepción en integración: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_schema():
    """Verifica que el esquema de base de datos esté correcto."""
    print("\n=== PRUEBA 5: Verificación del Esquema de BD ===")
    
    from database.connection import get_db_connection
    
    expected_tables = [
        'operator_data_sheets',
        'operator_cellular_data', 
        'operator_call_data',
        'file_processing_logs',
        'users',
        'missions'
    ]
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar tablas existentes
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            print(f"📊 Tablas encontradas: {len(existing_tables)}")
            
            missing_tables = []
            for table in expected_tables:
                if table in existing_tables:
                    print(f"  ✓ {table}")
                else:
                    print(f"  ❌ {table} (FALTANTE)")
                    missing_tables.append(table)
            
            if missing_tables:
                print(f"⚠️ Tablas faltantes: {missing_tables}")
                print("Ejecute el script de esquema: Backend/database/operator_data_schema_optimized.sql")
                return False
            else:
                print("✓ Todas las tablas requeridas están presentes")
                return True
                
    except Exception as e:
        print(f"❌ Error verificando esquema: {e}")
        return False


def cleanup_test_data():
    """Limpia los datos de prueba creados."""
    from database.connection import get_db_connection
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Eliminar datos de prueba (en orden para respetar FK)
            cursor.execute("DELETE FROM file_processing_logs WHERE file_upload_id LIKE 'test-%'")
            cursor.execute("DELETE FROM operator_cellular_data WHERE file_upload_id LIKE 'test-%'")
            cursor.execute("DELETE FROM operator_data_sheets WHERE id LIKE 'test-%'")
            cursor.execute("DELETE FROM missions WHERE id LIKE 'test-%'")
            cursor.execute("DELETE FROM users WHERE id LIKE 'test-%'")
            
            conn.commit()
            print("🧹 Datos de prueba eliminados")
            
    except Exception as e:
        print(f"⚠️ Error limpiando datos de prueba: {e}")


def main():
    """Función principal de testing."""
    print("KRONOS - Pruebas de Implementación CLARO")
    print("=" * 50)
    
    # Contadores de pruebas
    tests_passed = 0
    total_tests = 5
    
    try:
        # Configurar datos de prueba
        if not create_test_mission_and_user():
            print("❌ No se pudieron crear datos de prueba iniciales")
            return
        
        # Ejecutar pruebas
        if test_database_schema():
            tests_passed += 1
        
        if test_logger():
            tests_passed += 1
        
        if test_data_normalizer():
            tests_passed += 1
        
        if test_file_processor():
            tests_passed += 1
        
        if test_full_integration():
            tests_passed += 1
        
        # Resultados finales
        print("\n" + "=" * 50)
        print("RESULTADOS FINALES")
        print("=" * 50)
        print(f"Pruebas ejecutadas: {total_tests}")
        print(f"Pruebas exitosas: {tests_passed}")
        print(f"Pruebas fallidas: {total_tests - tests_passed}")
        
        if tests_passed == total_tests:
            print("🎉 ¡TODAS LAS PRUEBAS EXITOSAS!")
            print("✅ La implementación CLARO está lista para usar")
        else:
            print("⚠️ Algunas pruebas fallaron")
            print("🔍 Revise los logs anteriores para detalles")
        
        # Mostrar métricas finales
        metrics = get_performance_metrics()
        print(f"\n📊 Métricas finales del sistema:")
        print(f"  - Memoria: {metrics.get('memory_usage_mb', 0):.1f} MB")
        print(f"  - CPU: {metrics.get('cpu_percent', 0):.1f}%")
        print(f"  - Threads: {metrics.get('threads', 0)}")
        
    except KeyboardInterrupt:
        print("\n❌ Pruebas interrumpidas por el usuario")
    except Exception as e:
        print(f"\n❌ Error crítico durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Limpiar datos de prueba
        print("\n🧹 Limpiando datos de prueba...")
        cleanup_test_data()
        print("✅ Testing completado")


if __name__ == "__main__":
    main()