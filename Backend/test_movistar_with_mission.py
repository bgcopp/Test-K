"""
Test Movistar con Mision Real
=============================
Crea una mision real y procesa el archivo de Movistar para probar
la funcionalidad completa de Cell ID y LAC.

Author: KRONOS Development Team
Date: 2025-08-14
"""

import os
import sys
import uuid
from datetime import datetime

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db_connection
from services.file_processor_service import FileProcessorService
from services.operator_data_service import get_operator_sheet_data


def create_test_mission():
    """Crea una mision de prueba"""
    mission_id = str(uuid.uuid4())
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO missions (
                id, code, name, description, status, start_date, 
                end_date, created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            mission_id,
            f"TEST-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "Mision Test Cell ID LAC",
            "Prueba de funcionalidad Cell ID y LAC para Movistar",
            "En Progreso",
            "2024-04-18",
            "2024-04-19",
            "admin",
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        
    print(f"Mision creada: {mission_id}")
    return mission_id


def process_movistar_with_mission(mission_id):
    """Procesa el archivo de Movistar con una mision valida"""
    file_path = r"C:\Soluciones\BGC\claude\KNSOft\datatest\Movistar\Formato Excel\jgd202410754_07F08305_vozm_saliente_ MOVISTAR.xlsx"
    
    if not os.path.exists(file_path):
        print(f"Archivo no encontrado: {file_path}")
        return None
    
    print(f"Procesando: {os.path.basename(file_path)}")
    
    processor = FileProcessorService()
    
    file_upload_id = str(uuid.uuid4())
    file_name = os.path.basename(file_path)
    
    print(f"File Upload ID: {file_upload_id}")
    
    # Leer archivo
    with open(file_path, 'rb') as f:
        file_bytes = f.read()
    
    # Procesar archivo
    result = processor.process_movistar_llamadas_salientes(
        file_bytes, file_name, file_upload_id, mission_id
    )
    
    if result['success']:
        print(f"EXITO: {result.get('processed_records')} registros procesados")
        print(f"Errores: {result.get('failed_records', 0)}")
        return file_upload_id
    else:
        print(f"ERROR: {result.get('error')}")
        return None


def verify_cell_id_lac_data(file_upload_id):
    """Verifica los datos de Cell ID y LAC"""
    print(f"\nVerificando Cell ID y LAC...")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Estadisticas
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(cellid_decimal) as with_cellid,
                COUNT(lac_decimal) as with_lac,
                COUNT(DISTINCT celda_origen) as unique_celdas
            FROM operator_call_data 
            WHERE file_upload_id = ?
        """, (file_upload_id,))
        
        stats = cursor.fetchone()
        total, with_cellid, with_lac, unique_celdas = stats
        
        print(f"Total registros: {total}")
        print(f"Con Cell ID: {with_cellid}")
        print(f"Con LAC: {with_lac}")
        print(f"Celdas unicas: {unique_celdas}")
        
        if total > 0:
            conversion_rate = (with_cellid / total * 100)
            print(f"Tasa conversion: {conversion_rate:.1f}%")
            
            # Verificar conversion especifica
            cursor.execute("""
                SELECT celda_origen, cellid_decimal, lac_decimal, COUNT(*) as count
                FROM operator_call_data 
                WHERE file_upload_id = ?
                AND celda_origen = '07F083-05'
                GROUP BY celda_origen, cellid_decimal, lac_decimal
            """, (file_upload_id,))
            
            specific = cursor.fetchone()
            if specific:
                celda, cellid, lac, count = specific
                print(f"\nVerificacion especifica:")
                print(f"  {celda} -> Cell ID: {cellid}, LAC: {lac} ({count} registros)")
                
                # Verificar valores esperados
                expected_cellid = 520323  # 07F083 hex = 520323 dec
                expected_lac = 5          # 05 hex = 5 dec
                
                cellid_ok = cellid == expected_cellid
                lac_ok = lac == expected_lac
                
                print(f"  Cell ID correcto: {'SI' if cellid_ok else 'NO'} (esperado: {expected_cellid})")
                print(f"  LAC correcto: {'SI' if lac_ok else 'NO'} (esperado: {expected_lac})")
                
                return cellid_ok and lac_ok
        
        return total > 0


def test_api_with_new_fields(file_upload_id):
    """Prueba la API con los nuevos campos"""
    print(f"\nProbando API...")
    
    response = get_operator_sheet_data(file_upload_id, page=1, page_size=5)
    
    if response.get('success'):
        columns = response.get('columns', [])
        display_names = response.get('displayNames', {})
        data = response.get('data', [])
        
        print(f"API exitosa: {len(data)} registros")
        
        # Verificar nuevas columnas
        has_cellid = 'cellid_decimal' in columns
        has_lac = 'lac_decimal' in columns
        
        print(f"Columna cellid_decimal: {'SI' if has_cellid else 'NO'}")
        print(f"Columna lac_decimal: {'SI' if has_lac else 'NO'}")
        
        if has_cellid:
            cellid_name = display_names.get('cellid_decimal', 'N/A')
            print(f"  Display: '{cellid_name}'")
        
        if has_lac:
            lac_name = display_names.get('lac_decimal', 'N/A')  
            print(f"  Display: '{lac_name}'")
        
        # Muestra de datos
        if data:
            print(f"\nMuestra de datos:")
            for i, record in enumerate(data[:2], 1):
                celda = record.get('celda_origen', 'N/A')
                cellid = record.get('cellid_decimal', 'N/A')
                lac = record.get('lac_decimal', 'N/A')
                numero = record.get('numero_origen', 'N/A')
                
                print(f"  {i}. {numero} | Celda: {celda} -> Cell ID: {cellid}, LAC: {lac}")
        
        return has_cellid and has_lac
    else:
        print(f"Error API: {response.get('error')}")
        return False


def cleanup_test_data(mission_id, file_upload_id):
    """Limpia los datos de prueba"""
    print(f"\nLimpiando datos...")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Eliminar datos de llamadas
        cursor.execute("DELETE FROM operator_call_data WHERE file_upload_id = ?", (file_upload_id,))
        call_deleted = cursor.rowcount
        
        # Eliminar hoja de datos
        cursor.execute("DELETE FROM operator_data_sheets WHERE id = ?", (file_upload_id,))
        sheet_deleted = cursor.rowcount
        
        # Eliminar mision
        cursor.execute("DELETE FROM missions WHERE id = ?", (mission_id,))
        mission_deleted = cursor.rowcount
        
        conn.commit()
        
        print(f"Eliminado: {call_deleted} registros, {sheet_deleted} hoja, {mission_deleted} mision")


def main():
    """Funcion principal"""
    print("KRONOS - Test Movistar Cell ID y LAC con Mision")
    print("=" * 48)
    
    # Crear mision
    mission_id = create_test_mission()
    
    try:
        # Procesar archivo
        file_upload_id = process_movistar_with_mission(mission_id)
        
        if file_upload_id:
            # Verificar datos
            data_ok = verify_cell_id_lac_data(file_upload_id)
            
            # Probar API
            api_ok = test_api_with_new_fields(file_upload_id)
            
            # Resultado
            print(f"\n{'='*48}")
            print(f"Conversion Cell ID/LAC: {'PASS' if data_ok else 'FAIL'}")
            print(f"API con nuevos campos: {'PASS' if api_ok else 'FAIL'}")
            print(f"RESULTADO FINAL: {'EXITOSO' if (data_ok and api_ok) else 'CON ERRORES'}")
            
            # Preguntar si limpiar
            response = input(f"\n¿Limpiar datos de prueba? (s/N): ").strip().lower()
            if response == 's':
                cleanup_test_data(mission_id, file_upload_id)
                print("Datos eliminados.")
            else:
                print(f"Datos conservados:")
                print(f"  Mission ID: {mission_id}")
                print(f"  File Upload ID: {file_upload_id}")
        
        else:
            # Si fallo, limpiar la mision
            cleanup_test_data(mission_id, None)
            print("Prueba fallida")
            
    except Exception as e:
        print(f"Error: {e}")
        cleanup_test_data(mission_id, None)


if __name__ == "__main__":
    main()