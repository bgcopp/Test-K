#!/usr/bin/env python3
"""
ANALISIS DE ARCHIVOS REALES KRONOS - VERSION SIMPLE
===============================================================================
Analiza los archivos reales para determinar ocurrencias correctas
"""

import pandas as pd
import os
from collections import Counter
import json
from datetime import datetime

def analyze_hunter_file(file_path):
    """Analiza el archivo SCANHUNTER.xlsx"""
    print(f"=== ANALIZANDO ARCHIVO HUNTER: {file_path} ===")
    
    if not os.path.exists(file_path):
        print(f"ERROR: Archivo no encontrado: {file_path}")
        return None
    
    try:
        df = pd.read_excel(file_path)
        print(f"OK Archivo leido exitosamente")
        print(f"DATOS Filas: {len(df)}, Columnas: {len(df.columns)}")
        print(f"COLUMNAS: {list(df.columns)}")
        print()
        
        print("PRIMERAS 5 FILAS:")
        print(df.head())
        print()
        
        # Buscar columna de Cell ID
        cell_id_columns = [col for col in df.columns if 'cell' in col.lower() or 'celda' in col.lower()]
        print(f"CELL ID Columnas potenciales: {cell_id_columns}")
        
        if cell_id_columns:
            cell_column = cell_id_columns[0]
            unique_cells = df[cell_column].dropna().unique()
            print(f"CELDAS unicas encontradas ({len(unique_cells)}): {list(unique_cells)}")
        else:
            for col in df.columns:
                sample_values = df[col].dropna().head(10).tolist()
                print(f"COLUMNA '{col}': {sample_values}")
        
        return df
        
    except Exception as e:
        print(f"ERROR al leer archivo HUNTER: {e}")
        return None

def analyze_claro_file(file_path):
    """Analiza un archivo de datos CLARO"""
    print(f"=== ANALIZANDO ARCHIVO CLARO: {os.path.basename(file_path)} ===")
    
    if not os.path.exists(file_path):
        print(f"ERROR: Archivo no encontrado: {file_path}")
        return None
    
    try:
        df = pd.read_excel(file_path)
        print(f"OK Archivo leido exitosamente")
        print(f"DATOS Filas: {len(df)}, Columnas: {len(df.columns)}")
        print(f"COLUMNAS: {list(df.columns)}")
        print()
        
        print("PRIMERAS 5 FILAS:")
        print(df.head())
        print()
        
        # Buscar columnas de números de teléfono
        phone_columns = []
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['numero', 'phone', 'originador', 'receptor', 'numero_a', 'numero_b']):
                phone_columns.append(col)
        
        print(f"TELEFONO Columnas potenciales: {phone_columns}")
        
        # Buscar columnas de celdas
        cell_columns = []
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['celda', 'cell', 'tower']):
                cell_columns.append(col)
        
        print(f"CELDA Columnas potenciales: {cell_columns}")
        
        # Analizar números únicos en columnas de teléfonos
        all_phones = set()
        for col in phone_columns:
            phones_in_col = df[col].dropna().astype(str).unique()
            print(f"NUMEROS unicos en '{col}' ({len(phones_in_col)}): {list(phones_in_col[:10])}")
            if len(phones_in_col) > 10:
                print("... (mas numeros)")
            all_phones.update(phones_in_col)
        
        print(f"TOTAL numeros unicos encontrados: {len(all_phones)}")
        
        # Contar ocurrencias de números específicos
        target_numbers = ['3143534707', '3104277553', '3224274851', '573143534707', '573104277553', '573224274851']
        
        print("\nANALISIS DE NUMEROS OBJETIVO:")
        for target in target_numbers:
            count = 0
            found_in_columns = []
            
            for col in phone_columns:
                col_count = (df[col].astype(str) == target).sum()
                if col_count > 0:
                    count += col_count
                    found_in_columns.append(f"{col}({col_count})")
            
            if count > 0:
                print(f"OK {target}: {count} ocurrencias en {', '.join(found_in_columns)}")
            else:
                print(f"NO {target}: No encontrado")
        
        return df
        
    except Exception as e:
        print(f"ERROR al leer archivo CLARO: {e}")
        return None

def main():
    """Función principal de análisis"""
    print("=" * 80)
    print("INICIANDO ANALISIS DE ARCHIVOS REALES KRONOS")
    print("=" * 80)
    
    # Rutas de archivos
    base_path = r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)"
    
    hunter_file = os.path.join(base_path, "SCANHUNTER.xlsx")
    claro_files = [
        "1-225211_LLAMADAS_ENTRANTES_POR_CELDA_545612_0.xlsx",
        "1-225211_LLAMADAS_SALIENTES_POR_CELDA_545613_0.xlsx", 
        "2-225211_LLAMADAS_ENTRANTES_POR_CELDA_545614_0.xlsx",
        "2-225211_LLAMADAS_SALIENTES_POR_CELDA_545615_0.xlsx"
    ]
    
    # Analizar archivo HUNTER
    hunter_df = analyze_hunter_file(hunter_file)
    print("\n" + "-" * 60 + "\n")
    
    # Analizar archivos CLARO
    for claro_file in claro_files:
        file_path = os.path.join(base_path, claro_file)
        claro_df = analyze_claro_file(file_path)
        print("\n" + "-" * 60 + "\n")
    
    print("ANALISIS COMPLETADO")

if __name__ == "__main__":
    main()