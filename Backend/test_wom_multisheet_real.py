#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test de procesamiento real de archivos WOM con múltiples hojas.
Verifica que el sistema procese correctamente el 100% de los registros de todas las hojas.
"""

import os
import sys
import json
import sqlite3
import hashlib
from datetime import datetime
import pandas as pd

# Agregar el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.connection import get_db_connection
from services.file_processor_service import FileProcessorService
from services.mission_service import MissionService
from services.auth_service import AuthService

class WOMMultiSheetTester:
    def __init__(self):
        self.file_processor = FileProcessorService()
        self.mission_service = MissionService()
        self.auth_service = AuthService()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "test_name": "WOM Multi-sheet Real Processing Test",
            "tests": []
        }
        
    def setup_test_data(self):
        """Configura datos de prueba necesarios"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Usar usuario SYSTEM
                user_id = 'SYSTEM'
                
                # Crear misión de prueba con ID generado
                mission_code = f"WOM_TEST_{datetime.now().strftime('%H%M%S')}"
                mission_id = f"test_wom_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                cursor.execute("""
                    INSERT INTO missions (
                        id, code, name, description, start_date, end_date, status, created_by
                    ) VALUES (?, ?, ?, ?, date('now'), date('now', '+1 day'), 'En Progreso', ?)
                """, (mission_id, mission_code, 'Test WOM Multi-sheet', 'Prueba procesamiento multiples hojas', user_id))
                conn.commit()
                
                print(f"[OK] Datos de prueba configurados - Mision ID: {mission_id}")
                return mission_id, user_id
                
        except Exception as e:
            print(f"[ERROR] Error configurando datos de prueba: {e}")
            return None, None
    
    def test_wom_multisheet_processing(self):
        """Prueba el procesamiento del archivo WOM con múltiples hojas"""
        
        test_result = {
            "test": "WOM Multi-sheet Processing",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Configurar datos
            mission_id, user_id = self.setup_test_data()
            if not mission_id:
                test_result["status"] = "ERROR"
                test_result["error"] = "No se pudo configurar datos de prueba"
                self.results["tests"].append(test_result)
                return
            
            # Path al archivo de prueba
            file_path = r"C:\Soluciones\BGC\claude\KNSOft\archivos\CeldasDiferenteOperador\wom\PUNTO 1 TRÁFICO DATOS WOM.xlsx"
            
            if not os.path.exists(file_path):
                test_result["status"] = "ERROR"
                test_result["error"] = f"Archivo no encontrado: {file_path}"
                self.results["tests"].append(test_result)
                return
            
            # Analizar archivo antes de procesar
            print("\n" + "="*80)
            print("ANÁLISIS DEL ARCHIVO")
            print("="*80)
            
            xl_file = pd.ExcelFile(file_path)
            sheet_info = {}
            total_expected = 0
            
            for sheet_name in xl_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                records = len(df)
                total_expected += records
                sheet_info[sheet_name] = records
                print(f"  Hoja '{sheet_name}': {records} registros")
            
            print(f"\nTotal esperado: {total_expected} registros")
            
            # Leer archivo para procesamiento
            with open(file_path, 'rb') as f:
                file_bytes = f.read()
            
            # Calcular checksum del archivo
            file_checksum = hashlib.sha256(file_bytes).hexdigest()
            
            # Crear registro en operator_data_sheets
            with get_db_connection() as conn:
                cursor = conn.cursor()
                file_upload_id = f"wom_test_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                cursor.execute("""
                    INSERT INTO operator_data_sheets (
                        id, mission_id, operator, file_type, file_name, 
                        file_size_bytes, file_checksum, operator_file_format,
                        uploaded_by, uploaded_at, processing_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 'PROCESSING')
                """, (
                    file_upload_id, mission_id, 'WOM', 'CELLULAR_DATA', 
                    os.path.basename(file_path), len(file_bytes), file_checksum,
                    'EXCEL', user_id
                ))
                conn.commit()
            
            print(f"\n[OK] Registro de carga creado - ID: {file_upload_id}")
            
            # Procesar archivo
            print("\n" + "="*80)
            print("PROCESANDO ARCHIVO")
            print("="*80)
            
            result = self.file_processor.process_wom_datos_por_celda(
                file_bytes=file_bytes,
                file_name=os.path.basename(file_path),
                file_upload_id=str(file_upload_id),
                mission_id=str(mission_id)
            )
            
            # Analizar resultados
            print("\n" + "="*80)
            print("RESULTADOS DEL PROCESAMIENTO")
            print("="*80)
            
            print(f"  Estado: {'[OK] EXITOSO' if result.get('success') else '[ERROR] FALLIDO'}")
            print(f"  Registros procesados: {result.get('records_processed', 0)}")
            print(f"  Registros fallidos: {result.get('records_failed', 0)}")
            
            if 'details' in result:
                details = result['details']
                print(f"\nDetalles:")
                print(f"  - Registros originales: {details.get('original_records', 'N/A')}")
                print(f"  - Registros limpiados: {details.get('cleaned_records', 'N/A')}")
                print(f"  - Chunks procesados: {details.get('chunks_processed', 'N/A')}")
            
            # Verificar registros en la base de datos
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Contar registros insertados
                cursor.execute("""
                    SELECT COUNT(*) FROM wom_cellular_data 
                    WHERE file_upload_id = ?
                """, (file_upload_id,))
                db_count = cursor.fetchone()[0]
                
                # Verificar hojas procesadas
                cursor.execute("""
                    SELECT DISTINCT source_sheet FROM wom_cellular_data 
                    WHERE file_upload_id = ?
                """, (file_upload_id,))
                sheets_in_db = [row[0] for row in cursor.fetchall()]
            
            print(f"\n" + "="*80)
            print("VERIFICACIÓN EN BASE DE DATOS")
            print("="*80)
            print(f"  Registros en BD: {db_count}")
            print(f"  Hojas procesadas: {sheets_in_db}")
            
            # Comparación con lo esperado
            print(f"\n" + "="*80)
            print("COMPARACIÓN CON ESPERADO")
            print("="*80)
            print(f"  Esperado: {total_expected} registros")
            print(f"  Procesado: {result.get('records_processed', 0)} registros")
            print(f"  En BD: {db_count} registros")
            
            # Determinar éxito
            success = (
                result.get('success', False) and 
                db_count == total_expected and
                result.get('records_processed', 0) == total_expected
            )
            
            if success:
                print(f"\n[OK] TEST EXITOSO: 100% de registros procesados correctamente")
                test_result["status"] = "SUCCESS"
            else:
                print(f"\n[WARNING] TEST CON DISCREPANCIAS")
                test_result["status"] = "WARNING"
                test_result["warning"] = f"Esperado: {total_expected}, Procesado: {result.get('records_processed', 0)}, En BD: {db_count}"
            
            test_result["details"] = {
                "file": os.path.basename(file_path),
                "sheets": sheet_info,
                "expected_total": total_expected,
                "processed": result.get('records_processed', 0),
                "failed": result.get('records_failed', 0),
                "in_database": db_count,
                "sheets_in_db": sheets_in_db,
                "processing_result": result
            }
            
        except Exception as e:
            print(f"\n[ERROR] ERROR en el test: {str(e)}")
            test_result["status"] = "ERROR"
            test_result["error"] = str(e)
            
            import traceback
            test_result["traceback"] = traceback.format_exc()
        
        self.results["tests"].append(test_result)
    
    def cleanup_test_data(self):
        """Limpia los datos de prueba"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Eliminar datos de prueba
                cursor.execute("DELETE FROM missions WHERE id LIKE 'test_wom_%'")
                
                conn.commit()
                print("\n[OK] Datos de prueba limpiados")
        except Exception as e:
            print(f"\n[WARNING] Error limpiando datos de prueba: {e}")
    
    def save_results(self):
        """Guarda los resultados del test"""
        filename = f"wom_multisheet_real_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\nResultados guardados en: {filename}")
        return filename

def main():
    print("=" * 80)
    print("TEST REAL DE PROCESAMIENTO WOM MULTI-HOJA")
    print("=" * 80)
    
    tester = WOMMultiSheetTester()
    
    try:
        # Ejecutar test
        tester.test_wom_multisheet_processing()
        
        # Guardar resultados
        tester.save_results()
        
        # Limpiar datos de prueba
        tester.cleanup_test_data()
        
    except Exception as e:
        print(f"\n[ERROR] Error ejecutando test: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("TEST COMPLETADO")
    print("=" * 80)

if __name__ == "__main__":
    main()