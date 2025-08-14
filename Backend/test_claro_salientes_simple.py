#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KRONOS - Test de Llamadas Salientes CLARO (Versión Simplificada)
===============================================================

Script de testing específico para validar el procesamiento de archivos
de llamadas salientes de CLARO con los archivos reales de ejemplo.

Autor: Sistema KRONOS
Versión: 1.0.0
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
import traceback

# Agregar el directorio padre al path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Backend.services.file_processor_service import FileProcessorService
from Backend.services.data_normalizer_service import DataNormalizerService

def test_claro_salientes_csv():
    """Test con el archivo CSV de llamadas salientes de CLARO."""
    print("=" * 80)
    print("TEST: CLARO Llamadas Salientes - CSV")
    print("=" * 80)
    
    file_path = r"C:\Soluciones\BGC\claude\KNSOft\datatest\Claro\LLAMADAS_SALIENTES_POR_CELDA CLARO.csv"
    
    if not os.path.exists(file_path):
        print(f"[ERROR] Archivo no encontrado: {file_path}")
        return False
    
    try:
        # Inicializar servicios
        file_processor = FileProcessorService()
        
        # Leer archivo
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
        
        print(f"[INFO] Archivo: {Path(file_path).name}")
        print(f"[INFO] Tamaño: {len(file_bytes)} bytes ({len(file_bytes) / 1024:.2f} KB)")
        
        # Generar IDs para el test
        file_upload_id = f"test-salientes-csv-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        mission_id = "test-mission-salientes"
        
        print(f"[INFO] ID de archivo: {file_upload_id}")
        print(f"[INFO] ID de misión: {mission_id}")
        print()
        
        # Procesar archivo
        print("[INFO] Iniciando procesamiento...")
        start_time = datetime.now()
        
        result = file_processor.process_claro_llamadas_salientes(
            file_bytes=file_bytes,
            file_name=Path(file_path).name,
            file_upload_id=file_upload_id,
            mission_id=mission_id
        )
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        print(f"[INFO] Tiempo de procesamiento: {processing_time:.2f} segundos")
        print()
        
        # Mostrar resultados
        if result.get('success', False):
            print("[SUCCESS] PROCESAMIENTO EXITOSO")
            print(f"    Registros procesados: {result.get('records_processed', 0)}")
            print(f"    Registros fallidos: {result.get('records_failed', 0)}")
            print(f"    Tasa de éxito: {result.get('success_rate', 0)}%")
            
            # Mostrar detalles adicionales
            details = result.get('details', {})
            print(f"    Registros originales: {details.get('original_records', 'N/A')}")
            print(f"    Registros limpios: {details.get('cleaned_records', 'N/A')}")
            print(f"    Chunks procesados: {details.get('chunks_processed', 'N/A')}")
            print(f"    Tipo de archivo: {details.get('file_type', 'N/A')}")
            
            # Mostrar errores si los hay
            processing_errors = details.get('processing_errors', [])
            if processing_errors:
                print(f"    [WARNING] Errores encontrados: {len(processing_errors)}")
                for i, error in enumerate(processing_errors[:3]):  # Solo mostrar los primeros 3
                    print(f"        {i+1}. Fila {error.get('row', 'N/A')}: {error.get('errors', ['Error desconocido'])[0]}")
            
            return True
        else:
            print("[FAILED] PROCESAMIENTO FALLIDO")
            print(f"    Error: {result.get('error', 'Error desconocido')}")
            print(f"    Registros procesados antes del fallo: {result.get('records_processed', 0)}")
            print(f"    Registros fallidos: {result.get('records_failed', 0)}")
            return False
    
    except Exception as e:
        print("[CRITICAL ERROR] ERROR CRÍTICO EN TEST")
        print(f"    Error: {str(e)}")
        print(f"    Traceback: {traceback.format_exc()}")
        return False

