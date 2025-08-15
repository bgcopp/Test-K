#!/usr/bin/env python3
"""
Script para probar el procesamiento completo del archivo CLARO con logs detallados.
"""

import sys
import os
import uuid
import pandas as pd
from datetime import datetime

# Agregar el directorio padre al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.file_processor_service import FileProcessorService
from database.connection import get_db_connection

def create_test_mission():
    """Crear una misión de prueba para el procesamiento."""
    mission_id = f"test_mission_{uuid.uuid4().hex[:8]}"
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Crear misión de prueba
        cursor.execute("""
            INSERT INTO missions (id, name, description, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            mission_id,
            "Misión de Prueba CLARO",
            "Prueba de procesamiento 100% registros CLARO",
            "active",
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        print(f"✅ Misión de prueba creada: {mission_id}")
    
    return mission_id

def test_claro_processing():
    """Probar el procesamiento completo del archivo CLARO."""
    file_path = r"C:\Soluciones\BGC\claude\KNSOft\datatest\Claro\formato excel\DATOS_POR_CELDA CLARO.xlsx"
    
    print("=" * 80)
    print("PRUEBA DE PROCESAMIENTO COMPLETO - ARCHIVO CLARO")
    print("=" * 80)
    
    try:
        # Crear misión de prueba
        mission_id = create_test_mission()
        
        # Inicializar el procesador
        processor = FileProcessorService()
        
        # Leer archivo para verificar estructura
        print(f"📂 Leyendo archivo: {file_path}")
        df = pd.read_excel(file_path)
        print(f"📊 Total de registros en archivo: {len(df)}")
        print(f"📋 Columnas: {list(df.columns)}")
        print()
        
        # Mostrar muestra de datos
        print("🔍 MUESTRA DE DATOS (primeros 3 registros):")
        print(df.head(3).to_string())
        print()
        
        # Procesar archivo
        print("🚀 INICIANDO PROCESAMIENTO...")
        print("-" * 50)
        
        result = processor.process_claro_cellular_data(
            file_path=file_path,
            mission_id=mission_id
        )
        
        print("📋 RESULTADO DEL PROCESAMIENTO:")
        print("-" * 50)
        print(f"✅ Éxito: {result.get('success', False)}")
        print(f"📈 Registros procesados: {result.get('records_processed', 0)}")
        print(f"❌ Registros fallidos: {result.get('records_failed', 0)}")
        print(f"🎯 Tasa de éxito: {result.get('success_rate', 0)}%")
        print(f"⏱️ Tiempo de procesamiento: {result.get('processing_time_seconds', 0)} segundos")
        
        # Mostrar detalles
        details = result.get('details', {})
        print(f"\n📊 DETALLES:")
        print(f"   - Registros originales: {details.get('original_records', 0)}")
        print(f"   - Registros limpiados: {details.get('cleaned_records', 0)}")
        print(f"   - Chunks procesados: {details.get('chunks_processed', 0)}")
        
        # Mostrar errores si los hay
        errors = details.get('processing_errors', [])
        if errors:
            print(f"\n❌ ERRORES ENCONTRADOS ({len(errors)}):")
            for i, error in enumerate(errors[:5], 1):
                print(f"   {i}. Fila {error.get('row', 'N/A')}: {error.get('errors', [])}")
        
        # Verificar datos en base de datos
        print("\n🔍 VERIFICACIÓN EN BASE DE DATOS:")
        print("-" * 50)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Contar registros insertados
            cursor.execute("""
                SELECT COUNT(*) FROM operator_cellular_data 
                WHERE mission_id = ?
            """, (mission_id,))
            
            db_count = cursor.fetchone()[0]
            print(f"📊 Registros en BD: {db_count}")
            
            # Mostrar algunos ejemplos
            cursor.execute("""
                SELECT numero_telefono, fecha_hora_inicio, celda_id, operator
                FROM operator_cellular_data 
                WHERE mission_id = ?
                ORDER BY fecha_hora_inicio
                LIMIT 5
            """, (mission_id,))
            
            sample_records = cursor.fetchall()
            if sample_records:
                print(f"\n📋 MUESTRA DE REGISTROS EN BD:")
                for i, (numero, fecha, celda, operador) in enumerate(sample_records, 1):
                    print(f"   {i}. {numero} | {fecha} | {celda} | {operador}")
        
        # Análisis final
        print(f"\n🎯 ANÁLISIS FINAL:")
        print("-" * 50)
        expected_records = len(df)
        actual_processed = result.get('records_processed', 0)
        
        if actual_processed == expected_records:
            print("✅ ¡ÉXITO COMPLETO! Todos los registros fueron procesados.")
        else:
            missing = expected_records - actual_processed
            print(f"⚠️  PROCESAMIENTO INCOMPLETO:")
            print(f"   - Esperados: {expected_records}")
            print(f"   - Procesados: {actual_processed}")
            print(f"   - Faltantes: {missing} ({(missing/expected_records)*100:.1f}%)")
            
            # Investigar por qué faltan registros
            print(f"\n🔍 INVESTIGANDO REGISTROS FALTANTES...")
            
            if result.get('success', False) and result.get('success_rate', 0) < 100:
                print("   - El procesamiento se completó pero con errores")
                print("   - Algunos registros no pasaron las validaciones")
            elif not result.get('success', False):
                print("   - El procesamiento falló completamente")
                print(f"   - Error: {result.get('error', 'No especificado')}")
            else:
                print("   - Causa desconocida - revisar logs del sistema")
        
        return result
        
    except Exception as e:
        print(f"💥 ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_claro_processing()