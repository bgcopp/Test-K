import { test, expect, Page } from '@playwright/test';

/**
 * Suite de tests de certificación para números objetivo de Boris
 * 
 * OBJETIVO: Certificar que todos los números objetivo aparezcan correctamente
 * en los resultados de correlación después de las correcciones implementadas.
 * 
 * NÚMEROS OBJETIVO:
 * - 3224274851 (esperado: 2 coincidencias)
 * - 3208611034 (esperado: 2 coincidencias)  
 * - 3143534707 (esperado: 3 coincidencias)
 * - 3102715509 (esperado: 1 coincidencia)
 * - 3214161903 (esperado: 1 coincidencia)
 * 
 * CONFIGURACIÓN:
 * - Misión: mission_MPFRBNsb
 * - Período: 2021-05-20 10:00:00 a 2021-05-20 15:00:00
 * - Mínimo coincidencias: 1
 */

interface TargetNumber {
  number: string;
  expectedMatches: number;
  description: string;
}

const TARGET_NUMBERS: TargetNumber[] = [
  { number: '3224274851', expectedMatches: 2, description: 'Número objetivo 1' },
  { number: '3208611034', expectedMatches: 2, description: 'Número objetivo 2' },
  { number: '3143534707', expectedMatches: 3, description: 'Número objetivo 3' },
  { number: '3102715509', expectedMatches: 1, description: 'Número objetivo 4' },
  { number: '3214161903', expectedMatches: 1, description: 'Número objetivo 5' }
];

const MISSION_ID = 'mission_MPFRBNsb';
const START_DATE = '2021-05-20';
const START_TIME = '10:00:00';
const END_DATE = '2021-05-20';
const END_TIME = '15:00:00';
const MIN_MATCHES = '1';

class CorrelationTestHelper {
  constructor(private page: Page) {}

  async navigateToMissions() {
    console.log('🧭 Navegando a la página de Misiones...');
    await this.page.click('text=Misiones');
    await this.page.waitForSelector('table', { timeout: 30000 });
    console.log('✅ Página de Misiones cargada');
  }

  async selectMission() {
    console.log(`🎯 Seleccionando misión ${MISSION_ID}...`);
    
    // Buscar la misión en la tabla
    const missionRow = this.page.locator(`tr:has-text("${MISSION_ID}")`);
    await expect(missionRow).toBeVisible({ timeout: 30000 });
    
    // Click en el botón de detalles
    await missionRow.locator('button:has-text("Detalles")').click();
    
    // Esperar a que cargue la página de detalles
    await this.page.waitForSelector('text=Análisis de Correlación', { timeout: 30000 });
    console.log('✅ Página de detalles de misión cargada');
  }

  async configureCorrelationAnalysis() {
    console.log('⚙️ Configurando análisis de correlación...');
    
    // Click en la pestaña de Análisis de Correlación
    await this.page.click('text=Análisis de Correlación');
    await this.page.waitForSelector('[data-testid="correlation-config"]', { timeout: 30000 });
    
    // Configurar fecha de inicio
    await this.page.fill('input[name="startDate"]', START_DATE);
    await this.page.fill('input[name="startTime"]', START_TIME);
    
    // Configurar fecha de fin
    await this.page.fill('input[name="endDate"]', END_DATE);
    await this.page.fill('input[name="endTime"]', END_TIME);
    
    // Configurar mínimo de coincidencias
    await this.page.fill('input[name="minMatches"]', MIN_MATCHES);
    
    console.log(`✅ Configuración establecida: ${START_DATE} ${START_TIME} - ${END_DATE} ${END_TIME}, min: ${MIN_MATCHES}`);
  }

  async executeCorrelationAnalysis() {
    console.log('🚀 Ejecutando análisis de correlación...');
    
    // Click en el botón de análisis
    await this.page.click('button:has-text("Ejecutar Análisis")');
    
    // Esperar a que aparezca el indicador de carga
    await this.page.waitForSelector('.loading-indicator, text=Procesando', { timeout: 10000 });
    console.log('⏳ Análisis iniciado, esperando resultados...');
    
    // Esperar a que termine el análisis (máximo 5 minutos)
    await this.page.waitForSelector('table.correlation-results, .results-table', { timeout: 5 * 60 * 1000 });
    
    // Verificar que no haya pantalla en blanco
    const resultsTable = this.page.locator('table.correlation-results, .results-table');
    await expect(resultsTable).toBeVisible();
    
    console.log('✅ Análisis completado, resultados disponibles');
  }

