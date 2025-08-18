/**
 * Test Helpers para KRONOS - Playwright Testing Utilities
 * 
 * Funciones utilitarias reutilizables para tests de Playwright en KRONOS
 * Específicamente diseñadas para testing del algoritmo de correlación
 */

import { Page, expect } from '@playwright/test';
import path from 'path';

// Configuración base para tests
export const TEST_CONFIG = {
    baseUrl: 'http://localhost:8000',
    defaultTimeout: 30000,
    loginCredentials: {
        username: 'admin',
        password: 'admin123'
    },
    testDataPaths: {
        scanhunter: 'C:\\Soluciones\\BGC\\claude\\KNSOft\\archivos\\Copia de SCANHUNTER.csv',
        claroDatos: 'C:\\Soluciones\\BGC\\claude\\KNSOft\\datatest\\Claro\\DATOS_POR_CELDA CLARO.csv',
        claroEntrantes: 'C:\\Soluciones\\BGC\\claude\\KNSOft\\datatest\\Claro\\LLAMADAS_ENTRANTES_POR_CELDA CLARO.csv',
        claroSalientes: 'C:\\Soluciones\\BGC\\claude\\KNSOft\\datatest\\Claro\\LLAMADAS_SALIENTES_POR_CELDA CLARO.csv'
    }
};

/**
 * Navega a la aplicación KRONOS y verifica que cargue correctamente
 */
export async function navigateToApplication(page: Page): Promise<void> {
    console.log('🌐 Navegando a KRONOS...');
    
    await page.goto(TEST_CONFIG.baseUrl);
    await page.waitForLoadState('networkidle');
    
    // Verificar que la aplicación cargó
    await expect(page.locator('body')).toBeVisible();
    
    // Esperar que aparezca el contenido principal (login o dashboard)
    await page.waitForSelector('form, nav, [data-testid="app-content"]', { 
        timeout: TEST_CONFIG.defaultTimeout 
    });
    
    console.log('✅ Navegación exitosa');
}

/**
 * Realiza login en KRONOS
 */
export async function loginToKronos(page: Page, credentials = TEST_CONFIG.loginCredentials): Promise<void> {
    console.log('🔐 Realizando login...');
    
    try {
        // Verificar si ya estamos logueados (existe navbar)
        const navbar = page.locator('nav');
        if (await navbar.isVisible({ timeout: 5000 })) {
            console.log('✅ Ya logueado - navegando al dashboard');
            await page.goto(`${TEST_CONFIG.baseUrl}/#/dashboard`);
            return;
        }
    } catch (error) {
        // No estamos logueados, proceder con login
    }
    
    // Buscar formulario de login
    const usernameInput = page.locator('input[type="text"], input[name="username"], input[placeholder*="usuario" i]');
    const passwordInput = page.locator('input[type="password"], input[name="password"], input[placeholder*="contraseña" i]');
    const loginButton = page.locator('button[type="submit"], button:has-text("Ingresar"), button:has-text("Login")');
    
    await expect(usernameInput).toBeVisible({ timeout: 10000 });
    
    // Rellenar credenciales
    await usernameInput.fill(credentials.username);
    await passwordInput.fill(credentials.password);
    
    // Hacer login
    await loginButton.click();
    
    // Esperar redirección al dashboard
    await page.waitForURL('**/dashboard', { timeout: TEST_CONFIG.defaultTimeout });
    await page.waitForLoadState('networkidle');
    
    // Verificar que estamos en el dashboard
    await expect(page.locator('nav')).toBeVisible();
    
    console.log('✅ Login exitoso');
}

/**
 * Crea una misión de test para validaciones
 */
