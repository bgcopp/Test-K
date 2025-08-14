"""
KRONOS Data Validators
===============================================================================
Módulo de validaciones para datos de entrada del backend de KRONOS.
Incluye validadores para emails, contraseñas, datos de misiones, archivos
y otros tipos de datos específicos de la aplicación.

Características principales:
- Validación de emails con regex
- Validación de fortaleza de contraseñas
- Validación de datos geográficos (lat/lon)
- Validación de datos de misiones
- Validación de formatos de archivos
- Validación de permisos y roles
===============================================================================
"""

import re
import mimetypes
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
import json

# Expresiones regulares para validaciones
EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128

# MIME types permitidos para archivos
ALLOWED_FILE_TYPES = {
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
    'application/vnd.ms-excel',  # .xls
    'text/csv',  # .csv
}

# Estados válidos para misiones
VALID_MISSION_STATUSES = {'Planificación', 'En Progreso', 'Completada', 'Cancelada'}

# Estados válidos para usuarios
VALID_USER_STATUSES = {'active', 'inactive'}


class ValidationError(Exception):
    """Excepción personalizada para errores de validación"""
    pass


def validate_email(email: str) -> bool:
    """
    Valida formato de email
    
    Args:
        email: String del email a validar
        
    Returns:
        True si el email tiene formato válido
    """
    if not email or not isinstance(email, str):
        return False
    
    return bool(EMAIL_REGEX.match(email.strip()))


def validate_required_string(value: Any, field_name: str, min_length: int = 1, max_length: int = 255) -> str:
    """
    Valida que un valor sea string no vacío
    
    Args:
        value: Valor a validar
        field_name: Nombre del campo para mensajes de error
        min_length: Longitud mínima
        max_length: Longitud máxima
        
    Returns:
        String validado y limpio
        
    Raises:
        ValidationError: Si la validación falla
    """
    if not value:
        raise ValidationError(f"{field_name} es requerido")
    
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} debe ser un string")
    
    cleaned_value = value.strip()
    
    if len(cleaned_value) < min_length:
        raise ValidationError(f"{field_name} debe tener al menos {min_length} caracteres")
    
    if len(cleaned_value) > max_length:
        raise ValidationError(f"{field_name} no puede exceder {max_length} caracteres")
    
    return cleaned_value


def validate_password_strength(password: str) -> bool:
    """
    Valida la fortaleza de una contraseña
    
    Requisitos:
    - Al menos 8 caracteres
    - Máximo 128 caracteres
    - Al menos una letra minúscula
    - Al menos una letra mayúscula  
    - Al menos un número
    - Al menos un carácter especial
    
    Args:
        password: Contraseña a validar
        
    Returns:
        True si la contraseña cumple con los requisitos
    """
    if not password or not isinstance(password, str):
        return False
    
    if len(password) < PASSWORD_MIN_LENGTH or len(password) > PASSWORD_MAX_LENGTH:
        return False
    
    # Verificar que tenga al menos una minúscula
    if not re.search(r'[a-z]', password):
        return False
    
    # Verificar que tenga al menos una mayúscula
    if not re.search(r'[A-Z]', password):
        return False
    
    # Verificar que tenga al menos un número
    if not re.search(r'\d', password):
        return False
    
    # Verificar que tenga al menos un carácter especial
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    
    return True


def validate_user_data(data: Dict[str, Any], is_update: bool = False) -> Dict[str, Any]:
    """
    Valida datos de usuario para crear o actualizar
    
    Args:
        data: Diccionario con datos del usuario
        is_update: True si es actualización (algunos campos opcionales)
        
    Returns:
        Diccionario con datos validados
        
    Raises:
        ValidationError: Si hay errores de validación
    """
    validated_data = {}
    
    # Validar nombre (requerido siempre)
    if not is_update or 'name' in data:
        validated_data['name'] = validate_required_string(
            data.get('name'), 'name', min_length=2, max_length=100
        )
    
    # Validar email (requerido siempre)
    if not is_update or 'email' in data:
        email = data.get('email')
        if not email:
            raise ValidationError("email es requerido")
        
        email = email.strip().lower()
        if not validate_email(email):
            raise ValidationError("Formato de email inválido")
        
        validated_data['email'] = email
    
    # Validar roleId (requerido en creación)
    if not is_update or 'roleId' in data:
        role_id = data.get('roleId')
        if not is_update and not role_id:
            raise ValidationError("roleId es requerido")
        
        if role_id:
            validated_data['role_id'] = validate_required_string(role_id, 'roleId')
    
    # Validar status
    if 'status' in data:
        status = data.get('status')
        if status not in VALID_USER_STATUSES:
            raise ValidationError(f"status debe ser uno de: {', '.join(VALID_USER_STATUSES)}")
        validated_data['status'] = status
    
    # Validar avatar (opcional)
    if 'avatar' in data:
        avatar = data.get('avatar')
        if avatar:
            validated_data['avatar'] = validate_required_string(avatar, 'avatar', max_length=500)
    
    return validated_data


def validate_role_data(data: Dict[str, Any], is_update: bool = False) -> Dict[str, Any]:
    """
    Valida datos de rol para crear o actualizar
    
    Args:
        data: Diccionario con datos del rol
        is_update: True si es actualización
        
    Returns:
        Diccionario con datos validados
        
    Raises:
        ValidationError: Si hay errores de validación
    """
    validated_data = {}
    
    # Validar nombre (requerido siempre)
    if not is_update or 'name' in data:
        validated_data['name'] = validate_required_string(
            data.get('name'), 'name', min_length=2, max_length=100
        )
    
    # Validar permissions (requerido siempre)
    if not is_update or 'permissions' in data:
        permissions = data.get('permissions')
        if not permissions:
            raise ValidationError("permissions es requerido")
        
        validated_permissions = validate_permissions_structure(permissions)
        validated_data['permissions'] = validated_permissions
    
    return validated_data


def validate_permissions_structure(permissions: Any) -> Dict[str, Any]:
    """
    Valida la estructura de permisos
    
    Args:
        permissions: Objeto de permisos a validar
        
    Returns:
        Diccionario de permisos validado
        
    Raises:
        ValidationError: Si la estructura es inválida
    """
    if not isinstance(permissions, dict):
        raise ValidationError("permissions debe ser un objeto")
    
    # Estructura esperada de permisos
    expected_resources = {
        'users': ['create', 'read', 'update', 'delete'],
        'roles': ['create', 'read', 'update', 'delete'],
        'missions': ['create', 'read', 'update', 'delete'],
        'dashboard': ['read'],
        'targetAnalysis': ['execute']
    }
    
    validated_permissions = {}
    
    for resource, actions in expected_resources.items():
        if resource not in permissions:
            raise ValidationError(f"permissions debe incluir {resource}")
        
        resource_perms = permissions[resource]
        if not isinstance(resource_perms, dict):
            raise ValidationError(f"permissions.{resource} debe ser un objeto")
        
        validated_resource_perms = {}
        for action in actions:
            if action not in resource_perms:
                raise ValidationError(f"permissions.{resource} debe incluir {action}")
            
            if not isinstance(resource_perms[action], bool):
                raise ValidationError(f"permissions.{resource}.{action} debe ser boolean")
            
            validated_resource_perms[action] = resource_perms[action]
        
        validated_permissions[resource] = validated_resource_perms
    
    return validated_permissions