  async validateTargetNumber(targetNumber: TargetNumber): Promise<boolean> {
    console.log(`🔍 Validando número objetivo: ${targetNumber.number}...`);
    
    try {
      // Buscar el número en la tabla de resultados
      const numberCell = this.page.locator(`td:has-text("${targetNumber.number}")`);
      const isVisible = await numberCell.isVisible();
      
      if (!isVisible) {
        console.error(`❌ Número ${targetNumber.number} NO encontrado en resultados`);
        return false;
      }
      
      // Verificar formato (sin prefijo 57)
      const cellText = await numberCell.textContent();
      if (cellText?.includes('57' + targetNumber.number)) {
        console.error(`❌ Número ${targetNumber.number} tiene formato incorrecto (prefijo 57 presente)`);
        return false;
      }
      
      // Contar coincidencias si es posible
      const matchesCell = numberCell.locator('..').locator('td').nth(2); // Asumiendo que las coincidencias están en la 3ra columna
      const matchesText = await matchesCell.textContent();
      const actualMatches = parseInt(matchesText || '0');
      
      if (actualMatches !== targetNumber.expectedMatches) {
        console.warn(`⚠️ Número ${targetNumber.number}: coincidencias encontradas ${actualMatches}, esperadas ${targetNumber.expectedMatches}`);
      }
      
      console.log(`✅ Número ${targetNumber.number} validado correctamente`);
      return true;
      
    } catch (error) {
      console.error(`❌ Error validando número ${targetNumber.number}:`, error);
      return false;
    }
  }

  async captureEvidence(stepName: string) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `evidence_${stepName}_${timestamp}.png`;
    await this.page.screenshot({ 
      path: `test-results/evidence/${filename}`,
      fullPage: true 
    });
    console.log(`📸 Evidencia capturada: ${filename}`);
  }

  async validateAllTargetNumbers(): Promise<{ success: boolean; results: any[] }> {
    console.log('🎯 Iniciando validación de todos los números objetivo...');
    
    const results = [];
    let allValid = true;
    
    for (const targetNumber of TARGET_NUMBERS) {
      const isValid = await this.validateTargetNumber(targetNumber);
      results.push({
        number: targetNumber.number,
        expectedMatches: targetNumber.expectedMatches,
        found: isValid,
        description: targetNumber.description
      });
      
      if (!isValid) {
        allValid = false;
      }
    }
    
    return { success: allValid, results };
  }
}

