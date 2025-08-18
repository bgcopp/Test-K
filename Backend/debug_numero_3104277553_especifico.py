#!/usr/bin/env python3
"""
DEBUG ESPECÍFICO - Número 3104277553
===================================
El testing muestra que este número ESTÁ en los archivos pero NO en la BD.
Investigar específicamente qué ocurre durante el proceso de carga.
"""

import pandas as pd
import os
import sys

# Archivos de prueba
TEST_FILES = [
    r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\1-225211_LLAMADAS_ENTRANTES_POR_CELDA_545612_0.xlsx",
    r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\1-225211_LLAMADAS_SALIENTES_POR_CELDA_545613_0.xlsx",
    r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\2-225211_LLAMADAS_ENTRANTES_POR_CELDA_545614_0.xlsx",
    r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\2-225211_LLAMADAS_SALIENTES_POR_CELDA_545615_0.xlsx"
]

TARGET_NUMBER = "3104277553"

def analizar_numero_especifico():
    print("ANÁLISIS ESPECÍFICO DEL NÚMERO 3104277553")
    print("=" * 60)
    print(f"Buscando número: {TARGET_NUMBER}")
    print()
    
    total_apariciones = 0
    archivos_con_numero = []
    
    for file_path in TEST_FILES:
        if not os.path.exists(file_path):
            print(f"⚠️  Archivo no encontrado: {os.path.basename(file_path)}")
            continue
        
        print(f"Analizando: {os.path.basename(file_path)}")
        print("-" * 40)
        
        try:
            # Leer archivo
            df = pd.read_excel(file_path)
            print(f"  Total registros en archivo: {len(df)}")
            print(f"  Columnas: {list(df.columns)}")
            
            # Buscar el número específico
            apariciones_originador = 0
            apariciones_receptor = 0
            registros_encontrados = []
            
            if 'originador' in df.columns:
                # Buscar en originador (tanto con 57 como sin 57)
                mask_orig = df['originador'].astype(str).str.contains(TARGET_NUMBER, na=False)
                apariciones_originador = mask_orig.sum()
                
                if apariciones_originador > 0:
                    registros_orig = df[mask_orig]
                    for idx, row in registros_orig.iterrows():
                        registros_encontrados.append({
                            'tipo': 'originador',
                            'fila': idx,
                            'originador': row['originador'],
                            'receptor': row.get('receptor', 'N/A'),
                            'fecha_hora': row.get('fecha_hora', 'N/A'),
                            'celda_inicio': row.get('celda_inicio_llamada', 'N/A'),
                            'celda_final': row.get('celda_final_llamada', 'N/A')
                        })
            
            if 'receptor' in df.columns:
                # Buscar en receptor
                mask_recv = df['receptor'].astype(str).str.contains(TARGET_NUMBER, na=False)
                apariciones_receptor = mask_recv.sum()
                
                if apariciones_receptor > 0:
                    registros_recv = df[mask_recv]
                    for idx, row in registros_recv.iterrows():
                        registros_encontrados.append({
                            'tipo': 'receptor',
                            'fila': idx,
                            'originador': row.get('originador', 'N/A'),
                            'receptor': row['receptor'],
                            'fecha_hora': row.get('fecha_hora', 'N/A'),
                            'celda_inicio': row.get('celda_inicio_llamada', 'N/A'),
                            'celda_final': row.get('celda_final_llamada', 'N/A')
                        })
            
            total_en_archivo = apariciones_originador + apariciones_receptor
            total_apariciones += total_en_archivo
            
            print(f"  Apariciones como originador: {apariciones_originador}")
            print(f"  Apariciones como receptor: {apariciones_receptor}")
            print(f"  TOTAL en este archivo: {total_en_archivo}")
            
            if total_en_archivo > 0:
                archivos_con_numero.append(os.path.basename(file_path))
                print(f"  ✅ NÚMERO ENCONTRADO EN ESTE ARCHIVO")
                
                print(f"  Detalles de registros encontrados:")
                for i, reg in enumerate(registros_encontrados, 1):
                    print(f"    Registro {i} (fila {reg['fila']}):")
                    print(f"      Tipo: {reg['tipo']}")
                    print(f"      Originador: {reg['originador']}")
                    print(f"      Receptor: {reg['receptor']}")
                    print(f"      Fecha: {reg['fecha_hora']}")
                    print(f"      Celda inicio: {reg['celda_inicio']}")
                    print(f"      Celda final: {reg['celda_final']}")
                    print()
            else:
                print(f"  ❌ Número NO encontrado en este archivo")
            
            print()
            
        except Exception as e:
            print(f"  ❌ Error procesando archivo: {e}")
            print()
    
    print("RESUMEN FINAL:")
    print("=" * 40)
    print(f"Total apariciones encontradas: {total_apariciones}")
    print(f"Archivos que contienen el número: {len(archivos_con_numero)}")
    if archivos_con_numero:
        print(f"Archivos: {archivos_con_numero}")
    
    if total_apariciones > 0:
        print(f"✅ CONFIRMADO: El número {TARGET_NUMBER} SÍ ESTÁ en los archivos de origen")
        print("❌ PROBLEMA: El número no está llegando a la base de datos")
        print("🔍 ACCIÓN: Revisar algoritmo de carga específico para este número")
    else:
        print(f"❌ El número {TARGET_NUMBER} NO está en ningún archivo de prueba")
        print("🔍 ACCIÓN: Verificar si está en otros archivos o fechas diferentes")

def simular_procesamiento_numero():
    """Simular exactamente lo que pasaría con este número en el proceso de carga."""
    print("\n" + "=" * 60)
    print("SIMULACIÓN DE PROCESAMIENTO DEL NÚMERO")
    print("=" * 60)
    
    # Simular diferentes transformaciones
    numero_original = "573104277553"  # Formato con prefijo
    numero_sin_prefijo = "3104277553"   # Formato sin prefijo
    
    print(f"Número original (con 57): {numero_original}")
    print(f"Número sin prefijo: {numero_sin_prefijo}")
    
    # Simular validaciones comunes
    validaciones = []
    
    # 1. Longitud
    if len(numero_sin_prefijo) >= 8:
        validaciones.append("✅ Longitud válida")
    else:
        validaciones.append("❌ Longitud inválida")
    
    # 2. Solo dígitos
    if numero_sin_prefijo.isdigit():
        validaciones.append("✅ Solo dígitos")
    else:
        validaciones.append("❌ Contiene caracteres no numéricos")
    
    # 3. Formato colombiano
    if numero_sin_prefijo.startswith('3') and len(numero_sin_prefijo) == 10:
        validaciones.append("✅ Formato celular colombiano válido")
    else:
        validaciones.append("❌ Formato celular colombiano inválido")
    
    print("\nValidaciones simuladas:")
    for validacion in validaciones:
        print(f"  {validacion}")
    
    # Simular hash para duplicados
    import hashlib
    hash_sim = hashlib.md5(f"{numero_original}_{numero_sin_prefijo}".encode()).hexdigest()[:8]
    print(f"\nHash simulado para duplicados: {hash_sim}")
    
    # Simular normalización
    print(f"\nNormalización simulada:")
    print(f"  Input: {numero_original}")
    print(f"  Output: {numero_sin_prefijo}")
    print(f"  Preservado: {numero_original}")

if __name__ == "__main__":
    analizar_numero_especifico()
    simular_procesamiento_numero()