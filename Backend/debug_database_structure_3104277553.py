"""
Análisis de estructura de base de datos para investigar el número 3104277553
"""

import sqlite3
import pandas as pd
import os

def connect_database():
    """Conecta a la base de datos SQLite"""
    db_path = os.path.join(os.path.dirname(__file__), 'kronos.db')
    return sqlite3.connect(db_path)

def explore_database_structure():
    """Explorar la estructura completa de la base de datos"""
    
    conn = connect_database()
    
    print("=== EXPLORANDO ESTRUCTURA DE BASE DE DATOS ===")
    
    # 1. Obtener todas las tablas
    query_tables = """
    SELECT name FROM sqlite_master 
    WHERE type='table'
    ORDER BY name
    """
    
    tables_df = pd.read_sql_query(query_tables, conn)
    print(f"Tablas encontradas: {len(tables_df)}")
    
    for table_name in tables_df['name']:
        print(f"\n--- TABLA: {table_name} ---")
        
        # Obtener información de columnas
        query_columns = f"PRAGMA table_info({table_name})"
        columns_df = pd.read_sql_query(query_columns, conn)
        
        print("Columnas:")
        for _, col in columns_df.iterrows():
            print(f"  - {col['name']} ({col['type']})")
        
        # Contar registros
        try:
            count_query = f"SELECT COUNT(*) as count FROM {table_name}"
            count_result = pd.read_sql_query(count_query, conn)
            print(f"Total de registros: {count_result.iloc[0]['count']}")
        except:
            print("No se pudo contar registros")
    
    conn.close()

def search_3104277553_in_all_tables():
    """Buscar el número 3104277553 en todas las tablas posibles"""
    
    conn = connect_database()
    
    print("\n=== BUSCANDO 3104277553 EN TODAS LAS TABLAS ===")
    
    # Obtener todas las tablas
    query_tables = """
    SELECT name FROM sqlite_master 
    WHERE type='table'
    ORDER BY name
    """
    
    tables_df = pd.read_sql_query(query_tables, conn)
    
    for table_name in tables_df['name']:
        print(f"\n--- BUSCANDO EN TABLA: {table_name} ---")
        
        try:
            # Obtener estructura de columnas
            query_columns = f"PRAGMA table_info({table_name})"
            columns_df = pd.read_sql_query(query_columns, conn)
            
            # Buscar en cada columna de texto
            for _, col in columns_df.iterrows():
                col_name = col['name']
                col_type = col['type'].upper()
                
                if 'TEXT' in col_type or 'VARCHAR' in col_type or 'CHAR' in col_type:
                    try:
                        search_query = f"""
                        SELECT COUNT(*) as count 
                        FROM {table_name} 
                        WHERE {col_name} = '3104277553'
                        """
                        
                        result = pd.read_sql_query(search_query, conn)
                        count = result.iloc[0]['count']
                        
                        if count > 0:
                            print(f"  ✓ ENCONTRADO en columna '{col_name}': {count} registros")
                            
                            # Obtener detalles de los registros encontrados
                            detail_query = f"""
                            SELECT * FROM {table_name} 
                            WHERE {col_name} = '3104277553'
                            LIMIT 5
                            """
                            
                            details = pd.read_sql_query(detail_query, conn)
                            print("    Primeros registros:")
                            for idx, row in details.iterrows():
                                print(f"      {dict(row)}")
                        else:
                            print(f"  - No encontrado en columna '{col_name}'")
                            
                    except Exception as e:
                        print(f"  ! Error buscando en columna '{col_name}': {str(e)}")
        
        except Exception as e:
            print(f"Error procesando tabla {table_name}: {str(e)}")
    
    conn.close()

def search_cell_53591():
    """Buscar específicamente la celda 53591"""
    
    conn = connect_database()
    
    print("\n=== BUSCANDO CELDA 53591 ===")
    
    # Obtener todas las tablas
    query_tables = """
    SELECT name FROM sqlite_master 
    WHERE type='table'
    ORDER BY name
    """
    
    tables_df = pd.read_sql_query(query_tables, conn)
    
    for table_name in tables_df['name']:
        print(f"\n--- BUSCANDO CELDA 53591 EN TABLA: {table_name} ---")
        
        try:
            # Obtener estructura de columnas
            query_columns = f"PRAGMA table_info({table_name})"
            columns_df = pd.read_sql_query(query_columns, conn)
            
            # Buscar en cada columna
            for _, col in columns_df.iterrows():
                col_name = col['name']
                
                try:
                    search_query = f"""
                    SELECT COUNT(*) as count 
                    FROM {table_name} 
                    WHERE {col_name} = '53591'
                    """
                    
                    result = pd.read_sql_query(search_query, conn)
                    count = result.iloc[0]['count']
                    
                    if count > 0:
                        print(f"  ✓ CELDA 53591 encontrada en columna '{col_name}': {count} registros")
                
                except:
                    # Intentar búsqueda numérica
                    try:
                        search_query = f"""
                        SELECT COUNT(*) as count 
                        FROM {table_name} 
                        WHERE {col_name} = 53591
                        """
                        
                        result = pd.read_sql_query(search_query, conn)
                        count = result.iloc[0]['count']
                        
                        if count > 0:
                            print(f"  ✓ CELDA 53591 encontrada (numérica) en columna '{col_name}': {count} registros")
                    except:
                        pass
        
        except Exception as e:
            print(f"Error procesando tabla {table_name}: {str(e)}")
    
    conn.close()

if __name__ == "__main__":
    print("INICIANDO ANÁLISIS DE ESTRUCTURA DE BASE DE DATOS")
    print("=" * 60)
    
    try:
        explore_database_structure()
        search_3104277553_in_all_tables()
        search_cell_53591()
        
        print("\n" + "=" * 60)
        print("ANÁLISIS DE ESTRUCTURA COMPLETADO")
        
    except Exception as e:
        print(f"ERROR EN ANÁLISIS: {str(e)}")
        import traceback
        traceback.print_exc()