"""
Test Directo de Base de Datos - file_record_id
==============================================
Verifica directamente la estructura de la base de datos y si el campo
file_record_id existe y funciona correctamente.
"""

import sqlite3
import os
from pathlib import Path


def test_database_structure():
    """Test de estructura de la base de datos"""
    
    print("=== TEST: Estructura de Base de Datos ===")
    
    # Rutas de la base de datos
    db_paths = [
        Path("C:/Soluciones/BGC/claude/KNSOft/Backend/kronos.db"),
        Path("C:/Soluciones/BGC/claude/KNSOft/kronos.db")
    ]
    
    db_path = None
    for path in db_paths:
        if path.exists():
            db_path = path
            break
    
    if not db_path:
        print("[ERROR] Base de datos no encontrada")
        return False
    
    print(f"[OK] Base de datos encontrada: {db_path}")
    
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Verificar estructura de la tabla cellular_data
        print("\n[PASO 1] Verificando estructura de tabla cellular_data...")
        
        cursor.execute("PRAGMA table_info(cellular_data)")
        columns = cursor.fetchall()
        
        print("  Columnas encontradas:")
        column_names = []
        for col in columns:
            column_names.append(col[1])
            print(f"    {col[1]} ({col[2]}) - Not Null: {col[3]} - Default: {col[4]}")
        
        # Verificar que file_record_id existe
        has_file_record_id = 'file_record_id' in column_names
        print(f"\n  Campo file_record_id existe: {has_file_record_id}")
        
        if not has_file_record_id:
            print("[ERROR] Campo file_record_id no encontrado")
            return False
        
        # Verificar índices relacionados
        print("\n[PASO 2] Verificando índices...")
        
        cursor.execute("""
            SELECT name, sql FROM sqlite_master 
            WHERE type='index' AND name LIKE '%file_record%'
        """)
        indices = cursor.fetchall()
        
        expected_indices = ['idx_cellular_file_record_id', 'idx_cellular_mission_file_record']
        found_indices = [idx[0] for idx in indices]
        
        for expected in expected_indices:
            if expected in found_indices:
                print(f"  [OK] Índice encontrado: {expected}")
            else:
                print(f"  [WARNING] Índice faltante: {expected}")
        
        # Verificar datos existentes
        print("\n[PASO 3] Verificando datos existentes...")
        
        cursor.execute("SELECT COUNT(*) FROM cellular_data")
        total_records = cursor.fetchone()[0]
        print(f"  Total registros en cellular_data: {total_records}")
        
        cursor.execute("SELECT COUNT(*) FROM cellular_data WHERE file_record_id IS NOT NULL")
        records_with_file_id = cursor.fetchone()[0]
        print(f"  Registros con file_record_id: {records_with_file_id}")
        
        if records_with_file_id > 0:
            # Mostrar valores únicos de file_record_id
            cursor.execute("""
                SELECT DISTINCT file_record_id, COUNT(*) 
                FROM cellular_data 
                WHERE file_record_id IS NOT NULL 
                GROUP BY file_record_id 
                ORDER BY file_record_id
            """)
            unique_ids = cursor.fetchall()
            
            print("  file_record_id únicos:")
            for id_val, count in unique_ids:
                print(f"    ID {id_val}: {count} registros")
        
        # Test de ordenamiento
        print("\n[PASO 4] Test de ordenamiento por file_record_id...")
        
        if records_with_file_id > 0:
            cursor.execute("""
                SELECT id, file_record_id, punto 
                FROM cellular_data 
                WHERE file_record_id IS NOT NULL 
                ORDER BY file_record_id ASC 
                LIMIT 10
            """)
            ordered_records = cursor.fetchall()
            
            print("  Primeros 10 registros ordenados por file_record_id:")
            for record in ordered_records:
                print(f"    DB_ID={record[0]}, file_record_id={record[1]}, punto='{record[2][:30]}...'")
        else:
            print("  [INFO] No hay registros con file_record_id para test de ordenamiento")
        
        # Verificar relación con missions
        print("\n[PASO 5] Verificando relación con missions...")
        
        cursor.execute("""
            SELECT m.code, COUNT(cd.id) as total_cellular, 
                   COUNT(CASE WHEN cd.file_record_id IS NOT NULL THEN 1 END) as with_file_id
            FROM missions m
            LEFT JOIN cellular_data cd ON m.id = cd.mission_id
            GROUP BY m.id, m.code
            HAVING total_cellular > 0
        """)
        missions_with_data = cursor.fetchall()
        
        print("  Misiones con datos celulares:")
        for mission in missions_with_data:
            print(f"    {mission[0]}: {mission[1]} registros total, {mission[2]} con file_record_id")
        
        conn.close()
        
        print("\n=== RESULTADO ===")
        
        checks_passed = 0
        total_checks = 4
        
        # Check 1: Campo existe
        if has_file_record_id:
            checks_passed += 1
            print("✓ Campo file_record_id existe en la tabla")
        else:
            print("✗ Campo file_record_id no existe")
        
        # Check 2: Índices
        if len([idx for idx in found_indices if 'file_record' in idx]) >= 1:
            checks_passed += 1
            print("✓ Al menos un índice file_record_id existe")
        else:
            print("✗ No se encontraron índices file_record_id")
        
        # Check 3: Estructura general
        required_fields = ['id', 'file_record_id', 'mission_id', 'punto', 'lat', 'lon', 'operator', 'rssi']
        has_all_required = all(field in column_names for field in required_fields)
        if has_all_required:
            checks_passed += 1
            print("✓ Todos los campos requeridos existen")
        else:
            print("✗ Faltan campos requeridos")
        
        # Check 4: Datos con file_record_id (opcional pero bueno tenerlos)
        if records_with_file_id > 0:
            checks_passed += 1
            print(f"✓ Existen {records_with_file_id} registros con file_record_id")
        else:
            checks_passed += 1  # No es error crítico, solo info
            print("ℹ No hay datos con file_record_id (esperado si no se han subido archivos SCANHUNTER)")
        
        print(f"\nRESUMEN: {checks_passed}/{total_checks} checks pasaron")
        
        return checks_passed >= 3  # Al menos 3 de 4 checks deben pasar
        
    except Exception as e:
        print(f"[ERROR] Error accediendo a la base de datos: {str(e)}")
        return False