def validate_mission_data(data: Dict[str, Any], is_update: bool = False) -> Dict[str, Any]:
    """
    Valida datos de misión para crear o actualizar
    
    Args:
        data: Diccionario con datos de la misión
        is_update: True si es actualización
        
    Returns:
        Diccionario con datos validados
        
    Raises:
        ValidationError: Si hay errores de validación
    """
    validated_data = {}
    
    # Validar code (requerido en creación)
    if not is_update or 'code' in data:
        if not is_update:
            validated_data['code'] = validate_required_string(
                data.get('code'), 'code', min_length=2, max_length=20
            )
        elif 'code' in data:
            validated_data['code'] = validate_required_string(
                data.get('code'), 'code', min_length=2, max_length=20
            )
    
    # Validar name (requerido en creación)
    if not is_update or 'name' in data:
        if not is_update:
            validated_data['name'] = validate_required_string(
                data.get('name'), 'name', min_length=2, max_length=200
            )
        elif 'name' in data:
            validated_data['name'] = validate_required_string(
                data.get('name'), 'name', min_length=2, max_length=200
            )
    
    # Validar description (opcional)
    if 'description' in data:
        description = data.get('description')
        if description:
            validated_data['description'] = validate_required_string(
                description, 'description', max_length=1000
            )
    
    # Validar status
    if 'status' in data:
        status = data.get('status')
        if status not in VALID_MISSION_STATUSES:
            raise ValidationError(f"status debe ser uno de: {', '.join(VALID_MISSION_STATUSES)}")
        validated_data['status'] = status
    
    # Validar fechas
    if not is_update or 'startDate' in data:
        start_date = data.get('startDate')
        if not is_update and not start_date:
            raise ValidationError("startDate es requerido")
        
        if start_date:
            validated_data['start_date'] = validate_date_string(start_date, 'startDate')
    
    if 'endDate' in data:
        end_date = data.get('endDate')
        if end_date:
            validated_data['end_date'] = validate_date_string(end_date, 'endDate')
    
    return validated_data


def validate_date_string(date_str: str, field_name: str) -> str:
    """
    Valida formato de fecha (YYYY-MM-DD)
    
    Args:
        date_str: String de fecha a validar
        field_name: Nombre del campo para errores
        
    Returns:
        String de fecha validado
        
    Raises:
        ValidationError: Si el formato es inválido
    """
    if not date_str or not isinstance(date_str, str):
        raise ValidationError(f"{field_name} debe ser un string")
    
    try:
        # Intentar parsear la fecha
        datetime.strptime(date_str, '%Y-%m-%d')
        return date_str
    except ValueError:
        raise ValidationError(f"{field_name} debe tener formato YYYY-MM-DD")


def validate_coordinates(lat: Union[str, float], lon: Union[str, float]) -> Tuple[float, float]:
    """
    Valida coordenadas geográficas
    
    Args:
        lat: Latitud
        lon: Longitud
        
    Returns:
        Tupla con lat, lon como floats
        
    Raises:
        ValidationError: Si las coordenadas son inválidas
    """
    try:
        lat_float = float(lat)
        lon_float = float(lon)
    except (ValueError, TypeError):
        raise ValidationError("lat y lon deben ser números válidos")
    
    if lat_float < -90.0 or lat_float > 90.0:
        raise ValidationError("lat debe estar entre -90.0 y 90.0")
    
    if lon_float < -180.0 or lon_float > 180.0:
        raise ValidationError("lon debe estar entre -180.0 y 180.0")
    
    return lat_float, lon_float


def validate_signal_strength(signal: Union[str, int]) -> int:
    """
    Valida intensidad de señal (debe ser negativa o cero)
    
    Args:
        signal: Intensidad de señal
        
    Returns:
        Signal como integer
        
    Raises:
        ValidationError: Si la señal es inválida
    """
    try:
        signal_int = int(signal)
    except (ValueError, TypeError):
        raise ValidationError("signal debe ser un número entero")
    
    if signal_int > 0:
        raise ValidationError("signal debe ser menor o igual a 0")
    
    return signal_int


