#!/usr/bin/env python3
"""
VERIFICACION ESPECIFICA DEL NUMERO 3143534707
===============================================================================
Analiza específicamente el número 3143534707 para verificar en qué celdas aparece
"""

import pandas as pd
import os
from collections import defaultdict

def analyze_3143534707():
    """Analiza específicamente el número 3143534707"""
    target_number = '3143534707'
    
    # Cargar células HUNTER
    hunter_file = r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\SCANHUNTER.xlsx"
    hunter_df = pd.read_excel(hunter_file)
    hunter_cells = set(hunter_df['CELLID'].dropna().astype(str))
    print(f"HUNTER células: {sorted(list(hunter_cells))}")
    print()
    
    # Archivos CLARO
    base_path = r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)"
    claro_files = [
        "1-225211_LLAMADAS_ENTRANTES_POR_CELDA_545612_0.xlsx",
        "1-225211_LLAMADAS_SALIENTES_POR_CELDA_545613_0.xlsx", 
        "2-225211_LLAMADAS_ENTRANTES_POR_CELDA_545614_0.xlsx",
        "2-225211_LLAMADAS_SALIENTES_POR_CELDA_545615_0.xlsx"
    ]
    
    target_cells = set()
    all_records = []
    
    for claro_file in claro_files:
        file_path = os.path.join(base_path, claro_file)
        print(f"=== ANALIZANDO: {claro_file} ===")
        
        try:
            df = pd.read_excel(file_path)
            
            # Normalizar números
            df['originador_norm'] = df['originador'].apply(lambda x: str(x).replace('57', '', 1) if str(x).startswith('57') and len(str(x)) == 12 else str(x))
            df['receptor_norm'] = df['receptor'].apply(lambda x: str(x).replace('57', '', 1) if str(x).startswith('57') and len(str(x)) == 12 else str(x))
            
            # Convertir celdas a string
            df['celda_inicio_str'] = df['celda_inicio_llamada'].astype(str)
            df['celda_final_str'] = df['celda_final_llamada'].astype(str)
            
            # Buscar registros con el número objetivo
            target_records = df[
                (df['originador_norm'] == target_number) | 
                (df['receptor_norm'] == target_number)
            ]
            
            print(f"Registros encontrados con {target_number}: {len(target_records)}")
            
            for _, row in target_records.iterrows():
                celda_inicio = row['celda_inicio_str']
                celda_final = row['celda_final_str']
                
                # Verificar si las celdas están en HUNTER
                if row['originador_norm'] == target_number:
                    print(f"  Como ORIGINADOR - Celda inicio: {celda_inicio} {'✓ HUNTER' if celda_inicio in hunter_cells else '✗'}")
                    if celda_inicio in hunter_cells:
                        target_cells.add(celda_inicio)
                        all_records.append({
                            'archivo': claro_file,
                            'tipo': 'originador',
                            'celda': celda_inicio,
                            'fecha': row.get('fecha_llamada', 'N/A'),
                            'hora': row.get('hora_llamada', 'N/A')
                        })
                
                if row['receptor_norm'] == target_number:
                    print(f"  Como RECEPTOR - Celda final: {celda_final} {'✓ HUNTER' if celda_final in hunter_cells else '✗'}")
                    if celda_final in hunter_cells:
                        target_cells.add(celda_final)
                        all_records.append({
                            'archivo': claro_file,
                            'tipo': 'receptor',
                            'celda': celda_final,
                            'fecha': row.get('fecha_llamada', 'N/A'),
                            'hora': row.get('hora_llamada', 'N/A')
                        })
            
            print()
            
        except Exception as e:
            print(f"ERROR: {e}")
    
    print("=== RESUMEN FINAL ===")
    print(f"Número analizado: {target_number}")
    print(f"Celdas HUNTER donde aparece: {sorted(list(target_cells))}")
    print(f"Total ocurrencias (por regla de celda única): {len(target_cells)}")
    
    print("\nDETALLE POR CELDA:")
    for celda in sorted(target_cells):
        records_in_cell = [r for r in all_records if r['celda'] == celda]
        print(f"  Celda {celda}: {len(records_in_cell)} registros")
        for record in records_in_cell:
            print(f"    - {record['tipo']} en {record['archivo']} ({record['fecha']} {record['hora']})")
    
    return target_cells, all_records

if __name__ == "__main__":
    analyze_3143534707()