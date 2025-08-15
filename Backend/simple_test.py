#!/usr/bin/env python3
import sys
import os
import pandas as pd

# Agregar el directorio padre al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.file_processor_service import FileProcessorService

def test_claro_processing():
    file_path = r"C:\Soluciones\BGC\claude\KNSOft\datatest\Claro\formato excel\DATOS_POR_CELDA CLARO.xlsx"
    mission_id = "mission_MPFRBNsb"
    
    print("PRUEBA DE PROCESAMIENTO COMPLETO - ARCHIVO CLARO")
    print("=" * 60)
    
    try:
        processor = FileProcessorService()
        
        # Leer archivo
        df = pd.read_excel(file_path)
        print(f"Total registros en archivo: {len(df)}")
        print(f"Columnas: {list(df.columns)}")
        print()
        
        # Leer archivo como bytes
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
        
        # Procesar archivo
        print("INICIANDO PROCESAMIENTO...")
        file_upload_id = "test_upload_" + str(hash(file_path))[-8:]
        result = processor.process_claro_data_por_celda(
            file_bytes=file_bytes,
            file_name="DATOS_POR_CELDA CLARO.xlsx",
            file_upload_id=file_upload_id,
            mission_id=mission_id
        )
        
        print("\nRESULTADO:")
        print(f"Exito: {result.get('success', False)}")
        print(f"Registros procesados: {result.get('records_processed', 0)}")
        print(f"Registros fallidos: {result.get('records_failed', 0)}")
        print(f"Tasa de exito: {result.get('success_rate', 0)}%")
        
        details = result.get('details', {})
        print(f"\nDETALLES:")
        print(f"Originales: {details.get('original_records', 0)}")
        print(f"Limpiados: {details.get('cleaned_records', 0)}")
        print(f"Chunks: {details.get('chunks_processed', 0)}")
        
        # Análisis final
        expected = len(df)
        processed = result.get('records_processed', 0)
        
        if processed == expected:
            print("\nEXITO COMPLETO!")
        else:
            missing = expected - processed
            print(f"\nPROCESAMIENTO INCOMPLETO:")
            print(f"Esperados: {expected}")
            print(f"Procesados: {processed}")
            print(f"Faltantes: {missing}")
            
            if result.get('error'):
                print(f"Error: {result.get('error')}")
        
        return result
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_claro_processing()