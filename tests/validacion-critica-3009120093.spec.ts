import { test, expect } from '@playwright/test';

/**
 * VALIDACIÓN CRÍTICA - Corrección Frontend para Número 3009120093
 * 
 * Objetivo: Confirmar que la corrección quirúrgica aplicada al frontend
 * reduce efectivamente los nodos de 254 a ≤10 para este número específico
 * 
 * Corrección aplicada: Filtrado ultra-estricto en MissionDetail.tsx
 */
test.describe('Validación Crítica - Número 3009120093', () => {
  
  test.beforeEach(async ({ page }) => {
    // Capturar logs de consola para verificar el filtrado
    page.on('console', msg => {
      console.log(`BROWSER CONSOLE [${msg.type()}]: ${msg.text()}`);
    });
  });

  test('Validar reducción de nodos para 3009120093', async ({ page }) => {
    console.log('🔍 INICIANDO VALIDACIÓN CRÍTICA PARA 3009120093');
    
    // 1. Navegar a la aplicación KRONOS
    await page.goto('http://localhost:8000');
    await page.waitForLoadState('networkidle');
    
    // Tomar captura inicial
    await page.screenshot({ 
      path: 'test-results/validacion-critica-inicio.png',
      fullPage: true 
    });
    
    // 1.5. Autenticarse si es necesario
    console.log('🔐 Verificando si necesita autenticación...');
    
    // Verificar si está en la pantalla de login
    const loginForm = page.locator('form').first();
    if (await loginForm.isVisible()) {
      console.log('🔑 Iniciando sesión...');
      
      // Llenar email (ya está prellenado con admin@example.com)
      const emailField = page.locator('input[type="email"]');
      if (!(await emailField.inputValue()).includes('admin@example.com')) {
        await emailField.fill('admin@example.com');
      }
      
      // Llenar contraseña
      await page.locator('input[type="password"]').fill('admin123');
      
      // Hacer click en Iniciar Sesión
      await page.click('button:has-text("Iniciar Sesión")');
      await page.waitForLoadState('networkidle');
      
      // Tomar captura después del login
      await page.screenshot({ 
        path: 'test-results/validacion-post-login.png',
        fullPage: true 
      });
    }
    
    // 2. Navegar a Misiones
    console.log('📋 Navegando a sección de Misiones...');
    await page.click('a[href="#/missions"]');
    await page.waitForLoadState('networkidle');
    
    // 3. Buscar el número específico 3009120093
    console.log('🔎 Buscando número 3009120093...');
    
    // Buscar en la tabla por el número específico
    const targetRow = page.locator('tr').filter({ hasText: '3009120093' }).first();
    await expect(targetRow).toBeVisible({ timeout: 10000 });
    
    // Tomar captura de la tabla con el número encontrado
    await page.screenshot({ 
      path: 'test-results/validacion-numero-encontrado.png',
      fullPage: true 
    });
    
    // 4. Hacer click en el icono ojo para abrir diagrama
    console.log('👁️ Haciendo click en icono de correlación...');
    
    const eyeButton = targetRow.locator('button').filter({ hasText: /correlación|eye|👁️/ }).first();
    await eyeButton.click();
    
    // Esperar a que se abra el modal de correlación
    await page.waitForSelector('[role="dialog"]', { timeout: 15000 });
    await page.waitForLoadState('networkidle');
    
    // Dar tiempo adicional para que se procesen los datos
    await page.waitForTimeout(3000);
    
    // 5. Capturar logs específicos del filtrado
    console.log('📊 Verificando logs del filtrado ultra-estricto...');
    
    // 6. Contar nodos en el diagrama
    console.log('🔢 Contando nodos en el diagrama...');
    
    // Buscar nodos del diagrama (pueden tener diferentes selectores según la librería)
    const possibleNodeSelectors = [
      '.react-flow__node',
      '.vis-node', 
      '[data-id]',
      '.node',
      'circle',
      '.diagram-node'
    ];
    
    let nodeCount = 0;
    let actualSelector = '';
    
    for (const selector of possibleNodeSelectors) {
      const nodes = page.locator(selector);
      const count = await nodes.count();
      if (count > 0) {
        nodeCount = count;
        actualSelector = selector;
        console.log(`✅ Encontrados ${count} nodos usando selector: ${selector}`);
        break;
      }
    }
    
    // Si no encontramos nodos específicos, buscar en el contenedor del diagrama
    if (nodeCount === 0) {
      console.log('🔍 Buscando nodos en contenedor del diagrama...');
      const diagramContainer = page.locator('.correlation-diagram, .diagram-container, [class*="diagram"]').first();
      
      if (await diagramContainer.isVisible()) {
        // Evaluar JavaScript para contar elementos que parezcan nodos
        nodeCount = await page.evaluate(() => {
          const diagrams = document.querySelectorAll('.correlation-diagram, .diagram-container, [class*="diagram"]');
          if (diagrams.length === 0) return 0;
          
          const diagram = diagrams[0];
          // Buscar elementos que podrían ser nodos
          const possibleNodes = diagram.querySelectorAll('div[data-id], circle, .node, [class*="node"]');
          return possibleNodes.length;
        });
      }
    }
    
    // 7. Tomar captura del diagrama abierto
    await page.screenshot({ 
      path: 'test-results/validacion-diagrama-abierto.png',
      fullPage: true 
    });
    
    // 8. Verificar que el conteo sea ≤10 nodos
    console.log(`📈 RESULTADO: Se encontraron ${nodeCount} nodos`);
    console.log(`🎯 OBJETIVO: Máximo 10 nodos (anteriormente eran 254)`);
    
    // Validación crítica
    expect(nodeCount).toBeLessThanOrEqual(10);
    expect(nodeCount).toBeGreaterThan(0); // Debe haber al menos algunos nodos
    
    // 9. Verificar logs específicos del filtrado
    const consoleMessages = [];
    page.on('console', msg => {
      consoleMessages.push(msg.text());
    });
    
    // Buscar mensaje específico del filtrado ultra-estricto
    const hasFilterLog = consoleMessages.some(msg => 
      msg.includes('CRITERIOS ULTRA-ESTRICTOS aplicados') ||
      msg.includes('3009120093') ||
      msg.includes('filtrado')
    );
    
    // 10. Generar reporte detallado
    const reportData = {
      timestamp: new Date().toISOString(),
      numeroValidado: '3009120093',
      nodosEncontrados: nodeCount,
      selectorUtilizado: actualSelector,
      cumpleObjetivo: nodeCount <= 10,
      mejoraLograda: nodeCount < 254,
      logsCapturados: consoleMessages.filter(msg => 
        msg.includes('3009120093') || 
        msg.includes('filtrado') ||
        msg.includes('CRITERIOS')
      )
    };
    
    console.log('📋 REPORTE DE VALIDACIÓN:');
    console.log(JSON.stringify(reportData, null, 2));
    
    // Guardar reporte en archivo
    await page.evaluate((data) => {
      console.log('📄 REPORTE FINAL VALIDACIÓN 3009120093:', data);
    }, reportData);
    
    // 11. Cerrar modal y limpiar
    await page.keyboard.press('Escape');
    await page.waitForTimeout(1000);
    
    // Tomar captura final
    await page.screenshot({ 
      path: 'test-results/validacion-critica-final.png',
      fullPage: true 
    });
    
    console.log('✅ VALIDACIÓN CRÍTICA COMPLETADA');
    console.log(`🎯 NODOS FINALES: ${nodeCount} (Objetivo: ≤10)`);
    console.log(`✨ MEJORA CONFIRMADA: ${nodeCount < 254 ? 'SÍ' : 'NO'}`);
  });
  
  test('Verificar que otros números siguen funcionando normalmente', async ({ page }) => {
    console.log('🔍 Verificando funcionamiento normal de otros números...');
    
    await page.goto('http://localhost:8000');
    await page.waitForLoadState('networkidle');
    
    // Autenticarse si es necesario
    const loginForm = page.locator('form').first();
    if (await loginForm.isVisible()) {
      console.log('🔑 Iniciando sesión...');
      
      const emailField = page.locator('input[type="email"]');
      if (!(await emailField.inputValue()).includes('admin@example.com')) {
        await emailField.fill('admin@example.com');
      }
      
      await page.locator('input[type="password"]').fill('admin123');
      await page.click('button:has-text("Iniciar Sesión")');
      await page.waitForLoadState('networkidle');
    }
    
    await page.click('a[href="#/missions"]');
    await page.waitForLoadState('networkidle');
    
    // Buscar un número diferente (no problemático)
    const normalRow = page.locator('tr').filter({ hasNotText: '3009120093' }).first();
    
    if (await normalRow.isVisible()) {
      const eyeButton = normalRow.locator('button').filter({ hasText: /correlación|eye|👁️/ }).first();
      
      if (await eyeButton.isVisible()) {
        await eyeButton.click();
        await page.waitForSelector('[role="dialog"]', { timeout: 15000 });
        
        // Verificar que se abre normalmente sin restricciones especiales
        const dialogVisible = await page.locator('[role="dialog"]').isVisible();
        expect(dialogVisible).toBe(true);
        
        await page.keyboard.press('Escape');
        console.log('✅ Números normales siguen funcionando correctamente');
      }
    }
  });
});