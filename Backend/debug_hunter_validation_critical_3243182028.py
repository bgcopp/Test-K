#!/usr/bin/env python3
"""
VALIDACIÓN CRÍTICA HUNTER - Número 3243182028
===============================================================================
PROBLEMA IDENTIFICADO:
El número 3243182028 muestra ocurrencias en celdas [16478, 22504, 6159, 6578]
PERO estas celdas pueden NO estar definidas en SCANHUNTER.xlsx (archivo HUNTER real)

ANÁLISIS REQUERIDO:
1. Extraer TODAS las celdas definidas en SCANHUNTER.xlsx
2. Comparar con las celdas encontradas para 3243182028
3. Identificar cuáles son válidas y cuáles son falsas
4. Calcular el conteo CORRECTO para correlación

Autor: Boris's Data Engineering Algorithm Expert - Claude Code
Fecha: 2025-08-18
===============================================================================
"""

import pandas as pd
from pathlib import Path
import json
from datetime import datetime
from typing import Set, Dict, Any, List
import logging

# Configurar logging detallado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def extract_hunter_cells_from_scanhunter() -> Set[str]:
    """
    Extrae TODAS las celdas definidas en el archivo HUNTER real (SCANHUNTER.xlsx)
    
    Returns:
        Set de celdas HUNTER válidas
    """
    hunter_file = Path(r"C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\SCANHUNTER.xlsx")
    
    logger.info(f"=== EXTRAYENDO CELDAS HUNTER REALES ===")
    logger.info(f"Archivo: {hunter_file}")
    
    if not hunter_file.exists():
        logger.error(f"ARCHIVO HUNTER NO ENCONTRADO: {hunter_file}")
        return set()
    
    try:
        # Leer TODAS las hojas del archivo HUNTER
        excel_data = pd.read_excel(hunter_file, sheet_name=None, dtype=str)
        logger.info(f"Hojas encontradas en SCANHUNTER.xlsx: {list(excel_data.keys())}")
        
        hunter_cells = set()
        
        for sheet_name, df in excel_data.items():
            logger.info(f"Procesando hoja: {sheet_name} - {len(df)} filas")
            logger.info(f"Columnas disponibles: {list(df.columns)}")
            
            # Buscar columnas que contengan información de celdas
            possible_cell_columns = []
            for col in df.columns:
                col_str = str(col).lower()
                if any(keyword in col_str for keyword in ['cell', 'celda', 'sector', 'id', 'bts', 'site']):
                    possible_cell_columns.append(col)
            
            logger.info(f"Columnas potenciales de celdas en {sheet_name}: {possible_cell_columns}")
            
            # Extraer valores únicos de columnas de celda
            for col in possible_cell_columns:
                try:
                    unique_values = df[col].dropna().astype(str).unique()
                    for value in unique_values:
                        value_clean = str(value).strip()
                        if value_clean and value_clean != 'nan' and value_clean.isdigit():
                            hunter_cells.add(value_clean)
                            logger.debug(f"Celda encontrada en {col}: {value_clean}")
                except Exception as e:
                    logger.warning(f"Error procesando columna {col}: {e}")
            
            # También buscar en TODAS las columnas valores que parezcan IDs de celda
            for col in df.columns:
                try:
                    # Solo considerar columnas numéricas o que contengan números
                    unique_values = df[col].dropna().astype(str).unique()
                    cell_count_before = len(hunter_cells)
                    
                    for value in unique_values:
                        value_clean = str(value).strip()
                        # Si es un número de 4-6 dígitos, podría ser una celda
                        if value_clean.isdigit() and 1000 <= int(value_clean) <= 999999:
                            hunter_cells.add(value_clean)
                    
                    cell_count_after = len(hunter_cells)
                    if cell_count_after > cell_count_before:
                        logger.info(f"Columna {col} aportó {cell_count_after - cell_count_before} celdas adicionales")
                        
                except Exception as e:
                    continue
        
        logger.info(f"TOTAL CELDAS HUNTER EXTRAÍDAS: {len(hunter_cells)}")
        
        # Mostrar muestra de celdas encontradas
        if hunter_cells:
            hunter_sorted = sorted(list(hunter_cells), key=int)
            logger.info(f"Primeras 30 celdas HUNTER: {hunter_sorted[:30]}")
            logger.info(f"Últimas 20 celdas HUNTER: {hunter_sorted[-20:]}")
        
        return hunter_cells
        
    except Exception as e:
        logger.error(f"ERROR CRÍTICO extrayendo celdas HUNTER: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return set()

def validate_3243182028_cells(hunter_cells: Set[str]) -> Dict[str, Any]:
    """
    Valida las celdas específicas del número 3243182028 contra HUNTER real
    
    Args:
        hunter_cells: Set de celdas HUNTER válidas
        
    Returns:
        Dict con análisis detallado
    """
    # Celdas encontradas para 3243182028 según análisis previo
    celdas_encontradas = ['16478', '22504', '6159', '6578']
    
    logger.info(f"=== VALIDANDO CELDAS DEL NÚMERO 3243182028 ===")
    logger.info(f"Celdas encontradas en archivos CLARO: {celdas_encontradas}")
    logger.info(f"Total celdas HUNTER disponibles: {len(hunter_cells)}")
    
    # Validación celda por celda
    celdas_validas = []
    celdas_invalidas = []
    
    for celda in celdas_encontradas:
        if celda in hunter_cells:
            celdas_validas.append(celda)
            logger.info(f"✓ CELDA {celda}: VÁLIDA (existe en HUNTER)")
        else:
            celdas_invalidas.append(celda)
            logger.warning(f"✗ CELDA {celda}: INVÁLIDA (NO existe en HUNTER)")
    
    # Conteo correcto vs incorrecto
    conteo_actual = len(celdas_encontradas)  # Lo que muestra el algoritmo actual
    conteo_correcto = len(celdas_validas)    # Lo que debería mostrar
    inflacion = conteo_actual - conteo_correcto
    
    logger.info(f"RESULTADO CRÍTICO:")
    logger.info(f"  - Conteo actual (INCORRECTO): {conteo_actual}")
    logger.info(f"  - Conteo correcto (solo HUNTER): {conteo_correcto}")
    logger.info(f"  - Inflación detectada: {inflacion} celdas falsas")
    
    return {
        'numero': '3243182028',
        'celdas_encontradas': celdas_encontradas,
        'celdas_validas_hunter': celdas_validas,
        'celdas_invalidas': celdas_invalidas,
        'conteo_actual_incorrecto': conteo_actual,
        'conteo_correcto': conteo_correcto,
        'inflacion_detectada': inflacion,
        'impacto_porcentual': (inflacion / conteo_actual * 100) if conteo_actual > 0 else 0,
        'detalle_validacion': [
            {'celda': celda, 'valida': celda in hunter_cells} 
            for celda in celdas_encontradas
        ]
    }

def generate_algorithm_correction_proposal(validation_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Genera propuesta de corrección para el algoritmo de correlación
    
    Args:
        validation_result: Resultado de validación
        
    Returns:
        Dict con propuesta de corrección
    """
    return {
        'problema_identificado': {
            'descripcion': 'Algoritmo cuenta celdas que NO están definidas en HUNTER real',
            'impacto': f"Inflación de {validation_result['inflacion_detectada']} celdas falsas ({validation_result['impacto_porcentual']:.1f}%)",
            'ejemplo': f"Número {validation_result['numero']}: {validation_result['conteo_actual_incorrecto']} → {validation_result['conteo_correcto']} ocurrencias"
        },
        'solucion_requerida': {
            'paso_1': 'Cargar celdas HUNTER reales de SCANHUNTER.xlsx al inicio',
            'paso_2': 'Filtrar query de correlación: AND celda IN (hunter_cells_valid)',
            'paso_3': 'Validar cada celda antes de contar ocurrencias',
            'paso_4': 'Excluir automáticamente celdas no-HUNTER'
        },
        'implementacion_algoritmica': {
            'pre_filtro': 'hunter_cells = extract_real_hunter_cells()',
            'query_modification': 'WHERE celda IN (SELECT cell_id FROM hunter_cells)',
            'validation_logic': 'if celda not in hunter_cells: skip_counting',
            'performance_impact': 'Mínimo - una vez por sesión'
        },
        'beneficios_esperados': {
            'precision_mejorada': 'Eliminación completa de celdas falsas',
            'conteos_exactos': 'Solo celdas definidas en HUNTER',
            'correlaciones_confiables': 'Resultados basados en datos reales',
            'algoritmo_robusto': 'Validación automática contra HUNTER'
        }
    }

def main():
    """Ejecutar validación crítica completa"""
    logger.info("=== INICIANDO VALIDACIÓN CRÍTICA HUNTER-CORRELACIÓN ===")
    
    # Paso 1: Extraer celdas HUNTER reales
    hunter_cells = extract_hunter_cells_from_scanhunter()
    
    if not hunter_cells:
        logger.error("FALLO CRÍTICO: No se pudieron extraer celdas HUNTER")
        return {
            'success': False,
            'error': 'No se pudieron extraer celdas HUNTER del archivo real'
        }
    
    # Paso 2: Validar número específico 3243182028
    validation_result = validate_3243182028_cells(hunter_cells)
    
    # Paso 3: Generar propuesta de corrección
    correction_proposal = generate_algorithm_correction_proposal(validation_result)
    
    # Paso 4: Compilar reporte final
    final_report = {
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'hunter_analysis': {
            'total_cells_extracted': len(hunter_cells),
            'sample_cells': sorted(list(hunter_cells), key=int)[:50]
        },
        'numero_3243182028_validation': validation_result,
        'algorithm_correction_proposal': correction_proposal,
        'critical_findings': {
            'hunter_cells_count': len(hunter_cells),
            'validation_passed': len(validation_result['celdas_validas_hunter']) > 0,
            'false_cells_detected': len(validation_result['celdas_invalidas']) > 0,
            'inflation_percentage': validation_result['impacto_porcentual']
        }
    }
    
    # Guardar reporte
    output_file = f"hunter_validation_critical_3243182028_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)
    
    # Mostrar resultados en consola
    print("\n" + "="*80)
    print("VALIDACIÓN CRÍTICA HUNTER - RESULTADOS FINALES")
    print("="*80)
    print(f"\n📊 CELDAS HUNTER EXTRAÍDAS: {len(hunter_cells)}")
    print(f"\n🎯 VALIDACIÓN NÚMERO 3243182028:")
    print(f"   - Celdas encontradas: {len(validation_result['celdas_encontradas'])}")
    print(f"   - Celdas VÁLIDAS (en HUNTER): {len(validation_result['celdas_validas_hunter'])}")
    print(f"   - Celdas INVÁLIDAS: {len(validation_result['celdas_invalidas'])}")
    print(f"   - INFLACIÓN DETECTADA: {validation_result['inflacion_detectada']} celdas ({validation_result['impacto_porcentual']:.1f}%)")
    
    if validation_result['celdas_invalidas']:
        print(f"   - Celdas inválidas: {validation_result['celdas_invalidas']}")
    
    print(f"\n📈 CORRECCIÓN REQUERIDA:")
    print(f"   - Conteo actual: {validation_result['conteo_actual_incorrecto']} ❌")
    print(f"   - Conteo correcto: {validation_result['conteo_correcto']} ✅")
    
    print(f"\n💾 Reporte guardado en: {output_file}")
    
    logger.info("=== VALIDACIÓN CRÍTICA COMPLETADA ===")
    return final_report

if __name__ == "__main__":
    main()