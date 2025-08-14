"""
KRONOS - Test de Implementación del Procesador TIGO
===============================================================================
Pruebas unitarias e integración para validar la implementación completa del
procesador TIGO incluyendo:

1. Validación de estructura de archivos
2. Procesamiento de llamadas mixtas (ENTRANTES y SALIENTES en un archivo)
3. Manejo de archivos Excel con múltiples pestañas
4. Conversión de coordenadas formato TIGO (comas como decimales)
5. Validación de campos específicos TIGO (DIRECCION: O/I)
6. Integración con base de datos unificada
===============================================================================
"""

import unittest
import os
import sys
import tempfile
import json
import pandas as pd
from datetime import datetime, date
import base64
from io import BytesIO

# Configurar path para importaciones
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.operator_processors.tigo_processor import TigoProcessor, TigoProcessorError
from services.operator_processors import get_operator_processor, is_operator_supported
from utils.validators import (
    validate_tigo_datetime_format, validate_tigo_coordinates,
    validate_tigo_direction_field, validate_tigo_llamada_record,
    ValidationError
)
from database.connection import get_database_manager
from database.operator_models import OperatorFileUpload, OperatorCallData


class TestTigoValidators(unittest.TestCase):
    """Pruebas para validadores específicos de TIGO"""
    
    def test_validate_tigo_datetime_format(self):
        """Test validación de formato fecha/hora TIGO"""
        # Casos válidos
        test_cases = [
            ("28/02/2025 01:20:19", datetime(2025, 2, 28, 1, 20, 19)),
            ("15/12/2024 23:59:59", datetime(2024, 12, 15, 23, 59, 59)),
            ("01/01/2023 00:00:00", datetime(2023, 1, 1, 0, 0, 0)),
            ("29/02/2024 12:30:45", datetime(2024, 2, 29, 12, 30, 45))  # Año bisiesto
        ]
        
        for date_str, expected in test_cases:
            with self.subTest(date_str=date_str):
                result = validate_tigo_datetime_format(date_str)
                self.assertEqual(result, expected)
        
        # Casos inválidos
        invalid_cases = [
            "",
            None,
            "2025-02-28 01:20:19",  # Formato incorrecto
            "28/13/2025 01:20:19",  # Mes inválido
            "32/01/2025 01:20:19",  # Día inválido
            "28/02/1999 01:20:19",  # Año muy antiguo
            "invalid_date"
        ]
        
        for invalid_date in invalid_cases:
            with self.subTest(invalid_date=invalid_date):
                with self.assertRaises(ValidationError):
                    validate_tigo_datetime_format(invalid_date)
    
    def test_validate_tigo_coordinates(self):
        """Test validación de coordenadas formato TIGO"""
        # Casos válidos
        test_cases = [
            ("-74,074989", "4,64958", (-74.074989, 4.64958)),
            ("-74.074989", "4.64958", (-74.074989, 4.64958)),
            ('"-74,074989"', '"4,64958"', (-74.074989, 4.64958)),  # Con comillas
            ("0,0", "0,0", (0.0, 0.0)),
            ("-74,0", "-10,0", (-74.0, -10.0))
        ]
        
        for lat_str, lon_str, expected in test_cases:
            with self.subTest(lat=lat_str, lon=lon_str):
                result = validate_tigo_coordinates(lat_str, lon_str)
                self.assertAlmostEqual(result[0], expected[0], places=6)
                self.assertAlmostEqual(result[1], expected[1], places=6)
        
        # Casos inválidos
        invalid_cases = [
            ("", ""),
            (None, None),
            ("invalid", "invalid"),
            ("91,0", "0,0"),  # Latitud fuera de rango
            ("0,0", "181,0"),  # Longitud fuera de rango
        ]
        
        for lat_str, lon_str in invalid_cases:
            with self.subTest(lat=lat_str, lon=lon_str):
                with self.assertRaises(ValidationError):
                    validate_tigo_coordinates(lat_str, lon_str)
    
    def test_validate_tigo_direction_field(self):
        """Test validación de campo dirección TIGO"""
        # Casos válidos
        test_cases = [
            ("O", "O"),
            ("I", "I"),
            ("SALIENTE", "SALIENTE"),
            ("ENTRANTE", "ENTRANTE"),
            ("o", "O"),  # Case insensitive
            ("i", "I"),
            (" O ", "O")  # Con espacios
        ]
        
        for direction, expected in test_cases:
            with self.subTest(direction=direction):
                result = validate_tigo_direction_field(direction)
                self.assertEqual(result, expected)
        
        # Casos inválidos
        invalid_cases = ["", None, "X", "OUT", "IN", "OTRO"]
        
        for invalid_direction in invalid_cases:
            with self.subTest(direction=invalid_direction):
                with self.assertRaises(ValidationError):
                    validate_tigo_direction_field(invalid_direction)
    
    def test_validate_tigo_llamada_record(self):
        """Test validación de registro completo TIGO"""
        # Registro válido
        valid_record = {
            'tipo_de_llamada': '200',
            'numero_a': '3005722406',
            'numero_marcado': 'web.colombiamovil.com.co',
            'direccion': 'O',
            'fecha_hora_origen': '28/02/2025 01:20:19',
            'duracion_total_seg': '0',
            'celda_origen_truncada': '010006CC',
            'tecnologia': '4G',
            'trcsextracodec': '10.198.50.152',
            'latitude': '4,64958',
            'longitude': '-74,074989',
            'ciudad': 'BOGOTÁ. D.C.',
            'departamento': 'CUNDINAMARCA',
            'azimuth': '350',
            'altura': '22',
            'potencia': '18,2'
        }
        
        result = validate_tigo_llamada_record(valid_record)
        
        # Verificar campos básicos
        self.assertEqual(result['tipo_de_llamada'], '200')
        self.assertEqual(result['numero_a'], '3005722406')
        self.assertEqual(result['numero_marcado'], 'web.colombiamovil.com.co')
        self.assertEqual(result['direccion'], 'O')
        self.assertIsInstance(result['fecha_hora_origen'], datetime)
        self.assertEqual(result['duracion_total_seg'], 0)
        self.assertEqual(result['celda_origen_truncada'], '010006CC')
        self.assertEqual(result['tecnologia'], '4G')
        
        # Verificar coordenadas convertidas
        self.assertAlmostEqual(result['latitud'], 4.64958, places=5)
        self.assertAlmostEqual(result['longitud'], -74.074989, places=6)
        
        # Verificar datos de antena
        self.assertAlmostEqual(result['azimuth'], 350.0, places=1)
        self.assertAlmostEqual(result['altura'], 22.0, places=1)
        self.assertAlmostEqual(result['potencia'], 18.2, places=1)


