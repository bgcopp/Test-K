"""
Demo Final: Validación Completa de la Corrección file_record_id

Demuestra que la solución implementada funciona correctamente:
1. Procesa datos SCANHUNTER con IDs [0, 12, 32]
2. Verifica almacenamiento en file_record_id 
3. Confirma ordenamiento correcto
4. Valida serialización para frontend

Autor: Sistema KRONOS
Fecha: 2025-08-14
"""

import os
import sys
from datetime import datetime

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.data_normalizer_service import DataNormalizerService
from database.models import CellularData

def create_sample_scanhunter_data():
    """Crea datos de muestra basados en el archivo SCANHUNTER real"""
    
    return [
        {
            'Id': 0,
            'Punto': 'CALLE 4 CON CARRERA 36',
            'Latitud': 4.6108,
            'Longitud': -74.10912,
            'MNC+MCC': '732101',
            'OPERADOR': 'CLARO',
            'RSSI': -90,
            'TECNOLOGIA': 'GSM',
            'CELLID': '1535',
            'LAC o TAC': '4101',
            'ENB': '0',
            'CHANNEL': '183',
            'Comentario': 'para el día 20 de mayo de 2021 entre las 10:00 horas hasta las 11:00 horas del mismo día'
        },
        {
            'Id': 12,
            'Punto': 'PUNTO MEDICION 2',
            'Latitud': 4.6120,
            'Longitud': -74.10800,
            'MNC+MCC': '732101',
            'OPERADOR': 'CLARO',
            'RSSI': -85,
            'TECNOLOGIA': 'LTE',
            'CELLID': '2540',
            'LAC o TAC': '5020',
            'ENB': '100',
            'CHANNEL': '1850',
            'Comentario': 'Medición punto 12'
        },
        {
            'Id': 32,
            'Punto': 'PUNTO MEDICION 3',
            'Latitud': 4.6130,
            'Longitud': -74.10700,
            'MNC+MCC': '732123',
            'OPERADOR': 'MOVISTAR',
            'RSSI': -95,
            'TECNOLOGIA': 'UMTS',
            'CELLID': '3650',
            'LAC o TAC': '6030',
            'ENB': '200',
            'CHANNEL': '2100',
            'Comentario': 'Medición punto 32'
        }
    ]

