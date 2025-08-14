"""
KRONOS - Test de Robustez para Procesamiento de N Hojas TIGO
===========================================================

Este test valida que el procesador de archivos TIGO puede manejar
robustamente archivos Excel con N hojas (1, 3, 5, y archivos complejos).

Casos de prueba:
1. Archivo con 1 hoja válida
2. Archivo con 3 hojas válidas
3. Archivo con 5 hojas (2 válidas, 1 vacía, 2 con errores)
4. Archivo con N hojas mixtas (algunas válidas, otras con problemas)

Verificaciones:
- Manejo robusto de errores por hoja
- Preservación de información de origen
- Logging detallado
- Estadísticas correctas de procesamiento
- Continuación del procesamiento cuando algunas hojas fallan

Autor: Sistema KRONOS
Versión: 1.0.0
"""

import os
import sys
import time
import json
import pandas as pd
import io
from datetime import datetime
from pathlib import Path

# Configurar path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from services.file_processor_service import FileProcessorService
from database.connection import get_db_connection
from utils.operator_logger import OperatorLogger


class TigoMultiSheetRobustnessTest:
    """Test de robustez para procesamiento de múltiples hojas TIGO."""
    
    def __init__(self):
        self.test_results = {
            'test_execution_time': None,
            'test_timestamp': datetime.now().isoformat(),
            'test_cases': [],
            'summary': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'test_coverage': []
            }
        }
        
        # Configurar logging
        self.logger = OperatorLogger('TigoMultiSheetTest')
        
        # Inicializar servicio de procesamiento
        self.file_processor = FileProcessorService()
        
        # IDs para testing
        self.mission_id = 'test_mission_multisheet_' + datetime.now().strftime('%Y%m%d_%H%M%S')
        
    def create_test_excel_single_sheet(self) -> bytes:
        """Crear archivo Excel con 1 hoja válida."""
        data = {
            'TIPO_DE_LLAMADA': [20, 200, 20, 200, 20],
            'NUMERO A': ['3001234567', '3009876543', '3005551234', '3007778888', '3002223333'],
            'NUMERO MARCADO': ['3001234567', '3009876543', '3005551234', '3007778888', '3002223333'],
            'DIRECCION: O SALIENTE, I ENTRANTE': ['O', 'I', 'O', 'I', 'O'],
            'DURACION TOTAL seg': [120, 45, 300, 78, 156],
            'FECHA Y HORA ORIGEN': [
                '2024-01-15 10:30:00',
                '2024-01-15 11:45:00',
                '2024-01-15 14:20:00',
                '2024-01-15 16:05:00',
                '2024-01-15 18:30:00'
            ],
            'CELDA_ORIGEN_TRUNCADA': ['CEL001', 'CEL002', 'CEL003', 'CEL004', 'CEL005'],
            'TECH': ['4G', '3G', '4G', '4G', '3G'],
            'LATITUDE': [-4.60971, -4.61234, -4.60456, -4.61789, -4.60234],
            'LONGITUDE': [-74.08175, -74.08567, -74.07890, -74.08345, -74.07654],
            'OPERADOR': ['TIGO', 'TIGO', 'TIGO', 'TIGO', 'TIGO']
        }
        
        df = pd.DataFrame(data)
        
        # Crear Excel en memoria
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Hoja1', index=False)
        
        return buffer.getvalue()
    
    def create_test_excel_three_sheets(self) -> bytes:
        """Crear archivo Excel con 3 hojas válidas."""
        
        # Datos para hoja 1 - Llamadas matutinas
        data1 = {
            'TIPO_DE_LLAMADA': [20, 20, 200],
            'NUMERO A': ['3001111111', '3002222222', '3003333333'],
            'NUMERO MARCADO': ['3001111111', '3002222222', '3003333333'],
            'DIRECCION: O SALIENTE, I ENTRANTE': ['O', 'I', 'O'],
            'DURACION TOTAL seg': [60, 120, 90],
            'FECHA Y HORA ORIGEN': [
                '2024-01-15 08:00:00',
                '2024-01-15 09:30:00',
                '2024-01-15 10:15:00'
            ],
            'CELDA_ORIGEN_TRUNCADA': ['CEL_MAT001', 'CEL_MAT002', 'CEL_MAT003'],
            'TECH': ['4G', '4G', '3G'],
            'LATITUDE': [-4.60971, -4.61234, -4.60456],
            'LONGITUDE': [-74.08175, -74.08567, -74.07890],
            'OPERADOR': ['TIGO', 'TIGO', 'TIGO']
        }
        
        # Datos para hoja 2 - Llamadas vespertinas
        data2 = {
            'TIPO_DE_LLAMADA': [200, 20, 200, 20],
            'NUMERO A': ['3004444444', '3005555555', '3006666666', '3007777777'],
            'NUMERO MARCADO': ['3004444444', '3005555555', '3006666666', '3007777777'],
            'DIRECCION: O SALIENTE, I ENTRANTE': ['I', 'O', 'I', 'O'],
            'DURACION TOTAL seg': [180, 240, 150, 300],
            'FECHA Y HORA ORIGEN': [
                '2024-01-15 14:00:00',
                '2024-01-15 15:30:00',
                '2024-01-15 16:45:00',
                '2024-01-15 17:20:00'
            ],
            'CELDA_ORIGEN_TRUNCADA': ['CEL_VES001', 'CEL_VES002', 'CEL_VES003', 'CEL_VES004'],
            'TECH': ['4G', '4G', '4G', '3G'],
            'LATITUDE': [-4.61789, -4.60234, -4.61456, -4.60789],
            'LONGITUDE': [-74.08345, -74.07654, -74.08123, -74.07456],
            'OPERADOR': ['TIGO', 'TIGO', 'TIGO', 'TIGO']
        }
        
        # Datos para hoja 3 - Llamadas nocturnas
        data3 = {
            'TIPO_DE_LLAMADA': [20, 200],
            'NUMERO A': ['3008888888', '3009999999'],
            'NUMERO MARCADO': ['3008888888', '3009999999'],
            'DIRECCION: O SALIENTE, I ENTRANTE': ['O', 'I'],
            'DURACION TOTAL seg': [45, 78],
            'FECHA Y HORA ORIGEN': [
                '2024-01-15 20:00:00',
                '2024-01-15 22:30:00'
            ],
            'CELDA_ORIGEN_TRUNCADA': ['CEL_NOC001', 'CEL_NOC002'],
            'TECH': ['4G', '4G'],
            'LATITUDE': [-4.60123, -4.61567],
            'LONGITUDE': [-74.08789, -74.07234],
            'OPERADOR': ['TIGO', 'TIGO']
        }
        
        df1 = pd.DataFrame(data1)
        df2 = pd.DataFrame(data2)
        df3 = pd.DataFrame(data3)
        
        # Crear Excel en memoria
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df1.to_excel(writer, sheet_name='Llamadas_Matutinas', index=False)
            df2.to_excel(writer, sheet_name='Llamadas_Vespertinas', index=False)
            df3.to_excel(writer, sheet_name='Llamadas_Nocturnas', index=False)
        
        return buffer.getvalue()
    
    def create_test_excel_complex_multisheet(self) -> bytes:
        """
        Crear archivo Excel complejo con 5 hojas:
        - 2 hojas válidas con datos
        - 1 hoja vacía
        - 1 hoja con estructura incorrecta
        - 1 hoja con datos corruptos
        """
        
        # Hoja 1: Válida con llamadas salientes
        valid_data1 = {
            'TIPO_DE_LLAMADA': [20, 200, 20],
            'NUMERO A': ['3001000001', '3001000002', '3001000003'],
            'NUMERO MARCADO': ['3001000001', '3001000002', '3001000003'],
            'DIRECCION: O SALIENTE, I ENTRANTE': ['O', 'O', 'O'],
            'DURACION TOTAL seg': [120, 180, 90],
            'FECHA Y HORA ORIGEN': [
                '2024-01-15 09:00:00',
                '2024-01-15 10:00:00',
                '2024-01-15 11:00:00'
            ],
            'CELDA_ORIGEN_TRUNCADA': ['CEL_SAL001', 'CEL_SAL002', 'CEL_SAL003'],
            'TECH': ['4G', '4G', '3G'],
            'LATITUDE': [-4.60000, -4.61000, -4.62000],
            'LONGITUDE': [-74.08000, -74.09000, -74.07000],
            'OPERADOR': ['TIGO', 'TIGO', 'TIGO']
        }
        
        # Hoja 2: Válida con llamadas entrantes
        valid_data2 = {
            'TIPO_DE_LLAMADA': [200, 20],
            'NUMERO A': ['3002000001', '3002000002'],
            'NUMERO MARCADO': ['3002000001', '3002000002'],
            'DIRECCION: O SALIENTE, I ENTRANTE': ['I', 'I'],
            'DURACION TOTAL seg': [200, 150],
            'FECHA Y HORA ORIGEN': [
                '2024-01-15 15:00:00',
                '2024-01-15 16:00:00'
            ],
            'CELDA_ORIGEN_TRUNCADA': ['CEL_ENT001', 'CEL_ENT002'],
            'TECH': ['4G', '4G'],
            'LATITUDE': [-4.63000, -4.64000],
            'LONGITUDE': [-74.06000, -74.05000],
            'OPERADOR': ['TIGO', 'TIGO']
        }
        
        # Hoja 3: Vacía (solo headers)
        empty_data = pd.DataFrame(columns=[
            'TIPO_DE_LLAMADA', 'NUMERO A', 'NUMERO MARCADO', 'DIRECCION: O SALIENTE, I ENTRANTE',
            'DURACION TOTAL seg', 'FECHA Y HORA ORIGEN', 'CELDA_ORIGEN_TRUNCADA',
            'TECH', 'LATITUDE', 'LONGITUDE', 'OPERADOR'
        ])
        
        # Hoja 4: Estructura incorrecta (columnas faltantes)
        invalid_structure = {
            'CAMPO_INCORRECTO': ['valor1', 'valor2'],
            'OTRO_CAMPO': ['valor3', 'valor4']
        }
        
        # Hoja 5: Datos corruptos (tipos incorrectos)
        corrupt_data = {
            'TIPO_DE_LLAMADA': [999],  # Código inválido
            'NUMERO A': ['texto_no_numero'],
            'NUMERO MARCADO': ['otro_texto'],
            'DIRECCION: O SALIENTE, I ENTRANTE': ['X'],  # Valor inválido
            'DURACION TOTAL seg': ['texto_en_lugar_de_numero'],
            'FECHA Y HORA ORIGEN': ['fecha_invalida'],
            'CELDA_ORIGEN_TRUNCADA': ['CEL_CORRUPT'],
            'TECH': ['TECH_INVALID'],
            'LATITUDE': ['texto_coord'],
            'LONGITUDE': ['otra_coord_invalid'],
            'OPERADOR': ['TIGO']
        }
        
        df_valid1 = pd.DataFrame(valid_data1)
        df_valid2 = pd.DataFrame(valid_data2)
        df_invalid = pd.DataFrame(invalid_structure)
        df_corrupt = pd.DataFrame(corrupt_data)
        
        # Crear Excel en memoria
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_valid1.to_excel(writer, sheet_name='Valida_Salientes', index=False)
            df_valid2.to_excel(writer, sheet_name='Valida_Entrantes', index=False)
            empty_data.to_excel(writer, sheet_name='Hoja_Vacia', index=False)
            df_invalid.to_excel(writer, sheet_name='Estructura_Incorrecta', index=False)
            df_corrupt.to_excel(writer, sheet_name='Datos_Corruptos', index=False)
        
        return buffer.getvalue()
    
    def test_single_sheet_processing(self) -> dict:
        """Test procesamiento de archivo con 1 hoja."""
        test_name = "single_sheet_processing"
        self.logger.info(f"Iniciando test: {test_name}")
        
        try:
            # Crear archivo de test
            file_bytes = self.create_test_excel_single_sheet()
            file_upload_id = f"test_single_{int(time.time())}"
            
            # Procesar archivo
            result = self.file_processor.process_tigo_llamadas_unificadas(
                file_bytes, "test_single_sheet.xlsx", file_upload_id, self.mission_id
            )
            
            # Verificaciones
            assertions = []
            
            # Verificar éxito general
            assertions.append({
                'description': 'Procesamiento exitoso',
                'expected': True,
                'actual': result.get('success', False),
                'passed': result.get('success', False) == True
            })
            
            # Verificar registros procesados
            expected_records = 5  # 5 registros en el archivo de prueba
            actual_records = result.get('records_processed', 0)
            assertions.append({
                'description': 'Registros procesados correctamente',
                'expected': expected_records,
                'actual': actual_records,
                'passed': actual_records == expected_records
            })
            
            # Verificar información de hojas
            sheet_info = result.get('details', {}).get('sheet_processing_summary', {})
            if sheet_info:
                assertions.append({
                    'description': 'Total de hojas procesadas',
                    'expected': 1,
                    'actual': sheet_info.get('total_sheets', 0),
                    'passed': sheet_info.get('total_sheets', 0) == 1
                })
                
                assertions.append({
                    'description': 'Hojas exitosas',
                    'expected': 1,
                    'actual': sheet_info.get('successful_sheets', 0),
                    'passed': sheet_info.get('successful_sheets', 0) == 1
                })
            
            all_passed = all(assertion['passed'] for assertion in assertions)
            
            return {
                'test_name': test_name,
                'passed': all_passed,
                'assertions': assertions,
                'result_data': result,
                'execution_time': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Error en test {test_name}: {e}")
            return {
                'test_name': test_name,
                'passed': False,
                'error': str(e),
                'execution_time': time.time()
            }
    
    def test_three_sheets_processing(self) -> dict:
        """Test procesamiento de archivo con 3 hojas."""
        test_name = "three_sheets_processing"
        self.logger.info(f"Iniciando test: {test_name}")
        
        try:
            # Crear archivo de test
            file_bytes = self.create_test_excel_three_sheets()
            file_upload_id = f"test_three_{int(time.time())}"
            
            # Procesar archivo
            result = self.file_processor.process_tigo_llamadas_unificadas(
                file_bytes, "test_three_sheets.xlsx", file_upload_id, self.mission_id
            )
            
            # Verificaciones
            assertions = []
            
            # Verificar éxito general
            assertions.append({
                'description': 'Procesamiento exitoso',
                'expected': True,
                'actual': result.get('success', False),
                'passed': result.get('success', False) == True
            })
            
            # Verificar registros procesados (3 + 4 + 2 = 9 registros)
            expected_records = 9
            actual_records = result.get('records_processed', 0)
            assertions.append({
                'description': 'Registros procesados correctamente',
                'expected': expected_records,
                'actual': actual_records,
                'passed': actual_records == expected_records
            })
            
            # Verificar información de hojas
            sheet_info = result.get('details', {}).get('sheet_processing_summary', {})
            if sheet_info:
                assertions.append({
                    'description': 'Total de hojas procesadas',
                    'expected': 3,
                    'actual': sheet_info.get('total_sheets', 0),
                    'passed': sheet_info.get('total_sheets', 0) == 3
                })
                
                assertions.append({
                    'description': 'Hojas exitosas',
                    'expected': 3,
                    'actual': sheet_info.get('successful_sheets', 0),
                    'passed': sheet_info.get('successful_sheets', 0) == 3
                })
                
                # Verificar nombres de hojas
                expected_sheet_names = ['Llamadas_Matutinas', 'Llamadas_Vespertinas', 'Llamadas_Nocturnas']
                actual_sheet_names = sheet_info.get('successful_sheet_names', [])
                assertions.append({
                    'description': 'Nombres de hojas correctos',
                    'expected': set(expected_sheet_names),
                    'actual': set(actual_sheet_names),
                    'passed': set(actual_sheet_names) == set(expected_sheet_names)
                })
            
            all_passed = all(assertion['passed'] for assertion in assertions)
            
            return {
                'test_name': test_name,
                'passed': all_passed,
                'assertions': assertions,
                'result_data': result,
                'execution_time': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Error en test {test_name}: {e}")
            return {
                'test_name': test_name,
                'passed': False,
                'error': str(e),
                'execution_time': time.time()
            }
    
    def test_complex_multisheet_processing(self) -> dict:
        """Test procesamiento de archivo complejo con hojas mixtas."""
        test_name = "complex_multisheet_processing"
        self.logger.info(f"Iniciando test: {test_name}")
        
        try:
            # Crear archivo de test
            file_bytes = self.create_test_excel_complex_multisheet()
            file_upload_id = f"test_complex_{int(time.time())}"
            
            # Procesar archivo
            result = self.file_processor.process_tigo_llamadas_unificadas(
                file_bytes, "test_complex_multisheet.xlsx", file_upload_id, self.mission_id
            )
            
            # Verificaciones
            assertions = []
            
            # En este caso, el procesamiento debería ser exitoso parcialmente
            # Solo las hojas válidas deberían procesarse
            assertions.append({
                'description': 'Procesamiento parcialmente exitoso',
                'expected': True,
                'actual': result.get('success', False),
                'passed': result.get('success', False) == True
            })
            
            # Solo deberían procesarse registros de las 2 hojas válidas (3 + 2 = 5)
            expected_records = 5
            actual_records = result.get('records_processed', 0)
            assertions.append({
                'description': 'Solo registros válidos procesados',
                'expected': expected_records,
                'actual': actual_records,
                'passed': actual_records == expected_records
            })
            
            # Verificar información de hojas
            sheet_info = result.get('details', {}).get('sheet_processing_summary', {})
            if sheet_info:
                assertions.append({
                    'description': 'Total de hojas en archivo',
                    'expected': 5,
                    'actual': sheet_info.get('total_sheets', 0),
                    'passed': sheet_info.get('total_sheets', 0) == 5
                })
                
                assertions.append({
                    'description': 'Hojas exitosas (solo válidas)',
                    'expected': 2,
                    'actual': sheet_info.get('successful_sheets', 0),
                    'passed': sheet_info.get('successful_sheets', 0) == 2
                })
                
                assertions.append({
                    'description': 'Hojas fallidas detectadas',
                    'expected': 2,  # Estructura incorrecta y datos corruptos
                    'actual': sheet_info.get('failed_sheets', 0),
                    'passed': sheet_info.get('failed_sheets', 0) == 2
                })
                
                assertions.append({
                    'description': 'Hojas vacías detectadas',
                    'expected': 1,
                    'actual': sheet_info.get('empty_sheets', 0),
                    'passed': sheet_info.get('empty_sheets', 0) == 1
                })
                
                # Verificar que las hojas válidas fueron procesadas
                expected_valid_sheets = ['Valida_Salientes', 'Valida_Entrantes']
                actual_valid_sheets = sheet_info.get('successful_sheet_names', [])
                assertions.append({
                    'description': 'Hojas válidas identificadas correctamente',
                    'expected': set(expected_valid_sheets),
                    'actual': set(actual_valid_sheets),
                    'passed': set(actual_valid_sheets) == set(expected_valid_sheets)
                })
            
            all_passed = all(assertion['passed'] for assertion in assertions)
            
            return {
                'test_name': test_name,
                'passed': all_passed,
                'assertions': assertions,
                'result_data': result,
                'execution_time': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Error en test {test_name}: {e}")
            return {
                'test_name': test_name,
                'passed': False,
                'error': str(e),
                'execution_time': time.time()
            }
    
    def verify_source_information_preservation(self) -> dict:
        """Verificar que la información de origen se preserva correctamente."""
        test_name = "source_information_preservation"
        self.logger.info(f"Iniciando test: {test_name}")
        
        try:
            # Usar archivo de 3 hojas para verificar información de origen
            file_bytes = self.create_test_excel_three_sheets()
            file_upload_id = f"test_source_{int(time.time())}"
            
            # Procesar archivo
            result = self.file_processor.process_tigo_llamadas_unificadas(
                file_bytes, "test_source_info.xlsx", file_upload_id, self.mission_id
            )
            
            # Verificar que se procesó exitosamente
            if not result.get('success', False):
                return {
                    'test_name': test_name,
                    'passed': False,
                    'error': 'Falló el procesamiento base',
                    'execution_time': time.time()
                }
            
            # Verificar información en base de datos
            assertions = []
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Consultar registros procesados
                cursor.execute("""
                    SELECT operator_specific_data 
                    FROM operator_call_data 
                    WHERE file_upload_id = ?
                """, (file_upload_id,))
                
                records = cursor.fetchall()
                
                # Verificar que hay registros
                assertions.append({
                    'description': 'Registros encontrados en BD',
                    'expected': 9,  # 3 + 4 + 2 registros
                    'actual': len(records),
                    'passed': len(records) == 9
                })
                
                # Verificar información de origen en algunos registros
                source_sheets_found = set()
                valid_source_info_count = 0
                
                for record in records:
                    try:
                        operator_data = json.loads(record[0]) if record[0] else {}
                        
                        if 'source_sheet' in operator_data:
                            source_sheets_found.add(operator_data['source_sheet'])
                            
                            # Verificar campos de origen
                            if ('sheet_index' in operator_data and 
                                'total_sheets_in_file' in operator_data and 
                                'call_direction' in operator_data):
                                valid_source_info_count += 1
                                
                    except json.JSONDecodeError:
                        continue
                
                # Verificar hojas de origen
                expected_sheets = {'Llamadas_Matutinas', 'Llamadas_Vespertinas', 'Llamadas_Nocturnas'}
                assertions.append({
                    'description': 'Hojas de origen preservadas',
                    'expected': expected_sheets,
                    'actual': source_sheets_found,
                    'passed': source_sheets_found == expected_sheets
                })
                
                # Verificar que la mayoría de registros tienen información completa
                assertions.append({
                    'description': 'Información de origen completa',
                    'expected': True,
                    'actual': valid_source_info_count >= 8,  # Al menos 8 de 9 registros
                    'passed': valid_source_info_count >= 8
                })
            
            all_passed = all(assertion['passed'] for assertion in assertions)
            
            return {
                'test_name': test_name,
                'passed': all_passed,
                'assertions': assertions,
                'records_checked': len(records),
                'source_sheets_found': list(source_sheets_found),
                'execution_time': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Error en test {test_name}: {e}")
            return {
                'test_name': test_name,
                'passed': False,
                'error': str(e),
                'execution_time': time.time()
            }
    
    def run_all_tests(self) -> dict:
        """Ejecutar todos los tests de robustez."""
        start_time = time.time()
        
        self.logger.info("=== INICIANDO TESTS DE ROBUSTEZ MULTISHEET TIGO ===")
        
        # Ejecutar tests individuales
        test_methods = [
            self.test_single_sheet_processing,
            self.test_three_sheets_processing,
            self.test_complex_multisheet_processing,
            self.verify_source_information_preservation
        ]
        
        for test_method in test_methods:
            test_result = test_method()
            self.test_results['test_cases'].append(test_result)
            
            if test_result['passed']:
                self.test_results['summary']['passed_tests'] += 1
                self.logger.info(f"[PASS] {test_result['test_name']} PASO")
            else:
                self.test_results['summary']['failed_tests'] += 1
                self.logger.error(f"[FAIL] {test_result['test_name']} FALLO")
            
            self.test_results['summary']['total_tests'] += 1
        
        # Calcular tiempo de ejecución
        execution_time = time.time() - start_time
        self.test_results['test_execution_time'] = execution_time
        
        # Determinar cobertura de testing
        self.test_results['summary']['test_coverage'] = [
            'Procesamiento de archivo con 1 hoja',
            'Procesamiento de archivo con 3 hojas válidas',
            'Procesamiento robusto con hojas mixtas (válidas/inválidas/vacías)',
            'Preservación de información de origen por hoja',
            'Manejo de errores por hoja individual',
            'Logging detallado de estadísticas por hoja'
        ]
        
        # Log final
        success_rate = (self.test_results['summary']['passed_tests'] / 
                       self.test_results['summary']['total_tests'] * 100)
        
        self.logger.info(
            f"=== TESTS COMPLETADOS ===\n"
            f"Exito: {self.test_results['summary']['passed_tests']}/{self.test_results['summary']['total_tests']} "
            f"({success_rate:.1f}%)\n"
            f"Tiempo total: {execution_time:.2f}s"
        )
        
        return self.test_results


def main():
    """Función principal para ejecutar los tests."""
    
    # Crear y ejecutar tests
    test_suite = TigoMultiSheetRobustnessTest()
    results = test_suite.run_all_tests()
    
    # Guardar resultados
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"tigo_multisheet_robustness_test_report_{timestamp}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n=== REPORTE DE TESTS DE ROBUSTEZ MULTISHEET TIGO ===")
    print(f"Archivo de reporte: {report_file}")
    print(f"Tests ejecutados: {results['summary']['total_tests']}")
    print(f"Tests exitosos: {results['summary']['passed_tests']}")
    print(f"Tests fallidos: {results['summary']['failed_tests']}")
    print(f"Tiempo de ejecucion: {results['test_execution_time']:.2f}s")
    
    # Mostrar detalles de tests fallidos
    failed_tests = [test for test in results['test_cases'] if not test['passed']]
    if failed_tests:
        print(f"\n=== TESTS FALLIDOS ===")
        for test in failed_tests:
            print(f"- {test['test_name']}: {test.get('error', 'Ver detalles en reporte')}")
    
    return results


if __name__ == "__main__":
    main()