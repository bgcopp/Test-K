#!/usr/bin/env python3
"""
KRONOS - Test de Validación de Tablas de Base de Datos
=====================================================

Test end-to-end para verificar que el error del dashboard "no such table: operator_data_sheets"
está completamente solucionado.

Autor: Sistema KRONOS - Testing Engineer
Fecha: 2025-08-14
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

# Configuración de base de datos
DB_PATH = Path(__file__).parent / "kronos.db"

def test_database_tables():
    """
    TEST 1: Verificar existencia de tablas necesarias
    
    Validaciones:
    1. operator_data_sheets existe
    2. operator_cellular_data existe  
    3. operator_call_data existe
    4. Validar estructura de schemas
    5. Verificar foreign keys
    """
    
    print("=" * 80)
    print("TEST 1: VALIDACIÓN DE TABLAS DE BASE DE DATOS")
    print("=" * 80)
    
    test_results = {
        "test_name": "database_tables_validation",
        "timestamp": datetime.now().isoformat(),
        "database_path": str(DB_PATH),
        "database_exists": False,
        "tables_validation": {},
        "foreign_keys_validation": {},
        "overall_status": "UNKNOWN",
        "errors": [],
        "warnings": []
    }
    
    try:
        # 1. Verificar que la base de datos existe
        if not DB_PATH.exists():
            error_msg = f"CRITICO: Base de datos no encontrada en {DB_PATH}"
            print(f"[ERROR] {error_msg}")
            test_results["errors"].append(error_msg)
            test_results["overall_status"] = "FAILED"
            return test_results
            
        test_results["database_exists"] = True
        print(f"[OK] Base de datos encontrada: {DB_PATH}")
        
        # 2. Conectar y verificar tablas
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Obtener lista de todas las tablas
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            existing_tables = [row[0] for row in cursor.fetchall()]
            print(f"📋 Tablas existentes: {', '.join(existing_tables)}")
            
            # 3. Verificar tablas específicas requeridas
            required_tables = [
                "operator_data_sheets",
                "operator_cellular_data", 
                "operator_call_data"
            ]
            
            for table_name in required_tables:
                print(f"\n🔍 Verificando tabla: {table_name}")
                
                table_result = {
                    "exists": False,
                    "schema": None,
                    "row_count": 0,
                    "indexes": [],
                    "constraints": []
                }
                
                try:
                    # Verificar existencia
                    cursor.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name = ?
                    """, (table_name,))
                    
                    if cursor.fetchone():
                        table_result["exists"] = True
                        print(f"  ✅ Tabla {table_name} existe")
                        
                        # Obtener schema
                        cursor.execute("""
                            SELECT sql FROM sqlite_master 
                            WHERE type='table' AND name = ?
                        """, (table_name,))
                        schema_sql = cursor.fetchone()[0]
                        table_result["schema"] = schema_sql
                        
                        # Obtener número de registros
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        row_count = cursor.fetchone()[0]
                        table_result["row_count"] = row_count
                        print(f"  📊 Registros: {row_count}")
                        
                        # Obtener índices
                        cursor.execute("""
                            SELECT name FROM sqlite_master 
                            WHERE type='index' AND tbl_name = ?
                            AND name NOT LIKE 'sqlite_%'
                        """, (table_name,))
                        indexes = [row[0] for row in cursor.fetchall()]
                        table_result["indexes"] = indexes
                        if indexes:
                            print(f"  🔍 Índices: {', '.join(indexes)}")
                        
                        # Verificar columnas específicas según la tabla
                        cursor.execute(f"PRAGMA table_info({table_name})")
                        columns_info = cursor.fetchall()
                        column_names = [col[1] for col in columns_info]
                        print(f"  📝 Columnas: {', '.join(column_names)}")
                        
                        # Validaciones específicas por tabla
                        if table_name == "operator_data_sheets":
                            required_columns = ['id', 'mission_id', 'file_name', 'file_checksum', 'operator', 'processing_status']
                            missing_columns = set(required_columns) - set(column_names)
                            if missing_columns:
                                error = f"Columnas faltantes en {table_name}: {missing_columns}"
                                test_results["errors"].append(error)
                                print(f"  ❌ {error}")
                            else:
                                print(f"  ✅ Todas las columnas requeridas presentes")
                                
                        elif table_name == "operator_cellular_data":
                            required_columns = ['id', 'file_upload_id', 'numero_telefono', 'fecha_hora_inicio', 'celda_id']
                            missing_columns = set(required_columns) - set(column_names)
                            if missing_columns:
                                error = f"Columnas faltantes en {table_name}: {missing_columns}"
                                test_results["errors"].append(error)
                                print(f"  ❌ {error}")
                            else:
                                print(f"  ✅ Todas las columnas requeridas presentes")
                                
                        elif table_name == "operator_call_data":
                            required_columns = ['id', 'file_upload_id', 'numero_origen', 'numero_destino', 'fecha_hora_llamada']
                            missing_columns = set(required_columns) - set(column_names)
                            if missing_columns:
                                error = f"Columnas faltantes en {table_name}: {missing_columns}"
                                test_results["errors"].append(error)
                                print(f"  ❌ {error}")
                            else:
                                print(f"  ✅ Todas las columnas requeridas presentes")
                        
                    else:
                        table_result["exists"] = False
                        error = f"❌ CRÍTICO: Tabla {table_name} NO EXISTE"
                        print(f"  {error}")
                        test_results["errors"].append(error)
                        
                except Exception as e:
                    error = f"Error verificando tabla {table_name}: {str(e)}"
                    table_result["error"] = error
                    test_results["errors"].append(error)
                    print(f"  ❌ {error}")
                
                test_results["tables_validation"][table_name] = table_result
            
            # 4. Verificar Foreign Keys
            print(f"\n🔗 Verificando Foreign Keys...")
            
            try:
                # Verificar que PRAGMA foreign_keys está habilitado
                cursor.execute("PRAGMA foreign_keys")
                fk_status = cursor.fetchone()[0]
                print(f"  📋 Foreign Keys habilitadas: {'Sí' if fk_status else 'No'}")
                
                # Verificar integridad de FK en operator_data_sheets
                if "operator_data_sheets" in [t for t, r in test_results["tables_validation"].items() if r["exists"]]:
                    cursor.execute("PRAGMA foreign_key_check(operator_data_sheets)")
                    fk_violations = cursor.fetchall()
                    if fk_violations:
                        error = f"Violaciones de Foreign Key en operator_data_sheets: {fk_violations}"
                        test_results["errors"].append(error)
                        print(f"  ❌ {error}")
                    else:
                        print(f"  ✅ Foreign Keys válidas en operator_data_sheets")
                
                test_results["foreign_keys_validation"]["enabled"] = bool(fk_status)
                test_results["foreign_keys_validation"]["violations"] = len(fk_violations) if 'fk_violations' in locals() else 0
                
            except Exception as e:
                warning = f"No se pudo verificar Foreign Keys: {str(e)}"
                test_results["warnings"].append(warning)
                print(f"  ⚠️ {warning}")
        
        # 5. Determinar estado general
        missing_tables = [name for name, result in test_results["tables_validation"].items() if not result["exists"]]
        
        if missing_tables:
            test_results["overall_status"] = "FAILED"
            print(f"\n❌ TEST FALLIDO: Tablas faltantes: {', '.join(missing_tables)}")
        elif test_results["errors"]:
            test_results["overall_status"] = "FAILED_WITH_ERRORS"
            print(f"\n⚠️ TEST CON ERRORES: {len(test_results['errors'])} errores encontrados")
        else:
            test_results["overall_status"] = "PASSED"
            print(f"\n✅ TEST EXITOSO: Todas las tablas necesarias existen y están configuradas correctamente")
            
    except Exception as e:
        error_msg = f"Error crítico durante validación de base de datos: {str(e)}"
        test_results["errors"].append(error_msg)
        test_results["overall_status"] = "CRITICAL_ERROR"
        print(f"\n💥 {error_msg}")
    
    return test_results


def main():
    """Ejecutar test completo de validación de tablas"""
    
    print("KRONOS - Test de Validacion de Tablas de Base de Datos")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    # Ejecutar test
    results = test_database_tables()
    
    # Guardar resultados
    results_file = Path(__file__).parent / f"database_tables_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n[SAVE] Resultados guardados en: {results_file}")
    except Exception as e:
        print(f"[WARN] No se pudieron guardar los resultados: {e}")
    
    # Resumen final
    print("\n" + "=" * 80)
    print("RESUMEN FINAL")
    print("=" * 80)
    print(f"Estado General: {results['overall_status']}")
    print(f"Errores: {len(results['errors'])}")
    print(f"Advertencias: {len(results['warnings'])}")
    
    if results["overall_status"] == "PASSED":
        print("[SUCCESS] TODAS LAS TABLAS ESTAN CORRECTAS - El error del dashboard deberia estar solucionado")
        return True
    else:
        print("[FAILED] HAY PROBLEMAS CON LA BASE DE DATOS - El error del dashboard persistira")
        if results["errors"]:
            print("\n[ERROR] Errores encontrados:")
            for i, error in enumerate(results["errors"], 1):
                print(f"  {i}. {error}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)