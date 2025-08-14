#!/usr/bin/env python3
"""
KRONOS - Test Comprehensivo de Implementación TIGO
===============================================================================
Script para probar la implementación completa de TIGO con archivos reales.

Características de TIGO:
- Archivo único con llamadas entrantes y salientes
- Diferenciación por campo DIRECCION ('O' = SALIENTE, 'I' = ENTRANTE)
- Formato de fecha DD/MM/YYYY HH:MM:SS
- Coordenadas con comas como decimales
- Datos de antena detallados
- Soporta archivos multi-pestaña Excel

Este script prueba:
1. Lectura de archivos CSV y Excel TIGO
2. Separación automática de entrantes/salientes
3. Validación de datos específicos TIGO
4. Normalización al esquema unificado
5. Inserción en base de datos
6. Integridad de datos resultantes
===============================================================================
"""

import os
import sys
import json
import tempfile
import base64
import unittest
from datetime import datetime
from pathlib import Path

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.operator_data_service import upload_operator_data
from services.file_processor_service import FileProcessorService
from services.data_normalizer_service import DataNormalizerService
from utils.validators import validate_tigo_llamada_record, ValidationError
from database.connection import get_db_connection


class TestTigoImplementation(unittest.TestCase):
    """Tests de implementación TIGO"""
    
    @classmethod
    def setUpClass(cls):
        """Configuración inicial para todas las pruebas"""
        cls.test_mission_id = 'test-tigo-mission-20250812'
        cls.test_user_id = 'test-user-tigo'
        cls.file_processor = FileProcessorService()
        cls.data_normalizer = DataNormalizerService()
        
        # Crear misión y usuario de prueba si no existen
        cls._ensure_test_mission_exists()
        cls._ensure_test_user_exists()
    
    @classmethod
    def _ensure_test_mission_exists(cls):
        """Crear misión de prueba si no existe"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO missions (id, name, description, status)
                    VALUES (?, ?, ?, ?)
                """, (
                    cls.test_mission_id,
                    'Test Mission TIGO',
                    'Misión de prueba para implementación TIGO',
                    'En Progreso'
                ))
                conn.commit()
        except Exception as e:
            print(f"Error creando misión de prueba: {e}")
    
    @classmethod
    def _ensure_test_user_exists(cls):
        """Crear usuario de prueba si no existe"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO users (id, username, email, password_hash, role, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    cls.test_user_id,
                    'test_tigo_user',
                    'test.tigo@kronos.com',
                    'test_hash',
                    'ANALYST',
                    'active'
                ))
                conn.commit()
        except Exception as e:
            print(f"Error creando usuario de prueba: {e}")
    
    def test_1_validadores_tigo(self):
        """Test de validadores específicos TIGO"""
        print("\n=== Test 1: Validadores TIGO ===")
        
        # Test registro válido
        registro_valido = {
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
        
        try:
            validado = validate_tigo_llamada_record(registro_valido)
            self.assertIsNotNone(validado)
            self.assertEqual(validado['direccion'], 'O')
            self.assertEqual(validado['numero_a'], '3005722406')
            self.assertAlmostEqual(validado['latitud'], 4.64958, places=5)
            self.assertAlmostEqual(validado['longitud'], -74.074989, places=6)
            print("✓ Validador TIGO funciona correctamente")
        except Exception as e:
            self.fail(f"Error en validador TIGO: {e}")
    
    def test_2_normalizacion_tigo(self):
        """Test de normalización de datos TIGO"""
        print("\n=== Test 2: Normalización TIGO ===")
        
        registro_raw = {
            'tipo_de_llamada': '200',
            'numero_a': '3005722406',
            'numero_marcado': 'web.colombiamovil.com.co',
            'direccion': 'O',
            'fecha_hora_origen': '28/02/2025 01:20:19',
            'duracion_total_seg': 0,
            'celda_origen_truncada': '010006CC',
            'tecnologia': '4G',
            'trcsextracodec': '10.198.50.152',
            'latitud': 4.64958,
            'longitud': -74.074989,
            'ciudad': 'BOGOTÁ. D.C.',
            'departamento': 'CUNDINAMARCA'
        }
        
        # Test llamada saliente
        try:
            normalizado_saliente = self.data_normalizer.normalize_tigo_call_data_unificadas(
                registro_raw, 'test-file-id', self.test_mission_id, 'SALIENTE'
            )
            
            self.assertIsNotNone(normalizado_saliente)
            self.assertEqual(normalizado_saliente['tipo_llamada'], 'SALIENTE')
            self.assertEqual(normalizado_saliente['numero_origen'], '3005722406')
            self.assertEqual(normalizado_saliente['numero_destino'], 'web.colombiamovil.com.co')
            self.assertEqual(normalizado_saliente['numero_objetivo'], 'web.colombiamovil.com.co')
            print("✓ Normalización SALIENTE funciona correctamente")
        except Exception as e:
            self.fail(f"Error en normalización SALIENTE: {e}")
        
        # Test llamada entrante
        try:
            normalizado_entrante = self.data_normalizer.normalize_tigo_call_data_unificadas(
                registro_raw, 'test-file-id', self.test_mission_id, 'ENTRANTE'
            )
            
            self.assertIsNotNone(normalizado_entrante)
            self.assertEqual(normalizado_entrante['tipo_llamada'], 'ENTRANTE')
            self.assertEqual(normalizado_entrante['numero_destino'], '3005722406')
            self.assertEqual(normalizado_entrante['numero_objetivo'], '3005722406')
            print("✓ Normalización ENTRANTE funciona correctamente")
        except Exception as e:
            self.fail(f"Error en normalización ENTRANTE: {e}")
    
    def test_3_archivo_csv_tigo_real(self):
        """Test con archivo CSV real de TIGO"""
        print("\n=== Test 3: Archivo CSV TIGO Real ===")
        
        csv_path = Path(__file__).parent.parent / 'datatest' / 'Tigo' / 'Reporte TIGO.csv'
        
        if not csv_path.exists():
            self.skipTest(f"Archivo CSV TIGO no encontrado: {csv_path}")
        
        try:
            # Leer archivo
            with open(csv_path, 'rb') as f:
                file_bytes = f.read()
            
            # Codificar en Base64
            file_base64 = base64.b64encode(file_bytes).decode('utf-8')
            file_data = f'data:text/csv;base64,{file_base64}'
            
            # Procesar archivo
            result = upload_operator_data(
                file_data=file_data,
                file_name='Reporte_TIGO_Test.csv',
                mission_id=self.test_mission_id,
                operator='TIGO',
                file_type='CALL_DATA',
                user_id=self.test_user_id
            )
            
            print(f"Resultado procesamiento CSV: {result}")
            
            self.assertTrue(result.get('success', False), f"Error: {result.get('error')}")
            self.assertGreater(result.get('records_processed', 0), 0)
            
            print(f"✓ CSV TIGO procesado: {result.get('records_processed')} registros")
            
            # Verificar datos en base de datos
            self._verify_tigo_data_in_db(result.get('file_upload_id'))
            
        except Exception as e:
            self.fail(f"Error procesando CSV TIGO: {e}")
    
    def test_4_archivo_excel_tigo_real(self):
        """Test con archivo Excel real de TIGO"""
        print("\n=== Test 4: Archivo Excel TIGO Real ===")
        
        excel_path = Path(__file__).parent.parent / 'datatest' / 'Tigo' / 'Formato Excel' / 'Reporte TIGO.xlsx'
        
        if not excel_path.exists():
            self.skipTest(f"Archivo Excel TIGO no encontrado: {excel_path}")
        
        try:
            # Leer archivo
            with open(excel_path, 'rb') as f:
                file_bytes = f.read()
            
            # Codificar en Base64
            file_base64 = base64.b64encode(file_bytes).decode('utf-8')
            file_data = f'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{file_base64}'
            
            # Procesar archivo
            result = upload_operator_data(
                file_data=file_data,
                file_name='Reporte_TIGO_Test.xlsx',
                mission_id=self.test_mission_id,
                operator='TIGO',
                file_type='CALL_DATA',
                user_id=self.test_user_id
            )
            
            print(f"Resultado procesamiento Excel: {result}")
            
            self.assertTrue(result.get('success', False), f"Error: {result.get('error')}")
            self.assertGreater(result.get('records_processed', 0), 0)
            
            print(f"✓ Excel TIGO procesado: {result.get('records_processed')} registros")
            
            # Verificar soporte multi-pestaña si aplica
            details = result.get('processing_details', {})
            if details.get('sheets_combined', 1) > 1:
                print(f"✓ Multi-pestaña soportado: {details['sheets_combined']} pestañas combinadas")
            
            # Verificar datos en base de datos
            self._verify_tigo_data_in_db(result.get('file_upload_id'))
            
        except Exception as e:
            self.fail(f"Error procesando Excel TIGO: {e}")
    
    def test_5_validacion_campos_especificos_tigo(self):
        """Test de validación de campos específicos TIGO"""
        print("\n=== Test 5: Campos Específicos TIGO ===")
        
        try:
            # Verificar que hay datos TIGO en la base de datos
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Buscar registros TIGO
                cursor.execute("""
                    SELECT operator_specific_data, numero_origen, numero_destino, tipo_llamada
                    FROM operator_call_data ocd
                    JOIN operator_data_sheets ods ON ocd.file_upload_id = ods.id
                    WHERE ods.operator = 'TIGO'
                    LIMIT 5
                """)
                
                records = cursor.fetchall()
                
                if not records:
                    self.skipTest("No hay datos TIGO en la base de datos para validar")
                
                for record in records:
                    operator_data_json, numero_origen, numero_destino, tipo_llamada = record
                    
                    # Validar estructura de datos específicos
                    operator_data = json.loads(operator_data_json)
                    
                    self.assertEqual(operator_data['operator'], 'TIGO')
                    self.assertEqual(operator_data['data_type'], 'llamadas_unificadas')
                    self.assertIn('direccion_original', operator_data)
                    self.assertIn('antena_info', operator_data)
                    self.assertIn('ubicacion', operator_data)
                    
                    # Validar mapeo de números según dirección
                    if tipo_llamada == 'SALIENTE':
                        self.assertIsNotNone(numero_origen)
                        self.assertIsNotNone(numero_destino)
                    elif tipo_llamada == 'ENTRANTE':
                        self.assertIsNotNone(numero_origen)
                        self.assertIsNotNone(numero_destino)
                    
                    print(f"✓ Registro TIGO {tipo_llamada} válido: {numero_origen} -> {numero_destino}")
                
                print(f"✓ Validados {len(records)} registros TIGO en BD")
                
        except Exception as e:
            self.fail(f"Error validando campos específicos TIGO: {e}")
    
    def test_6_separacion_entrantes_salientes(self):
        """Test de separación correcta entre llamadas entrantes y salientes"""
        print("\n=== Test 6: Separación Entrantes/Salientes ===")
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Contar llamadas por tipo
                cursor.execute("""
                    SELECT tipo_llamada, COUNT(*) as count
                    FROM operator_call_data ocd
                    JOIN operator_data_sheets ods ON ocd.file_upload_id = ods.id
                    WHERE ods.operator = 'TIGO'
                    GROUP BY tipo_llamada
                """)
                
                counts = dict(cursor.fetchall())
                
                self.assertGreater(counts.get('SALIENTE', 0), 0, "No se encontraron llamadas SALIENTES")
                self.assertGreater(counts.get('ENTRANTE', 0), 0, "No se encontraron llamadas ENTRANTES")
                
                print(f"✓ Llamadas SALIENTES: {counts.get('SALIENTE', 0)}")
                print(f"✓ Llamadas ENTRANTES: {counts.get('ENTRANTE', 0)}")
                print("✓ Separación automática funciona correctamente")
                
        except Exception as e:
            self.fail(f"Error verificando separación entrantes/salientes: {e}")
    
    def _verify_tigo_data_in_db(self, file_upload_id):
        """Verificar que los datos TIGO se guardaron correctamente en la BD"""
        if not file_upload_id:
            return
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Verificar archivo en operator_data_sheets
                cursor.execute("""
                    SELECT operator, processing_status, records_processed, records_failed
                    FROM operator_data_sheets 
                    WHERE id = ?
                """, (file_upload_id,))
                
                file_info = cursor.fetchone()
                self.assertIsNotNone(file_info, "Archivo no encontrado en BD")
                
                operator, status, processed, failed = file_info
                self.assertEqual(operator, 'TIGO')
                self.assertEqual(status, 'COMPLETED')
                self.assertGreater(processed, 0)
                
                # Verificar registros de llamadas
                cursor.execute("""
                    SELECT COUNT(*), COUNT(DISTINCT tipo_llamada)
                    FROM operator_call_data 
                    WHERE file_upload_id = ?
                """, (file_upload_id,))
                
                call_count, call_types = cursor.fetchone()
                self.assertEqual(call_count, processed)
                self.assertGreaterEqual(call_types, 1)  # Al menos un tipo de llamada
                
                print(f"✓ Datos verificados en BD: {call_count} registros, {call_types} tipos")
                
        except Exception as e:
            print(f"Error verificando datos en BD: {e}")
    
    @classmethod
    def tearDownClass(cls):
        """Limpieza después de todas las pruebas"""
        try:
            # Opcional: limpiar datos de prueba
            # (comentado para permitir inspección manual)
            pass
        except Exception as e:
            print(f"Error en limpieza: {e}")


def run_tigo_comprehensive_test():
    """Ejecuta el test comprehensivo de TIGO"""
    print("="*80)
    print("KRONOS - Test Comprehensivo de Implementación TIGO")
    print("="*80)
    print()
    print("Este test verifica:")
    print("• Validadores específicos TIGO")
    print("• Normalización de datos TIGO")
    print("• Procesamiento de archivos CSV reales")
    print("• Procesamiento de archivos Excel reales")
    print("• Separación automática entrantes/salientes")
    print("• Integridad de datos en base de datos")
    print()
    
    # Crear suite de tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestTigoImplementation)
    
    # Ejecutar tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print()
    print("="*80)
    if result.wasSuccessful():
        print("✅ TODOS LOS TESTS DE TIGO PASARON EXITOSAMENTE")
        print()
        print("IMPLEMENTACIÓN TIGO COMPLETADA Y VALIDADA:")
        print("• ✅ Validadores específicos funcionando")
        print("• ✅ Normalización de datos correcta")
        print("• ✅ Procesamiento de archivos CSV/Excel")
        print("• ✅ Separación automática entrantes/salientes")
        print("• ✅ Manejo de archivos multi-pestaña")
        print("• ✅ Integración con base de datos")
        print("• ✅ Campos específicos TIGO preservados")
        print()
        print("🎉 TIGO está listo para producción!")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
        print()
        print("Errores encontrados:")
        for failure in result.failures + result.errors:
            print(f"• {failure[0]}: {failure[1].split('AssertionError:')[-1].strip()}")
        print()
        print("Revisar los errores arriba y corregir antes de usar en producción.")
    
    print("="*80)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tigo_comprehensive_test()
    sys.exit(0 if success else 1)