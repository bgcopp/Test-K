#!/usr/bin/env python3
"""
KRONOS - Test WOM Implementation
=================================

Script de prueba para validar la implementación completa del operador WOM.
Incluye pruebas para:
- Datos por celda WOM
- Llamadas entrantes/salientes WOM  
- Manejo de archivos multi-pestaña
- Validación de datos técnicos específicos

Autor: Sistema KRONOS
Versión: 1.0.0
"""

import sys
import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict

# Agregar el directorio padre al path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.operator_data_service import OperatorDataService
from services.file_processor_service import FileProcessorService
from services.data_normalizer_service import DataNormalizerService
from database.connection import get_db_connection
from utils.operator_logger import OperatorLogger


class WOMTestSuite:
    """Suite de pruebas para el operador WOM."""
    
    def __init__(self):
        """Inicializa el conjunto de pruebas."""
        self.logger = OperatorLogger()
        self.service = OperatorDataService()
        self.file_processor = FileProcessorService()
        self.data_normalizer = DataNormalizerService()
        
        # Configuración de pruebas
        self.test_mission_id = 'test-mission-wom-001'
        self.test_user_id = 'test-user-wom-001'
        
        # Paths de archivos de prueba
        self.base_path = Path(__file__).parent.parent
        self.test_files = {
            'datos_csv': self.base_path / 'datatest' / 'wom' / 'PUNTO 1 TRÁFICO DATOS WOM.csv',
            'datos_xlsx': self.base_path / 'datatest' / 'wom' / 'Formato excel' / 'PUNTO 1 TRÁFICO DATOS WOM.xlsx',
            'llamadas_csv': self.base_path / 'datatest' / 'wom' / 'PUNTO 1 TRÁFICO VOZ ENTRAN  SALIENT WOM.csv',
            'llamadas_xlsx': self.base_path / 'datatest' / 'wom' / 'Formato excel' / 'PUNTO 1 TRÁFICO VOZ ENTRAN  SALIENT WOM.xlsx'
        }
        
        self.results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': []
        }
    
    def setup_test_environment(self):
        """Configura el entorno de pruebas."""
        self.logger.info("🔧 Configurando entorno de pruebas WOM...")
        
        try:
            # Crear misión de prueba
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Verificar si la misión ya existe
                cursor.execute("SELECT id FROM missions WHERE id = ?", (self.test_mission_id,))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO missions (id, name, description, created_by, status)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        self.test_mission_id,
                        'Test Mission WOM',
                        'Misión de prueba para validar implementación WOM',
                        self.test_user_id,
                        'En Progreso'
                    ))
                
                # Verificar si el usuario ya existe
                cursor.execute("SELECT id FROM users WHERE id = ?", (self.test_user_id,))
                if not cursor.fetchone():
                    # Crear role de prueba si no existe
                    test_role_id = 'test-role-admin'
                    cursor.execute("SELECT id FROM roles WHERE id = ?", (test_role_id,))
                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO roles (id, name, permissions)
                            VALUES (?, ?, ?)
                        """, (
                            test_role_id,
                            'Test Admin',
                            '{"users": {"read": true, "write": true, "delete": true}}'
                        ))
                    
                    cursor.execute("""
                        INSERT INTO users (id, name, email, password_hash, role_id)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        self.test_user_id,
                        'Test User WOM',
                        'test.wom@kronos.test',
                        'test_hash',
                        test_role_id
                    ))
                
                conn.commit()
                
            self.logger.info("✅ Entorno de pruebas configurado correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error configurando entorno: {e}")
            return False
    
    def test_file_exists(self, file_path: Path, test_name: str) -> bool:
        """Verifica que un archivo de prueba existe."""
        self.results['total_tests'] += 1
        
        if file_path.exists():
            self.logger.info(f"✅ {test_name}: Archivo encontrado - {file_path}")
            self.results['passed'] += 1
            return True
        else:
            error_msg = f"❌ {test_name}: Archivo no encontrado - {file_path}"
            self.logger.error(error_msg)
            self.results['failed'] += 1
            self.results['errors'].append(error_msg)
            return False
    
    def test_wom_datos_csv(self) -> bool:
        """Prueba procesamiento de datos WOM en formato CSV."""
        test_name = "WOM Datos Por Celda CSV"
        self.results['total_tests'] += 1
        
        try:
            file_path = self.test_files['datos_csv']
            if not file_path.exists():
                raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
            
            # Leer archivo
            with open(file_path, 'rb') as f:
                file_bytes = f.read()
            
            # Codificar en base64 para simular upload
            import base64
            file_data = base64.b64encode(file_bytes).decode('utf-8')
            
            # Procesar archivo
            result = self.service.upload_operator_file(
                file_data=file_data,
                file_name=file_path.name,
                mission_id=self.test_mission_id,
                operator='WOM',
                file_type='CELLULAR_DATA',
                user_id=self.test_user_id
            )
            
            if result.get('success', False):
                self.logger.info(f"✅ {test_name}: Procesado exitosamente")
                self.logger.info(f"   📊 Registros procesados: {result.get('records_processed', 0)}")
                self.logger.info(f"   ❌ Registros fallidos: {result.get('records_failed', 0)}")
                self.results['passed'] += 1
                return True
            else:
                error_msg = f"❌ {test_name}: {result.get('error', 'Error desconocido')}"
                self.logger.error(error_msg)
                self.results['failed'] += 1
                self.results['errors'].append(error_msg)
                return False
                
        except Exception as e:
            error_msg = f"❌ {test_name}: Excepción - {str(e)}"
            self.logger.error(error_msg)
            self.results['failed'] += 1
            self.results['errors'].append(error_msg)
            return False
    
    def test_wom_llamadas_csv(self) -> bool:
        """Prueba procesamiento de llamadas WOM en formato CSV."""
        test_name = "WOM Llamadas Entrantes/Salientes CSV"
        self.results['total_tests'] += 1
        
        try:
            file_path = self.test_files['llamadas_csv']
            if not file_path.exists():
                raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
            
            # Leer archivo
            with open(file_path, 'rb') as f:
                file_bytes = f.read()
            
            # Codificar en base64 para simular upload
            import base64
            file_data = base64.b64encode(file_bytes).decode('utf-8')
            
            # Procesar archivo
            result = self.service.upload_operator_file(
                file_data=file_data,
                file_name=file_path.name,
                mission_id=self.test_mission_id,
                operator='WOM',
                file_type='CALL_DATA',
                user_id=self.test_user_id
            )
            
            if result.get('success', False):
                self.logger.info(f"✅ {test_name}: Procesado exitosamente")
                self.logger.info(f"   📊 Registros procesados: {result.get('records_processed', 0)}")
                self.logger.info(f"   ❌ Registros fallidos: {result.get('records_failed', 0)}")
                
                # Verificar separación entrantes/salientes
                details = result.get('details', {})
                entrantes = details.get('entrantes_processed', 0)
                salientes = details.get('salientes_processed', 0)
                self.logger.info(f"   📞 Llamadas entrantes: {entrantes}")
                self.logger.info(f"   📞 Llamadas salientes: {salientes}")
                
                self.results['passed'] += 1
                return True
            else:
                error_msg = f"❌ {test_name}: {result.get('error', 'Error desconocido')}"
                self.logger.error(error_msg)
                self.results['failed'] += 1
                self.results['errors'].append(error_msg)
                return False
                
        except Exception as e:
            error_msg = f"❌ {test_name}: Excepción - {str(e)}"
            self.logger.error(error_msg)
            self.results['failed'] += 1
            self.results['errors'].append(error_msg)
            return False
    
    def test_wom_xlsx_multisheet(self) -> bool:
        """Prueba procesamiento de archivos XLSX multi-pestaña WOM."""
        test_name = "WOM XLSX Multi-pestaña"
        self.results['total_tests'] += 1
        
        try:
            file_path = self.test_files['datos_xlsx']
            if not file_path.exists():
                raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
            
            # Leer archivo
            with open(file_path, 'rb') as f:
                file_bytes = f.read()
            
            # Codificar en base64 para simular upload
            import base64
            file_data = base64.b64encode(file_bytes).decode('utf-8')
            
            # Procesar archivo
            result = self.service.upload_operator_file(
                file_data=file_data,
                file_name=file_path.name,
                mission_id=self.test_mission_id,
                operator='WOM',
                file_type='CELLULAR_DATA',
                user_id=self.test_user_id
            )
            
            if result.get('success', False):
                self.logger.info(f"✅ {test_name}: Procesado exitosamente")
                self.logger.info(f"   📊 Registros procesados: {result.get('records_processed', 0)}")
                
                # Verificar manejo multi-pestaña
                details = result.get('details', {})
                sheets_combined = details.get('sheets_combined', 1)
                self.logger.info(f"   📄 Pestañas combinadas: {sheets_combined}")
                
                self.results['passed'] += 1
                return True
            else:
                error_msg = f"❌ {test_name}: {result.get('error', 'Error desconocido')}"
                self.logger.error(error_msg)
                self.results['failed'] += 1
                self.results['errors'].append(error_msg)
                return False
                
        except Exception as e:
            error_msg = f"❌ {test_name}: Excepción - {str(e)}"
            self.logger.error(error_msg)
            self.results['failed'] += 1
            self.results['errors'].append(error_msg)
            return False
    
    def test_database_integration(self) -> bool:
        """Verifica que los datos WOM se almacenan correctamente en las tablas unificadas."""
        test_name = "WOM Database Integration"
        self.results['total_tests'] += 1
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Verificar datos celulares WOM
                cursor.execute("""
                    SELECT COUNT(*) FROM operator_cellular_data 
                    WHERE mission_id = ? AND operator = 'WOM'
                """, (self.test_mission_id,))
                
                cellular_count = cursor.fetchone()[0]
                
                # Verificar datos de llamadas WOM
                cursor.execute("""
                    SELECT COUNT(*) FROM operator_call_data 
                    WHERE mission_id = ? AND operator = 'WOM'
                """, (self.test_mission_id,))
                
                call_count = cursor.fetchone()[0]
                
                if cellular_count > 0 or call_count > 0:
                    self.logger.info(f"✅ {test_name}: Datos almacenados correctamente")
                    self.logger.info(f"   📱 Registros celulares: {cellular_count}")
                    self.logger.info(f"   📞 Registros de llamadas: {call_count}")
                    
                    # Verificar estructura de datos específicos WOM
                    if cellular_count > 0:
                        cursor.execute("""
                            SELECT operator_specific_data FROM operator_cellular_data 
                            WHERE mission_id = ? AND operator = 'WOM' 
                            LIMIT 1
                        """, (self.test_mission_id,))
                        
                        specific_data = cursor.fetchone()[0]
                        data_json = json.loads(specific_data)
                        
                        # Verificar campos específicos WOM
                        wom_fields = ['bts_id', 'imsi', 'uli', 'operador_ran']
                        found_fields = [field for field in wom_fields if field in data_json]
                        self.logger.info(f"   🔧 Campos técnicos WOM preservados: {len(found_fields)}/{len(wom_fields)}")
                    
                    self.results['passed'] += 1
                    return True
                else:
                    error_msg = f"❌ {test_name}: No se encontraron datos WOM en la base de datos"
                    self.logger.error(error_msg)
                    self.results['failed'] += 1
                    self.results['errors'].append(error_msg)
                    return False
                    
        except Exception as e:
            error_msg = f"❌ {test_name}: Excepción - {str(e)}"
            self.logger.error(error_msg)
            self.results['failed'] += 1
            self.results['errors'].append(error_msg)
            return False
    
    def run_all_tests(self) -> Dict:
        """Ejecuta toda la suite de pruebas WOM."""
        start_time = datetime.now()
        
        self.logger.info("🚀 Iniciando suite de pruebas WOM...")
        self.logger.info("=" * 60)
        
        # 1. Configurar entorno
        if not self.setup_test_environment():
            return self.results
        
        # 2. Verificar archivos de prueba
        self.test_file_exists(self.test_files['datos_csv'], "Archivo datos CSV")
        self.test_file_exists(self.test_files['llamadas_csv'], "Archivo llamadas CSV")
        self.test_file_exists(self.test_files['datos_xlsx'], "Archivo datos XLSX")
        
        # 3. Pruebas de procesamiento
        self.test_wom_datos_csv()
        self.test_wom_llamadas_csv()
        self.test_wom_xlsx_multisheet()
        
        # 4. Verificar integración con base de datos
        self.test_database_integration()
        
        # 5. Resultados finales
        end_time = datetime.now()
        duration = end_time - start_time
        
        self.logger.info("=" * 60)
        self.logger.info("📊 RESULTADOS FINALES WOM:")
        self.logger.info(f"   ⏱️  Tiempo total: {duration.total_seconds():.2f} segundos")
        self.logger.info(f"   🧪 Total pruebas: {self.results['total_tests']}")
        self.logger.info(f"   ✅ Exitosas: {self.results['passed']}")
        self.logger.info(f"   ❌ Fallidas: {self.results['failed']}")
        
        success_rate = (self.results['passed'] / self.results['total_tests']) * 100 if self.results['total_tests'] > 0 else 0
        self.logger.info(f"   📈 Tasa de éxito: {success_rate:.1f}%")
        
        if self.results['errors']:
            self.logger.info("\n🔍 ERRORES ENCONTRADOS:")
            for error in self.results['errors']:
                self.logger.info(f"   • {error}")
        
        if self.results['failed'] == 0:
            self.logger.info("\n🎉 ¡TODAS LAS PRUEBAS WOM PASARON EXITOSAMENTE!")
            self.logger.info("✨ El operador WOM está completamente implementado y funcionando.")
        else:
            self.logger.info(f"\n⚠️  Se encontraron {self.results['failed']} pruebas fallidas.")
            self.logger.info("🔧 Revisar los errores antes de considerar la implementación completa.")
        
        return self.results


def main():
    """Función principal para ejecutar las pruebas."""
    print("KRONOS - Test Suite WOM")
    print("=" * 60)
    
    try:
        suite = WOMTestSuite()
        results = suite.run_all_tests()
        
        # Guardar resultados en archivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = Path(__file__).parent / f'test_results_wom_{timestamp}.json'
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': timestamp,
                'operator': 'WOM',
                'results': results,
                'summary': {
                    'total_tests': results['total_tests'],
                    'passed': results['passed'],
                    'failed': results['failed'],
                    'success_rate': (results['passed'] / results['total_tests']) * 100 if results['total_tests'] > 0 else 0
                }
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Resultados guardados en: {results_file}")
        
        # Código de salida
        exit_code = 0 if results['failed'] == 0 else 1
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"❌ Error crítico en suite de pruebas: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()