class TestTigoProcessor(unittest.TestCase):
    """Pruebas para TigoProcessor"""
    
    def setUp(self):
        """Configurar pruebas"""
        self.processor = TigoProcessor()
        
        # Datos de prueba TIGO
        self.sample_data = [
            [
                "TIPO_DE_LLAMADA", "NUMERO A", "NUMERO MARCADO", "TRCSEXTRACODEC",
                "DIRECCION: O SALIENTE, I ENTRANTE", "DURACION TOTAL seg", 
                "FECHA Y HORA ORIGEN", "CELDA_ORIGEN_TRUNCADA", "TECH", "DIRECCION",
                "CITY_DS", "DEPARTMENT_DS", "AZIMUTH", "ALTURA", "POTENCIA",
                "LONGITUDE", "LATITUDE", "TIPO_COBERTURA", "TIPO_ESTRUCTURA", 
                "OPERADOR", "CELLID_NVAL"
            ],
            [
                "200", "345901014118450", "internet.movistar.com.co", "10.198.50.152",
                "O", "0", "28/02/2025 01:20:19", "010006CC", "4G", 
                "Diagonal 61D N 26A-29", "BOGOTÁ. D.C.", "CUNDINAMARCA", "350", 
                "22", "18,2", "-74,074989", "4,64958", "6 - 1. URBANA", 
                "12 - ROOFTOP + TOWER", "TIGO", "1"
            ],
            [
                "200", "3005722406", "web.colombiamovil.com.co", "", "O", "0",
                "28/02/2025 01:09:27", "010006CC", "4G", "Diagonal 61D N 26A-29",
                "BOGOTÁ. D.C.", "CUNDINAMARCA", "350", "22", "18,2", 
                "-74,074989", "4,64958", "6 - 1. URBANA", "12 - ROOFTOP + TOWER",
                "TIGO", "1"
            ],
            [
                "200", "3042743777", "ims", "", "I", "15", "28/02/2025 01:08:16",
                "030006CC", "4G", "Diagonal 61D N 26A-29", "BOGOTÁ. D.C.",
                "CUNDINAMARCA", "260", "22", "18,2", "-74,074989", "4,64958",
                "6 - 1. URBANA", "12 - ROOFTOP + TOWER", "TIGO", "3"
            ]
        ]
    
    def test_get_supported_file_types(self):
        """Test obtención de tipos de archivo soportados"""
        supported_types = self.processor.get_supported_file_types()
        
        expected_types = {'LLAMADAS_MIXTAS': 'Llamadas entrantes y salientes en archivo único - diferenciadas por campo DIRECCION'}
        self.assertEqual(supported_types, expected_types)
    
    def test_validate_file_structure(self):
        """Test validación de estructura de archivo"""
        # Crear CSV de prueba
        df = pd.DataFrame(self.sample_data[1:], columns=self.sample_data[0])
        csv_content = df.to_csv(index=False)
        
        # Crear archivo base64
        csv_bytes = csv_content.encode('utf-8')
        csv_base64 = base64.b64encode(csv_bytes).decode('utf-8')
        
        file_data = {
            'name': 'tigo_test.csv',
            'content': f'data:text/csv;base64,{csv_base64}'
        }
        
        # Validar estructura
        result = self.processor.validate_file_structure(file_data, 'LLAMADAS_MIXTAS')
        
        # Verificar resultado
        self.assertTrue(result['is_valid'])
        self.assertEqual(result['file_type'], 'LLAMADAS_MIXTAS')
        self.assertEqual(result['operator'], 'TIGO')
        self.assertEqual(result['validation_type'], 'llamadas_mixtas_tigo')
        
        # Verificar que encontró direcciones válidas
        direccion_validation = result['direccion_validation']
        self.assertIn('O', direccion_validation['valid_directions'])
        self.assertIn('I', direccion_validation['valid_directions'])
    
    def test_validate_file_structure_excel_multiple_sheets(self):
        """Test validación de archivo Excel con múltiples pestañas"""
        # Crear Excel con múltiples pestañas
        df = pd.DataFrame(self.sample_data[1:], columns=self.sample_data[0])
        
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Hoja1', index=False)
            df.to_excel(writer, sheet_name='Hoja2', index=False)
            df.to_excel(writer, sheet_name='Hoja3', index=False)
        
        excel_bytes = excel_buffer.getvalue()
        excel_base64 = base64.b64encode(excel_bytes).decode('utf-8')
        
        file_data = {
            'name': 'tigo_test.xlsx',
            'content': f'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{excel_base64}'
        }
        
        # Validar estructura
        result = self.processor.validate_file_structure(file_data, 'LLAMADAS_MIXTAS')
        
        # Verificar resultado
        self.assertTrue(result['is_valid'])
        self.assertEqual(result['sheets_count'], 3)
        self.assertEqual(set(result['sheet_names']), {'Hoja1', 'Hoja2', 'Hoja3'})
    
    def test_normalize_column_names(self):
        """Test normalización de nombres de columnas"""
        df_test = pd.DataFrame(columns=[
            "TIPO_DE_LLAMADA", "NUMERO A", "DIRECCION: O SALIENTE, I ENTRANTE",
            "DURACION TOTAL seg", "FECHA Y HORA ORIGEN"
        ])
        
        normalized_df = self.processor._normalize_column_names(df_test, self.processor.LLAMADAS_COLUMN_MAPPING)
        
        expected_columns = {
            'tipo_de_llamada', 'numero_a', 'direccion_tipo',
            'duracion_total_seg', 'fecha_hora_origen'
        }
        self.assertEqual(set(normalized_df.columns), expected_columns)
    
    def test_clean_llamadas_dataframe(self):
        """Test limpieza de DataFrame de llamadas"""
        df_test = pd.DataFrame([
            ['3005722406', 'O', '28/02/2025 01:20:19', '010006CC', '0', '4,64958', '-74,074989'],
            [None, 'O', '28/02/2025 01:21:19', '010006CC', '5', '4,64958', '-74,074989'],  # Número None
            ['3042743777', 'I', '28/02/2025 01:22:19', '030006CC', '10.5', '4,64958', '-74,074989']
        ], columns=['numero_a', 'direccion_tipo', 'fecha_hora_origen', 'celda_origen_truncada', 
                   'duracion_total_seg', 'latitud', 'longitud'])
        
        cleaned_df = self.processor._clean_llamadas_dataframe(df_test)
        
        # Debe eliminar fila con número vacío
        self.assertEqual(len(cleaned_df), 2)
        
        # Verificar conversión de coordenadas
        self.assertEqual(cleaned_df.iloc[0]['latitud'], 4.64958)
        self.assertEqual(cleaned_df.iloc[0]['longitud'], -74.074989)
        
        # Verificar conversión de duración
        self.assertEqual(cleaned_df.iloc[0]['duracion_total_seg'], 0.0)
        self.assertEqual(cleaned_df.iloc[1]['duracion_total_seg'], 10.5)
    
    def test_extract_tigo_row_data(self):
        """Test extracción de datos específicos TIGO de una fila"""
        row_data = pd.Series({
            'numero_a': '3005722406',
            'numero_marcado': 'web.colombiamovil.com.co',
            'direccion_tipo': 'O',
            'fecha_hora_origen': '28/02/2025 01:20:19',
            'duracion_total_seg': 0,
            'celda_origen_truncada': '010006CC',
            'tecnologia': '4G',
            'latitud': 4.64958,
            'longitud': -74.074989,
            'ciudad': 'BOGOTÁ. D.C.',
            'departamento': 'CUNDINAMARCA',
            'azimuth': 350.0,
            'altura': 22.0,
            'potencia': 18.2
        })
        
        extracted_data = self.processor._extract_tigo_row_data(row_data)
        
        # Verificar campos principales
        self.assertEqual(extracted_data['numero_a'], '3005722406')
        self.assertEqual(extracted_data['numero_marcado'], 'web.colombiamovil.com.co')
        self.assertEqual(extracted_data['direccion_tipo'], 'O')
        self.assertEqual(extracted_data['celda_origen_truncada'], '010006CC')
        self.assertEqual(extracted_data['tecnologia'], '4G')
        
        # Verificar coordenadas
        self.assertEqual(extracted_data['latitud'], 4.64958)
        self.assertEqual(extracted_data['longitud'], -74.074989)
        
        # Verificar datos de antena
        self.assertEqual(extracted_data['azimuth'], 350.0)
        self.assertEqual(extracted_data['altura'], 22.0)
        self.assertEqual(extracted_data['potencia'], 18.2)


