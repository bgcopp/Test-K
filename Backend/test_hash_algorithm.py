#!/usr/bin/env python3
"""
Script para probar el algoritmo de hash con datos reales del archivo CLARO.
"""

import sys
import os
import pandas as pd
import hashlib
from datetime import datetime
from collections import Counter

# Agregar el directorio padre al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.data_normalizer_service import DataNormalizerService

def test_hash_duplicates():
    """
    Probar si el algoritmo de hash genera duplicados con datos reales.
    """
    file_path = r"C:\Soluciones\BGC\claude\KNSOft\datatest\Claro\formato excel\DATOS_POR_CELDA CLARO.xlsx"
    
    print("=" * 80)
    print("PRUEBA DE ALGORITMO DE HASH - ARCHIVO CLARO")
    print("=" * 80)
    
    try:
        # Leer archivo Excel
        print(f"Leyendo archivo: {file_path}")
        df = pd.read_excel(file_path)
        print(f"Total de registros: {len(df)}")
        print()
        
        # Inicializar el normalizador
        normalizer = DataNormalizerService()
        
        # Procesar todos los registros y calcular hashes
        hashes = []
        sample_records = []
        
        print("Procesando registros y calculando hashes...")
        print("-" * 50)
        
        for index, row in df.iterrows():
            # Simular normalización básica para CLARO
            raw_record = row.to_dict()
            
            # Normalizar fecha
            fecha_trafico = str(raw_record.get('fecha_trafico', ''))
            if len(fecha_trafico) == 14 and fecha_trafico.isdigit():
                year = int(fecha_trafico[:4])
                month = int(fecha_trafico[4:6])
                day = int(fecha_trafico[6:8])
                hour = int(fecha_trafico[8:10])
                minute = int(fecha_trafico[10:12])
                second = int(fecha_trafico[12:14])
                
                fecha_datetime = datetime(year, month, day, hour, minute, second)
            else:
                fecha_datetime = None
            
            # Crear record normalizado simulado
            normalized_record = {
                'numero_telefono': str(raw_record.get('numero', '')),
                'fecha_hora_inicio': fecha_datetime,
                'celda_id': str(raw_record.get('celda_decimal', '')),
                'operator': 'CLARO',
                'tipo_conexion': str(raw_record.get('tipo_cdr', ''))
            }
            
            # Calcular hash usando la función real del normalizador
            record_hash = normalizer._calculate_record_hash(normalized_record)
            hashes.append(record_hash)
            
            # Guardar algunos ejemplos para análisis
            if len(sample_records) < 10:
                sample_records.append({
                    'index': index + 1,
                    'numero': normalized_record['numero_telefono'],
                    'fecha': fecha_datetime,
                    'celda': normalized_record['celda_id'],
                    'hash': record_hash
                })
            
            # Mostrar progreso cada 25 registros
            if (index + 1) % 25 == 0:
                print(f"   Procesados: {index + 1}/{len(df)}")
        
        print(f"Procesamiento completo: {len(hashes)} hashes generados")
        print()
        
        # Analizar duplicados
        hash_counts = Counter(hashes)
        duplicates = {hash_val: count for hash_val, count in hash_counts.items() if count > 1}
        
        print("ANALISIS DE DUPLICADOS:")
        print("-" * 50)
        print(f"Hashes unicos: {len(hash_counts)}")
        print(f"Hashes duplicados: {len(duplicates)}")
        print(f"Total de registros duplicados: {sum(duplicates.values()) - len(duplicates)}")
        print()
        
        if duplicates:
            print("HASHES DUPLICADOS ENCONTRADOS:")
            print("-" * 50)
            for i, (hash_val, count) in enumerate(list(duplicates.items())[:5], 1):
                print(f"{i}. Hash: {hash_val[:16]}... (aparece {count} veces)")
                
                # Encontrar registros con este hash
                duplicate_records = []
                for j, h in enumerate(hashes):
                    if h == hash_val:
                        record_data = df.iloc[j]
                        duplicate_records.append({
                            'row': j + 1,
                            'numero': record_data['numero'],
                            'fecha': record_data['fecha_trafico'],
                            'celda': record_data['celda_decimal']
                        })
                
                print(f"   Registros con este hash:")
                for dup_rec in duplicate_records[:3]:  # Mostrar máximo 3
                    print(f"     Fila {dup_rec['row']}: {dup_rec['numero']} | {dup_rec['fecha']} | {dup_rec['celda']}")
                print()
        else:
            print("NO SE ENCONTRARON HASHES DUPLICADOS")
            print("   Todos los registros tienen hashes unicos")
        
        # Mostrar muestra de hashes
        print("MUESTRA DE HASHES GENERADOS:")
        print("-" * 50)
        for i, sample in enumerate(sample_records[:5], 1):
            print(f"{i}. Fila {sample['index']}: {sample['numero']} | {sample['fecha']} | {sample['celda']}")
            print(f"   Hash: {sample['hash'][:32]}...")
            print()
        
        # Análisis estadístico adicional
        print("ESTADISTICAS ADICIONALES:")
        print("-" * 50)
        
        # Contar registros por número de teléfono
        numeros_count = df['numero'].value_counts()
        print(f"Números únicos: {len(numeros_count)}")
        print(f"Número con más registros: {numeros_count.index[0]} ({numeros_count.iloc[0]} registros)")
        
        # Contar registros por fecha
        fechas_count = df['fecha_trafico'].value_counts()
        print(f"Fechas únicas: {len(fechas_count)}")
        print(f"Fecha con más registros: {fechas_count.index[0]} ({fechas_count.iloc[0]} registros)")
        
        return {
            'total_records': len(df),
            'unique_hashes': len(hash_counts),
            'duplicate_hashes': len(duplicates),
            'duplicate_records': sum(duplicates.values()) - len(duplicates),
            'success_rate': (len(hash_counts) / len(df)) * 100
        }
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_hash_duplicates()