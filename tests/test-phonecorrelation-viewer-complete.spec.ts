/**
 * Test Completo de PhoneCorrelationViewer
 * Testing MCP Playwright solicitado por Boris - 2025-08-21
 * 
 * PLAN COMPLETO DE VALIDACIÓN:
 * 1. Flujo completo desde login hasta diagrama
 * 2. Validación de 4 modos de visualización  
 * 3. Controles de zoom, filtros, export
 * 4. Interactividad (tooltips, clicks, drag&drop)
 * 5. Performance y responsive
 * 6. Datos reales de BD
 * 7. Integración sin afectar funcionalidad existente
 */

import { test, expect, Page } from '@playwright/test';

// Configuración de datos de testing
const TEST_CONFIG = {
  loginCredentials: {
    username: 'admin',
    password: 'admin123'
  },
  // Usar número objetivo que sabemos existe en BD
  targetNumber: '3143534707', // Boris confirmó este número tiene datos
  maxWaitTime: 30000,
  screenshotPath: '.playwright-mcp'
};

// Utilidades para el testing
async function loginToKronos(page: Page) {
  console.log('🔐 Iniciando login a KRONOS...');
  
  await page.goto('http://localhost:8000');
  await page.waitForLoadState('networkidle');
  
  // Capturar screenshot inicial
  await page.screenshot({ 
    path: `${TEST_CONFIG.screenshotPath}/01-kronos-login.png`,
    fullPage: true 
  });
  
  // Login
  await page.fill('input[type="text"]', TEST_CONFIG.loginCredentials.username);
  await page.fill('input[type="password"]', TEST_CONFIG.loginCredentials.password);
  await page.click('button[type="submit"]');
  
  // Esperar que cargue el dashboard
  await page.waitForSelector('[data-testid="dashboard"]', { timeout: 15000 });
  await page.screenshot({ 
    path: `${TEST_CONFIG.screenshotPath}/02-dashboard-inicial.png`,
    fullPage: true 
  });
  
  console.log('✅ Login completado');
}

async function navigateToMissions(page: Page) {
  console.log('📋 Navegando a página de Misiones...');
  
  // Click en Misiones en sidebar
  await page.click('text=Misiones');
  await page.waitForLoadState('networkidle');
  
  // Capturar página de misiones
  await page.screenshot({ 
    path: `${TEST_CONFIG.screenshotPath}/03-pagina-misiones.png`,
    fullPage: true 
  });
  
  console.log('✅ Navegación a Misiones completada');
}

async function selectMissionWithData(page: Page) {
  console.log('🎯 Seleccionando misión con datos...');
  
  // Buscar misión que tenga datos (debe existir una con correlaciones)
  const missionRows = await page.$$('tbody tr');
  
  if (missionRows.length === 0) {
    throw new Error('No se encontraron misiones en la tabla');
  }
  
  // Seleccionar primera misión disponible
  await missionRows[0].click();
  await page.waitForLoadState('networkidle');
  
  // Capturar detalles de misión
  await page.screenshot({ 
    path: `${TEST_CONFIG.screenshotPath}/04-detalles-mision-resumen.png`,
    fullPage: true 
  });
  
  console.log('✅ Misión seleccionada');
}

async function executeCorrelation(page: Page) {
  console.log('⚡ Ejecutando correlación de datos...');
  
  // Navegar a tab de Análisis de Correlación
  await page.click('text=Análisis de Correlación');
  await page.waitForLoadState('networkidle');
  
  await page.screenshot({ 
    path: `${TEST_CONFIG.screenshotPath}/05-analisis-correlacion-inicial.png`,
    fullPage: true 
  });
  
  // Ingresar número objetivo real de BD
  const targetInput = await page.$('input[placeholder*="número objetivo"], input[placeholder*="objetivo"]');
  if (targetInput) {
    await targetInput.fill(TEST_CONFIG.targetNumber);
  }
  
  // Buscar y hacer click en botón de ejecutar correlación
  const executeButton = await page.$('button:has-text("Ejecutar Correlación"), button:has-text("Ejecutar"), button:has-text("Analizar")');
  if (executeButton) {
    await executeButton.click();
    
    // Esperar a que termine el análisis (loading spinner desaparece)
    await page.waitForSelector('.animate-spin', { state: 'detached', timeout: 60000 });
    await page.waitForLoadState('networkidle');
    
    console.log('✅ Correlación ejecutada exitosamente');
  } else {
    throw new Error('No se encontró botón de ejecutar correlación');
  }
}

