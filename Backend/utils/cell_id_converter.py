"""
KRONOS Cell ID Converter Utility
=====================================
Utilidades para extraer y convertir Cell ID y LAC desde columnas celda_origen
de archivos de operadores como Movistar.

Funcionalidades principales:
- Extracción de cellid y lac desde formato XXX-yyy
- Conversión de hexadecimal a decimal
- Validación de formatos

Author: KRONOS Development Team
Date: 2025-08-14
"""

import re
import logging
from typing import Dict, Optional, Tuple

# Configurar logger específico para este módulo
logger = logging.getLogger(__name__)

def extract_cellid_lac_from_celda_origen(celda_origen: str, operator: str = "MOVISTAR") -> Dict[str, Optional[int]]:
    """
    Extrae y convierte cellid y lac desde el campo celda_origen.
    Soporta múltiples formatos según el operador.
    
    Args:
        celda_origen (str): Campo celda_origen con Cell ID y LAC
        operator (str): Operador para determinar el formato
                       "MOVISTAR": XXX-yyy (ej: 07F083-05)
                       "TIGO": XXXXXXYY (ej: 010006CC)
    
    Returns:
        Dict[str, Optional[int]]: Diccionario con cellid_decimal y lac_decimal
                                 None si no se puede convertir
    
    Examples:
        >>> extract_cellid_lac_from_celda_origen("07F083-05", "MOVISTAR")
        {'cellid_decimal': 520323, 'lac_decimal': 5}
        
        >>> extract_cellid_lac_from_celda_origen("010006CC", "TIGO")
        {'cellid_decimal': 65542, 'lac_decimal': 204}
        
        >>> extract_cellid_lac_from_celda_origen("invalid")
        {'cellid_decimal': None, 'lac_decimal': None}
    """
    result = {'cellid_decimal': None, 'lac_decimal': None}
    
    if not celda_origen or pd.isna(celda_origen):
        logger.debug(f"celda_origen vacío o NaN: {celda_origen}")
        return result
    
    try:
        # Limpiar el string y convertir a string si no lo es
        celda_str = str(celda_origen).strip().upper()
        
        if operator.upper() == "MOVISTAR":
            # Formato MOVISTAR: XXX-yyy (con guión)
            pattern = r'^([A-F0-9]+)-([A-F0-9]+)$'
            match = re.match(pattern, celda_str)
            
            if match:
                cellid_hex = match.group(1)
                lac_hex = match.group(2)
            else:
                logger.warning(f"Formato MOVISTAR no reconocido: {celda_origen}")
                return result
                
        elif operator.upper() == "TIGO":
            # Formato TIGO: XXXXXXYY (8 caracteres, sin separador)
            if len(celda_str) == 8 and re.match(r'^[A-F0-9]{8}$', celda_str):
                cellid_hex = celda_str[:6]  # Primeros 6 caracteres
                lac_hex = celda_str[6:]     # Últimos 2 caracteres
            else:
                logger.warning(f"Formato TIGO no reconocido: {celda_origen} (debe ser 8 caracteres hex)")
                return result
                
        else:
            # Formato por defecto: intentar MOVISTAR primero, luego TIGO
            # Intentar formato MOVISTAR (con guión)
            movistar_pattern = r'^([A-F0-9]+)-([A-F0-9]+)$'
            movistar_match = re.match(movistar_pattern, celda_str)
            
            if movistar_match:
                cellid_hex = movistar_match.group(1)
                lac_hex = movistar_match.group(2)
            elif len(celda_str) == 8 and re.match(r'^[A-F0-9]{8}$', celda_str):
                # Intentar formato TIGO (8 caracteres)
                cellid_hex = celda_str[:6]
                lac_hex = celda_str[6:]
            else:
                logger.warning(f"Formato no reconocido para operador {operator}: {celda_origen}")
                return result
        
        # Convertir de hexadecimal a decimal
        cellid_decimal = int(cellid_hex, 16)
        lac_decimal = int(lac_hex, 16)
        
        result['cellid_decimal'] = cellid_decimal
        result['lac_decimal'] = lac_decimal
        
        logger.debug(f"Conversión exitosa ({operator}): {celda_origen} -> cellid={cellid_decimal}, lac={lac_decimal}")
        
    except ValueError as e:
        logger.error(f"Error convirtiendo valores hexadecimales en {celda_origen}: {e}")
    except Exception as e:
        logger.error(f"Error inesperado procesando {celda_origen}: {e}")
    
    return result


