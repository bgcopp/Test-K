"""
KRONOS Utility Helpers
===============================================================================
Funciones auxiliares y utilidades comunes para el backend de KRONOS.
Incluye generadores de ID, conversores de datos, procesadores de archivos
base64 y otras funciones de soporte.

Características principales:
- Generación de IDs únicos
- Conversión de datos entre formatos
- Procesamiento de archivos base64
- Mapeo de estructuras de datos
- Funciones de fecha y tiempo
- Utilidades de serialización
===============================================================================
"""

import base64
import io
import json
import secrets
import string
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple
import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def generate_id(prefix: str = '', length: int = 12) -> str:
    """
    Genera un ID único alfanumérico
    
    Args:
        prefix: Prefijo opcional para el ID
        length: Longitud de la parte aleatoria
        
    Returns:
        ID único como string
    """
    # Generar string aleatorio seguro
    alphabet = string.ascii_letters + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    if prefix:
        return f"{prefix}_{random_part}"
    
    return random_part


def generate_user_id() -> str:
    """Genera ID único para usuarios"""
    return generate_id('user', 8)


def generate_role_id() -> str:
    """Genera ID único para roles"""
    return generate_id('role', 8)


def generate_mission_id() -> str:
    """Genera ID único para misiones"""
    return generate_id('mission', 8)




def generate_target_id(cell_id: Union[str, int], operator_id: str) -> str:
    """
    Genera ID único para registro de objetivo
    
    Args:
        cell_id: ID del registro celular
        operator_id: ID del operador
        
    Returns:
        ID único para el objetivo
    """
    return f"target_{cell_id}_{operator_id}_{generate_id(length=6)}"


def decode_base64_file(file_data: Dict[str, Any]) -> Tuple[bytes, str, str]:
    """
    Decodifica archivo en formato base64 desde el frontend
    
    Args:
        file_data: {"name": "...", "content": "data:mime/type;base64,..."}
        
    Returns:
        Tupla con (contenido_bytes, nombre_archivo, tipo_mime)
        
    Raises:
        ValueError: Si el formato es inválido
    """
    try:
        name = file_data.get('name', '')
        content = file_data.get('content', '')
        
        if not content or not content.startswith('data:'):
            raise ValueError("Formato de archivo inválido - debe ser data URL")
        
        if ',' not in content:
            raise ValueError("Formato de data URL inválido - falta separador")
        
        # Extraer tipo MIME y contenido base64
        content_type, content_string = content.split(',', 1)
        mime_type = content_type.split(';')[0].replace('data:', '')
        
        if not content_string.strip():
            raise ValueError("Contenido base64 vacío")
        
        # Decodificar base64 con validación
        try:
            decoded_bytes = base64.b64decode(content_string, validate=True)
        except Exception as decode_error:
            raise ValueError(f"Contenido base64 inválido: {str(decode_error)}")
        
        if len(decoded_bytes) == 0:
            raise ValueError("Archivo vacío después de decodificar")
        
        return decoded_bytes, name, mime_type
        
    except ValueError:
        # Re-lanzar errores de validación
        raise
    except Exception as e:
        logger.error(f"Error inesperado decodificando archivo base64: {e}")
        raise ValueError(f"Error procesando archivo: {str(e)}")


def create_file_like_object(decoded_bytes: bytes) -> io.BytesIO:
    """
    Crea un objeto file-like desde bytes para usar con pandas
    
    Args:
        decoded_bytes: Contenido del archivo como bytes
        
    Returns:
        Objeto BytesIO para usar con pandas
    """
    return io.BytesIO(decoded_bytes)


