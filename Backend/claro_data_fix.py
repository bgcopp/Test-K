#!/usr/bin/env python3
"""
KRONOS - FIX CRÍTICO PARA ARCHIVOS CLARO MALFORMADOS
========================================================================
Fix específico para el problema del archivo DATOS_POR_CELDA CLARO.csv
que tiene datos concatenados en una sola línea sin separadores.

PROBLEMA IDENTIFICADO:
- Archivo de 500,433 bytes con solo 2 líneas
- Primera línea contiene 99,000 registros concatenados sin separadores de línea
- Pandas detecta registros incorrectamente

SOLUCIÓN:
1. Detectar archivos con datos concatenados
2. Procesar línea por línea manualmente
3. Extraer registros individuales basado en patrón de datos CLARO
4. Reconstruir CSV con formato correcto

MODO DE USO:
python claro_data_fix.py
========================================================================
"""

import sys
import os
import re
import pandas as pd
from pathlib import Path

# Agregar directorio Backend al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class ClaroDataFixer:
    """Fix para archivos CLARO con datos concatenados"""
    
    def __init__(self):
        self.claro_datos_pattern = re.compile(
            r'(\d{11,}),(\d{14}),(DATOS),(\d+),(\d+)'
        )
        
    def detect_concatenated_file(self, file_path):
        """Detecta si un archivo tiene datos concatenados"""
        with open(file_path, 'rb') as f:
            content = f.read()
        
        line_count = content.count(b'\n') + 1 if content else 0
        file_size = len(content)
        
        # Si archivo grande (>100KB) pero solo 1-2 líneas, probablemente concatenado
        if file_size > 100000 and line_count <= 2:
            first_line = content.split(b'\n')[0]
            if len(first_line) > 50000:  # Primera línea muy larga
                return True, {
                    'file_size': file_size,
                    'line_count': line_count,
                    'first_line_length': len(first_line)
                }
        
        return False, None
    
    def fix_datos_concatenated_file(self, input_path, output_path=None):
        """
        Corrige archivo de datos CLARO con registros concatenados
        
        Args:
            input_path: Ruta del archivo malformado
            output_path: Ruta del archivo corregido (opcional)
        
        Returns:
            Dict con resultados del fix
        """
        if output_path is None:
            output_path = input_path.replace('.csv', '_FIXED.csv')
        
        print(f"[FIX] Procesando archivo: {input_path}")
        
        # Leer archivo completo
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        header = lines[0].strip()
        
        print(f"[FIX] Header detectado: {header}")
        
        # Procesar línea con datos concatenados
        data_line = lines[1] if len(lines) > 1 else ""
        
        if not data_line:
            print("[ERROR] No hay datos para procesar")
            return {'success': False, 'error': 'Sin datos'}
        
        print(f"[FIX] Procesando línea de {len(data_line):,} caracteres")
        
        # Extraer registros usando regex
        matches = self.claro_datos_pattern.findall(data_line)
        
        print(f"[FIX] Registros extraídos: {len(matches):,}")
        
        if not matches:
            print("[ERROR] No se pudieron extraer registros válidos")
            return {'success': False, 'error': 'Sin registros extraíbles'}
        
        # Escribir archivo corregido
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            # Escribir header
            f.write(header + '\n')
            
            # Escribir registros
            for match in matches:
                numero, fecha_trafico, tipo_cdr, celda_decimal, lac_decimal = match
                f.write(f"{numero},{fecha_trafico},{tipo_cdr},{celda_decimal},{lac_decimal}\n")
        
        # Verificar archivo corregido
        verification = self._verify_fixed_file(output_path)
        
        result = {
            'success': True,
            'input_file': input_path,
            'output_file': output_path,
            'original_records_detected': len(matches),
            'verification': verification
        }
        
        print(f"[SUCCESS] Archivo corregido guardado: {output_path}")
        print(f"[SUCCESS] Registros procesados: {len(matches):,}")
        
        return result
    
    def _verify_fixed_file(self, file_path):
        """Verifica que el archivo corregido sea válido"""
        try:
            df = pd.read_csv(file_path)
            
            return {
                'valid': True,
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': list(df.columns)
            }
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    def process_claro_test_files(self):
        """Procesa archivos de prueba CLARO"""
        test_files = [
            Path('../datatest/Claro/DATOS_POR_CELDA CLARO.csv')
        ]
        
        results = {}
        
        for file_path in test_files:
            if not file_path.exists():
                print(f"[WARNING] Archivo no encontrado: {file_path}")
                continue
            
            print(f"\n{'='*60}")
            print(f"PROCESANDO: {file_path.name}")
            print(f"{'='*60}")
            
            # Detectar si archivo está concatenado
            is_concatenated, concat_info = self.detect_concatenated_file(file_path)
            
            if is_concatenated:
                print(f"[DETECTED] Archivo concatenado detectado:")
                print(f"  - Tamaño: {concat_info['file_size']:,} bytes")
                print(f"  - Líneas: {concat_info['line_count']}")
                print(f"  - Primera línea: {concat_info['first_line_length']:,} caracteres")
                
                # Aplicar fix
                fix_result = self.fix_datos_concatenated_file(str(file_path))
                results[str(file_path)] = fix_result
                
                if fix_result['success']:
                    # Probar lectura con pandas
                    print(f"\n[VERIFICATION] Verificando archivo corregido...")
                    try:
                        df_fixed = pd.read_csv(fix_result['output_file'])
                        print(f"  - Pandas lee correctamente: {len(df_fixed):,} registros")
                        print(f"  - Columnas: {list(df_fixed.columns)}")
                        print(f"  - Muestra de datos:")
                        print(df_fixed.head(3).to_string(index=False))
                    except Exception as e:
                        print(f"  - ERROR leyendo archivo corregido: {e}")
                
            else:
                print(f"[OK] Archivo parece estar bien formateado")
                results[str(file_path)] = {'success': True, 'needs_fix': False}
        
        return results


def main():
    """Función principal"""
    print("KRONOS - FIX CRÍTICO ARCHIVOS CLARO CONCATENADOS")
    print("=" * 60)
    
    fixer = ClaroDataFixer()
    results = fixer.process_claro_test_files()
    
    print(f"\n{'='*60}")
    print("RESUMEN DE RESULTADOS")
    print("=" * 60)
    
    for file_path, result in results.items():
        print(f"\nArchivo: {Path(file_path).name}")
        if result.get('needs_fix') is False:
            print("  Status: OK - No requiere corrección")
        elif result.get('success'):
            print(f"  Status: CORREGIDO EXITOSAMENTE")
            print(f"  Registros: {result.get('original_records_detected', 'N/A'):,}")
            print(f"  Archivo corregido: {result.get('output_file', 'N/A')}")
        else:
            print(f"  Status: ERROR - {result.get('error', 'Desconocido')}")


if __name__ == "__main__":
    main()