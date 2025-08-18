#!/usr/bin/env python3
"""
VERIFICACIÓN URGENTE BACKEND - Correlación de Números Objetivo
==============================================================

Test específico para verificar que el backend retorna correctamente los
números objetivo con la configuración exacta que usará la UI.

CONFIGURACIÓN CRÍTICA:
- Período: 2021-05-20 10:00:00 a 2021-05-20 14:30:00
- Mínimo coincidencias: 1
- Misión: mission_MPFRBNsb

NÚMEROS OBJETIVO ESPERADOS:
- 3143534707: 3 coincidencias
- 3224274851: 2 coincidencias
- 3208611034: 2 coincidencias
- 3214161903: 1 coincidencia
- 3102715509: 1 coincidencia
"""

import os
import sys
import sqlite3
import json
from datetime import datetime
from pathlib import Path

# Configurar path para imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from database.connection import init_database, get_database_manager
from services.correlation_analysis_service import get_correlation_service

def setup_database():
    """Inicializa la base de datos para testing"""
    try:
        print("Inicializando base de datos...")
        db_path = os.path.join(current_dir, 'kronos.db')
        init_database(db_path, force_recreate=False)
        print("Base de datos inicializada correctamente")
        return True
    except Exception as e:
        print(f"Error inicializando base de datos: {e}")
        return False

def verify_mission_exists(mission_id="mission_MPFRBNsb"):
    """Verifica que la misión existe en la base de datos"""
    try:
        print(f"\nVerificando existencia de mision: {mission_id}")
        
        db_manager = get_database_manager()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar si la misión existe
            cursor.execute("SELECT id, code, name FROM missions WHERE id = ?", (mission_id,))
            mission = cursor.fetchone()
            
            if mission:
                print(f"Mision encontrada: {mission[1]} - {mission[2]}")
                return True
            else:
                print(f"Mision '{mission_id}' no encontrada en la base de datos")
                
                # Mostrar misiones disponibles
                cursor.execute("SELECT id, code, name FROM missions ORDER BY code")
                available_missions = cursor.fetchall()
                
                if available_missions:
                    print("\nMisiones disponibles:")
                    for m in available_missions:
                        print(f"   - {m[0]}: {m[1]} - {m[2]}")
                else:
                    print("No hay misiones en la base de datos")
                
                return False
                
    except Exception as e:
        print(f"Error verificando mision: {e}")
        return False

def verify_data_availability(mission_id="mission_MPFRBNsb"):
    """Verifica que hay datos disponibles para el análisis"""
    try:
        print(f"\nVerificando disponibilidad de datos para mision: {mission_id}")
        
        db_manager = get_database_manager()
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar datos HUNTER
            cursor.execute("""
                SELECT COUNT(*) FROM cellular_data 
                WHERE mission_id = ? 
                AND date_time BETWEEN '2021-05-20 10:00:00' AND '2021-05-20 14:30:00'
            """, (mission_id,))
            hunter_count = cursor.fetchone()[0]
            
            # Verificar datos de operadores para el período
            cursor.execute("""
                SELECT COUNT(*) FROM operator_data 
                WHERE mission_id = ? 
                AND datetime BETWEEN '2021-05-20 10:00:00' AND '2021-05-20 14:30:00'
            """, (mission_id,))
            operator_count = cursor.fetchone()[0]
            
            # Verificar Cell IDs específicos (51438 y 56124) en el período
            cursor.execute("""
                SELECT DISTINCT cell_id, COUNT(*) as registros
                FROM operator_data 
                WHERE mission_id = ? 
                AND datetime BETWEEN '2021-05-20 10:00:00' AND '2021-05-20 14:30:00'
                AND cell_id IN (51438, 56124)
                GROUP BY cell_id
                ORDER BY cell_id
            """, (mission_id,))
            critical_cells = cursor.fetchall()
            
            print(f"Datos HUNTER en periodo: {hunter_count} registros")
            print(f"Datos operadores en periodo: {operator_count} registros")
            
            if critical_cells:
                print(f"Cell IDs criticos disponibles:")
                for cell_id, count in critical_cells:
                    print(f"   - Cell ID {cell_id}: {count} registros")
            else:
                print("Cell IDs criticos (51438, 56124) no encontrados en el periodo")
            
            # Verificar números objetivo específicos en datos de operadores
            target_numbers = ['3143534707', '3224274851', '3208611034', '3214161903', '3102715509']
            print(f"\nVerificando numeros objetivo en datos de operadores:")
            
            for number in target_numbers:
                # Buscar número con y sin prefijo 57
                cursor.execute("""
                    SELECT COUNT(*) FROM operator_data 
                    WHERE mission_id = ? 
                    AND datetime BETWEEN '2021-05-20 10:00:00' AND '2021-05-20 14:30:00'
                    AND (numero_celular = ? OR numero_celular = ?)
                """, (mission_id, number, f"57{number}"))
                count = cursor.fetchone()[0]
                print(f"   - {number}: {count} registros")
            
            return hunter_count > 0 and operator_count > 0
            
    except Exception as e:
        print(f"Error verificando datos: {e}")
        return False