class TestTigoIntegration(unittest.TestCase):
    """Pruebas de integración para TIGO"""
    
    def test_operator_processor_registry(self):
        """Test que TIGO está registrado en el sistema"""
        # Verificar que TIGO es soportado
        self.assertTrue(is_operator_supported('TIGO'))
        
        # Verificar que se puede obtener el procesador
        processor = get_operator_processor('TIGO')
        self.assertIsNotNone(processor)
        self.assertIsInstance(processor, TigoProcessor)
        self.assertEqual(processor.operator, 'TIGO')
    
    def test_tigo_file_types_integration(self):
        """Test tipos de archivo TIGO en integración"""
        processor = get_operator_processor('TIGO')
        supported_types = processor.get_supported_file_types()
        
        self.assertIn('LLAMADAS_MIXTAS', supported_types)
        self.assertIn('Llamadas entrantes y salientes', supported_types['LLAMADAS_MIXTAS'])
    
    def test_build_tigo_specific_data(self):
        """Test construcción de datos específicos TIGO"""
        processor = TigoProcessor()
        
        row_data = pd.Series({
            'numero_a': '3005722406',
            'numero_marcado': 'web.colombiamovil.com.co',
            'fecha_hora_origen': '28/02/2025 01:20:19',
            'tecnologia': '4G',
            'ciudad': 'BOGOTÁ. D.C.',
            'departamento': 'CUNDINAMARCA'
        }, name=0)
        
        validated_row = {
            'direccion_tipo': 'O',
            'tecnologia': '4G',
            'trcsextracodec': '10.198.50.152',
            'ciudad': 'BOGOTÁ. D.C.',
            'departamento': 'CUNDINAMARCA',
            'latitud': 4.64958,
            'longitud': -74.074989,
            'azimuth': 350.0,
            'altura': 22.0,
            'potencia': 18.2,
            'tipo_cobertura': '6 - 1. URBANA',
            'tipo_estructura': '12 - ROOFTOP + TOWER'
        }
        
        specific_data_json = processor._build_tigo_specific_data(row_data, validated_row)
        specific_data = json.loads(specific_data_json)
        
        # Verificar estructura
        self.assertEqual(specific_data['operator'], 'TIGO')
        self.assertEqual(specific_data['data_type'], 'llamadas_mixtas')
        self.assertEqual(specific_data['direccion_original'], 'O')
        self.assertEqual(specific_data['tecnologia'], '4G')
        
        # Verificar ubicación
        self.assertIn('ubicacion', specific_data)
        self.assertEqual(specific_data['ubicacion']['ciudad'], 'BOGOTÁ. D.C.')
        self.assertEqual(specific_data['ubicacion']['departamento'], 'CUNDINAMARCA')
        
        # Verificar info de antena
        self.assertIn('antena_info', specific_data)
        self.assertEqual(specific_data['antena_info']['azimuth'], 350.0)
        self.assertEqual(specific_data['antena_info']['altura_metros'], 22.0)
        self.assertEqual(specific_data['antena_info']['potencia_dbm'], 18.2)


