#!/usr/bin/env python3
"""
ANÁLISIS EXHAUSTIVO DE NÚMEROS ESPECÍFICOS CON CONTEOS INCORRECTOS
================================================================

Análisis directo de archivos Excel fuente para validar conteos reales
vs algoritmo de correlación para números específicos reportados por Boris.

Números objetivo con discrepancias:
- 3243182028: Boris manual=1, Algoritmo=5
- 3009120093: Boris manual=2, Algoritmo=4  
- 3124390973: Boris manual=2, Algoritmo=4

Autor: Claude Code - Data Engineering Algorithm Expert
Para: Boris - KRONOS Project  
Fecha: 2025-08-18
Propósito: Resolver discrepancias críticas en algoritmo de correlación
================================================================
"""

import pandas as pd
import openpyxl
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple, Any
import logging
from collections import defaultdict

# Configurar logging detallado
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NumberDiscrepancyAnalyzer:
    """
    Analizador especializado para números con conteos incorrectos
    
    Compara conteos manuales de Boris vs archivos fuente vs base de datos vs algoritmo
    para identificar la fuente exacta de las discrepancias.
    """
    
    def __init__(self):
        # Números problemáticos reportados por Boris
        self.problematic_numbers = {
            '3243182028': {
                'manual_count': 1,
                'manual_cells': ['16478'],
                'algorithm_count': 5,
                'algorithm_cells': ['16478', '22504', '51438']
            },
            '3009120093': {
                'manual_count': 2,
                'manual_cells': ['22504', '56121'],
                'algorithm_count': 4,
                'algorithm_cells': ['22504', '51438', '56121']
            },
            '3124390973': {
                'manual_count': 2,
                'manual_cells': ['22504', '51438'],
                'algorithm_count': 4,
                'algorithm_cells': ['22504', '51438', '52356']
            }
        }
        
        # Archivos fuente específicos
        self.excel_files = [
            r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\1-225211_LLAMADAS_ENTRANTES_POR_CELDA_545612_0.xlsx",
            r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\1-225211_LLAMADAS_SALIENTES_POR_CELDA_545613_0.xlsx",
            r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\2-225211_LLAMADAS_ENTRANTES_POR_CELDA_545614_0.xlsx",
            r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\2-225211_LLAMADAS_SALIENTES_POR_CELDA_545615_0.xlsx"
        ]
        
        # Patrones de búsqueda para cada número
        self.search_patterns = {}
        for number in self.problematic_numbers.keys():
            self.search_patterns[number] = [
                number,                    # 3243182028
                f"57{number}",            # 573243182028
                f"+57{number}",           # +573243182028
                f"57 {number}",           # 57 3243182028
                f"+57 {number}",          # +57 3243182028
                f"0057{number}",          # 00573243182028
            ]
        
        self.results = {
            'analysis_timestamp': datetime.now().isoformat(),
            'numbers_analyzed': list(self.problematic_numbers.keys()),
            'files_examined': [],
            'source_data_findings': {},
            'database_findings': {},
            'discrepancy_analysis': {},
            'recommendations': []
        }

    def analyze_number_in_excel(self, file_path: str, target_number: str) -> Dict[str, Any]:
        """
        Busca un número específico en un archivo Excel y documenta todas las ocurrencias
        
        Args:
            file_path: Ruta al archivo Excel
            target_number: Número a buscar
            
        Returns:
            Dict con todos los detalles de las ocurrencias encontradas
        """
        logger.info(f"Buscando {target_number} en: {Path(file_path).name}")
        
        file_analysis = {
            'file_path': file_path,
            'file_name': Path(file_path).name,
            'number_found': False,
            'total_occurrences': 0,
            'detailed_occurrences': [],
            'cells_found': set(),
            'patterns_found': set(),
            'excel_references': [],
            'analysis_successful': True
        }
        
        try:
            # Usar pandas para análisis inicial
            excel_file = pd.ExcelFile(file_path)
            
            for sheet_name in excel_file.sheet_names:
                logger.info(f"  Analizando hoja: {sheet_name}")
                
                try:
                    # Leer hoja completa
                    df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str)
                    logger.info(f"    Dimensiones: {df.shape}")
                    logger.info(f"    Columnas: {list(df.columns)}")
                    
                    # Buscar en cada columna
                    for col_name in df.columns:
                        if pd.api.types.is_object_dtype(df[col_name]):
                            col_str = df[col_name].astype(str)
                            
                            # Probar cada patrón de búsqueda
                            for pattern in self.search_patterns[target_number]:
                                mask = col_str.str.contains(pattern, na=False, regex=False)
                                matches = df[mask]
                                
                                if not matches.empty:
                                    logger.info(f"    ¡ENCONTRADO! Patrón '{pattern}' en columna '{col_name}': {len(matches)} coincidencias")
                                    
                                    file_analysis['number_found'] = True
                                    file_analysis['patterns_found'].add(pattern)
                                    
                                    for idx, row in matches.iterrows():
                                        excel_row = idx + 2  # +2 porque pandas es 0-based y Excel 1-based + header
                                        excel_ref = f"{sheet_name}!{col_name}{excel_row}"
                                        
                                        # Extraer información de celdas
                                        celda_inicio = str(row.get('celda_inicio_llamada', ''))
                                        celda_final = str(row.get('celda_final_llamada', ''))
                                        originador = str(row.get('originador', ''))
                                        receptor = str(row.get('receptor', ''))
                                        fecha_hora = str(row.get('fecha_hora', ''))
                                        
                                        # Determinar qué celda es relevante
                                        relevant_cell = None
                                        role = None
                                        
                                        if col_name == 'originador' and pattern in originador:
                                            relevant_cell = celda_inicio
                                            role = 'originador'
                                        elif col_name == 'receptor' and pattern in receptor:
                                            relevant_cell = celda_final
                                            role = 'receptor'
                                        
                                        occurrence_detail = {
                                            'sheet': sheet_name,
                                            'excel_row': excel_row,
                                            'excel_reference': excel_ref,
                                            'column_found': col_name,
                                            'pattern_matched': pattern,
                                            'cell_value': str(row[col_name]),
                                            'relevant_cell': relevant_cell,
                                            'role': role,
                                            'celda_inicio': celda_inicio,
                                            'celda_final': celda_final,
                                            'originador': originador,
                                            'receptor': receptor,
                                            'fecha_hora': fecha_hora,
                                            'full_row': dict(row)
                                        }
                                        
                                        file_analysis['detailed_occurrences'].append(occurrence_detail)
                                        file_analysis['excel_references'].append(excel_ref)
                                        
                                        if relevant_cell and relevant_cell != 'nan':
                                            file_analysis['cells_found'].add(relevant_cell)
                                            logger.info(f"      Fila {excel_row}: {role} en celda {relevant_cell}")
                    
                except Exception as e:
                    logger.error(f"    Error procesando hoja {sheet_name}: {str(e)}")
                    continue
            
            file_analysis['total_occurrences'] = len(file_analysis['detailed_occurrences'])
            file_analysis['cells_found'] = list(file_analysis['cells_found'])
            file_analysis['patterns_found'] = list(file_analysis['patterns_found'])
            
            logger.info(f"  Resultado: {file_analysis['total_occurrences']} ocurrencias, celdas: {file_analysis['cells_found']}")
            
        except Exception as e:
            logger.error(f"Error analizando {file_path}: {str(e)}")
            file_analysis['analysis_successful'] = False
            file_analysis['error'] = str(e)
        
        return file_analysis

    def analyze_number_in_database(self, target_number: str) -> Dict[str, Any]:
        """
        Busca un número específico en la base de datos SQLite
        
        Args:
            target_number: Número a buscar
            
        Returns:
            Dict con información de la base de datos
        """
        logger.info(f"Buscando {target_number} en base de datos...")
        
        db_analysis = {
            'number': target_number,
            'database_accessible': False,
            'total_records': 0,
            'records_as_origin': 0,
            'records_as_destination': 0,
            'cells_as_origin': set(),
            'cells_as_destination': set(),
            'detailed_records': [],
            'analysis_successful': True
        }
        
        try:
            db_path = r"C:\Soluciones\BGC\claude\KNSOft\Backend\kronos.db"
            if not Path(db_path).exists():
                logger.warning(f"Base de datos no encontrada: {db_path}")
                db_analysis['analysis_successful'] = False
                db_analysis['error'] = "Base de datos no accesible"
                return db_analysis
            
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                db_analysis['database_accessible'] = True
                
                # Buscar como originador
                patterns = self.search_patterns[target_number]
                for pattern in patterns:
                    cursor.execute("""
                        SELECT mission_id, numero_origen, numero_destino, celda_origen, celda_destino, 
                               operator, fecha_hora_llamada, duracion_segundos, 'origin' as role
                        FROM operator_call_data 
                        WHERE numero_origen LIKE ? OR numero_origen = ?
                    """, (f'%{pattern}%', pattern))
                    
                    origin_records = cursor.fetchall()
                    for record in origin_records:
                        record_dict = dict(record)
                        db_analysis['detailed_records'].append(record_dict)
                        db_analysis['cells_as_origin'].add(str(record['celda_origen']))
                
                # Buscar como receptor
                for pattern in patterns:
                    cursor.execute("""
                        SELECT mission_id, numero_origen, numero_destino, celda_origen, celda_destino, 
                               operator, fecha_hora_llamada, duracion_segundos, 'destination' as role
                        FROM operator_call_data 
                        WHERE numero_destino LIKE ? OR numero_destino = ?
                    """, (f'%{pattern}%', pattern))
                    
                    dest_records = cursor.fetchall()
                    for record in dest_records:
                        record_dict = dict(record)
                        db_analysis['detailed_records'].append(record_dict)
                        db_analysis['cells_as_destination'].add(str(record['celda_destino']))
                
                db_analysis['total_records'] = len(db_analysis['detailed_records'])
                db_analysis['records_as_origin'] = len([r for r in db_analysis['detailed_records'] if r['role'] == 'origin'])
                db_analysis['records_as_destination'] = len([r for r in db_analysis['detailed_records'] if r['role'] == 'destination'])
                db_analysis['cells_as_origin'] = list(db_analysis['cells_as_origin'])
                db_analysis['cells_as_destination'] = list(db_analysis['cells_as_destination'])
                
                logger.info(f"  Registros en BD: {db_analysis['total_records']} total")
                logger.info(f"  Como origen: {db_analysis['records_as_origin']} en celdas {db_analysis['cells_as_origin']}")
                logger.info(f"  Como destino: {db_analysis['records_as_destination']} en celdas {db_analysis['cells_as_destination']}")
        
        except Exception as e:
            logger.error(f"Error consultando base de datos: {str(e)}")
            db_analysis['analysis_successful'] = False
            db_analysis['error'] = str(e)
        
        return db_analysis

    def analyze_discrepancies(self, number: str, source_findings: Dict, db_findings: Dict) -> Dict[str, Any]:
        """
        Analiza discrepancias entre conteo manual, archivos fuente, BD y algoritmo
        
        Args:
            number: Número analizado
            source_findings: Hallazgos en archivos fuente
            db_findings: Hallazgos en base de datos
            
        Returns:
            Dict con análisis de discrepancias
        """
        logger.info(f"Analizando discrepancias para {number}...")
        
        problem_data = self.problematic_numbers[number]
        
        # Consolidar celdas encontradas en archivos fuente
        source_cells = set()
        source_count = 0
        for file_data in source_findings.values():
            if file_data.get('analysis_successful', False):
                source_cells.update(file_data.get('cells_found', []))
                source_count += file_data.get('total_occurrences', 0)
        
        # Consolidar celdas de base de datos
        db_cells = set()
        if db_findings.get('analysis_successful', False):
            db_cells.update(db_findings.get('cells_as_origin', []))
            db_cells.update(db_findings.get('cells_as_destination', []))
        
        discrepancy = {
            'number': number,
            'comparison': {
                'boris_manual': {
                    'count': problem_data['manual_count'],
                    'cells': set(problem_data['manual_cells'])
                },
                'source_files': {
                    'count': source_count,
                    'cells': source_cells
                },
                'database': {
                    'count': db_findings.get('total_records', 0),
                    'cells': db_cells
                },
                'algorithm': {
                    'count': problem_data['algorithm_count'],
                    'cells': set(problem_data['algorithm_cells'])
                }
            },
            'discrepancies_identified': [],
            'possible_causes': [],
            'severity': 'UNKNOWN'
        }
        
        # Comparar conteos
        boris_count = discrepancy['comparison']['boris_manual']['count']
        source_count = discrepancy['comparison']['source_files']['count']
        db_count = discrepancy['comparison']['database']['count']
        algo_count = discrepancy['comparison']['algorithm']['count']
        
        # Identificar discrepancias
        if boris_count != source_count:
            discrepancy['discrepancies_identified'].append(f"Boris manual ({boris_count}) vs Archivos fuente ({source_count})")
            if source_count > boris_count:
                discrepancy['possible_causes'].append("Boris puede haber omitido ocurrencias en revisión manual")
            else:
                discrepancy['possible_causes'].append("Archivos fuente pueden tener datos faltantes")
        
        if source_count != db_count:
            discrepancy['discrepancies_identified'].append(f"Archivos fuente ({source_count}) vs Base de datos ({db_count})")
            if db_count > source_count:
                discrepancy['possible_causes'].append("Proceso ETL está duplicando registros")
            else:
                discrepancy['possible_causes'].append("Proceso ETL está perdiendo registros")
        
        if db_count != algo_count:
            discrepancy['discrepancies_identified'].append(f"Base de datos ({db_count}) vs Algoritmo ({algo_count})")
            if algo_count > db_count:
                discrepancy['possible_causes'].append("Algoritmo está inflando conteos (multiplicación incorrecta)")
            else:
                discrepancy['possible_causes'].append("Algoritmo está perdiendo registros")
        
        # Comparar celdas
        boris_cells = discrepancy['comparison']['boris_manual']['cells']
        source_cells = discrepancy['comparison']['source_files']['cells']
        db_cells = discrepancy['comparison']['database']['cells']
        algo_cells = discrepancy['comparison']['algorithm']['cells']
        
        if boris_cells != source_cells:
            discrepancy['discrepancies_identified'].append(f"Celdas Boris {boris_cells} vs Archivos fuente {source_cells}")
        
        if source_cells != db_cells:
            discrepancy['discrepancies_identified'].append(f"Celdas archivos fuente {source_cells} vs BD {db_cells}")
        
        if db_cells != algo_cells:
            discrepancy['discrepancies_identified'].append(f"Celdas BD {db_cells} vs Algoritmo {algo_cells}")
        
        # Determinar severidad
        if len(discrepancy['discrepancies_identified']) == 0:
            discrepancy['severity'] = 'NONE'
        elif len(discrepancy['discrepancies_identified']) <= 2:
            discrepancy['severity'] = 'MODERATE'
        else:
            discrepancy['severity'] = 'CRITICAL'
        
        # Convertir sets a listas para serialización
        for comparison_type in discrepancy['comparison'].values():
            if isinstance(comparison_type['cells'], set):
                comparison_type['cells'] = list(comparison_type['cells'])
        
        logger.info(f"  Discrepancias identificadas: {len(discrepancy['discrepancies_identified'])}")
        logger.info(f"  Severidad: {discrepancy['severity']}")
        
        return discrepancy

    def generate_recommendations(self, all_discrepancies: Dict[str, Dict]) -> List[str]:
        """
        Genera recomendaciones basadas en todas las discrepancias encontradas
        
        Args:
            all_discrepancies: Todas las discrepancias analizadas
            
        Returns:
            Lista de recomendaciones
        """
        recommendations = []
        
        # Analizar patrones comunes
        etl_issues = 0
        algo_issues = 0
        manual_issues = 0
        
        for discrepancy in all_discrepancies.values():
            for cause in discrepancy.get('possible_causes', []):
                if 'ETL' in cause:
                    etl_issues += 1
                elif 'Algoritmo' in cause:
                    algo_issues += 1
                elif 'Boris' in cause and 'manual' in cause:
                    manual_issues += 1
        
        if etl_issues > 1:
            recommendations.append("CRÍTICO: Revisar proceso ETL - múltiples números muestran duplicación de datos")
            recommendations.append("Verificar que el proceso de carga no esté insertando registros duplicados")
        
        if algo_issues > 1:
            recommendations.append("CRÍTICO: Revisar algoritmo de correlación - está inflando conteos consistentemente")
            recommendations.append("Verificar lógica de conteo único por combinación número-celda")
        
        if manual_issues > 1:
            recommendations.append("Revisar criterios de conteo manual - puede haber diferencias metodológicas")
        
        # Recomendaciones específicas
        recommendations.append("Implementar validación cruzada automática entre archivos fuente y BD")
        recommendations.append("Agregar logging detallado en proceso ETL para rastrear duplicaciones")
        recommendations.append("Crear tests automatizados con números de referencia conocidos")
        
        return recommendations

    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """
        Ejecuta análisis completo de todos los números problemáticos
        
        Returns:
            Dict con todos los resultados del análisis
        """
        logger.info("=== INICIANDO ANÁLISIS EXHAUSTIVO DE NÚMEROS CON CONTEOS INCORRECTOS ===")
        
        # Verificar archivos disponibles
        available_files = []
        for file_path in self.excel_files:
            if Path(file_path).exists():
                available_files.append(file_path)
                logger.info(f"✓ Archivo disponible: {Path(file_path).name}")
            else:
                logger.warning(f"✗ Archivo no encontrado: {file_path}")
        
        if not available_files:
            logger.error("¡CRÍTICO! Ningún archivo Excel está disponible")
            return {
                'success': False,
                'error': 'No se encontraron archivos Excel para analizar',
                'timestamp': datetime.now().isoformat()
            }
        
        # Analizar cada número problemático
        for number in self.problematic_numbers.keys():
            logger.info(f"\n=== ANALIZANDO NÚMERO {number} ===")
            
            # 1. Analizar en archivos fuente
            source_findings = {}
            for file_path in available_files:
                file_result = self.analyze_number_in_excel(file_path, number)
                source_findings[Path(file_path).name] = file_result
                self.results['files_examined'].append({
                    'file': Path(file_path).name,
                    'analyzed_for_number': number,
                    'success': file_result.get('analysis_successful', False)
                })
            
            self.results['source_data_findings'][number] = source_findings
            
            # 2. Analizar en base de datos
            db_finding = self.analyze_number_in_database(number)
            self.results['database_findings'][number] = db_finding
            
            # 3. Analizar discrepancias
            discrepancy_analysis = self.analyze_discrepancies(number, source_findings, db_finding)
            self.results['discrepancy_analysis'][number] = discrepancy_analysis
        
        # 4. Generar recomendaciones
        self.results['recommendations'] = self.generate_recommendations(self.results['discrepancy_analysis'])
        
        logger.info("\n=== ANÁLISIS COMPLETADO ===")
        for number in self.problematic_numbers.keys():
            discrepancy = self.results['discrepancy_analysis'][number]
            logger.info(f"{number}: {len(discrepancy['discrepancies_identified'])} discrepancias - Severidad: {discrepancy['severity']}")
        
        self.results['analysis_completed'] = True
        self.results['success'] = True
        
        return self.results

    def save_results(self, output_file: str = None) -> str:
        """
        Guarda resultados del análisis en archivo JSON
        
        Args:
            output_file: Ruta del archivo de salida (opcional)
            
        Returns:
            Ruta del archivo guardado
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"analisis_discrepancias_numeros_especificos_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Resultados guardados en: {output_file}")
        return output_file


def main():
    """Función principal para ejecutar el análisis"""
    try:
        analyzer = NumberDiscrepancyAnalyzer()
        results = analyzer.run_comprehensive_analysis()
        
        # Guardar resultados
        output_file = analyzer.save_results()
        
        # Mostrar resumen ejecutivo
        print("\n" + "="*80)
        print("RESUMEN EJECUTIVO - ANÁLISIS DE DISCREPANCIAS NUMÉRICAS")
        print("="*80)
        print(f"Timestamp: {results['analysis_timestamp']}")
        print(f"Números analizados: {len(results['numbers_analyzed'])}")
        print(f"Archivos examinados: {len(results['files_examined'])}")
        
        print(f"\nDISCREPANCIAS POR NÚMERO:")
        for number, discrepancy in results['discrepancy_analysis'].items():
            print(f"  {number}: {len(discrepancy['discrepancies_identified'])} discrepancias - {discrepancy['severity']}")
        
        if results.get('recommendations'):
            print(f"\nRECOMENDACIONES CRÍTICAS:")
            for rec in results['recommendations'][:3]:  # Mostrar solo las primeras 3
                print(f"  • {rec}")
        
        print(f"\nResultados completos en: {output_file}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error durante análisis: {str(e)}")
        raise


if __name__ == "__main__":
    main()