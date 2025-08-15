"""
KRONOS File Processor Service
===============================================================================
Servicio especializado en procesamiento de archivos Excel y CSV para datos
celulares y de operadores. Maneja decodificación base64, validación,
limpieza de datos y transformación a estructuras de la BD.

Características principales:
- Procesamiento de archivos Excel (.xlsx, .xls) y CSV
- Decodificación segura de archivos base64 desde frontend
- Validación y limpieza automática de datos
- Detección inteligente de estructura de columnas
- Transformación a modelos de BD
- Manejo robusto de errores de formato
- Logging detallado de procesamiento
- Optimización para grandes volúmenes de datos
===============================================================================
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from pathlib import Path
import chardet

from utils.helpers import (
    decode_base64_file, 
    read_excel_file, 
    read_csv_file,
    clean_dataframe,
    normalize_column_names,
    validate_dataframe_not_empty
)
from utils.validators import (
    validate_file_data,
    validate_cellular_data_record,
    validate_operator_data_record,
    ValidationError
)

logger = logging.getLogger(__name__)


class FileProcessorError(Exception):
    """Excepción personalizada para errores del procesador de archivos"""
    pass


class FileProcessor:
    """Procesador principal de archivos para KRONOS"""
    
    # Mapeo de columnas para datos celulares SCANHUNTER
    CELLULAR_COLUMN_MAPPING = {
        # Identificación (case-insensitive)
        'id': 'id',
        'Id': 'id',  # SCANHUNTER usa 'Id' con mayúscula
        'punto': 'punto',
        'Punto': 'punto',  # SCANHUNTER usa 'Punto' con mayúscula
        'punto_medicion': 'punto',
        'location': 'punto',
        
        # Coordenadas geográficas
        'latitud': 'lat',
        'Latitud': 'lat',  # SCANHUNTER usa 'Latitud' con mayúscula
        'latitude': 'lat',
        'lat': 'lat',
        'longitud': 'lon',
        'Longitud': 'lon',  # SCANHUNTER usa 'Longitud' con mayúscula
        'longitude': 'lon',
        'lng': 'lon',
        'lon': 'lon',
        
        # Información de red
        'mnc+mcc': 'mnc_mcc',
        'MNC+MCC': 'mnc_mcc',  # SCANHUNTER usa 'MNC+MCC' con mayúsculas
        'mncmcc': 'mnc_mcc',
        'mnc_mcc': 'mnc_mcc',
        'plmn': 'mnc_mcc',
        'operador': 'operator',
        'OPERADOR': 'operator',  # SCANHUNTER usa 'OPERADOR' con mayúsculas
        'operator': 'operator',
        'carrier': 'operator',
        'provider': 'operator',
        
        # Métricas de señal
        'rssi': 'rssi',
        'RSSI': 'rssi',  # SCANHUNTER usa 'RSSI' con mayúsculas
        'señal': 'rssi',
        'signal': 'rssi',
        'signal_strength': 'rssi',
        'intensidad': 'rssi',
        
        # Información técnica celular
        'tecnologia': 'tecnologia',
        'TECNOLOGIA': 'tecnologia',  # SCANHUNTER usa 'TECNOLOGIA' con mayúsculas
        'technology': 'tecnologia',
        'tech': 'tecnologia',
        'cellid': 'cell_id',
        'CELLID': 'cell_id',  # SCANHUNTER usa 'CELLID' con mayúsculas
        'cell_id': 'cell_id',
        'celda': 'cell_id',
        'lac o tac': 'lac_tac',
        'LAC o TAC': 'lac_tac',  # SCANHUNTER usa 'LAC o TAC' con mayúsculas
        'lac_o_tac': 'lac_tac',
        'lac_tac': 'lac_tac',
        'lac': 'lac_tac',
        'tac': 'lac_tac',
        'enb': 'enb',
        'ENB': 'enb',  # SCANHUNTER usa 'ENB' con mayúsculas
        'enodeb': 'enb',
        'channel': 'channel',
        'CHANNEL': 'channel',  # SCANHUNTER usa 'CHANNEL' con mayúsculas
        'canal': 'channel',
        'arfcn': 'channel',
        
        # Información adicional
        'comentario': 'comentario',
        'Comentario': 'comentario',  # SCANHUNTER usa 'Comentario' con mayúscula inicial
        'comment': 'comentario',
        'observaciones': 'comentario',
        'notes': 'comentario'
    }
    
    # Mapeo de columnas para datos de operador
    OPERATOR_COLUMN_MAPPING = {
        'id': 'operatorId',
        'operador_id': 'operatorId',
        'operator_id': 'operatorId',
        'nombre': 'name',
        'name': 'name',
        'operador': 'name',
        'operator': 'name',
        'torres': 'towers',
        'towers': 'towers',
        'antenas': 'towers',
        'antennas': 'towers',
        'cobertura': 'coverage',
        'coverage': 'coverage',
        'cover': 'coverage'
    }
    
    def __init__(self):
        pass
    
    def process_cellular_file(self, file_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Procesa archivo de datos celulares
        
        Args:
            file_data: {"name": "...", "content": "data:mime/type;base64,..."}
            
        Returns:
            Lista de registros de datos celulares validados
            
        Raises:
            FileProcessorError: Si hay errores en el procesamiento
        """
        try:
            logger.info(f"Iniciando procesamiento de archivo celular: {file_data.get('name', 'unknown')}")
            
            # Validar y decodificar archivo
            validated_file = validate_file_data(file_data)
            file_bytes, filename, mime_type = decode_base64_file(validated_file)
            
            # Leer archivo según tipo
            if mime_type in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                           'application/vnd.ms-excel']:
                df = read_excel_file(file_bytes)
            elif mime_type == 'text/csv':
                df = self._read_csv_with_encoding_detection(file_bytes)
            else:
                raise FileProcessorError(f"Tipo de archivo no soportado: {mime_type}")
            
            # Limpiar y normalizar
            df = self._clean_cellular_dataframe(df)
            
            # Validar que no esté vacío
            validate_dataframe_not_empty(df, "registros celulares")
            
            # Convertir a registros validados
            records = self._dataframe_to_cellular_records(df)
            
            logger.info(f"Procesamiento exitoso: {len(records)} registros celulares")
            return records
            
        except ValidationError as e:
            logger.warning(f"Error de validación procesando archivo celular: {e}")
            raise FileProcessorError(str(e))
        except FileProcessorError:
            raise
        except Exception as e:
            logger.error(f"Error inesperado procesando archivo celular: {e}")
            raise FileProcessorError(f"Error procesando archivo: {str(e)}")
    
    def process_operator_file(self, file_data: Dict[str, Any], sheet_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Procesa archivo de datos de operador
        
        Args:
            file_data: {"name": "...", "content": "data:mime/type;base64,..."}
            sheet_name: Nombre de la hoja específica para Excel (opcional)
            
        Returns:
            Lista de registros de datos de operador validados
            
        Raises:
            FileProcessorError: Si hay errores en el procesamiento
        """
        try:
            logger.info(f"Iniciando procesamiento de archivo operador: {file_data.get('name', 'unknown')}")
            
            # Validar y decodificar archivo
            validated_file = validate_file_data(file_data)
            file_bytes, filename, mime_type = decode_base64_file(validated_file)
            
            # Leer archivo según tipo
            if mime_type in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                           'application/vnd.ms-excel']:
                df = read_excel_file(file_bytes, sheet_name)
            elif mime_type == 'text/csv':
                df = self._read_csv_with_encoding_detection(file_bytes)
            else:
                raise FileProcessorError(f"Tipo de archivo no soportado: {mime_type}")
            
            # Limpiar y normalizar
            df = self._clean_operator_dataframe(df)
            
            # Validar que no esté vacío
            validate_dataframe_not_empty(df, "registros de operador")
            
            # Convertir a registros validados
            records = self._dataframe_to_operator_records(df)
            
            logger.info(f"Procesamiento exitoso: {len(records)} registros de operador")
            return records
            
        except ValidationError as e:
            logger.warning(f"Error de validación procesando archivo operador: {e}")
            raise FileProcessorError(str(e))
        except FileProcessorError:
            raise
        except Exception as e:
            logger.error(f"Error inesperado procesando archivo operador: {e}")
            raise FileProcessorError(f"Error procesando archivo: {str(e)}")
    
    def get_excel_sheet_names(self, file_data: Dict[str, Any]) -> List[str]:
        """
        Obtiene nombres de hojas de un archivo Excel
        
        Args:
            file_data: Datos del archivo Excel
            
        Returns:
            Lista de nombres de hojas
            
        Raises:
            FileProcessorError: Si hay errores leyendo el archivo
        """
        try:
            validated_file = validate_file_data(file_data)
            file_bytes, filename, mime_type = decode_base64_file(validated_file)
            
            if mime_type not in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                               'application/vnd.ms-excel']:
                raise FileProcessorError("El archivo no es un Excel válido")
            
            # Leer todas las hojas para obtener nombres
            excel_file = pd.ExcelFile(file_bytes)
            return excel_file.sheet_names
            
        except FileProcessorError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo hojas de Excel: {e}")
            raise FileProcessorError(f"Error leyendo archivo Excel: {str(e)}")
    
    def validate_cellular_file_structure(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida la estructura de un archivo de datos celulares sin procesarlo completamente
        
        Args:
            file_data: Datos del archivo
            
        Returns:
            Información sobre la estructura del archivo
        """
        try:
            validated_file = validate_file_data(file_data)
            file_bytes, filename, mime_type = decode_base64_file(validated_file)
            
            # Leer solo las primeras filas
            if mime_type in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                           'application/vnd.ms-excel']:
                df = read_excel_file(file_bytes).head(5)
            else:
                df = self._read_csv_with_encoding_detection(file_bytes).head(5)
            
            # Analizar columnas
            columns = list(df.columns)
            mapped_columns = self._map_cellular_columns(df)
            
            required_columns = ['lat', 'lon', 'signal', 'operator']
            missing_columns = [col for col in required_columns if col not in mapped_columns.columns]
            
            return {
                'filename': filename,
                'total_columns': len(columns),
                'original_columns': columns,
                'mapped_columns': list(mapped_columns.columns),
                'missing_columns': missing_columns,
                'is_valid': len(missing_columns) == 0,
                'sample_rows': len(df)
            }
            
        except Exception as e:
            logger.error(f"Error validando estructura de archivo celular: {e}")
            raise FileProcessorError(f"Error analizando archivo: {str(e)}")
    
    def validate_operator_file_structure(self, file_data: Dict[str, Any], sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Valida la estructura de un archivo de datos de operador
        
        Args:
            file_data: Datos del archivo
            sheet_name: Nombre de la hoja específica
            
        Returns:
            Información sobre la estructura del archivo
        """
        try:
            validated_file = validate_file_data(file_data)
            file_bytes, filename, mime_type = decode_base64_file(validated_file)
            
            # Leer solo las primeras filas
            if mime_type in ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                           'application/vnd.ms-excel']:
                df = read_excel_file(file_bytes, sheet_name).head(5)
            else:
                df = self._read_csv_with_encoding_detection(file_bytes).head(5)
            
            # Analizar columnas
            columns = list(df.columns)
            mapped_columns = self._map_operator_columns(df)
            
            required_columns = ['operatorId', 'name', 'towers', 'coverage']
            missing_columns = [col for col in required_columns if col not in mapped_columns.columns]
            
            return {
                'filename': filename,
                'sheet_name': sheet_name,
                'total_columns': len(columns),
                'original_columns': columns,
                'mapped_columns': list(mapped_columns.columns),
                'missing_columns': missing_columns,
                'is_valid': len(missing_columns) == 0,
                'sample_rows': len(df)
            }
            
        except Exception as e:
            logger.error(f"Error validando estructura de archivo operador: {e}")
            raise FileProcessorError(f"Error analizando archivo: {str(e)}")
    
    def _read_csv_with_encoding_detection(self, file_bytes: bytes) -> pd.DataFrame:
        """
        Lee CSV detectando automáticamente la codificación y delimitador
        
        Args:
            file_bytes: Contenido del archivo CSV
            
        Returns:
            DataFrame con los datos
        """
        logger.info(f"Iniciando detección de CSV. Tamaño del archivo: {len(file_bytes)} bytes")
        
        # Mostrar muestra del archivo para debugging
        try:
            sample = file_bytes[:500].decode('utf-8', errors='ignore')
            logger.info(f"Muestra del archivo (primeros 500 bytes): {repr(sample[:200])}")
        except:
            logger.info("No se pudo mostrar muestra del archivo")
        
        # Detectar encoding
        detected_encoding = chardet.detect(file_bytes)
        encoding = detected_encoding.get('encoding', 'utf-8')
        confidence = detected_encoding.get('confidence', 0)
        
        logger.info(f"Encoding detectado: {encoding} (confianza: {confidence:.2f})")
        
        # Intentar con el encoding detectado primero
        encodings_to_try = [encoding, 'utf-8', 'latin1', 'cp1252', 'iso-8859-1', 'windows-1252', 'utf-16', 'utf-8-sig']
        
        # Delimitadores a probar (punto y coma es prioritario para SCANHUNTER)
        delimiters_to_try = [';', ',', '\t', '|', ':', ' ']
        
        for enc in encodings_to_try:
            if enc is None:
                continue
                
            for delimiter in delimiters_to_try:
                try:
                    logger.debug(f"Probando encoding={enc}, delimiter='{delimiter}'")
                    
                    # Intentar leer como string primero
                    try:
                        text_content = file_bytes.decode(enc)
                        logger.debug(f"Archivo decodificado exitosamente con {enc}. Líneas encontradas: {len(text_content.splitlines())}")
                    except UnicodeDecodeError as e:
                        logger.debug(f"Error decodificando con {enc}: {e}")
                        continue
                    
                    # Intentar leer con pandas
                    df = read_csv_file(file_bytes, encoding=enc, delimiter=delimiter)
                    
                    logger.debug(f"CSV leído. Columnas: {len(df.columns)}, Filas: {len(df)}")
                    logger.debug(f"Nombres de columnas: {list(df.columns)}")
                    
                    # Verificar que el DataFrame tenga sentido
                    if len(df.columns) > 1 and len(df) > 0:
                        logger.info(f"✅ CSV leído exitosamente con encoding={enc}, delimiter='{delimiter}'")
                        logger.info(f"Resultado: {len(df)} filas, {len(df.columns)} columnas")
                        return df
                    elif len(df.columns) == 1:
                        logger.debug(f"Solo 1 columna encontrada con delimiter '{delimiter}', probando siguiente")
                    else:
                        logger.debug(f"DataFrame vacío con delimiter '{delimiter}'")
                        
                except Exception as e:
                    logger.debug(f"Error leyendo CSV con encoding {enc} y delimiter '{delimiter}': {e}")
                    continue
        
        # Si llegamos aquí, no pudimos leer el archivo
        logger.error("❌ No se pudo leer el archivo CSV con ninguna combinación")
        logger.error("Combinaciones probadas:")
        logger.error(f"  Encodings: {encodings_to_try}")
        logger.error(f"  Delimitadores: {delimiters_to_try}")
        
        # Intentar mostrar información adicional
        try:
            # Verificar si es realmente un CSV o si tiene BOM
            if file_bytes.startswith(b'\xef\xbb\xbf'):
                logger.error("  ⚠️ Archivo tiene BOM UTF-8")
            elif file_bytes.startswith(b'\xff\xfe') or file_bytes.startswith(b'\xfe\xff'):
                logger.error("  ⚠️ Archivo parece ser UTF-16")
                
            # Mostrar tipos de caracteres encontrados
            printable_chars = sum(1 for b in file_bytes[:1000] if 32 <= b <= 126)
            logger.error(f"  Caracteres imprimibles en primera muestra: {printable_chars}/1000")
            
        except Exception as e:
            logger.error(f"  Error obteniendo información adicional: {e}")
        
        raise FileProcessorError("No se pudo leer el archivo CSV con ninguna combinación de codificación y delimitador")
    
    def _clean_cellular_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia y normaliza DataFrame de datos celulares SCANHUNTER"""
        # Limpiar básico
        df = clean_dataframe(df, [])
        
        # Mapear columnas
        df = self._map_cellular_columns(df)
        
        # Verificar columnas requeridas para SCANHUNTER
        required_columns = ['punto', 'lat', 'lon', 'mnc_mcc', 'operator', 'rssi', 'tecnologia', 'cell_id']
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise FileProcessorError(f"Columnas faltantes en archivo SCANHUNTER: {', '.join(missing_columns)}")
        
        # Limpiar tipos de datos
        df = self._clean_scanhunter_data_types(df)
        
        return df
    
    def _clean_operator_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia y normaliza DataFrame de datos de operador"""
        # Limpiar básico
        df = clean_dataframe(df, [])
        
        # Mapear columnas
        df = self._map_operator_columns(df)
        
        # Verificar columnas requeridas
        required_columns = ['operatorId', 'name', 'towers', 'coverage']
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise FileProcessorError(f"Columnas faltantes en archivo operador: {', '.join(missing_columns)}")
        
        # Limpiar tipos de datos
        df = self._clean_operator_data_types(df)
        
        return df
    
    def _map_cellular_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Mapea columnas de datos celulares a nombres estándar"""
        return normalize_column_names(df, self.CELLULAR_COLUMN_MAPPING)
    
    def _map_operator_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Mapea columnas de datos de operador a nombres estándar"""
        return normalize_column_names(df, self.OPERATOR_COLUMN_MAPPING)
    
    def _clean_scanhunter_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia tipos de datos para columnas SCANHUNTER expandidas"""
        df_clean = df.copy()
        
        # Limpiar punto (identificador del punto de medición)
        df_clean['punto'] = df_clean['punto'].astype(str).str.strip()
        
        # Convertir coordenadas a float (SCANHUNTER usa coma decimal)
        for col in ['lat', 'lon']:
            if col in df_clean.columns:
                # Reemplazar comas por puntos para conversión correcta
                df_clean[col] = df_clean[col].astype(str).str.replace(',', '.', regex=False)
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        
        # Limpiar MNC+MCC (código de red)
        df_clean['mnc_mcc'] = df_clean['mnc_mcc'].astype(str).str.strip()
        
        # Limpiar operador como string
        df_clean['operator'] = df_clean['operator'].astype(str).str.strip()
        
        # Convertir RSSI a integer (valores negativos típicamente)
        df_clean['rssi'] = pd.to_numeric(df_clean['rssi'], errors='coerce').astype('Int64')
        
        # Limpiar tecnología
        df_clean['tecnologia'] = df_clean['tecnologia'].astype(str).str.strip().str.upper()
        
        # Limpiar Cell ID
        df_clean['cell_id'] = df_clean['cell_id'].astype(str).str.strip()
        
        # Campos opcionales - limpiar solo si existen
        if 'lac_tac' in df_clean.columns:
            df_clean['lac_tac'] = df_clean['lac_tac'].astype(str).str.strip()
            # Reemplazar valores vacíos o '0' con None
            df_clean['lac_tac'] = df_clean['lac_tac'].replace(['', '0', 'nan', 'None'], None)
        
        if 'enb' in df_clean.columns:
            df_clean['enb'] = df_clean['enb'].astype(str).str.strip()
            # Reemplazar valores vacíos o '0' con None
            df_clean['enb'] = df_clean['enb'].replace(['', '0', 'nan', 'None'], None)
        
        if 'channel' in df_clean.columns:
            df_clean['channel'] = df_clean['channel'].astype(str).str.strip()
            # Reemplazar valores vacíos con None
            df_clean['channel'] = df_clean['channel'].replace(['', 'nan', 'None'], None)
        
        if 'comentario' in df_clean.columns:
            df_clean['comentario'] = df_clean['comentario'].astype(str).str.strip()
            # Reemplazar valores vacíos con None
            df_clean['comentario'] = df_clean['comentario'].replace(['', 'nan', 'None'], None)
        
        # Eliminar filas con datos críticos faltantes
        critical_columns = ['punto', 'lat', 'lon', 'mnc_mcc', 'operator', 'rssi', 'tecnologia', 'cell_id']
        df_clean = df_clean.dropna(subset=critical_columns)
        
        return df_clean
    
    def _clean_operator_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia tipos de datos para columnas de operador"""
        df_clean = df.copy()
        
        # Limpiar strings
        for col in ['operatorId', 'name']:
            df_clean[col] = df_clean[col].astype(str).str.strip()
        
        # Convertir torres a integer
        df_clean['towers'] = pd.to_numeric(df_clean['towers'], errors='coerce').astype('Int64')
        
        # Limpiar coverage como string (mantener formato)
        df_clean['coverage'] = df_clean['coverage'].astype(str).str.strip()
        
        # Eliminar filas con datos críticos faltantes
        df_clean = df_clean.dropna(subset=['operatorId', 'name', 'towers', 'coverage'])
        
        return df_clean
    
    def _dataframe_to_cellular_records(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Convierte DataFrame a registros celulares SCANHUNTER validados"""
        records = []
        
        for index, row in df.iterrows():
            try:
                # Construir registro con todos los campos SCANHUNTER
                record_data = {
                    'file_record_id': int(row['id']) if pd.notna(row.get('id')) else None,  # ID original del archivo
                    'punto': row['punto'],
                    'lat': float(row['lat']),
                    'lon': float(row['lon']),
                    'mnc_mcc': str(row['mnc_mcc']),
                    'operator': str(row['operator']),
                    'rssi': int(row['rssi']),
                    'tecnologia': str(row['tecnologia']),
                    'cell_id': str(row['cell_id']),
                    'lac_tac': str(row['lac_tac']) if pd.notna(row.get('lac_tac')) else None,
                    'enb': str(row['enb']) if pd.notna(row.get('enb')) else None,
                    'channel': str(row['channel']) if pd.notna(row.get('channel')) else None,
                    'comentario': str(row['comentario']) if pd.notna(row.get('comentario')) else None
                }
                
                # Validar registro individual
                validated_record = validate_cellular_data_record(record_data)
                records.append(validated_record)
                
            except ValidationError as e:
                logger.warning(f"Registro celular SCANHUNTER inválido en fila {index + 1}: {e}")
                # Continuar con los demás registros
                continue
            except Exception as e:
                logger.error(f"Error procesando registro celular SCANHUNTER en fila {index + 1}: {e}")
                continue
        
        if not records:
            raise FileProcessorError("No se pudo procesar ningún registro válido del archivo SCANHUNTER")
        
        logger.info(f"Procesados {len(records)} de {len(df)} registros celulares SCANHUNTER")
        return records
    
    def _dataframe_to_operator_records(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Convierte DataFrame a registros de operador validados"""
        records = []
        
        for index, row in df.iterrows():
            try:
                record_data = {
                    'operatorId': row['operatorId'],
                    'name': row['name'],
                    'towers': row['towers'],
                    'coverage': row['coverage']
                }
                
                # Validar registro individual
                validated_record = validate_operator_data_record(record_data)
                records.append(validated_record)
                
            except ValidationError as e:
                logger.warning(f"Registro operador inválido en fila {index + 1}: {e}")
                # Continuar con los demás registros
                continue
            except Exception as e:
                logger.error(f"Error procesando registro operador en fila {index + 1}: {e}")
                continue
        
        if not records:
            raise FileProcessorError("No se pudo procesar ningún registro válido del archivo")
        
        logger.info(f"Procesados {len(records)} de {len(df)} registros de operador")
        return records


# Instancia global del procesador
file_processor = FileProcessor()


def get_file_processor() -> FileProcessor:
    """Retorna la instancia del procesador de archivos"""
    return file_processor