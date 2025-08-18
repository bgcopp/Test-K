#!/usr/bin/env python3
"""
ANÁLISIS COMPLETO CARGA CLARO
============================

Script para analizar por qué los archivos CLARO no cargan el 100% de registros
y asegurar que se carguen todos sin validación de duplicidad.

Autor: Boris - Análisis Carga Completa
Fecha: 2025-08-18
"""

import os
import sys
import pandas as pd
import sqlite3
import json
from datetime import datetime
import traceback

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Archivos a analizar
ARCHIVOS_CLARO = [
    r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\1-225211_LLAMADAS_ENTRANTES_POR_CELDA_545612_0.xlsx",
    r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\1-225211_LLAMADAS_SALIENTES_POR_CELDA_545613_0.xlsx",
    r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\2-225211_LLAMADAS_ENTRANTES_POR_CELDA_545614_0.xlsx",
    r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\2-225211_LLAMADAS_SALIENTES_POR_CELDA_545615_0.xlsx"
]

DB_PATH = r"C:\Soluciones\BGC\claude\KNSOft\Backend\kronos.db"

# Números objetivo que buscamos
NUMEROS_OBJETIVO = ['3224274851', '3208611034', '3104277553', '3102715509', '3143534707', '3214161903']

def print_section(title):
    """Imprime una sección."""
    print(f"\n{'='*70}")
    print(f" {title}")
    print(f"{'='*70}")

def print_error(message):
    """Imprime un mensaje de error."""
    print(f"[ERROR] {message}")

def print_info(message):
    """Imprime un mensaje informativo."""
    print(f"[INFO] {message}")

def print_success(message):
    """Imprime un mensaje de éxito."""
    print(f"[SUCCESS] {message}")

def print_warning(message):
    """Imprime un mensaje de advertencia."""
    print(f"[WARNING] {message}")

def analizar_archivos_excel():
    """Analiza cada archivo Excel para contar registros reales."""
    print_section("ANÁLISIS DE ARCHIVOS EXCEL ORIGINALES")
    
    total_registros_excel = 0
    archivos_info = {}
    
    for archivo in ARCHIVOS_CLARO:
        if not os.path.exists(archivo):
            print_error(f"Archivo no encontrado: {archivo}")
            continue
            
        try:
            print_info(f"Analizando: {os.path.basename(archivo)}")
            
            # Leer Excel
            df = pd.read_excel(archivo)
            registros = len(df)
            total_registros_excel += registros
            
            print_info(f"  Registros en Excel: {registros}")
            print_info(f"  Columnas: {list(df.columns)}")
            
            # Buscar números objetivo en este archivo
            numeros_encontrados = []
            for col in df.columns:
                if any(keyword in col.lower() for keyword in ['origen', 'destino', 'numero', 'phone']):
                    for numero in NUMEROS_OBJETIVO:
                        # Buscar en diferentes formatos
                        encontrado = False
                        if (df[col].astype(str).str.contains(numero, na=False)).any():
                            encontrado = True
                        elif (df[col].astype(str).str.contains(f"57{numero}", na=False)).any():
                            encontrado = True
                        
                        if encontrado and numero not in numeros_encontrados:
                            numeros_encontrados.append(numero)
                            
            if numeros_encontrados:
                print_success(f"  Números objetivo encontrados: {numeros_encontrados}")
            else:
                print_warning(f"  No se encontraron números objetivo en este archivo")
            
            archivos_info[archivo] = {
                'registros': registros,
                'columnas': list(df.columns),
                'numeros_objetivo': numeros_encontrados,
                'muestra': df.head(2).to_dict('records') if len(df) > 0 else []
            }
            
        except Exception as e:
            print_error(f"Error analizando {archivo}: {e}")
            traceback.print_exc()
    
    print_info(f"TOTAL REGISTROS EN EXCEL: {total_registros_excel}")
    return total_registros_excel, archivos_info

