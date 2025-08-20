#!/usr/bin/env python3
"""
TEST DIRECTO: Endpoint get_call_interactions()
==============================================

Objetivo: Probar directamente el endpoint get_call_interactions() 
para verificar exactamente que datos retorna y como llegan al frontend.

PROBLEMA REPORTADO POR BORIS:
- Frontend recibe "N/A" en coordenadas GPS
- Pero el backend SI tiene los datos GPS correctos

HIPOTESIS:
- Puede haber un problema de formato de datos
- Puede haber un problema en la comunicacion Eel Python->JavaScript
- Puede haber un problema de nombres de campos

FECHA: 2025-08-20
"""

import sys
from pathlib import Path
import sqlite3
import json
import traceback

# Configurar path para imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Importar el endpoint directamente
from main import get_call_interactions

def test_endpoint_directo():
    """
    Prueba directa del endpoint get_call_interactions() 
    usando los mismos parametros que usa el frontend
    """
    print("=" * 80)
    print("TEST DIRECTO: get_call_interactions()")
    print("=" * 80)
    
    # Parametros exactos basados en los datos confirmados
    mission_id = "mission_MPFRBNsb"
    target_number = "3113330727"  # Numero confirmado en BD
    start_datetime = "2021-01-01 00:00:00"
    end_datetime = "2024-12-31 23:59:59"
    
    print(f"Parametros del test:")
    print(f"  mission_id: {mission_id}")
    print(f"  target_number: {target_number}")
    print(f"  start_datetime: {start_datetime}")
    print(f"  end_datetime: {end_datetime}")
    
    try:
        print(f"\nEjecutando get_call_interactions()...")
        
        # Llamar al endpoint directamente
        result = get_call_interactions(
            mission_id=mission_id,
            target_number=target_number,
            start_datetime=start_datetime,
            end_datetime=end_datetime
        )
        
        print(f"\nRESULTADO DEL ENDPOINT:")
        print(f"Tipo de resultado: {type(result)}")
        print(f"Cantidad de registros: {len(result) if result else 0}")
        
        if result:
            # Analizar primer registro en detalle
            primer_registro = result[0]
            print(f"\nANALISIS DEL PRIMER REGISTRO:")
            print(f"Tipo: {type(primer_registro)}")
            
            # Verificar campos GPS especificos
            campos_gps = ['lat_hunter', 'lon_hunter', 'punto_hunter', 'hunter_source']
            print(f"\nCAMPOS GPS EN EL RESULTADO:")
            for campo in campos_gps:
                if campo in primer_registro:
                    valor = primer_registro[campo]
                    print(f"  {campo}: {valor} (tipo: {type(valor)})")
                else:
                    print(f"  {campo}: CAMPO NO ENCONTRADO")
            
            # Verificar todos los campos disponibles
            print(f"\nTODOS LOS CAMPOS DISPONIBLES:")
            for key, value in primer_registro.items():
                tipo_valor = type(value).__name__
                valor_mostrar = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                print(f"  {key}: {valor_mostrar} ({tipo_valor})")
            
            # Guardar resultado completo para revision
            resultado_completo = {
                "timestamp": "2025-08-20",
                "endpoint_test": "get_call_interactions",
                "parametros": {
                    "mission_id": mission_id,
                    "target_number": target_number,
                    "start_datetime": start_datetime,
                    "end_datetime": end_datetime
                },
                "resultado_tipo": str(type(result)),
                "cantidad_registros": len(result),
                "primer_registro": primer_registro,
                "todos_los_registros": result
            }
            
            output_file = current_dir / "test_endpoint_get_call_interactions_resultado.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(resultado_completo, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"\nResultado completo guardado en: {output_file}")
            
        else:
            print("\nNo se obtuvieron resultados del endpoint")
            print("Verificando si hay problema con la inicializacion...")
            
            # Verificar conectividad directa a BD
            try:
                db_path = current_dir / 'kronos.db'
                with sqlite3.connect(str(db_path)) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM operator_call_data WHERE mission_id = ? AND numero_origen = ?", 
                                 (mission_id, target_number))
                    count = cursor.fetchone()[0]
                    print(f"Verificacion directa BD: {count} registros encontrados")
            except Exception as db_error:
                print(f"Error verificando BD directamente: {db_error}")
        
    except Exception as e:
        print(f"\nERROR ejecutando endpoint: {e}")
        print(f"Traceback completo:")
        traceback.print_exc()
        
        # Intentar diagnosis adicional
        print(f"\nDIAGNOSIS ADICIONAL:")
        try:
            # Verificar si los servicios estan inicializados
            from main import auth_service, mission_service
            print(f"auth_service inicializado: {auth_service is not None}")
            print(f"mission_service inicializado: {mission_service is not None}")
        except Exception as init_error:
            print(f"Error verificando servicios: {init_error}")

