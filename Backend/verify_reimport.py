import sqlite3

conn = sqlite3.connect('kronos.db')

print('=== VERIFICACION DE RE-IMPORTACION ===')

# 1. Estadísticas generales
cursor = conn.execute('SELECT COUNT(*) FROM cellular_data WHERE mission_id = "mission_MPFRBNsb"')
total_in_db = cursor.fetchone()[0]

cursor = conn.execute('SELECT COUNT(DISTINCT cell_id) FROM cellular_data WHERE mission_id = "mission_MPFRBNsb"')
unique_cells_db = cursor.fetchone()[0]

print(f'Total registros en BD: {total_in_db}')
print(f'Cell IDs unicos en BD: {unique_cells_db}')
print(f'Cell IDs unicos esperados: 57')

# 2. Verificar Cell IDs críticos que DEBEN estar
print('\nVerificando Cell IDs criticos que DEBEN estar:')
expected_cells = ['1535', '51203', '51438', '53591', '56124', '77924']

for cell in expected_cells:
    cursor = conn.execute('SELECT COUNT(*) FROM cellular_data WHERE mission_id = "mission_MPFRBNsb" AND cell_id = ?', (cell,))
    count = cursor.fetchone()[0]
    status = "OK" if count > 0 else "FALTA"
    print(f'  [{status}] {cell}: {count} registros')

# 3. Verificar que celdas corruptas NO estén
print('\nVerificando que celdas corruptas NO esten:')
corrupt_cells = ['16040', '16477', '16478']

for cell in corrupt_cells:
    cursor = conn.execute('SELECT COUNT(*) FROM cellular_data WHERE mission_id = "mission_MPFRBNsb" AND cell_id = ?', (cell,))
    count = cursor.fetchone()[0]
    status = "OK" if count == 0 else "ERROR"
    print(f'  [{status}] {cell}: {count} registros (debe ser 0)')

# 4. Listar todos los Cell IDs para comparación
print('\nTodos los Cell IDs en BD:')
cursor = conn.execute('SELECT DISTINCT cell_id FROM cellular_data WHERE mission_id = "mission_MPFRBNsb" ORDER BY cell_id')
bd_cells = [row[0] for row in cursor.fetchall()]
print(f'BD: {bd_cells}')

# Cell IDs del archivo original
archivo_cells = ['10111', '10248', '10263', '10753', '11713', '118', '12252', '12283', '128164613', '130618373', '130618376', '130660356', '13922', '1532', '1535', '153663690', '1537', '153721240', '153721289', '153881497', '1604042', '16104', '1647820', '17403', '20137', '20248', '20249', '20251', '202647', '22504', '24310', '24841', '2525', '26948', '27073', '27473', '34088', '34859', '35582', '36709', '41716', '41719', '42282', '43924', '43925', '43927', '43928', '44753', '51203', '51438', '53591', '56124', '58480', '58659', '6159', '64065', '77924']

print(f'\nArchivo: {sorted(archivo_cells)}')

# 5. Comparación final
bd_set = set(bd_cells)
archivo_set = set(archivo_cells)

solo_en_bd = bd_set - archivo_set
solo_en_archivo = archivo_set - bd_set
coincidencias = bd_set.intersection(archivo_set)

print(f'\nCOMPARACION FINAL:')
print(f'  Coincidencias: {len(coincidencias)}/57')
print(f'  Solo en BD: {sorted(list(solo_en_bd))}')
print(f'  Solo en archivo: {sorted(list(solo_en_archivo))}')

# Resultado
if len(solo_en_bd) == 0 and len(solo_en_archivo) == 0:
    print('\n[EXITO] RE-IMPORTACION PERFECTA - DATOS CORRECTOS')
else:
    print('\n[ERROR] Aun hay diferencias entre BD y archivo')

conn.close()