#!/usr/bin/env python3
"""
KRONOS - Test Rápido de Normalización de Números
================================================

Test específico para validar que la función de normalización
de números funciona correctamente y retorna números SIN prefijo 57.
"""

import os
import sys

# Agregar el directorio del backend al path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

from services.correlation_analysis_service import CorrelationAnalysisService


def test_normalize_phone_number():
    """
    Test específico para la función _normalize_phone_number.
    """
    print("=" * 60)
    print("TEST DE NORMALIZACIÓN DE NÚMEROS DE TELÉFONO")
    print("=" * 60)
    
    service = CorrelationAnalysisService()
    
    # Casos de prueba
    test_cases = [
        # (entrada, salida_esperada, descripción)
        ("573224274851", "3224274851", "Número con prefijo 57 (12 dígitos)"),
        ("573208611034", "3208611034", "Número con prefijo 57 (12 dígitos)"),
        ("573143534707", "3143534707", "Número con prefijo 57 (12 dígitos)"),
        ("573102715509", "3102715509", "Número con prefijo 57 (12 dígitos)"),
        ("573214161903", "3214161903", "Número con prefijo 57 (12 dígitos)"),
        ("3224274851", "3224274851", "Número sin prefijo (10 dígitos)"),
        ("3208611034", "3208611034", "Número sin prefijo (10 dígitos)"),
        ("", "", "Número vacío"),
        ("57123", "57123", "Número corto con 57 (no remover)"),
        ("1234567890", "1234567890", "Número de 10 dígitos sin 57"),
    ]
    
    print("Ejecutando casos de prueba:")
    print("-" * 60)
    
    all_passed = True
    
    for i, (input_number, expected, description) in enumerate(test_cases, 1):
        result = service._normalize_phone_number(input_number)
        
        status = "PASS" if result == expected else "FAIL"
        if result != expected:
            all_passed = False
        
        print(f"{i:2d}. {description}")
        print(f"    Entrada:  '{input_number}'")
        print(f"    Esperado: '{expected}'")
        print(f"    Obtenido: '{result}'")
        print(f"    Estado:   {status}")
        print()
    
    print("=" * 60)
    if all_passed:
        print("TODOS LOS TESTS PASARON")
        print("La funcion de normalizacion funciona correctamente.")
        print("Los numeros objetivo apareceran SIN prefijo 57 en el frontend.")
    else:
        print("ALGUNOS TESTS FALLARON")
        print("La funcion de normalizacion requiere correcciones.")
    
    return all_passed


def test_target_numbers_specifically():
    """
    Test específico para los números objetivo de Boris.
    """
    print("\n" + "=" * 60)
    print("TEST ESPECÍFICO NÚMEROS OBJETIVO")
    print("=" * 60)
    
    service = CorrelationAnalysisService()
    
    target_numbers = [
        "573224274851",  # Debe resultar en 3224274851
        "573208611034",  # Debe resultar en 3208611034
        "573143534707",  # Debe resultar en 3143534707
        "573102715509",  # Debe resultar en 3102715509
        "573214161903",  # Debe resultar en 3214161903
    ]
    
    expected_format = [
        "3224274851",
        "3208611034", 
        "3143534707",
        "3102715509",
        "3214161903"
    ]
    
    print("Validando números objetivo específicos:")
    print("-" * 60)
    
    all_correct = True
    
    for i, (input_num, expected) in enumerate(zip(target_numbers, expected_format), 1):
        result = service._normalize_phone_number(input_num)
        
        is_correct = result == expected
        if not is_correct:
            all_correct = False
        
        status = "OK" if is_correct else "ERROR"
        
        print(f"{status} Número {i}: {input_num} -> {result}")
        print(f"   Esperado: {expected}")
        print(f"   Correcto: {'Sí' if is_correct else 'No'}")
        print()
    
    print("=" * 60)
    if all_correct:
        print("PERFECTO: Todos los numeros objetivo se normalizan correctamente")
        print("El frontend recibira exactamente:")
        for num in expected_format:
            print(f"  - {num}")
    else:
        print("ERROR: Algunos numeros objetivo no se normalizan correctamente")
        print("Esto impedira que aparezcan en el frontend como se espera.")
    
    return all_correct


def main():
    """
    Función principal del test.
    """
    print("KRONOS - Test de Validación de Normalización de Números")
    
    # Test 1: Función general de normalización
    test1_passed = test_normalize_phone_number()
    
    # Test 2: Números objetivo específicos
    test2_passed = test_target_numbers_specifically()
    
    # Resultado final
    print("\n" + "=" * 80)
    print("RESULTADO FINAL")
    print("=" * 80)
    
    if test1_passed and test2_passed:
        print("EXITO COMPLETO")
        print("La normalizacion de numeros funciona perfectamente.")
        print("Los numeros objetivo apareceran correctamente en el frontend SIN prefijo 57.")
        exit_code = 0
    else:
        print("FALLO EN VALIDACION")
        print("La normalizacion de numeros requiere correcciones adicionales.")
        exit_code = 1
    
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)