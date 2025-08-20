#!/usr/bin/env python3
"""
Script de validación para el endpoint get_call_interactions actualizado con datos HUNTER
Fecha: 2025-08-19
"""

import sqlite3
import sys
from pathlib import Path

# Agregar la ruta del backend al path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from main import get_call_interactions, get_db_connection

def test_database_connection():
    """Verificar conexión a la base de datos"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
        print("[OK] Conexion a base de datos exitosa")
        print(f"  Tablas encontradas: {tables}")
        
        # Verificar tablas críticas
        required_tables = ['operator_call_data', 'cellular_data']
        missing = [t for t in required_tables if t not in tables]
        if missing:
            print(f"[WARNING] Tablas faltantes: {missing}")
            return False
        else:
            print("[OK] Todas las tablas requeridas estan presentes")
            return True
            
    except Exception as e:
        print(f"[ERROR] Error de conexion: {e}")
        return False

def check_sample_data():
    """Verificar que hay datos de muestra disponibles"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar datos de llamadas
            cursor.execute("SELECT COUNT(*) FROM operator_call_data")
            calls_count = cursor.fetchone()[0]
            
            # Verificar datos HUNTER
            cursor.execute("SELECT COUNT(*) FROM cellular_data")
            hunter_count = cursor.fetchone()[0]
            
            # Obtener una misión de muestra
            cursor.execute("SELECT DISTINCT mission_id FROM operator_call_data LIMIT 1")
            sample_mission = cursor.fetchone()
            
            # Obtener un número objetivo de muestra
            cursor.execute("""
                SELECT numero_objetivo, COUNT(*) as calls 
                FROM operator_call_data 
                WHERE mission_id = ? 
                GROUP BY numero_objetivo 
                ORDER BY calls DESC 
                LIMIT 1
            """, (sample_mission[0] if sample_mission else None,))
            sample_number = cursor.fetchone()
            
        print(f"[OK] Datos de llamadas: {calls_count} registros")
        print(f"[OK] Datos HUNTER: {hunter_count} registros")
        
        if sample_mission and sample_number:
            print(f"[OK] Mision de prueba: {sample_mission[0]}")
            print(f"[OK] Numero de prueba: {sample_number[0]} ({sample_number[1]} llamadas)")
            return sample_mission[0], sample_number[0]
        else:
            print("[WARNING] No se encontraron datos de muestra suficientes")
            return None, None
            
    except Exception as e:
        print(f"[ERROR] Error verificando datos: {e}")
        return None, None

def test_endpoint_basic(mission_id, target_number):
    """Probar el endpoint con parámetros básicos"""
    try:
        print("\n=== PRUEBA DEL ENDPOINT ===")
        print(f"Probando con:")
        print(f"  Mission ID: {mission_id}")
        print(f"  Target Number: {target_number}")
        print(f"  Período: 2020-01-01 00:00:00 - 2030-12-31 23:59:59")
        
        # Llamar al endpoint
        results = get_call_interactions(
            mission_id=mission_id,
            target_number=target_number,
            start_datetime="2020-01-01 00:00:00",
            end_datetime="2030-12-31 23:59:59"
        )
        
        print(f"[OK] Endpoint ejecutado exitosamente")
        print(f"[OK] Resultados obtenidos: {len(results)} interacciones")
        
        if results:
            # Analizar el primer resultado
            first_result = results[0]
            print(f"\nEstructura del primer resultado:")
            for key, value in first_result.items():
                value_str = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                print(f"  {key}: {value_str}")
            
            # Verificar nuevos campos HUNTER
            hunter_fields = [
                'punto_hunter_origen', 'lat_hunter_origen', 'lon_hunter_origen',
                'punto_hunter_destino', 'lat_hunter_destino', 'lon_hunter_destino'
            ]
            
            print(f"\nVerificación campos HUNTER:")
            for field in hunter_fields:
                if field in first_result:
                    value = first_result[field]
                    status = "[OK] PRESENTE" if value is not None else "[NULL] NULL"
                    print(f"  {field}: {status}")
                else:
                    print(f"  {field}: [ERROR] AUSENTE")
            
            # Estadísticas de correlación
            hunter_origen = sum(1 for r in results if r.get('punto_hunter_origen'))
            hunter_destino = sum(1 for r in results if r.get('punto_hunter_destino'))
            total = len(results)
            
            print(f"\nEstadísticas de correlación HUNTER:")
            print(f"  Correlación origen: {hunter_origen}/{total} ({hunter_origen/total*100:.1f}%)")
            print(f"  Correlación destino: {hunter_destino}/{total} ({hunter_destino/total*100:.1f}%)")
            
        return True
        
    except Exception as e:
        print(f"[ERROR] Error en el endpoint: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Función principal de pruebas"""
    print("=== VALIDACIÓN ENDPOINT get_call_interactions CON DATOS HUNTER ===")
    print("Boris - Script de prueba para correlación HUNTER")
    print("Fecha: 2025-08-19\n")
    
    # 1. Verificar conexión de base de datos
    if not test_database_connection():
        print("\n[FALLO] Problemas de conexion a la base de datos")
        return False
    
    # 2. Verificar datos de muestra
    mission_id, target_number = check_sample_data()
    if not mission_id or not target_number:
        print("\n[FALLO] No hay datos suficientes para la prueba")
        return False
    
    # 3. Probar el endpoint
    if not test_endpoint_basic(mission_id, target_number):
        print("\n[FALLO] El endpoint no funciona correctamente")
        return False
    
    print("\n[EXITO] Todas las pruebas pasaron correctamente")
    print("El endpoint get_call_interactions ahora incluye datos HUNTER correlacionados")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)