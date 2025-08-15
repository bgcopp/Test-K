#!/usr/bin/env python3
"""
KRONOS - Test Simplificado de Validacion de Tablas
=================================================

Test end-to-end para verificar que el error del dashboard "no such table: operator_data_sheets"
esta completamente solucionado.

Autor: Sistema KRONOS - Testing Engineer  
Fecha: 2025-08-14
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

# Configuracion de base de datos
DB_PATH = Path(__file__).parent / "kronos.db"

def test_database_tables():
    """
    TEST 1: Verificar existencia de tablas necesarias
    """
    
    print("=" * 80)
    print("TEST 1: VALIDACION DE TABLAS DE BASE DE DATOS")
    print("=" * 80)
    
    test_results = {
        "test_name": "database_tables_validation",
        "timestamp": datetime.now().isoformat(),
        "database_path": str(DB_PATH),
        "database_exists": False,
        "tables_validation": {},
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
            print(f"[INFO] Tablas existentes: {', '.join(existing_tables)}")
            
            # 3. Verificar tablas especificas requeridas
            required_tables = [
                "operator_data_sheets",
                "operator_cellular_data", 
                "operator_call_data"
            ]
            
            all_tables_exist = True
            
            for table_name in required_tables:
                print(f"\n[CHECK] Verificando tabla: {table_name}")
                
                table_result = {
                    "exists": False,
                    "row_count": 0,
                    "columns": []
                }
                
                try:
                    # Verificar existencia
                    cursor.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name = ?
                    """, (table_name,))
                    
                    if cursor.fetchone():
                        table_result["exists"] = True
                        print(f"  [OK] Tabla {table_name} existe")
                        
                        # Obtener numero de registros
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        row_count = cursor.fetchone()[0]
                        table_result["row_count"] = row_count
                        print(f"  [INFO] Registros: {row_count}")
                        
                        # Obtener columnas
                        cursor.execute(f"PRAGMA table_info({table_name})")
                        columns_info = cursor.fetchall()
                        column_names = [col[1] for col in columns_info]
                        table_result["columns"] = column_names
                        print(f"  [INFO] Columnas: {', '.join(column_names[:5])}{'...' if len(column_names) > 5 else ''}")
                        
                    else:
                        table_result["exists"] = False
                        error = f"CRITICO: Tabla {table_name} NO EXISTE"
                        print(f"  [ERROR] {error}")
                        test_results["errors"].append(error)
                        all_tables_exist = False
                        
                except Exception as e:
                    error = f"Error verificando tabla {table_name}: {str(e)}"
                    table_result["error"] = error
                    test_results["errors"].append(error)
                    print(f"  [ERROR] {error}")
                    all_tables_exist = False
                
                test_results["tables_validation"][table_name] = table_result
        
        # 4. Determinar estado general
        if all_tables_exist and not test_results["errors"]:
            test_results["overall_status"] = "PASSED"
            print(f"\n[SUCCESS] TEST EXITOSO: Todas las tablas necesarias existen")
        else:
            test_results["overall_status"] = "FAILED"
            print(f"\n[FAILED] TEST FALLIDO: {len(test_results['errors'])} errores encontrados")
            
    except Exception as e:
        error_msg = f"Error critico durante validacion de base de datos: {str(e)}"
        test_results["errors"].append(error_msg)
        test_results["overall_status"] = "CRITICAL_ERROR"
        print(f"\n[CRITICAL] {error_msg}")
    
    return test_results


def main():
    """Ejecutar test completo de validacion de tablas"""
    
    print("KRONOS - Test de Validacion de Tablas de Base de Datos")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    # Ejecutar test
    results = test_database_tables()
    
    # Guardar resultados
    results_file = Path(__file__).parent / f"database_simple_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n[SAVE] Resultados guardados en: {results_file}")
    except Exception as e:
        print(f"[WARN] No se pudieron guardar los resultados: {e}")
    
    # Resumen final
    print("\n" + "=" * 80)
    print("RESUMEN FINAL - TEST 1: BASE DE DATOS")
    print("=" * 80)
    print(f"Estado General: {results['overall_status']}")
    print(f"Errores: {len(results['errors'])}")
    print(f"Advertencias: {len(results['warnings'])}")
    
    if results["overall_status"] == "PASSED":
        print("[SUCCESS] TODAS LAS TABLAS ESTAN CORRECTAS")
        print("         El error 'no such table: operator_data_sheets' deberia estar solucionado")
        return True
    else:
        print("[FAILED] HAY PROBLEMAS CON LA BASE DE DATOS")
        print("        El error del dashboard persistira")
        if results["errors"]:
            print("\n[ERROR] Errores encontrados:")
            for i, error in enumerate(results["errors"], 1):
                print(f"  {i}. {error}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)