#!/usr/bin/env python3
"""
KRONOS - FIX CRÍTICO PARA TERMINADORES DE LÍNEA CLARO
========================================================================
Fix específico para el problema del archivo DATOS_POR_CELDA CLARO.csv
que usa terminadores CR (\r) en lugar de LF (\n) o CRLF (\r\n).

PROBLEMA IDENTIFICADO:
- Archivo usa terminadores CR (\r) únicamente
- Pandas y herramientas estándar no los interpretan correctamente
- Resultado: 99,000 registros aparecen como concatenados sin saltos de línea

SOLUCIÓN:
1. Detectar archivos con terminadores CR
2. Convertir CR a LF o CRLF
3. Recrear archivo con terminadores estándar
4. Validar que el conteo sea correcto

MODO DE USO:
python claro_line_terminator_fix.py
========================================================================
"""

import sys
import os
import pandas as pd
from pathlib import Path

# Agregar directorio Backend al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class LineTerminatorFixer:
    """Fix para archivos CLARO con terminadores de línea incorrectos"""
    
    def __init__(self):
        self.test_files = [
            Path('../datatest/Claro/DATOS_POR_CELDA CLARO.csv'),
            Path('../datatest/Claro/LLAMADAS_ENTRANTES_POR_CELDA CLARO.csv'),
            Path('../datatest/Claro/LLAMADAS_SALIENTES_POR_CELDA CLARO.csv')
        ]
    
    def detect_line_terminators(self, file_path):
        """Detecta el tipo de terminadores de línea en un archivo"""
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Contar diferentes tipos de terminadores
        cr_count = content.count(b'\r')
        lf_count = content.count(b'\n')
        crlf_count = content.count(b'\r\n')
        
        # Determinar tipo predominante
        if crlf_count > 0:
            terminator_type = 'CRLF'
            line_count = crlf_count + 1
        elif lf_count > cr_count:
            terminator_type = 'LF'
            line_count = lf_count + 1
        elif cr_count > 0:
            terminator_type = 'CR'
            line_count = cr_count + 1
        else:
            terminator_type = 'NONE'
            line_count = 1
        
        return {
            'terminator_type': terminator_type,
            'line_count': line_count,
            'cr_count': cr_count,
            'lf_count': lf_count,
            'crlf_count': crlf_count,
            'file_size': len(content)
        }
    
    def fix_line_terminators(self, input_path, output_path=None, target_terminator='LF'):
        """
        Corrige terminadores de línea en archivo
        
        Args:
            input_path: Ruta del archivo malformado
            output_path: Ruta del archivo corregido (opcional)
            target_terminator: 'LF', 'CRLF', o 'CR'
        
        Returns:
            Dict con resultados del fix
        """
        if output_path is None:
            output_path = str(input_path).replace('.csv', '_FIXED_TERMINATORS.csv')
        
        print(f"[FIX] Procesando archivo: {input_path}")
        
        # Leer archivo en modo binario
        with open(input_path, 'rb') as f:
            content = f.read()
        
        original_info = self.detect_line_terminators(input_path)
        print(f"[FIX] Terminadores originales: {original_info['terminator_type']}")
        print(f"[FIX] Líneas detectadas: {original_info['line_count']:,}")
        
        # Normalizar terminadores
        # Primero convertir todo a LF
        content_normalized = content.replace(b'\r\n', b'\n')  # CRLF -> LF
        content_normalized = content_normalized.replace(b'\r', b'\n')  # CR -> LF
        
        # Luego convertir a terminador objetivo si es necesario
        if target_terminator == 'CRLF':
            content_final = content_normalized.replace(b'\n', b'\r\n')
        elif target_terminator == 'CR':
            content_final = content_normalized.replace(b'\n', b'\r')
        else:  # LF
            content_final = content_normalized
        
        # Escribir archivo corregido
        with open(output_path, 'wb') as f:
            f.write(content_final)
        
        # Verificar archivo corregido
        fixed_info = self.detect_line_terminators(output_path)
        verification = self._verify_fixed_file(output_path)
        
        result = {
            'success': True,
            'input_file': str(input_path),
            'output_file': output_path,
            'original_terminators': original_info,
            'fixed_terminators': fixed_info,
            'verification': verification
        }
        
        print(f"[SUCCESS] Archivo corregido guardado: {output_path}")
        print(f"[SUCCESS] Terminadores convertidos: {original_info['terminator_type']} -> {fixed_info['terminator_type']}")
        print(f"[SUCCESS] Líneas: {original_info['line_count']:,} -> {fixed_info['line_count']:,}")
        
        return result
    
    def _verify_fixed_file(self, file_path):
        """Verifica que el archivo corregido sea válido"""
        try:
            # Probar lectura con pandas
            df = pd.read_csv(file_path)
            
            return {
                'pandas_valid': True,
                'pandas_rows': len(df),
                'pandas_columns': len(df.columns),
                'column_names': list(df.columns),
                'sample_data': df.head(3).to_dict('records') if len(df) > 0 else []
            }
        except Exception as e:
            return {
                'pandas_valid': False,
                'pandas_error': str(e)
            }
    
    def process_all_test_files(self):
        """Procesa todos los archivos de prueba CLARO"""
        results = {}
        
        print("KRONOS - FIX TERMINADORES DE LÍNEA CLARO")
        print("=" * 60)
        
        for file_path in self.test_files:
            if not file_path.exists():
                print(f"[WARNING] Archivo no encontrado: {file_path}")
                continue
            
            print(f"\n{'='*60}")
            print(f"PROCESANDO: {file_path.name}")
            print(f"{'='*60}")
            
            # Analizar terminadores originales
            original_info = self.detect_line_terminators(file_path)
            
            print(f"[ANALYSIS] Información del archivo original:")
            print(f"  - Tamaño: {original_info['file_size']:,} bytes")
            print(f"  - Terminadores: {original_info['terminator_type']}")
            print(f"  - Líneas detectadas: {original_info['line_count']:,}")
            print(f"  - CR: {original_info['cr_count']:,}")
            print(f"  - LF: {original_info['lf_count']:,}")
            print(f"  - CRLF: {original_info['crlf_count']:,}")
            
            # Detectar si necesita corrección
            needs_fix = original_info['terminator_type'] == 'CR'
            
            if needs_fix:
                print(f"[DETECTED] Archivo necesita corrección de terminadores")
                
                # Aplicar fix
                fix_result = self.fix_line_terminators(file_path)
                results[str(file_path)] = fix_result
                
                if fix_result['success']:
                    # Probar lectura con pandas
                    print(f"\n[VERIFICATION] Verificando archivo corregido...")
                    verification = fix_result['verification']
                    
                    if verification['pandas_valid']:
                        print(f"  - Pandas lee correctamente: {verification['pandas_rows']:,} registros")
                        print(f"  - Columnas: {verification['column_names']}")
                        
                        if verification['sample_data']:
                            print(f"  - Muestra de datos:")
                            for i, record in enumerate(verification['sample_data'][:3]):
                                print(f"    Registro {i+1}: {record}")
                    else:
                        print(f"  - ERROR leyendo archivo corregido: {verification['pandas_error']}")
                
            else:
                print(f"[OK] Archivo ya tiene terminadores correctos ({original_info['terminator_type']})")
                results[str(file_path)] = {
                    'success': True, 
                    'needs_fix': False,
                    'original_terminators': original_info
                }
        
        return results
    
    def generate_comparison_report(self, results):
        """Genera reporte comparativo de resultados"""
        print(f"\n{'='*60}")
        print("REPORTE COMPARATIVO - ANTES Y DESPUÉS")
        print("=" * 60)
        
        for file_path, result in results.items():
            file_name = Path(file_path).name
            print(f"\n📁 {file_name}")
            print("-" * 40)
            
            if result.get('needs_fix') is False:
                orig = result['original_terminators']
                print(f"  Status: OK - Ya tiene terminadores {orig['terminator_type']}")
                print(f"  Líneas: {orig['line_count']:,}")
            elif result.get('success'):
                orig = result['original_terminators']
                fixed = result['fixed_terminators']
                verif = result['verification']
                
                print(f"  Status: CORREGIDO EXITOSAMENTE")
                print(f"  Terminadores: {orig['terminator_type']} -> {fixed['terminator_type']}")
                print(f"  Líneas: {orig['line_count']:,} -> {fixed['line_count']:,}")
                
                if verif['pandas_valid']:
                    print(f"  Pandas registros: {verif['pandas_rows']:,}")
                    print(f"  Columnas: {len(verif['column_names'])}")
                else:
                    print(f"  ERROR Pandas: {verif['pandas_error']}")
            else:
                print(f"  Status: ERROR - {result.get('error', 'Desconocido')}")


def main():
    """Función principal"""
    fixer = LineTerminatorFixer()
    results = fixer.process_all_test_files()
    fixer.generate_comparison_report(results)


if __name__ == "__main__":
    main()