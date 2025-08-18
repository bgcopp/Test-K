import { test, expect, Page } from '@playwright/test';
import { DebugHelper } from './debug-helpers';

/**
 * Test de diagnóstico para debugging detallado
 * 
 * Este test está diseñado para capturar máxima información
 * cuando otros tests fallan, facilitando el diagnóstico
 */

test.describe('Diagnóstico Detallado - Números Objetivo', () => {
  let debugHelper: DebugHelper;

  test.beforeEach(async ({ page }) => {
    debugHelper = new DebugHelper(page);
    await debugHelper.injectDebugScript();
  });

  test('Diagnóstico completo del flujo de correlación', async ({ page }) => {
    console.log('🔬 Iniciando diagnóstico completo...');
    
    try {
      // 1. Navegación inicial
      console.log('🔬 Paso 1: Navegación inicial');
      await page.goto('/');
      await debugHelper.captureFullPageState('01_inicio');
      await debugHelper.generateDebugReport();
      
      // 2. Ir a misiones
      console.log('🔬 Paso 2: Navegación a misiones');
      await page.click('text=Misiones');
      await debugHelper.waitForStableContent();
      await debugHelper.captureFullPageState('02_misiones');
      
      // 3. Seleccionar misión específica
      console.log('🔬 Paso 3: Selección de misión');
      const missionRow = page.locator('tr:has-text("mission_MPFRBNsb")');
      
      if (await missionRow.isVisible()) {
        console.log('✅ Misión encontrada');
        await missionRow.locator('button:has-text("Detalles")').click();
      } else {
        console.error('❌ Misión no encontrada');
        await debugHelper.captureFullPageState('ERROR_mission_not_found');
        throw new Error('Misión mission_MPFRBNsb no encontrada');
      }
      
      await debugHelper.waitForStableContent();
      await debugHelper.captureFullPageState('03_detalle_mision');
      
      // 4. Configurar análisis de correlación
      console.log('🔬 Paso 4: Configuración de análisis');
      await page.click('text=Análisis de Correlación');
      await debugHelper.waitForStableContent();
      await debugHelper.captureFullPageState('04_config_correlacion');
      
      // Verificar que el formulario de configuración esté presente
      const configForm = page.locator('[data-testid="correlation-config"]');
      if (await configForm.isVisible()) {
        console.log('✅ Formulario de configuración encontrado');
      } else {
        console.log('⚠️ Formulario de configuración no encontrado, buscando inputs...');
        const dateInputs = page.locator('input[type="date"], input[name*="Date"]');
        const timeInputs = page.locator('input[type="time"], input[name*="Time"]');
        const numberInputs = page.locator('input[type="number"], input[name*="min"]');
        
        console.log(`📋 Inputs encontrados: ${await dateInputs.count()} fecha, ${await timeInputs.count()} hora, ${await numberInputs.count()} número`);
      }
      
      // Configurar parámetros
      await page.fill('input[name="startDate"]', '2021-05-20');
      await page.fill('input[name="startTime"]', '10:00:00');
      await page.fill('input[name="endDate"]', '2021-05-20');
      await page.fill('input[name="endTime"]', '15:00:00');
      await page.fill('input[name="minMatches"]', '1');
      
      await debugHelper.captureFullPageState('05_parametros_configurados');
      
      // 5. Ejecutar análisis
      console.log('🔬 Paso 5: Ejecución de análisis');
      const executeButton = page.locator('button:has-text("Ejecutar Análisis")');
      
      if (await executeButton.isVisible()) {
        console.log('✅ Botón de ejecución encontrado');
        await executeButton.click();
      } else {
        console.error('❌ Botón de ejecución no encontrado');
        await debugHelper.captureFullPageState('ERROR_execute_button_not_found');
        throw new Error('Botón de ejecutar análisis no encontrado');
      }
      
      // Verificar inicio de análisis
      const loadingIndicator = page.locator('.loading-indicator, text=Procesando, .spinner');
      const loadingVisible = await loadingIndicator.isVisible({ timeout: 10000 });
      
      if (loadingVisible) {
        console.log('✅ Análisis iniciado (indicador de carga visible)');
        await debugHelper.captureFullPageState('06_analisis_iniciado');
      } else {
        console.log('⚠️ No se detectó indicador de carga');
        await debugHelper.captureFullPageState('WARNING_no_loading_indicator');
      }
      
      // 6. Esperar resultados
      console.log('🔬 Paso 6: Esperando resultados (hasta 5 minutos)');
      const resultsTable = page.locator('table.correlation-results, .results-table, table');
      
      await resultsTable.waitFor({ 
        state: 'visible', 
        timeout: 5 * 60 * 1000 
      });
      
      console.log('✅ Tabla de resultados visible');
      await debugHelper.waitForStableContent();
      await debugHelper.captureFullPageState('07_resultados_cargados');
      
      // 7. Análisis detallado de resultados
      console.log('🔬 Paso 7: Análisis de resultados');
      await debugHelper.logTableContent();
      await debugHelper.searchForTargetNumbers();
      
      // Capturar información detallada de la tabla
      const rows = resultsTable.locator('tbody tr');
      const totalRows = await rows.count();
      
      console.log(`📊 Total de filas en resultados: ${totalRows}`);
      
      // 8. Búsqueda específica de números objetivo
      console.log('🔬 Paso 8: Búsqueda específica de números objetivo');
      const targetNumbers = ['3224274851', '3208611034', '3143534707', '3102715509', '3214161903'];
      const foundNumbers = [];
      const missingNumbers = [];
      
      for (const number of targetNumbers) {
        const numberElement = page.locator(`td:has-text("${number}")`);
        const isFound = await numberElement.isVisible();
        
        if (isFound) {
          foundNumbers.push(number);
          console.log(`✅ Número ${number} ENCONTRADO`);
        } else {
          missingNumbers.push(number);
          console.log(`❌ Número ${number} NO ENCONTRADO`);
          
          // Buscar con filtro si disponible
          const searchInput = page.locator('input[placeholder*="Buscar"], input[name="search"]').first();
          if (await searchInput.isVisible({ timeout: 2000 })) {
            console.log(`🔍 Intentando búsqueda filtrada para ${number}...`);
            await searchInput.fill(number);
            await page.waitForTimeout(2000);
            
            const filteredResult = await page.locator(`td:has-text("${number}")`).isVisible();
            if (filteredResult) {
              console.log(`✅ Número ${number} encontrado con filtro`);
              foundNumbers.push(number);
              missingNumbers.pop();
            }
            
            await searchInput.clear();
            await page.waitForTimeout(1000);
          }
        }
      }
      
      await debugHelper.captureFullPageState('08_busqueda_completada');
      
      // 9. Generar reporte final de diagnóstico
      console.log('🔬 Paso 9: Generando reporte final');
      
      const diagnosticReport = {
        timestamp: new Date().toISOString(),
        mission: 'mission_MPFRBNsb',
        totalRows: totalRows,
        targetNumbers: {
          total: targetNumbers.length,
          found: foundNumbers.length,
          missing: missingNumbers.length,
          foundList: foundNumbers,
          missingList: missingNumbers
        },
        analysis: {
          tableVisible: await resultsTable.isVisible(),
          hasData: totalRows > 0,
          expectedMinimumRows: 9, // suma de coincidencias esperadas
          meetsExpectation: totalRows >= 9
        }
      };
      
      const fs = require('fs');
      const reportPath = `test-results/evidence/diagnostic_report_${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
      fs.writeFileSync(reportPath, JSON.stringify(diagnosticReport, null, 2));
      
      console.log('📊 REPORTE DE DIAGNÓSTICO FINAL:');
      console.log(`✅ Números encontrados: ${foundNumbers.length}/${targetNumbers.length}`);
      console.log(`❌ Números faltantes: ${missingNumbers.length}`);
      console.log(`📊 Total de resultados: ${totalRows}`);
      console.log(`📄 Reporte guardado: ${reportPath}`);
      
      // Las expectativas del diagnóstico son menos estrictas
      // Solo falla si no hay resultados en absoluto
      expect(totalRows).toBeGreaterThan(0);
      
      if (missingNumbers.length > 0) {
        console.warn(`⚠️ DIAGNÓSTICO: ${missingNumbers.length} números objetivo no encontrados: ${missingNumbers.join(', ')}`);
      } else {
        console.log('🏆 DIAGNÓSTICO EXITOSO: Todos los números objetivo encontrados');
      }
      
    } catch (error) {
      console.error('❌ Error en diagnóstico:', error);
      await debugHelper.captureFullPageState('ERROR_diagnostic_failure');
      throw error;
    }
  });

  test('Verificación de conectividad y estado del backend', async ({ page }) => {
    console.log('🔌 Verificando conectividad y estado del backend...');
    
    // Verificar que la aplicación responda
    const response = await page.goto('/');
    expect(response?.status()).toBe(200);
    
    // Verificar elementos básicos de la interfaz
    await expect(page.locator('body')).toBeVisible();
    await expect(page.locator('text=Misiones')).toBeVisible();
    
    // Capturar estado inicial
    await debugHelper.captureFullPageState('connectivity_check');
    
    console.log('✅ Conectividad verificada');
  });
});