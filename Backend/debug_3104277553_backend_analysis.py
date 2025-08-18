"""
Análisis backend específico para el número 3104277553
Investigación exhaustiva para confirmar por qué no aparece en resultados de correlación
"""

import sqlite3
import pandas as pd
import json
from datetime import datetime
import os

def connect_database():
    """Conecta a la base de datos SQLite"""
    db_path = os.path.join(os.path.dirname(__file__), 'kronos.db')
    return sqlite3.connect(db_path)

def analyze_3104277553_in_database():
    """Análisis exhaustivo del número 3104277553 en base de datos"""
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "target_number": "3104277553",
        "target_cell": "53591",
        "analysis": {}
    }
    
    conn = connect_database()
    
    # 1. Verificar existencia en operator_call_data
    print("=== 1. VERIFICANDO EXISTENCIA EN OPERATOR_CALL_DATA ===")
    
    query_origen = """
    SELECT 
        id, numero_origen, numero_destino, celda, operador, 
        fecha, hora, duracion_llamada, tipo_llamada
    FROM operator_call_data 
    WHERE numero_origen = '3104277553'
    """
    
    df_origen = pd.read_sql_query(query_origen, conn)
    print(f"Registros como ORIGINADOR: {len(df_origen)}")
    
    if len(df_origen) > 0:
        print("DETALLES DE REGISTROS COMO ORIGINADOR:")
        for idx, row in df_origen.iterrows():
            print(f"  - ID: {row['id']}, Celda: {row['celda']}, Operador: {row['operador']}")
            print(f"    Destino: {row['numero_destino']}, Fecha: {row['fecha']}")
    
    # Verificar como destino también
    query_destino = """
    SELECT 
        id, numero_origen, numero_destino, celda, operador, 
        fecha, hora, duracion_llamada, tipo_llamada
    FROM operator_call_data 
    WHERE numero_destino = '3104277553'
    """
    
    df_destino = pd.read_sql_query(query_destino, conn)
    print(f"Registros como DESTINO: {len(df_destino)}")
    
    # Guardar resultados
    results["analysis"]["database_records"] = {
        "as_originator": len(df_origen),
        "as_destination": len(df_destino),
        "originator_details": df_origen.to_dict('records') if len(df_origen) > 0 else [],
        "destination_details": df_destino.to_dict('records') if len(df_destino) > 0 else []
    }
    
    # 2. Verificar celdas HUNTER cargadas
    print("\n=== 2. VERIFICANDO CELDAS HUNTER CARGADAS ===")
    
    # Obtener todas las celdas únicas de operator_call_data
    query_all_cells = """
    SELECT DISTINCT celda, COUNT(*) as record_count
    FROM operator_call_data 
    GROUP BY celda
    ORDER BY celda
    """
    
    df_all_cells = pd.read_sql_query(query_all_cells, conn)
    total_cells = len(df_all_cells)
    print(f"Total de celdas únicas en base de datos: {total_cells}")
    
    # Verificar específicamente celda 53591
    target_cell_data = df_all_cells[df_all_cells['celda'] == '53591']
    
    if len(target_cell_data) > 0:
        print(f"✓ Celda 53591 ENCONTRADA en base de datos")
        print(f"  - Número de registros en esta celda: {target_cell_data.iloc[0]['record_count']}")
    else:
        print("✗ Celda 53591 NO encontrada en base de datos")
    
    results["analysis"]["cell_analysis"] = {
        "total_cells_in_db": total_cells,
        "target_cell_53591_exists": len(target_cell_data) > 0,
        "target_cell_record_count": int(target_cell_data.iloc[0]['record_count']) if len(target_cell_data) > 0 else 0
    }
    
    # 3. Verificar si existe alguna tabla de celdas HUNTER específica
    print("\n=== 3. VERIFICANDO TABLAS HUNTER ===")
    
    query_tables = """
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name LIKE '%hunter%'
    """
    
    hunter_tables = pd.read_sql_query(query_tables, conn)
    print(f"Tablas HUNTER encontradas: {list(hunter_tables['name'])}")
    
    results["analysis"]["hunter_tables"] = list(hunter_tables['name'])
    
    # 4. Análisis de operadores para el número objetivo
    print("\n=== 4. ANÁLISIS DE OPERADORES ===")
    
    if len(df_origen) > 0:
        operators = df_origen['operador'].unique()
        print(f"Operadores del número 3104277553: {list(operators)}")
        
        for op in operators:
            count = len(df_origen[df_origen['operador'] == op])
            print(f"  - {op}: {count} registros")
    
    results["analysis"]["operator_analysis"] = {
        "operators": list(df_origen['operador'].unique()) if len(df_origen) > 0 else [],
        "operator_counts": df_origen.groupby('operador').size().to_dict() if len(df_origen) > 0 else {}
    }
    
    # 5. Verificar rango de fechas
    print("\n=== 5. ANÁLISIS DE FECHAS ===")
    
    if len(df_origen) > 0:
        fechas = pd.to_datetime(df_origen['fecha'])
        print(f"Fecha más antigua: {fechas.min()}")
        print(f"Fecha más reciente: {fechas.max()}")
        
        results["analysis"]["date_analysis"] = {
            "earliest_date": str(fechas.min()),
            "latest_date": str(fechas.max()),
            "date_range_days": (fechas.max() - fechas.min()).days
        }
    
    conn.close()
    
    # Guardar resultados
    output_file = f"debug_3104277553_backend_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== RESULTADOS GUARDADOS EN: {output_file} ===")
    
    return results

def check_correlation_algorithm_filters():
    """Verificar los filtros aplicados en el algoritmo de correlación"""
    
    print("\n=== VERIFICANDO ALGORITMO DE CORRELACIÓN ===")
    
    # Verificar si existe el archivo de servicio de correlación
    correlation_service_path = os.path.join(os.path.dirname(__file__), 'services', 'correlation_service_hunter_validated.py')
    
    if os.path.exists(correlation_service_path):
        print(f"✓ Archivo de servicio encontrado: {correlation_service_path}")
        
        with open(correlation_service_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar menciones de filtros HUNTER
        hunter_mentions = content.count('hunter')
        print(f"Menciones de 'hunter' en el código: {hunter_mentions}")
        
        # Buscar filtros de celda
        if 'celda' in content.lower():
            print("✓ El algoritmo incluye filtros por celda")
        else:
            print("✗ No se detectaron filtros por celda explícitos")
            
    else:
        print(f"✗ No se encontró el archivo: {correlation_service_path}")

if __name__ == "__main__":
    print("INICIANDO ANÁLISIS BACKEND DEL NÚMERO 3104277553")
    print("=" * 60)
    
    try:
        results = analyze_3104277553_in_database()
        check_correlation_algorithm_filters()
        
        print("\n" + "=" * 60)
        print("ANÁLISIS COMPLETADO - REVISE EL ARCHIVO JSON GENERADO")
        
    except Exception as e:
        print(f"ERROR EN ANÁLISIS: {str(e)}")
        import traceback
        traceback.print_exc()