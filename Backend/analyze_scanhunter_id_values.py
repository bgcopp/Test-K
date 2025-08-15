#!/usr/bin/env python3
"""
Análisis exhaustivo de los valores de ID en SCANHUNTER.xlsx
Para verificar los valores reales en la columna 'Id'
"""

import pandas as pd
import json
from datetime import datetime
import os

def analyze_scanhunter_ids():
    """Analiza los valores únicos de ID en el archivo SCANHUNTER.xlsx"""
    
    file_path = r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\SCANHUNTER.xlsx"
    
    print("=== ANÁLISIS DE VALORES ID EN SCANHUNTER.xlsx ===")
    print(f"Archivo: {file_path}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    if not os.path.exists(file_path):
        print(f"ERROR: El archivo no existe en la ruta especificada")
        return
    
    try:
        # Leer el archivo Excel
        print("Leyendo archivo Excel...")
        df = pd.read_excel(file_path)
        
        print(f"Archivo leído exitosamente")
        print(f"Total de filas: {len(df)}")
        print(f"Total de columnas: {len(df.columns)}")
        
        # Mostrar nombres de columnas
        print(f"\nCOLUMNAS DISPONIBLES:")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i}. '{col}'")
        
        # Verificar si existe la columna 'Id'
        id_columns = [col for col in df.columns if 'id' in col.lower()]
        print(f"\nColumnas que contienen 'id': {id_columns}")
        
        # Analizar la columna 'Id' específicamente
        if 'Id' in df.columns:
            id_column = 'Id'
        elif 'ID' in df.columns:
            id_column = 'ID'
        elif 'id' in df.columns:
            id_column = 'id'
        else:
            print("ERROR: No se encontró columna 'Id' en el archivo")
            return
        
        print(f"\nANALISIS DE LA COLUMNA: '{id_column}'")
        print("-" * 40)
        
        # Obtener valores únicos de ID
        unique_ids = df[id_column].unique()
        unique_ids_sorted = sorted([x for x in unique_ids if pd.notna(x)])
        
        print(f"Valores únicos de ID encontrados: {unique_ids_sorted}")
        print(f"Cantidad de valores únicos: {len(unique_ids_sorted)}")
        
        # Contar registros por ID
        id_counts = df[id_column].value_counts().sort_index()
        
        print(f"\nDISTRIBUCION DE REGISTROS POR ID:")
        print("-" * 40)
        for id_val, count in id_counts.items():
            if pd.notna(id_val):
                print(f"   ID {id_val}: {count} registros")
        
        # Mostrar ejemplos de registros para cada ID
        print(f"\nEJEMPLOS DE REGISTROS POR ID:")
        print("-" * 40)
        
        for id_val in unique_ids_sorted[:5]:  # Mostrar hasta 5 IDs
            print(f"\n   ID = {id_val}:")
            id_samples = df[df[id_column] == id_val].head(3)  # 3 ejemplos por ID
            
            for idx, row in id_samples.iterrows():
                print(f"      Fila {idx + 1}: ID={row[id_column]}", end="")
                # Mostrar algunas columnas adicionales para contexto
                other_cols = [col for col in df.columns if col != id_column][:3]
                for col in other_cols:
                    if pd.notna(row[col]):
                        value = str(row[col])[:20] + "..." if len(str(row[col])) > 20 else str(row[col])
                        print(f", {col}={value}", end="")
                print()
        
        # Verificar valores nulos
        null_count = df[id_column].isnull().sum()
        print(f"\nValores nulos en columna ID: {null_count}")
        
        # Resumen final
        print(f"\nRESUMEN FINAL:")
        print("-" * 40)
        print(f"Valores únicos de ID: {unique_ids_sorted}")
        print(f"Total de registros: {len(df)}")
        print(f"IDs únicos: {len(unique_ids_sorted)}")
        print(f"Valores nulos: {null_count}")
        
        # Guardar resultado en JSON para referencia
        result = {
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "total_records": int(len(df)),
            "total_columns": int(len(df.columns)),
            "unique_ids": [int(x) for x in unique_ids_sorted],
            "id_counts": {int(k): int(v) for k, v in id_counts.dropna().items()},
            "null_count": int(null_count),
            "columns": list(df.columns)
        }
        
        output_file = f"scanhunter_id_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\nAnalisis guardado en: {output_file}")
        
    except Exception as e:
        print(f"ERROR al procesar el archivo: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_scanhunter_ids()