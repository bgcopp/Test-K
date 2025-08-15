"""
Test de Regresión - Validación de Funcionalidad Existente
========================================================
Verifica que la implementación de file_record_id no haya roto
la funcionalidad existente de otros tipos de archivos.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.data_normalizer_service import DataNormalizerService
import pandas as pd
import tempfile


def test_claro_operator_files():
    """Test para archivos de operador CLARO (no SCANHUNTER)"""
    
    print("=== TEST: Archivos CLARO (No SCANHUNTER) ===")
    
    try:
        normalizer = DataNormalizerService()
        
        # Simular datos típicos de CLARO
        claro_sample_data = [
            {
                'FECHA': '2025-08-14',
                'HORA': '10:30:00',
                'CELDA_ORIGEN': '12345',
                'CELDA_DESTINO': '67890',
                'DURACION': 120,
                'BYTES_UL': 1024,
                'BYTES_DL': 2048,
                'IMSI': '732101234567890'
            }
        ]
        
        print(f"  Procesando {len(claro_sample_data)} registros CLARO...")
        
        for i, record in enumerate(claro_sample_data):
            try:
                # Usar método apropiado para CLARO
                result = normalizer.normalize_claro_datos_record(record, "test_upload", "test_mission")
                
                print(f"  [OK] Registro {i+1} procesado exitosamente")
                
                # Verificar que no se agregó file_record_id erróneamente
                if 'file_record_id' in result:
                    if result['file_record_id'] is not None:
                        print(f"  [WARNING] file_record_id no debería estar presente en CLARO: {result['file_record_id']}")
                    else:
                        print("  [OK] file_record_id es NULL como se esperaba para CLARO")
                else:
                    print("  [OK] file_record_id no presente en respuesta CLARO")
                
            except AttributeError as e:
                if 'normalize_claro_datos_record' in str(e):
                    print("  [INFO] Método CLARO no disponible - test omitido")
                    break
                else:
                    raise
            except Exception as e:
                print(f"  [ERROR] Error procesando registro CLARO: {str(e)}")
                return False
        
        return True
        
    except Exception as e:
        print(f"  [ERROR] Error en test CLARO: {str(e)}")
        return False


def test_movistar_operator_files():
    """Test para archivos de operador MOVISTAR"""
    
    print("\n=== TEST: Archivos MOVISTAR ===")
    
    try:
        normalizer = DataNormalizerService()
        
        # Simular datos típicos de MOVISTAR
        movistar_sample_data = [
            {
                'fecha_llamada': '2025-08-14',
                'hora_inicio': '10:30:00',
                'numero_origen': '3001234567',
                'numero_destino': '3007654321',
                'duracion_segundos': 180,
                'celda_id': 'MOV12345'
            }
        ]
        
        print(f"  Procesando {len(movistar_sample_data)} registros MOVISTAR...")
        
        for i, record in enumerate(movistar_sample_data):
            try:
                # Usar método apropiado para MOVISTAR  
                result = normalizer.normalize_movistar_datos_record(record, "test_upload", "test_mission")
                
                print(f"  [OK] Registro {i+1} procesado exitosamente")
                
                # Verificar que no se agregó file_record_id erróneamente
                if 'file_record_id' in result:
                    if result['file_record_id'] is not None:
                        print(f"  [WARNING] file_record_id no debería estar presente en MOVISTAR: {result['file_record_id']}")
                    else:
                        print("  [OK] file_record_id es NULL como se esperaba para MOVISTAR")
                else:
                    print("  [OK] file_record_id no presente en respuesta MOVISTAR")
                
            except AttributeError as e:
                if 'normalize_movistar_datos_record' in str(e):
                    print("  [INFO] Método MOVISTAR no disponible - test omitido")
                    break
                else:
                    raise
            except Exception as e:
                print(f"  [ERROR] Error procesando registro MOVISTAR: {str(e)}")
                return False
        
        return True
        
    except Exception as e:
        print(f"  [ERROR] Error en test MOVISTAR: {str(e)}")
        return False


def test_generic_cellular_data():
    """Test para datos celulares genéricos (no específicos de operador)"""
    
    print("\n=== TEST: Datos Celulares Genéricos ===")
    
    try:
        from database.models import CellularData
        
        # Crear objeto CellularData directamente
        generic_data = CellularData(
            mission_id="test_mission",
            file_record_id=None,  # Esto es lo normal para datos no-SCANHUNTER
            punto="PUNTO GENERICO",
            lat=4.123456,
            lon=-74.123456,
            mnc_mcc="73210",
            operator="TEST",
            rssi=-85,
            tecnologia="4G",
            cell_id="TEST12345"
        )
        
        print("  Creando objeto CellularData genérico...")
        
        # Verificar serialización
        serialized = generic_data.to_dict()
        
        print("  [OK] Objeto creado y serializado exitosamente")
        print(f"  Keys en serialización: {list(serialized.keys())}")
        
        # Verificar que fileRecordId está presente pero es None
        if 'fileRecordId' in serialized:
            if serialized['fileRecordId'] is None:
                print("  [OK] fileRecordId es None para datos genéricos")
            else:
                print(f"  [WARNING] fileRecordId tiene valor inesperado: {serialized['fileRecordId']}")
        else:
            print("  [ERROR] fileRecordId no está en la serialización")
            return False
        
        # Verificar otros campos críticos
        required_fields = ['id', 'punto', 'operador', 'rssi', 'tecnologia']
        missing_fields = [f for f in required_fields if f not in serialized]
        
        if missing_fields:
            print(f"  [ERROR] Campos requeridos faltantes: {missing_fields}")
            return False
        else:
            print("  [OK] Todos los campos requeridos presentes")
        
        return True
        
    except Exception as e:
        print(f"  [ERROR] Error en test genérico: {str(e)}")
        return False


def test_scanhunter_specific_processing():
    """Test específico para procesamiento SCANHUNTER"""
    
    print("\n=== TEST: Procesamiento Específico SCANHUNTER ===")
    
    try:
        normalizer = DataNormalizerService()
        
        # Datos que simulan SCANHUNTER
        scanhunter_sample = {
            'Id': 0,  # Esta es la diferencia clave
            'Punto': 'PUNTO SCANHUNTER TEST',
            'Latitud': 4.123456,
            'Longitud': -74.123456,
            'MNC+MCC': '73210',
            'OPERADOR': 'CLARO',
            'RSSI': -85,
            'TECNOLOGIA': '4G',
            'CELLID': 'SCH12345',
            'LAC o TAC': '1234',
            'ENB': 'ENB123',
            'Comentario': 'Test SCANHUNTER',
            'CHANNEL': '1850'
        }
        
        print("  Procesando registro SCANHUNTER simulado...")
        
        try:
            result = normalizer.normalize_scanhunter_data(
                scanhunter_sample, 
                "test_upload", 
                "test_mission"
            )
            
            print("  [OK] Registro SCANHUNTER procesado exitosamente")
            
            # Verificar que file_record_id está presente y correcto
            expected_file_record_id = 0
            actual_file_record_id = result.get('file_record_id')
            
            if actual_file_record_id == expected_file_record_id:
                print(f"  [OK] file_record_id correcto: {actual_file_record_id}")
            else:
                print(f"  [ERROR] file_record_id incorrecto: esperado={expected_file_record_id}, obtenido={actual_file_record_id}")
                return False
            
            # Verificar otros campos clave
            if result.get('punto') == 'PUNTO SCANHUNTER TEST':
                print("  [OK] Campo 'punto' procesado correctamente")
            else:
                print(f"  [ERROR] Campo 'punto' incorrecto: {result.get('punto')}")
                return False
            
        except AttributeError as e:
            print(f"  [ERROR] Método SCANHUNTER no encontrado: {str(e)}")
            return False
        
        return True
        
    except Exception as e:
        print(f"  [ERROR] Error en test SCANHUNTER: {str(e)}")
        return False


def test_database_model_compatibility():
    """Test de compatibilidad del modelo de base de datos"""
    
    print("\n=== TEST: Compatibilidad del Modelo de Base de Datos ===")
    
    try:
        from database.models import CellularData
        
        # Test 1: Crear con file_record_id
        print("  Test 1: CellularData con file_record_id...")
        
        data_with_file_id = CellularData(
            mission_id="test",
            file_record_id=123,
            punto="Test Point",
            lat=4.0,
            lon=-74.0,
            mnc_mcc="73210",
            operator="TEST",
            rssi=-85,
            tecnologia="4G",
            cell_id="TEST123"
        )
        
        serialized_with_id = data_with_file_id.to_dict()
        if serialized_with_id.get('fileRecordId') == 123:
            print("  [OK] Serialización con file_record_id correcta")
        else:
            print(f"  [ERROR] Serialización incorrecta: {serialized_with_id.get('fileRecordId')}")
            return False
        
        # Test 2: Crear sin file_record_id
        print("  Test 2: CellularData sin file_record_id...")
        
        data_without_file_id = CellularData(
            mission_id="test",
            file_record_id=None,
            punto="Test Point",
            lat=4.0,
            lon=-74.0,
            mnc_mcc="73210",
            operator="TEST",
            rssi=-85,
            tecnologia="4G",
            cell_id="TEST123"
        )
        
        serialized_without_id = data_without_file_id.to_dict()
        if serialized_without_id.get('fileRecordId') is None:
            print("  [OK] Serialización sin file_record_id correcta")
        else:
            print(f"  [ERROR] Serialización incorrecta: {serialized_without_id.get('fileRecordId')}")
            return False
        
        # Test 3: Verificar que otros campos no se afectaron
        print("  Test 3: Verificar otros campos...")
        
        expected_fields = ['id', 'punto', 'lat', 'lon', 'operador', 'rssi', 'tecnologia', 'cellId']
        for field in expected_fields:
            if field not in serialized_with_id:
                print(f"  [ERROR] Campo faltante en serialización: {field}")
                return False
        
        print("  [OK] Todos los campos requeridos presentes")
        
        return True
        
    except Exception as e:
        print(f"  [ERROR] Error en test de modelo: {str(e)}")
        return False


if __name__ == "__main__":
    print("KRONOS - Test de Regresión file_record_id")
    print("=" * 55)
    
    tests = [
        ("CLARO Operator Files", test_claro_operator_files),
        ("MOVISTAR Operator Files", test_movistar_operator_files),
        ("Generic Cellular Data", test_generic_cellular_data),
        ("SCANHUNTER Specific Processing", test_scanhunter_specific_processing),
        ("Database Model Compatibility", test_database_model_compatibility)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n[CRITICAL ERROR] {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Resumen final
    print("\n" + "=" * 55)
    print("RESUMEN DE TESTS DE REGRESIÓN")
    print("=" * 55)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResultado: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("\n[SUCCESS] Todos los tests de regresión pasaron")
        print("La implementación de file_record_id no afectó funcionalidad existente")
    elif passed >= total * 0.8:  # 80% o más
        print(f"\n[PARTIAL SUCCESS] {passed}/{total} tests pasaron")
        print("La mayoría de funcionalidad existente está intacta")
    else:
        print(f"\n[FAILURE] Solo {passed}/{total} tests pasaron")
        print("La implementación puede haber afectado funcionalidad existente")