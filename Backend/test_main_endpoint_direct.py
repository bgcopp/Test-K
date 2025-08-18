#!/usr/bin/env python3
"""
Test directo del endpoint analyze_correlation desde main.py
Simula el llamado exacto que haría el frontend
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Configurar path para imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Importar main para inicialización
import main

def test_analyze_correlation_endpoint():
    """Test directo del endpoint analyze_correlation"""
    print("="*60)
    print("TEST DIRECTO ENDPOINT ANALYZE_CORRELATION")
    print("="*60)
    
    try:
        # Inicializar backend
        print("Inicializando backend...")
        main.initialize_backend()
        print("Backend inicializado correctamente")
        
        # Parámetros exactos que usará la UI
        mission_id = "mission_MPFRBNsb"
        start_date = "2021-05-20T10:00"  # Formato datetime-local del frontend
        end_date = "2021-05-20T14:30"    # Formato datetime-local del frontend
        min_coincidences = 1
        
        print(f"\nParametros del test:")
        print(f"  Mission ID: {mission_id}")
        print(f"  Periodo: {start_date} a {end_date}")
        print(f"  Min coincidencias: {min_coincidences}")
        
        # Llamar al endpoint directamente como lo haría Eel
        print(f"\nEjecutando analyze_correlation...")
        result = main.analyze_correlation(
            mission_id=mission_id,
            start_date=start_date,
            end_date=end_date,
            min_coincidences=min_coincidences
        )
        
        # Verificar resultado
        if not isinstance(result, dict):
            print(f"ERROR: Resultado no es diccionario: {type(result)}")
            return False
        
        print(f"\nResultado obtenido:")
        print(f"  Success: {result.get('success')}")
        
        if not result.get('success'):
            error = result.get('error', 'Error desconocido')
            print(f"  Error: {error}")
            return False
        
        # Analizar datos
        data = result.get('data', [])
        print(f"  Numeros encontrados: {len(data)}")
        
        if not data:
            print("ERROR: No se encontraron datos")
            return False
        
        # Verificar números objetivo específicos
        target_numbers = {
            '3143534707': 3,
            '3224274851': 2,
            '3208611034': 2,
            '3214161903': 1,
            '3102715509': 1
        }
        
        found_targets = {}
        print(f"\nVerificando numeros objetivo:")
        
        for item in data:
            numero = item.get('numero_celular', '')
            coincidencias = item.get('total_coincidencias', 0)
            
            if numero in target_numbers:
                found_targets[numero] = coincidencias
                expected = target_numbers[numero]
                status = "OK" if coincidencias >= expected else "WARN"
                print(f"  {status} {numero}: {coincidencias} coincidencias (esperado: {expected})")
        
        # Números faltantes
        missing = set(target_numbers.keys()) - set(found_targets.keys())
        if missing:
            print(f"\nNumeros objetivo faltantes:")
            for numero in missing:
                print(f"  MISSING {numero}: esperado {target_numbers[numero]} coincidencias")
        
        # Verificar formato
        if data:
            sample = data[0]
            required_fields = ['numero_celular', 'total_coincidencias', 'operadores']
            print(f"\nVerificacion de formato:")
            for field in required_fields:
                status = "OK" if field in sample else "MISSING"
                print(f"  {status} Campo '{field}'")
            
            # Verificar que no tenga prefijo 57
            numero = sample.get('numero_celular', '')
            if numero.startswith('57'):
                print(f"  WARN: Numero con prefijo 57: {numero}")
            else:
                print(f"  OK: Numero sin prefijo 57: {numero}")
        
        # Guardar resultado
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"main_endpoint_test_result_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\nResultado guardado en: {output_file}")
        
        # Resumen
        total_found = len(found_targets)
        total_expected = len(target_numbers)
        success = total_found == total_expected
        
        print(f"\nRESUMEN:")
        print(f"  Numeros objetivo encontrados: {total_found}/{total_expected}")
        print(f"  Estado: {'EXITOSO' if success else 'PARCIAL'}")
        
        return success
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        print(f"Traceback:\n{traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_analyze_correlation_endpoint()
    print("="*60)
    if success:
        print("TEST COMPLETADO EXITOSAMENTE")
        print("El backend retorna correctamente los numeros objetivo")
    else:
        print("TEST FALLO")
        print("Hay problemas en el backend que requieren correccion")
    print("="*60)
    
    sys.exit(0 if success else 1)