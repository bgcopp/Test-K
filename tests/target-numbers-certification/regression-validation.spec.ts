import { test, expect, Page } from '@playwright/test';

/**
 * Tests de regresión para validar que las correcciones implementadas
 * funcionen consistentemente en múltiples ejecuciones
 */

const MISSION_ID = 'mission_MPFRBNsb';
const TARGET_NUMBERS = ['3224274851', '3208611034', '3143534707', '3102715509', '3214161903'];

class RegressionValidator {
  constructor(private page: Page) {}

  async executeFullCorrelationCycle(): Promise<string[]> {
    console.log('🔄 Ejecutando ciclo completo de correlación...');
    
    await this.page.goto('/');
    await this.page.click('text=Misiones');
    await this.page.waitForSelector('table', { timeout: 30000 });
    
    const missionRow = this.page.locator(`tr:has-text("${MISSION_ID}")`);
    await missionRow.locator('button:has-text("Detalles")').click();
    
    await this.page.waitForSelector('text=Análisis de Correlación', { timeout: 30000 });
    await this.page.click('text=Análisis de Correlación');
    await this.page.waitForSelector('[data-testid="correlation-config"]', { timeout: 30000 });
    
    // Configurar análisis
    await this.page.fill('input[name="startDate"]', '2021-05-20');
    await this.page.fill('input[name="startTime"]', '10:00:00');
    await this.page.fill('input[name="endDate"]', '2021-05-20');
    await this.page.fill('input[name="endTime"]', '15:00:00');
    await this.page.fill('input[name="minMatches"]', '1');
    
    // Ejecutar análisis
    await this.page.click('button:has-text("Ejecutar Análisis")');
    await this.page.waitForSelector('.loading-indicator, text=Procesando', { timeout: 10000 });
    await this.page.waitForSelector('table.correlation-results, .results-table', { timeout: 5 * 60 * 1000 });
    
    // Extraer todos los números encontrados
    const numberCells = this.page.locator('td').filter({ hasText: /^\d+$/ });
    const count = await numberCells.count();
    const foundNumbers = [];
    
    for (let i = 0; i < count; i++) {
      const cellText = await numberCells.nth(i).textContent();
      if (cellText && /^\d{10}$/.test(cellText)) {
        foundNumbers.push(cellText);
      }
    }
    
    return [...new Set(foundNumbers)]; // Eliminar duplicados
  }

  async validateConsistentResults(results1: string[], results2: string[]): Promise<boolean> {
    console.log('🔍 Validando consistencia entre ejecuciones...');
    
    // Los resultados deben ser idénticos
    const set1 = new Set(results1);
    const set2 = new Set(results2);
    
    if (set1.size !== set2.size) {
      console.error(`❌ Tamaños diferentes: ${set1.size} vs ${set2.size}`);
      return false;
    }
    
    for (const number of set1) {
      if (!set2.has(number)) {
        console.error(`❌ Número ${number} presente en primera ejecución pero no en segunda`);
        return false;
      }
    }
    
    for (const number of set2) {
      if (!set1.has(number)) {
        console.error(`❌ Número ${number} presente en segunda ejecución pero no en primera`);
        return false;
      }
    }
    
    console.log(`✅ Resultados consistentes: ${set1.size} números únicos en ambas ejecuciones`);
    return true;
  }
}

