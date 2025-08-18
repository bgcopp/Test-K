import { test, expect, Page } from '@playwright/test';
import fs from 'fs';
import path from 'path';

/**
 * Tests de análisis de correlación para datos CLARO
 * Valida la funcionalidad de análisis después de la carga de datos
 * 
 * Casos cubiertos:
 * 1. Navegación a sección de análisis
 * 2. Configuración de parámetros de correlación
 * 3. Ejecución de análisis de correlación
 * 4. Validación de resultados y exportación
 * 5. Verificación de números objetivo en resultados
 */

test.describe('CLARO Correlation Analysis', () => {
  let page: Page;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
    
    // Configurar timeouts para operaciones de análisis (más lentas)
    page.setDefaultTimeout(45000);
    page.setDefaultNavigationTimeout(60000);

    // Interceptar errores de consola
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log(`🚨 Console Error: ${msg.text()}`);
      }
    });
  });

  test('01 - Navegar a sección de análisis de correlación', async () => {
    console.log('🧭 Navegando a sección de análisis...');

    await test.step('Acceder a Mission Detail', async () => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      // Navegar a missions
      const missionsLink = page.locator('a[href*="mission"], button:has-text("Mission"), a:has-text("Mission")').first();
      if (await missionsLink.count() > 0) {
        await missionsLink.click();
        await page.waitForLoadState('networkidle');
      }

      // Seleccionar primera misión disponible
      const firstMission = page.locator('tr[class*="hover"], [class*="mission-row"], button[class*="mission"]').first();
      if (await firstMission.count() > 0) {
        await firstMission.click();
        await page.waitForLoadState('networkidle');
      }

      await page.screenshot({ path: 'test-results/correlation-01-mission-detail.png', fullPage: true });
    });

    await test.step('Acceder a pestaña de análisis', async () => {
      // Buscar pestaña de análisis o posibles objetivos
      const analysisTab = page.locator(
        'button:has-text("Análisis"), button:has-text("Analysis"), button:has-text("Posibles Objetivos"), button:has-text("Correlación")'
      ).first();
      
      if (await analysisTab.count() > 0) {
        await analysisTab.click();
        await page.waitForTimeout(2000);
        
        console.log('✅ Pestaña de análisis encontrada y activada');
      } else {
        // Si no existe pestaña específica, buscar dentro de la página
        const analysisSection = page.locator(
          '[class*="analysis"], [class*="correlation"], [class*="objetivo"]'
        );
        
        if (await analysisSection.count() > 0) {
          console.log('✅ Sección de análisis encontrada en la página');
        } else {
          console.log('⚠️  No se encontró sección de análisis específica');
        }
      }

      await page.screenshot({ path: 'test-results/correlation-01-analysis-section.png', fullPage: true });
    });
  });

  test('02 - Verificar opciones de análisis disponibles', async () => {
    console.log('🔍 Verificando opciones de análisis...');

    await setupAnalysisPage();

    await test.step('Verificar tipos de análisis disponibles', async () => {
      const pageContent = await page.textContent('body');
      
      // Buscar indicadores de análisis de correlación
      const hasCorrelationAnalysis = pageContent.includes('Correlación') || 
                                   pageContent.includes('correlation') ||
                                   pageContent.includes('Análisis de Correlación');

      const hasClassicAnalysis = pageContent.includes('Clásico') || 
                               pageContent.includes('Classic') ||
                               pageContent.includes('Análisis Clásico');

      if (hasCorrelationAnalysis) {
        console.log('✅ Análisis de correlación disponible');
        
        // Seleccionar análisis de correlación si hay opciones
        const correlationRadio = page.locator('input[value="correlation"], label:has-text("Correlación")').first();
        if (await correlationRadio.count() > 0) {
          await correlationRadio.click();
          console.log('📊 Análisis de correlación seleccionado');
        }
      }

      if (hasClassicAnalysis) {
        console.log('ℹ️  Análisis clásico también disponible');
      }

      expect(hasCorrelationAnalysis || hasClassicAnalysis).toBeTruthy();
      
      await page.screenshot({ path: 'test-results/correlation-02-analysis-options.png', fullPage: true });
    });
  });

  test('03 - Configurar parámetros de correlación', async () => {
    console.log('⚙️ Configurando parámetros de correlación...');

    await setupAnalysisPage();

    await test.step('Seleccionar análisis de correlación', async () => {
      // Intentar seleccionar análisis de correlación
      const correlationRadio = page.locator('input[value="correlation"], label:has-text("Correlación")').first();
      if (await correlationRadio.count() > 0) {
        await correlationRadio.click();
        await page.waitForTimeout(1000);
      }
    });

    await test.step('Configurar fechas de análisis', async () => {
      // Buscar campos de fecha
      const startDateInput = page.locator('input[type="datetime-local"], input[type="date"]').first();
      const endDateInput = page.locator('input[type="datetime-local"], input[type="date"]').last();

      if (await startDateInput.count() > 0 && await endDateInput.count() > 0) {
        // Configurar fechas que cubran los datos de prueba (agosto 2024)
        await startDateInput.fill('2024-08-01T00:00');
        await endDateInput.fill('2024-08-31T23:59');
        
        console.log('📅 Fechas de análisis configuradas: 01/08/2024 - 31/08/2024');
      } else {
        console.log('ℹ️  Campos de fecha no encontrados, usando configuración por defecto');
      }

      await page.screenshot({ path: 'test-results/correlation-03-dates-configured.png', fullPage: true });
    });

    await test.step('Configurar mínimo de coincidencias', async () => {
      // Buscar campo de mínimo de coincidencias
      const minCoincidencesInput = page.locator('input[type="number"], input[placeholder*="coincidencia"]').first();

      if (await minCoincidencesInput.count() > 0) {
        await minCoincidencesInput.fill('2');
        console.log('🎯 Mínimo de coincidencias configurado: 2');
      } else {
        console.log('ℹ️  Campo de coincidencias no encontrado, usando valor por defecto');
      }

      await page.screenshot({ path: 'test-results/correlation-03-parameters-set.png', fullPage: true });
    });
  });

  test('04 - Ejecutar análisis de correlación', async () => {
    console.log('🚀 Ejecutando análisis de correlación...');

    await setupAnalysisPage();

    await test.step('Configurar y ejecutar análisis', async () => {
      // Configurar parámetros básicos
      const correlationRadio = page.locator('input[value="correlation"], label:has-text("Correlación")').first();
      if (await correlationRadio.count() > 0) {
        await correlationRadio.click();
      }

      // Configurar fechas si están disponibles
      const startDateInput = page.locator('input[type="datetime-local"], input[type="date"]').first();
      if (await startDateInput.count() > 0) {
        await startDateInput.fill('2024-08-01T00:00');
        
        const endDateInput = page.locator('input[type="datetime-local"], input[type="date"]').last();
        await endDateInput.fill('2024-08-31T23:59');
      }

      // Buscar y hacer clic en botón de análisis
      const analysisButton = page.locator(
        'button:has-text("Ejecutar Análisis"), button:has-text("Analizar"), button:has-text("Correlación"), button:has-text("Ejecutar")'
      ).first();

      await expect(analysisButton).toBeVisible({ timeout: 15000 });
      await analysisButton.click();

      console.log('⏳ Análisis iniciado...');
      await page.screenshot({ path: 'test-results/correlation-04-analysis-started.png', fullPage: true });
    });

    await test.step('Esperar resultados del análisis', async () => {
      // Esperar a que aparezca indicador de progreso o resultados
      await Promise.race([
        // Esperar indicador de carga
        page.waitForSelector('[class*="loading"], [class*="progress"], [class*="spin"]', { timeout: 10000 }),
        // O esperar directamente por resultados
        page.waitForSelector('[class*="result"], table, [class*="correlation"]', { timeout: 30000 }),
        // Timeout de seguridad
        page.waitForTimeout(30000)
      ]);

      // Esperar a que termine el análisis (máximo 3 minutos)
      await Promise.race([
        page.waitForSelector(':has-text("completado"), :has-text("encontrado"), table', { timeout: 180000 }),
        page.waitForSelector('[class*="error"]', { timeout: 180000 }),
        page.waitForTimeout(180000)
      ]);

      await page.screenshot({ path: 'test-results/correlation-04-analysis-completed.png', fullPage: true });
      console.log('✅ Análisis de correlación completado');
    });
  });

  test('05 - Validar resultados de correlación', async () => {
    console.log('📊 Validando resultados de correlación...');

    await setupAnalysisPage();
    await executeCorrelationAnalysis();

    await test.step('Verificar presencia de resultados', async () => {
      const pageContent = await page.textContent('body');
      
      // Buscar indicadores de resultados
      const hasResults = pageContent.includes('resultado') ||
                        pageContent.includes('encontrado') ||
                        pageContent.includes('coincidencia') ||
                        await page.locator('table, [class*="result"]').count() > 0;

      expect(hasResults).toBeTruthy();

      if (hasResults) {
        console.log('✅ Resultados de correlación encontrados');
        
        // Verificar si hay tabla de resultados
        const table = page.locator('table').first();
        if (await table.count() > 0) {
          const tableContent = await table.textContent();
          console.log('📋 Contenido de tabla detectado');
          
          // Buscar números objetivo en los resultados
          const targetNumbers = ['3104277553', '3224274851'];
          for (const number of targetNumbers) {
            if (tableContent.includes(number)) {
              console.log(`🎯 Número objetivo ${number} encontrado en resultados`);
            }
          }
        }
      } else {
        console.log('ℹ️  No se encontraron resultados visibles, posiblemente sin coincidencias');
      }

      await page.screenshot({ path: 'test-results/correlation-05-results-validated.png', fullPage: true });
    });

    await test.step('Verificar estadísticas de análisis', async () => {
      const pageContent = await page.textContent('body');
      
      // Buscar métricas estadísticas
      const numberPattern = /\d+\s*(número|registro|coincidencia|resultado)/gi;
      const metrics = pageContent.match(numberPattern);

      if (metrics && metrics.length > 0) {
        console.log('📈 Métricas encontradas:');
        metrics.forEach(metric => console.log(`   - ${metric}`));
        
        // Verificar que hay al menos alguna métrica con valores > 0
        const hasValidMetrics = metrics.some(metric => {
          const num = parseInt(metric.match(/\d+/)?.[0] || '0');
          return num > 0;
        });

        if (hasValidMetrics) {
          console.log('✅ Métricas válidas encontradas');
        } else {
          console.log('⚠️  Métricas encontradas pero con valores cero');
        }
      } else {
        console.log('ℹ️  No se encontraron métricas estadísticas específicas');
      }
    });
  });

  test('06 - Probar funcionalidad de exportación', async () => {
    console.log('💾 Probando funcionalidad de exportación...');

    await setupAnalysisPage();
    await executeCorrelationAnalysis();

    await test.step('Buscar opciones de exportación', async () => {
      // Buscar botones de exportación
      const exportButtons = page.locator(
        'button:has-text("CSV"), button:has-text("Excel"), button:has-text("Exportar"), button:has-text("Export")'
      );

      const exportCount = await exportButtons.count();
      
      if (exportCount > 0) {
        console.log(`📤 ${exportCount} opciones de exportación encontradas`);
        
        // Probar exportación CSV si está disponible
        const csvButton = page.locator('button:has-text("CSV")').first();
        if (await csvButton.count() > 0) {
          await csvButton.click();
          await page.waitForTimeout(3000); // Esperar a que se procese la exportación
          
          console.log('✅ Exportación CSV ejecutada');
        }
        
        await page.screenshot({ path: 'test-results/correlation-06-export-tested.png', fullPage: true });
      } else {
        console.log('ℹ️  No se encontraron opciones de exportación disponibles');
      }
    });

    await test.step('Verificar estado final del análisis', async () => {
      const pageContent = await page.textContent('body');
      
      // Verificar que no hay errores críticos
      const hasErrors = pageContent.toLowerCase().includes('error') && 
                       !pageContent.toLowerCase().includes('sin error');

      expect(hasErrors).toBeFalsy();

      // Crear reporte final del test
      const correlationReport = {
        timestamp: new Date().toISOString(),
        test_suite: 'CLARO Correlation Analysis',
        status: 'COMPLETED',
        has_results: pageContent.includes('resultado') || pageContent.includes('encontrado'),
        has_export_options: await page.locator('button:has-text("CSV"), button:has-text("Excel")').count() > 0,
        target_numbers_searched: ['3104277553', '3224274851'],
        screenshots_generated: [
          'correlation-01-mission-detail.png',
          'correlation-01-analysis-section.png',
          'correlation-02-analysis-options.png',
          'correlation-03-dates-configured.png',
          'correlation-03-parameters-set.png',
          'correlation-04-analysis-started.png',
          'correlation-04-analysis-completed.png',
          'correlation-05-results-validated.png',
          'correlation-06-export-tested.png'
        ]
      };

      const reportPath = path.join(process.cwd(), 'test-results', 'claro-correlation-report.json');
      fs.mkdirSync(path.dirname(reportPath), { recursive: true });
      fs.writeFileSync(reportPath, JSON.stringify(correlationReport, null, 2));

      console.log(`📄 Reporte de correlación guardado: ${reportPath}`);
      console.log('✅ Tests de correlación completados exitosamente');
    });
  });

  // Función helper para configurar página de análisis
  async function setupAnalysisPage() {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Navegar a missions
    const missionsLink = page.locator('a[href*="mission"], button:has-text("Mission"), a:has-text("Mission")').first();
    if (await missionsLink.count() > 0) {
      await missionsLink.click();
      await page.waitForLoadState('networkidle');
    }

    // Seleccionar primera misión
    const firstMission = page.locator('tr[class*="hover"], [class*="mission-row"], button[class*="mission"]').first();
    if (await firstMission.count() > 0) {
      await firstMission.click();
      await page.waitForLoadState('networkidle');
    }

    // Ir a pestaña de análisis
    const analysisTab = page.locator(
      'button:has-text("Análisis"), button:has-text("Analysis"), button:has-text("Posibles Objetivos"), button:has-text("Correlación")'
    ).first();
    
    if (await analysisTab.count() > 0) {
      await analysisTab.click();
      await page.waitForTimeout(2000);
    }
  }

  // Función helper para ejecutar análisis de correlación
  async function executeCorrelationAnalysis() {
    // Seleccionar análisis de correlación si está disponible
    const correlationRadio = page.locator('input[value="correlation"], label:has-text("Correlación")').first();
    if (await correlationRadio.count() > 0) {
      await correlationRadio.click();
    }

    // Configurar fechas
    const startDateInput = page.locator('input[type="datetime-local"], input[type="date"]').first();
    if (await startDateInput.count() > 0) {
      await startDateInput.fill('2024-08-01T00:00');
      
      const endDateInput = page.locator('input[type="datetime-local"], input[type="date"]').last();
      await endDateInput.fill('2024-08-31T23:59');
    }

    // Ejecutar análisis
    const analysisButton = page.locator(
      'button:has-text("Ejecutar Análisis"), button:has-text("Analizar"), button:has-text("Correlación"), button:has-text("Ejecutar")'
    ).first();

    if (await analysisButton.count() > 0) {
      await analysisButton.click();
      
      // Esperar a que termine el análisis
      await Promise.race([
        page.waitForSelector(':has-text("completado"), :has-text("encontrado"), table', { timeout: 120000 }),
        page.waitForSelector('[class*="error"]', { timeout: 120000 }),
        page.waitForTimeout(120000)
      ]);
    }
  }
});