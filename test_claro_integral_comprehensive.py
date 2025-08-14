#!/usr/bin/env python3
"""
KRONOS - Testing Integral Completo del Operador CLARO
====================================================

Este script realiza un testing integral completo de todas las funcionalidades
implementadas para el operador CLARO, incluyendo:

1. Testing de Integración End-to-End para los 3 tipos de documentos CLARO
2. Testing de Performance y Memory Usage  
3. Testing de Validación de Datos
4. Testing de Casos Edge
5. Testing de Business Logic
6. Generación de Reporte Integral

Autor: Sistema KRONOS Testing
Versión: 1.0.0
Fecha: 2025-08-12
"""

import os
import sys
import time
import json
import traceback
import psutil
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import sqlite3

# Agregar el directorio del backend al path
backend_dir = Path(__file__).parent / "Backend"
sys.path.insert(0, str(backend_dir))

from database.connection import get_db_connection
from services.operator_data_service import upload_operator_data, get_operator_statistics
from services.file_processor_service import FileProcessorService
from utils.operator_logger import OperatorLogger

class ClaroIntegralTester:
    """
    Clase principal para realizar testing integral del operador CLARO.
    """
    
    def __init__(self):
        """Inicializa el tester con configuración de testing."""
        self.logger = OperatorLogger()
        self.file_processor = FileProcessorService()
        self.test_results = {
            'start_time': datetime.now().isoformat(),
            'tests': {},
            'performance_metrics': {},
            'critical_issues': [],
            'major_issues': [],
            'minor_issues': [],
            'recommendations': []
        }
        
        # Datos de testing
        self.test_mission_id = "test-mission-claro"
        self.test_user_id = "test-user-claro"
        
        # Archivos de prueba
        self.test_files = {
            'DATOS_POR_CELDA': {
                'csv': 'datatest/Claro/DATOS_POR_CELDA CLARO.csv',
                'xlsx': 'datatest/Claro/formato excel/DATOS_POR_CELDA CLARO.xlsx'
            },
            'LLAMADAS_ENTRANTES': {
                'csv': 'datatest/Claro/LLAMADAS_ENTRANTES_POR_CELDA CLARO.csv',
                'xlsx': 'datatest/Claro/formato excel/LLAMADAS_ENTRANTES_POR_CELDA CLARO.xlsx'
            },
            'LLAMADAS_SALIENTES': {
                'csv': 'datatest/Claro/LLAMADAS_SALIENTES_POR_CELDA CLARO.csv',
                'xlsx': 'datatest/Claro/formato excel/LLAMADAS_SALIENTES_POR_CELDA CLARO.xlsx'
            }
        }
        
        # Umbrales de performance (en segundos)
        self.performance_thresholds = {
            'small_file': 30,    # < 1MB
            'medium_file': 60,   # 1-10MB
            'large_file': 120    # > 10MB
        }
        
        print("🔧 ClaroIntegralTester inicializado")
        print(f"📁 Directorio de trabajo: {os.getcwd()}")
    
    def setup_test_environment(self) -> bool:
        """Configura el entorno de testing."""
        try:
            # Crear misión de prueba
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Insertar misión de prueba si no existe
                cursor.execute("""
                    INSERT OR IGNORE INTO missions (id, name, description, status, created_by)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    self.test_mission_id,
                    "Misión de Testing CLARO",
                    "Misión creada automáticamente para testing integral de CLARO",
                    "ACTIVE",
                    self.test_user_id
                ))
                
                # Insertar usuario de prueba si no existe
                cursor.execute("""
                    INSERT OR IGNORE INTO users (id, username, email, password_hash)
                    VALUES (?, ?, ?, ?)
                """, (
                    self.test_user_id,
                    "test-claro-user",
                    "test.claro@kronos.test",
                    "hashed_password_test"
                ))
                
                conn.commit()
            
            print("✅ Entorno de testing configurado correctamente")
            return True
            
        except Exception as e:
            self.test_results['critical_issues'].append(f"Error configurando entorno: {str(e)}")
            print(f"❌ Error configurando entorno: {e}")
            return False
    
    def encode_file_to_base64(self, file_path: str) -> Optional[str]:
        """Codifica un archivo a Base64 para simulación de carga frontend."""
        try:
            with open(file_path, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            self.logger.error(f"Error codificando archivo {file_path}: {e}")
            return None
    
    def get_file_size_category(self, file_path: str) -> str:
        """Determina la categoría de tamaño del archivo."""
        try:
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if size_mb < 1:
                return 'small_file'
            elif size_mb <= 10:
                return 'medium_file'
            else:
                return 'large_file'
        except:
            return 'medium_file'
    
    def test_file_upload(self, file_path: str, file_type: str, document_type: str, format_type: str) -> Dict[str, Any]:
        """Prueba la carga de un archivo específico."""
        test_name = f"{document_type}_{format_type.upper()}"
        
        print(f"\n🧪 Testing {test_name}: {file_path}")
        
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            return {
                'test_name': test_name,
                'success': False,
                'error': f'Archivo no encontrado: {file_path}',
                'duration': 0,
                'memory_usage': 0
            }
        
        # Métricas iniciales
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        start_time = time.time()
        
        try:
            # Codificar archivo
            file_data = self.encode_file_to_base64(file_path)
            if not file_data:
                return {
                    'test_name': test_name,
                    'success': False,
                    'error': 'Error codificando archivo a Base64',
                    'duration': time.time() - start_time,
                    'memory_usage': 0
                }
            
            # Llamar a la función de carga
            result = upload_operator_data(
                file_data=file_data,
                file_name=os.path.basename(file_path),
                mission_id=self.test_mission_id,
                operator='CLARO',
                file_type=file_type,
                user_id=self.test_user_id
            )
            
            # Métricas finales
            end_time = time.time()
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            duration = end_time - start_time
            memory_usage = final_memory - initial_memory
            
            # Evaluar resultado
            test_result = {
                'test_name': test_name,
                'success': result.get('success', False),
                'duration': duration,
                'memory_usage': memory_usage,
                'file_size_mb': os.path.getsize(file_path) / 1024 / 1024,
                'records_processed': result.get('records_processed', 0),
                'records_failed': result.get('records_failed', 0),
                'file_upload_id': result.get('file_upload_id'),
                'response': result
            }
            
            # Evaluar performance
            size_category = self.get_file_size_category(file_path)
            threshold = self.performance_thresholds[size_category]
            
            if duration > threshold:
                self.test_results['major_issues'].append(
                    f"{test_name}: Performance - Duración {duration:.1f}s excede umbral {threshold}s"
                )
            
            if memory_usage > 100:  # 100MB
                self.test_results['major_issues'].append(
                    f"{test_name}: Memory - Uso de memoria {memory_usage:.1f}MB excesivo"
                )
            
            if not result.get('success', False):
                error_msg = result.get('error', 'Error desconocido')
                if 'CRITICAL' in error_msg or 'SYSTEM' in error_msg:
                    self.test_results['critical_issues'].append(
                        f"{test_name}: {error_msg}"
                    )
                else:
                    self.test_results['major_issues'].append(
                        f"{test_name}: {error_msg}"
                    )
            
            print(f"   ⏱️  Duración: {duration:.2f}s")
            print(f"   🧠 Memoria: {memory_usage:.2f}MB")
            print(f"   📊 Registros: {result.get('records_processed', 0)} procesados, {result.get('records_failed', 0)} fallidos")
            
            if result.get('success', False):
                print(f"   ✅ {test_name} - SUCCESS")
            else:
                print(f"   ❌ {test_name} - FAILED: {result.get('error', 'Unknown error')}")
            
            return test_result
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Excepción durante testing: {str(e)}"
            
            self.test_results['critical_issues'].append(f"{test_name}: {error_msg}")
            
            print(f"   💥 {test_name} - EXCEPTION: {error_msg}")
            
            return {
                'test_name': test_name,
                'success': False,
                'error': error_msg,
                'duration': duration,
                'memory_usage': 0,
                'exception': str(e),
                'traceback': traceback.format_exc()
            }
    
    def test_data_integrity(self, file_upload_id: str, expected_type: str) -> Dict[str, Any]:
        """Verifica la integridad de los datos almacenados."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Verificar metadatos del archivo
                cursor.execute("""
                    SELECT operator, file_type, processing_status, records_processed, records_failed
                    FROM operator_data_sheets WHERE id = ?
                """, (file_upload_id,))
                
                file_info = cursor.fetchone()
                if not file_info:
                    return {'success': False, 'error': 'Archivo no encontrado en metadatos'}
                
                operator, file_type, status, processed, failed = file_info
                
                # Verificar datos según el tipo
                if file_type == 'CELLULAR_DATA':
                    cursor.execute("""
                        SELECT COUNT(*), 
                               COUNT(CASE WHEN numero_telefono IS NOT NULL THEN 1 END),
                               COUNT(CASE WHEN celda_id IS NOT NULL THEN 1 END),
                               COUNT(CASE WHEN fecha_hora_inicio IS NOT NULL THEN 1 END)
                        FROM operator_cellular_data WHERE file_upload_id = ?
                    """, (file_upload_id,))
                    
                elif file_type == 'CALL_DATA':
                    cursor.execute("""
                        SELECT COUNT(*),
                               COUNT(CASE WHEN numero_origen IS NOT NULL THEN 1 END),
                               COUNT(CASE WHEN numero_destino IS NOT NULL THEN 1 END),
                               COUNT(CASE WHEN fecha_hora_llamada IS NOT NULL THEN 1 END),
                               COUNT(CASE WHEN tipo_llamada = 'ENTRANTE' THEN 1 END),
                               COUNT(CASE WHEN tipo_llamada = 'SALIENTE' THEN 1 END)
                        FROM operator_call_data WHERE file_upload_id = ?
                    """, (file_upload_id,))
                
                data_stats = cursor.fetchone()
                
                return {
                    'success': True,
                    'file_metadata': {
                        'operator': operator,
                        'file_type': file_type,
                        'status': status,
                        'records_processed': processed,
                        'records_failed': failed
                    },
                    'data_integrity': {
                        'total_records': data_stats[0] if data_stats else 0,
                        'field_completeness': data_stats[1:] if data_stats else []
                    }
                }
                
        except Exception as e:
            return {'success': False, 'error': f"Error verificando integridad: {str(e)}"}
    
    def test_business_logic(self) -> Dict[str, Any]:
        """Verifica la lógica de negocio específica de CLARO."""
        print("\n🏢 Testing Business Logic...")
        
        business_tests = {
            'call_data_target_assignment': {'passed': 0, 'failed': 0, 'issues': []},
            'data_normalization': {'passed': 0, 'failed': 0, 'issues': []},
            'duplicate_detection': {'passed': 0, 'failed': 0, 'issues': []}
        }
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Test 1: Verificar asignación correcta de números objetivo en llamadas
                cursor.execute("""
                    SELECT tipo_llamada, numero_origen, numero_destino, numero_objetivo
                    FROM operator_call_data 
                    WHERE file_upload_id IN (
                        SELECT id FROM operator_data_sheets 
                        WHERE operator = 'CLARO' AND file_type = 'CALL_DATA'
                    )
                    LIMIT 100
                """)
                
                call_records = cursor.fetchall()
                for record in call_records:
                    tipo, origen, destino, objetivo = record
                    
                    if tipo == 'ENTRANTE' and objetivo != destino:
                        business_tests['call_data_target_assignment']['failed'] += 1
                        business_tests['call_data_target_assignment']['issues'].append(
                            f"Llamada ENTRANTE: objetivo ({objetivo}) debería ser destino ({destino})"
                        )
                    elif tipo == 'SALIENTE' and objetivo != origen:
                        business_tests['call_data_target_assignment']['failed'] += 1
                        business_tests['call_data_target_assignment']['issues'].append(
                            f"Llamada SALIENTE: objetivo ({objetivo}) debería ser origen ({origen})"
                        )
                    else:
                        business_tests['call_data_target_assignment']['passed'] += 1
                
                # Test 2: Verificar normalización de números telefónicos
                cursor.execute("""
                    SELECT numero_telefono, COUNT(*)
                    FROM operator_cellular_data 
                    WHERE file_upload_id IN (
                        SELECT id FROM operator_data_sheets 
                        WHERE operator = 'CLARO' AND file_type = 'CELLULAR_DATA'
                    )
                    GROUP BY numero_telefono
                    HAVING LENGTH(numero_telefono) NOT IN (10, 12)  -- +573xxxxxxxxx o 3xxxxxxxxx
                    LIMIT 10
                """)
                
                invalid_numbers = cursor.fetchall()
                if invalid_numbers:
                    for number, count in invalid_numbers:
                        business_tests['data_normalization']['failed'] += count
                        business_tests['data_normalization']['issues'].append(
                            f"Número mal formateado: {number} (longitud: {len(number)})"
                        )
                else:
                    business_tests['data_normalization']['passed'] += 1
                
                # Test 3: Verificar detección de duplicados
                cursor.execute("""
                    SELECT file_checksum, COUNT(*)
                    FROM operator_data_sheets 
                    WHERE operator = 'CLARO'
                    GROUP BY file_checksum
                    HAVING COUNT(*) > 1
                """)
                
                duplicates = cursor.fetchall()
                if duplicates:
                    for checksum, count in duplicates:
                        business_tests['duplicate_detection']['failed'] += count - 1
                        business_tests['duplicate_detection']['issues'].append(
                            f"Checksum duplicado: {checksum[:16]}... ({count} archivos)"
                        )
                else:
                    business_tests['duplicate_detection']['passed'] += 1
                
        except Exception as e:
            for test in business_tests.values():
                test['issues'].append(f"Error ejecutando test: {str(e)}")
        
        return business_tests
    
    def test_edge_cases(self) -> Dict[str, Any]:
        """Prueba casos edge y manejo de errores."""
        print("\n⚠️  Testing Edge Cases...")
        
        edge_tests = {
            'empty_file': {'status': 'pending'},
            'corrupted_file': {'status': 'pending'}, 
            'large_file': {'status': 'pending'},
            'invalid_format': {'status': 'pending'},
            'missing_columns': {'status': 'pending'}
        }
        
        # Test 1: Archivo vacío
        try:
            empty_data = base64.b64encode(b"header1,header2\n").decode('utf-8')
            result = upload_operator_data(
                file_data=empty_data,
                file_name="empty_test.csv",
                mission_id=self.test_mission_id,
                operator='CLARO',
                file_type='CELLULAR_DATA',
                user_id=self.test_user_id
            )
            
            edge_tests['empty_file'] = {
                'status': 'tested',
                'handles_gracefully': not result.get('success', True),
                'error_message': result.get('error', 'No error')
            }
            
        except Exception as e:
            edge_tests['empty_file'] = {
                'status': 'exception',
                'error': str(e)
            }
        
        # Test 2: Datos corruptos
        try:
            corrupted_data = base64.b64encode(b"corrupted,data\n\x00\x01\x02invalid").decode('utf-8')
            result = upload_operator_data(
                file_data=corrupted_data,
                file_name="corrupted_test.csv",
                mission_id=self.test_mission_id,
                operator='CLARO',
                file_type='CELLULAR_DATA',
                user_id=self.test_user_id
            )
            
            edge_tests['corrupted_file'] = {
                'status': 'tested',
                'handles_gracefully': not result.get('success', True),
                'error_message': result.get('error', 'No error')
            }
            
        except Exception as e:
            edge_tests['corrupted_file'] = {
                'status': 'exception',
                'error': str(e)
            }
        
        return edge_tests
    
    def run_comprehensive_testing(self) -> Dict[str, Any]:
        """Ejecuta el testing integral completo."""
        print("🚀 Iniciando Testing Integral Completo del Operador CLARO")
        print("=" * 60)
        
        # Configurar entorno
        if not self.setup_test_environment():
            return self.test_results
        
        # TEST 1: End-to-End Testing de los 3 tipos de documentos
        print("\n📋 FASE 1: End-to-End Testing de Documentos CLARO")
        print("-" * 50)
        
        for doc_type, files in self.test_files.items():
            for format_type, file_path in files.items():
                if os.path.exists(file_path):
                    file_type = 'CELLULAR_DATA' if 'DATOS' in doc_type else 'CALL_DATA'
                    
                    test_result = self.test_file_upload(
                        file_path=file_path,
                        file_type=file_type,
                        document_type=doc_type,
                        format_type=format_type
                    )
                    
                    self.test_results['tests'][test_result['test_name']] = test_result
                    
                    # Verificar integridad de datos si el upload fue exitoso
                    if test_result['success'] and test_result.get('file_upload_id'):
                        integrity_result = self.test_data_integrity(
                            test_result['file_upload_id'], 
                            file_type
                        )
                        test_result['data_integrity'] = integrity_result
                else:
                    print(f"   ⚠️  Archivo no encontrado: {file_path}")
                    self.test_results['minor_issues'].append(f"Archivo de prueba no encontrado: {file_path}")
        
        # TEST 2: Business Logic Testing
        print("\n🏢 FASE 2: Business Logic Testing")
        print("-" * 50)
        business_logic_results = self.test_business_logic()
        self.test_results['business_logic'] = business_logic_results
        
        # TEST 3: Edge Cases Testing  
        print("\n⚠️  FASE 3: Edge Cases Testing")
        print("-" * 50)
        edge_cases_results = self.test_edge_cases()
        self.test_results['edge_cases'] = edge_cases_results
        
        # TEST 4: Performance Analysis
        print("\n⚡ FASE 4: Performance Analysis")
        print("-" * 50)
        self.analyze_performance()
        
        # TEST 5: System Statistics
        print("\n📊 FASE 5: System Statistics")
        print("-" * 50)
        system_stats = get_operator_statistics()
        self.test_results['system_statistics'] = system_stats
        
        # Finalizar resultados
        self.test_results['end_time'] = datetime.now().isoformat()
        self.test_results['total_duration'] = (
            datetime.fromisoformat(self.test_results['end_time']) - 
            datetime.fromisoformat(self.test_results['start_time'])
        ).total_seconds()
        
        self.generate_recommendations()
        
        return self.test_results
    
    def analyze_performance(self):
        """Analiza métricas de performance de los tests ejecutados."""
        performance_summary = {
            'total_tests': 0,
            'avg_duration': 0,
            'max_duration': 0,
            'avg_memory_usage': 0,
            'max_memory_usage': 0,
            'tests_above_threshold': 0
        }
        
        durations = []
        memory_usages = []
        
        for test_name, test_data in self.test_results['tests'].items():
            if test_data.get('success') and 'duration' in test_data:
                performance_summary['total_tests'] += 1
                duration = test_data['duration']
                memory = test_data.get('memory_usage', 0)
                
                durations.append(duration)
                memory_usages.append(memory)
                
                performance_summary['max_duration'] = max(performance_summary['max_duration'], duration)
                performance_summary['max_memory_usage'] = max(performance_summary['max_memory_usage'], memory)
                
                # Verificar si excede umbrales
                file_size = test_data.get('file_size_mb', 1)
                if file_size < 1:
                    threshold = self.performance_thresholds['small_file']
                elif file_size <= 10:
                    threshold = self.performance_thresholds['medium_file']
                else:
                    threshold = self.performance_thresholds['large_file']
                
                if duration > threshold:
                    performance_summary['tests_above_threshold'] += 1
        
        if durations:
            performance_summary['avg_duration'] = sum(durations) / len(durations)
            performance_summary['avg_memory_usage'] = sum(memory_usages) / len(memory_usages)
        
        self.test_results['performance_metrics'] = performance_summary
        
        print(f"   📊 Tests ejecutados: {performance_summary['total_tests']}")
        print(f"   ⏱️  Duración promedio: {performance_summary['avg_duration']:.2f}s")
        print(f"   ⏱️  Duración máxima: {performance_summary['max_duration']:.2f}s")
        print(f"   🧠 Memoria promedio: {performance_summary['avg_memory_usage']:.2f}MB")
        print(f"   🧠 Memoria máxima: {performance_summary['max_memory_usage']:.2f}MB")
        print(f"   ⚠️  Tests sobre umbral: {performance_summary['tests_above_threshold']}")
    
    def generate_recommendations(self):
        """Genera recomendaciones basadas en los resultados."""
        recommendations = []
        
        # Análisis de issues críticos
        if self.test_results['critical_issues']:
            recommendations.append({
                'priority': 'CRÍTICO',
                'category': 'Funcionalidad',
                'issue': f"Se encontraron {len(self.test_results['critical_issues'])} errores críticos",
                'recommendation': 'Resolver errores críticos antes de continuar con producción',
                'impact': 'ALTO'
            })
        
        # Análisis de performance
        perf = self.test_results.get('performance_metrics', {})
        if perf.get('tests_above_threshold', 0) > 0:
            recommendations.append({
                'priority': 'MAYOR',
                'category': 'Performance',
                'issue': f"{perf['tests_above_threshold']} tests excedieron umbrales de performance",
                'recommendation': 'Optimizar procesamiento de archivos grandes y manejo de memoria',
                'impact': 'MEDIO'
            })
        
        # Análisis de business logic
        business = self.test_results.get('business_logic', {})
        for test_name, test_data in business.items():
            if test_data.get('failed', 0) > 0:
                recommendations.append({
                    'priority': 'MAYOR',
                    'category': 'Business Logic',
                    'issue': f"Errores en {test_name}: {test_data['failed']} casos fallidos",
                    'recommendation': f"Revisar implementación de {test_name}",
                    'impact': 'MEDIO'
                })
        
        # Preparación para Fase 2 (MOVISTAR)
        success_rate = self.calculate_overall_success_rate()
        if success_rate >= 90:
            recommendations.append({
                'priority': 'INFO',
                'category': 'Fase 2',
                'issue': f'CLARO tiene {success_rate:.1f}% de éxito',
                'recommendation': 'CLARO está listo para producción. Proceder con implementación MOVISTAR',
                'impact': 'POSITIVO'
            })
        else:
            recommendations.append({
                'priority': 'MAYOR',
                'category': 'Fase 2',
                'issue': f'CLARO tiene solo {success_rate:.1f}% de éxito',
                'recommendation': 'Resolver issues de CLARO antes de implementar MOVISTAR',
                'impact': 'ALTO'
            })
        
        self.test_results['recommendations'] = recommendations
    
    def calculate_overall_success_rate(self) -> float:
        """Calcula la tasa de éxito general de los tests."""
        total_tests = len(self.test_results['tests'])
        if total_tests == 0:
            return 0.0
        
        successful_tests = sum(1 for test in self.test_results['tests'].values() if test.get('success', False))
        return (successful_tests / total_tests) * 100
    
    def save_results(self, output_file: str = "claro_testing_integral_report.json"):
        """Guarda los resultados en archivo JSON."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False, default=str)
            print(f"\n💾 Resultados guardados en: {output_file}")
        except Exception as e:
            print(f"❌ Error guardando resultados: {e}")
    
    def print_executive_summary(self):
        """Imprime un resumen ejecutivo de los resultados."""
        print("\n" + "=" * 80)
        print("📋 RESUMEN EJECUTIVO - TESTING INTEGRAL CLARO")
        print("=" * 80)
        
        # Estadísticas generales
        total_tests = len(self.test_results['tests'])
        successful_tests = sum(1 for test in self.test_results['tests'].values() if test.get('success', False))
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"🔢 Tests Ejecutados: {total_tests}")
        print(f"✅ Tests Exitosos: {successful_tests}")
        print(f"❌ Tests Fallidos: {total_tests - successful_tests}")
        print(f"📊 Tasa de Éxito: {success_rate:.1f}%")
        print(f"⏱️  Duración Total: {self.test_results.get('total_duration', 0):.1f}s")
        
        # Issues por severidad
        print(f"\n🚨 Issues Críticos: {len(self.test_results['critical_issues'])}")
        print(f"⚠️  Issues Mayores: {len(self.test_results['major_issues'])}")
        print(f"ℹ️  Issues Menores: {len(self.test_results['minor_issues'])}")
        
        # Performance
        perf = self.test_results.get('performance_metrics', {})
        print(f"\n⚡ Performance:")
        print(f"   Duración Promedio: {perf.get('avg_duration', 0):.2f}s")
        print(f"   Memoria Promedio: {perf.get('avg_memory_usage', 0):.2f}MB")
        print(f"   Tests sobre umbral: {perf.get('tests_above_threshold', 0)}")
        
        # Estado para Fase 2
        print(f"\n🚀 Estado para Fase 2 (MOVISTAR):")
        if success_rate >= 90 and len(self.test_results['critical_issues']) == 0:
            print("   ✅ LISTO - CLARO cumple criterios para producción")
        elif success_rate >= 80:
            print("   ⚠️  CONDICIONAL - Resolver issues menores antes de Fase 2")
        else:
            print("   ❌ NO LISTO - Resolver issues críticos antes de continuar")
        
        # Top 3 recomendaciones
        print(f"\n💡 Recomendaciones Prioritarias:")
        for i, rec in enumerate(self.test_results.get('recommendations', [])[:3], 1):
            print(f"   {i}. [{rec['priority']}] {rec['recommendation']}")


def main():
    """Función principal del testing integral."""
    print("KRONOS - Testing Integral Completo del Operador CLARO")
    print("Iniciado:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 80)
    
    tester = ClaroIntegralTester()
    
    try:
        # Ejecutar testing completo
        results = tester.run_comprehensive_testing()
        
        # Mostrar resumen ejecutivo
        tester.print_executive_summary()
        
        # Guardar resultados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"claro_testing_integral_report_{timestamp}.json"
        tester.save_results(output_file)
        
        print(f"\n🏁 Testing integral completado exitosamente")
        print(f"📄 Reporte detallado disponible en: {output_file}")
        
        return 0 if len(results['critical_issues']) == 0 else 1
        
    except KeyboardInterrupt:
        print("\n⚠️  Testing interrumpido por el usuario")
        return 2
    
    except Exception as e:
        print(f"\n💥 Error crítico durante testing: {e}")
        traceback.print_exc()
        return 3


if __name__ == "__main__":
    sys.exit(main())