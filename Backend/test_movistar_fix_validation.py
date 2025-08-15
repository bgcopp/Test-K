#!/usr/bin/env python3
"""
Script de prueba para validar la corrección del procesamiento de archivos MOVISTAR.
Prueba específicamente que los duplicados no causen aborto del procesamiento.
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

def test_movistar_file_upload():
    """Prueba la carga del archivo MOVISTAR con la corrección de duplicados"""
    
    print("=== PRUEBA DE ARCHIVO MOVISTAR CON CORRECCIÓN DE DUPLICADOS ===\n")
    
    # Ruta del archivo de prueba
    file_path = r"C:\Soluciones\BGC\claude\KNSOft\datatest\Movistar\Formato Excel\jgd202410754_00007301_datos_ MOVISTAR.xlsx"
    
    if not os.path.exists(file_path):
        print(f"ERROR: ARCHIVO NO ENCONTRADO: {file_path}")
        return False
    
    print(f"Archivo: {file_path}")
    
    try:
        # Inicializar servicios
        db = DatabaseManager()
        processor = FileProcessorService()
        
        # IDs de prueba - usar registros existentes en la DB
        mission_id = "mission_MPFRBNsb"  # Misión existente en la DB
        file_upload_id = "a089ee6d-edd1-474e-bd78-dc611ef4fb04"  # Sheet MOVISTAR existente
        
        print(f"Mission ID: {mission_id}")
        print(f"Upload ID: {file_upload_id}")
        
        # Simular la carga del archivo
        print("\nIniciando procesamiento del archivo MOVISTAR...")
        
        # Leer el archivo como bytes
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
        
        file_name = os.path.basename(file_path)
        
        result = processor.process_movistar_datos_por_celda(
            file_bytes=file_bytes,
            file_name=file_name,
            mission_id=mission_id,
            file_upload_id=file_upload_id
        )
        
        print("\nRESULTADOS:")
        print(f"   Éxito: {result.get('success', False)}")
        print(f"   Mensaje: {result.get('message', 'N/A')}")
        print(f"   Registros procesados: {result.get('processedRecords', 0)}")
        print(f"   Registros fallidos: {result.get('records_failed', 0)}")
        print(f"   Duplicados omitidos: {result.get('records_duplicated', 0)}")
        print(f"   Errores de validación: {result.get('records_validation_failed', 0)}")
        print(f"   Otros errores: {result.get('records_other_errors', 0)}")
        print(f"   Tasa de éxito: {result.get('success_rate', 0):.1f}%")
        
        # Análisis detallado
        if 'details' in result:
            details = result['details']
            print("\nDETALLES DEL PROCESAMIENTO:")
            if 'duplicate_analysis' in details:
                dup_analysis = details['duplicate_analysis']
                print(f"   Duplicados detectados: {dup_analysis.get('detected_duplicates', 0)}")
                print(f"   Errores de validación: {dup_analysis.get('validation_failures', 0)}")
                print(f"   Otros errores: {dup_analysis.get('other_failures', 0)}")
                print(f"   Porcentaje duplicados: {dup_analysis.get('duplicate_percentage', 0):.1f}%")
        
        # Verificar la corrección específica
        expected_success = result.get('success', False)
        actual_duplicates = result.get('records_duplicated', 0)
        actual_processed = result.get('processedRecords', 0)
        actual_failed = result.get('records_failed', 0)
        
        print(f"\nEVALUACIÓN DE LA CORRECCIÓN:")
        print(f"   Total procesados: {actual_processed}")
        print(f"   Total duplicados: {actual_duplicates}")
        print(f"   Total errores reales: {actual_failed}")
        print(f"   Marcado como exitoso: {expected_success}")
        
        # Verificar que la corrección funcionó
        correction_worked = True
        if expected_success and actual_processed > 0:
            print("   [EXITO] CORRECCIÓN EXITOSA: El archivo se procesó correctamente")
            if actual_duplicates > 0:
                print(f"   [EXITO] Los {actual_duplicates} duplicados se omitieron sin causar error")
            if actual_failed < 255:  # El límite anterior que causaba el aborto
                print(f"   [EXITO] Errores reales ({actual_failed}) no alcanzaron el límite de aborto")
        else:
            print("   [ERROR] PROBLEMA PERSISTENTE: El archivo aún se marca como error")
            correction_worked = False
        
        # Verificar que no se abortó por exceso de errores
        if 'error' in result and 'Demasiados errores' in result.get('error', ''):
            print("   [ERROR] ERROR: El procesamiento se abortó por exceso de errores")
            correction_worked = False
        else:
            print("   [EXITO] El procesamiento no se abortó por límite de errores")
        
        return correction_worked
        
    except Exception as e:
        print(f"ERROR EN LA PRUEBA: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_movistar_file_upload()
    exit_code = 0 if success else 1
    print(f"\nRESULTADO FINAL: {'CORRECCIÓN EXITOSA' if success else 'CORRECCIÓN FALLIDA'}")
    sys.exit(exit_code)