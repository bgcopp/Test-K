#!/usr/bin/env python3
"""
Verificar específicamente la celda 51203 y el número 3143534707
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

def verificar_celda_51203():
    """Verificación específica de la celda 51203"""
    
    celda_objetivo = "51203"
    numero_objetivo = "3143534707"
    
    logger.info(f"=== VERIFICACIÓN CELDA {celda_objetivo} ===")
    
    with get_database_manager().get_session() as session:
        # 1. Verificar si la celda 51203 existe en cellular_data (HUNTER)
        query_hunter = text("""
            SELECT COUNT(*) as count
            FROM cellular_data 
            WHERE cell_id = :celda
        """)
        
        result = session.execute(query_hunter, {'celda': celda_objetivo})
        hunter_count = result.fetchone()[0]
        
        if hunter_count > 0:
            logger.info(f"✓ Celda {celda_objetivo} SÍ existe en cellular_data HUNTER ({hunter_count} registros)")
        else:
            logger.error(f"✗ Celda {celda_objetivo} NO existe en cellular_data HUNTER")
        
        # 2. Verificar si hay llamadas en esta celda
        query_llamadas = text("""
            SELECT COUNT(*) as count
            FROM operator_call_data 
            WHERE (celda_origen = :celda OR celda_destino = :celda)
        """)
        
        result = session.execute(query_llamadas, {'celda': celda_objetivo})
        llamadas_count = result.fetchone()[0]
        logger.info(f"Total llamadas en celda {celda_objetivo}: {llamadas_count}")
        
        # 3. Verificar específicamente el número en esta celda
        query_numero_celda = text("""
            SELECT 
                'originador' as rol,
                numero_origen as numero,
                operator,
                fecha_hora_llamada,
                COUNT(*) as registros
            FROM operator_call_data 
            WHERE numero_origen = :numero 
              AND celda_origen = :celda
            GROUP BY numero_origen, operator, fecha_hora_llamada
            
            UNION ALL
            
            SELECT 
                'receptor' as rol,
                numero_destino as numero,
                operator,
                fecha_hora_llamada,
                COUNT(*) as registros
            FROM operator_call_data 
            WHERE numero_destino = :numero 
              AND celda_destino = :celda
            GROUP BY numero_destino, operator, fecha_hora_llamada
        """)
        
        result = session.execute(query_numero_celda, {
            'numero': numero_objetivo,
            'celda': celda_objetivo
        })
        
        registros_especificos = result.fetchall()
        
        if registros_especificos:
            logger.info(f"Registros del número {numero_objetivo} en celda {celda_objetivo}:")
            for row in registros_especificos:
                rol = row[0]
                numero = row[1]
                operador = row[2]
                fecha = row[3]
                count = row[4]
                logger.info(f"  Como {rol}: {count} reg, {operador}, {fecha}")
        else:
            logger.warning(f"NO se encontraron registros del número {numero_objetivo} en celda {celda_objetivo}")
        
        # 4. Buscar números similares en esta celda
        query_similares = text("""
            SELECT DISTINCT
                CASE 
                    WHEN numero_origen LIKE :numero_pattern THEN numero_origen
                    WHEN numero_destino LIKE :numero_pattern THEN numero_destino
                END as numero_similar,
                CASE 
                    WHEN numero_origen LIKE :numero_pattern THEN 'originador'
                    WHEN numero_destino LIKE :numero_pattern THEN 'receptor'
                END as rol
            FROM operator_call_data 
            WHERE (celda_origen = :celda OR celda_destino = :celda)
              AND (numero_origen LIKE :numero_pattern OR numero_destino LIKE :numero_pattern)
        """)
        
        numero_pattern = f"%{numero_objetivo[-7:]}%"  # Últimos 7 dígitos
        result = session.execute(query_similares, {
            'numero_pattern': numero_pattern,
            'celda': celda_objetivo
        })
        
        similares = result.fetchall()
        if similares:
            logger.info(f"Números similares a {numero_objetivo} en celda {celda_objetivo}:")
            for row in similares:
                numero_sim = row[0]
                rol = row[1]
                logger.info(f"  {numero_sim} como {rol}")
        
        # 5. Verificar todos los números que terminan en los mismos dígitos
        query_terminan = text("""
            SELECT DISTINCT
                CASE 
                    WHEN numero_origen LIKE :termina_en THEN numero_origen
                    WHEN numero_destino LIKE :termina_en THEN numero_destino
                END as numero,
                CASE 
                    WHEN numero_origen LIKE :termina_en THEN 'originador'
                    WHEN numero_destino LIKE :termina_en THEN 'receptor'
                END as rol
            FROM operator_call_data 
            WHERE (celda_origen = :celda OR celda_destino = :celda)
              AND (numero_origen LIKE :termina_en OR numero_destino LIKE :termina_en)
        """)
        
        termina_en = f"%{numero_objetivo[-4:]}"  # Últimos 4 dígitos
        result = session.execute(query_terminan, {
            'termina_en': termina_en,
            'celda': celda_objetivo
        })
        
        terminan_similar = result.fetchall()
        if terminan_similar:
            logger.info(f"Números que terminan en {numero_objetivo[-4:]} en celda {celda_objetivo}:")
            for row in terminan_similar:
                numero = row[0]
                rol = row[1]
                logger.info(f"  {numero} como {rol}")
        
        # 6. Lista completa de números en esta celda
        query_todos = text("""
            SELECT DISTINCT
                CASE 
                    WHEN numero_origen IS NOT NULL THEN numero_origen
                    WHEN numero_destino IS NOT NULL THEN numero_destino
                END as numero,
                COUNT(*) as registros
            FROM operator_call_data 
            WHERE (celda_origen = :celda OR celda_destino = :celda)
              AND (numero_origen IS NOT NULL OR numero_destino IS NOT NULL)
            GROUP BY numero
            ORDER BY registros DESC
            LIMIT 10
        """)
        
        result = session.execute(query_todos, {'celda': celda_objetivo})
        todos_numeros = result.fetchall()
        
        logger.info(f"Top 10 números más activos en celda {celda_objetivo}:")
        for row in todos_numeros:
            numero = row[0]
            registros = row[1]
            logger.info(f"  {numero}: {registros} registros")

if __name__ == "__main__":
    verificar_celda_51203()