export async function createTestMission(page: Page, config: {
    name: string;
    description: string;
    code?: string;
}): Promise<string> {
    console.log('📝 Creando misión de test...');
    
    // Navegar a missions
    await page.goto(`${TEST_CONFIG.baseUrl}/#/missions`);
    await page.waitForLoadState('networkidle');
    
    // Verificar si ya existe una misión de test
    const existingMission = page.locator(`text="${config.name}"`);
    if (await existingMission.isVisible({ timeout: 5000 })) {
        console.log('📋 Misión de test ya existe, usando existente...');
        
        // Hacer clic en la misión existente
        await existingMission.click();
        
        // Extraer ID de la URL
        await page.waitForURL('**/missions/**');
        const url = page.url();
        const missionId = url.split('/').pop() || 'unknown';
        
        console.log(`✅ Usando misión existente: ${missionId}`);
        return missionId;
    }
    
    // Crear nueva misión
    const createButton = page.locator('button:has-text("Crear"), button:has-text("Nueva")');
    await createButton.click();
    
    // Rellenar formulario
    await page.locator('input[name="name"], input[placeholder*="nombre" i]').fill(config.name);
    await page.locator('input[name="code"], input[placeholder*="código" i]').fill(config.code || `TEST-${Date.now()}`);
    await page.locator('textarea[name="description"], textarea[placeholder*="descripción" i]').fill(config.description);
    
    // Guardar
    const saveButton = page.locator('button:has-text("Guardar"), button:has-text("Crear")');
    await saveButton.click();
    
    // Esperar redirección a detalle de misión
    await page.waitForURL('**/missions/**');
    const url = page.url();
    const missionId = url.split('/').pop() || 'unknown';
    
    console.log(`✅ Misión creada: ${missionId}`);
    return missionId;
}

/**
 * Sube archivo SCANHUNTER a una misión específica
 */
export async function uploadScanHunterFile(page: Page, missionId: string): Promise<void> {
    console.log('📤 Subiendo archivo SCANHUNTER...');
    
    // Navegar a la misión
    await page.goto(`${TEST_CONFIG.baseUrl}/#/missions/${missionId}`);
    await page.waitForLoadState('networkidle');
    
    // Ir a pestaña de datos celulares
    const cellularTab = page.locator('button:has-text("Datos Celulares")');
    await cellularTab.click();
    
    // Verificar si ya hay datos
    const dataTable = page.locator('table');
    if (await dataTable.isVisible({ timeout: 5000 })) {
        console.log('✅ Datos SCANHUNTER ya existen');
        return;
    }
    
    // Buscar input de archivo
    const fileInput = page.locator('input[type="file"]');
    await expect(fileInput).toBeVisible();
    
    // Subir archivo
    await fileInput.setInputFiles(TEST_CONFIG.testDataPaths.scanhunter);
    
    // Esperar procesamiento
    await page.waitForSelector('table, text="Error", text="Procesado"', { 
        timeout: 60000 
    });
    
    console.log('✅ Archivo SCANHUNTER subido');
}

/**
 * Sube archivos de operador (CLARO, MOVISTAR, etc.)
 */
export async function uploadOperatorFile(page: Page, missionId: string, config: {
    operator: 'CLARO' | 'MOVISTAR' | 'TIGO' | 'WOM';
    fileType: 'DATOS' | 'LLAMADAS_ENTRANTES' | 'LLAMADAS_SALIENTES' | 'VOZ' | 'REPORTE';
    filePath?: string;
}): Promise<void> {
    console.log(`📤 Subiendo archivo ${config.operator} - ${config.fileType}...`);
    
    // Navegar a la misión
    await page.goto(`${TEST_CONFIG.baseUrl}/#/missions/${missionId}`);
    await page.waitForLoadState('networkidle');
    
    // Ir a pestaña de datos de operador
    const operatorTab = page.locator('button:has-text("Datos de Operador")');
    await operatorTab.click();
    
    // Seleccionar operador
    const operatorSelect = page.locator('select[name="operator"], select:has(option:text("CLARO"))');
    await operatorSelect.selectOption(config.operator);
    
    // Seleccionar tipo de documento
    const documentTypeSelect = page.locator('select[name="documentType"]');
    await documentTypeSelect.selectOption({ label: new RegExp(config.fileType, 'i') });
    
    // Subir archivo
    const fileInput = page.locator('input[type="file"]');
    const filePath = config.filePath || getOperatorFilePath(config.operator, config.fileType);
    await fileInput.setInputFiles(filePath);
    
    // Hacer clic en cargar
    const uploadButton = page.locator('button:has-text("Cargar"), button:has-text("Subir")');
    await uploadButton.click();
    
    // Esperar procesamiento
    await page.waitForSelector('text="Procesamiento completado", text="Error", .notification', { 
        timeout: 120000 
    });
    
    console.log(`✅ Archivo ${config.operator} subido`);
}