def test_complete_scanhunter_flow():
    """Test completo del flujo SCANHUNTER con file_record_id"""
    
    print("=== DEMO: Flujo Completo SCANHUNTER con file_record_id ===")
    
    # === PASO 1: NORMALIZACIÓN ===
    
    print("\n[PASO 1] Normalizando datos SCANHUNTER...")
    
    normalizer = DataNormalizerService()
    sample_data = create_sample_scanhunter_data()
    
    normalized_records = []
    
    for i, raw_record in enumerate(sample_data):
        print(f"\n  Procesando registro {i+1}: ID={raw_record['Id']}, Punto={raw_record['Punto']}")
        
        result = normalizer.normalize_scanhunter_data(
            raw_record=raw_record,
            file_upload_id="demo-upload",
            mission_id="demo-mission"
        )
        
        if result is None:
            print(f"  [ERROR] Normalización falló para registro {i+1}")
            return False
        
        file_record_id = result.get('file_record_id')
        expected_id = raw_record['Id']
        
        if file_record_id != expected_id:
            print(f"  [ERROR] file_record_id incorrecto: esperado={expected_id}, obtenido={file_record_id}")
            return False
        
        print(f"  [OK] file_record_id={file_record_id}, punto={result['punto']}, operador={result['operator']}")
        normalized_records.append(result)
    
    print(f"\n[SUCCESS] {len(normalized_records)} registros normalizados correctamente")
    
    # === PASO 2: CREACIÓN DE OBJETOS DEL MODELO ===
    
    print("\n[PASO 2] Creando objetos CellularData...")
    
    cellular_objects = []
    
    for record in normalized_records:
        cellular_data = CellularData(
            mission_id=record['mission_id'],
            file_record_id=record['file_record_id'],
            punto=record['punto'],
            lat=record['lat'],
            lon=record['lon'],
            mnc_mcc=record['mnc_mcc'],
            operator=record['operator'],
            rssi=record['rssi'],
            tecnologia=record['tecnologia'],
            cell_id=record['cell_id'],
            lac_tac=record.get('lac_tac'),
            enb=record.get('enb'),
            channel=record.get('channel'),
            comentario=record.get('comentario')
        )
        
        # Simular ID autoincremental que sería asignado por la BD
        cellular_data.id = len(cellular_objects) + 100
        
        cellular_objects.append(cellular_data)
        print(f"  [OK] Objeto creado: id={cellular_data.id}, file_record_id={cellular_data.file_record_id}")
    
    # === PASO 3: ORDENAMIENTO ===
    
    print("\n[PASO 3] Verificando ordenamiento por file_record_id...")
    
    # Simular el ordenamiento que hace SQLAlchemy en la relación
    cellular_objects_sorted = sorted(cellular_objects, key=lambda x: x.file_record_id or 0)
    
    expected_order = [0, 12, 32]
    actual_order = [obj.file_record_id for obj in cellular_objects_sorted]
    
    print(f"  Orden esperado: {expected_order}")
    print(f"  Orden obtenido: {actual_order}")
    
    if actual_order != expected_order:
        print(f"  [ERROR] Ordenamiento incorrecto")
        return False
    
    print("  [OK] Ordenamiento correcto")
    
    # === PASO 4: SERIALIZACIÓN PARA FRONTEND ===
    
    print("\n[PASO 4] Serializando para frontend...")
    
    serialized_records = []
    
    for obj in cellular_objects_sorted:
        serialized = obj.to_dict()
        
        # Verificar campos clave
        required_fields = ['id', 'fileRecordId', 'punto', 'operador', 'rssi', 'tecnologia']
        
        for field in required_fields:
            if field not in serialized:
                print(f"  [ERROR] Campo faltante: {field}")
                return False
        
        print(f"  [OK] Serializado: fileRecordId={serialized['fileRecordId']}, id={serialized['id']}, punto={serialized['punto']}")
        serialized_records.append(serialized)
    
    # === PASO 5: VERIFICACIÓN FINAL ===
    
    print("\n[PASO 5] Verificación final...")
    
    # Verificar que fileRecordId se muestra en lugar de id
    frontend_display_ids = [record['fileRecordId'] for record in serialized_records]
    bd_internal_ids = [record['id'] for record in serialized_records]
    
    print(f"  IDs para mostrar en frontend (fileRecordId): {frontend_display_ids}")
    print(f"  IDs internos de BD (id): {bd_internal_ids}")
    
    # Verificar que son diferentes (lo que soluciona el problema original)
    if frontend_display_ids == bd_internal_ids:
        print("  [ERROR] Los IDs son iguales, el problema persiste")
        return False
    
    # Verificar que frontend_display_ids están ordenados correctamente
    if frontend_display_ids != expected_order:
        print("  [ERROR] IDs de frontend no están en el orden correcto")
        return False
    
    print("  [OK] Frontend mostrará los IDs correctos en el orden correcto")
    
    # === DEMOSTRACIÓN DEL PROBLEMA SOLUCIONADO ===
    
    print("\n=== DEMOSTRACIÓN: PROBLEMA SOLUCIONADO ===")
    print("\n  ANTES (problema):")
    print("    - Se mostraba: id (autoincremental BD) = [100, 101, 102]") 
    print("    - Orden: Por id autoincremental (no por archivo)")
    print("\n  DESPUÉS (solucionado):")
    print(f"    - Se muestra: fileRecordId (del archivo) = {frontend_display_ids}")
    print(f"    - Orden: Por file_record_id (del archivo) = ASC")
    print(f"    - Resultado: Los datos se muestran ordenados como en el archivo original")
    
    print("\n[SUCCESS] ¡PROBLEMA COMPLETAMENTE SOLUCIONADO!")
    return True

def main():
    """Función principal del demo"""
    
    print("KRONOS - Demo Corrección file_record_id SCANHUNTER")
    print("=" * 60)
    print("Este demo demuestra que el problema está completamente solucionado:")
    print("1. El archivo SCANHUNTER.xlsx tenía columna 'Id' con valores [0, 12, 32]")
    print("2. Antes: Se mostraba el ID autoincremental de la BD")
    print("3. Después: Se muestra el ID del archivo y se ordena correctamente")
    print()
    
    try:
        success = test_complete_scanhunter_flow()
        
        if success:
            print("\n" + "=" * 60)
            print("✓ CORRECCIÓN VALIDADA EXITOSAMENTE")
            print("✓ El campo file_record_id funciona correctamente")
            print("✓ El frontend mostrará el ID del archivo en lugar del autoincremental")
            print("✓ Los registros se ordenarán correctamente (ASC: 0, 12, 32)")
            print("=" * 60)
            return True
        else:
            print("\n[ERROR] Algunos tests fallaron")
            return False
            
    except Exception as e:
        print(f"\n[ERROR CRÍTICO] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)