def test_comparacion_sql_directa():
    """
    Compara el resultado del endpoint vs la consulta SQL directa
    para verificar si hay perdida de datos en el proceso
    """
    print(f"\n" + "=" * 80)
    print("COMPARACION: Endpoint vs SQL Directo")
    print("=" * 80)
    
    mission_id = "mission_MPFRBNsb"
    target_number = "3113330727"
    start_datetime = "2021-01-01 00:00:00"
    end_datetime = "2024-12-31 23:59:59"
    
    # SQL directo (mismo que en main.py)
    query = """
    SELECT 
        ocd.numero_origen as originador,
        ocd.numero_destino as receptor,
        ocd.fecha_hora_llamada as fecha_hora, 
        ocd.duracion_segundos as duracion,
        ocd.operator as operador,
        ocd.celda_origen,
        ocd.celda_destino,
        ocd.latitud_origen,
        ocd.longitud_origen,
        ocd.latitud_destino,
        ocd.longitud_destino,
        cd_origen.punto as punto_hunter_origen,
        cd_origen.lat as lat_hunter_origen,
        cd_origen.lon as lon_hunter_origen,
        cd_destino.punto as punto_hunter_destino,
        cd_destino.lat as lat_hunter_destino,
        cd_destino.lon as lon_hunter_destino,
        COALESCE(cd_destino.punto, cd_origen.punto) as punto_hunter,
        COALESCE(cd_destino.lat, cd_origen.lat) as lat_hunter,
        COALESCE(cd_destino.lon, cd_origen.lon) as lon_hunter,
        CASE 
            WHEN cd_destino.punto IS NOT NULL THEN 'destino'
            WHEN cd_origen.punto IS NOT NULL THEN 'origen' 
            ELSE 'ninguno'
        END as hunter_source
    FROM operator_call_data ocd
    LEFT JOIN cellular_data cd_origen ON (cd_origen.cell_id = ocd.celda_origen AND cd_origen.mission_id = ocd.mission_id)
    LEFT JOIN cellular_data cd_destino ON (cd_destino.cell_id = ocd.celda_destino AND cd_destino.mission_id = ocd.mission_id)
    WHERE ocd.mission_id = ?
      AND (ocd.numero_origen = ? OR ocd.numero_destino = ?)
      AND ocd.fecha_hora_llamada BETWEEN ? AND ?  
    ORDER BY ocd.fecha_hora_llamada DESC
    """
    
    try:
        db_path = current_dir / 'kronos.db'
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(query, (mission_id, target_number, target_number, start_datetime, end_datetime))
            rows = cursor.fetchall()
            
            if rows:
                column_names = [description[0] for description in cursor.description]
                sql_directo_result = []
                
                for row in rows:
                    registro = {}
                    for i, value in enumerate(row):
                        field_name = column_names[i]
                        registro[field_name] = value
                    sql_directo_result.append(registro)
                
                print(f"SQL Directo encontro: {len(sql_directo_result)} registros")
                primer_sql = sql_directo_result[0]
                print(f"Primer registro SQL - lat_hunter: {primer_sql.get('lat_hunter')} (tipo: {type(primer_sql.get('lat_hunter'))})")
                print(f"Primer registro SQL - lon_hunter: {primer_sql.get('lon_hunter')} (tipo: {type(primer_sql.get('lon_hunter'))})")
                print(f"Primer registro SQL - punto_hunter: {primer_sql.get('punto_hunter')}")
                
                return sql_directo_result
            else:
                print("SQL Directo no encontro registros")
                return []
                
    except Exception as e:
        print(f"Error en SQL directo: {e}")
        traceback.print_exc()
        return []

def main():
    """Funcion principal del test"""
    print("TEST ENDPOINT get_call_interactions() - Investigacion Boris")
    print("Objetivo: Verificar exactamente que datos retorna el backend")
    print("Problema: Frontend recibe 'N/A' pero backend tiene datos GPS")
    
    # Test 1: Endpoint directo
    test_endpoint_directo()
    
    # Test 2: Comparacion con SQL directo
    sql_result = test_comparacion_sql_directa()
    
    print(f"\n" + "=" * 80)
    print("CONCLUSION DEL TEST")
    print("=" * 80)
    print("Si el endpoint retorna datos GPS validos pero el frontend recibe 'N/A',")
    print("el problema NO esta en el backend sino en:")
    print("1. La comunicacion Eel Python->JavaScript")
    print("2. El frontend TypeScript que procesa los datos")
    print("3. El componente TableCorrelationModal.tsx")

if __name__ == "__main__":
    main()