/**
 * Obtiene la ruta del archivo de operador según tipo
 */
function getOperatorFilePath(operator: string, fileType: string): string {
    const basePath = 'C:\\Soluciones\\BGC\\claude\\KNSOft\\datatest';
    
    switch (operator) {
        case 'CLARO':
            switch (fileType) {
                case 'DATOS':
                    return `${basePath}\\Claro\\DATOS_POR_CELDA CLARO.csv`;
                case 'LLAMADAS_ENTRANTES':
                    return `${basePath}\\Claro\\LLAMADAS_ENTRANTES_POR_CELDA CLARO.csv`;
                case 'LLAMADAS_SALIENTES':
                    return `${basePath}\\Claro\\LLAMADAS_SALIENTES_POR_CELDA CLARO.csv`;
            }
            break;
        case 'MOVISTAR':
            switch (fileType) {
                case 'DATOS':
                    return `${basePath}\\Movistar\\jgd202410754_00007301_datos_ MOVISTAR.csv`;
                case 'VOZ':
                    return `${basePath}\\Movistar\\jgd202410754_07F08305_vozm_saliente_ MOVISTAR.csv`;
            }
            break;
        case 'TIGO':
            return `${basePath}\\Tigo\\Reporte TIGO.csv`;
        case 'WOM':
            switch (fileType) {
                case 'DATOS':
                    return `${basePath}\\wom\\PUNTO 1 TRÁFICO DATOS WOM.csv`;
                case 'VOZ':
                    return `${basePath}\\wom\\PUNTO 1 TRÁFICO VOZ ENTRAN  SALIENT WOM.csv`;
            }
            break;
    }
    
    throw new Error(`No se encontró archivo para ${operator} - ${fileType}`);
}

/**
 * Navega a la sección de análisis de correlación
 */
export async function navigateToCorrelationAnalysis(page: Page, missionId: string): Promise<void> {
    console.log('🔍 Navegando a análisis de correlación...');
    
    await page.goto(`${TEST_CONFIG.baseUrl}/#/missions/${missionId}`);
    await page.waitForLoadState('networkidle');
    
    // Ir a pestaña de análisis
    const analysisTab = page.locator('button:has-text("Posibles Objetivos"), button:has-text("Análisis")');
    await analysisTab.click();
    
    // Seleccionar modo correlación
    const correlationRadio = page.locator('input[value="correlation"]');
    await correlationRadio.check();
    
    console.log('✅ En análisis de correlación');
}

/**
 * Configura y ejecuta análisis de correlación
 */
export async function executeCorrelationAnalysis(page: Page, config: {
    startDate: string;
    endDate: string;
    minCoincidences: number;
}): Promise<void> {
    console.log('⚙️ Configurando análisis de correlación...');
    
    // Configurar fechas
    await page.locator('input[type="datetime-local"]').first().fill(config.startDate);
    await page.locator('input[type="datetime-local"]').nth(1).fill(config.endDate);
    
    // Configurar coincidencias mínimas
    await page.locator('input[type="number"]').fill(config.minCoincidences.toString());
    
    // Ejecutar análisis
    const executeButton = page.locator('button:has-text("Ejecutar Análisis")');
    await executeButton.click();
    
    console.log('🚀 Análisis iniciado, esperando resultados...');
    
    // Esperar que termine el análisis
    await page.waitForSelector('text=Analizando...', { timeout: 5000 });
    await page.waitForSelector('text=Analizando...', { state: 'hidden', timeout: 120000 });
    
    console.log('✅ Análisis completado');
}

