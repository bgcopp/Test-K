#!/usr/bin/env python3
"""
Validador de Resultados para Pruebas E2E CLARO
 
Script para validación detallada de resultados después de la ejecución
de pruebas Playwright. Genera reportes detallados y validaciones de BD.

Funcionalidades:
- Validación de carga exacta de 5,611 registros CLARO
- Verificación de números objetivo específicos
- Análisis de resultados de correlación
- Generación de reportes ejecutivos
- Comparación con criterios de éxito definidos

@author Testing Team KRONOS
@version 1.0.0
"""

import sqlite3
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

# Configuración de archivos y números objetivo
EXPECTED_TOTAL_RECORDS = 5611
TARGET_NUMBERS = [
    '3224274851', '3208611034', '3104277553', 
    '3102715509', '3143534707', '3214161903'
]

CLARO_FILES_EXPECTED = [
    {'name': '1-225211_LLAMADAS_ENTRANTES_POR_CELDA_545612_0.xlsx', 'records': 973},
    {'name': '1-225211_LLAMADAS_SALIENTES_POR_CELDA_545613_0.xlsx', 'records': 961},
    {'name': '2-225211_LLAMADAS_ENTRANTES_POR_CELDA_545614_0.xlsx', 'records': 1939},
    {'name': '2-225211_LLAMADAS_SALIENTES_POR_CELDA_545615_0.xlsx', 'records': 1738}
]

