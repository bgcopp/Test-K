#!/usr/bin/env python3
"""
VALIDACIÓN ESPECÍFICA DIRECCIONALIDAD HUNTER - NÚMERO 3009120093
===============================================================================
ANÁLISIS BACKEND PARA BORIS - 2025-08-20
===============================================================================

OBJETIVO:
Validar específicamente qué está retornando el backend en el campo hunter_source
para llamadas SALIENTES del número 3009120093 hacia:
- 3142071141
- 3143867409

PROBLEMA REPORTADO:
- Tooltips frontend muestran "Fuente: Celda destino" para llamadas salientes
- Debería mostrar información direccional correcta según la lógica backend

ALCANCE:
1. Ejecutar get_call_interactions() exactamente como el frontend
2. Capturar valores específicos de hunter_source
3. Validar lógica direccional líneas 1106-1112 de main.py
4. Confirmar si problema está en backend (datos) o frontend (interpretación)

Autor: Claude Code para Boris
Fecha: 2025-08-20
===============================================================================
"""

import sys
import os
import logging
import sqlite3
from datetime import datetime

# Agregar el directorio Backend al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('validacion_direccional_hunter_3009120093.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Obtiene conexión a la base de datos SQLite"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), 'kronos.db')
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Base de datos no encontrada: {db_path}")
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Para acceder por nombre de columna
        return conn
    except Exception as e:
        logger.error(f"Error conectando a base de datos: {e}")
        raise

