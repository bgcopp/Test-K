#!/usr/bin/env python3
"""
KRONOS - DIAGNÓSTICO CRÍTICO PROCESAMIENTO ARCHIVOS CLARO
========================================================================
Script de diagnóstico urgente para identificar los 3 problemas reportados:

1. CONTEO INCORRECTO: 650k registros cuando archivo real tiene 1 línea
2. PERFORMANCE LENTA: Validaciones excesivamente lentas 
3. SIN PERSISTENCIA: Datos no se guardan en base de datos

MODO DE USO:
python test_claro_critical_diagnosis.py

ARCHIVOS DE PRUEBA:
- datatest/Claro/DATOS_POR_CELDA CLARO.csv (1 línea - problema crítico)
- datatest/Claro/LLAMADAS_ENTRANTES_POR_CELDA CLARO.csv (974 líneas)
- datatest/Claro/LLAMADAS_SALIENTES_POR_CELDA CLARO.csv (962 líneas)
========================================================================
"""

import sys
import os
import time
import logging
import base64
import traceback
from pathlib import Path

# Agregar directorio Backend al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.operator_processors.claro_processor import ClaroProcessor
from database.connection import get_database_manager
from database.operator_models import OperatorFileUpload, OperatorCellularData, OperatorCallData

# Configurar logging para diagnóstico
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('claro_diagnosis.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ClaroCriticalDiagnosis:
    """Diagnóstico crítico del procesador CLARO"""
    
    def __init__(self):
        self.test_files = {
            'DATOS': Path('../datatest/Claro/DATOS_POR_CELDA CLARO.csv'),
            'LLAMADAS_ENTRANTES': Path('../datatest/Claro/LLAMADAS_ENTRANTES_POR_CELDA CLARO.csv'),
            'LLAMADAS_SALIENTES': Path('../datatest/Claro/LLAMADAS_SALIENTES_POR_CELDA CLARO.csv')
        }
        self.processor = ClaroProcessor()
        self.mission_id = "TEST-CLARO-DIAGNOSIS-2025"
        self.test_results = {}
    
    def run_full_diagnosis(self):
        """Ejecuta diagnóstico completo"""
        print("="*80)
        print("KRONOS - DIAGNÓSTICO CRÍTICO CLARO EN PRODUCCIÓN")
        print("="*80)
        
        try:
            # Limpiar datos previos
            self._cleanup_test_data()
            
            # Diagnóstico de cada archivo
            for file_type, file_path in self.test_files.items():
                if file_path.exists():
                    print(f"\n[ARCHIVO] DIAGNOSTICO: {file_type}")
                    print("-" * 50)
                    self._diagnose_file(file_type, file_path)
                else:
                    print(f"[WARNING] ARCHIVO NO ENCONTRADO: {file_path}")
            
            # Reporte final
            self._generate_final_report()
            
        except Exception as e:
            logger.error(f"Error crítico en diagnóstico: {e}")
            traceback.print_exc()
    
    def _diagnose_file(self, file_type, file_path):
        """Diagnóstica un archivo específico paso a paso"""
        test_result = {
            'file_type': file_type,
            'file_path': str(file_path),
            'file_size': file_path.stat().st_size if file_path.exists() else 0,
            'timings': {},
            'errors': [],
            'stages': {}
        }
        
        try:
            # ETAPA 1: Análisis básico del archivo
            print(f"[ETAPA 1] Análisis básico del archivo")
            start_time = time.time()
            
            file_analysis = self._analyze_raw_file(file_path)
            test_result['stages']['raw_analysis'] = file_analysis
            
            elapsed = time.time() - start_time
            test_result['timings']['raw_analysis'] = elapsed
            print(f"   [TIEMPO] {elapsed:.3f}s")
            print(f"   [TAMAÑO] {file_analysis['file_size']:,} bytes")
            print(f"   [LINEAS] {file_analysis['line_count']:,}")
            print(f"   [PRIMERA_LINEA] {file_analysis['first_line_length']:,} caracteres")
            
            if file_analysis['line_count'] == 1 and file_analysis['file_size'] > 100000:
                print(f"   [PROBLEMA_DETECTADO] 1 línea pero archivo muy grande ({file_analysis['file_size']:,} bytes)")
                print(f"   [POSIBLE_CAUSA] Datos concatenados sin separadores de línea")
            
            # ETAPA 2: Conversión a formato base64 (simulando upload)
            print(f"\n[ETAPA 2] Preparación upload (Base64)")
            start_time = time.time()
            
            file_data = self._create_file_data(file_path)
            
            elapsed = time.time() - start_time
            test_result['timings']['base64_conversion'] = elapsed
            print(f"   [TIEMPO] Conversión Base64: {elapsed:.3f}s")
            
            # ETAPA 3: Validación de estructura
            print(f"\n[ETAPA 3] Validación estructura")
            start_time = time.time()
            
            validation_result = self.processor.validate_file_structure(file_data, file_type)
            test_result['stages']['validation'] = validation_result
            
            elapsed = time.time() - start_time
            test_result['timings']['validation'] = elapsed
            print(f"   [TIEMPO] Validación: {elapsed:.3f}s")
            print(f"   [VALIDO] {validation_result.get('is_valid', False)}")
            
            if not validation_result.get('is_valid', False):
                print(f"   [ERROR] Validación: {validation_result.get('error', 'Desconocido')}")
                test_result['errors'].append(f"Validación falló: {validation_result.get('error')}")
                return
            
            # ETAPA 4: Diagnóstico de lectura CSV (problema crítico)
            print(f"\n[ETAPA 4] Diagnóstico lectura CSV")
            start_time = time.time()
            
            csv_diagnosis = self._diagnose_csv_reading(file_path)
            test_result['stages']['csv_diagnosis'] = csv_diagnosis
            
            elapsed = time.time() - start_time
            test_result['timings']['csv_diagnosis'] = elapsed
            print(f"   [TIEMPO] Diagnóstico CSV: {elapsed:.3f}s")
            print(f"   [REGISTROS_PANDAS] {csv_diagnosis['pandas_row_count']:,}")
            print(f"   [DELIMITADOR] '{csv_diagnosis['detected_delimiter']}'")
            print(f"   [COLUMNAS] {csv_diagnosis['column_count']}")
            
            if csv_diagnosis['pandas_row_count'] > 100000 and file_analysis['line_count'] == 1:
                print(f"   [PROBLEMA_CRITICO] Pandas detecta {csv_diagnosis['pandas_row_count']:,} registros pero archivo solo tiene 1 línea")
                print(f"   [DIAGNOSTICO] Archivo malformado - datos concatenados sin separadores de línea correctos")
                test_result['errors'].append("Archivo malformado: datos concatenados")
            
            # ETAPA 5: Procesamiento completo
            print(f"\n[ETAPA 5] Procesamiento completo")
            start_time = time.time()
            
            # Verificar estado BD antes
            pre_count = self._count_database_records(file_type)
            print(f"   [BD_ANTES] {pre_count} registros")
            
            try:
                processing_result = self.processor.process_file(file_data, file_type, self.mission_id)
                test_result['stages']['processing'] = processing_result
                
                elapsed = time.time() - start_time
                test_result['timings']['processing'] = elapsed
                print(f"   [TIEMPO] Procesamiento: {elapsed:.3f}s")
                print(f"   [EXITO] {processing_result.get('success', False)}")
                print(f"   [PROCESADOS] {processing_result.get('records_processed', 0):,} registros")
                
                # Verificar estado BD después
                post_count = self._count_database_records(file_type)
                print(f"   [BD_DESPUES] {post_count} registros")
                test_result['database_persistence'] = {
                    'before': pre_count,
                    'after': post_count,
                    'difference': post_count - pre_count
                }
                
                if post_count == pre_count:
                    print(f"   [PROBLEMA_PERSISTENCIA] No se guardaron datos en BD")
                    test_result['errors'].append("Sin persistencia: registros no guardados en BD")
                
            except Exception as e:
                elapsed = time.time() - start_time
                test_result['timings']['processing'] = elapsed
                error_msg = f"Error procesamiento: {str(e)}"
                print(f"   [ERROR] {error_msg}")
                test_result['errors'].append(error_msg)
            
        except Exception as e:
            error_msg = f"Error crítico diagnosticando {file_type}: {str(e)}"
            logger.error(error_msg)
            test_result['errors'].append(error_msg)
        
        finally:
            self.test_results[file_type] = test_result
    
    def _analyze_raw_file(self, file_path):
        """Analiza archivo sin procesamiento"""
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Contar líneas reales
        line_count = content.count(b'\n') + 1 if content else 0
        
        # Analizar primera línea
        first_line = content.split(b'\n')[0] if content else b''
        
        return {
            'file_size': len(content),
            'line_count': line_count,
            'first_line_length': len(first_line),
            'has_bom': content.startswith(b'\xef\xbb\xbf'),
            'encoding_hint': 'utf-8-sig' if content.startswith(b'\xef\xbb\xbf') else 'utf-8'
        }
    
    def _diagnose_csv_reading(self, file_path):
        """Diagnóstica específicamente la lectura CSV"""
        import pandas as pd
        import chardet
        
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Detectar encoding
        detected = chardet.detect(content)
        encoding = detected.get('encoding', 'utf-8')
        
        # Probar diferentes delimitadores
        delimiters = [',', ';', '\t', '|']
        best_result = None
        
        for delimiter in delimiters:
            try:
                # Leer sample para diagnóstico
                df_sample = pd.read_csv(file_path, encoding=encoding, delimiter=delimiter, nrows=10)
                
                if len(df_sample.columns) > 1:
                    # Leer archivo completo para conteo
                    df_full = pd.read_csv(file_path, encoding=encoding, delimiter=delimiter)
                    
                    result = {
                        'detected_delimiter': delimiter,
                        'encoding': encoding,
                        'pandas_row_count': len(df_full),
                        'column_count': len(df_full.columns),
                        'columns': list(df_full.columns),
                        'sample_data': df_sample.head(3).to_dict('records') if len(df_sample) > 0 else []
                    }
                    
                    if best_result is None or result['column_count'] > best_result['column_count']:
                        best_result = result
                        
            except Exception as e:
                continue
        
        return best_result or {
            'detected_delimiter': 'UNKNOWN',
            'encoding': encoding,
            'pandas_row_count': 0,
            'column_count': 0,
            'columns': [],
            'error': 'No se pudo leer el archivo CSV'
        }
    
    def _create_file_data(self, file_path):
        """Crea estructura de datos como la recibe el procesador"""
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # Determinar MIME type
        if file_path.suffix.lower() == '.csv':
            mime_type = 'text/csv'
        elif file_path.suffix.lower() in ['.xlsx', '.xls']:
            mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        else:
            mime_type = 'application/octet-stream'
        
        # Codificar en base64 como hace el frontend
        base64_content = base64.b64encode(file_content).decode('utf-8')
        
        # Formato correcto que espera el validador
        return {
            'name': file_path.name,  # El validador espera 'name', no 'filename'
            'content': f'data:{mime_type};base64,{base64_content}',  # Formato data URL
            'size': len(file_content)
        }
    
    def _count_database_records(self, file_type):
        """Cuenta registros en base de datos por tipo"""
        try:
            db_manager = get_database_manager()
            db_manager.initialize()  # Asegurar inicialización
            with db_manager.get_session() as session:
                if file_type == 'DATOS':
                    count = session.query(OperatorCellularData).filter(
                        OperatorCellularData.mission_id == self.mission_id,
                        OperatorCellularData.operator == 'CLARO'
                    ).count()
                else:
                    count = session.query(OperatorCallData).filter(
                        OperatorCallData.mission_id == self.mission_id,
                        OperatorCallData.operator == 'CLARO'
                    ).count()
                return count
        except Exception as e:
            logger.error(f"Error contando registros BD: {e}")
            return -1
    
    def _cleanup_test_data(self):
        """Limpia datos de prueba previos"""
        try:
            db_manager = get_database_manager()
            db_manager.initialize()  # Asegurar inicialización
            with db_manager.get_session() as session:
                # Eliminar registros de prueba
                session.query(OperatorFileUpload).filter(
                    OperatorFileUpload.mission_id == self.mission_id
                ).delete()
                session.query(OperatorCellularData).filter(
                    OperatorCellularData.mission_id == self.mission_id
                ).delete()
                session.query(OperatorCallData).filter(
                    OperatorCallData.mission_id == self.mission_id
                ).delete()
                session.commit()
                print(" Datos de prueba previos eliminados")
        except Exception as e:
            logger.warning(f"Error limpiando datos previos: {e}")
    
    def _generate_final_report(self):
        """Genera reporte final con diagnóstico"""
        print("\n" + "="*80)
        print("REPORTE FINAL - DIAGNÓSTICO CRÍTICO CLARO")
        print("="*80)
        
        critical_issues = []
        major_issues = []
        performance_issues = []
        
        for file_type, result in self.test_results.items():
            print(f"\n ARCHIVO: {file_type}")
            print("-" * 40)
            
            # Analizar errores
            if result.get('errors'):
                print(" ERRORES DETECTADOS:")
                for error in result['errors']:
                    print(f"   • {error}")
                    
                    if "datos concatenados" in error.lower():
                        critical_issues.append(f"{file_type}: Archivo malformado - datos concatenados sin separadores")
                    elif "sin persistencia" in error.lower():
                        critical_issues.append(f"{file_type}: Datos no se guardan en base de datos")
                    else:
                        major_issues.append(f"{file_type}: {error}")
            
            # Analizar performance
            timings = result.get('timings', {})
            if timings:
                print("  TIEMPOS DE PROCESAMIENTO:")
                total_time = sum(timings.values())
                for stage, time_val in timings.items():
                    print(f"   • {stage}: {time_val:.3f}s")
                    
                    if time_val > 5.0:  # Más de 5 segundos es lento
                        performance_issues.append(f"{file_type}: {stage} muy lento ({time_val:.1f}s)")
                
                print(f"   • TOTAL: {total_time:.3f}s")
            
            # Analizar persistencia
            persistence = result.get('database_persistence')
            if persistence:
                print(" PERSISTENCIA BASE DE DATOS:")
                print(f"   • Antes: {persistence['before']} registros")
                print(f"   • Después: {persistence['after']} registros")
                print(f"   • Diferencia: {persistence['difference']} registros")
        
        # Resumen de problemas críticos
        print(f"\n PROBLEMAS CRÍTICOS IDENTIFICADOS ({len(critical_issues)}):")
        for issue in critical_issues:
            print(f"   • {issue}")
        
        print(f"\n  PROBLEMAS MAYORES ({len(major_issues)}):")
        for issue in major_issues:
            print(f"   • {issue}")
        
        print(f"\n PROBLEMAS DE PERFORMANCE ({len(performance_issues)}):")
        for issue in performance_issues:
            print(f"   • {issue}")
        
        # Recomendaciones específicas
        print(f"\n RECOMENDACIONES INMEDIATAS:")
        
        if any("datos concatenados" in issue for issue in critical_issues):
            print("    URGENTE: Corregir lectura de archivos CSV malformados")
            print("      - Implementar detección de datos concatenados")
            print("      - Agregar separación automática de registros")
            print("      - Validar conteo real vs. aparente")
        
        if any("sin persistencia" in issue for issue in critical_issues):
            print("    URGENTE: Verificar transacciones de base de datos")
            print("      - Revisar commits de sesión")
            print("      - Validar manejo de excepciones")
            print("      - Confirmar configuración de BD")
        
        if performance_issues:
            print("    OPTIMIZACIÓN: Mejorar performance")
            print("      - Optimizar validaciones")
            print("      - Implementar procesamiento en lotes")
            print("      - Usar índices de BD apropiados")


if __name__ == "__main__":
    diagnosis = ClaroCriticalDiagnosis()
    diagnosis.run_full_diagnosis()