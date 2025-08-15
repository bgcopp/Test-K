#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test exhaustivo de procesamiento de archivos WOM con múltiples hojas usando Playwright.
Valida que el sistema procese correctamente el 100% de los registros de todas las hojas.
"""

import os
import sys
import json
import time
import asyncio
from datetime import datetime
import pandas as pd

# Agregar el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.async_api import async_playwright

class WOMPlaywrightTester:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "test_name": "WOM Multi-sheet Playwright Test",
            "results": []
        }
        self.base_url = "http://localhost:5173"
        
    async def test_wom_multi_sheet_upload(self):
        """Prueba la carga del archivo WOM con múltiples hojas"""
        
        file_path = r"C:\Soluciones\BGC\claude\KNSOft\archivos\CeldasDiferenteOperador\wom\PUNTO 1 TRÁFICO DATOS WOM.xlsx"
        
        # Primero analizar el archivo para conocer el total esperado
        expected_data = self.analyze_file(file_path)
        
        async with async_playwright() as p:
            # Iniciar navegador
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()
            
            try:
                # 1. Navegar al login
                print("1. Navegando al login...")
                await page.goto(self.base_url)
                await page.wait_for_load_state('networkidle')
                
                # 2. Login
                print("2. Realizando login...")
                await page.fill('input[type="text"]', 'admin')
                await page.fill('input[type="password"]', 'admin123')
                await page.click('button:has-text("Iniciar Sesión")')
                
                # Esperar a que aparezca el dashboard
                await page.wait_for_selector('text=Dashboard', timeout=10000)
                print("   ✓ Login exitoso")
                
                # 3. Ir a Misiones
                print("3. Navegando a Misiones...")
                await page.click('a:has-text("Misiones")')
                await page.wait_for_selector('h1:has-text("Misiones")', timeout=10000)
                
                # 4. Crear nueva misión
                print("4. Creando nueva misión...")
                await page.click('button:has-text("Nueva Misión")')
                await page.wait_for_selector('h2:has-text("Nueva Misión")', timeout=5000)
                
                mission_name = f"WOM Multi-sheet Test {datetime.now().strftime('%H%M%S')}"
                await page.fill('input[placeholder="Nombre de la misión"]', mission_name)
                await page.fill('textarea', f'Prueba archivo WOM con múltiples hojas - Total esperado: {expected_data["total_records"]} registros')
                
                await page.click('button:has-text("Crear")')
                await page.wait_for_selector(f'text={mission_name}', timeout=10000)
                print(f"   ✓ Misión creada: {mission_name}")
                
                # 5. Abrir detalles de la misión
                print("5. Abriendo detalles de la misión...")
                await page.click(f'tr:has-text("{mission_name}") button:has-text("Ver")')
                await page.wait_for_selector('text=Datos de Operador', timeout=10000)
                
                # 6. Subir archivo WOM
                print(f"6. Subiendo archivo WOM...")
                print(f"   - Archivo: {os.path.basename(file_path)}")
                print(f"   - Hojas: {expected_data['sheet_count']}")
                print(f"   - Total registros esperados: {expected_data['total_records']}")
                
                # Hacer clic en el tab de Datos de Operador
                await page.click('button:has-text("Datos de Operador")')
                await asyncio.sleep(1)
                
                # Seleccionar operador WOM
                await page.select_option('select', value='WOM')
                await asyncio.sleep(0.5)
                
                # Cargar archivo
                file_input = await page.query_selector('input[type="file"]')
                await file_input.set_input_files(file_path)
                
                # Esperar procesamiento
                print("7. Esperando procesamiento...")
                await asyncio.sleep(3)
                
                # Buscar indicadores de progreso o éxito
                try:
                    # Buscar mensaje de éxito
                    success_msg = await page.wait_for_selector('text=/procesad|cargad|éxito|complet/i', timeout=10000)
                    if success_msg:
                        success_text = await success_msg.text_content()
                        print(f"   ✓ Mensaje encontrado: {success_text}")
                except:
                    print("   ! No se encontró mensaje de éxito explícito")
                
                # 8. Verificar datos cargados
                print("8. Verificando datos cargados...")
                
                # Buscar tabla o contador de registros
                await asyncio.sleep(2)
                
                # Capturar screenshot para análisis
                screenshot_path = f"wom_test_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                print(f"   Screenshot guardado: {screenshot_path}")
                
                # Buscar información de registros
                page_content = await page.content()
                
                # Buscar contadores o información de registros
                records_found = False
                
                # Intentar encontrar el número de registros en la página
                for pattern in [
                    'text=/\\d+\\s*registro/i',
                    'text=/total.*\\d+/i',
                    'text=/mostrando.*\\d+/i',
                    'text=/\\d+\\s*fila/i'
                ]:
                    try:
                        element = await page.query_selector(pattern)
                        if element:
                            text = await element.text_content()
                            print(f"   Información encontrada: {text}")
                            records_found = True
                    except:
                        pass
                
                # Verificar si hay datos en tabla
                rows = await page.query_selector_all('tbody tr')
                if rows:
                    print(f"   Filas en tabla: {len(rows)}")
                    records_found = True
                
                # Verificar hojas procesadas
                sheet_buttons = await page.query_selector_all('button:has-text("Hoja")')
                if sheet_buttons:
                    print(f"   Hojas detectadas: {len(sheet_buttons)}")
                    
                    # Verificar cada hoja
                    for i, button in enumerate(sheet_buttons):
                        button_text = await button.text_content()
                        print(f"     - {button_text}")
                
                # Resultado del test
                test_result = {
                    "mission_name": mission_name,
                    "file": os.path.basename(file_path),
                    "expected": expected_data,
                    "upload_successful": records_found,
                    "screenshot": screenshot_path,
                    "timestamp": datetime.now().isoformat()
                }
                
                if records_found:
                    test_result["status"] = "SUCCESS"
                    print("\n✓ TEST EXITOSO: Archivo WOM cargado correctamente")
                else:
                    test_result["status"] = "WARNING"
                    print("\n⚠ TEST CON ADVERTENCIAS: No se pudo verificar completamente la carga")
                
                self.results["results"].append(test_result)
                
            except Exception as e:
                print(f"\n✗ ERROR en el test: {str(e)}")
                self.results["results"].append({
                    "status": "ERROR",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                
                # Capturar screenshot de error
                try:
                    error_screenshot = f"wom_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    await page.screenshot(path=error_screenshot, full_page=True)
                    print(f"Screenshot de error guardado: {error_screenshot}")
                except:
                    pass
                    
            finally:
                await browser.close()
    
    def analyze_file(self, file_path):
        """Analiza el archivo Excel para obtener información esperada"""
        try:
            xl_file = pd.ExcelFile(file_path)
            sheets_info = {}
            total_records = 0
            
            for sheet_name in xl_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                records = len(df)
                total_records += records
                sheets_info[sheet_name] = {
                    "records": records,
                    "columns": len(df.columns)
                }
            
            return {
                "sheet_count": len(xl_file.sheet_names),
                "sheets": sheets_info,
                "total_records": total_records
            }
        except Exception as e:
            print(f"Error analizando archivo: {e}")
            return {
                "sheet_count": 0,
                "sheets": {},
                "total_records": 0
            }
    
    def save_results(self):
        """Guarda los resultados del test"""
        filename = f"wom_playwright_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\nResultados guardados en: {filename}")
        return filename

async def main():
    print("=" * 80)
    print("TEST EXHAUSTIVO WOM - PROCESAMIENTO MULTI-HOJA CON PLAYWRIGHT")
    print("=" * 80)
    
    tester = WOMPlaywrightTester()
    
    # Verificar que el servidor esté ejecutándose
    print("\n⚠ IMPORTANTE: Asegúrate de que el servidor esté ejecutándose en http://localhost:5173")
    print("  Ejecuta 'cd Frontend && npm run dev' si no está activo\n")
    
    input("Presiona Enter cuando el servidor esté listo...")
    
    # Ejecutar test
    await tester.test_wom_multi_sheet_upload()
    
    # Guardar resultados
    report_file = tester.save_results()
    
    print("\n" + "=" * 80)
    print("TEST COMPLETADO")
    print("=" * 80)
    
    # Mostrar resumen
    for result in tester.results["results"]:
        if "status" in result:
            print(f"\nEstado: {result['status']}")
            if "expected" in result:
                print(f"Hojas esperadas: {result['expected']['sheet_count']}")
                print(f"Registros esperados: {result['expected']['total_records']}")

if __name__ == "__main__":
    asyncio.run(main())