class ClaroResultsValidator:
    """Validador principal de resultados de pruebas CLARO"""
    
    def __init__(self, db_path: str = None):
        """
        Inicializar validador
        
        Args:
            db_path: Ruta a la base de datos SQLite (por defecto Backend/kronos.db)
        """
        if db_path is None:
            # Buscar base de datos en ubicación estándar
            current_dir = Path(__file__).parent.parent.parent
            self.db_path = current_dir / "Backend" / "kronos.db"
        else:
            self.db_path = Path(db_path)
            
        if not self.db_path.exists():
            raise FileNotFoundError(f"Base de datos no encontrada: {self.db_path}")
            
        self.report_data = {}
        self.validation_results = {}
        
    def connect_database(self) -> sqlite3.Connection:
        """Crear conexión a la base de datos"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
        
    def validate_claro_records_count(self) -> Dict[str, Any]:
        """
        Validar conteo exacto de registros CLARO cargados
        
        Returns:
            Dict con resultados de validación de conteo
        """
        print("🔢 Validando conteo de registros CLARO...")
        
        try:
            with self.connect_database() as conn:
                cursor = conn.cursor()
                
                # Contar registros de llamadas CLARO
                cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM operator_call_data 
                    WHERE operator = 'CLARO'
                """)
                call_data_count = cursor.fetchone()['count']
                
                # Contar registros de datos celulares CLARO
                cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM operator_cellular_data 
                    WHERE operator = 'CLARO'
                """)
                cellular_data_count = cursor.fetchone()['count']
                
                total_count = call_data_count + cellular_data_count
                
                # Distribución por dirección de llamadas
                cursor.execute("""
                    SELECT 
                        CASE 
                            WHEN LOWER(direction) LIKE '%entrant%' OR LOWER(direction) = 'entrante' THEN 'entrantes'
                            WHEN LOWER(direction) LIKE '%salien%' OR LOWER(direction) = 'saliente' THEN 'salientes'
                            ELSE direction
                        END as direction_normalized,
                        COUNT(*) as count
                    FROM operator_call_data 
                    WHERE operator = 'CLARO'
                    GROUP BY direction_normalized
                """)
                direction_distribution = {row['direction_normalized']: row['count'] for row in cursor.fetchall()}
                
                validation_result = {
                    'success': total_count == EXPECTED_TOTAL_RECORDS,
                    'call_data_records': call_data_count,
                    'cellular_data_records': cellular_data_count,
                    'total_records': total_count,
                    'expected_records': EXPECTED_TOTAL_RECORDS,
                    'difference': total_count - EXPECTED_TOTAL_RECORDS,
                    'direction_distribution': direction_distribution,
                    'validation_status': 'PASSED' if total_count == EXPECTED_TOTAL_RECORDS else 'FAILED'
                }
                
                print(f"   📊 Llamadas: {call_data_count}")
                print(f"   📊 Datos Celulares: {cellular_data_count}")
                print(f"   📊 Total: {total_count}/{EXPECTED_TOTAL_RECORDS}")
                print(f"   📊 Estado: {'✅ CORRECTO' if total_count == EXPECTED_TOTAL_RECORDS else '❌ INCORRECTO'}")
                
                return validation_result
                
        except Exception as e:
            print(f"❌ Error validando conteo: {e}")
            return {
                'success': False,
                'error': str(e),
                'validation_status': 'ERROR'
            }
    
    def validate_target_numbers(self) -> Dict[str, Any]:
        """
        Validar presencia de números objetivo en los datos
        
        Returns:
            Dict con análisis detallado de números objetivo
        """
        print("🎯 Validando números objetivo...")
        
        try:
            with self.connect_database() as conn:
                cursor = conn.cursor()
                
                target_analysis = {}
                
                for number in TARGET_NUMBERS:
                    analysis = {
                        'number': number,
                        'found_in_claro_calls': False,
                        'found_in_claro_cellular': False,
                        'found_in_hunter': False,
                        'call_connections': [],
                        'cellular_connections': [],
                        'hunter_connections': [],
                        'total_occurrences': 0
                    }
                    
                    # Buscar en datos de llamadas CLARO
                    cursor.execute("""
                        SELECT DISTINCT origen, destino, fecha_inicio, cell_id
                        FROM operator_call_data
                        WHERE operator = 'CLARO' 
                        AND (origen = ? OR destino = ?)
                        LIMIT 50
                    """, (number, number))
                    
                    claro_call_results = cursor.fetchall()
                    if claro_call_results:
                        analysis['found_in_claro_calls'] = True
                        for row in claro_call_results:
                            other_number = row['destino'] if row['origen'] == number else row['origen']
                            analysis['call_connections'].append({
                                'connected_to': other_number,
                                'timestamp': row['fecha_inicio'],
                                'cell_id': row['cell_id']
                            })
                    
                    # Buscar en datos celulares CLARO
                    cursor.execute("""
                        SELECT DISTINCT numero, cell_id, timestamp
                        FROM operator_cellular_data
                        WHERE operator = 'CLARO' AND numero = ?
                        LIMIT 50
                    """, (number,))
                    
                    claro_cellular_results = cursor.fetchall()
                    if claro_cellular_results:
                        analysis['found_in_claro_cellular'] = True
                        for row in claro_cellular_results:
                            analysis['cellular_connections'].append({
                                'cell_id': row['cell_id'],
                                'timestamp': row['timestamp']
                            })
                    
                    # Buscar en datos HUNTER
                    cursor.execute("""
                        SELECT DISTINCT numero_a, numero_b, fecha_hora, cell_id
                        FROM scanner_cellular_data
                        WHERE numero_a = ? OR numero_b = ?
                        LIMIT 50
                    """, (number, number))
                    
                    hunter_results = cursor.fetchall()
                    if hunter_results:
                        analysis['found_in_hunter'] = True
                        for row in hunter_results:
                            other_number = row['numero_b'] if row['numero_a'] == number else row['numero_a']
                            analysis['hunter_connections'].append({
                                'connected_to': other_number,
                                'timestamp': row['fecha_hora'],
                                'cell_id': row['cell_id']
                            })
                    
                    analysis['total_occurrences'] = len(claro_call_results) + len(claro_cellular_results) + len(hunter_results)
                    analysis['found_anywhere'] = analysis['found_in_claro_calls'] or analysis['found_in_claro_cellular'] or analysis['found_in_hunter']
                    
                    target_analysis[number] = analysis
                    
                    status = "✅ ENCONTRADO" if analysis['found_anywhere'] else "❌ NO ENCONTRADO"
                    print(f"   📱 {number}: {status} ({analysis['total_occurrences']} ocurrencias)")
                
                # Calcular estadísticas generales
                found_numbers = [n for n, a in target_analysis.items() if a['found_anywhere']]
                found_in_claro = [n for n, a in target_analysis.items() if a['found_in_claro_calls'] or a['found_in_claro_cellular']]
                found_in_hunter = [n for n, a in target_analysis.items() if a['found_in_hunter']]
                
                validation_result = {
                    'success': len(found_numbers) >= len(TARGET_NUMBERS) * 0.5,  # Al menos 50% de números encontrados
                    'target_numbers_analysis': target_analysis,
                    'summary': {
                        'total_targets': len(TARGET_NUMBERS),
                        'found_anywhere': len(found_numbers),
                        'found_in_claro': len(found_in_claro),
                        'found_in_hunter': len(found_in_hunter),
                        'not_found': len(TARGET_NUMBERS) - len(found_numbers),
                        'success_rate': len(found_numbers) / len(TARGET_NUMBERS) * 100
                    },
                    'validation_status': 'PASSED' if len(found_numbers) >= len(TARGET_NUMBERS) * 0.5 else 'FAILED'
                }
                
                print(f"   📊 Encontrados: {len(found_numbers)}/{len(TARGET_NUMBERS)} ({validation_result['summary']['success_rate']:.1f}%)")
                
                return validation_result
                
        except Exception as e:
            print(f"❌ Error validando números objetivo: {e}")
            return {
                'success': False,
                'error': str(e),
                'validation_status': 'ERROR'
            }
    
    def validate_correlation_capability(self) -> Dict[str, Any]:
        """
        Validar capacidad de correlación entre datos CLARO y HUNTER
        
        Returns:
            Dict con análisis de capacidad de correlación
        """
        print("🔄 Validando capacidad de correlación...")
        
        try:
            with self.connect_database() as conn:
                cursor = conn.cursor()
                
                # Buscar coincidencias temporales entre CLARO y HUNTER
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM operator_call_data ocd
                    JOIN scanner_cellular_data scd ON (
                        ocd.origen = scd.numero_a OR ocd.origen = scd.numero_b OR 
                        ocd.destino = scd.numero_a OR ocd.destino = scd.numero_b
                    )
                    WHERE ocd.operator = 'CLARO'
                    AND datetime(ocd.fecha_inicio) >= datetime('2021-05-20 10:00:00')
                    AND datetime(ocd.fecha_inicio) <= datetime('2021-05-20 14:30:00')
                    AND datetime(scd.fecha_hora) >= datetime('2021-05-20 10:00:00')
                    AND datetime(scd.fecha_hora) <= datetime('2021-05-20 14:30:00')
                """)
                
                temporal_correlations = cursor.fetchone()['count']
                
                # Buscar correlaciones por celda
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM operator_call_data ocd
                    JOIN scanner_cellular_data scd ON ocd.cell_id = scd.cell_id
                    WHERE ocd.operator = 'CLARO'
                    AND ocd.cell_id IS NOT NULL
                    AND scd.cell_id IS NOT NULL
                """)
                
                cell_correlations = cursor.fetchone()['count']
                
                # Estadísticas de datos para correlación
                cursor.execute("SELECT COUNT(*) as count FROM operator_call_data WHERE operator = 'CLARO'")
                claro_records = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM scanner_cellular_data")
                hunter_records = cursor.fetchone()['count']
                
                validation_result = {
                    'success': temporal_correlations > 0 or cell_correlations > 0,
                    'temporal_correlations': temporal_correlations,
                    'cell_correlations': cell_correlations,
                    'total_correlations': temporal_correlations + cell_correlations,
                    'data_availability': {
                        'claro_records': claro_records,
                        'hunter_records': hunter_records,
                        'correlation_potential': min(claro_records, hunter_records)
                    },
                    'validation_status': 'PASSED' if (temporal_correlations > 0 or cell_correlations > 0) else 'FAILED'
                }
                
                print(f"   📊 Correlaciones temporales: {temporal_correlations}")
                print(f"   📊 Correlaciones por celda: {cell_correlations}")
                print(f"   📊 Capacidad de correlación: {'✅ DISPONIBLE' if validation_result['success'] else '❌ LIMITADA'}")
                
                return validation_result
                
        except Exception as e:
            print(f"❌ Error validando correlación: {e}")
            return {
                'success': False,
                'error': str(e),
                'validation_status': 'ERROR'
            }
    
    def validate_hunter_data_integrity(self) -> Dict[str, Any]:
        """
        Validar integridad de datos HUNTER cargados
        
        Returns:
            Dict con análisis de integridad de datos HUNTER
        """
        print("🦸 Validando integridad de datos HUNTER...")
        
        try:
            with self.connect_database() as conn:
                cursor = conn.cursor()
                
                # Conteo básico
                cursor.execute("SELECT COUNT(*) as count FROM scanner_cellular_data")
                total_hunter_records = cursor.fetchone()['count']
                
                # Registros con datos válidos
                cursor.execute("""
                    SELECT COUNT(*) as count FROM scanner_cellular_data 
                    WHERE numero_a IS NOT NULL 
                    AND numero_b IS NOT NULL 
                    AND fecha_hora IS NOT NULL
                """)
                valid_records = cursor.fetchone()['count']
                
                # Números únicos
                cursor.execute("""
                    SELECT COUNT(DISTINCT numero_a) + COUNT(DISTINCT numero_b) as count 
                    FROM scanner_cellular_data
                """)
                unique_numbers = cursor.fetchone()['count']
                
                # Celdas únicas
                cursor.execute("SELECT COUNT(DISTINCT cell_id) as count FROM scanner_cellular_data WHERE cell_id IS NOT NULL")
                unique_cells = cursor.fetchone()['count']
                
                validation_result = {
                    'success': total_hunter_records > 0 and valid_records > 0,
                    'total_records': total_hunter_records,
                    'valid_records': valid_records,
                    'invalid_records': total_hunter_records - valid_records,
                    'data_quality': (valid_records / total_hunter_records * 100) if total_hunter_records > 0 else 0,
                    'unique_numbers': unique_numbers,
                    'unique_cells': unique_cells,
                    'validation_status': 'PASSED' if total_hunter_records > 0 and valid_records > 0 else 'FAILED'
                }
                
                print(f"   📊 Total registros: {total_hunter_records}")
                print(f"   📊 Registros válidos: {valid_records} ({validation_result['data_quality']:.1f}%)")
                print(f"   📊 Números únicos: {unique_numbers}")
                print(f"   📊 Celdas únicas: {unique_cells}")
                
                return validation_result
                
        except Exception as e:
            print(f"❌ Error validando datos HUNTER: {e}")
            return {
                'success': False,
                'error': str(e),
                'validation_status': 'ERROR'
            }
    
    def generate_executive_report(self) -> Dict[str, Any]:
        """
        Generar reporte ejecutivo completo
        
        Returns:
            Dict con reporte ejecutivo detallado
        """
        print("📋 Generando reporte ejecutivo...")
        
        timestamp = datetime.now().isoformat()
        
        # Ejecutar todas las validaciones
        claro_validation = self.validate_claro_records_count()
        target_validation = self.validate_target_numbers()
        correlation_validation = self.validate_correlation_capability()
        hunter_validation = self.validate_hunter_data_integrity()
        
        # Determinar éxito general
        all_validations = [claro_validation, target_validation, correlation_validation, hunter_validation]
        successful_validations = sum(1 for v in all_validations if v.get('success', False))
        overall_success = successful_validations >= 3  # Al menos 3 de 4 validaciones exitosas
        
        executive_report = {
            'report_metadata': {
                'timestamp': timestamp,
                'validator_version': '1.0.0',
                'database_path': str(self.db_path),
                'validation_suite': 'CLARO E2E Complete Validation'
            },
            
            'executive_summary': {
                'overall_status': 'PASSED' if overall_success else 'FAILED',
                'successful_validations': successful_validations,
                'total_validations': len(all_validations),
                'success_rate': (successful_validations / len(all_validations) * 100),
                'critical_issues': [],
                'recommendations': []
            },
            
            'detailed_validations': {
                'claro_records_validation': claro_validation,
                'target_numbers_validation': target_validation,
                'correlation_validation': correlation_validation,
                'hunter_data_validation': hunter_validation
            },
            
            'key_metrics': {
                'expected_claro_records': EXPECTED_TOTAL_RECORDS,
                'actual_claro_records': claro_validation.get('total_records', 0),
                'target_numbers_found': target_validation.get('summary', {}).get('found_anywhere', 0),
                'target_numbers_total': len(TARGET_NUMBERS),
                'hunter_records_loaded': hunter_validation.get('total_records', 0),
                'correlation_potential': correlation_validation.get('total_correlations', 0)
            }
        }
        
        # Identificar problemas críticos
        if not claro_validation.get('success'):
            executive_report['executive_summary']['critical_issues'].append(
                f"Carga de registros CLARO incorrecta: {claro_validation.get('total_records', 0)}/{EXPECTED_TOTAL_RECORDS}"
            )
        
        if not hunter_validation.get('success'):
            executive_report['executive_summary']['critical_issues'].append(
                "Datos HUNTER no cargados correctamente"
            )
        
        if not target_validation.get('success'):
            executive_report['executive_summary']['critical_issues'].append(
                f"Números objetivo no encontrados suficientemente: {target_validation.get('summary', {}).get('found_anywhere', 0)}/{len(TARGET_NUMBERS)}"
            )
        
        # Generar recomendaciones
        recommendations = executive_report['executive_summary']['recommendations']
        
        if claro_validation.get('total_records', 0) != EXPECTED_TOTAL_RECORDS:
            recommendations.append("Verificar integridad de archivos CLARO fuente")
            recommendations.append("Revisar algoritmo de carga para evitar duplicados o pérdidas")
        
        if target_validation.get('summary', {}).get('found_anywhere', 0) < len(TARGET_NUMBERS):
            recommendations.append("Ampliar ventana temporal de búsqueda de números objetivo")
            recommendations.append("Verificar formatos de números en archivos fuente")
        
        if not correlation_validation.get('success'):
            recommendations.append("Revisar algoritmo de correlación temporal")
            recommendations.append("Validar sincronización de timestamps entre fuentes")
        
        recommendations.extend([
            "Implementar monitoreo continuo de calidad de datos",
            "Establecer alertas automáticas para cargas fallidas",
            "Documentar casos de prueba adicionales para regresión"
        ])
        
        print(f"   📊 Estado General: {'✅ EXITOSO' if overall_success else '❌ FALLIDO'}")
        print(f"   📊 Validaciones Exitosas: {successful_validations}/{len(all_validations)}")
        print(f"   📊 Problemas Críticos: {len(executive_report['executive_summary']['critical_issues'])}")
        
        return executive_report
    
    def run_full_validation(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Ejecutar suite completa de validación
        
        Returns:
            Tuple de (éxito, reporte_completo)
        """
        print("🚀 Iniciando validación completa de resultados CLARO E2E...")
        print(f"📄 Base de datos: {self.db_path}")
        print("=" * 60)
        
        try:
            report = self.generate_executive_report()
            success = report['executive_summary']['overall_status'] == 'PASSED'
            
            print("=" * 60)
            print(f"🎯 VALIDACIÓN COMPLETA: {'✅ EXITOSA' if success else '❌ FALLIDA'}")
            
            return success, report
            
        except Exception as e:
            print(f"❌ Error crítico durante validación: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            
            error_report = {
                'report_metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e),
                    'traceback': traceback.format_exc()
                },
                'executive_summary': {
                    'overall_status': 'ERROR',
                    'critical_issues': [f"Error crítico: {str(e)}"]
                }
            }
            
            return False, error_report

def main():
    """Función principal para ejecución standalone"""
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = None
    
    validator = ClaroResultsValidator(db_path)
    success, report = validator.run_full_validation()
    
    # Guardar reporte
    report_filename = f"claro_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Intentar guardar en test-results, si no existe usar directorio actual
    try:
        test_results_dir = Path(__file__).parent.parent.parent / "test-results"
        test_results_dir.mkdir(exist_ok=True)
        report_path = test_results_dir / report_filename
    except:
        report_path = Path(report_filename)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"📊 Reporte guardado: {report_path}")
    
    # Salir con código apropiado
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()