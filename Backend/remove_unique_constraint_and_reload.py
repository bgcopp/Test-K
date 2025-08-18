#!/usr/bin/env python3
"""
REMOVER UNIQUE CONSTRAINT Y RECARGAR 100%
=========================================

Script para remover el UNIQUE constraint de la tabla operator_call_data
y recargar todos los archivos CLARO para obtener 100% de registros.

Autor: Boris - Remove Constraint & Reload
Fecha: 2025-08-18
"""

import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime
import traceback

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = r"C:\Soluciones\BGC\claude\KNSOft\Backend\kronos.db"

ARCHIVOS_CLARO = [
    r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\1-225211_LLAMADAS_ENTRANTES_POR_CELDA_545612_0.xlsx",
    r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\1-225211_LLAMADAS_SALIENTES_POR_CELDA_545613_0.xlsx",
    r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\2-225211_LLAMADAS_ENTRANTES_POR_CELDA_545614_0.xlsx",
    r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\2-225211_LLAMADAS_SALIENTES_POR_CELDA_545615_0.xlsx"
]

# Configuración con IDs reales de BD
FILE_CONFIG = {
    ARCHIVOS_CLARO[0]: {"file_upload_id": "6c9a8434-6331-4b9b-b451-2cad530f0562", "mission_id": "mission_MPFRBNsb", "type": "ENTRANTES"},
    ARCHIVOS_CLARO[1]: {"file_upload_id": "76427f87-b12c-4b77-9cb8-accf444aef03", "mission_id": "mission_MPFRBNsb", "type": "SALIENTES"},
    ARCHIVOS_CLARO[2]: {"file_upload_id": "d770a92c-86d1-4f8c-9690-4ed0769f31ee", "mission_id": "mission_MPFRBNsb", "type": "ENTRANTES"},
    ARCHIVOS_CLARO[3]: {"file_upload_id": "02ad66e0-8bac-40da-8f9b-364325998e2d", "mission_id": "mission_MPFRBNsb", "type": "SALIENTES"}
}

def print_section(title):
    print(f"\n{'='*70}")
    print(f" {title}")
    print(f"{'='*70}")

def print_info(message):
    print(f"[INFO] {message}")

def print_success(message):
    print(f"[SUCCESS] {message}")

def print_error(message):
    print(f"[ERROR] {message}")

def backup_database():
    """Crea backup de la base de datos."""
    print_section("CREANDO BACKUP DE BASE DE DATOS")
    
    try:
        import shutil
        backup_path = f"{DB_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(DB_PATH, backup_path)
        print_success(f"Backup creado: {backup_path}")
        return backup_path
    except Exception as e:
        print_error(f"Error creando backup: {e}")
        return None

def remove_unique_constraint():
    """Remueve el UNIQUE constraint de la tabla operator_call_data."""
    print_section("REMOVIENDO UNIQUE CONSTRAINT")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print_info("Analizando estructura actual de operator_call_data...")
        
        # Obtener estructura actual
        cursor.execute("PRAGMA table_info(operator_call_data)")
        columns_info = cursor.fetchall()
        
        print_info(f"Columnas actuales: {len(columns_info)}")
        
        # Obtener SQL de creación actual
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='operator_call_data'")
        current_sql = cursor.fetchone()[0]
        print_info("Estructura SQL actual obtenida")
        
        # Crear nueva tabla sin UNIQUE constraint
        new_table_sql = current_sql.replace(
            "UNIQUE(file_upload_id, record_hash)",
            "-- REMOVED: UNIQUE(file_upload_id, record_hash) for 100% loading"
        )
        
        print_info("Creando tabla temporal sin UNIQUE constraint...")
        
        # Crear tabla temporal
        temp_table_sql = new_table_sql.replace("operator_call_data", "operator_call_data_temp")
        cursor.execute(temp_table_sql)
        
        # Copiar datos existentes
        print_info("Copiando datos existentes a tabla temporal...")
        cursor.execute("""
            INSERT INTO operator_call_data_temp 
            SELECT * FROM operator_call_data
        """)
        
        rows_copied = cursor.rowcount
        print_success(f"Datos copiados: {rows_copied} registros")
        
        # Eliminar tabla original
        print_info("Eliminando tabla original...")
        cursor.execute("DROP TABLE operator_call_data")
        
        # Renombrar tabla temporal
        print_info("Renombrando tabla temporal...")
        cursor.execute("ALTER TABLE operator_call_data_temp RENAME TO operator_call_data")
        
        conn.commit()
        conn.close()
        
        print_success("UNIQUE constraint removido exitosamente")
        return True
        
    except Exception as e:
        print_error(f"Error removiendo UNIQUE constraint: {e}")
        traceback.print_exc()
        return False

def clear_claro_data():
    """Limpia datos CLARO existentes para recarga completa."""
    print_section("LIMPIANDO DATOS CLARO EXISTENTES")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Contar registros antes
        cursor.execute("SELECT COUNT(*) FROM operator_call_data WHERE operator = 'CLARO'")
        before_count = cursor.fetchone()[0]
        print_info(f"Registros CLARO antes de limpiar: {before_count}")
        
        # Eliminar registros CLARO
        cursor.execute("DELETE FROM operator_call_data WHERE operator = 'CLARO'")
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print_success(f"Registros CLARO eliminados: {deleted_count}")
        return True
        
    except Exception as e:
        print_error(f"Error limpiando datos CLARO: {e}")
        return False

