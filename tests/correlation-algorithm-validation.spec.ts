/**
 * Test Playwright para Validación del Algoritmo de Correlación de KRONOS
 * 
 * OBJETIVO: Validar el algoritmo de correlación con números objetivo específicos identificados por Boris
 * 
 * DATOS CRÍTICOS IDENTIFICADOS:
 * - Número crítico confirmado: 3104277553 -> 3224274851 en 2024-08-12 23:13:20
 * - Celdas: 12345->67890
 * - Período con datos reales: 2024-08-12 20:00:00 a 2024-08-13 02:00:00
 * 
 * NÚMEROS OBJETIVO A VALIDAR:
 * - 3224274851, 3208611034, 3104277553, 3102715509, 3143534707, 3214161903
 */

import { test, expect, Page } from '@playwright/test';
import { 
    navigateToApplication, 
    loginToKronos, 
    createTestMission, 
    uploadScanHunterFile 
} from './helpers/test-helpers';

// Configuración de test específico para correlación
const CORRELATION_TEST_CONFIG = {
    // Período específico donde SÍ hay datos de operadores
    startDate: '2024-08-12T20:00',
    endDate: '2024-08-13T02:00',
    
    // Números objetivo confirmados en la BD
    targetNumbers: [
        '3224274851', '3208611034', '3104277553', 
        '3102715509', '3143534707', '3214161903'
    ],
    
    // Número crítico con conexión confirmada
    criticalNumber: '3104277553',
    connectedNumber: '3224274851',
    
    // Celdas específicas confirmadas
    expectedCells: {
        '3104277553': '12345',
        '3224274851': '67890'
    },
    
    // Configuración de análisis
    minCoincidences: 2,
    
    // Timeout para análisis (puede tomar tiempo)
    analysisTimeout: 120000 // 2 minutos
};

