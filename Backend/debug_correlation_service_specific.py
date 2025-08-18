#!/usr/bin/env python3
"""
Debug específico del servicio de correlación para el número 3143534707
Verificar si el problema está en la lógica de búsqueda o en la implementación
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import init_database, get_database_manager
from sqlalchemy import text
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Inicializar base de datos
init_database()

def debug_numero_especifico():
    """Debug específico para el número 3143534707"""
    
    numero_objetivo = "3143534707"
    celdas_esperadas = ["53591", "51438", "56124", "51203"]
    
    logger.info(f"=== DEBUG ESPECÍFICO NÚMERO {numero_objetivo} ===")
    
    with get_database_manager().get_session() as session:
        # 1. Verificar presencia del número en BD
        query_presencia = text("""
            SELECT COUNT(*) as total_registros
            FROM operator_call_data 
            WHERE (numero_origen = :numero OR numero_destino = :numero)
        """)
        
        result = session.execute(query_presencia, {'numero': numero_objetivo})
        total_registros = result.fetchone()[0]
        logger.info(f"Total registros del número en BD: {total_registros}")
        
        # 2. Verificar por rol (originador vs receptor)
        logger.info(f"\n--- ANÁLISIS POR ROL ---")
        
        # Como originador
        query_originador = text("""
            SELECT DISTINCT celda_origen, COUNT(*) as count
            FROM operator_call_data 
            WHERE numero_origen = :numero
              AND celda_origen IS NOT NULL
            GROUP BY celda_origen
            ORDER BY celda_origen
        """)
        
        result = session.execute(query_originador, {'numero': numero_objetivo})
        originador_data = result.fetchall()
        
        logger.info(f"Como ORIGINADOR:")
        for row in originador_data:
            celda = str(row[0])
            count = row[1]
            es_objetivo = "✓" if celda in celdas_esperadas else "✗"
            logger.info(f"  Celda origen {celda}: {count} registros {es_objetivo}")
        
        # Como receptor
        query_receptor = text("""
            SELECT DISTINCT celda_destino, COUNT(*) as count
            FROM operator_call_data 
            WHERE numero_destino = :numero
              AND celda_destino IS NOT NULL
            GROUP BY celda_destino
            ORDER BY celda_destino
        """)
        
        result = session.execute(query_receptor, {'numero': numero_objetivo})
        receptor_data = result.fetchall()
        
        logger.info(f"Como RECEPTOR:")
        for row in receptor_data:
            celda = str(row[0])
            count = row[1]
            es_objetivo = "✓" if celda in celdas_esperadas else "✗"
            logger.info(f"  Celda destino {celda}: {count} registros {es_objetivo}")
        
        # 3. Simular query del servicio dinámico
        logger.info(f"\n--- SIMULACIÓN QUERY SERVICIO DINÁMICO ---")
        
        # Obtener celdas HUNTER primero
        query_hunter = text("""
            SELECT DISTINCT cell_id
            FROM cellular_data 
            WHERE cell_id IS NOT NULL
        """)
        
        result = session.execute(query_hunter)
        hunter_cells = [str(row[0]) for row in result.fetchall()]
        hunter_cells_str = ','.join([f"'{cell}'" for cell in hunter_cells])
        
        logger.info(f"Total celdas HUNTER disponibles: {len(hunter_cells)}")
        
        # Query simulando el servicio dinámico
        query_dinamico = text(f"""
            WITH unique_correlations AS (
                -- Números como originadores
                SELECT 
                    numero_origen as numero,
                    operator as operador,
                    celda_origen as celda,
                    fecha_hora_llamada as fecha_hora
                FROM operator_call_data 
                WHERE celda_origen IN ({hunter_cells_str})
                  AND numero_origen = :numero
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
                WHERE celda_destino IN ({hunter_cells_str})
                  AND numero_destino = :numero
                  AND numero_destino IS NOT NULL
                  AND numero_destino != ''
            )
            SELECT 
                numero,
                operador,
                celda,
                COUNT(*) as registros_por_celda
            FROM unique_correlations
            GROUP BY numero, operador, celda
            ORDER BY celda
        """)
        
        result = session.execute(query_dinamico, {'numero': numero_objetivo})
        correlaciones_encontradas = result.fetchall()
        
        logger.info(f"Correlaciones encontradas por servicio dinámico:")
        celdas_encontradas = []
        for row in correlaciones_encontradas:
            numero = row[0]
            operador = row[1]
            celda = str(row[2])
            registros = row[3]
            es_objetivo = "✓" if celda in celdas_esperadas else "✗"
            celdas_encontradas.append(celda)
            logger.info(f"  {numero} ({operador}) en celda {celda}: {registros} reg {es_objetivo}")
        
        # 4. Verificar celdas objetivo específicamente
        logger.info(f"\n--- VERIFICACIÓN CELDAS OBJETIVO ---")
        for celda_objetivo in celdas_esperadas:
            query_celda = text("""
                SELECT 
                    'originador' as rol,
                    numero_origen as numero,
                    operator,
                    COUNT(*) as registros
                FROM operator_call_data 
                WHERE numero_origen = :numero 
                  AND celda_origen = :celda
                GROUP BY numero_origen, operator
                
                UNION ALL
                
                SELECT 
                    'receptor' as rol,
                    numero_destino as numero,
                    operator,
                    COUNT(*) as registros
                FROM operator_call_data 
                WHERE numero_destino = :numero 
                  AND celda_destino = :celda
                GROUP BY numero_destino, operator
            """)
            
            result = session.execute(query_celda, {
                'numero': numero_objetivo,
                'celda': celda_objetivo
            })
            
            registros_celda = result.fetchall()
            if registros_celda:
                logger.info(f"  Celda {celda_objetivo}:")
                for row in registros_celda:
                    rol = row[0]
                    numero = row[1]
                    operador = row[2]
                    count = row[3]
                    logger.info(f"    Como {rol}: {count} registros ({operador})")
            else:
                logger.warning(f"  Celda {celda_objetivo}: NO ENCONTRADA")
        
        # 5. Resumen de correlación
        logger.info(f"\n--- RESUMEN ---")
        logger.info(f"Celdas esperadas: {celdas_esperadas}")
        logger.info(f"Celdas encontradas: {sorted(celdas_encontradas)}")
        faltantes = set(celdas_esperadas) - set(celdas_encontradas)
        extras = set(celdas_encontradas) - set(celdas_esperadas)
        
        if faltantes:
            logger.error(f"Celdas FALTANTES: {list(faltantes)}")
        if extras:
            logger.warning(f"Celdas EXTRA: {list(extras)}")
        
        if set(celdas_esperadas) == set(celdas_encontradas):
            logger.info("✅ CORRELACIÓN CORRECTA - Todas las celdas encontradas")
        else:
            logger.error("❌ CORRELACIÓN INCORRECTA - Discrepancia detectada")

if __name__ == "__main__":
    debug_numero_especifico()