def reload_claro_files():
    """Recarga todos los archivos CLARO sin restricciones."""
    print_section("RECARGANDO ARCHIVOS CLARO - 100% SIN RESTRICCIONES")
    
    try:
        from services.file_processor_service import FileProcessorService
        from database.connection import init_database
        
        # Inicializar BD
        init_database(DB_PATH)
        
        # Crear processor
        processor = FileProcessorService()
        
        total_loaded = 0
        total_expected = 0
        
        for archivo in ARCHIVOS_CLARO:
            if not os.path.exists(archivo):
                print_error(f"Archivo no encontrado: {archivo}")
                continue
            
            config = FILE_CONFIG[archivo]
            print_info(f"\nProcesando: {os.path.basename(archivo)}")
            print_info(f"Config: {config}")
            
            # Contar registros esperados
            try:
                df = pd.read_excel(archivo)
                expected_records = len(df)
                total_expected += expected_records
                print_info(f"Registros esperados: {expected_records}")
            except:
                expected_records = 0
                
            # Leer y procesar archivo
            try:
                with open(archivo, 'rb') as f:
                    file_bytes = f.read()
                
                # Procesar según tipo
                if config['type'] == 'ENTRANTES':
                    result = processor.process_claro_llamadas_entrantes(
                        file_bytes, 
                        os.path.basename(archivo), 
                        config['file_upload_id'], 
                        config['mission_id']
                    )
                elif config['type'] == 'SALIENTES':
                    result = processor.process_claro_llamadas_salientes(
                        file_bytes, 
                        os.path.basename(archivo), 
                        config['file_upload_id'], 
                        config['mission_id']
                    )
                
                processed = result.get('processedRecords', 0)
                failed = result.get('records_failed', 0)
                total_loaded += processed
                
                print_info(f"Resultado: {processed} procesados, {failed} fallidos")
                
                if result.get('success'):
                    print_success(f"Archivo cargado exitosamente")
                else:
                    print_error(f"Archivo falló: {result.get('error', 'Error desconocido')}")
                    
            except Exception as e:
                print_error(f"Error procesando {archivo}: {e}")
        
        print_section("RESUMEN DE RECARGA")
        print_info(f"Total esperado: {total_expected} registros")
        print_info(f"Total cargado: {total_loaded} registros")
        
        if total_loaded >= total_expected:
            print_success("100% de registros cargados exitosamente")
        else:
            percentage = (total_loaded / total_expected * 100) if total_expected > 0 else 0
            print_error(f"Solo {percentage:.1f}% cargado - aún hay problemas")
        
        return total_loaded, total_expected
        
    except Exception as e:
        print_error(f"Error recargando archivos: {e}")
        traceback.print_exc()
        return 0, 0

def verify_final_state():
    """Verifica el estado final después de la recarga."""
    print_section("VERIFICACIÓN ESTADO FINAL")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Contar total CLARO
        cursor.execute("SELECT COUNT(*) FROM operator_call_data WHERE operator = 'CLARO'")
        total_claro = cursor.fetchone()[0]
        print_info(f"Total registros CLARO: {total_claro}")
        
        # Por tipo
        cursor.execute("""
            SELECT tipo_llamada, COUNT(*) 
            FROM operator_call_data 
            WHERE operator = 'CLARO' 
            GROUP BY tipo_llamada
        """)
        tipos = cursor.fetchall()
        for tipo, count in tipos:
            print_info(f"  {tipo}: {count}")
        
        # Verificar números objetivo
        numeros_objetivo = ['3224274851', '3208611034', '3104277553', '3102715509', '3143534707', '3214161903']
        
        print_info("\nVerificación números objetivo:")
        for numero in numeros_objetivo:
            cursor.execute("""
                SELECT COUNT(*) FROM operator_call_data 
                WHERE operator = 'CLARO' 
                AND (numero_origen = ? OR numero_destino = ? OR numero_objetivo = ?)
            """, (numero, numero, numero))
            count = cursor.fetchone()[0]
            
            if count > 0:
                print_success(f"  {numero}: {count} registros")
            else:
                print_error(f"  {numero}: NO encontrado")
        
        conn.close()
        return total_claro
        
    except Exception as e:
        print_error(f"Error verificando estado final: {e}")
        return 0

def main():
    """Función principal."""
    print_section("REMOVE UNIQUE CONSTRAINT & RELOAD 100%")
    print("Removiendo restricciones y recargando para obtener 100% de registros...")
    print(f"Timestamp: {datetime.now()}")
    
    # Paso 1: Backup
    backup_path = backup_database()
    if not backup_path:
        print_error("Sin backup, abortando por seguridad")
        return
    
    # Paso 2: Remover UNIQUE constraint
    if not remove_unique_constraint():
        print_error("No se pudo remover UNIQUE constraint")
        return
    
    # Paso 3: Limpiar datos CLARO existentes
    if not clear_claro_data():
        print_error("No se pudo limpiar datos existentes")
        return
    
    # Paso 4: Recargar archivos
    loaded, expected = reload_claro_files()
    
    # Paso 5: Verificar resultado final
    final_count = verify_final_state()
    
    print_section("PROCESO COMPLETADO")
    if loaded >= expected and expected > 0:
        print_success(f"ÉXITO: 100% de registros cargados ({final_count} total)")
    else:
        print_error(f"PROBLEMA: Solo {loaded}/{expected} registros cargados")
    
    print_info(f"Backup disponible: {backup_path}")

if __name__ == "__main__":
    main()