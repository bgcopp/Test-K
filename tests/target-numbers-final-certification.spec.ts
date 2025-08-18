import { test, expect } from '@playwright/test';
import { Page } from '@playwright/test';

/**
 * TEST DE CERTIFICACIÓN FINAL - NÚMEROS OBJETIVO
 * 
 * Criterios de Éxito:
 * - Los 5 números objetivo deben aparecer en resultados
 * - Formato sin prefijo 57: "3224274851" no "573224274851"
 * - Coincidencias correctas para cada número
 * - No debe mostrar "0 de 88 resultados"
 * 
 * Números Objetivo Esperados:
 * - 3143534707 (3 coincidencias)
 * - 3224274851 (2 coincidencias)
 * - 3208611034 (2 coincidencias) 
 * - 3214161903 (1 coincidencia)
 * - 3102715509 (1 coincidencia)
 */

// Configuración del test
const TARGET_NUMBERS = [
    { number: '3143534707', expectedCoincidences: 3 },
    { number: '3224274851', expectedCoincidences: 2 },
    { number: '3208611034', expectedCoincidences: 2 },
    { number: '3214161903', expectedCoincidences: 1 },
    { number: '3102715509', expectedCoincidences: 1 }
];

const MISSION_CONFIG = {
    missionId: 'mission_MPFRBNsb',
    startDate: '2021-05-20T10:00',
    endDate: '2021-05-20T14:30',
    minCoincidences: 1
};

