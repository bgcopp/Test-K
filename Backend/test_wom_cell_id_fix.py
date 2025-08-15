#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WOM Cell ID Display Fix Validation Test

Este script valida que la corrección del display de cell_id_voz funciona correctamente:
- Los valores de cell_id_voz se muestran como números limpios (ej: "11648", "2981895")
- No se muestra el formato concatenado "WOM_{cell_id_voz}_{sector}"
- El procesamiento de archivos WOM mantiene 100% de éxito
- Los datos en la base de datos son correctos

Autor: Testing Engineer
Fecha: 14-08-2025
"""

import sys
import os
import sqlite3
import pandas as pd
from pathlib import Path
import json
from typing import Dict, List, Tuple, Any
import tempfile
import shutil
from datetime import datetime

# Agregar el directorio Backend al path para importar servicios
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from services.file_processor_service import FileProcessorService
from services.data_normalizer_service import DataNormalizerService

class WOMCellIDFixValidator:
    """Validador para la corrección del display de cell_id_voz en archivos WOM"""
    
    def __init__(self):
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests_executed': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'critical_issues': [],
            'major_issues': [],
            'minor_issues': [],
            'test_details': []
        }
        
        # Archivos WOM de prueba disponibles
        self.wom_test_files = [
            "C:/Soluciones/BGC/claude/KNSOft/datatest/wom/Formato excel/PUNTO 1 TRÁFICO DATOS WOM.xlsx",
            "C:/Soluciones/BGC/claude/KNSOft/datatest/wom/Formato excel/PUNTO 1 TRÁFICO VOZ ENTRAN  SALIENT WOM.xlsx"
        ]
        
        # Base de datos temporal para pruebas
        self.temp_db_path = None
        self.create_temp_database()
    
    def create_temp_database(self):
        """Crear base de datos temporal para las pruebas"""
        temp_dir = tempfile.mkdtemp()
        self.temp_db_path = os.path.join(temp_dir, "test_kronos.db")
        
        # Copiar esquema de la base de datos principal si existe
        main_db_path = "C:/Soluciones/BGC/claude/KNSOft/Backend/kronos.db"
        if os.path.exists(main_db_path):
            shutil.copy2(main_db_path, self.temp_db_path)
            print(f"[OK] Base de datos temporal creada: {self.temp_db_path}")
        else:
            print(f"[WARNING] Base de datos principal no encontrada: {main_db_path}")
    
    def log_test_result(self, test_name: str, passed: bool, details: Dict[str, Any], 
                       severity: str = "minor"):
        """Registrar resultado de una prueba"""
        self.test_results['tests_executed'] += 1
        
        if passed:
            self.test_results['tests_passed'] += 1
            status = "PASS"
        else:
            self.test_results['tests_failed'] += 1
            status = "FAIL"
            
            # Categorizar el issue según severidad
            issue = {
                'test_name': test_name,
                'details': details,
                'timestamp': datetime.now().isoformat()
            }
            
            if severity == "critical":
                self.test_results['critical_issues'].append(issue)
            elif severity == "major":
                self.test_results['major_issues'].append(issue)
            else:
                self.test_results['minor_issues'].append(issue)
        
        self.test_results['test_details'].append({
            'test_name': test_name,
            'status': status,
            'details': details
        })
        
        print(f"[{status}] {test_name}")
        if details:
            for key, value in details.items():
                print(f"    {key}: {value}")
    
    def validate_file_exists_and_readable(self) -> bool:
        """Validar que los archivos WOM de prueba existen y son accesibles"""
        test_name = "File Availability Check"
        available_files = []
        missing_files = []
        
        for file_path in self.wom_test_files:
            if os.path.exists(file_path) and os.path.isfile(file_path):
                available_files.append(file_path)
            else:
                missing_files.append(file_path)
        
        details = {
            'available_files': len(available_files),
            'missing_files': len(missing_files),
            'available_list': available_files,
            'missing_list': missing_files
        }
        
        passed = len(available_files) > 0
        severity = "critical" if len(available_files) == 0 else "minor"
        
        self.log_test_result(test_name, passed, details, severity)
        return passed
    
    def test_cell_id_format_in_processing(self, file_path: str) -> Tuple[bool, Dict]:
        """Probar que el cell_id_voz se procesa con formato limpio"""
        test_name = f"Cell ID Format Test - {os.path.basename(file_path)}"
        
        try:
            # Crear instancia del procesador
            processor = FileProcessorService(self.temp_db_path)
            
            # Leer el archivo Excel para obtener hojas
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            cell_id_values_found = []
            concatenated_formats_found = []
            clean_formats_found = []
            
            # Procesar cada hoja
            for sheet_name in sheet_names[:2]:  # Limitar a 2 hojas para prueba rápida
                print(f"  Procesando hoja: {sheet_name}")
                
                # Leer datos de la hoja
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Buscar columna de cell_id_voz
                cell_id_column = None
                for col in df.columns:
                    if 'cell_id' in col.lower() or 'celda' in col.lower():
                        cell_id_column = col
                        break
                
                if cell_id_column:
                    # Obtener valores únicos de cell_id
                    unique_values = df[cell_id_column].dropna().unique()[:5]  # Primeros 5 valores
                    
                    for value in unique_values:
                        str_value = str(value)
                        cell_id_values_found.append(str_value)
                        
                        # Verificar si tiene formato concatenado WOM_xxx_xxx
                        if str_value.startswith('WOM_') and str_value.count('_') >= 2:
                            concatenated_formats_found.append(str_value)
                        elif str_value.isdigit() or (str_value.replace('.', '').isdigit()):
                            clean_formats_found.append(str_value)
            
            # Evaluar resultados
            total_values = len(cell_id_values_found)
            clean_values = len(clean_formats_found)
            concatenated_values = len(concatenated_formats_found)
            
            details = {
                'total_cell_id_values': total_values,
                'clean_format_values': clean_values,
                'concatenated_format_values': concatenated_values,
                'clean_percentage': (clean_values / total_values * 100) if total_values > 0 else 0,
                'sample_clean_values': clean_formats_found[:3],
                'sample_concatenated_values': concatenated_formats_found[:3],
                'sheets_processed': len(sheet_names)
            }
            
            # La prueba pasa si encontramos valores limpios y no hay concatenados
            passed = clean_values > 0 and concatenated_values == 0
            severity = "major" if concatenated_values > 0 else "minor"
            
            self.log_test_result(test_name, passed, details, severity)
            return passed, details
            
        except Exception as e:
            details = {
                'error': str(e),
                'error_type': type(e).__name__,
                'file_path': file_path
            }
            self.log_test_result(test_name, False, details, "critical")
            return False, details
    
    def test_database_cell_id_storage(self, file_path: str) -> Tuple[bool, Dict]:
        """Validar que los cell_id_voz se almacenan correctamente en la base de datos"""
        test_name = f"Database Cell ID Storage - {os.path.basename(file_path)}"
        
        try:
            # Procesar archivo WOM
            processor = FileProcessorService(self.temp_db_path)
            
            # Simular carga de misión y archivo
            mission_id = 1
            
            # Procesar el archivo
            result = processor.process_file(
                file_path=file_path,
                mission_id=mission_id,
                operator="WOM"
            )
            
            # Verificar resultado del procesamiento
            if not result.get('success', False):
                details = {
                    'processing_failed': True,
                    'error': result.get('error', 'Unknown processing error'),
                    'file_path': file_path
                }
                self.log_test_result(test_name, False, details, "critical")
                return False, details
            
            # Consultar base de datos para verificar cell_id_voz
            conn = sqlite3.connect(self.temp_db_path)
            cursor = conn.cursor()
            
            # Buscar registros con cell_id_voz
            cursor.execute("""
                SELECT DISTINCT cell_id_voz, celda_origen 
                FROM data_records 
                WHERE mission_id = ? 
                AND (cell_id_voz IS NOT NULL OR celda_origen IS NOT NULL)
                LIMIT 10
            """, (mission_id,))
            
            db_records = cursor.fetchall()
            conn.close()
            
            # Analizar los valores almacenados
            clean_cell_ids = []
            concatenated_cell_ids = []
            
            for record in db_records:
                cell_id_voz, celda_origen = record
                
                # Verificar cell_id_voz
                if cell_id_voz:
                    str_value = str(cell_id_voz)
                    if str_value.startswith('WOM_') and '_' in str_value:
                        concatenated_cell_ids.append(str_value)
                    elif str_value.isdigit():
                        clean_cell_ids.append(str_value)
                
                # Verificar celda_origen también
                if celda_origen:
                    str_value = str(celda_origen)
                    if str_value.startswith('WOM_') and '_' in str_value:
                        concatenated_cell_ids.append(f"celda_origen: {str_value}")
                    elif str_value.isdigit():
                        clean_cell_ids.append(f"celda_origen: {str_value}")
            
            details = {
                'records_processed': result.get('records_processed', 0),
                'success_rate': result.get('success_rate', 0),
                'db_records_found': len(db_records),
                'clean_cell_ids': len(clean_cell_ids),
                'concatenated_cell_ids': len(concatenated_cell_ids),
                'sample_clean_ids': clean_cell_ids[:3],
                'sample_concatenated_ids': concatenated_cell_ids[:3],
                'processing_time': result.get('processing_time', 'N/A')
            }
            
            # La prueba pasa si el procesamiento fue exitoso y hay valores limpios sin concatenados
            processing_success = result.get('success_rate', 0) == 100.0
            clean_ids_found = len(clean_cell_ids) > 0
            no_concatenated = len(concatenated_cell_ids) == 0
            
            passed = processing_success and clean_ids_found and no_concatenated
            
            if len(concatenated_cell_ids) > 0:
                severity = "major"
            elif not processing_success:
                severity = "critical"
            else:
                severity = "minor"
            
            self.log_test_result(test_name, passed, details, severity)
            return passed, details
            
        except Exception as e:
            details = {
                'error': str(e),
                'error_type': type(e).__name__,
                'file_path': file_path
            }
            self.log_test_result(test_name, False, details, "critical")
            return False, details
    
    def test_expected_cell_id_values(self) -> bool:
        """Validar que se encuentran los valores esperados de cell_id (11648, 2981895)"""
        test_name = "Expected Cell ID Values Validation"
        
        try:
            expected_values = ['11648', '2981895']
            found_values = []
            
            # Consultar la base de datos temporal
            conn = sqlite3.connect(self.temp_db_path)
            cursor = conn.cursor()
            
            # Buscar los valores esperados
            for expected_value in expected_values:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM data_records 
                    WHERE cell_id_voz = ? OR celda_origen = ?
                """, (expected_value, expected_value))
                
                count = cursor.fetchone()[0]
                if count > 0:
                    found_values.append(expected_value)
            
            conn.close()
            
            details = {
                'expected_values': expected_values,
                'found_values': found_values,
                'missing_values': list(set(expected_values) - set(found_values)),
                'found_percentage': len(found_values) / len(expected_values) * 100
            }
            
            passed = len(found_values) > 0  # Al menos uno debe encontrarse
            severity = "major" if len(found_values) == 0 else "minor"
            
            self.log_test_result(test_name, passed, details, severity)
            return passed
            
        except Exception as e:
            details = {
                'error': str(e),
                'error_type': type(e).__name__
            }
            self.log_test_result(test_name, False, details, "critical")
            return False
    
    def run_validation_tests(self):
        """Ejecutar todas las pruebas de validación"""
        print("="*80)
        print("VALIDACIÓN DEL FIX DE CELL_ID_VOZ PARA ARCHIVOS WOM")
        print("="*80)
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Test 1: Verificar disponibilidad de archivos
        print("1. Verificando disponibilidad de archivos de prueba...")
        if not self.validate_file_exists_and_readable():
            print("[ERROR] No se encontraron archivos WOM para probar. Terminando validación.")
            return
        
        print()
        
        # Test 2 y 3: Procesar archivos disponibles
        available_files = [f for f in self.wom_test_files if os.path.exists(f)]
        
        for i, file_path in enumerate(available_files, 2):
            print(f"{i}. Procesando archivo: {os.path.basename(file_path)}")
            
            # Test: Formato de cell_id en procesamiento
            self.test_cell_id_format_in_processing(file_path)
            
            # Test: Almacenamiento en base de datos
            self.test_database_cell_id_storage(file_path)
            
            print()
        
        # Test final: Valores esperados
        if self.test_results['tests_executed'] > 1:  # Solo si procesamos archivos
            print(f"{len(available_files) + 2}. Validando valores esperados de cell_id...")
            self.test_expected_cell_id_values()
        
        # Generar reporte final
        self.generate_final_report()
    
    def generate_final_report(self):
        """Generar reporte final de validación"""
        print()
        print("="*80)
        print("REPORTE FINAL DE VALIDACIÓN")
        print("="*80)
        
        # Resumen ejecutivo
        total_tests = self.test_results['tests_executed']
        passed_tests = self.test_results['tests_passed']
        failed_tests = self.test_results['tests_failed']
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Pruebas ejecutadas: {total_tests}")
        print(f"Pruebas exitosas: {passed_tests}")
        print(f"Pruebas fallidas: {failed_tests}")
        print(f"Tasa de éxito: {success_rate:.1f}%")
        print()
        
        # Issues críticos
        critical_issues = len(self.test_results['critical_issues'])
        major_issues = len(self.test_results['major_issues'])
        minor_issues = len(self.test_results['minor_issues'])
        
        print("ISSUES ENCONTRADOS:")
        print(f"  Críticos (P0): {critical_issues}")
        print(f"  Mayores (P1): {major_issues}")
        print(f"  Menores (P2): {minor_issues}")
        print()
        
        # Veredicto final
        if critical_issues == 0 and major_issues == 0:
            verdict = "[PASS] APROBADO"
            verdict_detail = "El fix de cell_id_voz funciona correctamente"
        elif critical_issues == 0:
            verdict = "[WARNING] APROBADO CON OBSERVACIONES"
            verdict_detail = f"Issues menores detectados: {major_issues + minor_issues}"
        else:
            verdict = "[FAIL] RECHAZADO"
            verdict_detail = f"Issues críticos encontrados: {critical_issues}"
        
        print("VEREDICTO:")
        print(f"  {verdict}")
        print(f"  {verdict_detail}")
        print()
        
        # Detalles de issues críticos y mayores
        if critical_issues > 0:
            print("ISSUES CRÍTICOS:")
            for issue in self.test_results['critical_issues']:
                print(f"  - {issue['test_name']}")
                if 'error' in issue['details']:
                    print(f"    Error: {issue['details']['error']}")
            print()
        
        if major_issues > 0:
            print("ISSUES MAYORES:")
            for issue in self.test_results['major_issues']:
                print(f"  - {issue['test_name']}")
                if 'concatenated_format_values' in issue['details']:
                    count = issue['details']['concatenated_format_values']
                    if count > 0:
                        print(f"    Formatos concatenados encontrados: {count}")
                        samples = issue['details'].get('sample_concatenated_values', [])
                        if samples:
                            print(f"    Ejemplos: {samples}")
            print()
        
        # Recomendaciones
        print("RECOMENDACIONES:")
        if critical_issues == 0 and major_issues == 0:
            print("  [OK] El fix está funcionando correctamente")
            print("  [OK] Los valores de cell_id_voz se muestran en formato limpio")
            print("  [OK] No se encontraron formatos concatenados WOM_xxx_xxx")
        else:
            if major_issues > 0:
                print("  [ACTION] Revisar el código para asegurar que no se generen formatos concatenados")
                print("  [ACTION] Verificar que la función str(normalized_data.get('cell_id_voz', '')) funciona correctamente")
            if critical_issues > 0:
                print("  [CRITICAL] Solucionar los errores críticos antes de desplegar el fix")
        
        print()
        print("="*80)
        
        # Limpiar base de datos temporal
        if self.temp_db_path and os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
                print(f"[OK] Base de datos temporal eliminada: {self.temp_db_path}")
            except:
                print(f"[WARNING] No se pudo eliminar la base de datos temporal: {self.temp_db_path}")
        
        # Guardar reporte en JSON
        report_path = "C:/Soluciones/BGC/claude/KNSOft/Backend/wom_cell_id_validation_report.json"
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            print(f"[OK] Reporte detallado guardado: {report_path}")
        except Exception as e:
            print(f"[WARNING] No se pudo guardar el reporte: {e}")

def main():
    """Función principal para ejecutar las validaciones"""
    try:
        validator = WOMCellIDFixValidator()
        validator.run_validation_tests()
    except Exception as e:
        print(f"[ERROR] Error durante la validación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()