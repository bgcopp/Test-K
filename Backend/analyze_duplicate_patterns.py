#!/usr/bin/env python3
"""
Análisis detallado de patrones de duplicados en el archivo CLARO.
"""

import pandas as pd
from collections import defaultdict, Counter

def analyze_duplicate_patterns():
    """
    Analizar los patrones de duplicados para determinar si son legítimos.
    """
    file_path = r"C:\Soluciones\BGC\claude\KNSOft\datatest\Claro\formato excel\DATOS_POR_CELDA CLARO.xlsx"
    
    print("=" * 80)
    print("ANÁLISIS DE PATRONES DE DUPLICADOS - ARCHIVO CLARO")
    print("=" * 80)
    
    try:
        # Leer archivo Excel
        df = pd.read_excel(file_path)
        print(f"Total de registros: {len(df)}")
        print()
        
        # Crear clave de negocio para identificar duplicados
        df['business_key'] = (
            df['numero'].astype(str) + '|' +
            df['fecha_trafico'].astype(str) + '|' +
            df['celda_decimal'].astype(str)
        )
        
        # Encontrar duplicados
        business_key_counts = df['business_key'].value_counts()
        duplicates = business_key_counts[business_key_counts > 1]
        
        print("RESUMEN DE DUPLICADOS:")
        print("-" * 50)
        print(f"Registros únicos por clave de negocio: {len(business_key_counts)}")
        print(f"Claves de negocio duplicadas: {len(duplicates)}")
        print(f"Total registros afectados por duplicados: {duplicates.sum()}")
        print(f"Registros únicos que se procesarían: {len(business_key_counts)}")
        print(f"Registros que se rechazarían: {duplicates.sum() - len(duplicates)}")
        print()
        
        # Analizar patrones de duplicados
        print("PATRONES DE DUPLICADOS MÁS FRECUENTES:")
        print("-" * 50)
        
        for i, (business_key, count) in enumerate(duplicates.head(10).items(), 1):
            numero, fecha, celda = business_key.split('|')
            
            print(f"{i}. Número: {numero} | Fecha: {fecha} | Celda: {celda}")
            print(f"   Aparece {count} veces")
            
            # Obtener todos los registros con esta clave
            duplicate_rows = df[df['business_key'] == business_key]
            
            # Verificar si hay diferencias en otros campos
            differences = []
            if 'tipo_cdr' in df.columns:
                tipo_values = duplicate_rows['tipo_cdr'].unique()
                if len(tipo_values) > 1:
                    differences.append(f"tipo_cdr: {tipo_values}")
            
            if 'lac_decimal' in df.columns:
                lac_values = duplicate_rows['lac_decimal'].unique()
                if len(lac_values) > 1:
                    differences.append(f"lac_decimal: {lac_values}")
            
            if differences:
                print(f"   Diferencias en otros campos: {', '.join(differences)}")
            else:
                print("   Registros completamente idénticos")
            
            print()
        
        # Análisis temporal
        print("ANÁLISIS TEMPORAL DE DUPLICADOS:")
        print("-" * 50)
        
        # Contar duplicados por fecha
        df['fecha_solo'] = df['fecha_trafico'].astype(str).str[:8]  # YYYYMMDD
        fecha_counts = df.groupby('fecha_solo')['business_key'].nunique()
        
        print("Registros únicos por día:")
        for fecha, count in fecha_counts.items():
            year = fecha[:4]
            month = fecha[4:6]
            day = fecha[6:8]
            print(f"  {day}/{month}/{year}: {count} registros únicos")
        
        print()
        
        # Análisis por número de teléfono
        print("ANÁLISIS POR NÚMERO DE TELÉFONO:")
        print("-" * 50)
        
        numero_duplicates = defaultdict(int)
        for business_key, count in duplicates.items():
            numero = business_key.split('|')[0]
            numero_duplicates[numero] += count - 1  # Solo contar los extras
        
        # Números con más duplicados
        top_duplicate_numbers = sorted(numero_duplicates.items(), key=lambda x: x[1], reverse=True)[:10]
        
        print("Números con más registros duplicados:")
        for numero, extra_count in top_duplicate_numbers:
            total_records = len(df[df['numero'].astype(str) == numero])
            unique_records = len(df[df['numero'].astype(str) == numero]['business_key'].unique())
            print(f"  {numero}: {total_records} registros total, {unique_records} únicos, {extra_count} duplicados")
        
        print()
        
        # Recomendaciones
        print("RECOMENDACIONES:")
        print("-" * 50)
        
        duplicate_percentage = ((duplicates.sum() - len(duplicates)) / len(df)) * 100
        
        if duplicate_percentage > 50:
            print("ALTA presencia de duplicados (>50%)")
            print("- Revisar proceso de generación del archivo fuente")
            print("- Considerar si los duplicados son errores del sistema")
        elif duplicate_percentage > 20:
            print("MODERADA presencia de duplicados (20-50%)")
            print("- Los duplicados podrían ser legítimos (múltiples sesiones simultáneas)")
            print("- Considerar agregar timestamp con mayor precisión al hash")
        else:
            print("BAJA presencia de duplicados (<20%)")
            print("- Los duplicados parecen normales para datos de telecomunicaciones")
        
        print(f"\nPorcentaje de duplicados: {duplicate_percentage:.1f}%")
        print(f"Tasa de procesamiento esperada: {(len(business_key_counts)/len(df))*100:.1f}%")
        
        return {
            'total_records': len(df),
            'unique_business_keys': len(business_key_counts),
            'duplicate_keys': len(duplicates),
            'records_to_reject': duplicates.sum() - len(duplicates),
            'expected_success_rate': (len(business_key_counts)/len(df))*100
        }
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    analyze_duplicate_patterns()