test.describe('Certificación Final - Números Objetivo', () => {
    
    test.beforeEach(async ({ page }) => {
        console.log('🚀 Iniciando certificación final de números objetivo...');
        
        // Configurar timeouts extendidos para aplicación desktop
        page.setDefaultTimeout(60000);
        page.setDefaultNavigationTimeout(60000);
    });

    test('Debe encontrar todos los números objetivo en la UI de KRONOS', async ({ page }) => {
        
        // PASO 1: Iniciar aplicación KRONOS
        console.log('📱 PASO 1: Navegando a KRONOS...');
        await page.goto('http://localhost:8081', { waitUntil: 'networkidle' });
        
        // Esperar que la aplicación cargue
        await expect(page.locator('text=KRONOS')).toBeVisible({ timeout: 30000 });
        console.log('✅ Aplicación KRONOS iniciada correctamente');
        
        // PASO 2: Verificar que estamos en el login o ya autenticados
        const isLoginPage = await page.locator('input[type="password"]').isVisible();
        if (isLoginPage) {
            console.log('🔐 Realizando login...');
            await page.fill('input[type="text"]', 'admin');
            await page.fill('input[type="password"]', 'admin123');
            await page.click('button[type="submit"]');
            await page.waitForLoadState('networkidle');
        }
        
        // PASO 3: Navegar a misiones
        console.log('📋 PASO 3: Navegando a misiones...');
        await page.click('text=Misiones');
        await page.waitForLoadState('networkidle');
        
        // PASO 4: Seleccionar misión específica MPFRBNsb
        console.log('🎯 PASO 4: Seleccionando misión MPFRBNsb...');
        const missionRow = page.locator(`tr:has-text("${MISSION_CONFIG.missionId}")`);
        await expect(missionRow).toBeVisible({ timeout: 15000 });
        await missionRow.click();
        await page.waitForLoadState('networkidle');
        
        // PASO 5: Ir a análisis de correlación
        console.log('🔍 PASO 5: Navegando a análisis de correlación...');
        await page.click('text=Posibles Objetivos');
        await page.waitForLoadState('networkidle');
        
        // Seleccionar análisis de correlación
        await page.check('input[value="correlation"]');
        await page.waitForTimeout(1000);
        
        // PASO 6: Configurar parámetros exactos
        console.log('⚙️ PASO 6: Configurando parámetros de análisis...');
        
        // Configurar fecha de inicio
        await page.fill('input[type="datetime-local"]', MISSION_CONFIG.startDate);
        await page.waitForTimeout(500);
        
        // Configurar fecha de fin - buscar el segundo input datetime-local
        const endDateInput = page.locator('input[type="datetime-local"]').nth(1);
        await endDateInput.fill(MISSION_CONFIG.endDate);
        await page.waitForTimeout(500);
        
        // Configurar mínimo de coincidencias
        await page.fill('input[type="number"]', MISSION_CONFIG.minCoincidences.toString());
        await page.waitForTimeout(500);
        
        console.log(`📅 Configuración aplicada:
        - Fecha inicio: ${MISSION_CONFIG.startDate}
        - Fecha fin: ${MISSION_CONFIG.endDate}
        - Mín. coincidencias: ${MISSION_CONFIG.minCoincidences}`);
        
        // PASO 7: Ejecutar análisis
        console.log('🚀 PASO 7: Ejecutando análisis de correlación...');
        const executeButton = page.locator('button:has-text("Ejecutar Análisis")');
        await executeButton.click();
        
        // Esperar a que complete el análisis (máximo 2 minutos)
        await page.waitForSelector('text=Análisis de Correlación Completado', { timeout: 120000 });
        console.log('✅ Análisis completado exitosamente');
        
        // PASO 8: Verificar que aparecen los números objetivo
        console.log('🎯 PASO 8: Verificando presencia de números objetivo...');
        
        // Esperar a que aparezca la tabla de resultados
        await expect(page.locator('table')).toBeVisible({ timeout: 30000 });
        
        // Capturar screenshot de evidencia
        await page.screenshot({ 
            path: `tests/evidence/certification-final-${Date.now()}.png`,
            fullPage: true 
        });
        
        // Verificar cada número objetivo
        let foundNumbers = 0;
        const verificationResults = [];
        
        for (const targetNumber of TARGET_NUMBERS) {
            console.log(`🔍 Verificando número: ${targetNumber.number}...`);
            
            // Buscar el número en la tabla
            const numberCell = page.locator(`td:has-text("${targetNumber.number}")`);
            const isVisible = await numberCell.isVisible();
            
            if (isVisible) {
                foundNumbers++;
                
                // Verificar formato sin prefijo 57
                const cellText = await numberCell.textContent();
                const hasCorrectFormat = cellText === targetNumber.number;
                
                // Verificar coincidencias (buscar en la fila del número)
                const row = page.locator(`tr:has(td:text-is("${targetNumber.number}"))`);
                const coincidencesCell = row.locator('td').nth(1); // Segunda columna
                const coincidencesText = await coincidencesCell.textContent();
                const actualCoincidences = parseInt(coincidencesText?.trim() || '0');
                
                verificationResults.push({
                    number: targetNumber.number,
                    found: true,
                    correctFormat: hasCorrectFormat,
                    expectedCoincidences: targetNumber.expectedCoincidences,
                    actualCoincidences,
                    coincidencesMatch: actualCoincidences === targetNumber.expectedCoincidences
                });
                
                console.log(`✅ ${targetNumber.number}: Encontrado con ${actualCoincidences} coincidencias (esperadas: ${targetNumber.expectedCoincidences})`);
            } else {
                verificationResults.push({
                    number: targetNumber.number,
                    found: false,
                    correctFormat: false,
                    expectedCoincidences: targetNumber.expectedCoincidences,
                    actualCoincidences: 0,
                    coincidencesMatch: false
                });
                console.log(`❌ ${targetNumber.number}: NO encontrado`);
            }
        }
        
        // PASO 9: Verificar que NO muestra "0 de 88 resultados"
        console.log('📊 PASO 9: Verificando que hay resultados...');
        const noResultsText = page.locator('text=0 de');
        const hasNoResults = await noResultsText.isVisible();
        
        // PASO 10: Generar reporte de certificación
        console.log('📋 PASO 10: Generando reporte de certificación...');
        
        console.log(`
        ==========================================
        🏆 REPORTE DE CERTIFICACIÓN FINAL
        ==========================================
        
        📊 RESUMEN:
        - Números objetivo encontrados: ${foundNumbers}/5
        - Números faltantes: ${5 - foundNumbers}
        - Sin resultados vacíos: ${!hasNoResults ? '✅ SÍ' : '❌ NO'}
        
        📋 DETALLE POR NÚMERO:
        ${verificationResults.map(result => `
        ${result.found ? '✅' : '❌'} ${result.number}:
           - Encontrado: ${result.found ? 'SÍ' : 'NO'}
           - Formato correcto: ${result.correctFormat ? 'SÍ' : 'NO'}
           - Coincidencias: ${result.actualCoincidences}/${result.expectedCoincidences} ${result.coincidencesMatch ? '✅' : '❌'}
        `).join('')}
        
        🎯 CRITERIOS DE ÉXITO:
        ${foundNumbers === 5 ? '✅' : '❌'} Todos los números objetivo presentes
        ${verificationResults.every(r => r.correctFormat) ? '✅' : '❌'} Formato sin prefijo 57
        ${verificationResults.every(r => r.coincidencesMatch) ? '✅' : '❌'} Coincidencias correctas
        ${!hasNoResults ? '✅' : '❌'} Resultados no vacíos
        
        ==========================================
        `);
        
        // Aserciones finales para el test
        expect(foundNumbers).toBe(5); // Todos los números deben estar presentes
        expect(hasNoResults).toBe(false); // No debe mostrar 0 resultados
        
        // Verificar formato correcto para todos los números
        for (const result of verificationResults) {
            expect(result.found).toBe(true);
            expect(result.correctFormat).toBe(true);
            expect(result.coincidencesMatch).toBe(true);
        }
        
        console.log('🎉 ¡CERTIFICACIÓN FINAL COMPLETADA EXITOSAMENTE!');
    });
    
    test.afterEach(async ({ page }) => {
        // Capturar evidencia final
        await page.screenshot({ 
            path: `tests/evidence/final-state-${Date.now()}.png`,
            fullPage: true 
        });
    });
});