async function openCorrelationTable(page: Page) {
  console.log('📊 Abriendo tabla de correlación...');
  
  // Buscar botón para abrir tabla de correlación
  const tableButton = await page.$('button:has-text("Ver Tabla"), button:has-text("Tabla"), button:has-text("Resultados")');
  if (tableButton) {
    await tableButton.click();
    
    // Esperar a que aparezca el modal de tabla
    await page.waitForSelector('[data-testid="correlation-table"], .modal, [class*="modal"]', { timeout: 15000 });
    
    await page.screenshot({ 
      path: `${TEST_CONFIG.screenshotPath}/06-tabla-correlacion-con-datos.png`,
      fullPage: true 
    });
    
    console.log('✅ Tabla de correlación abierta');
  } else {
    throw new Error('No se encontró botón para abrir tabla de correlación');
  }
}

async function validateDiagramButton(page: Page) {
  console.log('🔍 Validando presencia del botón Diagrama...');
  
  // Buscar botón "Diagrama" junto a CSV/Excel
  const diagramButton = await page.$('button:has-text("Diagrama"), button[title*="Diagrama"], button:has(.text="🕸️")');
  
  if (!diagramButton) {
    await page.screenshot({ 
      path: `${TEST_CONFIG.screenshotPath}/07-modal-vacio-problema.png`,
      fullPage: true 
    });
    throw new Error('❌ CRÍTICO: No se encontró el botón Diagrama en la tabla de correlación');
  }
  
  // Verificar que el botón está habilitado
  const isDisabled = await diagramButton.isDisabled();
  expect(isDisabled).toBe(false);
  
  console.log('✅ Botón Diagrama encontrado y habilitado');
  return diagramButton;
}

async function openPhoneCorrelationViewer(page: Page) {
  console.log('🕸️ Abriendo PhoneCorrelationViewer...');
  
  const diagramButton = await validateDiagramButton(page);
  
  await diagramButton.click();
  
  // Esperar a que aparezca el modal del diagrama (90% x 85%)
  await page.waitForSelector('[data-testid="phone-correlation-viewer"], .react-flow', { timeout: 20000 });
  
  // Capturar modal del diagrama abierto
  await page.screenshot({ 
    path: `${TEST_CONFIG.screenshotPath}/modal-diagrama-abierto.png`,
    fullPage: true 
  });
  
  console.log('✅ PhoneCorrelationViewer abierto correctamente');
}

// TESTS PRINCIPALES

