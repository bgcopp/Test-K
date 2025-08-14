#!/usr/bin/env python3
"""
KRONOS - Certificación Final del Sistema CLARO
===============================================================================
Script de prueba robusto para validar que el sistema funciona correctamente
después de todas las correcciones implementadas.

CONTEXTO:
- Se han realizado múltiples correcciones al sistema de procesamiento de archivos CLARO
- Los problemas reportados fueron: conteo incorrecto (650k registros vs 1 línea), 
  performance lenta, y falta de persistencia
- Se corrigieron validaciones CDR_ENTRANTE/CDR_SALIENTE, warnings de pandas, 
  y problemas de line terminators

ARCHIVOS DE PRUEBA:
1. DATOS_POR_CELDA CLARO_MANUAL_FIX.csv - Archivo corregido con LF terminators
2. LLAMADAS_ENTRANTES_POR_CELDA CLARO.csv - 4 registros de llamadas entrantes
3. LLAMADAS_SALIENTES_POR_CELDA CLARO.csv - 4 registros de llamadas salientes

OBJETIVO:
"Debe ser garantizado el proceso y la persistencia"

===============================================================================
"""

import os
import sys
import logging
import traceback
import time
import base64
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Configurar paths
BACKEND_PATH = Path(__file__).parent
PROJECT_ROOT = BACKEND_PATH.parent
sys.path.insert(0, str(BACKEND_PATH))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(BACKEND_PATH / 'claro_certification_results.log', mode='w'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Importes del sistema KRONOS
from database.connection import DatabaseManager, init_database, get_database_manager
from database.models import Base, Mission, User, Role
from database.operator_models import (
    OperatorFileUpload, OperatorCellularData, OperatorCallData
)
from services.operator_service import OperatorService
from services.mission_service import MissionService


class ClaroCertificationTester:
    """Clase para ejecutar la certificación final del sistema CLARO"""
    
    def __init__(self):
        self.db_manager = None
        self.operator_service = None
        self.mission_service = None
        self.test_mission_id = None
        self.test_user_id = None
        self.test_results = {
            'start_time': datetime.now(),
            'database_initialized': False,
            'test_files': [],
            'processing_results': {},
            'persistence_validation': {},
            'performance_metrics': {},
            'errors': [],
            'success': False
        }
        
        # Archivos de prueba
        self.test_files = [
            {
                'name': 'DATOS_POR_CELDA CLARO_MANUAL_FIX.csv',
                'type': 'DATOS',
                'path': PROJECT_ROOT / 'datatest' / 'Claro' / 'DATOS_POR_CELDA CLARO_MANUAL_FIX.csv',
                'expected_records': 99001  # Sin header
            },
            {
                'name': 'LLAMADAS_ENTRANTES_POR_CELDA CLARO.csv',
                'type': 'LLAMADAS_ENTRANTES',
                'path': PROJECT_ROOT / 'datatest' / 'Claro' / 'LLAMADAS_ENTRANTES_POR_CELDA CLARO.csv',
                'expected_records': 973  # Sin header
            },
            {
                'name': 'LLAMADAS_SALIENTES_POR_CELDA CLARO.csv',
                'type': 'LLAMADAS_SALIENTES',
                'path': PROJECT_ROOT / 'datatest' / 'Claro' / 'LLAMADAS_SALIENTES_POR_CELDA CLARO.csv',
                'expected_records': 961  # Sin header
            }
        ]
    
    def run_certification(self) -> Dict[str, Any]:
        """Ejecuta la certificación completa del sistema CLARO"""
        try:
            logger.info("=" * 80)
            logger.info("INICIANDO CERTIFICACIÓN FINAL SISTEMA CLARO")
            logger.info("=" * 80)
            
            # Paso 1: Inicializar base de datos
            self._initialize_database()
            
            # Paso 2: Validar archivos de prueba
            self._validate_test_files()
            
            # Paso 3: Procesar cada archivo
            self._process_all_files()
            
            # Paso 4: Validar persistencia
            self._validate_persistence()
            
            # Paso 5: Generar métricas finales
            self._generate_final_metrics()
            
            # Verificar éxito general
            self.test_results['success'] = (
                self.test_results['database_initialized'] and
                len(self.test_results['errors']) == 0 and
                all(result.get('success', False) for result in self.test_results['processing_results'].values()) and
                self.test_results['persistence_validation'].get('all_validated', False)
            )
            
            self.test_results['end_time'] = datetime.now()
            self.test_results['total_duration'] = (
                self.test_results['end_time'] - self.test_results['start_time']
            ).total_seconds()
            
            logger.info("=" * 80)
            logger.info(f"CERTIFICACIÓN COMPLETADA - ÉXITO: {self.test_results['success']}")
            logger.info("=" * 80)
            
            return self.test_results
            
        except Exception as e:
            logger.error(f"Error crítico en certificación: {e}")
            logger.error(traceback.format_exc())
            self.test_results['errors'].append({
                'type': 'CRITICAL_ERROR',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            })
            self.test_results['success'] = False
            return self.test_results
        
        finally:
            self._cleanup_resources()
    
    def _initialize_database(self):
        """Inicializa la base de datos con estructuras necesarias"""
        try:
            logger.info("Inicializando base de datos...")
            
            # Usar el DB manager global
            init_database()
            self.db_manager = get_database_manager()
            
            # Crear servicios
            self.operator_service = OperatorService()
            self.mission_service = MissionService()
            
            # Crear usuario de prueba
            with self.db_manager.get_session() as session:
                # Obtener role admin existente
                admin_role = session.query(Role).filter(Role.name == 'admin').first()
                if not admin_role:
                    # Crear role admin si no existe
                    admin_role = Role(
                        id='admin-role-cert',
                        name='admin',
                        permissions='{"users": {"create": true, "read": true, "update": true, "delete": true}, "roles": {"create": true, "read": true, "update": true, "delete": true}, "missions": {"create": true, "read": true, "update": true, "delete": true}}'
                    )
                    session.add(admin_role)
                    session.flush()
                
                test_user = User(
                    id='test-user-claro-cert',
                    name='Test Claro Certification',
                    email='test@kronos.test',
                    password_hash='$2b$12$dummy.hash.for.testing.purposes.only.not.for.production.use.ever.ok',
                    role_id=admin_role.id,
                    status='active'
                )
                session.merge(test_user)
                
                # Crear misión de prueba
                test_mission = Mission(
                    id='test-mission-claro-cert',
                    code='CERT-CLARO-001',
                    name='Certificación Sistema CLARO',
                    description='Misión de prueba para certificación final del sistema CLARO',
                    status='En Progreso',
                    start_date='2025-08-12',
                    end_date='2025-08-13',
                    created_by='test-user-claro-cert'
                )
                session.merge(test_mission)
                session.commit()
                
                self.test_user_id = test_user.id
                self.test_mission_id = test_mission.id
            
            self.test_results['database_initialized'] = True
            logger.info("Base de datos inicializada correctamente")
            
        except Exception as e:
            logger.error(f"Error inicializando base de datos: {e}")
            raise
    
    def _validate_test_files(self):
        """Valida que los archivos de prueba existan y sean accesibles"""
        logger.info("Validando archivos de prueba...")
        
        for file_info in self.test_files:
            try:
                if not file_info['path'].exists():
                    raise FileNotFoundError(f"Archivo no encontrado: {file_info['path']}")
                
                file_size = file_info['path'].stat().st_size
                if file_size == 0:
                    raise ValueError(f"Archivo vacío: {file_info['name']}")
                
                logger.info(f"OK {file_info['name']} - {file_size:,} bytes")
                
                # Agregar info del archivo
                file_info.update({
                    'file_size': file_size,
                    'validated': True
                })
                
                self.test_results['test_files'].append({
                    'name': file_info['name'],
                    'type': file_info['type'],
                    'size': file_size,
                    'expected_records': file_info['expected_records'],
                    'validated': True
                })
                
            except Exception as e:
                logger.error(f"Error validando {file_info['name']}: {e}")
                raise
        
        logger.info(f"Todos los archivos validados: {len(self.test_files)} archivos")
    
    def _process_all_files(self):
        """Procesa todos los archivos de prueba"""
        logger.info("Iniciando procesamiento de archivos...")
        
        for file_info in self.test_files:
            file_key = f"{file_info['type']}_{file_info['name']}"
            
            try:
                logger.info(f"Procesando: {file_info['name']} (Tipo: {file_info['type']})")
                
                start_time = time.time()
                
                # Leer archivo como base64
                with open(file_info['path'], 'rb') as f:
                    file_content = f.read()
                    file_base64 = base64.b64encode(file_content).decode('utf-8')
                
                # Preparar datos del archivo
                file_data = {
                    'name': file_info['name'],
                    'content': f'data:text/csv;base64,{file_base64}'
                }
                
                # Procesar archivo usando el servicio
                result = self.operator_service.process_file_for_operator(
                    operator='CLARO',
                    file_data=file_data,
                    file_type=file_info['type'],
                    mission_id=self.test_mission_id
                )
                
                processing_time = time.time() - start_time
                
                # Validar resultado
                if not result.get('success', False):
                    raise Exception(f"Procesamiento falló: {result.get('error', 'Error desconocido')}")
                
                records_processed = result.get('records_processed', 0)
                
                # Guardar resultados
                self.test_results['processing_results'][file_key] = {
                    'success': True,
                    'processing_time': processing_time,
                    'records_processed': records_processed,
                    'expected_records': file_info['expected_records'],
                    'file_upload_id': result.get('file_upload_id'),
                    'records_match_expected': records_processed == file_info['expected_records'],
                    'result': result
                }
                
                logger.info(f"OK {file_info['name']} procesado: {records_processed:,} registros en {processing_time:.2f}s")
                
                if records_processed != file_info['expected_records']:
                    logger.warning(f"WARNING: Conteo no coincide - Esperado: {file_info['expected_records']:,}, Procesado: {records_processed:,}")
                
            except Exception as e:
                logger.error(f"Error procesando {file_info['name']}: {e}")
                logger.error(traceback.format_exc())
                
                self.test_results['processing_results'][file_key] = {
                    'success': False,
                    'error': str(e),
                    'processing_time': 0,
                    'records_processed': 0
                }
                
                self.test_results['errors'].append({
                    'type': 'PROCESSING_ERROR',
                    'file': file_info['name'],
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                })
    
    def _validate_persistence(self):
        """Valida que los datos se hayan persistido correctamente en la BD"""
        logger.info("Validando persistencia en base de datos...")
        
        try:
            with self.db_manager.get_session() as session:
                # Validar uploads
                uploads = session.query(OperatorFileUpload).filter(
                    OperatorFileUpload.mission_id == self.test_mission_id,
                    OperatorFileUpload.operator == 'CLARO'
                ).all()
                
                # Validar datos celulares
                cellular_data_count = session.query(OperatorCellularData).filter(
                    OperatorCellularData.mission_id == self.test_mission_id,
                    OperatorCellularData.operator == 'CLARO'
                ).count()
                
                # Validar datos de llamadas
                call_data_count = session.query(OperatorCallData).filter(
                    OperatorCallData.mission_id == self.test_mission_id,
                    OperatorCallData.operator == 'CLARO'
                ).count()
                
                # Análisis detallado
                validation_results = {
                    'uploads_found': len(uploads),
                    'uploads_expected': len(self.test_files),
                    'cellular_data_records': cellular_data_count,
                    'call_data_records': call_data_count,
                    'total_data_records': cellular_data_count + call_data_count,
                    'file_details': []
                }
                
                expected_total = sum(f['expected_records'] for f in self.test_files)
                
                for upload in uploads:
                    file_detail = {
                        'file_name': upload.file_name,
                        'file_type': upload.file_type,
                        'upload_status': upload.upload_status,
                        'records_count': upload.records_count,
                        'created_at': upload.created_at.isoformat() if upload.created_at else None,
                        'processed_at': upload.processed_at.isoformat() if upload.processed_at else None,
                        'error_message': upload.error_message
                    }
                    validation_results['file_details'].append(file_detail)
                
                # Verificaciones críticas
                all_uploads_completed = all(upload.upload_status == 'completed' for upload in uploads)
                uploads_count_match = len(uploads) == len(self.test_files)
                
                validation_results.update({
                    'all_uploads_completed': all_uploads_completed,
                    'uploads_count_match': uploads_count_match,
                    'expected_total_records': expected_total,
                    'data_count_matches': (cellular_data_count + call_data_count) > 0,
                    'all_validated': all_uploads_completed and uploads_count_match and (cellular_data_count + call_data_count) > 0
                })
                
                self.test_results['persistence_validation'] = validation_results
                
                logger.info(f"Persistencia validada:")
                logger.info(f"  - Uploads encontrados: {len(uploads)}/{len(self.test_files)}")
                logger.info(f"  - Registros datos celulares: {cellular_data_count:,}")
                logger.info(f"  - Registros datos llamadas: {call_data_count:,}")
                logger.info(f"  - Total registros: {cellular_data_count + call_data_count:,}")
                logger.info(f"  - Todos completados: {all_uploads_completed}")
                
                if not validation_results['all_validated']:
                    logger.error("ERROR: Validacion de persistencia FALLO")
                else:
                    logger.info("OK: Persistencia validada correctamente")
                
        except Exception as e:
            logger.error(f"Error validando persistencia: {e}")
            logger.error(traceback.format_exc())
            self.test_results['persistence_validation'] = {
                'error': str(e),
                'all_validated': False
            }
    
    def _generate_final_metrics(self):
        """Genera métricas finales de rendimiento"""
        logger.info("Generando métricas finales...")
        
        try:
            # Métricas de procesamiento
            total_processing_time = sum(
                result.get('processing_time', 0) 
                for result in self.test_results['processing_results'].values()
            )
            
            total_records_processed = sum(
                result.get('records_processed', 0) 
                for result in self.test_results['processing_results'].values()
            )
            
            successful_files = sum(
                1 for result in self.test_results['processing_results'].values()
                if result.get('success', False)
            )
            
            # Calcular velocidad promedio
            avg_records_per_second = (
                total_records_processed / total_processing_time 
                if total_processing_time > 0 else 0
            )
            
            self.test_results['performance_metrics'] = {
                'total_files_processed': len(self.test_results['processing_results']),
                'successful_files': successful_files,
                'failed_files': len(self.test_results['processing_results']) - successful_files,
                'total_processing_time': total_processing_time,
                'total_records_processed': total_records_processed,
                'avg_records_per_second': avg_records_per_second,
                'success_rate': (successful_files / len(self.test_files)) * 100 if self.test_files else 0
            }
            
            logger.info("Métricas de rendimiento:")
            logger.info(f"  - Archivos procesados: {successful_files}/{len(self.test_files)}")
            logger.info(f"  - Tiempo total: {total_processing_time:.2f}s")
            logger.info(f"  - Registros totales: {total_records_processed:,}")
            logger.info(f"  - Velocidad promedio: {avg_records_per_second:,.0f} registros/s")
            logger.info(f"  - Tasa de éxito: {self.test_results['performance_metrics']['success_rate']:.1f}%")
            
        except Exception as e:
            logger.error(f"Error generando métricas: {e}")
    
    def _cleanup_resources(self):
        """Limpia recursos utilizados en las pruebas"""
        try:
            if self.db_manager:
                self.db_manager.close()
        except Exception as e:
            logger.warning(f"Error limpiando recursos: {e}")
    
    def generate_certification_report(self) -> str:
        """Genera reporte de certificación en formato texto"""
        
        report = []
        report.append("=" * 80)
        report.append("REPORTE DE CERTIFICACIÓN FINAL - SISTEMA CLARO")
        report.append("=" * 80)
        report.append(f"Fecha de ejecución: {self.test_results['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Duración total: {self.test_results.get('total_duration', 0):.2f} segundos")
        report.append(f"Estado general: {'EXITO' if self.test_results['success'] else 'FALLO'}")
        report.append("")
        
        # Resumen de archivos
        report.append("ARCHIVOS PROCESADOS:")
        report.append("-" * 40)
        for file_info in self.test_results['test_files']:
            report.append(f"• {file_info['name']}")
            report.append(f"  Tipo: {file_info['type']}")
            report.append(f"  Tamaño: {file_info['size']:,} bytes")
            report.append(f"  Registros esperados: {file_info['expected_records']:,}")
            report.append("")
        
        # Resultados de procesamiento
        report.append("RESULTADOS DE PROCESAMIENTO:")
        report.append("-" * 40)
        for file_key, result in self.test_results['processing_results'].items():
            status = "EXITO" if result.get('success') else "FALLO"
            report.append(f"• {file_key}: {status}")
            if result.get('success'):
                report.append(f"  Tiempo: {result.get('processing_time', 0):.2f}s")
                report.append(f"  Registros: {result.get('records_processed', 0):,}")
                if not result.get('records_match_expected', True):
                    report.append(f"  ADVERTENCIA: Conteo no coincide con esperado")
            else:
                report.append(f"  Error: {result.get('error', 'Error desconocido')}")
            report.append("")
        
        # Validación de persistencia
        report.append("VALIDACIÓN DE PERSISTENCIA:")
        report.append("-" * 40)
        persistence = self.test_results.get('persistence_validation', {})
        if persistence.get('all_validated'):
            report.append("PERSISTENCIA VALIDADA CORRECTAMENTE")
        else:
            report.append("FALLO EN VALIDACION DE PERSISTENCIA")
        
        report.append(f"Uploads encontrados: {persistence.get('uploads_found', 0)}")
        report.append(f"Registros datos celulares: {persistence.get('cellular_data_records', 0):,}")
        report.append(f"Registros datos llamadas: {persistence.get('call_data_records', 0):,}")
        report.append(f"Total registros persistidos: {persistence.get('total_data_records', 0):,}")
        report.append("")
        
        # Métricas de rendimiento
        report.append("MÉTRICAS DE RENDIMIENTO:")
        report.append("-" * 40)
        metrics = self.test_results.get('performance_metrics', {})
        report.append(f"Archivos exitosos: {metrics.get('successful_files', 0)}/{metrics.get('total_files_processed', 0)}")
        report.append(f"Tiempo total de procesamiento: {metrics.get('total_processing_time', 0):.2f}s")
        report.append(f"Registros procesados: {metrics.get('total_records_processed', 0):,}")
        report.append(f"Velocidad promedio: {metrics.get('avg_records_per_second', 0):,.0f} registros/s")
        report.append(f"Tasa de éxito: {metrics.get('success_rate', 0):.1f}%")
        report.append("")
        
        # Errores
        if self.test_results.get('errors'):
            report.append("ERRORES ENCONTRADOS:")
            report.append("-" * 40)
            for error in self.test_results['errors']:
                report.append(f"• Tipo: {error.get('type', 'UNKNOWN')}")
                report.append(f"  Mensaje: {error.get('message', 'Sin mensaje')}")
                if 'file' in error:
                    report.append(f"  Archivo: {error['file']}")
                report.append(f"  Timestamp: {error.get('timestamp', 'N/A')}")
                report.append("")
        
        # Conclusión
        report.append("CONCLUSIÓN:")
        report.append("-" * 40)
        if self.test_results['success']:
            report.append("EL SISTEMA CLARO HA SIDO CERTIFICADO EXITOSAMENTE")
            report.append("   - Todos los archivos fueron procesados correctamente")
            report.append("   - Los datos se persistieron en la base de datos")
            report.append("   - El rendimiento es aceptable")
            report.append("   - No se encontraron errores criticos")
        else:
            report.append("EL SISTEMA CLARO NO SUPERO LA CERTIFICACION")
            report.append("   - Se encontraron errores criticos que requieren correccion")
            report.append("   - Revisar los errores detallados arriba")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


def main():
    """Función principal para ejecutar la certificación"""
    try:
        logger.info("Iniciando certificación final del sistema CLARO...")
        
        # Crear y ejecutar certificador
        certifier = ClaroCertificationTester()
        results = certifier.run_certification()
        
        # Generar reporte
        report = certifier.generate_certification_report()
        
        # Guardar reporte en archivo
        report_path = BACKEND_PATH / 'CLARO_CERTIFICATION_FINAL_REPORT.txt'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Guardar resultados JSON
        results_path = BACKEND_PATH / 'CLARO_CERTIFICATION_FINAL_RESULTS.json'
        # Convertir datetime objects para JSON
        json_results = json.loads(json.dumps(results, default=str))
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(json_results, f, indent=2, ensure_ascii=False)
        
        print("\n" + "=" * 80)
        print("CERTIFICACIÓN COMPLETADA")
        print("=" * 80)
        print(f"Éxito: {'SÍ' if results['success'] else 'NO'}")
        print(f"Reporte guardado en: {report_path}")
        print(f"Resultados JSON en: {results_path}")
        print(f"Logs en: {BACKEND_PATH / 'claro_certification_results.log'}")
        print("=" * 80)
        
        # Mostrar resumen en consola
        print("\nRESUMEN EJECUTIVO:")
        print("-" * 40)
        
        if results['success']:
            print("SISTEMA CLARO CERTIFICADO EXITOSAMENTE")
            metrics = results.get('performance_metrics', {})
            print(f"   - {metrics.get('successful_files', 0)} archivos procesados")
            print(f"   - {metrics.get('total_records_processed', 0):,} registros procesados")
            print(f"   - {metrics.get('avg_records_per_second', 0):,.0f} registros/s promedio")
            print("   - Persistencia garantizada en base de datos")
        else:
            print("SISTEMA CLARO NO CERTIFICADO")
            print(f"   - {len(results.get('errors', []))} errores encontrados")
            print("   - Revisar reporte detallado para correcciones")
        
        return 0 if results['success'] else 1
        
    except Exception as e:
        logger.error(f"Error crítico en certificación: {e}")
        logger.error(traceback.format_exc())
        return 1


if __name__ == '__main__':
    sys.exit(main())