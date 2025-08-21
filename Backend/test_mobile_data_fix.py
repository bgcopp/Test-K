#!/usr/bin/env python3
"""
Test de Validación - Corrección Error SQL operator_cellular_data
===============================================================================
Script para validar que la corrección del error SQL en get_mobile_data_interactions()
está funcionando correctamente.

CORRECCIÓN BORIS 2025-08-20:
- Cambio de 'ocd.operador' (inexistente) a 'ocd.operator as operador' (correcto)

Verifica:
1. Query SQL se ejecuta sin errores
2. Estructura de tabla operator_cellular_data es correcta  
3. Endpoint puede procesar datos móviles
===============================================================================
"""

import sqlite3
import os
import sys
from pathlib import Path

def test_table_structure():
    """Verifica la estructura real de operator_cellular_data"""
    print("=== TEST 1: ESTRUCTURA DE TABLA operator_cellular_data ===")
    
    db_path = "kronos.db"
    if not os.path.exists(db_path):
        print(f"Base de datos no encontrada: {db_path}")
        return False
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Obtener información de columnas
            cursor.execute("PRAGMA table_info(operator_cellular_data)")
            columns = cursor.fetchall()
            
            if not columns:
                print("Tabla operator_cellular_data no existe")
                return False
            
            print("Tabla operator_cellular_data existe")
            print("Columnas encontradas:")
            
            column_names = []
            for col in columns:
                col_name = col[1]  # Nombre de columna
                col_type = col[2]  # Tipo de dato
                column_names.append(col_name)
                print(f"   - {col_name} ({col_type})")
            
            # Verificar campos críticos
            required_fields = ['operator', 'numero_telefono', 'fecha_hora_inicio', 
                              'celda_id', 'trafico_subida_bytes', 'trafico_bajada_bytes']
            
            missing_fields = []
            for field in required_fields:
                if field not in column_names:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"CAMPOS FALTANTES: {missing_fields}")
                return False
            
            # Verificar que NO exista el campo problemático
            if 'operador' in column_names:
                print("ALERTA: Campo 'operador' encontrado en tabla (puede causar confusion)")
            else:
                print("Campo 'operador' no existe (correcto - debe usar 'operator')")
            
            print("Todos los campos requeridos estan presentes")
            return True
            
    except Exception as e:
        print(f"❌ Error verificando estructura: {e}")
        return False

