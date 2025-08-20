"""
KRONOS - Test para Diagram Correlation Service
===============================================================================
Script de prueba para validar el funcionamiento del servicio de diagrama
de correlación interactivo con datos reales de la base de datos.

Funcionalidades de prueba:
1. Conectividad con base de datos
2. Extracción de celdas HUNTER
3. Generación de red de comunicaciones
4. Construcción de nodos y aristas
5. Validación de estructura JSON de respuesta

Autor: Claude Code para Boris
Fecha: 2025-08-18
Versión: 1.0.0 - Pruebas iniciales
===============================================================================
"""

import os
import sys
import logging
import json
from pathlib import Path

# Configurar path para imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from services.diagram_correlation_service import get_diagram_correlation_service
from database.connection import get_database_manager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_database_connectivity():
    """Prueba 1: Verificar conectividad con base de datos"""
    print("\n" + "="*80)
    print("PRUEBA 1: CONECTIVIDAD CON BASE DE DATOS")
    print("="*80)
    
    try:
        db_manager = get_database_manager()
        with db_manager.get_session() as session:
            # Verificar tablas principales
            result = session.execute("SELECT COUNT(*) FROM cellular_data").scalar()
            print(f"✓ Registros en cellular_data: {result}")
            
            result = session.execute("SELECT COUNT(*) FROM operator_call_data").scalar()
            print(f"✓ Registros en operator_call_data: {result}")
            
            result = session.execute("SELECT COUNT(*) FROM missions").scalar()
            print(f"✓ Registros en missions: {result}")
            
            # Verificar misión de prueba
            result = session.execute("SELECT id FROM missions LIMIT 1").fetchone()
            if result:
                print(f"✓ Misión de prueba disponible: {result[0]}")
                return result[0]
            else:
                print("⚠️  No hay misiones disponibles para prueba")
                return None
                
    except Exception as e:
        print(f"❌ Error de conectividad: {e}")
        return None


def test_hunter_cells_extraction(mission_id):
    """Prueba 2: Extracción de celdas HUNTER"""
    print("\n" + "="*80)
    print("PRUEBA 2: EXTRACCIÓN DE CELDAS HUNTER")
    print("="*80)
    
    try:
        service = get_diagram_correlation_service()
        
        with service.db_manager.get_session() as session:
            hunter_cells = service._extract_hunter_cells(session, mission_id)
            
            print(f"✓ Celdas HUNTER extraídas: {len(hunter_cells)}")
            if hunter_cells:
                print(f"✓ Primeras 10 celdas: {sorted(list(hunter_cells))[:10]}")
                return hunter_cells
            else:
                print("⚠️  No se encontraron celdas HUNTER")
                return set()
                
    except Exception as e:
        print(f"❌ Error extrayendo celdas HUNTER: {e}")
        return set()


def test_sample_numbers_extraction(mission_id):
    """Prueba 3: Obtener números de muestra para pruebas"""
    print("\n" + "="*80)
    print("PRUEBA 3: NÚMEROS DE MUESTRA DISPONIBLES")
    print("="*80)
    
    try:
        db_manager = get_database_manager()
        with db_manager.get_session() as session:
            # Obtener números objetivo únicos
            result = session.execute(f"""
                SELECT DISTINCT numero_objetivo, COUNT(*) as comunicaciones
                FROM operator_call_data 
                WHERE mission_id = '{mission_id}'
                GROUP BY numero_objetivo
                ORDER BY comunicaciones DESC
                LIMIT 10
            """).fetchall()
            
            print(f"✓ Números objetivo disponibles para prueba:")
            numeros_muestra = []
            for row in result:
                numero = row[0]
                count = row[1]
                print(f"  - {numero}: {count} comunicaciones")
                numeros_muestra.append(numero)
            
            return numeros_muestra[:3]  # Retornar top 3
            
    except Exception as e:
        print(f"❌ Error obteniendo números de muestra: {e}")
        return []


