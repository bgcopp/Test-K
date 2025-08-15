#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WOM Cell ID Display Fix - Simple Validation Test

Este test simplificado verifica directamente el procesamiento de datos WOM
para confirmar que los cell_id_voz se muestran en formato limpio sin concatenación.

Autor: Testing Engineer
Fecha: 14-08-2025
"""

import sys
import os
import pandas as pd
from pathlib import Path
import json
from datetime import datetime

# Agregar el directorio Backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from services.data_normalizer_service import DataNormalizerService

class SimpleCellIDValidator:
    """Validador simple para cell_id_voz en archivos WOM"""
    
    def __init__(self):
        self.results = []
        self.normalizer = DataNormalizerService()
    
    def test_wom_file_processing(self, file_path: str):
        """Procesar archivo WOM y verificar formato de cell_id_voz"""
        print(f"\nProcesando: {os.path.basename(file_path)}")
        print("-" * 60)
        
        try:
            # Leer el archivo Excel
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            print(f"Hojas encontradas: {len(sheet_names)}")
            
            total_clean_ids = 0
            total_concatenated_ids = 0
            all_cell_ids = []
            
            # Procesar cada hoja (limitado a las primeras 2 para prueba rápida)
            for sheet_name in sheet_names[:2]:
                print(f"\n  Procesando hoja: '{sheet_name}'")
                
                # Leer datos de la hoja
                df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=100)  # Primeras 100 filas
                
                # Buscar columnas relevantes de cell_id
                cell_id_cols = []
                for col in df.columns:
                    col_lower = str(col).lower()
                    if any(keyword in col_lower for keyword in ['cell_id', 'celda', 'cell']):
                        cell_id_cols.append(col)
                
                print(f"    Columnas de cell_id encontradas: {cell_id_cols}")
                
                if cell_id_cols:
                    for col in cell_id_cols:
                        # Obtener valores únicos no nulos
                        unique_values = df[col].dropna().unique()[:10]  # Primeros 10 valores
                        
                        for value in unique_values:
                            str_value = str(value).strip()
                            if str_value and str_value != 'nan':
                                all_cell_ids.append(str_value)
                                
                                # Verificar formato
                                if str_value.startswith('WOM_') and str_value.count('_') >= 2:
                                    total_concatenated_ids += 1
                                    print(f"    [CONCATENADO] {str_value}")
                                elif str_value.replace('.', '').replace('-', '').isdigit():
                                    total_clean_ids += 1
                                    print(f"    [LIMPIO] {str_value}")
                                else:
                                    print(f"    [OTRO] {str_value}")
            
            # Resultados del archivo
            file_result = {
                'file': os.path.basename(file_path),
                'sheets_processed': min(len(sheet_names), 2),
                'total_cell_ids': len(all_cell_ids),
                'clean_ids': total_clean_ids,
                'concatenated_ids': total_concatenated_ids,
                'sample_clean': [id for id in all_cell_ids if not id.startswith('WOM_')][:5],
                'sample_concatenated': [id for id in all_cell_ids if id.startswith('WOM_')][:5]
            }
            
            self.results.append(file_result)
            
            print(f"\n  RESUMEN:")
            print(f"    Total cell_ids: {len(all_cell_ids)}")
            print(f"    Formato limpio: {total_clean_ids}")
            print(f"    Formato concatenado: {total_concatenated_ids}")
            
            if total_concatenated_ids > 0:
                print(f"    [PROBLEMA] Se encontraron {total_concatenated_ids} IDs concatenados")
                return False
            elif total_clean_ids > 0:
                print(f"    [OK] Todos los IDs están en formato limpio")
                return True
            else:
                print(f"    [WARNING] No se encontraron cell_ids válidos")
                return False
                
        except Exception as e:
            print(f"    [ERROR] {str(e)}")
            error_result = {
                'file': os.path.basename(file_path),
                'error': str(e),
                'error_type': type(e).__name__
            }
            self.results.append(error_result)
            return False
    
    def test_data_normalizer_directly(self):
        """Probar el normalizador de datos directamente"""
        print(f"\n\nPrueba directa del normalizador de datos")
        print("-" * 60)
        
        # Crear datos de prueba que simulan datos WOM
        test_data = pd.DataFrame({
            'CELL_ID_VOZ': [11648, 2981895, 123456],
            'SECTOR': [1, 1, 2],
            'NUMERO_ORIGEN': ['56912345678', '56987654321', '56911111111'],
            'OPERADOR_TECNOLOGIA': ['WOM_LTE', 'WOM_LTE', 'WOM_LTE'],
            'FECHA_HORA_INICIO': ['2024-08-14 10:00:00', '2024-08-14 10:05:00', '2024-08-14 10:10:00'],
            'DURACION_SEG': [120, 85, 200]
        })
        
        print("Datos de prueba:")
        print(test_data[['CELL_ID_VOZ', 'SECTOR']].head())
        
        try:
            # Normalizar usando el servicio WOM Cellular Data
            normalized_df = self.normalizer.normalize_wom_cellular_data(test_data)
            
            print(f"\nDatos normalizados (columnas cell_id_voz):")
            if 'cell_id_voz' in normalized_df.columns:
                cell_id_values = normalized_df['cell_id_voz'].tolist()
                print(f"Valores cell_id_voz: {cell_id_values}")
                
                # Verificar que los valores son limpios
                clean_values = []
                concatenated_values = []
                
                for value in cell_id_values:
                    str_value = str(value)
                    if str_value.startswith('WOM_') and '_' in str_value:
                        concatenated_values.append(str_value)
                    else:
                        clean_values.append(str_value)
                
                print(f"Valores limpios: {clean_values}")
                print(f"Valores concatenados: {concatenated_values}")
                
                if concatenated_values:
                    print(f"[PROBLEMA] El normalizador aún genera valores concatenados")
                    return False
                else:
                    print(f"[OK] El normalizador produce valores limpios")
                    return True
            else:
                print("[ERROR] Columna cell_id_voz no encontrada en datos normalizados")
                return False
                
        except Exception as e:
            print(f"[ERROR] Error en normalización: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_validation(self):
        """Ejecutar todas las validaciones"""
        print("=" * 80)
        print("VALIDACION SIMPLE - WOM CELL_ID_VOZ DISPLAY FIX")
        print("=" * 80)
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test 1: Normalizador directo
        normalizer_ok = self.test_data_normalizer_directly()
        
        # Test 2: Archivos WOM reales
        wom_files = [
            "C:/Soluciones/BGC/claude/KNSOft/datatest/wom/Formato excel/PUNTO 1 TRÁFICO DATOS WOM.xlsx",
            "C:/Soluciones/BGC/claude/KNSOft/datatest/wom/Formato excel/PUNTO 1 TRÁFICO VOZ ENTRAN  SALIENT WOM.xlsx"
        ]
        
        files_processed = 0
        files_ok = 0
        
        for file_path in wom_files:
            if os.path.exists(file_path):
                files_processed += 1
                if self.test_wom_file_processing(file_path):
                    files_ok += 1
        
        # Generar veredicto final
        print(f"\n\n" + "=" * 80)
        print("REPORTE FINAL")
        print("=" * 80)
        
        print(f"Normalizador directo: {'OK' if normalizer_ok else 'FAIL'}")
        print(f"Archivos procesados: {files_processed}")
        print(f"Archivos OK: {files_ok}")
        
        overall_success = normalizer_ok and (files_ok == files_processed if files_processed > 0 else True)
        
        if overall_success:
            print(f"\n[PASS] VALIDACION EXITOSA")
            print(f"  El fix de cell_id_voz está funcionando correctamente")
            print(f"  Los valores se muestran en formato limpio sin concatenación")
        else:
            print(f"\n[FAIL] VALIDACION FALLIDA")
            print(f"  Se detectaron problemas en el formato de cell_id_voz")
            if not normalizer_ok:
                print(f"  - El normalizador aún genera valores concatenados")
            if files_processed > 0 and files_ok < files_processed:
                print(f"  - {files_processed - files_ok} archivos tienen problemas")
        
        # Guardar resultados detallados
        detailed_results = {
            'timestamp': datetime.now().isoformat(),
            'normalizer_test': normalizer_ok,
            'files_processed': files_processed,
            'files_ok': files_ok,
            'overall_success': overall_success,
            'file_details': self.results
        }
        
        report_path = "C:/Soluciones/BGC/claude/KNSOft/Backend/wom_simple_validation_report.json"
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(detailed_results, f, indent=2, ensure_ascii=False)
            print(f"\n[OK] Reporte guardado: {report_path}")
        except Exception as e:
            print(f"[WARNING] No se pudo guardar reporte: {e}")
        
        print("=" * 80)

def main():
    """Función principal"""
    try:
        validator = SimpleCellIDValidator()
        validator.run_validation()
    except Exception as e:
        print(f"[ERROR] Error en validación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()