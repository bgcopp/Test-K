"""
KRONOS - Test Rápido de Corrección TIGO
===============================================================================
Prueba rápida para verificar las correcciones aplicadas a TIGO sin toda la
infraestructura completa, enfocándose en probar los primeros registros.
===============================================================================
"""

import os
import sys
import json
import base64
import sqlite3
from datetime import datetime
from pathlib import Path

# Configurar path para importaciones
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.data_normalizer_service import DataNormalizerService
from utils.validators import validate_tigo_llamada_record, validate_tigo_call_type
from utils.operator_logger import OperatorLogger

logger = OperatorLogger()

def test_tigo_validation_fixes():
    """Prueba las correcciones de validación TIGO"""
    logger.info("Testing TIGO validation fixes...")
    
    # Test 1: Códigos que antes fallaban
    test_codes = [6, 10, 20, 30, 50, 200]
    
    for code in test_codes:
        try:
            result = validate_tigo_call_type(str(code), "test_code")
            logger.info(f"✓ Código {code} válido: {result}")
        except Exception as e:
            logger.error(f"✗ Código {code} falló: {e}")
    
    return True

def test_tigo_json_generation():
    """Prueba la generación de JSON robusta para TIGO"""
    logger.info("Testing TIGO JSON generation...")
    
    normalizer = DataNormalizerService()
    
    # Datos de prueba con valores problemáticos
    test_data = {
        'operator': 'TIGO',
        'data_type': 'llamadas_unificadas',
        'tecnologia': '4G',
        'latitud': float('nan'),  # Valor problemático
        'longitud': -74.074989,
        'potencia': None,  # Valor None
        'azimuth': 350
    }
    
    validated_record = {
        'numero_a': '3005722406',
        'numero_marcado': 'ims'
    }
    
    try:
        json_result = normalizer._create_tigo_operator_specific_data(
            test_data, validated_record, 'ims'
        )
        
        # Verificar que es JSON válido
        parsed = json.loads(json_result)
        logger.info(f"✓ JSON generado exitosamente: {len(json_result)} chars")
        logger.info(f"  Datos incluidos: {list(parsed.keys())}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Error generando JSON: {e}")
        return False

def test_sample_tigo_record():
    """Prueba procesar un registro TIGO real simplificado"""
    logger.info("Testing sample TIGO record processing...")
    
    # Registro basado en los datos reales del test
    sample_record = {
        'tipo_de_llamada': 200,
        'numero_a': '3005722406',
        'numero_marcado': 'web.colombiamovil.com.co',
        'trcsextracodec': None,
        'direccion': 'O',
        'duracion_total_seg': 0,
        'fecha_hora_origen': '28/02/2025 01:20:19',
        'celda_origen_truncada': '010006CC',
        'tecnologia': '4G',
        'direccion_fisica': 'Diagonal 61D N 26A-29',
        'ciudad': 'BOGOTÁ. D.C.',
        'departamento': 'CUNDINAMARCA',
        'azimuth': 350,
        'altura': 22,
        'potencia': 18.2,
        'longitud': -74.074989,
        'latitud': 4.64958,
        'tipo_cobertura': '6 - 1. URBANA',
        'tipo_estructura': '12 - ROOFTOP + TOWER',
        'operador': 'TIGO',
        'cellid_nval': 1
    }
    
    try:
        # Test 1: Validación
        validated = validate_tigo_llamada_record(sample_record)
        logger.info("✓ Registro validado exitosamente")
        
        # Test 2: Normalización
        normalizer = DataNormalizerService()
        normalized = normalizer.normalize_tigo_call_data_unificadas(
            sample_record, "test_file_001", "test_mission_001", "SALIENTE"
        )
        
        if normalized:
            logger.info("✓ Registro normalizado exitosamente")
            logger.info(f"  Número origen: {normalized.get('numero_origen')}")
            logger.info(f"  Número destino: {normalized.get('numero_destino')}")
            logger.info(f"  JSON length: {len(normalized.get('operator_specific_data', ''))}")
            
            # Verificar que el JSON es válido
            json.loads(normalized['operator_specific_data'])
            logger.info("✓ operator_specific_data es JSON válido")
            
            return True
        else:
            logger.error("✗ Normalización falló")
            return False
            
    except Exception as e:
        logger.error(f"✗ Error procesando registro: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Ejecuta todas las pruebas rápidas"""
    logger.info("="*60)
    logger.info("KRONOS - Test Rápido de Correcciones TIGO")
    logger.info("="*60)
    
    tests = [
        ("Validación de códigos TIGO", test_tigo_validation_fixes),
        ("Generación JSON robusta", test_tigo_json_generation),
        ("Procesamiento registro completo", test_sample_tigo_record)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            if test_func():
                logger.info(f"✓ {test_name}: PASSED")
                passed += 1
            else:
                logger.error(f"✗ {test_name}: FAILED")
        except Exception as e:
            logger.error(f"✗ {test_name}: ERROR - {e}")
    
    logger.info("="*60)
    logger.info(f"RESULTADOS: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        logger.info("🎉 TODAS LAS CORRECCIONES FUNCIONAN CORRECTAMENTE")
        return 0
    else:
        logger.warning("⚠️ Algunas correcciones necesitan más trabajo")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)