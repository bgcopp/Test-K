#!/usr/bin/env python3
"""
ANÁLISIS DE ARCHIVOS REALES KRONOS
===============================================================================
Analiza los archivos reales para determinar:
1. Número real de ocurrencias de cada teléfono
2. Si se procesan originador y receptor correctamente
3. Por qué salen solo pocos números en lugar de más

Archivos a analizar:
- SCANHUNTER.xlsx (datos de celdas HUNTER)
- Archivos CLARO (datos de llamadas)

Autor: Claude Code para Boris
Fecha: 2025-08-18
===============================================================================
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
        print(f"❌ ERROR: Archivo no encontrado: {file_path}")
        return None
    
    try:
        # Leer el archivo Excel
        df = pd.read_excel(file_path)
        print(f"OK Archivo leido exitosamente")
        print(f"DATOS Filas: {len(df)}, Columnas: {len(df.columns)}")
        print(f"COLUMNAS disponibles: {list(df.columns)}")
        print()
        
        # Mostrar primeras filas
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
            # Buscar por contenido que parezca Cell ID
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
        print(f"❌ ERROR: Archivo no encontrado: {file_path}")
        return None
    
    try:
        # Leer el archivo Excel
        df = pd.read_excel(file_path)
        print(f"✅ Archivo leído exitosamente")
        print(f"📊 Filas: {len(df)}, Columnas: {len(df.columns)}")
        print(f"📋 Columnas disponibles: {list(df.columns)}")
        print()
        
        # Mostrar primeras filas
        print("🔍 PRIMERAS 5 FILAS:")
        print(df.head())
        print()
        
        # Buscar columnas de números de teléfono
        phone_columns = []
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['numero', 'phone', 'originador', 'receptor', 'numero_a', 'numero_b']):
                phone_columns.append(col)
        
        print(f"📞 Columnas potenciales de teléfonos: {phone_columns}")
        
        # Buscar columnas de celdas
        cell_columns = []
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['celda', 'cell', 'tower']):
                cell_columns.append(col)
        
        print(f"📡 Columnas potenciales de celdas: {cell_columns}")
        
        # Analizar números únicos en columnas de teléfonos
        all_phones = set()
        for col in phone_columns:
            phones_in_col = df[col].dropna().astype(str).unique()
            print(f"📞 Números únicos en '{col}' ({len(phones_in_col)}): {list(phones_in_col[:10])}{'...' if len(phones_in_col) > 10 else ''}")
            all_phones.update(phones_in_col)
        
        print(f"📞 TOTAL números únicos encontrados: {len(all_phones)}")
        
        # Contar ocurrencias de números específicos que mencionaste
        target_numbers = ['3143534707', '3104277553', '3224274851', '573143534707', '573104277553', '573224274851']
        
        print("\n🎯 ANÁLISIS DE NÚMEROS OBJETIVO:")
        for target in target_numbers:
            count = 0
            found_in_columns = []
            
            for col in phone_columns:
                col_count = (df[col].astype(str) == target).sum()
                if col_count > 0:
                    count += col_count
                    found_in_columns.append(f"{col}({col_count})")
            
            if count > 0:
                print(f"✅ {target}: {count} ocurrencias en {', '.join(found_in_columns)}")
            else:
                print(f"❌ {target}: No encontrado")
        
        # Analizar celdas si están disponibles
        if cell_columns:
            for col in cell_columns[:2]:  # Solo primeras 2 columnas de celdas
                unique_cells = df[col].dropna().unique()
                print(f"📡 Celdas únicas en '{col}' ({len(unique_cells)}): {list(unique_cells[:10])}{'...' if len(unique_cells) > 10 else ''}")
        
        return df
        
    except Exception as e:
        print(f"❌ ERROR al leer archivo CLARO: {e}")
        return None

def analyze_correlation_logic():
    """Analiza la lógica esperada de correlación"""
    print("\n" + "="*80)
    print("ANÁLISIS DE LÓGICA DE CORRELACIÓN ESPERADA")
    print("="*80)
    
    print("""
🔍 PROCESO ESPERADO:

1. DATOS HUNTER (SCANHUNTER.xlsx):
   - Contiene Cell IDs de recorrido de red
   - Estos son las celdas "objetivo" para correlacionar

2. DATOS CLARO (archivos de llamadas):
   - Contienen registros de llamadas con:
     * ORIGINADOR (quien llama)
     * RECEPTOR (quien recibe)
     * CELDA de la llamada
   - AMBOS números (originador Y receptor) deben considerarse

3. CORRELACIÓN:
   - Si un número (originador O receptor) usa una celda que está en HUNTER
   - Y aparece >= mínimo de ocurrencias
   - Entonces es un "objetivo potencial"

4. PROBLEMA IDENTIFICADO:
   - Solo salen 3 números → Posible filtrado incorrecto
   - Números específicos como 3143534707 tienen ocurrencias incorrectas
   - Posible que solo se revise originador O solo receptor, no ambos
    """)

def main():
    """Función principal de análisis"""
    print("="*80)
    print("INICIANDO ANÁLISIS DE ARCHIVOS REALES KRONOS")
    print("="*80)
    
    # Rutas de archivos
    base_path = r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)"
    
    hunter_file = os.path.join(base_path, "SCANHUNTER.xlsx")
    claro_files = [
        "1-225211_LLAMADAS_ENTRANTES_POR_CELDA_545612_0.xlsx",
        "1-225211_LLAMADAS_SALIENTES_POR_CELDA_545613_0.xlsx", 
        "2-225211_LLAMADAS_ENTRANTES_POR_CELDA_545614_0.xlsx",
        "2-225211_LLAMADAS_SALIENTES_POR_CELDA_545615_0.xlsx"
    ]
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'hunter_analysis': {},
        'claro_analysis': [],
        'correlation_issues': []
    }
    
    # Analizar archivo HUNTER
    hunter_df = analyze_hunter_file(hunter_file)
    if hunter_df is not None:
        results['hunter_analysis'] = {
            'file_found': True,
            'rows': len(hunter_df),
            'columns': list(hunter_df.columns)
        }
    
    # Analizar archivos CLARO
    for claro_file in claro_files:
        file_path = os.path.join(base_path, claro_file)
        claro_df = analyze_claro_file(file_path)
        
        if claro_df is not None:
            analysis = {
                'filename': claro_file,
                'rows': len(claro_df),
                'columns': list(claro_df.columns),
                'file_found': True
            }
            results['claro_analysis'].append(analysis)
        else:
            results['claro_analysis'].append({
                'filename': claro_file,
                'file_found': False
            })
        
        print("\n" + "-"*60 + "\n")
    
    # Análisis de lógica de correlación
    analyze_correlation_logic()
    
    # Guardar resultados
    output_file = f"file_analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📄 REPORTE GUARDADO: {output_file}")
    print("\n" + "="*80)
    print("ANÁLISIS COMPLETADO")
    print("="*80)

if __name__ == "__main__":
    main()