"""
Analisis simple de numeros objetivo en BD
Boris - KRONOS Analysis
"""

import sqlite3
import json
from datetime import datetime

def analyze_target_numbers_simple():
    """Analiza el estado real de los numeros objetivo"""
    
    target_numbers = [
        '3224274851', '3208611034', '3104277553', 
        '3102715509', '3143534707', '3214161903'
    ]
    
    print("\n" + "="*70)
    print("ANALISIS SIMPLE DE NUMEROS OBJETIVO")
    print("="*70)
    
    results = {}
    
    try:
        conn = sqlite3.connect('kronos.db')
        cursor = conn.cursor()
        
        # Obtener total de registros
        cursor.execute("SELECT COUNT(*) FROM operator_call_data")
        total_records = cursor.fetchone()[0]
        print(f"\nTotal registros en BD: {total_records}")
        
        print(f"\nBUSQUEDA DE NUMEROS:")
        print("-" * 50)
        
        found_count = 0
        
        for number in target_numbers:
            # Busqueda exhaustiva
            cursor.execute("""
                SELECT COUNT(*) as total,
                       GROUP_CONCAT(DISTINCT operator) as operators,
                       GROUP_CONCAT(DISTINCT tipo_llamada) as tipos,
                       MIN(fecha_hora_llamada) as primera,
                       MAX(fecha_hora_llamada) as ultima
                FROM operator_call_data
                WHERE numero_origen = ? OR numero_destino = ? OR numero_objetivo = ?
                   OR numero_origen LIKE '%' || ? || '%' 
                   OR numero_destino LIKE '%' || ? || '%'
                   OR numero_objetivo LIKE '%' || ? || '%'
            """, (number, number, number, number, number, number))
            
            result = cursor.fetchone()
            total_found = result[0]
            
            if total_found > 0:
                found_count += 1
                status = "[ENCONTRADO]"
                print(f"{status} {number}: {total_found} registros")
                print(f"    Operadores: {result[1]}")
                print(f"    Tipos: {result[2]}")
                print(f"    Periodo: {result[3]} a {result[4]}")
                
                # Detalles especificos
                cursor.execute("""
                    SELECT numero_origen, numero_destino, numero_objetivo, 
                           celda_origen, celda_destino, fecha_hora_llamada
                    FROM operator_call_data
                    WHERE numero_origen = ? OR numero_destino = ? OR numero_objetivo = ?
                    LIMIT 3
                """, (number, number, number))
                
                details = cursor.fetchall()
                for i, detail in enumerate(details):
                    print(f"    Registro {i+1}: {detail[0]} -> {detail[1]} | Celdas: {detail[3]}->{detail[4]}")
            else:
                status = "[NO ENCONTRADO]"
                print(f"{status} {number}: 0 registros")
            
            results[number] = {
                'found': total_found > 0,
                'count': total_found,
                'operators': result[1] if result[1] else '',
                'tipos': result[2] if result[2] else ''
            }
            
            print()
        
        conn.close()
        
        print("="*70)
        print("RESUMEN FINAL")
        print("="*70)
        print(f"Numeros encontrados: {found_count}/{len(target_numbers)}")
        
        if found_count == len(target_numbers):
            print("\n*** EXITO TOTAL: TODOS LOS NUMEROS ESTAN EN LA BD ***")
        else:
            missing = [num for num, data in results.items() if not data['found']]
            print(f"\nNumeros faltantes: {', '.join(missing)}")
        
        # Caso especifico reportado
        print(f"\nCASO ESPECIFICO: 3104277553 -> 3224274851")
        cursor = sqlite3.connect('kronos.db')
        cursor.execute("""
            SELECT id, operator, fecha_hora_llamada, duracion_segundos,
                   celda_origen, celda_destino
            FROM operator_call_data
            WHERE numero_origen = '3104277553' AND numero_destino = '3224274851'
        """)
        
        specific_case = cursor.fetchall()
        if specific_case:
            print(f"[OK] Encontrado: {len(specific_case)} registro(s)")
            for record in specific_case:
                print(f"    ID: {record[0]}, {record[1]}, {record[2]}, {record[3]}s, Celdas: {record[4]}->{record[5]}")
        else:
            print("[ERROR] Caso especifico NO encontrado")
        
        cursor.close()
        
        # Guardar reporte simple
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_records': total_records,
            'found_count': found_count,
            'target_count': len(target_numbers),
            'success': found_count == len(target_numbers),
            'results': results
        }
        
        report_file = f"analisis_simple_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nReporte guardado: {report_file}")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    analyze_target_numbers_simple()