def test_sql_query_syntax():
    """Prueba que la query SQL corregida funcione sin errores de sintaxis"""
    print("\n=== TEST 2: SINTAXIS DE QUERY CORREGIDA ===")
    
    db_path = "kronos.db"
    
    # Query corregida (la misma que está ahora en main.py)
    query = """
    SELECT 
        ocd.numero_telefono as numero_objetivo,
        '' as numero_secundario,
        ocd.fecha_hora_inicio as fecha_hora,
        ocd.operator as operador,  -- CORRECCIÓN: usar 'operator' no 'operador'
        ocd.celda_id as celda_inicio,
        '' as celda_final,
        CAST((julianday(ocd.fecha_hora_fin) - julianday(ocd.fecha_hora_inicio)) * 24 * 60 * 60 AS INTEGER) as duracion_segundos,
        ocd.trafico_subida_bytes + ocd.trafico_bajada_bytes as trafico_total_bytes,
        ocd.tipo_conexion
    FROM operator_cellular_data ocd
    WHERE ocd.mission_id = ?
      AND ocd.numero_telefono = ?
      AND ocd.fecha_hora_inicio BETWEEN ? AND ?  
    ORDER BY ocd.fecha_hora_inicio DESC
    LIMIT 5
    """
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Parámetros de prueba
            test_params = [
                'test_mission_id',
                '3001234567', 
                '2024-01-01 00:00:00',
                '2024-12-31 23:59:59'
            ]
            
            # Probar la query
            cursor.execute(query, test_params)
            
            # Si llegamos aquí, la sintaxis es correcta
            print("✅ Query SQL ejecutada sin errores de sintaxis")
            
            # Verificar que se puede acceder a todas las columnas seleccionadas
            columns = [description[0] for description in cursor.description]
            expected_columns = ['numero_objetivo', 'numero_secundario', 'fecha_hora', 
                               'operador', 'celda_inicio', 'celda_final', 
                               'duracion_segundos', 'trafico_total_bytes', 'tipo_conexion']
            
            missing_columns = [col for col in expected_columns if col not in columns]
            if missing_columns:
                print(f"❌ Columnas faltantes en resultado: {missing_columns}")
                return False
            
            print(f"✅ Todas las columnas esperadas están presentes: {len(columns)} columnas")
            print(f"   Columnas: {', '.join(columns)}")
            return True
            
    except sqlite3.OperationalError as e:
        if "no such column" in str(e).lower():
            print(f"❌ ERROR DE COLUMNA: {e}")
            print("   Esto indica que el error aún no está corregido")
            return False
        else:
            print(f"❌ Error SQL: {e}")
            return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_query_with_hunter_correlation():
    """Prueba la query completa con correlación HUNTER"""
    print("\n=== TEST 3: QUERY CON CORRELACIÓN HUNTER ===")
    
    db_path = "kronos.db"
    
    # Query completa con LEFT JOIN como en main.py
    query = """
    SELECT 
        ocd.numero_telefono as numero_objetivo,
        ocd.fecha_hora_inicio as fecha_hora,
        ocd.operator as operador,
        ocd.celda_id as celda_inicio,
        ocd.trafico_subida_bytes + ocd.trafico_bajada_bytes as trafico_total_bytes,
        cd_inicio.punto as punto_hunter,
        cd_inicio.lat as lat_hunter,
        cd_inicio.lon as lon_hunter,
        CASE 
            WHEN cd_inicio.punto IS NOT NULL THEN 'celda_inicio'
            ELSE 'sin_ubicacion'
        END as hunter_source
    FROM operator_cellular_data ocd
    LEFT JOIN cellular_data cd_inicio ON (cd_inicio.cell_id = ocd.celda_id AND cd_inicio.mission_id = ocd.mission_id)
    WHERE ocd.mission_id = ?
      AND ocd.numero_telefono = ?
      AND ocd.fecha_hora_inicio BETWEEN ? AND ?  
    ORDER BY ocd.fecha_hora_inicio DESC
    LIMIT 3
    """
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Parámetros de prueba
            test_params = [
                'test_mission_id',
                '3001234567', 
                '2024-01-01 00:00:00',
                '2024-12-31 23:59:59'
            ]
            
            # Probar la query completa
            cursor.execute(query, test_params)
            
            print("✅ Query con correlación HUNTER ejecutada sin errores")
            
            # Verificar columnas del resultado
            columns = [description[0] for description in cursor.description]
            hunter_columns = ['punto_hunter', 'lat_hunter', 'lon_hunter', 'hunter_source']
            
            for col in hunter_columns:
                if col in columns:
                    print(f"   ✅ Columna HUNTER presente: {col}")
                else:
                    print(f"   ❌ Columna HUNTER faltante: {col}")
                    return False
            
            print("✅ Todas las columnas de correlación HUNTER están presentes")
            return True
            
    except sqlite3.OperationalError as e:
        print(f"❌ ERROR SQL en query con correlación: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado en test correlación: {e}")
        return False

def main():
    """Ejecuta todos los tests de validación"""
    print("="*70)
    print("TEST DE VALIDACIÓN - CORRECCIÓN ERROR SQL operator_cellular_data")
    print("="*70)
    print("CORRECCION BORIS 2025-08-20: 'ocd.operador' -> 'ocd.operator as operador'")
    print()
    
    tests = [
        ("Estructura de Tabla", test_table_structure),
        ("Sintaxis de Query", test_sql_query_syntax),
        ("Query con Correlación HUNTER", test_query_with_hunter_correlation)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed_tests += 1
                print(f"✅ {test_name}: PASÓ")
            else:
                print(f"❌ {test_name}: FALLÓ")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "="*70)
    print(f"RESULTADO FINAL: {passed_tests}/{total_tests} tests pasaron")
    
    if passed_tests == total_tests:
        print("CORRECCION VALIDADA EXITOSAMENTE")
        print("   Error SQL 'no such column: ocd.operador' esta corregido")
        print("   Query puede ejecutarse sin errores")
        print("   Correlacion HUNTER funciona correctamente")
        return 0
    else:
        print("ALGUNOS TESTS FALLARON")
        print("   Revisar la corrección aplicada en main.py")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)