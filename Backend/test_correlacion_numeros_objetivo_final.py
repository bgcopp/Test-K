"""
Test final para verificar que TODOS los números objetivo sean detectados
Validación específica después de corrección del algoritmo
Boris - KRONOS Final Validation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.correlation_analysis_service import CorrelationAnalysisService
import sqlite3
import json
from datetime import datetime

def test_all_target_numbers():
    """Verificar que TODOS los números objetivo sean detectados"""
    
    print("\n" + "="*80)
    print("TEST FINAL - DETECCIÓN DE TODOS LOS NÚMEROS OBJETIVO")
    print("="*80)
    
    # Números objetivo de Boris
    target_numbers = [
        '3224274851', '3208611034', '3104277553', 
        '3102715509', '3143534707', '3214161903'
    ]
    
    print(f"Números objetivo: {', '.join(target_numbers)}")
    
    # 1. VERIFICAR DATOS DISPONIBLES EN BD
    print(f"\n1. VERIFICACIÓN DE DATOS DISPONIBLES")
    print("-" * 60)
    
    try:
        conn = sqlite3.connect('kronos.db')
        cursor = conn.cursor()
        
        # Verificar período con más datos
        cursor.execute("""
            SELECT MIN(fecha_hora_llamada) as min_date, 
                   MAX(fecha_hora_llamada) as max_date,
                   COUNT(*) as total_records
            FROM operator_call_data
            WHERE numero_origen IN ('3224274851', '3208611034', '3104277553', '3102715509', '3143534707', '3214161903')
               OR numero_destino IN ('3224274851', '3208611034', '3104277553', '3102715509', '3143534707', '3214161903')
        """)
        
        date_range = cursor.fetchone()
        print(f"Período con datos objetivo: {date_range[0]} a {date_range[1]}")
        print(f"Total registros con números objetivo: {date_range[2]}")
        
        # Verificar cada número individualmente
        print(f"\n2. ANÁLISIS POR NÚMERO INDIVIDUAL")
        print("-" * 60)
        
        individual_results = {}
        
        for number in target_numbers:
            cursor.execute("""
                SELECT COUNT(*) as total,
                       GROUP_CONCAT(DISTINCT celda_origen) as celdas_origen,
                       GROUP_CONCAT(DISTINCT celda_destino) as celdas_destino,
                       MIN(fecha_hora_llamada) as primera,
                       MAX(fecha_hora_llamada) as ultima
                FROM operator_call_data
                WHERE numero_origen = ? OR numero_destino = ?
            """, (number, number))
            
            result = cursor.fetchone()
            
            all_cells = set()
            if result[1]:  # celdas_origen
                all_cells.update(result[1].split(','))
            if result[2]:  # celdas_destino  
                all_cells.update(result[2].split(','))
            
            individual_results[number] = {
                'total_records': result[0],
                'unique_cells': list(all_cells),
                'cell_count': len(all_cells),
                'period': f"{result[3]} a {result[4]}" if result[3] else "Sin datos"
            }
            
            status = "✅ DATOS DISPONIBLES" if result[0] > 0 else "❌ SIN DATOS"
            print(f"{number}: {status}")
            if result[0] > 0:
                print(f"  Registros: {result[0]}")
                print(f"  Celdas únicas: {len(all_cells)} ({', '.join(list(all_cells)[:5])}{'...' if len(all_cells) > 5 else ''})")
                print(f"  Período: {result[3]} a {result[4]}")
        
        # 3. VERIFICAR DATOS HUNTER
        print(f"\n3. VERIFICACIÓN DE DATOS HUNTER")
        print("-" * 60)
        
        cursor.execute("SELECT COUNT(*) FROM cellular_data")
        hunter_total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT cell_id) FROM cellular_data")
        hunter_unique_cells = cursor.fetchone()[0]
        
        print(f"Total registros HUNTER: {hunter_total}")
        print(f"Cell IDs únicos HUNTER: {hunter_unique_cells}")
        
        # Obtener algunas cell IDs de HUNTER
        cursor.execute("SELECT DISTINCT cell_id FROM cellular_data LIMIT 10")
        sample_hunter_cells = [str(row[0]) for row in cursor.fetchall()]
        print(f"Ejemplo Cell IDs HUNTER: {', '.join(sample_hunter_cells)}")
        
        conn.close()
        
    except Exception as e:
        print(f"ERROR en verificación BD: {e}")
        return
    
    # 4. EJECUTAR ALGORITMO CORREGIDO
    print(f"\n4. EJECUTANDO ALGORITMO CORREGIDO")
    print("-" * 60)
    
    try:
        service = CorrelationAnalysisService()
        
        # Usar período amplio para capturar todos los datos
        if date_range[0] and date_range[1]:
            start_date = date_range[0]
            end_date = date_range[1]
        else:
            # Período por defecto amplio
            start_date = '2021-01-01 00:00:00'
            end_date = '2024-12-31 23:59:59'
        
        print(f"Período de análisis: {start_date} a {end_date}")
        
        results = service.analyze_correlation(
            start_date=start_date,
            end_date=end_date,
            min_coincidences=1,
            mission_id=1
        )
        
        print(f"\n5. RESULTADOS DE CORRELACIÓN")
        print("="*60)
        
        if 'error' in results:
            print(f"❌ ERROR: {results['error']}")
            return
        
        correlations = results.get('correlations', [])
        total_found = len(correlations)
        
        print(f"Total números con correlaciones: {total_found}")
        
        # Verificar cada número objetivo
        target_found = []
        target_missing = []
        
        for number in target_numbers:
            found = False
            for corr in correlations:
                if corr['numero_celular'] == number:
                    target_found.append(number)
                    found = True
                    print(f"\n✅ {number}: {corr['total_coincidencias']} coincidencias")
                    break
            
            if not found:
                target_missing.append(number)
                print(f"\n❌ {number}: NO encontrado en correlación")
        
        print(f"\n" + "="*60)
        print("RESUMEN FINAL")
        print("="*60)
        
        success_rate = (len(target_found) / len(target_numbers)) * 100
        
        print(f"Números objetivo detectados: {len(target_found)}/{len(target_numbers)} ({success_rate:.1f}%)")
        print(f"Números encontrados: {', '.join(target_found) if target_found else 'Ninguno'}")
        print(f"Números faltantes: {', '.join(target_missing) if target_missing else 'Ninguno'}")
        
        if len(target_found) == len(target_numbers):
            print(f"\n🎉 ÉXITO TOTAL: TODOS LOS NÚMEROS OBJETIVO DETECTADOS")
        elif len(target_found) > 0:
            print(f"\n⚠️ ÉXITO PARCIAL: {len(target_found)}/{len(target_numbers)} números detectados")
            
            # Analizar por qué faltan algunos
            print(f"\nANÁLISIS DE NÚMEROS FALTANTES:")
            for missing in target_missing:
                data = individual_results.get(missing, {})
                if data.get('total_records', 0) == 0:
                    print(f"  {missing}: No tiene datos en BD")
                elif data.get('cell_count', 0) == 0:
                    print(f"  {missing}: No tiene celdas asociadas")
                else:
                    print(f"  {missing}: Tiene {data['cell_count']} celdas pero no coinciden con HUNTER")
                    print(f"    Celdas: {', '.join(data['unique_cells'][:3])}")
        else:
            print(f"\n❌ FALLA TOTAL: Ningún número objetivo detectado")
        
        # Guardar reporte detallado
        report = {
            'timestamp': datetime.now().isoformat(),
            'target_numbers': target_numbers,
            'period_analyzed': f"{start_date} a {end_date}",
            'individual_results': individual_results,
            'correlation_results': results,
            'target_found': target_found,
            'target_missing': target_missing,
            'success_rate': success_rate,
            'total_correlations': total_found
        }
        
        report_file = f"test_final_numeros_objetivo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\nReporte detallado guardado: {report_file}")
        
    except Exception as e:
        print(f"ERROR en algoritmo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_all_target_numbers()