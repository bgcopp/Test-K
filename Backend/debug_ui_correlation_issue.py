"""
DIAGNÓSTICO L2: Análisis forense del problema de números objetivo no visibles en UI
================================================================================
Problema: Los números objetivo aparecen en tests backend pero NO en la UI de KRONOS
Misión: mission_MPFRBNsb
Período UI: 20/05/2021 10:00 AM - 20/05/2021 02:20 PM
================================================================================
"""

import sqlite3
import json
from datetime import datetime
import sys
import os

# Agregar directorio de servicios al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from services.correlation_analysis_service import CorrelationAnalysisService

def debug_ui_correlation_issue():
    """Análisis forense completo del problema UI"""
    
    print("=" * 80)
    print("DIAGNÓSTICO L2: ANÁLISIS FORENSE DEL PROBLEMA UI")
    print("=" * 80)
    
    # Configuración idéntica a la UI
    mission_id = 'mission_MPFRBNsb'
    
    # Fechas EXACTAS como las muestra la UI
    ui_start_date = '2021-05-20T10:00'  # Como viene del frontend
    ui_end_date = '2021-05-20T14:20'    # 02:20 PM = 14:20 en 24h
    
    # Convertir a formato backend (como hace main.py)
    def normalize_datetime(date_str):
        """Convierte YYYY-MM-DDTHH:mm a YYYY-MM-DD HH:mm:ss"""
        if 'T' in date_str:
            return date_str.replace('T', ' ') + ':00'
        else:
            return date_str + ' 00:00:00'
    
    normalized_start = normalize_datetime(ui_start_date)
    normalized_end = normalize_datetime(ui_end_date)
    min_coincidences = 2  # Como en la UI
    
    print(f"\n[CONFIG] CONFIGURACION UI:")
    print(f"  - Mision: {mission_id}")
    print(f"  - Fecha inicio UI: {ui_start_date} (10:00 AM)")
    print(f"  - Fecha fin UI: {ui_end_date} (02:20 PM)")
    print(f"  - Min coincidencias: {min_coincidences}")
    print(f"\n[CONVERSION] CONVERSION BACKEND:")
    print(f"  - Fecha inicio normalizada: {normalized_start}")
    print(f"  - Fecha fin normalizada: {normalized_end}")
    
    # Números objetivo esperados
    target_numbers = ['3224274851', '3208611034', '3104277553', '3102715509', '3143534707', '3214161903']
    
    print(f"\n[TARGET] NUMEROS OBJETIVO ESPERADOS:")
    for num in target_numbers:
        print(f"  - {num}")
    
    # Conectar a BD
    db_path = os.path.join(os.path.dirname(__file__), 'kronos.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    try:
        # PASO 1: Verificar datos HUNTER en el período
        print(f"\n" + "=" * 80)
        print("PASO 1: VERIFICAR DATOS HUNTER EN EL PERÍODO")
        print("=" * 80)
        
        hunter_query = """
            SELECT COUNT(*) as total, 
                   COUNT(DISTINCT cell_id) as unique_cells,
                   MIN(created_at) as first_record,
                   MAX(created_at) as last_record
            FROM cellular_data
            WHERE mission_id = ?
            AND created_at BETWEEN ? AND ?
        """
        
        cursor = conn.execute(hunter_query, (mission_id, normalized_start, normalized_end))
        hunter_stats = cursor.fetchone()
        
        print(f"[HUNTER] Datos HUNTER:")
        print(f"  - Total registros: {hunter_stats['total']}")
        print(f"  - Cell IDs únicos: {hunter_stats['unique_cells']}")
        print(f"  - Primer registro: {hunter_stats['first_record']}")
        print(f"  - Último registro: {hunter_stats['last_record']}")
        
        # Obtener Cell IDs específicos
        cell_query = """
            SELECT DISTINCT cell_id
            FROM cellular_data
            WHERE mission_id = ?
            AND created_at BETWEEN ? AND ?
            AND cell_id IN ('51438', '53591', '56124', '63095', '51203', '2523')
            ORDER BY cell_id
        """
        
        cursor = conn.execute(cell_query, (mission_id, normalized_start, normalized_end))
        relevant_cells = [row[0] for row in cursor.fetchall()]
        
        print(f"\n[HUNTER] Cell IDs relevantes en HUNTER:")
        for cell in relevant_cells:
            print(f"  - {cell}")
        
        # PASO 2: Verificar datos de operadores en el período
        print(f"\n" + "=" * 80)
        print("PASO 2: VERIFICAR DATOS DE OPERADORES EN EL PERÍODO")
        print("=" * 80)
        
        # Verificar operator_call_data
        call_query = """
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT numero_origen) as unique_origen,
                   COUNT(DISTINCT numero_destino) as unique_destino,
                   COUNT(DISTINCT numero_objetivo) as unique_objetivo,
                   MIN(fecha_hora_llamada) as first_call,
                   MAX(fecha_hora_llamada) as last_call
            FROM operator_call_data
            WHERE mission_id = ?
            AND fecha_hora_llamada BETWEEN ? AND ?
        """
        
        cursor = conn.execute(call_query, (mission_id, normalized_start, normalized_end))
        call_stats = cursor.fetchone()
        
        print(f"[OPERATOR] Datos operator_call_data:")
        print(f"  - Total registros: {call_stats['total']}")
        print(f"  - Números origen únicos: {call_stats['unique_origen']}")
        print(f"  - Números destino únicos: {call_stats['unique_destino']}")
        print(f"  - Números objetivo únicos: {call_stats['unique_objetivo']}")
        print(f"  - Primera llamada: {call_stats['first_call']}")
        print(f"  - Última llamada: {call_stats['last_call']}")
        
        # Buscar números objetivo específicos
        print(f"\n[SEARCH] BUSQUEDA DE NUMEROS OBJETIVO EN OPERADORES:")
        
        for target in target_numbers:
            # Buscar en todos los campos posibles
            search_query = """
                SELECT 
                    'origen' as campo,
                    numero_origen as numero,
                    celda_origen as celda,
                    fecha_hora_llamada
                FROM operator_call_data
                WHERE mission_id = ?
                AND fecha_hora_llamada BETWEEN ? AND ?
                AND (numero_origen LIKE ? OR numero_origen LIKE ?)
                
                UNION ALL
                
                SELECT 
                    'destino' as campo,
                    numero_destino as numero,
                    celda_destino as celda,
                    fecha_hora_llamada
                FROM operator_call_data
                WHERE mission_id = ?
                AND fecha_hora_llamada BETWEEN ? AND ?
                AND (numero_destino LIKE ? OR numero_destino LIKE ?)
                
                UNION ALL
                
                SELECT 
                    'objetivo' as campo,
                    numero_objetivo as numero,
                    celda_objetivo as celda,
                    fecha_hora_llamada
                FROM operator_call_data
                WHERE mission_id = ?
                AND fecha_hora_llamada BETWEEN ? AND ?
                AND (numero_objetivo LIKE ? OR numero_objetivo LIKE ?)
            """
            
            # Buscar con y sin prefijo 57
            patterns = [f'%{target}%', f'%57{target}%']
            
            cursor = conn.execute(search_query, 
                (mission_id, normalized_start, normalized_end, patterns[0], patterns[1],
                 mission_id, normalized_start, normalized_end, patterns[0], patterns[1],
                 mission_id, normalized_start, normalized_end, patterns[0], patterns[1]))
            
            results = cursor.fetchall()
            
            if results:
                print(f"\n[OK] {target} ENCONTRADO ({len(results)} apariciones):")
                cells_found = set()
                for row in results[:5]:  # Mostrar primeras 5
                    cells_found.add(row[2])
                    print(f"    - Campo: {row[0]}, Celda: {row[2]}, Fecha: {row[3]}")
                if len(results) > 5:
                    print(f"    ... y {len(results)-5} más")
                print(f"    Celdas únicas: {sorted(cells_found)}")
            else:
                print(f"\n[FAIL] {target} NO ENCONTRADO en el periodo")
        
        # PASO 3: Ejecutar el servicio de correlación
        print(f"\n" + "=" * 80)
        print("PASO 3: EJECUTAR SERVICIO DE CORRELACIÓN")
        print("=" * 80)
        
        service = CorrelationAnalysisService()
        result = service.analyze_correlation(
            mission_id=mission_id,
            start_date=normalized_start,
            end_date=normalized_end,
            min_coincidences=min_coincidences
        )
        
        print(f"\n[RESULT] RESULTADO DEL SERVICIO:")
        print(f"  - Success: {result.get('success')}")
        print(f"  - Algoritmo: {result.get('algorithm')}")
        
        if result.get('success'):
            data = result.get('data', [])
            print(f"  - Total resultados: {len(data)}")
            
            # Buscar números objetivo en resultados
            found_targets = []
            for item in data:
                if item.get('numero_celular') in target_numbers:
                    found_targets.append(item)
            
            if found_targets:
                print(f"\n[OK] NUMEROS OBJETIVO EN RESULTADOS: {len(found_targets)}")
                for target in found_targets:
                    print(f"  - {target['numero_celular']}: {target['total_coincidencias']} coincidencias")
                    print(f"    Celdas: {target.get('celdas_coincidentes', [])}")
            else:
                print(f"\n[FAIL] NINGUN NUMERO OBJETIVO EN RESULTADOS")
                
                # Mostrar primeros 5 resultados para diagnóstico
                if data:
                    print(f"\n[LIST] PRIMEROS 5 RESULTADOS (de {len(data)}):")
                    for i, item in enumerate(data[:5], 1):
                        print(f"  {i}. {item.get('numero_celular')}: {item.get('total_coincidencias')} coincidencias")
        else:
            print(f"  - Error: {result.get('error')}")
        
        # PASO 4: Simular la llamada exacta del frontend
        print(f"\n" + "=" * 80)
        print("PASO 4: SIMULAR LLAMADA EXACTA DEL FRONTEND")
        print("=" * 80)
        
        # Importar la función expuesta de main.py
        try:
            from main import analyze_correlation as main_analyze_correlation
            
            # Llamar con parámetros exactos del frontend
            frontend_result = main_analyze_correlation(
                mission_id,
                ui_start_date,  # Con formato T
                ui_end_date,    # Con formato T  
                min_coincidences
            )
            
            print(f"\n[FRONTEND] RESULTADO DESDE main.py (como lo ve el frontend):")
            print(f"  - Success: {frontend_result.get('success')}")
            
            if frontend_result.get('success'):
                frontend_data = frontend_result.get('data', [])
                print(f"  - Total resultados: {len(frontend_data)}")
                
                # Verificar números objetivo
                frontend_targets = [d for d in frontend_data if d.get('numero_celular') in target_numbers]
                
                if frontend_targets:
                    print(f"  - [OK] Numeros objetivo encontrados: {len(frontend_targets)}")
                else:
                    print(f"  - [FAIL] Numeros objetivo NO encontrados")
                    
                    # Debug: mostrar qué números SÍ aparecen
                    if frontend_data:
                        print(f"\n  Números que SÍ aparecen (primeros 10):")
                        for item in frontend_data[:10]:
                            print(f"    - {item.get('numero_celular')}")
            else:
                print(f"  - Error: {frontend_result.get('error')}")
                
        except Exception as e:
            print(f"\n[WARNING] No se pudo importar main.py: {e}")
        
        # DIAGNÓSTICO FINAL
        print(f"\n" + "=" * 80)
        print("DIAGNÓSTICO L2 COMPLETO")
        print("=" * 80)
        
        print(f"\n[SUMMARY] RESUMEN DEL PROBLEMA:")
        print(f"  1. Hay datos HUNTER en el periodo? {'SI' if hunter_stats['total'] > 0 else 'NO'}")
        print(f"  2. Hay datos de operadores en el periodo? {'SI' if call_stats['total'] > 0 else 'NO'}")
        print(f"  3. Los numeros objetivo estan en BD? {'SI' if any(results) else 'NO'}")
        print(f"  4. El servicio encuentra correlaciones? {'SI' if result.get('success') and len(result.get('data', [])) > 0 else 'NO'}")
        print(f"  5. Los numeros objetivo aparecen en correlaciones? {'SI' if found_targets else 'NO'}")
        
        if not found_targets and data:
            print(f"\n[WARNING] PROBLEMA IDENTIFICADO:")
            print(f"  - El servicio encuentra {len(data)} correlaciones")
            print(f"  - PERO ningún número objetivo está incluido")
            print(f"  - Posibles causas:")
            print(f"    1. Las fechas/horas no coinciden exactamente")
            print(f"    2. Los Cell IDs no coinciden entre HUNTER y operadores")
            print(f"    3. El algoritmo de normalización está fallando")
            print(f"    4. El filtro min_coincidences={min_coincidences} es muy alto")
            
    finally:
        conn.close()
    
    print(f"\n" + "=" * 80)
    print("FIN DEL DIAGNÓSTICO L2")
    print("=" * 80)

if __name__ == "__main__":
    debug_ui_correlation_issue()