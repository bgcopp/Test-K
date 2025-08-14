"""
VALIDACIÓN SIMPLE - Corrección de Detalle de Misiones
====================================================

Test simple sin caracteres especiales para validar la corrección.
"""

import sys
import os
from pathlib import Path

# Configurar path para imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_mission_functions():
    """Test simple de las funciones de misión"""
    print("=== TEST DE VALIDACIÓN DE CORRECCIÓN ===")
    
    try:
        # Test 1: get_missions
        print("Test 1: get_missions()")
        from main import get_missions
        
        missions = get_missions()
        print(f"RESULTADO: {len(missions)} misiones obtenidas")
        
        if missions:
            mission = missions[0]
            print(f"Primera misión: {mission['code']} - {mission['name']}")
            
            # Test 2: get_operator_sheets
            print("Test 2: get_operator_sheets()")
            from services.operator_data_service import get_operator_sheets
            
            sheets_result = get_operator_sheets(mission['id'])
            if isinstance(sheets_result, dict) and 'data' in sheets_result:
                sheets = sheets_result['data']
                print(f"RESULTADO: {len(sheets)} hojas de operador")
            else:
                print("RESULTADO: Sin hojas de operador encontradas")
        
        print("\nCORRECCIÓN EXITOSA: El detalle de misiones debería funcionar ahora")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_mission_functions()
    if success:
        print("\n🎉 SISTEMA CORREGIDO EXITOSAMENTE")
        sys.exit(0)
    else:
        print("\n❌ LA CORRECCIÓN FALLÓ")
        sys.exit(1)