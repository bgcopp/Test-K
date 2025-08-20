"""
KRONOS - Servicio de Procesamiento de Archivos de Operadores
==========================================================

Este módulo maneja el procesamiento específico de archivos por operador,
implementando parsers especializados y validación robusta para cada formato.

Características principales:
- Procesamiento por chunks para archivos grandes
- Detección automática de encoding (UTF-8, Latin-1, etc.)
- Validación de estructura y contenido
- Manejo de errores granular por registro
- Soporte para CSV y XLSX
- Normalización automática de datos

Operadores soportados:
- CLARO: Datos por Celda, Llamadas Entrantes/Salientes
- MOVISTAR: Datos por Celda, Llamadas Salientes
- TIGO: Llamadas Mixtas (entrantes y salientes unificadas)
- WOM: Datos por celda y llamadas unificadas (entrantes/salientes)

Autor: Sistema KRONOS
Versión: 1.0.0
"""

import pandas as pd
import numpy as np
import io
import csv
from typing import Dict, List, Optional, Any, Tuple, Generator
import hashlib
import json
import re
from datetime import datetime
import sys
import os
from pathlib import Path
import chardet

# Agregar el directorio padre al path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db_connection
from services.data_normalizer_service import DataNormalizerService
from utils.operator_logger import OperatorLogger


