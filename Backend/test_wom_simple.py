"""
KRONOS WOM Simple Implementation Tests
===============================================================================
Suite simplificada de pruebas para el operador WOM enfocada en funcionalidades
core sin dependencias complejas de base de datos.
===============================================================================
"""

import os
import sys
import unittest
import json
import base64
from datetime import datetime
from io import BytesIO

# Agregar el directorio Backend al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar después de configurar el path
from services.operator_processors.wom_processor import WomProcessor, WomProcessorError
import pandas as pd


class TestWomProcessorCore(unittest.TestCase):
    """Tests core del procesador WOM sin BD"""
    
    def setUp(self):
        """Setup antes de cada prueba"""
        self.processor = WomProcessor()
    
    def test_supported_file_types(self):
        """Test de tipos de archivo soportados por WOM"""
        supported_types = self.processor.get_supported_file_types()
        
        self.assertIn('DATOS_POR_CELDA', supported_types)
        self.assertIn('LLAMADAS_ENTRANTES', supported_types)
        
        # Verificar descripciones
        self.assertIn('navegación móvil', supported_types['DATOS_POR_CELDA'].lower())
        self.assertIn('llamadas', supported_types['LLAMADAS_ENTRANTES'].lower())
        self.assertIn('sentido', supported_types['LLAMADAS_ENTRANTES'].lower())
    
    def test_validate_datos_file_structure_valid(self):
        """Test validación de estructura válida para datos por celda WOM"""
        # Crear datos de prueba simulando archivo WOM datos
        data = {
            'OPERADOR_TECNOLOGIA': ['WOM 4G', 'WOM 3G'],
            'BTS_ID': [11648, 1648],
            'TAC': [2717, 3717],
            'CELL_ID_VOZ': [2981895, 11648],
            'SECTOR': [7, 1],
            'FECHA_HORA_INICIO': ['18/04/2024 10:05', '18/04/2024 12:32'],
            'FECHA_HORA_FIN': ['18/04/2024 15:57', '18/04/2024 14:01'],
            'OPERADOR_RAN': ['WOM', 'WOM'],
            'NUMERO_ORIGEN': ['3236997579', '3132047972'],
            'DURACION_SEG': [21150, 5349],
            'UP_DATA_BYTES': [1777, 5053414],
            'DOWN_DATA_BYTES': [6673, 60373650],
            'IMSI': ['732360130234793', '732360044688911'],
            'LOCALIZACION_USUARIO': ['823702630a9d370263002d8007', '013702630e852d80'],
            'NOMBRE_ANTENA': ['BTA Ciudad Bachue I', 'BTA Ciudad Bachue I 3G'],
            'DIRECCION': ['Cr 95 G 86 B 21', 'Cr 95 G 86 B 21'],
            'LATITUD': ['4,71576', '4,71576'],
            'LONGITUD': ['-74,10501', '-74,10501'],
            'LOCALIDAD': ['Engativa', 'Engativa'],
            'CIUDAD': ['Bogota', 'Bogota'],
            'DEPARTAMENTO': ['Cundinamarca', 'Cundinamarca'],
            'REGIONAL': ['Center', 'Centro'],
            'ENTORNO_GEOGRAFICO': ['Urbano', 'Urbano (Inside municipal head)'],
            'ULI': ['73236027172981895', '732360371711648']
        }
        
        # Crear CSV en memoria
        df = pd.DataFrame(data)
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=False)
        csv_bytes = csv_buffer.getvalue()
        
        # Codificar en base64
        encoded_content = base64.b64encode(csv_bytes).decode('utf-8')
        file_data = {
            'name': 'test_wom_datos.csv',
            'content': f'data:text/csv;base64,{encoded_content}'
        }
        
        # Validar estructura
        result = self.processor.validate_file_structure(file_data, 'DATOS_POR_CELDA')
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(result['validation_type'], 'datos_por_celda_wom')
        self.assertEqual(result['operator'], 'WOM')
        self.assertIn('numero_origen', result['mapped_columns'])
        self.assertIn('up_data_bytes', result['mapped_columns'])
        self.assertIn('down_data_bytes', result['mapped_columns'])
        
        # Verificar validación de tecnologías
        tech_validation = result.get('technology_validation', {})
        self.assertIn('WOM 4G', tech_validation.get('valid_technologies', []))
        self.assertIn('WOM 3G', tech_validation.get('valid_technologies', []))
    
    def test_validate_llamadas_file_structure_valid(self):
        """Test validación de estructura válida para llamadas entrantes WOM"""
        # Crear datos de prueba simulando archivo WOM llamadas
        data = {
            'OPERADOR_TECNOLOGIA': ['WOM 3G', 'WOM 4G'],
            'BTS_ID': [1648, 11648],
            'TAC': [3717, 2717],
            'CELL_ID_VOZ': [11648, 2981895],
            'SECTOR': [1, 7],
            'NUMERO_ORIGEN': ['3025197022', '3213525987'],
            'NUMERO_DESTINO': ['3224139744', '3433209628101'],
            'FECHA_HORA_INICIO': ['18/04/2024 10:26', '18/04/2024 10:06'],
            'FECHA_HORA_FIN': ['18/04/2024 10:27', '18/04/2024 10:07'],
            'DURACION_SEG': [13, 49],
            'OPERADOR_RAN_ORIGEN': ['WOM', 'WOM'],
            'USER_LOCATION_INFO': ['013702630e852d80', '8237026302d80070'],
            'ACCESS_NETWORK_INFORMATION': ['3GPP-UTRAN-FDD;utran-sai-3gpp=7323600E852D80', '3GPP-E-UTRAN-FDD;utran-cell-id-3gpp=7323600A9D02D8007'],
            'IMEI': ['869123066856750', '3536714e+14'],
            'IMSI': ['', ''],
            'NOMBRE_ANTENA': ['BTA Ciudad Bachue I 3G', 'BTA Ciudad Bachue I'],
            'DIRECCION': ['Cr 95 G 86 B 21', 'Cr 95 G 86 B 21'],
            'LATITUD': ['4,71576', '4,71576'],
            'LONGITUD': ['-74,10501', '-74,10501'],
            'LOCALIDAD': ['Engativa', 'Engativa'],
            'CIUDAD': ['Bogota', 'Bogota'],
            'DEPARTAMENTO': ['Cundinamarca', 'Cundinamarca'],
            'SENTIDO': ['SALIENTE', 'ENTRANTE']
        }
        
        # Crear CSV en memoria
        df = pd.DataFrame(data)
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=False)
        csv_bytes = csv_buffer.getvalue()
        
        # Codificar en base64
        encoded_content = base64.b64encode(csv_bytes).decode('utf-8')
        file_data = {
            'name': 'test_wom_llamadas.csv',
            'content': f'data:text/csv;base64,{encoded_content}'
        }
        
        # Validar estructura
        result = self.processor.validate_file_structure(file_data, 'LLAMADAS_ENTRANTES')
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(result['validation_type'], 'llamadas_entrantes_wom')
        self.assertEqual(result['operator'], 'WOM')
        self.assertIn('numero_origen', result['mapped_columns'])
        self.assertIn('numero_destino', result['mapped_columns'])
        self.assertIn('sentido', result['mapped_columns'])
        
        # Verificar validación de SENTIDO
        sentido_validation = result.get('sentido_validation', {})
        self.assertIn('SALIENTE', sentido_validation.get('valid_directions', []))
        self.assertIn('ENTRANTE', sentido_validation.get('valid_directions', []))
    
    def test_wom_datetime_format_validation(self):
        """Test validación de formatos de fecha específicos de WOM"""
        # Test DD/MM/YYYY HH:MM:SS
        dt1 = self.processor._validate_wom_datetime_format('18/04/2024 10:26:57', 'test_field')
        self.assertEqual(dt1.year, 2024)
        self.assertEqual(dt1.month, 4)
        self.assertEqual(dt1.day, 18)
        self.assertEqual(dt1.hour, 10)
        self.assertEqual(dt1.minute, 26)
        self.assertEqual(dt1.second, 57)
        
        # Test DD/MM/YYYY HH:MM
        dt2 = self.processor._validate_wom_datetime_format('18/04/2024 10:26', 'test_field')
        self.assertEqual(dt2.year, 2024)
        self.assertEqual(dt2.month, 4)
        self.assertEqual(dt2.day, 18)
        self.assertEqual(dt2.hour, 10)
        self.assertEqual(dt2.minute, 26)
        self.assertEqual(dt2.second, 0)
        
        # Test YYYY-MM-DD HH:MM:SS
        dt3 = self.processor._validate_wom_datetime_format('2024-04-18 10:26:57', 'test_field')
        self.assertEqual(dt3.year, 2024)
        self.assertEqual(dt3.month, 4)
        self.assertEqual(dt3.day, 18)
        
        # Test formato inválido
        with self.assertRaises(Exception):
            self.processor._validate_wom_datetime_format('invalid-date', 'test_field')
    
    def test_coordinate_conversion_wom_format(self):
        """Test conversión de coordenadas con formato WOM (comas como decimales)"""
        # Simular datos de fila con coordenadas WOM y campos requeridos
        test_record = {
            'numero_origen': '3236997579',
            'fecha_hora_inicio': '18/04/2024 10:05',
            'duracion_seg': 21150,
            'cell_id_voz': 2981895,
            'latitud': '4,71576',
            'longitud': '-74,10501'
        }
        
        validated = self.processor._validate_wom_datos_record(test_record)
        
        # Verificar conversión correcta
        self.assertAlmostEqual(validated.get('latitud', 0), 4.71576, places=5)
        self.assertAlmostEqual(validated.get('longitud', 0), -74.10501, places=5)
    
    def test_llamadas_record_validation(self):
        """Test validación completa de registro de llamada WOM"""
        test_record = {
            'numero_origen': '3025197022',
            'numero_destino': '3224139744',
            'fecha_hora_inicio': '18/04/2024 10:26:57',
            'duracion_seg': 13,
            'cell_id_voz': 11648,
            'sentido': 'SALIENTE',
            'operador_tecnologia': 'WOM 3G',
            'latitud': '4,71576',
            'longitud': '-74,10501',
            'imei': '869123066856750'
        }
        
        validated = self.processor._validate_wom_llamadas_record(test_record)
        
        self.assertEqual(validated['numero_origen'], '3025197022')
        self.assertEqual(validated['numero_destino'], '3224139744')
        self.assertEqual(validated['sentido'], 'SALIENTE')
        self.assertAlmostEqual(validated['latitud'], 4.71576, places=5)
        self.assertAlmostEqual(validated['longitud'], -74.10501, places=5)
        self.assertEqual(validated['operador_tecnologia'], 'WOM 3G')
    
    def test_datos_record_validation(self):
        """Test validación completa de registro de datos por celda WOM"""
        test_record = {
            'numero_origen': '3236997579',
            'fecha_hora_inicio': '18/04/2024 10:05:03',
            'fecha_hora_fin': '18/04/2024 15:57:33',
            'duracion_seg': 21150,
            'cell_id_voz': 2981895,
            'up_data_bytes': 1777,
            'down_data_bytes': 6673,
            'operador_tecnologia': 'WOM 4G',
            'latitud': '4,71576',
            'longitud': '-74,10501',
            'imsi': '732360130234793'
        }
        
        validated = self.processor._validate_wom_datos_record(test_record)
        
        self.assertEqual(validated['numero_origen'], '3236997579')
        self.assertEqual(validated['operador_tecnologia'], 'WOM 4G')
        self.assertEqual(validated['up_data_bytes'], 1777)
        self.assertEqual(validated['down_data_bytes'], 6673)
        self.assertEqual(validated['duracion_seg'], 21150)
        self.assertAlmostEqual(validated['latitud'], 4.71576, places=5)
        self.assertAlmostEqual(validated['longitud'], -74.10501, places=5)
        self.assertIsNotNone(validated['fecha_hora_inicio'])
        self.assertIsNotNone(validated['fecha_hora_fin'])
    
    def test_excel_consolidation_simulation(self):
        """Test simulación de consolidación de múltiples pestañas Excel WOM"""
        # Simular datos de dos "pestañas"
        sheet1_data = pd.DataFrame({
            'OPERADOR_TECNOLOGIA': ['WOM 4G'],
            'NUMERO_ORIGEN': ['3236997579'],
            'CELL_ID_VOZ': [2981895],
            'FECHA_HORA_INICIO': ['18/04/2024 10:05'],
            'DURACION_SEG': [21150],
            'UP_DATA_BYTES': [1777],
            'DOWN_DATA_BYTES': [6673],
            'LATITUD': ['4,71576'],
            'LONGITUD': ['-74,10501']
        })
        
        sheet2_data = pd.DataFrame({
            'OPERADOR_TECNOLOGIA': ['WOM 3G'],
            'NUMERO_ORIGEN': ['3132047972'],
            'CELL_ID_VOZ': [11648],
            'FECHA_HORA_INICIO': ['18/04/2024 12:32'],
            'DURACION_SEG': [5349],
            'UP_DATA_BYTES': [5053414],
            'DOWN_DATA_BYTES': [60373650],
            'LATITUD': ['4,71576'],
            'LONGITUD': ['-74,10501']
        })
        
        # Simular consolidación (como lo hace el procesador real)
        consolidated = pd.concat([sheet1_data, sheet2_data], ignore_index=True)
        
        self.assertEqual(len(consolidated), 2)
        self.assertIn('WOM 4G', consolidated['OPERADOR_TECNOLOGIA'].values)
        self.assertIn('WOM 3G', consolidated['OPERADOR_TECNOLOGIA'].values)
        self.assertEqual(len(consolidated['NUMERO_ORIGEN'].unique()), 2)
        
        # Verificar que las coordenadas están en formato WOM (con comas)
        self.assertIn('4,71576', consolidated['LATITUD'].values)
        self.assertIn('-74,10501', consolidated['LONGITUD'].values)
    
    def test_build_wom_specific_data(self):
        """Test construcción de datos específicos WOM en formato JSON"""
        # Simular fila de datos
        test_row = pd.Series({
            'operador_tecnologia': 'WOM 4G',
            'numero_origen': '3236997579',
            'fecha_hora_inicio': '18/04/2024 10:05',
            'imsi': '732360130234793',
            'nombre_antena': 'BTA Ciudad Bachue I'
        })
        test_row.name = 0  # Simular índice de fila
        
        # Simular datos validados
        validated_data = {
            'operador_tecnologia': 'WOM 4G',
            'imsi': '732360130234793',
            'nombre_antena': 'BTA Ciudad Bachue I',
            'ciudad': 'Bogota',
            'latitud': 4.71576,
            'longitud': -74.10501
        }
        
        # Generar datos específicos para datos por celda
        specific_json = self.processor._build_wom_datos_specific_data(test_row, validated_data)
        specific_data = json.loads(specific_json)
        
        self.assertEqual(specific_data['operator'], 'WOM')
        self.assertEqual(specific_data['data_type'], 'datos_por_celda')
        self.assertEqual(specific_data['tecnologia'], 'WOM 4G')
        self.assertIn('technical_info', specific_data)
        self.assertIn('ubicacion', specific_data)
        self.assertIn('session_info', specific_data)
        
        # Verificar información técnica
        tech_info = specific_data['technical_info']
        self.assertEqual(tech_info['imsi'], '732360130234793')
        
        # Verificar ubicación
        ubicacion = specific_data['ubicacion']
        self.assertEqual(ubicacion['nombre_antena'], 'BTA Ciudad Bachue I')
        self.assertEqual(ubicacion['ciudad'], 'Bogota')
        
        coordenadas = ubicacion['coordenadas']
        self.assertEqual(coordenadas['latitud'], 4.71576)
        self.assertEqual(coordenadas['longitud'], -74.10501)
    
    def test_column_mapping_datos(self):
        """Test mapeo de columnas para datos por celda WOM"""
        # Crear DataFrame con columnas originales WOM
        original_df = pd.DataFrame({
            'OPERADOR_TECNOLOGIA': ['WOM 4G'],
            'NUMERO_ORIGEN': ['3236997579'],
            'UP_DATA_BYTES': [1777],
            'DOWN_DATA_BYTES': [6673],
            'LATITUD': ['4,71576'],
            'LONGITUD': ['-74,10501']
        })
        
        # Aplicar mapeo
        mapped_df = self.processor._normalize_column_names(original_df, self.processor.DATOS_COLUMN_MAPPING)
        
        # Verificar mapeo correcto
        self.assertIn('operador_tecnologia', mapped_df.columns)
        self.assertIn('numero_origen', mapped_df.columns)
        self.assertIn('up_data_bytes', mapped_df.columns)
        self.assertIn('down_data_bytes', mapped_df.columns)
        self.assertIn('latitud', mapped_df.columns)
        self.assertIn('longitud', mapped_df.columns)
        
        # Verificar que los datos se preservaron
        self.assertEqual(mapped_df['operador_tecnologia'].iloc[0], 'WOM 4G')
        self.assertEqual(mapped_df['numero_origen'].iloc[0], '3236997579')
        self.assertEqual(mapped_df['latitud'].iloc[0], '4,71576')
    
    def test_column_mapping_llamadas(self):
        """Test mapeo de columnas para llamadas WOM"""
        # Crear DataFrame con columnas originales WOM
        original_df = pd.DataFrame({
            'NUMERO_ORIGEN': ['3025197022'],
            'NUMERO_DESTINO': ['3224139744'],
            'SENTIDO': ['SALIENTE'],
            'OPERADOR_TECNOLOGIA': ['WOM 3G'],
            'IMEI': ['869123066856750']
        })
        
        # Aplicar mapeo
        mapped_df = self.processor._normalize_column_names(original_df, self.processor.LLAMADAS_COLUMN_MAPPING)
        
        # Verificar mapeo correcto
        self.assertIn('numero_origen', mapped_df.columns)
        self.assertIn('numero_destino', mapped_df.columns)
        self.assertIn('sentido', mapped_df.columns)
        self.assertIn('operador_tecnologia', mapped_df.columns)
        self.assertIn('imei', mapped_df.columns)
        
        # Verificar que los datos se preservaron
        self.assertEqual(mapped_df['numero_origen'].iloc[0], '3025197022')
        self.assertEqual(mapped_df['sentido'].iloc[0], 'SALIENTE')


