#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Análisis específico del período para el número 3143534707
Enfocado en datos de mayo 2021 excluyendo registros de 2024
Autor: SQLite Database Architect
Fecha: 2025-01-18
"""

import sqlite3
import json
from datetime import datetime

def analizar_periodo_especifico_3143534707():
    """
    Análisis del número 3143534707 enfocado únicamente en el período 
    de mayo 2021 para determinar la correlación correcta
    """
    
    # Conectar a la base de datos
    db_path = "kronos.db"
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        resultado = {
            "numero_analizado": "3143534707",
            "periodo_analizado": "Mayo 2021",
            "timestamp": datetime.now().isoformat(),
            "analisis_periodo": {}
        }
        
        print("=" * 80)
        print("ANÁLISIS PERÍODO ESPECÍFICO - NÚMERO 3143534707")
        print("PERÍODO: MAYO 2021 (Excluyendo datos de 2024)")
        print("=" * 80)
        
        # 1. REGISTROS COMO ORIGEN EN MAYO 2021
        print("\n1. REGISTROS COMO ORIGEN (MAYO 2021)")
        print("-" * 50)
        
        query_origen_mayo = """
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
        AND fecha_hora_llamada >= '2021-05-01'
        AND fecha_hora_llamada < '2021-06-01'
        GROUP BY numero_origen, numero_destino, celda_origen, celda_destino, fecha_hora_llamada, operator
        ORDER BY fecha_hora_llamada, celda_origen, celda_destino
        """
        
        cursor.execute(query_origen_mayo)
        registros_origen_mayo = cursor.fetchall()
        
        print(f"Registros encontrados como ORIGEN en mayo 2021: {len(registros_origen_mayo)}")
        
        celdas_origen_mayo = set()
        celdas_destino_cuando_origen_mayo = set()
        
        for reg in registros_origen_mayo:
            print(f"  Origen: {reg['numero_origen']} -> Destino: {reg['numero_destino']}")
            print(f"    Celda Origen: {reg['celda_origen']} | Celda Destino: {reg['celda_destino']}")
            print(f"    Fecha: {reg['fecha_hora_llamada']} | Operador: {reg['operator']}")
            print()
            
            if reg['celda_origen']:
                celdas_origen_mayo.add(str(reg['celda_origen']))
            if reg['celda_destino']:
                celdas_destino_cuando_origen_mayo.add(str(reg['celda_destino']))
        
        # 2. REGISTROS COMO DESTINO EN MAYO 2021
        print("\n2. REGISTROS COMO DESTINO (MAYO 2021)")
        print("-" * 50)
        
        query_destino_mayo = """
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
        AND fecha_hora_llamada >= '2021-05-01'
        AND fecha_hora_llamada < '2021-06-01'
        GROUP BY numero_origen, numero_destino, celda_origen, celda_destino, fecha_hora_llamada, operator
        ORDER BY fecha_hora_llamada, celda_origen, celda_destino
        """
        
        cursor.execute(query_destino_mayo)
        registros_destino_mayo = cursor.fetchall()
        
        print(f"Registros encontrados como DESTINO en mayo 2021: {len(registros_destino_mayo)}")
        
        celdas_origen_cuando_destino_mayo = set()
        celdas_destino_mayo = set()
        
        for reg in registros_destino_mayo:
            print(f"  Origen: {reg['numero_origen']} -> Destino: {reg['numero_destino']}")
            print(f"    Celda Origen: {reg['celda_origen']} | Celda Destino: {reg['celda_destino']}")
            print(f"    Fecha: {reg['fecha_hora_llamada']} | Operador: {reg['operator']}")
            print()
            
            if reg['celda_origen']:
                celdas_origen_cuando_destino_mayo.add(str(reg['celda_origen']))
            if reg['celda_destino']:
                celdas_destino_mayo.add(str(reg['celda_destino']))
        
        # 3. ANÁLISIS DE CORRELACIÓN PERÍODO MAYO 2021
        print("\n3. ANÁLISIS DE CORRELACIÓN (MAYO 2021 ÚNICAMENTE)")
        print("-" * 50)
        
        # Interpretación actual del algoritmo (ubicación física)
        celdas_ubicacion_fisica_mayo = set()
        
        # Cuando es originador, está físicamente en celda_origen
        celdas_ubicacion_fisica_mayo.update(celdas_origen_mayo)
        
        # Cuando es receptor, está físicamente en celda_destino
        celdas_ubicacion_fisica_mayo.update(celdas_destino_mayo)
        
        # Interpretación alternativa (cualquier celda involucrada)
        todas_las_celdas_involucradas_mayo = set()
        todas_las_celdas_involucradas_mayo.update(celdas_origen_mayo)
        todas_las_celdas_involucradas_mayo.update(celdas_destino_cuando_origen_mayo)
        todas_las_celdas_involucradas_mayo.update(celdas_origen_cuando_destino_mayo)
        todas_las_celdas_involucradas_mayo.update(celdas_destino_mayo)
        
        print("INTERPRETACIÓN ACTUAL - MAYO 2021 (Ubicación física):")
        print(f"  Celdas: {sorted(list(celdas_ubicacion_fisica_mayo))}")
        print(f"  Total: {len(celdas_ubicacion_fisica_mayo)} celdas")
        
        print("\nINTERPRETACIÓN ALTERNATIVA - MAYO 2021 (Cualquier celda involucrada):")
        print(f"  Celdas: {sorted(list(todas_las_celdas_involucradas_mayo))}")
        print(f"  Total: {len(todas_las_celdas_involucradas_mayo)} celdas")
        
        # 4. COMPARACIÓN CON EXPECTATIVA DE BORIS (MAYO 2021)
        print("\n4. COMPARACIÓN CON EXPECTATIVA DE BORIS (MAYO 2021)")
        print("-" * 50)
        
        celdas_esperadas_boris = {"53591", "51438", "56124", "51203"}
        
        match_actual_mayo = celdas_ubicacion_fisica_mayo == celdas_esperadas_boris
        match_alternativa_mayo = todas_las_celdas_involucradas_mayo == celdas_esperadas_boris
        
        print(f"Celdas esperadas por Boris: {sorted(list(celdas_esperadas_boris))}")
        print(f"Interpretación actual coincide: {match_actual_mayo}")
        print(f"Interpretación alternativa coincide: {match_alternativa_mayo}")
        
        if match_actual_mayo:
            print("COINCIDENCIA EXACTA con interpretacion actual (ubicacion fisica)")
        elif match_alternativa_mayo:
            print("COINCIDENCIA EXACTA con interpretacion alternativa (cualquier celda)")
        else:
            diferencia_actual = celdas_esperadas_boris.symmetric_difference(celdas_ubicacion_fisica_mayo)
            diferencia_alternativa = celdas_esperadas_boris.symmetric_difference(todas_las_celdas_involucradas_mayo)
            
            print(f"Diferencias interpretacion actual: {sorted(list(diferencia_actual))}")
            print(f"Diferencias interpretacion alternativa: {sorted(list(diferencia_alternativa))}")
        
        # 5. ANÁLISIS DETALLADO DE LA CELDA 51203
        print("\n5. ANÁLISIS ESPECÍFICO DE LA CELDA 51203")
        print("-" * 50)
        
        # Verificar todos los registros que involucran la celda 51203
        query_celda_51203 = """
        SELECT 
            numero_origen,
            numero_destino,
            celda_origen,
            celda_destino,
            fecha_hora_llamada,
            operator,
            CASE 
                WHEN numero_origen = '3143534707' THEN 'NUMERO_ES_ORIGEN'
                WHEN numero_destino = '3143534707' THEN 'NUMERO_ES_DESTINO'
                ELSE 'NO_RELACIONADO'
            END as relacion_numero
        FROM operator_call_data 
        WHERE (numero_origen = '3143534707' OR numero_destino = '3143534707')
        AND (celda_origen = '51203' OR celda_destino = '51203')
        AND fecha_hora_llamada >= '2021-05-01'
        AND fecha_hora_llamada < '2021-06-01'
        ORDER BY fecha_hora_llamada
        """
        
        cursor.execute(query_celda_51203)
        registros_celda_51203 = cursor.fetchall()
        
        print(f"Registros que involucran la celda 51203: {len(registros_celda_51203)}")
        
        for reg in registros_celda_51203:
            print(f"  {reg['relacion_numero']}: {reg['numero_origen']} -> {reg['numero_destino']}")
            print(f"    Celda Origen: {reg['celda_origen']} | Celda Destino: {reg['celda_destino']}")
            print(f"    Fecha: {reg['fecha_hora_llamada']}")
            print()
        
        # 6. RECOMENDACIÓN TÉCNICA FINAL
        print("\n6. RECOMENDACIÓN TÉCNICA FINAL")
        print("-" * 50)
        
        if match_actual_mayo:
            recomendacion = "CONFIRMAR: Implementar algoritmo de ubicacion fisica del numero"
            justificacion = "Los datos de mayo 2021 coinciden exactamente con la expectativa de Boris usando ubicacion fisica"
            algoritmo_correcto = "ubicacion_fisica"
        elif match_alternativa_mayo:
            recomendacion = "CONFIRMAR: Implementar algoritmo de cualquier celda involucrada"
            justificacion = "Los datos de mayo 2021 coinciden exactamente con la expectativa de Boris incluyendo cualquier celda"
            algoritmo_correcto = "cualquier_celda"
        else:
            recomendacion = "INVESTIGAR: Posible inconsistencia en datos o especificacion"
            justificacion = "Los datos de mayo 2021 no coinciden con ninguna interpretacion estandar"
            algoritmo_correcto = "requiere_clarificacion"
        
        print(f"Recomendación: {recomendacion}")
        print(f"Justificación: {justificacion}")
        print(f"Algoritmo recomendado: {algoritmo_correcto}")
        
        # Guardar resultado
        resultado["analisis_periodo"] = {
            "registros_origen_mayo": [dict(reg) for reg in registros_origen_mayo],
            "registros_destino_mayo": [dict(reg) for reg in registros_destino_mayo],
            "registros_celda_51203": [dict(reg) for reg in registros_celda_51203],
            "celdas_ubicacion_fisica_mayo": sorted(list(celdas_ubicacion_fisica_mayo)),
            "todas_celdas_involucradas_mayo": sorted(list(todas_las_celdas_involucradas_mayo)),
            "celdas_esperadas_boris": sorted(list(celdas_esperadas_boris)),
            "match_ubicacion_fisica": match_actual_mayo,
            "match_cualquier_celda": match_alternativa_mayo,
            "recomendacion": recomendacion,
            "justificacion": justificacion,
            "algoritmo_recomendado": algoritmo_correcto
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analisis_periodo_mayo_2021_{timestamp}.json"
        
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
    resultado = analizar_periodo_especifico_3143534707()
    if resultado:
        print("\n" + "=" * 80)
        print("ANÁLISIS DE PERÍODO COMPLETADO EXITOSAMENTE")
        print("=" * 80)
    else:
        print("Error en el análisis")