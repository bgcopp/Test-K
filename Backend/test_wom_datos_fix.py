#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test específico para verificar que el archivo PUNTO 1 TRÁFICO DATOS WOM.xlsx
se procese correctamente después de la corrección del logger.
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

class WOMDatosFixTester:
    def __init__(self):
        self.file_processor = FileProcessorService()
        
    def test_wom_datos_processing(self):
        """Prueba el procesamiento del archivo WOM datos con el logger corregido"""
        
        print("=" * 80)
        print("TEST PROCESAMIENTO WOM DATOS - LOGGER CORREGIDO")
        print("=" * 80)
        
        try:
            # Path al archivo de prueba
            file_path = r"C:\Soluciones\BGC\claude\KNSOft\archivos\CeldasDiferenteOperador\wom\PUNTO 1 TRÁFICO DATOS WOM.xlsx"
            
            if not os.path.exists(file_path):
                print(f"[ERROR] Archivo no encontrado: {file_path}")
                return
            
            # Analizar archivo
            print("\nAnalizando archivo...")
            xl_file = pd.ExcelFile(file_path)
            total_expected = 0
            
            for sheet_name in xl_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                records = len(df)
                total_expected += records
                print(f"  Hoja '{sheet_name}': {records} registros")
            
            print(f"Total esperado: {total_expected} registros")
            
            # Configurar datos de prueba
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                mission_id = f"test_wom_datos_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                user_id = 'SYSTEM'
                
                cursor.execute("""
                    INSERT INTO missions (
                        id, code, name, description, start_date, end_date, status, created_by
                    ) VALUES (?, ?, ?, ?, date('now'), date('now', '+1 day'), 'En Progreso', ?)
                """, (mission_id, f'WOM_DATOS_FIX_{datetime.now().strftime("%H%M%S")}', 
                      'Test WOM Datos Fix', 'Prueba corrección logger', user_id))
                
                # Leer archivo
                with open(file_path, 'rb') as f:
                    file_bytes = f.read()
                
                file_checksum = hashlib.sha256(file_bytes).hexdigest()
                file_upload_id = f"wom_datos_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
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
                print(f"[OK] Datos de prueba configurados")
            
            # Procesar archivo
            print("\nProcesando archivo...")
            result = self.file_processor.process_wom_datos_por_celda(
                file_bytes=file_bytes,
                file_name=os.path.basename(file_path),
                file_upload_id=file_upload_id,
                mission_id=mission_id
            )
            
            # Mostrar resultados
            print("\nResultados:")
            print(f"  Estado: {'[OK] EXITOSO' if result.get('success') else '[ERROR] FALLIDO'}")
            print(f"  Registros procesados: {result.get('records_processed', 0)}")
            print(f"  Registros fallidos: {result.get('records_failed', 0)}")
            
            if result.get('error'):
                print(f"  Error: {result['error']}")
            
            # Verificar en base de datos
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM wom_cellular_data 
                    WHERE file_upload_id = ?
                """, (file_upload_id,))
                db_count = cursor.fetchone()[0]
                
                # Limpiar datos de prueba
                cursor.execute("DELETE FROM missions WHERE id = ?", (mission_id,))
                conn.commit()
            
            print(f"\nVerificación:")
            print(f"  Registros en BD: {db_count}")
            print(f"  Esperado: {total_expected}")
            
            if result.get('success') and db_count == total_expected:
                print("\n[OK] TEST EXITOSO: Archivo procesado correctamente")
                print("     Logger funcionando sin errores")
            else:
                print("\n[WARNING] TEST CON PROBLEMAS")
                if not result.get('success'):
                    print(f"     Error en procesamiento: {result.get('error', 'Desconocido')}")
                if db_count != total_expected:
                    print(f"     Registros no coinciden: esperado {total_expected}, obtenido {db_count}")
            
        except Exception as e:
            print(f"\n[ERROR] Error en el test: {str(e)}")
            import traceback
            traceback.print_exc()

def main():
    tester = WOMDatosFixTester()
    tester.test_wom_datos_processing()
    
    print("\n" + "=" * 80)
    print("TEST COMPLETADO")
    print("=" * 80)

if __name__ == "__main__":
    main()