#!/usr/bin/env python3
"""
Script de diagnóstico para analizar por qué algunos registros del archivo CLARO no se procesan.
"""

import pandas as pd
import json
from datetime import datetime
from typing import Dict, Any, List, Tuple

def validate_claro_cellular_record(record: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Misma función de validación que usa el sistema para identificar registros problemáticos.
    """
    errors = []
    
    # Validar número telefónico
    numero = str(record.get('numero', '')).strip()
    if not numero:
        errors.append("Número telefónico vacío")
    elif len(numero) < 10:
        errors.append(f"Número telefónico muy corto: {numero}")
    elif len(numero) > 12:
        errors.append(f"Número telefónico muy largo: {numero}")
    elif not numero.isdigit():
        errors.append(f"Número telefónico contiene caracteres no numéricos: {numero}")
    
    # Validar fecha
    fecha = str(record.get('fecha_trafico', '')).strip()
    if not fecha:
        errors.append("Fecha de tráfico vacía")
    elif len(fecha) != 14:
        errors.append(f"Formato de fecha incorrecto (esperado YYYYMMDDHHMMSS): {fecha}")
    elif not fecha.isdigit():
        errors.append(f"Fecha contiene caracteres no numéricos: {fecha}")
    else:
        # Validar componentes de fecha
        try:
            year = int(fecha[:4])
            month = int(fecha[4:6])
            day = int(fecha[6:8])
            hour = int(fecha[8:10])
            minute = int(fecha[10:12])
            second = int(fecha[12:14])
            
            if not (2020 <= year <= 2030):
                errors.append(f"Año fuera de rango válido: {year}")
            if not (1 <= month <= 12):
                errors.append(f"Mes inválido: {month}")
            if not (1 <= day <= 31):
                errors.append(f"Día inválido: {day}")
            if not (0 <= hour <= 23):
                errors.append(f"Hora inválida: {hour}")
            if not (0 <= minute <= 59):
                errors.append(f"Minuto inválido: {minute}")
            if not (0 <= second <= 59):
                errors.append(f"Segundo inválido: {second}")
                
        except ValueError:
            errors.append(f"Error parseando fecha: {fecha}")
    
    # Validar tipo CDR
    tipo_cdr = str(record.get('tipo_cdr', '')).strip().upper()
    if not tipo_cdr:
        errors.append("Tipo CDR vacío")
    elif tipo_cdr not in ['DATOS', 'DATA', 'SMS', 'MMS', 'VOZ', 'VOICE']:
        errors.append(f"Tipo CDR no reconocido: {tipo_cdr}")
    
    # Validar celda
    celda = str(record.get('celda_decimal', '')).strip()
    if not celda:
        errors.append("Celda decimal vacía")
    elif not celda.isdigit():
        errors.append(f"Celda decimal no numérica: {celda}")
    
    # Validar LAC (puede estar vacío en algunos casos)
    lac = str(record.get('lac_decimal', '')).strip()
    if lac and not lac.isdigit():
        errors.append(f"LAC decimal no numérico: {lac}")
    
    return len(errors) == 0, errors

def analyze_claro_file():
    """
    Analiza el archivo CLARO para diagnosticar problemas de procesamiento.
    """
    file_path = r"C:\Soluciones\BGC\claude\KNSOft\datatest\Claro\formato excel\DATOS_POR_CELDA CLARO.xlsx"
    
    print("=" * 80)
    print("DIAGNÓSTICO DEL ARCHIVO CLARO")
    print("=" * 80)
    
    try:
        # Leer archivo Excel
        print(f"Leyendo archivo: {file_path}")
        df = pd.read_excel(file_path)
        
        print(f"Total de registros en el archivo: {len(df)}")
        print(f"Columnas disponibles: {list(df.columns)}")
        print()
        
        # Estadísticas generales
        print("ANÁLISIS DE COLUMNAS:")
        print("-" * 40)
        for col in df.columns:
            null_count = df[col].isnull().sum()
            unique_count = df[col].nunique()
            print(f"{col}: {null_count} nulos, {unique_count} valores únicos")
        print()
        
        # Validar cada registro
        valid_records = 0
        invalid_records = 0
        error_summary = {}
        sample_errors = []
        
        print("VALIDANDO REGISTROS...")
        print("-" * 40)
        
        for index, row in df.iterrows():
            record = row.to_dict()
            is_valid, errors = validate_claro_cellular_record(record)
            
            if is_valid:
                valid_records += 1
            else:
                invalid_records += 1
                
                # Contar tipos de errores
                for error in errors:
                    error_type = error.split(':')[0]  # Obtener tipo base del error
                    error_summary[error_type] = error_summary.get(error_type, 0) + 1
                
                # Guardar ejemplos de errores (primeros 10)
                if len(sample_errors) < 10:
                    sample_errors.append({
                        'row': index + 1,
                        'errors': errors,
                        'sample_data': {
                            'numero': record.get('numero', 'N/A'),
                            'fecha_trafico': record.get('fecha_trafico', 'N/A'),
                            'tipo_cdr': record.get('tipo_cdr', 'N/A'),
                            'celda_decimal': record.get('celda_decimal', 'N/A')
                        }
                    })
        
        # Resultados del análisis
        print(f"Registros válidos: {valid_records}")
        print(f"Registros inválidos: {invalid_records}")
        print(f"Porcentaje de éxito: {(valid_records / len(df)) * 100:.1f}%")
        print()
        
        # Resumen de errores
        print("RESUMEN DE ERRORES:")
        print("-" * 40)
        for error_type, count in sorted(error_summary.items(), key=lambda x: x[1], reverse=True):
            print(f"{error_type}: {count} registros")
        print()
        
        # Ejemplos de errores
        print("EJEMPLOS DE REGISTROS CON ERRORES:")
        print("-" * 40)
        for i, error_example in enumerate(sample_errors[:5], 1):
            print(f"\nEjemplo {i} (Fila {error_example['row']}):")
            print(f"  Datos: {error_example['sample_data']}")
            print(f"  Errores: {error_example['errors']}")
        
        # Análisis de tipos CDR únicos
        print("\nTIPOS CDR ÚNICOS EN EL ARCHIVO:")
        print("-" * 40)
        tipo_cdr_values = df['tipo_cdr'].value_counts() if 'tipo_cdr' in df.columns else {}
        for tipo, count in tipo_cdr_values.items():
            print(f"'{tipo}': {count} registros")
        
        # Guardar reporte detallado
        report = {
            'timestamp': datetime.now().isoformat(),
            'file_path': file_path,
            'total_records': len(df),
            'valid_records': valid_records,
            'invalid_records': invalid_records,
            'success_rate': (valid_records / len(df)) * 100,
            'error_summary': error_summary,
            'sample_errors': sample_errors,
            'tipo_cdr_values': tipo_cdr_values.to_dict() if hasattr(tipo_cdr_values, 'to_dict') else {},
            'columns': list(df.columns)
        }
        
        report_file = f"claro_diagnosis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\nReporte detallado guardado en: {report_file}")
        
        return report
        
    except Exception as e:
        print(f"Error analizando archivo: {e}")
        return None

if __name__ == "__main__":
    analyze_claro_file()