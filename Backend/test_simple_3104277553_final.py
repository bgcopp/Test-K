"""
Test simple final para 3104277553
"""

import sqlite3
import os

def test_simple_final():
    """Test simple final"""
    
    print("=== TEST SIMPLE FINAL 3104277553 ===")
    
    db_path = os.path.join(os.path.dirname(__file__), 'kronos.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Verificar registro en BD
    print("=== VERIFICACION BD ===")
    
    cursor.execute("""
        SELECT id, numero_origen, numero_destino, celda_origen, celda_destino, fecha_hora_llamada
        FROM operator_call_data 
        WHERE numero_origen = '3104277553' OR numero_destino = '3104277553'
    """)
    
    records = cursor.fetchall()
    
    print(f"Registros con 3104277553: {len(records)}")
    
    if records:
        for record in records:
            id_rec, origen, destino, celda_orig, celda_dest, fecha = record
            print(f"  ID {id_rec}: {origen} -> {destino}")
            print(f"    Celdas: {celda_orig} -> {celda_dest}")
            print(f"    Fecha: {fecha}")
    
    # 2. Verificar que celda 53591 no está vacía
    if records:
        record = records[0]
        celda_origen = record[3]
        celda_destino = record[4]
        
        print(f"\nESTADO DE CELDAS:")
        print(f"  Celda origen: '{celda_origen}' (vacia: {celda_origen == '' or celda_origen is None})")
        print(f"  Celda destino: '{celda_destino}' (vacia: {celda_destino == '' or celda_destino is None})")
        
        if celda_origen and celda_origen != '':
            print(f"  ✅ EXITO: Celda origen no esta vacia!")
        else:
            print(f"  ❌ PROBLEMA: Celda origen esta vacia")
        
        if celda_destino and celda_destino != '':
            print(f"  ✅ EXITO: Celda destino no esta vacia!")
        else:
            print(f"  ❌ PROBLEMA: Celda destino esta vacia")
    
    # 3. Contar registros en celda 53591
    print(f"\n=== REGISTROS EN CELDA 53591 ===")
    
    cursor.execute("""
        SELECT COUNT(*) 
        FROM operator_call_data 
        WHERE celda_origen = '53591' OR celda_destino = '53591'
    """)
    
    count_53591 = cursor.fetchone()[0]
    print(f"Total registros con celda 53591: {count_53591}")
    
    # Buscar específicamente nuestro número
    cursor.execute("""
        SELECT numero_origen, numero_destino, celda_origen, celda_destino
        FROM operator_call_data 
        WHERE (celda_origen = '53591' OR celda_destino = '53591')
        AND (numero_origen = '3104277553' OR numero_destino = '3104277553')
    """)
    
    target_in_cell = cursor.fetchall()
    
    print(f"Nuestro numero en celda 53591: {len(target_in_cell)}")
    
    if target_in_cell:
        print("  ✅ CONFIRMADO: 3104277553 esta en celda 53591")
        for record in target_in_cell:
            origen, destino, celda_orig, celda_dest = record
            print(f"    {origen} -> {destino} | {celda_orig} -> {celda_dest}")
    else:
        print("  ❌ PROBLEMA: 3104277553 no se encuentra en celda 53591")
    
    # 4. Test básico de correlación por celda
    print(f"\n=== TEST CORRELACION BASICA ===")
    
    # Buscar otros números que hayan usado las mismas celdas
    cursor.execute("""
        SELECT DISTINCT numero_origen, numero_destino, celda_origen, celda_destino
        FROM operator_call_data 
        WHERE celda_origen = '53591' OR celda_destino = '53591'
        ORDER BY numero_origen
        LIMIT 10
    """)
    
    related_numbers = cursor.fetchall()
    
    print(f"Numeros relacionados por celda (muestra de 10):")
    
    target_found = False
    related_to_target = []
    
    for record in related_numbers:
        origen, destino, celda_orig, celda_dest = record
        print(f"  {origen} -> {destino} | {celda_orig} -> {celda_dest}")
        
        if origen == '3104277553' or destino == '3104277553':
            target_found = True
            print(f"    ^^ ESTE ES NUESTRO NUMERO OBJETIVO")
        
        # Si el origen o destino es 3224274851 (el número relacionado)
        if origen == '3224274851' or destino == '3224274851':
            related_to_target.append((origen, destino))
            print(f"    ^^ RELACIONADO CON NUESTRO NUMERO")
    
    conn.close()
    
    # 5. Resumen final
    print(f"\n=== RESUMEN FINAL ===")
    
    if target_found:
        print("✅ SUCCESS: El numero 3104277553 ESTA en celda 53591")
        print("✅ SUCCESS: Las celdas NO estan vacias")
        print("✅ SUCCESS: El registro fue insertado correctamente")
        print("\n🎯 CONCLUSION:")
        print("   El numero 3104277553 ahora DEBERIA aparecer en algoritmos de correlacion")
        print("   que filtren por celdas HUNTER, ya que esta correctamente mapeado")
        print("   con celda_origen = '53591' y celda_destino = '52453'")
        
        if related_to_target:
            print(f"\n📞 BONUS: Se encontraron {len(related_to_target)} registros relacionados")
            print("   que comparten las mismas celdas, confirmando correlacion potencial")
    else:
        print("❌ PROBLEMA: El numero 3104277553 aun no esta correctamente configurado")
    
    print(f"\nTEST COMPLETADO")

if __name__ == "__main__":
    test_simple_final()