def validate_file_data(file_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida datos de archivo subido
    
    Args:
        file_data: {"name": "...", "content": "data:mime/type;base64,..."}
        
    Returns:
        Diccionario validado con name y content
        
    Raises:
        ValidationError: Si los datos son inválidos
    """
    if not isinstance(file_data, dict):
        raise ValidationError("file_data debe ser un objeto")
    
    # Validar nombre
    name = file_data.get('name')
    if not name or not isinstance(name, str):
        raise ValidationError("name es requerido y debe ser string")
    
    # Validar contenido
    content = file_data.get('content')
    if not content or not isinstance(content, str):
        raise ValidationError("content es requerido y debe ser string")
    
    # Validar formato base64
    if not content.startswith('data:'):
        raise ValidationError("content debe ser formato data URL")
    
    try:
        content_type, content_string = content.split(',', 1)
    except ValueError:
        raise ValidationError("Formato de content inválido")
    
    # Validar tipo MIME
    mime_type = content_type.split(';')[0].replace('data:', '')
    if mime_type not in ALLOWED_FILE_TYPES:
        raise ValidationError(f"Tipo de archivo no permitido: {mime_type}")
    
    return {
        'name': name.strip(),
        'content': content,
        'mime_type': mime_type
    }


def validate_cellular_data_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida un registro completo de datos celulares SCANHUNTER
    
    Args:
        record: Diccionario con datos del registro SCANHUNTER
        
    Returns:
        Registro validado con todos los campos SCANHUNTER
        
    Raises:
        ValidationError: Si los datos son inválidos
    """
    validated_record = {}
    
    # Validar punto de medición
    validated_record['punto'] = validate_required_string(
        record.get('punto'), 'punto', max_length=100
    )
    
    # Validar coordenadas
    lat, lon = validate_coordinates(record.get('lat'), record.get('lon'))
    validated_record['lat'] = lat
    validated_record['lon'] = lon
    
    # Validar MNC+MCC
    mnc_mcc = validate_required_string(record.get('mnc_mcc'), 'mnc_mcc')
    if not mnc_mcc.isdigit() or len(mnc_mcc) not in [5, 6]:
        raise ValidationError("mnc_mcc debe contener 5-6 dígitos numéricos")
    validated_record['mnc_mcc'] = mnc_mcc
    
    # Validar operador
    validated_record['operator'] = validate_required_string(
        record.get('operator'), 'operator', max_length=50
    )
    
    # Validar RSSI
    validated_record['rssi'] = validate_signal_strength(record.get('rssi'))
    
    # Validar tecnología
    tecnologia = validate_required_string(record.get('tecnologia'), 'tecnologia')
    valid_technologies = ['GSM', 'UMTS', '3G', 'LTE', '4G', '5G NR', '5G']
    if tecnologia not in valid_technologies:
        raise ValidationError(f"tecnologia debe ser uno de: {', '.join(valid_technologies)}")
    validated_record['tecnologia'] = tecnologia
    
    # Validar Cell ID
    validated_record['cell_id'] = validate_required_string(
        record.get('cell_id'), 'cell_id', max_length=50
    )
    
    # Campos opcionales
    for optional_field in ['lac_tac', 'enb', 'channel', 'comentario']:
        value = record.get(optional_field)
        if value and str(value).strip() and str(value) != 'nan':
            validated_record[optional_field] = str(value).strip()
    
    return validated_record


def validate_operator_data_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida un registro de datos de operador
    
    Args:
        record: Diccionario con datos del registro
        
    Returns:
        Registro validado
        
    Raises:
        ValidationError: Si los datos son inválidos
    """
    validated_record = {}
    
    # Validar operatorId
    validated_record['operator_id'] = validate_required_string(
        record.get('operatorId'), 'operatorId', max_length=50
    )
    
    # Validar name
    validated_record['name'] = validate_required_string(
        record.get('name'), 'name', max_length=100
    )
    
    # Validar towers
    towers = record.get('towers')
    try:
        towers_int = int(towers)
        if towers_int <= 0:
            raise ValidationError("towers debe ser un número positivo")
        validated_record['towers'] = towers_int
    except (ValueError, TypeError):
        raise ValidationError("towers debe ser un número entero positivo")
    
    # Validar coverage
    coverage = record.get('coverage')
    if not coverage or not isinstance(coverage, str):
        raise ValidationError("coverage es requerido")
    
    coverage = coverage.strip()
    if not coverage.endswith('%') or len(coverage) < 2:
        raise ValidationError("coverage debe terminar en % y tener formato válido")
    
    try:
        # Verificar que el valor antes del % sea un número
        float(coverage[:-1])
    except ValueError:
        raise ValidationError("coverage debe contener un número válido antes del %")
    
    validated_record['coverage'] = coverage
    
    return validated_record


# ============================================================================
# VALIDADORES ESPECÍFICOS PARA OPERADORES
# ============================================================================

def validate_colombian_phone_number(phone: str, field_name: str = "número telefónico") -> str:
    """
    Valida número telefónico colombiano
    
    Args:
        phone: Número telefónico a validar
        field_name: Nombre del campo para errores
        
    Returns:
        Número telefónico limpio y validado
        
    Raises:
        ValidationError: Si el número es inválido
    """
    if not phone:
        raise ValidationError(f"{field_name} es requerido")
    
    # Limpiar número (remover caracteres no numéricos)
    phone_clean = re.sub(r'[^\d]', '', str(phone))
    
    # Validar longitud (mínimo 10 dígitos para Colombia)
    if len(phone_clean) < 10:
        raise ValidationError(f"{field_name} debe tener al menos 10 dígitos")
    
    # Validar que no exceda 15 dígitos (TIGO puede tener números más largos)
    if len(phone_clean) > 15:
        raise ValidationError(f"{field_name} no puede exceder 15 dígitos")
    
    # Validar prefijos colombianos comunes
    if len(phone_clean) == 10:
        # Formato nacional: debe empezar con 3 (móviles) o con códigos de área válidos
        if not (phone_clean.startswith('3') or 
                phone_clean.startswith(('1', '2', '4', '5', '6', '7', '8'))):
            raise ValidationError(f"{field_name} no tiene un prefijo colombiano válido")
    elif len(phone_clean) in [12, 13, 14, 15]:
        # Formato internacional o TIGO extendido: flexibilizar validación
        # Permitir números internacionales válidos sin restricciones estrictas de país
        
        # Códigos de países comunes para validación básica
        valid_country_prefixes = [
            '1',    # NANP (USA, Canadá)
            '44',   # Reino Unido
            '49',   # Alemania
            '33',   # Francia
            '39',   # Italia
            '34',   # España
            '52',   # México
            '54',   # Argentina
            '55',   # Brasil
            '56',   # Chile
            '57',   # Colombia
            '58',   # Venezuela
            '593',  # Ecuador
            '594',  # Guyana Francesa
            '595',  # Paraguay
            '596',  # Martinica
            '597',  # Suriname
            '598',  # Uruguay
            # Agregar más prefijos según necesidad
        ]
        
        # Verificar si el número comienza con algún código de país válido
        is_valid_international = False
        for prefix in valid_country_prefixes:
            if phone_clean.startswith(prefix):
                is_valid_international = True
                break
        
        # Si no coincide con códigos conocidos, hacer validación básica de dígitos
        if not is_valid_international:
            # Aceptar números que al menos tengan estructura telefónica válida
            # (todos dígitos, longitud razonable)
            pass  # Ya pasó la validación de longitud y formato básico
    
    return phone_clean


def validate_claro_date_format(date_str: str, field_name: str = "fecha") -> datetime:
    """
    Valida y parsea fecha en formato CLARO (20240419080000)
    
    Args:
        date_str: String de fecha en formato YYYYMMDDHHMMSS
        field_name: Nombre del campo para errores
        
    Returns:
        Objeto datetime parseado
        
    Raises:
        ValidationError: Si el formato es inválido
    """
    if not date_str:
        raise ValidationError(f"{field_name} es requerido")
    
    date_str = str(date_str).strip()
    
    # Validar longitud
    if len(date_str) != 14:
        raise ValidationError(f"{field_name} debe tener formato YYYYMMDDHHMMSS (14 dígitos)")
    
    # Validar que sean solo dígitos
    if not date_str.isdigit():
        raise ValidationError(f"{field_name} debe contener solo dígitos")
    
    try:
        # Intentar parsear la fecha
        parsed_date = datetime.strptime(date_str, '%Y%m%d%H%M%S')
        
        # Validar rango razonable (no muy antigua ni muy futura)
        current_year = datetime.now().year
        if parsed_date.year < 2000 or parsed_date.year > current_year + 1:
            raise ValidationError(f"{field_name} tiene un año inválido: {parsed_date.year}")
        
        return parsed_date
    except ValueError as e:
        raise ValidationError(f"{field_name} tiene formato de fecha/hora inválido: {str(e)}")


def validate_claro_datetime_format(datetime_str: str, field_name: str = "fecha_hora") -> datetime:
    """
    Valida y parsea fecha/hora en formato CLARO (20/05/2021 10:02:26)
    
    Args:
        datetime_str: String de fecha/hora en formato DD/MM/YYYY HH:MM:SS
        field_name: Nombre del campo para errores
        
    Returns:
        Objeto datetime parseado
        
    Raises:
        ValidationError: Si el formato es inválido
    """
    if not datetime_str:
        raise ValidationError(f"{field_name} es requerido")
    
    datetime_str = str(datetime_str).strip()
    
    try:
        # Intentar parsear con formato DD/MM/YYYY HH:MM:SS
        parsed_datetime = datetime.strptime(datetime_str, '%d/%m/%Y %H:%M:%S')
        
        # Validar rango razonable
        current_year = datetime.now().year
        if parsed_datetime.year < 2000 or parsed_datetime.year > current_year + 1:
            raise ValidationError(f"{field_name} tiene un año inválido: {parsed_datetime.year}")
        
        return parsed_datetime
    except ValueError:
        # Intentar formato alternativo sin segundos
        try:
            parsed_datetime = datetime.strptime(datetime_str, '%d/%m/%Y %H:%M')
            return parsed_datetime
        except ValueError as e:
            raise ValidationError(f"{field_name} debe tener formato DD/MM/YYYY HH:MM:SS: {str(e)}")


def validate_cell_id(cell_id: Union[str, int], field_name: str = "celda") -> str:
    """
    Valida identificador de celda
    
    Args:
        cell_id: ID de la celda
        field_name: Nombre del campo para errores
        
    Returns:
        Cell ID validado como string
        
    Raises:
        ValidationError: Si el ID es inválido
    """
    if not cell_id and cell_id != 0:
        raise ValidationError(f"{field_name} es requerido")
    
    cell_id_str = str(cell_id).strip()
    
    # Validar que no esté vacío
    if not cell_id_str:
        raise ValidationError(f"{field_name} no puede estar vacío")
    
    # Validar longitud máxima (expandida para TIGO)
    if len(cell_id_str) > 50:
        raise ValidationError(f"{field_name} no puede exceder 50 caracteres")
    
    return cell_id_str


def validate_lac_tac(lac_tac: Union[str, int], field_name: str = "LAC/TAC") -> Optional[str]:
    """
    Valida código LAC/TAC
    
    Args:
        lac_tac: Código LAC o TAC
        field_name: Nombre del campo para errores
        
    Returns:
        LAC/TAC validado como string o None si está vacío
        
    Raises:
        ValidationError: Si el código es inválido
    """
    if not lac_tac and lac_tac != 0:
        return None
    
    lac_tac_str = str(lac_tac).strip()
    
    # Permitir valores vacíos o '0'
    if not lac_tac_str or lac_tac_str == '0':
        return None
    
    # Validar longitud máxima
    if len(lac_tac_str) > 10:
        raise ValidationError(f"{field_name} no puede exceder 10 caracteres")
    
    return lac_tac_str


def validate_call_duration(duration: Union[str, int, float], field_name: str = "duración") -> int:
    """
    Valida duración de llamada en segundos
    
    Args:
        duration: Duración en segundos
        field_name: Nombre del campo para errores
        
    Returns:
        Duración validada como entero
        
    Raises:
        ValidationError: Si la duración es inválida
    """
    if duration is None or duration == '':
        return 0
    
    try:
        duration_int = int(float(duration))
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} debe ser un número entero")
    
    # Validar que no sea negativa
    if duration_int < 0:
        raise ValidationError(f"{field_name} no puede ser negativa")
    
    # Validar duración máxima razonable (24 horas = 86400 segundos)
    if duration_int > 86400:
        raise ValidationError(f"{field_name} no puede exceder 24 horas")
    
    return duration_int


def validate_claro_call_type(call_type: str, field_name: str = "tipo") -> str:
    """
    Valida tipo de llamada CLARO
    
    Args:
        call_type: Tipo de llamada
        field_name: Nombre del campo para errores
        
    Returns:
        Tipo de llamada validado
        
    Raises:
        ValidationError: Si el tipo es inválido
    """
    if not call_type:
        raise ValidationError(f"{field_name} es requerido")
    
    call_type_clean = str(call_type).strip().upper()
    
    # Tipos válidos para CLARO
    valid_types = ['CDR_ENTRANTE', 'CDR_SALIENTE', 'ENTRANTE', 'SALIENTE']
    
    if call_type_clean not in valid_types:
        raise ValidationError(f"{field_name} debe ser uno de: {', '.join(valid_types)}")
    
    return call_type_clean


def validate_claro_datos_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida un registro completo de datos por celda CLARO
    
    Args:
        record: Diccionario con datos del registro CLARO
        
    Returns:
        Registro validado
        
    Raises:
        ValidationError: Si los datos son inválidos
    """
    validated_record = {}
    
    # Validar número telefónico
    validated_record['numero_telefono'] = validate_colombian_phone_number(
        record.get('numero_telefono'), 'numero_telefono'
    )
    
    # Validar fecha de tráfico
    validated_record['fecha_trafico'] = validate_claro_date_format(
        record.get('fecha_trafico'), 'fecha_trafico'
    )
    
    # Validar tipo CDR
    tipo_cdr = record.get('tipo_cdr')
    if not tipo_cdr:
        raise ValidationError("tipo_cdr es requerido")
    
    tipo_cdr_clean = str(tipo_cdr).strip().upper()
    if tipo_cdr_clean not in ['DATOS', 'DATA']:
        raise ValidationError("tipo_cdr debe ser DATOS o DATA")
    
    validated_record['tipo_cdr'] = tipo_cdr_clean
    
    # Validar celda decimal
    validated_record['celda_decimal'] = validate_cell_id(
        record.get('celda_decimal'), 'celda_decimal'
    )
    
    # Validar LAC decimal
    validated_record['lac_decimal'] = validate_lac_tac(
        record.get('lac_decimal'), 'lac_decimal'
    )
    
    return validated_record


def validate_claro_llamadas_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida un registro completo de llamadas CLARO
    
    Args:
        record: Diccionario con datos del registro de llamada CLARO
        
    Returns:
        Registro validado
        
    Raises:
        ValidationError: Si los datos son inválidos
    """
    validated_record = {}
    
    # Validar celdas
    validated_record['celda_inicio_llamada'] = validate_cell_id(
        record.get('celda_inicio_llamada'), 'celda_inicio_llamada'
    )
    
    celda_final = record.get('celda_final_llamada')
    if celda_final:
        validated_record['celda_final_llamada'] = validate_cell_id(
            celda_final, 'celda_final_llamada'
        )
    
    # Validar números telefónicos
    validated_record['originador'] = validate_colombian_phone_number(
        record.get('originador'), 'originador'
    )
    
    validated_record['receptor'] = validate_colombian_phone_number(
        record.get('receptor'), 'receptor'
    )
    
    # Validar fecha/hora
    validated_record['fecha_hora'] = validate_claro_datetime_format(
        record.get('fecha_hora'), 'fecha_hora'
    )
    
    # Validar duración
    validated_record['duracion'] = validate_call_duration(
        record.get('duracion'), 'duracion'
    )
    
    # Validar tipo de llamada
    validated_record['tipo'] = validate_claro_call_type(
        record.get('tipo'), 'tipo'
    )
    
    return validated_record


# ============================================================================
# VALIDADORES ESPECÍFICOS PARA TIGO
# ============================================================================

def validate_tigo_datetime_format(datetime_str: str, field_name: str = "fecha_hora") -> datetime:
    """
    Valida y parsea fecha/hora en formato TIGO (28/02/2025 01:20:19)
    
    Args:
        datetime_str: String de fecha/hora en formato DD/MM/YYYY HH:MM:SS
        field_name: Nombre del campo para errores
        
    Returns:
        Objeto datetime parseado
        
    Raises:
        ValidationError: Si el formato es inválido
    """
    if not datetime_str:
        raise ValidationError(f"{field_name} es requerido")
    
    datetime_str = str(datetime_str).strip()
    
    try:
        # Intentar parsear con formato DD/MM/YYYY HH:MM:SS
        parsed_datetime = datetime.strptime(datetime_str, '%d/%m/%Y %H:%M:%S')
        
        # Validar rango razonable
        current_year = datetime.now().year
        if parsed_datetime.year < 2000 or parsed_datetime.year > current_year + 1:
            raise ValidationError(f"{field_name} tiene un año inválido: {parsed_datetime.year}")
        
        return parsed_datetime
    except ValueError:
        # Intentar formato alternativo sin segundos
        try:
            parsed_datetime = datetime.strptime(datetime_str, '%d/%m/%Y %H:%M')
            return parsed_datetime
        except ValueError as e:
            raise ValidationError(f"{field_name} debe tener formato DD/MM/YYYY HH:MM:SS: {str(e)}")


def validate_tigo_coordinates(lat_str: str, lon_str: str) -> Tuple[float, float]:
    """
    Valida coordenadas en formato específico TIGO (con comas como decimales)
    
    Args:
        lat_str: Latitud en formato TIGO ("-74,074989" o "4,64958")
        lon_str: Longitud en formato TIGO
        
    Returns:
        Tupla con lat, lon como floats
        
    Raises:
        ValidationError: Si las coordenadas son inválidas
    """
    if not lat_str or not lon_str:
        raise ValidationError("Coordenadas TIGO son requeridas")
    
    try:
        # Convertir formato TIGO (comas como decimales, posibles comillas)
        lat_clean = str(lat_str).replace(',', '.').strip('"\'')
        lon_clean = str(lon_str).replace(',', '.').strip('"\'')
        
        lat_float = float(lat_clean)
        lon_float = float(lon_clean)
    except (ValueError, TypeError):
        raise ValidationError(f"Coordenadas TIGO inválidas: {lat_str}, {lon_str}")
    
    # Validar rangos
    if lat_float < -90.0 or lat_float > 90.0:
        raise ValidationError(f"Latitud TIGO fuera de rango: {lat_float}")
    
    if lon_float < -180.0 or lon_float > 180.0:
        raise ValidationError(f"Longitud TIGO fuera de rango: {lon_float}")
    
    return lat_float, lon_float


def validate_tigo_direction_field(direction: str, field_name: str = "direccion") -> str:
    """
    Valida campo de dirección TIGO ('O' = SALIENTE, 'I' = ENTRANTE)
    
    Args:
        direction: Campo dirección TIGO
        field_name: Nombre del campo para errores
        
    Returns:
        Dirección validada y normalizada
        
    Raises:
        ValidationError: Si la dirección es inválida
    """
    if not direction:
        raise ValidationError(f"{field_name} es requerido")
    
    direction_clean = str(direction).strip().upper()
    
    # Mapeo de valores válidos TIGO
    valid_directions = {
        'O': 'SALIENTE',
        'SALIENTE': 'SALIENTE',
        'I': 'ENTRANTE', 
        'ENTRANTE': 'ENTRANTE'
    }
    
    if direction_clean not in valid_directions:
        raise ValidationError(f"{field_name} debe ser 'O' (saliente) o 'I' (entrante), recibido: {direction_clean}")
    
    return direction_clean


def validate_tigo_antenna_data(azimuth: Any, altura: Any, potencia: Any) -> Dict[str, Optional[float]]:
    """
    Valida datos de antena específicos TIGO
    
    Args:
        azimuth: Azimut de la antena (0-360 grados)
        altura: Altura de la antena en metros
        potencia: Potencia de la antena (puede tener comas como decimales)
        
    Returns:
        Dict con datos de antena validados
        
    Raises:
        ValidationError: Si los datos son inválidos
    """
    result = {'azimuth': None, 'altura': None, 'potencia': None}
    
    # Validar azimuth
    if azimuth is not None and str(azimuth).strip():
        try:
            azimuth_float = float(str(azimuth).replace(',', '.'))
            if azimuth_float < 0 or azimuth_float > 360:
                raise ValidationError("Azimuth debe estar entre 0 y 360 grados")
            result['azimuth'] = azimuth_float
        except (ValueError, TypeError):
            raise ValidationError(f"Azimuth inválido: {azimuth}")
    
    # Validar altura
    if altura is not None and str(altura).strip():
        try:
            altura_float = float(str(altura).replace(',', '.'))
            if altura_float <= 0:
                raise ValidationError("Altura debe ser positiva")
            result['altura'] = altura_float
        except (ValueError, TypeError):
            raise ValidationError(f"Altura inválida: {altura}")
    
    # Validar potencia
    if potencia is not None and str(potencia).strip():
        try:
            potencia_str = str(potencia).replace(',', '.').strip('"\'')
            potencia_float = float(potencia_str)
            result['potencia'] = potencia_float
        except (ValueError, TypeError):
            raise ValidationError(f"Potencia inválida: {potencia}")
    
    return result


def validate_tigo_call_type(call_type: str, field_name: str = "tipo_llamada") -> str:
    """
    Valida tipo de llamada TIGO
    
    Args:
        call_type: Tipo de llamada TIGO
        field_name: Nombre del campo para errores
        
    Returns:
        Tipo de llamada validado
        
    Raises:
        ValidationError: Si el tipo es inválido
    """
    if not call_type:
        raise ValidationError(f"{field_name} es requerido")
    
    call_type_clean = str(call_type).strip()
    
    # TIGO usa códigos numéricos variados (ej: 6, 10, 20, 30, 50, 200)
    try:
        call_type_int = int(call_type_clean)
        # Validar rangos ampliados para TIGO
        if call_type_int < 1 or call_type_int > 999:
            raise ValidationError(f"{field_name} fuera de rango esperado: {call_type_int}")
        return str(call_type_int)
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} debe ser un código numérico: {call_type}")


def validate_tigo_llamada_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida un registro completo de llamada TIGO (mixta)
    
    Args:
        record: Diccionario con datos del registro de llamada TIGO
        
    Returns:
        Registro validado
        
    Raises:
        ValidationError: Si los datos son inválidos
    """
    validated_record = {}
    
    # Validar tipo de llamada
    validated_record['tipo_de_llamada'] = validate_tigo_call_type(
        record.get('tipo_de_llamada'), 'tipo_de_llamada'
    )
    
    # Validar número A (origen)
    validated_record['numero_a'] = validate_colombian_phone_number(
        record.get('numero_a'), 'numero_a'
    )
    
    # Validar número marcado (puede ser dominio web o número)
    numero_marcado = record.get('numero_marcado')
    if numero_marcado and str(numero_marcado).strip():
        numero_marcado_clean = str(numero_marcado).strip()
        # Si parece un número telefónico, validarlo
        if re.match(r'^[\d\+\-\s\(\)]+$', numero_marcado_clean):
            try:
                validated_record['numero_marcado'] = validate_colombian_phone_number(
                    numero_marcado_clean, 'numero_marcado'
                )
            except ValidationError:
                # Si no es un número válido, mantener como string
                validated_record['numero_marcado'] = numero_marcado_clean
        else:
            # Mantener dominios web y otros formatos
            validated_record['numero_marcado'] = numero_marcado_clean
    else:
        validated_record['numero_marcado'] = validated_record['numero_a']  # Usar número A como fallback
    
    # Validar dirección (O/I)
    validated_record['direccion'] = validate_tigo_direction_field(
        record.get('direccion'), 'direccion'
    )
    
    # Validar fecha/hora
    validated_record['fecha_hora_origen'] = validate_tigo_datetime_format(
        record.get('fecha_hora_origen'), 'fecha_hora_origen'
    )
    
    # Validar duración
    validated_record['duracion_total_seg'] = validate_call_duration(
        record.get('duracion_total_seg'), 'duracion_total_seg'
    )
    
    # Validar celda origen
    validated_record['celda_origen_truncada'] = validate_cell_id(
        record.get('celda_origen_truncada'), 'celda_origen_truncada'
    )
    
    # Validar tecnología
    tech = record.get('tecnologia')
    if tech:
        tech_clean = str(tech).strip().upper()
        valid_techs = ['4G', '3G', '2G', 'LTE', 'GSM', 'UMTS', '5G']
        if tech_clean not in valid_techs:
            # Permitir otras tecnologías pero limpiar
            tech_clean = tech_clean[:10]  # Limitar longitud
        validated_record['tecnologia'] = tech_clean
    
    # Validar codec
    codec = record.get('trcsextracodec')
    if codec and str(codec).strip():
        validated_record['trcsextracodec'] = str(codec).strip()
    
    # Validar coordenadas TIGO
    lat = record.get('latitude') or record.get('latitud')
    lon = record.get('longitude') or record.get('longitud')
    if lat is not None and lon is not None:
        try:
            validated_lat, validated_lon = validate_tigo_coordinates(lat, lon)
            validated_record['latitud'] = validated_lat
            validated_record['longitud'] = validated_lon
        except ValidationError:
            # Coordenadas inválidas, continuar sin ellas
            pass
    
    # Validar datos de antena
    try:
        antenna_data = validate_tigo_antenna_data(
            record.get('azimuth'), 
            record.get('altura'), 
            record.get('potencia')
        )
        validated_record.update(antenna_data)
    except ValidationError:
        # Datos de antena inválidos, continuar sin ellos
        pass
    
    # Validar campos descriptivos
    for field in ['ciudad', 'departamento', 'direccion_fisica', 'tipo_cobertura', 'tipo_estructura']:
        value = record.get(field)
        if value and str(value).strip():
            validated_record[field] = str(value).strip()[:100]  # Limitar longitud
    
    return validated_record


# ============================================================================
# VALIDADORES ESPECÍFICOS PARA MOVISTAR
# ============================================================================

def validate_movistar_date_format(date_str: str, field_name: str = "fecha") -> datetime:
    """
    Valida y parsea fecha en formato MOVISTAR (20240419080341)
    
    Args:
        date_str: String de fecha en formato YYYYMMDDHHMMSS
        field_name: Nombre del campo para errores
        
    Returns:
        Objeto datetime parseado
        
    Raises:
        ValidationError: Si el formato es inválido
    """
    if not date_str:
        raise ValidationError(f"{field_name} es requerido")
    
    date_str = str(date_str).strip()
    
    # Validar longitud
    if len(date_str) != 14:
        raise ValidationError(f"{field_name} debe tener formato YYYYMMDDHHMMSS (14 dígitos)")
    
    # Validar que sean solo dígitos
    if not date_str.isdigit():
        raise ValidationError(f"{field_name} debe contener solo dígitos")
    
    try:
        # Intentar parsear la fecha
        parsed_date = datetime.strptime(date_str, '%Y%m%d%H%M%S')
        
        # Validar rango razonable (no muy antigua ni muy futura)
        current_year = datetime.now().year
        if parsed_date.year < 2000 or parsed_date.year > current_year + 1:
            raise ValidationError(f"{field_name} tiene un año inválido: {parsed_date.year}")
        
        return parsed_date
    except ValueError as e:
        raise ValidationError(f"{field_name} tiene formato de fecha/hora inválido: {str(e)}")


def validate_traffic_bytes(traffic: Union[str, int, float], field_name: str = "tráfico") -> int:
    """
    Valida tráfico de datos en bytes
    
    Args:
        traffic: Cantidad de tráfico en bytes
        field_name: Nombre del campo para errores
        
    Returns:
        Tráfico validado como entero
        
    Raises:
        ValidationError: Si el tráfico es inválido
    """
    if traffic is None or traffic == '' or traffic == 0:
        return 0
    
    try:
        traffic_int = int(float(traffic))
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} debe ser un número entero")
    
    # Validar que no sea negativo
    if traffic_int < 0:
        raise ValidationError(f"{field_name} no puede ser negativo")
    
    # Validar límite máximo razonable (100 GB = 107,374,182,400 bytes)
    if traffic_int > 107374182400:
        raise ValidationError(f"{field_name} excede el límite máximo de 100 GB")
    
    return traffic_int


