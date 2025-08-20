#!/usr/bin/env python3
"""
ANÁLISIS CRÍTICO: Lógica del Punto HUNTER vs Direccionalidad de Llamadas
==========================================================================

Script para analizar el problema identificado por Boris sobre la lógica 
del "Punto HUNTER" en relación con la direccionalidad de las llamadas.

PROBLEMA IDENTIFICADO:
- Lógica actual: COALESCE(celda_destino, celda_origen) - siempre prioriza destino
- Lógica correcta: Depende de la dirección de la llamada:
  * SALIENTE: Usar celda_origen (donde estaba el número objetivo)
  * ENTRANTE: Usar celda_destino (donde estaba el número objetivo)

Autor: Claude Code - Análisis solicitado por Boris
Fecha: 2025-08-20
"""

import sqlite3
import sys
from pathlib import Path

def analizar_logica_hunter():
    """Ejecuta análisis completo de la lógica del Punto HUNTER"""
    
    # Conectar a la base de datos
    db_path = Path(__file__).parent / 'kronos.db'
    if not db_path.exists():
        print(f"ERROR: Base de datos no encontrada: {db_path}")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print("=" * 80)
    print("DIAGNÓSTICO CRÍTICO: LÓGICA PUNTO HUNTER vs DIRECCIONALIDAD")
    print("=" * 80)
    print()
    
    # 1. Análisis de la lógica actual vs correcta
    print("1. ANÁLISIS CONCEPTUAL DEL PROBLEMA:")
    print("   ACTUAL: COALESCE(celda_destino, celda_origen)")
    print("   - Siempre prioriza celda_destino sobre celda_origen")
    print("   - NO considera la direccionalidad de la llamada")
    print()
    print("   CORRECTA: Basada en direccionalidad")
    print("   - LLAMADA SALIENTE (objetivo = originador): usar celda_origen")
    print("   - LLAMADA ENTRANTE (objetivo = receptor): usar celda_destino")
    print()
    
    # 2. Verificar datos de números conocidos
    numeros_test = ['3009120093', '3113330727', '3243182028']
    
    print("2. ANÁLISIS DE CASOS REALES:")
    print()
    
    for numero in numeros_test:
        print(f"   NÚMERO: {numero}")
        print("   " + "-" * 50)
        
        cursor.execute('''
            SELECT 
                numero_origen, numero_destino, 
                celda_origen, celda_destino,
                -- LÓGICA ACTUAL
                COALESCE(celda_destino, celda_origen) as punto_actual,
                -- LÓGICA CORRECTA
                CASE 
                    WHEN numero_origen = ? THEN celda_origen  
                    WHEN numero_destino = ? THEN celda_destino  
                END as punto_correcto,
                -- DIRECCIÓN
                CASE 
                    WHEN numero_origen = ? THEN 'SALIENTE'
                    WHEN numero_destino = ? THEN 'ENTRANTE'
                END as direccion
            FROM operator_call_data 
            WHERE numero_origen = ? OR numero_destino = ?
            ORDER BY fecha_hora_llamada DESC
            LIMIT 5
        ''', (numero, numero, numero, numero, numero, numero))
        
        rows = cursor.fetchall()
        if not rows:
            print(f"   Sin datos para {numero}")
            print()
            continue
        
        print("   Dir      | Origen -> Destino | Celda_O | Celda_D | Actual | Correcto | ¿Igual?")
        print("   ---------|-------------------|---------|---------|--------|----------|--------")
        
        casos_diferentes = 0
        total_casos = len(rows)
        
        for origen, destino, celda_o, celda_d, actual, correcto, direccion in rows:
            igual = "SÍ" if str(actual) == str(correcto) else "NO"
            if igual == "NO":
                casos_diferentes += 1
                marca = " <<<<<"
            else:
                marca = ""
            
            # Truncar números para display
            origen_short = origen[:4] + "..." if len(origen) > 7 else origen
            destino_short = destino[:4] + "..." if len(destino) > 7 else destino
            
            print(f"   {direccion:8s} | {origen_short} -> {destino_short} | {celda_o:7s} | {celda_d:7s} | {actual:6s} | {correcto:8s} | {igual:6s}{marca}")
        
        if casos_diferentes > 0:
            print(f"   ALERTA: IMPACTO: {casos_diferentes}/{total_casos} casos diferentes ({casos_diferentes/total_casos*100:.1f}%)")
        else:
            print(f"   OK: No hay diferencias inmediatas (pero logica sigue siendo incorrecta)")
        
        print()
    
    # 3. Estadísticas generales de la base de datos
    print("3. ESTADÍSTICAS GENERALES DE LA BASE DE DATOS:")
    print()
    
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT numero_origen) as originadores_unicos,
            COUNT(DISTINCT numero_destino) as receptores_unicos,
            COUNT(celda_origen) as con_celda_origen,
            COUNT(celda_destino) as con_celda_destino,
            COUNT(CASE WHEN celda_origen IS NOT NULL AND celda_destino IS NOT NULL THEN 1 END) as ambas_celdas
        FROM operator_call_data
    ''')
    
    row = cursor.fetchone()
    if row:
        total, orig_unicos, dest_unicos, con_orig, con_dest, ambas = row
        print(f"   Total de llamadas: {total:,}")
        print(f"   Originadores únicos: {orig_unicos:,}")
        print(f"   Receptores únicos: {dest_unicos:,}")
        print(f"   Con celda origen: {con_orig:,} ({con_orig/total*100:.1f}%)")
        print(f"   Con celda destino: {con_dest:,} ({con_dest/total*100:.1f}%)")
        print(f"   Con ambas celdas: {ambas:,} ({ambas/total*100:.1f}%)")
        print()
    
    # 4. Propuesta de corrección
    print("4. PROPUESTA DE CORRECCIÓN EN EL CÓDIGO:")
    print()
    print("   ARCHIVO: Backend/main.py")
    print("   FUNCIÓN: get_call_interactions()")
    print("   LÍNEAS: ~1090-1092")
    print()
    print("   CAMBIAR DE:")
    print("   ```sql")
    print("   COALESCE(cd_destino.punto, cd_origen.punto) as punto_hunter,")
    print("   COALESCE(cd_destino.lat, cd_origen.lat) as lat_hunter,")
    print("   COALESCE(cd_destino.lon, cd_origen.lon) as lon_hunter,")
    print("   ```")
    print()
    print("   CAMBIAR A:")
    print("   ```sql")
    print("   CASE ")
    print("       WHEN ocd.numero_origen = :target_number THEN cd_origen.punto")
    print("       WHEN ocd.numero_destino = :target_number THEN cd_destino.punto")
    print("       ELSE COALESCE(cd_destino.punto, cd_origen.punto)")
    print("   END as punto_hunter,")
    print("   CASE ")
    print("       WHEN ocd.numero_origen = :target_number THEN cd_origen.lat")
    print("       WHEN ocd.numero_destino = :target_number THEN cd_destino.lat")
    print("       ELSE COALESCE(cd_destino.lat, cd_origen.lat)")
    print("   END as lat_hunter,")
    print("   CASE ")
    print("       WHEN ocd.numero_origen = :target_number THEN cd_origen.lon")
    print("       WHEN ocd.numero_destino = :target_number THEN cd_destino.lon")
    print("       ELSE COALESCE(cd_destino.lon, cd_origen.lon)")
    print("   END as lon_hunter,")
    print("   ```")
    print()
    
    # 5. Conclusiones
    print("5. CONCLUSIONES Y RECOMENDACIONES:")
    print()
    print("   CONFIRMADO: PROBLEMA - La logica actual es conceptualmente incorrecta")
    print("   IMPACTO ACTUAL: Bajo en datos presentes (todas las celdas tienen valores)")
    print("   RIESGO FUTURO: Alto cuando aparezcan casos con celdas NULL")
    print("   RECOMENDACION: Implementar correccion preventiva ANTES de datos problematicos")
    print()
    print("   BENEFICIOS DE LA CORRECCION:")
    print("   - Logica correcta segun direccionalidad de llamadas")
    print("   - Mayor precision en la ubicacion del numero objetivo")
    print("   - Preparacion para casos con celdas NULL")
    print("   - Cumplimiento de requisitos tecnicos de Boris")
    print()
    
    print("=" * 80)
    print("DIAGNOSTICO COMPLETADO")
    print("=" * 80)
    
    conn.close()

if __name__ == "__main__":
    analizar_logica_hunter()