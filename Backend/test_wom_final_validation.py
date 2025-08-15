#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WOM Cell ID Display Fix - Final Comprehensive Validation

Este test final valida exhaustivamente que la corrección del display de cell_id_voz
funciona correctamente en todos los niveles del sistema.

Autor: Testing Engineer
Fecha: 14-08-2025
"""

import sys
import os
import pandas as pd
import json
from datetime import datetime

# Agregar el directorio Backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from services.data_normalizer_service import DataNormalizerService
from services.file_processor_service import FileProcessorService

def test_raw_excel_files():
    """Verificar que los archivos Excel originales contienen los cell_ids esperados"""
    print("=" * 80)
    print("TEST 1: VALIDACION DE ARCHIVOS EXCEL ORIGINALES")
    print("=" * 80)
    
    wom_files = [
        "C:/Soluciones/BGC/claude/KNSOft/datatest/wom/Formato excel/PUNTO 1 TRÁFICO DATOS WOM.xlsx",
        "C:/Soluciones/BGC/claude/KNSOft/datatest/wom/Formato excel/PUNTO 1 TRÁFICO VOZ ENTRAN  SALIENT WOM.xlsx"
    ]
    
    expected_cell_ids = ['11648', '2981895']
    results = {}
    
    for file_path in wom_files:
        if not os.path.exists(file_path):
            print(f"[SKIP] Archivo no encontrado: {os.path.basename(file_path)}")
            continue
            
        print(f"\nAnalizando: {os.path.basename(file_path)}")
        print("-" * 60)
        
        try:
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            print(f"Hojas: {sheet_names}")
            
            file_results = {
                'sheets': [],
                'cell_ids_found': [],
                'expected_ids_found': [],
                'concatenated_found': []
            }
            
            for sheet_name in sheet_names:
                print(f"  Hoja: '{sheet_name}'")
                df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=20)
                
                # Buscar columnas de cell_id
                cell_id_cols = [col for col in df.columns if 'cell_id' in str(col).lower()]
                
                sheet_result = {
                    'name': sheet_name,
                    'cell_id_columns': cell_id_cols,
                    'cell_ids': []
                }
                
                if cell_id_cols:
                    for col in cell_id_cols:
                        unique_values = df[col].dropna().unique()
                        for value in unique_values:
                            str_value = str(value).strip()
                            if str_value and str_value != 'nan':
                                sheet_result['cell_ids'].append(str_value)
                                file_results['cell_ids_found'].append(str_value)
                                
                                # Verificar si es un ID esperado
                                if str_value in expected_cell_ids:
                                    file_results['expected_ids_found'].append(str_value)
                                    print(f"    [EXPECTED] {str_value}")
                                elif str_value.startswith('WOM_'):
                                    file_results['concatenated_found'].append(str_value)
                                    print(f"    [CONCATENATED] {str_value}")
                                else:
                                    print(f"    [OTHER] {str_value}")
                
                file_results['sheets'].append(sheet_result)
            
            results[os.path.basename(file_path)] = file_results
            
            print(f"  RESUMEN:")
            print(f"    Cell IDs totales: {len(file_results['cell_ids_found'])}")
            print(f"    IDs esperados encontrados: {len(file_results['expected_ids_found'])}")
            print(f"    IDs concatenados: {len(file_results['concatenated_found'])}")
            
        except Exception as e:
            print(f"  [ERROR] {str(e)}")
            results[os.path.basename(file_path)] = {'error': str(e)}
    
    return results

def test_data_normalizer():
    """Probar el normalizador de datos con datos simulados"""
    print("=" * 80)
    print("TEST 2: VALIDACION DEL NORMALIZADOR DE DATOS")
    print("=" * 80)
    
    normalizer = DataNormalizerService()
    
    # Datos de prueba que simulan estructura WOM
    test_data = pd.DataFrame({
        'CELL_ID_VOZ': [11648, 2981895, 123456, 789012],
        'SECTOR': [1, 1, 2, 3],
        'NUMERO_ORIGEN': ['56912345678', '56987654321', '56911111111', '56922222222'],
        'OPERADOR_TECNOLOGIA': ['WOM_LTE', 'WOM_LTE', 'WOM_LTE', 'WOM_LTE'],
        'FECHA_HORA_INICIO': ['2024-08-14 10:00:00', '2024-08-14 10:05:00', '2024-08-14 10:10:00', '2024-08-14 10:15:00'],
        'FECHA_HORA_FIN': ['2024-08-14 10:02:00', '2024-08-14 10:06:25', '2024-08-14 10:13:20', '2024-08-14 10:18:45'],
        'DURACION_SEG': [120, 85, 200, 285],
        'UP_DATA_BYTES': [1024, 2048, 512, 4096],
        'DOWN_DATA_BYTES': [8192, 4096, 1024, 16384]
    })
    
    print("Datos de entrada (sample):")
    print(test_data[['CELL_ID_VOZ', 'SECTOR', 'NUMERO_ORIGEN']].head())
    
    try:
        # Probar normalización
        normalized_df = normalizer.normalize_wom_cellular_data(test_data)
        
        if normalized_df is None:
            print("[ERROR] El normalizador retornó None")
            return False
        
        print(f"\nDatos normalizados:")
        print(f"Filas: {len(normalized_df)}")
        print(f"Columnas: {list(normalized_df.columns)}")
        
        if 'cell_id_voz' in normalized_df.columns:
            cell_id_values = normalized_df['cell_id_voz'].tolist()
            print(f"\nValores cell_id_voz: {cell_id_values}")
            
            # Analizar formato de los valores
            clean_values = []
            concatenated_values = []
            
            for value in cell_id_values:
                str_value = str(value)
                if str_value.startswith('WOM_') and '_' in str_value:
                    concatenated_values.append(str_value)
                elif str_value.replace('.', '').replace('-', '').isdigit():
                    clean_values.append(str_value)
            
            print(f"Valores limpios: {clean_values}")
            print(f"Valores concatenados: {concatenated_values}")
            
            if concatenated_values:
                print("[FAIL] Se encontraron valores concatenados en el normalizador")
                return False
            else:
                print("[PASS] Todos los valores están en formato limpio")
                return True
        else:
            print("[ERROR] Columna cell_id_voz no encontrada")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error en normalización: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_file_processor_integration():
    """Probar la integración completa del procesador de archivos"""
    print("=" * 80)
    print("TEST 3: VALIDACION DEL PROCESADOR DE ARCHIVOS (INTEGRATION)")
    print("=" * 80)
    
    # Verificar que el código del fix está presente
    processor_path = "C:/Soluciones/BGC/claude/KNSOft/Backend/services/file_processor_service.py"
    
    if os.path.exists(processor_path):
        with open(processor_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Buscar la línea específica del fix
            if "str(normalized_data.get('cell_id_voz', ''))" in content:
                print("[PASS] Fix implementado correctamente en file_processor_service.py")
                print("  Línea encontrada: str(normalized_data.get('cell_id_voz', ''))")
                
                # Verificar que no hay formatos concatenados obsoletos
                obsolete_patterns = [
                    'f"WOM_{normalized_data.get(\'cell_id_voz\', \'\')}_',
                    'f"WOM_{cell_id_voz}_',
                    '"WOM_" + str(cell_id_voz) + "_"'
                ]
                
                obsolete_found = []
                for pattern in obsolete_patterns:
                    if pattern in content:
                        obsolete_found.append(pattern)
                
                if obsolete_found:
                    print(f"[WARNING] Patrones obsoletos encontrados: {obsolete_found}")
                    return False
                else:
                    print("[PASS] No se encontraron patrones de concatenación obsoletos")
                    return True
            else:
                print("[FAIL] Fix no encontrado en file_processor_service.py")
                return False
    else:
        print(f"[ERROR] Archivo no encontrado: {processor_path}")
        return False

def main():
    """Ejecutar todas las validaciones"""
    print("WOM CELL_ID_VOZ DISPLAY FIX - VALIDACION FINAL COMPLETA")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Ejecutar todos los tests
    test1_results = test_raw_excel_files()
    test2_result = test_data_normalizer()  
    test3_result = test_file_processor_integration()
    
    # Resumen final
    print("=" * 80)
    print("RESUMEN FINAL DE VALIDACION")
    print("=" * 80)
    
    # Análisis de archivos Excel
    excel_analysis = {
        'files_processed': len([f for f in test1_results.keys() if 'error' not in test1_results[f]]),
        'expected_ids_found': 0,
        'concatenated_ids_found': 0
    }
    
    for file_name, file_data in test1_results.items():
        if 'error' not in file_data:
            excel_analysis['expected_ids_found'] += len(file_data.get('expected_ids_found', []))
            excel_analysis['concatenated_ids_found'] += len(file_data.get('concatenated_found', []))
    
    print(f"TEST 1 - Archivos Excel:")
    print(f"  Archivos procesados: {excel_analysis['files_processed']}")
    print(f"  IDs esperados encontrados: {excel_analysis['expected_ids_found']}")
    print(f"  IDs concatenados encontrados: {excel_analysis['concatenated_ids_found']}")
    print(f"  Resultado: {'PASS' if excel_analysis['expected_ids_found'] > 0 and excel_analysis['concatenated_ids_found'] == 0 else 'FAIL'}")
    
    print(f"\nTEST 2 - Normalizador de datos: {'PASS' if test2_result else 'FAIL'}")
    print(f"TEST 3 - Procesador de archivos: {'PASS' if test3_result else 'FAIL'}")
    
    # Veredicto final
    overall_success = (
        excel_analysis['expected_ids_found'] > 0 and 
        excel_analysis['concatenated_ids_found'] == 0 and
        test2_result and 
        test3_result
    )
    
    print(f"\n{'=' * 30}")
    if overall_success:
        print("VEREDICTO: [PASS] ✓ FIX VALIDADO EXITOSAMENTE")
        print()
        print("CONFIRMACIONES:")
        print("✓ Los archivos WOM muestran cell_id_voz en formato limpio (11648, 2981895)")
        print("✓ No se encontraron formatos concatenados WOM_xxx_xxx en archivos")
        print("✓ El normalizador produce valores limpios")
        print("✓ El código del fix está correctamente implementado")
        print()
        print("CONCLUSION:")
        print("El fix para mostrar cell_id_voz sin concatenación WOM_xxx_xxx")
        print("está funcionando correctamente. Los valores se muestran como")
        print("números limpios según lo esperado.")
    else:
        print("VEREDICTO: [FAIL] ✗ FIX REQUIERE REVISION")
        print()
        print("PROBLEMAS DETECTADOS:")
        if excel_analysis['expected_ids_found'] == 0:
            print("✗ No se encontraron los IDs esperados en archivos")
        if excel_analysis['concatenated_ids_found'] > 0:
            print("✗ Se encontraron IDs concatenados en archivos")
        if not test2_result:
            print("✗ El normalizador tiene problemas")
        if not test3_result:
            print("✗ El procesador de archivos requiere ajustes")
    
    print("=" * 30)
    
    # Guardar reporte completo
    final_report = {
        'timestamp': datetime.now().isoformat(),
        'overall_success': overall_success,
        'test1_excel_files': test1_results,
        'test2_normalizer': test2_result,
        'test3_processor': test3_result,
        'excel_analysis': excel_analysis
    }
    
    report_path = "C:/Soluciones/BGC/claude/KNSOft/Backend/wom_final_validation_report.json"
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)
        print(f"\n[OK] Reporte completo guardado: {report_path}")
    except Exception as e:
        print(f"[WARNING] No se pudo guardar reporte: {e}")

if __name__ == "__main__":
    main()