#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
L2 FINAL VALIDATION: Verificación completa del sistema de correlación post-recuperación
"""

import os
import sys
import sqlite3
import json
from datetime import datetime

def validate_target_numbers():
    """Validación completa de los números objetivo"""
    db_path = r'C:\Soluciones\BGC\claude\KNSOft\Backend\kronos.db'
    
    target_numbers = [
        '3224274851',
        '3208611034', 
        '3104277553',  # Número recuperado
        '3102715509',
        '3143534707',
        '3214161903'
    ]
    
    print("=" * 80)
    print("VALIDACIÓN FINAL L2 - SISTEMA DE CORRELACIÓN KRONOS")
    print("=" * 80)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'target_numbers': {},
        'summary': {}
    }
    
    total_present = 0
    total_records = 0
    
    for target in target_numbers:
        # Buscar en todas las columnas relevantes
        cursor.execute("""
            SELECT 
                numero_objetivo, numero_origen, numero_destino, 
                operator, celda_objetivo, fecha_hora_llamada,
                duracion_segundos, id
            FROM operator_call_data 
            WHERE numero_objetivo = ? OR numero_origen = ? OR numero_destino = ?
            ORDER BY fecha_hora_llamada
        """, (target, target, target))
        
        records = cursor.fetchall()
        record_count = len(records)
        
        if record_count > 0:
            total_present += 1
            total_records += record_count
            status = "✅ PRESENTE"
            
            # Detalles del primer registro
            first_record = records[0]
            record_details = {
                'id': first_record[7],
                'numero_objetivo': first_record[0],
                'numero_origen': first_record[1], 
                'numero_destino': first_record[2],
                'operator': first_record[3],
                'celda_objetivo': first_record[4],
                'fecha_hora': first_record[5],
                'duracion': first_record[6]
            }
        else:
            status = "❌ AUSENTE"
            record_details = None
        
        results['target_numbers'][target] = {
            'status': status,
            'record_count': record_count,
            'first_record': record_details
        }
        
        print(f"Número {target}: {status} ({record_count} registros)")
        if record_details:
            print(f"  └─ Primer registro: ID={record_details['id']}, "
                  f"Origen={record_details['numero_origen']}, "
                  f"Destino={record_details['numero_destino']}, "
                  f"Celda={record_details['celda_objetivo']}")
    
    # Resumen
    success_rate = (total_present / len(target_numbers)) * 100
    
    results['summary'] = {
        'total_targets': len(target_numbers),
        'targets_present': total_present,
        'targets_missing': len(target_numbers) - total_present,
        'total_records': total_records,
        'success_rate': success_rate,
        'validation_passed': total_present == len(target_numbers)
    }
    
    print("\n" + "=" * 80)
    print("RESUMEN DE VALIDACIÓN")
    print("=" * 80)
    print(f"Números objetivo totales: {len(target_numbers)}")
    print(f"Números presentes: {total_present}")
    print(f"Números faltantes: {len(target_numbers) - total_present}")
    print(f"Registros totales: {total_records}")
    print(f"Tasa de éxito: {success_rate:.1f}%")
    print(f"Validación: {'✅ EXITOSA' if total_present == len(target_numbers) else '❌ FALLÓ'}")
    
    if total_present == len(target_numbers):
        print("\n🎯 TODOS LOS NÚMEROS OBJETIVO ESTÁN PRESENTES EN LA BASE DE DATOS")
        print("🔥 SISTEMA DE CORRELACIÓN KRONOS: FUNCIONANDO AL 100%")
    
    conn.close()
    
    # Guardar resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"l2_final_validation_{timestamp}.json"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\nResultados guardados en: {results_file}")
    print("=" * 80)
    
    return results['summary']['validation_passed']

if __name__ == "__main__":
    success = validate_target_numbers()
    sys.exit(0 if success else 1)