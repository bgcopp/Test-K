#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INVESTIGACION CRITICA - DIAGRAMA CORRELACION 3113330727
========================================================

Investigacion del problema reportado por Boris:
El numero 3113330727 muestra 255 nodos cuando deberia mostrar solo interacciones directas.
"""

import sqlite3
import json
import sys
import os
from datetime import datetime

# Configurar encoding para Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

class DiagramInvestigator:
    def __init__(self):
        self.db_path = "kronos.db"
        self.target_number = "3113330727"
        
    def analyze_database_direct(self):
        """Analisis directo de la base de datos"""
        print(f"\nANALIZANDO NUMERO {self.target_number} EN BASE DE DATOS...")
        
        if not os.path.exists(self.db_path):
            print(f"ERROR: Base de datos no encontrada: {self.db_path}")
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verificar tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]
        print(f"Tablas encontradas: {tables}")
        
        if 'cdr_data' not in tables:
            print("ERROR: Tabla cdr_data no encontrada")
            conn.close()
            return
        
        # Analisis como origen
        cursor.execute("""
            SELECT COUNT(*) FROM cdr_data WHERE origen = ?
        """, (self.target_number,))
        origen_count = cursor.fetchone()[0]
        
        # Analisis como destino
        cursor.execute("""
            SELECT COUNT(*) FROM cdr_data WHERE destino = ?
        """, (self.target_number,))
        destino_count = cursor.fetchone()[0]
        
        # Destinos unicos cuando es origen
        cursor.execute("""
            SELECT COUNT(DISTINCT destino) FROM cdr_data WHERE origen = ?
        """, (self.target_number,))
        destinos_unicos = cursor.fetchone()[0]
        
        # Origenes unicos cuando es destino
        cursor.execute("""
            SELECT COUNT(DISTINCT origen) FROM cdr_data WHERE destino = ?
        """, (self.target_number,))
        origenes_unicos = cursor.fetchone()[0]
        
        # Top destinos
        cursor.execute("""
            SELECT destino, COUNT(*) as count FROM cdr_data 
            WHERE origen = ?
            GROUP BY destino
            ORDER BY count DESC
            LIMIT 10
        """, (self.target_number,))
        top_destinos = cursor.fetchall()
        
        # Buscar variantes del numero
        variantes = [
            self.target_number,
            self.target_number[1:] if len(self.target_number) > 10 else None,
            "57" + self.target_number if not self.target_number.startswith("57") else None,
        ]
        variantes = [v for v in variantes if v]
        
        print(f"\nRESULTADOS PARA {self.target_number}:")
        print(f"- Registros como ORIGEN: {origen_count}")
        print(f"- Registros como DESTINO: {destino_count}")
        print(f"- Destinos unicos: {destinos_unicos}")
        print(f"- Origenes unicos: {origenes_unicos}")
        print(f"- Total nodos unicos esperados: {destinos_unicos + origenes_unicos}")
        
        print(f"\nTop 10 destinos mas frecuentes:")
        for dest, count in top_destinos:
            print(f"  {dest}: {count} llamadas")
        
        # Probar variantes
        print(f"\nProbando variantes del numero:")
        total_variantes = 0
        for variante in variantes:
            cursor.execute("""
                SELECT COUNT(*) FROM cdr_data 
                WHERE origen = ? OR destino = ?
            """, (variante, variante))
            count = cursor.fetchone()[0]
            print(f"  {variante}: {count} registros")
            total_variantes += count
        
        conn.close()
        
        # DIAGNOSTICO
        nodos_esperados = destinos_unicos + origenes_unicos
        nodos_reportados = 255
        diferencia = nodos_reportados - nodos_esperados
        
        print(f"\nDIAGNOSTICO PRELIMINAR:")
        print(f"- Nodos esperados (DB): {nodos_esperados}")
        print(f"- Nodos reportados (UI): {nodos_reportados}")
        print(f"- Diferencia: {diferencia}")
        
        if diferencia > 0:
            print(f"PROBLEMA: Se estan agregando {diferencia} nodos extra en algun punto")
        else:
            print("Los datos de la base parecen correctos")
        
        # Guardar resultados
        resultados = {
            "numero_objetivo": self.target_number,
            "fecha_analisis": datetime.now().isoformat(),
            "registros_como_origen": origen_count,
            "registros_como_destino": destino_count,
            "destinos_unicos": destinos_unicos,
            "origenes_unicos": origenes_unicos,
            "nodos_esperados": nodos_esperados,
            "nodos_reportados_ui": nodos_reportados,
            "diferencia": diferencia,
            "top_destinos": top_destinos,
            "total_variantes": total_variantes
        }
        
        with open(f"investigacion_db_{self.target_number}.json", 'w') as f:
            json.dump(resultados, f, indent=2)
        
        print(f"\nResultados guardados en: investigacion_db_{self.target_number}.json")
        return resultados

if __name__ == "__main__":
    print("INICIANDO INVESTIGACION DEL DIAGRAMA")
    print("=" * 50)
    
    investigator = DiagramInvestigator()
    investigator.analyze_database_direct()
    
    print("\nINVESTIGACION COMPLETADA")