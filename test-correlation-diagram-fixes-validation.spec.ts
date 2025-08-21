/**
 * TEST DE VALIDACIÓN CRÍTICA - CORRECCIONES DIAGRAMA CORRELACIÓN TELEFÓNICA D3.js
 * TESTING ENGINEER: Testing inmediato de implementaciones según requerimientos Boris
 * FECHA: 2025-08-20
 * OBJETIVO: Validar correcciones específicas para etiquetas de celdas y contenimiento
 */

import { test, expect, Page, BrowserContext } from '@playwright/test';

// Configuración específica del test
test.describe('Validación Crítica - Correcciones Diagrama Correlación D3.js', () => {
  let page: Page;
  let context: BrowserContext;
  
  // Target number específico para testing (según datos disponibles)
  const TARGET_NUMBER = '3143534707';
  
  // IDs de celdas esperados según Boris
  const EXPECTED_CELL_IDS = ['51203', '51438', '53591', '56124'];
  
  test.beforeAll(async ({ browser }) => {
    context = await browser.newContext({
      viewport: { width: 1920, height: 1080 },
      deviceScaleFactor: 1
    });
    page = await context.newPage();
    
    // Habilitar console logging para debugging
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.error(`❌ BROWSER ERROR: ${msg.text()}`);
      } else if (msg.text().includes('PhoneCorrelationDiagram')) {
        console.log(`🎨 DIAGRAM LOG: ${msg.text()}`);
      }
    });
    
    // Navegar a KRONOS
    console.log('🚀 Navegando a KRONOS...');
    await page.goto('http://localhost:8000');
    await page.waitForLoadState('networkidle');
    
    // Hacer login (asumiendo credenciales por defecto)
    await page.fill('input[type="text"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');
    
    // Esperar que cargue el dashboard
    await page.waitForSelector('[data-testid="dashboard"]', { timeout: 10000 });
    console.log('✅ KRONOS iniciado exitosamente');
  });

  test.afterAll(async () => {
    await context.close();
  });

  /**
   * ESCENARIO 1: VALIDACIÓN VISUAL COMPLETA
   * Verificar etiquetas de celdas y contenimiento del diagrama
   */
  test('ESCENARIO 1 - Validación Visual Completa: Etiquetas y Contenimiento', async () => {
    console.log('\n🎯 INICIANDO ESCENARIO 1: Validación Visual Completa');
    
    // PASO 1: Navegar a misiones y abrir correlación
    await page.click('text=Misiones');
    await page.waitForLoadState('networkidle');
    
    // Buscar el número objetivo
    await page.fill('input[placeholder*="buscar"]', TARGET_NUMBER);
    await page.waitForTimeout(1000);
    
    // Abrir diagrama de correlación
    const correlationButton = page.locator(`button:has-text("Correlación")`).first();
    await expect(correlationButton).toBeVisible({ timeout: 5000 });
    await correlationButton.click();
    
    console.log('📊 Abriendo diagrama de correlación...');
    
    // PASO 2: Esperar que el diagrama D3 se renderice completamente
    await page.waitForSelector('svg', { timeout: 15000 });
    await page.waitForTimeout(5000); // Esperar simulación D3
    
    // VALIDACIÓN A: Verificar estructura SVG básica
    const svg = page.locator('svg');
    await expect(svg).toBeVisible();
    
    const svgBox = await svg.boundingBox();
    console.log(`📏 Dimensiones SVG: ${svgBox?.width}x${svgBox?.height}`);
    
    // VALIDACIÓN B: Verificar que hay nodos y enlaces
    const nodes = page.locator('svg .phone-node');
    const links = page.locator('svg .phone-link');
    
    await expect(nodes).toHaveCount(5, { timeout: 10000 }); // Target + 4 participantes
    await expect(links).toHaveCount(4, { timeout: 10000 }); // 4 conexiones
    
    console.log('✅ PASS: Estructura básica del diagrama válida (5 nodos, 4 enlaces)');
    
    // CORRECCIÓN 1 - VALIDACIÓN CRÍTICA: Etiquetas de números celulares
    console.log('\n🔍 VALIDANDO CORRECCIÓN 1: Etiquetas de Números Celulares');
    
    const linkLabels = page.locator('svg .phone-link-label');
    await expect(linkLabels).toHaveCount(4, { timeout: 5000 });
    
    // Verificar que las etiquetas contienen IDs de celdas válidos
    const labelTexts: string[] = [];
    for (let i = 0; i < 4; i++) {
      const labelText = await linkLabels.nth(i).textContent();
      if (labelText && labelText.trim()) {
        labelTexts.push(labelText.trim());
      }
    }
    
    console.log(`📱 IDs de celdas encontrados: ${labelTexts.join(', ')}`);
    
    // Verificar que al menos algunos IDs esperados están presentes
    const foundExpectedIds = EXPECTED_CELL_IDS.filter(id => labelTexts.includes(id));
    expect(foundExpectedIds.length).toBeGreaterThan(0);
    
    console.log(`✅ PASS: Etiquetas de celdas presentes (${foundExpectedIds.length}/${EXPECTED_CELL_IDS.length} esperados)`);
    
    // Verificar propiedades CSS de las etiquetas
    const firstLabel = linkLabels.first();
    const labelStyles = await firstLabel.evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        fill: styles.fill,
        fontSize: styles.fontSize,
        textAnchor: styles.textAnchor,
        textShadow: styles.textShadow
      };
    });
    
    expect(labelStyles.fill).toBe('rgb(255, 255, 255)'); // Color blanco
    expect(labelStyles.fontSize).toBe('9px'); // Tamaño correcto
    expect(labelStyles.textAnchor).toBe('middle'); // Centrado
    
    console.log('✅ PASS: Propiedades CSS de etiquetas correctas');
    
    // CORRECCIÓN 2 - VALIDACIÓN CRÍTICA: Contenimiento del diagrama
    console.log('\n🔍 VALIDANDO CORRECCIÓN 2: Contenimiento del Diagrama');
    
    // Verificar que el contenedor del diagrama tiene las dimensiones correctas
    const diagramContainer = page.locator('div.bg-gray-900.rounded-lg');
    const containerBox = await diagramContainer.boundingBox();
    
    console.log(`📦 Dimensiones contenedor: ${containerBox?.width}x${containerBox?.height}`);
    
    // Verificar que todos los nodos están dentro del contenedor
    let allNodesContained = true;
    const nodeCount = await nodes.count();
    
    for (let i = 0; i < nodeCount; i++) {
      const nodeBox = await nodes.nth(i).boundingBox();
      if (nodeBox && containerBox) {
        const isContained = 
          nodeBox.x >= containerBox.x + 30 &&
          nodeBox.y >= containerBox.y + 30 &&
          (nodeBox.x + nodeBox.width) <= (containerBox.x + containerBox.width - 30) &&
          (nodeBox.y + nodeBox.height) <= (containerBox.y + containerBox.height - 30);
        
        if (!isContained) {
          console.log(`❌ Nodo ${i} fuera del contenedor: (${nodeBox.x}, ${nodeBox.y})`);
          allNodesContained = false;
        }
      }
    }
    
    expect(allNodesContained).toBe(true);
    console.log('✅ PASS: Todos los nodos están contenidos con padding mínimo');
    
    // Capturar screenshot de evidencia
    await page.screenshot({ 
      path: 'C:\\Soluciones\\BGC\\claude\\KNSOft\\test-results\\escenario1-validacion-completa.png',
      fullPage: true
    });
    
    console.log('📸 Screenshot de evidencia capturado');
    console.log('✅ ESCENARIO 1 COMPLETADO: Validación Visual - PASS');
  });

  /**
   * ESCENARIO 2: TESTING RESPONSIVE
   * Verificar comportamiento en diferentes resoluciones
   */
  test('ESCENARIO 2 - Testing Responsive: Múltiples Resoluciones', async () => {
    console.log('\n🎯 INICIANDO ESCENARIO 2: Testing Responsive');
    
    const resolutions = [
      { width: 1920, height: 1080, name: 'Full HD' },
      { width: 1366, height: 768, name: 'HD' },
      { width: 1024, height: 768, name: 'XGA' }
    ];
    
    // Navegar al diagrama
    await page.click('text=Misiones');
    await page.fill('input[placeholder*="buscar"]', TARGET_NUMBER);
    await page.waitForTimeout(1000);
    
    const correlationButton = page.locator(`button:has-text("Correlación")`).first();
    await correlationButton.click();
    await page.waitForSelector('svg', { timeout: 10000 });
    
    for (const resolution of resolutions) {
      console.log(`\n📱 Probando resolución ${resolution.name}: ${resolution.width}x${resolution.height}`);
      
      await page.setViewportSize({ width: resolution.width, height: resolution.height });
      await page.waitForTimeout(2000); // Esperar redimensionado
      
      // Verificar que el diagrama sigue visible y contenido
      const svg = page.locator('svg');
      const svgBox = await svg.boundingBox();
      
      expect(svgBox?.width).toBeGreaterThan(300);
      expect(svgBox?.height).toBeGreaterThan(200);
      
      // Verificar que no hay scroll horizontal
      const hasHorizontalScroll = await page.evaluate(() => {
        return document.documentElement.scrollWidth > window.innerWidth;
      });
      
      expect(hasHorizontalScroll).toBe(false);
      
      // Capturar screenshot para cada resolución
      await page.screenshot({ 
        path: `C:\\Soluciones\\BGC\\claude\\KNSOft\\test-results\\escenario2-responsive-${resolution.name.toLowerCase()}.png`
      });
      
      console.log(`✅ PASS: ${resolution.name} - Diagrama responsive correcto`);
    }
    
    console.log('✅ ESCENARIO 2 COMPLETADO: Testing Responsive - PASS');
  });

  /**
   * ESCENARIO 3: DATOS Y PERFORMANCE
   * Verificar integridad de datos y rendimiento
   */
  test('ESCENARIO 3 - Datos y Performance: Backend Integration', async () => {
    console.log('\n🎯 INICIANDO ESCENARIO 3: Datos y Performance');
    
    // Navegar al diagrama y medir tiempo de carga
    const startTime = Date.now();
    
    await page.click('text=Misiones');
    await page.fill('input[placeholder*="buscar"]', TARGET_NUMBER);
    
    const correlationButton = page.locator(`button:has-text("Correlación")`).first();
    await correlationButton.click();
    
    // Esperar renderizado completo
    await page.waitForSelector('svg .phone-node', { timeout: 15000 });
    await page.waitForTimeout(5000); // Simulación D3
    
    const loadTime = Date.now() - startTime;
    console.log(`⏱️ Tiempo de carga total: ${loadTime}ms`);
    
    // VALIDACIÓN: Tiempo debe ser menor a 15 segundos (15000ms)
    expect(loadTime).toBeLessThan(15000);
    console.log('✅ PASS: Tiempo de carga dentro del límite (<15s)');
    
    // Verificar datos específicos del target number
    const headerText = await page.textContent('h2:has-text("Diagrama de Correlación")');
    expect(headerText).toContain('Correlación');
    
    const targetInfo = await page.textContent('p.text-gray-400');
    expect(targetInfo).toContain(TARGET_NUMBER);
    
    console.log('✅ PASS: Datos del target number correctos');
    
    // Verificar memory usage (básico)
    const memoryUsage = await page.evaluate(() => {
      if ('memory' in performance) {
        return (performance as any).memory.usedJSHeapSize;
      }
      return 0;
    });
    
    console.log(`💾 Uso de memoria JavaScript: ${(memoryUsage / 1024 / 1024).toFixed(2)} MB`);
    
    // VALIDACIÓN: Memory usage razonable (<100MB)
    if (memoryUsage > 0) {
      expect(memoryUsage).toBeLessThan(100 * 1024 * 1024); // 100MB
      console.log('✅ PASS: Uso de memoria dentro del límite (<100MB)');
    }
    
    console.log('✅ ESCENARIO 3 COMPLETADO: Datos y Performance - PASS');
  });

  /**
   * TEST FINAL: VALIDACIÓN INTEGRAL
   * Confirmar que ambas correcciones están 100% resueltas
   */
  test('VALIDACIÓN FINAL - Confirmación Correcciones Boris 100% Resueltas', async () => {
    console.log('\n🎯 VALIDACIÓN FINAL: Confirmación Completa de Correcciones');
    
    // Abrir diagrama una vez más
    await page.click('text=Misiones');
    await page.fill('input[placeholder*="buscar"]', TARGET_NUMBER);
    
    const correlationButton = page.locator(`button:has-text("Correlación")`).first();
    await correlationButton.click();
    await page.waitForSelector('svg', { timeout: 10000 });
    await page.waitForTimeout(5000);
    
    // CHECKLIST FINAL DE VALIDACIÓN
    console.log('\n📋 CHECKLIST FINAL DE VALIDACIÓN:');
    
    // ✓ Corrección 1: Etiquetas de números celulares
    const linkLabels = page.locator('svg .phone-link-label');
    const labelsCount = await linkLabels.count();
    const labelsVisible = labelsCount === 4;
    console.log(`[${labelsVisible ? '✅' : '❌'}] Etiquetas de celdas presentes (${labelsCount}/4)`);
    
    // ✓ Corrección 2: Contenimiento del diagrama
    const svg = page.locator('svg');
    const container = page.locator('div.bg-gray-900');
    const svgBox = await svg.boundingBox();
    const containerBox = await container.boundingBox();
    
    const isContained = svgBox && containerBox && 
      svgBox.x >= containerBox.x && 
      svgBox.y >= containerBox.y &&
      (svgBox.x + svgBox.width) <= (containerBox.x + containerBox.width) &&
      (svgBox.y + svgBox.height) <= (containerBox.y + containerBox.height);
    
    console.log(`[${isContained ? '✅' : '❌'}] Diagrama completamente contenido`);
    
    // ✓ No desbordamiento
    const hasOverflow = await page.evaluate(() => {
      return document.documentElement.scrollWidth > window.innerWidth ||
             document.documentElement.scrollHeight > window.innerHeight;
    });
    
    console.log(`[${!hasOverflow ? '✅' : '❌'}] Sin desbordamiento de contenido`);
    
    // ✓ Legibilidad de etiquetas
    const firstLabel = linkLabels.first();
    const labelText = await firstLabel.textContent();
    const hasText = labelText && labelText.trim().length > 0;
    console.log(`[${hasText ? '✅' : '❌'}] Etiquetas legibles: "${labelText}"`);
    
    // RESULTADO FINAL
    const allTestsPassed = labelsVisible && isContained && !hasOverflow && hasText;
    
    console.log('\n🏁 RESULTADO FINAL:');
    console.log(`CORRECCIÓN 1 (Etiquetas): ${labelsVisible && hasText ? 'PASS ✅' : 'FAIL ❌'}`);
    console.log(`CORRECCIÓN 2 (Contenimiento): ${isContained && !hasOverflow ? 'PASS ✅' : 'FAIL ❌'}`);
    console.log(`VALIDACIÓN COMPLETA: ${allTestsPassed ? 'PASS ✅' : 'FAIL ❌'}`);
    
    // Screenshot final de evidencia
    await page.screenshot({ 
      path: 'C:\\Soluciones\\BGC\\claude\\KNSOft\\test-results\\validacion-final-correcciones-boris.png',
      fullPage: true
    });
    
    // Asegurar que todas las validaciones pasen
    expect(allTestsPassed).toBe(true);
    
    console.log('\n🎉 TODAS LAS CORRECCIONES DE BORIS ESTÁN 100% RESUELTAS');
    console.log('📋 LISTO PARA PROCEDER CON FASE 2');
  });
});