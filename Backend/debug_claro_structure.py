#!/usr/bin/env python3
"""
Script para analizar la estructura de archivos CLARO y encontrar el problema de números faltantes.
Autor: Sistema KRONOS - Análisis crítico
"""

import pandas as pd
import re
from pathlib import Path

def analyze_claro_file_structure():
    """Analiza la estructura de archivos CLARO para identificar problemas"""
    
    # Archivos de prueba CLARO
    claro_files = [
        r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\1-225211_LLAMADAS_ENTRANTES_POR_CELDA_545612_0.xlsx",
        r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\1-225211_LLAMADAS_SALIENTES_POR_CELDA_545613_0.xlsx",
        r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\2-225211_LLAMADAS_ENTRANTES_POR_CELDA_545614_0.xlsx",
        r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\2-225211_LLAMADAS_SALIENTES_POR_CELDA_545615_0.xlsx"
    ]
    
    # Números objetivo que DEBEN aparecer
    target_numbers = ['3224274851', '3208611034', '3104277553', '3102715509', '3143534707', '3214161903']
    
    print("=" * 80)
    print("ANALISIS CRITICO DE ESTRUCTURA DE ARCHIVOS CLARO")
    print("=" * 80)
    
    for file_path in claro_files:
        if not Path(file_path).exists():
            print(f"ARCHIVO NO ENCONTRADO: {file_path}")
            continue
            
        print(f"\nANALIZANDO: {Path(file_path).name}")
        print("-" * 60)
        
        try:
            # Leer archivo Excel
            df = pd.read_excel(file_path)
            
            print(f"INFORMACION BASICA:")
            print(f"   - Total de filas: {len(df)}")
            print(f"   - Columnas: {list(df.columns)}")
            print(f"   - Primeras 3 filas:")
            print(df.head(3).to_string())
            
            # Buscar columnas de números telefónicos
            phone_columns = []
            for col in df.columns:
                if any(keyword in str(col).lower() for keyword in ['numero', 'telefono', 'originador', 'receptor', 'phone']):
                    phone_columns.append(col)
            
            print(f"\nCOLUMNAS DE NUMEROS DETECTADAS: {phone_columns}")
            
            # Analizar números únicos en cada columna de teléfonos
            for col in phone_columns:
                if col in df.columns:
                    print(f"\nANALISIS COLUMNA '{col}':")
                    
                    # Números únicos
                    unique_numbers = df[col].dropna().unique()
                    print(f"   - Numeros unicos: {len(unique_numbers)}")
                    
                    # Mostrar algunos ejemplos
                    sample_numbers = list(unique_numbers[:10])
                    print(f"   - Ejemplos: {sample_numbers}")
                    
                    # Buscar números objetivo
                    found_targets = []
                    for target in target_numbers:
                        # Buscar diferentes formatos
                        formats_to_check = [
                            target,
                            f"57{target}",
                            f"+57{target}",
                            f"0{target}"
                        ]
                        
                        for fmt in formats_to_check:
                            if any(str(num) == fmt for num in unique_numbers):
                                found_targets.append(f"{target} (formato: {fmt})")
                                break
                    
                    if found_targets:
                        print(f"   OK - NUMEROS OBJETIVO ENCONTRADOS: {found_targets}")
                    else:
                        print(f"   ERROR - NUMEROS OBJETIVO NO ENCONTRADOS")
                        
                        # Buscar similares (primeros 6 dígitos)
                        similar_found = []
                        for target in target_numbers:
                            prefix = target[:6]
                            similar = [str(num) for num in unique_numbers if str(num).startswith(prefix)]
                            if similar:
                                similar_found.extend(similar)
                        
                        if similar_found:
                            print(f"   INFO - NUMEROS SIMILARES (mismo prefijo): {similar_found[:5]}")
                    
                    # Analizar patrones de números
                    patterns = {
                        'con_57': 0,
                        'sin_57': 0,
                        'celular_3': 0,
                        'otros': 0
                    }
                    
                    for num in unique_numbers:
                        num_str = str(num).strip()
                        if num_str.startswith('57') and len(num_str) == 12:
                            patterns['con_57'] += 1
                        elif len(num_str) == 10 and num_str.startswith('3'):
                            patterns['sin_57'] += 1
                            patterns['celular_3'] += 1
                        else:
                            patterns['otros'] += 1
                    
                    print(f"   PATRONES DE NUMEROS:")
                    for pattern, count in patterns.items():
                        print(f"      {pattern}: {count}")
        
        except Exception as e:
            print(f"ERROR ANALIZANDO ARCHIVO: {str(e)}")
    
    print("\n" + "=" * 80)
    print("ANALISIS COMPLETADO")
    print("=" * 80)

if __name__ == "__main__":
    analyze_claro_file_structure()