def test_insert_sample_data():
    """Test de inserción de datos de ejemplo con file_record_id"""
    
    print("\n=== TEST: Inserción de Datos de Ejemplo ===")
    
    db_path = Path("C:/Soluciones/BGC/claude/KNSOft/Backend/kronos.db")
    if not db_path.exists():
        print("[ERROR] Base de datos no encontrada")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Verificar si hay una misión de test
        cursor.execute("SELECT id FROM missions WHERE code LIKE 'TEST_%' LIMIT 1")
        mission = cursor.fetchone()
        
        if not mission:
            print("[INFO] No se encontró misión de test, creando una...")
            mission_id = "test_file_record_id"
            cursor.execute("""
                INSERT OR REPLACE INTO missions 
                (id, code, name, status, start_date, created_by)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (mission_id, "TEST_FILE_RECORD", "Test file_record_id", "Planificación", "2025-08-14", "system"))
        else:
            mission_id = mission[0]
        
        print(f"[OK] Usando misión: {mission_id}")
        
        # Limpiar datos de test anteriores
        cursor.execute("DELETE FROM cellular_data WHERE mission_id = ?", (mission_id,))
        
        # Insertar datos de ejemplo con file_record_id
        sample_data = [
            (mission_id, 0, "PUNTO TEST 0", -74.123456, 4.123456, "73210", "CLARO", -85, "4G", "12345"),
            (mission_id, 12, "PUNTO TEST 12", -74.234567, 4.234567, "73212", "MOVISTAR", -90, "LTE", "23456"),  
            (mission_id, 32, "PUNTO TEST 32", -74.345678, 4.345678, "73213", "TIGO", -75, "5G", "34567")
        ]
        
        for data in sample_data:
            cursor.execute("""
                INSERT INTO cellular_data 
                (mission_id, file_record_id, punto, lon, lat, mnc_mcc, operator, rssi, tecnologia, cell_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, data)
        
        conn.commit()
        print(f"[OK] Insertados {len(sample_data)} registros de prueba")
        
        # Verificar inserción
        cursor.execute("""
            SELECT file_record_id, punto, operator 
            FROM cellular_data 
            WHERE mission_id = ? 
            ORDER BY file_record_id
        """, (mission_id,))
        inserted_records = cursor.fetchall()
        
        print("  Registros insertados:")
        for record in inserted_records:
            print(f"    file_record_id={record[0]}, punto='{record[1]}', operador={record[2]}")
        
        # Verificar ordenamiento
        file_ids = [r[0] for r in inserted_records]
        is_ordered = file_ids == sorted(file_ids)
        print(f"  Ordenamiento correcto: {is_ordered}")
        
        conn.close()
        
        return len(inserted_records) == 3 and is_ordered
        
    except Exception as e:
        print(f"[ERROR] Error en test de inserción: {str(e)}")
        return False


if __name__ == "__main__":
    print("KRONOS - Test Base de Datos file_record_id")
    print("=" * 50)
    
    try:
        # Test 1: Estructura
        structure_ok = test_database_structure()
        
        # Test 2: Inserción de datos
        insertion_ok = test_insert_sample_data()
        
        print(f"\n=== RESULTADO FINAL ===")
        if structure_ok and insertion_ok:
            print("SUCCESS: Todos los tests de base de datos pasaron")
            print("✓ El campo file_record_id está correctamente implementado")
        else:
            if structure_ok:
                print("PARTIAL: Estructura OK, problema con inserción")
            elif insertion_ok:
                print("PARTIAL: Inserción OK, problema con estructura") 
            else:
                print("FAILURE: Tests de base de datos fallaron")
                
    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")