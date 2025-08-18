#!/usr/bin/env python3
"""
Script para DEPURAR el algoritmo de carga CLARO y encontrar dónde se pierden los números.
Simulando el proceso paso a paso para identificar el problema crítico.

Autor: Sistema KRONOS - Depuración crítica
"""

import pandas as pd
import re
from pathlib import Path
import sys
import os

# Añadir el path del backend para importar servicios
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.file_processor_service import FileProcessorService
from services.data_normalizer_service import DataNormalizerService

def debug_claro_loading_step_by_step():
    """Simula el proceso de carga paso a paso para identificar donde se pierden los números"""
    
    print("=" * 80)
    print("DEPURACION CRITICA: ALGORITMO DE CARGA CLARO")
    print("=" * 80)
    
    # Números objetivo que DEBEN aparecer
    target_numbers = ['3224274851', '3208611034', '3104277553', '3102715509', '3143534707', '3214161903']
    
    # Archivo de prueba
    test_file = r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\1-225211_LLAMADAS_ENTRANTES_POR_CELDA_545612_0.xlsx"
    
    if not Path(test_file).exists():
        print(f"ERROR: Archivo de prueba no encontrado: {test_file}")
        return
    
    print(f"ARCHIVO DE PRUEBA: {Path(test_file).name}")
    print("-" * 80)
    
    # === PASO 1: LECTURA ORIGINAL ===
    print("\n1. LECTURA ORIGINAL DEL ARCHIVO:")
    df_original = pd.read_excel(test_file)
    print(f"   - Filas originales: {len(df_original)}")
    print(f"   - Columnas: {list(df_original.columns)}")
    
    # Buscar números objetivo en datos originales
    found_in_original = {}
    for target in target_numbers:
        found_in_original[target] = {
            'originador': (df_original['originador'].astype(str) == target).sum(),
            'receptor': (df_original['receptor'].astype(str) == target).sum()
        }
    
    print("   - Números objetivo en archivo original:")
    for target, counts in found_in_original.items():
        total = counts['originador'] + counts['receptor']
        print(f"     {target}: originador={counts['originador']}, receptor={counts['receptor']}, total={total}")
    
    # === PASO 2: SIMULANDO LIMPIEZA DE DATOS ===
    print("\n2. SIMULANDO LIMPIEZA DE DATOS (como hace FileProcessorService):")
    
    # Copiar y limpiar como hace el servicio
    clean_df = df_original.copy()
    
    # Limpiar números telefónicos (como en _clean_claro_call_data)
    print("   - Limpiando campo 'originador'...")
    clean_df['originador'] = clean_df['originador'].astype(str).str.strip()
    clean_df['originador'] = clean_df['originador'].str.replace(r'[^\d]', '', regex=True)  # Solo dígitos
    
    print("   - Limpiando campo 'receptor'...")
    clean_df['receptor'] = clean_df['receptor'].astype(str).str.strip()
    clean_df['receptor'] = clean_df['receptor'].str.replace(r'[^\d]', '', regex=True)  # Solo dígitos
    
    # Limpiar fecha-hora
    clean_df['fecha_hora'] = clean_df['fecha_hora'].astype(str).str.strip()
    
    # Limpiar tipo CDR
    clean_df['tipo'] = clean_df['tipo'].astype(str).str.strip().str.upper()
    
    # Remover filas completamente vacías
    before_dropna = len(clean_df)
    clean_df = clean_df.dropna(how='all')
    after_dropna = len(clean_df)
    print(f"   - Filas eliminadas por dropna(how='all'): {before_dropna - after_dropna}")
    
    # Remover filas donde campos críticos están vacíos
    critical_fields = ['originador', 'receptor', 'fecha_hora', 'tipo']
    before_critical = len(clean_df)
    for field in critical_fields:
        before_field = len(clean_df)
        clean_df = clean_df[clean_df[field].notna()]
        clean_df = clean_df[clean_df[field] != '']
        after_field = len(clean_df)
        print(f"   - Filas eliminadas por campo '{field}' vacío: {before_field - after_field}")
    
    print(f"   - Total de filas después de limpieza: {len(clean_df)} (perdidas: {before_critical - len(clean_df)})")
    
    # Buscar números objetivo después de limpieza
    found_after_cleaning = {}
    for target in target_numbers:
        found_after_cleaning[target] = {
            'originador': (clean_df['originador'].astype(str) == target).sum(),
            'receptor': (clean_df['receptor'].astype(str) == target).sum()
        }
    
    print("   - Números objetivo después de limpieza:")
    for target, counts in found_after_cleaning.items():
        total = counts['originador'] + counts['receptor']
        original_total = found_in_original[target]['originador'] + found_in_original[target]['receptor']
        lost = original_total - total
        print(f"     {target}: total={total} (perdidos en limpieza: {lost})")
    
    # === PASO 3: FILTRADO POR TIPO CDR ===
    print("\n3. FILTRADO POR TIPO CDR (CDR_ENTRANTE):")
    before_filter = len(clean_df)
    filtered_df = clean_df[clean_df['tipo'].str.contains('CDR_ENTRANTE', na=False)]
    after_filter = len(filtered_df)
    print(f"   - Filas antes del filtro: {before_filter}")
    print(f"   - Filas después del filtro CDR_ENTRANTE: {after_filter}")
    print(f"   - Filas eliminadas por filtro de tipo: {before_filter - after_filter}")
    
    # Buscar números objetivo después de filtrado
    found_after_filter = {}
    for target in target_numbers:
        found_after_filter[target] = {
            'originador': (filtered_df['originador'].astype(str) == target).sum(),
            'receptor': (filtered_df['receptor'].astype(str) == target).sum()
        }
    
    print("   - Números objetivo después de filtrado por tipo:")
    for target, counts in found_after_filter.items():
        total = counts['originador'] + counts['receptor']
        cleaned_total = found_after_cleaning[target]['originador'] + found_after_cleaning[target]['receptor']
        lost = cleaned_total - total
        print(f"     {target}: total={total} (perdidos en filtro: {lost})")
    
    # === PASO 4: SIMULANDO NORMALIZACIÓN ===
    print("\n4. SIMULANDO NORMALIZACION DE NUMEROS:")
    
    normalizer = DataNormalizerService()
    
    # Muestras de números para análisis
    sample_originadores = filtered_df['originador'].unique()[:20]
    sample_receptores = filtered_df['receptor'].unique()[:20]
    
    print("   - Ejemplos de normalización 'originador':")
    for orig in sample_originadores:
        normalized = normalizer._normalize_phone_number(str(orig))
        print(f"     {orig} -> {normalized}")
    
    print("   - Ejemplos de normalización 'receptor':")
    for recv in sample_receptores:
        normalized = normalizer._normalize_phone_number(str(recv))
        print(f"     {recv} -> {normalized}")
    
    # Verificar qué pasa con números objetivo específicos
    print("   - Normalización de números objetivo:")
    for target in target_numbers:
        normalized = normalizer._normalize_phone_number(target)
        print(f"     {target} -> {normalized}")
        
        # Buscar variaciones en el DataFrame
        variations_found = []
        for col in ['originador', 'receptor']:
            for value in filtered_df[col].unique():
                if str(value) == target or normalizer._normalize_phone_number(str(value)) == normalized:
                    variations_found.append(f"{col}:{value}")
        
        print(f"       Variaciones encontradas: {variations_found}")
    
    # === PASO 5: VALIDACIÓN DE REGISTROS INDIVIDUALES ===
    print("\n5. VALIDACION DE REGISTROS INDIVIDUALES:")
    
    # Simular validación como hace el servicio
    processor = FileProcessorService()
    
    total_records = len(filtered_df)
    valid_records = 0
    validation_errors = {}
    
    print(f"   - Validando {total_records} registros...")
    
    for idx, row in filtered_df.head(100).iterrows():  # Solo primeros 100 para no sobrecargar
        record = {
            'originador': str(row['originador']),
            'receptor': str(row['receptor']),
            'fecha_hora': str(row['fecha_hora']),
            'tipo': str(row['tipo']),
            'celda_inicio_llamada': str(row['celda_inicio_llamada']),
            'celda_final_llamada': str(row['celda_final_llamada']),
            'duracion': row['duracion']
        }
        
        is_valid, errors = processor._validate_claro_call_record(record, 'ENTRANTE')
        
        if is_valid:
            valid_records += 1
        else:
            for error in errors:
                if error not in validation_errors:
                    validation_errors[error] = 0
                validation_errors[error] += 1
    
    print(f"   - Registros válidos (muestra): {valid_records}/100")
    print(f"   - Errores de validación encontrados:")
    for error, count in validation_errors.items():
        print(f"     {error}: {count} veces")
    
    print("\n" + "=" * 80)
    print("ANALISIS COMPLETADO - REVISE LOS PASOS DONDE SE PIERDEN NUMEROS")
    print("=" * 80)

if __name__ == "__main__":
    debug_claro_loading_step_by_step()