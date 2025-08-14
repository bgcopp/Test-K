#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
L2 HASH IMPROVEMENT - Algoritmo mejorado para detección de duplicados
==================================================================
Mejora el algoritmo de hash para incluir TODOS los campos relevantes
Esto permite detectar duplicados exactos mientras preserva variaciones legítimas

Solution Architect Level 2
Fecha: 2025-08-13
"""

import hashlib
import json
from typing import Dict, Any

def calculate_improved_record_hash(normalized_data: Dict[str, Any]) -> str:
    """
    Calcula un hash único mejorado para el registro normalizado.
    
    VERSIÓN L2 MEJORADA:
    - Incluye TODOS los campos relevantes para detectar duplicados exactos
    - Permite múltiples sesiones legítimas del mismo usuario/celda/tiempo
    - Optimizado para patrones de telecomunicaciones reales
    
    Args:
        normalized_data (Dict[str, Any]): Datos normalizados
        
    Returns:
        str: Hash SHA256 del registro completo
    """
    # Hash mejorado L2: incluir TODOS los campos relevantes
    hash_components = [
        # Identificación básica
        str(normalized_data.get('file_upload_id', '')),
        str(normalized_data.get('mission_id', '')),
        str(normalized_data.get('operator', '')),
        
        # Información temporal y usuario
        str(normalized_data.get('numero_telefono', '')),
        str(normalized_data.get('fecha_hora_inicio', '')),
        str(normalized_data.get('fecha_hora_fin', '')),
        str(normalized_data.get('duracion_segundos', '')),
        
        # Información técnica de red
        str(normalized_data.get('celda_id', '')),
        str(normalized_data.get('lac_tac', '')),
        str(normalized_data.get('tecnologia', '')),
        str(normalized_data.get('tipo_conexion', '')),
        str(normalized_data.get('calidad_senal', '')),
        
        # Datos de tráfico
        str(normalized_data.get('trafico_subida_bytes', '')),
        str(normalized_data.get('trafico_bajada_bytes', '')),
        
        # Información geográfica
        str(normalized_data.get('latitud', '')),
        str(normalized_data.get('longitud', '')),
        
        # Datos específicos del operador (campos clave)
        extract_operator_specific_hash(normalized_data.get('operator_specific_data', ''))
    ]
    
    hash_string = '|'.join(hash_components)
    return hashlib.sha256(hash_string.encode('utf-8')).hexdigest()

def extract_operator_specific_hash(operator_specific_data: str) -> str:
    """
    Extrae campos clave del JSON de datos específicos para hash mejorado.
    
    Args:
        operator_specific_data (str): JSON con datos específicos del operador
        
    Returns:
        str: String con campos clave para hash
    """
    if not operator_specific_data:
        return ''
    
    try:
        data = json.loads(operator_specific_data)
        
        key_fields = []
        
        # Campos de metadatos específicos
        if 'claro_metadata' in data:
            claro_meta = data['claro_metadata']
            key_fields.extend([
                str(claro_meta.get('data_type', '')),
                str(claro_meta.get('file_format', ''))
            ])
        
        # Campos originales únicos (excluir los ya incluidos en hash principal)
        if 'original_fields' in data:
            orig_fields = data['original_fields']
            excluded_fields = {'numero', 'fecha_trafico', 'tipo_cdr', 'celda_decimal', 'lac_decimal'}
            for key, value in orig_fields.items():
                if key not in excluded_fields and value is not None:
                    key_fields.append(f"{key}:{str(value)}")
        
        return '|'.join(sorted(key_fields))  # Ordenar para consistencia
        
    except (json.JSONDecodeError, KeyError, TypeError):
        return ''

def validate_hash_improvement(test_records):
    """
    Valida que el hash mejorado funcione correctamente con datos de prueba
    
    Args:
        test_records: Lista de registros de prueba
    """
    print("VALIDACIÓN HASH L2 MEJORADO")
    print("=" * 50)
    
    hashes = []
    for i, record in enumerate(test_records, 1):
        hash_val = calculate_improved_record_hash(record)
        hashes.append(hash_val)
        print(f"Registro {i}: {hash_val[:16]}...")
    
    unique_hashes = len(set(hashes))
    total_records = len(test_records)
    
    print(f"\nResultados:")
    print(f"Total registros: {total_records}")
    print(f"Hashes únicos: {unique_hashes}")
    print(f"Duplicados detectados: {total_records - unique_hashes}")
    
    return unique_hashes == total_records

if __name__ == "__main__":
    # Test con datos de ejemplo
    test_data = [
        {
            'file_upload_id': 'file1',
            'numero_telefono': '573123456789',
            'fecha_hora_inicio': '2024-04-19 08:00:00',
            'celda_id': '175462',
            'trafico_subida_bytes': 0,
            'trafico_bajada_bytes': 0,
            'operator_specific_data': '{"claro_metadata": {"data_type": "cellular"}}'
        },
        {
            'file_upload_id': 'file1', 
            'numero_telefono': '573123456789',
            'fecha_hora_inicio': '2024-04-19 08:00:00',
            'celda_id': '175462',
            'trafico_subida_bytes': 1024,  # Diferente tráfico
            'trafico_bajada_bytes': 2048,
            'operator_specific_data': '{"claro_metadata": {"data_type": "cellular"}}'
        }
    ]
    
    validate_hash_improvement(test_data)