def run_wom_simple_tests():
    """Ejecuta las pruebas simplificadas de WOM"""
    print("=== EJECUTANDO PRUEBAS SIMPLIFICADAS WOM ===")
    
    # Configurar logging para tests
    import logging
    logging.basicConfig(level=logging.WARNING)  # Reducir verbosidad durante tests
    
    # Crear suite de tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Agregar tests
    suite.addTests(loader.loadTestsFromTestCase(TestWomProcessorCore))
    
    # Ejecutar tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Resumen
    print(f"\n=== RESUMEN PRUEBAS SIMPLIFICADAS WOM ===")
    print(f"Pruebas ejecutadas: {result.testsRun}")
    print(f"Errores: {len(result.errors)}")
    print(f"Fallos: {len(result.failures)}")
    
    if result.errors:
        print("\nERRORES:")
        for test, error in result.errors:
            print(f"  - {test}: {error}")
    
    if result.failures:
        print("\nFALLOS:")
        for test, failure in result.failures:
            print(f"  - {test}: {failure}")
    
    success = len(result.errors) == 0 and len(result.failures) == 0
    print(f"\nResultado: {'✓ ÉXITO' if success else '✗ FALLOS DETECTADOS'}")
    
    return success


if __name__ == '__main__':
    success = run_wom_simple_tests()
    sys.exit(0 if success else 1)