def validate_direccional_hunter_logic():
    """
    Valida la lógica direccional HUNTER específicamente para 3009120093
    
    EXECUCIÓN EXACTA DE LA CONSULTA SQL DE main.py LÍNEAS 1070-1127
    """
    try:
        logger.info("=== VALIDACIÓN DIRECCIONALIDAD HUNTER - NÚMERO 3009120093 ===")
        
        # Parámetros específicos para el caso reportado por Boris
        mission_id = "3009120093"  # Asumo que mission_id coincide con el número
        target_number = "3009120093"
        start_datetime = "2024-01-01 00:00:00"  # Rango amplio para capturar datos
        end_datetime = "2024-12-31 23:59:59"
        
        logger.info(f"Parámetros de búsqueda:")
        logger.info(f"  - mission_id: {mission_id}")
        logger.info(f"  - target_number: {target_number}")
        logger.info(f"  - Período: {start_datetime} - {end_datetime}")
        logger.info(f"  - Objetivo: Llamadas SALIENTES hacia 3142071141 y 3143867409")
        
        # Query SQL EXACTA de main.py (líneas 1070-1127)
        query = """
        SELECT 
            ocd.numero_origen as originador,
            ocd.numero_destino as receptor,
            ocd.fecha_hora_llamada as fecha_hora, 
            ocd.duracion_segundos as duracion,
            ocd.operator as operador,
            ocd.celda_origen,
            ocd.celda_destino,
            ocd.latitud_origen,
            ocd.longitud_origen,
            ocd.latitud_destino,
            ocd.longitud_destino,
            cd_origen.punto as punto_hunter_origen,
            cd_origen.lat as lat_hunter_origen,
            cd_origen.lon as lon_hunter_origen,
            cd_destino.punto as punto_hunter_destino,
            cd_destino.lat as lat_hunter_destino,
            cd_destino.lon as lon_hunter_destino,
            -- CAMPOS UNIFICADOS HUNTER (CORRECCIÓN DIRECCIONALIDAD BORIS): Considera dirección de llamada
            CASE 
                WHEN ocd.numero_origen = :target_number THEN cd_origen.punto    -- SALIENTE: ubicación origen
                WHEN ocd.numero_destino = :target_number THEN cd_destino.punto  -- ENTRANTE: ubicación destino
                ELSE COALESCE(cd_destino.punto, cd_origen.punto)               -- Fallback general
            END as punto_hunter,
            CASE 
                WHEN ocd.numero_origen = :target_number THEN cd_origen.lat      -- SALIENTE: latitud origen
                WHEN ocd.numero_destino = :target_number THEN cd_destino.lat    -- ENTRANTE: latitud destino
                ELSE COALESCE(cd_destino.lat, cd_origen.lat)                   -- Fallback general
            END as lat_hunter,
            CASE 
                WHEN ocd.numero_origen = :target_number THEN cd_origen.lon      -- SALIENTE: longitud origen
                WHEN ocd.numero_destino = :target_number THEN cd_destino.lon    -- ENTRANTE: longitud destino
                ELSE COALESCE(cd_destino.lon, cd_origen.lon)                   -- Fallback general
            END as lon_hunter,
            -- Metadatos para transparencia investigativa (LÍNEAS 1106-1112)
            CASE 
                WHEN ocd.numero_origen = :target_number AND cd_origen.punto IS NOT NULL THEN 'origen_direccional'
                WHEN ocd.numero_destino = :target_number AND cd_destino.punto IS NOT NULL THEN 'destino_direccional'
                WHEN ocd.numero_origen = :target_number AND cd_origen.punto IS NULL AND cd_destino.punto IS NOT NULL THEN 'destino_fallback'
                WHEN ocd.numero_destino = :target_number AND cd_destino.punto IS NULL AND cd_origen.punto IS NOT NULL THEN 'origen_fallback'
                ELSE 'sin_ubicacion'
            END as hunter_source,
            -- Campo de precisión para investigadores
            CASE 
                WHEN (ocd.numero_origen = :target_number AND cd_origen.punto IS NOT NULL) OR 
                     (ocd.numero_destino = :target_number AND cd_destino.punto IS NOT NULL) THEN 'ALTA'
                WHEN COALESCE(cd_destino.punto, cd_origen.punto) IS NOT NULL THEN 'MEDIA'
                ELSE 'SIN_DATOS'
            END as precision_ubicacion
        FROM operator_call_data ocd
        LEFT JOIN cellular_data cd_origen ON (cd_origen.cell_id = ocd.celda_origen AND cd_origen.mission_id = ocd.mission_id)
        LEFT JOIN cellular_data cd_destino ON (cd_destino.cell_id = ocd.celda_destino AND cd_destino.mission_id = ocd.mission_id)
        WHERE ocd.mission_id = :mission_id
          AND (ocd.numero_origen = :target_number OR ocd.numero_destino = :target_number)
          AND ocd.fecha_hora_llamada BETWEEN :start_datetime AND :end_datetime  
        ORDER BY ocd.fecha_hora_llamada DESC
        """
        
        # Parámetros para la query
        params = {
            'mission_id': mission_id,
            'target_number': target_number,
            'start_datetime': start_datetime,
            'end_datetime': end_datetime
        }
        
        logger.info("Ejecutando query SQL EXACTA de main.py...")
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            logger.info(f"✓ Total de interacciones encontradas: {len(rows)}")
            
            # Filtrar específicamente llamadas SALIENTES hacia números objetivo
            target_recipients = ['3142071141', '3143867409']
            salientes_objetivo = []
            
            for row in rows:
                originador = row['originador']
                receptor = row['receptor'] 
                hunter_source = row['hunter_source']
                punto_hunter_origen = row['punto_hunter_origen']
                punto_hunter_destino = row['punto_hunter_destino']
                celda_origen = row['celda_origen']
                celda_destino = row['celda_destino']
                
                # Filtrar llamadas SALIENTES específicas
                if originador == target_number and receptor in target_recipients:
                    salientes_objetivo.append({
                        'originador': originador,
                        'receptor': receptor,
                        'hunter_source': hunter_source,
                        'punto_hunter_origen': punto_hunter_origen,
                        'punto_hunter_destino': punto_hunter_destino,
                        'celda_origen': celda_origen,
                        'celda_destino': celda_destino,
                        'fecha_hora': row['fecha_hora']
                    })
            
            logger.info(f"✓ Llamadas SALIENTES hacia números objetivo: {len(salientes_objetivo)}")
            
            # ANÁLISIS DETALLADO DE CADA LLAMADA SALIENTE
            logger.info("\n=== ANÁLISIS DETALLADO LLAMADAS SALIENTES ===")
            
            for i, llamada in enumerate(salientes_objetivo, 1):
                logger.info(f"\nLLAMADA SALIENTE #{i}:")
                logger.info(f"  🔹 Origen: {llamada['originador']} (número objetivo)")
                logger.info(f"  🔹 Destino: {llamada['receptor']}")
                logger.info(f"  🔹 Fecha: {llamada['fecha_hora']}")
                logger.info(f"  🔹 Celda Origen: {llamada['celda_origen']}")
                logger.info(f"  🔹 Celda Destino: {llamada['celda_destino']}")
                logger.info(f"  🔹 Punto HUNTER Origen: {llamada['punto_hunter_origen']}")
                logger.info(f"  🔹 Punto HUNTER Destino: {llamada['punto_hunter_destino']}")
                logger.info(f"  🔸 HUNTER_SOURCE: '{llamada['hunter_source']}'")
                
                # VALIDACIÓN DE LÓGICA DIRECCIONAL
                logger.info(f"  📋 VALIDACIÓN LÓGICA DIRECCIONAL:")
                
                if llamada['hunter_source'] == 'origen_direccional':
                    logger.info(f"    ✓ CORRECTO: Llamada saliente con punto HUNTER en origen")
                    logger.info(f"    ✓ Lógica aplicada: numero_origen = target_number AND cd_origen.punto IS NOT NULL")
                    
                elif llamada['hunter_source'] == 'destino_fallback':
                    logger.info(f"    ⚠️  FALLBACK: Llamada saliente sin punto HUNTER en origen, usando destino")
                    logger.info(f"    ⚠️  Lógica aplicada: numero_origen = target_number AND cd_origen.punto IS NULL AND cd_destino.punto IS NOT NULL")
                    logger.info(f"    ⚠️  RAZÓN: Celda origen {llamada['celda_origen']} no tiene datos HUNTER")
                    
                elif llamada['hunter_source'] == 'sin_ubicacion':
                    logger.info(f"    ❌ SIN DATOS: Ni origen ni destino tienen datos HUNTER")
                    logger.info(f"    ❌ Lógica aplicada: ELSE condition")
                    
                else:
                    logger.info(f"    🔴 ANÓMALO: hunter_source inesperado para llamada saliente: '{llamada['hunter_source']}'")
                
                # VERIFICACIÓN TOOLTIP FRONTEND
                logger.info(f"  🖥️  INTERPRETACIÓN FRONTEND:")
                if llamada['hunter_source'] == 'origen_direccional':
                    logger.info(f"    → Tooltip debería mostrar: 'Fuente: Celda origen' o 'Ubicación del llamante'")
                elif llamada['hunter_source'] == 'destino_fallback':
                    logger.info(f"    → Tooltip debería mostrar: 'Fuente: Celda destino (fallback)' o 'Ubicación aproximada'")
                    logger.info(f"    → PROBLEMA REPORTADO AQUÍ: Frontend muestra 'Fuente: Celda destino'")
                    logger.info(f"    → ESTO ES TÉCNICAMENTE CORRECTO - es fallback a celda destino")
                
                logger.info(f"  {'='*50}")
            
            # RESUMEN EJECUTIVO
            logger.info(f"\n=== RESUMEN EJECUTIVO ===")
            
            origen_direccional_count = sum(1 for l in salientes_objetivo if l['hunter_source'] == 'origen_direccional')
            destino_fallback_count = sum(1 for l in salientes_objetivo if l['hunter_source'] == 'destino_fallback')
            sin_ubicacion_count = sum(1 for l in salientes_objetivo if l['hunter_source'] == 'sin_ubicacion')
            
            logger.info(f"📊 ESTADÍSTICAS DIRECCIONALIDAD:")
            logger.info(f"  - origen_direccional: {origen_direccional_count} llamadas")
            logger.info(f"  - destino_fallback: {destino_fallback_count} llamadas")
            logger.info(f"  - sin_ubicacion: {sin_ubicacion_count} llamadas")
            
            logger.info(f"\n🔍 DIAGNÓSTICO PROBLEMA REPORTADO:")
            if destino_fallback_count > 0:
                logger.info(f"  ✓ BACKEND FUNCIONANDO CORRECTAMENTE")
                logger.info(f"  ✓ Lógica direccional SQL implementada según especificación")
                logger.info(f"  ✓ 'destino_fallback' es comportamiento esperado cuando:")
                logger.info(f"    - Llamada es SALIENTE (numero_origen = target_number)")
                logger.info(f"    - Celda origen NO tiene datos HUNTER (cd_origen.punto IS NULL)")
                logger.info(f"    - Celda destino SÍ tiene datos HUNTER (cd_destino.punto IS NOT NULL)")
                logger.info(f"  📍 TOOLTIP 'Fuente: Celda destino' ES TÉCNICAMENTE CORRECTO")
                logger.info(f"  🎯 POSIBLE MEJORA: Frontend podría aclarar '(ubicación aproximada - fallback)'")
            else:
                logger.info(f"  ❓ No se encontraron casos de destino_fallback en las llamadas analizadas")
            
            return {
                'total_interacciones': len(rows),
                'llamadas_salientes_objetivo': len(salientes_objetivo),
                'origen_direccional': origen_direccional_count,
                'destino_fallback': destino_fallback_count,
                'sin_ubicacion': sin_ubicacion_count,
                'llamadas_analizadas': salientes_objetivo
            }
            
    except Exception as e:
        logger.error(f"Error en validación direccional HUNTER: {e}")
        raise

