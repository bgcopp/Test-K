import sqlite3

conn = sqlite3.connect('kronos.db')

# Celdas que coinciden entre HUNTER CLARO y llamadas
hunter_claro_query = 'SELECT DISTINCT cell_id FROM cellular_data WHERE mission_id = "mission_MPFRBNsb" AND operator = "CLARO"'
cursor = conn.execute(hunter_claro_query)
hunter_claro_cells = set([row[0] for row in cursor.fetchall()])

call_cells = set()
for field in ['celda_origen', 'celda_destino', 'celda_objetivo']:
    cursor = conn.execute(f'SELECT DISTINCT {field} FROM operator_call_data WHERE mission_id = "mission_MPFRBNsb" AND {field} IS NOT NULL')
    for row in cursor.fetchall():
        if row[0]:
            call_cells.add(str(row[0]).strip())

intersection = hunter_claro_cells.intersection(call_cells)
print(f'Interseccion CLARO: {sorted(list(intersection))}')

# Verificar números objetivo
target_numbers = ['3224274851', '3208611034', '3143534707', '3102715509', '3214161903']

print('\n=== VERIFICACION NUMEROS OBJETIVO ===')
for target in target_numbers:
    # Buscar celdas del número objetivo
    cursor = conn.execute(f'''
        SELECT DISTINCT celda_origen, celda_destino, celda_objetivo 
        FROM operator_call_data 
        WHERE mission_id = "mission_MPFRBNsb" 
        AND (numero_origen LIKE "%{target}%" OR numero_destino LIKE "%{target}%" OR numero_objetivo LIKE "%{target}%")
    ''')
    
    target_cells = set()
    for row in cursor.fetchall():
        for cell in row:
            if cell:
                target_cells.add(str(cell).strip())
    
    # Intersección con celdas CLARO HUNTER
    target_intersection = target_cells.intersection(intersection)
    
    print(f'{target}:')
    print(f'  - Celdas del numero: {sorted(list(target_cells))}')
    print(f'  - Interseccion con HUNTER CLARO: {sorted(list(target_intersection))}')

conn.close()