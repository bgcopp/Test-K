#!/usr/bin/env python3
"""
ANÁLISIS DE 6 NÚMEROS ESPECÍFICOS EN ARCHIVOS EXCEL - BORIS
========================================================================

Verificación de presencia de números específicos en archivos CLARO:
- 3224274851
- 3208611034
- 3104277553
- 3102715509
- 3143534707
- 3214161903

NO hace cambios en código - solo análisis de datos.

Autor: Data Engineering Algorithm Expert para Boris
Fecha: 2025-08-18
========================================================================
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Any
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Boris6NumbersAnalyzer:
    """
    Analizador especializado para los 6 números específicos de Boris
    """
    
    def __init__(self):
        # Números específicos a verificar (según solicitud de Boris)
        self.target_numbers = [
            '3224274851',
            '3208611034', 
            '3104277553',
            '3102715509',
            '3143534707',
            '3214161903'
        ]
        
        # Archivos Excel de CLARO
        self.excel_files = [
            r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\1-225211_LLAMADAS_ENTRANTES_POR_CELDA_545612_0.xlsx",
            r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\1-225211_LLAMADAS_SALIENTES_POR_CELDA_545613_0.xlsx",
            r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\2-225211_LLAMADAS_ENTRANTES_POR_CELDA_545614_0.xlsx",
            r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\2-225211_LLAMADAS_SALIENTES_POR_CELDA_545615_0.xlsx"
        ]
        
        # Generar patrones de búsqueda para cada número
        self.search_patterns = {}
        for number in self.target_numbers:
            self.search_patterns[number] = [
                number,                    # 3224274851
                f"57{number}",            # 573224274851
                f"+57{number}",           # +573224274851
                f"57 {number}",           # 57 3224274851
                f"+57 {number}",          # +57 3224274851
                f"0057{number}",          # 00573224274851
            ]
        
        self.results = {
            'analysis_timestamp': datetime.now().isoformat(),
            'numbers_analyzed': self.target_numbers,
            'files_examined': [],
            'findings': {},
            'summary': {}
        }

    def analyze_number_in_file(self, file_path: str, target_number: str) -> Dict[str, Any]:
        """
        Busca un número específico en un archivo Excel
        
        Args:
            file_path: Ruta al archivo Excel
            target_number: Número a buscar
            
        Returns:
            Dict con análisis detallado
        """
        logger.info(f"Analizando {target_number} en: {Path(file_path).name}")
        
        file_analysis = {
            'file_path': file_path,
            'file_name': Path(file_path).name,
            'number': target_number,
            'found': False,
            'total_occurrences': 0,
            'as_originator': 0,
            'as_receiver': 0,
            'cells_as_originator': [],
            'cells_as_receiver': [],
            'all_cells': [],
            'detailed_occurrences': [],
            'patterns_found': [],
            'analysis_successful': True
        }
        
        try:
            # Leer todas las hojas del archivo
            excel_data = pd.read_excel(file_path, sheet_name=None, dtype=str)
            
            for sheet_name, df in excel_data.items():
                logger.debug(f"  Procesando hoja: {sheet_name} - {len(df)} filas")
                
                # Buscar en columnas relevantes
                search_columns = ['originador', 'receptor', 'numero_origen', 'numero_destino']
                existing_columns = [col for col in search_columns if col in df.columns]
                
                for col_name in existing_columns:
                    col_str = df[col_name].astype(str)
                    
                    # Probar cada patrón de búsqueda
                    for pattern in self.search_patterns[target_number]:
                        mask = col_str.str.contains(pattern, na=False, regex=False)
                        matches = df[mask]
                        
                        if not matches.empty:
                            file_analysis['found'] = True
                            if pattern not in file_analysis['patterns_found']:
                                file_analysis['patterns_found'].append(pattern)
                            
                            logger.info(f"    ¡ENCONTRADO! {pattern} en {col_name}: {len(matches)} ocurrencias")
                            
                            for idx, row in matches.iterrows():
                                # Determinar rol y celda relevante
                                role = None
                                relevant_cell = None
                                
                                if col_name in ['originador', 'numero_origen']:
                                    role = 'originador'
                                    relevant_cell = str(row.get('celda_inicio_llamada', ''))
                                    if relevant_cell and relevant_cell != 'nan':
                                        file_analysis['cells_as_originator'].append(relevant_cell)
                                        file_analysis['as_originator'] += 1
                                        
                                elif col_name in ['receptor', 'numero_destino']:
                                    role = 'receptor'
                                    relevant_cell = str(row.get('celda_final_llamada', ''))
                                    if relevant_cell and relevant_cell != 'nan':
                                        file_analysis['cells_as_receiver'].append(relevant_cell)
                                        file_analysis['as_receiver'] += 1
                                
                                # Agregar a todas las celdas
                                if relevant_cell and relevant_cell != 'nan':
                                    file_analysis['all_cells'].append(relevant_cell)
                                
                                # Guardar detalle completo
                                occurrence_detail = {
                                    'sheet': sheet_name,
                                    'row': idx + 2,  # Excel row (1-based + header)
                                    'column': col_name,
                                    'pattern': pattern,
                                    'role': role,
                                    'cell': relevant_cell,
                                    'originador': str(row.get('originador', '')),
                                    'receptor': str(row.get('receptor', '')),
                                    'celda_inicio': str(row.get('celda_inicio_llamada', '')),
                                    'celda_final': str(row.get('celda_final_llamada', '')),
                                    'fecha_hora': str(row.get('fecha_hora', ''))
                                }
                                
                                file_analysis['detailed_occurrences'].append(occurrence_detail)
            
            # Limpiar duplicados en listas de celdas
            file_analysis['cells_as_originator'] = list(set(file_analysis['cells_as_originator']))
            file_analysis['cells_as_receiver'] = list(set(file_analysis['cells_as_receiver']))  
            file_analysis['all_cells'] = list(set(file_analysis['all_cells']))
            file_analysis['total_occurrences'] = len(file_analysis['detailed_occurrences'])
            
            if file_analysis['found']:
                logger.info(f"  RESUMEN {target_number}: {file_analysis['total_occurrences']} ocurrencias totales")
                logger.info(f"    Como originador: {file_analysis['as_originator']} (celdas: {file_analysis['cells_as_originator']})")
                logger.info(f"    Como receptor: {file_analysis['as_receiver']} (celdas: {file_analysis['cells_as_receiver']})")
            else:
                logger.debug(f"  {target_number}: No encontrado en {Path(file_path).name}")
                
        except Exception as e:
            logger.error(f"Error analizando {file_path}: {str(e)}")
            file_analysis['analysis_successful'] = False
            file_analysis['error'] = str(e)
        
        return file_analysis

    def run_complete_analysis(self) -> Dict[str, Any]:
        """
        Ejecuta análisis completo de los 6 números en todos los archivos
        
        Returns:
            Dict con todos los resultados
        """
        logger.info("=== INICIANDO ANÁLISIS DE 6 NÚMEROS ESPECÍFICOS PARA BORIS ===")
        
        # Verificar archivos disponibles
        available_files = []
        for file_path in self.excel_files:
            if Path(file_path).exists():
                available_files.append(file_path)
                logger.info(f"✓ Archivo disponible: {Path(file_path).name}")
            else:
                logger.warning(f"✗ Archivo no encontrado: {file_path}")
        
        if not available_files:
            logger.error("¡CRÍTICO! Ningún archivo Excel disponible")
            return {
                'success': False,
                'error': 'No se encontraron archivos Excel',
                'timestamp': datetime.now().isoformat()
            }
        
        # Analizar cada número en cada archivo
        for number in self.target_numbers:
            logger.info(f"\n=== ANALIZANDO NÚMERO {number} ===")
            
            number_findings = {
                'number': number,
                'present': False,
                'total_occurrences': 0,
                'total_as_originator': 0,
                'total_as_receiver': 0,
                'files_found_in': [],
                'all_cells': [],
                'cells_as_originator': [],
                'cells_as_receiver': [],
                'file_details': []
            }
            
            for file_path in available_files:
                file_result = self.analyze_number_in_file(file_path, number)
                number_findings['file_details'].append(file_result)
                
                if file_result['found']:
                    number_findings['present'] = True
                    number_findings['total_occurrences'] += file_result['total_occurrences']
                    number_findings['total_as_originator'] += file_result['as_originator']
                    number_findings['total_as_receiver'] += file_result['as_receiver']
                    number_findings['files_found_in'].append(file_result['file_name'])
                    
                    # Consolidar celdas
                    number_findings['all_cells'].extend(file_result['all_cells'])
                    number_findings['cells_as_originator'].extend(file_result['cells_as_originator'])
                    number_findings['cells_as_receiver'].extend(file_result['cells_as_receiver'])
            
            # Eliminar duplicados de celdas consolidadas
            number_findings['all_cells'] = list(set(number_findings['all_cells']))
            number_findings['cells_as_originator'] = list(set(number_findings['cells_as_originator']))
            number_findings['cells_as_receiver'] = list(set(number_findings['cells_as_receiver']))
            
            self.results['findings'][number] = number_findings
            
            # Log resumen por número
            if number_findings['present']:
                logger.info(f"✓ {number}: ENCONTRADO - {number_findings['total_occurrences']} ocurrencias en {len(number_findings['files_found_in'])} archivos")
                logger.info(f"  Celdas: {number_findings['all_cells']}")
            else:
                logger.info(f"✗ {number}: NO ENCONTRADO en ningún archivo")
        
        # Generar resumen general
        numbers_found = len([n for n in self.results['findings'].values() if n['present']])
        total_occurrences = sum([n['total_occurrences'] for n in self.results['findings'].values()])
        
        self.results['summary'] = {
            'numbers_found': numbers_found,
            'numbers_not_found': len(self.target_numbers) - numbers_found,
            'total_occurrences_all': total_occurrences,
            'files_analyzed': len(available_files),
            'analysis_successful': True
        }
        
        logger.info(f"\n=== ANÁLISIS COMPLETADO ===")
        logger.info(f"Números encontrados: {numbers_found}/{len(self.target_numbers)}")
        logger.info(f"Ocurrencias totales: {total_occurrences}")
        
        return self.results

    def save_results(self, output_base: str = None) -> tuple:
        """
        Guarda resultados en archivos JSON y TXT
        
        Args:
            output_base: Nombre base para archivos (opcional)
            
        Returns:
            Tuple con rutas de archivos generados (json, txt)
        """
        if output_base is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_base = f"analisis_boris_6_numeros_{timestamp}"
        
        # Guardar JSON detallado
        json_file = f"{output_base}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        
        # Generar reporte TXT legible
        txt_file = f"{output_base}_reporte.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("REPORTE DE ANÁLISIS - 6 NÚMEROS ESPECÍFICOS BORIS\n")
            f.write("="*80 + "\n")
            f.write(f"Fecha: {self.results['analysis_timestamp']}\n")
            f.write(f"Números analizados: {len(self.target_numbers)}\n")
            f.write(f"Archivos analizados: {self.results['summary']['files_analyzed']}\n\n")
            
            # Resumen general
            f.write("RESUMEN GENERAL:\n")
            f.write(f"- Números encontrados: {self.results['summary']['numbers_found']}\n")
            f.write(f"- Números NO encontrados: {self.results['summary']['numbers_not_found']}\n")
            f.write(f"- Ocurrencias totales: {self.results['summary']['total_occurrences_all']}\n\n")
            
            # Detalle por número
            for number, findings in self.results['findings'].items():
                f.write(f"\n{'-'*60}\n")
                f.write(f"NÚMERO: {number}\n")
                f.write(f"{'-'*60}\n")
                
                if findings['present']:
                    f.write(f"✓ PRESENTE: SÍ\n")
                    f.write(f"Archivos donde aparece: {', '.join(findings['files_found_in'])}\n")
                    f.write(f"Ocurrencias totales: {findings['total_occurrences']}\n")
                    f.write(f"Como originador: {findings['total_as_originator']}\n")
                    f.write(f"Como receptor: {findings['total_as_receiver']}\n")
                    f.write(f"Celdas (todas): {findings['all_cells']}\n")
                    f.write(f"Celdas como originador: {findings['cells_as_originator']}\n")
                    f.write(f"Celdas como receptor: {findings['cells_as_receiver']}\n")
                else:
                    f.write(f"✗ PRESENTE: NO\n")
                    f.write(f"No se encontró en ningún archivo.\n")
        
        logger.info(f"Resultados guardados:")
        logger.info(f"  JSON detallado: {json_file}")
        logger.info(f"  Reporte legible: {txt_file}")
        
        return json_file, txt_file

def main():
    """Función principal"""
    try:
        analyzer = Boris6NumbersAnalyzer()
        results = analyzer.run_complete_analysis()
        
        # Guardar resultados
        json_file, txt_file = analyzer.save_results()
        
        # Mostrar resumen en consola
        print("\n" + "="*80)
        print("ANÁLISIS COMPLETADO - NÚMEROS ESPECÍFICOS BORIS")
        print("="*80)
        
        for number, findings in results['findings'].items():
            status = "✓ ENCONTRADO" if findings['present'] else "✗ NO ENCONTRADO"
            if findings['present']:
                print(f"{number}: {status} - {findings['total_occurrences']} ocurrencias en celdas {findings['all_cells']}")
            else:
                print(f"{number}: {status}")
        
        print(f"\nRESUMEN:")
        print(f"  Números encontrados: {results['summary']['numbers_found']}/6")
        print(f"  Ocurrencias totales: {results['summary']['total_occurrences_all']}")
        print(f"\nArchivos generados:")
        print(f"  📄 JSON: {json_file}")
        print(f"  📋 TXT: {txt_file}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error en análisis: {str(e)}")
        raise

if __name__ == "__main__":
    main()