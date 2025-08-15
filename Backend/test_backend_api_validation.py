#!/usr/bin/env python3
"""
KRONOS - Test de Validacion de Backend API
==========================================

Test 2: Verificar que la función get_operator_statistics() del backend
funciona correctamente sin errores de "no such table".

Autor: Sistema KRONOS - Testing Engineer
Fecha: 2025-08-14
"""

import sys
import os
import json
import traceback
from datetime import datetime
from pathlib import Path

# Agregar el directorio actual al path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_backend_api():
    """
    TEST 2: Verificar función get_operator_statistics()
    
    Validaciones:
    1. Import exitoso del servicio
    2. Función get_operator_statistics() ejecuta sin errores
    3. Respuesta tiene estructura esperada
    4. No hay errores de "no such table"
    """
    
    print("=" * 80)
    print("TEST 2: VALIDACION DE BACKEND API")
    print("=" * 80)
    
    test_results = {
        "test_name": "backend_api_validation",
        "timestamp": datetime.now().isoformat(),
        "tests": {},
        "overall_status": "UNKNOWN",
        "errors": [],
        "warnings": []
    }
    
    try:
        # Test 1: Importar módulo
        print("[CHECK] Importando operator_data_service...")
        
        try:
            from services.operator_data_service import get_operator_statistics
            test_results["tests"]["import_success"] = True
            print("  [OK] Import exitoso")
        except ImportError as e:
            error = f"Error importando operator_data_service: {str(e)}"
            test_results["errors"].append(error)
            test_results["tests"]["import_success"] = False
            print(f"  [ERROR] {error}")
            return test_results
        except Exception as e:
            error = f"Error critico durante import: {str(e)}"
            test_results["errors"].append(error)
            test_results["tests"]["import_success"] = False
            print(f"  [ERROR] {error}")
            return test_results
        
        # Test 2: Llamar función sin parámetros (todas las misiones)
        print("\n[CHECK] Ejecutando get_operator_statistics()...")
        
        try:
            response = get_operator_statistics()
            test_results["tests"]["function_call_success"] = True
            print("  [OK] Función ejecutada sin errores")
            
            # Validar estructura de respuesta
            print("  [INFO] Validando estructura de respuesta...")
            
            if isinstance(response, dict):
                test_results["tests"]["response_is_dict"] = True
                print("    [OK] Respuesta es un diccionario")
                
                # Verificar campos requeridos
                required_fields = ['success', 'statistics', 'totals']
                missing_fields = []
                
                for field in required_fields:
                    if field in response:
                        print(f"    [OK] Campo '{field}' presente")
                    else:
                        missing_fields.append(field)
                        print(f"    [WARN] Campo '{field}' faltante")
                
                if not missing_fields:
                    test_results["tests"]["required_fields_present"] = True
                    print("    [OK] Todos los campos requeridos presentes")
                else:
                    test_results["tests"]["required_fields_present"] = False
                    warning = f"Campos faltantes: {missing_fields}"
                    test_results["warnings"].append(warning)
                    print(f"    [WARN] {warning}")
                
                # Verificar campo 'success'
                if 'success' in response:
                    success_value = response['success']
                    test_results["tests"]["success_field_value"] = success_value
                    print(f"    [INFO] Campo 'success': {success_value}")
                    
                    if success_value:
                        print("    [OK] Función reporta éxito")
                    else:
                        # Si success=False, verificar si hay error específico de tabla
                        error_msg = response.get('error', 'Error desconocido')
                        print(f"    [WARN] Función reporta fallo: {error_msg}")
                        
                        if 'no such table' in error_msg.lower():
                            error = f"ERROR CRÍTICO: Problema de tabla detectado: {error_msg}"
                            test_results["errors"].append(error)
                            print(f"    [ERROR] {error}")
                        else:
                            warning = f"Función falló pero no por tabla faltante: {error_msg}"
                            test_results["warnings"].append(warning)
                            print(f"    [WARN] {warning}")
                
                # Verificar estructura de 'totals'
                if 'totals' in response and isinstance(response['totals'], dict):
                    totals = response['totals']
                    expected_totals_fields = ['total_files', 'total_records', 'completed_files', 'success_rate']
                    
                    print("    [INFO] Validando estructura de 'totals':")
                    for field in expected_totals_fields:
                        if field in totals:
                            value = totals[field]
                            print(f"      [OK] {field}: {value}")
                        else:
                            print(f"      [WARN] {field}: faltante")
                
                # Imprimir respuesta completa para análisis
                print(f"\n  [INFO] Respuesta completa:")
                print(f"    {json.dumps(response, indent=4, ensure_ascii=False)}")
                
                test_results["response_data"] = response
                
            else:
                test_results["tests"]["response_is_dict"] = False
                error = f"Respuesta no es diccionario: {type(response)}"
                test_results["errors"].append(error)
                print(f"    [ERROR] {error}")
        
        except Exception as e:
            error = f"Error ejecutando get_operator_statistics(): {str(e)}"
            test_results["errors"].append(error)
            test_results["tests"]["function_call_success"] = False
            print(f"  [ERROR] {error}")
            print(f"  [DEBUG] Traceback: {traceback.format_exc()}")
            
            # Verificar si el error es específico de tabla faltante
            if 'no such table' in str(e).lower():
                critical_error = "CRÍTICO: Error de 'no such table' detectado en backend"
                test_results["errors"].append(critical_error)
                print(f"  [CRITICAL] {critical_error}")
        
        # Test 3: Llamar función con mission_id específico (aunque no exista)
        print("\n[CHECK] Ejecutando get_operator_statistics(mission_id='test')...")
        
        try:
            response_with_mission = get_operator_statistics(mission_id='test_mission_id')
            test_results["tests"]["function_call_with_mission_success"] = True
            print("  [OK] Función con mission_id ejecutada sin errores")
            print(f"  [INFO] Respuesta: {json.dumps(response_with_mission, indent=2, ensure_ascii=False)}")
            
        except Exception as e:
            error = f"Error ejecutando get_operator_statistics() con mission_id: {str(e)}"
            test_results["tests"]["function_call_with_mission_success"] = False
            print(f"  [ERROR] {error}")
            
            # No agregamos a errores principales si es solo por mission_id inválido
            if 'no such table' in str(e).lower():
                test_results["errors"].append(error)
                print(f"  [CRITICAL] Error de tabla detectado con mission_id")
            else:
                test_results["warnings"].append(error)
        
        # Determinar estado general
        has_table_errors = any('no such table' in error.lower() for error in test_results["errors"])
        has_critical_errors = len(test_results["errors"]) > 0
        
        if has_table_errors:
            test_results["overall_status"] = "FAILED_TABLE_ERROR"
            print(f"\n[CRITICAL] TEST FALLIDO: Errores de tabla detectados")
        elif has_critical_errors:
            test_results["overall_status"] = "FAILED_OTHER_ERROR"
            print(f"\n[ERROR] TEST FALLIDO: Errores encontrados (no de tabla)")
        else:
            # Verificar si al menos la función básica funcionó
            basic_success = test_results["tests"].get("function_call_success", False)
            response_success = test_results.get("response_data", {}).get("success", False)
            
            if basic_success and response_success:
                test_results["overall_status"] = "PASSED"
                print(f"\n[SUCCESS] TEST EXITOSO: Backend API funciona correctamente")
            elif basic_success:
                test_results["overall_status"] = "PASSED_WITH_WARNINGS"
                print(f"\n[SUCCESS] TEST EXITOSO CON ADVERTENCIAS: API funciona pero con warnings")
            else:
                test_results["overall_status"] = "FAILED"
                print(f"\n[FAILED] TEST FALLIDO: Función no ejecuta correctamente")
        
    except Exception as e:
        error_msg = f"Error crítico durante test de backend API: {str(e)}"
        test_results["errors"].append(error_msg)
        test_results["overall_status"] = "CRITICAL_ERROR"
        print(f"\n[CRITICAL] {error_msg}")
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
    
    return test_results


