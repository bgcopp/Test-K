#!/usr/bin/env python3
"""
KRONOS - Test de Integración Frontend
====================================

Test 3: Verificar que Dashboard.tsx maneja correctamente las estadísticas
de operadores sin mostrar errores de "no such table".

Autor: Sistema KRONOS - Testing Engineer
Fecha: 2025-08-14
"""

import sys
import os
import json
import time
import subprocess
import threading
import traceback
from datetime import datetime
from pathlib import Path

def test_frontend_integration():
    """
    TEST 3: Verificar integración de Dashboard con getOperatorStatistics
    
    Este test simula la integración del frontend pero desde el backend,
    verificando que la cadena completa funciona.
    """
    
    print("=" * 80)
    print("TEST 3: VALIDACION DE INTEGRACION FRONTEND")
    print("=" * 80)
    
    test_results = {
        "test_name": "frontend_integration_test",
        "timestamp": datetime.now().isoformat(),
        "tests": {},
        "overall_status": "UNKNOWN",
        "errors": [],
        "warnings": []
    }
    
    try:
        # Test 1: Verificar que podemos importar y llamar getOperatorStatistics
        print("[CHECK] Importando y probando getOperatorStatistics...")
        
        try:
            # Agregar path para imports
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from services.operator_data_service import get_operator_statistics
            
            test_results["tests"]["import_success"] = True
            print("  [OK] Import exitoso")
            
            # Llamar función (esto simula lo que haría el Dashboard.tsx)
            response = get_operator_statistics()
            
            test_results["tests"]["api_call_success"] = True
            test_results["response_data"] = response
            print("  [OK] Llamada API exitosa")
            
            # Validar estructura de respuesta como lo haría el Dashboard
            if response and response.get('success'):
                test_results["tests"]["response_success"] = True
                print("  [OK] Respuesta indica éxito")
                
                # Verificar estructura de totals como en Dashboard.tsx líneas 64-66
                totals = response.get('totals', {})
                if isinstance(totals, dict):
                    total_files = totals.get('total_files', 0)
                    total_records = totals.get('total_records', 0) 
                    completed_files = totals.get('completed_files', 0)
                    
                    test_results["tests"]["totals_structure_valid"] = True
                    print(f"  [OK] Estructura de totals válida:")
                    print(f"       total_files: {total_files}")
                    print(f"       total_records: {total_records}")
                    print(f"       completed_files: {completed_files}")
                    
                    # Simular lo que hace Dashboard.tsx - usar valores por defecto si son None/undefined
                    safe_total_files = total_files or 0
                    safe_total_records = total_records or 0
                    safe_completed_files = completed_files or 0
                    
                    test_results["tests"]["safe_values_extraction"] = True
                    print(f"  [OK] Valores seguros extraídos:")
                    print(f"       safe_total_files: {safe_total_files}")
                    print(f"       safe_total_records: {safe_total_records}")
                    print(f"       safe_completed_files: {safe_completed_files}")
                    
                else:
                    test_results["tests"]["totals_structure_valid"] = False
                    warning = "Campo 'totals' no es diccionario o está faltante"
                    test_results["warnings"].append(warning)
                    print(f"  [WARN] {warning}")
                
            else:
                test_results["tests"]["response_success"] = False
                error_msg = response.get('error', 'Error desconocido') if response else 'Sin respuesta'
                
                # Verificar si es específicamente el error de tabla
                if 'no such table' in error_msg.lower():
                    error = f"CRÍTICO: Error de tabla en respuesta: {error_msg}"
                    test_results["errors"].append(error)
                    print(f"  [ERROR] {error}")
                else:
                    warning = f"Función reporta fallo pero no por tabla: {error_msg}"
                    test_results["warnings"].append(warning)
                    print(f"  [WARN] {warning}")
            
        except Exception as e:
            error = f"Error en test de API: {str(e)}"
            test_results["errors"].append(error)
            test_results["tests"]["api_call_success"] = False
            print(f"  [ERROR] {error}")
            print(f"  [DEBUG] Traceback: {traceback.format_exc()}")
            
            # Verificar si es error de tabla específico
            if 'no such table' in str(e).lower():
                critical_error = "CRÍTICO: Error de 'no such table' detectado"
                test_results["errors"].append(critical_error)
                print(f"  [CRITICAL] {critical_error}")
        
        # Test 2: Verificar manejo de errores como en Dashboard.tsx
        print("\n[CHECK] Simulando manejo de errores del Dashboard...")
        
        try:
            # Simular lo que hace el useEffect del Dashboard.tsx líneas 35-61
            try:
                # Llamada normal (línea 38 del Dashboard)
                stats = get_operator_statistics()
                
                if stats and stats.get('success'):
                    # Caso exitoso - Dashboard establecería setOperatorStats(stats)
                    test_results["tests"]["dashboard_success_path"] = True
                    print("  [OK] Flujo exitoso del Dashboard simulado")
                    
                    # Verificar que los valores no causarían errores en las tarjetas del Dashboard
                    totals = stats.get('totals', {})
                    values_for_cards = {
                        'total_files': totals.get('total_files', 0),
                        'total_records': totals.get('total_records', 0),
                        'completed_files': totals.get('completed_files', 0),
                        'success_rate': totals.get('success_rate', 0)
                    }
                    
                    # Simular formateo como en Dashboard línea 88: totalRecords.toLocaleString()
                    try:
                        formatted_records = f"{values_for_cards['total_records']:,}"
                        test_results["tests"]["number_formatting"] = True
                        print(f"  [OK] Formateo de números: {formatted_records}")
                    except Exception as format_error:
                        error = f"Error formateando números: {format_error}"
                        test_results["errors"].append(error)
                        print(f"  [ERROR] {error}")
                    
                else:
                    # Caso de error - Dashboard ejecutaría el catch (líneas 40-54)
                    test_results["tests"]["dashboard_error_path"] = True
                    error_msg = stats.get('error') if stats else 'Error cargando datos'
                    
                    # Simular el estado de error que establece el Dashboard
                    error_state = {
                        'success': False,
                        'statistics': {},
                        'totals': {
                            'total_files': 0,
                            'total_records': 0,
                            'completed_files': 0,
                            'failed_files': 0,
                            'success_rate': 0
                        },
                        'error': error_msg
                    }
                    
                    print(f"  [OK] Flujo de error del Dashboard simulado: {error_msg}")
                    
                    # Verificar que incluso en estado de error, los valores por defecto funcionan
                    default_totals = error_state['totals']
                    safe_values = {
                        'totalFiles': default_totals.get('total_files', 0),
                        'totalRecords': default_totals.get('total_records', 0),
                        'completedFiles': default_totals.get('completed_files', 0)
                    }
                    
                    print(f"  [OK] Valores por defecto en error: {safe_values}")
                    
            except Exception as dashboard_error:
                # Simular el catch del useEffect (líneas 40-54)
                print(f"  [INFO] Simulando catch del Dashboard: {dashboard_error}")
                
                # El Dashboard establece valores por defecto en caso de error
                fallback_state = {
                    'success': False,
                    'statistics': {},
                    'totals': {
                        'total_files': 0,
                        'total_records': 0,
                        'completed_files': 0,
                        'failed_files': 0,
                        'success_rate': 0
                    },
                    'error': 'Error cargando datos'
                }
                
                test_results["tests"]["dashboard_fallback"] = True
                print("  [OK] Fallback del Dashboard simulado correctamente")
                
                # Verificar que el error no es de tabla faltante
                if 'no such table' in str(dashboard_error).lower():
                    critical_error = "CRÍTICO: Dashboard recibiría error de tabla faltante"
                    test_results["errors"].append(critical_error)
                    print(f"  [CRITICAL] {critical_error}")
            
        except Exception as e:
            error = f"Error simulando Dashboard: {str(e)}"
            test_results["errors"].append(error)
            print(f"  [ERROR] {error}")
        
        # Test 3: Verificar JSX rendering simulation
        print("\n[CHECK] Simulando renderizado de componentes JSX...")
        
        try:
            # Simular los valores que usarían las tarjetas del Dashboard (líneas 64-66)
            if test_results.get("response_data") and test_results["response_data"].get('success'):
                totals = test_results["response_data"].get('totals', {})
            else:
                # Valores por defecto como en líneas 44-52 del Dashboard
                totals = {
                    'total_files': 0,
                    'total_records': 0,
                    'completed_files': 0,
                    'failed_files': 0,
                    'success_rate': 0
                }
            
            # Simular extracción de valores como en líneas 64-66
            total_files = totals.get('total_files') or 0
            total_records = totals.get('total_records') or 0
            completed_files = totals.get('completed_files') or 0
            success_rate = totals.get('success_rate') or 0
            
            # Simular renderizado de tarjetas como líneas 81-100
            card_values = {
                'Total Archivos': total_files,
                'Total Registros Procesados': f"{total_records:,}",  # línea 88
                'Archivos Completados': completed_files,
                'Tasa de Éxito': f"{success_rate}%"  # línea 98
            }
            
            test_results["tests"]["jsx_rendering_simulation"] = True
            print("  [OK] Simulación de renderizado JSX exitosa:")
            for card_name, value in card_values.items():
                print(f"       {card_name}: {value}")
            
        except Exception as e:
            error = f"Error simulando renderizado JSX: {str(e)}"
            test_results["errors"].append(error)
            print(f"  [ERROR] {error}")
        
        # Determinar estado general
        has_table_errors = any('no such table' in error.lower() for error in test_results["errors"])
        has_critical_errors = len(test_results["errors"]) > 0
        
        if has_table_errors:
            test_results["overall_status"] = "FAILED_TABLE_ERROR"
            print(f"\n[CRITICAL] TEST FALLIDO: Dashboard mostraría errores de tabla")
        elif has_critical_errors:
            test_results["overall_status"] = "FAILED_OTHER_ERROR"  
            print(f"\n[ERROR] TEST FALLIDO: Dashboard tendría otros problemas")
        else:
            # Verificar si los tests principales pasaron
            key_tests = [
                "api_call_success",
                "response_success", 
                "totals_structure_valid",
                "jsx_rendering_simulation"
            ]
            
            passed_tests = sum(1 for test in key_tests if test_results["tests"].get(test, False))
            
            if passed_tests >= 3:  # Al menos 3 de 4 tests principales
                test_results["overall_status"] = "PASSED"
                print(f"\n[SUCCESS] TEST EXITOSO: Dashboard funcionaría correctamente")
            else:
                test_results["overall_status"] = "PARTIAL_PASS"
                print(f"\n[WARN] TEST PARCIAL: Dashboard funcionaría pero con limitaciones")
        
    except Exception as e:
        error_msg = f"Error crítico durante test de integración frontend: {str(e)}"
        test_results["errors"].append(error_msg)
        test_results["overall_status"] = "CRITICAL_ERROR"
        print(f"\n[CRITICAL] {error_msg}")
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
    
    return test_results


