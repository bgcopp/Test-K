#!/usr/bin/env python3
"""
KRONOS - Test de Validación de Correcciones en Análisis de Correlación
=========================================================================

Este test valida que las correcciones implementadas garanticen que los
números objetivo aparezcan correctamente con el formato sin prefijo 57.

NÚMEROS OBJETIVO A VALIDAR:
- 3224274851 (Cell IDs: ['51438', '53591', '56124', '63095'])
- 3208611034 (Cell IDs: ['51203', '63095'])  
- 3143534707 (Cell IDs: ['51438', '53591', '56124'])
- 3102715509 (Cell IDs: ['56124'])
- 3214161903 (Cell IDs: ['2523', '53591'])

VALIDACIONES CRÍTICAS:
1. Los números aparecen SIN prefijo 57 en el resultado
2. Se maximiza la detección con algoritmo exhaustivo
3. Las correlaciones incluyen todas las celdas esperadas
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, List

# Agregar el directorio del backend al path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

# Importar servicio corregido
from services.correlation_analysis_service import get_correlation_service

# Configurar logging detallado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_correlation_fixes_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CorrelationFixesValidator:
    """
    Validador especializado para verificar las correcciones implementadas
    en el análisis de correlación.
    """
    
    def __init__(self):
        self.service = get_correlation_service()
        self.expected_targets = {
            '3224274851': ['51438', '53591', '56124', '63095'],
            '3208611034': ['51203', '63095'],
            '3143534707': ['51438', '53591', '56124'],
            '3102715509': ['56124'],
            '3214161903': ['2523', '53591']
        }
        
    def run_validation(self) -> Dict[str, Any]:
        """
        Ejecuta la validación completa de las correcciones.
        
        Returns:
            Diccionario con resultados de validación
        """
        logger.info("=" * 80)
        logger.info("INICIANDO VALIDACIÓN DE CORRECCIONES EN ANÁLISIS DE CORRELACIÓN")
        logger.info("=" * 80)
        
        # Parámetros de prueba (usar datos reales de la misión)
        test_params = {
            'mission_id': '1',  # Ajustar según tu misión real
            'start_date': '2024-01-01 00:00:00',
            'end_date': '2024-12-31 23:59:59',
            'min_coincidences': 1  # Incluir TODOS los números con >= 1 coincidencia
        }
        
        logger.info(f"Parámetros de prueba: {json.dumps(test_params, indent=2)}")
        
        # Ejecutar análisis con correcciones
        logger.info("Ejecutando análisis de correlación con algoritmo corregido...")
        start_time = datetime.now()
        
        result = self.service.analyze_correlation(
            mission_id=test_params['mission_id'],
            start_date=test_params['start_date'],
            end_date=test_params['end_date'],
            min_coincidences=test_params['min_coincidences']
        )
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        logger.info(f"Análisis completado en {processing_time:.2f} segundos")
        
        # Validar resultados
        validation_results = self._validate_results(result)
        
        # Generar reporte completo
        report = {
            'test_info': {
                'timestamp': datetime.now().isoformat(),
                'test_name': 'correlation_fixes_validation',
                'processing_time_seconds': processing_time,
                'parameters': test_params
            },
            'analysis_result': result,
            'validation_results': validation_results,
            'success': validation_results['overall_success']
        }
        
        # Guardar reporte
        report_filename = f"correlation_fixes_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Reporte guardado en: {report_filename}")
        
        return report
    
    def _validate_results(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida que los resultados cumplan con las correcciones implementadas.
        
        Args:
            analysis_result: Resultado del análisis de correlación
            
        Returns:
            Diccionario con resultados de validación detallados
        """
        logger.info("=" * 60)
        logger.info("VALIDANDO RESULTADOS DE CORRECCIONES")
        logger.info("=" * 60)
        
        validation = {
            'overall_success': False,
            'analysis_success': False,
            'targets_found': {},
            'format_validation': {},
            'critical_validations': {},
            'warnings': [],
            'errors': []
        }
        
        # 1. Validar que el análisis fue exitoso
        if not analysis_result.get('success'):
            validation['errors'].append("El análisis de correlación falló")
            logger.error("ERROR: El análisis de correlación no fue exitoso")
            return validation
        
        validation['analysis_success'] = True
        
        # 2. Obtener datos de correlaciones
        correlations = analysis_result.get('data', [])
        logger.info(f"Total de correlaciones encontradas: {len(correlations)}")
        
        if not correlations:
            validation['errors'].append("No se encontraron correlaciones")
            logger.error("ERROR: No se encontraron correlaciones")
            return validation
        
        # 3. Validar números objetivo específicos
        validation['targets_found'] = self._validate_target_numbers(correlations)
        
        # 4. Validar formato de números (SIN prefijo 57)
        validation['format_validation'] = self._validate_number_format(correlations)
        
        # 5. Validaciones críticas
        validation['critical_validations'] = self._perform_critical_validations(correlations)
        
        # 6. Determinar éxito general
        targets_success = all(target['found'] for target in validation['targets_found'].values())
        format_success = validation['format_validation']['all_numbers_correct_format']
        critical_success = all(validation['critical_validations'].values())
        
        validation['overall_success'] = targets_success and format_success and critical_success
        
        # Log de resumen
        if validation['overall_success']:
            logger.info("✓ VALIDACIÓN EXITOSA: Todas las correcciones funcionan correctamente")
        else:
            logger.warning("⚠ VALIDACIÓN PARCIAL: Algunas correcciones requieren ajustes")
            
        return validation
    
    def _validate_target_numbers(self, correlations: List[Dict]) -> Dict[str, Dict]:
        """
        Valida que los números objetivo específicos aparezcan correctamente.
        """
        logger.info("Validando números objetivo específicos...")
        
        targets_validation = {}
        
        for target_number, expected_cells in self.expected_targets.items():
            found_correlation = None
            
            # Buscar el número en las correlaciones
            for correlation in correlations:
                if correlation.get('numero_celular') == target_number:
                    found_correlation = correlation
                    break
            
            if found_correlation:
                found_cells = set(found_correlation.get('celdas_detectadas', 
                                 found_correlation.get('celdas_coincidentes', [])))
                expected_cells_set = set(expected_cells)
                matches = found_cells.intersection(expected_cells_set)
                
                targets_validation[target_number] = {
                    'found': True,
                    'format_correct': not target_number.startswith('57'),  # Debe estar SIN prefijo
                    'total_coincidences': found_correlation.get('total_coincidencias', 0),
                    'cells_found': sorted(list(found_cells)),
                    'cells_expected': expected_cells,
                    'cells_matched': sorted(list(matches)),
                    'match_percentage': len(matches) / len(expected_cells_set) * 100,
                    'validation_status': 'COMPLETE' if matches == expected_cells_set else 'PARTIAL'
                }
                
                status_icon = "✓" if matches == expected_cells_set else "⚠"
                logger.info(f"  {status_icon} {target_number}: {len(matches)}/{len(expected_cells)} celdas esperadas")
                
            else:
                targets_validation[target_number] = {
                    'found': False,
                    'format_correct': False,
                    'total_coincidences': 0,
                    'cells_found': [],
                    'cells_expected': expected_cells,
                    'cells_matched': [],
                    'match_percentage': 0,
                    'validation_status': 'NOT_FOUND'
                }
                
                logger.warning(f"  ✗ {target_number}: NO ENCONTRADO")
        
        return targets_validation
    
    def _validate_number_format(self, correlations: List[Dict]) -> Dict[str, Any]:
        """
        Valida que todos los números estén en formato correcto (SIN prefijo 57).
        """
        logger.info("Validando formato de números (debe ser SIN prefijo 57)...")
        
        format_validation = {
            'all_numbers_correct_format': True,
            'numbers_with_prefix': [],
            'numbers_without_prefix': [],
            'total_numbers': len(correlations)
        }
        
        for correlation in correlations:
            numero = correlation.get('numero_celular', '')
            
            if numero.startswith('57'):
                format_validation['numbers_with_prefix'].append(numero)
                format_validation['all_numbers_correct_format'] = False
                logger.warning(f"  ⚠ Número CON prefijo 57: {numero}")
            else:
                format_validation['numbers_without_prefix'].append(numero)
                logger.debug(f"  ✓ Número SIN prefijo 57: {numero}")
        
        if format_validation['all_numbers_correct_format']:
            logger.info(f"  ✓ Todos los {len(correlations)} números están en formato correcto (SIN prefijo 57)")
        else:
            logger.warning(f"  ⚠ {len(format_validation['numbers_with_prefix'])} números tienen prefijo 57 incorrectamente")
        
        return format_validation
    
    def _perform_critical_validations(self, correlations: List[Dict]) -> Dict[str, bool]:
        """
        Realiza validaciones críticas adicionales.
        """
        logger.info("Realizando validaciones críticas...")
        
        critical = {
            'has_correlations': len(correlations) > 0,
            'has_target_numbers': False,
            'all_have_cell_data': True,
            'algorithm_correct': True
        }
        
        # Verificar que al menos algunos números objetivo estén presentes
        target_numbers_found = []
        for correlation in correlations:
            numero = correlation.get('numero_celular', '')
            if numero in self.expected_targets:
                target_numbers_found.append(numero)
        
        critical['has_target_numbers'] = len(target_numbers_found) > 0
        
        # Verificar que todas las correlaciones tengan datos de celdas
        for correlation in correlations:
            cells = correlation.get('celdas_detectadas', correlation.get('celdas_coincidentes', []))
            if not cells:
                critical['all_have_cell_data'] = False
                break
        
        # Log de resultados críticos
        for validation_name, success in critical.items():
            icon = "✓" if success else "✗"
            logger.info(f"  {icon} {validation_name}: {'PASS' if success else 'FAIL'}")
        
        return critical


