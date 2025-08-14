"""
KRONOS - Servicio de Normalización de Datos de Operadores
========================================================

Este módulo se encarga de normalizar los datos de diferentes operadores celulares
a un esquema unificado compatible con la base de datos del sistema KRONOS.

Características principales:
- Transformación de formatos específicos por operador al esquema unificado
- Validación y limpieza de datos durante la normalización
- Cálculo de hashes únicos para detectar duplicados
- Mapeo de campos específicos a campos estándar
- Soporte para datos celulares y de llamadas

Operadores soportados:
- CLARO: Datos por Celda, Llamadas Entrantes/Salientes  
- MOVISTAR: Datos por Celda, Llamadas Salientes
- TIGO: Llamadas Unificadas (entrantes y salientes en un archivo)
- WOM: (En desarrollo)

Autor: Sistema KRONOS
Versión: 1.0.0
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import re
import sys
import os

# Agregar el directorio padre al path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.operator_logger import OperatorLogger


class DataNormalizerService:
    """
    Servicio especializado en normalización de datos de operadores celulares.
    
    Convierte formatos específicos de cada operador al esquema unificado
    de la base de datos, aplicando validaciones y transformaciones necesarias.
    """
    
    def __init__(self):
        """Inicializa el servicio de normalización."""
        self.logger = OperatorLogger()
        
        # Patrones de validación
        self.PHONE_PATTERNS = {
            'colombia': re.compile(r'^(57)?3\d{9}$'),  # Móviles Colombia
            'general': re.compile(r'^\d{10,12}$')      # General 10-12 dígitos
        }
        
        # Mapeo de tecnologías por operador
        self.TECHNOLOGY_MAPPING = {
            'CLARO': {
                'default': 'LTE',  # Tecnología por defecto
                'patterns': {
                    'GSM': ['gsm', '2g'],
                    '3G': ['3g', 'umts', 'wcdma'],
                    'LTE': ['lte', '4g'],
                    '5G': ['5g', 'nr']
                }
            },
            'MOVISTAR': {
                'default': 'LTE',  # Tecnología por defecto
                'type_mapping': {
                    '6': 'LTE',    # MOVISTAR usa números para tecnología
                    '5': '3G',
                    '4': '3G',
                    '3': 'GSM',
                    '2': 'GSM'
                },
                'patterns': {
                    'GSM': ['gsm', '2g'],
                    '3G': ['3g', 'umts', 'wcdma'],
                    'LTE': ['lte', '4g'],
                    '5G': ['5g', 'nr']
                }
            }
        }
        
        # Mapeo de tipos de conexión
        self.CONNECTION_TYPE_MAPPING = {
            'DATOS': 'DATOS',
            'DATA': 'DATOS', 
            'SMS': 'SMS',
            'MMS': 'MMS',
            'VOZ': 'DATOS',  # En datos celulares, VOZ se mapea a DATOS
            'VOICE': 'DATOS'
        }
        
        self.logger.info("DataNormalizerService inicializado")
    
    def _normalize_phone_number(self, phone: str) -> str:
        """
        Normaliza un número telefónico al formato estándar.
        
        Args:
            phone (str): Número telefónico bruto
            
        Returns:
            str: Número normalizado
        """
        if not phone:
            return ''
        
        # Limpiar número (solo dígitos)
        clean_phone = re.sub(r'[^\d]', '', str(phone).strip())
        
        # Si tiene código de país Colombia (57) al inicio, mantenerlo
        if clean_phone.startswith('57') and len(clean_phone) == 12:
            return clean_phone
        
        # Si es número móvil colombiano sin código de país
        if len(clean_phone) == 10 and clean_phone.startswith('3'):
            return '57' + clean_phone
        
        # Retornar como está si no coincide con patrones conocidos
        return clean_phone
    
    def _parse_claro_datetime(self, date_str: str) -> Optional[datetime]:
        """
        Convierte fecha en formato CLARO (YYYYMMDDHHMMSS) a datetime.
        
        Args:
            date_str (str): Fecha en formato YYYYMMDDHHMMSS
            
        Returns:
            Optional[datetime]: Objeto datetime o None si hay error
        """
        if not date_str or len(date_str) != 14:
            return None
        
        try:
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            hour = int(date_str[8:10])
            minute = int(date_str[10:12])
            second = int(date_str[12:14])
            
            return datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
            
        except (ValueError, OverflowError) as e:
            self.logger.warning(f"Error parseando fecha CLARO '{date_str}': {e}")
            return None
    
    def _parse_movistar_datetime(self, date_str: str) -> Optional[datetime]:
        """
        Convierte fecha en formato MOVISTAR a datetime.
        
        Soporta múltiples formatos:
        - YYYYMMDDHHMMSS (formato compacto)
        - YYYY-MM-DD HH:MM:SS (formato estándar)
        - DD/MM/YYYY HH:MM:SS (formato alternativo)
        
        Args:
            date_str (str): Fecha en cualquier formato MOVISTAR
            
        Returns:
            Optional[datetime]: Objeto datetime o None si hay error
        """
        if not date_str:
            return None
        
        # Limpiar la fecha
        clean_date = str(date_str).strip()
        if not clean_date or clean_date.lower() in ['nan', 'null', 'none', '']:
            return None
        
        # Lista de formatos a probar
        date_formats = [
            '%Y-%m-%d %H:%M:%S',        # 2024-10-07 00:00:12
            '%Y%m%d%H%M%S',             # 20241007000012  
            '%d/%m/%Y %H:%M:%S',        # 07/10/2024 00:00:12
            '%Y-%m-%d %H:%M',           # 2024-10-07 00:00
            '%d/%m/%Y %H:%M',           # 07/10/2024 00:00
            '%Y-%m-%d',                 # 2024-10-07
            '%d/%m/%Y',                 # 07/10/2024
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(clean_date, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        
        # Si ningún formato funciona, intentar con pandas que es más flexible
        try:
            import pandas as pd
            parsed_date = pd.to_datetime(clean_date, errors='coerce')
            if not pd.isna(parsed_date):
                return parsed_date.to_pydatetime().replace(tzinfo=timezone.utc)
        except Exception:
            pass
        
        self.logger.warning(f"Error parseando fecha MOVISTAR '{clean_date}': formato no reconocido")
        return None

    def _determine_technology(self, operator: str, raw_data: Dict[str, Any]) -> str:
        """
        Determina la tecnología celular basada en los datos del operador.
        
        Args:
            operator (str): Nombre del operador
            raw_data (Dict[str, Any]): Datos brutos del registro
            
        Returns:
            str: Tecnología identificada
        """
        if operator == 'MOVISTAR':
            # MOVISTAR incluye campo específico tipo_tecnologia
            tipo_tech = str(raw_data.get('tipo_tecnologia', '')).strip()
            if tipo_tech:
                # Mapear número de tecnología MOVISTAR
                tech_mapping = self.TECHNOLOGY_MAPPING.get('MOVISTAR', {}).get('type_mapping', {})
                return tech_mapping.get(tipo_tech, 'LTE')
            
            # Si no hay tipo_tecnologia, usar LTE por defecto para MOVISTAR
            return 'LTE'
        
        elif operator == 'CLARO':
            # Para CLARO, usar LTE por defecto
            return self.TECHNOLOGY_MAPPING.get(operator, {}).get('default', 'LTE')
        
        # Fallback para otros operadores
        return self.TECHNOLOGY_MAPPING.get(operator, {}).get('default', 'UNKNOWN')
    
    def _normalize_connection_type(self, tipo_cdr: str) -> str:
        """
        Normaliza el tipo de conexión/CDR.
        
        Args:
            tipo_cdr (str): Tipo CDR original
            
        Returns:
            str: Tipo de conexión normalizado
        """
        if not tipo_cdr:
            return 'DATOS'
        
        tipo_clean = str(tipo_cdr).strip().upper()
        return self.CONNECTION_TYPE_MAPPING.get(tipo_clean, 'DATOS')
    
    def _calculate_record_hash(self, normalized_data: Dict[str, Any]) -> str:
        """
        Calcula un hash único para el registro normalizado.
        
        Este hash se usa para detectar duplicados exactos en la base de datos.
        
        Args:
            normalized_data (Dict[str, Any]): Datos normalizados
            
        Returns:
            str: Hash SHA256 del registro
        """
        # Crear string único basado en campos clave
        hash_components = [
            str(normalized_data.get('numero_telefono', '')),
            str(normalized_data.get('fecha_hora_inicio', '')),
            str(normalized_data.get('celda_id', '')),
            str(normalized_data.get('operator', '')),
            str(normalized_data.get('tipo_conexion', ''))
        ]
        
        hash_string = '|'.join(hash_components)
        return hashlib.sha256(hash_string.encode('utf-8')).hexdigest()
    
    def _create_operator_specific_data(self, operator: str, raw_data: Dict[str, Any]) -> str:
        """
        Crea un JSON con datos específicos del operador que no se mapean al esquema estándar.
        
        Args:
            operator (str): Nombre del operador
            raw_data (Dict[str, Any]): Datos brutos originales
            
        Returns:
            str: JSON con datos específicos del operador
        """
        specific_data = {
            'operator': operator,
            'original_fields': {}
        }
        
        if operator == 'CLARO':
            # Preservar campos específicos de CLARO que no están en esquema unificado
            claro_fields = {}
            
            # Agregar campos originales para auditoría
            for key, value in raw_data.items():
                if key not in ['numero', 'fecha_trafico', 'tipo_cdr', 'celda_decimal', 'lac_decimal']:
                    claro_fields[key] = str(value) if value is not None else None
            
            if claro_fields:
                specific_data['original_fields'] = claro_fields
            
            # Agregar metadatos específicos de CLARO
            specific_data['claro_metadata'] = {
                'data_type': 'cellular_data',
                'file_format': 'datos_por_celda'
            }
            
        elif operator == 'MOVISTAR':
            # Preservar campos específicos de MOVISTAR que no están en esquema unificado
            movistar_fields = {}
            
            # Campos principales que se mapean al esquema estándar
            cellular_mapped_fields = [
                'numero_que_navega', 'celda', 'trafico_de_subida', 'trafico_de_bajada',
                'fecha_hora_inicio_sesion', 'duracion', 'tipo_tecnologia', 'fecha_hora_fin_sesion'
            ]
            
            call_mapped_fields = [
                'numero_que_contesta', 'numero_que_marca', 'duracion', 'fecha_hora_inicio_llamada',
                'fecha_hora_fin_llamada', 'celda_origen', 'celda_destino'
            ]
            
            # Agregar campos originales para auditoría (excepto los que se mapean)
            for key, value in raw_data.items():
                if key not in cellular_mapped_fields and key not in call_mapped_fields:
                    movistar_fields[key] = str(value) if value is not None else None
            
            if movistar_fields:
                specific_data['original_fields'] = movistar_fields
            
            # Agregar metadatos específicos de MOVISTAR
            specific_data['movistar_metadata'] = {
                'data_type': self._determine_movistar_data_type(raw_data),
                'has_geographic_data': bool(raw_data.get('departamento') or raw_data.get('latitud_n')),
                'technology_code': raw_data.get('tipo_tecnologia', ''),
                'provider': raw_data.get('proveedor', ''),
                'file_format': 'movistar_standard'
            }
        
        return json.dumps(specific_data, ensure_ascii=False, default=str)
    
    def _determine_movistar_data_type(self, raw_data: Dict[str, Any]) -> str:
        """
        Determina el tipo de datos MOVISTAR basado en los campos presentes.
        
        Args:
            raw_data (Dict[str, Any]): Datos brutos del registro
            
        Returns:
            str: Tipo de datos ('cellular_data' o 'call_data')
        """
        # Si tiene campos de tráfico, es datos celulares
        if 'trafico_de_subida' in raw_data or 'trafico_de_bajada' in raw_data:
            return 'cellular_data'
        
        # Si tiene campos de llamadas, es datos de llamadas
        if 'numero_que_contesta' in raw_data and 'numero_que_marca' in raw_data:
            return 'call_data'
        
        # Fallback
        return 'unknown'
    
    def normalize_claro_cellular_data(self, raw_record: Dict[str, Any], 
                                    file_upload_id: str, mission_id: str) -> Optional[Dict[str, Any]]:
        """
        Normaliza un registro de datos celulares de CLARO al esquema unificado.
        
        Args:
            raw_record (Dict[str, Any]): Registro bruto de CLARO
            file_upload_id (str): ID del archivo fuente
            mission_id (str): ID de la misión
            
        Returns:
            Optional[Dict[str, Any]]: Datos normalizados o None si hay error
        """
        try:
            # === VALIDACIÓN DE ENTRADA ===
            required_fields = ['numero', 'fecha_trafico', 'tipo_cdr', 'celda_decimal']
            for field in required_fields:
                if field not in raw_record or not raw_record[field]:
                    self.logger.warning(f"Campo requerido faltante: {field}")
                    return None
            
            # === NORMALIZACIÓN DE CAMPOS PRINCIPALES ===
            
            # Normalizar número telefónico
            numero_normalizado = self._normalize_phone_number(raw_record['numero'])
            if not numero_normalizado:
                self.logger.warning(f"Número telefónico inválido: {raw_record['numero']}")
                return None
            
            # Convertir fecha
            fecha_inicio = self._parse_claro_datetime(str(raw_record['fecha_trafico']))
            if not fecha_inicio:
                self.logger.warning(f"Fecha inválida: {raw_record['fecha_trafico']}")
                return None
            
            # Normalizar celda
            celda_id = str(raw_record['celda_decimal']).strip()
            if not celda_id:
                self.logger.warning("Celda decimal vacía")
                return None
            
            # LAC puede estar vacío
            lac_tac = str(raw_record.get('lac_decimal', '')).strip() if raw_record.get('lac_decimal') else None
            
            # Determinar tecnología
            tecnologia = self._determine_technology('CLARO', raw_record)
            
            # Normalizar tipo de conexión
            tipo_conexion = self._normalize_connection_type(raw_record.get('tipo_cdr'))
            
            # === CREACIÓN DEL REGISTRO NORMALIZADO ===
            
            normalized_record = {
                'file_upload_id': file_upload_id,
                'mission_id': mission_id,
                'operator': 'CLARO',
                'numero_telefono': numero_normalizado,
                'fecha_hora_inicio': fecha_inicio.strftime('%Y-%m-%d %H:%M:%S'),
                'fecha_hora_fin': None,  # CLARO no proporciona hora de fin en datos por celda
                'duracion_segundos': None,  # No disponible en datos por celda
                'celda_id': celda_id,
                'lac_tac': lac_tac,
                
                # Datos de tráfico (CLARO no especifica bytes en datos por celda)
                'trafico_subida_bytes': 0,  # Placeholder
                'trafico_bajada_bytes': 0,  # Placeholder
                
                # Información geográfica (no disponible en formato básico)
                'latitud': None,
                'longitud': None,
                
                # Información técnica
                'tecnologia': tecnologia,
                'tipo_conexion': tipo_conexion,
                'calidad_senal': None,  # No disponible en datos por celda
                
                # Datos específicos del operador
                'operator_specific_data': self._create_operator_specific_data('CLARO', raw_record)
            }
            
            # Calcular hash para detección de duplicados
            normalized_record['record_hash'] = self._calculate_record_hash(normalized_record)
            
            self.logger.debug(
                f"Registro CLARO normalizado: {numero_normalizado} @ {fecha_inicio} en celda {celda_id}"
            )
            
            return normalized_record
            
        except Exception as e:
            self.logger.error(f"Error normalizando registro CLARO: {e}", exc_info=True)
            return None
    
    def _parse_claro_call_datetime(self, date_str: str) -> Optional[datetime]:
        """
        Convierte fecha en formato CLARO llamadas (dd/mm/yyyy hh:mm:ss) a datetime.
        
        Args:
            date_str (str): Fecha en formato dd/mm/yyyy hh:mm:ss
            
        Returns:
            Optional[datetime]: Objeto datetime o None si hay error
        """
        if not date_str:
            return None
        
        date_formats = [
            '%d/%m/%Y %H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%d-%m-%Y %H:%M:%S',
            '%Y/%m/%d %H:%M:%S'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        
        self.logger.warning(f"Error parseando fecha CLARO llamada '{date_str}'")
        return None
    
    def _determine_numero_objetivo(self, originador: str, receptor: str, tipo_llamada: str) -> str:
        """
        Determina cuál es el número objetivo basado en el tipo de llamada.
        
        Para llamadas entrantes, el número objetivo es típicamente el receptor
        (número al que se llama).
        Para llamadas salientes, el número objetivo es el originador
        (número que realiza la llamada).
        
        Args:
            originador (str): Número originador
            receptor (str): Número receptor
            tipo_llamada (str): Tipo de llamada
            
        Returns:
            str: Número objetivo identificado
        """
        if tipo_llamada == 'ENTRANTE':
            # En llamadas entrantes, el objetivo es quien recibe la llamada
            return receptor
        elif tipo_llamada == 'SALIENTE':
            # En llamadas salientes, el objetivo es quien hace la llamada
            return originador
        
        # Por defecto, usar el receptor
        return receptor
    
    def _calculate_call_record_hash(self, normalized_data: Dict[str, Any]) -> str:
        """
        Calcula un hash único para el registro normalizado de llamadas.
        
        Args:
            normalized_data (Dict[str, Any]): Datos normalizados
            
        Returns:
            str: Hash SHA256 del registro
        """
        # Crear string único basado en campos clave
        hash_components = [
            str(normalized_data.get('numero_origen', '')),
            str(normalized_data.get('numero_destino', '')),
            str(normalized_data.get('fecha_hora_llamada', '')),
            str(normalized_data.get('duracion_segundos', '')),
            str(normalized_data.get('operator', '')),
            str(normalized_data.get('tipo_llamada', ''))
        ]
        
        hash_string = '|'.join(hash_components)
        return hashlib.sha256(hash_string.encode('utf-8')).hexdigest()

    def normalize_claro_call_data_entrantes(self, raw_record: Dict[str, Any],
                                          file_upload_id: str, mission_id: str) -> Optional[Dict[str, Any]]:
        """
        Normaliza un registro de llamadas entrantes de CLARO al esquema unificado.
        
        Args:
            raw_record (Dict[str, Any]): Registro bruto de llamada CLARO
            file_upload_id (str): ID del archivo fuente  
            mission_id (str): ID de la misión
            
        Returns:
            Optional[Dict[str, Any]]: Datos normalizados o None si hay error
        """
        try:
            # === VALIDACIÓN DE ENTRADA ===
            required_fields = ['originador', 'receptor', 'fecha_hora', 'tipo']
            for field in required_fields:
                if field not in raw_record or not raw_record[field]:
                    self.logger.warning(f"Campo requerido faltante: {field}")
                    return None
            
            # === NORMALIZACIÓN DE CAMPOS PRINCIPALES ===
            
            # Normalizar números telefónicos
            numero_origen = self._normalize_phone_number(raw_record['originador'])
            if not numero_origen:
                self.logger.warning(f"Número originador inválido: {raw_record['originador']}")
                return None
            
            numero_destino = self._normalize_phone_number(raw_record['receptor'])
            if not numero_destino:
                self.logger.warning(f"Número receptor inválido: {raw_record['receptor']}")
                return None
            
            # Convertir fecha
            fecha_llamada = self._parse_claro_call_datetime(str(raw_record['fecha_hora']))
            if not fecha_llamada:
                self.logger.warning(f"Fecha inválida: {raw_record['fecha_hora']}")
                return None
            
            # Normalizar duración
            duracion_segundos = 0
            try:
                duracion_segundos = max(0, int(raw_record.get('duracion', 0)))
            except (ValueError, TypeError):
                self.logger.warning(f"Duración inválida: {raw_record.get('duracion', 0)}")
                duracion_segundos = 0
            
            # Tipo de llamada
            tipo_llamada = 'ENTRANTE'  # Forzar a ENTRANTE para este tipo de archivo
            
            # Determinar número objetivo (para investigaciones)
            numero_objetivo = self._determine_numero_objetivo(numero_origen, numero_destino, tipo_llamada)
            
            # Normalizar celdas
            celda_origen = str(raw_record.get('celda_inicio_llamada', '')).strip()
            if celda_origen and celda_origen.lower() in ['nan', 'null', 'none', '']:
                celda_origen = None
            
            celda_destino = str(raw_record.get('celda_final_llamada', '')).strip()
            if celda_destino and celda_destino.lower() in ['nan', 'null', 'none', '']:
                celda_destino = None
            
            # Para llamadas entrantes, la celda objetivo es la celda destino
            celda_objetivo = celda_destino
            
            # Determinar tecnología (por defecto LTE para CLARO)
            tecnologia = self._determine_technology('CLARO', raw_record)
            
            # === CREACIÓN DEL REGISTRO NORMALIZADO ===
            
            normalized_record = {
                'file_upload_id': file_upload_id,
                'mission_id': mission_id,
                'operator': 'CLARO',
                'tipo_llamada': tipo_llamada,
                
                # Números involucrados
                'numero_origen': numero_origen,
                'numero_destino': numero_destino,
                'numero_objetivo': numero_objetivo,
                
                # Información temporal
                'fecha_hora_llamada': fecha_llamada.strftime('%Y-%m-%d %H:%M:%S'),
                'duracion_segundos': duracion_segundos,
                
                # Información de celdas
                'celda_origen': celda_origen,
                'celda_destino': celda_destino,
                'celda_objetivo': celda_objetivo,
                
                # Información geográfica (no disponible en archivo básico)
                'latitud_origen': None,
                'longitud_origen': None,
                'latitud_destino': None,
                'longitud_destino': None,
                
                # Información técnica
                'tecnologia': tecnologia,
                'tipo_trafico': 'VOZ',  # Asumimos VOZ por defecto para llamadas
                'estado_llamada': 'COMPLETADA',  # Asumimos completada por defecto
                
                # Datos específicos del operador
                'operator_specific_data': self._create_call_operator_specific_data('CLARO', raw_record)
            }
            
            # Calcular hash para detección de duplicados
            normalized_record['record_hash'] = self._calculate_call_record_hash(normalized_record)
            
            self.logger.debug(
                f"Registro CLARO llamada entrante normalizado: {numero_origen} -> {numero_destino} @ {fecha_llamada}"
            )
            
            return normalized_record
            
        except Exception as e:
            self.logger.error(f"Error normalizando llamada CLARO entrante: {e}", exc_info=True)
            return None
    
    def _create_call_operator_specific_data(self, operator: str, raw_data: Dict[str, Any]) -> str:
        """
        Crea un JSON con datos específicos del operador para llamadas.
        
        Args:
            operator (str): Nombre del operador
            raw_data (Dict[str, Any]): Datos brutos originales
            
        Returns:
            str: JSON con datos específicos del operador
        """
        specific_data = {
            'operator': operator,
            'original_fields': {},
            'data_type': 'call_data'
        }
        
        if operator == 'CLARO':
            # Preservar campos específicos de CLARO que no están en esquema unificado
            claro_fields = {}
            
            # Agregar campos originales para auditoría
            for key, value in raw_data.items():
                if key not in ['originador', 'receptor', 'fecha_hora', 'duracion', 'tipo',
                              'celda_inicio_llamada', 'celda_final_llamada']:
                    claro_fields[key] = str(value) if value is not None else None
            
            if claro_fields:
                specific_data['original_fields'] = claro_fields
            
            # Agregar metadatos específicos de CLARO
            specific_data['claro_metadata'] = {
                'data_type': 'call_data',
                'file_format': 'llamadas_entrantes',
                'cdr_type': raw_data.get('tipo', 'CDR_ENTRANTE')
            }
        
        return json.dumps(specific_data, ensure_ascii=False, default=str)
    
    def normalize_claro_call_data_salientes(self, raw_record: Dict[str, Any],
                                          file_upload_id: str, mission_id: str) -> Optional[Dict[str, Any]]:
        """
        Normaliza un registro de llamadas salientes de CLARO al esquema unificado.
        
        Args:
            raw_record (Dict[str, Any]): Registro bruto de llamada CLARO
            file_upload_id (str): ID del archivo fuente  
            mission_id (str): ID de la misión
            
        Returns:
            Optional[Dict[str, Any]]: Datos normalizados o None si hay error
        """
        try:
            # === VALIDACIÓN DE ENTRADA ===
            required_fields = ['originador', 'receptor', 'fecha_hora', 'tipo']
            for field in required_fields:
                if field not in raw_record or not raw_record[field]:
                    self.logger.warning(f"Campo requerido faltante: {field}")
                    return None
            
            # === NORMALIZACIÓN DE CAMPOS PRINCIPALES ===
            
            # Normalizar números telefónicos
            numero_origen = self._normalize_phone_number(raw_record['originador'])
            if not numero_origen:
                self.logger.warning(f"Número originador inválido: {raw_record['originador']}")
                return None
            
            numero_destino = self._normalize_phone_number(raw_record['receptor'])
            if not numero_destino:
                self.logger.warning(f"Número receptor inválido: {raw_record['receptor']}")
                return None
            
            # Convertir fecha
            fecha_llamada = self._parse_claro_call_datetime(str(raw_record['fecha_hora']))
            if not fecha_llamada:
                self.logger.warning(f"Fecha inválida: {raw_record['fecha_hora']}")
                return None
            
            # Normalizar duración
            duracion_segundos = 0
            try:
                duracion_segundos = max(0, int(raw_record.get('duracion', 0)))
            except (ValueError, TypeError):
                self.logger.warning(f"Duración inválida: {raw_record.get('duracion', 0)}")
                duracion_segundos = 0
            
            # Tipo de llamada
            tipo_llamada = 'SALIENTE'  # Forzar a SALIENTE para este tipo de archivo
            
            # Determinar número objetivo (para investigaciones)
            numero_objetivo = self._determine_numero_objetivo(numero_origen, numero_destino, tipo_llamada)
            
            # Normalizar celdas
            celda_origen = str(raw_record.get('celda_inicio_llamada', '')).strip()
            if celda_origen and celda_origen.lower() in ['nan', 'null', 'none', '']:
                celda_origen = None
            
            celda_destino = str(raw_record.get('celda_final_llamada', '')).strip()
            if celda_destino and celda_destino.lower() in ['nan', 'null', 'none', '']:
                celda_destino = None
            
            # Para llamadas salientes, la celda objetivo es la celda origen
            celda_objetivo = celda_origen
            
            # Determinar tecnología (por defecto LTE para CLARO)
            tecnologia = self._determine_technology('CLARO', raw_record)
            
            # === CREACIÓN DEL REGISTRO NORMALIZADO ===
            
            normalized_record = {
                'file_upload_id': file_upload_id,
                'mission_id': mission_id,
                'operator': 'CLARO',
                'tipo_llamada': tipo_llamada,
                
                # Números involucrados
                'numero_origen': numero_origen,
                'numero_destino': numero_destino,
                'numero_objetivo': numero_objetivo,
                
                # Información temporal
                'fecha_hora_llamada': fecha_llamada.strftime('%Y-%m-%d %H:%M:%S'),
                'duracion_segundos': duracion_segundos,
                
                # Información de celdas
                'celda_origen': celda_origen,
                'celda_destino': celda_destino,
                'celda_objetivo': celda_objetivo,
                
                # Información geográfica (no disponible en archivo básico)
                'latitud_origen': None,
                'longitud_origen': None,
                'latitud_destino': None,
                'longitud_destino': None,
                
                # Información técnica
                'tecnologia': tecnologia,
                'tipo_trafico': 'VOZ',  # Asumimos VOZ por defecto para llamadas
                'estado_llamada': 'COMPLETADA',  # Asumimos completada por defecto
                
                # Datos específicos del operador
                'operator_specific_data': self._create_call_operator_specific_data_salientes('CLARO', raw_record)
            }
            
            # Calcular hash para detección de duplicados
            normalized_record['record_hash'] = self._calculate_call_record_hash(normalized_record)
            
            self.logger.debug(
                f"Registro CLARO llamada saliente normalizado: {numero_origen} -> {numero_destino} @ {fecha_llamada}"
            )
            
            return normalized_record
            
        except Exception as e:
            self.logger.error(f"Error normalizando llamada CLARO saliente: {e}", exc_info=True)
            return None
    
    def _create_call_operator_specific_data_salientes(self, operator: str, raw_data: Dict[str, Any]) -> str:
        """
        Crea un JSON con datos específicos del operador para llamadas salientes.
        
        Args:
            operator (str): Nombre del operador
            raw_data (Dict[str, Any]): Datos brutos originales
            
        Returns:
            str: JSON con datos específicos del operador
        """
        specific_data = {
            'operator': operator,
            'original_fields': {},
            'data_type': 'call_data_salientes'
        }
        
        if operator == 'CLARO':
            # Preservar campos específicos de CLARO que no están en esquema unificado
            claro_fields = {}
            
            # Agregar campos originales para auditoría
            for key, value in raw_data.items():
                if key not in ['originador', 'receptor', 'fecha_hora', 'duracion', 'tipo',
                              'celda_inicio_llamada', 'celda_final_llamada']:
                    claro_fields[key] = str(value) if value is not None else None
            
            if claro_fields:
                specific_data['original_fields'] = claro_fields
            
            # Agregar metadatos específicos de CLARO
            specific_data['claro_metadata'] = {
                'data_type': 'call_data',
                'file_format': 'llamadas_salientes',
                'cdr_type': raw_data.get('tipo', 'CDR_SALIENTE')
            }
        
        return json.dumps(specific_data, ensure_ascii=False, default=str)

    def normalize_claro_call_data(self, raw_record: Dict[str, Any],
                                file_upload_id: str, mission_id: str) -> Optional[Dict[str, Any]]:
        """
        Normaliza un registro de datos de llamadas de CLARO al esquema unificado.
        
        NOTA: Esta es la función genérica. Para llamadas entrantes específicamente,
        usar normalize_claro_call_data_entrantes().
        
        Args:
            raw_record (Dict[str, Any]): Registro bruto de llamada CLARO
            file_upload_id (str): ID del archivo fuente  
            mission_id (str): ID de la misión
            
        Returns:
            Optional[Dict[str, Any]]: Datos normalizados o None si hay error
        """
        try:
            # Detectar tipo de archivo por el campo 'tipo'
            tipo = str(raw_record.get('tipo', '')).upper()
            
            if 'CDR_ENTRANTE' in tipo:
                # Usar normalizador específico para llamadas entrantes
                return self.normalize_claro_call_data_entrantes(raw_record, file_upload_id, mission_id)
            elif 'CDR_SALIENTE' in tipo:
                # Usar normalizador específico para llamadas salientes
                return self.normalize_claro_call_data_salientes(raw_record, file_upload_id, mission_id)
            
            # Tipo de llamada no reconocido
            self.logger.warning(f"Tipo de llamada CLARO no implementado: {tipo}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error normalizando llamada CLARO: {e}", exc_info=True)
            return None
    
    def normalize_movistar_cellular_data(self, raw_record: Dict[str, Any],
                                       file_upload_id: str, mission_id: str) -> Optional[Dict[str, Any]]:
        """
        Normaliza un registro de datos celulares de MOVISTAR al esquema unificado.
        
        Args:
            raw_record (Dict[str, Any]): Registro bruto de MOVISTAR
            file_upload_id (str): ID del archivo fuente
            mission_id (str): ID de la misión
            
        Returns:
            Optional[Dict[str, Any]]: Datos normalizados o None si hay error
        """
        try:
            # === VALIDACIÓN DE ENTRADA ===
            required_fields = ['numero_que_navega', 'celda', 'fecha_hora_inicio_sesion']
            for field in required_fields:
                if field not in raw_record or raw_record[field] is None or str(raw_record[field]).strip() == '':
                    self.logger.warning(f"Campo requerido faltante en MOVISTAR: {field}")
                    return None
            
            # === NORMALIZACIÓN DE CAMPOS PRINCIPALES ===
            
            # Normalizar número telefónico
            numero_normalizado = self._normalize_phone_number(raw_record['numero_que_navega'])
            if not numero_normalizado:
                self.logger.warning(f"Número telefónico inválido MOVISTAR: {raw_record['numero_que_navega']}")
                return None
            
            # Parsear fecha de inicio de sesión
            fecha_inicio_str = str(raw_record['fecha_hora_inicio_sesion']).strip()
            fecha_inicio = self._parse_movistar_datetime(fecha_inicio_str)
            if not fecha_inicio:
                self.logger.warning(f"Fecha inválida MOVISTAR: {fecha_inicio_str}")
                return None
            
            # Normalizar celda
            celda_id = str(raw_record['celda']).strip()
            if not celda_id or celda_id.lower() in ['nan', 'null', 'none', '']:
                self.logger.warning("Celda inválida en MOVISTAR")
                return None
            
            # Determinar tecnología basada en tipo_tecnologia
            tecnologia = self._determine_technology('MOVISTAR', raw_record)
            
            # Normalizar tráfico (convertir a enteros)
            try:
                trafico_subida = int(float(raw_record.get('trafico_de_subida', 0))) if raw_record.get('trafico_de_subida') else 0
                trafico_bajada = int(float(raw_record.get('trafico_de_bajada', 0))) if raw_record.get('trafico_de_bajada') else 0
            except (ValueError, TypeError):
                trafico_subida = 0
                trafico_bajada = 0
                self.logger.debug("Tráfico MOVISTAR convertido a 0 por error de conversión")
            
            # Parsear fecha fin si está disponible
            fecha_fin = None
            if 'fecha_hora_fin_sesion' in raw_record and raw_record['fecha_hora_fin_sesion']:
                fecha_fin_str = str(raw_record['fecha_hora_fin_sesion']).strip()
                fecha_fin_dt = self._parse_movistar_datetime(fecha_fin_str)
                if fecha_fin_dt:
                    fecha_fin = fecha_fin_dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Calcular duración si hay fecha fin
            duracion_segundos = None
            if 'duracion' in raw_record and raw_record['duracion']:
                try:
                    duracion_segundos = int(float(raw_record['duracion']))
                except (ValueError, TypeError):
                    duracion_segundos = None
                    
            # Determinar tipo de conexión
            tipo_conexion = self._normalize_connection_type('DATOS')  # Para datos celulares siempre es DATOS
            
            # === CREACIÓN DEL REGISTRO NORMALIZADO ===
            
            normalized_record = {
                'file_upload_id': file_upload_id,
                'mission_id': mission_id,
                'operator': 'MOVISTAR',
                'numero_telefono': numero_normalizado,
                'fecha_hora_inicio': fecha_inicio.strftime('%Y-%m-%d %H:%M:%S'),
                'fecha_hora_fin': fecha_fin,
                'duracion_segundos': duracion_segundos,
                'celda_id': celda_id,
                'lac_tac': None,  # MOVISTAR no tiene LAC explícito en este formato
                
                # Datos de tráfico
                'trafico_subida_bytes': trafico_subida,
                'trafico_bajada_bytes': trafico_bajada,
                
                # Información geográfica (no disponible en formato básico)
                'latitud': None,
                'longitud': None,
                
                # Información técnica
                'tecnologia': tecnologia,
                'tipo_conexion': tipo_conexion,
                'calidad_senal': None,  # No disponible en datos por celda
                
                # Datos específicos del operador
                'operator_specific_data': self._create_operator_specific_data('MOVISTAR', raw_record)
            }
            
            # Calcular hash para detección de duplicados
            normalized_record['record_hash'] = self._calculate_record_hash(normalized_record)
            
            self.logger.debug(
                f"Registro MOVISTAR normalizado: {numero_normalizado} @ {fecha_inicio} en celda {celda_id}"
            )
            
            return normalized_record
            
        except Exception as e:
            self.logger.error(f"Error normalizando registro MOVISTAR: {e}", exc_info=True)
            return None
    
    def normalize_movistar_call_data_salientes(self, raw_record: Dict[str, Any],
                                             file_upload_id: str, mission_id: str) -> Optional[Dict[str, Any]]:
        """
        Normaliza un registro de llamadas salientes de MOVISTAR al esquema unificado.
        
        Args:
            raw_record (Dict[str, Any]): Registro bruto de llamada MOVISTAR
            file_upload_id (str): ID del archivo fuente
            mission_id (str): ID de la misión
            
        Returns:
            Optional[Dict[str, Any]]: Datos normalizados o None si hay error
        """
        try:
            # === VALIDACIÓN DE ENTRADA ===
            required_fields = ['numero_que_contesta', 'numero_que_marca', 'fecha_hora_inicio_llamada', 'duracion']
            for field in required_fields:
                if field not in raw_record or raw_record[field] is None or str(raw_record[field]).strip() == '':
                    self.logger.warning(f"Campo requerido faltante en llamada MOVISTAR: {field}")
                    return None
            
            # === NORMALIZACIÓN DE CAMPOS PRINCIPALES ===
            
            # Normalizar números telefónicos
            numero_contesta = self._normalize_phone_number(str(raw_record['numero_que_contesta']))
            numero_marca = self._normalize_phone_number(str(raw_record['numero_que_marca']))
            
            if not numero_contesta or not numero_marca:
                self.logger.warning(f"Números telefónicos inválidos MOVISTAR: {numero_contesta}, {numero_marca}")
                return None
            
            # Parsear fecha de inicio de llamada (formato: 20240418140744)
            fecha_inicio_str = str(raw_record['fecha_hora_inicio_llamada']).strip()
            fecha_inicio = self._parse_movistar_datetime(fecha_inicio_str)
            if not fecha_inicio:
                self.logger.warning(f"Fecha inicio inválida MOVISTAR: {fecha_inicio_str}")
                return None
            
            # Parsear fecha de fin si está disponible
            fecha_fin = None
            if 'fecha_hora_fin_llamada' in raw_record and raw_record['fecha_hora_fin_llamada']:
                fecha_fin_str = str(raw_record['fecha_hora_fin_llamada']).strip()
                fecha_fin_dt = self._parse_movistar_datetime(fecha_fin_str)
                if fecha_fin_dt:
                    fecha_fin = fecha_fin_dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Normalizar duración
            try:
                duracion_segundos = int(float(raw_record['duracion'])) if raw_record['duracion'] else 0
            except (ValueError, TypeError):
                duracion_segundos = 0
                self.logger.debug("Duración MOVISTAR convertida a 0 por error de conversión")
            
            # Determinar tecnología
            tecnologia = self._determine_technology('MOVISTAR', raw_record)
            
            # Extraer coordenadas si están disponibles
            latitud_origen = None
            longitud_origen = None
            try:
                if 'latitud_n' in raw_record and raw_record['latitud_n'] is not None:
                    latitud_origen = float(raw_record['latitud_n'])
                if 'longitud_w' in raw_record and raw_record['longitud_w'] is not None:
                    longitud_origen = float(raw_record['longitud_w'])
            except (ValueError, TypeError):
                pass
            
            # Normalizar celdas
            celda_origen = str(raw_record.get('celda_origen', '')).strip() if raw_record.get('celda_origen') else None
            celda_destino = str(raw_record.get('celda_destino', '')).strip() if raw_record.get('celda_destino') else None
            
            # Para llamadas salientes, el número que contesta es el origen y el que marca es el destino
            # (En MOVISTAR: numero_que_contesta = receptor, numero_que_marca = originador de la llamada)
            numero_origen = numero_marca  # El que marca es el originador 
            numero_destino = numero_contesta  # El que contesta es el receptor
            numero_objetivo = numero_destino  # Para análisis, el objetivo es el receptor
            
            # === CREACIÓN DEL REGISTRO NORMALIZADO ===
            
            normalized_record = {
                'file_upload_id': file_upload_id,
                'mission_id': mission_id,
                'operator': 'MOVISTAR',
                'tipo_llamada': 'SALIENTE',
                
                # Números involucrados
                'numero_origen': numero_origen,
                'numero_destino': numero_destino,
                'numero_objetivo': numero_objetivo,
                
                # Información temporal
                'fecha_hora_llamada': fecha_inicio.strftime('%Y-%m-%d %H:%M:%S'),
                'fecha_hora_fin': fecha_fin,
                'duracion_segundos': duracion_segundos,
                
                # Información de celdas
                'celda_origen': celda_origen,
                'celda_destino': celda_destino,
                'celda_objetivo': celda_origen,  # Celda del origen como objetivo
                
                # Información geográfica
                'latitud_origen': latitud_origen,
                'longitud_origen': longitud_origen,
                'latitud_destino': None,  # No disponible en este formato
                'longitud_destino': None,
                
                # Información técnica
                'tecnologia': tecnologia,
                'tipo_trafico': 'VOZ',
                'estado_llamada': 'COMPLETADA',  # Asumir completada si está en el log
                
                # Datos específicos del operador
                'operator_specific_data': self._create_movistar_call_operator_specific_data(raw_record)
            }
            
            # Calcular hash para detección de duplicados
            normalized_record['record_hash'] = self._calculate_call_record_hash(normalized_record)
            
            self.logger.debug(
                f"Registro MOVISTAR llamada saliente normalizado: {numero_origen} -> {numero_destino} @ {fecha_inicio}"
            )
            
            return normalized_record
            
        except Exception as e:
            self.logger.error(f"Error normalizando llamada MOVISTAR saliente: {e}", exc_info=True)
            return None
    
    def _create_movistar_call_operator_specific_data(self, raw_data: Dict[str, Any]) -> str:
        """
        Crea un JSON con datos específicos de MOVISTAR para llamadas.
        
        Args:
            raw_data (Dict[str, Any]): Datos brutos originales
            
        Returns:
            str: JSON con datos específicos del operador
        """
        specific_data = {
            'operator': 'MOVISTAR',
            'data_type': 'call_data_salientes',
            'original_fields': {}
        }
        
        # Preservar campos específicos de MOVISTAR que no están en esquema unificado
        movistar_fields = {}
        
        # Campos principales que se mapean al esquema estándar  
        mapped_fields = [
            'numero_que_contesta', 'numero_que_marca', 'fecha_hora_inicio_llamada', 
            'fecha_hora_fin_llamada', 'duracion', 'celda_origen', 'celda_destino',
            'latitud_n', 'longitud_w', 'tecnologia'
        ]
        
        # Agregar campos originales para auditoría (excepto los que se mapean)
        for key, value in raw_data.items():
            if key not in mapped_fields:
                movistar_fields[key] = str(value) if value is not None else None
        
        if movistar_fields:
            specific_data['original_fields'] = movistar_fields
        
        # Agregar metadatos específicos de MOVISTAR
        specific_data['movistar_metadata'] = {
            'data_type': 'call_data_salientes',
            'has_geographic_data': bool(raw_data.get('departamento') or raw_data.get('latitud_n')),
            'has_network_info': bool(raw_data.get('switch') or raw_data.get('proveedor')),
            'provider': raw_data.get('proveedor', ''),
            'switch': raw_data.get('switch', ''),
            'file_format': 'vozm_saliente_standard',
            'location_info': {
                'departamento': raw_data.get('departamento', ''),
                'localidad': raw_data.get('localidad', ''),
                'region': raw_data.get('region', ''),
                'direccion': raw_data.get('direccion', ''),
                'descripcion': raw_data.get('descripcion', '')
            },
            'network_info': {
                'ruta_entrante': raw_data.get('ruta_entrante', ''),
                'ruta_saliente': raw_data.get('ruta_saliente', ''),
                'azimut': raw_data.get('azimut', ''),
                'serial_origen': raw_data.get('serial_origen', ''),
                'serial_destino': raw_data.get('serial_destino', ''),
                'transferencia': raw_data.get('transferencia', '')
            }
        }
        
        return json.dumps(specific_data, ensure_ascii=False, default=str)
    
    def normalize_tigo_cellular_data(self, raw_record: Dict[str, Any],
                                   file_upload_id: str, mission_id: str) -> Optional[Dict[str, Any]]:
        """
        Normaliza un registro de datos celulares de TIGO al esquema unificado.
        
        NOTA: TIGO no maneja datos celulares por separado - todo está en las llamadas unificadas.
        Este método se mantiene por compatibilidad pero no debería usarse.
        
        Args:
            raw_record (Dict[str, Any]): Registro bruto de TIGO
            file_upload_id (str): ID del archivo fuente
            mission_id (str): ID de la misión
            
        Returns:
            Optional[Dict[str, Any]]: Datos normalizados o None si hay error
        """
        try:
            self.logger.warning("TIGO no maneja datos celulares separados - usar normalize_tigo_call_data_unificadas")
            return None
            
        except Exception as e:
            self.logger.error(f"Error normalizando registro TIGO: {e}", exc_info=True)
            return None

    def normalize_tigo_call_data_unificadas(self, raw_record: Dict[str, Any],
                                          file_upload_id: str, mission_id: str, 
                                          call_direction: str) -> Optional[Dict[str, Any]]:
        """
        Normaliza un registro de llamadas unificadas TIGO al esquema unificado.
        
        TIGO reporta llamadas entrantes y salientes en un solo archivo, diferenciadas
        por el campo 'direccion': 'O' = SALIENTE, 'I' = ENTRANTE
        
        Args:
            raw_record (Dict[str, Any]): Registro bruto de TIGO
            file_upload_id (str): ID del archivo fuente
            mission_id (str): ID de la misión
            call_direction (str): 'ENTRANTE' o 'SALIENTE' (ya determinado por el procesador)
            
        Returns:
            Optional[Dict[str, Any]]: Datos normalizados o None si hay error
        """
        try:
            from utils.validators import validate_tigo_llamada_record
            import uuid
            import json
            import hashlib
            from datetime import datetime
            
            # Validar registro usando validadores específicos TIGO
            validated_record = validate_tigo_llamada_record(raw_record)
            
            # Generar ID único para el registro
            record_id = str(uuid.uuid4())
            
            # Determinar números origen/destino/objetivo según la dirección
            if call_direction == 'SALIENTE':
                # Para llamadas salientes: numero_a es quien llama (origen)
                numero_origen = validated_record['numero_a']
                numero_destino_raw = validated_record.get('numero_marcado', validated_record['numero_a'])
                
                # TIGO: Convertir destinos no telefónicos a formato válido para BD
                numero_destino = self._normalize_tigo_destination(numero_destino_raw)
                numero_objetivo = numero_destino  # El objetivo es quien recibe
                
            elif call_direction == 'ENTRANTE':
                # Para llamadas entrantes: numero_a es quien recibe (destino)
                numero_origen_raw = validated_record.get('numero_marcado', validated_record['numero_a'])
                numero_origen = self._normalize_tigo_destination(numero_origen_raw)
                numero_destino = validated_record['numero_a']
                numero_objetivo = validated_record['numero_a']  # El objetivo es quien recibe
                
            else:
                self.logger.warning(f"Dirección de llamada TIGO no reconocida: {call_direction}")
                return None
            
            # Construir datos específicos del operador
            operator_specific_data = {
                'operator': 'TIGO',
                'data_type': 'llamadas_unificadas',
                'direccion_original': validated_record.get('direccion', ''),
                'tipo_llamada_original': validated_record.get('tipo_de_llamada', ''),
                'codec': validated_record.get('trcsextracodec', ''),
                'tecnologia': validated_record.get('tecnologia', ''),
                'ubicacion': {
                    'ciudad': validated_record.get('ciudad', ''),
                    'departamento': validated_record.get('departamento', ''),
                    'direccion_fisica': validated_record.get('direccion_fisica', ''),
                    'coordenadas': {
                        'latitud': validated_record.get('latitud'),
                        'longitud': validated_record.get('longitud')
                    }
                },
                'antena_info': {
                    'azimuth': validated_record.get('azimuth'),
                    'altura_metros': validated_record.get('altura'),
                    'potencia_dbm': validated_record.get('potencia'),
                    'tipo_cobertura': validated_record.get('tipo_cobertura', ''),
                    'tipo_estructura': validated_record.get('tipo_estructura', ''),
                    'cellid_nval': validated_record.get('cellid_nval', '')
                },
                'raw_fields': {
                    key: value for key, value in raw_record.items() 
                    if key not in ['numero_a', 'numero_marcado', 'fecha_hora_origen', 'duracion_total_seg']
                }
            }
            
            # Construir datos normalizados
            normalized_data = {
                'file_upload_id': file_upload_id,
                'mission_id': mission_id,
                'tipo_llamada': call_direction,
                'numero_origen': numero_origen,
                'numero_destino': numero_destino,
                'numero_objetivo': numero_objetivo,
                'fecha_hora_llamada': validated_record['fecha_hora_origen'].isoformat(),
                'duracion_segundos': validated_record.get('duracion_total_seg', 0),
                'celda_origen': validated_record.get('celda_origen_truncada', ''),
                'celda_destino': None,  # TIGO no reporta celda destino explícitamente
                'celda_objetivo': validated_record.get('celda_origen_truncada', ''),  # Usar celda origen como objetivo
                'latitud_origen': validated_record.get('latitud'),
                'longitud_origen': validated_record.get('longitud'),
                'latitud_destino': None,  # TIGO no reporta coordenadas destino
                'longitud_destino': None,
                'tecnologia': validated_record.get('tecnologia', ''),
                'tipo_trafico': 'VOZ',  # TIGO reporta principalmente voz
                'estado_llamada': 'COMPLETADA',  # Asumir completada si está en el reporte
                'operator_specific_data': self._create_tigo_operator_specific_data(
                    operator_specific_data, validated_record, 
                    numero_destino_raw if call_direction == 'SALIENTE' else numero_origen_raw
                ),
                'record_hash': None  # Se calculará más abajo
            }
            
            # Calcular hash del registro para deduplicación (mejorado para TIGO)
            # Incluir más campos únicos para evitar colisiones
            hash_data = f"{normalized_data['numero_origen']}-{normalized_data['numero_destino']}-{normalized_data['fecha_hora_llamada']}-{normalized_data['duracion_segundos']}-{validated_record.get('celda_origen_truncada', '')}-{validated_record.get('tipo_de_llamada', '')}-{file_upload_id}-{record_id[:8]}"
            normalized_data['record_hash'] = hashlib.sha256(hash_data.encode('utf-8')).hexdigest()[:32]
            
            self.logger.debug(
                f"Registro TIGO {call_direction} normalizado: {numero_origen} -> {numero_destino}",
                extra={'record_id': record_id, 'hash': normalized_data['record_hash']}
            )
            
            return normalized_data
            
        except Exception as e:
            self.logger.error(f"Error normalizando registro llamada TIGO {call_direction}: {e}")
            return None
    
    def _normalize_tigo_destination(self, destination: str) -> str:
        """
        Normaliza destinos TIGO para compatibilidad con constraints de BD.
        
        TIGO incluye destinos no telefónicos como:
        - internet.movistar.com.co (dominios web)
        - ims (servicios de red)
        - inetd.vodafone.iot (servicios IoT)
        
        Esta función convierte estos destinos a números telefónicos válidos
        mientras preserva la información original en operator_specific_data.
        
        Args:
            destination (str): Destino original de TIGO
            
        Returns:
            str: Número telefónico válido para BD
        """
        if not destination:
            return '0000000000'  # Número por defecto
        
        destination_clean = str(destination).strip()
        
        # Si ya es un número válido, devolverlo tal como está
        if destination_clean.isdigit() and len(destination_clean) >= 7:
            return destination_clean
        
        # Mapeo de servicios/dominios comunes a números identificadores
        service_mapping = {
            # Servicios de red
            'ims': '9999999001',
            'internet': '9999999002',
            'sip': '9999999003',
            'voip': '9999999004',
            'inetd': '9999999005',
            
            # Dominios web comunes
            'internet.movistar.com.co': '9999999010',
            'web.colombiamovil.com.co': '9999999011',
            'inetd.vodafone.iot': '9999999012',
            'portal.tigo.com.co': '9999999013',
            'data.claro.com.co': '9999999014',
            'web.5g.attmex.mx': '9999999015',          # AT&T México
            'internet.cnt.net.ec': '9999999016',       # CNT Ecuador
            'internet.mvno126.com': '9999999017',      # MVNO genérico
        }
        
        # Buscar mapeo exacto
        if destination_clean.lower() in service_mapping:
            return service_mapping[destination_clean.lower()]
        
        # Buscar mapeo por palabras clave
        destination_lower = destination_clean.lower()
        
        if 'internet' in destination_lower or 'web' in destination_lower:
            return '9999999020'  # Servicios web genéricos
        elif 'movistar' in destination_lower:
            return '9999999021'  # Servicios Movistar
        elif 'claro' in destination_lower:
            return '9999999022'  # Servicios Claro
        elif 'tigo' in destination_lower:
            return '9999999023'  # Servicios Tigo
        elif 'vodafone' in destination_lower:
            return '9999999024'  # Servicios Vodafone
        elif '.com' in destination_lower or '.net' in destination_lower or '.org' in destination_lower:
            return '9999999025'  # Dominios web genéricos
        elif 'iot' in destination_lower:
            return '9999999026'  # Servicios IoT
        else:
            # Para cualquier otro servicio, generar número basado en hash
            import hashlib
            hash_val = hashlib.md5(destination_clean.encode()).hexdigest()
            # Usar primeros 6 dígitos del hash + prefijo 9999
            return '9999' + hash_val[:6]
    
    def _create_tigo_operator_specific_data(self, base_data: Dict[str, Any], 
                                          validated_record: Dict[str, Any], 
                                          original_destination: str) -> str:
        """
        Crea datos específicos del operador TIGO incluyendo destinos originales.
        
        Args:
            base_data: Datos base del operador
            validated_record: Registro validado
            original_destination: Destino original antes de normalización
            
        Returns:
            str: JSON con datos específicos completos
        """
        import pandas as pd
        import numpy as np
        
        def clean_value(value):
            """Limpia valores que pueden causar problemas en JSON"""
            if pd.isna(value) or value is None or value is np.nan:
                return None
            if isinstance(value, (np.integer, np.floating)):
                if np.isnan(value) or np.isinf(value):
                    return None
                return float(value) if isinstance(value, np.floating) else int(value)
            return str(value) if value is not None else None
        
        # Limpiar datos base recursivamente
        def clean_dict(data):
            if isinstance(data, dict):
                return {k: clean_dict(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [clean_dict(item) for item in data]
            else:
                return clean_value(data)
        
        # Combinar datos base con información de destinos originales
        enhanced_data = clean_dict(base_data.copy())
        enhanced_data['original_destination'] = clean_value(original_destination)
        enhanced_data['destination_normalized'] = self._normalize_tigo_destination(str(original_destination) if original_destination else "")
        enhanced_data['is_service_call'] = not str(original_destination or "").isdigit()
        
        try:
            # Validar que el JSON se puede serializar correctamente
            json_str = json.dumps(enhanced_data, ensure_ascii=False)
            # Validar que se puede deserializar
            json.loads(json_str)
            return json_str
        except (TypeError, ValueError) as e:
            self.logger.warning(f"Error serializando JSON TIGO, usando fallback: {e}")
            # Fallback con datos mínimos
            fallback_data = {
                "operator": "TIGO",
                "data_type": "llamadas_unificadas",
                "processing_error": "JSON serialization failed",
                "error_details": str(e),
                "original_destination": str(original_destination) if original_destination else None
            }
            return json.dumps(fallback_data, ensure_ascii=False)
    
    def normalize_wom_cellular_data(self, raw_record: Dict[str, Any],
                                  file_upload_id: str, mission_id: str) -> Optional[Dict[str, Any]]:
        """
        Normaliza un registro de datos celulares de WOM al esquema unificado.
        
        Args:
            raw_record (Dict[str, Any]): Registro bruto de WOM
            file_upload_id (str): ID del archivo fuente
            mission_id (str): ID de la misión
            
        Returns:
            Optional[Dict[str, Any]]: Datos normalizados o None si hay error
        """
        try:
            # TODO: Implementar cuando tengamos especificaciones de WOM
            self.logger.warning("Normalización de datos WOM no implementada aún")
            return None
            
        except Exception as e:
            self.logger.error(f"Error normalizando registro WOM: {e}", exc_info=True)
            return None


# ==============================================================================
# FUNCIONES DE UTILIDAD Y VALIDACIÓN
# ==============================================================================

def validate_normalized_data(normalized_data: Dict[str, Any]) -> List[str]:
    """
    Valida que los datos normalizados cumplan con el esquema de la base de datos.
    
    Args:
        normalized_data (Dict[str, Any]): Datos normalizados a validar
        
    Returns:
        List[str]: Lista de errores encontrados (vacía si es válido)
    """
    errors = []
    
    # Validar campos requeridos
    required_fields = [
        'file_upload_id', 'mission_id', 'operator', 'numero_telefono',
        'fecha_hora_inicio', 'celda_id', 'record_hash'
    ]
    
    for field in required_fields:
        if field not in normalized_data or not normalized_data[field]:
            errors.append(f"Campo requerido faltante o vacío: {field}")
    
    # Validar tipos de datos
    if 'trafico_subida_bytes' in normalized_data:
        try:
            int(normalized_data['trafico_subida_bytes'] or 0)
        except (ValueError, TypeError):
            errors.append("trafico_subida_bytes debe ser numérico")
    
    if 'trafico_bajada_bytes' in normalized_data:
        try:
            int(normalized_data['trafico_bajada_bytes'] or 0)
        except (ValueError, TypeError):
            errors.append("trafico_bajada_bytes debe ser numérico")
    
    # Validar coordenadas geográficas
    if normalized_data.get('latitud') is not None:
        try:
            lat = float(normalized_data['latitud'])
            if not (-90.0 <= lat <= 90.0):
                errors.append(f"Latitud fuera de rango válido: {lat}")
        except (ValueError, TypeError):
            errors.append("Latitud debe ser numérica")
    
    if normalized_data.get('longitud') is not None:
        try:
            lon = float(normalized_data['longitud'])
            if not (-180.0 <= lon <= 180.0):
                errors.append(f"Longitud fuera de rango válido: {lon}")
        except (ValueError, TypeError):
            errors.append("Longitud debe ser numérica")
    
    # Validar formato de fecha
    if normalized_data.get('fecha_hora_inicio'):
        try:
            datetime.strptime(normalized_data['fecha_hora_inicio'], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            errors.append("Formato de fecha_hora_inicio inválido")
    
    # Validar operador
    valid_operators = ['CLARO', 'MOVISTAR', 'TIGO', 'WOM']
    if normalized_data.get('operator') not in valid_operators:
        errors.append(f"Operador inválido: {normalized_data.get('operator')}")
    
    # Validar JSON de datos específicos
    if normalized_data.get('operator_specific_data'):
        try:
            json.loads(normalized_data['operator_specific_data'])
        except json.JSONDecodeError:
            errors.append("operator_specific_data no es JSON válido")
    
    return errors



def test_claro_normalization() -> None:
    """
    Función de testing para normalización de datos CLARO.
    No expuesta via Eel, solo para desarrollo/debugging.
    """
    service = DataNormalizerService()
    
    # Datos de prueba CLARO
    test_record = {
        'numero': '573123456789',
        'fecha_trafico': '20240419080000',
        'tipo_cdr': 'DATOS',
        'celda_decimal': '175462',
        'lac_decimal': '20010'
    }
    
    print("Datos de prueba CLARO:")
    print(json.dumps(test_record, indent=2))
    
    normalized = service.normalize_claro_cellular_data(
        test_record, 'test-file-id', 'test-mission-id'
    )
    
    if normalized:
        print("\nDatos normalizados:")
        print(json.dumps(normalized, indent=2, default=str))
        
        # Validar datos normalizados
        errors = validate_normalized_data(normalized)
        if errors:
            print(f"\nErrores de validación: {errors}")
        else:
            print("\n✓ Datos normalizados válidos")
    else:
        print("\n❌ Error en normalización")

    # ==============================================================================
    # MÉTODOS ESPECÍFICOS PARA OPERADOR WOM
    # ==============================================================================
    
    def normalize_wom_cellular_data(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Normaliza datos celulares de WOM al esquema unificado.
        
        WOM maneja datos celulares con información técnica avanzada:
        - IMSI, IMEI para identificación de dispositivos
        - BTS_ID, TAC para información de infraestructura
        - Coordenadas con formato de comas decimales
        - Tecnología específica: WOM 3G, WOM 4G
        
        Args:
            df (pd.DataFrame): DataFrame con registros WOM
            
        Returns:
            Optional[pd.DataFrame]: DataFrame normalizado o None si hay error
        """
        try:
            self.logger.info(f"Iniciando normalización de {len(df)} registros WOM datos celulares")
            
            # Crear copia para evitar modificar original
            df_normalized = df.copy()
            
            # === MAPEO DE CAMPOS WOM A ESQUEMA UNIFICADO ===
            
            field_mapping = {
                'OPERADOR_TECNOLOGIA': 'operador_tecnologia',
                'BTS_ID': 'bts_id',
                'TAC': 'tac',
                'CELL_ID_VOZ': 'cell_id_voz',
                'SECTOR': 'sector',
                'FECHA_HORA_INICIO': 'fecha_hora_inicio',
                'FECHA_HORA_FIN': 'fecha_hora_fin',
                'OPERADOR_RAN': 'operador_ran',
                'NUMERO_ORIGEN': 'numero_origen',
                'DURACION_SEG': 'duracion_seg',
                'UP_DATA_BYTES': 'up_data_bytes',
                'DOWN_DATA_BYTES': 'down_data_bytes',
                'IMSI': 'imsi',
                'LOCALIZACION_USUARIO': 'localizacion_usuario',
                'NOMBRE_ANTENA': 'nombre_antena',
                'DIRECCION': 'direccion',
                'LATITUD': 'latitud',
                'LONGITUD': 'longitud',
                'LOCALIDAD': 'localidad',
                'CIUDAD': 'ciudad',
                'DEPARTAMENTO': 'departamento',
                'REGIONAL': 'regional',
                'ENTORNO_GEOGRAFICO': 'entorno_geografico',
                'ULI': 'uli'
            }
            
            # Renombrar columnas
            df_normalized = df_normalized.rename(columns=field_mapping)
            
            # === LIMPIEZA Y CONVERSIÓN DE DATOS ===
            
            # Limpiar números de teléfono
            if 'numero_origen' in df_normalized.columns:
                df_normalized['numero_origen'] = (df_normalized['numero_origen']
                                                 .astype(str)
                                                 .str.replace(r'[^\d]', '', regex=True)
                                                 .str.strip())
            
            # Procesar fechas formato WOM (dd/mm/yyyy HH:MM)
            for date_col in ['fecha_hora_inicio', 'fecha_hora_fin']:
                if date_col in df_normalized.columns:
                    df_normalized[date_col] = self._parse_wom_datetime(df_normalized[date_col])
            
            # Convertir coordenadas (formato con comas a puntos decimales)
            for coord_col in ['latitud', 'longitud']:
                if coord_col in df_normalized.columns:
                    df_normalized[coord_col] = (df_normalized[coord_col]
                                              .astype(str)
                                              .str.replace(',', '.')
                                              .str.strip('"\'')
                                              .replace(['', 'nan', 'None'], None))
                    df_normalized[coord_col] = pd.to_numeric(df_normalized[coord_col], errors='coerce')
            
            # Convertir campos numéricos
            numeric_fields = ['duracion_seg', 'up_data_bytes', 'down_data_bytes', 'bts_id', 'tac', 'cell_id_voz', 'sector']
            for field in numeric_fields:
                if field in df_normalized.columns:
                    df_normalized[field] = pd.to_numeric(df_normalized[field], errors='coerce').fillna(0)
            
            # Limpiar campos de texto
            text_fields = ['operador_tecnologia', 'operador_ran', 'nombre_antena', 'direccion', 
                          'localidad', 'ciudad', 'departamento', 'regional', 'entorno_geografico']
            for field in text_fields:
                if field in df_normalized.columns:
                    df_normalized[field] = (df_normalized[field]
                                          .astype(str)
                                          .str.strip()
                                          .replace(['nan', 'None', ''], None))
            
            # Limpiar campos técnicos específicos WOM
            technical_fields = ['imsi', 'localizacion_usuario', 'uli']
            for field in technical_fields:
                if field in df_normalized.columns:
                    df_normalized[field] = (df_normalized[field]
                                          .astype(str)
                                          .str.strip()
                                          .replace(['nan', 'None', ''], None))
            
            self.logger.info(f"Normalización WOM datos celulares completada: {len(df_normalized)} registros")
            
            return df_normalized
            
        except Exception as e:
            self.logger.error(f"Error normalizando datos celulares WOM: {e}", exc_info=True)
            return None

    def normalize_wom_call_data_entrantes(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Normaliza datos de llamadas de WOM al esquema unificado.
        
        WOM maneja llamadas entrantes y salientes en un solo archivo diferenciadas
        por el campo SENTIDO:
        - 'ENTRANTE' = llamada entrante
        - 'SALIENTE' = llamada saliente
        
        Args:
            df (pd.DataFrame): DataFrame con registros WOM
            
        Returns:
            Optional[pd.DataFrame]: DataFrame normalizado o None si hay error
        """
        try:
            self.logger.info(f"Iniciando normalización de {len(df)} registros WOM llamadas")
            
            # Crear copia para evitar modificar original
            df_normalized = df.copy()
            
            # === MAPEO DE CAMPOS WOM A ESQUEMA UNIFICADO ===
            
            field_mapping = {
                'OPERADOR_TECNOLOGIA': 'operador_tecnologia',
                'BTS_ID': 'bts_id',
                'TAC': 'tac',
                'CELL_ID_VOZ': 'cell_id_voz',
                'SECTOR': 'sector',
                'NUMERO_ORIGEN': 'numero_origen',
                'NUMERO_DESTINO': 'numero_destino',
                'FECHA_HORA_INICIO': 'fecha_hora_inicio',
                'FECHA_HORA_FIN': 'fecha_hora_fin',
                'DURACION_SEG': 'duracion_seg',
                'OPERADOR_RAN_ORIGEN': 'operador_ran_origen',
                'USER_LOCATION_INFO': 'user_location_info',
                'ACCESS_NETWORK_INFORMATION': 'access_network_information',
                'IMEI': 'imei',
                'IMSI': 'imsi',
                'NOMBRE_ANTENA': 'nombre_antena',
                'DIRECCION': 'direccion',
                'LATITUD': 'latitud',
                'LONGITUD': 'longitud',
                'LOCALIDAD': 'localidad',
                'CIUDAD': 'ciudad',
                'DEPARTAMENTO': 'departamento',
                'SENTIDO': 'sentido'
            }
            
            # Renombrar columnas
            df_normalized = df_normalized.rename(columns=field_mapping)
            
            # === LIMPIEZA Y CONVERSIÓN DE DATOS ===
            
            # Limpiar números de teléfono
            for num_col in ['numero_origen', 'numero_destino']:
                if num_col in df_normalized.columns:
                    df_normalized[num_col] = (df_normalized[num_col]
                                            .astype(str)
                                            .str.replace(r'[^\d]', '', regex=True)
                                            .str.strip())
            
            # Procesar fechas formato WOM (dd/mm/yyyy HH:MM)
            for date_col in ['fecha_hora_inicio', 'fecha_hora_fin']:
                if date_col in df_normalized.columns:
                    df_normalized[date_col] = self._parse_wom_datetime(df_normalized[date_col])
            
            # Convertir coordenadas (formato con comas a puntos decimales)
            for coord_col in ['latitud', 'longitud']:
                if coord_col in df_normalized.columns:
                    df_normalized[coord_col] = (df_normalized[coord_col]
                                              .astype(str)
                                              .str.replace(',', '.')
                                              .str.strip('"\'')
                                              .replace(['', 'nan', 'None'], None))
                    df_normalized[coord_col] = pd.to_numeric(df_normalized[coord_col], errors='coerce')
            
            # Convertir campos numéricos
            numeric_fields = ['duracion_seg', 'bts_id', 'tac', 'cell_id_voz', 'sector']
            for field in numeric_fields:
                if field in df_normalized.columns:
                    df_normalized[field] = pd.to_numeric(df_normalized[field], errors='coerce').fillna(0)
            
            # Normalizar campo SENTIDO
            if 'sentido' in df_normalized.columns:
                df_normalized['sentido'] = (df_normalized['sentido']
                                          .astype(str)
                                          .str.upper()
                                          .str.strip())
            
            # Limpiar campos de texto
            text_fields = ['operador_tecnologia', 'operador_ran_origen', 'nombre_antena', 'direccion',
                          'localidad', 'ciudad', 'departamento']
            for field in text_fields:
                if field in df_normalized.columns:
                    df_normalized[field] = (df_normalized[field]
                                          .astype(str)
                                          .str.strip()
                                          .replace(['nan', 'None', ''], None))
            
            # Limpiar campos técnicos específicos WOM
            technical_fields = ['imei', 'imsi', 'user_location_info', 'access_network_information']
            for field in technical_fields:
                if field in df_normalized.columns:
                    df_normalized[field] = (df_normalized[field]
                                          .astype(str)
                                          .str.strip()
                                          .replace(['nan', 'None', ''], None))
            
            self.logger.info(f"Normalización WOM llamadas completada: {len(df_normalized)} registros")
            
            return df_normalized
            
        except Exception as e:
            self.logger.error(f"Error normalizando datos de llamadas WOM: {e}", exc_info=True)
            return None

    def normalize_wom_cellular_data_record(self, raw_record: Dict[str, Any],
                                          file_upload_id: str, mission_id: str) -> Optional[Dict[str, Any]]:
        """
        Normaliza un registro individual de datos celulares WOM al esquema unificado.
        
        Args:
            raw_record (Dict[str, Any]): Registro bruto de WOM
            file_upload_id (str): ID del archivo fuente
            mission_id (str): ID de la misión
            
        Returns:
            Optional[Dict[str, Any]]: Datos normalizados o None si hay error
        """
        try:
            from utils.validators import validate_wom_cellular_record
            import uuid
            from datetime import datetime
            
            # Validar registro usando validadores específicos WOM
            validated_record = validate_wom_cellular_record(raw_record)
            
            # Generar ID único para el registro
            record_id = str(uuid.uuid4())
            
            # Construir datos normalizados
            normalized_data = {
                'id': record_id,
                'mission_id': mission_id,
                'file_upload_id': file_upload_id,
                'operator_technology': validated_record.get('operador_tecnologia', ''),
                'bts_id': validated_record.get('bts_id', 0),
                'tac': validated_record.get('tac', 0),
                'cell_id_voz': validated_record.get('cell_id_voz', 0),
                'sector': validated_record.get('sector', 0),
                'fecha_hora_inicio': validated_record.get('fecha_hora_inicio'),
                'fecha_hora_fin': validated_record.get('fecha_hora_fin'),
                'operador_ran': validated_record.get('operador_ran', ''),
                'numero_origen': validated_record.get('numero_origen', ''),
                'duracion_seg': validated_record.get('duracion_seg', 0),
                'up_data_bytes': validated_record.get('up_data_bytes', 0),
                'down_data_bytes': validated_record.get('down_data_bytes', 0),
                'imsi': validated_record.get('imsi', ''),
                'localizacion_usuario': validated_record.get('localizacion_usuario', ''),
                'nombre_antena': validated_record.get('nombre_antena', ''),
                'direccion': validated_record.get('direccion', ''),
                'latitud': validated_record.get('latitud'),
                'longitud': validated_record.get('longitud'),
                'localidad': validated_record.get('localidad', ''),
                'ciudad': validated_record.get('ciudad', ''),
                'departamento': validated_record.get('departamento', ''),
                'regional': validated_record.get('regional', ''),
                'entorno_geografico': validated_record.get('entorno_geografico', ''),
                'uli': validated_record.get('uli', ''),
                'created_at': datetime.now().isoformat()
            }
            
            return normalized_data
            
        except Exception as e:
            self.logger.error(f"Error normalizando registro WOM cellular: {e}", exc_info=True)
            return None

    def normalize_wom_call_data_record(self, raw_record: Dict[str, Any],
                                      file_upload_id: str, mission_id: str,
                                      call_direction: str) -> Optional[Dict[str, Any]]:
        """
        Normaliza un registro individual de llamadas WOM al esquema unificado.
        
        Args:
            raw_record (Dict[str, Any]): Registro bruto de WOM
            file_upload_id (str): ID del archivo fuente
            mission_id (str): ID de la misión
            call_direction (str): 'ENTRANTE' o 'SALIENTE'
            
        Returns:
            Optional[Dict[str, Any]]: Datos normalizados o None si hay error
        """
        try:
            from utils.validators import validate_wom_call_record
            import uuid
            from datetime import datetime
            
            # Validar registro usando validadores específicos WOM
            validated_record = validate_wom_call_record(raw_record)
            
            # Generar ID único para el registro
            record_id = str(uuid.uuid4())
            
            # Construir datos normalizados
            normalized_data = {
                'id': record_id,
                'mission_id': mission_id,
                'file_upload_id': file_upload_id,
                'operator_technology': validated_record.get('operador_tecnologia', ''),
                'bts_id': validated_record.get('bts_id', 0),
                'tac': validated_record.get('tac', 0),
                'cell_id_voz': validated_record.get('cell_id_voz', 0),
                'sector': validated_record.get('sector', 0),
                'numero_origen': validated_record.get('numero_origen', ''),
                'numero_destino': validated_record.get('numero_destino', ''),
                'fecha_hora_inicio': validated_record.get('fecha_hora_inicio'),
                'fecha_hora_fin': validated_record.get('fecha_hora_fin'),
                'duracion_seg': validated_record.get('duracion_seg', 0),
                'operador_ran_origen': validated_record.get('operador_ran_origen', ''),
                'user_location_info': validated_record.get('user_location_info', ''),
                'access_network_information': validated_record.get('access_network_information', ''),
                'imei': validated_record.get('imei', ''),
                'imsi': validated_record.get('imsi', ''),
                'nombre_antena': validated_record.get('nombre_antena', ''),
                'direccion': validated_record.get('direccion', ''),
                'latitud': validated_record.get('latitud'),
                'longitud': validated_record.get('longitud'),
                'localidad': validated_record.get('localidad', ''),
                'ciudad': validated_record.get('ciudad', ''),
                'departamento': validated_record.get('departamento', ''),
                'sentido': call_direction,
                'created_at': datetime.now().isoformat()
            }
            
            return normalized_data
            
        except Exception as e:
            self.logger.error(f"Error normalizando registro WOM call: {e}", exc_info=True)
            return None

    def _parse_wom_datetime(self, date_series: pd.Series) -> pd.Series:
        """
        Parsea fechas en formato WOM (dd/mm/yyyy HH:MM) a datetime.
        
        Args:
            date_series: Serie de pandas con fechas en formato WOM
            
        Returns:
            Serie con fechas convertidas a datetime
        """
        try:
            # Formato específico de WOM: dd/mm/yyyy HH:MM
            return pd.to_datetime(date_series, format='%d/%m/%Y %H:%M', errors='coerce')
        except Exception as e:
            self.logger.warning(f"Error parseando fechas WOM: {e}")
            # Intentar formato alternativo sin segundos
            try:
                return pd.to_datetime(date_series, format='%d/%m/%Y %H:%M:%S', errors='coerce')
            except:
                # Como último recurso, usar inferencia automática
                return pd.to_datetime(date_series, errors='coerce')


if __name__ == "__main__":
    # Código de testing básico
    service = DataNormalizerService()
    print("DataNormalizerService inicializado correctamente")
    
    # Test de normalización
    test_claro_normalization()