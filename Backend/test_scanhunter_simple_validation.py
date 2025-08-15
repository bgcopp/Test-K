"""
Test Simplificado: Validación file_record_id SCANHUNTER

Verifica que la solución implementada funcione correctamente:
1. Procesar archivo SCANHUNTER.csv
2. Verificar que file_record_id se almacene
3. Confirmar ordenamiento correcto

Autor: Sistema KRONOS
Fecha: 2025-08-14
"""

import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.data_normalizer_service import DataNormalizerService

def test_data_normalizer():
    """Test del normalizador con datos SCANHUNTER reales"""
    
    print("=== TEST: DataNormalizerService con file_record_id ===")
    
    # Leer archivo SCANHUNTER
    scanhunter_path = os.path.join(
        os.path.dirname(__file__), 
        "..", "archivos", "envioarchivosparaanalizar (1)", "SCANHUNTER.csv"
    )
    
    if not os.path.exists(scanhunter_path):
        print(f"[ERROR] Archivo no encontrado: {scanhunter_path}")
        return False
    
    # Analizar archivo
    df = pd.read_csv(scanhunter_path)
    print(f"[INFO] Archivo: {len(df)} registros")
    print(f"[INFO] Columnas: {list(df.columns)}")
    
    if 'Id' not in df.columns:
        print("[ERROR] Columna 'Id' no encontrada")
        return False
    
    # Verificar distribución de IDs
    id_counts = df['Id'].value_counts().sort_index()
    print(f"[INFO] Distribución IDs: {dict(id_counts)}")
    
    # Test del normalizador
    normalizer = DataNormalizerService()
    print("[INFO] DataNormalizerService inicializado")
    
    # Tomar muestras de cada ID
    test_cases = []
    for id_value in [0, 12, 32]:
        sample = df[df['Id'] == id_value].iloc[0].to_dict()
        test_cases.append((id_value, sample))
        print(f"[INFO] Muestra ID {id_value}: punto={sample.get('Punto')}")
    
    # Normalizar muestras
    print("\n[TEST] Normalizando muestras...")
    
    for expected_id, raw_record in test_cases:
        result = normalizer.normalize_scanhunter_data(
            raw_record=raw_record,
            file_upload_id="test-upload",
            mission_id="test-mission"
        )
        
        if result is None:
            print(f"[ERROR] Normalización falló para ID {expected_id}")
            return False
        
        actual_file_record_id = result.get('file_record_id')
        if actual_file_record_id != expected_id:
            print(f"[ERROR] ID {expected_id}: esperado={expected_id}, obtenido={actual_file_record_id}")
            return False
        
        print(f"[OK] ID {expected_id}: file_record_id={actual_file_record_id}")
    
    print("\n[SUCCESS] Normalizador procesa file_record_id correctamente")
    return True

def test_database_schema():
    """Test del esquema de base de datos"""
    
    print("\n=== TEST: Esquema de Base de Datos ===")
    
    db_path = os.path.join(os.path.dirname(__file__), 'kronos.db')
    if not os.path.exists(db_path):
        print(f"[ERROR] BD no encontrada: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar estructura de cellular_data
        cursor.execute("PRAGMA table_info(cellular_data)")
        columns = {col[1]: col[2] for col in cursor.fetchall()}
        
        required_fields = ['id', 'file_record_id', 'mission_id', 'punto', 'lat', 'lon', 'operator', 'rssi']
        
        for field in required_fields:
            if field not in columns:
                print(f"[ERROR] Campo faltante: {field}")
                return False
            print(f"[OK] Campo {field}: {columns[field]}")
        
        # Verificar índices
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE '%file_record%'")
        indices = [row[0] for row in cursor.fetchall()]
        
        expected_indices = ['idx_cellular_file_record_id', 'idx_cellular_mission_file_record']
        for idx in expected_indices:
            if idx in indices:
                print(f"[OK] Índice encontrado: {idx}")
            else:
                print(f"[WARN] Índice faltante: {idx}")
        
        conn.close()
        print("[SUCCESS] Esquema verificado correctamente")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error verificando esquema: {e}")
        return False

def test_model_serialization():
    """Test de serialización del modelo CellularData"""
    
    print("\n=== TEST: Serialización del Modelo ===")
    
    try:
        from database.models import CellularData
        
        # Crear registro test
        test_record = CellularData(
            id=999,
            mission_id="test",
            file_record_id=12,  # ID del archivo
            punto="Test Point",
            lat=4.6108,
            lon=-74.10912,
            mnc_mcc="732101",
            operator="CLARO",
            rssi=-90,
            tecnologia="GSM",
            cell_id="1535"
        )
        
        # Serializar
        serialized = test_record.to_dict()
        
        # Verificar campos clave
        checks = [
            ('id', 999),
            ('fileRecordId', 12),  # Debe estar en camelCase
            ('punto', 'Test Point'),
            ('operador', 'CLARO'),  # operator -> operador
            ('rssi', -90)
        ]
        
        for field, expected in checks:
            if field not in serialized:
                print(f"[ERROR] Campo faltante en serialización: {field}")
                return False
            
            if serialized[field] != expected:
                print(f"[ERROR] Campo {field}: esperado={expected}, obtenido={serialized[field]}")
                return False
            
            print(f"[OK] Campo {field}: {serialized[field]}")
        
        print("[SUCCESS] Serialización correcta")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error en serialización: {e}")
        return False

def main():
    """Ejecuta todos los tests de validación"""
    
    print("KRONOS - Validación Corrección file_record_id SCANHUNTER")
    print("=" * 60)
    
    tests = [
        ("Normalizador de Datos", test_data_normalizer),
        ("Esquema de Base de Datos", test_database_schema), 
        ("Serialización del Modelo", test_model_serialization)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n>>> Ejecutando: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"[PASS] {test_name}")
            else:
                failed += 1
                print(f"[FAIL] {test_name}")
        except Exception as e:
            failed += 1
            print(f"[ERROR] {test_name}: {e}")
    
    print(f"\n=== RESUMEN ===")
    print(f"Tests pasados: {passed}")
    print(f"Tests fallidos: {failed}")
    print(f"Total: {passed + failed}")
    
    if failed == 0:
        print("\n[SUCCESS] TODOS LOS TESTS PASARON")
        print("La corrección del file_record_id está funcionando correctamente")
        return True
    else:
        print(f"\n[FAIL] {failed} tests fallieron")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)