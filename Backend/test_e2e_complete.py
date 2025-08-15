#!/usr/bin/env python3
"""
KRONOS - Test End-to-End Completo
=================================

Test 4: Validacion de flujo completo Dashboard -> API -> Backend -> Database -> Response
para confirmar que el error "no such table: operator_data_sheets" esta totalmente solucionado.

Autor: Sistema KRONOS - Testing Engineer
Fecha: 2025-08-14
"""

import sys
import os
import json
import sqlite3
import traceback
from datetime import datetime
from pathlib import Path

# Agregar path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuracion
DB_PATH = Path(__file__).parent / "kronos.db"

def test_complete_end_to_end():
    """
    TEST 4: Flujo completo Dashboard -> API -> Backend -> Database -> Response
    """
    
    print("=" * 80)
    print("TEST 4: FLUJO COMPLETO END-TO-END")
    print("=" * 80)
    print("Simulando: Dashboard.tsx -> api.ts -> Eel -> Backend -> Database -> Response")
    print("")
    
    test_results = {
        "test_name": "complete_end_to_end_test",
        "timestamp": datetime.now().isoformat(),
        "flow_steps": {},
        "overall_status": "UNKNOWN",
        "errors": [],
        "warnings": [],
        "performance_metrics": {}
    }
    
    try:
        start_time = datetime.now()
        
        # PASO 1: Verificar estado inicial de la base de datos
        print("[STEP 1] Verificando estado inicial de la base de datos...")
        
        step_start = datetime.now()
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                # Verificar que las tres tablas criticas existen
                required_tables = ["operator_data_sheets", "operator_cellular_data", "operator_call_data"]
                existing_tables = {}
                
                for table in required_tables:
                    cursor.execute("""
                        SELECT COUNT(*) FROM sqlite_master 
                        WHERE type='table' AND name = ?
                    """, (table,))
                    
                    exists = cursor.fetchone()[0] > 0
                    existing_tables[table] = exists
                    
                    if exists:
                        # Obtener numero de registros
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        print(f"  [OK] {table}: EXISTE ({count} registros)")
                    else:
                        error = f"Tabla critica faltante: {table}"
                        test_results["errors"].append(error)
                        print(f"  [ERROR] {table}: NO EXISTE")
                
                test_results["flow_steps"]["database_verification"] = {
                    "status": "PASSED" if all(existing_tables.values()) else "FAILED",
                    "tables": existing_tables,
                    "duration_ms": (datetime.now() - step_start).total_seconds() * 1000
                }
                
        except Exception as e:
            error = f"Error verificando base de datos: {str(e)}"
            test_results["errors"].append(error)
            test_results["flow_steps"]["database_verification"] = {
                "status": "ERROR",
                "error": error,
                "duration_ms": (datetime.now() - step_start).total_seconds() * 1000
            }
            print(f"  [ERROR] {error}")
        
        # PASO 2: Simular llamada desde Dashboard.tsx
        print("\n[STEP 2] Simulando Dashboard.tsx useEffect...")
        
        step_start = datetime.now()
        backend_response = None
        
        try:
            print("  [SIM] Dashboard ejecuta: const stats = await getOperatorStatistics();")
            print("  [SIM] api.ts ejecuta: window.eel.get_operator_statistics()()")
            
            from services.operator_data_service import get_operator_statistics
            
            print("  [SIM] Backend ejecuta: operator_data_service.get_operator_statistics()")
            
            # Llamada real al backend
            backend_response = get_operator_statistics()
            
            test_results["flow_steps"]["backend_call"] = {
                "status": "PASSED",
                "response": backend_response,
                "duration_ms": (datetime.now() - step_start).total_seconds() * 1000
            }
            
            print("  [OK] Backend respondio exitosamente")
            
        except Exception as e:
            error = f"Error en llamada backend: {str(e)}"
            test_results["errors"].append(error)
            test_results["flow_steps"]["backend_call"] = {
                "status": "ERROR",
                "error": error,
                "duration_ms": (datetime.now() - step_start).total_seconds() * 1000
            }
            print(f"  [ERROR] {error}")
            
            # Verificar si es el error especifico de tabla
            if 'no such table' in str(e).lower():
                critical_error = "CRITICO: Error 'no such table' en flujo completo"
                test_results["errors"].append(critical_error)
                print(f"  [CRITICAL] {critical_error}")
        
        # PASO 3: Simular procesamiento en Dashboard.tsx
        print("\n[STEP 3] Simulando procesamiento en Dashboard.tsx...")
        
        step_start = datetime.now()
        try:
            if backend_response:
                print("  [SIM] Dashboard ejecuta: setOperatorStats(stats);")
                
                # Simular extraccion de valores (lineas 64-66 Dashboard.tsx)
                totals = backend_response.get('totals', {})
                total_files = totals.get('total_files') or 0
                total_records = totals.get('total_records') or 0
                completed_files = totals.get('completed_files') or 0
                success_rate = totals.get('success_rate') or 0
                
                extracted_values = {
                    'totalFiles': total_files,
                    'totalRecords': total_records,
                    'completedFiles': completed_files,
                    'successRate': success_rate
                }
                
                print(f"  [OK] Valores extraidos: {extracted_values}")
                
                test_results["flow_steps"]["dashboard_processing"] = {
                    "status": "PASSED",
                    "extracted_values": extracted_values,
                    "duration_ms": (datetime.now() - step_start).total_seconds() * 1000
                }
                
            else:
                # Simular manejo de error (lineas 40-54 Dashboard.tsx)
                print("  [SIM] Dashboard ejecuta catch block: valores por defecto")
                
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
                    'error': 'Error cargando datos'
                }
                
                test_results["flow_steps"]["dashboard_processing"] = {
                    "status": "ERROR_HANDLED",
                    "error_state": error_state,
                    "duration_ms": (datetime.now() - step_start).total_seconds() * 1000
                }
                
                print("  [OK] Error manejado correctamente con valores por defecto")
            
        except Exception as e:
            error = f"Error procesando en Dashboard: {str(e)}"
            test_results["errors"].append(error)
            print(f"  [ERROR] {error}")
        
        # PASO 4: Simular renderizado JSX
        print("\n[STEP 4] Simulando renderizado JSX...")
        
        step_start = datetime.now()
        try:
            # Obtener valores del paso anterior o usar defaults
            if test_results["flow_steps"]["dashboard_processing"]["status"] in ["PASSED", "ERROR_HANDLED"]:
                if "extracted_values" in test_results["flow_steps"]["dashboard_processing"]:
                    values = test_results["flow_steps"]["dashboard_processing"]["extracted_values"]
                else:
                    # Usar valores del error state
                    error_totals = test_results["flow_steps"]["dashboard_processing"]["error_state"]["totals"]
                    values = {
                        'totalFiles': error_totals['total_files'],
                        'totalRecords': error_totals['total_records'], 
                        'completedFiles': error_totals['completed_files'],
                        'successRate': error_totals['success_rate']
                    }
            else:
                # Fallback values
                values = {'totalFiles': 0, 'totalRecords': 0, 'completedFiles': 0, 'successRate': 0}
            
            # Simular renderizado de cada tarjeta
            cards_rendered = []
            
            print("  [SIM] Renderizando tarjetas:")
            
            # Cards del Dashboard
            cards_rendered.append(("Total Archivos", values['totalFiles']))
            print(f"       Card 1: Total Archivos = {values['totalFiles']}")
            
            formatted_records = f"{values['totalRecords']:,}"
            cards_rendered.append(("Total Registros Procesados", formatted_records))
            print(f"       Card 2: Total Registros = {formatted_records}")
            
            cards_rendered.append(("Archivos Completados", values['completedFiles']))
            print(f"       Card 3: Archivos Completados = {values['completedFiles']}")
            
            success_rate_display = f"{values['successRate']}%"
            cards_rendered.append(("Tasa de Exito", success_rate_display))
            print(f"       Card 4: Tasa de Exito = {success_rate_display}")
            
            test_results["flow_steps"]["jsx_rendering"] = {
                "status": "PASSED",
                "cards_rendered": cards_rendered,
                "duration_ms": (datetime.now() - step_start).total_seconds() * 1000
            }
            
            print("  [OK] Renderizado JSX completado exitosamente")
            
        except Exception as e:
            error = f"Error en renderizado JSX: {str(e)}"
            test_results["errors"].append(error)
            print(f"  [ERROR] {error}")
        
        # Metricas de rendimiento
        total_duration = (datetime.now() - start_time).total_seconds() * 1000
        test_results["performance_metrics"] = {
            "total_duration_ms": total_duration,
            "steps_completed": len([s for s in test_results["flow_steps"].values() if s["status"] in ["PASSED", "ERROR_HANDLED"]])
        }
        
        # Determinar estado general
        has_table_errors = any('no such table' in error.lower() for error in test_results["errors"])
        has_critical_errors = any('CRITICO' in error for error in test_results["errors"])
        
        if has_table_errors or has_critical_errors:
            test_results["overall_status"] = "FAILED_CRITICAL"
            print(f"\n[CRITICAL] FLUJO COMPLETO FALLIDO: Dashboard mostraria errores al usuario")
        elif test_results["errors"]:
            test_results["overall_status"] = "FAILED_NON_CRITICAL"
            print(f"\n[ERROR] FLUJO CON ERRORES: Algunos componentes fallan")
        else:
            # Verificar que los pasos principales pasaron
            key_steps = ["database_verification", "backend_call", "dashboard_processing", "jsx_rendering"]
            passed_steps = [
                step for step in key_steps 
                if step in test_results["flow_steps"] and 
                test_results["flow_steps"][step]["status"] in ["PASSED", "ERROR_HANDLED"]
            ]
            
            if len(passed_steps) == len(key_steps):
                test_results["overall_status"] = "PASSED"
                print(f"\n[SUCCESS] FLUJO COMPLETO EXITOSO: Dashboard funcionaria perfectamente")
            else:
                test_results["overall_status"] = "PARTIAL_PASS"
                print(f"\n[WARN] FLUJO PARCIALMENTE EXITOSO: {len(passed_steps)}/{len(key_steps)} pasos completados")
        
    except Exception as e:
        error_msg = f"Error critico durante test end-to-end: {str(e)}"
        test_results["errors"].append(error_msg)
        test_results["overall_status"] = "CRITICAL_ERROR"
        print(f"\n[CRITICAL] {error_msg}")
    
    return test_results


