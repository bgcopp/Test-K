#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Análisis de la interpretación específica de Boris para el número 3143534707
Explorando tercera interpretación: ubicación física + celda_destino cuando origina
Autor: SQLite Database Architect
Fecha: 2025-01-18
"""

import sqlite3
import json
from datetime import datetime

def analizar_interpretacion_boris_3143534707():
    """
    Análisis del número 3143534707 explorando la interpretación específica de Boris:
    - Cuando el número es ORIGINADOR: incluye celda_origen (donde está) Y celda_destino (hacia donde llama)
    - Cuando el número es RECEPTOR: incluye celda_destino (donde está)
    """
    
    # Conectar a la base de datos
    db_path = "kronos.db"
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        resultado = {
            "numero_analizado": "3143534707",
            "interpretacion": "Boris - Ubicacion fisica + destino cuando origina",
            "timestamp": datetime.now().isoformat(),
            "analisis_boris": {}
        }
        
        print("=" * 80)
        print("ANÁLISIS INTERPRETACIÓN ESPECÍFICA DE BORIS - NÚMERO 3143534707")
        print("INTERPRETACIÓN: Ubicación física + celda_destino cuando origina")
        print("=" * 80)
        
        # 1. DATOS DE MAYO 2021 ÚNICAMENTE
        print("\n1. REGISTROS DE MAYO 2021")
        print("-" * 50)
        
        # Registros como origen
        query_origen_mayo = """
        SELECT 
            numero_origen,
            numero_destino,
            celda_origen,
            celda_destino,
            fecha_hora_llamada,
            operator
        FROM operator_call_data 
        WHERE numero_origen = '3143534707'
        AND fecha_hora_llamada >= '2021-05-01'
        AND fecha_hora_llamada < '2021-06-01'
        ORDER BY fecha_hora_llamada
        """
        
        cursor.execute(query_origen_mayo)
        registros_origen = cursor.fetchall()
        
        # Registros como destino
        query_destino_mayo = """
        SELECT 
            numero_origen,
            numero_destino,
            celda_origen,
            celda_destino,
            fecha_hora_llamada,
            operator
        FROM operator_call_data 
        WHERE numero_destino = '3143534707'
        AND fecha_hora_llamada >= '2021-05-01'
        AND fecha_hora_llamada < '2021-06-01'
        ORDER BY fecha_hora_llamada
        """
        
        cursor.execute(query_destino_mayo)
        registros_destino = cursor.fetchall()
        
        print("REGISTROS COMO ORIGINADOR:")
        for reg in registros_origen:
            print(f"  {reg['numero_origen']} -> {reg['numero_destino']}")
            print(f"    Celda Origen: {reg['celda_origen']} | Celda Destino: {reg['celda_destino']}")
            print(f"    Fecha: {reg['fecha_hora_llamada']}")
            print()
        
        print("REGISTROS COMO RECEPTOR:")
        for reg in registros_destino:
            print(f"  {reg['numero_origen']} -> {reg['numero_destino']}")
            print(f"    Celda Origen: {reg['celda_origen']} | Celda Destino: {reg['celda_destino']}")
            print(f"    Fecha: {reg['fecha_hora_llamada']}")
            print()
        
        # 2. INTERPRETACIÓN DE BORIS
        print("\n2. INTERPRETACIÓN DE BORIS")
        print("-" * 50)
        
        celdas_interpretacion_boris = set()
        
        print("APLICANDO REGLA DE BORIS:")
        print("- Cuando 3143534707 es ORIGINADOR: incluir celda_origen Y celda_destino")
        print("- Cuando 3143534707 es RECEPTOR: incluir celda_destino")
        print()
        
        # Cuando es originador: incluir celda_origen Y celda_destino
        for reg in registros_origen:
            if reg['celda_origen']:
                celdas_interpretacion_boris.add(str(reg['celda_origen']))
                print(f"  + Celda {reg['celda_origen']} (origen donde está 3143534707)")
            
            if reg['celda_destino']:
                celdas_interpretacion_boris.add(str(reg['celda_destino']))
                print(f"  + Celda {reg['celda_destino']} (destino hacia donde llama 3143534707)")
        
        # Cuando es receptor: incluir celda_destino
        for reg in registros_destino:
            if reg['celda_destino']:
                celdas_interpretacion_boris.add(str(reg['celda_destino']))
                print(f"  + Celda {reg['celda_destino']} (destino donde está 3143534707)")
        
        print(f"\nCeldas según interpretación de Boris: {sorted(list(celdas_interpretacion_boris))}")
        print(f"Total: {len(celdas_interpretacion_boris)} celdas")
        
        # 3. COMPARACIÓN CON EXPECTATIVA
        print("\n3. COMPARACIÓN CON EXPECTATIVA DE BORIS")
        print("-" * 50)
        
        celdas_esperadas_boris = {"53591", "51438", "56124", "51203"}
        
        match_interpretacion_boris = celdas_interpretacion_boris == celdas_esperadas_boris
        
        print(f"Celdas esperadas por Boris: {sorted(list(celdas_esperadas_boris))}")
        print(f"Celdas calculadas con interpretación Boris: {sorted(list(celdas_interpretacion_boris))}")
        print(f"COINCIDENCIA EXACTA: {match_interpretacion_boris}")
        
        if match_interpretacion_boris:
            print("*** ÉXITO: La interpretación de Boris es CORRECTA ***")
        else:
            diferencia = celdas_esperadas_boris.symmetric_difference(celdas_interpretacion_boris)
            print(f"Diferencias: {sorted(list(diferencia))}")
        
        # 4. ANÁLISIS DETALLADO DE CADA CELDA
        print("\n4. ANÁLISIS DETALLADO DE CADA CELDA ESPERADA")
        print("-" * 50)
        
        celdas_esperadas = ["53591", "51438", "56124", "51203"]
        
        for celda in celdas_esperadas:
            print(f"\nCELDA {celda}:")
            
            # Buscar en registros como origen
            encontrada_origen = False
            for reg in registros_origen:
                if str(reg['celda_origen']) == celda:
                    print(f"  - Encontrada como celda_origen: 3143534707 -> {reg['numero_destino']}")
                    encontrada_origen = True
                if str(reg['celda_destino']) == celda:
                    print(f"  - Encontrada como celda_destino: 3143534707 -> {reg['numero_destino']}")
            
            # Buscar en registros como destino
            encontrada_destino = False
            for reg in registros_destino:
                if str(reg['celda_destino']) == celda:
                    print(f"  - Encontrada como celda_destino: {reg['numero_origen']} -> 3143534707")
                    encontrada_destino = True
            
            if not encontrada_origen and not encontrada_destino:
                print(f"  - NO encontrada en ningún registro")
        
        # 5. RECOMENDACIÓN TÉCNICA FINAL
        print("\n5. RECOMENDACIÓN TÉCNICA FINAL")
        print("-" * 50)
        
        if match_interpretacion_boris:
            recomendacion = "IMPLEMENTAR ALGORITMO DE BORIS"
            justificacion = "La interpretación de Boris coincide exactamente con su expectativa"
            algoritmo_correcto = "boris_ubicacion_mas_destino"
            detalle_algoritmo = {
                "cuando_es_originador": "incluir celda_origen Y celda_destino",
                "cuando_es_receptor": "incluir celda_destino",
                "logica": "El número puede estar físicamente en una celda pero comunicarse con otra"
            }
        else:
            recomendacion = "REQUIERE CLARIFICACION ADICIONAL"
            justificacion = "La interpretación de Boris no coincide con los datos"
            algoritmo_correcto = "pendiente_clarificacion"
            detalle_algoritmo = {}
        
        print(f"Recomendación: {recomendacion}")
        print(f"Justificación: {justificacion}")
        print(f"Algoritmo recomendado: {algoritmo_correcto}")
        
        if detalle_algoritmo:
            print("\nDetalle del algoritmo:")
            for key, value in detalle_algoritmo.items():
                print(f"  - {key}: {value}")
        
        # Guardar resultado
        resultado["analisis_boris"] = {
            "registros_origen": [dict(reg) for reg in registros_origen],
            "registros_destino": [dict(reg) for reg in registros_destino],
            "celdas_interpretacion_boris": sorted(list(celdas_interpretacion_boris)),
            "celdas_esperadas": sorted(list(celdas_esperadas_boris)),
            "coincidencia_exacta": match_interpretacion_boris,
            "recomendacion": recomendacion,
            "justificacion": justificacion,
            "algoritmo_recomendado": algoritmo_correcto,
            "detalle_algoritmo": detalle_algoritmo
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analisis_interpretacion_boris_{timestamp}.json"
        
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
    resultado = analizar_interpretacion_boris_3143534707()
    if resultado:
        print("\n" + "=" * 80)
        print("ANÁLISIS DE INTERPRETACIÓN BORIS COMPLETADO EXITOSAMENTE")
        print("=" * 80)
    else:
        print("Error en el análisis")