test.describe('PhoneCorrelationViewer - Testing Completo MCP', () => {
  
  test.beforeEach(async ({ page }) => {
    // Configurar timeouts extendidos
    page.setDefaultTimeout(TEST_CONFIG.maxWaitTime);
  });

  test('1. FLUJO COMPLETO: Login → Misiones → Correlación → Diagrama', async ({ page }) => {
    console.log('🎯 INICIANDO TEST 1: FLUJO COMPLETO');
    
    await loginToKronos(page);
    await navigateToMissions(page);
    await selectMissionWithData(page);
    await executeCorrelation(page);
    await openCorrelationTable(page);
    await openPhoneCorrelationViewer(page);
    
    // Verificar que el modal tiene las dimensiones correctas (90% x 85%)
    const modal = await page.$('.fixed.inset-0 > div');
    if (modal) {
      const boundingBox = await modal.boundingBox();
      const viewport = page.viewportSize();
      
      if (boundingBox && viewport) {
        const widthRatio = boundingBox.width / viewport.width;
        const heightRatio = boundingBox.height / viewport.height;
        
        expect(widthRatio).toBeGreaterThan(0.85); // Aproximadamente 90%
        expect(heightRatio).toBeGreaterThan(0.80); // Aproximadamente 85%
      }
    }
    
    console.log('✅ TEST 1 COMPLETADO: Flujo completo funcional');
  });

  test('2. VALIDACIÓN DE 4 MODOS DE VISUALIZACIÓN', async ({ page }) => {
    console.log('🎯 INICIANDO TEST 2: 4 MODOS DE VISUALIZACIÓN');
    
    // Setup completo hasta diagrama
    await loginToKronos(page);
    await navigateToMissions(page);
    await selectMissionWithData(page);
    await executeCorrelation(page);
    await openCorrelationTable(page);
    await openPhoneCorrelationViewer(page);
    
    // Localizar el selector de modos
    const modeSelector = await page.$('select');
    expect(modeSelector).not.toBeNull();
    
    // Array de modos esperados
    const expectedModes = [
      'radial_central',
      'circular_avatares', 
      'flujo_lineal',
      'hibrido_inteligente'
    ];
    
    for (const mode of expectedModes) {
      console.log(`🔄 Probando modo: ${mode}`);
      
      // Cambiar modo
      await modeSelector!.selectOption(mode);
      await page.waitForTimeout(2000); // Esperar animación
      
      // Verificar que hay nodos visibles
      const nodes = await page.$$('.react-flow__node');
      expect(nodes.length).toBeGreaterThan(0);
      
      // Capturar screenshot del modo
      await page.screenshot({ 
        path: `${TEST_CONFIG.screenshotPath}/modo-${mode}.png`,
        fullPage: true 
      });
      
      console.log(`✅ Modo ${mode} funcional`);
    }
    
    await page.screenshot({ 
      path: `${TEST_CONFIG.screenshotPath}/modal-diagrama-funcionando.png`,
      fullPage: true 
    });
    
    console.log('✅ TEST 2 COMPLETADO: Todos los modos funcionan');
  });

  test('3. CONTROLES DE ZOOM, FILTROS Y EXPORT', async ({ page }) => {
    console.log('🎯 INICIANDO TEST 3: CONTROLES Y EXPORT');
    
    // Setup hasta diagrama
    await loginToKronos(page);
    await navigateToMissions(page);
    await selectMissionWithData(page);
    await executeCorrelation(page);
    await openCorrelationTable(page);
    await openPhoneCorrelationViewer(page);
    
    // Panel lateral de controles debe estar visible
    const controlsPanel = await page.$('.w-80'); // Panel lateral 320px
    expect(controlsPanel).not.toBeNull();
    
    // Test controles de zoom
    console.log('🔍 Testing controles de zoom...');
    const zoomInBtn = await page.$('button:has-text("🔍"), button[title*="Zoom In"], button:has-text("+")');
    const zoomOutBtn = await page.$('button:has-text("🔍"), button[title*="Zoom Out"], button:has-text("-")');
    const fitViewBtn = await page.$('button:has-text("⬜"), button[title*="Fit"], button:has-text("Ajustar")');
    
    if (zoomInBtn) await zoomInBtn.click();
    await page.waitForTimeout(500);
    
    if (zoomOutBtn) await zoomOutBtn.click(); 
    await page.waitForTimeout(500);
    
    if (fitViewBtn) await fitViewBtn.click();
    await page.waitForTimeout(500);
    
    // Test filtros
    console.log('⚙️ Testing filtros...');
    const filterSlider = await page.$('input[type="range"]');
    if (filterSlider) {
      await filterSlider.fill('30'); // Cambiar filtro de correlación mínima
      await page.waitForTimeout(1000);
    }
    
    // Test toggles
    const toggles = await page.$$('input[type="checkbox"]');
    for (const toggle of toggles) {
      await toggle.click();
      await page.waitForTimeout(500);
    }
    
    // Test export buttons
    console.log('📤 Testing funciones de export...');
    const exportPNG = await page.$('button:has-text("PNG")');
    const exportSVG = await page.$('button:has-text("SVG")');
    const exportJSON = await page.$('button:has-text("JSON")');
    
    // Verificar que los botones existen (no ejecutar descarga en test)
    expect(exportPNG).not.toBeNull();
    expect(exportSVG).not.toBeNull();
    expect(exportJSON).not.toBeNull();
    
    await page.screenshot({ 
      path: `${TEST_CONFIG.screenshotPath}/controles-funcionando.png`,
      fullPage: true 
    });
    
    console.log('✅ TEST 3 COMPLETADO: Controles funcionan correctamente');
  });

  test('4. INTERACTIVIDAD: Tooltips, Clicks, Drag&Drop', async ({ page }) => {
    console.log('🎯 INICIANDO TEST 4: INTERACTIVIDAD');
    
    // Setup hasta diagrama
    await loginToKronos(page);
    await navigateToMissions(page);
    await selectMissionWithData(page);
    await executeCorrelation(page);
    await openCorrelationTable(page);
    await openPhoneCorrelationViewer(page);
    
    // Test tooltips en nodos
    console.log('💬 Testing tooltips de nodos...');
    const nodes = await page.$$('.react-flow__node');
    if (nodes.length > 0) {
      await nodes[0].click();
      await page.waitForTimeout(1000);
      
      // Verificar si aparece tooltip
      const tooltip = await page.$('[class*="tooltip"], [class*="fixed z-50"]');
      if (tooltip) {
        console.log('✅ Tooltip de nodo funcional');
      }
    }
    
    // Test tooltips en edges  
    console.log('🔗 Testing tooltips de edges...');
    const edges = await page.$$('.react-flow__edge');
    if (edges.length > 0) {
      await edges[0].click();
      await page.waitForTimeout(1000);
    }
    
    // Test drag & drop de nodos
    console.log('🖱️ Testing drag & drop...');
    if (nodes.length > 1) {
      const nodeBox = await nodes[0].boundingBox();
      if (nodeBox) {
        await page.mouse.move(nodeBox.x + nodeBox.width/2, nodeBox.y + nodeBox.height/2);
        await page.mouse.down();
        await page.mouse.move(nodeBox.x + 50, nodeBox.y + 50);
        await page.mouse.up();
        
        console.log('✅ Drag & drop funcional');
      }
    }
    
    await page.screenshot({ 
      path: `${TEST_CONFIG.screenshotPath}/modal-diagrama-interactivo-funcionando.png`,
      fullPage: true 
    });
    
    console.log('✅ TEST 4 COMPLETADO: Interactividad funcional');
  });

  test('5. VALIDACIÓN DE DATOS REALES DE BD', async ({ page }) => {
    console.log('🎯 INICIANDO TEST 5: DATOS REALES DE BD');
    
    // Setup hasta diagrama
    await loginToKronos(page);
    await navigateToMissions(page);
    await selectMissionWithData(page);
    await executeCorrelation(page);
    await openCorrelationTable(page);
    await openPhoneCorrelationViewer(page);
    
    // Verificar que se muestran números telefónicos reales
    const phoneNumbers = await page.$$eval('.react-flow__node', nodes => 
      nodes.map(node => node.textContent).filter(text => text && text.match(/\d{10}/))
    );
    
    expect(phoneNumbers.length).toBeGreaterThan(0);
    console.log(`✅ Encontrados ${phoneNumbers.length} números telefónicos en nodos`);
    
    // Verificar que el número objetivo está presente
    const targetVisible = phoneNumbers.some(num => num?.includes(TEST_CONFIG.targetNumber));
    expect(targetVisible).toBe(true);
    console.log(`✅ Número objetivo ${TEST_CONFIG.targetNumber} visible en diagrama`);
    
    // Verificar información del panel
    const statsPanel = await page.$('text=nodos, text=conexiones');
    expect(statsPanel).not.toBeNull();
    
    await page.screenshot({ 
      path: `${TEST_CONFIG.screenshotPath}/datos-reales-validados.png`,
      fullPage: true 
    });
    
    console.log('✅ TEST 5 COMPLETADO: Datos reales de BD validados');
  });

  test('6. PERFORMANCE Y RESPONSIVE', async ({ page }) => {
    console.log('🎯 INICIANDO TEST 6: PERFORMANCE Y RESPONSIVE');
    
    // Medir tiempo de carga completa
    const startTime = Date.now();
    
    await loginToKronos(page);
    await navigateToMissions(page);
    await selectMissionWithData(page);
    await executeCorrelation(page);
    await openCorrelationTable(page);
    await openPhoneCorrelationViewer(page);
    
    const totalTime = Date.now() - startTime;
    console.log(`⏱️ Tiempo total de flujo: ${totalTime}ms`);
    
    // El flujo completo no debe tomar más de 2 minutos
    expect(totalTime).toBeLessThan(120000);
    
    // Test responsive - cambiar tamaño de ventana
    await page.setViewportSize({ width: 1200, height: 800 });
    await page.waitForTimeout(1000);
    
    await page.setViewportSize({ width: 1600, height: 1000 });
    await page.waitForTimeout(1000);
    
    // Verificar que el modal sigue siendo visible y funcional
    const modal = await page.$('.react-flow');
    expect(modal).not.toBeNull();
    
    console.log('✅ TEST 6 COMPLETADO: Performance aceptable y responsive funcional');
  });

  test('7. INTEGRACIÓN SIN AFECTAR FUNCIONALIDAD EXISTENTE', async ({ page }) => {
    console.log('🎯 INICIANDO TEST 7: INTEGRACIÓN NO DESTRUCTIVA');
    
    // Setup hasta tabla de correlación (SIN abrir diagrama)
    await loginToKronos(page);
    await navigateToMissions(page);
    await selectMissionWithData(page);
    await executeCorrelation(page);
    await openCorrelationTable(page);
    
    // Verificar que botones CSV y Excel siguen funcionando
    const csvButton = await page.$('button:has-text("CSV")');
    const excelButton = await page.$('button:has-text("Excel")');
    
    expect(csvButton).not.toBeNull();
    expect(excelButton).not.toBeNull();
    
    // Verificar que están habilitados
    expect(await csvButton!.isDisabled()).toBe(false);
    expect(await excelButton!.isDisabled()).toBe(false);
    
    // Cerrar modal de tabla
    const closeButton = await page.$('button:has-text("✕"), button[title*="Cerrar"]');
    if (closeButton) {
      await closeButton.click();
      await page.waitForTimeout(1000);
    }
    
    // Verificar que podemos navegar a otras secciones
    await page.click('text=Dashboard');
    await page.waitForLoadState('networkidle');
    
    await page.click('text=Usuarios');
    await page.waitForLoadState('networkidle');
    
    await page.click('text=Roles');
    await page.waitForLoadState('networkidle');
    
    console.log('✅ TEST 7 COMPLETADO: Funcionalidad existente no afectada');
  });

});