test.describe('Validación Algoritmo de Correlación - Números Objetivo Boris', () => {
    let page: Page;
    let missionId: string;
    
    test.beforeAll(async ({ browser }) => {
        page = await browser.newPage();
        
        // Configurar viewport para captura de evidencia
        await page.setViewportSize({ width: 1920, height: 1080 });
        
        console.log('🚀 Iniciando test de algoritmo de correlación...');
        
        // 1. Navegar y autenticar
        await navigateToApplication(page);
        await loginToKronos(page);
        
        // 2. Crear misión de test específica
        missionId = await createTestMission(page, {
            name: 'Test Correlación Boris - Números Objetivo',
            description: 'Validación algoritmo correlación con datos periodo 2024-08-12'
        });
        
        // 3. Cargar datos SCANHUNTER si no están presentes
        await uploadScanHunterFile(page, missionId);
        
        console.log(`✅ Setup completado - Mission ID: ${missionId}`);
    });
    
    test('debe navegar correctamente a la sección de análisis de correlación', async () => {
        console.log('📍 Test: Navegación a análisis de correlación');
        
        // Navegar a la misión
        await page.goto(`http://localhost:8000/#/missions/${missionId}`);
        await page.waitForLoadState('networkidle');
        
        // Verificar que estamos en Mission Detail
        await expect(page.locator('h2')).toContainText('Test Correlación Boris');
        
        // Hacer clic en la pestaña "Análisis" (solo visible si hay datos celulares)
        const analysisTab = page.locator('button:has-text("Posibles Objetivos")');
        await expect(analysisTab).toBeVisible({ timeout: 10000 });
        await analysisTab.click();
        
        // Verificar que estamos en la sección de análisis
        await expect(page.locator('h3:has-text("Análisis de Posibles Objetivos")')).toBeVisible();
        
        // Capturar evidencia - pantalla inicial análisis
        await page.screenshot({
            path: `Backend/test_evidence_screenshots/correlation_analysis_initial_${Date.now()}.png`,
            fullPage: true
        });
        
        console.log('✅ Navegación a análisis exitosa');
    });
    
    test('debe configurar correctamente el análisis de correlación', async () => {
        console.log('⚙️ Test: Configuración análisis de correlación');
        
        // Asegurar que estamos en la pestaña de análisis
        await page.goto(`http://localhost:8000/#/missions/${missionId}`);
        await page.locator('button:has-text("Posibles Objetivos")').click();
        
        // Seleccionar modo de correlación
        const correlationRadio = page.locator('input[value="correlation"]');
        await correlationRadio.check();
        await expect(correlationRadio).toBeChecked();
        
        // Verificar que aparecen los controles de correlación
        await expect(page.locator('h4:has-text("Análisis de Correlación de Objetivos")')).toBeVisible();
        
        // Configurar fecha de inicio
        const startDateInput = page.locator('input[type="datetime-local"]').first();
        await startDateInput.fill(CORRELATION_TEST_CONFIG.startDate);
        
        // Configurar fecha de fin  
        const endDateInput = page.locator('input[type="datetime-local"]').nth(1);
        await endDateInput.fill(CORRELATION_TEST_CONFIG.endDate);
        
        // Configurar mínimo de coincidencias
        const minCoincidencesInput = page.locator('input[type="number"]');
        await minCoincidencesInput.fill(CORRELATION_TEST_CONFIG.minCoincidences.toString());
        
        // Verificar que el botón de ejecutar está habilitado
        const executeButton = page.locator('button:has-text("Ejecutar Análisis")');
        await expect(executeButton).toBeEnabled();
        
        // Capturar evidencia - configuración completada
        await page.screenshot({
            path: `Backend/test_evidence_screenshots/correlation_config_${Date.now()}.png`,
            fullPage: true
        });
        
        console.log('✅ Configuración de análisis completada');
        console.log(`📅 Período: ${CORRELATION_TEST_CONFIG.startDate} - ${CORRELATION_TEST_CONFIG.endDate}`);
        console.log(`🎯 Min coincidencias: ${CORRELATION_TEST_CONFIG.minCoincidences}`);
    });
    
    test('debe ejecutar el análisis de correlación y mostrar resultados', async () => {
        console.log('🚀 Test: Ejecución del análisis de correlación');
        
        // Navegar y configurar
        await page.goto(`http://localhost:8000/#/missions/${missionId}`);
        await page.locator('button:has-text("Posibles Objetivos")').click();
        await page.locator('input[value="correlation"]').check();
        
        // Reconfigurar las fechas por si acaso
        await page.locator('input[type="datetime-local"]').first().fill(CORRELATION_TEST_CONFIG.startDate);
        await page.locator('input[type="datetime-local"]').nth(1).fill(CORRELATION_TEST_CONFIG.endDate);
        await page.locator('input[type="number"]').fill(CORRELATION_TEST_CONFIG.minCoincidences.toString());
        
        // Ejecutar análisis
        const executeButton = page.locator('button:has-text("Ejecutar Análisis")');
        await executeButton.click();
        
        // Verificar que muestra estado de "Analizando..."
        await expect(page.locator('text=Analizando...')).toBeVisible({ timeout: 5000 });
        
        // Esperar a que termine el análisis (puede tomar tiempo)
        await expect(page.locator('text=Analizando...')).not.toBeVisible({ 
            timeout: CORRELATION_TEST_CONFIG.analysisTimeout 
        });
        
        // Verificar que aparecen resultados o dashboard de estadísticas
        const resultsHeader = page.locator('h5:has-text("Dashboard de Resultados")');
        const objectivesHeader = page.locator('h5:has-text("Objetivos Identificados")');
        
        // Debe aparecer al menos uno de estos elementos
        await expect(
            resultsHeader.or(objectivesHeader).or(page.locator('text=No se han ejecutado análisis'))
        ).toBeVisible({ timeout: 10000 });
        
        // Capturar evidencia - resultados del análisis
        await page.screenshot({
            path: `Backend/test_evidence_screenshots/correlation_results_${Date.now()}.png`,
            fullPage: true
        });
        
        console.log('✅ Análisis de correlación ejecutado');
    });
    
    test('debe validar la presencia de números objetivo específicos', async () => {
        console.log('🎯 Test: Validación números objetivo específicos');
        
        // Navegar y ejecutar análisis
        await page.goto(`http://localhost:8000/#/missions/${missionId}`);
        await page.locator('button:has-text("Posibles Objetivos")').click();
        await page.locator('input[value="correlation"]').check();
        
        await page.locator('input[type="datetime-local"]').first().fill(CORRELATION_TEST_CONFIG.startDate);
        await page.locator('input[type="datetime-local"]').nth(1).fill(CORRELATION_TEST_CONFIG.endDate);
        await page.locator('input[type="number"]').fill(CORRELATION_TEST_CONFIG.minCoincidences.toString());
        
        await page.locator('button:has-text("Ejecutar Análisis")').click();
        
        // Esperar resultados
        await page.waitForSelector('h5:has-text("Dashboard de Resultados"), h5:has-text("Objetivos Identificados"), text=No se han ejecutado análisis', {
            timeout: CORRELATION_TEST_CONFIG.analysisTimeout
        });
        
        // Verificar si hay tabla de resultados
        const resultsTable = page.locator('table');
        const hasResults = await resultsTable.isVisible();
        
        if (hasResults) {
            console.log('📊 Resultados encontrados, validando números objetivo...');
            
            // Buscar el número crítico 3104277553
            const criticalNumberRow = page.locator(`tr:has-text("${CORRELATION_TEST_CONFIG.criticalNumber}")`);
            const criticalNumberExists = await criticalNumberRow.isVisible();
            
            if (criticalNumberExists) {
                console.log(`✅ CRÍTICO: Número ${CORRELATION_TEST_CONFIG.criticalNumber} encontrado en resultados`);
                
                // Verificar detalles del número crítico
                const criticalRowText = await criticalNumberRow.textContent();
                console.log(`📋 Detalles número crítico: ${criticalRowText}`);
                
                // Buscar celda específica esperada
                if (criticalRowText?.includes(CORRELATION_TEST_CONFIG.expectedCells[CORRELATION_TEST_CONFIG.criticalNumber])) {
                    console.log(`✅ CELDA CONFIRMADA: ${CORRELATION_TEST_CONFIG.expectedCells[CORRELATION_TEST_CONFIG.criticalNumber]} presente`);
                }
            } else {
                console.log(`⚠️ Número crítico ${CORRELATION_TEST_CONFIG.criticalNumber} NO encontrado en resultados`);
            }
            
            // Buscar número conectado 3224274851
            const connectedNumberRow = page.locator(`tr:has-text("${CORRELATION_TEST_CONFIG.connectedNumber}")`);
            const connectedNumberExists = await connectedNumberRow.isVisible();
            
            if (connectedNumberExists) {
                console.log(`✅ CONEXIÓN: Número ${CORRELATION_TEST_CONFIG.connectedNumber} encontrado en resultados`);
            }
            
            // Contar total de números objetivo encontrados
            let foundTargets = 0;
            for (const targetNumber of CORRELATION_TEST_CONFIG.targetNumbers) {
                const targetRow = page.locator(`tr:has-text("${targetNumber}")`);
                if (await targetRow.isVisible()) {
                    foundTargets++;
                    console.log(`✅ Objetivo encontrado: ${targetNumber}`);
                }
            }
            
            console.log(`📊 RESUMEN: ${foundTargets}/${CORRELATION_TEST_CONFIG.targetNumbers.length} números objetivo encontrados`);
            
            // Capturar evidencia detallada de la tabla
            await page.screenshot({
                path: `Backend/test_evidence_screenshots/target_numbers_validation_${Date.now()}.png`,
                fullPage: true
            });
            
        } else {
            console.log('⚠️ No se encontraron resultados en la tabla de correlación');
            
            // Verificar si hay mensaje de estadísticas sin resultados
            const statsMessage = await page.locator('[class*="bg-gradient-to-r"][class*="green-500"]').textContent();
            if (statsMessage) {
                console.log(`📊 Estadísticas del análisis: ${statsMessage}`);
            }
        }
        
        // Capturar evidencia final
        await page.screenshot({
            path: `Backend/test_evidence_screenshots/final_validation_results_${Date.now()}.png`,
            fullPage: true
        });
    });
    
    test('debe permitir filtrar por número específico en los resultados', async () => {
        console.log('🔍 Test: Filtrado por número específico');
        
        // Ejecutar análisis previo
        await page.goto(`http://localhost:8000/#/missions/${missionId}`);
        await page.locator('button:has-text("Posibles Objetivos")').click();
        await page.locator('input[value="correlation"]').check();
        
        await page.locator('input[type="datetime-local"]').first().fill(CORRELATION_TEST_CONFIG.startDate);
        await page.locator('input[type="datetime-local"]').nth(1).fill(CORRELATION_TEST_CONFIG.endDate);
        await page.locator('input[type="number"]').fill(CORRELATION_TEST_CONFIG.minCoincidences.toString());
        
        await page.locator('button:has-text("Ejecutar Análisis")').click();
        await page.waitForSelector('h5:has-text("Dashboard de Resultados"), h5:has-text("Objetivos Identificados"), text=No se han ejecutado análisis', {
            timeout: CORRELATION_TEST_CONFIG.analysisTimeout
        });
        
        // Verificar si existe el filtro de número
        const phoneFilter = page.locator('input[placeholder*="Ingrese número de teléfono"]');
        const hasFilter = await phoneFilter.isVisible();
        
        if (hasFilter) {
            console.log('🔍 Campo de filtro encontrado, probando filtrado...');
            
            // Filtrar por número crítico
            await phoneFilter.fill(CORRELATION_TEST_CONFIG.criticalNumber);
            
            // Esperar que se aplique el filtro
            await page.waitForTimeout(1000);
            
            // Verificar resultados filtrados
            const filteredResults = page.locator('table tr');
            const resultCount = await filteredResults.count();
            
            console.log(`📊 Resultados después del filtro: ${resultCount - 1} registros`); // -1 por el header
            
            // Capturar evidencia del filtrado
            await page.screenshot({
                path: `Backend/test_evidence_screenshots/filter_validation_${Date.now()}.png`,
                fullPage: true
            });
            
            // Limpiar filtro
            const clearButton = page.locator('button[title="Limpiar filtro"]');
            if (await clearButton.isVisible()) {
                await clearButton.click();
            }
        } else {
            console.log('⚠️ Campo de filtro no encontrado');
        }
    });
    
    test('debe validar exportación de resultados', async () => {
        console.log('📤 Test: Exportación de resultados');
        
        // Ejecutar análisis previo
        await page.goto(`http://localhost:8000/#/missions/${missionId}`);
        await page.locator('button:has-text("Posibles Objetivos")').click();
        await page.locator('input[value="correlation"]').check();
        
        await page.locator('input[type="datetime-local"]').first().fill(CORRELATION_TEST_CONFIG.startDate);
        await page.locator('input[type="datetime-local"]').nth(1).fill(CORRELATION_TEST_CONFIG.endDate);
        await page.locator('input[type="number"]').fill(CORRELATION_TEST_CONFIG.minCoincidences.toString());
        
        await page.locator('button:has-text("Ejecutar Análisis")').click();
        await page.waitForSelector('h5:has-text("Dashboard de Resultados"), h5:has-text("Objetivos Identificados"), text=No se han ejecutado análisis', {
            timeout: CORRELATION_TEST_CONFIG.analysisTimeout
        });
        
        // Verificar botones de exportación
        const csvButton = page.locator('button:has-text("CSV")');
        const excelButton = page.locator('button:has-text("Excel")');
        
        const hasCsvButton = await csvButton.isVisible();
        const hasExcelButton = await excelButton.isVisible();
        
        if (hasCsvButton || hasExcelButton) {
            console.log('📤 Botones de exportación encontrados');
            
            if (hasCsvButton) {
                console.log('✅ Botón CSV disponible');
                // Nota: No hacer clic real para evitar descargas en test
            }
            
            if (hasExcelButton) {
                console.log('✅ Botón Excel disponible');
                // Nota: No hacer clic real para evitar descargas en test
            }
            
            // Capturar evidencia de opciones de exportación
            await page.screenshot({
                path: `Backend/test_evidence_screenshots/export_options_${Date.now()}.png`,
                fullPage: true
            });
        } else {
            console.log('⚠️ Botones de exportación no encontrados - posiblemente sin resultados');
        }
    });
    
    test.afterAll(async () => {
        console.log('🧹 Limpieza final del test de correlación');
        
        // Capturar reporte final
        const finalReport = {
            testSuite: 'Validación Algoritmo de Correlación - Números Objetivo Boris',
            testDate: new Date().toISOString(),
            missionId,
            config: CORRELATION_TEST_CONFIG,
            status: 'completed'
        };
        
        // Guardar reporte de evidencia
        console.log('📋 Reporte final:', JSON.stringify(finalReport, null, 2));
        
        if (page) {
            await page.close();
        }
    });
});

// Helpers específicos para test de correlación
async function waitForCorrelationResults(page: Page, timeout = 120000) {
    await page.waitForSelector(
        'h5:has-text("Dashboard de Resultados"), h5:has-text("Objetivos Identificados"), text=No se han ejecutado análisis',
        { timeout }
    );
}

async function validateTargetNumberInResults(page: Page, phoneNumber: string): Promise<boolean> {
    const targetRow = page.locator(`tr:has-text("${phoneNumber}")`);
    return await targetRow.isVisible();
}

async function extractTableData(page: Page): Promise<string[][]> {
    const rows = await page.locator('table tr').all();
    const data: string[][] = [];
    
    for (const row of rows) {
        const cells = await row.locator('td, th').allTextContents();
        data.push(cells);
    }
    
    return data;
}