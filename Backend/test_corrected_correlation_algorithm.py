#!/usr/bin/env python3
"""
KRONOS - Validación del Algoritmo de Correlación Corregido
========================================================
Boris 2025-08-18: Validar que el algoritmo corregido devuelva 
exactamente 4 celdas para el número 3143534707:

CELDAS ESPERADAS:
- 53591: Celda origen cuando es originador 
- 51203: Celda destino cuando es originador
- 51438: Celda origen cuando es originador
- 56124: Celda destino cuando es receptor

Este script verifica que la corrección del algoritmo funcione correctamente.
"""

import sys
import os
import json
from datetime import datetime

# Agregar el directorio padre al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import DatabaseManager
from services.correlation_service_dynamic import get_correlation_service_dynamic

def main():
    """Valida el algoritmo de correlación corregido"""
    print("=" * 80)
    print("VALIDACIÓN DEL ALGORITMO DE CORRELACIÓN CORREGIDO")
    print("=" * 80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Objetivo: Validar que 3143534707 devuelva exactamente 4 celdas")
    print()
    
    try:
        # Usar backup con datos reales de operadores
        import shutil
        backup_file = "kronos.db.backup_20250818_023501"
        temp_db = "test_correlation_temp.db"
        
        # Copiar backup para usar como base de datos temporal
        shutil.copy2(backup_file, temp_db)
        
        db_manager = DatabaseManager()
        db_manager.db_path = temp_db
        db_manager._initialized = True  # Marcar como inicializada para evitar recreación
        
        correlation_service = get_correlation_service_dynamic()
        
        # Parámetros de prueba (usar misión existente en el backup)
        mission_id = "mission_MPFRBNsb"
        numero_objetivo = "3143534707"
        start_datetime = "2024-08-01 00:00:00"
        end_datetime = "2024-08-31 23:59:59"
        
        print(f"Parámetros de prueba:")
        print(f"  - Misión: {mission_id}")
        print(f"  - Número objetivo: {numero_objetivo}")
        print(f"  - Período: {start_datetime} - {end_datetime}")
        print()
        
        with db_manager.get_session() as session:
            # 1. Verificar datos disponibles
            print("1. VERIFICANDO DATOS DISPONIBLES")
            print("-" * 50)
            
            # Extraer celdas HUNTER
            hunter_cells = correlation_service._extract_hunter_cells(session, mission_id)
            print(f"Celdas HUNTER encontradas: {len(hunter_cells)}")
            if len(hunter_cells) > 0:
                print(f"Primeras 10 celdas: {sorted(list(hunter_cells))[:10]}")
            print()
            
            # 2. Validación específica del número objetivo
            print("2. VALIDACIÓN ESPECÍFICA DEL NÚMERO OBJETIVO")
            print("-" * 50)
            
            validation_result = correlation_service.validate_number_correlation(
                session, numero_objetivo, hunter_cells
            )
            
            print(f"Número validado: {validation_result['numero']}")
            print(f"Total celdas encontradas: {validation_result['total_celdas']}")
            print(f"Total registros: {validation_result['total_registros']}")
            print(f"Algoritmo: {validation_result.get('algoritmo', 'N/A')}")
            print()
            
            print("Celdas únicas encontradas:")
            celdas_encontradas = set(validation_result['celdas_unicas'])
            for i, celda in enumerate(sorted(celdas_encontradas), 1):
                print(f"  {i}. {celda}")
            print()
            
            # Verificar contra las celdas esperadas
            celdas_esperadas = {'53591', '51203', '51438', '56124'}
            
            print("3. VERIFICACIÓN CONTRA CELDAS ESPERADAS")
            print("-" * 50)
            print("Celdas esperadas: 53591, 51203, 51438, 56124")
            print(f"Celdas encontradas: {', '.join(sorted(celdas_encontradas))}")
            print()
            
            # Análisis de concordancia
            celdas_correctas = celdas_esperadas.intersection(celdas_encontradas)
            celdas_faltantes = celdas_esperadas - celdas_encontradas
            celdas_extra = celdas_encontradas - celdas_esperadas
            
            print("Analisis de concordancia:")
            print(f"  - Celdas correctas ({len(celdas_correctas)}): {', '.join(sorted(celdas_correctas))}")
            if celdas_faltantes:
                print(f"  - Celdas faltantes ({len(celdas_faltantes)}): {', '.join(sorted(celdas_faltantes))}")
            if celdas_extra:
                print(f"  - Celdas extra ({len(celdas_extra)}): {', '.join(sorted(celdas_extra))}")
            print()
            
            # Resultado final
            total_esperadas = len(celdas_esperadas)
            total_encontradas = len(celdas_encontradas)
            exacta_match = celdas_esperadas == celdas_encontradas
            
            print("4. RESULTADO FINAL")
            print("-" * 50)
            if exacta_match:
                print(f"EXITO: El algoritmo devolvio exactamente las 4 celdas esperadas")
                status = "CORRECTED_SUCCESS"
            elif len(celdas_correctas) == total_esperadas and len(celdas_extra) > 0:
                print(f"PARCIAL: Todas las celdas esperadas estan presentes, pero hay {len(celdas_extra)} extras")
                status = "CORRECTED_PARTIAL"
            else:
                print(f"FALLA: El algoritmo no devolvio las celdas esperadas")
                print(f"   Esperadas: {total_esperadas}, Encontradas: {total_encontradas}, Correctas: {len(celdas_correctas)}")
                status = "CORRECTED_FAIL"
            
            print()
            
            # 3. Análisis detallado por rol
            print("5. ANÁLISIS DETALLADO POR ROL")
            print("-" * 50)
            
            roles_summary = {}
            for detalle in validation_result['detalles']:
                rol = detalle['rol']
                celda = detalle['celda']
                if rol not in roles_summary:
                    roles_summary[rol] = set()
                roles_summary[rol].add(celda)
            
            for rol in sorted(roles_summary.keys()):
                celdas_rol = roles_summary[rol]
                print(f"{rol}: {', '.join(sorted(celdas_rol))} ({len(celdas_rol)} celdas)")
            print()
            
            # 4. Ejecutar correlación completa
            print("6. CORRELACIÓN COMPLETA")
            print("-" * 50)
            
            correlation_result = correlation_service.analyze_correlation(
                mission_id, start_datetime, end_datetime, min_occurrences=1
            )
            
            if correlation_result['success']:
                print(f"Correlación exitosa: {correlation_result['total_count']} números encontrados")
                print(f"Tiempo de procesamiento: {correlation_result['processing_time']:.2f}s")
                
                # Buscar el número objetivo en los resultados
                numero_en_resultados = None
                for item in correlation_result['data']:
                    if item['numero_objetivo'] == numero_objetivo:
                        numero_en_resultados = item
                        break
                
                if numero_en_resultados:
                    print(f"Número {numero_objetivo} encontrado en resultados:")
                    print(f"  - Ocurrencias: {numero_en_resultados['ocurrencias']}")
                    print(f"  - Celdas: {', '.join(numero_en_resultados['celdas_relacionadas'])}")
                    print(f"  - Confianza: {numero_en_resultados['nivel_confianza']}%")
                else:
                    print(f"ADVERTENCIA: Numero {numero_objetivo} NO encontrado en resultados de correlacion")
            else:
                print(f"Error en correlacion: {correlation_result['message']}")
            
            print()
            
            # Guardar resultado completo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"corrected_correlation_validation_{timestamp}.json"
            
            result_data = {
                'timestamp': datetime.now().isoformat(),
                'test_name': 'Corrected Correlation Algorithm Validation',
                'numero_objetivo': numero_objetivo,
                'celdas_esperadas': list(celdas_esperadas),
                'celdas_encontradas': list(celdas_encontradas),
                'validation_result': validation_result,
                'correlation_result': correlation_result,
                'status': status,
                'exacta_match': exacta_match,
                'algorithm_corrected': True
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"Resultado completo guardado en: {filename}")
            print()
            
            # Limpiar archivo temporal
            if os.path.exists(temp_db):
                os.remove(temp_db)
                print(f"Base de datos temporal {temp_db} eliminada")
            
            return exacta_match
            
    except Exception as e:
        print(f"Error durante la validacion: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)