def validate_movistar_technology(technology: str, field_name: str = "tecnología") -> str:
    """
    Valida tecnología de red MOVISTAR
    
    Args:
        technology: Tecnología de red
        field_name: Nombre del campo para errores
        
    Returns:
        Tecnología validada
        
    Raises:
        ValidationError: Si la tecnología es inválida
    """
    if not technology:
        raise ValidationError(f"{field_name} es requerido")
    
    technology_clean = str(technology).strip().upper()
    
    # Tecnologías válidas para MOVISTAR
    valid_technologies = ['LTE', '3G', 'UMTS', 'GSM', '2G', '4G', '5G']
    
    if technology_clean not in valid_technologies:
        raise ValidationError(f"{field_name} debe ser uno de: {', '.join(valid_technologies)}")
    
    return technology_clean


def validate_movistar_provider(provider: str, field_name: str = "proveedor") -> str:
    """
    Valida proveedor de infraestructura MOVISTAR
    
    Args:
        provider: Proveedor de infraestructura
        field_name: Nombre del campo para errores
        
    Returns:
        Proveedor validado
        
    Raises:
        ValidationError: Si el proveedor es inválido
    """
    if not provider:
        raise ValidationError(f"{field_name} es requerido")
    
    provider_clean = str(provider).strip().upper()
    
    # Proveedores comunes para MOVISTAR
    valid_providers = ['HUAWEI', 'ERICSSON', 'NOKIA', 'ALCATEL', 'ZTE', 'SAMSUNG']
    
    if provider_clean not in valid_providers:
        # Permitir otros proveedores pero validar longitud
        if len(provider_clean) > 50:
            raise ValidationError(f"{field_name} no puede exceder 50 caracteres")
    
    return provider_clean