def test_diagram_generation(mission_id, numero_objetivo):
    """Prueba 4: Generación completa del diagrama"""
    print("\n" + "="*80)
    print(f"PRUEBA 4: GENERACIÓN DE DIAGRAMA - {numero_objetivo}")
    print("="*80)
    
    try:
        service = get_diagram_correlation_service()
        
        # Parámetros de prueba
        start_datetime = "2021-01-01 00:00:00"
        end_datetime = "2021-12-31 23:59:59"
        filtros = {}
        
        print(f"📊 Generando diagrama para número: {numero_objetivo}")
        print(f"📅 Período: {start_datetime} - {end_datetime}")
        
        # Generar diagrama
        result = service.get_correlation_diagram_data(
            mission_id=mission_id,
            numero_objetivo=numero_objetivo,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            filtros=filtros
        )
        
        # Validar estructura de respuesta
        print(f"\n📋 RESULTADOS DEL DIAGRAMA:")
        print(f"✓ Success: {result.get('success', False)}")
        print(f"✓ Número objetivo: {result.get('numero_objetivo', 'N/A')}")
        print(f"✓ Nodos generados: {len(result.get('nodos', []))}")
        print(f"✓ Aristas generadas: {len(result.get('aristas', []))}")
        print(f"✓ Celdas HUNTER: {len(result.get('celdas_hunter', []))}")
        print(f"✓ Tiempo procesamiento: {result.get('processing_time', 0):.3f}s")
        
        # Mostrar estadísticas si están disponibles
        if result.get('estadisticas'):
            stats = result['estadisticas']
            print(f"\n📈 ESTADÍSTICAS:")
            print(f"  - Total comunicaciones: {stats.get('total_comunicaciones', 0)}")
            print(f"  - Contactos únicos: {stats.get('contactos_unicos', 0)}")
            print(f"  - Duración total (min): {stats.get('duracion_total_minutos', 0)}")
            print(f"  - Tipos de tráfico: {stats.get('tipos_trafico', {})}")
        
        # Mostrar muestra de nodos
        nodos = result.get('nodos', [])
        if nodos:
            print(f"\n👥 MUESTRA DE NODOS:")
            for i, nodo in enumerate(nodos[:5]):
                print(f"  {i+1}. {nodo.get('numero', 'N/A')} ({nodo.get('tipo', 'N/A')}) - "
                      f"{nodo.get('total_comunicaciones', 0)} comunicaciones")
        
        # Mostrar muestra de aristas
        aristas = result.get('aristas', [])
        if aristas:
            print(f"\n🔗 MUESTRA DE ARISTAS:")
            for i, arista in enumerate(aristas[:5]):
                print(f"  {i+1}. {arista.get('origen', 'N/A')} → {arista.get('destino', 'N/A')} "
                      f"({arista.get('tipo_comunicacion', 'N/A')}) - "
                      f"{arista.get('duracion_segundos', 0)}s")
        
        return result
        
    except Exception as e:
        print(f"❌ Error generando diagrama: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None


def test_json_serialization(diagram_data):
    """Prueba 5: Serialización JSON (compatible con frontend)"""
    print("\n" + "="*80)
    print("PRUEBA 5: SERIALIZACIÓN JSON")
    print("="*80)
    
    try:
        if not diagram_data:
            print("⚠️  No hay datos de diagrama para serializar")
            return False
        
        # Intentar serializar a JSON
        json_str = json.dumps(diagram_data, indent=2, default=str)
        json_size = len(json_str)
        
        print(f"✓ Serialización JSON exitosa")
        print(f"✓ Tamaño JSON: {json_size:,} caracteres")
        print(f"✓ Tamaño JSON: {json_size/1024:.2f} KB")
        
        # Verificar que se puede deserializar
        parsed_data = json.loads(json_str)
        print(f"✓ Deserialización exitosa")
        
        # Validar estructura básica
        required_keys = ['success', 'numero_objetivo', 'nodos', 'aristas', 'estadisticas']
        missing_keys = [key for key in required_keys if key not in parsed_data]
        
        if not missing_keys:
            print(f"✓ Estructura JSON válida - todas las claves requeridas presentes")
        else:
            print(f"⚠️  Claves faltantes en JSON: {missing_keys}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en serialización JSON: {e}")
        return False


def run_complete_tests():
    """Ejecuta suite completa de pruebas"""
    print("🚀 INICIANDO PRUEBAS DEL DIAGRAM CORRELATION SERVICE")
    print("="*80)
    
    # Prueba 1: Conectividad
    mission_id = test_database_connectivity()
    if not mission_id:
        print("\n❌ PRUEBAS ABORTADAS: No hay conectividad con base de datos")
        return False
    
    # Prueba 2: Celdas HUNTER
    hunter_cells = test_hunter_cells_extraction(mission_id)
    
    # Prueba 3: Números de muestra
    numeros_muestra = test_sample_numbers_extraction(mission_id)
    if not numeros_muestra:
        print("\n❌ PRUEBAS ABORTADAS: No hay números de muestra disponibles")
        return False
    
    # Prueba 4: Generación de diagrama (probar con primer número)
    numero_test = numeros_muestra[0]
    diagram_data = test_diagram_generation(mission_id, numero_test)
    
    # Prueba 5: Serialización JSON
    json_success = test_json_serialization(diagram_data)
    
    # Resumen final
    print("\n" + "="*80)
    print("🎯 RESUMEN DE PRUEBAS")
    print("="*80)
    
    if diagram_data and diagram_data.get('success') and json_success:
        print("✅ TODAS LAS PRUEBAS EXITOSAS")
        print(f"   - Misión de prueba: {mission_id}")
        print(f"   - Número objetivo: {numero_test}")
        print(f"   - Nodos generados: {len(diagram_data.get('nodos', []))}")
        print(f"   - Aristas generadas: {len(diagram_data.get('aristas', []))}")
        print(f"   - Tiempo procesamiento: {diagram_data.get('processing_time', 0):.3f}s")
        print("\n🎉 El servicio está listo para uso en producción!")
        return True
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON")
        print("   - Revisar logs de error arriba")
        print("   - Verificar configuración de base de datos")
        print("   - Validar datos de prueba disponibles")
        return False


if __name__ == "__main__":
    print("KRONOS - Test del Diagram Correlation Service")
    print(f"Fecha: 2025-08-18")
    print(f"Base de datos: {current_dir / 'kronos.db'}")
    
    try:
        success = run_complete_tests()
        
        if success:
            print(f"\n✅ Suite de pruebas completada exitosamente")
            print(f"📄 El servicio de diagrama de correlación está operativo")
            sys.exit(0)
        else:
            print(f"\n❌ Suite de pruebas falló")
            print(f"🔧 Revisar configuración y datos antes de usar en producción")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n⚠️  Pruebas interrumpidas por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado en suite de pruebas: {e}")
        import traceback
        print(f"Traceback completo:\n{traceback.format_exc()}")
        sys.exit(1)