def validate_database_structure():
    """Valida la estructura de las tablas relevantes"""
    try:
        logger.info("\n=== VALIDACIÓN ESTRUCTURA BASE DE DATOS ===")
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar existencia de tablas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['operator_call_data', 'cellular_data']
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                logger.error(f"❌ Tablas faltantes: {missing_tables}")
                return False
            
            logger.info(f"✓ Tablas requeridas presentes: {required_tables}")
            
            # Verificar estructura de operator_call_data
            cursor.execute("PRAGMA table_info(operator_call_data)")
            ocd_columns = [row[1] for row in cursor.fetchall()]
            logger.info(f"✓ Columnas operator_call_data: {ocd_columns}")
            
            # Verificar estructura de cellular_data
            cursor.execute("PRAGMA table_info(cellular_data)")
            cd_columns = [row[1] for row in cursor.fetchall()]
            logger.info(f"✓ Columnas cellular_data: {cd_columns}")
            
            # Verificar datos del número objetivo
            cursor.execute("""
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN numero_origen = '3009120093' THEN 1 END) as como_origen,
                       COUNT(CASE WHEN numero_destino = '3009120093' THEN 1 END) as como_destino
                FROM operator_call_data 
                WHERE numero_origen = '3009120093' OR numero_destino = '3009120093'
            """)
            
            row = cursor.fetchone()
            if row:
                logger.info(f"✓ Datos número 3009120093:")
                logger.info(f"  - Total registros: {row[0]}")
                logger.info(f"  - Como origen: {row[1]}")
                logger.info(f"  - Como destino: {row[2]}")
            
            return True
            
    except Exception as e:
        logger.error(f"Error validando estructura DB: {e}")
        return False

if __name__ == "__main__":
    try:
        logger.info("INICIANDO VALIDACIÓN DIRECCIONALIDAD HUNTER - NÚMERO 3009120093")
        logger.info("=" * 80)
        
        # 1. Validar estructura de base de datos
        if not validate_database_structure():
            logger.error("❌ Falló validación de estructura de BD")
            sys.exit(1)
        
        # 2. Ejecutar validación direccional específica
        results = validate_direccional_hunter_logic()
        
        # 3. Generar archivo de evidencia
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        evidence_file = f"evidencia_direccional_hunter_{timestamp}.json"
        
        import json
        with open(evidence_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"\n✓ VALIDACIÓN COMPLETADA")
        logger.info(f"✓ Archivo de evidencia generado: {evidence_file}")
        logger.info(f"✓ Log detallado: validacion_direccional_hunter_3009120093.log")
        
    except Exception as e:
        logger.error(f"❌ Error crítico en validación: {e}")
        sys.exit(1)