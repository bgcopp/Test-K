#!/usr/bin/env python3
"""
KRONOS - Testing Integral Simplificado del Operador CLARO
=========================================================

Testing integral de todas las funcionalidades CLARO sin caracteres especiales.
"""

import os
import sys
import time
import json
import traceback
import psutil
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import sqlite3

# Agregar el directorio del backend al path
backend_dir = Path(__file__).parent / "Backend"
sys.path.insert(0, str(backend_dir))

from database.connection import get_db_connection
from services.operator_data_service import upload_operator_data, get_operator_statistics

class ClaroTester:
    def __init__(self):
        self.test_results = {
            'start_time': datetime.now().isoformat(),
            'tests': {},
            'critical_issues': [],
            'major_issues': [],
            'minor_issues': []
        }
        
        self.test_mission_id = "m1"  # Use existing mission
        self.test_user_id = "admin"  # Use existing admin user
        
        self.test_files = {
            'DATOS_XLSX': 'datatest/Claro/formato excel/DATOS_POR_CELDA CLARO.xlsx',
            'ENTRANTES_CSV': 'datatest/Claro/LLAMADAS_ENTRANTES_POR_CELDA CLARO.csv',
            'SALIENTES_CSV': 'datatest/Claro/LLAMADAS_SALIENTES_POR_CELDA CLARO.csv',
            'ENTRANTES_XLSX': 'datatest/Claro/formato excel/LLAMADAS_ENTRANTES_POR_CELDA CLARO.xlsx',
            'SALIENTES_XLSX': 'datatest/Claro/formato excel/LLAMADAS_SALIENTES_POR_CELDA CLARO.xlsx'
        }
    
    def setup_test_environment(self) -> bool:
        try:
            # Using existing mission and user, just verify they exist
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT id FROM missions WHERE id = ?", (self.test_mission_id,))
                if not cursor.fetchone():
                    self.test_results['critical_issues'].append(f"Mission {self.test_mission_id} not found")
                    return False
                
                cursor.execute("SELECT id FROM users WHERE id = ?", (self.test_user_id,))
                if not cursor.fetchone():
                    self.test_results['critical_issues'].append(f"User {self.test_user_id} not found")
                    return False
            
            print("Entorno de testing verificado correctamente")
            return True
            
        except Exception as e:
            self.test_results['critical_issues'].append(f"Error verificando entorno: {str(e)}")
            print(f"Error verificando entorno: {e}")
            return False
    
    def encode_file_to_base64(self, file_path: str) -> Optional[str]:
        try:
            with open(file_path, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            print(f"Error codificando archivo {file_path}: {e}")
            return None
    
    def test_file_upload(self, file_path: str, file_type: str, test_name: str) -> Dict[str, Any]:
        print(f"\nTesting {test_name}: {file_path}")
        
        if not os.path.exists(file_path):
            return {
                'test_name': test_name,
                'success': False,
                'error': f'Archivo no encontrado: {file_path}',
                'duration': 0
            }
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        start_time = time.time()
        
        try:
            file_data = self.encode_file_to_base64(file_path)
            if not file_data:
                return {
                    'test_name': test_name,
                    'success': False,
                    'error': 'Error codificando archivo a Base64',
                    'duration': time.time() - start_time
                }
            
            result = upload_operator_data(
                file_data=file_data,
                file_name=os.path.basename(file_path),
                mission_id=self.test_mission_id,
                operator='CLARO',
                file_type=file_type,
                user_id=self.test_user_id
            )
            
            end_time = time.time()
            final_memory = process.memory_info().rss / 1024 / 1024
            duration = end_time - start_time
            memory_usage = final_memory - initial_memory
            
            test_result = {
                'test_name': test_name,
                'success': result.get('success', False),
                'duration': duration,
                'memory_usage': memory_usage,
                'file_size_mb': os.path.getsize(file_path) / 1024 / 1024,
                'records_processed': result.get('records_processed', 0),
                'records_failed': result.get('records_failed', 0),
                'file_upload_id': result.get('file_upload_id'),
                'response': result
            }
            
            print(f"   Duracion: {duration:.2f}s")
            print(f"   Memoria: {memory_usage:.2f}MB")
            print(f"   Registros: {result.get('records_processed', 0)} procesados, {result.get('records_failed', 0)} fallidos")
            
            if result.get('success', False):
                print(f"   SUCCESS: {test_name}")
            else:
                print(f"   FAILED: {test_name} - {result.get('error', 'Unknown error')}")
                if 'CRITICAL' in str(result.get('error', '')):
                    self.test_results['critical_issues'].append(f"{test_name}: {result.get('error')}")
                else:
                    self.test_results['major_issues'].append(f"{test_name}: {result.get('error')}")
            
            return test_result
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Excepcion durante testing: {str(e)}"
            
            self.test_results['critical_issues'].append(f"{test_name}: {error_msg}")
            print(f"   EXCEPTION: {test_name} - {error_msg}")
            
            return {
                'test_name': test_name,
                'success': False,
                'error': error_msg,
                'duration': duration,
                'exception': str(e)
            }
    
    def run_tests(self) -> Dict[str, Any]:
        print("KRONOS - Testing Integral del Operador CLARO")
        print("Iniciado:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("=" * 60)
        
        if not self.setup_test_environment():
            return self.test_results
        
        print("\nFASE 1: Testing de Documentos CLARO")
        print("-" * 40)
        
        # Test all file types and formats
        test_configs = [
            ('DATOS_XLSX', 'CELLULAR_DATA', 'DATOS_POR_CELDA_XLSX'),
            ('ENTRANTES_CSV', 'CALL_DATA', 'LLAMADAS_ENTRANTES_CSV'),
            ('SALIENTES_CSV', 'CALL_DATA', 'LLAMADAS_SALIENTES_CSV'),
            ('ENTRANTES_XLSX', 'CALL_DATA', 'LLAMADAS_ENTRANTES_XLSX'),
            ('SALIENTES_XLSX', 'CALL_DATA', 'LLAMADAS_SALIENTES_XLSX')
        ]
        
        for file_key, file_type, test_name in test_configs:
            if os.path.exists(self.test_files[file_key]):
                result = self.test_file_upload(
                    self.test_files[file_key],
                    file_type,
                    test_name
                )
                self.test_results['tests'][test_name] = result
            else:
                print(f"   Archivo no encontrado: {self.test_files[file_key]}")
                self.test_results['minor_issues'].append(f"Archivo no encontrado: {self.test_files[file_key]}")
        
        print("\nFASE 2: Verificacion de Integridad de Datos")
        print("-" * 40)
        self.verify_data_integrity()
        
        print("\nFASE 3: Estadisticas del Sistema")
        print("-" * 40)
        try:
            system_stats = get_operator_statistics()
            self.test_results['system_statistics'] = system_stats
            print(f"Estadisticas obtenidas: {system_stats.get('success', False)}")
        except Exception as e:
            print(f"Error obteniendo estadisticas: {e}")
            self.test_results['major_issues'].append(f"Error en estadisticas: {str(e)}")
        
        self.test_results['end_time'] = datetime.now().isoformat()
        self.generate_summary()
        
        return self.test_results
    
    def verify_data_integrity(self):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Verificar datos celulares
                cursor.execute("""
                    SELECT COUNT(*) FROM operator_cellular_data 
                    WHERE file_upload_id IN (
                        SELECT id FROM operator_data_sheets 
                        WHERE operator = 'CLARO' AND file_type = 'CELLULAR_DATA'
                    )
                """)
                cellular_count = cursor.fetchone()[0]
                print(f"   Registros de datos celulares: {cellular_count}")
                
                # Verificar datos de llamadas
                cursor.execute("""
                    SELECT COUNT(*) FROM operator_call_data 
                    WHERE file_upload_id IN (
                        SELECT id FROM operator_data_sheets 
                        WHERE operator = 'CLARO' AND file_type = 'CALL_DATA'
                    )
                """)
                call_count = cursor.fetchone()[0]
                print(f"   Registros de llamadas: {call_count}")
                
                # Verificar tipos de llamadas
                cursor.execute("""
                    SELECT tipo_llamada, COUNT(*) FROM operator_call_data 
                    WHERE file_upload_id IN (
                        SELECT id FROM operator_data_sheets 
                        WHERE operator = 'CLARO' AND file_type = 'CALL_DATA'
                    )
                    GROUP BY tipo_llamada
                """)
                call_types = cursor.fetchall()
                for call_type, count in call_types:
                    print(f"   Llamadas {call_type}: {count}")
                
        except Exception as e:
            print(f"Error verificando integridad: {e}")
            self.test_results['major_issues'].append(f"Error verificando integridad: {str(e)}")
    
    def generate_summary(self):
        total_tests = len(self.test_results['tests'])
        successful_tests = sum(1 for test in self.test_results['tests'].values() if test.get('success', False))
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 60)
        print("RESUMEN EJECUTIVO - TESTING CLARO")
        print("=" * 60)
        print(f"Tests Ejecutados: {total_tests}")
        print(f"Tests Exitosos: {successful_tests}")
        print(f"Tests Fallidos: {total_tests - successful_tests}")
        print(f"Tasa de Exito: {success_rate:.1f}%")
        print(f"Issues Criticos: {len(self.test_results['critical_issues'])}")
        print(f"Issues Mayores: {len(self.test_results['major_issues'])}")
        print(f"Issues Menores: {len(self.test_results['minor_issues'])}")
        
        if success_rate >= 90 and len(self.test_results['critical_issues']) == 0:
            print("\nESTADO: LISTO para produccion y Fase 2 (MOVISTAR)")
        elif success_rate >= 80:
            print("\nESTADO: CONDICIONAL - Resolver issues menores")
        else:
            print("\nESTADO: NO LISTO - Resolver issues criticos")
    
    def save_results(self, output_file: str = "claro_testing_simple_report.json"):
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False, default=str)
            print(f"\nResultados guardados en: {output_file}")
        except Exception as e:
            print(f"Error guardando resultados: {e}")


def main():
    tester = ClaroTester()
    
    try:
        results = tester.run_tests()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"claro_testing_simple_report_{timestamp}.json"
        tester.save_results(output_file)
        
        print(f"\nTesting completado")
        print(f"Reporte disponible en: {output_file}")
        
        return 0 if len(results['critical_issues']) == 0 else 1
        
    except Exception as e:
        print(f"Error critico durante testing: {e}")
        traceback.print_exc()
        return 3


if __name__ == "__main__":
    sys.exit(main())