"""
Verificacion final simple sin caracteres Unicode
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.correlation_analysis_service import CorrelationAnalysisService

def verificacion_final():
    print("\n" + "="*60)
    print("VERIFICACION FINAL SIMPLE")
    print("="*60)
    
    service = CorrelationAnalysisService()
    
    result = service.analyze_correlation(
        start_date='2021-05-20 10:00:00',
        end_date='2021-05-20 14:30:00',
        min_coincidences=1,
        mission_id='mission_MPFRBNsb'
    )
    
    target_numbers = ['3143534707', '3224274851', '3208611034', '3214161903', '3102715509']
    correlations = result.get('correlations', [])
    
    print(f"Total correlaciones: {len(correlations)}")
    print(f"Numeros objetivo a buscar: {len(target_numbers)}")
    print()
    
    found_count = 0
    for target in target_numbers:
        found = False
        for corr in correlations:
            if corr.get('numero_celular') == target:
                found = True
                found_count += 1
                print(f"[OK] {target}: {corr['total_coincidencias']} coincidencias")
                break
        
        if not found:
            print(f"[FALTA] {target}")
    
    print()
    print(f"RESULTADO FINAL: {found_count}/{len(target_numbers)} numeros encontrados")
    
    if found_count == len(target_numbers):
        print("EXITO TOTAL - TODOS LOS NUMEROS DETECTADOS")
        return True
    else:
        print("PROBLEMA - FALTAN NUMEROS")
        return False

if __name__ == "__main__":
    success = verificacion_final()
    if success:
        print("\nREADY FOR PRODUCTION")
    else:
        print("\nREQUIERE CORRECCION")