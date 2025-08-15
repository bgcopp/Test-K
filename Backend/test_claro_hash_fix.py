#!/usr/bin/env python3
"""
Script de prueba para validar la corrección del hash en archivos CLARO reales.
Simula la carga completa del archivo DATOS_POR_CELDA CLARO.xlsx
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from datetime import datetime
from services.file_processor_service import FileProcessorService
from services.data_normalizer_service import DataNormalizerService
from database.connection import DatabaseManager
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_claro_file_upload():
    """Prueba la carga del archivo CLARO con el hash corregido"""
    
    print("=== PRUEBA DE ARCHIVO CLARO CON HASH CORREGIDO ===\n")
    
    # Ruta del archivo de prueba
    file_path = r"C:\Soluciones\BGC\claude\KNSOft\datatest\Claro\formato excel\DATOS_POR_CELDA CLARO.xlsx"
    
    if not os.path.exists(file_path):
        print(f"ERROR: ARCHIVO NO ENCONTRADO: {file_path}")
        return False
    
    print(f"Archivo: {file_path}")
    
    try:
        # Inicializar servicios
        db = DatabaseManager()
        processor = FileProcessorService()
        
        # IDs de prueba
        mission_id = "mission_1"
        file_upload_id = f"test_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"Mission ID: {mission_id}")
        print(f"Upload ID: {file_upload_id}")
        
        # Simular la carga del archivo
        print("\nIniciando procesamiento del archivo...")
        
        # Leer el archivo como bytes
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
        
        file_name = os.path.basename(file_path)
        
        result = processor.process_claro_data_por_celda(
            file_bytes=file_bytes,
            file_name=file_name,
            mission_id=mission_id,
            file_upload_id=file_upload_id
        )
        
        print("\nRESULTADOS:")
        print(f"   Exito: {result.get('success', False)}")
        print(f"   Mensaje: {result.get('message', 'N/A')}")
        print(f"   Registros procesados: {result.get('processedRecords', 0)}")
        print(f"   Registros fallidos: {result.get('records_failed', 0)}")
        print(f"   Duplicados omitidos: {result.get('records_duplicated', 0)}")
        print(f"   Errores de validacion: {result.get('records_validation_failed', 0)}")
        print(f"   Otros errores: {result.get('records_other_errors', 0)}")
        print(f"   Tasa de exito: {result.get('success_rate', 0):.1f}%")
        
        # Análisis detallado de duplicados
        if 'details' in result and 'duplicate_analysis' in result['details']:
            dup_analysis = result['details']['duplicate_analysis']
            print("\nANALISIS DE DUPLICADOS:")
            print(f"   Duplicados detectados: {dup_analysis.get('detected_duplicates', 0)}")
            print(f"   Errores de validacion: {dup_analysis.get('validation_failures', 0)}")
            print(f"   Otros errores: {dup_analysis.get('other_failures', 0)}")
            print(f"   Porcentaje duplicados: {dup_analysis.get('duplicate_percentage', 0):.1f}%")
        
        # Verificar si el archivo se marcó como exitoso
        expected_success = result.get('success', False)
        actual_duplicates = result.get('records_duplicated', 0)
        actual_processed = result.get('processedRecords', 0)
        
        print(f"\nEVALUACION DEL RESULTADO:")
        print(f"   Total procesados: {actual_processed}")
        print(f"   Total duplicados: {actual_duplicates}")
        print(f"   Marcado como exitoso: {expected_success}")
        
        if expected_success and actual_processed > 0:
            print("   CORRECCION EXITOSA: El archivo se proceso correctamente")
            if actual_duplicates > 0:
                print(f"   Los {actual_duplicates} duplicados se omitieron correctamente")
        else:
            print("   PROBLEMA PERSISTENTE: El archivo aun se marca como error")
        
        return expected_success
        
    except Exception as e:
        print(f"ERROR EN LA PRUEBA: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_claro_file_upload()
    exit_code = 0 if success else 1
    print(f"\nRESULTADO FINAL: {'EXITO' if success else 'FALLO'}")
    sys.exit(exit_code)