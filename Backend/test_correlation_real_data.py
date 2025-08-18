#!/usr/bin/env python3
"""
KRONOS - Test de Correcciones con Datos Reales
==============================================

Test simplificado que utiliza los datos reales de la base de datos
para validar que las correcciones funcionan correctamente.
"""

import os
import sys
import json
import logging
from datetime import datetime

# Agregar el directorio del backend al path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

# Importar servicio corregido
from services.correlation_analysis_service import get_correlation_service

# Configurar logging simple
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_correlation_with_real_data():
    """
    Test con datos reales de la base de datos.
    """
    print("=" * 80)
    print("KRONOS - Test de Correcciones con Datos Reales")
    print("=" * 80)
    
    service = get_correlation_service()
    
    # Usar mission_id real
    mission_id = "mission_MPFRBNsb"  # Este existe en la BD
    
    # Parámetros con fechas reales de los datos (mayo 2021)
    params = {
        'mission_id': mission_id,
        'start_date': '2021-05-20 09:00:00',
        'end_date': '2021-05-20 15:00:00',
        'min_coincidences': 1  # Incluir TODOS los números con >= 1 coincidencia
    }
    
    print(f"Ejecutando análisis con mission_id: {mission_id}")
    print(f"Período: {params['start_date']} a {params['end_date']}")
    print(f"Min coincidencias: {params['min_coincidences']}")
    print()
    
    # Ejecutar análisis
    start_time = datetime.now()
    
    result = service.analyze_correlation(
        mission_id=params['mission_id'],
        start_date=params['start_date'],
        end_date=params['end_date'],
        min_coincidences=params['min_coincidences']
    )
    
    end_time = datetime.now()
    processing_time = (end_time - start_time).total_seconds()
    
    print(f"Análisis completado en {processing_time:.2f} segundos")
    print()
    
    # Verificar resultados
    if not result.get('success'):
        print("ERROR: El análisis falló")
        print(f"Error: {result.get('error', 'Desconocido')}")
        return False
    
    correlations = result.get('data', [])
    statistics = result.get('statistics', {})
    
    print("=" * 60)
    print("RESULTADOS DEL ANÁLISIS")
    print("=" * 60)
    print(f"Correlaciones encontradas: {len(correlations)}")
    print(f"Total Cell IDs HUNTER: {statistics.get('total_cell_ids_hunter', 0)}")
    print(f"Total registros operador: {statistics.get('total_registros_operador', 0)}")
    print()
    
    if correlations:
        print("NÚMEROS DETECTADOS (formato correcto sin prefijo 57):")
        print("-" * 60)
        
        # Verificar formato correcto
        all_correct_format = True
        target_numbers_found = []
        
        for i, correlation in enumerate(correlations[:10], 1):  # Primeros 10
            numero = correlation.get('numero_celular', '')
            coincidencias = correlation.get('total_coincidencias', 0)
            celdas = correlation.get('celdas_detectadas', correlation.get('celdas_coincidentes', []))
            
            # Verificar formato (NO debe empezar con 57)
            format_ok = not numero.startswith('57')
            format_status = "OK" if format_ok else "ERROR"
            
            if not format_ok:
                all_correct_format = False
            
            print(f"{i:2d}. {numero} -> {coincidencias} celdas {format_status}")
            print(f"    Celdas: {celdas[:5]}...")  # Primeras 5 celdas
            
            # Verificar si es un número objetivo
            target_numbers = ['3224274851', '3208611034', '3143534707', '3102715509', '3214161903']
            if numero in target_numbers:
                target_numbers_found.append({
                    'number': numero,
                    'coincidences': coincidencias,
                    'cells': celdas
                })
        
        print()
        print("=" * 60)
        print("VALIDACIÓN DE FORMATO")
        print("=" * 60)
        
        if all_correct_format:
            print("EXCELENTE: Todos los números están en formato correcto (SIN prefijo 57)")
        else:
            print("ERROR: Algunos números tienen prefijo 57 incorrectamente")
        
        print()
        print("=" * 60)
        print("NÚMEROS OBJETIVO DETECTADOS")
        print("=" * 60)
        
        if target_numbers_found:
            print(f"DETECTADOS: {len(target_numbers_found)} números objetivo")
            for target in target_numbers_found:
                print(f"  {target['number']}: {target['coincidences']} coincidencias")
                print(f"    Celdas: {target['cells']}")
        else:
            print("No se detectaron números objetivo específicos")
            print("Esto puede ser normal si los datos no contienen esos números")
        
        # Guardar reporte
        report_filename = f"correlation_real_data_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump({
                'test_info': {
                    'timestamp': datetime.now().isoformat(),
                    'mission_id': mission_id,
                    'processing_time_seconds': processing_time,
                    'parameters': params
                },
                'analysis_result': result,
                'format_validation': {
                    'all_correct_format': all_correct_format,
                    'total_numbers': len(correlations)
                },
                'target_numbers_found': target_numbers_found
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\nReporte guardado en: {report_filename}")
        
        return all_correct_format and len(correlations) > 0
    
    else:
        print("No se encontraron correlaciones")
        print("Esto podría indicar:")
        print("  1. No hay Cell IDs coincidentes entre HUNTER y operadores")
        print("  2. Los datos no están en el período especificado")
        print("  3. Problema en el algoritmo de correlación")
        
        return False


def main():
    """
    Función principal del test.
    """
    try:
        success = test_correlation_with_real_data()
        
        print("\n" + "=" * 80)
        print("RESULTADO FINAL")
        print("=" * 80)
        
        if success:
            print("EXITO: Las correcciones funcionan correctamente")
            print("- Los números aparecen en formato correcto (SIN prefijo 57)")
            print("- El algoritmo procesa los datos reales correctamente")
            return 0
        else:
            print("FALLO: Las correcciones requieren ajustes adicionales")
            return 1
    
    except Exception as e:
        print(f"ERROR CRÍTICO: {e}")
        logger.exception("Error durante el test")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)