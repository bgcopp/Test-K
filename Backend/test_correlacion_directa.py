#!/usr/bin/env python3
"""
PRUEBA DIRECTA DE CORRELACIÓN
============================

Script para probar directamente el algoritmo de correlación
sin intentar cargar datos nuevamente.

Autor: Boris - Prueba Correlación Directa
Fecha: 2025-08-18
"""

import os
import sys
import json
from datetime import datetime
import traceback

# Agregar el directorio padre al path para importar servicios
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def print_section(title):
    """Imprime una sección del diagnóstico."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_error(message):
    """Imprime un mensaje de error."""
    print(f"[ERROR] {message}")

def print_info(message):
    """Imprime un mensaje informativo."""
    print(f"[INFO] {message}")

def print_success(message):
    """Imprime un mensaje de éxito."""
    print(f"[SUCCESS] {message}")

def test_correlation_algorithm():
    """Prueba el algoritmo de correlación con los datos CLARO cargados."""
    print_section("PRUEBA DIRECTA DEL ALGORITMO DE CORRELACIÓN")
    
    try:
        from services.correlation_service import get_correlation_service
        from database.connection import init_database
        
        print_info("Inicializando base de datos...")
        db_path = r"C:\Soluciones\BGC\claude\KNSOft\Backend\kronos.db"
        init_database(db_path)
        
        print_info("Inicializando servicio de correlación...")
        correlation_service = get_correlation_service()
        
        mission_id = "mission_MPFRBNsb"
        
        print_info(f"Ejecutando correlación para misión: {mission_id}")
        print_info("Período: 2021-05-20 00:00:00 - 2021-05-21 23:59:59")
        print_info("Min occurrences: 1")
        
        # Usar el nuevo servicio de correlación
        result = correlation_service.analyze_correlation(
            mission_id=mission_id,
            start_datetime="2021-05-20 00:00:00",
            end_datetime="2021-05-21 23:59:59",
            min_occurrences=1
        )
        
        print(f"\nRESULTADO DE CORRELACIÓN:")
        print(f"  Success: {result.get('success', False)}")
        print(f"  Total Results: {len(result.get('data', []))}")
        
        if result.get('success') and result.get('data'):
            print_success(f"Correlación exitosa: {len(result['data'])} resultados encontrados")
            
            # Mostrar estadísticas
            stats = result.get('statistics', {})
            print(f"\nESTADÍSTICAS:")
            print(f"  Processing Time: {stats.get('processingTime', 'N/A')}s")
            print(f"  Hunter Cells Total: {stats.get('hunterCellsTotal', 'N/A')}")
            print(f"  Analysis Type: {stats.get('analysisType', 'N/A')}")
            
            # Mostrar primeros 5 resultados
            print(f"\nPRIMEROS 5 RESULTADOS:")
            for i, res in enumerate(result['data'][:5]):
                print(f"  {i+1}. Número: {res.get('targetNumber', 'N/A')} - Operador: {res.get('operator', 'N/A')} - Confianza: {res.get('confidence', 'N/A')}% - Occurrences: {res.get('occurrences', 'N/A')}")
            
            # Verificar números objetivo específicos
            target_numbers = ['3224274851', '3208611034', '3104277553', '3102715509', '3143534707', '3214161903']
            found_targets = []
            
            print(f"\nVERIFICACIÓN NÚMEROS OBJETIVO:")
            for target in target_numbers:
                found = any(res.get('targetNumber') == target for res in result['data'])
                if found:
                    print_success(f"Número objetivo {target}: ENCONTRADO")
                    found_targets.append(target)
                else:
                    print_info(f"Número objetivo {target}: no encontrado en este período")
            
            print(f"\nRESUMEN:")
            print_info(f"Números objetivo encontrados: {len(found_targets)}/{len(target_numbers)}")
            
        else:
            print_info("Correlación ejecutada pero sin resultados")
            if result.get('statistics'):
                stats = result.get('statistics', {})
                print(f"Hunter Cells Total: {stats.get('hunterCellsTotal', 0)}")
        
        return result
        
    except Exception as e:
        print_error(f"Error ejecutando correlación: {e}")
        traceback.print_exc()
        return None

def main():
    """Función principal de la prueba."""
    print_section("PRUEBA DIRECTA DE CORRELACIÓN - KRONOS")
    print("Probando algoritmo de correlación con datos existentes...")
    print(f"Timestamp: {datetime.now()}")
    
    # Probar algoritmo de correlación
    correlation_result = test_correlation_algorithm()
    
    print_section("PRUEBA COMPLETADA")
    if correlation_result and correlation_result.get('success'):
        print_success("Algoritmo de correlación funcionando correctamente")
    else:
        print_error("Algoritmo de correlación con problemas")

if __name__ == "__main__":
    main()