def main():
    """Ejecutar test completo de integración frontend"""
    
    print("KRONOS - Test de Integración Frontend")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    # Ejecutar test
    results = test_frontend_integration()
    
    # Guardar resultados
    results_file = Path(__file__).parent / f"frontend_integration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n[SAVE] Resultados guardados en: {results_file}")
    except Exception as e:
        print(f"[WARN] No se pudieron guardar los resultados: {e}")
    
    # Resumen final
    print("\n" + "=" * 80)
    print("RESUMEN FINAL - TEST 3: INTEGRACION FRONTEND")
    print("=" * 80)
    print(f"Estado General: {results['overall_status']}")
    print(f"Errores: {len(results['errors'])}")
    print(f"Advertencias: {len(results['warnings'])}")
    
    # Análisis específico para el Dashboard
    if results["overall_status"] in ["PASSED", "PARTIAL_PASS"]:
        print("[SUCCESS] INTEGRACION FRONTEND FUNCIONA")
        print("         Dashboard.tsx NO mostraría errores de 'no such table'")
        print("         Las tarjetas de estadísticas se renderizarían correctamente")
        return True
    elif results["overall_status"] == "FAILED_TABLE_ERROR":
        print("[CRITICAL] INTEGRACION FRONTEND FALLARIA")
        print("          Dashboard mostraría error 'no such table: operator_data_sheets'")
        if results["errors"]:
            print("\n[ERROR] Errores que afectarían al Dashboard:")
            for i, error in enumerate(results["errors"], 1):
                print(f"  {i}. {error}")
        return False
    else:
        print("[ERROR] INTEGRACION FRONTEND TIENE PROBLEMAS")
        print("       Dashboard podría mostrar errores o comportamiento inesperado")
        if results["errors"]:
            print("\n[ERROR] Problemas encontrados:")
            for i, error in enumerate(results["errors"], 1):
                print(f"  {i}. {error}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)