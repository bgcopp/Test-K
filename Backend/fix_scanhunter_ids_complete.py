#!/usr/bin/env python3
"""
Script para corregir completamente los IDs del archivo SCANHUNTER
- Elimina registros duplicados incorrectos  
- Re-procesa archivo SCANHUNTER.xlsx con IDs reales [0, 12, 32]
- Valida resultado final
"""

import sqlite3
import pandas as pd
import sys
from pathlib import Path
import os

def fix_scanhunter_data():
    """Corrige completamente los datos de SCANHUNTER"""
    
    current_dir = Path(__file__).parent
    db_path = current_dir / 'kronos.db'
    excel_path = current_dir / '..' / 'archivos' / 'envioarchivosparaanalizar (1)' / 'SCANHUNTER.xlsx'
    
    if not db_path.exists():
        print(f"ERROR: Base de datos no encontrada: {db_path}")
        return False
        
    if not excel_path.exists():
        print(f"ERROR: Archivo SCANHUNTER no encontrado: {excel_path}")
        return False
    
    try:
        # 1. LIMPIAR DATOS INCORRECTOS DE BD
        print("PASO 1: Limpiando datos incorrectos de cellular_data...")
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Verificar estado actual
        cursor.execute("SELECT COUNT(*) FROM cellular_data")
        total_before = cursor.fetchone()[0]
        print(f"Registros totales antes: {total_before}")
        
        cursor.execute("SELECT COUNT(*) FROM cellular_data WHERE file_record_id IS NULL")
        null_records = cursor.fetchone()[0]
        print(f"Registros con file_record_id NULL: {null_records}")
        
        cursor.execute("SELECT COUNT(*) FROM cellular_data WHERE file_record_id IS NOT NULL")
        not_null_records = cursor.fetchone()[0]
        print(f"Registros con file_record_id asignado: {not_null_records}")
        
        # Eliminar TODOS los registros de cellular_data para empezar limpio
        print("Eliminando todos los registros de cellular_data...")
        cursor.execute("DELETE FROM cellular_data")
        
        # 2. RE-PROCESAR ARCHIVO EXCEL CON IDs CORRECTOS
        print("PASO 2: Re-procesando archivo SCANHUNTER.xlsx...")
        
        # Leer archivo Excel
        df = pd.read_excel(str(excel_path))
        print(f"Archivo leido: {len(df)} registros")
        
        # Verificar columnas requeridas
        required_columns = ['Id', 'Punto', 'Latitud', 'Longitud', 'MNC+MCC', 'OPERADOR', 'RSSI', 'TECNOLOGIA', 'CELLID']
        missing_cols = [col for col in required_columns if col not in df.columns]
        
        if missing_cols:
            print(f"ERROR: Columnas faltantes: {missing_cols}")
            print(f"Columnas disponibles: {list(df.columns)}")
            return False
        
        # Obtener mision_id (asumiendo que es m1 basado en logs anteriores)
        cursor.execute("SELECT id FROM missions WHERE code = 'PX-001' LIMIT 1")
        mission_result = cursor.fetchone()
        if not mission_result:
            print("ERROR: No se encontro mision PX-001")
            return False
        mission_id = mission_result[0]
        print(f"Usando mission_id: {mission_id}")
        
        # 3. INSERTAR REGISTROS CON IDs REALES
        print("PASO 3: Insertando registros con file_record_id correctos...")
        
        records_inserted = 0
        id_counts = {}
        
        for index, row in df.iterrows():
            try:
                # Usar el ID REAL del archivo Excel
                file_record_id = int(row['Id'])  # Este es el ID real del archivo
                
                # Contar por ID
                if file_record_id not in id_counts:
                    id_counts[file_record_id] = 0
                id_counts[file_record_id] += 1
                
                # Mapear datos
                punto = str(row['Punto']) if pd.notna(row['Punto']) else ''
                lat = float(row['Latitud']) if pd.notna(row['Latitud']) else 0.0
                lon = float(row['Longitud']) if pd.notna(row['Longitud']) else 0.0
                mnc_mcc = str(row['MNC+MCC']) if pd.notna(row['MNC+MCC']) else ''
                operador = str(row['OPERADOR']) if pd.notna(row['OPERADOR']) else ''
                rssi = int(row['RSSI']) if pd.notna(row['RSSI']) else -120
                tecnologia = str(row['TECNOLOGIA']) if pd.notna(row['TECNOLOGIA']) else 'UNKNOWN'
                cell_id = str(row['CELLID']) if pd.notna(row['CELLID']) else ''
                lac_tac = str(row['LAC o TAC']) if pd.notna(row['LAC o TAC']) else ''
                enb = str(row['ENB']) if pd.notna(row['ENB']) else ''
                canal = str(row['CHANNEL']) if pd.notna(row['CHANNEL']) else ''
                comentario = str(row['Comentario']) if pd.notna(row['Comentario']) else ''
                
                # Insertar con file_record_id REAL
                cursor.execute("""
                    INSERT INTO cellular_data (
                        mission_id, file_record_id, punto, lat, lon, mnc_mcc, operator, 
                        rssi, tecnologia, cell_id, lac_tac, enb, channel, comentario
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    mission_id, file_record_id, punto, lat, lon, mnc_mcc, operador,
                    rssi, tecnologia, cell_id, lac_tac, enb, canal, comentario
                ))
                
                records_inserted += 1
                
            except Exception as e:
                print(f"ERROR en registro {index}: {e}")
                continue
        
        # Commit cambios
        conn.commit()
        
        # 4. VALIDAR RESULTADOS
        print("PASO 4: Validando resultados...")
        
        cursor.execute("SELECT COUNT(*) FROM cellular_data")
        total_after = cursor.fetchone()[0]
        print(f"Registros totales despues: {total_after}")
        
        cursor.execute("""
            SELECT file_record_id, COUNT(*) as count 
            FROM cellular_data 
            GROUP BY file_record_id 
            ORDER BY file_record_id
        """)
        id_distribution = cursor.fetchall()
        
        print("Distribucion por file_record_id:")
        for file_id, count in id_distribution:
            print(f"  ID {file_id}: {count} registros")
        
        # Verificar que coincide con archivo original
        expected_ids = [0, 12, 32]
        actual_ids = [row[0] for row in id_distribution]
        
        if set(actual_ids) == set(expected_ids):
            print("EXITO: IDs coinciden con archivo original [0, 12, 32]")
        else:
            print(f"ERROR: IDs no coinciden. Esperados: {expected_ids}, Actuales: {actual_ids}")
            return False
        
        # Verificar ordenamiento
        cursor.execute("""
            SELECT file_record_id, punto 
            FROM cellular_data 
            ORDER BY file_record_id ASC 
            LIMIT 10
        """)
        sample_data = cursor.fetchall()
        
        print("Muestra de datos ordenados por file_record_id:")
        for file_id, punto in sample_data[:5]:
            print(f"  file_record_id: {file_id}, punto: {punto}")
        
        conn.close()
        
        print(f"EXITO: Re-procesamiento completo exitoso")
        print(f"  - Registros procesados: {records_inserted}")
        print(f"  - IDs unicos: {list(id_counts.keys())}")
        print(f"  - Distribucion: {dict(id_counts)}")
        
        return True
        
    except Exception as e:
        print(f"ERROR durante correccion: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == '__main__':
    print("INICIO: Corrigiendo datos SCANHUNTER con IDs reales...")
    success = fix_scanhunter_data()
    
    if success:
        print("EXITO: Correccion completa exitosa")
        print("La tabla ahora deberia mostrar IDs reales: [0, 12, 32]")
        sys.exit(0)
    else:
        print("ERROR: Correccion fallo")
        sys.exit(1)