/**
 * Valida la presencia de un número específico en los resultados
 */
export async function validateNumberInResults(page: Page, phoneNumber: string): Promise<{
    found: boolean;
    details?: string;
}> {
    const numberRow = page.locator(`tr:has-text("${phoneNumber}")`);
    const found = await numberRow.isVisible();
    
    if (found) {
        const details = await numberRow.textContent();
        return { found: true, details: details || undefined };
    }
    
    return { found: false };
}

/**
 * Captura screenshot con timestamp para evidencia
 */
export async function captureEvidence(page: Page, filename: string): Promise<string> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const fullFilename = `${filename}_${timestamp}.png`;
    const path = `Backend/test_evidence_screenshots/${fullFilename}`;
    
    await page.screenshot({
        path,
        fullPage: true
    });
    
    console.log(`📸 Evidencia capturada: ${fullFilename}`);
    return path;
}

/**
 * Espera a que el backend de KRONOS esté disponible
 */
export async function waitForKronosBackend(page: Page, maxAttempts = 10): Promise<boolean> {
    console.log('⏳ Esperando backend de KRONOS...');
    
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
            const response = await page.goto(TEST_CONFIG.baseUrl);
            if (response && response.ok()) {
                console.log('✅ Backend de KRONOS disponible');
                return true;
            }
        } catch (error) {
            console.log(`❌ Intento ${attempt}/${maxAttempts} falló`);
            if (attempt < maxAttempts) {
                await page.waitForTimeout(2000);
            }
        }
    }
    
    console.log('❌ Backend de KRONOS no disponible');
    return false;
}

/**
 * Extrae datos de la tabla de resultados
 */
export async function extractResultsTableData(page: Page): Promise<Array<Record<string, string>>> {
    const table = page.locator('table');
    
    if (!await table.isVisible()) {
        return [];
    }
    
    // Extraer headers
    const headers = await page.locator('table th').allTextContents();
    
    // Extraer filas de datos
    const rows = await page.locator('table tbody tr').all();
    const data: Array<Record<string, string>> = [];
    
    for (const row of rows) {
        const cells = await row.locator('td').allTextContents();
        const rowData: Record<string, string> = {};
        
        headers.forEach((header, index) => {
            rowData[header] = cells[index] || '';
        });
        
        data.push(rowData);
    }
    
    return data;
}

/**
 * Limpia datos de test después de la ejecución
 */
export async function cleanupTestData(page: Page, missionId: string): Promise<void> {
    console.log('🧹 Limpiando datos de test...');
    
    try {
        // Navegar a missions
        await page.goto(`${TEST_CONFIG.baseUrl}/#/missions`);
        
        // Buscar y eliminar misión de test
        const missionRow = page.locator(`tr:has-text("Test Correlación")`);
        if (await missionRow.isVisible({ timeout: 5000 })) {
            const deleteButton = missionRow.locator('button:has-text("Eliminar"), button[title*="eliminar" i]');
            if (await deleteButton.isVisible()) {
                await deleteButton.click();
                
                // Confirmar eliminación
                const confirmButton = page.locator('button:has-text("Confirmar"), button:has-text("Eliminar"), button:has-text("Sí")');
                if (await confirmButton.isVisible({ timeout: 5000 })) {
                    await confirmButton.click();
                }
            }
        }
        
        console.log('✅ Limpieza completada');
    } catch (error) {
        console.log('⚠️ Error en limpieza:', error);
    }
}