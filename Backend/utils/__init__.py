"""
KRONOS Backend Utils
===============================================================================
Módulo de utilidades del backend de KRONOS.
Expone validadores, helpers y funciones auxiliares.
"""

from utils.validators import (
    validate_email,
    validate_password_strength,
    validate_user_data,
    validate_role_data,
    validate_mission_data,
    validate_permissions_structure,
    validate_file_data,
    validate_cellular_data_record,
    validate_operator_data_record,
    ValidationError
)

from utils.helpers import (
    generate_id,
    generate_user_id,
    generate_role_id,
    generate_mission_id,
    generate_target_id,
    decode_base64_file,
    create_file_like_object,
    read_excel_file,
    read_csv_file,
    clean_dataframe,
    map_user_to_frontend,
    map_mission_to_frontend,
    map_cellular_record_to_frontend,
    map_target_record_to_frontend,
    serialize_for_json,
    safe_json_dumps,
    create_error_response,
    create_success_response,
    get_current_timestamp,
    normalize_column_names,
    validate_dataframe_not_empty,
    chunk_list,
    safe_get_nested,
    calculate_distance
)

__all__ = [
    # Validators
    'validate_email',
    'validate_password_strength',
    'validate_user_data',
    'validate_role_data',
    'validate_mission_data',
    'validate_permissions_structure',
    'validate_file_data',
    'validate_cellular_data_record',
    'validate_operator_data_record',
    'ValidationError',
    
    # Helpers
    'generate_id',
    'generate_user_id',
    'generate_role_id',
    'generate_mission_id',
    'generate_target_id',
    'decode_base64_file',
    'create_file_like_object',
    'read_excel_file',
    'read_csv_file',
    'clean_dataframe',
    'map_user_to_frontend',
    'map_mission_to_frontend',
    'map_cellular_record_to_frontend',
    'map_target_record_to_frontend',
    'serialize_for_json',
    'safe_json_dumps',
    'create_error_response',
    'create_success_response',
    'get_current_timestamp',
    'normalize_column_names',
    'validate_dataframe_not_empty',
    'chunk_list',
    'safe_get_nested',
    'calculate_distance'
]