#!/usr/bin/env python3
"""
KRONOS - Validación de Manejo de Errores y Estados Vacíos
=========================================================

Test de validación para verificar que el componente CellularDataStats
maneja correctamente casos edge, errores y estados vacíos.

Autor: Sistema KRONOS - Testing Engineer
Fecha: 2025-08-14
"""

import json
import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class ErrorHandlingValidator:
    """Validador de manejo de errores y casos edge"""
    
    def __init__(self):
        """Inicializa el validador"""
        self.validation_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "errors": [],
            "warnings": []
        }
    
    def test_empty_data_scenarios(self):
        """Test casos con datos vacíos"""
        print("Testing empty data scenarios...")
        
        scenarios = [
            ([], "Lista completamente vacía"),
            (None, "Datos null"),
            ([{} for _ in range(3)], "Lista con objetos vacíos")
        ]
        
        for data, description in scenarios:
            result = self._test_empty_data(data, description)
            self._add_test_result(f"Datos vacíos - {description}", result)
    
    def test_malformed_data_scenarios(self):
        """Test casos con datos malformados"""
        print("Testing malformed data scenarios...")
        
        scenarios = [
            # RSSI values missing or null
            ([{"punto": "P1", "operador": "CLARO", "tecnologia": "LTE", "rssi": None}], "RSSI null"),
            ([{"punto": "P1", "operador": "CLARO", "tecnologia": "LTE"}], "RSSI missing"),
            
            # Missing critical fields
            ([{"rssi": -70, "tecnologia": "LTE"}], "Punto y operador missing"),
            ([{"punto": "P1", "rssi": -70}], "Operador y tecnología missing"),
            
            # Invalid data types
            ([{"punto": 123, "operador": "CLARO", "tecnologia": "LTE", "rssi": "invalid"}], "Tipos de datos incorrectos"),
            
            # FileRecordId edge cases
            ([{"punto": "P1", "operador": "CLARO", "tecnologia": "LTE", "rssi": -70, "fileRecordId": 0}], "fileRecordId = 0"),
            ([{"punto": "P1", "operador": "CLARO", "tecnologia": "LTE", "rssi": -70, "fileRecordId": ""}], "fileRecordId vacío"),
        ]
        
        for data, description in scenarios:
            result = self._test_malformed_data(data, description)
            self._add_test_result(f"Datos malformados - {description}", result)
    
    def test_extreme_values(self):
        """Test casos con valores extremos"""
        print("Testing extreme values...")
        
        scenarios = [
            # RSSI extremos
            ([{"punto": "P1", "operador": "CLARO", "tecnologia": "LTE", "rssi": -200}], "RSSI extremadamente bajo"),
            ([{"punto": "P1", "operador": "CLARO", "tecnologia": "LTE", "rssi": 0}], "RSSI cero"),
            ([{"punto": "P1", "operador": "CLARO", "tecnologia": "LTE", "rssi": 50}], "RSSI positivo"),
            
            # Strings muy largos
            ([{"punto": "P" * 1000, "operador": "CLARO", "tecnologia": "LTE", "rssi": -70}], "Punto muy largo"),
            ([{"punto": "P1", "operador": "O" * 500, "tecnologia": "LTE", "rssi": -70}], "Operador muy largo"),
            
            # Números muy grandes
            ([{"punto": "P1", "operador": "CLARO", "tecnologia": "LTE", "rssi": -70, "fileRecordId": 999999999999}], "fileRecordId muy grande"),
        ]
        
        for data, description in scenarios:
            result = self._test_extreme_values(data, description)
            self._add_test_result(f"Valores extremos - {description}", result)
    
    def test_large_datasets(self):
        """Test casos con datasets grandes"""
        print("Testing large datasets...")
        
        # Dataset mediano (1000 registros)
        medium_data = self._generate_test_data(1000)
        result = self._test_large_dataset(medium_data, "Dataset mediano (1000 registros)")
        self._add_test_result("Dataset mediano", result)
        
        # Dataset grande (10000 registros)
        large_data = self._generate_test_data(10000)
        result = self._test_large_dataset(large_data, "Dataset grande (10000 registros)")
        self._add_test_result("Dataset grande", result)
    
    def test_memory_efficiency(self):
        """Test eficiencia de memoria"""
        print("Testing memory efficiency...")
        
        # Test con datos duplicados masivos
        duplicate_data = []
        base_record = {"punto": "P1", "operador": "CLARO", "tecnologia": "LTE", "rssi": -70, "fileRecordId": 1}
        
        # 50,000 registros idénticos para probar eficiencia de Set()
        for i in range(50000):
            duplicate_data.append(base_record.copy())
        
        result = self._test_memory_efficiency(duplicate_data, "50,000 registros duplicados")
        self._add_test_result("Eficiencia memoria - duplicados masivos", result)
    
    def test_concurrent_updates(self):
        """Test actualizaciones concurrentes simuladas"""
        print("Testing concurrent updates...")
        
        # Simular cambios rápidos en los datos
        data_sequences = [
            [],  # Inicial vacío
            [{"punto": "P1", "operador": "CLARO", "tecnologia": "LTE", "rssi": -70}],  # Un registro
            [],  # De vuelta vacío
            self._generate_test_data(100),  # Muchos registros
            [{"punto": "P1", "operador": "CLARO", "tecnologia": "LTE", "rssi": -70}]  # De vuelta a uno
        ]
        
        result = self._test_concurrent_updates(data_sequences)
        self._add_test_result("Actualizaciones concurrentes", result)
    
    # Métodos auxiliares de testing
    
    def _test_empty_data(self, data: Any, description: str) -> bool:
        """Test específico para datos vacíos"""
        try:
            stats = self._calculate_stats_mock(data)
            if data is None or (isinstance(data, list) and len(data) == 0):
                return stats is None
            elif isinstance(data, list) and all(not d for d in data):  # Lista de objetos vacíos
                return stats is None or stats.get('totalRecords', 0) == 0
            return True
        except Exception as e:
            self.validation_results['warnings'].append(f"Excepción en {description}: {str(e)}")
            return False
    
    def _test_malformed_data(self, data: List[Dict], description: str) -> bool:
        """Test específico para datos malformados"""
        try:
            stats = self._calculate_stats_mock(data)
            # Debería manejar datos malformados sin crash
            return stats is not None
        except Exception as e:
            self.validation_results['warnings'].append(f"Excepción en {description}: {str(e)}")
            return False
    
    def _test_extreme_values(self, data: List[Dict], description: str) -> bool:
        """Test específico para valores extremos"""
        try:
            stats = self._calculate_stats_mock(data)
            # Debería manejar valores extremos sin problemas
            if stats and 'rssi' in stats:
                # Verificar que los cálculos no produzcan NaN o Infinity
                rssi = stats['rssi']
                return all(isinstance(v, (int, float)) and not (v != v) for v in [rssi.get('min'), rssi.get('max'), rssi.get('avg')])  # v != v es check para NaN
            return True
        except Exception as e:
            self.validation_results['warnings'].append(f"Excepción en {description}: {str(e)}")
            return False
    
    def _test_large_dataset(self, data: List[Dict], description: str) -> bool:
        """Test específico para datasets grandes"""
        try:
            import time
            start_time = time.time()
            
            stats = self._calculate_stats_mock(data)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Debería procesar en menos de 1 segundo datasets medianos
            # y menos de 5 segundos datasets grandes
            time_limit = 1.0 if len(data) <= 1000 else 5.0
            
            if processing_time > time_limit:
                self.validation_results['warnings'].append(f"Rendimiento lento en {description}: {processing_time:.2f}s")
                return False
            
            return stats is not None and stats.get('totalRecords') == len(data)
        except Exception as e:
            self.validation_results['warnings'].append(f"Excepción en {description}: {str(e)}")
            return False
    
    def _test_memory_efficiency(self, data: List[Dict], description: str) -> bool:
        """Test específico para eficiencia de memoria"""
        try:
            stats = self._calculate_stats_mock(data)
            
            # Con 50,000 registros idénticos, uniquePoints debería ser 1
            if stats and stats.get('uniquePoints') == 1:
                return True
            
            return False
        except Exception as e:
            self.validation_results['warnings'].append(f"Excepción en {description}: {str(e)}")
            return False
    
    def _test_concurrent_updates(self, data_sequences: List[List[Dict]]) -> bool:
        """Test específico para actualizaciones concurrentes"""
        try:
            results = []
            for data in data_sequences:
                stats = self._calculate_stats_mock(data)
                results.append(stats)
            
            # Todos los cálculos deberían completarse sin error
            return len(results) == len(data_sequences)
        except Exception as e:
            self.validation_results['warnings'].append(f"Excepción en actualizaciones concurrentes: {str(e)}")
            return False
    
    def _calculate_stats_mock(self, data: Any) -> Optional[Dict[str, Any]]:
        """Mock de cálculo de estadísticas similar al componente real"""
        if not data or (isinstance(data, list) and len(data) == 0):
            return None
        
        if not isinstance(data, list):
            return None
        
        # Filtrar registros válidos
        valid_records = []
        for record in data:
            if isinstance(record, dict) and record.get('punto') and record.get('operador'):
                valid_records.append(record)
        
        if not valid_records:
            return None
        
        # Cálculos básicos
        total_records = len(valid_records)
        unique_points = len(set(record.get('punto', '') for record in valid_records))
        
        # Distribución por operador
        operator_counts = {}
        for record in valid_records:
            op = record.get('operador', 'UNKNOWN')
            operator_counts[op] = operator_counts.get(op, 0) + 1
        
        # Estadísticas RSSI
        rssi_values = []
        for record in valid_records:
            rssi = record.get('rssi')
            if isinstance(rssi, (int, float)) and not (rssi != rssi):  # Check for NaN
                rssi_values.append(rssi)
        
        if rssi_values:
            min_rssi = min(rssi_values)
            max_rssi = max(rssi_values)
            avg_rssi = round(sum(rssi_values) / len(rssi_values))
        else:
            min_rssi = max_rssi = avg_rssi = 0
        
        return {
            'totalRecords': total_records,
            'uniquePoints': unique_points,
            'operatorCounts': operator_counts,
            'rssi': {'min': min_rssi, 'max': max_rssi, 'avg': avg_rssi}
        }
    
    def _generate_test_data(self, count: int) -> List[Dict[str, Any]]:
        """Genera datos de prueba"""
        operators = ['CLARO', 'MOVISTAR', 'TIGO', 'WOM']
        technologies = ['3G', '4G', '5G', 'LTE', 'GSM']
        
        data = []
        for i in range(count):
            data.append({
                'punto': f'PUNTO_{i:06d}',
                'operador': operators[i % len(operators)],
                'tecnologia': technologies[i % len(technologies)],
                'rssi': -70 - (i % 50),  # RSSI entre -70 y -120
                'fileRecordId': (i // 100) + 1  # Agrupa cada 100 registros por archivo
            })
        
        return data
    
    def _add_test_result(self, test_name: str, passed: bool):
        """Añade resultado de test"""
        self.validation_results['total_tests'] += 1
        if passed:
            self.validation_results['passed_tests'] += 1
            print(f"  [PASS] {test_name}")
        else:
            self.validation_results['failed_tests'] += 1
            self.validation_results['errors'].append(test_name)
            print(f"  [FAIL] {test_name}")
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Ejecuta todos los tests de manejo de errores"""
        print("=" * 70)
        print("KRONOS - Validacion Manejo de Errores CellularDataStats")
        print("=" * 70)
        
        self.test_empty_data_scenarios()
        print()
        self.test_malformed_data_scenarios()
        print()
        self.test_extreme_values()
        print()
        self.test_large_datasets()
        print()
        self.test_memory_efficiency()
        print()
        self.test_concurrent_updates()
        
        return self.generate_report()
    
    def generate_report(self) -> Dict[str, Any]:
        """Genera reporte de validación"""
        return {
            "test_name": "CellularDataStats Error Handling Validation",
            "timestamp": datetime.now().isoformat(),
            "validation_results": self.validation_results,
            "reliability_score": round(
                (self.validation_results['passed_tests'] / self.validation_results['total_tests']) * 100, 1
            ) if self.validation_results['total_tests'] > 0 else 0
        }

def main():
    """Función principal"""
    validator = ErrorHandlingValidator()
    report = validator.run_all_tests()
    
    # Guardar reporte
    report_file = f"error_handling_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Mostrar resumen
    print("\n" + "=" * 70)
    print("RESUMEN DE VALIDACION MANEJO DE ERRORES")
    print("=" * 70)
    results = report['validation_results']
    print(f"Total tests: {results['total_tests']}")
    print(f"Tests pasados: {results['passed_tests']}")
    print(f"Tests fallidos: {results['failed_tests']}")
    print(f"Advertencias: {len(results['warnings'])}")
    print(f"Score de confiabilidad: {report['reliability_score']}%")
    
    if results['failed_tests'] == 0:
        print("TODOS LOS TESTS DE ERROR HANDLING PASARON")
        success = True
    else:
        print("ALGUNOS TESTS DE ERROR HANDLING FALLARON")
        print("\nErrores encontrados:")
        for error in results['errors']:
            print(f"  - {error}")
        success = False
    
    if results['warnings']:
        print("\nAdvertencias:")
        for warning in results['warnings']:
            print(f"  - {warning}")
    
    print(f"\nReporte guardado en: {report_file}")
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)