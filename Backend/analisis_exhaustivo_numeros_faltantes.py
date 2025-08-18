"""
Análisis exhaustivo de números faltantes en archivos CLARO
Investiga por qué 4 números específicos no aparecen en BD
Boris - KRONOS Data Engineering
"""

import pandas as pd
import sqlite3
import re
import json
import os
from pathlib import Path
from datetime import datetime
import openpyxl
from typing import List, Dict, Set, Tuple

class ExhaustiveNumberAnalyzer:
    
    def __init__(self):
        self.target_numbers = [
            '3224274851', '3208611034', '3104277553', 
            '3102715509', '3143534707', '3214161903'
        ]
        
        # Patrones de búsqueda exhaustivos
        self.search_patterns = [
            # Formato base
            '{number}',
            # Con prefijo 57
            '57{number}',
            '+57{number}',
            '(57){number}',
            # Con espacios y separadores
            '57 {number}',
            '+57 {number}',
            '57-{number}',
            '+57-{number}',
            # Formato internacional
            '0057{number}',
            '00-57-{number}',
            # Con separadores internos
            '{number[:3]}-{number[3:6]}-{number[6:]}',
            '{number[:3]} {number[3:6]} {number[6:]}',
            # Variaciones de celdas específicas
            'CELL_{number}',
            '{number}_CELL'
        ]
        
        self.results = {
            'analysis_timestamp': datetime.now().isoformat(),
            'target_numbers': self.target_numbers,
            'file_analysis': {},
            'database_analysis': {},
            'conclusions': {},
            'recommendations': []
        }
    
    def generate_number_variations(self, number: str) -> List[str]:
        """Genera todas las variaciones posibles de un número"""
        variations = []
        
        for pattern in self.search_patterns:
            try:
                if '{number[:3]}' in pattern:
                    # Formato con separadores internos
                    variation = pattern.format(
                        number=number,
                        **{f'number[{i}:{j}]': number[i:j] for i in range(0, 4, 3) for j in range(3, 11, 3) if i < len(number) and j <= len(number)}
                    )
                else:
                    variation = pattern.format(number=number)
                variations.append(variation)
            except:
                continue
        
        # Agregar el número tal como está
        variations.append(number)
        
        # Remover duplicados y ordenar
        return sorted(list(set(variations)))
    
    def search_in_dataframe(self, df: pd.DataFrame, number: str, file_path: str) -> Dict:
        """Busca un número en todas las columnas de un DataFrame"""
        
        variations = self.generate_number_variations(number)
        found_locations = []
        
        # Buscar en cada columna
        for col in df.columns:
            if df[col].dtype == 'object':  # Solo columnas de texto
                for variation in variations:
                    # Búsqueda exacta
                    exact_matches = df[df[col].astype(str) == variation]
                    if not exact_matches.empty:
                        for idx in exact_matches.index:
                            found_locations.append({
                                'location': f'Row {idx + 2}, Column {col}',  # +2 por header
                                'value_found': variation,
                                'context': str(df.loc[idx, col]),
                                'full_row': df.loc[idx].to_dict()
                            })
                    
                    # Búsqueda que contiene
                    contains_matches = df[df[col].astype(str).str.contains(variation, regex=False, na=False)]
                    if not contains_matches.empty:
                        for idx in contains_matches.index:
                            if not any(loc['location'].startswith(f'Row {idx + 2}') for loc in found_locations):
                                found_locations.append({
                                    'location': f'Row {idx + 2}, Column {col} (contains)',
                                    'value_found': variation,
                                    'context': str(df.loc[idx, col]),
                                    'full_row': df.loc[idx].to_dict()
                                })
        
        return {
            'file_path': file_path,
            'variations_searched': variations,
            'locations_found': found_locations,
            'total_occurrences': len(found_locations)
        }
    
    def analyze_excel_file(self, file_path: str) -> Dict:
        """Analiza un archivo Excel completo (todas las hojas)"""
        
        file_results = {
            'file_path': file_path,
            'sheets_analyzed': [],
            'numbers_found': {},
            'errors': []
        }
        
        try:
            # Obtener todas las hojas
            excel_file = pd.ExcelFile(file_path)
            
            for sheet_name in excel_file.sheet_names:
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    
                    sheet_analysis = {
                        'sheet_name': sheet_name,
                        'rows': len(df),
                        'columns': list(df.columns),
                        'numbers_found': {}
                    }
                    
                    # Buscar cada número objetivo
                    for number in self.target_numbers:
                        search_result = self.search_in_dataframe(df, number, f"{file_path}#{sheet_name}")
                        if search_result['total_occurrences'] > 0:
                            sheet_analysis['numbers_found'][number] = search_result
                            
                            if number not in file_results['numbers_found']:
                                file_results['numbers_found'][number] = []
                            file_results['numbers_found'][number].extend(search_result['locations_found'])
                    
                    file_results['sheets_analyzed'].append(sheet_analysis)
                    
                except Exception as e:
                    file_results['errors'].append(f"Error en hoja {sheet_name}: {str(e)}")
                    
        except Exception as e:
            file_results['errors'].append(f"Error abriendo archivo: {str(e)}")
        
        return file_results
    
    def analyze_csv_file(self, file_path: str) -> Dict:
        """Analiza un archivo CSV"""
        
        file_results = {
            'file_path': file_path,
            'numbers_found': {},
            'errors': []
        }
        
        try:
            # Intentar diferentes encodings
            encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    break
                except:
                    continue
            
            if df is None:
                file_results['errors'].append("No se pudo leer el archivo con ningún encoding")
                return file_results
            
            # Buscar cada número objetivo
            for number in self.target_numbers:
                search_result = self.search_in_dataframe(df, number, file_path)
                if search_result['total_occurrences'] > 0:
                    file_results['numbers_found'][number] = search_result['locations_found']
                    
        except Exception as e:
            file_results['errors'].append(f"Error procesando CSV: {str(e)}")
        
        return file_results
    
    def analyze_database(self) -> Dict:
        """Analiza la base de datos actual"""
        
        db_results = {
            'connection_success': False,
            'numbers_found': {},
            'search_patterns_used': [],
            'total_records_analyzed': 0
        }
        
        try:
            conn = sqlite3.connect('kronos.db')
            cursor = conn.cursor()
            
            db_results['connection_success'] = True
            
            # Obtener total de registros
            cursor.execute("SELECT COUNT(*) FROM operator_call_data")
            db_results['total_records_analyzed'] = cursor.fetchone()[0]
            
            for number in self.target_numbers:
                variations = self.generate_number_variations(number)
                db_results['search_patterns_used'].extend(variations)
                
                found_records = []
                
                for variation in variations:
                    # Buscar en todos los campos relevantes
                    cursor.execute("""
                        SELECT id, operator, tipo_llamada, numero_origen, numero_destino, numero_objetivo,
                               fecha_hora_llamada, duracion_segundos, celda_origen, celda_destino
                        FROM operator_call_data
                        WHERE numero_origen = ? OR numero_destino = ? OR numero_objetivo = ?
                           OR numero_origen LIKE ? OR numero_destino LIKE ? OR numero_objetivo LIKE ?
                    """, (variation, variation, variation, f'%{variation}%', f'%{variation}%', f'%{variation}%'))
                    
                    records = cursor.fetchall()
                    for record in records:
                        found_records.append({
                            'id': record[0],
                            'operator': record[1],
                            'tipo_llamada': record[2],
                            'numero_origen': record[3],
                            'numero_destino': record[4],
                            'numero_objetivo': record[5],
                            'fecha_hora_llamada': record[6],
                            'duracion_segundos': record[7],
                            'celda_origen': record[8],
                            'celda_destino': record[9],
                            'matched_variation': variation
                        })
                
                if found_records:
                    db_results['numbers_found'][number] = found_records
            
            conn.close()
            
        except Exception as e:
            db_results['error'] = str(e)
        
        return db_results
    
    def run_complete_analysis(self):
        """Ejecuta el análisis completo"""
        
        print("\n" + "="*80)
        print("ANÁLISIS EXHAUSTIVO DE NÚMEROS FALTANTES")
        print("="*80)
        print(f"Números objetivo: {', '.join(self.target_numbers)}")
        print(f"Iniciando análisis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. Análisis de base de datos
        print("\n1. ANALIZANDO BASE DE DATOS...")
        self.results['database_analysis'] = self.analyze_database()
        
        found_in_db = list(self.results['database_analysis']['numbers_found'].keys())
        missing_in_db = [n for n in self.target_numbers if n not in found_in_db]
        
        print(f"   Encontrados en BD: {len(found_in_db)}/6")
        print(f"   Faltantes en BD: {len(missing_in_db)}/6")
        if missing_in_db:
            print(f"   Números faltantes: {', '.join(missing_in_db)}")
        
        # 2. Análisis de archivos
        print("\n2. ANALIZANDO ARCHIVOS FUENTE...")
        
        # Buscar archivos CLARO
        file_patterns = [
            "archivos/envioarchivosparaanalizar*/*.xlsx",
            "datatest/Claro/**/*.xlsx",
            "archivos/CeldasDiferenteOperador/claro/*.xlsx",
            "**/*CLARO*.xlsx",
            "**/*claro*.csv"
        ]
        
        files_to_analyze = []
        for pattern in file_patterns:
            files_to_analyze.extend(Path(".").glob(pattern))
        
        # Remover duplicados
        files_to_analyze = list(set(files_to_analyze))
        
        print(f"   Archivos encontrados: {len(files_to_analyze)}")
        
        for file_path in files_to_analyze:
            if not file_path.exists():
                continue
                
            print(f"   Analizando: {file_path.name}")
            
            if file_path.suffix.lower() == '.xlsx':
                file_result = self.analyze_excel_file(str(file_path))
            elif file_path.suffix.lower() == '.csv':
                file_result = self.analyze_csv_file(str(file_path))
            else:
                continue
            
            self.results['file_analysis'][str(file_path)] = file_result
            
            # Reportar hallazgos inmediatos
            if file_result['numbers_found']:
                for number, locations in file_result['numbers_found'].items():
                    print(f"     *** ENCONTRADO: {number} ({len(locations)} ocurrencias)")
        
        # 3. Generar conclusiones
        print("\n3. GENERANDO CONCLUSIONES...")
        self.generate_conclusions()
        
        # 4. Guardar reporte
        self.save_report()
        
        # 5. Mostrar resumen
        self.print_summary()
    
    def generate_conclusions(self):
        """Genera conclusiones del análisis"""
        
        found_in_db = set(self.results['database_analysis']['numbers_found'].keys())
        
        # Números encontrados en archivos
        found_in_files = set()
        for file_result in self.results['file_analysis'].values():
            found_in_files.update(file_result['numbers_found'].keys())
        
        for number in self.target_numbers:
            in_db = number in found_in_db
            in_files = number in found_in_files
            
            if in_db and in_files:
                conclusion = "PROCESAMIENTO CORRECTO: Número en archivos Y en BD"
                priority = "BAJO"
            elif not in_db and in_files:
                conclusion = "PROBLEMA CRÍTICO: Número en archivos pero NO en BD"
                priority = "CRÍTICO"
            elif in_db and not in_files:
                conclusion = "DATO SINTÉTICO: Número en BD pero no en archivos fuente"
                priority = "INVESTIGAR"
            else:
                conclusion = "NO DISPONIBLE: Número no está en archivos ni BD"
                priority = "VERIFICAR CON PROVEEDOR"
            
            self.results['conclusions'][number] = {
                'in_database': in_db,
                'in_files': in_files,
                'conclusion': conclusion,
                'priority': priority
            }
    
    def save_report(self):
        """Guarda el reporte completo"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"analisis_exhaustivo_numeros_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        self.report_file = report_file
    
    def print_summary(self):
        """Imprime resumen ejecutivo"""
        
        print("\n" + "="*80)
        print("RESUMEN EJECUTIVO")
        print("="*80)
        
        print(f"\nArchivos analizados: {len(self.results['file_analysis'])}")
        print(f"Registros en BD analizados: {self.results['database_analysis'].get('total_records_analyzed', 0)}")
        
        print("\nRESULTADOS POR NÚMERO:")
        print("-" * 50)
        
        for number, conclusion in self.results['conclusions'].items():
            status_icon = "✅" if conclusion['priority'] == "BAJO" else "❌" if conclusion['priority'] == "CRÍTICO" else "⚠️"
            print(f"{status_icon} {number}: {conclusion['conclusion']}")
        
        # Contadores
        criticos = sum(1 for c in self.results['conclusions'].values() if c['priority'] == 'CRÍTICO')
        correctos = sum(1 for c in self.results['conclusions'].values() if c['priority'] == 'BAJO')
        
        print(f"\nPROCESAMIENTO CORRECTO: {correctos}/6 números")
        print(f"PROBLEMAS CRÍTICOS: {criticos}/6 números")
        
        if criticos > 0:
            print(f"\n🚨 SE ENCONTRARON {criticos} PROBLEMAS CRÍTICOS EN EL ALGORITMO")
        else:
            print(f"\n✅ TODOS LOS NÚMEROS DISPONIBLES SE PROCESARON CORRECTAMENTE")
        
        print(f"\nReporte completo guardado en: {self.report_file}")

if __name__ == "__main__":
    analyzer = ExhaustiveNumberAnalyzer()
    analyzer.run_complete_analysis()