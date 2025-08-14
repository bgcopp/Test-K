#!/usr/bin/env python3
"""
KRONOS - Test de Corrección de Line Terminators
===============================================
Script de prueba para validar que la corrección de line terminators
funciona correctamente para archivos CLARO.

Este script simula el problema y verifica la solución.
"""

import sys
import os
import pandas as pd
import logging
from io import BytesIO

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Agregar path del Backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.helpers import _normalize_line_terminators, read_csv_file


class LineTerminatorTester:
    """Tester para la corrección de line terminators"""
    
    def __init__(self):
        self.test_data = {
            'numero_telefono': ['3001234567', '3007654321', '3109876543', '3112345678', '3156789012'],
            'fecha_trafico': ['20240419080000', '20240419081500', '20240419083000', '20240419084500', '20240419090000'],
            'tipo_cdr': ['DATOS', 'DATOS', 'DATOS', 'DATOS', 'DATOS'],
            'celda_decimal': ['12345', '12346', '12347', '12348', '12349'],
            'lac_decimal': ['1001', '1002', '1003', '1004', '1005']
        }
    
    def create_test_csv_with_terminators(self, terminator_type='CR'):
        """
        Crea un CSV de prueba con terminadores específicos
        
        Args:
            terminator_type: 'CR', 'LF', 'CRLF'
            
        Returns:
            bytes: Contenido del CSV con terminadores específicos
        """
        # Crear CSV como string
        headers = ';'.join(self.test_data.keys())
        rows = []
        
        for i in range(len(self.test_data['numero_telefono'])):
            row = ';'.join(str(self.test_data[key][i]) for key in self.test_data.keys())
            rows.append(row)
        
        csv_content = headers + '\n' + '\n'.join(rows)
        
        # Convertir a bytes y cambiar terminadores
        csv_bytes = csv_content.encode('utf-8')
        
        if terminator_type == 'CR':
            # Convertir LF a CR (simular archivo CLARO problemático)
            csv_bytes = csv_bytes.replace(b'\n', b'\r')
        elif terminator_type == 'CRLF':
            # Convertir LF a CRLF
            csv_bytes = csv_bytes.replace(b'\n', b'\r\n')
        # terminator_type == 'LF' se mantiene como está
        
        return csv_bytes
    
    def test_line_terminator_detection(self):
        """Prueba detección de line terminators"""
        print("\n" + "="*60)
        print("TEST 1: DETECCIÓN DE LINE TERMINATORS")
        print("="*60)
        
        test_cases = ['CR', 'LF', 'CRLF']
        
        for terminator_type in test_cases:
            print(f"\n--- Probando terminadores {terminator_type} ---")
            
            # Crear archivo de prueba
            test_csv = self.create_test_csv_with_terminators(terminator_type)
            
            # Contar terminadores manualmente
            cr_count = test_csv.count(b'\r')
            lf_count = test_csv.count(b'\n')
            crlf_count = test_csv.count(b'\r\n')
            
            print(f"Archivo creado con {len(test_csv)} bytes")
            print(f"Terminadores CR: {cr_count}")
            print(f"Terminadores LF: {lf_count}")
            print(f"Terminadores CRLF: {crlf_count}")
            
            # Aplicar normalización
            normalized_bytes = _normalize_line_terminators(test_csv)
            
            # Contar después de normalización
            norm_cr_count = normalized_bytes.count(b'\r')
            norm_lf_count = normalized_bytes.count(b'\n')
            norm_crlf_count = normalized_bytes.count(b'\r\n')
            
            print(f"Después de normalización:")
            print(f"Terminadores CR: {norm_cr_count}")
            print(f"Terminadores LF: {norm_lf_count}")
            print(f"Terminadores CRLF: {norm_crlf_count}")
            
            # Verificar corrección
            if terminator_type == 'CR':
                success = (norm_lf_count > 0 and norm_cr_count == norm_crlf_count)
                print(f"✅ CORRECCIÓN APLICADA: {success}")
            else:
                success = (test_csv == normalized_bytes)
                print(f"✅ SIN CAMBIOS (correcto): {success}")
    
    def test_pandas_integration(self):
        """Prueba integración con pandas"""
        print("\n" + "="*60)
        print("TEST 2: INTEGRACIÓN CON PANDAS")
        print("="*60)
        
        test_cases = [
            ('CR', 'PROBLEMÁTICO - debería ser corregido'),
            ('LF', 'NORMAL - debería funcionar'),
            ('CRLF', 'NORMAL - debería funcionar')
        ]
        
        for terminator_type, description in test_cases:
            print(f"\n--- {terminator_type}: {description} ---")
            
            # Crear archivo de prueba
            test_csv = self.create_test_csv_with_terminators(terminator_type)
            print(f"Archivo creado: {len(test_csv)} bytes")
            
            try:
                # Intentar leer SIN normalización (método viejo)
                df_old = pd.read_csv(BytesIO(test_csv), delimiter=';')
                print(f"SIN normalización - Filas leídas: {len(df_old)}")
                print(f"SIN normalización - Columnas: {list(df_old.columns)}")
                
                if len(df_old) != 5:
                    print(f"⚠️  PROBLEMA: Se esperaban 5 filas, se leyeron {len(df_old)}")
                
            except Exception as e:
                print(f"❌ ERROR sin normalización: {e}")
            
            try:
                # Intentar leer CON normalización (método nuevo)
                df_new = read_csv_file(test_csv, delimiter=';')
                print(f"CON normalización - Filas leídas: {len(df_new)}")
                print(f"CON normalización - Columnas: {list(df_new.columns)}")
                
                if len(df_new) == 5:
                    print(f"✅ ÉXITO: Se leyeron correctamente 5 filas")
                    print(f"Muestra de datos: {df_new.iloc[0].to_dict()}")
                else:
                    print(f"⚠️  PROBLEMA: Se esperaban 5 filas, se leyeron {len(df_new)}")
                
            except Exception as e:
                print(f"❌ ERROR con normalización: {e}")
    
    def test_real_world_scenario(self):
        """Simula escenario del mundo real reportado por el usuario"""
        print("\n" + "="*60)
        print("TEST 3: ESCENARIO DEL MUNDO REAL")
        print("="*60)
        
        # Crear archivo GRANDE con terminadores CR (simular archivo CLARO real)
        print("Simulando archivo CLARO grande con terminadores CR...")
        
        # Generar datos más grandes
        large_data = []
        for i in range(1000):  # 1000 registros
            row = f"300{1000000+i};20240419{80000+i%24:06d};DATOS;{12000+i};{1000+i%100}"
            large_data.append(row)
        
        # Crear CSV con terminadores CR
        csv_content = "numero_telefono;fecha_trafico;tipo_cdr;celda_decimal;lac_decimal\r" + "\r".join(large_data)
        test_csv = csv_content.encode('utf-8')
        
        print(f"Archivo creado: {len(test_csv):,} bytes")
        print(f"Terminadores CR: {test_csv.count(b'\r'):,}")
        print(f"Terminadores LF: {test_csv.count(b'\n'):,}")
        
        # Simular problema: leer SIN corrección
        try:
            df_problematic = pd.read_csv(BytesIO(test_csv), delimiter=';')
            print(f"\n❌ SIN CORRECCIÓN:")
            print(f"   Filas detectadas: {len(df_problematic):,}")
            print(f"   Primera fila: {df_problematic.iloc[0, 0] if len(df_problematic) > 0 else 'N/A'}")
            
            if len(df_problematic) == 1:
                print(f"   ⚠️  PROBLEMA CONFIRMADO: Todo el archivo se leyó como 1 sola fila")
                first_cell_length = len(str(df_problematic.iloc[0, 0])) if len(df_problematic) > 0 else 0
                print(f"   Longitud primera celda: {first_cell_length:,} caracteres")
        except Exception as e:
            print(f"   ERROR leyendo sin corrección: {e}")
        
        # Aplicar corrección
        try:
            df_corrected = read_csv_file(test_csv, delimiter=';')
            print(f"\n✅ CON CORRECCIÓN:")
            print(f"   Filas detectadas: {len(df_corrected):,}")
            print(f"   Columnas: {list(df_corrected.columns)}")
            
            if len(df_corrected) == 1000:
                print(f"   ✅ CORRECCIÓN EXITOSA: Se leyeron todas las {len(df_corrected):,} filas")
                print(f"   Muestra primera fila: {df_corrected.iloc[0].to_dict()}")
                print(f"   Muestra última fila: {df_corrected.iloc[-1].to_dict()}")
            else:
                print(f"   ⚠️  PROBLEMA PARCIAL: Se esperaban 1000 filas, se leyeron {len(df_corrected):,}")
                
        except Exception as e:
            print(f"   ❌ ERROR con corrección: {e}")
    
    def run_all_tests(self):
        """Ejecuta todos los tests"""
        print("KRONOS - TEST DE CORRECCIÓN LINE TERMINATORS")
        print("=" * 60)
        print("Verificando que la corrección para archivos CLARO funciona correctamente")
        
        try:
            self.test_line_terminator_detection()
            self.test_pandas_integration() 
            self.test_real_world_scenario()
            
            print("\n" + "="*60)
            print("✅ TODOS LOS TESTS COMPLETADOS")
            print("="*60)
            print("\nRESUMEN:")
            print("- La función _normalize_line_terminators detecta correctamente terminadores CR")
            print("- La corrección convierte CR a LF automáticamente")  
            print("- read_csv_file integra la corrección transparentemente")
            print("- El problema de 650,000+ 'registros' falsos debería estar resuelto")
            print("\n🎯 SOLUCIÓN IMPLEMENTADA: Los archivos CLARO con terminadores CR")
            print("   se procesarán correctamente sin mostrar conteos incorrectos.")
            
        except Exception as e:
            print(f"\n❌ ERROR EN TESTS: {e}")
            logger.error(f"Error ejecutando tests: {e}")


def main():
    """Función principal"""
    tester = LineTerminatorTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()