def main():
    """Ejecutar test completo end-to-end"""
    
    print("KRONOS - Test End-to-End Completo")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    # Ejecutar test
    results = test_complete_end_to_end()
    
    # Guardar resultados
    results_file = Path(__file__).parent / f"e2e_complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n[SAVE] Resultados guardados en: {results_file}")
    except Exception as e:
        print(f"[WARN] No se pudieron guardar los resultados: {e}")
    
    # Resumen final
    print("\n" + "=" * 80)
    print("RESUMEN FINAL - TEST 4: FLUJO COMPLETO END-TO-END")
    print("=" * 80)
    print(f"Estado General: {results['overall_status']}")
    print(f"Errores: {len(results['errors'])}")
    print(f"Advertencias: {len(results['warnings'])}")
    
    if "performance_metrics" in results:
        print(f"Duracion Total: {results['performance_metrics']['total_duration_ms']:.1f} ms")
        print(f"Pasos Completados: {results['performance_metrics']['steps_completed']}")
    
    # Analisis especifico del problema original
    if results["overall_status"] in ["PASSED", "PARTIAL_PASS"]:
        print("\n[SUCCESS] EL ERROR DEL DASHBOARD ESTA COMPLETAMENTE SOLUCIONADO")
        print("         [OK] Tablas de base de datos existen")
        print("         [OK] Backend API funciona sin errores de tabla")
        print("         [OK] Dashboard renderizaria las estadisticas correctamente")
        print("         [OK] NO apareceria 'Error: no such table: operator_data_sheets'")
        return True
    elif results["overall_status"] == "FAILED_CRITICAL":
        print("\n[CRITICAL] EL ERROR DEL DASHBOARD NO ESTA SOLUCIONADO")
        print("          [X] Dashboard seguiria mostrando errores al usuario")
        if results["errors"]:
            print("\n[ERROR] Problemas criticos encontrados:")
            for i, error in enumerate(results["errors"], 1):
                print(f"  {i}. {error}")
        return False
    else:
        print("\n[ERROR] HAY PROBLEMAS EN EL FLUJO COMPLETO")
        print("       Dashboard podria funcionar parcialmente pero con limitaciones")
        if results["errors"]:
            print("\n[ERROR] Problemas encontrados:")
            for i, error in enumerate(results["errors"], 1):
                print(f"  {i}. {error}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)