def validate_cellid_lac_format(celda_origen: str) -> bool:
    """
    Valida si el formato de celda_origen es correcto para extracción.
    
    Args:
        celda_origen (str): Campo a validar
    
    Returns:
        bool: True si el formato es válido, False en caso contrario
    """
    if not celda_origen or pd.isna(celda_origen):
        return False
    
    try:
        celda_str = str(celda_origen).strip()
        pattern = r'^([A-Fa-f0-9]+)-([A-Fa-f0-9]+)$'
        return bool(re.match(pattern, celda_str))
    except Exception:
        return False


def convert_hex_to_decimal(hex_value: str) -> Optional[int]:
    """
    Convierte un valor hexadecimal a decimal.
    
    Args:
        hex_value (str): Valor en hexadecimal
    
    Returns:
        Optional[int]: Valor decimal o None si hay error
    """
    try:
        return int(hex_value, 16)
    except (ValueError, TypeError):
        logger.error(f"Error convirtiendo valor hexadecimal: {hex_value}")
        return None


def process_movistar_cellular_data(df) -> None:
    """
    Procesa un DataFrame de Movistar para extraer cellid_decimal y lac_decimal.
    Modifica el DataFrame in-place agregando las nuevas columnas.
    
    Args:
        df: DataFrame de pandas con datos de Movistar que incluye columna celda_origen
    """
    import pandas as pd
    
    if 'celda_origen' not in df.columns:
        logger.warning("DataFrame no contiene columna celda_origen")
        return
    
    logger.info(f"Procesando {len(df)} registros para extraer cellid y lac")
    
    # Inicializar columnas
    df['cellid_decimal'] = None
    df['lac_decimal'] = None
    
    # Aplicar extracción y conversión
    for idx, row in df.iterrows():
        result = extract_cellid_lac_from_celda_origen(row['celda_origen'])
        df.at[idx, 'cellid_decimal'] = result['cellid_decimal']
        df.at[idx, 'lac_decimal'] = result['lac_decimal']
    
    # Estadísticas de procesamiento
    cellid_converted = df['cellid_decimal'].notna().sum()
    lac_converted = df['lac_decimal'].notna().sum()
    
    logger.info(f"Conversión completada: {cellid_converted}/{len(df)} cellid, {lac_converted}/{len(df)} lac")


def get_conversion_stats(df) -> Dict[str, int]:
    """
    Obtiene estadísticas de conversión de un DataFrame procesado.
    
    Args:
        df: DataFrame con columnas cellid_decimal y lac_decimal
    
    Returns:
        Dict[str, int]: Estadísticas de conversión
    """
    stats = {
        'total_records': len(df),
        'cellid_converted': 0,
        'lac_converted': 0,
        'conversion_errors': 0
    }
    
    if 'cellid_decimal' in df.columns:
        stats['cellid_converted'] = df['cellid_decimal'].notna().sum()
    
    if 'lac_decimal' in df.columns:
        stats['lac_converted'] = df['lac_decimal'].notna().sum()
    
    # Registros con celda_origen pero sin conversión exitosa
    if 'celda_origen' in df.columns:
        has_celda_origen = df['celda_origen'].notna().sum()
        converted = stats['cellid_converted']
        stats['conversion_errors'] = has_celda_origen - converted
    
    return stats


# Importar pandas al nivel del módulo para las funciones que lo necesitan
try:
    import pandas as pd
except ImportError:
    logger.warning("pandas no disponible - algunas funciones pueden fallar")
    pd = None