def main():
    """Ejecutar test completo de backend API"""
    
    print("KRONOS - Test de Validacion de Backend API")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    # Ejecutar test
    results = test_backend_api()
    
    # Guardar resultados
    results_file = Path(__file__).parent / f"backend_api_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n[SAVE] Resultados guardados en: {results_file}")
    except Exception as e:
        print(f"[WARN] No se pudieron guardar los resultados: {e}")
    
    # Resumen final
    print("\n" + "=" * 80)
    print("RESUMEN FINAL - TEST 2: BACKEND API")
    print("=" * 80)
    print(f"Estado General: {results['overall_status']}")
    print(f"Errores: {len(results['errors'])}")
    print(f"Advertencias: {len(results['warnings'])}")
    
    # Análisis específico para el problema del dashboard
    if results["overall_status"] in ["PASSED", "PASSED_WITH_WARNINGS"]:
        print("[SUCCESS] BACKEND API FUNCIONA CORRECTAMENTE")
        print("         La función get_operator_statistics() no tiene errores de tabla")
        return True
    elif results["overall_status"] == "FAILED_TABLE_ERROR":
        print("[CRITICAL] BACKEND API TIENE ERRORES DE TABLA")
        print("          El error del dashboard NO está solucionado")
        if results["errors"]:
            print("\n[ERROR] Errores de tabla encontrados:")
            for i, error in enumerate(results["errors"], 1):
                print(f"  {i}. {error}")
        return False
    else:
        print("[ERROR] BACKEND API TIENE OTROS PROBLEMAS")
        print("       Revisar configuración del backend")
        if results["errors"]:
            print("\n[ERROR] Errores encontrados:")
            for i, error in enumerate(results["errors"], 1):
                print(f"  {i}. {error}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)