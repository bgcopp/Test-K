/**
 * TEST RÁPIDO DE VALIDACIÓN - CORRECCIONES CRÍTICAS DIAGRAMA D3.js
 * Testing Engineer: Validación inmediata de implementaciones Boris
 */

import { test, expect } from '@playwright/test';

test('Validación Rápida - Correcciones Diagrama Correlación', async ({ page }) => {
  console.log('🚀 INICIANDO VALIDACIÓN RÁPIDA DE CORRECCIONES');
  
  // Configurar timeouts extendidos
  test.setTimeout(120000); // 2 minutos
  
  try {
    // PASO 1: Navegar a KRONOS
    console.log('📍 Navegando a KRONOS...');
    await page.goto('http://localhost:8000', { 
      waitUntil: 'networkidle',
      timeout: 30000 
    });
    
    // PASO 2: Login rápido
    console.log('🔑 Realizando login...');
    await page.fill('input[type="text"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');
    
    // Esperar dashboard
    await page.waitForSelector('text=Dashboard', { timeout: 15000 });
    console.log('✅ Login exitoso');
    
    // PASO 3: Navegar a Misiones
    console.log('📊 Navegando a Misiones...');
    await page.click('text=Misiones');
    await page.waitForLoadState('networkidle');
    
    // PASO 4: Buscar target específico
    const targetNumber = '3143534707';
    console.log(`🔍 Buscando target: ${targetNumber}`);
    
    const searchInput = page.locator('input[placeholder*="buscar"], input[type="text"]').first();
    await searchInput.fill(targetNumber);
    await page.waitForTimeout(2000);
    
    // PASO 5: Abrir diagrama de correlación
    console.log('📈 Abriendo diagrama de correlación...');
    const correlationBtn = page.locator('button:has-text("Correlación"), button:has-text("Ver Correlación")').first();
    await correlationBtn.click({ timeout: 10000 });
    
    // PASO 6: Esperar renderizado D3
    console.log('🎨 Esperando renderizado del diagrama D3...');
    await page.waitForSelector('svg', { timeout: 20000 });
    await page.waitForTimeout(8000); // Tiempo para simulación D3
    
    // VALIDACIÓN 1: Verificar estructura básica
    console.log('\n🔍 VALIDACIÓN 1: Estructura básica del diagrama');
    
    const svg = page.locator('svg');
    await expect(svg).toBeVisible();
    
    const nodes = page.locator('svg .phone-node, svg circle[class*="node"]');
    const links = page.locator('svg .phone-link, svg line[class*="link"]');
    
    const nodeCount = await nodes.count();
    const linkCount = await links.count();
    
    console.log(`📊 Nodos encontrados: ${nodeCount}`);
    console.log(`🔗 Enlaces encontrados: ${linkCount}`);
    
    expect(nodeCount).toBeGreaterThan(0);
    expect(linkCount).toBeGreaterThan(0);
    
    // VALIDACIÓN 2: CORRECCIÓN 1 - Etiquetas de celdas
    console.log('\n🔍 VALIDACIÓN 2: CORRECCIÓN 1 - Etiquetas de números celulares');
    
    // Buscar etiquetas de texto en enlaces
    const linkLabels = page.locator('svg text[class*="label"], svg .phone-link-label');
    const labelCount = await linkLabels.count();
    
    console.log(`🏷️ Etiquetas encontradas: ${labelCount}`);
    
    if (labelCount > 0) {
      const firstLabelText = await linkLabels.first().textContent();
      console.log(`📱 Texto primera etiqueta: "${firstLabelText}"`);
      
      // Verificar propiedades visuales
      const labelStyles = await linkLabels.first().evaluate(el => ({
        fill: window.getComputedStyle(el).fill,
        fontSize: window.getComputedStyle(el).fontSize,
        display: window.getComputedStyle(el).display
      }));
      
      console.log(`🎨 Estilos etiqueta:`, labelStyles);
      expect(labelStyles.display).not.toBe('none');
      
      console.log('✅ CORRECCIÓN 1 VALIDADA: Etiquetas de celdas presentes');
    } else {
      console.log('⚠️ No se encontraron etiquetas - revisar implementación');
    }
    
    // VALIDACIÓN 3: CORRECCIÓN 2 - Contenimiento
    console.log('\n🔍 VALIDACIÓN 3: CORRECCIÓN 2 - Contenimiento del diagrama');
    
    const svgBox = await svg.boundingBox();
    const container = page.locator('.bg-gray-900, [class*="diagram-container"]').first();
    const containerBox = await container.boundingBox();
    
    console.log(`📦 SVG: ${svgBox?.width}x${svgBox?.height}`);
    console.log(`📦 Container: ${containerBox?.width}x${containerBox?.height}`);
    
    if (svgBox && containerBox) {
      const isContained = 
        svgBox.x >= containerBox.x - 10 &&
        svgBox.y >= containerBox.y - 10 &&
        (svgBox.x + svgBox.width) <= (containerBox.x + containerBox.width + 10) &&
        (svgBox.y + svgBox.height) <= (containerBox.y + containerBox.height + 10);
      
      console.log(`📐 Diagrama contenido: ${isContained ? 'SÍ' : 'NO'}`);
      
      if (isContained) {
        console.log('✅ CORRECCIÓN 2 VALIDADA: Diagrama correctamente contenido');
      } else {
        console.log('⚠️ Diagrama podría tener problemas de contenimiento');
      }
    }
    
    // VALIDACIÓN 4: No desbordamiento
    const hasOverflow = await page.evaluate(() => {
      return document.documentElement.scrollWidth > window.innerWidth ||
             document.documentElement.scrollHeight > window.innerHeight;
    });
    
    console.log(`📏 Desbordamiento detectado: ${hasOverflow ? 'SÍ' : 'NO'}`);
    
    if (!hasOverflow) {
      console.log('✅ Sin desbordamiento - Layout responsivo correcto');
    }
    
    // CAPTURA DE EVIDENCIA
    console.log('\n📸 Capturando screenshot de evidencia...');
    await page.screenshot({ 
      path: 'C:\\Soluciones\\BGC\\claude\\KNSOft\\validation-evidence.png',
      fullPage: true
    });
    
    // RESULTADO FINAL
    console.log('\n🏁 RESULTADO DE VALIDACIÓN:');
    console.log(`✅ Diagrama renderizado correctamente`);
    console.log(`✅ Estructura D3 válida (${nodeCount} nodos, ${linkCount} enlaces)`);
    console.log(`${labelCount > 0 ? '✅' : '⚠️'} Etiquetas de celdas: ${labelCount > 0 ? 'IMPLEMENTADAS' : 'PENDIENTES'}`);
    console.log(`${!hasOverflow ? '✅' : '⚠️'} Contenimiento: ${!hasOverflow ? 'CORRECTO' : 'REVISAR'}`);
    
    const overallSuccess = nodeCount > 0 && linkCount > 0 && !hasOverflow;
    console.log(`\n🎯 VALIDACIÓN GENERAL: ${overallSuccess ? 'PASS ✅' : 'REVISAR ⚠️'}`);
    
    if (overallSuccess) {
      console.log('🎉 CORRECCIONES BORIS VALIDADAS EXITOSAMENTE');
      console.log('🚀 LISTO PARA CONTINUAR CON FASE 2');
    }
    
  } catch (error) {
    console.error('❌ ERROR EN VALIDACIÓN:', error);
    
    // Captura de error para debugging
    await page.screenshot({ 
      path: 'C:\\Soluciones\\BGC\\claude\\KNSOft\\validation-error.png',
      fullPage: true
    });
    
    throw error;
  }
});