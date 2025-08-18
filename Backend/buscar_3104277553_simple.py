#!/usr/bin/env python3
"""
Búsqueda simple del número 3104277553
"""

import pandas as pd
import os

files = [
    r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\1-225211_LLAMADAS_ENTRANTES_POR_CELDA_545612_0.xlsx",
    r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\1-225211_LLAMADAS_SALIENTES_POR_CELDA_545613_0.xlsx",
    r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\2-225211_LLAMADAS_ENTRANTES_POR_CELDA_545614_0.xlsx",
    r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\2-225211_LLAMADAS_SALIENTES_POR_CELDA_545615_0.xlsx"
]

print("BUSQUEDA DEL NUMERO 3104277553")
print("=" * 40)

target = "3104277553"
total_found = 0

for file_path in files:
    if not os.path.exists(file_path):
        continue
    
    filename = os.path.basename(file_path)
    print(f"\nArchivo: {filename}")
    
    try:
        df = pd.read_excel(file_path)
        print(f"  Registros: {len(df)}")
        
        # Buscar en originador
        orig_matches = df['originador'].astype(str).str.contains(target, na=False).sum()
        print(f"  Como originador: {orig_matches}")
        
        # Buscar en receptor
        recv_matches = df['receptor'].astype(str).str.contains(target, na=False).sum()
        print(f"  Como receptor: {recv_matches}")
        
        file_total = orig_matches + recv_matches
        total_found += file_total
        print(f"  Total en archivo: {file_total}")
        
        # Si se encuentra, mostrar detalles
        if file_total > 0:
            print("  DETALLES:")
            if orig_matches > 0:
                mask = df['originador'].astype(str).str.contains(target, na=False)
                samples = df[mask].head(2)
                for idx, row in samples.iterrows():
                    print(f"    Fila {idx}: {row['originador']} -> {row['receptor']}")
            
            if recv_matches > 0:
                mask = df['receptor'].astype(str).str.contains(target, na=False)
                samples = df[mask].head(2)
                for idx, row in samples.iterrows():
                    print(f"    Fila {idx}: {row['originador']} -> {row['receptor']}")
    
    except Exception as e:
        print(f"  Error: {e}")

print(f"\nRESUMEN:")
print(f"Total apariciones: {total_found}")
if total_found > 0:
    print("El numero SI esta en los archivos")
else:
    print("El numero NO esta en los archivos")