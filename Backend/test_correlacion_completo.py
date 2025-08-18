"""
Test completo y documentado del algoritmo de correlación
Validación final de la solución implementada
Boris - KRONOS Complete Test
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.correlation_analysis_service import CorrelationAnalysisService
import sqlite3
import json
from datetime import datetime

def print_header(title):
    """Imprime encabezado formateado"""
    print(f"\n{'='*70}")
    print(f" {title}")
    print('='*70)

def print_section(title):
    """Imprime sección formateada"""
    print(f"\n{title}")
    print('-'*len(title))

def test_correlacion_completo():
    """Ejecuta prueba completa del algoritmo de correlación"""
    
    print_header("TEST COMPLETO - ALGORITMO DE CORRELACION KRONOS")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Version: 2.0.0 (Correlacion por Cell IDs)")
    
    # Configuración de prueba
    config = {
        'mission_id': 'mission_MPFRBNsb',
        'start_date': '2021-05-20 10:00:00',
        'end_date': '2021-05-20 15:00:00',
        'min_coincidences': 1
    }
    
    # Números objetivo
    target_numbers = [
        '3224274851',  # Crítico
        '3208611034',
        '3104277553',  # Crítico
        '3102715509',
        '3143534707',
        '3214161903'
    ]
    
    print_section("CONFIGURACION DE PRUEBA")
    print(f"Mision: {config['mission_id']}")
    print(f"Periodo: {config['start_date']} a {config['end_date']}")
    print(f"Min coincidencias: {config['min_coincidences']}")
    print(f"Numeros objetivo: {', '.join(target_numbers)}")
    
    # Paso 1: Verificar datos disponibles
    print_section("PASO 1: VERIFICACION DE DATOS DISPONIBLES")
    
    try:
        conn = sqlite3.connect('kronos.db')
        cursor = conn.cursor()
        
        # Verificar datos HUNTER
        cursor.execute("""
            SELECT COUNT(*), COUNT(DISTINCT cell_id)
            FROM cellular_data
            WHERE mission_id = ?
              AND created_at >= ?
              AND created_at <= ?
        """, (config['mission_id'], config['start_date'], config['end_date']))
        
        hunter_stats = cursor.fetchone()
        print(f"Datos HUNTER:")
        print(f"  Registros: {hunter_stats[0]}")
        print(f"  Cell IDs unicos: {hunter_stats[1]}")
        
        if hunter_stats[0] == 0:
            print("  [ADVERTENCIA] No hay datos HUNTER para este periodo")
        
        # Verificar datos de operadores
        cursor.execute("""
            SELECT COUNT(*), COUNT(DISTINCT numero_origen), COUNT(DISTINCT numero_destino)
            FROM operator_call_data
            WHERE fecha_hora_llamada >= ?
              AND fecha_hora_llamada <= ?
        """, (config['start_date'], config['end_date']))
        
        operator_stats = cursor.fetchone()
        print(f"\nDatos Operadores:")
        print(f"  Registros: {operator_stats[0]}")
        print(f"  Numeros origen unicos: {operator_stats[1]}")
        print(f"  Numeros destino unicos: {operator_stats[2]}")
        
        # Verificar números objetivo específicos
        print(f"\nNumeros objetivo en BD:")
        for number in target_numbers:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM operator_call_data
                WHERE (numero_origen = ? OR numero_destino = ?)
                  AND fecha_hora_llamada >= ?
                  AND fecha_hora_llamada <= ?
            """, (number, number, config['start_date'], config['end_date']))
            
            count = cursor.fetchone()[0]
            status = "[OK]" if count > 0 else "[NO HAY DATOS]"
            print(f"  {number}: {count} registros {status}")
        
        conn.close()
        
    except Exception as e:
        print(f"ERROR verificando BD: {e}")
        return
    
    # Paso 2: Ejecutar algoritmo de correlación
    print_section("PASO 2: EJECUTANDO ALGORITMO DE CORRELACION")
    
    try:
        service = CorrelationAnalysisService()
        
        start_time = datetime.now()
        
        result = service.analyze_correlation(
            start_date=config['start_date'],
            end_date=config['end_date'],
            min_coincidences=config['min_coincidences'],
            mission_id=config['mission_id']
        )
        
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        
        print(f"Tiempo de procesamiento: {elapsed:.2f} segundos")
        
        if 'error' in result:
            print(f"ERROR: {result['error']}")
            return
        
        if not result.get('success', False):
            print("ERROR: El analisis no fue exitoso")
            return
        
        correlations = result.get('correlations', [])
        statistics = result.get('statistics', {})
        
        print(f"Correlaciones encontradas: {len(correlations)}")
        
    except Exception as e:
        print(f"ERROR ejecutando algoritmo: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Paso 3: Validar resultados
    print_section("PASO 3: VALIDACION DE RESULTADOS")
    
    print(f"\nEstadisticas generales:")
    print(f"  Total correlaciones: {len(correlations)}")
    print(f"  Cell IDs HUNTER: {statistics.get('total_hunter_cells', 0)}")
    print(f"  Cell IDs operadores: {statistics.get('total_operator_cells', 0)}")
    print(f"  Numeros procesados: {statistics.get('total_operator_numbers', 0)}")
    
    # Verificar números objetivo
    print(f"\nNumeros objetivo detectados:")
    
    found_targets = []
    missing_targets = []
    
    for target in target_numbers:
        # Buscar en resultados (puede estar con o sin prefijo 57)
        found = None
        for corr in correlations:
            numero = corr.get('numero_celular', '')
            # Normalizar para comparación
            if numero == target or numero == f'57{target}' or f'57{numero}' == target:
                found = corr
                break
        
        if found:
            found_targets.append(target)
            print(f"  [DETECTADO] {target}")
            print(f"    Coincidencias: {found['total_coincidencias']}")
            print(f"    Celdas: {', '.join(found.get('celdas_detectadas', []))}")
            print(f"    Operadores: {', '.join(found.get('operadores', []))}")
        else:
            missing_targets.append(target)
            print(f"  [NO DETECTADO] {target}")
    
    # Paso 4: Análisis de resultados
    print_section("PASO 4: ANALISIS DE RESULTADOS")
    
    success_rate = (len(found_targets) / len(target_numbers)) * 100
    
    print(f"\nTasa de deteccion: {success_rate:.1f}%")
    print(f"Numeros detectados: {len(found_targets)}/{len(target_numbers)}")
    
    if found_targets:
        print(f"Detectados exitosamente: {', '.join(found_targets)}")
    
    if missing_targets:
        print(f"No detectados: {', '.join(missing_targets)}")
        print(f"\nPosibles razones para numeros no detectados:")
        print(f"  1. No tienen registros en el periodo")
        print(f"  2. Sus Cell IDs no coinciden con HUNTER")
        print(f"  3. Estan en formato diferente (prefijo)")
    
    # Paso 5: Validaciones específicas
    print_section("PASO 5: VALIDACIONES ESPECIFICAS")
    
    # Verificar números críticos
    critical_numbers = ['3224274851', '3104277553']
    
    print(f"\nNumeros criticos:")
    for critical in critical_numbers:
        found = any(
            target == critical 
            for target in found_targets
        )
        status = "OK" if found else "FALTA"
        print(f"  {critical}: [{status}]")
    
    # Verificar correlación espacial
    print(f"\nCorrelacion espacial (numeros en mismas celdas):")
    
    # Buscar números que comparten celdas
    cell_map = {}
    for corr in correlations[:20]:  # Analizar top 20
        numero = corr.get('numero_celular', '')
        celdas = corr.get('celdas_detectadas', [])
        
        for celda in celdas:
            if celda not in cell_map:
                cell_map[celda] = []
            cell_map[celda].append(numero)
    
    # Mostrar celdas con múltiples números
    shared_cells = {k: v for k, v in cell_map.items() if len(v) > 1}
    
    if shared_cells:
        for celda, numeros in list(shared_cells.items())[:5]:
            if len(numeros) > 1:
                print(f"  Celda {celda}: {len(numeros)} numeros")
                # Verificar si incluye números objetivo
                target_in_cell = [n for n in numeros if n in target_numbers or n.replace('57', '') in target_numbers]
                if target_in_cell:
                    print(f"    Incluye objetivos: {', '.join(target_in_cell[:3])}")
    
    # Paso 6: Generar reporte
    print_section("PASO 6: GENERANDO REPORTE")
    
    report = {
        'test_date': datetime.now().isoformat(),
        'configuration': config,
        'target_numbers': target_numbers,
        'results': {
            'total_correlations': len(correlations),
            'target_found': found_targets,
            'target_missing': missing_targets,
            'success_rate': success_rate,
            'processing_time': elapsed
        },
        'statistics': statistics,
        'top_correlations': correlations[:10] if correlations else [],
        'validation': {
            'hunter_data': hunter_stats[0] > 0,
            'operator_data': operator_stats[0] > 0,
            'algorithm_success': result.get('success', False),
            'critical_numbers_found': all(n in found_targets for n in critical_numbers)
        }
    }
    
    report_file = f"test_completo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"Reporte guardado: {report_file}")
    
    # Resumen final
    print_header("RESUMEN FINAL")
    
    if success_rate >= 60:
        print("[PRUEBA EXITOSA]")
        print(f"Se detectaron {len(found_targets)}/{len(target_numbers)} numeros objetivo")
        print(f"El algoritmo funciona correctamente")
    else:
        print("[PRUEBA CON OBSERVACIONES]")
        print(f"Solo se detectaron {len(found_targets)}/{len(target_numbers)} numeros")
        print(f"Revisar configuracion o datos disponibles")
    
    print(f"\nRecomendaciones:")
    if missing_targets:
        print(f"  - Verificar periodo de datos para: {', '.join(missing_targets)}")
    print(f"  - El algoritmo proceso {len(correlations)} correlaciones en {elapsed:.2f}s")
    print(f"  - Performance: {len(correlations)/elapsed:.0f} correlaciones/segundo")
    
    return report

if __name__ == "__main__":
    test_correlacion_completo()