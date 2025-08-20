#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRUEBA DIRECTA DEL SERVICIO DE CORRELACION PARA 3113330727
===========================================================

Probar directamente qué está retornando el servicio de correlación
para entender por qué se generan 255 nodos.
"""

import sys
import os
import json
from datetime import datetime

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from services.correlation_service_fixed import get_correlation_service_fixed
    from services.correlation_service import get_correlation_service
except ImportError as e:
    print(f"Error importando servicios: {e}")
    sys.exit(1)

def test_correlation_service_direct():
    """Probar directamente el servicio de correlación para 3113330727"""
    print("PROBANDO SERVICIO DE CORRELACION PARA 3113330727")
    print("=" * 60)
    
    target_number = "3113330727"
    
    # Parámetros de prueba (usando un período amplio)
    mission_id = "1"  # Asumir que hay una misión con ID 1
    start_datetime = "2021-05-01 00:00:00"
    end_datetime = "2021-05-31 23:59:59"
    min_occurrences = 1
    
    try:
        # PRUEBA 1: Servicio de correlación original
        print("\n1. PROBANDO SERVICIO ORIGINAL")
        print("-" * 40)
        
        original_service = get_correlation_service()
        print(f"Tipo de servicio: {type(original_service)}")
        
        # Llamar al método analyze_correlation
        original_results = original_service.analyze_correlation(
            mission_id, start_datetime, end_datetime, min_occurrences
        )
        
        print(f"Resultados del servicio original:")
        print(f"- success: {original_results.get('success')}")
        print(f"- Total resultados: {len(original_results.get('data', []))}")
        print(f"- Tiempo de procesamiento: {original_results.get('statistics', {}).get('processingTime')} segundos")
        
        # Buscar si 3113330727 está en los resultados
        target_found_original = False
        for result in original_results.get('data', []):
            if result.get('targetNumber') == target_number:
                target_found_original = True
                print(f"✅ {target_number} ENCONTRADO en servicio original:")
                print(f"   - Operador: {result.get('operator')}")
                print(f"   - Total llamadas: {result.get('totalCalls')}")
                print(f"   - Confianza: {result.get('confidence')}")
                break
        
        if not target_found_original:
            print(f"❌ {target_number} NO encontrado en servicio original")
        
        # Mostrar algunos números encontrados
        print(f"\nPrimeros 10 números encontrados por servicio original:")
        for i, result in enumerate(original_results.get('data', [])[:10]):
            print(f"   {i+1}. {result.get('targetNumber')} ({result.get('operator')}) - {result.get('totalCalls')} llamadas")
        
        # ANÁLISIS CRÍTICO: ¿Por qué 255 nodos?
        total_results = len(original_results.get('data', []))
        print(f"\n🔍 ANÁLISIS CRÍTICO:")
        print(f"   - Total números en resultado: {total_results}")
        print(f"   - ¿Coincide con los 255 nodos reportados? {total_results == 255}")
        
        if total_results == 255:
            print(f"🎯 PROBLEMA IDENTIFICADO: El servicio está retornando exactamente 255 números")
            print(f"   Esto significa que TODOS los números van al diagrama, no solo {target_number}")
        elif total_results > 255:
            print(f"⚠️ El servicio retorna MÁS números ({total_results}) que los mostrados (255)")
            print(f"   Podría haber un límite en el frontend")
        else:
            print(f"🤔 El servicio retorna MENOS números ({total_results}) que los mostrados (255)")
            print(f"   El problema podría estar en el frontend agregando nodos extra")
        
        # Guardar resultados para análisis
        with open(f"test_correlation_service_results_{target_number}.json", 'w', encoding='utf-8') as f:
            json.dump(original_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Resultados guardados en: test_correlation_service_results_{target_number}.json")
        
        # ANÁLISIS DE LA ESTRUCTURA DE DATOS
        print(f"\n📊 ANÁLISIS DE ESTRUCTURA DE DATOS:")
        if original_results.get('data'):
            first_result = original_results['data'][0]
            print(f"   Campos disponibles: {list(first_result.keys())}")
            print(f"   Ejemplo de resultado:")
            for key, value in first_result.items():
                print(f"     {key}: {value}")
        
        # PRUEBA 2: Verificar si hay métodos específicos para obtener correlaciones de un número
        print(f"\n2. BUSCANDO MÉTODOS ESPECÍFICOS PARA {target_number}")
        print("-" * 50)
        
        # Revisar si el servicio tiene métodos adicionales
        service_methods = [method for method in dir(original_service) if not method.startswith('_')]
        print(f"Métodos públicos del servicio: {service_methods}")
        
        # Si existe un método get_correlations específico, probarlo
        if hasattr(original_service, 'get_correlations'):
            print(f"\n⚡ Probando método get_correlations para {target_number}")
            try:
                specific_correlations = original_service.get_correlations(target_number)
                print(f"Correlaciones específicas para {target_number}: {len(specific_correlations) if specific_correlations else 0}")
                
                if specific_correlations:
                    print(f"Primeras 5 correlaciones específicas:")
                    for i, corr in enumerate(specific_correlations[:5]):
                        print(f"   {i+1}. {corr}")
                        
                    # ANÁLISIS CRÍTICO
                    if len(specific_correlations) == 255:
                        print(f"🎯 BINGO! get_correlations retorna exactamente 255 elementos")
                        print(f"   Este es probablemente el método que usa el frontend")
                    
            except Exception as e:
                print(f"Error probando get_correlations: {e}")
        
        return original_results
        
    except Exception as e:
        print(f"❌ Error probando servicio de correlación: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_frontend_call_simulation():
    """Simular la llamada que hace el frontend"""
    print(f"\n3. SIMULANDO LLAMADA DEL FRONTEND")
    print("-" * 40)
    
    # El frontend probablemente hace algo así:
    # window.eel.get_correlation_data('3113330727')
    
    # Intentar importar main.py para ver las funciones expuestas
    try:
        import main
        
        # Buscar funciones que contengan 'correlation' en su nombre
        main_functions = [func for func in dir(main) if 'correlation' in func.lower()]
        print(f"Funciones de correlación en main.py: {main_functions}")
        
        # Buscar funciones que contengan 'get' en su nombre
        get_functions = [func for func in dir(main) if func.startswith('get_')]
        print(f"Funciones get_ en main.py: {get_functions}")
        
        # Si existe get_correlation_data, probarla
        if hasattr(main, 'get_correlation_data'):
            print(f"\n⚡ Probando get_correlation_data('3113330727')")
            try:
                frontend_result = main.get_correlation_data('3113330727')
                print(f"Resultado de get_correlation_data:")
                print(f"   Tipo: {type(frontend_result)}")
                print(f"   Longitud: {len(frontend_result) if frontend_result else 0}")
                
                if isinstance(frontend_result, list) and len(frontend_result) == 255:
                    print(f"🎯 ENCONTRADO! get_correlation_data retorna exactamente 255 elementos")
                    print(f"   Este es el método que causa el problema")
                    
                    # Mostrar los primeros elementos
                    print(f"\nPrimeros 5 elementos:")
                    for i, item in enumerate(frontend_result[:5]):
                        print(f"   {i+1}. {item}")
                        
            except Exception as e:
                print(f"Error probando get_correlation_data: {e}")
        
    except ImportError as e:
        print(f"No se pudo importar main.py: {e}")

if __name__ == "__main__":
    test_correlation_service_direct()
    analyze_frontend_call_simulation()
    
    print(f"\n" + "="*60)
    print("INVESTIGACIÓN DEL SERVICIO DE CORRELACIÓN COMPLETADA")
    print("Revisa los archivos JSON generados para más detalles")
    print("="*60)