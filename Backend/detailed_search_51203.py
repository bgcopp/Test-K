#!/usr/bin/env python3
"""
Búsqueda detallada del número 3143534707 en la celda 51203
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

def busqueda_detallada():
    """Búsqueda detallada del número en la celda 51203"""
    
    celda_objetivo = "51203"
    numero_objetivo = "3143534707"
    
    logger.info(f"=== BÚSQUEDA DETALLADA: {numero_objetivo} EN CELDA {celda_objetivo} ===")
    
    with get_database_manager().get_session() as session:
        # 1. Búsqueda exacta como originador
        query_origen = text("""
            SELECT *
            FROM operator_call_data 
            WHERE numero_origen = :numero 
              AND celda_origen = :celda
        """)
        
        result = session.execute(query_origen, {
            'numero': numero_objetivo,
            'celda': celda_objetivo
        })
        
        registros_origen = result.fetchall()
        logger.info(f"Como ORIGINADOR en celda {celda_objetivo}: {len(registros_origen)} registros")
        
        for i, row in enumerate(registros_origen):
            logger.info(f"  Registro {i+1}: ID={row[0]}, fecha={row[4]}, operator={row[3]}")
        
        # 2. Búsqueda exacta como receptor
        query_destino = text("""
            SELECT *
            FROM operator_call_data 
            WHERE numero_destino = :numero 
              AND celda_destino = :celda
        """)
        
        result = session.execute(query_destino, {
            'numero': numero_objetivo,
            'celda': celda_objetivo
        })
        
        registros_destino = result.fetchall()
        logger.info(f"Como RECEPTOR en celda {celda_objetivo}: {len(registros_destino)} registros")
        
        for i, row in enumerate(registros_destino):
            logger.info(f"  Registro {i+1}: ID={row[0]}, fecha={row[4]}, operator={row[3]}")
        
        # 3. Búsqueda amplia con LIKE
        query_like = text("""
            SELECT 
                id,
                numero_origen,
                numero_destino,
                celda_origen,
                celda_destino,
                fecha_hora_llamada,
                operator
            FROM operator_call_data 
            WHERE (numero_origen LIKE :numero_like OR numero_destino LIKE :numero_like)
              AND (celda_origen = :celda OR celda_destino = :celda)
        """)
        
        numero_like = f"%{numero_objetivo}%"
        result = session.execute(query_like, {
            'numero_like': numero_like,
            'celda': celda_objetivo
        })
        
        registros_like = result.fetchall()
        logger.info(f"Búsqueda amplia (LIKE) en celda {celda_objetivo}: {len(registros_like)} registros")
        
        for i, row in enumerate(registros_like):
            id_reg = row[0]
            num_orig = row[1]
            num_dest = row[2] 
            celda_orig = row[3]
            celda_dest = row[4]
            fecha = row[5]
            operator = row[6]
            
            # Determinar rol y celda correcta
            if num_orig and numero_objetivo in str(num_orig):
                rol = "ORIGINADOR"
                celda_rol = celda_orig
            elif num_dest and numero_objetivo in str(num_dest):
                rol = "RECEPTOR"
                celda_rol = celda_dest
            else:
                rol = "DESCONOCIDO"
                celda_rol = "N/A"
            
            logger.info(f"  Reg {i+1} (ID={id_reg}): {rol} - {num_orig}→{num_dest}, celdas {celda_orig}→{celda_dest}, {fecha}, {operator}")
        
        # 4. Verificar tipos de datos
        query_tipos = text("""
            SELECT 
                typeof(numero_origen) as tipo_origen,
                typeof(numero_destino) as tipo_destino,
                typeof(celda_origen) as tipo_celda_origen,
                typeof(celda_destino) as tipo_celda_destino,
                numero_origen,
                numero_destino,
                celda_origen,
                celda_destino
            FROM operator_call_data 
            WHERE (numero_origen LIKE :numero_like OR numero_destino LIKE :numero_like)
              AND (celda_origen = :celda OR celda_destino = :celda)
            LIMIT 5
        """)
        
        result = session.execute(query_tipos, {
            'numero_like': numero_like,
            'celda': celda_objetivo
        })
        
        tipos_data = result.fetchall()
        if tipos_data:
            logger.info(f"Verificación de tipos de datos:")
            for row in tipos_data:
                logger.info(f"  tipos: orig={row[0]}, dest={row[1]}, celda_orig={row[2]}, celda_dest={row[3]}")
                logger.info(f"  valores: {row[4]}→{row[5]}, celdas {row[6]}→{row[7]}")
        
        # 5. Contar todas las apariciones del número en cualquier celda
        query_total = text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN numero_origen = :numero THEN 1 END) as como_origen,
                COUNT(CASE WHEN numero_destino = :numero THEN 1 END) as como_destino
            FROM operator_call_data 
            WHERE numero_origen = :numero OR numero_destino = :numero
        """)
        
        result = session.execute(query_total, {'numero': numero_objetivo})
        totales = result.fetchone()
        
        logger.info(f"Total general del número {numero_objetivo}:")
        logger.info(f"  Total registros: {totales[0]}")
        logger.info(f"  Como originador: {totales[1]}")
        logger.info(f"  Como receptor: {totales[2]}")

if __name__ == "__main__":
    busqueda_detallada()