def test_correlation_endpoint(mission_id="mission_MPFRBNsb"):
    """Ejecuta el test específico del endpoint de correlación"""
    try:
        print(f"\nEJECUTANDO TEST DE CORRELACION")
        print(f"   Periodo: 2021-05-20 10:00:00 a 2021-05-20 14:30:00")
        print(f"   Minimo coincidencias: 1")
        print(f"   Mision: {mission_id}")
        
        # Obtener servicio de correlación
        correlation_service = get_correlation_service()
        if not correlation_service:
            print("No se pudo obtener el servicio de correlacion")
            return False
        
        # Ejecutar análisis con configuración exacta
        result = correlation_service.analyze_correlation(
            mission_id=mission_id,
            start_date='2021-05-20 10:00:00',
            end_date='2021-05-20 14:30:00',
            min_coincidences=1
        )
        
        # Verificar estructura básica del resultado
        if not isinstance(result, dict):
            print(f"Resultado no es un diccionario: {type(result)}")
            return False
        
        if not result.get('success'):
            error_msg = result.get('error', 'Error desconocido')
            print(f"Error en analisis: {error_msg}")
            return False
        
        # Analizar datos retornados
        data = result.get('data', [])
        print(f"\nRESULTADOS DEL ANALISIS:")
        print(f"   Estado: Exitoso")
        print(f"   Total numeros encontrados: {len(data)}")
        
        if not data:
            print("No se encontraron numeros objetivo")
            return False
        
        # Verificar números objetivo específicos
        target_numbers = {
            '3143534707': 3,
            '3224274851': 2,
            '3208611034': 2,
            '3214161903': 1,
            '3102715509': 1
        }
        
        found_targets = {}
        
        print(f"\nVERIFICACION DE NUMEROS OBJETIVO:")
        for item in data:
            numero = item.get('numero_celular', '')
            coincidencias = item.get('total_coincidencias', 0)
            
            # Verificar si es uno de nuestros números objetivo
            if numero in target_numbers:
                found_targets[numero] = coincidencias
                expected = target_numbers[numero]
                status = "OK" if coincidencias >= expected else "WARN"
                print(f"   {status} {numero}: {coincidencias} coincidencias (esperado: {expected})")
        
        # Verificar números faltantes
        missing_targets = set(target_numbers.keys()) - set(found_targets.keys())
        if missing_targets:
            print(f"\nNUMEROS OBJETIVO FALTANTES:")
            for numero in missing_targets:
                print(f"   {numero}: No encontrado (esperado: {target_numbers[numero]} coincidencias)")
        
        # Verificar formato de respuesta para frontend
        print(f"\nVERIFICACION DE FORMATO PARA FRONTEND:")
        
        sample_item = data[0] if data else None
        if sample_item:
            required_fields = ['numero_celular', 'total_coincidencias', 'operadores']
            for field in required_fields:
                if field in sample_item:
                    print(f"   Campo '{field}': presente")
                else:
                    print(f"   Campo '{field}': faltante")
            
            # Verificar que números no tengan prefijo 57
            numero = sample_item.get('numero_celular', '')
            if numero.startswith('57'):
                print(f"   WARN: Numero con prefijo 57: {numero}")
            else:
                print(f"   OK: Numero sin prefijo 57: {numero}")
        
        # Guardar resultado completo para análisis
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"backend_correlation_verification_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\nResultado completo guardado en: {output_file}")
        
        # Resumen final
        total_found = len(found_targets)
        total_expected = len(target_numbers)
        
        print(f"\nRESUMEN FINAL:")
        print(f"   Numeros objetivo encontrados: {total_found}/{total_expected}")
        print(f"   Estado general: {'EXITOSO' if total_found == total_expected else 'PARCIAL'}")
        
        return total_found == total_expected
        
    except Exception as e:
        print(f"Error ejecutando test de correlacion: {e}")
        import traceback
        print(f"Traceback:\n{traceback.format_exc()}")
        return False

def main():
    """Función principal del test de verificación"""
    print("="*70)
    print("VERIFICACION URGENTE BACKEND - CORRELACION DE NUMEROS OBJETIVO")
    print("="*70)
    
    # Paso 1: Inicializar base de datos
    if not setup_database():
        print("\nFALLO: No se pudo inicializar la base de datos")
        return False
    
    # Paso 2: Verificar que la misión existe
    if not verify_mission_exists():
        print("\nFALLO: Mision no encontrada")
        return False
    
    # Paso 3: Verificar disponibilidad de datos
    if not verify_data_availability():
        print("\nFALLO: Datos insuficientes para analisis")
        return False
    
    # Paso 4: Ejecutar test de correlación
    if not test_correlation_endpoint():
        print("\nFALLO: Test de correlacion fallo")
        return False
    
    print("\n" + "="*70)
    print("VERIFICACION COMPLETADA EXITOSAMENTE")
    print("El backend esta retornando correctamente los numeros objetivo")
    print("="*70)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)