class FileProcessorService:
    """
    Servicio especializado en procesamiento de archivos de operadores celulares.
    
    Implementa un patrón Strategy para diferentes tipos de archivos y operadores,
    con énfasis en robustez, performance y logging detallado.
    """
    
    def __init__(self):
        """Inicializa el servicio con dependencias."""
        self.data_normalizer = DataNormalizerService()
        self.logger = OperatorLogger()
        
        # Configuración de procesamiento
        self.CHUNK_SIZE = 1000  # Registros por lote
        self.MAX_ERRORS_PER_FILE = 100  # Máximo errores antes de abortar
        
        # Patrones de validación
        self.PHONE_PATTERN = re.compile(r'^57\d{10}$|^\d{10}$')  # Números colombianos
        self.DATE_PATTERN = re.compile(r'^\d{14}$')  # YYYYMMDDHHMMSS
        self.MOVISTAR_DATE_PATTERN = re.compile(r'^\d{14}$')  # YYYYMMDDHHMMSS (igual formato)
        
        # Encodings a probar en orden
        self.ENCODINGS_TO_TRY = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        self.logger.info("FileProcessorService inicializado")
    
    def _detect_encoding(self, file_bytes: bytes) -> str:
        """
        Detecta automáticamente el encoding del archivo.
        
        Args:
            file_bytes (bytes): Contenido del archivo
            
        Returns:
            str: Encoding detectado
        """
        try:
            # Usar chardet para detección automática
            detection = chardet.detect(file_bytes[:10000])  # Muestra de los primeros 10KB
            if detection and detection['confidence'] > 0.7:
                detected_encoding = detection['encoding']
                self.logger.debug(f"Encoding auto-detectado: {detected_encoding} (confianza: {detection['confidence']:.2f})")
                return detected_encoding
        except:
            pass
        
        # Fallback: probar encodings comunes
        for encoding in self.ENCODINGS_TO_TRY:
            try:
                file_bytes.decode(encoding)
                self.logger.debug(f"Encoding detectado por prueba: {encoding}")
                return encoding
            except UnicodeDecodeError:
                continue
        
        # Último recurso
        self.logger.warning("No se pudo detectar encoding, usando utf-8 con errores ignore")
        return 'utf-8'
    
    def _chunk_dataframe(self, dataframe, chunk_size):
        """
        Divide un DataFrame en chunks más pequeños para procesamiento eficiente.
        
        Args:
            dataframe (pd.DataFrame): DataFrame a dividir
            chunk_size (int): Tamaño de cada chunk
            
        Yields:
            pd.DataFrame: Chunks del DataFrame original
        """
        try:
            total_rows = len(dataframe)
            if total_rows == 0:
                return
                
            for start_idx in range(0, total_rows, chunk_size):
                end_idx = min(start_idx + chunk_size, total_rows)
                chunk_df = dataframe.iloc[start_idx:end_idx].copy()
                
                self.logger.debug(f"Generado chunk: filas {start_idx+1} a {end_idx} ({len(chunk_df)} registros)")
                yield chunk_df
                
        except Exception as e:
            self.logger.error(f"Error generando chunks del DataFrame: {e}")
            raise
    
    def _read_csv_robust(self, file_bytes: bytes, delimiter: str = ',') -> pd.DataFrame:
        """
        Lee un archivo CSV de forma robusta manejando diferentes encodings y formatos.
        
        Args:
            file_bytes (bytes): Contenido del archivo
            delimiter (str): Delimitador CSV
            
        Returns:
            pd.DataFrame: Datos leídos
        """
        encoding = self._detect_encoding(file_bytes)
        
        try:
            # Intentar lectura directa
            df = pd.read_csv(
                io.BytesIO(file_bytes),
                delimiter=delimiter,
                encoding=encoding,
                dtype=str,  # Leer todo como string inicialmente
                na_filter=False,  # No convertir a NaN automáticamente
                skipinitialspace=True,
                quoting=csv.QUOTE_MINIMAL
            )
            
            self.logger.debug(f"CSV leído exitosamente: {len(df)} filas, {len(df.columns)} columnas")
            return df
            
        except Exception as e:
            self.logger.warning(f"Error leyendo CSV con {encoding}: {e}")
            
            # Intentar con otros encodings
            for alt_encoding in self.ENCODINGS_TO_TRY:
                if alt_encoding == encoding:
                    continue
                
                try:
                    df = pd.read_csv(
                        io.BytesIO(file_bytes),
                        delimiter=delimiter,
                        encoding=alt_encoding,
                        dtype=str,
                        na_filter=False,
                        skipinitialspace=True,
                        quoting=csv.QUOTE_MINIMAL,
                        on_bad_lines='skip'  # Saltar líneas problemáticas
                    )
                    
                    self.logger.info(f"CSV leído con encoding alternativo {alt_encoding}: {len(df)} filas")
                    return df
                    
                except Exception:
                    continue
            
            # Último intento con manejo de errores
            try:
                df = pd.read_csv(
                    io.BytesIO(file_bytes),
                    delimiter=delimiter,
                    encoding='utf-8',
                    dtype=str,
                    na_filter=False,
                    skipinitialspace=True,
                    quoting=csv.QUOTE_MINIMAL,
                    on_bad_lines='skip',
                    error_bad_lines=False
                )
                
                self.logger.warning(f"CSV leído con manejo de errores: {len(df)} filas")
                return df
                
            except Exception as final_error:
                self.logger.error(f"Error crítico leyendo CSV: {final_error}")
                raise
    
    def _read_excel_robust(self, file_bytes: bytes, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """
        Lee un archivo Excel de forma robusta.
        
        Args:
            file_bytes (bytes): Contenido del archivo
            sheet_name (Optional[str]): Nombre de la hoja (None = primera hoja)
            
        Returns:
            pd.DataFrame: Datos leídos
        """
        try:
            df = pd.read_excel(
                io.BytesIO(file_bytes),
                sheet_name=sheet_name or 0,  # Primera hoja si no se especifica
                dtype=str,  # Leer todo como string
                na_filter=False,
                engine='openpyxl'
            )
            
            self.logger.debug(f"Excel leído exitosamente: {len(df)} filas, {len(df.columns)} columnas")
            return df
            
        except Exception as e:
            self.logger.error(f"Error leyendo Excel: {e}")
            raise
    
    def _validate_claro_cellular_columns(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Valida que el DataFrame tenga las columnas requeridas para datos celulares de CLARO.
        
        Expected columns: numero, fecha_trafico, tipo_cdr, celda_decimal, lac_decimal
        
        Args:
            df (pd.DataFrame): DataFrame a validar
            
        Returns:
            Tuple[bool, List[str]]: (Es válido, Lista de errores)
        """
        required_columns = ['numero', 'fecha_trafico', 'tipo_cdr', 'celda_decimal', 'lac_decimal']
        errors = []
        
        # Normalizar nombres de columnas (remover espacios, lowercaseear)
        df.columns = df.columns.str.strip().str.lower()
        
        # Verificar columnas requeridas
        missing_columns = []
        for col in required_columns:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            errors.append(f"Columnas faltantes: {', '.join(missing_columns)}")
        
        # Verificar que hay datos
        if len(df) == 0:
            errors.append("El archivo no contiene datos")
        
        # Verificar columnas con datos vacíos
        for col in required_columns:
            if col in df.columns:
                empty_count = df[col].isna().sum() + (df[col] == '').sum()
                if empty_count == len(df):
                    errors.append(f"La columna '{col}' está completamente vacía")
                elif empty_count > len(df) * 0.5:
                    errors.append(f"La columna '{col}' tiene {empty_count} valores vacíos de {len(df)} total")
        
        return len(errors) == 0, errors
    
    def _clean_claro_cellular_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpia y prepara los datos celulares de CLARO para procesamiento.
        
        Args:
            df (pd.DataFrame): DataFrame con datos brutos
            
        Returns:
            pd.DataFrame: DataFrame limpio
        """
        # Crear copia para no modificar original
        clean_df = df.copy()
        
        # Limpiar números telefónicos
        clean_df['numero'] = clean_df['numero'].astype(str).str.strip()
        clean_df['numero'] = clean_df['numero'].str.replace(r'[^\d]', '', regex=True)  # Solo dígitos
        
        # Limpiar fechas
        clean_df['fecha_trafico'] = clean_df['fecha_trafico'].astype(str).str.strip()
        clean_df['fecha_trafico'] = clean_df['fecha_trafico'].str.replace(r'[^\d]', '', regex=True)
        
        # Limpiar tipo CDR
        clean_df['tipo_cdr'] = clean_df['tipo_cdr'].astype(str).str.strip().str.upper()
        
        # Limpiar celdas y LAC (convertir a string para manejo consistente)
        clean_df['celda_decimal'] = clean_df['celda_decimal'].astype(str).str.strip()
        clean_df['lac_decimal'] = clean_df['lac_decimal'].astype(str).str.strip()
        
        # Remover filas completamente vacías
        clean_df = clean_df.dropna(how='all')
        
        # Remover filas donde campos críticos están vacíos
        critical_fields = ['numero', 'fecha_trafico', 'celda_decimal']
        for field in critical_fields:
            clean_df = clean_df[clean_df[field].notna()]
            clean_df = clean_df[clean_df[field] != '']
        
        self.logger.debug(f"Datos limpiados: {len(clean_df)} filas válidas")
        return clean_df
    
    def _validate_claro_call_columns(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Valida que el DataFrame tenga las columnas requeridas para datos de llamadas de CLARO.
        
        Expected columns: celda_inicio_llamada, celda_final_llamada, originador, receptor, fecha_hora, duracion, tipo
        
        Args:
            df (pd.DataFrame): DataFrame a validar
            
        Returns:
            Tuple[bool, List[str]]: (Es válido, Lista de errores)
        """
        required_columns = ['celda_inicio_llamada', 'celda_final_llamada', 'originador', 'receptor', 'fecha_hora', 'duracion', 'tipo']
        errors = []
        
        # Normalizar nombres de columnas (remover espacios, lowercaseear)
        df.columns = df.columns.str.strip().str.lower()
        
        # Verificar columnas requeridas
        missing_columns = []
        for col in required_columns:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            errors.append(f"Columnas faltantes: {', '.join(missing_columns)}")
        
        # Verificar que hay datos
        if len(df) == 0:
            errors.append("El archivo no contiene datos")
        
        # Verificar columnas con datos vacíos (para archivos de llamadas, ser más tolerante)
        for col in required_columns:
            if col in df.columns:
                empty_count = df[col].isna().sum() + (df[col] == '').sum()
                valid_count = len(df) - empty_count
                
                if empty_count == len(df):
                    errors.append(f"La columna '{col}' está completamente vacía")
                elif valid_count < 3:  # Requerir al menos 3 registros válidos para llamadas
                    errors.append(f"La columna '{col}' tiene muy pocos datos válidos: {valid_count} de {len(df)} total")
        
        return len(errors) == 0, errors
    
    def _clean_claro_call_data(self, df: pd.DataFrame, call_type: str = 'ENTRANTE') -> pd.DataFrame:
        """
        Limpia y prepara los datos de llamadas de CLARO para procesamiento.
        
        CORRECCIÓN BORIS: Proceso menos restrictivo para cargar TODOS los registros
        
        Args:
            df (pd.DataFrame): DataFrame con datos brutos
            call_type (str): Tipo de llamada ('ENTRANTE' o 'SALIENTE')
            
        Returns:
            pd.DataFrame: DataFrame limpio
        """
        # Crear copia para no modificar original
        clean_df = df.copy()
        
        # Limpiar números telefónicos de forma más permisiva
        clean_df['originador'] = clean_df['originador'].astype(str).str.strip()
        clean_df['originador'] = clean_df['originador'].str.replace(r'[^\d]', '', regex=True)  # Solo dígitos
        
        clean_df['receptor'] = clean_df['receptor'].astype(str).str.strip()
        clean_df['receptor'] = clean_df['receptor'].str.replace(r'[^\d]', '', regex=True)  # Solo dígitos
        
        # Limpiar fechas - mantener formato original para parseo posterior
        clean_df['fecha_hora'] = clean_df['fecha_hora'].astype(str).str.strip()
        
        # Limpiar tipo CDR de forma más permisiva
        clean_df['tipo'] = clean_df['tipo'].astype(str).str.strip().str.upper()
        
        # Limpiar celdas (convertir a string para manejo consistente)
        clean_df['celda_inicio_llamada'] = clean_df['celda_inicio_llamada'].astype(str).str.strip()
        clean_df['celda_final_llamada'] = clean_df['celda_final_llamada'].astype(str).str.strip()
        
        # Limpiar duración (convertir a numérico)
        clean_df['duracion'] = pd.to_numeric(clean_df['duracion'], errors='coerce').fillna(0).astype(int)
        
        # CORRECCIÓN: Remover SOLO filas completamente vacías, ser muy permisivo
        clean_df = clean_df.dropna(how='all')
        
        # CORRECCIÓN: Validación mucho más permisiva, solo campos absolutamente críticos
        # Solo validar que tengan al menos originador O receptor (no ambos)
        clean_df = clean_df[
            (clean_df['originador'].notna() & (clean_df['originador'] != '') & (clean_df['originador'] != 'nan')) |
            (clean_df['receptor'].notna() & (clean_df['receptor'] != '') & (clean_df['receptor'] != 'nan'))
        ]
        
        # CORRECCIÓN: NO filtrar por tipo de llamada para cargar TODOS los registros
        # Comentamos el filtrado para preservar TODOS los datos
        # if call_type == 'ENTRANTE':
        #     clean_df = clean_df[clean_df['tipo'].str.contains('CDR_ENTRANTE', na=False)]
        # elif call_type == 'SALIENTE':
        #     clean_df = clean_df[clean_df['tipo'].str.contains('CDR_SALIENTE', na=False)]
        
        self.logger.debug(f"Datos de llamadas limpiados (MODO PERMISIVO): {len(clean_df)} filas válidas (TODOS los tipos)")
        return clean_df
    
    def _validate_claro_call_record(self, record: Dict[str, Any], call_type: str = 'ENTRANTE') -> Tuple[bool, List[str]]:
        """
        Valida un registro individual de datos de llamadas de CLARO.
        
        CORRECCIÓN BORIS: Validación muy permisiva para no perder registros
        
        Args:
            record (Dict[str, Any]): Registro a validar
            call_type (str): Tipo de llamada ('ENTRANTE' o 'SALIENTE')
            
        Returns:
            Tuple[bool, List[str]]: (Es válido, Lista de errores)
        """
        errors = []
        
        # CORRECCIÓN: Validar número originador de forma MUY permisiva
        originador = str(record.get('originador', '')).strip()
        
        # CORRECCIÓN: Validar número receptor de forma MUY permisiva
        receptor = str(record.get('receptor', '')).strip()
        
        # Solo rechazar si AMBOS números están vacíos
        if (not originador or originador == 'nan' or len(originador) < 8) and \
           (not receptor or receptor == 'nan' or len(receptor) < 8):
            errors.append("Tanto originador como receptor están vacíos o son muy cortos")
        
        # CORRECCIÓN: Validación de números menos restrictiva
        if originador and originador != 'nan':
            if len(originador) > 15:
                errors.append(f"Número originador muy largo: {originador}")
            elif not originador.isdigit():
                errors.append(f"Número originador contiene caracteres no numéricos: {originador}")
        
        if receptor and receptor != 'nan':
            if len(receptor) > 15:
                errors.append(f"Número receptor muy largo: {receptor}")
            elif not receptor.isdigit():
                errors.append(f"Número receptor contiene caracteres no numéricos: {receptor}")
        
        # CORRECCIÓN: Validación de fecha MUY permisiva (solo verificar que no esté vacía)
        fecha_hora = str(record.get('fecha_hora', '')).strip()
        if not fecha_hora or fecha_hora == 'nan':
            # Solo warning, no error crítico
            pass
        
        # CORRECCIÓN: NO validar tipo CDR para cargar TODOS los registros
        # Comentamos la validación de tipo para preservar todos los datos
        # tipo = str(record.get('tipo', '')).strip().upper()
        # if not tipo:
        #     errors.append("Tipo CDR vacío")
        # elif call_type == 'ENTRANTE' and 'CDR_ENTRANTE' not in tipo:
        #     errors.append(f"Tipo CDR no es CDR_ENTRANTE: {tipo}")
        # elif call_type == 'SALIENTE' and 'CDR_SALIENTE' not in tipo:
        #     errors.append(f"Tipo CDR no es CDR_SALIENTE: {tipo}")
        
        # Validar duración
        duracion = record.get('duracion', 0)
        try:
            duracion_int = int(duracion)
            if duracion_int < 0:
                errors.append(f"Duración no puede ser negativa: {duracion_int}")
        except (ValueError, TypeError):
            errors.append(f"Duración debe ser numérica: {duracion}")
        
        # Validar celdas (pueden estar vacías en algunos casos)
        celda_inicio = str(record.get('celda_inicio_llamada', '')).strip()
        if celda_inicio and celda_inicio != 'nan' and not celda_inicio.replace('.', '').isdigit():
            errors.append(f"Celda inicio no numérica: {celda_inicio}")
        
        celda_final = str(record.get('celda_final_llamada', '')).strip()
        if celda_final and celda_final != 'nan' and not celda_final.replace('.', '').isdigit():
            errors.append(f"Celda final no numérica: {celda_final}")
        
        return len(errors) == 0, errors

    def _validate_claro_cellular_record(self, record: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida un registro individual de datos celulares de CLARO.
        
        Args:
            record (Dict[str, Any]): Registro a validar
            
        Returns:
            Tuple[bool, List[str]]: (Es válido, Lista de errores)
        """
        errors = []
        
        # Validar número telefónico
        numero = str(record.get('numero', '')).strip()
        if not numero:
            errors.append("Número telefónico vacío")
        elif len(numero) < 10:
            errors.append(f"Número telefónico muy corto: {numero}")
        elif len(numero) > 12:
            errors.append(f"Número telefónico muy largo: {numero}")
        elif not numero.isdigit():
            errors.append(f"Número telefónico contiene caracteres no numéricos: {numero}")
        
        # Validar fecha
        fecha = str(record.get('fecha_trafico', '')).strip()
        if not fecha:
            errors.append("Fecha de tráfico vacía")
        elif len(fecha) != 14:
            errors.append(f"Formato de fecha incorrecto (esperado YYYYMMDDHHMMSS): {fecha}")
        elif not fecha.isdigit():
            errors.append(f"Fecha contiene caracteres no numéricos: {fecha}")
        else:
            # Validar componentes de fecha
            try:
                year = int(fecha[:4])
                month = int(fecha[4:6])
                day = int(fecha[6:8])
                hour = int(fecha[8:10])
                minute = int(fecha[10:12])
                second = int(fecha[12:14])
                
                if not (2020 <= year <= 2030):
                    errors.append(f"Año fuera de rango válido: {year}")
                if not (1 <= month <= 12):
                    errors.append(f"Mes inválido: {month}")
                if not (1 <= day <= 31):
                    errors.append(f"Día inválido: {day}")
                if not (0 <= hour <= 23):
                    errors.append(f"Hora inválida: {hour}")
                if not (0 <= minute <= 59):
                    errors.append(f"Minuto inválido: {minute}")
                if not (0 <= second <= 59):
                    errors.append(f"Segundo inválido: {second}")
                    
            except ValueError:
                errors.append(f"Error parseando fecha: {fecha}")
        
        # Validar tipo CDR
        tipo_cdr = str(record.get('tipo_cdr', '')).strip().upper()
        if not tipo_cdr:
            errors.append("Tipo CDR vacío")
        elif tipo_cdr not in ['DATOS', 'DATA', 'SMS', 'MMS', 'VOZ', 'VOICE']:
            errors.append(f"Tipo CDR no reconocido: {tipo_cdr}")
        
        # Validar celda
        celda = str(record.get('celda_decimal', '')).strip()
        if not celda:
            errors.append("Celda decimal vacía")
        elif not celda.isdigit():
            errors.append(f"Celda decimal no numérica: {celda}")
        
        # Validar LAC (puede estar vacío en algunos casos)
        lac = str(record.get('lac_decimal', '')).strip()
        if lac and not lac.isdigit():
            errors.append(f"LAC decimal no numérico: {lac}")
        
        return len(errors) == 0, errors
    
    def _process_claro_cellular_chunk(self, chunk_df: pd.DataFrame, file_upload_id: str, 
                                    mission_id: str, chunk_number: int) -> Dict[str, Any]:
        """
        Procesa un chunk de datos celulares de CLARO.
        
        Args:
            chunk_df (pd.DataFrame): Chunk de datos a procesar
            file_upload_id (str): ID del archivo
            mission_id (str): ID de la misión
            chunk_number (int): Número del chunk para logging
            
        Returns:
            Dict[str, Any]: Resultado del procesamiento del chunk
        """
        records_processed = 0
        records_failed = 0
        records_duplicated = 0  # NUEVO: contador de duplicados
        validation_failed = 0   # NUEVO: contador de errores de validación
        other_errors = 0        # NUEVO: contador de otros errores
        failed_records = []
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                for index, row in chunk_df.iterrows():
                    try:
                        # Convertir fila a diccionario
                        record = row.to_dict()
                        
                        # Validar registro
                        is_valid, errors = self._validate_claro_cellular_record(record)
                        if not is_valid:
                            # CAMBIO: errores de validación se clasifican por separado
                            validation_failed += 1
                            records_failed += 1
                            failed_records.append({
                                'row': index + 1,
                                'errors': errors,
                                'type': 'validation',
                                'record': record
                            })
                            
                            if len(failed_records) > 10:  # Limitar detalle de errores
                                break
                            continue
                        
                        # Normalizar datos
                        normalized_data = self.data_normalizer.normalize_claro_cellular_data(
                            record, file_upload_id, mission_id
                        )
                        
                        if not normalized_data:
                            validation_failed += 1
                            records_failed += 1
                            failed_records.append({
                                'row': index + 1,
                                'errors': ['Error en normalización'],
                                'type': 'normalization',
                                'record': record
                            })
                            continue
                        
                        # Verificar que existen los registros padre antes del INSERT
                        # para evitar FOREIGN KEY constraint failed
                        
                        # Verificar que file_upload_id existe en operator_data_sheets
                        cursor.execute("SELECT id FROM operator_data_sheets WHERE id = ?", 
                                     (normalized_data['file_upload_id'],))
                        if not cursor.fetchone():
                            raise Exception(f"file_upload_id '{normalized_data['file_upload_id']}' no existe en operator_data_sheets")
                        
                        # Verificar que mission_id existe en missions
                        cursor.execute("SELECT id FROM missions WHERE id = ?", 
                                     (normalized_data['mission_id'],))
                        if not cursor.fetchone():
                            raise Exception(f"mission_id '{normalized_data['mission_id']}' no existe en missions")
                        
                        # Insertar en base de datos
                        # cursor.execute("""
                        #     INSERT INTO operator_cellular_data (
                        #         file_upload_id, mission_id, operator, numero_telefono,
                        #         fecha_hora_inicio, celda_id, lac_tac, trafico_subida_bytes,
                        #         trafico_bajada_bytes, tecnologia, tipo_conexion, record_hash
                        #     ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        # """, (
                        #     normalized_data['file_upload_id'],
                        #     normalized_data['mission_id'],
                        #     normalized_data['operator'],
                        #     normalized_data['numero_telefono'],
                        #     normalized_data['fecha_hora_inicio'],
                        #     normalized_data['celda_id'],
                        #     normalized_data['lac_tac'],
                        #     normalized_data['trafico_subida_bytes'],
                        #     normalized_data['trafico_bajada_bytes'],
                        #     normalized_data['tecnologia'],
                        #     normalized_data['tipo_conexion'],
                        #     normalized_data['record_hash']
                        # ))

                        cursor.execute("""
                            INSERT INTO cellular_data (
                                mission_id, file_record_id, punto, lat, lon, mnc_mcc, operator,
                                rssi, tecnologia, cell_id, lac_tac, enb, 
                                comentario, channel, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        """, (
                            normalized_data['mission_id'],
                            normalized_data.get('file_record_id'),
                            normalized_data['punto'],
                            normalized_data['latitud'],
                            normalized_data['longitud'],
                            normalized_data['mnc_mcc'],
                            normalized_data['operator'],
                            normalized_data['rssi'],
                            normalized_data['tecnologia'],
                            normalized_data['cell_id'],
                            normalized_data['lac_tac'],
                            normalized_data['enb'],
                            normalized_data['comentario'],
                            normalized_data['channel']
                        ))
                        
                        records_processed += 1
                        
                    except Exception as e:
                        error_str = str(e)
                        
                        # NUEVO: Distinguir tipos de errores por mensaje
                        if "UNIQUE constraint failed" in error_str:
                            # Es un duplicado legítimo - NO cuenta como error para el límite
                            records_duplicated += 1
                            error_type = 'duplicate'
                            self.logger.debug(f"Registro duplicado omitido {index + 1} en chunk {chunk_number}: {error_str}")
                        else:
                            # Es un error real - SÍ cuenta para el límite de errores
                            other_errors += 1
                            records_failed += 1  # SOLO errores reales incrementan records_failed
                            error_type = 'database'
                            self.logger.error(f"Error procesando registro {index + 1} en chunk {chunk_number}: {e}")
                        
                        # Agregar a la lista de fallos (para debugging, pero no afecta límite de errores)
                        failed_records.append({
                            'row': index + 1,
                            'errors': [f'Error procesando registro: {error_str}'],
                            'type': error_type,
                            'record': record if 'record' in locals() else {}
                        })
                
                # Confirmar transacción del chunk
                conn.commit()
                
                self.logger.debug(
                    f"Chunk {chunk_number} procesado: {records_processed} exitosos, {records_failed} fallidos ({records_duplicated} duplicados, {validation_failed} validación, {other_errors} otros)"
                )
                
                return {
                    'success': True,
                    'records_processed': records_processed,
                    'records_failed': records_failed,
                    'records_duplicated': records_duplicated,      # NUEVO
                    'validation_failed': validation_failed,       # NUEVO
                    'other_errors': other_errors,                 # NUEVO
                    'failed_records': failed_records[:10]  # Limitar detalle
                }
                
        except Exception as e:
            self.logger.error(f"Error crítico procesando chunk {chunk_number}: {e}")
            return {
                'success': False,
                'error': str(e),
                'records_processed': records_processed,
                'records_failed': records_failed,
                'records_duplicated': records_duplicated,
                'validation_failed': validation_failed,
                'other_errors': other_errors
            }
    
    def _process_claro_call_chunk(self, chunk_df: pd.DataFrame, file_upload_id: str, 
                                mission_id: str, chunk_number: int, call_type: str = 'ENTRANTE') -> Dict[str, Any]:
        """
        Procesa un chunk de datos de llamadas de CLARO.
        
        Args:
            chunk_df (pd.DataFrame): Chunk de datos a procesar
            file_upload_id (str): ID del archivo
            mission_id (str): ID de la misión
            chunk_number (int): Número del chunk para logging
            call_type (str): Tipo de llamada ('ENTRANTE' o 'SALIENTE')
            
        Returns:
            Dict[str, Any]: Resultado del procesamiento del chunk
        """
        records_processed = 0
        records_failed = 0
        failed_records = []
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                for index, row in chunk_df.iterrows():
                    try:
                        # Convertir fila a diccionario
                        record = row.to_dict()
                        
                        # Validar registro
                        is_valid, errors = self._validate_claro_call_record(record, call_type)
                        if not is_valid:
                            records_failed += 1
                            failed_records.append({
                                'row': index + 1,
                                'errors': errors,
                                'record': record
                            })
                            
                            if len(failed_records) > 10:  # Limitar detalle de errores
                                break
                            continue
                        
                        # Normalizar datos según el tipo de llamada
                        if call_type == 'ENTRANTE':
                            normalized_data = self.data_normalizer.normalize_claro_call_data_entrantes(
                                record, file_upload_id, mission_id
                            )
                        elif call_type == 'SALIENTE':
                            normalized_data = self.data_normalizer.normalize_claro_call_data_salientes(
                                record, file_upload_id, mission_id
                            )
                        else:
                            # Fallback genérico
                            normalized_data = self.data_normalizer.normalize_claro_call_data(
                                record, file_upload_id, mission_id
                            )
                        
                        if not normalized_data:
                            records_failed += 1
                            failed_records.append({
                                'row': index + 1,
                                'errors': ['Error en normalización'],
                                'record': record
                            })
                            continue
                        
                        # Insertar en base de datos
                        cursor.execute("""
                            INSERT INTO operator_call_data (
                                file_upload_id, mission_id, operator, tipo_llamada,
                                numero_origen, numero_destino, numero_objetivo,
                                fecha_hora_llamada, duracion_segundos,
                                celda_origen, celda_destino, celda_objetivo,
                                latitud_origen, longitud_origen, latitud_destino, longitud_destino,
                                tecnologia, tipo_trafico, estado_llamada,
                                operator_specific_data, record_hash
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            normalized_data['file_upload_id'],
                            normalized_data['mission_id'],
                            normalized_data['operator'],
                            normalized_data['tipo_llamada'],
                            normalized_data['numero_origen'],
                            normalized_data['numero_destino'],
                            normalized_data['numero_objetivo'],
                            normalized_data['fecha_hora_llamada'],
                            normalized_data['duracion_segundos'],
                            normalized_data['celda_origen'],
                            normalized_data['celda_destino'],
                            normalized_data['celda_objetivo'],
                            normalized_data['latitud_origen'],
                            normalized_data['longitud_origen'],
                            normalized_data['latitud_destino'],
                            normalized_data['longitud_destino'],
                            normalized_data['tecnologia'],
                            normalized_data['tipo_trafico'],
                            normalized_data['estado_llamada'],
                            normalized_data['operator_specific_data'],
                            normalized_data['record_hash']
                        ))
                        
                        records_processed += 1
                        
                    except Exception as e:
                        records_failed += 1
                        failed_records.append({
                            'row': index + 1,
                            'errors': [f'Error procesando registro: {str(e)}'],
                            'record': record if 'record' in locals() else {}
                        })
                        
                        self.logger.error(
                            f"Error procesando registro {index + 1} en chunk {chunk_number}: {e}"
                        )
                
                # Confirmar transacción del chunk
                conn.commit()
                
                self.logger.debug(
                    f"Chunk {chunk_number} procesado: {records_processed} exitosos, {records_failed} fallidos"
                )
                
                return {
                    'success': True,
                    'records_processed': records_processed,
                    'records_failed': records_failed,
                    'failed_records': failed_records[:10]  # Limitar detalle
                }
                
        except Exception as e:
            self.logger.error(f"Error crítico procesando chunk {chunk_number}: {e}")
            return {
                'success': False,
                'error': str(e),
                'records_processed': records_processed,
                'records_failed': records_failed
            }
    
    def process_claro_data_por_celda(self, file_bytes: bytes, file_name: str,
                                   file_upload_id: str, mission_id: str) -> Dict[str, Any]:
        """
        Procesa un archivo de datos por celda de CLARO.
        
        Args:
            file_bytes (bytes): Contenido del archivo
            file_name (str): Nombre del archivo
            file_upload_id (str): ID único del archivo
            mission_id (str): ID de la misión
            
        Returns:
            Dict[str, Any]: Resultado del procesamiento
        """
        start_time = datetime.now()
        
        self.logger.info(
            f"Iniciando procesamiento CLARO datos por celda: {file_name}",
            extra={'file_size': len(file_bytes), 'file_upload_id': file_upload_id}
        )
        
        try:
            # === ETAPA 1: LECTURA DEL ARCHIVO ===
            
            # Determinar tipo de archivo
            file_extension = Path(file_name).suffix.lower()
            
            if file_extension == '.csv':
                # Para CLARO, el separador es ';'
                df = self._read_csv_robust(file_bytes, delimiter=';')
            elif file_extension == '.xlsx':
                df = self._read_excel_robust(file_bytes)
            else:
                return {
                    'success': False,
                    'error': f'Formato de archivo no soportado: {file_extension}'
                }
            
            self.logger.info(f"Archivo leído: {len(df)} registros, {len(df.columns)} columnas")
            
            # === ETAPA 2: VALIDACIÓN DE ESTRUCTURA ===
            
            is_valid_structure, structure_errors = self._validate_claro_cellular_columns(df)
            if not is_valid_structure:
                return {
                    'success': False,
                    'error': f'Estructura de archivo inválida: {"; ".join(structure_errors)}'
                }
            
            # === ETAPA 3: LIMPIEZA DE DATOS ===
            
            original_count = len(df)
            df = self._clean_claro_cellular_data(df)
            cleaned_count = len(df)
            
            if cleaned_count == 0:
                return {
                    'success': False,
                    'error': 'No quedaron registros válidos después de la limpieza'
                }
            
            if cleaned_count < original_count:
                self.logger.warning(
                    f"Se descartaron {original_count - cleaned_count} registros durante la limpieza"
                )
            
            # === ETAPA 4: PROCESAMIENTO POR CHUNKS ===
            
            total_processed = 0
            total_failed = 0
            total_duplicated = 0        # NUEVO: contador total de duplicados
            total_validation_failed = 0 # NUEVO: contador total de errores de validación
            total_other_errors = 0      # NUEVO: contador total de otros errores
            chunk_number = 0
            processing_errors = []
            
            # Procesar en chunks para manejar archivos grandes
            for start_idx in range(0, len(df), self.CHUNK_SIZE):
                chunk_number += 1
                end_idx = min(start_idx + self.CHUNK_SIZE, len(df))
                chunk_df = df.iloc[start_idx:end_idx]
                
                self.logger.debug(f"Procesando chunk {chunk_number}: registros {start_idx+1} a {end_idx}")
                
                chunk_result = self._process_claro_cellular_chunk(
                    chunk_df, file_upload_id, mission_id, chunk_number
                )
                
                if chunk_result.get('success', False):
                    total_processed += chunk_result.get('records_processed', 0)
                    total_failed += chunk_result.get('records_failed', 0)
                    total_duplicated += chunk_result.get('records_duplicated', 0)          # NUEVO
                    total_validation_failed += chunk_result.get('validation_failed', 0)  # NUEVO
                    total_other_errors += chunk_result.get('other_errors', 0)             # NUEVO
                    
                    # Acumular errores detallados (limitado)
                    if chunk_result.get('failed_records'):
                        processing_errors.extend(chunk_result['failed_records'][:5])
                        if len(processing_errors) > 20:  # Límite total de errores detallados
                            processing_errors = processing_errors[:20]
                
                else:
                    # Error crítico en el chunk
                    error_msg = chunk_result.get('error', 'Error desconocido en chunk')
                    self.logger.error(f"Error crítico en chunk {chunk_number}: {error_msg}")
                    
                    return {
                        'success': False,
                        'error': f'Error procesando datos (chunk {chunk_number}): {error_msg}',
                        'processedRecords': total_processed,
                        'records_failed': total_failed,
                        'records_duplicated': total_duplicated,
                        'records_validation_failed': total_validation_failed,
                        'records_other_errors': total_other_errors
                    }
                
                # Verificar si hay demasiados errores
                if total_failed > self.MAX_ERRORS_PER_FILE:
                    self.logger.error(f"Demasiados errores ({total_failed}), abortando procesamiento")
                    return {
                        'success': False,
                        'error': f'Demasiados errores en el archivo ({total_failed}). Verifique el formato.',
                        'processedRecords': total_processed,
                        'records_failed': total_failed
                    }
            
            # === ETAPA 5: RESULTADO FINAL ===
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Determinar éxito basado en ratio de registros procesados
            success_rate = (total_processed / (total_processed + total_failed)) * 100 if (total_processed + total_failed) > 0 else 0
            
            # NUEVA LÓGICA CON MÉTRICAS PRECISAS: usar contadores exactos de los chunks
            effective_failures = total_validation_failed + total_other_errors  # Solo errores reales, no duplicados
            effective_success_rate = (total_processed / (total_processed + effective_failures)) * 100 if (total_processed + effective_failures) > 0 else 0
            
            # NUEVA LÓGICA: Duplicados = comportamiento normal, no error
            is_successful = (
                total_processed > 0 and  # Se procesó al menos 1 registro único
                (effective_failures == 0 or effective_success_rate >= 80.0)  # Sin errores reales O tasa efectiva alta
            )
            
            result = {
                'success': is_successful,
                'processedRecords': total_processed,
                'records_failed': total_failed,
                'records_duplicated': total_duplicated,                    # NUEVO: contador exacto de duplicados
                'records_validation_failed': total_validation_failed,     # NUEVO: contador exacto de errores de validación
                'records_other_errors': total_other_errors,               # NUEVO: contador exacto de otros errores
                'success_rate': round(success_rate, 2),
                'processing_time_seconds': round(processing_time, 2),
                'details': {
                    'original_records': original_count,
                    'cleaned_records': cleaned_count,
                    'chunks_processed': chunk_number,
                    'processing_errors': processing_errors[:10],  # Limitar errores mostrados
                    'duplicate_analysis': {
                        'detected_duplicates': total_duplicated,
                        'validation_failures': total_validation_failed,
                        'other_failures': total_other_errors,
                        'duplicate_percentage': round((total_duplicated / total_failed) * 100, 1) if total_failed > 0 else 0
                    }
                }
            }
            
            if not is_successful:
                # Crear mensaje específico según tipo de problemas
                duplicate_percentage = (total_duplicated / total_failed) * 100 if total_failed > 0 else 0
                if duplicate_percentage >= 50.0:
                    result['error'] = f'Procesamiento incompleto: {total_processed}/{total_processed + total_failed} registros únicos procesados. {total_duplicated} registros duplicados omitidos ({duplicate_percentage:.1f}% del total de fallos). Verifique si el archivo contiene registros válidos adicionales.'
                else:
                    result['error'] = f'Tasa de procesamiento baja ({success_rate:.1f}%). Verifique el formato del archivo. Errores: {effective_failures} reales, {total_duplicated} duplicados.'
            
            self.logger.info(
                f"Procesamiento CLARO completado: {total_processed} exitosos, {total_failed} fallidos, {total_duplicated} duplicados ({success_rate:.1f}% éxito)"
            )
            
            # Actualizar tabla operator_data_sheets con conteo final
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    
                    processing_status = 'COMPLETED' if is_successful else 'FAILED'
                    
                    cursor.execute("""
                        UPDATE operator_data_sheets 
                        SET processing_status = ?, 
                            records_processed = ?, 
                            records_failed = ?,
                            processing_end_time = CURRENT_TIMESTAMP,
                            processing_duration_seconds = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (
                        processing_status,
                        total_processed,
                        total_failed,
                        int(processing_time),
                        file_upload_id
                    ))
                    
                    conn.commit()
                    
                    self.logger.info(f"Estado de procesamiento CLARO actualizado: {processing_status}")
            except Exception as update_error:
                self.logger.error(f"Error actualizando estado final CLARO: {update_error}")
            
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Error crítico procesando archivo CLARO: {str(e)}"
            
            self.logger.error(error_msg, exc_info=True)
            
            return {
                'success': False,
                'error': error_msg,
                'processing_time_seconds': round(processing_time, 2),
                'records_processed': 0,
                'records_failed': 0
            }
    
    def process_claro_llamadas_entrantes(self, file_bytes: bytes, file_name: str,
                                       file_upload_id: str, mission_id: str) -> Dict[str, Any]:
        """
        Procesa un archivo de llamadas entrantes de CLARO.
        
        Args:
            file_bytes (bytes): Contenido del archivo
            file_name (str): Nombre del archivo
            file_upload_id (str): ID único del archivo
            mission_id (str): ID de la misión
            
        Returns:
            Dict[str, Any]: Resultado del procesamiento
        """
        start_time = datetime.now()
        
        self.logger.info(
            f"Iniciando procesamiento CLARO llamadas entrantes: {file_name}",
            extra={'file_size': len(file_bytes), 'file_upload_id': file_upload_id}
        )
        
        try:
            # === ETAPA 1: LECTURA DEL ARCHIVO ===
            
            # Determinar tipo de archivo
            file_extension = Path(file_name).suffix.lower()
            
            if file_extension == '.csv':
                # Para CLARO llamadas entrantes, el separador es ','
                df = self._read_csv_robust(file_bytes, delimiter=',')
            elif file_extension == '.xlsx':
                df = self._read_excel_robust(file_bytes)
            else:
                return {
                    'success': False,
                    'error': f'Formato de archivo no soportado: {file_extension}'
                }
            
            self.logger.info(f"Archivo leído: {len(df)} registros, {len(df.columns)} columnas")
            
            # === ETAPA 2: VALIDACIÓN DE ESTRUCTURA ===
            
            is_valid_structure, structure_errors = self._validate_claro_call_columns(df)
            if not is_valid_structure:
                return {
                    'success': False,
                    'error': f'Estructura de archivo inválida: {"; ".join(structure_errors)}'
                }
            
            # === ETAPA 3: LIMPIEZA DE DATOS ===
            
            original_count = len(df)
            df = self._clean_claro_call_data(df, 'ENTRANTE')
            cleaned_count = len(df)
            
            if cleaned_count == 0:
                return {
                    'success': False,
                    'error': 'No quedaron registros válidos después de la limpieza (no se encontraron CDR_ENTRANTE)'
                }
            
            if cleaned_count < original_count:
                self.logger.warning(
                    f"Se descartaron {original_count - cleaned_count} registros durante la limpieza (solo CDR_ENTRANTE procesados)"
                )
            
            # === ETAPA 4: PROCESAMIENTO POR CHUNKS ===
            
            total_processed = 0
            total_failed = 0
            chunk_number = 0
            processing_errors = []
            
            # Procesar en chunks para manejar archivos grandes
            for start_idx in range(0, len(df), self.CHUNK_SIZE):
                chunk_number += 1
                end_idx = min(start_idx + self.CHUNK_SIZE, len(df))
                chunk_df = df.iloc[start_idx:end_idx]
                
                self.logger.debug(f"Procesando chunk {chunk_number}: registros {start_idx+1} a {end_idx}")
                
                chunk_result = self._process_claro_call_chunk(
                    chunk_df, file_upload_id, mission_id, chunk_number, 'ENTRANTE'
                )
                
                if chunk_result.get('success', False):
                    total_processed += chunk_result.get('records_processed', 0)
                    total_failed += chunk_result.get('records_failed', 0)
                    
                    # Acumular errores detallados (limitado)
                    if chunk_result.get('failed_records'):
                        processing_errors.extend(chunk_result['failed_records'][:5])
                        if len(processing_errors) > 20:  # Límite total de errores detallados
                            processing_errors = processing_errors[:20]
                
                else:
                    # Error crítico en el chunk
                    error_msg = chunk_result.get('error', 'Error desconocido en chunk')
                    self.logger.error(f"Error crítico en chunk {chunk_number}: {error_msg}")
                    
                    return {
                        'success': False,
                        'error': f'Error procesando datos (chunk {chunk_number}): {error_msg}',
                        'processedRecords': total_processed,
                        'records_failed': total_failed
                    }
                
                # Verificar si hay demasiados errores
                if total_failed > self.MAX_ERRORS_PER_FILE:
                    self.logger.error(f"Demasiados errores ({total_failed}), abortando procesamiento")
                    return {
                        'success': False,
                        'error': f'Demasiados errores en el archivo ({total_failed}). Verifique el formato.',
                        'processedRecords': total_processed,
                        'records_failed': total_failed
                    }
            
            # === ETAPA 5: RESULTADO FINAL ===
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Determinar éxito basado en ratio de registros procesados
            success_rate = (total_processed / (total_processed + total_failed)) * 100 if (total_processed + total_failed) > 0 else 0
            
            # NUEVA LÓGICA: Considerar exitoso si se procesó al menos 1 registro (duplicados = normal)
            is_successful = total_processed > 0
            
            result = {
                'success': is_successful,
                'processedRecords': total_processed,
                'records_failed': total_failed,
                'success_rate': round(success_rate, 2),
                'processing_time_seconds': round(processing_time, 2),
                'details': {
                    'original_records': original_count,
                    'cleaned_records': cleaned_count,
                    'chunks_processed': chunk_number,
                    'processing_errors': processing_errors[:10],  # Limitar errores mostrados
                    'file_type': 'CLARO_LLAMADAS_ENTRANTES'
                }
            }
            
            if not is_successful:
                result['error'] = f'Tasa de éxito baja ({success_rate:.1f}%). Verifique el formato del archivo.'
            
            self.logger.info(
                f"Procesamiento CLARO llamadas entrantes completado: {total_processed} exitosos, {total_failed} fallidos ({success_rate:.1f}% éxito)"
            )
            
            # Actualizar tabla operator_data_sheets con conteo final
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    
                    processing_status = 'COMPLETED' if is_successful else 'FAILED'
                    
                    cursor.execute("""
                        UPDATE operator_data_sheets 
                        SET processing_status = ?, 
                            records_processed = ?, 
                            records_failed = ?,
                            processing_end_time = CURRENT_TIMESTAMP,
                            processing_duration_seconds = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (
                        processing_status,
                        total_processed,
                        total_failed,
                        int(processing_time),
                        file_upload_id
                    ))
                    
                    conn.commit()
                    
                    self.logger.info(f"Estado de procesamiento CLARO llamadas entrantes actualizado: {processing_status}")
            except Exception as update_error:
                self.logger.error(f"Error actualizando estado final CLARO llamadas entrantes: {update_error}")
            
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Error crítico procesando archivo CLARO llamadas entrantes: {str(e)}"
            
            self.logger.error(error_msg, exc_info=True)
            
            return {
                'success': False,
                'error': error_msg,
                'processing_time_seconds': round(processing_time, 2),
                'records_processed': 0,
                'records_failed': 0
            }
    
    def _validate_movistar_cellular_columns(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Valida que el DataFrame tenga las columnas requeridas para datos celulares de MOVISTAR.
        
        Expected columns: numero_que_navega, celda, trafico_de_subida, trafico_de_bajada, 
                         fecha_hora_inicio_sesion, duracion, tipo_tecnologia, fecha_hora_fin_sesion
        
        Args:
            df (pd.DataFrame): DataFrame a validar
            
        Returns:
            Tuple[bool, List[str]]: (Es válido, Lista de errores)
        """
        required_columns = [
            'numero_que_navega', 'celda', 'trafico_de_subida', 'trafico_de_bajada',
            'fecha_hora_inicio_sesion', 'duracion', 'tipo_tecnologia', 'fecha_hora_fin_sesion'
        ]
        errors = []
        
        # Normalizar nombres de columnas (remover espacios, lowercaseear)
        df.columns = df.columns.str.strip().str.lower()
        
        # Verificar columnas requeridas
        missing_columns = []
        for col in required_columns:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            errors.append(f"Columnas faltantes: {', '.join(missing_columns)}")
        
        # Verificar que hay datos
        if len(df) == 0:
            errors.append("El archivo no contiene datos")
        
        # Verificar columnas con datos vacíos
        for col in required_columns:
            if col in df.columns:
                empty_count = df[col].isna().sum() + (df[col] == '').sum()
                if empty_count == len(df):
                    errors.append(f"La columna '{col}' está completamente vacía")
                elif empty_count > len(df) * 0.5:
                    errors.append(f"La columna '{col}' tiene {empty_count} valores vacíos de {len(df)} total")
        
        return len(errors) == 0, errors

    def _validate_movistar_call_columns(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Valida que el DataFrame tenga las columnas requeridas para datos de llamadas de MOVISTAR.
        
        Expected columns: numero_que_contesta, numero_que_marca, duracion, fecha_hora_inicio_llamada,
                         fecha_hora_fin_llamada, celda_origen, celda_destino
        
        Args:
            df (pd.DataFrame): DataFrame a validar
            
        Returns:
            Tuple[bool, List[str]]: (Es válido, Lista de errores)
        """
        required_columns = [
            'numero_que_contesta', 'numero_que_marca', 'duracion', 'fecha_hora_inicio_llamada',
            'fecha_hora_fin_llamada', 'celda_origen', 'celda_destino'
        ]
        errors = []
        
        # Normalizar nombres de columnas (remover espacios, lowercaseear)
        df.columns = df.columns.str.strip().str.lower()
        
        # Verificar columnas requeridas
        missing_columns = []
        for col in required_columns:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            errors.append(f"Columnas faltantes: {', '.join(missing_columns)}")
        
        # Verificar que hay datos
        if len(df) == 0:
            errors.append("El archivo no contiene datos")
        
        # Para llamadas, ser más tolerante con celdas vacías ya que pueden estar ausentes
        critical_fields = ['numero_que_contesta', 'numero_que_marca', 'duracion', 'fecha_hora_inicio_llamada']
        for col in critical_fields:
            if col in df.columns:
                empty_count = df[col].isna().sum() + (df[col] == '').sum()
                valid_count = len(df) - empty_count
                
                if empty_count == len(df):
                    errors.append(f"La columna crítica '{col}' está completamente vacía")
                elif valid_count < 3:  # Requerir al menos 3 registros válidos para llamadas
                    errors.append(f"La columna crítica '{col}' tiene muy pocos datos válidos: {valid_count} de {len(df)} total")
        
        return len(errors) == 0, errors

    def _clean_movistar_cellular_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpia y prepara los datos celulares de MOVISTAR para procesamiento.
        
        Args:
            df (pd.DataFrame): DataFrame con datos brutos
            
        Returns:
            pd.DataFrame: DataFrame limpio
        """
        # Crear copia para no modificar original
        clean_df = df.copy()
        
        # Limpiar números telefónicos
        clean_df['numero_que_navega'] = clean_df['numero_que_navega'].astype(str).str.strip()
        clean_df['numero_que_navega'] = clean_df['numero_que_navega'].str.replace(r'[^\d]', '', regex=True)
        
        # Limpiar fechas - MOVISTAR usa formato YYYYMMDDHHMMSS sin separadores
        clean_df['fecha_hora_inicio_sesion'] = clean_df['fecha_hora_inicio_sesion'].astype(str).str.strip()
        clean_df['fecha_hora_inicio_sesion'] = clean_df['fecha_hora_inicio_sesion'].str.replace(r'[^\d]', '', regex=True)
        
        clean_df['fecha_hora_fin_sesion'] = clean_df['fecha_hora_fin_sesion'].astype(str).str.strip()
        clean_df['fecha_hora_fin_sesion'] = clean_df['fecha_hora_fin_sesion'].str.replace(r'[^\d]', '', regex=True)
        
        # Limpiar celda (convertir a string para manejo consistente)
        clean_df['celda'] = clean_df['celda'].astype(str).str.strip()
        
        # Limpiar tráfico (convertir a numérico)
        clean_df['trafico_de_subida'] = pd.to_numeric(clean_df['trafico_de_subida'], errors='coerce').fillna(0).astype(int)
        clean_df['trafico_de_bajada'] = pd.to_numeric(clean_df['trafico_de_bajada'], errors='coerce').fillna(0).astype(int)
        
        # Limpiar duración (convertir a numérico)
        clean_df['duracion'] = pd.to_numeric(clean_df['duracion'], errors='coerce').fillna(0).astype(int)
        
        # Limpiar tipo tecnología
        clean_df['tipo_tecnologia'] = clean_df['tipo_tecnologia'].astype(str).str.strip()
        
        # Remover filas completamente vacías
        clean_df = clean_df.dropna(how='all')
        
        # Remover filas donde campos críticos están vacíos
        critical_fields = ['numero_que_navega', 'fecha_hora_inicio_sesion', 'celda']
        for field in critical_fields:
            clean_df = clean_df[clean_df[field].notna()]
            clean_df = clean_df[clean_df[field] != '']
        
        self.logger.debug(f"Datos celulares MOVISTAR limpiados: {len(clean_df)} filas válidas")
        return clean_df

    def _clean_movistar_call_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpia y prepara los datos de llamadas de MOVISTAR para procesamiento.
        
        Args:
            df (pd.DataFrame): DataFrame con datos brutos
            
        Returns:
            pd.DataFrame: DataFrame limpio
        """
        # Crear copia para no modificar original
        clean_df = df.copy()
        
        # Limpiar números telefónicos
        clean_df['numero_que_contesta'] = clean_df['numero_que_contesta'].astype(str).str.strip()
        clean_df['numero_que_contesta'] = clean_df['numero_que_contesta'].str.replace(r'[^\d]', '', regex=True)
        
        clean_df['numero_que_marca'] = clean_df['numero_que_marca'].astype(str).str.strip()
        clean_df['numero_que_marca'] = clean_df['numero_que_marca'].str.replace(r'[^\d]', '', regex=True)
        
        # Limpiar fechas - MOVISTAR usa formato YYYYMMDDHHMMSS
        clean_df['fecha_hora_inicio_llamada'] = clean_df['fecha_hora_inicio_llamada'].astype(str).str.strip()
        clean_df['fecha_hora_inicio_llamada'] = clean_df['fecha_hora_inicio_llamada'].str.replace(r'[^\d]', '', regex=True)
        
        clean_df['fecha_hora_fin_llamada'] = clean_df['fecha_hora_fin_llamada'].astype(str).str.strip()
        clean_df['fecha_hora_fin_llamada'] = clean_df['fecha_hora_fin_llamada'].str.replace(r'[^\d]', '', regex=True)
        
        # Limpiar celdas (convertir a string para manejo consistente)
        if 'celda_origen' in clean_df.columns:
            clean_df['celda_origen'] = clean_df['celda_origen'].astype(str).str.strip()
        
        if 'celda_destino' in clean_df.columns:
            clean_df['celda_destino'] = clean_df['celda_destino'].astype(str).str.strip()
        
        # Limpiar duración (convertir a numérico)
        clean_df['duracion'] = pd.to_numeric(clean_df['duracion'], errors='coerce').fillna(0).astype(int)
        
        # Remover filas completamente vacías
        clean_df = clean_df.dropna(how='all')
        
        # Remover filas donde campos críticos están vacíos
        critical_fields = ['numero_que_contesta', 'numero_que_marca', 'fecha_hora_inicio_llamada']
        for field in critical_fields:
            clean_df = clean_df[clean_df[field].notna()]
            clean_df = clean_df[clean_df[field] != '']
        
        self.logger.debug(f"Datos de llamadas MOVISTAR limpiados: {len(clean_df)} filas válidas")
        return clean_df

    def _validate_movistar_cellular_record(self, record: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida un registro individual de datos celulares de MOVISTAR.
        
        Args:
            record (Dict[str, Any]): Registro a validar
            
        Returns:
            Tuple[bool, List[str]]: (Es válido, Lista de errores)
        """
        errors = []
        
        # Validar número telefónico
        numero = str(record.get('numero_que_navega', '')).strip()
        if not numero:
            errors.append("Número que navega vacío")
        elif len(numero) < 10:
            errors.append(f"Número que navega muy corto: {numero}")
        elif len(numero) > 15:
            errors.append(f"Número que navega muy largo: {numero}")
        elif not numero.isdigit():
            errors.append(f"Número que navega contiene caracteres no numéricos: {numero}")
        
        # Validar fecha inicio sesión (formato YYYYMMDDHHMMSS)
        fecha_inicio = str(record.get('fecha_hora_inicio_sesion', '')).strip()
        if not fecha_inicio:
            errors.append("Fecha hora inicio sesión vacía")
        elif len(fecha_inicio) != 14:
            errors.append(f"Formato de fecha inicio incorrecto (esperado YYYYMMDDHHMMSS): {fecha_inicio}")
        elif not fecha_inicio.isdigit():
            errors.append(f"Fecha inicio contiene caracteres no numéricos: {fecha_inicio}")
        else:
            # Validar componentes de fecha
            try:
                year = int(fecha_inicio[:4])
                month = int(fecha_inicio[4:6])
                day = int(fecha_inicio[6:8])
                hour = int(fecha_inicio[8:10])
                minute = int(fecha_inicio[10:12])
                second = int(fecha_inicio[12:14])
                
                if not (2020 <= year <= 2030):
                    errors.append(f"Año fuera de rango válido: {year}")
                if not (1 <= month <= 12):
                    errors.append(f"Mes inválido: {month}")
                if not (1 <= day <= 31):
                    errors.append(f"Día inválido: {day}")
                if not (0 <= hour <= 23):
                    errors.append(f"Hora inválida: {hour}")
                if not (0 <= minute <= 59):
                    errors.append(f"Minuto inválido: {minute}")
                if not (0 <= second <= 59):
                    errors.append(f"Segundo inválido: {second}")
                    
            except ValueError:
                errors.append(f"Error parseando fecha inicio: {fecha_inicio}")
        
        # Validar celda
        celda = str(record.get('celda', '')).strip()
        if not celda:
            errors.append("Celda vacía")
        # Las celdas MOVISTAR pueden ser alfanuméricas (ej: "000073")
        
        # Validar tráfico (deben ser numéricos)
        trafico_subida = record.get('trafico_de_subida', 0)
        try:
            trafico_subida_int = int(trafico_subida)
            if trafico_subida_int < 0:
                errors.append(f"Tráfico de subida no puede ser negativo: {trafico_subida_int}")
        except (ValueError, TypeError):
            errors.append(f"Tráfico de subida debe ser numérico: {trafico_subida}")
        
        trafico_bajada = record.get('trafico_de_bajada', 0)
        try:
            trafico_bajada_int = int(trafico_bajada)
            if trafico_bajada_int < 0:
                errors.append(f"Tráfico de bajada no puede ser negativo: {trafico_bajada_int}")
        except (ValueError, TypeError):
            errors.append(f"Tráfico de bajada debe ser numérico: {trafico_bajada}")
        
        # Validar duración
        duracion = record.get('duracion', 0)
        try:
            duracion_int = int(duracion)
            if duracion_int < 0:
                errors.append(f"Duración no puede ser negativa: {duracion_int}")
        except (ValueError, TypeError):
            errors.append(f"Duración debe ser numérica: {duracion}")
        
        return len(errors) == 0, errors

    def _validate_movistar_call_record(self, record: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida un registro individual de datos de llamadas de MOVISTAR.
        
        Args:
            record (Dict[str, Any]): Registro a validar
            
        Returns:
            Tuple[bool, List[str]]: (Es válido, Lista de errores)
        """
        errors = []
        
        # Validar número que contesta
        numero_contesta = str(record.get('numero_que_contesta', '')).strip()
        if not numero_contesta:
            errors.append("Número que contesta vacío")
        elif len(numero_contesta) < 10:
            errors.append(f"Número que contesta muy corto: {numero_contesta}")
        elif len(numero_contesta) > 15:
            errors.append(f"Número que contesta muy largo: {numero_contesta}")
        elif not numero_contesta.isdigit():
            errors.append(f"Número que contesta contiene caracteres no numéricos: {numero_contesta}")
        
        # Validar número que marca
        numero_marca = str(record.get('numero_que_marca', '')).strip()
        if not numero_marca:
            errors.append("Número que marca vacío")
        elif len(numero_marca) < 10:
            errors.append(f"Número que marca muy corto: {numero_marca}")
        elif len(numero_marca) > 15:
            errors.append(f"Número que marca muy largo: {numero_marca}")
        elif not numero_marca.isdigit():
            errors.append(f"Número que marca contiene caracteres no numéricos: {numero_marca}")
        
        # Validar fecha inicio llamada (formato YYYYMMDDHHMMSS)
        fecha_inicio = str(record.get('fecha_hora_inicio_llamada', '')).strip()
        if not fecha_inicio:
            errors.append("Fecha hora inicio llamada vacía")
        elif len(fecha_inicio) != 14:
            errors.append(f"Formato de fecha inicio incorrecto (esperado YYYYMMDDHHMMSS): {fecha_inicio}")
        elif not fecha_inicio.isdigit():
            errors.append(f"Fecha inicio contiene caracteres no numéricos: {fecha_inicio}")
        else:
            # Validar componentes de fecha
            try:
                year = int(fecha_inicio[:4])
                month = int(fecha_inicio[4:6])
                day = int(fecha_inicio[6:8])
                hour = int(fecha_inicio[8:10])
                minute = int(fecha_inicio[10:12])
                second = int(fecha_inicio[12:14])
                
                if not (2020 <= year <= 2030):
                    errors.append(f"Año fuera de rango válido: {year}")
                if not (1 <= month <= 12):
                    errors.append(f"Mes inválido: {month}")
                if not (1 <= day <= 31):
                    errors.append(f"Día inválido: {day}")
                if not (0 <= hour <= 23):
                    errors.append(f"Hora inválida: {hour}")
                if not (0 <= minute <= 59):
                    errors.append(f"Minuto inválido: {minute}")
                if not (0 <= second <= 59):
                    errors.append(f"Segundo inválido: {second}")
                    
            except ValueError:
                errors.append(f"Error parseando fecha inicio llamada: {fecha_inicio}")
        
        # Validar duración
        duracion = record.get('duracion', 0)
        try:
            duracion_int = int(duracion)
            if duracion_int < 0:
                errors.append(f"Duración no puede ser negativa: {duracion_int}")
        except (ValueError, TypeError):
            errors.append(f"Duración debe ser numérica: {duracion}")
        
        # Validar celdas (pueden estar vacías en algunos casos)
        celda_origen = str(record.get('celda_origen', '')).strip()
        if celda_origen and celda_origen != 'nan':
            # Las celdas MOVISTAR pueden ser alfanuméricas (ej: "07F083-05")
            pass  # Acepta cualquier formato para celdas MOVISTAR
        
        return len(errors) == 0, errors

    def process_claro_llamadas_salientes(self, file_bytes: bytes, file_name: str,
                                       file_upload_id: str, mission_id: str) -> Dict[str, Any]:
        """
        Procesa un archivo de llamadas salientes de CLARO.
        
        Args:
            file_bytes (bytes): Contenido del archivo
            file_name (str): Nombre del archivo
            file_upload_id (str): ID único del archivo
            mission_id (str): ID de la misión
            
        Returns:
            Dict[str, Any]: Resultado del procesamiento
        """
        start_time = datetime.now()
        
        self.logger.info(
            f"Iniciando procesamiento CLARO llamadas salientes: {file_name}",
            extra={'file_size': len(file_bytes), 'file_upload_id': file_upload_id}
        )
        
        try:
            # === ETAPA 1: LECTURA DEL ARCHIVO ===
            
            # Determinar tipo de archivo
            file_extension = Path(file_name).suffix.lower()
            
            if file_extension == '.csv':
                # Para CLARO llamadas salientes, el separador es ','
                df = self._read_csv_robust(file_bytes, delimiter=',')
            elif file_extension == '.xlsx':
                df = self._read_excel_robust(file_bytes)
            else:
                return {
                    'success': False,
                    'error': f'Formato de archivo no soportado: {file_extension}'
                }
            
            self.logger.info(f"Archivo leído: {len(df)} registros, {len(df.columns)} columnas")
            
            # === ETAPA 2: VALIDACIÓN DE ESTRUCTURA ===
            
            is_valid_structure, structure_errors = self._validate_claro_call_columns(df)
            if not is_valid_structure:
                return {
                    'success': False,
                    'error': f'Estructura de archivo inválida: {"; ".join(structure_errors)}'
                }
            
            # === ETAPA 3: LIMPIEZA DE DATOS ===
            
            original_count = len(df)
            df = self._clean_claro_call_data(df, 'SALIENTE')
            cleaned_count = len(df)
            
            if cleaned_count == 0:
                return {
                    'success': False,
                    'error': 'No quedaron registros válidos después de la limpieza (no se encontraron CDR_SALIENTE)'
                }
            
            if cleaned_count < original_count:
                self.logger.warning(
                    f"Se descartaron {original_count - cleaned_count} registros durante la limpieza (solo CDR_SALIENTE procesados)"
                )
            
            # === ETAPA 4: PROCESAMIENTO POR CHUNKS ===
            
            total_processed = 0
            total_failed = 0
            chunk_number = 0
            processing_errors = []
            
            # Procesar en chunks para manejar archivos grandes
            for start_idx in range(0, len(df), self.CHUNK_SIZE):
                chunk_number += 1
                end_idx = min(start_idx + self.CHUNK_SIZE, len(df))
                chunk_df = df.iloc[start_idx:end_idx]
                
                self.logger.debug(f"Procesando chunk {chunk_number}: registros {start_idx+1} a {end_idx}")
                
                chunk_result = self._process_claro_call_chunk(
                    chunk_df, file_upload_id, mission_id, chunk_number, 'SALIENTE'
                )
                
                if chunk_result.get('success', False):
                    total_processed += chunk_result.get('records_processed', 0)
                    total_failed += chunk_result.get('records_failed', 0)
                    
                    # Acumular errores detallados (limitado)
                    if chunk_result.get('failed_records'):
                        processing_errors.extend(chunk_result['failed_records'][:5])
                        if len(processing_errors) > 20:  # Límite total de errores detallados
                            processing_errors = processing_errors[:20]

                else:
                    # Error crítico en el chunk
                    error_msg = chunk_result.get('error', 'Error desconocido en chunk')
                    self.logger.error(f"Error crítico en chunk {chunk_number}: {error_msg}")
                    
                    return {
                        'success': False,
                        'error': f'Error procesando datos (chunk {chunk_number}): {error_msg}',
                        'processedRecords': total_processed,
                        'records_failed': total_failed
                    }
                
                # Verificar si hay demasiados errores
                if total_failed > self.MAX_ERRORS_PER_FILE:
                    self.logger.error(f"Demasiados errores ({total_failed}), abortando procesamiento")
                    return {
                        'success': False,
                        'error': f'Demasiados errores en el archivo ({total_failed}). Verifique el formato.',
                        'processedRecords': total_processed,
                        'records_failed': total_failed
                    }
            
            # === ETAPA 5: RESULTADO FINAL ===
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Determinar éxito basado en ratio de registros procesados
            success_rate = (total_processed / (total_processed + total_failed)) * 100 if (total_processed + total_failed) > 0 else 0
            
            # NUEVA LÓGICA: Considerar exitoso si se procesó al menos 1 registro (duplicados = normal)
            is_successful = total_processed > 0
            
            result = {
                'success': is_successful,
                'processedRecords': total_processed,
                'records_failed': total_failed,
                'success_rate': round(success_rate, 2),
                'processing_time_seconds': round(processing_time, 2),
                'details': {
                    'original_records': original_count,
                    'cleaned_records': cleaned_count,
                    'chunks_processed': chunk_number,
                    'processing_errors': processing_errors[:10],  # Limitar errores mostrados
                    'file_type': 'CLARO_LLAMADAS_SALIENTES'
                }
            }
            
            if not is_successful:
                result['error'] = f'Tasa de éxito baja ({success_rate:.1f}%). Verifique el formato del archivo.'
            
            self.logger.info(
                f"Procesamiento CLARO llamadas salientes completado: {total_processed} exitosos, {total_failed} fallidos ({success_rate:.1f}% éxito)"
            )
            
            # Actualizar tabla operator_data_sheets con conteo final
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    
                    processing_status = 'COMPLETED' if is_successful else 'FAILED'
                    
                    cursor.execute("""
                        UPDATE operator_data_sheets 
                        SET processing_status = ?, 
                            records_processed = ?, 
                            records_failed = ?,
                            processing_end_time = CURRENT_TIMESTAMP,
                            processing_duration_seconds = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (
                        processing_status,
                        total_processed,
                        total_failed,
                        int(processing_time),
                        file_upload_id
                    ))
                    
                    conn.commit()
                    
                    self.logger.info(f"Estado de procesamiento CLARO llamadas salientes actualizado: {processing_status}")
            except Exception as update_error:
                self.logger.error(f"Error actualizando estado final CLARO llamadas salientes: {update_error}")
            
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Error crítico procesando archivo CLARO llamadas salientes: {str(e)}"
            
            self.logger.error(error_msg, exc_info=True)
            
            return {
                'success': False,
                'error': error_msg,
                'processing_time_seconds': round(processing_time, 2),
                'records_processed': 0,
                'records_failed': 0
            }

    def process_movistar_datos_por_celda(self, file_bytes: bytes, file_name: str,
                                       file_upload_id: str, mission_id: str) -> Dict[str, Any]:
        """
        Procesa un archivo de datos por celda de MOVISTAR.
        
        Args:
            file_bytes (bytes): Contenido del archivo
            file_name (str): Nombre del archivo
            file_upload_id (str): ID único del archivo
            mission_id (str): ID de la misión
            
        Returns:
            Dict[str, Any]: Resultado del procesamiento
        """
        start_time = datetime.now()
        
        self.logger.info(
            f"Iniciando procesamiento MOVISTAR datos por celda: {file_name}",
            extra={'file_size': len(file_bytes), 'file_upload_id': file_upload_id}
        )
        
        try:
            # === ETAPA 1: LECTURA DEL ARCHIVO ===
            
            # Determinar tipo de archivo
            file_extension = Path(file_name).suffix.lower()
            
            if file_extension == '.csv':
                # Para MOVISTAR, usar separador coma
                df = self._read_csv_robust(file_bytes, delimiter=',')
            elif file_extension == '.xlsx':
                df = self._read_excel_robust(file_bytes)
            else:
                return {
                    'success': False,
                    'error': f'Formato de archivo no soportado: {file_extension}'
                }
            
            self.logger.info(f"Archivo leído: {len(df)} registros, {len(df.columns)} columnas")
            
            # === ETAPA 2: VALIDACIÓN DE ESTRUCTURA ===
            
            is_valid_structure, structure_errors = self._validate_movistar_cellular_columns(df)
            if not is_valid_structure:
                return {
                    'success': False,
                    'error': f'Estructura de archivo inválida: {"; ".join(structure_errors)}'
                }
            
            # === ETAPA 3: LIMPIEZA DE DATOS ===
            
            original_count = len(df)
            df = self._clean_movistar_cellular_data(df)
            cleaned_count = len(df)
            
            if cleaned_count == 0:
                return {
                    'success': False,
                    'error': 'No quedaron registros válidos después de la limpieza'
                }
            
            if cleaned_count < original_count:
                self.logger.warning(
                    f"Se descartaron {original_count - cleaned_count} registros durante la limpieza"
                )
            
            # === ETAPA 4: PROCESAMIENTO POR CHUNKS ===
            
            total_processed = 0
            total_failed = 0
            total_duplicated = 0      # NUEVO: contador total de duplicados
            total_validation_failed = 0  # NUEVO: contador total de errores de validación
            total_other_errors = 0    # NUEVO: contador total de otros errores
            chunk_number = 0
            processing_errors = []
            
            # Procesar en chunks para manejar archivos grandes
            for start_idx in range(0, len(df), self.CHUNK_SIZE):
                chunk_number += 1
                end_idx = min(start_idx + self.CHUNK_SIZE, len(df))
                chunk_df = df.iloc[start_idx:end_idx]
                
                self.logger.debug(f"Procesando chunk {chunk_number}: registros {start_idx+1} a {end_idx}")
                
                chunk_result = self._process_movistar_cellular_chunk(
                    chunk_df, file_upload_id, mission_id, chunk_number
                )
                
                if chunk_result.get('success', False):
                    total_processed += chunk_result.get('records_processed', 0)
                    total_failed += chunk_result.get('records_failed', 0)
                    total_duplicated += chunk_result.get('records_duplicated', 0)      # NUEVO
                    total_validation_failed += chunk_result.get('validation_failed', 0)  # NUEVO
                    total_other_errors += chunk_result.get('other_errors', 0)         # NUEVO
                    
                    # Acumular errores detallados (limitado)
                    if chunk_result.get('failed_records'):
                        processing_errors.extend(chunk_result['failed_records'][:5])
                        if len(processing_errors) > 20:  # Límite total de errores detallados
                            processing_errors = processing_errors[:20]
                
                else:
                    # Error crítico en el chunk
                    error_msg = chunk_result.get('error', 'Error desconocido en chunk')
                    self.logger.error(f"Error crítico en chunk {chunk_number}: {error_msg}")
                    
                    return {
                        'success': False,
                        'error': f'Error procesando datos (chunk {chunk_number}): {error_msg}',
                        'processedRecords': total_processed,
                        'records_failed': total_failed
                    }
                
                # Verificar si hay demasiados errores
                if total_failed > self.MAX_ERRORS_PER_FILE:
                    self.logger.error(f"Demasiados errores ({total_failed}), abortando procesamiento")
                    return {
                        'success': False,
                        'error': f'Demasiados errores en el archivo ({total_failed}). Verifique el formato.',
                        'processedRecords': total_processed,
                        'records_failed': total_failed
                    }
            
            # === ETAPA 5: RESULTADO FINAL ===
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Determinar éxito basado en ratio de registros procesados
            success_rate = (total_processed / (total_processed + total_failed)) * 100 if (total_processed + total_failed) > 0 else 0
            
            # NUEVA LÓGICA: Considerar exitoso si se procesó al menos 1 registro (duplicados = normal)
            is_successful = total_processed > 0
            
            result = {
                'success': is_successful,
                'processedRecords': total_processed,
                'records_failed': total_failed,
                'records_duplicated': total_duplicated,      # NUEVO: incluir duplicados
                'records_validation_failed': total_validation_failed,  # NUEVO
                'records_other_errors': total_other_errors,  # NUEVO
                'success_rate': round(success_rate, 2),
                'processing_time_seconds': round(processing_time, 2),
                'details': {
                    'original_records': original_count,
                    'cleaned_records': cleaned_count,
                    'chunks_processed': chunk_number,
                    'processing_errors': processing_errors[:10],  # Limitar errores mostrados
                    'file_type': 'MOVISTAR_DATOS_POR_CELDA',
                    'duplicate_analysis': {  # NUEVO: análisis detallado de duplicados
                        'detected_duplicates': total_duplicated,
                        'validation_failures': total_validation_failed,
                        'other_failures': total_other_errors,
                        'duplicate_percentage': round((total_duplicated / original_count) * 100, 1) if original_count > 0 else 0
                    }
                }
            }
            
            if not is_successful:
                result['error'] = f'Tasa de éxito baja ({success_rate:.1f}%). Verifique el formato del archivo.'
            
            self.logger.info(
                f"Procesamiento MOVISTAR datos por celda completado: {total_processed} exitosos, {total_failed} fallidos, {total_duplicated} duplicados ({success_rate:.1f}% éxito)"
            )
            
            # Actualizar tabla operator_data_sheets con conteo final
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    
                    processing_status = 'COMPLETED' if is_successful else 'FAILED'
                    
                    cursor.execute("""
                        UPDATE operator_data_sheets 
                        SET processing_status = ?, 
                            records_processed = ?, 
                            records_failed = ?,
                            processing_end_time = CURRENT_TIMESTAMP,
                            processing_duration_seconds = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (
                        processing_status,
                        total_processed,
                        total_failed,
                        int(processing_time),
                        file_upload_id
                    ))
                    
                    conn.commit()
                    
                    self.logger.info(f"Estado de procesamiento MOVISTAR datos por celda actualizado: {processing_status}")
            except Exception as update_error:
                self.logger.error(f"Error actualizando estado final MOVISTAR datos por celda: {update_error}")
            
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Error crítico procesando archivo MOVISTAR datos por celda: {str(e)}"
            
            self.logger.error(error_msg, exc_info=True)
            
            return {
                'success': False,
                'error': error_msg,
                'processing_time_seconds': round(processing_time, 2),
                'records_processed': 0,
                'records_failed': 0
            }

    def process_movistar_llamadas_salientes(self, file_bytes: bytes, file_name: str,
                                          file_upload_id: str, mission_id: str) -> Dict[str, Any]:
        """
        Procesa un archivo de llamadas salientes de MOVISTAR.
        
        Args:
            file_bytes (bytes): Contenido del archivo
            file_name (str): Nombre del archivo
            file_upload_id (str): ID único del archivo
            mission_id (str): ID de la misión
            
        Returns:
            Dict[str, Any]: Resultado del procesamiento
        """
        start_time = datetime.now()
        
        self.logger.info(
            f"Iniciando procesamiento MOVISTAR llamadas salientes: {file_name}",
            extra={'file_size': len(file_bytes), 'file_upload_id': file_upload_id}
        )
        
        try:
            # === ETAPA 1: LECTURA DEL ARCHIVO ===
            
            # Determinar tipo de archivo
            file_extension = Path(file_name).suffix.lower()
            
            if file_extension == '.csv':
                # Para MOVISTAR, usar separador coma
                df = self._read_csv_robust(file_bytes, delimiter=',')
            elif file_extension == '.xlsx':
                df = self._read_excel_robust(file_bytes)
            else:
                return {
                    'success': False,
                    'error': f'Formato de archivo no soportado: {file_extension}'
                }
            
            self.logger.info(f"Archivo leído: {len(df)} registros, {len(df.columns)} columnas")
            
            # === ETAPA 2: VALIDACIÓN DE ESTRUCTURA ===
            
            is_valid_structure, structure_errors = self._validate_movistar_call_columns(df)
            if not is_valid_structure:
                return {
                    'success': False,
                    'error': f'Estructura de archivo inválida: {"; ".join(structure_errors)}'
                }
            
            # === ETAPA 3: LIMPIEZA DE DATOS ===
            
            original_count = len(df)
            df = self._clean_movistar_call_data(df)
            cleaned_count = len(df)
            
            if cleaned_count == 0:
                return {
                    'success': False,
                    'error': 'No quedaron registros válidos después de la limpieza'
                }
            
            if cleaned_count < original_count:
                self.logger.warning(
                    f"Se descartaron {original_count - cleaned_count} registros durante la limpieza"
                )
            
            # === ETAPA 4: PROCESAMIENTO POR CHUNKS ===
            
            total_processed = 0
            total_failed = 0
            chunk_number = 0
            processing_errors = []
            
            # Procesar en chunks para manejar archivos grandes
            for start_idx in range(0, len(df), self.CHUNK_SIZE):
                chunk_number += 1
                end_idx = min(start_idx + self.CHUNK_SIZE, len(df))
                chunk_df = df.iloc[start_idx:end_idx]
                
                self.logger.debug(f"Procesando chunk {chunk_number}: registros {start_idx+1} a {end_idx}")
                
                chunk_result = self._process_movistar_call_chunk(
                    chunk_df, file_upload_id, mission_id, chunk_number
                )
                
                if chunk_result.get('success', False):
                    total_processed += chunk_result.get('records_processed', 0)
                    total_failed += chunk_result.get('records_failed', 0)
                    
                    # Acumular errores detallados (limitado)
                    if chunk_result.get('failed_records'):
                        processing_errors.extend(chunk_result['failed_records'][:5])
                        if len(processing_errors) > 20:  # Límite total de errores detallados
                            processing_errors = processing_errors[:20]
                
                else:
                    # Error crítico en el chunk
                    error_msg = chunk_result.get('error', 'Error desconocido en chunk')
                    self.logger.error(f"Error crítico en chunk {chunk_number}: {error_msg}")
                    
                    return {
                        'success': False,
                        'error': f'Error procesando datos (chunk {chunk_number}): {error_msg}',
                        'processedRecords': total_processed,
                        'records_failed': total_failed
                    }
                
                # Verificar si hay demasiados errores
                if total_failed > self.MAX_ERRORS_PER_FILE:
                    self.logger.error(f"Demasiados errores ({total_failed}), abortando procesamiento")
                    return {
                        'success': False,
                        'error': f'Demasiados errores en el archivo ({total_failed}). Verifique el formato.',
                        'processedRecords': total_processed,
                        'records_failed': total_failed
                    }
            
            # === ETAPA 5: RESULTADO FINAL ===
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Determinar éxito basado en ratio de registros procesados
            success_rate = (total_processed / (total_processed + total_failed)) * 100 if (total_processed + total_failed) > 0 else 0
            
            # NUEVA LÓGICA: Considerar exitoso si se procesó al menos 1 registro (duplicados = normal)
            is_successful = total_processed > 0
            
            result = {
                'success': is_successful,
                'processedRecords': total_processed,
                'records_failed': total_failed,
                'success_rate': round(success_rate, 2),
                'processing_time_seconds': round(processing_time, 2),
                'details': {
                    'original_records': original_count,
                    'cleaned_records': cleaned_count,
                    'chunks_processed': chunk_number,
                    'processing_errors': processing_errors[:10],  # Limitar errores mostrados
                    'file_type': 'MOVISTAR_LLAMADAS_SALIENTES'
                }
            }
            
            if not is_successful:
                result['error'] = f'Tasa de éxito baja ({success_rate:.1f}%). Verifique el formato del archivo.'
            
            self.logger.info(
                f"Procesamiento MOVISTAR llamadas salientes completado: {total_processed} exitosos, {total_failed} fallidos ({success_rate:.1f}% éxito)"
            )
            
            # Actualizar tabla operator_data_sheets con conteo final
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    
                    processing_status = 'COMPLETED' if is_successful else 'FAILED'
                    
                    cursor.execute("""
                        UPDATE operator_data_sheets 
                        SET processing_status = ?, 
                            records_processed = ?, 
                            records_failed = ?,
                            processing_end_time = CURRENT_TIMESTAMP,
                            processing_duration_seconds = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (
                        processing_status,
                        total_processed,
                        total_failed,
                        int(processing_time),
                        file_upload_id
                    ))
                    
                    conn.commit()
                    
                    self.logger.info(f"Estado de procesamiento MOVISTAR llamadas salientes actualizado: {processing_status}")
            except Exception as update_error:
                self.logger.error(f"Error actualizando estado final MOVISTAR llamadas salientes: {update_error}")
            
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Error crítico procesando archivo MOVISTAR llamadas salientes: {str(e)}"
            
            self.logger.error(error_msg, exc_info=True)
            
            return {
                'success': False,
                'error': error_msg,
                'processing_time_seconds': round(processing_time, 2),
                'records_processed': 0,
                'records_failed': 0
            }

    def _process_movistar_cellular_chunk(self, chunk_df: pd.DataFrame, file_upload_id: str, 
                                       mission_id: str, chunk_number: int) -> Dict[str, Any]:
        """
        Procesa un chunk de datos celulares de MOVISTAR.
        
        Args:
            chunk_df (pd.DataFrame): Chunk de datos a procesar
            file_upload_id (str): ID del archivo
            mission_id (str): ID de la misión
            chunk_number (int): Número del chunk para logging
            
        Returns:
            Dict[str, Any]: Resultado del procesamiento del chunk
        """
        records_processed = 0
        records_failed = 0
        records_duplicated = 0  # NUEVO: contador de duplicados
        validation_failed = 0   # NUEVO: contador de errores de validación
        other_errors = 0        # NUEVO: contador de otros errores
        failed_records = []
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                for index, row in chunk_df.iterrows():
                    try:
                        # Convertir fila a diccionario
                        record = row.to_dict()
                        
                        # Validar registro
                        is_valid, errors = self._validate_movistar_cellular_record(record)
                        if not is_valid:
                            # CAMBIO: errores de validación se clasifican por separado
                            validation_failed += 1
                            records_failed += 1
                            failed_records.append({
                                'row': index + 1,
                                'errors': errors,
                                'type': 'validation',
                                'record': record
                            })
                            
                            if len(failed_records) > 10:  # Limitar detalle de errores
                                break
                            continue
                        
                        # Normalizar datos
                        normalized_data = self.data_normalizer.normalize_movistar_cellular_data(
                            record, file_upload_id, mission_id
                        )
                        
                        if not normalized_data:
                            validation_failed += 1
                            records_failed += 1
                            failed_records.append({
                                'row': index + 1,
                                'errors': ['Error en normalización'],
                                'type': 'normalization',
                                'record': record
                            })
                            continue
                        
                        # Insertar en base de datos
                        cursor.execute("""
                            INSERT INTO operator_cellular_data (
                                file_upload_id, mission_id, operator, numero_telefono,
                                fecha_hora_inicio, celda_id, lac_tac, trafico_subida_bytes,
                                trafico_bajada_bytes, tecnologia, tipo_conexion, record_hash
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            normalized_data['file_upload_id'],
                            normalized_data['mission_id'],
                            normalized_data['operator'],
                            normalized_data['numero_telefono'],
                            normalized_data['fecha_hora_inicio'],
                            normalized_data['celda_id'],
                            normalized_data['lac_tac'],
                            normalized_data['trafico_subida_bytes'],
                            normalized_data['trafico_bajada_bytes'],
                            normalized_data['tecnologia'],
                            normalized_data['tipo_conexion'],
                            normalized_data['record_hash']
                        ))
                        
                        records_processed += 1
                        
                    except Exception as e:
                        error_str = str(e)
                        
                        # NUEVO: Distinguir tipos de errores por mensaje
                        if "UNIQUE constraint failed" in error_str:
                            # Es un duplicado legítimo - NO cuenta como error para el límite
                            records_duplicated += 1
                            error_type = 'duplicate'
                            self.logger.debug(f"Registro duplicado omitido MOVISTAR {index + 1} en chunk {chunk_number}: {error_str}")
                        else:
                            # Es un error real - SÍ cuenta para el límite de errores
                            other_errors += 1
                            records_failed += 1  # SOLO errores reales incrementan records_failed
                            error_type = 'database'
                            self.logger.error(f"Error procesando registro MOVISTAR {index + 1} en chunk {chunk_number}: {e}")
                        
                        # Agregar a la lista de fallos (para debugging, pero no afecta límite de errores)
                        failed_records.append({
                            'row': index + 1,
                            'errors': [f'Error procesando registro: {error_str}'],
                            'type': error_type,
                            'record': record if 'record' in locals() else {}
                        })
                
                # Confirmar transacción del chunk
                conn.commit()
                
                self.logger.debug(
                    f"Chunk MOVISTAR {chunk_number} procesado: {records_processed} exitosos, {records_failed} fallidos ({records_duplicated} duplicados, {validation_failed} validación, {other_errors} otros)"
                )
                
                return {
                    'success': True,
                    'records_processed': records_processed,
                    'records_failed': records_failed,
                    'records_duplicated': records_duplicated,      # NUEVO
                    'validation_failed': validation_failed,       # NUEVO
                    'other_errors': other_errors,                 # NUEVO
                    'failed_records': failed_records[:10]  # Limitar detalle
                }
                
        except Exception as e:
            self.logger.error(f"Error crítico procesando chunk MOVISTAR {chunk_number}: {e}")
            return {
                'success': False,
                'error': str(e),
                'records_processed': records_processed,
                'records_failed': records_failed,
                'records_duplicated': records_duplicated,
                'validation_failed': validation_failed,
                'other_errors': other_errors
            }

    def _process_movistar_call_chunk(self, chunk_df: pd.DataFrame, file_upload_id: str, 
                                   mission_id: str, chunk_number: int) -> Dict[str, Any]:
        """
        Procesa un chunk de datos de llamadas de MOVISTAR.
        
        Args:
            chunk_df (pd.DataFrame): Chunk de datos a procesar
            file_upload_id (str): ID del archivo
            mission_id (str): ID de la misión
            chunk_number (int): Número del chunk para logging
            
        Returns:
            Dict[str, Any]: Resultado del procesamiento del chunk
        """
        records_processed = 0
        records_failed = 0
        failed_records = []
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                for index, row in chunk_df.iterrows():
                    try:
                        # Convertir fila a diccionario
                        record = row.to_dict()
                        
                        # Validar registro
                        is_valid, errors = self._validate_movistar_call_record(record)
                        if not is_valid:
                            records_failed += 1
                            failed_records.append({
                                'row': index + 1,
                                'errors': errors,
                                'record': record
                            })
                            
                            if len(failed_records) > 10:  # Limitar detalle de errores
                                break
                            continue
                        
                        # Normalizar datos de llamadas MOVISTAR
                        normalized_data = self.data_normalizer.normalize_movistar_call_data_salientes(
                            record, file_upload_id, mission_id
                        )
                        
                        if not normalized_data:
                            records_failed += 1
                            failed_records.append({
                                'row': index + 1,
                                'errors': ['Error en normalización'],
                                'record': record
                            })
                            continue
                        
                        # Extraer cellid_decimal y lac_decimal desde celda_origen
                        from utils.cell_id_converter import extract_cellid_lac_from_celda_origen
                        cell_data = extract_cellid_lac_from_celda_origen(normalized_data.get('celda_origen', ''))
                        normalized_data['cellid_decimal'] = cell_data['cellid_decimal']
                        normalized_data['lac_decimal'] = cell_data['lac_decimal']
                        
                        # Insertar en base de datos
                        cursor.execute("""
                            INSERT INTO operator_call_data (
                                file_upload_id, mission_id, operator, tipo_llamada,
                                numero_origen, numero_destino, numero_objetivo,
                                fecha_hora_llamada, duracion_segundos,
                                celda_origen, celda_destino, celda_objetivo,
                                latitud_origen, longitud_origen, latitud_destino, longitud_destino,
                                tecnologia, tipo_trafico, estado_llamada,
                                operator_specific_data, record_hash,
                                cellid_decimal, lac_decimal
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            normalized_data['file_upload_id'],
                            normalized_data['mission_id'],
                            normalized_data['operator'],
                            normalized_data['tipo_llamada'],
                            normalized_data['numero_origen'],
                            normalized_data['numero_destino'],
                            normalized_data['numero_objetivo'],
                            normalized_data['fecha_hora_llamada'],
                            normalized_data['duracion_segundos'],
                            normalized_data['celda_origen'],
                            normalized_data['celda_destino'],
                            normalized_data['celda_objetivo'],
                            normalized_data['latitud_origen'],
                            normalized_data['longitud_origen'],
                            normalized_data['latitud_destino'],
                            normalized_data['longitud_destino'],
                            normalized_data['tecnologia'],
                            normalized_data['tipo_trafico'],
                            normalized_data['estado_llamada'],
                            normalized_data['operator_specific_data'],
                            normalized_data['record_hash'],
                            normalized_data['cellid_decimal'],
                            normalized_data['lac_decimal']
                        ))
                        
                        records_processed += 1
                        
                    except Exception as e:
                        records_failed += 1
                        failed_records.append({
                            'row': index + 1,
                            'errors': [f'Error procesando registro: {str(e)}'],
                            'record': record if 'record' in locals() else {}
                        })
                        
                        self.logger.error(
                            f"Error procesando registro MOVISTAR {index + 1} en chunk {chunk_number}: {e}"
                        )
                
                # Confirmar transacción del chunk
                conn.commit()
                
                self.logger.debug(
                    f"Chunk llamadas MOVISTAR {chunk_number} procesado: {records_processed} exitosos, {records_failed} fallidos"
                )
                
                return {
                    'success': True,
                    'records_processed': records_processed,
                    'records_failed': records_failed,
                    'failed_records': failed_records[:10]  # Limitar detalle
                }
                
        except Exception as e:
            self.logger.error(f"Error crítico procesando chunk llamadas MOVISTAR {chunk_number}: {e}")
            return {
                'success': False,
                'error': str(e),
                'records_processed': records_processed,
                'records_failed': records_failed
            }

    # ==============================================================================
    # PROCESAMIENTO ESPECÍFICO PARA TIGO
    # ==============================================================================

    def process_tigo_llamadas_unificadas(self, file_bytes: bytes, file_name: str,
                                        file_upload_id: str, mission_id: str) -> Dict[str, Any]:
        """
        Procesa un archivo de llamadas unificadas de TIGO (entrantes y salientes en un archivo).
        
        TIGO diferencia entre llamadas entrantes y salientes usando el campo DIRECCION:
        - 'O' = SALIENTE 
        - 'I' = ENTRANTE
        
        Args:
            file_bytes (bytes): Contenido del archivo TIGO
            file_name (str): Nombre del archivo original
            file_upload_id (str): ID único del archivo cargado
            mission_id (str): ID de la misión asociada
            
        Returns:
            Dict[str, Any]: Resultado del procesamiento con estadísticas
        """
        start_time = datetime.now()
        
        self.logger.info(
            f"Iniciando procesamiento TIGO llamadas unificadas: {file_name}",
            extra={'file_upload_id': file_upload_id, 'mission_id': mission_id}
        )
        
        try:
            # === CREAR REGISTRO EN OPERATOR_DATA_SHEETS PRIMERO ===
            # Esto es CRÍTICO para que no falle la foreign key constraint
            
            import hashlib
            file_checksum = hashlib.sha256(file_bytes).hexdigest()
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Nota: La verificación de duplicados se maneja en operator_data_service.py
                # Si llegamos aquí, significa que ya se validó que no hay duplicados
                # o se limpiaron los registros fallidos anteriores
                
                # Nota: El registro en operator_data_sheets ya fue creado por operator_data_service.py
                # Solo necesitamos usar el file_upload_id proporcionado
                
                self.logger.info(f"Procesando archivo TIGO con ID existente: {file_upload_id}")
            
            # === LECTURA DEL ARCHIVO ===
            
            # Detectar encoding
            encoding = self._detect_encoding(file_bytes)
            
            # Determinar formato y leer datos
            if file_name.lower().endswith('.xlsx'):
                # Manejar Excel potencialmente multi-pestaña
                dfs = []
                excel_buffer = io.BytesIO(file_bytes)
                
                try:
                    # Leer todas las pestañas del archivo Excel
                    excel_file = pd.ExcelFile(excel_buffer)
                    sheet_names = excel_file.sheet_names
                    
                    self.logger.info(f"Archivo Excel TIGO con {len(sheet_names)} pestañas: {sheet_names}")
                    
                    # Estadísticas detalladas por hoja
                    sheet_stats = {
                        'total_sheets': len(sheet_names),
                        'successful_sheets': 0,
                        'failed_sheets': 0,
                        'empty_sheets': 0,
                        'sheet_details': {},
                        'failed_sheet_errors': {}
                    }
                    
                    for sheet_index, sheet_name in enumerate(sheet_names, 1):
                        try:
                            self.logger.info(f"Procesando hoja {sheet_index}/{len(sheet_names)}: '{sheet_name}'")
                            
                            df_sheet = pd.read_excel(excel_buffer, sheet_name=sheet_name)
                            
                            if len(df_sheet) == 0:
                                sheet_stats['empty_sheets'] += 1
                                sheet_stats['sheet_details'][sheet_name] = {
                                    'status': 'empty',
                                    'records': 0,
                                    'columns': 0,
                                    'error': None
                                }
                                self.logger.warning(f"Hoja '{sheet_name}' está vacía, omitiendo")
                                continue
                            
                            # Agregar metadatos de origen
                            df_sheet['_source_sheet'] = sheet_name
                            df_sheet['_sheet_index'] = sheet_index
                            df_sheet['_total_sheets'] = len(sheet_names)
                            
                            dfs.append(df_sheet)
                            sheet_stats['successful_sheets'] += 1
                            sheet_stats['sheet_details'][sheet_name] = {
                                'status': 'success',
                                'records': len(df_sheet),
                                'columns': len(df_sheet.columns),
                                'error': None
                            }
                            
                            self.logger.info(f"Hoja '{sheet_name}' procesada exitosamente: {len(df_sheet)} registros, {len(df_sheet.columns)} columnas")
                            
                        except Exception as e:
                            sheet_stats['failed_sheets'] += 1
                            sheet_stats['failed_sheet_errors'][sheet_name] = str(e)
                            sheet_stats['sheet_details'][sheet_name] = {
                                'status': 'failed',
                                'records': 0,
                                'columns': 0,
                                'error': str(e)
                            }
                            
                            self.logger.error(f"Error procesando hoja '{sheet_name}' ({sheet_index}/{len(sheet_names)}): {e}", exc_info=True)
                            # Continuar con las demás hojas
                            continue
                    
                    # Reporte final de hojas procesadas
                    self.logger.info(
                        f"Resumen procesamiento hojas TIGO: "
                        f"{sheet_stats['successful_sheets']} exitosas, "
                        f"{sheet_stats['failed_sheets']} fallidas, "
                        f"{sheet_stats['empty_sheets']} vacías de {sheet_stats['total_sheets']} total"
                    )
                    
                    if not dfs:
                        error_details = []
                        if sheet_stats['failed_sheets'] > 0:
                            error_details.append(f"{sheet_stats['failed_sheets']} hojas fallaron")
                        if sheet_stats['empty_sheets'] > 0:
                            error_details.append(f"{sheet_stats['empty_sheets']} hojas estaban vacías")
                        
                        error_msg = f"No se pudieron procesar datos de ninguna hoja del archivo Excel. {'; '.join(error_details)}"
                        
                        return {
                            'success': False,
                            'error': error_msg,
                            'records_processed': 0,
                            'records_failed': 0,
                            'sheet_processing_details': sheet_stats
                        }
                    
                    # Combinar todas las pestañas válidas
                    df = pd.concat(dfs, ignore_index=True)
                    
                    self.logger.info(
                        f"Combinadas {len(dfs)} pestañas válidas en {len(df)} registros totales. "
                        f"Hojas procesadas: {[name for name, details in sheet_stats['sheet_details'].items() if details['status'] == 'success']}"
                    )
                    
                except Exception as e:
                    return {
                        'success': False,
                        'error': f'Error leyendo archivo Excel TIGO: {str(e)}',
                        'records_processed': 0,
                        'records_failed': 0
                    }
            
            elif file_name.lower().endswith('.csv'):
                # Leer CSV
                df = self._read_csv_robust(file_bytes, delimiter=',')
                
            else:
                return {
                    'success': False,
                    'error': f'Formato de archivo no soportado para TIGO: {file_name}',
                    'records_processed': 0,
                    'records_failed': 0
                }
            
            # === VALIDACIÓN INICIAL ===
            
            if df is None or len(df) == 0:
                return {
                    'success': False,
                    'error': 'El archivo TIGO está vacío o no se pudo leer',
                    'records_processed': 0,
                    'records_failed': 0
                }
            
            self.logger.info(f"Archivo TIGO leído: {len(df)} registros, {len(df.columns)} columnas")
            
            # Mapear columnas TIGO a nombres estándar
            tigo_column_mapping = {
                'TIPO_DE_LLAMADA': 'tipo_de_llamada',
                'NUMERO A': 'numero_a',
                'NUMERO MARCADO': 'numero_marcado',
                'TRCSEXTRACODEC': 'trcsextracodec',
                'DIRECCION: O SALIENTE, I ENTRANTE': 'direccion',
                'DURACION TOTAL seg': 'duracion_total_seg',
                'FECHA Y HORA ORIGEN': 'fecha_hora_origen',
                'CELDA_ORIGEN_TRUNCADA': 'celda_origen_truncada',
                'TECH': 'tecnologia',
                'DIRECCION': 'direccion_fisica',
                'CITY_DS': 'ciudad',
                'DEPARTMENT_DS': 'departamento',
                'AZIMUTH': 'azimuth',
                'ALTURA': 'altura',
                'POTENCIA': 'potencia',
                'LONGITUDE': 'longitud',
                'LATITUDE': 'latitud',
                'TIPO_COBERTURA': 'tipo_cobertura',
                'TIPO_ESTRUCTURA': 'tipo_estructura',
                'OPERADOR': 'operador',
                'CELLID_NVAL': 'cellid_nval'
            }
            
            # Normalizar nombres de columnas
            df_normalized = df.copy()
            df_normalized.columns = df_normalized.columns.str.strip()
            
            # Mapear columnas TIGO
            columns_to_rename = {}
            for original_col in df_normalized.columns:
                if original_col in tigo_column_mapping:
                    columns_to_rename[original_col] = tigo_column_mapping[original_col]
            
            df_normalized = df_normalized.rename(columns=columns_to_rename)
            
            # Verificar columnas esenciales
            required_columns = ['tipo_de_llamada', 'numero_a', 'direccion', 'fecha_hora_origen']
            missing_columns = [col for col in required_columns if col not in df_normalized.columns]
            
            if missing_columns:
                return {
                    'success': False,
                    'error': f'Archivo TIGO falta columnas requeridas: {", ".join(missing_columns)}',
                    'records_processed': 0,
                    'records_failed': 0
                }
            
            # === LIMPIEZA DE DATOS ===
            
            # Limpiar valores nulos en campos críticos
            df_clean = df_normalized.dropna(subset=['numero_a', 'direccion']).copy()
            
            # Convertir coordenadas formato TIGO (comas a puntos decimales)
            for coord_col in ['latitud', 'longitud']:
                if coord_col in df_clean.columns:
                    df_clean[coord_col] = (df_clean[coord_col]
                                          .astype(str)
                                          .str.replace(',', '.')
                                          .str.strip('"\'')
                                          .replace(['', 'nan', 'None'], None))
                    
                    # Convertir a float donde sea posible
                    df_clean[coord_col] = pd.to_numeric(df_clean[coord_col], errors='coerce')
            
            # Convertir potencia (formato con comas)
            if 'potencia' in df_clean.columns:
                df_clean['potencia'] = (df_clean['potencia']
                                       .astype(str)
                                       .str.replace(',', '.')
                                       .str.strip('"\''))
                df_clean['potencia'] = pd.to_numeric(df_clean['potencia'], errors='coerce')
            
            # Convertir duración a numérico
            if 'duracion_total_seg' in df_clean.columns:
                df_clean['duracion_total_seg'] = pd.to_numeric(df_clean['duracion_total_seg'], errors='coerce').fillna(0)
            
            self.logger.info(f"Datos TIGO limpiados: {len(df_clean)} registros válidos de {len(df)} originales")
            
            # === SEPARACIÓN POR DIRECCIÓN ===
            
            # Separar registros por dirección (O/I)
            df_entrantes = df_clean[df_clean['direccion'].str.upper().isin(['I', 'ENTRANTE'])].copy()
            df_salientes = df_clean[df_clean['direccion'].str.upper().isin(['O', 'SALIENTE'])].copy()
            
            self.logger.info(f"Separación TIGO: {len(df_entrantes)} entrantes, {len(df_salientes)} salientes")
            
            # === PROCESAMIENTO EN CHUNKS ===
            
            total_records_processed = 0
            total_records_failed = 0
            all_failed_records = []
            
            # Procesar llamadas entrantes
            if len(df_entrantes) > 0:
                for chunk_df in self._chunk_dataframe(df_entrantes, self.CHUNK_SIZE):
                    chunk_result = self._process_tigo_chunk(
                        chunk_df, 'ENTRANTE', file_upload_id, mission_id
                    )
                    
                    total_records_processed += chunk_result.get('records_processed', 0)
                    total_records_failed += chunk_result.get('records_failed', 0)
                    
                    if chunk_result.get('failed_records'):
                        all_failed_records.extend(chunk_result['failed_records'])
                    
                    if not chunk_result.get('success', False):
                        self.logger.error(f"Error procesando chunk TIGO entrantes: {chunk_result.get('error')}")
            
            # Procesar llamadas salientes
            if len(df_salientes) > 0:
                for chunk_df in self._chunk_dataframe(df_salientes, self.CHUNK_SIZE):
                    chunk_result = self._process_tigo_chunk(
                        chunk_df, 'SALIENTE', file_upload_id, mission_id
                    )
                    
                    total_records_processed += chunk_result.get('records_processed', 0)
                    total_records_failed += chunk_result.get('records_failed', 0)
                    
                    if chunk_result.get('failed_records'):
                        all_failed_records.extend(chunk_result['failed_records'])
                    
                    if not chunk_result.get('success', False):
                        self.logger.error(f"Error procesando chunk TIGO salientes: {chunk_result.get('error')}")
            
            # === RESULTADO FINAL ===
            
            processing_time = datetime.now() - start_time
            
            self.logger.info(
                f"Procesamiento TIGO completado: {total_records_processed} exitosos, {total_records_failed} fallidos",
                extra={
                    'processing_time_seconds': processing_time.total_seconds(),
                    'entrantes_count': len(df_entrantes),
                    'salientes_count': len(df_salientes)
                }
            )
            
            # Preparar detalles del resultado final
            result_details = {
                'processing_time_seconds': processing_time.total_seconds(),
                'entrantes_processed': len(df_entrantes),
                'salientes_processed': len(df_salientes),
                'sheets_combined': len(dfs) if file_name.lower().endswith('.xlsx') else 1
            }
            
            # Agregar información detallada de hojas si es Excel multi-hoja
            if file_name.lower().endswith('.xlsx') and 'sheet_stats' in locals():
                result_details.update({
                    'sheet_processing_summary': {
                        'total_sheets': sheet_stats['total_sheets'],
                        'successful_sheets': sheet_stats['successful_sheets'],
                        'failed_sheets': sheet_stats['failed_sheets'],
                        'empty_sheets': sheet_stats['empty_sheets'],
                        'successful_sheet_names': [name for name, details in sheet_stats['sheet_details'].items() if details['status'] == 'success'],
                        'failed_sheet_names': list(sheet_stats['failed_sheet_errors'].keys()),
                        'sheet_record_counts': {name: details['records'] for name, details in sheet_stats['sheet_details'].items() if details['status'] == 'success'}
                    }
                })
                
                # Logs de resumen final con información de hojas
                self.logger.info(
                    f"Procesamiento TIGO completado con {sheet_stats['successful_sheets']} hojas exitosas: "
                    f"{total_records_processed} registros exitosos, {total_records_failed} fallidos",
                    extra={
                        'sheet_summary': result_details['sheet_processing_summary'],
                        'processing_time_seconds': processing_time.total_seconds()
                    }
                )
            
            # Actualizar estado final en operator_data_sheets
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                processing_status = 'COMPLETED' if total_records_failed == 0 else 'FAILED'
                
                cursor.execute("""
                    UPDATE operator_data_sheets 
                    SET processing_status = ?, 
                        records_processed = ?, 
                        records_failed = ?,
                        processing_end_time = CURRENT_TIMESTAMP,
                        processing_duration_seconds = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    processing_status,
                    total_records_processed,
                    total_records_failed,
                    int(processing_time.total_seconds()),
                    file_upload_id
                ))
                
                conn.commit()
                
                self.logger.info(f"Estado de procesamiento TIGO actualizado: {processing_status}")
            
            return {
                'success': True,
                'processedRecords': total_records_processed,  # CORRECCIÓN: Usar nombre consistente con frontend
                'records_processed': total_records_processed,  # Mantener por compatibilidad
                'records_failed': total_records_failed,
                'failed_records': all_failed_records[:10],  # Limitar a primeros 10 errores
                'details': result_details
            }
            
        except Exception as e:
            self.logger.error(f"Error crítico procesando archivo TIGO {file_name}: {e}", exc_info=True)
            
            # Actualizar estado como FAILED en caso de error crítico
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        UPDATE operator_data_sheets 
                        SET processing_status = 'FAILED', 
                            error_details = ?,
                            processing_end_time = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (str(e), file_upload_id))
                    
                    conn.commit()
            except Exception as update_error:
                self.logger.error(f"Error actualizando estado de fallo: {update_error}")
            
            return {
                'success': False,
                'error': f'Error crítico: {str(e)}',
                'processedRecords': 0,  # CORRECCIÓN: Usar nombre consistente con frontend
                'records_processed': 0,  # Mantener por compatibilidad
                'records_failed': 0
            }

    def _process_tigo_chunk(self, df_chunk: pd.DataFrame, call_direction: str,
                           file_upload_id: str, mission_id: str) -> Dict[str, Any]:
        """
        Procesa un chunk de datos TIGO para un tipo específico de llamada.
        
        Args:
            df_chunk: DataFrame con registros del chunk
            call_direction: 'ENTRANTE' o 'SALIENTE'
            file_upload_id: ID del archivo fuente
            mission_id: ID de la misión
            
        Returns:
            Dict con resultado del procesamiento del chunk
        """
        chunk_number = getattr(self, '_current_chunk_number', 0) + 1
        setattr(self, '_current_chunk_number', chunk_number)
        
        records_processed = 0
        records_failed = 0
        failed_records = []
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                for index, row in df_chunk.iterrows():
                    try:
                        # Preparar datos del registro con información de origen
                        row_data = dict(row)
                        
                        # Preservar información de origen si está disponible
                        source_sheet = row_data.get('_source_sheet', 'unknown')
                        sheet_index = row_data.get('_sheet_index', 0)
                        total_sheets = row_data.get('_total_sheets', 1)
                        
                        # Normalizar registro TIGO usando DataNormalizerService
                        normalized_data = self.data_normalizer.normalize_tigo_call_data_unificadas(
                            row_data, file_upload_id, mission_id, call_direction
                        )
                        
                        # Agregar información de origen al operator_specific_data
                        if normalized_data and 'operator_specific_data' in normalized_data:
                            operator_data = json.loads(normalized_data['operator_specific_data']) if isinstance(normalized_data['operator_specific_data'], str) else normalized_data['operator_specific_data']
                            if operator_data is None:
                                operator_data = {}
                            
                            operator_data.update({
                                'source_sheet': source_sheet,
                                'sheet_index': sheet_index,
                                'total_sheets_in_file': total_sheets,
                                'call_direction': call_direction
                            })
                            
                            normalized_data['operator_specific_data'] = json.dumps(operator_data, ensure_ascii=False)
                        
                        if not normalized_data:
                            records_failed += 1
                            failed_records.append({
                                'row': index + 1,
                                'errors': ['No se pudo normalizar el registro'],
                                'record': dict(row)
                            })
                            continue
                        
                        # Insertar en base de datos
                        cursor.execute("""
                            INSERT INTO operator_call_data (
                                file_upload_id, mission_id, operator, tipo_llamada, numero_origen, 
                                numero_destino, numero_objetivo, fecha_hora_llamada, duracion_segundos,
                                celda_origen, celda_destino, celda_objetivo, latitud_origen, 
                                longitud_origen, latitud_destino, longitud_destino, tecnologia,
                                tipo_trafico, estado_llamada, operator_specific_data, record_hash,
                                cellid_decimal, lac_decimal
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            normalized_data['file_upload_id'],
                            normalized_data['mission_id'],
                            'TIGO',  # operator
                            normalized_data['tipo_llamada'],
                            normalized_data['numero_origen'],
                            normalized_data['numero_destino'],
                            normalized_data['numero_objetivo'],
                            normalized_data['fecha_hora_llamada'],
                            normalized_data['duracion_segundos'],
                            normalized_data['celda_origen'],
                            normalized_data['celda_destino'],
                            normalized_data['celda_objetivo'],
                            normalized_data['latitud_origen'],
                            normalized_data['longitud_origen'],
                            normalized_data['latitud_destino'],
                            normalized_data['longitud_destino'],
                            normalized_data['tecnologia'],
                            normalized_data['tipo_trafico'],
                            normalized_data['estado_llamada'],
                            normalized_data['operator_specific_data'],
                            normalized_data['record_hash'],
                            normalized_data['cellid_decimal'],
                            normalized_data['lac_decimal']
                        ))
                        
                        records_processed += 1
                        
                    except Exception as e:
                        records_failed += 1
                        failed_records.append({
                            'row': index + 1,
                            'errors': [f'Error procesando registro: {str(e)}'],
                            'record': dict(row) if 'row' in locals() else {}
                        })
                        
                        self.logger.error(
                            f"Error procesando registro TIGO {call_direction} {index + 1} en chunk {chunk_number}: {e}"
                        )
                
                # Confirmar transacción del chunk
                conn.commit()
                
                self.logger.debug(
                    f"Chunk TIGO {call_direction} {chunk_number} procesado: {records_processed} exitosos, {records_failed} fallidos"
                )
                
                return {
                    'success': True,
                    'records_processed': records_processed,
                    'records_failed': records_failed,
                    'failed_records': failed_records[:10]  # Limitar detalle
                }
                
        except Exception as e:
            self.logger.error(f"Error crítico procesando chunk TIGO {call_direction} {chunk_number}: {e}")
            return {
                'success': False,
                'error': str(e),
                'records_processed': records_processed,
                'records_failed': records_failed
            }

    # ==============================================================================
    # MÉTODOS ESPECÍFICOS PARA OPERADOR WOM
    # ==============================================================================
    
    def process_wom_datos_por_celda(self, file_bytes: bytes, file_name: str,
                                   file_upload_id: str, mission_id: str) -> Dict[str, Any]:
        """
        Procesa un archivo de datos por celda de WOM.
        
        WOM maneja datos celulares con información técnica avanzada incluyendo:
        - IMSI, IMEI para identificación de dispositivos
        - BTS_ID, TAC para información de infraestructura
        - Coordenadas con formato de comas decimales
        - Multi-pestaña en archivos XLSX
        
        Args:
            file_bytes (bytes): Contenido del archivo WOM
            file_name (str): Nombre del archivo original
            file_upload_id (str): ID único del archivo cargado
            mission_id (str): ID de la misión asociada
            
        Returns:
            Dict[str, Any]: Resultado del procesamiento con estadísticas
        """
        start_time = datetime.now()
        
        self.logger.info(
            f"Iniciando procesamiento WOM datos por celda: {file_name}",
            extra={
                'file_name': file_name,
                'file_upload_id': file_upload_id,
                'mission_id': mission_id,
                'operator': 'WOM',
                'file_type': 'CELLULAR_DATA'
            }
        )
        
        try:
            # === LECTURA DE ARCHIVO ===
            
            # Leer archivo (CSV o XLSX multi-pestaña)
            dfs = []
            if file_name.lower().endswith('.xlsx'):
                # WOM usa archivos multi-pestaña: leer todas las pestañas
                try:
                    excel_file = pd.ExcelFile(io.BytesIO(file_bytes))
                    self.logger.info(f"Pestañas encontradas en {file_name}: {excel_file.sheet_names}")
                    
                    for sheet_name in excel_file.sheet_names:
                        sheet_df = pd.read_excel(excel_file, sheet_name=sheet_name)
                        if not sheet_df.empty:
                            sheet_df['source_sheet'] = sheet_name
                            dfs.append(sheet_df)
                            self.logger.info(f"Pestaña '{sheet_name}': {len(sheet_df)} registros")
                    
                    if not dfs:
                        return {
                            'success': False,
                            'error': 'No se encontraron datos válidos en ninguna pestaña del archivo Excel',
                            'records_processed': 0,
                            'records_failed': 0
                        }
                    
                    # Combinar todas las pestañas
                    df = pd.concat(dfs, ignore_index=True)
                    self.logger.info(f"Total registros combinados: {len(df)}")
                    
                except Exception as excel_error:
                    self.logger.error(f"Error leyendo Excel multi-pestaña: {excel_error}")
                    return {
                        'success': False,
                        'error': f'Error leyendo archivo Excel: {str(excel_error)}',
                        'records_processed': 0,
                        'records_failed': 0
                    }
            else:
                # Archivo CSV
                df = self._read_csv_robust(file_bytes, delimiter=',')
                if df is None or df.empty:
                    return {
                        'success': False,
                        'error': 'No se pudo leer el archivo CSV o está vacío',
                        'records_processed': 0,
                        'records_failed': 0
                    }
            
            self.logger.info(f"Archivo WOM datos por celda leído: {len(df)} registros")
            
            # === VALIDACIÓN DE ESTRUCTURA ===
            
            # Campos requeridos específicos de WOM datos por celda
            required_fields = [
                'OPERADOR_TECNOLOGIA', 'BTS_ID', 'TAC', 'CELL_ID_VOZ', 'SECTOR',
                'FECHA_HORA_INICIO', 'FECHA_HORA_FIN', 'OPERADOR_RAN', 'NUMERO_ORIGEN',
                'DURACION_SEG', 'UP_DATA_BYTES', 'DOWN_DATA_BYTES', 'IMSI',
                'NOMBRE_ANTENA', 'DIRECCION', 'LATITUD', 'LONGITUD',
                'LOCALIDAD', 'CIUDAD', 'DEPARTAMENTO'
            ]
            
            # Verificar campos requeridos
            missing_fields = [field for field in required_fields if field not in df.columns]
            if missing_fields:
                return {
                    'success': False,
                    'error': f'Campos requeridos faltantes: {", ".join(missing_fields)}',
                    'records_processed': 0,
                    'records_failed': 0
                }
            
            # === NORMALIZACIÓN DE DATOS ===
            
            # Normalizar usando DataNormalizerService
            df_normalized = self.data_normalizer.normalize_wom_cellular_data(df)
            
            if df_normalized is None or df_normalized.empty:
                return {
                    'success': False,
                    'error': 'Error en normalización de datos WOM',
                    'records_processed': 0,
                    'records_failed': 0
                }
            
            # === LIMPIEZA Y VALIDACIÓN ===
            
            # Filtrar registros con datos válidos
            df_clean = df_normalized.dropna(subset=['numero_origen', 'operador_tecnologia']).copy()
            
            # Convertir coordenadas formato WOM (comas a puntos decimales)
            for coord_col in ['latitud', 'longitud']:
                if coord_col in df_clean.columns:
                    df_clean[coord_col] = (df_clean[coord_col]
                                          .astype(str)
                                          .str.replace(',', '.')
                                          .str.strip('"\'')
                                          .replace(['', 'nan', 'None'], None))
                    
                    # Convertir a float donde sea posible
                    df_clean[coord_col] = pd.to_numeric(df_clean[coord_col], errors='coerce')
            
            # Convertir campos numéricos específicos de WOM
            numeric_fields = ['duracion_seg', 'up_data_bytes', 'down_data_bytes', 'bts_id', 'tac', 'cell_id_voz', 'sector']
            for field in numeric_fields:
                if field in df_clean.columns:
                    df_clean[field] = pd.to_numeric(df_clean[field], errors='coerce').fillna(0)
            
            self.logger.info(f"Datos WOM limpiados: {len(df_clean)} registros válidos de {len(df)} originales")
            
            # === PROCESAMIENTO EN CHUNKS ===
            
            total_records_processed = 0
            total_records_failed = 0
            total_duplicated = 0          # NUEVO: contador de duplicados
            total_validation_failed = 0  # NUEVO: contador de errores de validación
            total_other_errors = 0       # NUEVO: contador de otros errores
            all_failed_records = []
            
            for chunk_df in self._chunk_dataframe(df_clean, self.CHUNK_SIZE):
                chunk_result = self._process_wom_cellular_chunk(
                    chunk_df, file_upload_id, mission_id
                )
                
                total_records_processed += chunk_result.get('records_processed', 0)
                total_records_failed += chunk_result.get('records_failed', 0)
                total_duplicated += chunk_result.get('records_duplicated', 0)          # NUEVO
                total_validation_failed += chunk_result.get('validation_failed', 0)  # NUEVO
                total_other_errors += chunk_result.get('other_errors', 0)             # NUEVO
                
                if chunk_result.get('failed_records'):
                    all_failed_records.extend(chunk_result['failed_records'])
                
                if not chunk_result.get('success', False):
                    self.logger.error(f"Error procesando chunk WOM datos: {chunk_result.get('error')}")
            
            # === RESULTADO FINAL ===
            
            processing_time = datetime.now() - start_time
            
            self.logger.info(
                f"Procesamiento WOM datos por celda completado: {total_records_processed} exitosos, {total_records_failed} fallidos",
                extra={
                    'processing_time_seconds': processing_time.total_seconds(),
                    'total_processed': total_records_processed,
                    'total_failed': total_records_failed
                }
            )
            
            # Actualizar tabla operator_data_sheets con conteo final
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    
                    processing_status = 'COMPLETED' if total_records_failed == 0 else 'FAILED'
                    
                    cursor.execute("""
                        UPDATE operator_data_sheets 
                        SET processing_status = ?, 
                            records_processed = ?, 
                            records_failed = ?,
                            processing_end_time = CURRENT_TIMESTAMP,
                            processing_duration_seconds = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (
                        processing_status,
                        total_records_processed,
                        total_records_failed,
                        int(processing_time.total_seconds()),
                        file_upload_id
                    ))
                    
                    conn.commit()
                    
                    self.logger.info(f"Estado de procesamiento WOM datos por celda actualizado: {processing_status}")
            except Exception as update_error:
                self.logger.error(f"Error actualizando estado final WOM datos por celda: {update_error}")
            
            return {
                'success': True,
                'processedRecords': total_records_processed,  # CORRECCIÓN: Usar nombre consistente con frontend
                'records_processed': total_records_processed,  # Mantener por compatibilidad
                'records_failed': total_records_failed,
                'records_duplicated': total_duplicated,                    # NUEVO: contador exacto de duplicados
                'records_validation_failed': total_validation_failed,     # NUEVO: contador exacto de errores de validación
                'records_other_errors': total_other_errors,               # NUEVO: contador exacto de otros errores
                'failed_records': all_failed_records[:10],  # Limitar a primeros 10 errores
                'details': {
                    'processing_time_seconds': processing_time.total_seconds(),
                    'sheets_combined': len(dfs) if file_name.lower().endswith('.xlsx') else 1,
                    'operator_technology_types': df_clean['operador_tecnologia'].value_counts().to_dict() if 'operador_tecnologia' in df_clean.columns else {}
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error crítico procesando archivo WOM datos por celda {file_name}: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Error crítico: {str(e)}',
                'processedRecords': 0,  # CORRECCIÓN: Usar nombre consistente con frontend
                'records_processed': 0,  # Mantener por compatibilidad
                'records_failed': 0
            }

    def process_wom_llamadas_entrantes(self, file_bytes: bytes, file_name: str,
                                      file_upload_id: str, mission_id: str) -> Dict[str, Any]:
        """
        Procesa un archivo de llamadas entrantes/salientes de WOM (unificado).
        
        WOM maneja llamadas entrantes y salientes en un solo archivo, diferenciadas
        por el campo SENTIDO:
        - 'ENTRANTE' = llamada entrante
        - 'SALIENTE' = llamada saliente
        
        Incluye información técnica avanzada como IMEI, IMSI, ACCESS_NETWORK_INFORMATION
        
        Args:
            file_bytes (bytes): Contenido del archivo WOM
            file_name (str): Nombre del archivo original
            file_upload_id (str): ID único del archivo cargado
            mission_id (str): ID de la misión asociada
            
        Returns:
            Dict[str, Any]: Resultado del procesamiento con estadísticas
        """
        start_time = datetime.now()
        
        self.logger.info(
            f"Iniciando procesamiento WOM llamadas entrantes/salientes: {file_name}",
            extra={
                'file_name': file_name,
                'file_upload_id': file_upload_id,
                'mission_id': mission_id,
                'operator': 'WOM',
                'file_type': 'CALL_DATA'
            }
        )
        
        try:
            # === LECTURA DE ARCHIVO ===
            
            # Leer archivo (CSV o XLSX multi-pestaña)
            dfs = []
            if file_name.lower().endswith('.xlsx'):
                # WOM usa archivos multi-pestaña: leer todas las pestañas
                try:
                    excel_file = pd.ExcelFile(io.BytesIO(file_bytes))
                    self.logger.info(f"Pestañas encontradas en {file_name}: {excel_file.sheet_names}")
                    
                    for sheet_name in excel_file.sheet_names:
                        sheet_df = pd.read_excel(excel_file, sheet_name=sheet_name)
                        if not sheet_df.empty:
                            sheet_df['source_sheet'] = sheet_name
                            dfs.append(sheet_df)
                            self.logger.info(f"Pestaña '{sheet_name}': {len(sheet_df)} registros")
                    
                    if not dfs:
                        return {
                            'success': False,
                            'error': 'No se encontraron datos válidos en ninguna pestaña del archivo Excel',
                            'records_processed': 0,
                            'records_failed': 0
                        }
                    
                    # Combinar todas las pestañas
                    df = pd.concat(dfs, ignore_index=True)
                    self.logger.info(f"Total registros combinados: {len(df)}")
                    
                except Exception as excel_error:
                    self.logger.error(f"Error leyendo Excel multi-pestaña: {excel_error}")
                    return {
                        'success': False,
                        'error': f'Error leyendo archivo Excel: {str(excel_error)}',
                        'records_processed': 0,
                        'records_failed': 0
                    }
            else:
                # Archivo CSV
                df = self._read_csv_robust(file_bytes, delimiter=',')
                if df is None or df.empty:
                    return {
                        'success': False,
                        'error': 'No se pudo leer el archivo CSV o está vacío',
                        'records_processed': 0,
                        'records_failed': 0
                    }
            
            self.logger.info(f"Archivo WOM llamadas leído: {len(df)} registros")
            
            # === VALIDACIÓN DE ESTRUCTURA ===
            
            # Campos requeridos específicos de WOM llamadas
            required_fields = [
                'OPERADOR_TECNOLOGIA', 'BTS_ID', 'TAC', 'CELL_ID_VOZ', 'SECTOR',
                'NUMERO_ORIGEN', 'NUMERO_DESTINO', 'FECHA_HORA_INICIO', 'FECHA_HORA_FIN',
                'DURACION_SEG', 'OPERADOR_RAN_ORIGEN', 'NOMBRE_ANTENA', 'DIRECCION',
                'LATITUD', 'LONGITUD', 'LOCALIDAD', 'CIUDAD', 'DEPARTAMENTO', 'SENTIDO'
            ]
            
            # Verificar campos requeridos
            missing_fields = [field for field in required_fields if field not in df.columns]
            if missing_fields:
                return {
                    'success': False,
                    'error': f'Campos requeridos faltantes: {", ".join(missing_fields)}',
                    'records_processed': 0,
                    'records_failed': 0
                }
            
            # === NORMALIZACIÓN DE DATOS ===
            
            # Normalizar usando DataNormalizerService
            df_normalized = self.data_normalizer.normalize_wom_call_data_entrantes(df)
            
            if df_normalized is None or df_normalized.empty:
                return {
                    'success': False,
                    'error': 'Error en normalización de datos WOM',
                    'records_processed': 0,
                    'records_failed': 0
                }
            
            # === LIMPIEZA Y VALIDACIÓN ===
            
            # Filtrar registros con datos válidos
            df_clean = df_normalized.dropna(subset=['numero_origen', 'sentido']).copy()
            
            # Convertir coordenadas formato WOM (comas a puntos decimales)
            for coord_col in ['latitud', 'longitud']:
                if coord_col in df_clean.columns:
                    df_clean[coord_col] = (df_clean[coord_col]
                                          .astype(str)
                                          .str.replace(',', '.')
                                          .str.strip('"\'')
                                          .replace(['', 'nan', 'None'], None))
                    
                    # Convertir a float donde sea posible
                    df_clean[coord_col] = pd.to_numeric(df_clean[coord_col], errors='coerce')
            
            # Convertir duración a numérico
            if 'duracion_seg' in df_clean.columns:
                df_clean['duracion_seg'] = pd.to_numeric(df_clean['duracion_seg'], errors='coerce').fillna(0)
            
            self.logger.info(f"Datos WOM limpiados: {len(df_clean)} registros válidos de {len(df)} originales")
            
            # === SEPARACIÓN POR SENTIDO ===
            
            # Separar registros por sentido de llamada
            df_entrantes = df_clean[df_clean['sentido'].str.upper().isin(['ENTRANTE'])].copy()
            df_salientes = df_clean[df_clean['sentido'].str.upper().isin(['SALIENTE'])].copy()
            
            self.logger.info(f"Separación WOM: {len(df_entrantes)} entrantes, {len(df_salientes)} salientes")
            
            # === PROCESAMIENTO EN CHUNKS ===
            
            total_records_processed = 0
            total_records_failed = 0
            total_duplicated = 0          # NUEVO: contador de duplicados
            total_validation_failed = 0  # NUEVO: contador de errores de validación
            total_other_errors = 0       # NUEVO: contador de otros errores
            all_failed_records = []
            
            # Procesar llamadas entrantes
            if len(df_entrantes) > 0:
                for chunk_df in self._chunk_dataframe(df_entrantes, self.CHUNK_SIZE):
                    chunk_result = self._process_wom_call_chunk(
                        chunk_df, 'ENTRANTE', file_upload_id, mission_id
                    )
                    
                    total_records_processed += chunk_result.get('records_processed', 0)
                    total_records_failed += chunk_result.get('records_failed', 0)
                    total_duplicated += chunk_result.get('records_duplicated', 0)          # NUEVO
                    total_validation_failed += chunk_result.get('validation_failed', 0)  # NUEVO
                    total_other_errors += chunk_result.get('other_errors', 0)             # NUEVO
                    
                    if chunk_result.get('failed_records'):
                        all_failed_records.extend(chunk_result['failed_records'])
                    
                    if not chunk_result.get('success', False):
                        self.logger.error(f"Error procesando chunk WOM entrantes: {chunk_result.get('error')}")
            
            # Procesar llamadas salientes
            if len(df_salientes) > 0:
                for chunk_df in self._chunk_dataframe(df_salientes, self.CHUNK_SIZE):
                    chunk_result = self._process_wom_call_chunk(
                        chunk_df, 'SALIENTE', file_upload_id, mission_id
                    )
                    
                    total_records_processed += chunk_result.get('records_processed', 0)
                    total_records_failed += chunk_result.get('records_failed', 0)
                    total_duplicated += chunk_result.get('records_duplicated', 0)          # NUEVO
                    total_validation_failed += chunk_result.get('validation_failed', 0)  # NUEVO
                    total_other_errors += chunk_result.get('other_errors', 0)             # NUEVO
                    
                    if chunk_result.get('failed_records'):
                        all_failed_records.extend(chunk_result['failed_records'])
                    
                    if not chunk_result.get('success', False):
                        self.logger.error(f"Error procesando chunk WOM salientes: {chunk_result.get('error')}")
            
            # === RESULTADO FINAL ===
            
            processing_time = datetime.now() - start_time
            
            self.logger.info(
                f"Procesamiento WOM llamadas completado: {total_records_processed} exitosos, {total_records_failed} fallidos",
                extra={
                    'processing_time_seconds': processing_time.total_seconds(),
                    'entrantes_count': len(df_entrantes),
                    'salientes_count': len(df_salientes)
                }
            )
            
            # Actualizar tabla operator_data_sheets con conteo final
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    
                    processing_status = 'COMPLETED' if total_records_failed == 0 else 'FAILED'
                    
                    cursor.execute("""
                        UPDATE operator_data_sheets 
                        SET processing_status = ?, 
                            records_processed = ?, 
                            records_failed = ?,
                            processing_end_time = CURRENT_TIMESTAMP,
                            processing_duration_seconds = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (
                        processing_status,
                        total_records_processed,
                        total_records_failed,
                        int(processing_time.total_seconds()),
                        file_upload_id
                    ))
                    
                    conn.commit()
                    
                    self.logger.info(f"Estado de procesamiento WOM llamadas actualizado: {processing_status}")
            except Exception as update_error:
                self.logger.error(f"Error actualizando estado final WOM llamadas: {update_error}")
            
            return {
                'success': True,
                'processedRecords': total_records_processed,  # CORRECCIÓN: Usar nombre consistente con frontend
                'records_processed': total_records_processed,  # Mantener por compatibilidad
                'records_failed': total_records_failed,
                'records_duplicated': total_duplicated,                    # NUEVO: contador exacto de duplicados
                'records_validation_failed': total_validation_failed,     # NUEVO: contador exacto de errores de validación
                'records_other_errors': total_other_errors,               # NUEVO: contador exacto de otros errores
                'failed_records': all_failed_records[:10],  # Limitar a primeros 10 errores
                'details': {
                    'processing_time_seconds': processing_time.total_seconds(),
                    'entrantes_processed': len(df_entrantes),
                    'salientes_processed': len(df_salientes),
                    'sheets_combined': len(dfs) if file_name.lower().endswith('.xlsx') else 1,
                    'technology_distribution': df_clean['operador_tecnologia'].value_counts().to_dict() if 'operador_tecnologia' in df_clean.columns else {}
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error crítico procesando archivo WOM llamadas {file_name}: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Error crítico: {str(e)}',
                'processedRecords': 0,  # CORRECCIÓN: Usar nombre consistente con frontend
                'records_processed': 0,  # Mantener por compatibilidad
                'records_failed': 0
            }

    def _process_wom_cellular_chunk(self, df_chunk: pd.DataFrame,
                                   file_upload_id: str, mission_id: str) -> Dict[str, Any]:
        """
        Procesa un chunk de datos celulares WOM.
        
        Args:
            df_chunk: DataFrame con registros del chunk
            file_upload_id: ID del archivo fuente
            mission_id: ID de la misión
            
        Returns:
            Dict con resultado del procesamiento del chunk
        """
        chunk_number = getattr(self, '_current_chunk_number', 0) + 1
        setattr(self, '_current_chunk_number', chunk_number)
        
        records_processed = 0
        records_failed = 0
        records_duplicated = 0  # NUEVO: contador de duplicados
        validation_failed = 0   # NUEVO: contador de errores de validación
        other_errors = 0        # NUEVO: contador de otros errores
        failed_records = []
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                for index, row in df_chunk.iterrows():
                    try:
                        # Normalizar registro WOM usando DataNormalizerService
                        normalized_data = self.data_normalizer.normalize_wom_cellular_data_record(
                            dict(row), file_upload_id, mission_id
                        )
                        
                        if not normalized_data:
                            records_failed += 1
                            failed_records.append({
                                'row': index + 1,
                                'errors': ['No se pudo normalizar el registro'],
                                'record': dict(row)
                            })
                            continue
                        
                        # Insertar en tabla unificada operator_cellular_data
                        cursor.execute("""
                            INSERT INTO operator_cellular_data (
                                file_upload_id, mission_id, operator, numero_telefono,
                                fecha_hora_inicio, fecha_hora_fin, duracion_segundos, celda_id, 
                                lac_tac, trafico_subida_bytes, trafico_bajada_bytes, latitud, 
                                longitud, tecnologia, tipo_conexion, operator_specific_data, record_hash
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            normalized_data['file_upload_id'],
                            normalized_data['mission_id'],
                            'WOM',
                            normalized_data['numero_origen'],
                            normalized_data['fecha_hora_inicio'],
                            normalized_data['fecha_hora_fin'],
                            normalized_data['duracion_seg'],
                            str(normalized_data.get('cell_id_voz', '')),
                            str(normalized_data.get('tac', '')),
                            normalized_data.get('up_data_bytes', 0),
                            normalized_data.get('down_data_bytes', 0),
                            normalized_data.get('latitud'),
                            normalized_data.get('longitud'),
                            self._map_wom_technology(normalized_data.get('operator_technology', 'WOM')),
                            'DATOS',
                            json.dumps({
                                'bts_id': normalized_data.get('bts_id'),
                                'imsi': normalized_data.get('imsi'),
                                'localizacion_usuario': normalized_data.get('localizacion_usuario'),
                                'nombre_antena': normalized_data.get('nombre_antena'),
                                'direccion': normalized_data.get('direccion'),
                                'localidad': normalized_data.get('localidad'),
                                'ciudad': normalized_data.get('ciudad'),
                                'departamento': normalized_data.get('departamento'),
                                'regional': normalized_data.get('regional'),
                                'entorno_geografico': normalized_data.get('entorno_geografico'),
                                'uli': normalized_data.get('uli'),
                                'operador_ran': normalized_data.get('operador_ran')
                            }),
                            hashlib.md5(f"{normalized_data['numero_origen']}{normalized_data['fecha_hora_inicio']}{normalized_data.get('cell_id_voz', '')}".encode()).hexdigest()
                        ))
                        
                        records_processed += 1
                        
                    except Exception as record_error:
                        error_str = str(record_error)
                        
                        # NUEVO: Distinguir tipos de errores por mensaje
                        if "UNIQUE constraint failed" in error_str:
                            # Es un duplicado legítimo - NO cuenta como error para el límite
                            records_duplicated += 1
                            error_type = 'duplicate'
                            self.logger.debug(f"Registro duplicado omitido WOM cellular {index + 1} en chunk {chunk_number}: {error_str}")
                        else:
                            # Error real - cuenta para el límite de errores
                            records_failed += 1
                            if "constraint failed" in error_str.lower() or "check constraint" in error_str.lower():
                                validation_failed += 1
                                error_type = 'validation'
                            else:
                                other_errors += 1
                                error_type = 'other'
                            
                            self.logger.warning(f"Error procesando registro WOM cellular chunk {chunk_number} fila {index + 1}: {record_error}")
                            
                            failed_records.append({
                                'row': index + 1,
                                'error_type': error_type,
                                'errors': [error_str],
                                'record': dict(row)
                            })
                
                conn.commit()
                
                self.logger.debug(
                    f"Chunk WOM cellular {chunk_number} procesado: {records_processed} exitosos, {records_failed} fallidos ({records_duplicated} duplicados, {validation_failed} validación, {other_errors} otros)"
                )
                
                return {
                    'success': True,
                    'records_processed': records_processed,
                    'records_failed': records_failed,
                    'records_duplicated': records_duplicated,      # NUEVO
                    'validation_failed': validation_failed,       # NUEVO
                    'other_errors': other_errors,                 # NUEVO
                    'failed_records': failed_records[:10]  # Limitar detalle
                }
                
        except Exception as e:
            self.logger.error(f"Error crítico procesando chunk WOM cellular {chunk_number}: {e}")
            return {
                'success': False,
                'error': str(e),
                'records_processed': records_processed,
                'records_failed': records_failed,
                'records_duplicated': records_duplicated,
                'validation_failed': validation_failed,
                'other_errors': other_errors
            }

    def _process_wom_call_chunk(self, df_chunk: pd.DataFrame, call_direction: str,
                               file_upload_id: str, mission_id: str) -> Dict[str, Any]:
        """
        Procesa un chunk de datos de llamadas WOM para un tipo específico de llamada.
        
        Args:
            df_chunk: DataFrame con registros del chunk
            call_direction: 'ENTRANTE' o 'SALIENTE'
            file_upload_id: ID del archivo fuente
            mission_id: ID de la misión
            
        Returns:
            Dict con resultado del procesamiento del chunk
        """
        chunk_number = getattr(self, '_current_chunk_number', 0) + 1
        setattr(self, '_current_chunk_number', chunk_number)
        
        records_processed = 0
        records_failed = 0
        records_duplicated = 0  # NUEVO: contador de duplicados
        validation_failed = 0   # NUEVO: contador de errores de validación
        other_errors = 0        # NUEVO: contador de otros errores
        failed_records = []
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                for index, row in df_chunk.iterrows():
                    try:
                        # Normalizar registro WOM usando DataNormalizerService
                        normalized_data = self.data_normalizer.normalize_wom_call_data_record(
                            dict(row), file_upload_id, mission_id, call_direction
                        )
                        
                        if not normalized_data:
                            records_failed += 1
                            failed_records.append({
                                'row': index + 1,
                                'errors': ['No se pudo normalizar el registro'],
                                'record': dict(row)
                            })
                            continue
                        
                        # Insertar en tabla unificada operator_call_data
                        cursor.execute("""
                            INSERT INTO operator_call_data (
                                file_upload_id, mission_id, operator, tipo_llamada, numero_origen,
                                numero_destino, numero_objetivo, fecha_hora_llamada, duracion_segundos,
                                celda_origen, celda_destino, celda_objetivo, latitud_origen, longitud_origen,
                                latitud_destino, longitud_destino, calidad_senal, tecnologia,
                                operator_specific_data, record_hash
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            normalized_data['file_upload_id'],
                            normalized_data['mission_id'],
                            'WOM',
                            call_direction,
                            normalized_data['numero_origen'],
                            normalized_data['numero_destino'],
                            normalized_data['numero_destino'] if call_direction == 'SALIENTE' else normalized_data['numero_origen'],
                            normalized_data['fecha_hora_inicio'],
                            normalized_data['duracion_seg'],
                            str(normalized_data.get('cell_id_voz', '')),
                            None,  # celda_destino no disponible en WOM
                            str(normalized_data.get('cell_id_voz', '')),
                            normalized_data.get('latitud'),
                            normalized_data.get('longitud'),
                            None,  # latitud_destino no disponible
                            None,  # longitud_destino no disponible
                            None,  # calidad_senal no disponible en WOM
                            self._map_wom_technology(normalized_data.get('operator_technology', 'WOM')),
                            json.dumps({
                                'bts_id': normalized_data.get('bts_id'),
                                'tac': normalized_data.get('tac'),
                                'sector': normalized_data.get('sector'),
                                'operador_ran_origen': normalized_data.get('operador_ran_origen'),
                                'user_location_info': normalized_data.get('user_location_info'),
                                'access_network_information': normalized_data.get('access_network_information'),
                                'imei': normalized_data.get('imei'),
                                'imsi': normalized_data.get('imsi'),
                                'nombre_antena': normalized_data.get('nombre_antena'),
                                'direccion': normalized_data.get('direccion'),
                                'localidad': normalized_data.get('localidad'),
                                'ciudad': normalized_data.get('ciudad'),
                                'departamento': normalized_data.get('departamento'),
                                'sentido': normalized_data.get('sentido'),
                                'fecha_hora_fin': normalized_data.get('fecha_hora_fin')
                            }),
                            hashlib.md5(f"{normalized_data['numero_origen']}{normalized_data['numero_destino']}{normalized_data['fecha_hora_inicio']}".encode()).hexdigest()
                        ))
                        
                        records_processed += 1
                        
                    except Exception as record_error:
                        error_str = str(record_error)
                        
                        # NUEVO: Distinguir tipos de errores por mensaje
                        if "UNIQUE constraint failed" in error_str:
                            # Es un duplicado legítimo - NO cuenta como error para el límite
                            records_duplicated += 1
                            error_type = 'duplicate'
                            self.logger.debug(f"Registro duplicado omitido WOM call {call_direction} {index + 1} en chunk {chunk_number}: {error_str}")
                        else:
                            # Error real - cuenta para el límite de errores
                            records_failed += 1
                            if "constraint failed" in error_str.lower() or "check constraint" in error_str.lower():
                                validation_failed += 1
                                error_type = 'validation'
                            else:
                                other_errors += 1
                                error_type = 'other'
                            
                            self.logger.warning(f"Error procesando registro WOM call {call_direction} chunk {chunk_number} fila {index + 1}: {record_error}")
                            
                            failed_records.append({
                                'row': index + 1,
                                'error_type': error_type,
                                'errors': [error_str],
                                'record': dict(row)
                            })
                
                conn.commit()
                
                self.logger.debug(
                    f"Chunk WOM {call_direction} {chunk_number} procesado: {records_processed} exitosos, {records_failed} fallidos ({records_duplicated} duplicados, {validation_failed} validación, {other_errors} otros)"
                )
                
                return {
                    'success': True,
                    'records_processed': records_processed,
                    'records_failed': records_failed,
                    'records_duplicated': records_duplicated,      # NUEVO
                    'validation_failed': validation_failed,       # NUEVO
                    'other_errors': other_errors,                 # NUEVO
                    'failed_records': failed_records[:10]  # Limitar detalle
                }
                
        except Exception as e:
            self.logger.error(f"Error crítico procesando chunk WOM {call_direction} {chunk_number}: {e}")
            return {
                'success': False,
                'error': str(e),
                'records_processed': records_processed,
                'records_failed': records_failed,
                'records_duplicated': records_duplicated,
                'validation_failed': validation_failed,
                'other_errors': other_errors
            }
            
    def _map_wom_technology(self, technology_value: str) -> str:
        """
        Mapea tecnologías WOM a valores estándar para BD.
        """
        if not technology_value or not isinstance(technology_value, str):
            return 'UNKNOWN'
        
        tech_upper = technology_value.upper().strip()
        
        # Mapeo directo
        mapping = {
            'WOM 3G': '3G',
            'WOM 4G': '4G',
            'WOM 5G': '5G',
            'WOM LTE': 'LTE',
            'WOM GSM': 'GSM',
            'WOM 2G': '2G'
        }
        
        if tech_upper in mapping:
            return mapping[tech_upper]
        
        # Busqueda parcial
        if '3G' in tech_upper:
            return '3G'
        elif '4G' in tech_upper:
            return '4G' 
        elif '5G' in tech_upper:
            return '5G'
        elif 'LTE' in tech_upper:
            return 'LTE'
        elif 'GSM' in tech_upper:
            return 'GSM'
        elif '2G' in tech_upper:
            return '2G'
        
        return 'UNKNOWN'

    def process_scanhunter_data(self, file_bytes: bytes, file_name: str,
                               file_upload_id: str, mission_id: str) -> Dict[str, Any]:
        """
        Procesa un archivo de datos SCANHUNTER para mediciones de scanner celular.
        
        SCANHUNTER es un formato específico para datos de scanner celular con columnas:
        ['Id', 'Punto', 'Latitud', 'Longitud', 'MNC+MCC', 'OPERADOR', 'RSSI', 
         'TECNOLOGIA', 'CELLID', 'LAC o TAC', 'ENB', 'Comentario', 'CHANNEL']
        
        Args:
            file_bytes (bytes): Contenido del archivo
            file_name (str): Nombre del archivo
            file_upload_id (str): ID único del archivo
            mission_id (str): ID de la misión
            
        Returns:
            Dict[str, Any]: Resultado del procesamiento
        """
        start_time = datetime.now()
        
        self.logger.info(
            f"Iniciando procesamiento SCANHUNTER: {file_name}",
            extra={'file_size': len(file_bytes), 'file_upload_id': file_upload_id}
        )
        
        try:
            # === ETAPA 1: LECTURA DEL ARCHIVO ===
            
            # Determinar tipo de archivo
            file_extension = Path(file_name).suffix.lower()
            
            if file_extension == '.xlsx':
                df = self._read_excel_robust(file_bytes)
            elif file_extension == '.csv':
                df = self._read_csv_robust(file_bytes, delimiter=',')  # SCANHUNTER típicamente usa comas
            else:
                return {
                    'success': False,
                    'error': f'Formato de archivo no soportado para SCANHUNTER: {file_extension}'
                }
            
            self.logger.info(f"Archivo SCANHUNTER leído: {len(df)} registros, {len(df.columns)} columnas")
            
            # === ETAPA 2: VALIDACIÓN DE ESTRUCTURA ===
            
            is_valid_structure, structure_errors = self._validate_scanhunter_columns(df)
            if not is_valid_structure:
                return {
                    'success': False,
                    'error': f'Estructura de archivo SCANHUNTER inválida: {"; ".join(structure_errors)}'
                }
            
            # === ETAPA 3: LIMPIEZA DE DATOS ===
            
            original_count = len(df)
            df = self._clean_scanhunter_data(df)
            cleaned_count = len(df)
            
            if cleaned_count == 0:
                return {
                    'success': False,
                    'error': 'No quedaron registros válidos después de la limpieza'
                }
            
            if cleaned_count < original_count:
                self.logger.warning(
                    f"Se descartaron {original_count - cleaned_count} registros durante la limpieza SCANHUNTER"
                )
            
            # === ETAPA 4: PROCESAMIENTO POR CHUNKS ===
            
            total_processed = 0
            total_failed = 0
            chunk_number = 0
            processing_errors = []
            
            # Procesar en chunks para manejar archivos grandes
            for start_idx in range(0, len(df), self.CHUNK_SIZE):
                chunk_number += 1
                end_idx = min(start_idx + self.CHUNK_SIZE, len(df))
                chunk_df = df.iloc[start_idx:end_idx]
                
                self.logger.debug(f"Procesando chunk SCANHUNTER {chunk_number}: registros {start_idx+1} a {end_idx}")
                
                chunk_result = self._process_scanhunter_chunk(
                    chunk_df, file_upload_id, mission_id, chunk_number
                )
                
                if chunk_result.get('success', False):
                    total_processed += chunk_result.get('records_processed', 0)
                    total_failed += chunk_result.get('records_failed', 0)
                    
                    # Acumular errores detallados (limitado)
                    if chunk_result.get('failed_records'):
                        processing_errors.extend(chunk_result['failed_records'][:5])
                        if len(processing_errors) > 20:  # Límite total de errores detallados
                            processing_errors = processing_errors[:20]
                
                else:
                    # Error crítico en el chunk
                    error_msg = chunk_result.get('error', 'Error desconocido en chunk')
                    self.logger.error(f"Error crítico en chunk SCANHUNTER {chunk_number}: {error_msg}")
                    
                    return {
                        'success': False,
                        'error': f'Error crítico en procesamiento chunk {chunk_number}: {error_msg}',
                        'partial_results': {
                            'processedRecords': total_processed,
                            'records_failed': total_failed,
                            'chunks_completed': chunk_number - 1
                        }
                    }
                
                # Verificar si hay demasiados errores
                if total_failed > self.MAX_ERRORS_PER_FILE:
                    self.logger.error(
                        f"Demasiados errores en SCANHUNTER ({total_failed}), abortando procesamiento"
                    )
                    return {
                        'success': False,
                        'error': f'Demasiados errores: {total_failed} > {self.MAX_ERRORS_PER_FILE}',
                        'partial_results': {
                            'processedRecords': total_processed,
                            'records_failed': total_failed,
                            'chunks_completed': chunk_number
                        }
                    }
            
            # === RESULTADO FINAL ===
            
            processing_time = (datetime.now() - start_time).total_seconds()
            success_rate = (total_processed / (total_processed + total_failed)) * 100 if (total_processed + total_failed) > 0 else 0
            
            result = {
                'success': True,
                'processedRecords': total_processed,
                'records_failed': total_failed,
                'success_rate': round(success_rate, 2),
                'processing_time_seconds': round(processing_time, 2),
                'chunks_processed': chunk_number,
                'file_info': {
                    'name': file_name,
                    'size_bytes': len(file_bytes),
                    'original_records': original_count,
                    'cleaned_records': cleaned_count
                }
            }
            
            # Agregar errores detallados si los hay
            if processing_errors:
                result['processing_errors'] = processing_errors
            
            self.logger.info(
                f"SCANHUNTER procesado exitosamente: {total_processed} registros, "
                f"{success_rate:.2f}% éxito, {processing_time:.2f}s",
                extra={
                    'processedRecords': total_processed,
                    'records_failed': total_failed,
                    'processing_time': processing_time,
                    'file_upload_id': file_upload_id
                }
            )
            
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(
                f"Error crítico procesando SCANHUNTER {file_name}: {str(e)}",
                exc_info=True,
                extra={'file_upload_id': file_upload_id, 'processing_time': processing_time}
            )
            
            return {
                'success': False,
                'error': f'Error crítico: {str(e)}',
                'processing_time_seconds': round(processing_time, 2)
            }

    def _validate_scanhunter_columns(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Valida que el DataFrame tenga las columnas esperadas de SCANHUNTER.
        
        Args:
            df (pd.DataFrame): DataFrame a validar
            
        Returns:
            Tuple[bool, List[str]]: (es_válido, lista_de_errores)
        """
        errors = []
        
        # Columnas esperadas de SCANHUNTER
        expected_columns = [
            'Id', 'Punto', 'Latitud', 'Longitud', 'MNC+MCC', 'OPERADOR', 
            'RSSI', 'TECNOLOGIA', 'CELLID', 'LAC o TAC', 'ENB', 'Comentario', 'CHANNEL'
        ]
        
        # Verificar que tenga todas las columnas requeridas
        missing_columns = []
        for col in expected_columns:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            errors.append(f"Columnas faltantes: {', '.join(missing_columns)}")
        
        # Verificar que no esté vacío
        if len(df) == 0:
            errors.append("El archivo está vacío")
        
        # Verificar tipos de datos básicos
        if len(df) > 0:
            try:
                # Verificar que latitud y longitud sean numéricos
                if 'Latitud' in df.columns:
                    pd.to_numeric(df['Latitud'], errors='coerce')
                if 'Longitud' in df.columns:
                    pd.to_numeric(df['Longitud'], errors='coerce')
                if 'RSSI' in df.columns:
                    pd.to_numeric(df['RSSI'], errors='coerce')
            except Exception as e:
                errors.append(f"Error validando tipos de datos: {str(e)}")
        
        is_valid = len(errors) == 0
        
        if is_valid:
            self.logger.info(f"Estructura SCANHUNTER válida: {len(df)} registros, {len(df.columns)} columnas")
        else:
            self.logger.error(f"Estructura SCANHUNTER inválida: {'; '.join(errors)}")
        
        return is_valid, errors

    def _clean_scanhunter_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpia y prepara datos SCANHUNTER para procesamiento.
        
        Args:
            df (pd.DataFrame): DataFrame bruto
            
        Returns:
            pd.DataFrame: DataFrame limpio
        """
        df_clean = df.copy()
        original_count = len(df_clean)
        
        try:
            # === LIMPIEZA DE COORDENADAS ===
            
            # Convertir coordenadas a numérico, eliminando registros inválidos
            df_clean['Latitud'] = pd.to_numeric(df_clean['Latitud'], errors='coerce')
            df_clean['Longitud'] = pd.to_numeric(df_clean['Longitud'], errors='coerce')
            
            # Eliminar registros con coordenadas inválidas
            df_clean = df_clean.dropna(subset=['Latitud', 'Longitud'])
            
            # Validar rangos de coordenadas
            df_clean = df_clean[
                (df_clean['Latitud'] >= -90) & (df_clean['Latitud'] <= 90) &
                (df_clean['Longitud'] >= -180) & (df_clean['Longitud'] <= 180)
            ]
            
            # === LIMPIEZA DE RSSI ===
            
            # Convertir RSSI a numérico
            df_clean['RSSI'] = pd.to_numeric(df_clean['RSSI'], errors='coerce')
            df_clean = df_clean.dropna(subset=['RSSI'])
            
            # Validar rango de RSSI (debe ser negativo, típicamente entre -150 y 0)
            df_clean = df_clean[
                (df_clean['RSSI'] <= 0) & (df_clean['RSSI'] >= -150)
            ]
            
            # === LIMPIEZA DE CAMPOS DE TEXTO ===
            
            # Limpiar y validar campos obligatorios de texto
            text_fields = ['Punto', 'OPERADOR', 'TECNOLOGIA']
            for field in text_fields:
                if field in df_clean.columns:
                    # Convertir a string y limpiar
                    df_clean[field] = df_clean[field].astype(str).str.strip()
                    # Eliminar registros con valores vacíos o 'nan'
                    df_clean = df_clean[
                        (df_clean[field] != '') & 
                        (df_clean[field] != 'nan') & 
                        (df_clean[field] != 'None')
                    ]
            
            # === LIMPIEZA DE CAMPOS TÉCNICOS ===
            
            # Limpiar CELLID, LAC o TAC, ENB
            numeric_fields = ['CELLID', 'LAC o TAC', 'ENB', 'CHANNEL']
            for field in numeric_fields:
                if field in df_clean.columns:
                    df_clean[field] = pd.to_numeric(df_clean[field], errors='coerce')
                    # No eliminar registros por estos campos, solo convertir
            
            # Limpiar MNC+MCC (debe ser numérico y positivo)
            if 'MNC+MCC' in df_clean.columns:
                df_clean['MNC+MCC'] = pd.to_numeric(df_clean['MNC+MCC'], errors='coerce')
                df_clean = df_clean.dropna(subset=['MNC+MCC'])
                df_clean = df_clean[df_clean['MNC+MCC'] > 0]
            
            # === NORMALIZACIÓN DE TECNOLOGÍA ===
            
            if 'TECNOLOGIA' in df_clean.columns:
                df_clean['TECNOLOGIA'] = df_clean['TECNOLOGIA'].str.upper().str.strip()
                # Mapear tecnologías conocidas
                tech_mapping = {
                    'LTE': '4G',
                    'UMTS': '3G',
                    'WCDMA': '3G',
                    'EDGE': '2G',
                    'GPRS': '2G'
                }
                df_clean['TECNOLOGIA'] = df_clean['TECNOLOGIA'].replace(tech_mapping)
            
            cleaned_count = len(df_clean)
            
            self.logger.info(
                f"Limpieza SCANHUNTER completada: {original_count} -> {cleaned_count} registros "
                f"({((original_count - cleaned_count) / original_count) * 100:.1f}% descartados)"
            )
            
            return df_clean
            
        except Exception as e:
            self.logger.error(f"Error en limpieza SCANHUNTER: {str(e)}", exc_info=True)
            # Devolver DataFrame original en caso de error
            return df

    def _process_scanhunter_chunk(self, chunk_df: pd.DataFrame, file_upload_id: str,
                                 mission_id: str, chunk_number: int) -> Dict[str, Any]:
        """
        Procesa un chunk de datos SCANHUNTER.
        
        Args:
            chunk_df (pd.DataFrame): Chunk de datos a procesar
            file_upload_id (str): ID del archivo
            mission_id (str): ID de la misión
            chunk_number (int): Número del chunk para logging
            
        Returns:
            Dict[str, Any]: Resultado del procesamiento del chunk
        """
        records_processed = 0
        records_failed = 0
        failed_records = []
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                for index, row in chunk_df.iterrows():
                    try:
                        # Convertir fila a diccionario
                        record = row.to_dict()
                        
                        # Validar registro
                        is_valid, errors = self._validate_scanhunter_record(record)
                        if not is_valid:
                            records_failed += 1
                            failed_records.append({
                                'row': index + 1,
                                'errors': errors,
                                'record': record
                            })
                            
                            if len(failed_records) > 10:  # Limitar detalle de errores
                                break
                            continue
                        
                        # Normalizar datos usando DataNormalizerService
                        normalized_data = self.data_normalizer.normalize_scanhunter_data(
                            record, file_upload_id, mission_id
                        )
                        
                        if not normalized_data:
                            records_failed += 1
                            failed_records.append({
                                'row': index + 1,
                                'errors': ['Error en normalización'],
                                'record': record
                            })
                            continue
                        
                        # Insertar en tabla cellular_data (que ya tiene los campos expandidos)
                        cursor.execute("""
                            INSERT INTO cellular_data (
                                mission_id, file_record_id, punto, lat, lon, mnc_mcc, operator,
                                rssi, tecnologia, cell_id, lac_tac, enb, 
                                comentario, channel, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        """, (
                            normalized_data['mission_id'],
                            normalized_data.get('file_record_id'),
                            normalized_data['punto'],
                            normalized_data['lat'],
                            normalized_data['lon'],
                            normalized_data['mnc_mcc'],
                            normalized_data['operator'],
                            normalized_data['rssi'],
                            normalized_data['tecnologia'],
                            normalized_data['cell_id'],
                            normalized_data['lac_tac'],
                            normalized_data['enb'],
                            normalized_data['comentario'],
                            normalized_data['channel']
                        ))
                        
                        records_processed += 1
                        
                    except Exception as e:
                        records_failed += 1
                        failed_records.append({
                            'row': index + 1,
                            'errors': [f'Error procesando registro: {str(e)}'],
                            'record': record if 'record' in locals() else {}
                        })
                        
                        self.logger.error(
                            f"Error procesando registro SCANHUNTER {index + 1}: {str(e)}",
                            extra={'chunk_number': chunk_number, 'row_index': index}
                        )
                        
                        if len(failed_records) > 10:
                            break
                
                # Commit del chunk
                conn.commit()
                
            self.logger.info(
                f"Chunk SCANHUNTER {chunk_number} procesado: "
                f"{records_processed} exitosos, {records_failed} fallidos"
            )
            
            return {
                'success': True,
                'records_processed': records_processed,
                'records_failed': records_failed,
                'failed_records': failed_records if failed_records else None
            }
            
        except Exception as e:
            self.logger.error(f"Error crítico en chunk SCANHUNTER {chunk_number}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'records_processed': records_processed,
                'records_failed': records_failed
            }

    def _validate_scanhunter_record(self, record: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida un registro individual de SCANHUNTER.
        
        Args:
            record (Dict[str, Any]): Registro a validar
            
        Returns:
            Tuple[bool, List[str]]: (es_válido, lista_de_errores)
        """
        errors = []
        
        # Campos obligatorios
        required_fields = ['Punto', 'Latitud', 'Longitud', 'OPERADOR', 'RSSI', 'TECNOLOGIA', 'CELLID']
        
        for field in required_fields:
            if field not in record or record[field] is None:
                errors.append(f"Campo obligatorio faltante: {field}")
            elif field in ['Punto', 'OPERADOR', 'TECNOLOGIA'] and str(record[field]).strip() == '':
                errors.append(f"Campo obligatorio vacío: {field}")
        
        # Validaciones específicas si los campos están presentes
        try:
            # Coordenadas
            if 'Latitud' in record and record['Latitud'] is not None:
                lat = float(record['Latitud'])
                if lat < -90 or lat > 90:
                    errors.append(f"Latitud fuera de rango: {lat}")
            
            if 'Longitud' in record and record['Longitud'] is not None:
                lon = float(record['Longitud'])
                if lon < -180 or lon > 180:
                    errors.append(f"Longitud fuera de rango: {lon}")
            
            # RSSI
            if 'RSSI' in record and record['RSSI'] is not None:
                rssi = int(record['RSSI'])
                if rssi > 0 or rssi < -150:
                    errors.append(f"RSSI fuera de rango esperado: {rssi} (debe estar entre -150 y 0)")
            
            # MNC+MCC
            if 'MNC+MCC' in record and record['MNC+MCC'] is not None:
                mnc_mcc = int(record['MNC+MCC'])
                if mnc_mcc <= 0:
                    errors.append(f"MNC+MCC inválido: {mnc_mcc}")
            
        except (ValueError, TypeError) as e:
            errors.append(f"Error de tipo de dato: {str(e)}")
        
        return len(errors) == 0, errors


# ==============================================================================
# FUNCIONES DE UTILIDAD Y TESTING
# ==============================================================================

def test_claro_file_processing(file_path: str, mission_id: str = 'test-mission') -> None:
    """
    Función de testing para procesamiento de archivos CLARO.
    No expuesta via Eel, solo para desarrollo/debugging.
    """
    service = FileProcessorService()
    
    try:
        # Leer archivo de prueba
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
        
        file_name = Path(file_path).name
        file_upload_id = f"test-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"Procesando archivo de prueba: {file_name}")
        print(f"Tamaño: {len(file_bytes)} bytes")
        
        result = service.process_claro_data_por_celda(
            file_bytes, file_name, file_upload_id, mission_id
        )
        
        print(f"Resultado: {result}")
        
    except Exception as e:
        print(f"Error en test: {e}")


if __name__ == "__main__":
    # Código de testing básico
    service = FileProcessorService()
    print("FileProcessorService inicializado correctamente")
    
    # Test básico de detección de encoding
    test_data = "número,fecha_trafico,tipo_cdr\n573123456789,20240419080000,DATOS\n".encode('utf-8')
    encoding = service._detect_encoding(test_data)
    print(f"Encoding detectado: {encoding}")

