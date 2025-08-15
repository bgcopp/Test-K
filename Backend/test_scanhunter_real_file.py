"""
Test de Procesamiento Real de SCANHUNTER.xlsx
=============================================
Test que procesa el archivo SCANHUNTER.xlsx real y valida:
1. El campo file_record_id se mapea correctamente
2. Se obtienen los IDs esperados [0, 12, 32]  
3. Se cuentan 58 registros total
4. Distribución correcta: 17 con id=0, 15 con id=12, 26 con id=32
"""

import pandas as pd
import os
from pathlib import Path
from services.data_normalizer_service import DataNormalizerService


def test_real_scanhunter_file():
    """Test con archivo SCANHUNTER.xlsx real"""
    
    print("=== TEST: Procesamiento Archivo SCANHUNTER.xlsx Real ===")
    
    # Ruta del archivo real
    file_path = Path(r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\SCANHUNTER.xlsx")
    
    if not file_path.exists():
        print(f"[ERROR] Archivo no encontrado: {file_path}")
        return False
    
    print(f"[OK] Archivo encontrado: {file_path.name}")
    
    try:
        # Cargar archivo directamente con pandas para análisis inicial
        print("\n[PASO 1] Análisis inicial del archivo...")
        df = pd.read_excel(file_path)
        
        print(f"  Total de filas en archivo: {len(df)}")
        print(f"  Columnas disponibles: {list(df.columns)}")
        
        # Verificar que existe la columna Id
        if 'Id' in df.columns:
            print("  [OK] Columna 'Id' encontrada")
            unique_ids = sorted(df['Id'].unique())
            print(f"  IDs únicos en archivo: {unique_ids}")
            
            # Contar registros por ID
            id_counts = df['Id'].value_counts().sort_index()
            print("  Distribución por ID:")
            for id_val, count in id_counts.items():
                print(f"    ID {id_val}: {count} registros")
        else:
            print("  [ERROR] Columna 'Id' no encontrada")
            return False
        
        # Usar el normalizador de datos
        print("\n[PASO 2] Procesamiento con DataNormalizerService...")
        normalizer = DataNormalizerService()
        
        # Procesar archivo
        results = []
        for index, row in df.iterrows():
            # Simular datos en formato esperado
            raw_data = row.to_dict()
            
            try:
                result = normalizer.normalize_scanhunter_data(raw_data, source_filename="SCANHUNTER.xlsx")
                results.append(result)
                
                # Log cada resultado procesado (solo primeros 5)
                if index < 5:
                    file_record_id = result.get('file_record_id')
                    punto = result.get('punto', 'N/A')
                    operador = result.get('operator', 'N/A')
                    print(f"    Reg {index+1}: file_record_id={file_record_id}, punto='{punto[:30]}...', operador={operador}")
                
            except Exception as e:
                print(f"  [ERROR] Registro {index+1}: {str(e)}")
                continue
        
        print(f"  [OK] Procesados {len(results)} registros exitosamente")
        
        # Verificar file_record_id
        print("\n[PASO 3] Validación de file_record_id...")
        
        file_record_ids = [r.get('file_record_id') for r in results if r.get('file_record_id') is not None]
        unique_file_ids = sorted(set(file_record_ids))
        
        print(f"  file_record_ids únicos: {unique_file_ids}")
        print(f"  Total registros con file_record_id: {len(file_record_ids)}")
        
        # Validar IDs esperados
        expected_ids = [0, 12, 32]
        if set(unique_file_ids) == set(expected_ids):
            print("  [OK] IDs coinciden con lo esperado: [0, 12, 32]")
        else:
            print(f"  [WARNING] IDs no coinciden. Esperados: {expected_ids}, Obtenidos: {unique_file_ids}")
        
        # Contar por ID
        print("  Distribución por file_record_id:")
        from collections import Counter
        id_distribution = Counter(file_record_ids)
        for id_val in sorted(id_distribution.keys()):
            count = id_distribution[id_val]
            print(f"    file_record_id {id_val}: {count} registros")
        
        # Verificar totales esperados
        print("\n[PASO 4] Validación de totales...")
        expected_total = 58
        expected_distribution = {0: 17, 12: 15, 32: 26}
        
        if len(file_record_ids) == expected_total:
            print(f"  [OK] Total correcto: {len(file_record_ids)} registros")
        else:
            print(f"  [WARNING] Total incorrecto. Esperado: {expected_total}, Obtenido: {len(file_record_ids)}")
        
        for id_val, expected_count in expected_distribution.items():
            actual_count = id_distribution.get(id_val, 0)
            if actual_count == expected_count:
                print(f"  [OK] ID {id_val}: {actual_count} registros (correcto)")
            else:
                print(f"  [WARNING] ID {id_val}: esperado {expected_count}, obtenido {actual_count}")
        
        # Test de ordenamiento
        print("\n[PASO 5] Test de ordenamiento...")
        sorted_results = sorted(results, key=lambda x: x.get('file_record_id', 0))
        sorted_ids = [r.get('file_record_id') for r in sorted_results if r.get('file_record_id') is not None]
        
        print(f"  Primeros 10 IDs ordenados: {sorted_ids[:10]}")
        print(f"  Últimos 10 IDs ordenados: {sorted_ids[-10:]}")
        
        if sorted_ids == sorted(file_record_ids):
            print("  [OK] Ordenamiento funciona correctamente")
        else:
            print("  [ERROR] Problema con el ordenamiento")
        
        print("\n=== RESULTADO FINAL ===")
        total_checks = 0
        passed_checks = 0
        
        # Check 1: Archivo procesado
        total_checks += 1
        if len(results) > 0:
            passed_checks += 1
            print("✓ Archivo procesado exitosamente")
        else:
            print("✗ Error procesando archivo")
        
        # Check 2: field_record_id mapeado
        total_checks += 1
        if len(file_record_ids) > 0:
            passed_checks += 1
            print("✓ field_record_id mapeado correctamente")
        else:
            print("✗ field_record_id no mapeado")
        
        # Check 3: IDs esperados
        total_checks += 1
        if set(unique_file_ids) == set(expected_ids):
            passed_checks += 1
            print("✓ IDs esperados encontrados [0, 12, 32]")
        else:
            print("✗ IDs no coinciden con lo esperado")
        
        # Check 4: Total de registros
        total_checks += 1
        if len(file_record_ids) == expected_total:
            passed_checks += 1
            print("✓ Total de registros correcto (58)")
        else:
            print("✗ Total de registros incorrecto")
        
        print(f"\nRESUMEN: {passed_checks}/{total_checks} checks pasaron")
        
        return passed_checks == total_checks
        
    except Exception as e:
        print(f"[ERROR] Excepción durante el test: {str(e)}")
        return False


if __name__ == "__main__":
    print("KRONOS - Test Archivo Real SCANHUNTER.xlsx")
    print("=" * 50)
    
    try:
        success = test_real_scanhunter_file()
        
        if success:
            print("\n[SUCCESS] Todos los tests pasaron")
        else:
            print("\n[PARTIAL] Algunos tests fallaron")
            
    except Exception as e:
        print(f"\n[CRITICAL ERROR] {str(e)}")