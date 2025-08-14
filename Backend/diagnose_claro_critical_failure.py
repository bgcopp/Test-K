"""
DIAGNÓSTICO CRÍTICO - Procesamiento de Archivos CLARO
================================================================
Script específico para diagnosticar el fallo exacto en el procesamiento
de archivos CLARO que ocurre después de completar todas las validaciones.

PROBLEMA IDENTIFICADO:
- Frontend muestra 100% progreso completado
- Todas las validaciones se marcan como [COMPLETADO]  
- Al final el archivo aparece con estado "Error" y no persiste
- El resumen sigue mostrando "0 archivos cargados, 0 registros totales"

OBJETIVOS:
1. Reproducir el problema paso a paso
2. Identificar el punto exacto de falla
3. Encontrar la causa raíz del problema de persistencia
4. Proponer corrección específica
"""

import os
import sys
import logging
import traceback
import base64
from pathlib import Path
from datetime import datetime

# Configurar path para imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Configurar logging específico para diagnóstico
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('claro_critical_diagnosis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

from database.connection import init_database, get_database_manager
from services.operator_service import get_operator_service
from services.mission_service import get_mission_service
from database.operator_models import OperatorFileUpload, OperatorCellularData, OperatorCallData


class ClaroCriticalDiagnoser:
    """Diagnosticador específico para el problema crítico de CLARO"""
    
    def __init__(self):
        self.test_mission_id = None
        self.test_files = []
        self.db_manager = None
        
    def setup_test_environment(self):
        """Configura el entorno de testing específico"""
        try:
            logger.info("="*80)
            logger.info("INICIANDO DIAGNÓSTICO CRÍTICO CLARO")
            logger.info("="*80)
            
            # Inicializar base de datos
            logger.info("1. Inicializando base de datos...")
            init_database(force_recreate=False)
            self.db_manager = get_database_manager()
            logger.info("OK Base de datos inicializada")
            
            # Crear misión de testing
            logger.info("2. Creando misión de testing...")
            mission_service = get_mission_service()
            mission_data = {
                'code': 'DIAG-CLARO-001',
                'name': 'Diagnóstico Crítico CLARO',
                'description': 'Misión específica para diagnosticar falla crítica en procesamiento CLARO',
                'status': 'En Progreso',
                'startDate': '2025-01-01',
                'endDate': '2025-12-31'
            }
            
            mission = mission_service.create_mission(mission_data, created_by='admin')
            self.test_mission_id = mission['id']
            logger.info(f"OK Misión de testing creada: {self.test_mission_id}")
            
            # Preparar archivos de testing
            logger.info("3. Preparando archivos de testing...")
            self._prepare_test_files()
            logger.info(f"OK Archivos preparados: {len(self.test_files)}")
            
            return True
            
        except Exception as e:
            logger.error(f"ERROR configurando entorno de testing: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def _prepare_test_files(self):
        """Prepara los archivos de testing específicos para CLARO"""
        test_data_dir = Path(current_dir) / '..' / 'datatest' / 'Claro'
        
        test_files_info = [
            {
                'filename': 'DATOS_POR_CELDA CLARO_MANUAL_FIX.csv',
                'file_type': 'DATOS',
                'expected_records': 99000  # Estimado basado en logs
            },
            {
                'filename': 'LLAMADAS_ENTRANTES_POR_CELDA CLARO.csv', 
                'file_type': 'LLAMADAS_ENTRANTES',
                'expected_records': 970  # Estimado basado en logs
            },
            {
                'filename': 'LLAMADAS_SALIENTES_POR_CELDA CLARO.csv',
                'file_type': 'LLAMADAS_SALIENTES', 
                'expected_records': 960  # Estimado basado en logs
            }
        ]
        
        for file_info in test_files_info:
            file_path = test_data_dir / file_info['filename']
            if file_path.exists():
                # Leer archivo y convertir a base64
                with open(file_path, 'rb') as f:
                    file_bytes = f.read()
                
                file_data = {
                    'filename': file_info['filename'],
                    'content': base64.b64encode(file_bytes).decode('utf-8'),
                    'size': len(file_bytes),
                    'type': 'text/csv'
                }
                
                self.test_files.append({
                    'data': file_data,
                    'file_type': file_info['file_type'],
                    'expected_records': file_info['expected_records'],
                    'path': str(file_path)
                })
                logger.info(f"Archivo preparado: {file_info['filename']} ({len(file_bytes):,} bytes)")
            else:
                logger.warning(f"Archivo no encontrado: {file_path}")
    
    def run_step_by_step_diagnosis(self):
        """Ejecuta diagnóstico paso a paso para encontrar el punto exacto de falla"""
        
        if not self.test_files:
            logger.error("No hay archivos de testing preparados")
            return False
            
        operator_service = get_operator_service()
        
        for i, test_file in enumerate(self.test_files):
            logger.info(f"\n{'='*60}")
            logger.info(f"DIAGNOSTICANDO ARCHIVO {i+1}/{len(self.test_files)}")
            logger.info(f"Archivo: {test_file['data']['filename']}")
            logger.info(f"Tipo: {test_file['file_type']}")
            logger.info(f"Tamaño: {test_file['data']['size']:,} bytes")
            logger.info(f"{'='*60}")
            
            try:
                # ETAPA 1: Validación de estructura
                logger.info("ETAPA 1: Validando estructura del archivo...")
                validation_result = operator_service.validate_file_for_operator(
                    'CLARO', 
                    test_file['data'], 
                    test_file['file_type']
                )
                
                if validation_result.get('is_valid'):
                    logger.info("[OK] ETAPA 1 COMPLETADA - Validación exitosa")
                    logger.info(f"  - Columnas encontradas: {len(validation_result.get('original_columns', []))}")
                    logger.info(f"  - Filas de muestra: {validation_result.get('sample_rows', 0)}")
                else:
                    logger.error(f"[FAIL] ETAPA 1 FALLIDA - Validación falló: {validation_result.get('error')}")
                    continue
                
                # ETAPA 2: Verificar estado inicial de BD
                logger.info("\nETAPA 2: Verificando estado inicial de BD...")
                initial_uploads = self._count_uploads()
                initial_cellular = self._count_cellular_data()
                initial_calls = self._count_call_data()
                
                logger.info(f"  - Uploads iniciales: {initial_uploads}")
                logger.info(f"  - Datos celulares iniciales: {initial_cellular}")
                logger.info(f"  - Datos llamadas iniciales: {initial_calls}")
                logger.info("[OK] ETAPA 2 COMPLETADA - Estado inicial registrado")
                
                # ETAPA 3: Procesamiento del archivo
                logger.info(f"\nETAPA 3: Procesando archivo {test_file['data']['filename']}...")
                logger.info("  Iniciando procesamiento...")
                
                try:
                    processing_result = operator_service.process_file_for_operator(
                        'CLARO',
                        test_file['data'],
                        test_file['file_type'],
                        self.test_mission_id
                    )
                    
                    logger.info("[OK] ETAPA 3 COMPLETADA - Procesamiento sin excepción")
                    logger.info(f"  - Resultado: {processing_result.get('success', False)}")
                    logger.info(f"  - Registros procesados: {processing_result.get('records_processed', 0)}")
                    logger.info(f"  - File upload ID: {processing_result.get('file_upload_id')}")
                    
                except Exception as proc_error:
                    logger.error(f"[FAIL] ETAPA 3 FALLIDA - Error en procesamiento: {proc_error}")
                    logger.error(f"  Traceback: {traceback.format_exc()}")
                    continue
                
                # ETAPA 4: Verificar persistencia en BD
                logger.info("\nETAPA 4: Verificando persistencia en BD...")
                final_uploads = self._count_uploads()
                final_cellular = self._count_cellular_data()
                final_calls = self._count_call_data()
                
                logger.info(f"  - Uploads finales: {final_uploads} (incremento: {final_uploads - initial_uploads})")
                logger.info(f"  - Datos celulares finales: {final_cellular} (incremento: {final_cellular - initial_cellular})")
                logger.info(f"  - Datos llamadas finales: {final_calls} (incremento: {final_calls - initial_calls})")
                
                # VERIFICACIÓN CRÍTICA: ¿Los datos realmente persisten?
                if final_uploads > initial_uploads:
                    logger.info("[OK] ETAPA 4 PARCIAL - Upload registrado en BD")
                    
                    # Verificar el estado específico del upload
                    upload_info = self._get_upload_details(processing_result.get('file_upload_id'))
                    if upload_info:
                        logger.info(f"  - Estado del upload: {upload_info.get('upload_status')}")
                        logger.info(f"  - Registros reportados: {upload_info.get('records_count')}")
                        logger.info(f"  - Mensaje de error: {upload_info.get('error_message')}")
                        
                        if upload_info.get('upload_status') == 'completed':
                            logger.info("[OK] ETAPA 4 COMPLETADA - Persistencia exitosa")
                        else:
                            logger.error(f"[FAIL] ETAPA 4 FALLIDA - Upload con estado: {upload_info.get('upload_status')}")
                            logger.error(f"  PROBLEMA CRÍTICO IDENTIFICADO: Procesamiento reportado como exitoso pero upload marcado como {upload_info.get('upload_status')}")
                    else:
                        logger.error("[FAIL] ETAPA 4 FALLIDA - No se pudo recuperar información del upload")
                else:
                    logger.error("[FAIL] ETAPA 4 FALLIDA - Ningún upload fue persistido")
                    logger.error("  PROBLEMA CRÍTICO: Procesamiento sin excepción pero sin persistencia")
                
                # ETAPA 5: Verificar resumen de la misión
                logger.info("\nETAPA 5: Verificando resumen de la misión...")
                mission_summary = operator_service.get_mission_operator_summary(self.test_mission_id)
                claro_details = mission_summary.get('operator_details', {}).get('CLARO', {})
                
                logger.info(f"  - Archivos CLARO en misión: {claro_details.get('total_files', 0)}")
                logger.info(f"  - Registros totales CLARO: {claro_details.get('statistics', {}).get('total_records', 0)}")
                
                if claro_details.get('total_files', 0) > 0:
                    logger.info("[OK] ETAPA 5 COMPLETADA - Archivo visible en resumen")
                else:
                    logger.error("[FAIL] ETAPA 5 FALLIDA - Archivo no visible en resumen de misión")
                    logger.error("  PROBLEMA: Archivo procesado pero no aparece en resumen")
                
                logger.info(f"\nRESUMEN DEL DIAGNÓSTICO PARA {test_file['data']['filename']}:")
                logger.info(f"  - Validación: {'[OK]' if validation_result.get('is_valid') else '[FAIL]'}")
                logger.info(f"  - Procesamiento: {'[OK]' if 'processing_result' in locals() and processing_result.get('success') else '[FAIL]'}")
                logger.info(f"  - Persistencia: {'[OK]' if final_uploads > initial_uploads else '[FAIL]'}")
                logger.info(f"  - Estado final: {'[OK]' if upload_info and upload_info.get('upload_status') == 'completed' else '[FAIL]'}")
                logger.info(f"  - Visible en resumen: {'[OK]' if claro_details.get('total_files', 0) > 0 else '[FAIL]'}")
                
                # Si hay discrepancias, registrar detalles específicos
                if processing_result.get('success') and upload_info and upload_info.get('upload_status') != 'completed':
                    logger.error("\n" + "=" * 60)
                    logger.error("DISCREPANCIA CRÍTICA IDENTIFICADA:")
                    logger.error("- El procesamiento retorna success=True")
                    logger.error(f"- Pero el upload tiene estado: {upload_info.get('upload_status')}")
                    logger.error(f"- Error registrado: {upload_info.get('error_message')}")
                    logger.error("ESTO INDICA UN FALLO EN LA TRANSACCIÓN O COMMIT")
                    logger.error("=" * 60)
                
            except Exception as e:
                logger.error(f"ERROR GENERAL en diagnóstico de archivo: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                
        logger.info(f"\n{'='*80}")
        logger.info("DIAGNÓSTICO CRÍTICO COMPLETADO")
        logger.info("Ver logs anteriores para identificar puntos de falla específicos")
        logger.info("="*80)
        
        return True
    
    def _count_uploads(self) -> int:
        """Cuenta uploads en BD"""
        try:
            with self.db_manager.get_session() as session:
                return session.query(OperatorFileUpload).filter_by(
                    mission_id=self.test_mission_id, 
                    operator='CLARO'
                ).count()
        except Exception as e:
            logger.error(f"Error contando uploads: {e}")
            return -1
    
    def _count_cellular_data(self) -> int:
        """Cuenta datos celulares en BD"""
        try:
            with self.db_manager.get_session() as session:
                return session.query(OperatorCellularData).filter_by(
                    mission_id=self.test_mission_id,
                    operator='CLARO'
                ).count()
        except Exception as e:
            logger.error(f"Error contando datos celulares: {e}")
            return -1
    
    def _count_call_data(self) -> int:
        """Cuenta datos de llamadas en BD"""
        try:
            with self.db_manager.get_session() as session:
                return session.query(OperatorCallData).filter_by(
                    mission_id=self.test_mission_id,
                    operator='CLARO'
                ).count()
        except Exception as e:
            logger.error(f"Error contando datos de llamadas: {e}")
            return -1
    
    def _get_upload_details(self, upload_id: str) -> dict:
        """Obtiene detalles específicos de un upload"""
        try:
            with self.db_manager.get_session() as session:
                upload = session.query(OperatorFileUpload).filter_by(id=upload_id).first()
                if upload:
                    return {
                        'id': upload.id,
                        'upload_status': upload.upload_status,
                        'records_count': upload.records_count,
                        'error_message': upload.error_message,
                        'created_at': upload.created_at,
                        'processed_at': upload.processed_at
                    }
                return None
        except Exception as e:
            logger.error(f"Error obteniendo detalles de upload: {e}")
            return None
    
    def cleanup(self):
        """Limpieza del entorno de testing"""
        try:
            if self.db_manager:
                logger.info("Cerrando conexiones de base de datos...")
                self.db_manager.close()
                logger.info("[OK] Limpieza completada")
        except Exception as e:
            logger.error(f"Error en limpieza: {e}")


def main():
    """Función principal del diagnóstico"""
    diagnoser = ClaroCriticalDiagnoser()
    
    try:
        # Configurar entorno de testing
        if not diagnoser.setup_test_environment():
            logger.error("No se pudo configurar el entorno de testing")
            return False
            
        # Ejecutar diagnóstico paso a paso
        logger.info("\nIniciando diagnóstico paso a paso...")
        success = diagnoser.run_step_by_step_diagnosis()
        
        if success:
            logger.info("\n[OK] Diagnóstico completado exitosamente")
            logger.info("Revisa el log para identificar el punto exacto de falla")
        else:
            logger.error("\n[FAIL] Diagnóstico completado con errores")
            
        return success
        
    except Exception as e:
        logger.error(f"Error general en diagnóstico: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False
        
    finally:
        diagnoser.cleanup()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)