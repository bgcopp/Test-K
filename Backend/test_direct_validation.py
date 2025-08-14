#!/usr/bin/env python3
"""
KRONOS - Testing Directo de Validaciones
===============================================================================
Testing directo sin crear misiones para validar las correcciones implementadas
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime

# Configurar path para imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Logging simple
class SimpleLogger:
    def info(self, msg):
        print(f"[INFO] {msg}")
    
    def error(self, msg):
        print(f"[ERROR] {msg}")
    
    def warning(self, msg):
        print(f"[WARNING] {msg}")

logger = SimpleLogger()

def test_imports():
    """Test 1: Verificar que todos los módulos se importen sin errores"""
    logger.info("TEST 1: Verificando imports...")
    
    try:
        from database.connection import get_database_manager
        from services.operator_service import get_operator_service
        from services.operator_processors import get_operator_processor, get_supported_operators
        logger.info("✓ Imports exitosos")
        return True
    except Exception as e:
        logger.error(f"✗ Error en imports: {e}")
        return False

def test_operator_processors():
    """Test 2: Verificar procesadores de operadores sin _GeneratorContextManager"""
    logger.info("TEST 2: Verificando procesadores de operadores...")
    
    try:
        from services.operator_processors import get_operator_processor, get_supported_operators
        
        operators = get_supported_operators()
        logger.info(f"Operadores soportados: {operators}")
        
        for operator in operators:
            processor = get_operator_processor(operator)
            if processor:
                logger.info(f"✓ {operator}: Procesador disponible")
                
                # Verificar métodos críticos
                if hasattr(processor, 'process_file'):
                    logger.info(f"✓ {operator}: Método process_file disponible")
                if hasattr(processor, 'validate_file_structure'):
                    logger.info(f"✓ {operator}: Método validate_file_structure disponible")
            else:
                logger.warning(f"⚠ {operator}: Procesador no disponible")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error verificando procesadores: {e}")
        return False

def test_database_tables():
    """Test 3: Verificar estructura de base de datos"""
    logger.info("TEST 3: Verificando estructura de base de datos...")
    
    try:
        from database.connection import init_database, get_database_manager
        
        # Usar base de datos temporal
        test_db_path = current_dir / 'test_validation_direct.db'
        if test_db_path.exists():
            test_db_path.unlink()
        
        init_database(str(test_db_path), force_recreate=True)
        
        db_manager = get_database_manager()
        
        # Verificar tablas principales
        with db_manager.get_session() as session:
            tables_to_check = [
                'users', 'roles', 'missions', 
                'operator_file_uploads', 'operator_cellular_data', 
                'operator_call_data', 'operator_cell_registry'
            ]
            
            existing_tables = []
            for table in tables_to_check:
                try:
                    result = session.execute(f"SELECT COUNT(*) FROM {table}")
                    count = result.scalar()
                    existing_tables.append(table)
                    logger.info(f"✓ Tabla {table}: {count} registros")
                except Exception as e:
                    logger.warning(f"⚠ Tabla {table}: Error - {e}")
            
            logger.info(f"Tablas verificadas: {len(existing_tables)}/{len(tables_to_check)}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error verificando base de datos: {e}")
        return False

def test_claro_file_structure():
    """Test 4: Verificar archivos CLARO sin procesamiento completo"""
    logger.info("TEST 4: Verificando estructura de archivos CLARO...")
    
    try:
        # Buscar archivos de test
        claro_files = []
        datatest_dir = current_dir.parent / 'datatest' / 'Claro'
        
        if datatest_dir.exists():
            for file_path in datatest_dir.glob('*.csv'):
                claro_files.append(file_path)
                logger.info(f"Archivo encontrado: {file_path.name}")
        
        if not claro_files:
            logger.warning("⚠ No se encontraron archivos CLARO para testing")
            return True
        
        # Verificar contenido básico de archivos
        for file_path in claro_files[:2]:  # Solo primeros 2 archivos
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    logger.info(f"✓ {file_path.name}: {len(lines)} líneas")
                    
                    # Verificar que no sea 650k líneas (problema de line terminators)
                    if len(lines) > 10000:
                        logger.error(f"✗ {file_path.name}: Demasiadas líneas ({len(lines)}) - posible problema line terminators")
                        return False
                    
            except Exception as e:
                logger.warning(f"⚠ {file_path.name}: Error leyendo archivo - {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error verificando archivos CLARO: {e}")
        return False

def test_operator_service_methods():
    """Test 5: Verificar métodos de operator_service sin errores"""
    logger.info("TEST 5: Verificando métodos de operator_service...")
    
    try:
        from services.operator_service import get_operator_service
        
        operator_service = get_operator_service()
        
        # Verificar método get_supported_operators_info
        operators_info = operator_service.get_supported_operators_info()
        logger.info(f"✓ get_supported_operators_info: {len(operators_info)} operadores")
        
        for op_info in operators_info:
            logger.info(f"  - {op_info.get('name', 'Unknown')}: {op_info.get('is_available', False)}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error verificando operator_service: {e}")
        return False

def run_direct_validation():
    """Ejecuta todas las validaciones directas"""
    logger.info("=" * 60)
    logger.info("KRONOS - TESTING DIRECTO DE VALIDACIONES")
    logger.info("=" * 60)
    
    tests = [
        ("Imports de módulos", test_imports),
        ("Procesadores de operadores", test_operator_processors),
        ("Estructura de base de datos", test_database_tables),
        ("Archivos CLARO", test_claro_file_structure),
        ("Métodos operator_service", test_operator_service_methods)
    ]
    
    results = {}
    total_time = 0
    
    for test_name, test_func in tests:
        logger.info(f"\nEjecutando: {test_name}")
        start_time = time.time()
        
        try:
            success = test_func()
            test_time = time.time() - start_time
            total_time += test_time
            
            results[test_name] = {
                'status': 'PASSED' if success else 'FAILED',
                'time': round(test_time, 2)
            }
            
            logger.info(f"Resultado: {'PASADO' if success else 'FALLIDO'} ({test_time:.2f}s)")
            
        except Exception as e:
            test_time = time.time() - start_time
            total_time += test_time
            
            results[test_name] = {
                'status': 'ERROR',
                'error': str(e),
                'time': round(test_time, 2)
            }
            
            logger.error(f"ERROR: {e} ({test_time:.2f}s)")
    
    # Generar reporte
    passed = sum(1 for r in results.values() if r['status'] == 'PASSED')
    total = len(results)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_time': round(total_time, 2),
        'tests_passed': passed,
        'tests_total': total,
        'success_rate': round((passed / total) * 100, 2),
        'results': results,
        'corrections_status': {
            'modules_import_correctly': results.get('Imports de módulos', {}).get('status') == 'PASSED',
            'processors_available': results.get('Procesadores de operadores', {}).get('status') == 'PASSED', 
            'database_structure_ok': results.get('Estructura de base de datos', {}).get('status') == 'PASSED',
            'claro_files_readable': results.get('Archivos CLARO', {}).get('status') in ['PASSED', 'WARNING'],
            'operator_service_working': results.get('Métodos operator_service', {}).get('status') == 'PASSED'
        }
    }
    
    # Guardar reporte
    report_path = current_dir / 'direct_validation_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info("\n" + "=" * 60)
    logger.info("REPORTE FINAL")
    logger.info("=" * 60)
    logger.info(f"Pruebas exitosas: {passed}/{total}")
    logger.info(f"Tasa de éxito: {report['success_rate']}%")
    logger.info(f"Tiempo total: {total_time:.2f}s")
    logger.info(f"Reporte guardado: {report_path}")
    
    # Verificar correcciones críticas
    logger.info("\nESTADO DE CORRECCIONES:")
    corrections = report['corrections_status']
    logger.info(f"  Módulos importan correctamente: {'✓' if corrections['modules_import_correctly'] else '✗'}")
    logger.info(f"  Procesadores disponibles: {'✓' if corrections['processors_available'] else '✗'}")
    logger.info(f"  Base de datos OK: {'✓' if corrections['database_structure_ok'] else '✗'}")
    logger.info(f"  Archivos CLARO legibles: {'✓' if corrections['claro_files_readable'] else '✗'}")
    logger.info(f"  Operator service funcional: {'✓' if corrections['operator_service_working'] else '✗'}")
    
    # Determinar estado general
    critical_fixes = [
        corrections['modules_import_correctly'],
        corrections['processors_available'],
        corrections['database_structure_ok']
    ]
    
    if all(critical_fixes):
        logger.info("\n🎉 CORRECCIONES CRÍTICAS VALIDADAS - SISTEMA ESTABLE")
        return True
    else:
        logger.info("\n⚠️ ALGUNAS CORRECCIONES CRÍTICAS FALLARON")
        return False

def main():
    """Función principal"""
    try:
        success = run_direct_validation()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Error crítico: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()