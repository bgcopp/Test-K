#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INVESTIGACIÓN CRÍTICA - DIAGRAMA CORRELACIÓN 3113330727
======================================================

Investigación específica del problema reportado por Boris:
El número 3113330727 muestra 255 nodos cuando debería mostrar solo interacciones directas.

OBJETIVOS DE LA INVESTIGACIÓN:
1. Consultar directamente la base de datos para obtener datos reales
2. Verificar cuántos registros existen realmente para 3113330727
3. Analizar el servicio de correlación paso a paso
4. Identificar exactamente dónde se generan los 255 nodos
5. Comparar con el comportamiento esperado

Ejecutar: python debug_3113330727_investigation.py
"""

import sqlite3
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar servicios del backend
try:
    from services.correlation_service import CorrelationService
    from services.data_normalizer_service import DataNormalizerService
except ImportError as e:
    print(f"❌ Error importando servicios: {e}")
    print("Ejecutando investigación básica sin servicios...")

class DiagramInvestigator:
    def __init__(self):
        self.db_path = "kronos.db"
        self.target_number = "3113330727"
        self.investigation_results = {
            "target_number": self.target_number,
            "investigation_timestamp": datetime.now().isoformat(),
            "database_analysis": {},
            "correlation_service_analysis": {},
            "data_flow_analysis": {},
            "problem_diagnosis": "",
            "recommended_solution": "",
            "evidence": []
        }
    
    def verify_database_connection(self):
        """Verificar conexión a la base de datos"""
        print("🔌 Verificando conexión a la base de datos...")
        
        if not os.path.exists(self.db_path):
            print(f"❌ Base de datos no encontrada: {self.db_path}")
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar tablas existentes
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"📊 Tablas encontradas: {[table[0] for table in tables]}")
            
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Error conectando a la base de datos: {e}")
            return False
    
    def analyze_target_number_in_database(self):
        """Análisis directo del número objetivo en la base de datos"""
        print(f"🔍 Analizando número {self.target_number} directamente en la base de datos...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Consulta 1: Buscar el número como origen
        cursor.execute("""
            SELECT COUNT(*) as total_as_origin
            FROM cdr_data 
            WHERE origen = ?
        """, (self.target_number,))
        
        origin_count = cursor.fetchone()[0]
        print(f"📱 Registros donde {self.target_number} es ORIGEN: {origin_count}")
        
        # Consulta 2: Buscar el número como destino
        cursor.execute("""
            SELECT COUNT(*) as total_as_destination
            FROM cdr_data 
            WHERE destino = ?
        """, (self.target_number,))
        
        destination_count = cursor.fetchone()[0]
        print(f"📱 Registros donde {self.target_number} es DESTINO: {destination_count}")
        
        # Consulta 3: Total de interacciones únicas
        cursor.execute("""
            SELECT COUNT(DISTINCT destino) as unique_destinations
            FROM cdr_data 
            WHERE origen = ?
        """, (self.target_number,))
        
        unique_destinations = cursor.fetchone()[0]
        print(f"🎯 Destinos únicos cuando {self.target_number} es origen: {unique_destinations}")
        
        # Consulta 4: Orígenes únicos cuando es destino
        cursor.execute("""
            SELECT COUNT(DISTINCT origen) as unique_origins
            FROM cdr_data 
            WHERE destino = ?
        """, (self.target_number,))
        
        unique_origins = cursor.fetchone()[0]
        print(f"🎯 Orígenes únicos cuando {self.target_number} es destino: {unique_origins}")
        
        # Consulta 5: Análisis detallado de interacciones
        cursor.execute("""
            SELECT destino, COUNT(*) as interaction_count
            FROM cdr_data 
            WHERE origen = ?
            GROUP BY destino
            ORDER BY interaction_count DESC
            LIMIT 10
        """, (self.target_number,))
        
        top_destinations = cursor.fetchall()
        print(f"📊 Top 10 destinos más frecuentes:")
        for dest, count in top_destinations:
            print(f"  - {dest}: {count} interacciones")
        
        # Consulta 6: Buscar en períodos específicos
        cursor.execute("""
            SELECT DATE(fecha_inicio) as date, COUNT(*) as daily_count
            FROM cdr_data 
            WHERE origen = ? OR destino = ?
            GROUP BY DATE(fecha_inicio)
            ORDER BY daily_count DESC
            LIMIT 5
        """, (self.target_number, self.target_number))
        
        daily_activity = cursor.fetchall()
        print(f"📅 Días con más actividad:")
        for date, count in daily_activity:
            print(f"  - {date}: {count} registros")
        
        # Guardar resultados del análisis de base de datos
        self.investigation_results["database_analysis"] = {
            "total_as_origin": origin_count,
            "total_as_destination": destination_count,
            "unique_destinations": unique_destinations,
            "unique_origins": unique_origins,
            "top_destinations": top_destinations,
            "daily_activity": daily_activity,
            "total_unique_interactions": unique_destinations + unique_origins
        }
        
        conn.close()
        
        # DIAGNÓSTICO PRELIMINAR
        total_unique_nodes = unique_destinations + unique_origins
        print(f"\n🎯 ANÁLISIS PRELIMINAR:")
        print(f"   - Nodos únicos esperados: {total_unique_nodes}")
        print(f"   - Nodos reportados en UI: 255")
        print(f"   - Diferencia: {255 - total_unique_nodes}")
        
        if total_unique_nodes < 255:
            print(f"⚠️ PROBLEMA IDENTIFICADO: Se están agregando {255 - total_unique_nodes} nodos extra")
            self.investigation_results["problem_diagnosis"] = f"El diagrama muestra {255 - total_unique_nodes} nodos más de los que existen en la base de datos"
        else:
            print(f"✅ Los datos de la base parecen correctos")
    
    def test_correlation_service_directly(self):
        """Probar el servicio de correlación directamente"""
        print(f"\n🔧 Probando servicio de correlación directamente...")
        
        try:
            # Importar y probar el servicio de correlación
            correlation_service = CorrelationService()
            
            # Simular la llamada que hace el frontend
            print(f"📞 Llamando a get_correlations para {self.target_number}...")
            correlations = correlation_service.get_correlations(self.target_number)
            
            if correlations:
                print(f"📊 Correlaciones retornadas por el servicio: {len(correlations)}")
                
                # Analizar la estructura de los datos retornados
                if isinstance(correlations, list) and len(correlations) > 0:
                    first_item = correlations[0]
                    print(f"🔍 Estructura del primer elemento: {list(first_item.keys()) if isinstance(first_item, dict) else type(first_item)}")
                    
                    # Contar nodos únicos en los datos del servicio
                    unique_nodes = set()
                    for correlation in correlations:
                        if isinstance(correlation, dict):
                            if 'origen' in correlation:
                                unique_nodes.add(correlation['origen'])
                            if 'destino' in correlation:
                                unique_nodes.add(correlation['destino'])
                    
                    print(f"🎯 Nodos únicos en datos del servicio: {len(unique_nodes)}")
                    
                    self.investigation_results["correlation_service_analysis"] = {
                        "service_response_count": len(correlations),
                        "unique_nodes_in_service": len(unique_nodes),
                        "first_item_structure": str(type(first_item)),
                        "sample_data": correlations[:3] if len(correlations) >= 3 else correlations
                    }
                    
                    # COMPARACIÓN CRÍTICA
                    db_unique = self.investigation_results["database_analysis"]["total_unique_interactions"]
                    service_unique = len(unique_nodes)
                    
                    print(f"\n🔍 COMPARACIÓN CRÍTICA:")
                    print(f"   - Base de datos directa: {db_unique} nodos únicos")
                    print(f"   - Servicio de correlación: {service_unique} nodos únicos")
                    print(f"   - UI reportada: 255 nodos")
                    
                    if service_unique == 255:
                        print(f"🎯 PROBLEMA IDENTIFICADO: El servicio de correlación está retornando {service_unique} nodos")
                        self.investigation_results["problem_diagnosis"] = "El problema está en el servicio de correlación que retorna más datos de los esperados"
                    elif db_unique == service_unique and service_unique < 255:
                        print(f"🎯 PROBLEMA IDENTIFICADO: El problema está en el frontend, transformando {service_unique} en 255 nodos")
                        self.investigation_results["problem_diagnosis"] = "El problema está en el frontend durante la transformación de datos"
                
            else:
                print("❌ El servicio no retornó datos")
                self.investigation_results["correlation_service_analysis"] = {
                    "service_response_count": 0,
                    "error": "No se obtuvieron datos del servicio"
                }
                
        except Exception as e:
            print(f"❌ Error probando servicio de correlación: {e}")
            self.investigation_results["correlation_service_analysis"] = {
                "error": str(e)
            }
    
    def analyze_data_normalization(self):
        """Analizar el proceso de normalización de datos"""
        print(f"\n🔧 Analizando proceso de normalización de datos...")
        
        try:
            normalizer = DataNormalizerService()
            
            # Probar normalización del número objetivo
            normalized = normalizer.normalize_phone_number(self.target_number)
            print(f"📱 Normalización de {self.target_number}: {normalized}")
            
            # Verificar si hay variantes del número en la base de datos
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Buscar variantes posibles del número
            variants = [
                self.target_number,
                normalized,
                self.target_number[1:] if len(self.target_number) > 10 else None,  # Sin código de país
                "57" + self.target_number if not self.target_number.startswith("57") else None,  # Con código de país
            ]
            
            variants = [v for v in variants if v]  # Filtrar None
            
            print(f"🔍 Buscando variantes del número: {variants}")
            
            total_records = 0
            for variant in variants:
                cursor.execute("""
                    SELECT COUNT(*) FROM cdr_data 
                    WHERE origen = ? OR destino = ?
                """, (variant, variant))
                
                count = cursor.fetchone()[0]
                print(f"  - {variant}: {count} registros")
                total_records += count
            
            print(f"📊 Total de registros considerando variantes: {total_records}")
            
            conn.close()
            
            self.investigation_results["data_flow_analysis"] = {
                "original_number": self.target_number,
                "normalized_number": normalized,
                "variants_tested": variants,
                "total_records_all_variants": total_records
            }
            
        except Exception as e:
            print(f"❌ Error analizando normalización: {e}")
            self.investigation_results["data_flow_analysis"] = {
                "error": str(e)
            }
    
    def generate_diagnosis_and_solution(self):
        """Generar diagnóstico final y solución recomendada"""
        print(f"\n🩺 GENERANDO DIAGNÓSTICO FINAL...")
        
        db_analysis = self.investigation_results.get("database_analysis", {})
        service_analysis = self.investigation_results.get("correlation_service_analysis", {})
        
        # Análisis de los datos
        db_unique = db_analysis.get("total_unique_interactions", 0)
        service_unique = service_analysis.get("unique_nodes_in_service", 0)
        reported_ui = 255
        
        print(f"📊 RESUMEN DE HALLAZGOS:")
        print(f"   - Base de datos: {db_unique} nodos únicos reales")
        print(f"   - Servicio backend: {service_unique} nodos retornados")
        print(f"   - UI frontend: {reported_ui} nodos mostrados")
        
        # Generar diagnóstico específico
        if service_unique == reported_ui:
            diagnosis = f"PROBLEMA EN BACKEND: El servicio de correlación está retornando {service_unique} registros cuando debería retornar solo {db_unique} interacciones directas."
            solution = """
