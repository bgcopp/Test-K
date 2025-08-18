"""
Test final para verificar que 3104277553 ahora aparece en algoritmo de correlación
"""

import sys
import os
import sqlite3

# Agregar el directorio de servicios al path  
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.correlation_analysis_service import CorrelationAnalysisService

def test_correlacion_3104277553():
    """Test final del algoritmo de correlación con 3104277553"""
    
    print("=== TEST FINAL CORRELACION 3104277553 ===")
    print("=" * 50)
    
    # 1. Verificar que el número está en la base de datos
    print("=== VERIFICACION BASE DE DATOS ===")
    
    db_path = os.path.join(os.path.dirname(__file__), 'kronos.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, numero_origen, numero_destino, celda_origen, celda_destino
        FROM operator_call_data 
        WHERE numero_origen = '3104277553' OR numero_destino = '3104277553'
    """)
    
    records = cursor.fetchall()
    
    if records:
        print(f"CONFIRMADO: {len(records)} registros con 3104277553 en BD")
        for record in records:
            id_rec, origen, destino, celda_orig, celda_dest = record
            print(f"  ID {id_rec}: {origen} -> {destino} | Celdas: {celda_orig} -> {celda_dest}")
    else:
        print("ERROR: No se encontraron registros con 3104277553")
        conn.close()
        return
    
    conn.close()
    
    # 2. Probar algoritmo de correlación
    print(f"\n=== PROBANDO ALGORITMO DE CORRELACION ===")
    
    try:
        # Inicializar servicio de correlación
        correlation_service = CorrelationAnalysisService()
        
        # Probar con diferentes números objetivo que sabemos están relacionados
        target_numbers = ['3104277553', '3224274851']
        
        for target_number in target_numbers:
            print(f"\n--- Probando correlación para {target_number} ---")
            
            try:
                # Ejecutar análisis de correlación
                result = correlation_service.analyze_correlations(
                    mission_id='mission_MPFRBNsb',
                    target_numbers=[target_number],
                    start_date='2021-05-20',
                    end_date='2021-05-20',
                    algorithm='hunter_validated'  # Usar el algoritmo hunter validated
                )
                
                print(f"Resultado para {target_number}:")
                
                if result and 'correlations' in result:
                    correlations = result['correlations']
                    
                    if correlations and len(correlations) > 0:
                        print(f"  ✅ CORRELACIONES ENCONTRADAS: {len(correlations)}")
                        
                        # Buscar específicamente el número 3104277553 en los resultados
                        found_3104277553 = False
                        
                        for corr in correlations[:10]:  # Mostrar las primeras 10
                            numero_corr = corr.get('numero', '')
                            confidence = corr.get('confidence', 0)
                            call_count = corr.get('call_count', 0)
                            
                            print(f"    - {numero_corr} (confidence: {confidence}, calls: {call_count})")
                            
                            if numero_corr == '3104277553':
                                found_3104277553 = True
                                print(f"      🎯 ENCONTRADO 3104277553 EN CORRELACIONES!")
                        
                        if target_number != '3104277553' and found_3104277553:
                            print(f"  🎯 ÉXITO: 3104277553 aparece en correlaciones de {target_number}")
                        elif target_number == '3104277553':
                            print(f"  ℹ️  Correlaciones para el número objetivo mismo")
                            
                    else:
                        print(f"  ❌ NO SE ENCONTRARON CORRELACIONES")
                else:
                    print(f"  ❌ RESULTADO VACÍO O INVÁLIDO")
                    
            except Exception as e:
                print(f"  ❌ ERROR en correlación para {target_number}: {e}")
                
    except Exception as e:
        print(f"ERROR inicializando servicio de correlación: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. Test específico de búsqueda por celda
    print(f"\n=== TEST BUSQUEDA POR CELDA 53591 ===")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Buscar todos los números que han usado la celda 53591
    cursor.execute("""
        SELECT DISTINCT numero_origen as numero, 'origen' as tipo
        FROM operator_call_data 
        WHERE celda_origen = '53591'
        UNION
        SELECT DISTINCT numero_destino as numero, 'destino' as tipo
        FROM operator_call_data 
        WHERE celda_destino = '53591'
        ORDER BY numero
    """)
    
    numeros_celda_53591 = cursor.fetchall()
    
    print(f"Números únicos que han usado celda 53591: {len(numeros_celda_53591)}")
    
    target_found_in_cell = False
    for numero, tipo in numeros_celda_53591:
        if numero == '3104277553':
            print(f"  🎯 CONFIRMADO: 3104277553 encontrado como {tipo} en celda 53591")
            target_found_in_cell = True
        elif numero == '3224274851':
            print(f"  📞 RELACIONADO: 3224274851 encontrado como {tipo} en celda 53591")
    
    if target_found_in_cell:
        print("✅ El número 3104277553 ESTÁ CORRECTAMENTE en celda 53591")
    else:
        print("❌ El número 3104277553 NO se encontró en celda 53591")
    
    conn.close()
    
    print(f"\n" + "=" * 50)
    print("TEST FINAL COMPLETADO")
    
    if target_found_in_cell:
        print("🎯 CONCLUSIÓN: El número 3104277553 debería aparecer en correlaciones")
    else:
        print("❌ PROBLEMA: El número aún no está correctamente configurado")

if __name__ == "__main__":
    test_correlacion_3104277553()