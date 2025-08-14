#!/usr/bin/env python3
"""
Script para verificar el estado detallado por operador
"""

from database.connection import get_db_connection

def main():
    print('=== ESTADO DETALLADO POR OPERADOR ===')

    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Obtener estadísticas detalladas por operador
        cursor.execute('''
            SELECT 
                operator,
                COUNT(*) as total_files,
                SUM(CASE WHEN processing_status = 'COMPLETED' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN processing_status = 'FAILED' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN processing_status = 'PENDING' THEN 1 ELSE 0 END) as pending,
                SUM(records_processed) as total_records,
                file_type
            FROM operator_data_sheets 
            GROUP BY operator, file_type
            ORDER BY operator, file_type
        ''')
        
        results = cursor.fetchall()
        current_operator = None
        
        for row in results:
            operator, total_files, completed, failed, pending, total_records, file_type = row
            
            if operator != current_operator:
                print(f'\n{operator}:')
                current_operator = operator
            
            status_icon = 'OK' if failed == 0 else 'WARNING' if failed < total_files else 'FAIL'
            print(f'  {file_type}: {total_files} archivos, {completed} OK, {failed} FAIL, {total_records or 0} registros [{status_icon}]')

    print('\n=== TIPOS DE ARCHIVOS SOPORTADOS ===')
    operators_info = [
        ('CLARO', ['CELLULAR_DATA', 'CALL_DATA']),
        ('MOVISTAR', ['CELLULAR_DATA', 'CALL_DATA']), 
        ('TIGO', ['CALL_DATA']),
        ('WOM', ['CELLULAR_DATA', 'CALL_DATA'])
    ]

    for operator, types in operators_info:
        print(f'{operator}: {len(types)} tipos -> {", ".join(types)}')

if __name__ == "__main__":
    main()