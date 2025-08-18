import sqlite3

conn = sqlite3.connect('kronos.db')

print('=== ANALISIS DETALLADO CELDA 16040 ===')

# 1. Ver todos los registros de 16040 en HUNTER
print('1. REGISTROS DE CELDA 16040 EN HUNTER:')
cursor = conn.execute('SELECT operator, tecnologia, lat, lon, punto FROM cellular_data WHERE mission_id = "mission_MPFRBNsb" AND cell_id = "16040"')
hunter_records = cursor.fetchall()
for i, row in enumerate(hunter_records, 1):
    print(f'   {i}. {row[0]} - {row[1]} - {row[2]}, {row[3]} - {row[4]}')

# 2. Verificar si 16040 de CLARO específicamente está en la intersección
print('\n2. CELDA 16040 DE CLARO EN HUNTER:')
cursor = conn.execute('SELECT COUNT(*) FROM cellular_data WHERE mission_id = "mission_MPFRBNsb" AND cell_id = "16040" AND operator = "CLARO"')
claro_hunter_count = cursor.fetchone()[0]
print(f'   - Registros CLARO en HUNTER: {claro_hunter_count}')

# 3. Ver las celdas CLARO en HUNTER que están en la intersección
print('\n3. INTERSECCION CLARO HUNTER vs LLAMADAS:')
cursor = conn.execute('SELECT DISTINCT cell_id FROM cellular_data WHERE mission_id = "mission_MPFRBNsb" AND operator = "CLARO" ORDER BY cell_id')
hunter_claro_cells = set([row[0] for row in cursor.fetchall()])

# Celdas de llamadas CLARO
call_cells = set()
for field in ['celda_origen', 'celda_destino', 'celda_objetivo']:
    cursor = conn.execute(f'SELECT DISTINCT {field} FROM operator_call_data WHERE mission_id = "mission_MPFRBNsb" AND operator = "CLARO" AND {field} IS NOT NULL')
    for row in cursor.fetchall():
        if row[0]:
            call_cells.add(str(row[0]).strip())

intersection = hunter_claro_cells.intersection(call_cells)
print(f'   - Celdas CLARO HUNTER: {len(hunter_claro_cells)}')
print(f'   - Celdas en llamadas CLARO: {len(call_cells)}')
print(f'   - Intersección: {len(intersection)}')
print(f'   - 16040 en intersección: {"16040" in intersection}')

if '16040' in intersection:
    print('   ✓ 16040 DEBERÍA aparecer en correlaciones')
else:
    print('   ✗ 16040 NO debería aparecer en correlaciones')

print(f'\n   Intersección completa: {sorted(list(intersection))}')

# 4. Verificar números objetivo que usan celda 16040
print('\n4. NUMEROS OBJETIVO QUE USAN CELDA 16040:')
target_numbers = ['3224274851', '3208611034', '3143534707', '3102715509', '3214161903']

for target in target_numbers:
    cursor = conn.execute(f'''
        SELECT COUNT(*) FROM operator_call_data 
        WHERE mission_id = "mission_MPFRBNsb" 
        AND (numero_origen LIKE "%{target}%" OR numero_destino LIKE "%{target}%" OR numero_objetivo LIKE "%{target}%")
        AND (celda_origen = "16040" OR celda_destino = "16040" OR celda_objetivo = "16040")
    ''')
    count = cursor.fetchone()[0]
    if count > 0:
        print(f'   - {target}: {count} registros usan celda 16040')

conn.close()