test.describe('Tests de Regresión - Consistencia de Correcciones', () => {
  let validator: RegressionValidator;

  test.beforeEach(async ({ page }) => {
    validator = new RegressionValidator(page);
  });

  test('Ejecuciones múltiples deben producir resultados idénticos', async ({ page }) => {
    console.log('🔄 Iniciando test de consistencia con múltiples ejecuciones...');
    
    // Primera ejecución
    console.log('🥇 Primera ejecución...');
    const results1 = await validator.executeFullCorrelationCycle();
    
    // Capturar evidencia de primera ejecución
    await page.screenshot({ 
      path: `test-results/evidence/regression_execution_1_${new Date().toISOString().replace(/[:.]/g, '-')}.png`,
      fullPage: true 
    });
    
    // Pequeña pausa para asegurar separación
    await page.waitForTimeout(2000);
    
    // Segunda ejecución
    console.log('🥈 Segunda ejecución...');
    const results2 = await validator.executeFullCorrelationCycle();
    
    // Capturar evidencia de segunda ejecución
    await page.screenshot({ 
      path: `test-results/evidence/regression_execution_2_${new Date().toISOString().replace(/[:.]/g, '-')}.png`,
      fullPage: true 
    });
    
    // Validar consistencia
    const isConsistent = await validator.validateConsistentResults(results1, results2);
    
    // Log detallado
    console.log('📊 RESULTADOS DE REGRESIÓN:');
    console.log(`🥇 Primera ejecución: ${results1.length} números únicos`);
    console.log(`🥈 Segunda ejecución: ${results2.length} números únicos`);
    console.log(`🔍 Consistente: ${isConsistent ? 'SÍ' : 'NO'}`);
    
    // Verificar que todos los números objetivo están en ambas ejecuciones
    for (const targetNumber of TARGET_NUMBERS) {
      const inResults1 = results1.includes(targetNumber);
      const inResults2 = results2.includes(targetNumber);
      
      console.log(`🎯 ${targetNumber}: Ejecución 1: ${inResults1 ? '✅' : '❌'}, Ejecución 2: ${inResults2 ? '✅' : '❌'}`);
      
      expect(inResults1).toBe(true);
      expect(inResults2).toBe(true);
    }
    
    expect(isConsistent).toBe(true);
    
    console.log('🏆 Test de regresión EXITOSO: Resultados consistentes en múltiples ejecuciones');
  });

  test('Validar estabilidad del algoritmo de correlación', async ({ page }) => {
    console.log('🧪 Validando estabilidad del algoritmo...');
    
    const executionResults = [];
    const targetNumbersFound = {};
    
    // Inicializar contadores
    TARGET_NUMBERS.forEach(num => targetNumbersFound[num] = 0);
    
    // Ejecutar análisis 3 veces
    for (let i = 1; i <= 3; i++) {
      console.log(`🔄 Ejecución ${i}/3...`);
      
      const results = await validator.executeFullCorrelationCycle();
      executionResults.push(results);
      
      // Contar ocurrencias de números objetivo
      TARGET_NUMBERS.forEach(targetNumber => {
        if (results.includes(targetNumber)) {
          targetNumbersFound[targetNumber]++;
        }
      });
      
      // Capturar evidencia
      await page.screenshot({ 
        path: `test-results/evidence/stability_execution_${i}_${new Date().toISOString().replace(/[:.]/g, '-')}.png`,
        fullPage: true 
      });
      
      await page.waitForTimeout(1000);
    }
    
    // Verificar que todos los números objetivo aparezcan en todas las ejecuciones
    console.log('📊 RESULTADOS DE ESTABILIDAD:');
    for (const [number, count] of Object.entries(targetNumbersFound)) {
      console.log(`🎯 ${number}: ${count}/3 ejecuciones`);
      expect(count).toBe(3); // Debe aparecer en las 3 ejecuciones
    }
    
    // Verificar consistencia general
    const firstExecution = executionResults[0];
    for (let i = 1; i < executionResults.length; i++) {
      const isConsistent = await validator.validateConsistentResults(firstExecution, executionResults[i]);
      expect(isConsistent).toBe(true);
    }
    
    console.log('🏆 Algoritmo ESTABLE: Todos los números objetivo aparecen consistentemente');
  });

  test('Validar tiempo de respuesta del algoritmo', async ({ page }) => {
    console.log('⏱️ Validando tiempo de respuesta del algoritmo...');
    
    const startTime = Date.now();
    
    await validator.executeFullCorrelationCycle();
    
    const endTime = Date.now();
    const executionTime = endTime - startTime;
    const executionTimeMinutes = executionTime / (1000 * 60);
    
    console.log(`⏱️ Tiempo de ejecución: ${executionTimeMinutes.toFixed(2)} minutos`);
    
    // El análisis no debe tomar más de 5 minutos
    expect(executionTimeMinutes).toBeLessThan(5);
    
    // Capturar evidencia del rendimiento
    await page.screenshot({ 
      path: `test-results/evidence/performance_validation_${new Date().toISOString().replace(/[:.]/g, '-')}.png`,
      fullPage: true 
    });
    
    console.log(`✅ Rendimiento validado: ${executionTimeMinutes.toFixed(2)} min < 5 min`);
  });

  test('Validar que no hay números con prefijo 57 en múltiples ejecuciones', async ({ page }) => {
    console.log('🔍 Validando ausencia de prefijo 57 en múltiples ejecuciones...');
    
    for (let i = 1; i <= 2; i++) {
      console.log(`🔄 Ejecución ${i}/2...`);
      
      const results = await validator.executeFullCorrelationCycle();
      
      // Verificar que ningún resultado tenga prefijo 57
      const numbersWithPrefix57 = results.filter(number => number.startsWith('57'));
      
      console.log(`🔍 Ejecución ${i}: ${results.length} números, ${numbersWithPrefix57.length} con prefijo 57`);
      
      if (numbersWithPrefix57.length > 0) {
        console.error(`❌ Números con prefijo 57 encontrados: ${numbersWithPrefix57.join(', ')}`);
      }
      
      expect(numbersWithPrefix57.length).toBe(0);
      
      await page.waitForTimeout(1000);
    }
    
    console.log('✅ Validación exitosa: No se encontraron números con prefijo 57 en ninguna ejecución');
  });
});