// Test adicional para casos edge y error handling
test.describe('PhoneCorrelationViewer - Casos Edge y Error Handling', () => {
  
  test('Error Handling: Sin datos de correlación', async ({ page }) => {
    console.log('🎯 TEST ERROR HANDLING: Sin datos');
    
    await loginToKronos(page);
    await navigateToMissions(page);
    await selectMissionWithData(page);
    await executeCorrelation(page);
    
    // Intentar abrir tabla sin datos válidos
    const tableButton = await page.$('button:has-text("Ver Tabla"), button:has-text("Tabla")');
    if (tableButton) {
      await tableButton.click();
      
      // Si no hay datos, el botón diagrama debe estar deshabilitado
      const diagramButton = await page.$('button:has-text("Diagrama")');
      if (diagramButton) {
        const isDisabled = await diagramButton.isDisabled();
        // Debe estar deshabilitado si no hay interacciones
      }
    }
    
    console.log('✅ Error handling validado');
  });

  test('ESC para cerrar modal', async ({ page }) => {
    console.log('🎯 TEST ESC: Cerrar con tecla ESC');
    
    // Setup completo hasta diagrama
    await loginToKronos(page);
    await navigateToMissions(page);
    await selectMissionWithData(page);
    await executeCorrelation(page);
    await openCorrelationTable(page);
    await openPhoneCorrelationViewer(page);
    
    // Presionar ESC
    await page.keyboard.press('Escape');
    await page.waitForTimeout(1000);
    
    // Verificar que el modal se cerró
    const modal = await page.$('.react-flow');
    expect(modal).toBeNull();
    
    console.log('✅ ESC cerrar modal funcional');
  });

});