#!/usr/bin/env python3
"""
TEST INICIALIZADO: Endpoint get_call_interactions()
==================================================

Prueba el endpoint get_call_interactions() con inicializacion completa
del backend para simular condiciones reales de ejecucion.
"""

import sys
from pathlib import Path
import sqlite3
import json
import traceback
import logging

# Configurar path para imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Configurar logging similar al main
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def inicializar_backend_minimo():
    """Inicializa backend de forma minima para testing"""
    try:
        # Importar y configurar base de datos
        from database.connection import init_database
        
        db_path = current_dir / 'kronos.db'
        logger.info(f"Inicializando BD: {db_path}")
        
        # No recrear, usar BD existente
        init_database(str(db_path), force_recreate=False)
        logger.info("Base de datos inicializada correctamente")
        
        return True
        
    except Exception as e:
        logger.error(f"Error inicializando backend: {e}")
        traceback.print_exc()
        return False

def test_endpoint_con_inicializacion():
    """Prueba endpoint con inicializacion completa"""
    print("=" * 80)
    print("TEST ENDPOINT CON INICIALIZACION COMPLETA")
    print("=" * 80)
    
    # Inicializar backend
    if not inicializar_backend_minimo():
        print("ERROR: No se pudo inicializar backend")
        return
    
    # Importar endpoint despues de inicializacion
    try:
        from main import get_call_interactions
        print("Endpoint importado correctamente")
    except Exception as e:
        print(f"Error importando endpoint: {e}")
        traceback.print_exc()
        return
    
    # Parametros de prueba
    mission_id = "mission_MPFRBNsb"
    target_number = "3113330727"
    start_datetime = "2021-01-01 00:00:00"
    end_datetime = "2024-12-31 23:59:59"
    
    print(f"\nParametros:")
    print(f"  mission_id: {mission_id}")
    print(f"  target_number: {target_number}")
    print(f"  start_datetime: {start_datetime}")
    print(f"  end_datetime: {end_datetime}")
    
    try:
        print(f"\nEjecutando get_call_interactions()...")
        result = get_call_interactions(
            mission_id=mission_id,
            target_number=target_number,
            start_datetime=start_datetime,
            end_datetime=end_datetime
        )
        
        print(f"\nRESULTADO:")
        print(f"Tipo: {type(result)}")
        print(f"Cantidad: {len(result) if result else 0}")
        
        if result and len(result) > 0:
            primer_registro = result[0]
            print(f"\nPRIMER REGISTRO:")
            
            # Verificar campos GPS criticos
            campos_criticos = ['lat_hunter', 'lon_hunter', 'punto_hunter']
            for campo in campos_criticos:
                if campo in primer_registro:
                    valor = primer_registro[campo]
                    print(f"  {campo}: {valor} (tipo: {type(valor)})")
                else:
                    print(f"  {campo}: NO ENCONTRADO")
            
            # Verificar que sea JSON serializable (como lo enviaria Eel)
            try:
                json_str = json.dumps(result, ensure_ascii=False, default=str)
                print(f"\nJSON SERIALIZABLE: SI (longitud: {len(json_str)} chars)")
                
                # Verificar que los GPS se mantienen en JSON
                parsed_back = json.loads(json_str)
                if parsed_back and len(parsed_back) > 0:
                    json_lat = parsed_back[0].get('lat_hunter')
                    json_lon = parsed_back[0].get('lon_hunter')
                    print(f"GPS en JSON - lat_hunter: {json_lat} (tipo: {type(json_lat)})")
                    print(f"GPS en JSON - lon_hunter: {json_lon} (tipo: {type(json_lon)})")
                
            except Exception as json_error:
                print(f"ERROR JSON SERIALIZATION: {json_error}")
            
            # Guardar resultado
            output_file = current_dir / "test_endpoint_inicializado_resultado.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "timestamp": "2025-08-20",
                    "test_type": "endpoint_inicializado",
                    "parametros": {
                        "mission_id": mission_id,
                        "target_number": target_number,
                        "start_datetime": start_datetime,
                        "end_datetime": end_datetime
                    },
                    "resultado": result
                }, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"\nResultado guardado en: {output_file}")
            
        else:
            print("\nNo se obtuvieron resultados")
        
    except Exception as e:
        print(f"\nERROR ejecutando endpoint: {e}")
        traceback.print_exc()

def verificar_datos_directos_bd():
    """Verificacion directa de BD para comparar"""
    print(f"\n" + "=" * 60)
    print("VERIFICACION DIRECTA BD")
    print("=" * 60)
    
    try:
        db_path = current_dir / 'kronos.db'
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            
            # Misma query que el endpoint
            query = """
            SELECT 
                ocd.numero_origen, ocd.numero_destino,
                COALESCE(cd_destino.lat, cd_origen.lat) as lat_hunter,
                COALESCE(cd_destino.lon, cd_origen.lon) as lon_hunter,
                COALESCE(cd_destino.punto, cd_origen.punto) as punto_hunter
            FROM operator_call_data ocd
            LEFT JOIN cellular_data cd_origen ON (cd_origen.cell_id = ocd.celda_origen AND cd_origen.mission_id = ocd.mission_id)
            LEFT JOIN cellular_data cd_destino ON (cd_destino.cell_id = ocd.celda_destino AND cd_destino.mission_id = ocd.mission_id)
            WHERE ocd.mission_id = 'mission_MPFRBNsb'
              AND (ocd.numero_origen = '3113330727' OR ocd.numero_destino = '3113330727')
            LIMIT 1
            """
            
            cursor.execute(query)
            row = cursor.fetchone()
            
            if row:
                print(f"BD DIRECTA:")
                print(f"  numero_origen: {row[0]}")
                print(f"  numero_destino: {row[1]}")
                print(f"  lat_hunter: {row[2]} (tipo: {type(row[2])})")
                print(f"  lon_hunter: {row[3]} (tipo: {type(row[3])})")
                print(f"  punto_hunter: {row[4]}")
            else:
                print("BD DIRECTA: No se encontraron registros")
    
    except Exception as e:
        print(f"Error verificacion BD: {e}")

def main():
    print("TEST ENDPOINT get_call_interactions() CON INICIALIZACION")
    print("Investigacion problema GPS Frontend - Boris")
    
    # Test principal
    test_endpoint_con_inicializacion()
    
    # Verificacion adicional
    verificar_datos_directos_bd()
    
    print(f"\n" + "=" * 80)
    print("SIGUIENTE PASO:")
    print("Si este test muestra que el backend retorna GPS correctamente,")
    print("investigar el frontend TableCorrelationModal.tsx y como procesa")
    print("los datos recibidos del endpoint get_call_interactions()")

if __name__ == "__main__":
    main()