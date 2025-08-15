"""
KRONOS Scanner Cellular Data Processor
====================================================================
Procesador especializado para archivos de datos de scanner celular
en formato SCANHUNTER.xlsx con validación robusta y mapeo optimizado.

Características principales:
- Mapeo inteligente de columnas SCANHUNTER -> base de datos
- Validación integral de datos con reportes detallados
- Detección de duplicados y anomalías
- Procesamiento por lotes optimizado
- Integración con sistema de misiones KRONOS
====================================================================
"""

import pandas as pd
import numpy as np
import re
import hashlib
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import logging

# Configurar logging
logger = logging.getLogger(__name__)

class ValidationSeverity(Enum):
    """Niveles de severidad para validaciones"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationResult:
    """Resultado de validación para un registro"""
    row_index: int
    field: str
    severity: ValidationSeverity
    message: str
    original_value: Any
    suggested_value: Any = None

@dataclass
class ProcessingStats:
    """Estadísticas de procesamiento"""
    total_rows: int
    valid_rows: int
    invalid_rows: int
    warnings: int
    errors: int
    duplicates: int
    processing_time: float

class ScannerDataProcessor:
    """
    Procesador principal para datos de scanner celular SCANHUNTER
    """
    
    # Mapeo de columnas SCANHUNTER -> campo base de datos
    COLUMN_MAPPING = {
        'Id': 'measurement_sequence',
        'Punto': 'punto', 
        'Latitud': 'latitude',
        'Longitud': 'longitude',
        'MNC+MCC': 'mnc_mcc',
        'OPERADOR': 'operator_name',
        'RSSI': 'rssi_dbm',
        'TECNOLOGIA': 'technology',
        'CELLID': 'cell_id',
        'LAC o TAC': 'lac_tac',
        'ENB': 'enb_id',
        'Comentario': 'comentario',
        'CHANNEL': 'channel'
    }
    
    # Mapeo de operadores (normalización)
    OPERATOR_MAPPING = {
        'CLARO': 'CLARO',
        'COMCEL': 'CLARO',  # Nombre anterior de CLARO
        'MOVISTAR': 'MOVISTAR',
        'TELEFONICA': 'MOVISTAR',  # Nombre corporativo
        'TIGO': 'TIGO',
        'COLOMBIA MOVIL': 'TIGO',  # Nombre corporativo
        'WOM': 'WOM',
        'PARTNERS': 'PARTNERS',
        'ETB': 'ETB',
        'UNE': 'TIGO',  # UNE fue adquirido por TIGO
        'UNKNOWN': 'UNKNOWN'
    }
    
    # Mapeo de tecnologías (normalización)
    TECHNOLOGY_MAPPING = {
        'GSM': 'GSM',
        '2G': 'GSM',
        'UMTS': 'UMTS',
        '3G': '3G',
        'WCDMA': 'UMTS',
        'LTE': 'LTE',
        '4G': '4G',
        'NR': '5G NR',
        '5G': '5G',
        '5G NR': '5G NR',
        'UNKNOWN': 'UNKNOWN',
        '': 'UNKNOWN'
    }
    
    # Rangos válidos para MNC en Colombia (MCC 732)
    COLOMBIA_MNC_CODES = {
        '101': 'CLARO',  # Claro
        '102': 'CLARO',  # Claro
        '103': 'CLARO',  # Claro/ETB
        '111': 'MOVISTAR/TIGO',  # Compartido
        '123': 'MOVISTAR',  # Movistar
        '130': 'WOM',  # WOM
        '154': 'PARTNERS'  # Partners Telecom
    }
    
    def __init__(self, mission_id: str):
        """
        Inicializa el procesador para una misión específica
        
        Args:
            mission_id: ID de la misión KRONOS
        """
        self.mission_id = mission_id
        self.validation_results: List[ValidationResult] = []
        self.stats = ProcessingStats(0, 0, 0, 0, 0, 0, 0.0)
        self.duplicate_hashes: set = set()
        
    def process_file(self, file_path: str, filename: str = None) -> Tuple[pd.DataFrame, ProcessingStats, List[ValidationResult]]:
        """
        Procesa un archivo SCANHUNTER completo
        
        Args:
            file_path: Ruta al archivo Excel o CSV
            filename: Nombre del archivo (opcional)
            
        Returns:
            Tuple con (DataFrame procesado, estadísticas, validaciones)
        """
        start_time = datetime.now()
        
        try:
            # Cargar datos
            if file_path.lower().endswith('.xlsx'):
                df = pd.read_excel(file_path)
            elif file_path.lower().endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                raise ValueError(f"Formato de archivo no soportado: {file_path}")
                
            logger.info(f"Cargado archivo {filename or file_path} con {len(df)} filas")
            
            # Procesar DataFrame
            processed_df = self._process_dataframe(df, filename or file_path)
            
            # Calcular estadísticas finales
            end_time = datetime.now()
            self.stats.processing_time = (end_time - start_time).total_seconds()
            self.stats.total_rows = len(df)
            self.stats.valid_rows = len(processed_df)
            self.stats.invalid_rows = self.stats.total_rows - self.stats.valid_rows
            self.stats.warnings = len([v for v in self.validation_results if v.severity == ValidationSeverity.WARNING])
            self.stats.errors = len([v for v in self.validation_results if v.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]])
            
            logger.info(f"Procesamiento completado: {self.stats.valid_rows}/{self.stats.total_rows} registros válidos")
            
            return processed_df, self.stats, self.validation_results
            
        except Exception as e:
            logger.error(f"Error procesando archivo {filename or file_path}: {str(e)}")
            raise
    
    def _process_dataframe(self, df: pd.DataFrame, filename: str) -> pd.DataFrame:
        """
        Procesa un DataFrame con validaciones completas
        
        Args:
            df: DataFrame original
            filename: Nombre del archivo fuente
            
        Returns:
            DataFrame procesado y validado
        """
        # Resetear resultados anteriores
        self.validation_results.clear()
        self.duplicate_hashes.clear()
        
        # Verificar columnas requeridas
        self._validate_columns(df)
        
        # Mapear columnas
        mapped_df = self._map_columns(df)
        
        # Validar y limpiar datos
        validated_df = self._validate_and_clean_data(mapped_df)
        
        # Agregar metadatos
        validated_df = self._add_metadata(validated_df, filename)
        
        # Filtrar registros válidos
        valid_df = validated_df[validated_df['is_validated'] == True].copy()
        
        return valid_df
    
    def _validate_columns(self, df: pd.DataFrame) -> None:
        """Valida que estén presentes las columnas requeridas"""
        required_columns = ['Punto', 'Latitud', 'Longitud', 'OPERADOR', 'RSSI', 'CELLID']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            error_msg = f"Columnas requeridas faltantes: {', '.join(missing_columns)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Advertir sobre columnas opcionales faltantes
        optional_columns = ['MNC+MCC', 'TECNOLOGIA', 'LAC o TAC', 'ENB', 'Comentario', 'CHANNEL']
        missing_optional = [col for col in optional_columns if col not in df.columns]
        
        if missing_optional:
            logger.warning(f"Columnas opcionales faltantes: {', '.join(missing_optional)}")
    
    def _map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Mapea columnas SCANHUNTER a formato base de datos"""
        mapped_df = pd.DataFrame()
        
        for scanhunter_col, db_field in self.COLUMN_MAPPING.items():
            if scanhunter_col in df.columns:
                mapped_df[db_field] = df[scanhunter_col].copy()
            else:
                # Valor por defecto para columnas faltantes
                mapped_df[db_field] = None
        
        # Agregar campos requeridos por la base de datos
        mapped_df['mission_id'] = self.mission_id
        mapped_df['is_validated'] = False
        mapped_df['validation_errors'] = ''
        
        return mapped_df
    
    def _validate_and_clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Realiza validación y limpieza completa de todos los campos
        """
        cleaned_df = df.copy()
        
        for index, row in cleaned_df.iterrows():
            row_errors = []
            
            # Validar punto de medición
            punto_result = self._validate_punto(row['punto'], index)
            if punto_result:
                self.validation_results.append(punto_result)
                if punto_result.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
                    row_errors.append(punto_result.message)
                if punto_result.suggested_value:
                    cleaned_df.at[index, 'punto'] = punto_result.suggested_value
            
            # Validar coordenadas
            lat_result = self._validate_latitude(row['latitude'], index)
            if lat_result:
                self.validation_results.append(lat_result)
                if lat_result.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
                    row_errors.append(lat_result.message)
                elif lat_result.suggested_value is not None:
                    cleaned_df.at[index, 'latitude'] = lat_result.suggested_value
            
            lon_result = self._validate_longitude(row['longitude'], index)
            if lon_result:
                self.validation_results.append(lon_result)
                if lon_result.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
                    row_errors.append(lon_result.message)
                elif lon_result.suggested_value is not None:
                    cleaned_df.at[index, 'longitude'] = lon_result.suggested_value
            
            # Validar MNC+MCC
            mnc_result = self._validate_mnc_mcc(row['mnc_mcc'], index)
            if mnc_result:
                self.validation_results.append(mnc_result)
                if mnc_result.suggested_value:
                    cleaned_df.at[index, 'mnc_mcc'] = mnc_result.suggested_value
            
            # Validar operador
            operator_result = self._validate_operator(row['operator_name'], index)
            if operator_result:
                self.validation_results.append(operator_result)
                if operator_result.suggested_value:
                    cleaned_df.at[index, 'operator_name'] = operator_result.suggested_value
            
            # Validar RSSI
            rssi_result = self._validate_rssi(row['rssi_dbm'], index)
            if rssi_result:
                self.validation_results.append(rssi_result)
                if rssi_result.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
                    row_errors.append(rssi_result.message)
                elif rssi_result.suggested_value is not None:
                    cleaned_df.at[index, 'rssi_dbm'] = rssi_result.suggested_value
            
            # Validar tecnología
            tech_result = self._validate_technology(row['technology'], index)
            if tech_result:
                self.validation_results.append(tech_result)
                if tech_result.suggested_value:
                    cleaned_df.at[index, 'technology'] = tech_result.suggested_value
            
            # Validar Cell ID
            cell_result = self._validate_cell_id(row['cell_id'], index)
            if cell_result:
                self.validation_results.append(cell_result)
                if cell_result.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
                    row_errors.append(cell_result.message)
                elif cell_result.suggested_value:
                    cleaned_df.at[index, 'cell_id'] = cell_result.suggested_value
            
            # Detectar duplicados
            duplicate_result = self._check_duplicate(cleaned_df.iloc[index], index)
            if duplicate_result:
                self.validation_results.append(duplicate_result)
                self.stats.duplicates += 1
            
            # Establecer estado de validación
            if not row_errors:
                cleaned_df.at[index, 'is_validated'] = True
            else:
                cleaned_df.at[index, 'validation_errors'] = '; '.join(row_errors)
        
        return cleaned_df
    
    def _validate_punto(self, value: Any, row_index: int) -> Optional[ValidationResult]:
        """Valida campo punto de medición"""
        if pd.isna(value) or str(value).strip() == '':
            return ValidationResult(
                row_index, 'punto', ValidationSeverity.ERROR,
                "Punto de medición es requerido", value
            )
        
        cleaned_value = str(value).strip()
        
        if len(cleaned_value) > 100:
            return ValidationResult(
                row_index, 'punto', ValidationSeverity.WARNING,
                f"Punto de medición muy largo ({len(cleaned_value)} caracteres)", 
                value, cleaned_value[:100]
            )
        
        if cleaned_value != str(value):
            return ValidationResult(
                row_index, 'punto', ValidationSeverity.INFO,
                "Punto de medición limpiado (espacios)", value, cleaned_value
            )
        
        return None
    
    def _validate_latitude(self, value: Any, row_index: int) -> Optional[ValidationResult]:
        """Valida campo latitud"""
        if pd.isna(value):
            return ValidationResult(
                row_index, 'latitude', ValidationSeverity.ERROR,
                "Latitud es requerida", value
            )
        
        try:
            lat = float(value)
            
            if lat < -90.0 or lat > 90.0:
                return ValidationResult(
                    row_index, 'latitude', ValidationSeverity.ERROR,
                    f"Latitud fuera de rango válido (-90 a 90): {lat}", value
                )
            
            # Verificar si está en rango de Colombia (-4.2 a 15.9)
            if not (-4.5 <= lat <= 16.0):
                return ValidationResult(
                    row_index, 'latitude', ValidationSeverity.WARNING,
                    f"Latitud fuera del rango típico de Colombia: {lat}", value
                )
            
            return ValidationResult(
                row_index, 'latitude', ValidationSeverity.INFO,
                f"Latitud válida: {lat}", value, lat
            ) if lat != value else None
            
        except (ValueError, TypeError):
            return ValidationResult(
                row_index, 'latitude', ValidationSeverity.ERROR,
                f"Latitud no es un número válido: {value}", value
            )
    
    def _validate_longitude(self, value: Any, row_index: int) -> Optional[ValidationResult]:
        """Valida campo longitud"""
        if pd.isna(value):
            return ValidationResult(
                row_index, 'longitude', ValidationSeverity.ERROR,
                "Longitud es requerida", value
            )
        
        try:
            lon = float(value)
            
            if lon < -180.0 or lon > 180.0:
                return ValidationResult(
                    row_index, 'longitude', ValidationSeverity.ERROR,
                    f"Longitud fuera de rango válido (-180 a 180): {lon}", value
                )
            
            # Verificar si está en rango de Colombia (-82 a -66)
            if not (-83.0 <= lon <= -66.0):
                return ValidationResult(
                    row_index, 'longitude', ValidationSeverity.WARNING,
                    f"Longitud fuera del rango típico de Colombia: {lon}", value
                )
            
            return ValidationResult(
                row_index, 'longitude', ValidationSeverity.INFO,
                f"Longitud válida: {lon}", value, lon
            ) if lon != value else None
            
        except (ValueError, TypeError):
            return ValidationResult(
                row_index, 'longitude', ValidationSeverity.ERROR,
                f"Longitud no es un número válido: {value}", value
            )
    
    def _validate_mnc_mcc(self, value: Any, row_index: int) -> Optional[ValidationResult]:
        """Valida campo MNC+MCC"""
        if pd.isna(value) or str(value).strip() == '':
            return ValidationResult(
                row_index, 'mnc_mcc', ValidationSeverity.WARNING,
                "MNC+MCC vacío - se requerirá para análisis avanzado", value, "732000"
            )
        
        cleaned_value = str(value).strip()
        
        # Validar formato numérico
        if not cleaned_value.isdigit():
            return ValidationResult(
                row_index, 'mnc_mcc', ValidationSeverity.ERROR,
                f"MNC+MCC debe contener solo números: {cleaned_value}", value
            )
        
        # Validar longitud (5-6 dígitos)
        if len(cleaned_value) < 5 or len(cleaned_value) > 6:
            return ValidationResult(
                row_index, 'mnc_mcc', ValidationSeverity.ERROR,
                f"MNC+MCC debe tener 5-6 dígitos: {cleaned_value}", value
            )
        
        # Verificar MCC para Colombia (732)
        if not cleaned_value.startswith('732'):
            return ValidationResult(
                row_index, 'mnc_mcc', ValidationSeverity.WARNING,
                f"MCC no es 732 (Colombia): {cleaned_value}", value
            )
        
        return ValidationResult(
            row_index, 'mnc_mcc', ValidationSeverity.INFO,
            f"MNC+MCC válido: {cleaned_value}", value, cleaned_value
        ) if cleaned_value != str(value).strip() else None
    
    def _validate_operator(self, value: Any, row_index: int) -> Optional[ValidationResult]:
        """Valida campo operador"""
        if pd.isna(value) or str(value).strip() == '':
            return ValidationResult(
                row_index, 'operator_name', ValidationSeverity.ERROR,
                "Operador es requerido", value
            )
        
        original_operator = str(value).strip().upper()
        normalized_operator = self.OPERATOR_MAPPING.get(original_operator, 'UNKNOWN')
        
        if normalized_operator == 'UNKNOWN':
            return ValidationResult(
                row_index, 'operator_name', ValidationSeverity.WARNING,
                f"Operador no reconocido: {original_operator}", value, 'UNKNOWN'
            )
        
        if normalized_operator != original_operator:
            return ValidationResult(
                row_index, 'operator_name', ValidationSeverity.INFO,
                f"Operador normalizado: {original_operator} -> {normalized_operator}", 
                value, normalized_operator
            )
        
        return None
    
    def _validate_rssi(self, value: Any, row_index: int) -> Optional[ValidationResult]:
        """Valida campo RSSI"""
        if pd.isna(value):
            return ValidationResult(
                row_index, 'rssi_dbm', ValidationSeverity.ERROR,
                "RSSI es requerido", value
            )
        
        try:
            rssi = int(float(value))
            
            # RSSI debe ser negativo o cero
            if rssi > 0:
                # Intenta corregir si parece ser un valor positivo por error
                corrected_rssi = -abs(rssi)
                return ValidationResult(
                    row_index, 'rssi_dbm', ValidationSeverity.WARNING,
                    f"RSSI positivo corregido a negativo: {rssi} -> {corrected_rssi}", 
                    value, corrected_rssi
                )
            
            # Rango típico de RSSI: -30 a -120 dBm
            if rssi < -150:
                return ValidationResult(
                    row_index, 'rssi_dbm', ValidationSeverity.ERROR,
                    f"RSSI demasiado bajo (posible error): {rssi}", value
                )
            elif rssi > -30:
                return ValidationResult(
                    row_index, 'rssi_dbm', ValidationSeverity.WARNING,
                    f"RSSI inusualmente alto: {rssi}", value
                )
            
            return ValidationResult(
                row_index, 'rssi_dbm', ValidationSeverity.INFO,
                f"RSSI válido: {rssi}", value, rssi
            ) if rssi != value else None
            
        except (ValueError, TypeError):
            return ValidationResult(
                row_index, 'rssi_dbm', ValidationSeverity.ERROR,
                f"RSSI no es un número válido: {value}", value
            )
    
    def _validate_technology(self, value: Any, row_index: int) -> Optional[ValidationResult]:
        """Valida campo tecnología"""
        if pd.isna(value) or str(value).strip() == '':
            return ValidationResult(
                row_index, 'technology', ValidationSeverity.WARNING,
                "Tecnología vacía - asignando UNKNOWN", value, 'UNKNOWN'
            )
        
        original_tech = str(value).strip().upper()
        normalized_tech = self.TECHNOLOGY_MAPPING.get(original_tech, 'UNKNOWN')
        
        if normalized_tech == 'UNKNOWN':
            return ValidationResult(
                row_index, 'technology', ValidationSeverity.WARNING,
                f"Tecnología no reconocida: {original_tech}", value, 'UNKNOWN'
            )
        
        if normalized_tech != original_tech:
            return ValidationResult(
                row_index, 'technology', ValidationSeverity.INFO,
                f"Tecnología normalizada: {original_tech} -> {normalized_tech}", 
                value, normalized_tech
            )
        
        return None
    
    def _validate_cell_id(self, value: Any, row_index: int) -> Optional[ValidationResult]:
        """Valida campo Cell ID"""
        if pd.isna(value) or str(value).strip() == '':
            return ValidationResult(
                row_index, 'cell_id', ValidationSeverity.ERROR,
                "Cell ID es requerido", value
            )
        
        cleaned_value = str(value).strip()
        
        if len(cleaned_value) > 50:
            return ValidationResult(
                row_index, 'cell_id', ValidationSeverity.WARNING,
                f"Cell ID muy largo ({len(cleaned_value)} caracteres)", 
                value, cleaned_value[:50]
            )
        
        # Normalizar formato (remover caracteres especiales comunes)
        normalized_cell_id = re.sub(r'[^\w\-]', '', cleaned_value)
        
        if normalized_cell_id != cleaned_value:
            return ValidationResult(
                row_index, 'cell_id', ValidationSeverity.INFO,
                f"Cell ID normalizado: {cleaned_value} -> {normalized_cell_id}", 
                value, normalized_cell_id
            )
        
        return None
    
    def _check_duplicate(self, row: pd.Series, row_index: int) -> Optional[ValidationResult]:
        """Detecta registros duplicados"""
        # Crear hash único basado en campos clave
        hash_components = [
            str(row['mission_id']),
            str(row['punto']),
            str(row['latitude']),
            str(row['longitude']),
            str(row['cell_id']),
            str(row['operator_name'])
        ]
        
        row_hash = hashlib.md5('|'.join(hash_components).encode()).hexdigest()
        
        if row_hash in self.duplicate_hashes:
            return ValidationResult(
                row_index, 'duplicate', ValidationSeverity.WARNING,
                "Posible registro duplicado detectado", row_hash
            )
        
        self.duplicate_hashes.add(row_hash)
        return None
    
    def _add_metadata(self, df: pd.DataFrame, filename: str) -> pd.DataFrame:
        """Agrega metadatos de procesamiento"""
        df = df.copy()
        
        # Agregar información de archivo fuente
        df['file_source'] = filename
        df['processing_timestamp'] = datetime.now()
        
        # Generar hash único para cada registro válido
        for index, row in df.iterrows():
            if row['is_validated']:
                hash_components = [
                    str(row['mission_id']),
                    str(row['punto']),
                    str(row['latitude']),
                    str(row['longitude']),
                    str(row['cell_id']),
                    str(row['operator_name']),
                    str(row['rssi_dbm']),
                    str(row['technology'])
                ]
                df.at[index, 'data_hash'] = hashlib.md5('|'.join(hash_components).encode()).hexdigest()
        
        return df
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Genera resumen de validaciones"""
        summary = {
            'total_validations': len(self.validation_results),
            'by_severity': {},
            'by_field': {},
            'most_common_issues': {}
        }
        
        # Contar por severidad
        for severity in ValidationSeverity:
            count = len([v for v in self.validation_results if v.severity == severity])
            summary['by_severity'][severity.value] = count
        
        # Contar por campo
        field_counts = {}
        for validation in self.validation_results:
            field_counts[validation.field] = field_counts.get(validation.field, 0) + 1
        summary['by_field'] = field_counts
        
        # Problemas más comunes
        message_counts = {}
        for validation in self.validation_results:
            message_counts[validation.message] = message_counts.get(validation.message, 0) + 1
        
        summary['most_common_issues'] = dict(
            sorted(message_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        return summary