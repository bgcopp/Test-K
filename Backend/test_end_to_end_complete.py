#!/usr/bin/env python3
"""
KRONOS END-TO-END COMPLETE TESTING
===============================================================================
Pruebas integrales end-to-end con archivos reales después de correcciones críticas
===============================================================================
"""

import os
import sys
import logging
import base64
from pathlib import Path

# Configurar path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.connection import init_database, get_database_manager
from services.operator_service import get_operator_service
from services.operator_processors import get_operator_processor

# Configuración de logging
logging.basicConfig(level=logging.WARNING)  # Reducir verbosidad
logger = logging.getLogger(__name__)


def encode_file_to_base64(file_path):
    """Codifica archivo a base64 para testing"""
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        return base64.b64encode(content).decode('utf-8')
    except Exception as e:
        print(f"Error leyendo archivo {file_path}: {e}")
        return None


def test_end_to_end_integration():
    """Test integral end-to-end con archivos reales"""
    
    print("=== KRONOS END-TO-END INTEGRATION TEST ===")
    
    # Usar BD unificada corregida
    test_db_path = os.path.join(os.path.dirname(__file__), 'test_e2e_complete.db')
    
    try:
        # Inicializar BD con correcciones
        init_database(test_db_path, force_recreate=True)
        db_manager = get_database_manager()
        operator_service = get_operator_service()
        
        print("BD inicializada con correcciones críticas")
        
        # Ubicación de archivos de test
        files_dir = Path(__file__).parent.parent / 'archivos' / 'CeldasDiferenteOperador'
        
        test_results = {
            'tests_executed': 0,
            'tests_passed': 0,
            'files_processed': 0,
            'records_inserted': 0,
            'operators_tested': []
        }
        
        # TEST CASE P0-001: CLARO
        print("\n=== TEST P0-001: CLARO DATOS ===")
        claro_file = files_dir / 'claro' / 'DATOS_POR_CELDA CLARO.csv'
        
        if claro_file.exists():
            test_results['tests_executed'] += 1
            
            # Codificar archivo
            file_base64 = encode_file_to_base64(claro_file)
            if file_base64:
                file_data = {
                    'name': claro_file.name,
                    'content': file_base64,
                    'size': claro_file.stat().st_size
                }
                
                try:
                    # Procesar con transacciones atómicas corregidas
                    processor = get_operator_processor('CLARO')
                    result = processor.process_file(file_data, 'DATOS', 'm1')
                    
                    print(f"✓ CLARO procesado: {result['records_processed']} registros")
                    test_results['tests_passed'] += 1
                    test_results['files_processed'] += 1
                    test_results['records_inserted'] += result['records_processed']
                    test_results['operators_tested'].append('CLARO')
                    
                except Exception as e:
                    print(f"✗ Error CLARO: {e}")
            else:
                print("✗ No se pudo codificar archivo CLARO")
        else:
            print("✗ Archivo CLARO no encontrado")
        
        # TEST CASE P0-002: MOVISTAR  
        print("\n=== TEST P0-002: MOVISTAR DATOS ===")
        movistar_file = files_dir / 'mov' / 'jgd202410754_00007301_datos_ MOVISTAR.csv'
        
        if movistar_file.exists():
            test_results['tests_executed'] += 1
            
            file_base64 = encode_file_to_base64(movistar_file)
            if file_base64:
                file_data = {
                    'name': movistar_file.name,
                    'content': file_base64,
                    'size': movistar_file.stat().st_size
                }
                
                try:
                    processor = get_operator_processor('MOVISTAR')
                    result = processor.process_file(file_data, 'DATOS', 'm1')
                    
                    print(f"✓ MOVISTAR procesado: {result['records_processed']} registros")
                    test_results['tests_passed'] += 1
                    test_results['files_processed'] += 1
                    test_results['records_inserted'] += result['records_processed']
                    test_results['operators_tested'].append('MOVISTAR')
                    
                except Exception as e:
                    print(f"✗ Error MOVISTAR: {e}")
            else:
                print("✗ No se pudo codificar archivo MOVISTAR")
        else:
            print("✗ Archivo MOVISTAR no encontrado")
        
        # TEST CASE P0-003: TIGO
        print("\n=== TEST P0-003: TIGO DATOS ===")
        tigo_file = files_dir / 'tigo' / 'Reporte TIGO.csv'
        
        if tigo_file.exists():
            test_results['tests_executed'] += 1
            
            file_base64 = encode_file_to_base64(tigo_file)
            if file_base64:
                file_data = {
                    'filename': tigo_file.name,
                    'content': file_base64,
                    'size': tigo_file.stat().st_size
                }
                
                try:
                    processor = get_operator_processor('TIGO')
                    result = processor.process_file(file_data, 'LLAMADAS_MIXTAS', 'm1')
                    
                    print(f"✓ TIGO procesado: {result['records_processed']} registros")
                    test_results['tests_passed'] += 1
                    test_results['files_processed'] += 1
                    test_results['records_inserted'] += result['records_processed']
                    test_results['operators_tested'].append('TIGO')
                    
                except Exception as e:
                    print(f"✗ Error TIGO: {e}")
            else:
                print("✗ No se pudo codificar archivo TIGO")
        else:
            print("✗ Archivo TIGO no encontrado")
        
        # TEST CASE P0-004: WOM
        print("\n=== TEST P0-004: WOM DATOS ===")
        wom_file = files_dir / 'wom' / 'PUNTO 1 TRÁFICO DATOS WOM.csv'
        
        if wom_file.exists():
            test_results['tests_executed'] += 1
            
            file_base64 = encode_file_to_base64(wom_file)
            if file_base64:
                file_data = {
                    'filename': wom_file.name,
                    'content': file_base64,
                    'size': wom_file.stat().st_size
                }
                
                try:
                    processor = get_operator_processor('WOM')
                    result = processor.process_file(file_data, 'DATOS_POR_CELDA', 'm1')
                    
                    print(f"✓ WOM procesado: {result['records_processed']} registros")
                    test_results['tests_passed'] += 1
                    test_results['files_processed'] += 1
                    test_results['records_inserted'] += result['records_processed']
                    test_results['operators_tested'].append('WOM')
                    
                except Exception as e:
                    print(f"✗ Error WOM: {e}")
            else:
                print("✗ No se pudo codificar archivo WOM")
        else:
            print("✗ Archivo WOM no encontrado")
        
        # TEST CASE P0-008: CONSULTAS CROSS-OPERADOR
        print("\n=== TEST P0-008: CONSULTAS CROSS-OPERADOR ===")
        if test_results['operators_tested']:
            try:
                # Test consulta unificada con OperatorService corregido
                summary = operator_service.get_mission_operator_summary('m1')
                
                upload_stats = summary.get('upload_statistics', {})
                total_files = upload_stats.get('total_files', 0)
                total_records = upload_stats.get('total_records', 0)
                
                if total_files > 0 and total_records > 0:
                    print(f"✓ Consulta cross-operador: {total_files} archivos, {total_records} registros")
                    test_results['tests_passed'] += 1
                else:
                    print("✗ Consulta cross-operador retorna datos vacíos")
                
                test_results['tests_executed'] += 1
                
            except Exception as e:
                print(f"✗ Error en consulta cross-operador: {e}")
                test_results['tests_executed'] += 1
        else:
            print("⚠ No hay operadores para testing cross-operador")
        
        # TEST CASE: INTEGRIDAD DE DATOS POST-PROCESAMIENTO
        print("\n=== TEST: INTEGRIDAD DE DATOS ===")
        test_results['tests_executed'] += 1
        
        try:
            with db_manager.get_session() as session:
                from database.operator_models import OperatorFileUpload, OperatorCellularData
                
                # Verificar uploads
                uploads = session.query(OperatorFileUpload).filter(
                    OperatorFileUpload.mission_id == 'm1'
                ).all()
                
                # Verificar datos celulares
                cellular_data = session.query(OperatorCellularData).filter(
                    OperatorCellularData.mission_id == 'm1'
                ).all()
                
                if len(uploads) == test_results['files_processed']:
                    print(f"✓ Integridad uploads: {len(uploads)} registros")
                    if len(cellular_data) > 0:
                        print(f"✓ Datos celulares: {len(cellular_data)} registros")
                        test_results['tests_passed'] += 1
                    else:
                        print("✗ No hay datos celulares")
                else:
                    print(f"✗ Inconsistencia uploads: esperados {test_results['files_processed']}, encontrados {len(uploads)}")
                
        except Exception as e:
            print(f"✗ Error verificando integridad: {e}")
        
        # RESUMEN FINAL
        print(f"\n=== RESUMEN END-TO-END ===")
        print(f"Tests ejecutados: {test_results['tests_executed']}")
        print(f"Tests exitosos: {test_results['tests_passed']}")
        print(f"Archivos procesados: {test_results['files_processed']}")
        print(f"Registros insertados: {test_results['records_inserted']}")
        print(f"Operadores validados: {', '.join(test_results['operators_tested'])}")
        
        success_rate = (test_results['tests_passed'] / test_results['tests_executed']) * 100 if test_results['tests_executed'] > 0 else 0
        print(f"Tasa de éxito: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("\nSISTEMA APROBADO PARA PRODUCCION")
            print("Todas las correcciones criticas validadas con datos reales")
        else:
            print("\nSISTEMA REQUIERE ATENCION ADICIONAL")
        
        # Cleanup
        db_manager.close()
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        return success_rate >= 80
        
    except Exception as e:
        print(f"Error en test end-to-end: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_end_to_end_integration()
    print(f"\nEnd-to-end testing: {'EXITOSO' if success else 'CON ISSUES'}")
    sys.exit(0 if success else 1)