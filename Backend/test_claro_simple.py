#!/usr/bin/env python3
"""
KRONOS - Test Simple para CLARO - Llamadas Entrantes
===================================================

Test básico para validar la funcionalidad core sin dependencias complejas de BD.

Uso:
    python test_claro_simple.py
"""

import os
import sys
from pathlib import Path

# Agregar el directorio padre al path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.file_processor_service import FileProcessorService
from services.data_normalizer_service import DataNormalizerService


def test_basic_functionality():
    """Test básico de funcionalidad core."""
    print("=== TEST BASICO CLARO LLAMADAS ENTRANTES ===")
    
    # Inicializar servicios
    processor = FileProcessorService()
    normalizer = DataNormalizerService()
    
    # Archivo de prueba
    csv_file = Path(__file__).parent.parent / 'datatest' / 'Claro' / 'LLAMADAS_ENTRANTES_POR_CELDA CLARO.csv'
    
    if not csv_file.exists():
        print(f"ERROR: Archivo no encontrado: {csv_file}")
        return False
    
    print(f"Procesando: {csv_file.name}")
    
    try:
        # 1. Leer archivo
        with open(csv_file, 'rb') as f:
            file_bytes = f.read()
        
        df = processor._read_csv_robust(file_bytes, delimiter=',')
        print(f"OK: Archivo leido: {len(df)} filas, {len(df.columns)} columnas")
        print(f"   Columnas: {list(df.columns)}")
        
        # 2. Validar estructura
        is_valid, errors = processor._validate_claro_call_columns(df)
        if is_valid:
            print("OK: Estructura de archivo valida")
        else:
            print(f"WARN: Problemas de estructura: {errors}")
        
        # 3. Limpiar datos
        clean_df = processor._clean_claro_call_data(df)
        print(f"OK: Datos limpiados: {len(clean_df)} registros CDR_ENTRANTE validos")
        
        if len(clean_df) == 0:
            print("ERROR: No hay datos validos para procesar")
            return False
        
        # 4. Test de normalización con muestra
        print("\n=== TEST NORMALIZACION ===")
        success_count = 0
        
        for i, (_, row) in enumerate(clean_df.head(3).iterrows()):
            record = row.to_dict()
            print(f"\nRegistro {i+1}:")
            print(f"  Originador: {record['originador']}")
            print(f"  Receptor: {record['receptor']}")
            print(f"  Fecha: {record['fecha_hora']}")
            print(f"  Duración: {record['duracion']}s")
            print(f"  Tipo: {record['tipo']}")
            
            # Validar registro
            is_valid_record, record_errors = processor._validate_claro_call_record(record)
            if is_valid_record:
                print("  OK: Registro valido")
                
                # Normalizar
                normalized = normalizer.normalize_claro_call_data_entrantes(
                    record, f"test-file-{i}", "test-mission"
                )
                
                if normalized:
                    print("  OK: Normalizacion exitosa")
                    print(f"    - Numero origen: {normalized['numero_origen']}")
                    print(f"    - Numero destino: {normalized['numero_destino']}")
                    print(f"    - Numero objetivo: {normalized['numero_objetivo']}")
                    print(f"    - Fecha normalizada: {normalized['fecha_hora_llamada']}")
                    print(f"    - Tipo llamada: {normalized['tipo_llamada']}")
                    success_count += 1
                else:
                    print("  ERROR: Error en normalizacion")
            else:
                print(f"  ERROR: Registro invalido: {record_errors}")
        
        print(f"\n=== RESUMEN ===")
        print(f"Archivo: {csv_file.name}")
        print(f"Filas totales: {len(df)}")
        print(f"Registros CDR_ENTRANTE válidos: {len(clean_df)}")
        print(f"Normalizaciones exitosas: {success_count}/3")
        
        success = success_count > 0
        print(f"Resultado general: {'EXITOSO' if success else 'FALLIDO'}")
        
        return success
        
    except Exception as e:
        print(f"ERROR CRITICO: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)