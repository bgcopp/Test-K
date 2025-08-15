"""
Test con Archivo Real de Movistar
=================================
Procesa el archivo real de Movistar para verificar la funcionalidad completa
de extraccion y conversion de Cell ID y LAC.

Author: KRONOS Development Team
Date: 2025-08-14
"""

import os
import sys
from datetime import datetime

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db_connection
from services.file_processor_service import FileProcessorService
from services.operator_data_service import get_operator_sheet_data


def process_movistar_file():
    """Procesa el archivo real de Movistar"""
    file_path = r"C:\Soluciones\BGC\claude\KNSOft\datatest\Movistar\Formato Excel\jgd202410754_07F08305_vozm_saliente_ MOVISTAR.xlsx"
    
    if not os.path.exists(file_path):
        print(f"Archivo no encontrado: {file_path}")
        return None
    
    print(f"Procesando archivo: {os.path.basename(file_path)}")
    
    # Crear instancia del procesador
    processor = FileProcessorService()
    
    # Generar IDs unicos
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    test_mission_id = f"test_mission_{timestamp}"
    file_upload_id = f"movistar_test_{timestamp}"
    
    print(f"Mission ID: {test_mission_id}")
    print(f"File Upload ID: {file_upload_id}")
    
    # Leer archivo
    with open(file_path, 'rb') as f:
        file_bytes = f.read()
    
    file_name = os.path.basename(file_path)
    
    # Procesar archivo
    print("Iniciando procesamiento...")
    result = processor.process_movistar_llamadas_salientes(
        file_bytes, file_name, file_upload_id, test_mission_id
    )
    
    if result['success']:
        print(f"Procesamiento exitoso!")
        print(f"Registros procesados: {result.get('processed_records', 0)}")
        print(f"Registros fallidos: {result.get('failed_records', 0)}")
        print(f"Tiempo de procesamiento: {result.get('processing_time_ms', 0)}ms")
        
        return file_upload_id
    else:
        print(f"Error: {result.get('error')}")
        return None


def verify_data(file_upload_id):
    """Verifica los datos procesados"""
    print(f"\nVerificando datos procesados...")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Estadisticas generales
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT celda_origen) as unique_celdas,
                COUNT(cellid_decimal) as with_cellid,
                COUNT(lac_decimal) as with_lac,
                MIN(cellid_decimal) as min_cellid,
                MAX(cellid_decimal) as max_cellid,
                MIN(lac_decimal) as min_lac,
                MAX(lac_decimal) as max_lac
            FROM operator_call_data 
            WHERE file_upload_id = ?
        """, (file_upload_id,))
        
        stats = cursor.fetchone()
        
        print(f"Total registros: {stats[0]}")
        print(f"Celdas unicas: {stats[1]}")
        print(f"Con Cell ID: {stats[2]}")
        print(f"Con LAC: {stats[3]}")
        print(f"Cell ID rango: {stats[4]} - {stats[5]}")
        print(f"LAC rango: {stats[6]} - {stats[7]}")
        
        # Muestras de conversion
        cursor.execute("""
            SELECT celda_origen, cellid_decimal, lac_decimal, COUNT(*) as count
            FROM operator_call_data 
            WHERE file_upload_id = ?
            GROUP BY celda_origen, cellid_decimal, lac_decimal
            ORDER BY count DESC
            LIMIT 5
        """, (file_upload_id,))
        
        samples = cursor.fetchall()
        print("\nConversiones mas frecuentes:")
        for sample in samples:
            print(f"  {sample[0]} -> Cell ID: {sample[1]}, LAC: {sample[2]} ({sample[3]} registros)")


def test_api_with_new_columns(file_upload_id):
    """Prueba la API con las nuevas columnas"""
    print(f"\nProbando API con nuevas columnas...")
    
    response = get_operator_sheet_data(file_upload_id, page=1, page_size=10)
    
    if response.get('success'):
        columns = response.get('columns', [])
        display_names = response.get('displayNames', {})
        data = response.get('data', [])
        
        print(f"API exitosa: {len(data)} registros obtenidos")
        print(f"Columnas disponibles: {len(columns)}")
        
        # Verificar nuevas columnas
        if 'cellid_decimal' in columns:
            print("✓ Columna cellid_decimal presente")
            cellid_display = display_names.get('cellid_decimal', 'N/A')
            print(f"  Display name: '{cellid_display}'")
        
        if 'lac_decimal' in columns:
            print("✓ Columna lac_decimal presente")  
            lac_display = display_names.get('lac_decimal', 'N/A')
            print(f"  Display name: '{lac_display}'")
        
        # Mostrar datos de muestra
        if data:
            print("\nDatos de muestra:")
            for i, record in enumerate(data[:3], 1):
                celda = record.get('celda_origen', 'N/A')
                cellid = record.get('cellid_decimal', 'N/A')
                lac = record.get('lac_decimal', 'N/A')
                numero_origen = record.get('numero_origen', 'N/A')
                fecha = record.get('fecha_hora_llamada', 'N/A')
                
                print(f"  {i}. {numero_origen} | {fecha}")
                print(f"     Celda: {celda} -> Cell ID: {cellid}, LAC: {lac}")
        
        return True
    else:
        print(f"Error en API: {response.get('error')}")
        return False


def cleanup(file_upload_id):
    """Limpia los datos de prueba"""
    print(f"\nLimpiando datos de prueba...")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM operator_call_data WHERE file_upload_id = ?", (file_upload_id,))
        deleted_call = cursor.rowcount
        
        cursor.execute("DELETE FROM operator_data_sheets WHERE id = ?", (file_upload_id,))
        deleted_sheet = cursor.rowcount
        
        conn.commit()
        
        print(f"Eliminados: {deleted_call} registros, {deleted_sheet} hoja")


def main():
    """Funcion principal"""
    print("KRONOS - Test con Archivo Real de Movistar")
    print("=" * 45)
    
    # Procesar archivo
    file_upload_id = process_movistar_file()
    
    if file_upload_id:
        # Verificar datos
        verify_data(file_upload_id)
        
        # Probar API
        api_ok = test_api_with_new_columns(file_upload_id)
        
        # Preguntar si limpiar
        response = input("\n¿Eliminar datos de prueba? (s/N): ").strip().lower()
        if response == 's':
            cleanup(file_upload_id)
        else:
            print(f"Datos conservados. File Upload ID: {file_upload_id}")
        
        print(f"\nPrueba completada: {'EXITOSA' if api_ok else 'CON ERRORES'}")
    else:
        print("No se pudo procesar el archivo")


if __name__ == "__main__":
    main()