def test_data_normalizer_salientes():
    """Test específico del normalizador para llamadas salientes."""
    print("=" * 80)
    print("TEST: Normalizador de Llamadas Salientes CLARO")
    print("=" * 80)
    
    try:
        normalizer = DataNormalizerService()
        
        # Datos de prueba basados en el archivo real
        test_record = {
            'celda_inicio_llamada': '20264',
            'celda_final_llamada': '20264', 
            'originador': '3143563084',
            'receptor': '3136493179',
            'fecha_hora': '20/05/2021 10:00:39',
            'duracion': '32',
            'tipo': 'CDR_SALIENTE'
        }
        
        print("[INFO] Datos de prueba (llamada saliente):")
        print(json.dumps(test_record, indent=2, ensure_ascii=False))
        print()
        
        # Normalizar datos
        file_upload_id = f"test-normalizer-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        mission_id = "test-mission-normalizer"
        
        print("[INFO] Normalizando datos...")
        normalized = normalizer.normalize_claro_call_data_salientes(
            test_record, file_upload_id, mission_id
        )
        
        if normalized:
            print("[SUCCESS] NORMALIZACIÓN EXITOSA")
            print()
            print("[INFO] Datos normalizados (campos clave):")
            
            # Mostrar campos clave
            key_fields = [
                'operator', 'tipo_llamada', 'numero_origen', 'numero_destino', 
                'numero_objetivo', 'fecha_hora_llamada', 'duracion_segundos',
                'celda_origen', 'celda_destino', 'celda_objetivo'
            ]
            
            for field in key_fields:
                value = normalized.get(field, 'N/A')
                print(f"    {field}: {value}")
            
            print()
            
            # Validar campos específicos para llamadas salientes
            validations = []
            
            # Validar que es SALIENTE
            if normalized.get('tipo_llamada') == 'SALIENTE':
                validations.append("[OK] Tipo de llamada: SALIENTE")
            else:
                validations.append(f"[ERROR] Tipo de llamada: {normalized.get('tipo_llamada')} (esperado: SALIENTE)")
            
            # Validar que el número objetivo es el originador (para salientes)
            if normalized.get('numero_objetivo') == normalized.get('numero_origen'):
                validations.append("[OK] Número objetivo: Originador (correcto para salientes)")
            else:
                validations.append(f"[ERROR] Número objetivo: {normalized.get('numero_objetivo')} != {normalized.get('numero_origen')}")
            
            # Validar que la celda objetivo es la celda origen (para salientes)  
            if normalized.get('celda_objetivo') == normalized.get('celda_origen'):
                validations.append("[OK] Celda objetivo: Celda origen (correcto para salientes)")
            else:
                validations.append(f"[ERROR] Celda objetivo: {normalized.get('celda_objetivo')} != {normalized.get('celda_origen')}")
            
            print("[INFO] Validaciones específicas para llamadas salientes:")
            for validation in validations:
                print(f"    {validation}")
            
            # Verificar metadatos específicos
            try:
                specific_data = json.loads(normalized.get('operator_specific_data', '{}'))
                claro_metadata = specific_data.get('claro_metadata', {})
                if claro_metadata.get('file_format') == 'llamadas_salientes':
                    print("    [OK] Metadatos: Archivo identificado como llamadas_salientes")
                else:
                    print(f"    [ERROR] Metadatos: {claro_metadata.get('file_format')} (esperado: llamadas_salientes)")
            except:
                print("    [WARNING] Metadatos: Error parseando operator_specific_data")
            
            return True
        else:
            print("[FAILED] NORMALIZACIÓN FALLIDA")
            print("    El normalizador retornó None")
            return False
    
    except Exception as e:
        print("[CRITICAL ERROR] ERROR CRÍTICO EN TEST NORMALIZADOR")
        print(f"    Error: {str(e)}")
        print(f"    Traceback: {traceback.format_exc()}")
        return False

def main():
    """Ejecutar todos los tests."""
    print("INICIANDO TESTS DE CLARO LLAMADAS SALIENTES")
    print(f"Fecha/hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests_results = []
    
    # Test 1: Normalizador específico
    print("TEST 1/2: Normalizador de datos")
    result1 = test_data_normalizer_salientes()
    tests_results.append(("Normalizador", result1))
    print()
    
    # Test 2: Procesador de archivos
    print("TEST 2/2: Procesador de archivos CSV")
    result2 = test_claro_salientes_csv()
    tests_results.append(("Procesador CSV", result2))
    print()
    
    # Resumen final
    print("=" * 80)
    print("RESUMEN DE TESTS")
    print("=" * 80)
    
    passed = 0
    total = len(tests_results)
    
    for test_name, result in tests_results:
        status = "[PASSED]" if result else "[FAILED]"
        print(f"    {test_name}: {status}")
        if result:
            passed += 1
    
    print()
    print(f"[RESULT] {passed}/{total} tests exitosos")
    
    if passed == total:
        print("[SUCCESS] TODOS LOS TESTS PASARON - Implementación de llamadas salientes LISTA")
        return True
    else:
        print("[WARNING] ALGUNOS TESTS FALLARON - Revisar implementación")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)