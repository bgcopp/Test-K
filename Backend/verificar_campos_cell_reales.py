#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERIFICACIÓN CRÍTICA: CAMPOS CELL REALES EN operator_call_data
Determinar qué campo contiene realmente los cell_ids para correlacionar con cellular_data
Author: Claude Code Assistant para Boris
Date: 2025-08-20
"""

import sqlite3

def verificar_campos_cell_reales():
    """
    Verifica todos los campos de operator_call_data para encontrar donde están los cell_ids reales
    """
    print("=" * 80)
    print("VERIFICACIÓN CRÍTICA: CAMPOS CELL REALES")
    print("=" * 80)
    
    conn = sqlite3.connect('kronos.db')
    cursor = conn.cursor()
    
    try:
        # 1. Verificar TODOS los campos con valores no nulos
        print("1. ANÁLISIS DE CAMPOS CON DATOS:")
        print("-" * 50)
        
        cursor.execute("PRAGMA table_info(operator_call_data)")
        all_columns = cursor.fetchall()
        
        for col in all_columns:
            col_name = col[1]
            col_type = col[2]
            
            # Contar valores no nulos
            cursor.execute(f"SELECT COUNT(*) FROM operator_call_data WHERE {col_name} IS NOT NULL AND {col_name} != ''")
            non_null_count = cursor.fetchone()[0]
            
            # Si hay datos, mostrar muestras
            if non_null_count > 0:
                cursor.execute(f"SELECT DISTINCT {col_name} FROM operator_call_data WHERE {col_name} IS NOT NULL AND {col_name} != '' LIMIT 5")
                samples = cursor.fetchall()
                sample_values = [str(row[0]) for row in samples]
                
                print(f"{col_name} ({col_type}): {non_null_count} registros")
                print(f"  Muestras: {sample_values}")
                print()
        
        # 2. Buscar ESPECÍFICAMENTE campos que pueden contener cell_ids
        print("2. BÚSQUEDA ESPECÍFICA DE CELL_IDS:")
        print("-" * 50)
        
        # Verificar campos que podrían contener cell_ids numéricos
        potential_fields = []
        for col in all_columns:
            col_name = col[1].lower()
            if any(term in col_name for term in ['cell', 'celda', 'id']):
                potential_fields.append(col[1])
        
        print(f"Campos potenciales para cell_ids: {potential_fields}")
        
        for field in potential_fields:
            cursor.execute(f"SELECT DISTINCT {field} FROM operator_call_data WHERE {field} IS NOT NULL LIMIT 10")
            values = cursor.fetchall()
            if values:
                print(f"\n{field}:")
                for val in values:
                    print(f"  {val[0]}")
        
        # 3. Comparar con cellular_data cell_ids
        print("\n3. COMPARACIÓN CON CELLULAR_DATA:")
        print("-" * 50)
        
        cursor.execute("SELECT DISTINCT cell_id FROM cellular_data LIMIT 10")
        cellular_cells = cursor.fetchall()
        print("Cell_ids en cellular_data:")
        for cell in cellular_cells:
            print(f"  {cell[0]}")
        
        # 4. BÚSQUEDA INTELIGENTE DE CORRELACIÓN
        print("\n4. BÚSQUEDA AUTOMÁTICA DE CORRELACIÓN:")
        print("-" * 50)
        
        # Obtener algunos cell_ids de cellular_data
        cursor.execute("SELECT DISTINCT cell_id FROM cellular_data LIMIT 5")
        test_cell_ids = [row[0] for row in cursor.fetchall()]
        
        # Buscar en TODOS los campos de operator_call_data
        for col in all_columns:
            col_name = col[1]
            matches = 0
            
            for test_cell in test_cell_ids:
                cursor.execute(f"SELECT COUNT(*) FROM operator_call_data WHERE {col_name} = ?", (test_cell,))
                count = cursor.fetchone()[0]
                matches += count
            
            if matches > 0:
                print(f"✓ CORRELACIÓN ENCONTRADA en {col_name}: {matches} coincidencias")
                
                # Mostrar ejemplos de correlación
                for test_cell in test_cell_ids[:3]:
                    cursor.execute(f"SELECT numero_origen, numero_destino, {col_name} FROM operator_call_data WHERE {col_name} = ? LIMIT 2", (test_cell,))
                    examples = cursor.fetchall()
                    for ex in examples:
                        print(f"    Cell {test_cell}: {ex[0]} -> {ex[1]} (campo: {ex[2]})")
        
        # 5. DIAGNÓSTICO FINAL
        print("\n5. DIAGNÓSTICO FINAL:")
        print("-" * 50)
        print("✓ Análisis completado")
        print("Si no se encontraron correlaciones, el problema está en:")
        print("1. Los datos de cell_id no están cargados en operator_call_data")
        print("2. Los cell_ids están en un formato diferente")
        print("3. Hay un problema en el proceso de carga de datos")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    verificar_campos_cell_reales()