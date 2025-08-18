#!/usr/bin/env python3
"""
Test de Regresión para Algoritmo de Correlación
===============================================================================
Asegura que las correcciones al algoritmo de correlación se mantengan
y que no se introduzcan regresiones en futuras modificaciones.

Casos de prueba específicos:
1. Números objetivo conocidos aparecen con formato correcto
2. numero_celular sin prefijo 57, numero_original con prefijo
3. Números con coincidencias de Cell IDs aparecen en resultados
4. Asociación correcta de números con todas las celdas del registro
===============================================================================
"""

import logging
import json
from datetime import datetime
from services.correlation_analysis_service import get_correlation_service

# Configurar logging
logging.basicConfig(level=logging.WARNING)  # Reducir ruido en test
logger = logging.getLogger(__name__)

class CorrelationRegressionTest:
    """Conjunto de tests de regresión para algoritmo de correlación"""
    
    def __init__(self):
        self.service = get_correlation_service()
        self.mission_id = "mission_MPFRBNsb"
        self.start_date = "2021-05-20 10:00:00"
        self.end_date = "2021-05-20 13:20:00"
        self.min_coincidences = 1
    
    def run_all_tests(self):
        """Ejecuta todos los tests de regresión"""
        print("=" * 80)
        print("TEST DE REGRESION: ALGORITMO DE CORRELACION")
        print("=" * 80)
        
        tests = [
            self.test_target_numbers_format,
            self.test_number_normalization,
            self.test_cell_id_association,
            self.test_algorithm_consistency
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                print(f"\nEjecutando: {test.__name__}")
                result = test()
                if result:
                    print(f"PASO: {test.__name__}")
                    passed += 1
                else:
                    print(f"FALLO: {test.__name__}")
                    failed += 1
            except Exception as e:
                print(f"ERROR: {test.__name__} - {e}")
                failed += 1
        
        print("\n" + "=" * 60)
        print("RESUMEN DE TESTS DE REGRESION")
        print("=" * 60)
        print(f"Tests que pasaron: {passed}")
        print(f"Tests que fallaron: {failed}")
        print(f"Porcentaje de exito: {(passed/(passed+failed)*100):.1f}%")
        
        if failed == 0:
            print("\nTODOS LOS TESTS DE REGRESION PASARON")
            print("   El algoritmo mantiene la funcionalidad corregida")
            return True
        else:
            print(f"\n{failed} TEST(S) FALLARON - POSIBLE REGRESION DETECTADA")
            return False
    
    def test_target_numbers_format(self):
        """Test: Números objetivo aparecen con formato correcto"""
        result = self._get_analysis_result()
        if not result:
            return False
        
        # Números objetivo que sabemos que deben aparecer (tienen Cell IDs coincidentes)
        expected_targets = ['3208611034', '3143534707']
        
        found_targets = []
        for correlation in result['data']:
            numero_celular = correlation.get('numero_celular', '')
            if numero_celular in expected_targets:
                found_targets.append(numero_celular)
        
        # Verificar que se encontraron todos los esperados
        missing = set(expected_targets) - set(found_targets)
        if missing:
            print(f"   Numeros objetivo faltantes: {missing}")
            return False
        
        print(f"   Todos los numeros objetivo esperados encontrados: {found_targets}")
        return True
    
    def test_number_normalization(self):
        """Test: numero_celular sin prefijo 57, numero_original con prefijo"""
        result = self._get_analysis_result()
        if not result:
            return False
        
        errors = []
        checked = 0
        
        for correlation in result['data']:
            numero_celular = correlation.get('numero_celular', '')
            numero_original = correlation.get('numero_original', '')
            
            # Verificar que numero_celular NO empiece con 57
            if numero_celular.startswith('57'):
                errors.append(f"numero_celular con prefijo 57: {numero_celular}")
            
            # Verificar que numero_original SÍ empiece con 57 (para números colombianos)
            if len(numero_original) == 12 and not numero_original.startswith('57'):
                errors.append(f"numero_original sin prefijo 57: {numero_original}")
            
            checked += 1
            if checked >= 10:  # Verificar solo primeros 10 para eficiencia
                break
        
        if errors:
            print(f"   Errores de normalizacion encontrados:")
            for error in errors[:5]:  # Mostrar solo primeros 5 errores
                print(f"      {error}")
            return False
        
        print(f"   Normalizacion correcta verificada en {checked} registros")
        return True
    
    def test_cell_id_association(self):
        """Test: Números se asocian correctamente con todas las celdas del registro"""
        # Test específico para 3143534707 que debe tener cell_id 51203
        result = self._get_analysis_result()
        if not result:
            return False
        
        target_correlation = None
        for correlation in result['data']:
            if correlation.get('numero_celular') == '3143534707':
                target_correlation = correlation
                break
        
        if not target_correlation:
            print("   3143534707 no encontrado en resultados")
            return False
        
        celdas_coincidentes = target_correlation.get('celdas_coincidentes', [])
        
        # 3143534707 debe tener cell_id 51203 (que está en HUNTER)
        if '51203' not in celdas_coincidentes:
            print(f"   Cell ID 51203 faltante para 3143534707. Encontrado: {celdas_coincidentes}")
            return False
        
        print(f"   3143534707 correctamente asociado con cell_id 51203")
        return True
    
    def test_algorithm_consistency(self):
        """Test: Algoritmo produce resultados consistentes"""
        # Ejecutar análisis dos veces y verificar que los resultados sean idénticos
        result1 = self._get_analysis_result()
        result2 = self._get_analysis_result()
        
        if not result1 or not result2:
            return False
        
        # Comparar conteos básicos
        count1 = len(result1['data'])
        count2 = len(result2['data'])
        
        if count1 != count2:
            print(f"   Inconsistencia en conteo: {count1} vs {count2}")
            return False
        
        # Comparar algunos números específicos
        numbers1 = set(c.get('numero_celular', '') for c in result1['data'][:10])
        numbers2 = set(c.get('numero_celular', '') for c in result2['data'][:10])
        
        if numbers1 != numbers2:
            print(f"   Inconsistencia en numeros: diferencias encontradas")
            return False
        
        print(f"   Algoritmo produce resultados consistentes ({count1} registros)")
        return True
    
    def _get_analysis_result(self):
        """Obtiene resultado de análisis para tests"""
        try:
            result = self.service.analyze_correlation(
                mission_id=self.mission_id,
                start_date=self.start_date,
                end_date=self.end_date,
                min_coincidences=self.min_coincidences
            )
            
            if not result.get('success'):
                print(f"   Error en analisis: {result.get('error')}")
                return None
            
            return result
            
        except Exception as e:
            print(f"   Excepcion en analisis: {e}")
            return None

def main():
    """Función principal del test de regresión"""
    test_suite = CorrelationRegressionTest()
    success = test_suite.run_all_tests()
    
    if success:
        print("\nALGORITMO DE CORRELACION MANTIENE FUNCIONALIDAD CORREGIDA")
        exit(0)
    else:
        print("\nREGRESION DETECTADA - REVISAR CAMBIOS RECIENTES")
        exit(1)

if __name__ == "__main__":
    main()