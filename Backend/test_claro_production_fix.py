#!/usr/bin/env python3
"""
Test final de corrección de problemas CLARO en producción
"""

import os
import sys
import logging
import base64
from datetime import datetime

# Add Backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from database.connection import DatabaseManager
from services.operator_service import get_operator_service
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

def create_test_mission():
    """Crear misión de test para validaciones"""
    db_manager = DatabaseManager()
    db_manager.initialize()
    
    with db_manager.get_session() as session:
        # Check if test mission exists
        existing = session.execute(
            text("SELECT COUNT(*) FROM missions WHERE id = 'TEST-CLARO-PRODUCTION'")
        ).scalar()
        
        if existing == 0:
            # Create test mission
            session.execute(text("""
                INSERT INTO missions (id, code, name, description, status, start_date, created_by, created_at)
                VALUES ('TEST-CLARO-PRODUCTION', 'TEST-CLARO-PROD', 'Test Misión CLARO Producción', 
                       'Misión de prueba para validar archivos CLARO', 'Planificación', 
                       '2025-01-01', 'admin', CURRENT_TIMESTAMP)
            """))
            session.commit()
            print("Mision de test creada")
        else:
            print("Mision de test ya existe")

def test_claro_file(file_path, file_type):
    """Test individual de archivo CLARO"""
    print(f"\n{'='*50}")
    print(f"PROBANDO: {file_type}")
    print(f"Archivo: {file_path}")
    print(f"{'='*50}")
    
    # Read file and encode to base64
    with open(file_path, 'rb') as f:
        content = f.read()
    
    file_data = {
        'name': os.path.basename(file_path),
        'content': 'data:text/csv;base64,' + base64.b64encode(content).decode('utf-8')
    }
    
    print(f"Archivo: {file_data['name']}")
    print(f"Tamaño: {len(content):,} bytes")
    
    try:
        # Initialize database for operator service
        db_manager = DatabaseManager()
        db_manager.initialize()
        
        # Get operator service
        operator_service = get_operator_service()
        
        # Process file
        start_time = datetime.now()
        result = operator_service.process_file_for_operator(
            'CLARO', 
            file_data, 
            file_type, 
            'TEST-CLARO-PRODUCTION'
        )
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        
        print(f"EXITO!")
        print(f"Tiempo: {processing_time:.3f}s")
        print(f"Registros procesados: {result.get('records_processed', 0)}")
        print(f"ID archivo: {result.get('file_id', 'N/A')}")
        
        return True, result
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False, str(e)

def main():
    """Test principal"""
    print("KRONOS - Test Final Correccion CLARO")
    print("="*60)
    
    # Create test mission
    create_test_mission()
    
    # Test files
    test_files = [
        ('../datatest/Claro/DATOS_POR_CELDA CLARO_MANUAL_FIX.csv', 'DATOS'),
        ('../datatest/Claro/LLAMADAS_ENTRANTES_POR_CELDA CLARO.csv', 'LLAMADAS_ENTRANTES'),
        ('../datatest/Claro/LLAMADAS_SALIENTES_POR_CELDA CLARO.csv', 'LLAMADAS_SALIENTES')
    ]
    
    results = []
    
    for file_path, file_type in test_files:
        if os.path.exists(file_path):
            success, result = test_claro_file(file_path, file_type)
            results.append((file_type, success, result))
        else:
            print(f"Archivo no encontrado: {file_path}")
            results.append((file_type, False, f"Archivo no encontrado: {file_path}"))
    
    # Summary
    print(f"\n{'='*60}")
    print("RESUMEN FINAL")
    print(f"{'='*60}")
    
    success_count = sum(1 for _, success, _ in results if success)
    total_count = len(results)
    
    for file_type, success, result in results:
        status = "EXITO" if success else "ERROR"
        print(f"{file_type:20} | {status}")
        if not success:
            print(f"{'':20} | {result}")
    
    print(f"\nRESULTADO: {success_count}/{total_count} archivos procesados exitosamente")
    
    if success_count == total_count:
        print("SISTEMA CLARO OPERATIVO - LISTO PARA PRODUCCION")
    else:
        print("Sistema requiere correcciones adicionales")

if __name__ == '__main__':
    main()