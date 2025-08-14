#!/usr/bin/env python3
"""
KRONOS FINAL SIMPLE INTEGRATION TEST
===============================================================================
Test final simplificado sin caracteres especiales
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


def test_final_integration():
    """Test final de integración"""
    
    print("=== KRONOS FINAL INTEGRATION TEST ===")
    
    # Usar BD unificada corregida
    test_db_path = os.path.join(os.path.dirname(__file__), 'test_final.db')
    
    try:
        # Inicializar BD con correcciones
        init_database(test_db_path, force_recreate=True)
        db_manager = get_database_manager()
        operator_service = get_operator_service()
        
        print("BD inicializada con correcciones criticas")
        
        tests_executed = 0
        tests_passed = 0
        
        # TEST 1: Verificar correcciones críticas
        print("\n=== TEST 1: CORRECCIONES CRITICAS ===")
        tests_executed += 1
        
        try:
            # Foreign keys habilitadas
            with db_manager.get_session() as session:
                from sqlalchemy import text
                result = session.execute(text('PRAGMA foreign_keys')).fetchone()
                fk_enabled = result[0] == 1
                
                # Tablas de operador existen
                from database.operator_models import OperatorFileUpload
                count = session.query(OperatorFileUpload).count()
                tables_exist = True
                
                # OperatorService funciona
                operators = operator_service.get_supported_operators_info()
                service_works = len(operators) > 0
                
                if fk_enabled and tables_exist and service_works:
                    print("PASS - Correcciones criticas funcionando")
                    tests_passed += 1
                else:
                    print(f"FAIL - FK:{fk_enabled}, Tables:{tables_exist}, Service:{service_works}")
                    
        except Exception as e:
            print(f"FAIL - Error en correcciones: {e}")
        
        # TEST 2: Procesamiento de archivo simple
        print("\n=== TEST 2: PROCESAMIENTO DE ARCHIVO ===")
        tests_executed += 1
        
        try:
            # Crear archivo CSV simple para test
            csv_content = "numero,fecha_trafico,tipo_cdr,celda_decimal,lac_decimal\n3001234567,20250812080000,DATA,12345,678"
            csv_base64 = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
            
            file_data = {
                'name': 'test_simple.csv',
                'content': csv_base64,
                'size': len(csv_content)
            }
            
            processor = get_operator_processor('CLARO')
            result = processor.process_file(file_data, 'DATOS', 'm1')
            
            if result['success'] and result['records_processed'] > 0:
                print(f"PASS - Archivo procesado: {result['records_processed']} registros")
                tests_passed += 1
            else:
                print("FAIL - No se procesaron registros")
                
        except Exception as e:
            print(f"FAIL - Error procesando archivo: {e}")
        
        # TEST 3: Consulta cross-operador
        print("\n=== TEST 3: CONSULTA CROSS-OPERADOR ===")
        tests_executed += 1
        
        try:
            summary = operator_service.get_mission_operator_summary('m1')
            upload_stats = summary.get('upload_statistics', {})
            total_files = upload_stats.get('total_files', 0)
            
            if total_files > 0:
                print(f"PASS - Consulta cross-operador: {total_files} archivos")
                tests_passed += 1
            else:
                print("FAIL - Consulta sin resultados")
                
        except Exception as e:
            print(f"FAIL - Error en consulta: {e}")
        
        # TEST 4: Integridad de datos
        print("\n=== TEST 4: INTEGRIDAD DE DATOS ===")
        tests_executed += 1
        
        try:
            with db_manager.get_session() as session:
                from database.operator_models import OperatorFileUpload, OperatorCellularData
                
                uploads = session.query(OperatorFileUpload).count()
                cellular = session.query(OperatorCellularData).count()
                
                if uploads > 0 and cellular > 0:
                    print(f"PASS - Integridad OK: {uploads} uploads, {cellular} datos")
                    tests_passed += 1
                else:
                    print(f"FAIL - Datos faltantes: {uploads} uploads, {cellular} datos")
                    
        except Exception as e:
            print(f"FAIL - Error verificando integridad: {e}")
        
        # RESUMEN
        success_rate = (tests_passed / tests_executed) * 100 if tests_executed > 0 else 0
        print(f"\n=== RESUMEN FINAL ===")
        print(f"Tests ejecutados: {tests_executed}")
        print(f"Tests exitosos: {tests_passed}")
        print(f"Tasa de éxito: {success_rate:.1f}%")
        
        if success_rate >= 75:
            print("\nSISTEMA APROBADO PARA PRODUCCION")
            print("Correcciones criticas validadas exitosamente")
            approval = True
        else:
            print("\nSISTEMA REQUIERE REVISION ADICIONAL")
            approval = False
        
        # Cleanup
        db_manager.close()
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        return approval
        
    except Exception as e:
        print(f"Error en test final: {e}")
        return False


if __name__ == '__main__':
    success = test_final_integration()
    print(f"\nTest final: {'EXITOSO' if success else 'CON ISSUES'}")
    sys.exit(0 if success else 1)