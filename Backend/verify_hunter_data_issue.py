"""
VERIFICACIÓN L2: Por qué faltan Cell IDs en HUNTER
=====================================================
"""

import sqlite3
import os

def verify_hunter_data():
    db_path = os.path.join(os.path.dirname(__file__), 'kronos.db')
    conn = sqlite3.connect(db_path)
    
    mission_id = 'mission_MPFRBNsb'
    
    print("=" * 80)
    print("VERIFICACION L2: CELL IDS EN HUNTER")
    print("=" * 80)
    
    # 1. Ver TODOS los Cell IDs en la misión (sin filtro de fecha)
    query1 = """
        SELECT DISTINCT cell_id, COUNT(*) as count
        FROM cellular_data  
        WHERE mission_id = ?
        AND cell_id IS NOT NULL
        GROUP BY cell_id
        ORDER BY cell_id
    """
    
    cursor = conn.execute(query1, (mission_id,))
    all_cells = cursor.fetchall()
    
    print(f"\n[INFO] Cell IDs en TODA la mision (sin filtro de fecha):")
    print(f"Total Cell IDs unicos: {len(all_cells)}")
    
    # Cell IDs críticos que necesitamos
    critical_cells = ['51438', '53591', '56124', '63095', '51203', '2523']
    
    for cell_id, count in all_cells[:20]:  # Mostrar primeros 20
        marker = " <-- CRITICO" if cell_id in critical_cells else ""
        print(f"  - {cell_id}: {count} registros{marker}")
    
    # 2. Ver distribución temporal de los Cell IDs críticos
    print(f"\n[INFO] Distribucion temporal de Cell IDs criticos:")
    
    for cell in critical_cells:
        query2 = """
            SELECT 
                MIN(created_at) as first_seen,
                MAX(created_at) as last_seen,
                COUNT(*) as total
            FROM cellular_data
            WHERE mission_id = ?
            AND cell_id = ?
        """
        
        cursor = conn.execute(query2, (mission_id, cell))
        result = cursor.fetchone()
        
        if result and result[2] > 0:
            print(f"\n  Cell ID {cell}:")
            print(f"    Primera vez: {result[0]}")
            print(f"    Ultima vez:  {result[1]}")
            print(f"    Total:       {result[2]} registros")
        else:
            print(f"\n  Cell ID {cell}: NO ENCONTRADO en datos HUNTER")
    
    # 3. Ver qué Cell IDs están en el período específico de la UI
    print(f"\n[INFO] Cell IDs en el periodo de la UI (10:00 - 14:20):")
    
    query3 = """
        SELECT DISTINCT cell_id
        FROM cellular_data
        WHERE mission_id = ?
        AND created_at BETWEEN '2021-05-20 10:00:00' AND '2021-05-20 14:20:00'
        AND cell_id IN ('51438', '53591', '56124', '63095', '51203', '2523')
        ORDER BY cell_id
    """
    
    cursor = conn.execute(query3, (mission_id,))
    period_cells = [row[0] for row in cursor.fetchall()]
    
    print(f"Cell IDs criticos en periodo UI: {period_cells}")
    
    missing_cells = set(critical_cells) - set(period_cells)
    if missing_cells:
        print(f"\n[WARNING] Cell IDs FALTANTES en periodo UI:")
        for cell in sorted(missing_cells):
            print(f"  - {cell} NO esta en el periodo 10:00-14:20")
    
    # 4. Sugerir período óptimo
    print(f"\n[SUGERENCIA] Periodo optimo para capturar todos los Cell IDs criticos:")
    
    query4 = """
        SELECT 
            MIN(created_at) as earliest,
            MAX(created_at) as latest
        FROM cellular_data
        WHERE mission_id = ?
        AND cell_id IN ('51438', '53591', '56124', '63095', '51203', '2523')
    """
    
    cursor = conn.execute(query4, (mission_id,))
    optimal = cursor.fetchone()
    
    if optimal:
        print(f"  Fecha inicio sugerida: {optimal[0]}")
        print(f"  Fecha fin sugerida:    {optimal[1]}")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("FIN DE VERIFICACION L2")
    print("=" * 80)

if __name__ == "__main__":
    verify_hunter_data()