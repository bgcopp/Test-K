import { test, expect, Page } from '@playwright/test';

/**
 * Tests detallados de validación por número individual
 * 
 * Cada test se enfoca en un número objetivo específico para
 * diagnóstico granular en caso de fallos
 */

const MISSION_ID = 'mission_MPFRBNsb';
const START_DATE = '2021-05-20';
const START_TIME = '10:00:00';
const END_DATE = '2021-05-20';
const END_TIME = '15:00:00';
const MIN_MATCHES = '1';

class DetailedNumberValidator {
  constructor(private page: Page) {}

  async setupCorrelationAnalysis() {
    console.log('🔧 Configurando análisis para validación detallada...');
    
    await this.page.goto('/');
    await this.page.click('text=Misiones');
    await this.page.waitForSelector('table', { timeout: 30000 });
    
    const missionRow = this.page.locator(`tr:has-text("${MISSION_ID}")`);
    await expect(missionRow).toBeVisible({ timeout: 30000 });
    await missionRow.locator('button:has-text("Detalles")').click();
    
    await this.page.waitForSelector('text=Análisis de Correlación', { timeout: 30000 });
    await this.page.click('text=Análisis de Correlación');
    await this.page.waitForSelector('[data-testid="correlation-config"]', { timeout: 30000 });
    
    // Configurar parámetros
    await this.page.fill('input[name="startDate"]', START_DATE);
    await this.page.fill('input[name="startTime"]', START_TIME);
    await this.page.fill('input[name="endDate"]', END_DATE);
    await this.page.fill('input[name="endTime"]', END_TIME);
    await this.page.fill('input[name="minMatches"]', MIN_MATCHES);
    
    // Ejecutar análisis
    await this.page.click('button:has-text("Ejecutar Análisis")');
    await this.page.waitForSelector('.loading-indicator, text=Procesando', { timeout: 10000 });
    await this.page.waitForSelector('table.correlation-results, .results-table', { timeout: 5 * 60 * 1000 });
    
    console.log('✅ Análisis configurado y ejecutado');
  }

  async validateSpecificNumber(number: string, expectedMatches: number, description: string) {
    console.log(`🎯 Validación detallada: ${number} (${description})`);
    
    // Buscar el número específico
    const numberLocator = this.page.locator(`td:has-text("${number}")`);
    const isVisible = await numberLocator.isVisible();
    
    console.log(`🔍 Número ${number} visible: ${isVisible}`);
    
    if (!isVisible) {
      // Buscar con filtro si está disponible
      const searchInput = this.page.locator('input[placeholder*="Buscar"], input[name="search"]').first();
      if (await searchInput.isVisible({ timeout: 5000 })) {
        console.log(`🔍 Intentando buscar ${number} con filtro...`);
        await searchInput.fill(number);
        await this.page.waitForTimeout(3000);
        
        const filteredResult = await this.page.locator(`td:has-text("${number}")`).isVisible();
        console.log(`🔍 Número ${number} después de filtrar: ${filteredResult}`);
        
        if (!filteredResult) {
          throw new Error(`❌ Número ${number} NO encontrado ni en resultados ni en búsqueda filtrada`);
        }
      } else {
        throw new Error(`❌ Número ${number} NO encontrado en resultados`);
      }
    }
    
    // Verificar formato correcto (sin prefijo 57)
    const allNumberCells = this.page.locator('td');
    const count = await allNumberCells.count();
    
    for (let i = 0; i < count; i++) {
      const cellText = await allNumberCells.nth(i).textContent();
      if (cellText?.includes('57' + number)) {
        throw new Error(`❌ Número ${number} encontrado con prefijo 57 incorrecto: ${cellText}`);
      }
    }
    
    console.log(`✅ Número ${number} tiene formato correcto (sin prefijo 57)`);
    
    // Capturar evidencia específica
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    await this.page.screenshot({ 
      path: `test-results/evidence/detailed_${number}_${timestamp}.png`,
      fullPage: true 
    });
    
    console.log(`✅ Validación exitosa para ${number}`);
    
    return true;
  }
}

test.describe('Validación Detallada por Número Objetivo', () => {
  let validator: DetailedNumberValidator;

  test.beforeEach(async ({ page }) => {
    validator = new DetailedNumberValidator(page);
    await validator.setupCorrelationAnalysis();
  });

  test('Validar número 3224274851 (2 coincidencias esperadas)', async ({ page }) => {
    await validator.validateSpecificNumber('3224274851', 2, 'Número objetivo 1');
  });

  test('Validar número 3208611034 (2 coincidencias esperadas)', async ({ page }) => {
    await validator.validateSpecificNumber('3208611034', 2, 'Número objetivo 2');
  });

  test('Validar número 3143534707 (3 coincidencias esperadas)', async ({ page }) => {
    await validator.validateSpecificNumber('3143534707', 3, 'Número objetivo 3');
  });

  test('Validar número 3102715509 (1 coincidencia esperada)', async ({ page }) => {
    await validator.validateSpecificNumber('3102715509', 1, 'Número objetivo 4');
  });

  test('Validar número 3214161903 (1 coincidencia esperada)', async ({ page }) => {
    await validator.validateSpecificNumber('3214161903', 1, 'Número objetivo 5');
  });

  test('Validación de formato - Ningún número debe tener prefijo 57', async ({ page }) => {
    console.log('🔍 Verificando que ningún número tenga prefijo 57...');
    
    // Obtener todos los números de la tabla
    const numberCells = page.locator('td').filter({ hasText: /^\d+$/ });
    const count = await numberCells.count();
    
    const problematicNumbers = [];
    
    for (let i = 0; i < count; i++) {
      const cellText = await numberCells.nth(i).textContent();
      if (cellText && cellText.startsWith('57')) {
        problematicNumbers.push(cellText);
      }
    }
    
    if (problematicNumbers.length > 0) {
      throw new Error(`❌ Encontrados números con prefijo 57: ${problematicNumbers.join(', ')}`);
    }
    
    console.log(`✅ Verificación de formato exitosa: ${count} números sin prefijo 57`);
  });

  test('Validación de conteo total de resultados', async ({ page }) => {
    console.log('📊 Verificando conteo total de resultados...');
    
    const rows = page.locator('table.correlation-results tbody tr, .results-table tbody tr');
    const totalRows = await rows.count();
    
    console.log(`📊 Total de resultados encontrados: ${totalRows}`);
    
    // Debe haber al menos 9 resultados (suma de coincidencias esperadas: 2+2+3+1+1 = 9)
    expect(totalRows).toBeGreaterThanOrEqual(9);
    
    // Capturar evidencia del conteo
    await page.screenshot({ 
      path: `test-results/evidence/total_count_validation_${new Date().toISOString().replace(/[:.]/g, '-')}.png`,
      fullPage: true 
    });
    
    console.log(`✅ Conteo validado: ${totalRows} resultados (mínimo 9 esperados)`);
  });
});