SOLUCIÓN RECOMENDADA:
1. Revisar el método get_correlations() en correlation_service.py
2. Verificar que el filtrado esté limitando a interacciones directas únicamente
3. Asegurar que no se incluyan datos de otros números o períodos
4. Implementar logging detallado para rastrear el flujo de datos
5. Verificar que no se estén duplicando registros en la consulta SQL
"""
        elif db_unique == service_unique and service_unique < reported_ui:
            diagnosis = f"PROBLEMA EN FRONTEND: El backend retorna {service_unique} registros correctos, pero el frontend los transforma en {reported_ui} nodos."
            solution = """
SOLUCIÓN RECOMENDADA:
1. Revisar CorrelationDiagramModal.tsx para verificar transformación de datos
2. Analizar graphTransformations.ts para detectar duplicación de nodos
3. Verificar NetworkDiagram.tsx para ver si se agregan nodos adicionales
4. Implementar logging en cada paso de transformación
5. Verificar que no se estén incluyendo nodos de referencia o auxiliares
"""
        else:
            diagnosis = f"PROBLEMA COMPLEJO: Discrepancia en múltiples capas. DB:{db_unique} -> Service:{service_unique} -> UI:{reported_ui}"
            solution = """
SOLUCIÓN RECOMENDADA:
1. Investigación completa end-to-end con Playwright
2. Logging detallado en cada capa del sistema
3. Revisión del pipeline completo de datos
4. Verificación de caché o datos persistentes
5. Análisis de transformaciones intermedias
"""
        
        self.investigation_results["problem_diagnosis"] = diagnosis
        self.investigation_results["recommended_solution"] = solution
        
        print(f"\n🎯 DIAGNÓSTICO:")
        print(diagnosis)
        print(f"\n💡 SOLUCIÓN:")
        print(solution)
    
    def save_investigation_report(self):
        """Guardar reporte completo de la investigación"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"investigation_report_3113330727_{timestamp}.json"
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.investigation_results, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Reporte guardado en: {report_path}")
            
            # Crear resumen ejecutivo
            summary_path = f"investigation_summary_3113330727_{timestamp}.md"
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(f"""# REPORTE DE INVESTIGACIÓN - DIAGRAMA CORRELACIÓN
## Número: {self.target_number}
## Fecha: {self.investigation_results['investigation_timestamp']}

### PROBLEMA REPORTADO:
El diagrama muestra 255 nodos cuando debería mostrar solo interacciones directas.

### HALLAZGOS:
- **Base de datos**: {self.investigation_results.get('database_analysis', {}).get('total_unique_interactions', 'N/A')} nodos únicos reales
- **Servicio backend**: {self.investigation_results.get('correlation_service_analysis', {}).get('unique_nodes_in_service', 'N/A')} nodos retornados
- **UI frontend**: 255 nodos mostrados

### DIAGNÓSTICO:
{self.investigation_results.get('problem_diagnosis', 'Pendiente')}

### SOLUCIÓN RECOMENDADA:
{self.investigation_results.get('recommended_solution', 'Pendiente')}

### PRÓXIMOS PASOS:
1. Ejecutar tests de Playwright para validar el flujo completo
2. Implementar la solución identificada
3. Verificar la corrección con testing end-to-end
""")
            
            print(f"📋 Resumen ejecutivo guardado en: {summary_path}")
            
        except Exception as e:
            print(f"❌ Error guardando reporte: {e}")
    
    def run_complete_investigation(self):
        """Ejecutar investigación completa"""
        print("INICIANDO INVESTIGACION COMPLETA DEL DIAGRAMA")
        print("=" * 60)
        
        # Verificar conexión a base de datos
        if not self.verify_database_connection():
            print("ERROR: No se puede continuar sin acceso a la base de datos")
            return
        
        # Ejecutar análisis paso a paso
        self.analyze_target_number_in_database()
        self.test_correlation_service_directly()
        self.analyze_data_normalization()
        self.generate_diagnosis_and_solution()
        self.save_investigation_report()
        
        print("\n✅ INVESTIGACIÓN COMPLETA FINALIZADA")
        print("📊 Revisa los archivos generados para obtener el diagnóstico detallado")

if __name__ == "__main__":
    investigator = DiagramInvestigator()
    investigator.run_complete_investigation()