"""
Test simple final para verificar numeros objetivo
Sin caracteres Unicode para evitar problemas de encoding
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.correlation_analysis_service import CorrelationAnalysisService
import sqlite3

def test_simple():
    print("\n" + "="*70)
    print("TEST SIMPLE FINAL - NUMEROS OBJETIVO")
    print("="*70)
    
    target_numbers = [
        '3224274851', '3208611034', '3104277553', 
        '3102715509', '3143534707', '3214161903'
    ]
    
    print(f"Numeros objetivo: {', '.join(target_numbers)}")
    
    # Verificar datos en BD
    try:
        conn = sqlite3.connect('kronos.db')
        cursor = conn.cursor()
        
        print(f"\nDatos disponibles en BD:")
        for number in target_numbers:
            cursor.execute("""
                SELECT COUNT(*) FROM operator_call_data
                WHERE numero_origen = ? OR numero_destino = ?
            """, (number, number))
            
            count = cursor.fetchone()[0]
            status = "OK" if count > 0 else "FALTA"
            print(f"  {number}: {count} registros [{status}]")
        
        conn.close()
        
    except Exception as e:
        print(f"ERROR BD: {e}")
        return
    
    # Ejecutar correlacion
    try:
        print(f"\nEjecutando algoritmo de correlacion...")
        
        service = CorrelationAnalysisService()
        
        results = service.analyze_correlation(
            start_date='2021-05-20 10:00:00',
            end_date='2021-05-20 15:00:00',
            min_coincidences=1,
            mission_id='mission_MPFRBNsb'
        )
        
        if 'error' in results:
            print(f"ERROR: {results['error']}")
            return
        
        correlations = results.get('correlations', [])
        
        print(f"\nResultados de correlacion:")
        print(f"Total numeros correlacionados: {len(correlations)}")
        
        # Verificar numeros objetivo
        found_targets = []
        
        for number in target_numbers:
            found = False
            for corr in correlations:
                if corr['numero_celular'] == number:
                    found_targets.append(number)
                    found = True
                    print(f"  [ENCONTRADO] {number}: {corr['total_coincidencias']} coincidencias")
                    break
            
            if not found:
                print(f"  [FALTA] {number}: NO encontrado")
        
        print(f"\n" + "="*50)
        print("RESUMEN")
        print("="*50)
        print(f"Numeros encontrados: {len(found_targets)}/{len(target_numbers)}")
        print(f"Lista encontrados: {', '.join(found_targets) if found_targets else 'Ninguno'}")
        
        success_rate = (len(found_targets) / len(target_numbers)) * 100
        print(f"Tasa de exito: {success_rate:.1f}%")
        
        if len(found_targets) == len(target_numbers):
            print(f"\n*** EXITO TOTAL ***")
        elif len(found_targets) > 0:
            print(f"\n*** EXITO PARCIAL ***")
        else:
            print(f"\n*** FALLA TOTAL ***")
        
    except Exception as e:
        print(f"ERROR algoritmo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple()