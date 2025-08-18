#!/usr/bin/env python3
"""
VERIFICACION DE NUMEROS OBJETIVO - KRONOS
===============================================================================
Verifica ocurrencias exactas de números objetivo usando la regla:
1 ocurrencia por combinación única número-celda (no por registro individual)
"""

import pandas as pd
import os
from collections import defaultdict
import json
from datetime import datetime

def normalize_phone(phone_str):
    """Normaliza número telefónico para comparaciones"""
    if pd.isna(phone_str):
        return None
    
    phone_clean = str(phone_str).strip()
    if phone_clean.startswith('57') and len(phone_clean) == 12:
        return phone_clean[2:]  # Remueve prefijo 57
    elif len(phone_clean) == 10:
        return phone_clean  # Ya está normalizado
    else:
        return phone_clean  # Devuelve tal como está

def load_hunter_cells():
    """Carga células HUNTER únicas"""
    file_path = r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\SCANHUNTER.xlsx"
    
    try:
        df = pd.read_excel(file_path)
        if 'CELLID' in df.columns:
            hunter_cells = set(df['CELLID'].dropna().astype(str))
            print(f"HUNTER: {len(hunter_cells)} células únicas cargadas")
            return hunter_cells
        else:
            print(f"ERROR: Columna CELLID no encontrada en {file_path}")
            print(f"Columnas disponibles: {list(df.columns)}")
            return set()
    except Exception as e:
        print(f"ERROR cargando HUNTER: {e}")
        return set()

def verify_target_occurrences():
    """Verifica ocurrencias de números objetivo según regla de celda única"""
    
    # Números objetivo a verificar
    target_numbers = ['3224274851', '3208611034', '3104277553', '3102715509', '3143534707']
    
    # Cargar células HUNTER
    hunter_cells = load_hunter_cells()
    if not hunter_cells:
        print("ERROR: No se pudieron cargar células HUNTER")
        return
    
    # Archivos CLARO
    base_path = r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)"
    claro_files = [
        "1-225211_LLAMADAS_ENTRANTES_POR_CELDA_545612_0.xlsx",
        "1-225211_LLAMADAS_SALIENTES_POR_CELDA_545613_0.xlsx", 
        "2-225211_LLAMADAS_ENTRANTES_POR_CELDA_545614_0.xlsx",
        "2-225211_LLAMADAS_SALIENTES_POR_CELDA_545615_0.xlsx"
    ]
    
    # Estructura para contar: target_number -> set de celdas únicas
    target_cell_combinations = defaultdict(set)
    
    print("=== VERIFICACION DE NUMEROS OBJETIVO ===")
    print(f"Números a verificar: {target_numbers}")
    print(f"Células HUNTER: {len(hunter_cells)} únicas")
    print()
    
    # Procesar cada archivo CLARO
    for claro_file in claro_files:
        file_path = os.path.join(base_path, claro_file)
        print(f"Procesando: {claro_file}")
        
        try:
            df = pd.read_excel(file_path)
            
            # Normalizar números telefónicos
            df['originador_norm'] = df['originador'].apply(normalize_phone)
            df['receptor_norm'] = df['receptor'].apply(normalize_phone)
            
            # Convertir celdas a string
            df['celda_inicio_str'] = df['celda_inicio_llamada'].astype(str)
            df['celda_final_str'] = df['celda_final_llamada'].astype(str)
            
            # Buscar registros con números objetivo
            for target in target_numbers:
                # Filtrar registros que contengan el número objetivo
                target_records = df[
                    (df['originador_norm'] == target) | 
                    (df['receptor_norm'] == target)
                ]
                
                if len(target_records) > 0:
                    print(f"  {target}: {len(target_records)} registros encontrados")
                    
                    # Para cada registro, verificar si usa celdas HUNTER
                    for _, row in target_records.iterrows():
                        celda_inicio = row['celda_inicio_str']
                        celda_final = row['celda_final_str']
                        
                        # Si el número es originador y celda inicio está en HUNTER
                        if row['originador_norm'] == target and celda_inicio in hunter_cells:
                            target_cell_combinations[target].add(celda_inicio)
                        
                        # Si el número es receptor y celda final está en HUNTER    
                        if row['receptor_norm'] == target and celda_final in hunter_cells:
                            target_cell_combinations[target].add(celda_final)
                else:
                    print(f"  {target}: 0 registros")
                    
        except Exception as e:
            print(f"  ERROR procesando {claro_file}: {e}")
    
    print("\n=== RESULTADOS FINALES ===")
    print("Conteo por regla de celda única (1 por combinación número-celda):")
    
    results = {}
    for target in target_numbers:
        unique_cells = target_cell_combinations[target]
        occurrence_count = len(unique_cells)
        
        results[target] = {
            'occurrences': occurrence_count,
            'cells': sorted(list(unique_cells))
        }
        
        if occurrence_count > 0:
            print(f"OK {target}: {occurrence_count} ocurrencias")
            print(f"  Celdas: {sorted(list(unique_cells))}")
        else:
            print(f"NO {target}: 0 ocurrencias")
    
    # Guardar resultados
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"target_numbers_verification_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\nResultados guardados en: {output_file}")
    
    return results

def main():
    """Función principal"""
    print("=" * 80)
    print("VERIFICACION DE NUMEROS OBJETIVO - KRONOS")
    print("=" * 80)
    print("Regla: 1 ocurrencia por combinación única número-celda")
    print("=" * 80)
    
    results = verify_target_occurrences()
    
    print("\n" + "=" * 80)
    print("VERIFICACION COMPLETADA")
    print("=" * 80)

if __name__ == "__main__":
    main()