def validate_movistar_region_data(department: str, locality: str, region: str) -> Tuple[str, str, str]:
    """
    Valida datos de región MOVISTAR (departamento, localidad, región)
    
    Args:
        department: Departamento
        locality: Localidad  
        region: Región
        
    Returns:
        Tupla con datos validados
        
    Raises:
        ValidationError: Si los datos son inválidos
    """
    # Validar departamento
    if not department:
        raise ValidationError("departamento es requerido")
    department_clean = validate_required_string(department, 'departamento', max_length=100)
    
    # Validar localidad
    if not locality:
        raise ValidationError("localidad es requerida")
    locality_clean = validate_required_string(locality, 'localidad', max_length=100)
    
    # Validar región
    if not region:
        raise ValidationError("región es requerida")
    region_clean = validate_required_string(region, 'región', max_length=100)
    
    return department_clean, locality_clean, region_clean


def validate_movistar_datos_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida un registro completo de datos por celda MOVISTAR
    
    Args:
        record: Diccionario con datos del registro MOVISTAR
        
    Returns:
        Registro validado
        
    Raises:
        ValidationError: Si los datos son inválidos
    """
    validated_record = {}
    
    # Validar número telefónico
    validated_record['numero_que_navega'] = validate_colombian_phone_number(
        record.get('numero_que_navega'), 'numero_que_navega'
    )
    
    # Validar ruta entrante
    ruta_entrante = record.get('ruta_entrante')
    if ruta_entrante is not None:
        validated_record['ruta_entrante'] = str(ruta_entrante).strip()
    
    # Validar celda
    validated_record['celda'] = validate_cell_id(
        record.get('celda'), 'celda'
    )
    
    # Validar tráfico de subida y bajada
    validated_record['trafico_de_subida'] = validate_traffic_bytes(
        record.get('trafico_de_subida'), 'trafico_de_subida'
    )
    
    validated_record['trafico_de_bajada'] = validate_traffic_bytes(
        record.get('trafico_de_bajada'), 'trafico_de_bajada'
    )
    
    # Validar fechas de inicio y fin de sesión
    validated_record['fecha_hora_inicio_sesion'] = validate_movistar_date_format(
        record.get('fecha_hora_inicio_sesion'), 'fecha_hora_inicio_sesion'
    )
    
    fecha_fin = record.get('fecha_hora_fin_sesion')
    if fecha_fin:
        validated_record['fecha_hora_fin_sesion'] = validate_movistar_date_format(
            fecha_fin, 'fecha_hora_fin_sesion'
        )
    
    # Validar duración
    validated_record['duracion'] = validate_call_duration(
        record.get('duracion'), 'duracion'
    )
    
    # Validar tipo de tecnología
    tipo_tecnologia = record.get('tipo_tecnologia')
    if tipo_tecnologia is not None:
        validated_record['tipo_tecnologia'] = str(tipo_tecnologia).strip()
    
    # Validar coordenadas
    lat, lon = validate_coordinates(
        record.get('latitud_n'), record.get('longitud_w')
    )
    validated_record['latitud_n'] = lat
    validated_record['longitud_w'] = lon
    
    # Validar proveedor y tecnología
    validated_record['proveedor'] = validate_movistar_provider(
        record.get('proveedor'), 'proveedor'
    )
    
    validated_record['tecnologia'] = validate_movistar_technology(
        record.get('tecnologia'), 'tecnologia'
    )
    
    # Validar datos de región
    department, locality, region = validate_movistar_region_data(
        record.get('departamento', ''),
        record.get('localidad', ''),
        record.get('region', '')
    )
    validated_record['departamento'] = department
    validated_record['localidad'] = locality
    validated_record['region'] = region
    
    # Validar descripción y dirección
    descripcion = record.get('descripcion')
    if descripcion:
        validated_record['descripcion'] = validate_required_string(
            descripcion, 'descripcion', max_length=200
        )
    
    direccion = record.get('direccion')
    if direccion:
        validated_record['direccion'] = validate_required_string(
            direccion, 'direccion', max_length=200
        )
    
    # Validar celda_ (campo adicional)
    celda_adicional = record.get('celda_')
    if celda_adicional:
        validated_record['celda_'] = validate_cell_id(
            celda_adicional, 'celda_'
        )
    
    return validated_record


def validate_movistar_llamadas_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida un registro completo de llamadas salientes MOVISTAR
    
    Args:
        record: Diccionario con datos del registro de llamada MOVISTAR
        
    Returns:
        Registro validado
        
    Raises:
        ValidationError: Si los datos son inválidos
    """
    validated_record = {}
    
    # Validar números telefónicos
    validated_record['numero_que_contesta'] = validate_colombian_phone_number(
        record.get('numero_que_contesta'), 'numero_que_contesta'
    )
    
    validated_record['numero_que_marca'] = validate_colombian_phone_number(
        record.get('numero_que_marca'), 'numero_que_marca'
    )
    
    # Validar número marcado (puede ser diferente al que marca)
    numero_marcado = record.get('numero_marcado')
    if numero_marcado:
        validated_record['numero_marcado'] = validate_colombian_phone_number(
            numero_marcado, 'numero_marcado'
        )
    
    # Validar seriales (opcionales)
    serial_destino = record.get('serial_destino')
    if serial_destino and str(serial_destino).strip() not in ["''", '']:
        validated_record['serial_destino'] = str(serial_destino).strip()
    
    serial_origen = record.get('serial_origen')
    if serial_origen and str(serial_origen).strip() not in ["''", '']:
        validated_record['serial_origen'] = str(serial_origen).strip()
    
    # Validar duración
    validated_record['duracion'] = validate_call_duration(
        record.get('duracion'), 'duracion'
    )
    
    # Validar rutas
    ruta_entrante = record.get('ruta_entrante')
    if ruta_entrante is not None:
        validated_record['ruta_entrante'] = str(ruta_entrante).strip()
    
    ruta_saliente = record.get('ruta_saliente')
    if ruta_saliente is not None:
        validated_record['ruta_saliente'] = str(ruta_saliente).strip()
    
    # Validar transferencia
    transferencia = record.get('transferencia')
    if transferencia and str(transferencia).strip() not in ["''", '']:
        validated_record['transferencia'] = str(transferencia).strip()
    
    # Validar fechas de inicio y fin de llamada
    validated_record['fecha_hora_inicio_llamada'] = validate_movistar_date_format(
        record.get('fecha_hora_inicio_llamada'), 'fecha_hora_inicio_llamada'
    )
    
    fecha_fin = record.get('fecha_hora_fin_llamada')
    if fecha_fin:
        validated_record['fecha_hora_fin_llamada'] = validate_movistar_date_format(
            fecha_fin, 'fecha_hora_fin_llamada'
        )
    
    # Validar switch
    switch = record.get('switch')
    if switch:
        validated_record['switch'] = str(switch).strip()
    
    # Validar celdas origen y destino
    celda_origen = record.get('celda_origen')
    if celda_origen:
        validated_record['celda_origen'] = validate_cell_id(
            celda_origen, 'celda_origen'
        )
    
    celda_destino = record.get('celda_destino')
    if celda_destino and str(celda_destino).strip() not in ["''", '']:
        validated_record['celda_destino'] = validate_cell_id(
            celda_destino, 'celda_destino'
        )
    
    # Validar coordenadas
    lat, lon = validate_coordinates(
        record.get('latitud_n'), record.get('longitud_w')
    )
    validated_record['latitud_n'] = lat
    validated_record['longitud_w'] = lon
    
    # Validar proveedor y tecnología
    validated_record['proveedor'] = validate_movistar_provider(
        record.get('proveedor'), 'proveedor'
    )
    
    validated_record['tecnologia'] = validate_movistar_technology(
        record.get('tecnologia'), 'tecnologia'
    )
    
    # Validar datos de región
    department, locality, region = validate_movistar_region_data(
        record.get('departamento', ''),
        record.get('localidad', ''),
        record.get('region', '')
    )
    validated_record['departamento'] = department
    validated_record['localidad'] = locality
    validated_record['region'] = region
    
    # Validar descripción y dirección
    descripcion = record.get('descripcion')
    if descripcion:
        validated_record['descripcion'] = validate_required_string(
            descripcion, 'descripcion', max_length=200
        )
    
    direccion = record.get('direccion')
    if direccion:
        validated_record['direccion'] = validate_required_string(
            direccion, 'direccion', max_length=200
        )
    
    # Validar celda y azimut
    celda = record.get('celda')
    if celda:
        validated_record['celda'] = validate_cell_id(celda, 'celda')
    
    azimut = record.get('azimut')
    if azimut is not None:
        try:
            azimut_int = int(float(azimut))
            if azimut_int < 0 or azimut_int > 360:
                raise ValidationError("azimut debe estar entre 0 y 360 grados")
            validated_record['azimut'] = azimut_int
        except (ValueError, TypeError):
            raise ValidationError("azimut debe ser un número entero")
    
    return validated_record


