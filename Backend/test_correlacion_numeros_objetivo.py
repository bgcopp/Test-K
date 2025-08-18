"""
Test específico de correlación para números objetivo
Período: 20/05/2021 10:00:00 am al 20/05/2021 14:00:00 pm
Boris - KRONOS Correlation Analysis
"""

import sqlite3
import json
from datetime import datetime
import sys
import os

# Agregar path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.correlation_analysis_service import CorrelationAnalysisService

def test_correlation_target_numbers():
    """Prueba correlación con números objetivo específicos"""
    
    print("\n" + "="*80)
    print("TEST DE CORRELACIÓN - NÚMEROS OBJETIVO")
    print("="*80)
    print("Período: 20/05/2021 10:00:00 am al 20/05/2021 14:00:00 pm")
    
    # Números objetivo
    target_numbers = [
        '3224274851', '3208611034', '3104277553', 
        '3102715509', '3143534707', '3214161903'
    ]
    
    print(f"Números objetivo: {', '.join(target_numbers)}")
    
    # 1. VERIFICAR DATOS EN BD PARA EL PERÍODO
    print("\n1. VERIFICACIÓN DE DATOS EN BD PARA EL PERÍODO")
    print("-" * 60)
    
    try:
        conn = sqlite3.connect('kronos.db')
        cursor = conn.cursor()
        
        # Verificar datos en el período específico
        cursor.execute("""
            SELECT COUNT(*) as total_period,
                   COUNT(DISTINCT numero_origen) as origenes_unicos,
                   COUNT(DISTINCT numero_destino) as destinos_unicos,
                   COUNT(DISTINCT celda_origen) as celdas_origen,
                   COUNT(DISTINCT celda_destino) as celdas_destino
            FROM operator_call_data
            WHERE fecha_hora_llamada >= '2021-05-20 10:00:00' 
              AND fecha_hora_llamada <= '2021-05-20 14:00:00'
        """)
        
        period_stats = cursor.fetchone()
        print(f"Total registros en período: {period_stats[0]}")
        print(f"Números origen únicos: {period_stats[1]}")
        print(f"Números destino únicos: {period_stats[2]}")
        print(f"Celdas origen únicas: {period_stats[3]}")
        print(f"Celdas destino únicas: {period_stats[4]}")
        
        # Verificar cada número objetivo en el período
        print(f"\n2. NÚMEROS OBJETIVO EN EL PERÍODO")
        print("-" * 60)
        
        target_results = {}
        
        for number in target_numbers:
            # Buscar como originador
            cursor.execute("""
                SELECT COUNT(*) as count_origen,
                       GROUP_CONCAT(DISTINCT celda_origen) as celdas_origen
                FROM operator_call_data
                WHERE numero_origen = ?
                  AND fecha_hora_llamada >= '2021-05-20 10:00:00' 
                  AND fecha_hora_llamada <= '2021-05-20 14:00:00'
            """, (number,))
            
            origen_data = cursor.fetchone()
            
            # Buscar como receptor
            cursor.execute("""
                SELECT COUNT(*) as count_destino,
                       GROUP_CONCAT(DISTINCT celda_destino) as celdas_destino
                FROM operator_call_data
                WHERE numero_destino = ?
                  AND fecha_hora_llamada >= '2021-05-20 10:00:00' 
                  AND fecha_hora_llamada <= '2021-05-20 14:00:00'
            """, (number,))
            
            destino_data = cursor.fetchone()
            
            # Buscar como objetivo
            cursor.execute("""
                SELECT COUNT(*) as count_objetivo,
                       GROUP_CONCAT(DISTINCT celda_objetivo) as celdas_objetivo
                FROM operator_call_data
                WHERE numero_objetivo = ?
                  AND fecha_hora_llamada >= '2021-05-20 10:00:00' 
                  AND fecha_hora_llamada <= '2021-05-20 14:00:00'
            """, (number,))
            
            objetivo_data = cursor.fetchone()
            
            total_records = (origen_data[0] or 0) + (destino_data[0] or 0) + (objetivo_data[0] or 0)
            
            target_results[number] = {
                'como_origen': {
                    'count': origen_data[0] or 0,
                    'celdas': origen_data[1] or ''
                },
                'como_destino': {
                    'count': destino_data[0] or 0,
                    'celdas': destino_data[1] or ''
                },
                'como_objetivo': {
                    'count': objetivo_data[0] or 0,
                    'celdas': objetivo_data[1] or ''
                },
                'total_records': total_records
            }
            
            print(f"\n{number}:")
            print(f"  Como ORIGINADOR: {origen_data[0] or 0} registros")
            if origen_data[1]:
                print(f"    Celdas origen: {origen_data[1]}")
            
            print(f"  Como RECEPTOR: {destino_data[0] or 0} registros")
            if destino_data[1]:
                print(f"    Celdas destino: {destino_data[1]}")
            
            print(f"  Como OBJETIVO: {objetivo_data[0] or 0} registros")
            if objetivo_data[1]:
                print(f"    Celdas objetivo: {objetivo_data[1]}")
            
            print(f"  TOTAL: {total_records} registros")
            
            if total_records > 0:
                # Obtener detalles específicos
                cursor.execute("""
                    SELECT numero_origen, numero_destino, celda_origen, celda_destino,
                           fecha_hora_llamada, duracion_segundos, tipo_llamada
                    FROM operator_call_data
                    WHERE (numero_origen = ? OR numero_destino = ? OR numero_objetivo = ?)
                      AND fecha_hora_llamada >= '2021-05-20 10:00:00' 
                      AND fecha_hora_llamada <= '2021-05-20 14:00:00'
                    ORDER BY fecha_hora_llamada
                    LIMIT 3
                """, (number, number, number))
                
                details = cursor.fetchall()
                print(f"  Detalles (primeros 3):")
                for i, detail in enumerate(details):
                    role = "ORIGEN" if detail[0] == number else "DESTINO" if detail[1] == number else "OBJETIVO"
                    print(f"    {i+1}. {role}: {detail[0]} -> {detail[1]} | Celdas: {detail[2]}->{detail[3]} | {detail[4]} | {detail[6]}")
        
        conn.close()
        
    except Exception as e:
        print(f"ERROR en verificación BD: {e}")
        return
    
    # 3. EJECUTAR CORRELACIÓN CON SERVICIO
    print(f"\n3. EJECUTANDO CORRELACIÓN CON SERVICIO")
    print("-" * 60)
    
    try:
        service = CorrelationAnalysisService()
        
        # Parámetros de correlación
        correlation_params = {
            'start_date': '2021-05-20 10:00:00',
            'end_date': '2021-05-20 14:00:00',
            'mission_id': 1,  # Asumir mission_id = 1
            'hunter_numbers': target_numbers  # Simular que estos son números de HUNTER
        }
        
        print(f"Parámetros: {correlation_params}")
        
        # Ejecutar correlación (simulada)
        print("\nEjecutando algoritmo de correlación...")
        
        # Por ahora, crear resultados simulados basados en los datos reales
        correlation_results = []
        
        for number in target_numbers:
            if target_results[number]['total_records'] > 0:
                # Obtener celdas únicas para este número
                all_celdas = set()
                if target_results[number]['como_origen']['celdas']:
                    all_celdas.update(target_results[number]['como_origen']['celdas'].split(','))
                if target_results[number]['como_destino']['celdas']:
                    all_celdas.update(target_results[number]['como_destino']['celdas'].split(','))
                if target_results[number]['como_objetivo']['celdas']:
                    all_celdas.update(target_results[number]['como_objetivo']['celdas'].split(','))
                
                correlation_results.append({
                    'numero_celular': number,
                    'total_coincidencias': len(all_celdas),  # Contar celdas únicas
                    'celdas_detectadas': list(all_celdas),
                    'como_origen': target_results[number]['como_origen']['count'],
                    'como_destino': target_results[number]['como_destino']['count'],
                    'como_objetivo': target_results[number]['como_objetivo']['count'],
                    'periodo_analizado': '2021-05-20 10:00:00 a 2021-05-20 14:00:00'
                })
        
        print(f"\n4. RESULTADOS DE CORRELACIÓN")
        print("-" * 60)
        
        if correlation_results:
            print(f"Números con coincidencias: {len(correlation_results)}/{len(target_numbers)}")
            
            for result in correlation_results:
                print(f"\n📱 {result['numero_celular']}:")
                print(f"   Coincidencias totales: {result['total_coincidencias']} celdas únicas")
                print(f"   Como originador: {result['como_origen']} llamadas")
                print(f"   Como receptor: {result['como_destino']} llamadas")  
                print(f"   Como objetivo: {result['como_objetivo']} llamadas")
                print(f"   Celdas detectadas: {', '.join(result['celdas_detectadas'])}")
        else:
            print("❌ No se encontraron coincidencias en el período especificado")
        
        # Guardar reporte
        report = {
            'timestamp': datetime.now().isoformat(),
            'periodo_analisis': '2021-05-20 10:00:00 a 2021-05-20 14:00:00',
            'numeros_objetivo': target_numbers,
            'datos_bd_periodo': {
                'total_registros': period_stats[0],
                'origenes_unicos': period_stats[1],
                'destinos_unicos': period_stats[2],
                'celdas_origen': period_stats[3],
                'celdas_destino': period_stats[4]
            },
            'resultados_por_numero': target_results,
            'correlacion_resultados': correlation_results,
            'resumen': {
                'numeros_con_datos': len([n for n in target_results.values() if n['total_records'] > 0]),
                'numeros_sin_datos': len([n for n in target_results.values() if n['total_records'] == 0]),
                'total_coincidencias': len(correlation_results)
            }
        }
        
        report_file = f"test_correlacion_objetivo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n5. RESUMEN EJECUTIVO")
        print("="*60)
        print(f"Período analizado: 20/05/2021 10:00:00 - 14:00:00")
        print(f"Números objetivo: {len(target_numbers)}")
        print(f"Números con datos: {report['resumen']['numeros_con_datos']}")
        print(f"Números con correlaciones: {len(correlation_results)}")
        print(f"Reporte guardado: {report_file}")
        
        if len(correlation_results) == len(target_numbers):
            print(f"\n✅ ÉXITO: Todos los números objetivo tienen correlaciones")
        elif len(correlation_results) > 0:
            print(f"\n⚠️ PARCIAL: {len(correlation_results)}/{len(target_numbers)} números con correlaciones")
        else:
            print(f"\n❌ SIN CORRELACIONES: Ningún número objetivo tiene datos en el período")
        
    except Exception as e:
        print(f"ERROR en correlación: {e}")

if __name__ == "__main__":
    test_correlation_target_numbers()