def _normalize_line_terminators(file_bytes: bytes) -> bytes:
    """
    Detecta y normaliza terminadores de línea problemáticos
    
    CORRECCIÓN CRÍTICA para archivos CLARO que usan CR (\r) únicamente,
    lo que causa que pandas malinterprete el archivo como una sola línea
    con 650,000+ caracteres en lugar de múltiples registros.
    
    Args:
        file_bytes: Contenido original del archivo
        
    Returns:
        Contenido con terminadores normalizados a LF (\n)
    """
    try:
        # Contar diferentes tipos de terminadores
        cr_count = file_bytes.count(b'\r')
        lf_count = file_bytes.count(b'\n')
        crlf_count = file_bytes.count(b'\r\n')
        
        # Determinar tipo predominante
        if crlf_count > 0:
            # Ya tiene CRLF, dejar como está
            terminator_type = 'CRLF'
            estimated_lines = crlf_count + 1
        elif lf_count > cr_count:
            # Ya tiene LF, dejar como está
            terminator_type = 'LF' 
            estimated_lines = lf_count + 1
        elif cr_count > 0:
            # PROBLEMA DETECTADO: Solo CR (archivos CLARO problemáticos)
            terminator_type = 'CR'
            estimated_lines = cr_count + 1
        else:
            # Archivo sin terminadores (probablemente muy pequeño)
            terminator_type = 'NONE'
            estimated_lines = 1
        
        # Log de diagnóstico
        logger.info(f"Line terminators detectados - Tipo: {terminator_type}, "
                   f"Líneas estimadas: {estimated_lines:,}, "
                   f"CR: {cr_count:,}, LF: {lf_count:,}, CRLF: {crlf_count:,}")
        
        # APLICAR CORRECCIÓN si es necesario
        if terminator_type == 'CR':
            logger.warning(f"CORRECCIÓN APLICADA: Archivo con terminadores CR únicos detected. "
                          f"Normalizando {cr_count:,} terminadores CR a LF")
            
            # Normalizar: CR -> LF (sin tocar CRLF existentes)
            # Primero preservar CRLF temporalmente
            content_normalized = file_bytes.replace(b'\r\n', b'\x00CRLF\x00')
            # Luego convertir CR restantes a LF
            content_normalized = content_normalized.replace(b'\r', b'\n')
            # Restaurar CRLF
            content_normalized = content_normalized.replace(b'\x00CRLF\x00', b'\r\n')
            
            # Verificar corrección
            new_lf_count = content_normalized.count(b'\n')
            logger.info(f"CORRECCIÓN COMPLETADA: {new_lf_count:,} terminadores LF después de normalización")
            
            return content_normalized
        else:
            # Archivo ya tiene terminadores correctos
            return file_bytes
            
    except Exception as e:
        logger.error(f"Error normalizando line terminators: {e}")
        # En caso de error, devolver el contenido original
        return file_bytes


def read_excel_file(file_bytes: bytes, sheet_name: Optional[str] = None) -> pd.DataFrame:
    """
    Lee archivo Excel desde bytes usando pandas
    
    Args:
        file_bytes: Contenido del archivo Excel
        sheet_name: Nombre de la hoja específica (opcional)
        
    Returns:
        DataFrame con los datos
        
    Raises:
        ValueError: Si hay error leyendo el archivo
    """
    try:
        file_obj = create_file_like_object(file_bytes)
        
        # Leer con pandas
        if sheet_name:
            df = pd.read_excel(file_obj, sheet_name=sheet_name)
        else:
            df = pd.read_excel(file_obj)
        
        return df
        
    except Exception as e:
        logger.error(f"Error leyendo archivo Excel: {e}")
        raise ValueError(f"Error leyendo archivo Excel: {str(e)}")


def read_csv_file(file_bytes: bytes, **kwargs) -> pd.DataFrame:
    """
    Lee archivo CSV desde bytes usando pandas con configuración robusta
    Incluye detección y normalización automática de line terminators
    
    Args:
        file_bytes: Contenido del archivo CSV
        **kwargs: Argumentos adicionales para pd.read_csv
        
    Returns:
        DataFrame con los datos
        
    Raises:
        ValueError: Si hay error leyendo el archivo
    """
    try:
        # CORRECCIÓN CRÍTICA: Detectar y normalizar line terminators
        normalized_bytes = _normalize_line_terminators(file_bytes)
        file_obj = create_file_like_object(normalized_bytes)
        
        # Configuración por defecto para CSVs más robusta
        default_kwargs = {
            'encoding': 'utf-8',
            'sep': ',',
            'skipinitialspace': True,
            'na_values': ['', 'NA', 'N/A', 'NULL', 'null', 'nan', 'NaN'],
            'keep_default_na': True,
            'dtype': str,  # Leer todo como string inicialmente
            'engine': 'python'  # Motor más flexible
        }
        
        # Mapear delimiter a sep para compatibilidad
        if 'delimiter' in kwargs:
            kwargs['sep'] = kwargs.pop('delimiter')
        
        default_kwargs.update(kwargs)
        
        logger.debug(f"Leyendo CSV con parámetros: {default_kwargs}")
        
        df = pd.read_csv(file_obj, **default_kwargs)
        
        # Limpiar nombres de columnas
        if len(df.columns) > 0:
            df.columns = df.columns.str.strip()
            df.columns = df.columns.str.replace('\n', ' ')
            df.columns = df.columns.str.replace('\r', ' ')
        
        logger.debug(f"CSV leído exitosamente: {len(df)} filas, columnas: {list(df.columns)}")
        return df
        
    except Exception as e:
        logger.error(f"Error leyendo archivo CSV: {e}")
        raise ValueError(f"Error leyendo archivo CSV: {str(e)}")


