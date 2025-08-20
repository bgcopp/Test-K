#!/usr/bin/env python3
"""
VERIFICACION: Numeros objetivo en base de datos
===============================================

Objetivo: Verificar que numeros objetivo estan realmente en la base de datos
para poder probar get_call_interactions() con datos reales.
"""

import sqlite3
from pathlib import Path

def get_db_connection():
    """Obtiene conexion directa a la base de datos SQLite"""
    current_dir = Path(__file__).parent
    db_path = current_dir / 'kronos.db'
    return sqlite3.connect(str(db_path))

def verificar_numeros_objetivo():
    """Verifica que numeros objetivo estan en la base de datos"""
    print("VERIFICACION DE NUMEROS OBJETIVO EN BASE DE DATOS")
    print("=" * 60)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Obtener numeros unicos como origen
        print("\nNUMEROS COMO ORIGINADORES (sample):")
        cursor.execute("""
        SELECT DISTINCT numero_origen, COUNT(*) as total_llamadas
        FROM operator_call_data 
        WHERE mission_id = 'mission_MPFRBNsb'
        GROUP BY numero_origen
        ORDER BY total_llamadas DESC
        LIMIT 10
        """)
        originadores = cursor.fetchall()
        
        for numero, total in originadores:
            print(f"  {numero}: {total} llamadas como originador")
        
        # Obtener numeros unicos como destino
        print("\nNUMEROS COMO RECEPTORES (sample):")
        cursor.execute("""
        SELECT DISTINCT numero_destino, COUNT(*) as total_llamadas
        FROM operator_call_data 
        WHERE mission_id = 'mission_MPFRBNsb'
        GROUP BY numero_destino
        ORDER BY total_llamadas DESC
        LIMIT 10
        """)
        receptores = cursor.fetchall()
        
        for numero, total in receptores:
            print(f"  {numero}: {total} llamadas como receptor")
        
        # Buscar numeros con mas actividad (origen O destino)
        print("\nNUMEROS CON MAS ACTIVIDAD TOTAL:")
        cursor.execute("""
        WITH numeros_actividad AS (
            SELECT numero_origen as numero, COUNT(*) as llamadas
            FROM operator_call_data 
            WHERE mission_id = 'mission_MPFRBNsb'
            GROUP BY numero_origen
            
            UNION ALL
            
            SELECT numero_destino as numero, COUNT(*) as llamadas
            FROM operator_call_data 
            WHERE mission_id = 'mission_MPFRBNsb'
            GROUP BY numero_destino
        )
        SELECT numero, SUM(llamadas) as total_actividad
        FROM numeros_actividad
        GROUP BY numero
        ORDER BY total_actividad DESC
        LIMIT 10
        """)
        
        numeros_activos = cursor.fetchall()
        for numero, total in numeros_activos:
            print(f"  {numero}: {total} interacciones totales")
        
        # Verificar si algunos de los numeros reportados por Boris existen
        numeros_boris = ['3113330727', '3243182028', '3009120093']
        print(f"\nVERIFICANDO NUMEROS REPORTADOS POR BORIS: {numeros_boris}")
        
        for numero in numeros_boris:
            # Buscar como origen
            cursor.execute("""
            SELECT COUNT(*) FROM operator_call_data 
            WHERE mission_id = 'mission_MPFRBNsb' AND numero_origen = ?
            """, (numero,))
            como_origen = cursor.fetchone()[0]
            
            # Buscar como destino
            cursor.execute("""
            SELECT COUNT(*) FROM operator_call_data 
            WHERE mission_id = 'mission_MPFRBNsb' AND numero_destino = ?
            """, (numero,))
            como_destino = cursor.fetchone()[0]
            
            total = como_origen + como_destino
            print(f"  {numero}: {total} interacciones ({como_origen} origen, {como_destino} destino)")
        
        # Retornar un numero con actividad para pruebas
        if numeros_activos:
            numero_prueba = numeros_activos[0][0]
            print(f"\nNUMERO RECOMENDADO PARA PRUEBAS: {numero_prueba}")
            return numero_prueba
        
        return None

if __name__ == "__main__":
    verificar_numeros_objetivo()