"""
Test manual de correlación para el período de agosto 2024
Verificar que los números objetivo aparezcan correctamente
Boris - KRONOS Manual Test
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.correlation_analysis_service import CorrelationAnalysisService
import json
from datetime import datetime

def test_correlation_manual():
    """Test manual de correlación con datos reales"""
    
    print("\n" + "="*70)
    print("TEST MANUAL DE CORRELACIÓN - AGOSTO 2024")
    print("="*70)
    
    # Números de HUNTER simulados (los números objetivo)
    hunter_numbers = [
        '3224274851', '3208611034', '3104277553', 
        '3102715509', '3143534707', '3214161903'
    ]
    
    print(f"Números HUNTER simulados: {', '.join(hunter_numbers)}")
    print(f"Período: 2024-08-12 20:00:00 a 2024-08-13 02:00:00")
    
    try:
        # Inicializar servicio
        service = CorrelationAnalysisService()
        
        # Crear datos simulados de HUNTER
        hunter_data = []
        for i, number in enumerate(hunter_numbers):
            hunter_data.append({
                'id_archivo': i + 1,
                'numero_celular': number,
                'celda_inicio': f'CELL_{i+1000}',
                'celda_fin': f'CELL_{i+2000}',
                'fecha_inicio': '2024-08-12 20:00:00',
                'fecha_fin': '2024-08-13 02:00:00'
            })
        
        print(f"\nDatos HUNTER simulados: {len(hunter_data)} registros")
        
        # Ejecutar correlación
        print(f"\nEjecutando análisis de correlación...")
        
        results = service.analyze_correlation(
            start_date='2024-08-12 20:00:00',
            end_date='2024-08-13 02:00:00',
            min_coincidences=1,
            mission_id=1
        )
        
        print(f"\n" + "="*50)
        print("RESULTADOS DEL ANÁLISIS")
        print("="*50)
        
        if 'error' in results:
            print(f"❌ ERROR: {results['error']}")
            return
        
        correlations = results.get('correlations', [])
        
        print(f"Total de correlaciones encontradas: {len(correlations)}")
        
        if correlations:
            print(f"\nDETALLE DE CORRELACIONES:")
            print("-" * 40)
            
            for corr in correlations:
                number = corr['numero_celular']
                coincidences = corr['total_coincidencias']
                
                print(f"\n📱 {number}:")
                print(f"   Coincidencias: {coincidences}")
                
                # Verificar si es uno de nuestros números críticos
                if number in ['3104277553', '3224274851']:
                    print(f"   🎯 NÚMERO CRÍTICO DETECTADO")
                
                # Mostrar algunas celdas
                if 'detalles' in corr and corr['detalles']:
                    print(f"   Primeras celdas:")
                    for i, detalle in enumerate(corr['detalles'][:3]):
                        celda = detalle.get('celda_detectada', 'N/A')
                        tipo = detalle.get('tipo_correlacion', 'N/A')
                        print(f"     {i+1}. Celda: {celda} ({tipo})")
            
            # Buscar específicamente la conexión crítica
            critical_found = False
            for corr in correlations:
                if corr['numero_celular'] == '3104277553':
                    print(f"\n🔍 VERIFICACIÓN NÚMERO CRÍTICO 3104277553:")
                    print(f"   ✅ Encontrado con {corr['total_coincidencias']} coincidencias")
                    critical_found = True
                    break
            
            if not critical_found:
                print(f"\n⚠️ NÚMERO CRÍTICO 3104277553 NO ENCONTRADO EN RESULTADOS")
                
            # Buscar 3224274851
            receptor_found = False
            for corr in correlations:
                if corr['numero_celular'] == '3224274851':
                    print(f"\n🔍 VERIFICACIÓN NÚMERO RECEPTOR 3224274851:")
                    print(f"   ✅ Encontrado con {corr['total_coincidencias']} coincidencias")
                    receptor_found = True
                    break
            
            if not receptor_found:
                print(f"\n⚠️ NÚMERO RECEPTOR 3224274851 NO ENCONTRADO EN RESULTADOS")
        
        else:
            print(f"\n❌ NO SE ENCONTRARON CORRELACIONES")
            print(f"Posibles causas:")
            print(f"  - Los números no están en el período especificado")
            print(f"  - El algoritmo tiene problemas de detección")
            print(f"  - Los datos HUNTER simulados no coinciden")
        
        # Verificar datos reales en BD
        print(f"\n" + "="*50)
        print("VERIFICACIÓN DIRECTA EN BD")
        print("="*50)
        
        import sqlite3
        conn = sqlite3.connect('kronos.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT numero_origen, numero_destino, fecha_hora_llamada, 
                   celda_origen, celda_destino
            FROM operator_call_data
            WHERE (numero_origen IN ('3104277553', '3224274851') OR 
                   numero_destino IN ('3104277553', '3224274851'))
              AND fecha_hora_llamada >= '2024-08-12 20:00:00'
              AND fecha_hora_llamada <= '2024-08-13 02:00:00'
            ORDER BY fecha_hora_llamada
        """)
        
        real_data = cursor.fetchall()
        
        if real_data:
            print(f"✅ Datos reales encontrados: {len(real_data)} registros")
            for i, record in enumerate(real_data):
                print(f"  {i+1}. {record[0]} -> {record[1]} | {record[2]} | Celdas: {record[3]}->{record[4]}")
        else:
            print(f"❌ No hay datos reales en el período especificado")
        
        conn.close()
        
        # Guardar reporte
        report = {
            'timestamp': datetime.now().isoformat(),
            'test_type': 'manual_correlation',
            'period': '2024-08-12 20:00:00 a 2024-08-13 02:00:00',
            'hunter_numbers': hunter_numbers,
            'results': results,
            'real_data_found': len(real_data) if real_data else 0,
            'correlations_found': len(correlations) if correlations else 0
        }
        
        report_file = f"test_correlacion_manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\nReporte guardado: {report_file}")
        
    except Exception as e:
        print(f"ERROR en test manual: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_correlation_manual()