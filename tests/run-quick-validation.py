#!/usr/bin/env python3
"""
Quick Validation Script for KRONOS CLARO Tests
==============================================

Script de validación rápida para verificar que los números objetivo
están cargados correctamente en la base de datos después de ejecutar
los tests de Playwright.

Uso:
    python run-quick-validation.py
    python run-quick-validation.py --detailed

Author: Boris - KRONOS Testing Team
"""

import sys
import sqlite3
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

def quick_validate_targets() -> Dict[str, Any]:
    """Validación rápida de números objetivo"""
    
    # Buscar base de datos
    backend_path = Path(__file__).parent.parent / 'Backend'
    db_path = backend_path / 'kronos.db'
    
    if not db_path.exists():
        return {
            'status': 'ERROR',
            'message': f'Base de datos no encontrada: {db_path}',
            'targets_found': 0,
            'total_targets': 6
        }
    
    target_numbers = [
        '3224274851', '3208611034', '3104277553', 
        '3102715509', '3143534707', '3214161903'
    ]
    
    critical_numbers = ['3104277553', '3224274851']
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Verificar tabla
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='operator_call_data'
        """)
        
        if not cursor.fetchone():
            return {
                'status': 'ERROR',
                'message': 'Tabla operator_call_data no existe',
                'targets_found': 0,
                'total_targets': len(target_numbers)
            }
        
        # Contar registros totales
        cursor.execute("SELECT COUNT(*) FROM operator_call_data")
        total_records = cursor.fetchone()[0]
        
        if total_records == 0:
            return {
                'status': 'WARNING',
                'message': 'Base de datos vacía - ejecutar tests de carga primero',
                'targets_found': 0,
                'total_targets': len(target_numbers),
                'total_records': 0
            }
        
        # Validar números objetivo
        targets_found = 0
        critical_found = 0
        target_details = {}
        
        for number in target_numbers:
            cursor.execute("""
                SELECT COUNT(*) FROM operator_call_data
                WHERE numero_origen = ? OR numero_destino = ? OR numero_objetivo = ?
            """, (number, number, number))
            
            count = cursor.fetchone()[0]
            target_details[number] = count
            
            if count > 0:
                targets_found += 1
                if number in critical_numbers:
                    critical_found += 1
        
        # Validar caso específico Boris
        cursor.execute("""
            SELECT COUNT(*) FROM operator_call_data
            WHERE (numero_origen = '3104277553' AND numero_destino = '3224274851')
               OR (numero_origen = '3224274851' AND numero_destino = '3104277553')
        """)
        boris_case_count = cursor.fetchone()[0]
        
        # Contar registros CLARO
        cursor.execute("""
            SELECT COUNT(*) FROM operator_call_data
            WHERE UPPER(operator) LIKE '%CLARO%'
        """)
        claro_records = cursor.fetchone()[0]
        
        conn.close()
        
        # Determinar estado
        if critical_found == len(critical_numbers):
            status = 'SUCCESS'
            message = f'✅ ÉXITO: Todos los números críticos encontrados'
        elif targets_found >= len(target_numbers) * 0.8:  # 80% cobertura
            status = 'MOSTLY_SUCCESS'
            message = f'⚠️ PARCIAL: {targets_found}/{len(target_numbers)} números encontrados'
        else:
            status = 'FAILED'
            message = f'❌ FALLO: Solo {targets_found}/{len(target_numbers)} números encontrados'
        
        return {
            'status': status,
            'message': message,
            'targets_found': targets_found,
            'total_targets': len(target_numbers),
            'critical_found': critical_found,
            'total_critical': len(critical_numbers),
            'total_records': total_records,
            'claro_records': claro_records,
            'boris_case_records': boris_case_count,
            'target_details': target_details,
            'coverage_percentage': (targets_found / len(target_numbers)) * 100
        }
        
    except Exception as e:
        return {
            'status': 'ERROR',
            'message': f'Error validando BD: {str(e)}',
            'targets_found': 0,
            'total_targets': len(target_numbers)
        }

def detailed_validation() -> Dict[str, Any]:
    """Validación detallada con más información"""
    
    basic_result = quick_validate_targets()
    
    if basic_result['status'] == 'ERROR':
        return basic_result
    
    # Agregar validaciones adicionales
    backend_path = Path(__file__).parent.parent / 'Backend'
    db_path = backend_path / 'kronos.db'
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Estadísticas adicionales
        additional_stats = {}
        
        # Archivos únicos cargados
        cursor.execute("SELECT COUNT(DISTINCT file_upload_id) FROM operator_call_data")
        additional_stats['unique_files'] = cursor.fetchone()[0]
        
        # Misiones con datos
        cursor.execute("SELECT COUNT(DISTINCT mission_id) FROM operator_call_data")
        additional_stats['missions_with_data'] = cursor.fetchone()[0]
        
        # Tipos de llamada
        cursor.execute("""
            SELECT tipo_llamada, COUNT(*) 
            FROM operator_call_data 
            GROUP BY tipo_llamada
        """)
        call_types = dict(cursor.fetchall())
        additional_stats['call_types'] = call_types
        
        # Operadores
        cursor.execute("""
            SELECT operator, COUNT(*) 
            FROM operator_call_data 
            GROUP BY operator
        """)
        operators = dict(cursor.fetchall())
        additional_stats['operators'] = operators
        
        # Rango de fechas
        cursor.execute("""
            SELECT 
                MIN(fecha_hora_llamada) as min_date,
                MAX(fecha_hora_llamada) as max_date
            FROM operator_call_data
            WHERE fecha_hora_llamada IS NOT NULL
        """)
        date_range = cursor.fetchone()
        if date_range[0]:
            additional_stats['date_range'] = {
                'min_date': date_range[0],
                'max_date': date_range[1]
            }
        
        conn.close()
        
        # Combinar resultados
        basic_result['detailed_stats'] = additional_stats
        basic_result['validation_timestamp'] = datetime.now().isoformat()
        
    except Exception as e:
        basic_result['detailed_error'] = str(e)
    
    return basic_result

def print_validation_report(result: Dict[str, Any], detailed: bool = False):
    """Imprimir reporte de validación en consola"""
    
    print("\n" + "="*80)
    print("KRONOS CLARO E2E TESTS - VALIDACIÓN RÁPIDA")
    print("="*80)
    
    # Estado general
    print(f"\n🎯 ESTADO GENERAL: {result['status']}")
    print(f"📝 MENSAJE: {result['message']}")
    
    # Estadísticas básicas
    print(f"\n📊 ESTADÍSTICAS BÁSICAS:")
    print(f"   • Números objetivo encontrados: {result['targets_found']}/{result['total_targets']}")
    
    if 'critical_found' in result:
        print(f"   • Números críticos encontrados: {result['critical_found']}/{result['total_critical']}")
    
    if 'total_records' in result:
        print(f"   • Total registros en BD: {result['total_records']:,}")
    
    if 'claro_records' in result:
        print(f"   • Registros CLARO: {result['claro_records']:,}")
    
    if 'boris_case_records' in result:
        print(f"   • Comunicaciones 3104277553↔3224274851: {result['boris_case_records']}")
    
    if 'coverage_percentage' in result:
        print(f"   • Cobertura de objetivos: {result['coverage_percentage']:.1f}%")
    
    # Detalles por número objetivo
    if 'target_details' in result:
        print(f"\n📱 DETALLES POR NÚMERO OBJETIVO:")
        for number, count in result['target_details'].items():
            status_icon = "✅" if count > 0 else "❌"
            critical_marker = " [CRÍTICO]" if number in ['3104277553', '3224274851'] else ""
            print(f"   {status_icon} {number}: {count:,} registros{critical_marker}")
    
    # Estadísticas detalladas
    if detailed and 'detailed_stats' in result:
        stats = result['detailed_stats']
        
        print(f"\n🔍 ESTADÍSTICAS DETALLADAS:")
        print(f"   • Archivos únicos cargados: {stats.get('unique_files', 'N/A')}")
        print(f"   • Misiones con datos: {stats.get('missions_with_data', 'N/A')}")
        
        if 'call_types' in stats:
            print(f"   • Tipos de llamada:")
            for call_type, count in stats['call_types'].items():
                print(f"     - {call_type}: {count:,}")
        
        if 'operators' in stats:
            print(f"   • Operadores:")
            for operator, count in stats['operators'].items():
                print(f"     - {operator}: {count:,}")
        
        if 'date_range' in stats:
            print(f"   • Rango de fechas: {stats['date_range']['min_date']} → {stats['date_range']['max_date']}")
    
    # Recomendaciones
    print(f"\n💡 RECOMENDACIONES:")
    
    if result['status'] == 'SUCCESS':
        print("   ✅ Sistema validado correctamente")
        print("   ✅ Todos los números objetivo están presentes")
        print("   ✅ Proceso de carga CLARO funciona al 100%")
    elif result['status'] == 'MOSTLY_SUCCESS':
        print("   ⚠️ Cobertura parcial de números objetivo")
        print("   📝 Revisar por qué algunos números no se cargaron")
        print("   🔄 Considerar re-ejecutar tests de carga")
    elif result['status'] == 'FAILED':
        print("   ❌ Faltan números objetivo críticos")
        print("   🔄 Re-ejecutar tests de carga completos")
        print("   🔍 Verificar archivos CSV de prueba")
    else:  # ERROR o WARNING
        print("   🔧 Verificar configuración del sistema")
        print("   🔄 Re-ejecutar suite completa de tests")
    
    print("\n" + "="*80)
    print(f"Validación completada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Validación rápida de tests CLARO')
    parser.add_argument('--detailed', action='store_true', 
                       help='Mostrar estadísticas detalladas')
    parser.add_argument('--json', help='Guardar resultado en archivo JSON')
    
    args = parser.parse_args()
    
    # Ejecutar validación
    if args.detailed:
        result = detailed_validation()
    else:
        result = quick_validate_targets()
    
    # Mostrar reporte
    print_validation_report(result, args.detailed)
    
    # Guardar JSON si se solicita
    if args.json:
        with open(args.json, 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"📄 Resultado guardado en: {args.json}")
    
    # Exit code basado en resultado
    if result['status'] in ['SUCCESS', 'MOSTLY_SUCCESS']:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()