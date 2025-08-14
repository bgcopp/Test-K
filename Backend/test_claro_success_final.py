#!/usr/bin/env python3
"""
Test final específico para validar que uploads exitosos de CLARO funcionan correctamente
"""

import sys
import os
import base64

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import get_db_connection
from services.operator_data_service import upload_operator_data

def test_successful_claro_upload():
    """Test con datos CLARO correctamente formateados"""
    
    # Obtener misión y usuario
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM missions LIMIT 1")
        mission_id = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM users LIMIT 1") 
        user_id = cursor.fetchone()[0]
    
    # Datos CLARO CELLULAR_DATA con formato correcto
    claro_data = """numero,fecha_trafico,tipo_cdr,celda_decimal,lac_decimal
573001234567,"2024-08-01 10:15:30",DATA,12345,678
573007654321,"2024-08-01 10:20:45",DATA,12346,679
573009876543,"2024-08-01 10:25:15",DATA,12347,680"""
    
    csv_base64 = base64.b64encode(claro_data.encode('utf-8')).decode('utf-8')
    
    result = upload_operator_data(
        file_data=csv_base64,
        file_name='claro_success_test.csv',
        mission_id=mission_id,
        operator='CLARO',
        file_type='CELLULAR_DATA',
        user_id=user_id
    )
    
    print("RESULTADO DEL TEST DE EXITO:")
    print(f"Success: {result.get('success')}")
    print(f"Campos presentes: {list(result.keys())}")
    
    if result.get('success'):
        print(f"sheetId: {result.get('sheetId')}")
        print(f"processedRecords: {result.get('processedRecords')}")
        print(f"warnings: {result.get('warnings')}")
        print(f"errors: {result.get('errors')}")
        
        # Validar que tiene todos los campos correctos
        has_all_fields = (
            'sheetId' in result and
            'processedRecords' in result and 
            'warnings' in result and
            'errors' in result and
            'file_upload_id' not in result and
            'records_processed' not in result
        )
        
        print(f"TODOS LOS CAMPOS CORRECTOS: {has_all_fields}")
        return has_all_fields
    else:
        print(f"Error: {result.get('error')}")
        return False

if __name__ == "__main__":
    success = test_successful_claro_upload()
    print(f"\nRESULTADO FINAL: {'EXITO' if success else 'FALLO'}")