def run_tigo_tests():
    """Ejecuta todas las pruebas de TIGO"""
    # Crear suite de pruebas
    loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # Agregar pruebas de validadores
    test_suite.addTest(loader.loadTestsFromTestCase(TestTigoValidators))
    
    # Agregar pruebas de procesador
    test_suite.addTest(loader.loadTestsFromTestCase(TestTigoProcessor))
    
    # Agregar pruebas de integración
    test_suite.addTest(loader.loadTestsFromTestCase(TestTigoIntegration))
    
    # Ejecutar pruebas
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    print("="*80)
    print("KRONOS - Pruebas de Implementación TIGO")
    print("="*80)
    
    success = run_tigo_tests()
    
    print("\n" + "="*80)
    if success:
        print("TODAS LAS PRUEBAS TIGO PASARON EXITOSAMENTE")
        print("\nImplementacion TIGO COMPLETA y VALIDADA:")
        print("• TigoProcessor implementado")
        print("• Validadores especificos TIGO")
        print("• Manejo de archivos Excel multipestaƒas")
        print("• Conversion de coordenadas formato TIGO")
        print("• Validacion campo DIRECCION (O/I)")
        print("• Integracion con sistema de operadores")
    else:
        print("ALGUNAS PRUEBAS FALLARON")
        print("\nRevisar errores arriba para depuracion")
    
    print("="*80)