# ==============================================================================
# VALIDADORES ESPECÍFICOS PARA OPERADOR WOM
# ==============================================================================

def validate_wom_cellular_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida un registro de datos celulares de WOM.
    
    WOM maneja datos celulares con información técnica avanzada:
    - IMSI, IMEI para identificación de dispositivos
    - BTS_ID, TAC para información de infraestructura
    - Coordenadas con formato de comas decimales
    - Tecnología específica: WOM 3G, WOM 4G
    
    Args:
        record: Diccionario con datos del registro WOM
        
    Returns:
        Diccionario con datos validados
        
    Raises:
        ValidationError: Si la validación falla
    """
    if not isinstance(record, dict):
        raise ValidationError("El registro debe ser un diccionario")
    
    validated_record = {}
    
    # Validar tecnología del operador
    operator_tech = record.get('operador_tecnologia', '').strip()
    if not operator_tech:
        raise ValidationError("operador_tecnologia es requerido")
    
    # WOM acepta: WOM 3G, WOM 4G
    valid_wom_techs = ['WOM 3G', 'WOM 4G']
    if operator_tech not in valid_wom_techs:
        raise ValidationError(f"operador_tecnologia debe ser uno de: {', '.join(valid_wom_techs)}")
    
    validated_record['operador_tecnologia'] = operator_tech
    
    # Validar número de teléfono
    numero_origen = validate_colombian_phone_number(
        record.get('numero_origen'), 'numero_origen'
    )
    validated_record['numero_origen'] = numero_origen
    
    # Validar fechas
    fecha_inicio = validate_wom_datetime(
        record.get('fecha_hora_inicio'), 'fecha_hora_inicio'
    )
    validated_record['fecha_hora_inicio'] = fecha_inicio
    
    fecha_fin = validate_wom_datetime(
        record.get('fecha_hora_fin'), 'fecha_hora_fin'
    )
    validated_record['fecha_hora_fin'] = fecha_fin
    
    # Validar duración
    duracion = record.get('duracion_seg')
    if duracion is not None:
        validated_record['duracion_seg'] = validate_duration_seconds(duracion, 'duracion_seg')
    
    # Validar campos técnicos específicos WOM
    bts_id = record.get('bts_id')
    if bts_id is not None:
        validated_record['bts_id'] = validate_positive_integer(bts_id, 'bts_id')
    
    tac = record.get('tac')
    if tac is not None:
        validated_record['tac'] = validate_positive_integer(tac, 'tac')
    
    cell_id_voz = record.get('cell_id_voz')
    if cell_id_voz is not None:
        validated_record['cell_id_voz'] = validate_positive_integer(cell_id_voz, 'cell_id_voz')
    
    sector = record.get('sector')
    if sector is not None:
        validated_record['sector'] = validate_positive_integer(sector, 'sector')
    
    # Validar datos de tráfico
    up_data = record.get('up_data_bytes')
    if up_data is not None:
        validated_record['up_data_bytes'] = validate_non_negative_integer(up_data, 'up_data_bytes')
    
    down_data = record.get('down_data_bytes')
    if down_data is not None:
        validated_record['down_data_bytes'] = validate_non_negative_integer(down_data, 'down_data_bytes')
    
    # Validar coordenadas geográficas
    lat = record.get('latitud')
    if lat is not None:
        validated_record['latitud'] = validate_latitude(lat, 'latitud')
    
    lon = record.get('longitud')
    if lon is not None:
        validated_record['longitud'] = validate_longitude(lon, 'longitud')
    
    # Validar campos de texto opcionales
    optional_text_fields = [
        'operador_ran', 'imsi', 'localizacion_usuario', 'nombre_antena',
        'direccion', 'localidad', 'ciudad', 'departamento', 'regional',
        'entorno_geografico', 'uli'
    ]
    
    for field in optional_text_fields:
        value = record.get(field)
        if value is not None and str(value).strip():
            validated_record[field] = str(value).strip()
    
    return validated_record


def validate_wom_call_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida un registro de llamadas de WOM.
    
    WOM maneja llamadas entrantes y salientes en un solo archivo diferenciadas
    por el campo SENTIDO ('ENTRANTE'/'SALIENTE').
    
    Args:
        record: Diccionario con datos del registro WOM
        
    Returns:
        Diccionario con datos validados
        
    Raises:
        ValidationError: Si la validación falla
    """
    if not isinstance(record, dict):
        raise ValidationError("El registro debe ser un diccionario")
    
    validated_record = {}
    
    # Validar tecnología del operador
    operator_tech = record.get('operador_tecnologia', '').strip()
    if not operator_tech:
        raise ValidationError("operador_tecnologia es requerido")
    
    # WOM acepta: WOM 3G, WOM 4G
    valid_wom_techs = ['WOM 3G', 'WOM 4G']
    if operator_tech not in valid_wom_techs:
        raise ValidationError(f"operador_tecnologia debe ser uno de: {', '.join(valid_wom_techs)}")
    
    validated_record['operador_tecnologia'] = operator_tech
    
    # Validar números de teléfono
    numero_origen = validate_colombian_phone_number(
        record.get('numero_origen'), 'numero_origen'
    )
    validated_record['numero_origen'] = numero_origen
    
    numero_destino = record.get('numero_destino')
    if numero_destino:
        validated_record['numero_destino'] = validate_colombian_phone_number(
            numero_destino, 'numero_destino'
        )
    
    # Validar sentido de llamada
    sentido = record.get('sentido', '').strip().upper()
    if sentido not in ['ENTRANTE', 'SALIENTE']:
        raise ValidationError("sentido debe ser 'ENTRANTE' o 'SALIENTE'")
    validated_record['sentido'] = sentido
    
    # Validar fechas
    fecha_inicio = validate_wom_datetime(
        record.get('fecha_hora_inicio'), 'fecha_hora_inicio'
    )
    validated_record['fecha_hora_inicio'] = fecha_inicio
    
    fecha_fin = validate_wom_datetime(
        record.get('fecha_hora_fin'), 'fecha_hora_fin'
    )
    validated_record['fecha_hora_fin'] = fecha_fin
    
    # Validar duración
    duracion = record.get('duracion_seg')
    if duracion is not None:
        validated_record['duracion_seg'] = validate_duration_seconds(duracion, 'duracion_seg')
    
    # Validar campos técnicos específicos WOM
    bts_id = record.get('bts_id')
    if bts_id is not None:
        validated_record['bts_id'] = validate_positive_integer(bts_id, 'bts_id')
    
    tac = record.get('tac')
    if tac is not None:
        validated_record['tac'] = validate_positive_integer(tac, 'tac')
    
    cell_id_voz = record.get('cell_id_voz')
    if cell_id_voz is not None:
        validated_record['cell_id_voz'] = validate_positive_integer(cell_id_voz, 'cell_id_voz')
    
    sector = record.get('sector')
    if sector is not None:
        validated_record['sector'] = validate_positive_integer(sector, 'sector')
    
    # Validar coordenadas geográficas
    lat = record.get('latitud')
    if lat is not None:
        validated_record['latitud'] = validate_latitude(lat, 'latitud')
    
    lon = record.get('longitud')
    if lon is not None:
        validated_record['longitud'] = validate_longitude(lon, 'longitud')
    
    # Validar campos de texto opcionales
    optional_text_fields = [
        'operador_ran_origen', 'user_location_info', 'access_network_information',
        'imei', 'imsi', 'nombre_antena', 'direccion', 'localidad', 'ciudad', 'departamento'
    ]
    
    for field in optional_text_fields:
        value = record.get(field)
        if value is not None and str(value).strip():
            validated_record[field] = str(value).strip()
    
    return validated_record


def validate_wom_datetime(value: Any, field_name: str) -> datetime:
    """
    Valida y convierte fechas en formato WOM (dd/mm/yyyy HH:MM).
    
    Args:
        value: Valor a validar
        field_name: Nombre del campo para errores
        
    Returns:
        Objeto datetime validado
        
    Raises:
        ValidationError: Si la validación falla
    """
    if value is None:
        raise ValidationError(f"{field_name} es requerido")
    
    if isinstance(value, datetime):
        return value
    
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} debe ser una fecha en formato string")
    
    value = value.strip()
    if not value:
        raise ValidationError(f"{field_name} no puede estar vacío")
    
    # Intentar parsear formato WOM: dd/mm/yyyy HH:MM
    try:
        return datetime.strptime(value, '%d/%m/%Y %H:%M')
    except ValueError:
        pass
    
    # Intentar formato alternativo con segundos
    try:
        return datetime.strptime(value, '%d/%m/%Y %H:%M:%S')
    except ValueError:
        pass
    
    # Intentar formato ISO como último recurso
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        pass
    
    raise ValidationError(
        f"{field_name} debe tener formato 'dd/mm/yyyy HH:MM' o 'dd/mm/yyyy HH:MM:SS'"
    )