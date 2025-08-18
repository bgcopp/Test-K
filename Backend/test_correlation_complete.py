"""
Prueba completa del sistema de análisis de correlación de objetivos.
Valida el funcionamiento end-to-end de la funcionalidad implementada.
"""

import sys
import os
import sqlite3
import json
from datetime import datetime, timedelta

# Agregar el directorio actual al path
sys.path.insert(0, os.getcwd())

from services.correlation_analysis_service import get_correlation_service

def create_test_data():
    """Crear datos de prueba temporalmente alineados para validar el análisis."""
    
    print("📝 Creando datos de prueba temporalmente alineados...")
    
    conn = sqlite3.connect('kronos.db')
    cursor = conn.cursor()
    
    try:
        # Obtener la misión Fenix021
        cursor.execute("SELECT id FROM missions WHERE code = 'Fenix021'")
        mission_result = cursor.fetchone()
        if not mission_result:
            print("❌ Misión Fenix021 no encontrada")
            return None
        
        mission_id = mission_result[0]
        print(f"✅ Misión encontrada: {mission_id}")
        
        # Limpiar datos de prueba anteriores si existen
        cursor.execute("DELETE FROM operator_cellular_data WHERE operator = 'TEST_OPERATOR'")
        cursor.execute("DELETE FROM operator_call_data WHERE operator = 'TEST_OPERATOR'")
        
        # Obtener algunas celdas de HUNTER para crear coincidencias
        cursor.execute("""
            SELECT DISTINCT cell_id 
            FROM cellular_data 
            WHERE mission_id = ? 
            LIMIT 5
        """, (mission_id,))
        
        hunter_cells = [row[0] for row in cursor.fetchall()]
        print(f"📍 Celdas HUNTER encontradas: {hunter_cells}")
        
        if not hunter_cells:
            print("❌ No hay celdas HUNTER para crear pruebas")
            return None
        
        # Crear datos de operador con coincidencias
        base_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Números de prueba (colombianos válidos)
        test_numbers = [
            "3001234567",
            "3009876543", 
            "3012345678",
            "3154567890",
            "3207654321"
        ]
        
        # Insertar datos celulares de operador
        for i, number in enumerate(test_numbers):
            for j, cell_id in enumerate(hunter_cells[:3]):  # Usar las primeras 3 celdas
                # Crear coincidencias variadas
                coincidences = 2 + (i * j) % 5  # Entre 2 y 6 coincidencias
                
                for k in range(coincidences):
                    cursor.execute("""
                        INSERT INTO operator_cellular_data (
                            file_upload_id, mission_id, operator, numero_telefono,
                            fecha_hora_inicio, fecha_hora_fin, celda_id, lac_tac,
                            trafico_subida_bytes, trafico_bajada_bytes,
                            tecnologia, tipo_conexion, record_hash, created_at
                        ) VALUES (
                            'test_upload_cellular', ?, 'TEST_OPERATOR', ?,
                            datetime('now', '-{} minutes'), datetime('now', '-{} minutes'),
                            ?, '12345', 1048576, 2097152, 'LTE', 'DATOS',
                            'test_hash_{}_{}_{}', datetime('now')
                        )
                    """.format(
                        i * 30 + k * 5,  # Diferentes horarios
                        i * 30 + k * 5 - 10,
                        number, cell_id, k
                    ), (mission_id, number, cell_id))
        
        # Insertar datos de llamadas
        for i, number in enumerate(test_numbers):
            for j, cell_id in enumerate(hunter_cells[:2]):  # Usar las primeras 2 celdas
                coincidences = 1 + (i + j) % 4  # Entre 1 y 4 coincidencias
                
                for k in range(coincidences):
                    cursor.execute("""
                        INSERT INTO operator_call_data (
                            file_upload_id, mission_id, operator, tipo_llamada,
                            numero_origen, numero_destino, numero_objetivo,
                            fecha_hora_llamada, duracion_segundos,
                            celda_origen, celda_destino, celda_objetivo,
                            tecnologia, tipo_trafico, estado_llamada,
                            record_hash, created_at
                        ) VALUES (
                            'test_upload_calls', ?, 'TEST_OPERATOR', 'ENTRANTE',
                            '6011234567', ?, ?,
                            datetime('now', '-{} minutes'), ?,
                            ?, ?, ?,
                            'LTE', 'VOZ', 'COMPLETADA',
                            'test_call_hash_{}_{}_{}', datetime('now')
                        )
                    """.format(
                        i * 45 + k * 8,  # Diferentes horarios para llamadas
                        120 + (i * 10) + (k * 5)  # Duración variable
                    ), (mission_id, number, number, number, cell_id, cell_id, cell_id, number, cell_id, k))
        
        conn.commit()
        print("✅ Datos de prueba creados exitosamente")
        
        # Verificar datos creados
        cursor.execute("SELECT COUNT(*) FROM operator_cellular_data WHERE operator = 'TEST_OPERATOR'")
        cellular_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM operator_call_data WHERE operator = 'TEST_OPERATOR'")
        calls_count = cursor.fetchone()[0]
        
        print(f"📊 Datos creados: {cellular_count} registros celulares, {calls_count} llamadas")
        
        return mission_id
        
    except Exception as e:
        print(f"❌ Error creando datos de prueba: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def run_correlation_test(mission_id):
    """Ejecutar prueba completa del análisis de correlación."""
    
    print("\n🔍 EJECUTANDO ANÁLISIS DE CORRELACIÓN")
    print("=" * 50)
    
    service = get_correlation_service()
    
    # Parámetros de prueba
    start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    min_coincidences = 2
    
    print(f"📅 Rango de fechas: {start_date} a {end_date}")
    print(f"🎯 Coincidencias mínimas: {min_coincidences}")
    
    # Ejecutar análisis
    result = service.analyze_correlation(
        mission_id=mission_id,
        start_date=start_date,
        end_date=end_date,
        min_coincidences=min_coincidences
    )
    
    # Mostrar resultados
    print(f"\n📈 RESULTADOS DEL ANÁLISIS")
    print("=" * 30)
    
    if result.get('success'):
        print(f"✅ Análisis exitoso")
        print(f"⏱️ Tiempo: {result.get('processing_time_seconds')} segundos")
        
        statistics = result.get('statistics', {})
        print(f"\n📊 ESTADÍSTICAS:")
        for key, value in statistics.items():
            print(f"   {key}: {value}")
        
        data = result.get('data', [])
        print(f"\n🎯 NÚMEROS CON COINCIDENCIAS: {len(data)}")
        
        if data:
            print("\nTop resultados:")
            for i, item in enumerate(data[:5], 1):
                print(f"\n{i}. 📱 {item['numero_celular']}")
                print(f"   🎯 Coincidencias: {item['total_coincidencias']}")
                print(f"   📡 Operadores: {', '.join(item['operadores'])}")
                print(f"   📅 Primera aparición: {item['primera_aparicion']}")
                print(f"   📅 Última aparición: {item['ultima_aparicion']}")
                print(f"   📍 Celdas: {list(item['celdas_detalle'].keys())}")
                
                # Mostrar detalle de celdas
                for cell_id, count in item['celdas_detalle'].items():
                    print(f"      • Celda {cell_id}: {count} veces")
        
        # Probar exportación
        print(f"\n📤 PROBANDO EXPORTACIÓN")
        print("=" * 25)
        
        try:
            # Probar exportación CSV
            csv_success = service.export_to_csv(result, 'test_correlation_export.csv')
            print(f"📄 CSV: {'✅' if csv_success else '❌'}")
            
            # Probar exportación Excel
            excel_success = service.export_to_excel(result, 'test_correlation_export.xlsx')
            print(f"📊 Excel: {'✅' if excel_success else '❌'}")
            
        except Exception as e:
            print(f"❌ Error en exportación: {e}")
        
    else:
        print(f"❌ Error en análisis: {result.get('error')}")
    
    return result.get('success', False)

def cleanup_test_data():
    """Limpiar datos de prueba."""
    print("\n🧹 Limpiando datos de prueba...")
    
    conn = sqlite3.connect('kronos.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM operator_cellular_data WHERE operator = 'TEST_OPERATOR'")
        cellular_deleted = cursor.rowcount
        
        cursor.execute("DELETE FROM operator_call_data WHERE operator = 'TEST_OPERATOR'")
        calls_deleted = cursor.rowcount
        
        conn.commit()
        print(f"✅ Limpieza completada: {cellular_deleted + calls_deleted} registros eliminados")
        
    except Exception as e:
        print(f"❌ Error en limpieza: {e}")
    finally:
        conn.close()

def main():
    """Función principal de prueba."""
    print("🚀 PRUEBA COMPLETA DEL SISTEMA DE CORRELACIÓN DE OBJETIVOS")
    print("=" * 60)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Paso 1: Crear datos de prueba
        mission_id = create_test_data()
        if not mission_id:
            print("❌ No se pudo crear datos de prueba")
            return False
        
        # Paso 2: Ejecutar análisis
        success = run_correlation_test(mission_id)
        
        # Paso 3: Limpiar
        cleanup_test_data()
        
        # Resultado final
        print(f"\n🏁 RESULTADO FINAL")
        print("=" * 20)
        if success:
            print("✅ TODAS LAS PRUEBAS EXITOSAS")
            print("🎯 El sistema de correlación de objetivos está funcionando correctamente")
        else:
            print("❌ ALGUNAS PRUEBAS FALLARON")
            print("🔧 Revisar logs para detalles")
        
        return success
        
    except Exception as e:
        print(f"💥 ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    main()