def verificar_bd_actual():
    """Verifica cuántos registros hay actualmente en la BD."""
    print_section("VERIFICACIÓN DE BASE DE DATOS ACTUAL")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Total registros CLARO
        cursor.execute("SELECT COUNT(*) FROM operator_call_data WHERE operator = 'CLARO'")
        registros_bd = cursor.fetchone()[0]
        print_info(f"Registros CLARO en BD: {registros_bd}")
        
        # Por tipo de llamada
        cursor.execute("""
            SELECT tipo_llamada, COUNT(*) 
            FROM operator_call_data 
            WHERE operator = 'CLARO' 
            GROUP BY tipo_llamada
        """)
        tipos = cursor.fetchall()
        print_info("Distribución por tipo:")
        for tipo, count in tipos:
            print_info(f"  {tipo}: {count} registros")
        
        # Buscar números objetivo en BD
        numeros_en_bd = {}
        for numero in NUMEROS_OBJETIVO:
            cursor.execute("""
                SELECT COUNT(*) FROM operator_call_data 
                WHERE operator = 'CLARO' 
                AND (numero_origen = ? OR numero_destino = ? OR numero_objetivo = ?)
            """, (numero, numero, numero))
            count = cursor.fetchone()[0]
            numeros_en_bd[numero] = count
            
            if count > 0:
                print_success(f"Número {numero}: {count} registros en BD")
            else:
                print_warning(f"Número {numero}: NO encontrado en BD")
        
        conn.close()
        return registros_bd, numeros_en_bd
        
    except Exception as e:
        print_error(f"Error verificando BD: {e}")
        return 0, {}

def buscar_numeros_objetivo_detallado():
    """Búsqueda detallada de números objetivo en archivos Excel."""
    print_section("BÚSQUEDA DETALLADA DE NÚMEROS OBJETIVO EN EXCEL")
    
    for archivo in ARCHIVOS_CLARO:
        if not os.path.exists(archivo):
            continue
            
        try:
            print_info(f"\nAnalizando: {os.path.basename(archivo)}")
            df = pd.read_excel(archivo)
            
            print_info(f"Columnas disponibles: {list(df.columns)}")
            
            # Buscar en cada columna
            for col in df.columns:
                print_info(f"\n  Buscando en columna: {col}")
                
                for numero in NUMEROS_OBJETIVO:
                    # Diferentes formatos de búsqueda
                    formatos = [numero, f"57{numero}", f"+57{numero}"]
                    
                    for formato in formatos:
                        mask = df[col].astype(str).str.contains(formato, na=False)
                        coincidencias = df[mask]
                        
                        if len(coincidencias) > 0:
                            print_success(f"    ✓ Número {numero} (formato {formato}): {len(coincidencias)} coincidencias")
                            
                            # Mostrar muestra
                            for idx, row in coincidencias.head(2).iterrows():
                                print_info(f"      Fila {idx}: {row[col]}")
                        
        except Exception as e:
            print_error(f"Error buscando en {archivo}: {e}")

