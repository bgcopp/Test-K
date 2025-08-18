#!/usr/bin/env python3
"""
ANALISIS DE CORRELACION REAL KRONOS
===============================================================================
Analiza correlacion cruzada entre celdas HUNTER y archivos CLARO reales
para identificar por que el algoritmo no encuentra todos los numeros
"""

import pandas as pd
import os
from collections import Counter, defaultdict

def load_hunter_data():
    """Carga datos HUNTER reales"""
    file_path = r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\SCANHUNTER.xlsx"
    
    try:
        df = pd.read_excel(file_path)
        hunter_cells = set(df['CELLID'].dropna().astype(str))
        print(f"HUNTER: {len(hunter_cells)} celdas unicas")
        print(f"HUNTER celdas: {sorted(list(hunter_cells))[:10]}... (primeras 10)")
        return hunter_cells
    except Exception as e:
        print(f"ERROR cargando HUNTER: {e}")
        return set()

def analyze_claro_correlation(hunter_cells):
    """Analiza correlacion con archivos CLARO"""
    base_path = r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)"
    claro_files = [
        "1-225211_LLAMADAS_ENTRANTES_POR_CELDA_545612_0.xlsx",
        "1-225211_LLAMADAS_SALIENTES_POR_CELDA_545613_0.xlsx", 
        "2-225211_LLAMADAS_ENTRANTES_POR_CELDA_545614_0.xlsx",
        "2-225211_LLAMADAS_SALIENTES_POR_CELDA_545615_0.xlsx"
    ]
    
    all_correlations = defaultdict(int)  # numero -> count
    cell_matches = set()  # celdas que coinciden
    total_records = 0
    
    for claro_file in claro_files:
        file_path = os.path.join(base_path, claro_file)
        print(f"\n=== ANALIZANDO: {claro_file} ===")
        
        try:
            df = pd.read_excel(file_path)
            total_records += len(df)
            
            # Convertir celdas a string para comparacion
            df['celda_inicio_str'] = df['celda_inicio_llamada'].astype(str)
            df['celda_final_str'] = df['celda_final_llamada'].astype(str)
            
            # Encontrar coincidencias con celdas HUNTER
            matches_inicio = df['celda_inicio_str'].isin(hunter_cells)
            matches_final = df['celda_final_str'].isin(hunter_cells)
            matches_any = matches_inicio | matches_final
            
            matched_records = df[matches_any]
            
            print(f"Total registros: {len(df)}")
            print(f"Coincidencias con HUNTER: {len(matched_records)}")
            
            if len(matched_records) > 0:
                # Celdas que coinciden
                matched_cells_inicio = set(df[matches_inicio]['celda_inicio_str'].unique())
                matched_cells_final = set(df[matches_final]['celda_final_str'].unique())
                file_cell_matches = matched_cells_inicio.union(matched_cells_final)
                cell_matches.update(file_cell_matches)
                
                print(f"Celdas coincidentes: {sorted(list(file_cell_matches))}")
                
                # Contar numeros por originador Y receptor
                for _, row in matched_records.iterrows():
                    originador = str(row['originador'])
                    receptor = str(row['receptor'])
                    
                    # Contar si la celda coincide
                    if row['celda_inicio_str'] in hunter_cells or row['celda_final_str'] in hunter_cells:
                        all_correlations[originador] += 1
                        all_correlations[receptor] += 1
            else:
                print("NO hay coincidencias de celdas")
                
        except Exception as e:
            print(f"ERROR: {e}")
    
    print(f"\n=== RESUMEN CORRELACION ===")
    print(f"Total registros procesados: {total_records}")
    print(f"Celdas HUNTER que coinciden: {len(cell_matches)}")
    print(f"Celdas coincidentes: {sorted(list(cell_matches))}")
    print(f"Numeros con correlaciones: {len(all_correlations)}")
    
    # Top numeros por ocurrencias
    top_numbers = sorted(all_correlations.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\nTOP 20 NUMEROS CON MAS OCURRENCIAS:")
    for i, (numero, count) in enumerate(top_numbers[:20]):
        print(f"{i+1:2}. {numero}: {count} ocurrencias")
    
    # Numeros objetivo especificos
    target_numbers = ['3143534707', '3104277553', '3224274851']
    print(f"\nNUMEROS OBJETIVO ESPECIFICOS:")
    for target in target_numbers:
        count = all_correlations.get(target, 0)
        if count > 0:
            print(f"OK {target}: {count} ocurrencias")
        else:
            print(f"NO {target}: 0 ocurrencias")
    
    return all_correlations, cell_matches

def analyze_minimum_occurrences(correlations):
    """Analiza como cambian resultados con diferentes minimos"""
    print(f"\n=== ANALISIS POR MINIMO DE OCURRENCIAS ===")
    
    for min_occ in [1, 2, 3, 5, 10]:
        filtered = {k: v for k, v in correlations.items() if v >= min_occ}
        print(f"Min {min_occ}: {len(filtered)} numeros")

def main():
    print("=" * 80)
    print("ANALISIS DE CORRELACION REAL KRONOS")
    print("=" * 80)
    
    # Cargar celdas HUNTER
    hunter_cells = load_hunter_data()
    if not hunter_cells:
        print("ERROR: No se pudieron cargar celdas HUNTER")
        return
    
    print(f"\nHUNTER celdas totales: {len(hunter_cells)}")
    
    # Analizar correlacion
    correlations, cell_matches = analyze_claro_correlation(hunter_cells)
    
    # Analizar por minimos
    analyze_minimum_occurrences(correlations)
    
    print(f"\n=== DIAGNOSTICO ===")
    if len(correlations) == 0:
        print("ERROR CRITICO: No hay correlaciones encontradas")
        print("Posibles causas:")
        print("1. Las celdas en HUNTER no coinciden con celdas en CLARO")
        print("2. Formato de celdas diferente (string vs int)")
        print("3. Error en logica de correlacion")
    elif len(correlations) < 10:
        print("ADVERTENCIA: Muy pocas correlaciones encontradas")
        print("Es posible que haya problema en el algoritmo")
    else:
        print("OK: Correlaciones encontradas correctamente")
    
    print("\nANALISIS COMPLETADO")

if __name__ == "__main__":
    main()