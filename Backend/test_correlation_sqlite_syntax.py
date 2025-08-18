#!/usr/bin/env python3
"""
Test rápido de sintaxis SQL para validar las correcciones SQLite
===============================================================================

Autor: Claude Code para Boris
Fecha: 2025-08-18
"""

import sqlite3
import tempfile
import os

def test_sqlite_syntax():
    """
    Test directo de la sintaxis SQL con SQLite para verificar correcciones
    """
    print("=" * 80)
    print("TEST DE SINTAXIS SQL - COMPATIBILIDAD SQLITE")
    print("=" * 80)
    
    # Crear base de datos temporal
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Crear tablas de test
        print("[SETUP] Creando tablas de test...")
        
        cursor.execute("""
            CREATE TABLE operator_call_data (
                id INTEGER PRIMARY KEY,
                mission_id TEXT,
                numero_origen TEXT,
                numero_destino TEXT,
                celda_origen TEXT,
                celda_destino TEXT,
                operator TEXT,
                fecha_hora_llamada TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE cellular_data (
                id INTEGER PRIMARY KEY,
                mission_id TEXT,
                cell_id TEXT
            )
        """)
        
        # Insertar datos de test
        print("[SETUP] Insertando datos de test...")
        
        cursor.execute("""
            INSERT INTO cellular_data (mission_id, cell_id) 
            VALUES ('test_mission', '16040'), ('test_mission', '16041')
        """)
        
        cursor.execute("""
            INSERT INTO operator_call_data 
            (mission_id, numero_origen, numero_destino, celda_origen, celda_destino, operator, fecha_hora_llamada)
            VALUES 
            ('test_mission', '3001234567', '3007654321', '16040', '16041', 'CLARO', '2024-08-15 10:00:00'),
            ('test_mission', '3001234567', '3009876543', '16040', '16042', 'CLARO', '2024-08-15 11:00:00')
        """)
        
        conn.commit()
        
        # Test del SQL corregido
        print("[TEST] Probando SQL corregido...")
        
        hunter_cells_str = "'16040','16041'"
        
        # Query corregida compatible con SQLite
        sql_query = f"""
            WITH unique_correlations AS (
                -- Números como originadores
                SELECT 
                    numero_origen as numero,
                    operator as operador,
                    celda_origen as celda,
                    fecha_hora_llamada as fecha_hora
                FROM operator_call_data 
                WHERE mission_id = 'test_mission'
                  AND celda_origen IN ({hunter_cells_str})
                  AND date(fecha_hora_llamada) BETWEEN '2024-08-15' AND '2024-08-15'
                  AND numero_origen IS NOT NULL
                  AND numero_origen != ''
                
                UNION 
                
                -- Números como receptores
                SELECT 
                    numero_destino as numero,
                    operator as operador,
                    celda_destino as celda,
                    fecha_hora_llamada as fecha_hora
                FROM operator_call_data 
                WHERE mission_id = 'test_mission'
                  AND celda_destino IN ({hunter_cells_str})
                  AND date(fecha_hora_llamada) BETWEEN '2024-08-15' AND '2024-08-15'
                  AND numero_destino IS NOT NULL
                  AND numero_destino != ''
            ),
            correlation_stats AS (
                SELECT 
                    numero,
                    operador,
                    COUNT(DISTINCT celda) as ocurrencias,
                    MIN(fecha_hora) as primera_deteccion_global,
                    MAX(fecha_hora) as ultima_deteccion_global
                FROM unique_correlations
                GROUP BY numero, operador
                HAVING COUNT(DISTINCT celda) >= 1
            ),
            celda_groups AS (
                SELECT 
                    cs.numero,
                    cs.operador,
                    cs.ocurrencias,
                    cs.primera_deteccion_global,
                    cs.ultima_deteccion_global,
                    GROUP_CONCAT(DISTINCT uc.celda) as celdas_relacionadas
                FROM correlation_stats cs
                JOIN unique_correlations uc ON cs.numero = uc.numero AND cs.operador = uc.operador
                GROUP BY cs.numero, cs.operador, cs.ocurrencias, cs.primera_deteccion_global, cs.ultima_deteccion_global
            )
            SELECT * FROM celda_groups
            ORDER BY ocurrencias DESC, numero ASC
        """
        
        # Ejecutar query
        cursor.execute(sql_query)
        results = cursor.fetchall()
        
        print(f"[RESULTADO] Query ejecutada exitosamente!")
        print(f"[RESULTADO] Filas devueltas: {len(results)}")
        
        for row in results:
            print(f"  - {row[0]} ({row[1]}) - {row[2]} ocurrencias - Celdas: {row[5]}")
        
        # Test específico de GROUP_CONCAT sin separador personalizado
        print(f"\n[TEST] Verificando GROUP_CONCAT estándar...")
        
        simple_query = """
            SELECT numero_origen, GROUP_CONCAT(DISTINCT celda_origen) as celdas
            FROM operator_call_data 
            WHERE mission_id = 'test_mission'
            GROUP BY numero_origen
        """
        
        cursor.execute(simple_query)
        simple_results = cursor.fetchall()
        
        print(f"[RESULTADO] GROUP_CONCAT simple ejecutado exitosamente!")
        for row in simple_results:
            print(f"  - {row[0]}: {row[1]}")
        
        conn.close()
        
        print(f"\n[SUCCESS] SINTAXIS SQL VALIDADA CORRECTAMENTE PARA SQLITE")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error en validación SQL: {e}")
        return False
        
    finally:
        # Limpiar archivo temporal
        if os.path.exists(db_path):
            os.unlink(db_path)

if __name__ == "__main__":
    print("Iniciando test de sintaxis SQL...")
    
    success = test_sqlite_syntax()
    
    print(f"\n" + "=" * 80)
    if success:
        print("[SUCCESS] SINTAXIS SQL CORREGIDA Y VALIDADA")
        print("El servicio de correlación dinámico ahora es compatible con SQLite")
    else:
        print("[ERROR] SINTAXIS SQL TIENE PROBLEMAS")
        print("Revisar query para mayor compatibilidad con SQLite")
    print("=" * 80)