def verificar_configuracion_carga():
    """Verifica la configuración actual del file processor para carga."""
    print_section("VERIFICACIÓN DE CONFIGURACIÓN DE CARGA")
    
    try:
        from services.file_processor_service import FileProcessorService
        
        # Crear instancia para revisar configuración
        processor = FileProcessorService()
        
        print_info("FileProcessorService inicializado correctamente")
        
        # Verificar si hay validación de duplicidad
        print_info("Revisando código del file processor...")
        
        # Leer el código fuente para verificar validaciones
        file_processor_path = r"C:\Soluciones\BGC\claude\KNSOft\Backend\services\file_processor_service.py"
        if os.path.exists(file_processor_path):
            with open(file_processor_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Buscar validaciones de duplicidad
            if 'UNIQUE constraint' in content or 'duplicate' in content.lower():
                print_warning("Se encontraron referencias a validaciones de duplicidad")
            
            if 'record_hash' in content:
                print_warning("Se encontró uso de record_hash - posible validación de duplicidad")
                
            # Contar chunking
            if 'chunk' in content.lower():
                print_info("Procesamiento por chunks detectado")
                
        return processor
        
    except Exception as e:
        print_error(f"Error verificando configuración: {e}")
        traceback.print_exc()
        return None

def generar_reporte_completo(registros_excel, registros_bd, archivos_info, numeros_bd):
    """Genera un reporte completo del análisis."""
    print_section("GENERACIÓN DE REPORTE COMPLETO")
    
    # Calcular diferencia
    diferencia = registros_excel - registros_bd
    porcentaje_cargado = (registros_bd / registros_excel * 100) if registros_excel > 0 else 0
    
    reporte = {
        "timestamp": datetime.now().isoformat(),
        "analisis_tipo": "Carga Completa CLARO - Debug",
        "archivos_analizados": ARCHIVOS_CLARO,
        "registros_excel_total": registros_excel,
        "registros_bd_actual": registros_bd,
        "diferencia": diferencia,
        "porcentaje_cargado": round(porcentaje_cargado, 2),
        "archivos_detalle": archivos_info,
        "numeros_objetivo_bd": numeros_bd,
        "problemas_identificados": [],
        "recomendaciones": []
    }
    
    # Identificar problemas
    if diferencia > 0:
        reporte["problemas_identificados"].append(f"Se perdieron {diferencia} registros en la carga ({100-porcentaje_cargado:.1f}%)")
        reporte["recomendaciones"].append("Revisar validaciones de duplicidad en file_processor_service.py")
        reporte["recomendaciones"].append("Verificar procesamiento por chunks")
    
    # Problemas con números objetivo
    numeros_faltantes = [num for num, count in numeros_bd.items() if count == 0]
    if numeros_faltantes:
        reporte["problemas_identificados"].append(f"Números objetivo faltantes: {numeros_faltantes}")
        reporte["recomendaciones"].append("Verificar normalización de números telefónicos")
    
    # Guardar reporte
    report_path = f"analisis_carga_completa_claro_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)
    
    print_success(f"Reporte guardado: {report_path}")
    
    # Resumen
    print_info(f"\nRESUMEN DEL ANÁLISIS:")
    print_info(f"Registros en Excel: {registros_excel}")
    print_info(f"Registros en BD: {registros_bd}")
    print_info(f"Porcentaje cargado: {porcentaje_cargado:.1f}%")
    
    if diferencia > 0:
        print_error(f"PROBLEMA: Faltan {diferencia} registros ({100-porcentaje_cargado:.1f}%)")
    else:
        print_success("Todos los registros fueron cargados")
        
    return report_path

def main():
    """Función principal del análisis."""
    print_section("ANÁLISIS COMPLETO CARGA CLARO - DEBUG")
    print("Analizando por qué los archivos CLARO no cargan el 100%...")
    print(f"Timestamp: {datetime.now()}")
    
    # Fase 1: Analizar archivos Excel originales
    registros_excel, archivos_info = analizar_archivos_excel()
    
    # Fase 2: Verificar BD actual
    registros_bd, numeros_bd = verificar_bd_actual()
    
    # Fase 3: Búsqueda detallada de números objetivo
    buscar_numeros_objetivo_detallado()
    
    # Fase 4: Verificar configuración de carga
    processor = verificar_configuracion_carga()
    
    # Fase 5: Generar reporte
    report_path = generar_reporte_completo(registros_excel, registros_bd, archivos_info, numeros_bd)
    
    print_section("ANÁLISIS COMPLETADO")
    print_info(f"Reporte disponible: {report_path}")
    
    # Conclusiones
    if registros_excel > registros_bd:
        print_error("CONCLUSIÓN: Hay pérdida de registros en la carga")
        print_info("Se requiere eliminar validaciones de duplicidad")
    else:
        print_success("CONCLUSIÓN: No hay pérdida de registros")

if __name__ == "__main__":
    main()