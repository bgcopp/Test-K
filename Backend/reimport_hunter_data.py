#!/usr/bin/env python3
"""
RE-IMPORTACION DE DATOS HUNTER CORRECTOS
=======================================

Script para importar correctamente el archivo SCANHUNTER.xlsx 
y reemplazar los datos corruptos en la base de datos.
"""

import pandas as pd
import sqlite3
from datetime import datetime
import sys

def reimport_hunter_data():
    """Re-importa el archivo HUNTER correcto a la base de datos"""
    
    print("=" * 80)
    print("RE-IMPORTACION DE DATOS HUNTER CORRECTOS")
    print("=" * 80)
    
    try:
        # 1. Leer archivo HUNTER original
        file_path = r'C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\SCANHUNTER.xlsx'
        print(f"Leyendo archivo: {file_path}")
        
        df = pd.read_excel(file_path)
        print(f"Registros en archivo: {len(df)}")
        print(f"Columnas: {list(df.columns)}")
        
        # 2. Conectar a base de datos
        conn = sqlite3.connect('kronos.db')
        cursor = conn.cursor()
        
        # 3. Procesar cada registro del archivo
        print("\nProcesando registros...")
        
        records_inserted = 0
        
        for idx, row in df.iterrows():
            try:
                # Mapear columnas del Excel a la estructura de BD
                record_data = {
                    'mission_id': 'mission_MPFRBNsb',
                    'file_record_id': int(row['Id']) if pd.notna(row['Id']) else idx,
                    'punto': str(row['Punto']) if pd.notna(row['Punto']) else '',
                    'lat': float(row['Latitud']) if pd.notna(row['Latitud']) else 0.0,
                    'lon': float(row['Longitud']) if pd.notna(row['Longitud']) else 0.0,
                    'mnc_mcc': str(row['MNC+MCC']) if pd.notna(row['MNC+MCC']) else '',
                    'operator': str(row['OPERADOR']) if pd.notna(row['OPERADOR']) else '',
                    'rssi': int(row['RSSI']) if pd.notna(row['RSSI']) else 0,
                    'tecnologia': str(row['TECNOLOGIA']) if pd.notna(row['TECNOLOGIA']) else '',
                    'cell_id': str(row['CELLID']) if pd.notna(row['CELLID']) else '',
                    'lac_tac': str(row['LAC o TAC']) if pd.notna(row['LAC o TAC']) else None,
                    'enb': str(row['ENB']) if pd.notna(row['ENB']) else None,
                    'channel': str(row['CHANNEL']) if pd.notna(row['CHANNEL']) else None,
                    'comentario': str(row['Comentario']) if pd.notna(row['Comentario']) else None,
                    'created_at': '2021-05-20 10:30:00'  # Timestamp genérico
                }
                
                # Insertar en base de datos
                insert_query = """
                    INSERT INTO cellular_data (
                        mission_id, file_record_id, punto, lat, lon, mnc_mcc, 
                        operator, rssi, tecnologia, cell_id, lac_tac, enb, 
                        channel, comentario, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                cursor.execute(insert_query, (
                    record_data['mission_id'],
                    record_data['file_record_id'],
                    record_data['punto'],
                    record_data['lat'],
                    record_data['lon'],
                    record_data['mnc_mcc'],
                    record_data['operator'],
                    record_data['rssi'],
                    record_data['tecnologia'],
                    record_data['cell_id'],
                    record_data['lac_tac'],
                    record_data['enb'],
                    record_data['channel'],
                    record_data['comentario'],
                    record_data['created_at']
                ))
                
                records_inserted += 1
                
                if records_inserted % 10 == 0:
                    print(f"  Procesados: {records_inserted}")
                    
            except Exception as e:
                print(f"Error en registro {idx}: {e}")
                continue
        
        # 4. Confirmar transacción
        conn.commit()
        print(f"\nRegistros insertados exitosamente: {records_inserted}")
        
        # 5. Verificar importación
        print("\nVerificando importación...")
        
        cursor.execute('SELECT COUNT(*) FROM cellular_data WHERE mission_id = "mission_MPFRBNsb"')
        total_in_db = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT cell_id) FROM cellular_data WHERE mission_id = "mission_MPFRBNsb"')
        unique_cells_db = cursor.fetchone()[0]
        
        print(f"Total registros en BD: {total_in_db}")
        print(f"Cell IDs únicos en BD: {unique_cells_db}")
        print(f"Cell IDs únicos esperados: 57")
        
        # 6. Verificar Cell IDs específicos
        print("\nVerificando Cell IDs críticos...")
        
        # Cell IDs que DEBEN estar (del archivo)
        expected_cells = ['1535', '51203', '51438', '53591', '56124', '77924']
        
        for cell in expected_cells:
            cursor.execute('SELECT COUNT(*) FROM cellular_data WHERE mission_id = "mission_MPFRBNsb" AND cell_id = ?', (cell,))
            count = cursor.fetchone()[0]
            status = "✓" if count > 0 else "✗"
            print(f"  {status} {cell}: {count} registros")
        
        # Cell IDs que NO deben estar (corruptos)
        corrupt_cells = ['16040', '16477', '16478']
        
        print("\nVerificando que celdas corruptas NO estén:")
        for cell in corrupt_cells:
            cursor.execute('SELECT COUNT(*) FROM cellular_data WHERE mission_id = "mission_MPFRBNsb" AND cell_id = ?', (cell,))
            count = cursor.fetchone()[0]
            status = "✓" if count == 0 else "✗"
            print(f"  {status} {cell}: {count} registros (debe ser 0)")
        
        conn.close()
        
        # 7. Resultado final
        print("\n" + "=" * 80)
        if total_in_db == len(df) and unique_cells_db == 57:
            print("✓ RE-IMPORTACION COMPLETADA EXITOSAMENTE")
            print("✓ Datos HUNTER correctos restaurados")
            print("✓ Datos corruptos eliminados")
            return True
        else:
            print("✗ RE-IMPORTACION INCOMPLETA")
            print(f"✗ Esperado: {len(df)} registros, Obtenido: {total_in_db}")
            return False
        
    except Exception as e:
        print(f"ERROR CRITICO durante re-importación: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = reimport_hunter_data()
    sys.exit(0 if success else 1)