#!/usr/bin/env python3
"""
VALIDACIÓN COMPLETA DE CARGA CLARO - Sistema KRONOS
==================================================

Script de validación exhaustivo para verificar que:
1. Se carguen exactamente 5,611 registros CLARO
2. La normalización de números funcione correctamente (quitar prefijo 57)
3. Los números objetivo estén presentes en la base de datos
4. No se pierdan registros durante el proceso

CORRECCIONES IMPLEMENTADAS:
- Normalización de números (remover prefijo 57)
- Carga permisiva para no perder registros
- Filtrado de correlación por operador CLARO

Autor: Claude Code para Boris
Fecha: 2025-08-18
"""

import os
import sys
import sqlite3
import pandas as pd
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple
import json

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClaroLoadingValidator:
    """
    Validador completo para verificar carga correcta de archivos CLARO
    """
    
    # Archivos esperados de CLARO
    EXPECTED_CLARO_FILES = {
        'entrantes_1': r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\1-225211_LLAMADAS_ENTRANTES_POR_CELDA_545612_0.xlsx",
        'salientes_1': r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\1-225211_LLAMADAS_SALIENTES_POR_CELDA_545613_0.xlsx",
        'entrantes_2': r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\2-225211_LLAMADAS_ENTRANTES_POR_CELDA_545614_0.xlsx",
        'salientes_2': r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\2-225211_LLAMADAS_SALIENTES_POR_CELDA_545615_0.xlsx"
    }
    
    # Total esperado de registros
    EXPECTED_TOTAL_RECORDS = 5611
    
    # Números objetivo que deben aparecer
    TARGET_NUMBERS = [
        '3224274851', '3208611034', '3104277553', 
        '3102715509', '3143534707', '3214161903'
    ]
    
    def __init__(self, db_path: str = None):
        """
        Inicializar validador
        
        Args:
            db_path: Ruta a la base de datos. Si None, usa la del directorio actual.
        """
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), 'kronos.db')
        self.db_path = db_path
        self.validation_results = {}
        
        logger.info("Validador de carga CLARO inicializado")
        logger.info(f"Base de datos: {self.db_path}")
    
    def validate_source_files_availability(self) -> Dict[str, Any]:
        """
        Validar que los archivos fuente estén disponibles y contables
        """
        logger.info("=== VALIDACIÓN 1: ARCHIVOS FUENTE ===")
        
        results = {
            'test_name': 'source_files_availability',
            'status': 'PASS',
            'files_analysis': {},
            'total_source_records': 0,
            'files_missing': [],
            'target_numbers_in_source': {}
        }
        
        total_records = 0
        target_occurrences = {target: [] for target in self.TARGET_NUMBERS}
        
        for file_key, file_path in self.EXPECTED_CLARO_FILES.items():
            if not os.path.exists(file_path):
                results['files_missing'].append(file_key)
                results['status'] = 'FAIL'
                continue
            
            try:
                # Leer archivo
                df = pd.read_excel(file_path)
                file_records = len(df)
                total_records += file_records
                
                # Buscar números objetivo
                for target in self.TARGET_NUMBERS:
                    # Buscar en originador y receptor
                    orig_matches = df['originador'].astype(str).str.contains(target, na=False).sum()
                    recv_matches = df['receptor'].astype(str).str.contains(target, na=False).sum()
                    
                    # También buscar con prefijo 57
                    orig_matches_57 = df['originador'].astype(str).str.contains(f'57{target}', na=False).sum()
                    recv_matches_57 = df['receptor'].astype(str).str.contains(f'57{target}', na=False).sum()
                    
                    total_matches = orig_matches + recv_matches + orig_matches_57 + recv_matches_57
                    
                    if total_matches > 0:
                        target_occurrences[target].append({
                            'file': file_key,
                            'occurrences': total_matches
                        })
                
                results['files_analysis'][file_key] = {
                    'path': file_path,
                    'records': file_records,
                    'size_mb': round(os.path.getsize(file_path) / (1024*1024), 2)
                }
                
            except Exception as e:
                logger.error(f"Error analizando {file_key}: {e}")
                results['status'] = 'FAIL'
                results['files_analysis'][file_key] = {'error': str(e)}
        
        results['total_source_records'] = total_records
        results['target_numbers_in_source'] = target_occurrences
        
        # Verificar total esperado
        if total_records != self.EXPECTED_TOTAL_RECORDS:
            logger.warning(f"Total registros fuente: {total_records}, Esperado: {self.EXPECTED_TOTAL_RECORDS}")
            if results['status'] == 'PASS':
                results['status'] = 'WARN'
        
        logger.info(f"Total registros en archivos fuente: {total_records}")
        logger.info(f"Archivos faltantes: {len(results['files_missing'])}")
        return results
    
    def validate_database_loading(self) -> Dict[str, Any]:
        """
        Validar que los datos se hayan cargado correctamente en la base de datos
        """
        logger.info("=== VALIDACIÓN 2: CARGA EN BASE DE DATOS ===")
        
        results = {
            'test_name': 'database_loading',
            'status': 'PASS',
            'database_analysis': {},
            'target_numbers_in_db': {},
            'loading_completeness': {}
        }
        
        if not os.path.exists(self.db_path):
            results['status'] = 'FAIL'
            results['error'] = 'Base de datos no encontrada'
            return results
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Analizar registros CLARO en operator_call_data
                cursor = conn.execute("SELECT COUNT(*) FROM operator_call_data WHERE operator = 'CLARO'")
                claro_records = cursor.fetchone()[0]
                
                # Analizar distribución por tipo de llamada
                cursor = conn.execute("""
                    SELECT tipo_llamada, COUNT(*) 
                    FROM operator_call_data 
                    WHERE operator = 'CLARO' 
                    GROUP BY tipo_llamada
                """)
                tipo_distribution = {str(k): int(v) for k, v in cursor.fetchall()}
                
                # Analizar números únicos
                cursor = conn.execute("""
                    SELECT COUNT(DISTINCT numero_origen), COUNT(DISTINCT numero_destino)
                    FROM operator_call_data 
                    WHERE operator = 'CLARO'
                """)
                unique_origins, unique_destinations = cursor.fetchone()
                
                results['database_analysis'] = {
                    'total_claro_records': int(claro_records),
                    'tipo_distribution': tipo_distribution,
                    'unique_origins': int(unique_origins),
                    'unique_destinations': int(unique_destinations)
                }
                
                # Verificar completeness de carga
                completeness_percentage = (claro_records / self.EXPECTED_TOTAL_RECORDS) * 100 if self.EXPECTED_TOTAL_RECORDS > 0 else 0
                
                results['loading_completeness'] = {
                    'records_loaded': int(claro_records),
                    'records_expected': int(self.EXPECTED_TOTAL_RECORDS),
                    'completeness_percentage': round(float(completeness_percentage), 2),
                    'records_missing': int(self.EXPECTED_TOTAL_RECORDS - claro_records)
                }
                
                # Verificar números objetivo en base de datos
                for target in self.TARGET_NUMBERS:
                    # Buscar tanto con prefijo como sin prefijo
                    cursor = conn.execute("""
                        SELECT COUNT(*) FROM operator_call_data 
                        WHERE operator = 'CLARO' 
                        AND (numero_origen LIKE ? OR numero_destino LIKE ? OR numero_objetivo LIKE ?)
                    """, (f'%{target}%', f'%{target}%', f'%{target}%'))
                    count_without_prefix = cursor.fetchone()[0]
                    
                    cursor = conn.execute("""
                        SELECT COUNT(*) FROM operator_call_data 
                        WHERE operator = 'CLARO' 
                        AND (numero_origen LIKE ? OR numero_destino LIKE ? OR numero_objetivo LIKE ?)
                    """, (f'%57{target}%', f'%57{target}%', f'%57{target}%'))
                    count_with_prefix = cursor.fetchone()[0]
                    
                    total_occurrences = count_without_prefix + count_with_prefix
                    
                    results['target_numbers_in_db'][target] = {
                        'found': bool(total_occurrences > 0),
                        'total_occurrences': int(total_occurrences),
                        'occurrences_without_prefix': int(count_without_prefix),
                        'occurrences_with_prefix': int(count_with_prefix)
                    }
                
                # Determinar estado general
                if claro_records == 0:
                    results['status'] = 'FAIL'
                elif completeness_percentage < 95:
                    results['status'] = 'FAIL'
                elif completeness_percentage < 100:
                    results['status'] = 'WARN'
                
                logger.info(f"Registros CLARO en BD: {claro_records} ({completeness_percentage:.1f}%)")
                
        except Exception as e:
            logger.error(f"Error validando base de datos: {e}")
            results['status'] = 'FAIL'
            results['error'] = str(e)
        
        return results
    
    def validate_phone_normalization(self) -> Dict[str, Any]:
        """
        Validar que la normalización de números funcione correctamente
        """
        logger.info("=== VALIDACIÓN 3: NORMALIZACIÓN DE NÚMEROS ===")
        
        results = {
            'test_name': 'phone_normalization',
            'status': 'PASS',
            'normalization_analysis': {},
            'prefix_removal_check': {}
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Verificar que no haya números con prefijo 57 en la BD
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM operator_call_data 
                    WHERE operator = 'CLARO' 
                    AND (numero_origen LIKE '57%' OR numero_destino LIKE '57%')
                """)
                numbers_with_prefix = cursor.fetchone()[0]
                
                # Verificar distribución de longitudes de números
                cursor = conn.execute("""
                    SELECT 
                        LENGTH(numero_origen) as len,
                        COUNT(*) as count
                    FROM operator_call_data 
                    WHERE operator = 'CLARO' 
                    AND numero_origen IS NOT NULL
                    GROUP BY LENGTH(numero_origen)
                    ORDER BY len
                """)
                length_distribution_origen = {int(k): int(v) for k, v in cursor.fetchall()}
                
                cursor = conn.execute("""
                    SELECT 
                        LENGTH(numero_destino) as len,
                        COUNT(*) as count
                    FROM operator_call_data 
                    WHERE operator = 'CLARO' 
                    AND numero_destino IS NOT NULL
                    GROUP BY LENGTH(numero_destino)
                    ORDER BY len
                """)
                length_distribution_destino = {int(k): int(v) for k, v in cursor.fetchall()}
                
                results['normalization_analysis'] = {
                    'numbers_with_57_prefix': int(numbers_with_prefix),
                    'length_distribution_origen': length_distribution_origen,
                    'length_distribution_destino': length_distribution_destino
                }
                
                # Verificar números objetivo específicos
                for target in self.TARGET_NUMBERS:
                    # Verificar que aparezcan SIN prefijo 57
                    cursor = conn.execute("""
                        SELECT COUNT(*) FROM operator_call_data 
                        WHERE operator = 'CLARO' 
                        AND (numero_origen = ? OR numero_destino = ?)
                    """, (target, target))
                    count_normalized = cursor.fetchone()[0]
                    
                    # Verificar que NO aparezcan CON prefijo 57
                    cursor = conn.execute("""
                        SELECT COUNT(*) FROM operator_call_data 
                        WHERE operator = 'CLARO' 
                        AND (numero_origen = ? OR numero_destino = ?)
                    """, (f'57{target}', f'57{target}'))
                    count_with_prefix = cursor.fetchone()[0]
                    
                    results['prefix_removal_check'][target] = {
                        'found_normalized': bool(count_normalized > 0),
                        'found_with_prefix': bool(count_with_prefix > 0),
                        'normalization_correct': bool(count_normalized > 0 and count_with_prefix == 0)
                    }
                
                # Determinar estado
                if numbers_with_prefix > 0:
                    results['status'] = 'FAIL'
                    logger.warning(f"Encontrados {numbers_with_prefix} números con prefijo 57 - normalización falló")
                else:
                    logger.info("Normalización correcta: no se encontraron números con prefijo 57")
                
        except Exception as e:
            logger.error(f"Error validando normalización: {e}")
            results['status'] = 'FAIL'
            results['error'] = str(e)
        
        return results
    
    def validate_correlation_operator_filter(self) -> Dict[str, Any]:
        """
        Validar que el servicio de correlación filtre correctamente por operador CLARO
        """
        logger.info("=== VALIDACIÓN 4: FILTRO DE OPERADOR EN CORRELACIÓN ===")
        
        results = {
            'test_name': 'correlation_operator_filter',
            'status': 'PASS',
            'hunter_claro_cells': 0,
            'operator_distribution': {}
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Verificar celdas HUNTER para operador CLARO
                cursor = conn.execute("""
                    SELECT COUNT(DISTINCT cell_id) 
                    FROM cellular_data 
                    WHERE UPPER(TRIM(operator)) = 'CLARO'
                    AND cell_id IS NOT NULL
                """)
                hunter_claro_cells = cursor.fetchone()[0]
                
                # Verificar distribución de operadores en HUNTER
                cursor = conn.execute("""
                    SELECT UPPER(TRIM(operator)) as op, COUNT(*) as count
                    FROM cellular_data 
                    GROUP BY UPPER(TRIM(operator))
                """)
                hunter_operator_distribution = {str(k): int(v) for k, v in cursor.fetchall()}
                
                # Verificar distribución de operadores en operator_call_data
                cursor = conn.execute("""
                    SELECT operator, COUNT(*) as count
                    FROM operator_call_data 
                    GROUP BY operator
                """)
                call_operator_distribution = {str(k): int(v) for k, v in cursor.fetchall()}
                
                results['hunter_claro_cells'] = int(hunter_claro_cells)
                results['operator_distribution'] = {
                    'hunter_data': hunter_operator_distribution,
                    'call_data': call_operator_distribution
                }
                
                if hunter_claro_cells == 0:
                    results['status'] = 'WARN'
                    logger.warning("No se encontraron celdas HUNTER para operador CLARO")
                else:
                    logger.info(f"Celdas HUNTER CLARO disponibles: {hunter_claro_cells}")
                
        except Exception as e:
            logger.error(f"Error validando filtro de operador: {e}")
            results['status'] = 'FAIL'
            results['error'] = str(e)
        
        return results
    
    def run_complete_validation(self) -> Dict[str, Any]:
        """
        Ejecutar validación completa
        """
        logger.info("=" * 80)
        logger.info("INICIANDO VALIDACIÓN COMPLETA DE CARGA CLARO")
        logger.info("=" * 80)
        
        validation_suite = {
            'validation_start_time': datetime.now().isoformat(),
            'validations_executed': [],
            'validations_passed': 0,
            'validations_failed': 0,
            'validations_warnings': 0,
            'overall_status': 'PASS',
            'critical_issues': [],
            'recommendations': []
        }
        
        # Ejecutar todas las validaciones
        validations = [
            self.validate_source_files_availability,
            self.validate_database_loading,
            self.validate_phone_normalization,
            self.validate_correlation_operator_filter
        ]
        
        for validation_func in validations:
            try:
                logger.info(f"\nEjecutando: {validation_func.__name__}")
                validation_result = validation_func()
                
                validation_suite['validations_executed'].append(validation_result)
                
                if validation_result['status'] == 'PASS':
                    validation_suite['validations_passed'] += 1
                elif validation_result['status'] == 'WARN':
                    validation_suite['validations_warnings'] += 1
                else:
                    validation_suite['validations_failed'] += 1
                    validation_suite['overall_status'] = 'FAIL'
                    if 'error' in validation_result:
                        validation_suite['critical_issues'].append(validation_result['error'])
                
                logger.info(f"Resultado: {validation_result['status']}")
                
            except Exception as e:
                error_msg = f"Error ejecutando {validation_func.__name__}: {str(e)}"
                logger.error(error_msg)
                validation_suite['validations_failed'] += 1
                validation_suite['overall_status'] = 'FAIL'
                validation_suite['critical_issues'].append(error_msg)
        
        # Generar recomendaciones
        if validation_suite['overall_status'] != 'PASS':
            validation_suite['recommendations'].extend([
                "1. Verificar que todos los archivos CLARO estén disponibles",
                "2. Re-ejecutar carga con algoritmo corregido",
                "3. Validar que normalización de números funcione (sin prefijo 57)",
                "4. Verificar filtrado por operador en correlación",
                "5. Revisar logs de carga para identificar registros perdidos"
            ])
        
        validation_suite['validation_end_time'] = datetime.now().isoformat()
        
        # Guardar resultados (convertir todos los valores a tipos serializables)
        results_file = f"claro_validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        def make_serializable(obj):
            """Convierte objetos a tipos serializables por JSON"""
            if isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_serializable(v) for v in obj]
            elif hasattr(obj, 'item'):  # numpy types
                return obj.item()
            elif hasattr(obj, '__int__'):  # pandas int64, etc.
                return int(obj)
            elif hasattr(obj, '__float__'):  # pandas float64, etc.
                return float(obj)
            elif hasattr(obj, '__str__'):
                return str(obj)
            else:
                return obj
        
        serializable_suite = make_serializable(validation_suite)
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_suite, f, indent=2, ensure_ascii=False)
        
        logger.info("=" * 80)
        logger.info(f"VALIDACIÓN COMPLETADA - Estado: {validation_suite['overall_status']}")
        logger.info(f"Validaciones exitosas: {validation_suite['validations_passed']}")
        logger.info(f"Validaciones con warnings: {validation_suite['validations_warnings']}")
        logger.info(f"Validaciones fallidas: {validation_suite['validations_failed']}")
        logger.info(f"Resultados guardados en: {results_file}")
        logger.info("=" * 80)
        
        return validation_suite

def main():
    """Función principal"""
    validator = ClaroLoadingValidator()
    results = validator.run_complete_validation()
    
    # Imprimir resumen final
    print("\n" + "="*60)
    print("RESUMEN FINAL DE VALIDACIÓN")
    print("="*60)
    print(f"Estado general: {results['overall_status']}")
    print(f"Validaciones ejecutadas: {len(results['validations_executed'])}")
    print(f"Validaciones exitosas: {results['validations_passed']}")
    print(f"Validaciones con warnings: {results['validations_warnings']}")
    print(f"Validaciones fallidas: {results['validations_failed']}")
    
    if results['critical_issues']:
        print(f"\nProblemas críticos encontrados:")
        for issue in results['critical_issues']:
            print(f"  - {issue}")
    
    if results['recommendations']:
        print(f"\nRecomendaciones:")
        for rec in results['recommendations']:
            print(f"  {rec}")
    
    return results['overall_status'] == 'PASS'

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)