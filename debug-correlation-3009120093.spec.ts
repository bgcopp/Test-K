/**
 * Prueba Playwright para Debugging Crítico del Número 3009120093
 * 
 * OBJETIVO: Interceptar todas las llamadas de red y analizar exactamente
 * qué datos está devolviendo el backend vs qué está procesando el frontend
 * 
 * PROBLEMA: 254 nodos se siguen mostrando después de todas las correcciones
 */

import { test, expect, Page } from '@playwright/test';

interface CorrelationApiResponse {
    success: boolean;
    data: Array<{
        targetNumber: string;
        operator: string;
        occurrences: number;
        relatedCells: string[];
        confidence: number;
        firstDetection: string;
        lastDetection: string;
    }>;
    error?: string;
    metadata?: {
        totalRecords: number;
        filteredRecords: number;
        targetNumber: string;
    };
}

interface NetworkCall {
    url: string;
    method: string;
    requestData?: any;
    responseData?: any;
    status: number;
    timestamp: number;
}

test.describe('🚨 DEBUG CRÍTICO: Análisis 3009120093 - Problema 254 Nodos', () => {
    let page: Page;
    let networkCalls: NetworkCall[] = [];
    let correlationResponse: CorrelationApiResponse | null = null;

    test.beforeEach(async ({ page: testPage }) => {
        page = testPage;
        networkCalls = [];
        correlationResponse = null;

        // Configurar interceptación de TODAS las llamadas de red
        await page.route('**/*', async (route) => {
            const request = route.request();
            const url = request.url();
            
            // Interceptar solo llamadas relevantes
            if (url.includes('/api/') || url.includes('analyzeCorrelation')) {
                console.log(`🌐 INTERCEPTANDO: ${request.method()} ${url}`);
                
                const response = await route.fetch();
                const responseBody = await response.text();
                
                let parsedResponse;
                try {
                    parsedResponse = JSON.parse(responseBody);
                } catch {
                    parsedResponse = responseBody;
                }

                const networkCall: NetworkCall = {
                    url,
                    method: request.method(),
                    requestData: request.postDataJSON(),
                    responseData: parsedResponse,
                    status: response.status(),
                    timestamp: Date.now()
                };

                networkCalls.push(networkCall);

                // Guardar respuesta de correlación específicamente
                if (url.includes('analyzeCorrelation')) {
                    correlationResponse = parsedResponse as CorrelationApiResponse;
                    console.log(`📥 RESPUESTA CORRELACIÓN CAPTURADA:`, {
                        success: correlationResponse.success,
                        dataLength: correlationResponse.data?.length || 0,
                        hasError: !!correlationResponse.error
                    });
                }

                await route.fulfill({ response });
            } else {
                await route.continue();
            }
        });

        // Configurar logging de consola detallado
        page.on('console', (msg) => {
            const logText = msg.text();
            
            // Capturar logs específicos del problema
            if (logText.includes('3009120093') || 
                logText.includes('254') || 
                logText.includes('DIAGRAMA') || 
                logText.includes('NODOS') ||
                logText.includes('FILTRADO')) {
                console.log(`🖥️ CONSOLE LOG: ${msg.type()}: ${logText}`);
            }
        });

        // Capturar errores de JavaScript
        page.on('pageerror', (error) => {
            console.error(`❌ JAVASCRIPT ERROR: ${error.message}`);
        });
    });

    test('🔍 Análisis completo: Backend → Frontend → Diagrama para 3009120093', async () => {
        console.log('\n🚀 INICIANDO ANÁLISIS CRÍTICO DEL NÚMERO 3009120093\n');

        // PASO 1: Navegar a la aplicación
        await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
        await page.waitForTimeout(2000);

        // PASO 2: Navegar a una misión específica
        console.log('📂 PASO 1: Navegando a misiones...');
        await page.click('a[href="#/missions"]');
        await page.waitForTimeout(1000);

        // PASO 3: Seleccionar una misión que tenga datos
        console.log('🎯 PASO 2: Seleccionando misión con datos...');
        const missionLink = page.locator('a[href*="/mission/"]').first();
        await missionLink.waitFor({ state: 'visible' });
        await missionLink.click();
        await page.waitForTimeout(2000);

        // PASO 4: Ir a la pestaña de correlación
        console.log('🔗 PASO 3: Navegando a pestaña de correlación...');
        await page.click('button:has-text("Análisis de Correlación")');
        await page.waitForTimeout(1000);

        // PASO 5: Ejecutar correlación para capturar llamada de red
        console.log('⚡ PASO 4: Ejecutando análisis de correlación...');
        const executeButton = page.locator('button:has-text("Ejecutar Correlación")');
        await executeButton.waitFor({ state: 'visible' });
        await executeButton.click();

        // PASO 6: Esperar a que complete la correlación
        console.log('⏳ PASO 5: Esperando respuesta del backend...');
        await page.waitForTimeout(10000); // Dar tiempo suficiente

        // PASO 7: Verificar que se recibió respuesta de correlación
        expect(correlationResponse).not.toBeNull();
        expect(correlationResponse?.success).toBe(true);

        console.log('\n📊 ANÁLISIS DE RESPUESTA DEL BACKEND:');
        console.log(`✅ Total de registros recibidos: ${correlationResponse?.data?.length || 0}`);
        
        if (correlationResponse?.data) {
            // Buscar específicamente el número 3009120093
            const targetResult = correlationResponse.data.find(
                result => result.targetNumber === '3009120093'
            );

            if (targetResult) {
                console.log(`🎯 NÚMERO OBJETIVO ENCONTRADO:`);
                console.log(`  - Número: ${targetResult.targetNumber}`);
                console.log(`  - Operador: ${targetResult.operator}`);
                console.log(`  - Ocurrencias: ${targetResult.occurrences}`);
                console.log(`  - Celdas relacionadas: ${targetResult.relatedCells.length}`);
                console.log(`  - Celdas: [${targetResult.relatedCells.join(', ')}]`);
                console.log(`  - Confianza: ${targetResult.confidence}`);
            } else {
                console.log(`❌ NÚMERO 3009120093 NO ENCONTRADO en respuesta del backend`);
            }

            // Analizar distribución de números
            const operatorCounts = correlationResponse.data.reduce((acc, result) => {
                acc[result.operator] = (acc[result.operator] || 0) + 1;
                return acc;
            }, {} as Record<string, number>);

            console.log(`📈 DISTRIBUCIÓN POR OPERADOR:`, operatorCounts);

            // Contar números con pocas celdas vs muchas celdas
            const cellDistribution = correlationResponse.data.reduce((acc, result) => {
                const cellCount = result.relatedCells.length;
                if (cellCount <= 2) acc.lowCells++;
                else if (cellCount <= 5) acc.mediumCells++;
                else acc.highCells++;
                return acc;
            }, { lowCells: 0, mediumCells: 0, highCells: 0 });

            console.log(`📊 DISTRIBUCIÓN POR CELDAS:`, cellDistribution);
        }

        // PASO 8: Buscar el número 3009120093 en la tabla de resultados
        console.log('\n🔍 PASO 6: Buscando número 3009120093 en tabla...');
        
        // Filtrar por el número específico
        const phoneFilter = page.locator('input[placeholder*="3224274851"]');
        await phoneFilter.fill('3009120093');
        await page.waitForTimeout(1000);

        // Verificar si aparece en la tabla
        const numberInTable = page.locator('td:has-text("3009120093")');
        const isNumberVisible = await numberInTable.isVisible().catch(() => false);

        console.log(`📋 NÚMERO EN TABLA: ${isNumberVisible ? '✅ Visible' : '❌ No visible'}`);

        if (isNumberVisible) {
            // PASO 9: Hacer clic en el botón de ver diagrama
            console.log('👁️ PASO 7: Haciendo clic en Ver Diagrama...');
            
            const viewDiagramButton = page.locator('tr:has(td:has-text("3009120093")) button[title*="diagrama"]');
            await viewDiagramButton.waitFor({ state: 'visible' });
            await viewDiagramButton.click();

            // PASO 10: Esperar a que abra el modal del diagrama
            console.log('🔍 PASO 8: Esperando modal del diagrama...');
            await page.waitForSelector('[class*="modal"], [class*="Modal"]', { timeout: 10000 });
            await page.waitForTimeout(3000); // Dar tiempo para que se procesen los datos

            // PASO 11: Capturar información del diagrama
            console.log('\n📊 ANÁLISIS DEL DIAGRAMA:');
            
            // Buscar el elemento que muestra el número de nodos
            const nodeCountElements = await page.locator('text=/nodos/i, text=/nodes/i').allTextContents();
            console.log(`🔢 ELEMENTOS CON "NODOS":`, nodeCountElements);

            // Buscar información del objetivo
            const targetInfo = await page.locator('text=/Objetivo.*3009120093/i').allTextContents();
            console.log(`🎯 INFO DEL OBJETIVO:`, targetInfo);

            // Buscar estadísticas del diagrama
            const statsInfo = await page.locator('text=/Total.*nodos/i').allTextContents();
            console.log(`📈 ESTADÍSTICAS:`, statsInfo);

            // Capturar screenshot del diagrama
            console.log('📸 PASO 9: Capturando screenshot del diagrama...');
            await page.screenshot({ 
                path: `debug-diagram-3009120093-${Date.now()}.png`,
                fullPage: true 
            });

        } else {
            console.log('❌ No se pudo encontrar el número 3009120093 en la tabla de resultados');
        }

        // PASO 12: Análisis final de logs y datos
        console.log('\n📝 RESUMEN FINAL:');
        console.log(`🌐 Total de llamadas de red interceptadas: ${networkCalls.length}`);
        console.log(`📥 Respuesta de correlación capturada: ${!!correlationResponse}`);
        
        if (correlationResponse) {
            console.log(`📊 Registros del backend: ${correlationResponse.data?.length || 0}`);
        }

        // Guardar todos los datos capturados
        const debugData = {
            timestamp: new Date().toISOString(),
            targetNumber: '3009120093',
            networkCalls: networkCalls,
            correlationResponse: correlationResponse,
            testResult: isNumberVisible ? 'FOUND_IN_TABLE' : 'NOT_FOUND_IN_TABLE'
        };

        await page.evaluate((data) => {
            console.log('💾 GUARDANDO DATOS DE DEBUG:', JSON.stringify(data, null, 2));
        }, debugData);

        // Escribir reporte a archivo
        const fs = require('fs');
        fs.writeFileSync(
            `debug-report-3009120093-${Date.now()}.json`, 
            JSON.stringify(debugData, null, 2)
        );

        console.log('\n✅ ANÁLISIS COMPLETO FINALIZADO');
    });

    test('🧪 Prueba específica del filtrado en CorrelationDiagramModal', async () => {
        console.log('\n🔬 PRUEBA ESPECÍFICA: Análisis del filtrado de datos en el modal\n');

        // Esta prueba simula exactamente lo que hace el CorrelationDiagramModal
        await page.goto('http://localhost:3000');
        
        // Inyectar script de debugging en la página
        await page.addInitScript(() => {
            // Override de console.log para capturar logs específicos
            const originalLog = console.log;
            (window as any).debugLogs = [];
            
            console.log = (...args) => {
                const message = args.join(' ');
                if (message.includes('FILTRADO') || 
                    message.includes('DIAGRAMA') || 
                    message.includes('3009120093') ||
                    message.includes('nodos')) {
                    (window as any).debugLogs.push({
                        timestamp: Date.now(),
                        message: message
                    });
                }
                originalLog(...args);
            };
        });

        // Simular datos de correlación como los que recibiría el modal
        const simulatedCorrelationData = await page.evaluate(() => {
            // Esta función simula el filtrado exacto del CorrelationDiagramModal
            const targetNumber = '3009120093';
            
            // Simular datos como los que vienen del backend
            const allCorrelationData = Array.from({ length: 300 }, (_, i) => ({
                targetNumber: `300${(9120000 + i).toString().padStart(7, '0')}`,
                operator: ['CLARO', 'MOVISTAR', 'TIGO'][i % 3],
                occurrences: Math.floor(Math.random() * 100) + 1,
                relatedCells: [`5120${i % 10}`, `5140${(i + 1) % 10}`, `5200${i % 5}`],
                confidence: 0.5 + Math.random() * 0.5,
                firstDetection: '2021-05-20T10:00:00Z',
                lastDetection: '2021-05-20T14:00:00Z'
            }));

            // Asegurar que existe el número objetivo
            allCorrelationData[0] = {
                targetNumber: '3009120093',
                operator: 'CLARO',
                occurrences: 45,
                relatedCells: ['51203', '51438', '52001'],
                confidence: 0.95,
                firstDetection: '2021-05-20T10:00:00Z',
                lastDetection: '2021-05-20T14:00:00Z'
            };

            console.log(`🎯 SIMULACIÓN: Dataset completo con ${allCorrelationData.length} registros`);

            // Replicar exactamente el filtrado del CorrelationDiagramModal
            const targetResult = allCorrelationData.find(result => result.targetNumber === targetNumber);
            if (!targetResult) {
                console.error(`❌ No se encontró resultado para ${targetNumber}`);
                return { originalCount: allCorrelationData.length, filteredCount: 0 };
            }

            const targetCells = targetResult.relatedCells;
            console.log(`📡 Celdas objetivo (${targetNumber}): [${targetCells.join(', ')}]`);

            const relatedCorrelationData = allCorrelationData.filter(result => {
                if (result.targetNumber === targetNumber) {
                    console.log(`✅ INCLUIDO - Número objetivo: ${result.targetNumber}`);
                    return true;
                }

                // FILTRADO EXACTO del modal actual
                const sharedCells = result.relatedCells.filter(cell => targetCells.includes(cell));
                const hasSharedCells = sharedCells.length >= 1;
                const hasMinOccurrences = result.occurrences >= 2;
                const hasMinConfidence = result.confidence >= 0.5;

                if (hasSharedCells && hasMinOccurrences && hasMinConfidence) {
                    console.log(`✅ INCLUIDO - ${result.targetNumber}: ${sharedCells.length} celdas compartidas, ${result.occurrences} ocurrencias, ${result.confidence.toFixed(2)} confianza`);
                    return true;
                } else {
                    console.log(`❌ EXCLUIDO - ${result.targetNumber}: ${sharedCells.length} celdas, ${result.occurrences} ocurrencias, ${result.confidence.toFixed(2)} confianza`);
                    return false;
                }
            });

            console.log(`🔗 RESULTADO FILTRADO: ${relatedCorrelationData.length} de ${allCorrelationData.length} registros`);

            return {
                originalCount: allCorrelationData.length,
                filteredCount: relatedCorrelationData.length,
                targetFound: !!targetResult,
                targetCells: targetCells
            };
        });

        console.log('\n📊 RESULTADO DE LA SIMULACIÓN:');
        console.log(`📥 Registros originales: ${simulatedCorrelationData.originalCount}`);
        console.log(`📤 Registros filtrados: ${simulatedCorrelationData.filteredCount}`);
        console.log(`🎯 Objetivo encontrado: ${simulatedCorrelationData.targetFound ? '✅' : '❌'}`);
        console.log(`📡 Celdas objetivo: [${simulatedCorrelationData.targetCells?.join(', ') || 'N/A'}]`);

        // Obtener logs de debugging
        const debugLogs = await page.evaluate(() => (window as any).debugLogs || []);
        
        console.log('\n📝 LOGS DE DEBUGGING CAPTURADOS:');
        debugLogs.forEach((log: any, index: number) => {
            console.log(`${index + 1}. ${log.message}`);
        });

        // Verificar que el filtrado está funcionando según lo esperado
        expect(simulatedCorrelationData.filteredCount).toBeGreaterThan(0);
        expect(simulatedCorrelationData.filteredCount).toBeLessThan(simulatedCorrelationData.originalCount);
    });
});