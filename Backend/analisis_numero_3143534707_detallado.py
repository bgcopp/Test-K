#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Análisis detallado del número 3143534707 para validar algoritmo de correlación
Autor: SQLite Database Architect
Fecha: 2025-01-18
"""

import sqlite3
import json
from datetime import datetime

def analizar_numero_3143534707():
    """
    Análisis exhaustivo del número 3143534707 para determinar 
    la interpretación correcta del algoritmo de correlación
    """
    
    # Conectar a la base de datos
    db_path = "kronos.db"
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Para acceso por nombre de columna
        cursor = conn.cursor()
        
        resultado = {
            "numero_analizado": "3143534707",
            "timestamp": datetime.now().isoformat(),
            "analisis": {}
        }
        
        print("=" * 80)
        print("ANÁLISIS DETALLADO DEL NÚMERO 3143534707")
        print("=" * 80)
        
        # 1. ANÁLISIS DE ESTRUCTURA DE TABLAS
        print("\n1. ESTRUCTURA DE TABLAS RELEVANTES")
        print("-" * 50)
        
        # Verificar estructura de operator_call_data
        cursor.execute("PRAGMA table_info(operator_call_data)")
        columnas = cursor.fetchall()
        
        print("Tabla operator_call_data:")
        for col in columnas:
            print(f"  - {col['name']}: {col['type']}")
        
        resultado["analisis"]["estructura_tabla"] = [dict(col) for col in columnas]
        
        # 2. BÚSQUEDA COMO NÚMERO DE ORIGEN
        print("\n2. REGISTROS COMO NÚMERO DE ORIGEN")
        print("-" * 50)
        
        query_origen = """
        SELECT 
            numero_origen,
            numero_destino,
            celda_origen,
            celda_destino,
            fecha_hora_llamada,
            operator,
            COUNT(*) as cantidad_registros
        FROM operator_call_data 
        WHERE numero_origen = '3143534707'
        GROUP BY numero_origen, numero_destino, celda_origen, celda_destino, fecha_hora_llamada, operator
        ORDER BY fecha_hora_llamada, celda_origen, celda_destino
        """
        
        cursor.execute(query_origen)
        registros_origen = cursor.fetchall()
        
        print(f"Registros encontrados como ORIGEN: {len(registros_origen)}")
        
        celdas_origen_set = set()
        celdas_destino_set = set()
        
        for reg in registros_origen:
            print(f"  Origen: {reg['numero_origen']} -> Destino: {reg['numero_destino']}")
            print(f"    Celda Origen: {reg['celda_origen']} | Celda Destino: {reg['celda_destino']}")
            print(f"    Fecha: {reg['fecha_hora_llamada']} | Operador: {reg['operator']} | Cantidad: {reg['cantidad_registros']}")
            print()
            
            if reg['celda_origen']:
                celdas_origen_set.add(str(reg['celda_origen']))
            if reg['celda_destino']:
                celdas_destino_set.add(str(reg['celda_destino']))
        
        resultado["analisis"]["registros_como_origen"] = [dict(reg) for reg in registros_origen]
        resultado["analisis"]["celdas_origen_involucradas"] = sorted(list(celdas_origen_set))
        resultado["analisis"]["celdas_destino_cuando_origen"] = sorted(list(celdas_destino_set))
        
        # 3. BÚSQUEDA COMO NÚMERO DE DESTINO
        print("\n3. REGISTROS COMO NÚMERO DE DESTINO")
        print("-" * 50)
        
        query_destino = """
        SELECT 
            numero_origen,
            numero_destino,
            celda_origen,
            celda_destino,
            fecha_hora_llamada,
            operator,
            COUNT(*) as cantidad_registros
        FROM operator_call_data 
        WHERE numero_destino = '3143534707'
        GROUP BY numero_origen, numero_destino, celda_origen, celda_destino, fecha_hora_llamada, operator
        ORDER BY fecha_hora_llamada, celda_origen, celda_destino
        """
        
        cursor.execute(query_destino)
        registros_destino = cursor.fetchall()
        
        print(f"Registros encontrados como DESTINO: {len(registros_destino)}")
        
        celdas_origen_cuando_destino = set()
        celdas_destino_cuando_destino = set()
        
        for reg in registros_destino:
            print(f"  Origen: {reg['numero_origen']} -> Destino: {reg['numero_destino']}")
            print(f"    Celda Origen: {reg['celda_origen']} | Celda Destino: {reg['celda_destino']}")
            print(f"    Fecha: {reg['fecha_hora_llamada']} | Operador: {reg['operator']} | Cantidad: {reg['cantidad_registros']}")
            print()
            
            if reg['celda_origen']:
                celdas_origen_cuando_destino.add(str(reg['celda_origen']))
            if reg['celda_destino']:
                celdas_destino_cuando_destino.add(str(reg['celda_destino']))
        
        resultado["analisis"]["registros_como_destino"] = [dict(reg) for reg in registros_destino]
        resultado["analisis"]["celdas_origen_cuando_destino"] = sorted(list(celdas_origen_cuando_destino))
        resultado["analisis"]["celdas_destino_involucradas"] = sorted(list(celdas_destino_cuando_destino))
        
        # 4. ANÁLISIS DE CORRELACIÓN
        print("\n4. ANÁLISIS DE CORRELACIÓN")
        print("-" * 50)
        
        # Interpretación actual del algoritmo (ubicación física)
        celdas_ubicacion_fisica = set()
        
        # Cuando es originador, está físicamente en celda_origen
        for reg in registros_origen:
            if reg['celda_origen']:
                celdas_ubicacion_fisica.add(str(reg['celda_origen']))
        
        # Cuando es receptor, está físicamente en celda_destino
        for reg in registros_destino:
            if reg['celda_destino']:
                celdas_ubicacion_fisica.add(str(reg['celda_destino']))
        
        # Interpretación alternativa (cualquier celda involucrada)
        todas_las_celdas_involucradas = set()
        
        # Todas las celdas cuando es originador
        for reg in registros_origen:
            if reg['celda_origen']:
                todas_las_celdas_involucradas.add(str(reg['celda_origen']))
            if reg['celda_destino']:
                todas_las_celdas_involucradas.add(str(reg['celda_destino']))
        
        # Todas las celdas cuando es receptor
        for reg in registros_destino:
            if reg['celda_origen']:
                todas_las_celdas_involucradas.add(str(reg['celda_origen']))
            if reg['celda_destino']:
                todas_las_celdas_involucradas.add(str(reg['celda_destino']))
        
        print("INTERPRETACIÓN ACTUAL (Ubicación física):")
        print(f"  Celdas: {sorted(list(celdas_ubicacion_fisica))}")
        print(f"  Total: {len(celdas_ubicacion_fisica)} celdas")
        
        print("\nINTERPRETACIÓN ALTERNATIVA (Cualquier celda involucrada):")
        print(f"  Celdas: {sorted(list(todas_las_celdas_involucradas))}")
        print(f"  Total: {len(todas_las_celdas_involucradas)} celdas")
        
        resultado["analisis"]["interpretacion_actual"] = {
            "celdas": sorted(list(celdas_ubicacion_fisica)),
            "total": len(celdas_ubicacion_fisica),
            "descripcion": "Ubicación física del número (celda_origen cuando origina, celda_destino cuando recibe)"
        }
        
        resultado["analisis"]["interpretacion_alternativa"] = {
            "celdas": sorted(list(todas_las_celdas_involucradas)),
            "total": len(todas_las_celdas_involucradas),
            "descripcion": "Cualquier celda involucrada en comunicación"
        }
        
        # 5. COMPARACIÓN CON EXPECTATIVA DE BORIS
        print("\n5. COMPARACIÓN CON EXPECTATIVA DE BORIS")
        print("-" * 50)
        
        celdas_esperadas_boris = {"53591", "51438", "56124", "51203"}
        
        match_actual = celdas_ubicacion_fisica == celdas_esperadas_boris
        match_alternativa = todas_las_celdas_involucradas == celdas_esperadas_boris
        
        print(f"Celdas esperadas por Boris: {sorted(list(celdas_esperadas_boris))}")
        print(f"Interpretación actual coincide: {match_actual}")
        print(f"Interpretación alternativa coincide: {match_alternativa}")
        
        if not match_actual and not match_alternativa:
            diferencia_actual = celdas_esperadas_boris.symmetric_difference(celdas_ubicacion_fisica)
            diferencia_alternativa = celdas_esperadas_boris.symmetric_difference(todas_las_celdas_involucradas)
            
            print(f"\nDiferencias interpretación actual: {sorted(list(diferencia_actual))}")
            print(f"Diferencias interpretación alternativa: {sorted(list(diferencia_alternativa))}")
        
        resultado["analisis"]["comparacion_boris"] = {
            "celdas_esperadas": sorted(list(celdas_esperadas_boris)),
            "match_interpretacion_actual": match_actual,
            "match_interpretacion_alternativa": match_alternativa
        }
        
        # 6. RECOMENDACIÓN TÉCNICA
        print("\n6. RECOMENDACIÓN TÉCNICA")
        print("-" * 50)
        
        if match_alternativa and not match_actual:
            recomendacion = "Implementar interpretación alternativa - cualquier celda involucrada"
            justificacion = "Los datos coinciden exactamente con la expectativa de Boris"
        elif match_actual and not match_alternativa:
            recomendacion = "Mantener interpretación actual - ubicación física"
            justificacion = "Los datos coinciden exactamente con la expectativa de Boris"
        elif not match_actual and not match_alternativa:
            recomendacion = "Requiere análisis adicional de datos y especificación de negocio"
            justificacion = "Ninguna interpretación coincide exactamente con la expectativa"
        else:
            recomendacion = "Ambas interpretaciones son válidas - consultar especificación de negocio"
            justificacion = "Ambos enfoques dan el mismo resultado"
        
        print(f"Recomendación: {recomendacion}")
        print(f"Justificación: {justificacion}")
        
        resultado["analisis"]["recomendacion"] = {
            "decision": recomendacion,
            "justificacion": justificacion
        }
        
        # Guardar resultado en archivo JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analisis_3143534707_detallado_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, indent=2, ensure_ascii=False)
        
        print(f"\nResultados guardados en: {filename}")
        
        conn.close()
        return resultado
        
    except sqlite3.Error as e:
        print(f"Error de SQLite: {e}")
        return None
    except Exception as e:
        print(f"Error general: {e}")
        return None

if __name__ == "__main__":
    resultado = analizar_numero_3143534707()
    if resultado:
        print("\n" + "=" * 80)
        print("ANÁLISIS COMPLETADO EXITOSAMENTE")
        print("=" * 80)
    else:
        print("Error en el análisis")