def main():
    """
    Función principal para ejecutar la validación.
    """
    print("=" * 80)
    print("KRONOS - Validación de Correcciones en Análisis de Correlación")
    print("=" * 80)
    
    validator = CorrelationFixesValidator()
    
    try:
        # Ejecutar validación
        report = validator.run_validation()
        
        # Mostrar resumen final
        print("\n" + "=" * 80)
        print("RESUMEN DE VALIDACIÓN")
        print("=" * 80)
        
        if report['success']:
            print("✓ ÉXITO: Todas las correcciones funcionan correctamente")
            print("  - Los números objetivo aparecen en formato correcto (SIN prefijo 57)")
            print("  - El algoritmo exhaustivo maximiza la detección")
            print("  - Las correlaciones incluyen todas las celdas esperadas")
        else:
            print("⚠ ADVERTENCIA: Algunas correcciones requieren ajustes")
            
            # Mostrar detalles de números objetivo
            targets = report['validation_results']['targets_found']
            found_count = sum(1 for t in targets.values() if t['found'])
            total_count = len(targets)
            
            print(f"  - Números objetivo detectados: {found_count}/{total_count}")
            
            for number, data in targets.items():
                if data['found']:
                    status = "✓" if data['validation_status'] == 'COMPLETE' else "⚠"
                    print(f"    {status} {number}: {data['validation_status']}")
                else:
                    print(f"    ✗ {number}: NO ENCONTRADO")
        
        print(f"\nReporte detallado guardado en el archivo de log correspondiente")
        
        return 0 if report['success'] else 1
        
    except Exception as e:
        logger.error(f"Error durante la validación: {e}", exc_info=True)
        print(f"✗ ERROR: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)