def clean_dataframe(df: pd.DataFrame, required_columns: List[str]) -> pd.DataFrame:
    """
    Limpia y valida un DataFrame
    
    Args:
        df: DataFrame a limpiar
        required_columns: Lista de columnas requeridas
        
    Returns:
        DataFrame limpio
        
    Raises:
        ValueError: Si faltan columnas requeridas
    """
    # Verificar columnas requeridas
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        raise ValueError(f"Columnas faltantes: {', '.join(missing_columns)}")
    
    # Remover filas completamente vacías y hacer copia explícita
    df_clean = df.dropna(how='all').copy()
    
    # Convertir a string y limpiar espacios en columnas de texto
    for col in df_clean.columns:
        if df_clean[col].dtype == 'object':
            df_clean.loc[:, col] = df_clean[col].astype(str).str.strip()
            # Reemplazar 'nan' string con NaN real
            df_clean.loc[:, col] = df_clean[col].replace('nan', pd.NA)
    
    return df_clean


def map_user_to_frontend(user_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mapea datos de usuario de BD a formato del frontend
    
    Args:
        user_dict: Diccionario con datos del usuario de BD
        
    Returns:
        Diccionario mapeado para el frontend
    """
    mapped = user_dict.copy()
    
    # Mapear campos específicos
    if 'role_id' in mapped:
        mapped['roleId'] = mapped.pop('role_id')
    
    # Remover campos sensibles
    mapped.pop('password_hash', None)
    
    # Convertir timestamps a strings si existen
    for field in ['created_at', 'updated_at', 'last_login']:
        if field in mapped and mapped[field]:
            if isinstance(mapped[field], datetime):
                mapped[field] = mapped[field].isoformat()
    
    return mapped


def map_mission_to_frontend(mission_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mapea datos de misión de BD a formato del frontend
    
    Args:
        mission_dict: Diccionario con datos de la misión de BD
        
    Returns:
        Diccionario mapeado para el frontend
    """
    mapped = mission_dict.copy()
    
    # Mapear campos específicos
    if 'start_date' in mapped:
        mapped['startDate'] = mapped.pop('start_date')
    
    if 'end_date' in mapped:
        mapped['endDate'] = mapped.pop('end_date')
    
    if 'created_by' in mapped:
        mapped['createdBy'] = mapped.pop('created_by')
    
    # Convertir timestamps a strings si existen
    for field in ['created_at', 'updated_at']:
        if field in mapped and mapped[field]:
            if isinstance(mapped[field], datetime):
                mapped[field] = mapped[field].isoformat()
    
    return mapped


def map_cellular_record_to_frontend(record_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mapea registro celular de BD a formato del frontend
    
    Args:
        record_dict: Diccionario con datos del registro de BD
        
    Returns:
        Diccionario mapeado para el frontend
    """
    mapped = record_dict.copy()
    
    # Convertir coordenadas a strings
    if 'lat' in mapped:
        mapped['lat'] = str(mapped['lat'])
    
    if 'lon' in mapped:
        mapped['lon'] = str(mapped['lon'])
    
    return mapped




def map_target_record_to_frontend(record_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mapea registro de objetivo de BD a formato del frontend
    
    Args:
        record_dict: Diccionario con datos del registro de BD
        
    Returns:
        Diccionario mapeado para el frontend
    """
    mapped = record_dict.copy()
    
    # Mapear campos específicos
    if 'target_id' in mapped:
        mapped['targetId'] = mapped.pop('target_id')
    
    if 'source_sheet' in mapped:
        mapped['sourceSheet'] = mapped.pop('source_sheet')
    
    # Convertir coordenadas a strings
    if 'lat' in mapped:
        mapped['lat'] = str(mapped['lat'])
    
    if 'lon' in mapped:
        mapped['lon'] = str(mapped['lon'])
    
    return mapped


def serialize_for_json(obj: Any) -> Any:
    """
    Serializa objetos para JSON manejando tipos especiales
    
    Args:
        obj: Objeto a serializar
        
    Returns:
        Objeto serializable para JSON
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, (set, frozenset)):
        return list(obj)
    elif hasattr(obj, 'to_dict'):
        return obj.to_dict()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    else:
        return obj


def safe_json_dumps(obj: Any, **kwargs) -> str:
    """
    JSON dumps seguro que maneja tipos especiales
    
    Args:
        obj: Objeto a serializar
        **kwargs: Argumentos adicionales para json.dumps
        
    Returns:
        String JSON
    """
    return json.dumps(obj, default=serialize_for_json, **kwargs)


def create_error_response(message: str, error_type: str = "error") -> Dict[str, str]:
    """
    Crea respuesta de error estándar
    
    Args:
        message: Mensaje de error
        error_type: Tipo de error
        
    Returns:
        Diccionario con error formateado
    """
    return {
        "error": error_type,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }


def create_success_response(data: Any = None, message: str = "success") -> Dict[str, Any]:
    """
    Crea respuesta de éxito estándar
    
    Args:
        data: Datos a incluir en la respuesta
        message: Mensaje de éxito
        
    Returns:
        Diccionario con respuesta formateada
    """
    response = {
        "status": "success",
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    
    return response


def get_current_timestamp() -> str:
    """Retorna timestamp actual en formato ISO"""
    return datetime.now().isoformat()


def normalize_column_names(df: pd.DataFrame, column_mapping: Dict[str, str] = None) -> pd.DataFrame:
    """
    Normaliza nombres de columnas de un DataFrame con mapeo case-insensitive
    
    Args:
        df: DataFrame a normalizar
        column_mapping: Mapeo personalizado de nombres de columnas (case-insensitive)
        
    Returns:
        DataFrame con columnas normalizadas
    """
    df_normalized = df.copy()
    
    # Aplicar mapeo personalizado case-insensitive si se proporciona
    if column_mapping:
        # Crear mapeo case-insensitive
        case_insensitive_mapping = {}
        
        for original_col in df_normalized.columns:
            # Normalizar el nombre original para búsqueda
            normalized_original = str(original_col).lower().strip()
            # También probar con espacios como underscores y sin espacios
            variants = [
                normalized_original,
                normalized_original.replace(' ', '_'),
                normalized_original.replace(' ', ''),
                normalized_original.replace('_', ' '),
                normalized_original.replace('+', '_')  # Para MNC+MCC
            ]
            
            # Buscar coincidencia en el mapeo
            for variant in variants:
                if variant in column_mapping:
                    case_insensitive_mapping[original_col] = column_mapping[variant]
                    logger.debug(f"Mapeando columna '{original_col}' -> '{column_mapping[variant]}' (variante: '{variant}')")
                    break
        
        df_normalized = df_normalized.rename(columns=case_insensitive_mapping)
        logger.info(f"Columnas mapeadas: {len(case_insensitive_mapping)}/{len(df.columns)}")
        logger.info(f"Columnas finales: {list(df_normalized.columns)}")
    
    return df_normalized


def validate_dataframe_not_empty(df: pd.DataFrame, entity_name: str = "datos") -> None:
    """
    Valida que un DataFrame no esté vacío
    
    Args:
        df: DataFrame a validar
        entity_name: Nombre de la entidad para el mensaje de error
        
    Raises:
        ValueError: Si el DataFrame está vacío
    """
    if df.empty:
        raise ValueError(f"No se encontraron {entity_name} válidos en el archivo")
    
    if len(df.index) == 0:
        raise ValueError(f"El archivo no contiene {entity_name}")


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Divide una lista en chunks de tamaño específico
    
    Args:
        lst: Lista a dividir
        chunk_size: Tamaño de cada chunk
        
    Returns:
        Lista de listas (chunks)
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def safe_get_nested(data: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    """
    Obtiene valor anidado de un diccionario de manera segura
    
    Args:
        data: Diccionario fuente
        keys: Lista de claves anidadas
        default: Valor por defecto si no se encuentra
        
    Returns:
        Valor encontrado o default
    """
    current = data
    try:
        for key in keys:
            current = current[key]
        return current
    except (KeyError, TypeError):
        return default


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula distancia aproximada entre dos puntos geográficos (fórmula haversine simplificada)
    
    Args:
        lat1, lon1: Coordenadas del primer punto
        lat2, lon2: Coordenadas del segundo punto
        
    Returns:
        Distancia en kilómetros (aproximada)
    """
    import math
    
    # Convertir a radianes
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Diferencias
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Fórmula haversine simplificada
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radio de la Tierra en km
    r = 6371
    
    return c * r