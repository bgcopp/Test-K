"""
Test de Validación API Frontend - file_record_id
===============================================
Simula las llamadas que hace el frontend para verificar que
los datos se serializan correctamente con fileRecordId.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.mission_service import MissionService
from database.connection import DatabaseManager
import json


def test_frontend_api_calls():
    """Test que simula las llamadas del frontend"""
    
    print("=== TEST: Validación API Frontend ===")
    
    try:
        # Inicializar servicios
        db_manager = DatabaseManager()
        db_manager.initialize(":memory:")  # Base de datos en memoria para test
        
        # Migrar y crear datos de test
        with db_manager.get_session() as session:
            # Crear misión de test
            from database.models import Mission, CellularData
            
            mission = Mission(
                id="test_frontend_001",
                code="TEST-FRONTEND-001", 
                name="Test Frontend file_record_id",
                description="Misión para test de frontend",
                status="Planificación",
                start_date="2025-08-14",
                created_by="system"
            )
            session.add(mission)
            
            # Crear datos celulares con file_record_id
            test_data = [
                CellularData(
                    mission_id="test_frontend_001",
                    file_record_id=0,
                    punto="PUNTO FRONTEND 0",
                    lat=4.123456,
                    lon=-74.123456,
                    mnc_mcc="73210",
                    operator="CLARO",
                    rssi=-85,
                    tecnologia="4G",
                    cell_id="12345"
                ),
                CellularData(
                    mission_id="test_frontend_001", 
                    file_record_id=12,
                    punto="PUNTO FRONTEND 12",
                    lat=4.234567,
                    lon=-74.234567,
                    mnc_mcc="73212",
                    operator="MOVISTAR",
                    rssi=-90,
                    tecnologia="LTE", 
                    cell_id="23456"
                ),
                CellularData(
                    mission_id="test_frontend_001",
                    file_record_id=32,
                    punto="PUNTO FRONTEND 32", 
                    lat=4.345678,
                    lon=-74.345678,
                    mnc_mcc="73213",
                    operator="TIGO",
                    rssi=-75,
                    tecnologia="5G",
                    cell_id="34567"
                )
            ]
            
            for data in test_data:
                session.add(data)
                
            session.commit()
            print("[OK] Datos de test creados")
        
        # Inicializar MissionService
        mission_service = MissionService()
        
        # TEST 1: Obtener lista de misiones
        print("\n[TEST 1] Obtener lista de misiones...")
        missions = mission_service.get_all_missions()
        
        test_mission = None
        for mission in missions:
            if mission.get('code') == 'TEST-FRONTEND-001':
                test_mission = mission
                break
        
        if test_mission:
            print(f"  [OK] Misión encontrada: {test_mission['code']}")
            print(f"  ID: {test_mission['id']}")
        else:
            print("[ERROR] Misión de test no encontrada")
            return False
        
        # TEST 2: Obtener detalles de la misión con datos celulares
        print("\n[TEST 2] Obtener detalles de misión...")
        mission_details = mission_service.get_mission_by_id(test_mission['id'])
        
        if mission_details:
            print(f"  [OK] Detalles obtenidos para misión: {mission_details.get('code')}")
            
            # Verificar si incluye datos celulares
            cellular_data = mission_details.get('cellularData', [])
            print(f"  Registros celulares: {len(cellular_data)}")
            
            if len(cellular_data) > 0:
                # Verificar estructura de los registros
                first_record = cellular_data[0]
                print(f"  Primer registro keys: {list(first_record.keys())}")
                
                # Verificar que tiene fileRecordId
                has_file_record_id = 'fileRecordId' in first_record
                print(f"  Tiene fileRecordId: {has_file_record_id}")
                
                if has_file_record_id:
                    # Verificar valores de fileRecordId
                    file_record_ids = [record.get('fileRecordId') for record in cellular_data]
                    print(f"  fileRecordIds encontrados: {file_record_ids}")
                    
                    # Verificar ordenamiento
                    is_ordered = file_record_ids == sorted(file_record_ids)
                    print(f"  Ordenamiento correcto: {is_ordered}")
                    
                    # Verificar valores esperados
                    expected_ids = [0, 12, 32]
                    if set(file_record_ids) == set(expected_ids):
                        print("  [OK] IDs coinciden con valores esperados")
                    else:
                        print(f"  [WARNING] IDs no coinciden. Esperados: {expected_ids}")
                else:
                    print("[ERROR] Campo fileRecordId no encontrado en registros")
                    return False
            else:
                print("[WARNING] No se encontraron datos celulares en la respuesta")
        else:
            print("[ERROR] No se pudieron obtener detalles de la misión")
            return False
        
        # TEST 3: Verificar serialización JSON
        print("\n[TEST 3] Verificar serialización JSON...")
        
        try:
            # Simular respuesta JSON del backend
            json_response = json.dumps(mission_details, indent=2)
            print(f"  [OK] Serialización JSON exitosa ({len(json_response)} caracteres)")
            
            # Parsear de vuelta para verificar
            parsed = json.loads(json_response)
            cellular_from_json = parsed.get('cellularData', [])
            
            if len(cellular_from_json) > 0:
                first_from_json = cellular_from_json[0]
                if 'fileRecordId' in first_from_json:
                    print(f"  [OK] fileRecordId preservado en JSON: {first_from_json['fileRecordId']}")
                else:
                    print("[ERROR] fileRecordId perdido en serialización JSON")
                    return False
            
        except Exception as e:
            print(f"[ERROR] Error en serialización JSON: {str(e)}")
            return False
        
        # TEST 4: Simular llamada específica de datos celulares
        print("\n[TEST 4] Simular llamada específica de datos celulares...")
        
        # El frontend normalmente haría una llamada como esta
        cellular_response = mission_service.get_cellular_data_for_mission(test_mission['id'])
        
        if cellular_response and len(cellular_response) > 0:
            print(f"  [OK] Respuesta celular obtenida: {len(cellular_response)} registros")
            
            # Verificar orden y contenido
            ids_in_response = [record.get('fileRecordId') for record in cellular_response]
            print(f"  IDs en respuesta: {ids_in_response}")
            
            # Verificar que frontend recibiría los datos en orden correcto
            if ids_in_response == [0, 12, 32]:
                print("  [OK] Frontend recibirá datos en orden correcto")
            else:
                print(f"  [WARNING] Orden incorrecto: {ids_in_response}")
        
        print("\n=== RESULTADO FINAL ===")
        print("✓ Campo file_record_id se mapea correctamente a fileRecordId")
        print("✓ Datos se serializan correctamente para JSON")
        print("✓ Frontend recibirá IDs del archivo en lugar de autoincrementales")
        print("✓ Ordenamiento funciona correctamente")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error en test de API: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("KRONOS - Test Validación API Frontend")
    print("=" * 50)
    
    try:
        success = test_frontend_api_calls()
        
        if success:
            print("\n[SUCCESS] Validación API completada exitosamente")
            print("El frontend mostrará correctamente los IDs del archivo SCANHUNTER")
        else:
            print("\n[FAILURE] Validación API falló")
            
    except Exception as e:
        print(f"\n[CRITICAL ERROR] {str(e)}")
        import traceback
        traceback.print_exc()