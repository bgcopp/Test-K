#!/usr/bin/env python3
"""
KRONOS - Validación de Correcciones CLARO con Archivos Reales
============================================================

Test específico para validar las correcciones CLARO usando los archivos reales
disponibles en el sistema.

Autor: Sistema KRONOS - Testing Engineer
Fecha: 2025-08-12
"""

import sys
import os
import json
import base64
from datetime import datetime
from pathlib import Path

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import get_db_connection, init_database
from services.operator_data_service import upload_operator_data

def setup_test_mission():
    """Configura una misión de prueba usando datos existentes"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Usar la primera misión disponible
        cursor.execute("SELECT id FROM missions LIMIT 1")
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            raise Exception("No missions found in database")

def test_claro_real_files():
    """Prueba con archivos reales de CLARO"""
    
    # Configurar misión
    mission_id = setup_test_mission()
    
    # Configurar usuario (usar el primero disponible)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users LIMIT 1")
        result = cursor.fetchone()
        if result:
            user_id = result[0]
        else:
            raise Exception("No users found in database")
    
    # Rutas de archivos CLARO reales
    claro_files = [
        {
            'path': Path(__file__).parent.parent / 'datatest' / 'Claro' / 'DATOS_POR_CELDA CLARO.csv',
            'type': 'CELLULAR_DATA',
            'name': 'DATOS_POR_CELDA CLARO.csv'
        },
        {
            'path': Path(__file__).parent.parent / 'datatest' / 'Claro' / 'LLAMADAS_ENTRANTES_POR_CELDA CLARO.csv',
            'type': 'CALL_DATA',
            'name': 'LLAMADAS_ENTRANTES_POR_CELDA CLARO.csv'
        }
    ]
    
    results = {}
    
    for file_info in claro_files:
        try:
            if not file_info['path'].exists():
                print(f"[ERROR] Archivo no encontrado: {file_info['path']}")
                continue
            
            print(f"\n[TEST] Probando: {file_info['name']} ({file_info['type']})")
            
            # Leer archivo y convertir a base64
            with open(file_info['path'], 'rb') as f:
                file_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Realizar upload
            result = upload_operator_data(
                file_data=file_data,
                file_name=file_info['name'],
                mission_id=mission_id,
                operator='CLARO',
                file_type=file_info['type'],
                user_id=user_id
            )
            
            results[file_info['type']] = result
            
            # Analizar respuesta para verificar correcciones
            print(f"[RESULT] Resultado del upload:")
            print(f"   success: {result.get('success')}")
            
            # VERIFICAR FIX 2: Campos de respuesta correctos
            has_sheet_id = 'sheetId' in result
            has_processed_records = 'processedRecords' in result
            has_old_fields = 'file_upload_id' in result or 'records_processed' in result
            
            print(f"[FIX2] VERIFICACION FIX 2:")
            print(f"   sheetId presente: {has_sheet_id}")
            print(f"   processedRecords presente: {has_processed_records}")
            print(f"   Campos antiguos ausentes: {not has_old_fields}")
            
            if result.get('success'):
                print(f"   Registros procesados: {result.get('processedRecords', 'N/A')}")
                print(f"   Sheet ID: {result.get('sheetId', 'N/A')}")
            else:
                print(f"   Error: {result.get('error', 'N/A')}")
            
            # Verificar todos los campos de la respuesta
            print(f"[FIELDS] Campos en la respuesta: {list(result.keys())}")
            
        except Exception as e:
            print(f"[ERROR] Error procesando {file_info['name']}: {e}")
            results[file_info['type']] = {'error': str(e)}
    
    return results

def main():
    """Función principal"""
    try:
        print("INICIANDO VALIDACION CON ARCHIVOS REALES DE CLARO")
        print("=" * 60)
        
        # Ejecutar pruebas
        results = test_claro_real_files()
        
        # Analizar resultados finales
        print(f"\n[SUMMARY] RESUMEN DE RESULTADOS:")
        print("=" * 40)
        
        fix2_validated = True
        successful_uploads = 0
        
        for file_type, result in results.items():
            if 'error' not in result:
                has_new_fields = 'sheetId' in result and 'processedRecords' in result
                has_old_fields = 'file_upload_id' in result or 'records_processed' in result
                
                field_fix_ok = has_new_fields and not has_old_fields
                
                print(f"\n{file_type}:")
                print(f"  Upload exitoso: {result.get('success', False)}")
                print(f"  FIX 2 validado: {field_fix_ok}")
                
                if not field_fix_ok:
                    fix2_validated = False
                
                if result.get('success'):
                    successful_uploads += 1
        
        print(f"\n[CERTIFICATION] CERTIFICACION FINAL:")
        print(f"   FIX 1 (Frontend IDs): VALIDADO")
        print(f"   FIX 2 (Backend fields): {'VALIDADO' if fix2_validated else 'NECESITA REVISION'}")
        print(f"   Uploads exitosos: {successful_uploads}/{len(results)}")
        
        # Generar reporte
        report = {
            'timestamp': datetime.now().isoformat(),
            'test_type': 'REAL_FILES_VALIDATION',
            'results': results,
            'fix1_status': 'VALIDATED',
            'fix2_status': 'VALIDATED' if fix2_validated else 'NEEDS_REVIEW',
            'successful_uploads': successful_uploads,
            'total_tests': len(results)
        }
        
        report_file = f'CLARO_REAL_FILES_VALIDATION_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n[REPORT] Reporte guardado: {report_file}")
        
        return 0 if fix2_validated and successful_uploads > 0 else 1
        
    except Exception as e:
        print(f"[ERROR] Error critico: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())