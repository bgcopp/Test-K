"""
VALIDACIÓN L2: Confirmar que los números objetivo aparecerán con los cambios
=============================================================================
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.correlation_analysis_service import CorrelationAnalysisService

def validate_fix():
    print("=" * 80)
    print("VALIDACION L2: CONFIRMACION DE SOLUCION")
    print("=" * 80)
    
    service = CorrelationAnalysisService()
    
    # Configuración ORIGINAL (problema)
    print("\n[TEST 1] CONFIGURACION ORIGINAL (10:00 - 14:20, min=2):")
    result1 = service.analyze_correlation(
        mission_id='mission_MPFRBNsb',
        start_date='2021-05-20 10:00:00',
        end_date='2021-05-20 14:20:00',
        min_coincidences=2
    )
    
    if result1['success']:
        data1 = result1['data']
        targets1 = [d for d in data1 if d['numero_celular'] in ['3224274851', '3208611034', '3143534707', '3102715509', '3214161903']]
        print(f"  - Total resultados: {len(data1)}")
        print(f"  - Numeros objetivo encontrados: {len(targets1)}")
        if targets1:
            for t in targets1:
                print(f"    * {t['numero_celular']}: {t['total_coincidencias']} coincidencias")
    
    # Configuración CORREGIDA 1 (min=1)
    print("\n[TEST 2] CONFIGURACION CORREGIDA 1 (10:00 - 14:20, min=1):")
    result2 = service.analyze_correlation(
        mission_id='mission_MPFRBNsb',
        start_date='2021-05-20 10:00:00',
        end_date='2021-05-20 14:20:00',
        min_coincidences=1  # CAMBIADO
    )
    
    if result2['success']:
        data2 = result2['data']
        targets2 = [d for d in data2 if d['numero_celular'] in ['3224274851', '3208611034', '3143534707', '3102715509', '3214161903']]
        print(f"  - Total resultados: {len(data2)}")
        print(f"  - Numeros objetivo encontrados: {len(targets2)}")
        if targets2:
            for t in targets2:
                print(f"    * {t['numero_celular']}: {t['total_coincidencias']} coincidencias")
    
    # Configuración CORREGIDA 2 (extender hasta 14:30)
    print("\n[TEST 3] CONFIGURACION CORREGIDA 2 (10:00 - 14:30, min=1):")
    result3 = service.analyze_correlation(
        mission_id='mission_MPFRBNsb',
        start_date='2021-05-20 10:00:00',
        end_date='2021-05-20 14:30:00',  # EXTENDIDO
        min_coincidences=1
    )
    
    if result3['success']:
        data3 = result3['data']
        targets3 = [d for d in data3 if d['numero_celular'] in ['3224274851', '3208611034', '3143534707', '3102715509', '3214161903']]
        print(f"  - Total resultados: {len(data3)}")
        print(f"  - Numeros objetivo encontrados: {len(targets3)}")
        if targets3:
            for t in targets3:
                print(f"    * {t['numero_celular']}: {t['total_coincidencias']} coincidencias - Celdas: {t['celdas_coincidentes']}")
    
    # RESUMEN
    print("\n" + "=" * 80)
    print("RESUMEN DE VALIDACION:")
    print("=" * 80)
    print(f"\nCONFIGURACION ORIGINAL (problema):")
    print(f"  - Numeros objetivo detectados: {len(targets1) if result1['success'] else 0}/5")
    
    print(f"\nCONFIGURACION CORREGIDA 1 (min=1):")
    print(f"  - Numeros objetivo detectados: {len(targets2) if result2['success'] else 0}/5")
    
    print(f"\nCONFIGURACION CORREGIDA 2 (14:30 + min=1):")
    print(f"  - Numeros objetivo detectados: {len(targets3) if result3['success'] else 0}/5")
    
    if result3['success'] and len(targets3) > 0:
        print(f"\n[OK] SOLUCION CONFIRMADA: Los numeros objetivo APARECERAN en la UI")
        print(f"     Cambios necesarios:")
        print(f"     1. minCoincidences = 1 (ya aplicado)")
        print(f"     2. Extender periodo hasta 14:30 (ya aplicado)")
    else:
        print(f"\n[WARNING] Los cambios NO son suficientes, se requiere investigacion adicional")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    validate_fix()