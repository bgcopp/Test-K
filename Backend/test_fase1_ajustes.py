#!/usr/bin/env python3
"""
PRUEBA FASE 1 - Ajustes de extracción de números
===============================================
Verificar que los ajustes de la Fase 1 funcionen correctamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.correlation_analysis_service import CorrelationAnalysisService
import logging

# Configurar logging para ver detalles
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_number_variations():
    """Probar la función de variaciones de números."""
    service = CorrelationAnalysisService()
    
    test_numbers = [
        '3224274851',
        '573224274851', 
        '3208611034',
        '1234567890'
    ]
    
    print("PRUEBA: Función _get_number_variations")
    print("=" * 50)
    
    for number in test_numbers:
        variations = service._get_number_variations(number)
        normalized = service._normalize_phone_number(number)
        
        print(f"Número: {number}")
        print(f"  Variaciones: {variations}")
        print(f"  Normalizado: {normalized}")
        print()

def test_number_extraction():
    """Probar la extracción mejorada de números."""
    service = CorrelationAnalysisService()
    
    print("\nPRUEBA: Extracción mejorada de números")
    print("=" * 50)
    
    # Usar parámetros de prueba con misión real
    mission_id = "mission_MPFRBNsb"  # Operacion Fenix
    start_date = "2021-05-20 00:00:00"
    end_date = "2021-05-20 23:59:59"
    
    try:
        with service.get_db_connection() as conn:
            # Solo probar la extracción de números
            numbers_data = service._extract_operator_numbers(
                conn, mission_id, start_date, end_date
            )
            
            print(f"Números extraídos: {len(numbers_data)}")
            
            # Mostrar algunos ejemplos
            count = 0
            for normalized_key, appearances in numbers_data.items():
                if count >= 5:  # Solo primeros 5
                    break
                    
                original_numbers = list(set(app['original_number'] for app in appearances))
                print(f"  Clave: {normalized_key}")
                print(f"    Originales: {original_numbers}")
                print(f"    Apariciones: {len(appearances)}")
                count += 1
                
    except Exception as e:
        print(f"Error en la prueba: {e}")

if __name__ == "__main__":
    print("INICIANDO PRUEBAS DE AJUSTES FASE 1")
    print("=" * 60)
    
    test_number_variations()
    test_number_extraction()
    
    print("\nPRUEBAS COMPLETADAS")