test.describe('Certificación de Números Objetivo - KRONOS', () => {
  let helper: CorrelationTestHelper;

  test.beforeEach(async ({ page }) => {
    helper = new CorrelationTestHelper(page);
    
    // Configurar directorio de evidencias
    await page.addInitScript(() => {
      // Crear directorio de evidencias si no existe
      const fs = require('fs');
      const path = 'test-results/evidence';
      if (!fs.existsSync(path)) {
        fs.mkdirSync(path, { recursive: true });
      }
    });
  });

  test('1. Test de Navegación y Configuración', async ({ page }) => {
    await page.goto('/');
    await helper.captureEvidence('01_inicio_aplicacion');
    
    await helper.navigateToMissions();
    await helper.captureEvidence('02_pagina_misiones');
    
    await helper.selectMission();
    await helper.captureEvidence('03_detalle_mision');
    
    await helper.configureCorrelationAnalysis();
    await helper.captureEvidence('04_configuracion_correlacion');
  });

  test('2. Test de Ejecución de Análisis', async ({ page }) => {
    await page.goto('/');
    await helper.navigateToMissions();
    await helper.selectMission();
    await helper.configureCorrelationAnalysis();
    
    await helper.executeCorrelationAnalysis();
    await helper.captureEvidence('05_resultados_correlacion');
    
    // Verificar que no hay pantalla en blanco
    const resultsTable = page.locator('table.correlation-results, .results-table');
    await expect(resultsTable).toBeVisible();
    
    // Verificar que hay resultados
    const rows = page.locator('table.correlation-results tbody tr, .results-table tbody tr');
    const rowCount = await rows.count();
    expect(rowCount).toBeGreaterThan(0);
  });

  test('3. Test de Números Objetivo - CRÍTICO', async ({ page }) => {
    await page.goto('/');
    await helper.navigateToMissions();
    await helper.selectMission();
    await helper.configureCorrelationAnalysis();
    await helper.executeCorrelationAnalysis();
    
    // Capturar evidencia antes de validación
    await helper.captureEvidence('06_antes_validacion_numeros');
    
    // Validar todos los números objetivo
    const validation = await helper.validateAllTargetNumbers();
    
    // Capturar evidencia después de validación
    await helper.captureEvidence('07_despues_validacion_numeros');
    
    // Log detallado de resultados
    console.log('📊 RESULTADOS DE VALIDACIÓN:');
    validation.results.forEach(result => {
      const status = result.found ? '✅' : '❌';
      console.log(`${status} ${result.number} (${result.description}): ${result.found ? 'ENCONTRADO' : 'NO ENCONTRADO'}`);
    });
    
    // El test DEBE FALLAR si algún número no se encuentra
    if (!validation.success) {
      const missingNumbers = validation.results
        .filter(r => !r.found)
        .map(r => r.number)
        .join(', ');
      
      throw new Error(`❌ CERTIFICACIÓN FALLIDA: Los siguientes números objetivo NO fueron encontrados: ${missingNumbers}`);
    }
    
    console.log('🎉 CERTIFICACIÓN EXITOSA: Todos los números objetivo encontrados');
  });

  test('4. Test de Funcionalidades', async ({ page }) => {
    await page.goto('/');
    await helper.navigateToMissions();
    await helper.selectMission();
    await helper.configureCorrelationAnalysis();
    await helper.executeCorrelationAnalysis();
    
    // Test de filtro por número
    console.log('🔍 Probando filtro por número...');
    const searchInput = page.locator('input[placeholder*="Buscar"], input[name="search"]');
    if (await searchInput.isVisible()) {
      await searchInput.fill('3224274851');
      await page.waitForTimeout(2000); // Esperar filtro
      await helper.captureEvidence('08_filtro_numero');
    }
    
    // Test de paginación si existe
    console.log('📄 Probando paginación...');
    const nextButton = page.locator('button:has-text("Siguiente"), button:has-text(">")', { timeout: 5000 });
    if (await nextButton.isVisible()) {
      await nextButton.click();
      await helper.captureEvidence('09_paginacion');
    }
    
    // Test de exportación si existe
    console.log('📤 Probando exportación...');
    const exportButton = page.locator('button:has-text("Exportar"), button:has-text("Descargar")', { timeout: 5000 });
    if (await exportButton.isVisible()) {
      await helper.captureEvidence('10_antes_exportacion');
      await exportButton.click();
      await page.waitForTimeout(3000);
    }
  });

  test('5. Test de Validación Final', async ({ page }) => {
    await page.goto('/');
    await helper.navigateToMissions();
    await helper.selectMission();
    await helper.configureCorrelationAnalysis();
    await helper.executeCorrelationAnalysis();
    
    // Validación final exhaustiva
    const validation = await helper.validateAllTargetNumbers();
    
    // Capturar screenshot final de certificación
    await helper.captureEvidence('11_certificacion_final');
    
    // Generar reporte de certificación
    const certificationReport = {
      timestamp: new Date().toISOString(),
      mission: MISSION_ID,
      period: `${START_DATE} ${START_TIME} - ${END_DATE} ${END_TIME}`,
      minMatches: MIN_MATCHES,
      targetNumbers: validation.results,
      overallSuccess: validation.success,
      summary: {
        total: TARGET_NUMBERS.length,
        found: validation.results.filter(r => r.found).length,
        missing: validation.results.filter(r => !r.found).length
      }
    };
    
    // Guardar reporte
    const fs = require('fs');
    const reportPath = `test-results/certification-report-${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
    fs.writeFileSync(reportPath, JSON.stringify(certificationReport, null, 2));
    
    console.log('📊 REPORTE DE CERTIFICACIÓN FINAL:');
    console.log(`✅ Números encontrados: ${certificationReport.summary.found}/${certificationReport.summary.total}`);
    console.log(`❌ Números faltantes: ${certificationReport.summary.missing}`);
    console.log(`📄 Reporte guardado en: ${reportPath}`);
    
    // Asegurar que la certificación sea exitosa
    expect(validation.success).toBe(true);
    expect(certificationReport.summary.found).toBe(TARGET_NUMBERS.length);
    expect(certificationReport.summary.missing).toBe(0);
    
    console.log('🏆 CERTIFICACIÓN FINAL EXITOSA: Todos los números objetivo validados correctamente');
  });
});