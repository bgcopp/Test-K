/**
 * Test de Investigación del Diagrama de Correlación
 * 
 * Investigación específica del problema reportado por Boris:
 * El número 3113330727 muestra 255 nodos cuando debería mostrar solo interacciones directas
 * 
 * OBJETIVOS:
 * 1. Capturar logs detallados de consola
 * 2. Interceptar llamadas de red al backend
 * 3. Analizar flujo completo de datos
 * 4. Identificar punto exacto donde se agregan nodos extra
 * 5. Comparar datos backend vs frontend
 */

import { test, expect, Page, Request, Response } from '@playwright/test';
import { promises as fs } from 'fs';
import path from 'path';

interface NetworkLog {
  url: string;
  method: string;
  requestPayload?: any;
  responsePayload?: any;
  timestamp: string;
  status?: number;
}

interface ConsoleLog {
  type: string;
  text: string;
  timestamp: string;
  args?: any[];
}

interface InvestigationReport {
  targetNumber: string;
  consoleMessages: ConsoleLog[];
  networkRequests: NetworkLog[];
  backendDataCount: number;
  frontendNodesCount: number;
  filteredDataCount: number;
  transformedDataCount: number;
  finalVisualizationCount: number;
  issueIdentified: string;
  recommendedSolution: string;
  capturedAt: string;
}

let investigationReport: InvestigationReport;
let consoleMessages: ConsoleLog[] = [];
let networkRequests: NetworkLog[] = [];

test.describe('Investigación Diagrama Correlación - Número 3113330727', () => {
  
  test.beforeEach(async ({ page }) => {
    console.log('🔍 Iniciando investigación del diagrama para número 3113330727');
    
    // Inicializar el reporte de investigación
    investigationReport = {
      targetNumber: '3113330727',
      consoleMessages: [],
      networkRequests: [],
      backendDataCount: 0,
      frontendNodesCount: 0,
      filteredDataCount: 0,
      transformedDataCount: 0,
      finalVisualizationCount: 0,
      issueIdentified: '',
      recommendedSolution: '',
      capturedAt: new Date().toISOString()
    };

    // Limpiar arrays de captura
    consoleMessages = [];
    networkRequests = [];

    // Configurar captura de logs de consola
    page.on('console', (msg) => {
      const logEntry: ConsoleLog = {
        type: msg.type(),
        text: msg.text(),
        timestamp: new Date().toISOString(),
        args: msg.args().map(arg => arg.toString())
      };
      consoleMessages.push(logEntry);
      console.log(`📝 Console [${msg.type()}]: ${msg.text()}`);
    });

    // Configurar interceptación de requests de red
    page.on('request', (request: Request) => {
      const networkLog: NetworkLog = {
        url: request.url(),
        method: request.method(),
        timestamp: new Date().toISOString()
      };
      
      // Capturar payload del request si existe
      if (request.postData()) {
        try {
          networkLog.requestPayload = JSON.parse(request.postData() || '{}');
        } catch (e) {
          networkLog.requestPayload = request.postData();
        }
      }
      
      networkRequests.push(networkLog);
      console.log(`🌐 Request: ${request.method()} ${request.url()}`);
    });

    // Configurar interceptación de responses de red
    page.on('response', async (response: Response) => {
      const requestIndex = networkRequests.findIndex(req => req.url === response.url());
      if (requestIndex !== -1) {
        networkRequests[requestIndex].status = response.status();
        
        // Capturar payload de response si es relevante para correlación
        if (response.url().includes('correlation') || response.url().includes('analyze')) {
          try {
            const responseBody = await response.text();
            networkRequests[requestIndex].responsePayload = JSON.parse(responseBody);
            console.log(`📊 Response for ${response.url()}: ${responseBody.length} characters`);
          } catch (e) {
            console.log(`⚠️ Error parsing response for ${response.url()}: ${e}`);
          }
        }
      }
    });

    // Navegar a KRONOS
    console.log('🚀 Navegando a KRONOS...');
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('Investigación completa del problema del diagrama', async ({ page }) => {
    console.log('🎯 Iniciando investigación completa para número 3113330727');

    // FASE 1: Navegar a Misiones
    console.log('📋 FASE 1: Navegando a la sección de Misiones');
    await page.click('text=Misiones');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'Backend/diagram_investigation_evidence/01-missions-page.png' });

    // FASE 2: Buscar y abrir misión con el número problema
    console.log('🔍 FASE 2: Buscando misión que contenga el número 3113330727');
    
    // Verificar si hay misiones en la tabla
    const missionRows = await page.locator('table tbody tr').count();
    console.log(`📊 Encontradas ${missionRows} misiones en la tabla`);
    
    let missionFound = false;
    for (let i = 0; i < missionRows; i++) {
      const row = page.locator('table tbody tr').nth(i);
      const missionText = await row.textContent();
      console.log(`🔍 Revisando misión ${i + 1}: ${missionText?.substring(0, 100)}...`);
      
      // Buscar por el número específico o abrir cualquier misión para análisis
      if (missionText?.includes('3113330727') || i === 0) {
        console.log(`✅ Abriendo misión ${i + 1} para análisis`);
        await row.click();
        await page.waitForLoadState('networkidle');
        missionFound = true;
        break;
      }
    }

    if (!missionFound) {
      console.log('⚠️ No se encontró misión específica, creando una para testing');
      // Aquí podríamos crear una misión de prueba si es necesario
    }

    await page.screenshot({ path: 'Backend/diagram_investigation_evidence/02-mission-detail.png' });

    // FASE 3: Navegar a la pestaña de Análisis
    console.log('📈 FASE 3: Navegando a la pestaña de Análisis');
    await page.click('text=Análisis');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'Backend/diagram_investigation_evidence/03-analysis-tab.png' });

    // FASE 4: Buscar el número problema y abrir su diagrama
    console.log('🎯 FASE 4: Buscando número 3113330727 en la tabla de análisis');
    
    // Verificar si existe un campo de búsqueda
    const searchInput = page.locator('input[placeholder*="Buscar"], input[type="search"]');
    if (await searchInput.count() > 0) {
      console.log('🔍 Usando campo de búsqueda para encontrar el número');
      await searchInput.fill('3113330727');
      await page.waitForTimeout(2000); // Esperar a que se aplique el filtro
    }

    // Buscar el número en la tabla
    const analysisRows = await page.locator('table tbody tr').count();
    console.log(`📊 Encontradas ${analysisRows} filas en análisis`);
    
    let numberFound = false;
    for (let i = 0; i < analysisRows; i++) {
      const row = page.locator('table tbody tr').nth(i);
      const rowText = await row.textContent();
      
      if (rowText?.includes('3113330727')) {
        console.log(`✅ Encontrado número 3113330727 en fila ${i + 1}`);
        
        // Buscar botón de diagrama en esta fila
        const diagramButton = row.locator('button:has-text("Diagrama"), button[title*="diagrama"], button[title*="Diagrama"]');
        if (await diagramButton.count() > 0) {
          console.log('🖱️ Haciendo clic en botón de diagrama');
          await diagramButton.click();
          numberFound = true;
          break;
        } else {
          console.log('⚠️ No se encontró botón de diagrama en esta fila');
        }
      }
    }

    if (!numberFound) {
      console.log('❌ No se encontró el número 3113330727 o su botón de diagrama');
      // Intentar hacer clic en cualquier botón de diagrama para análisis general
      const anyDiagramButton = page.locator('button:has-text("Diagrama"), button[title*="diagrama"]').first();
      if (await anyDiagramButton.count() > 0) {
        console.log('🔄 Abriendo cualquier diagrama disponible para análisis');
        await anyDiagramButton.click();
      }
    }

    await page.waitForTimeout(3000); // Esperar a que se abra el modal

    // FASE 5: Analizar el diagrama que se abre
    console.log('📊 FASE 5: Analizando el diagrama abierto');
    
    // Verificar si se abrió el modal del diagrama
    const diagramModal = page.locator('[role="dialog"], .modal, .diagram-modal');
    if (await diagramModal.count() > 0) {
      console.log('✅ Modal de diagrama detectado');
      await page.screenshot({ path: 'Backend/diagram_investigation_evidence/04-diagram-modal-opened.png' });
      
      // Esperar a que cargue completamente el diagrama
      await page.waitForTimeout(5000);
      
      // FASE 6: Capturar información del diagrama
      console.log('🔬 FASE 6: Capturando información detallada del diagrama');
      
      // Intentar obtener el número de nodos desde el frontend
      const nodeCount = await page.evaluate(() => {
        // Buscar elementos que representen nodos en el diagrama
        const nodes = document.querySelectorAll('[data-testid="node"], .node, circle[r], .vis-network canvas');
        console.log('🔍 Elementos de nodos encontrados:', nodes.length);
        return nodes.length;
      });
      
      investigationReport.frontendNodesCount = nodeCount;
      console.log(`📊 Nodos detectados en el frontend: ${nodeCount}`);
      
      // Capturar logs específicos de la correlación
      const correlationLogs = consoleMessages.filter(log => 
        log.text.toLowerCase().includes('correlation') || 
        log.text.toLowerCase().includes('node') ||
        log.text.toLowerCase().includes('diagram') ||
        log.text.includes('3113330727')
      );
      
      console.log(`📝 Logs de correlación capturados: ${correlationLogs.length}`);
      correlationLogs.forEach(log => {
        console.log(`  - [${log.type}] ${log.text}`);
      });
      
      // Capturar requests de red relacionados con correlación
      const correlationRequests = networkRequests.filter(req => 
        req.url.includes('correlation') || 
        req.url.includes('analyze') ||
        req.url.includes('diagram')
      );
      
      console.log(`🌐 Requests de correlación capturados: ${correlationRequests.length}`);
      correlationRequests.forEach(req => {
        console.log(`  - ${req.method} ${req.url} (Status: ${req.status})`);
        if (req.responsePayload) {
          console.log(`    Response data points: ${JSON.stringify(req.responsePayload).length} characters`);
        }
      });
      
      await page.screenshot({ path: 'Backend/diagram_investigation_evidence/05-diagram-loaded.png' });
      
    } else {
      console.log('❌ No se pudo detectar el modal del diagrama');
      await page.screenshot({ path: 'Backend/diagram_investigation_evidence/04-no-diagram-modal.png' });
    }

    // FASE 7: Actualizar reporte de investigación
    investigationReport.consoleMessages = consoleMessages;
    investigationReport.networkRequests = networkRequests;
    
    // Guardar reporte de investigación
    await saveInvestigationReport(investigationReport);
    
    console.log('✅ Investigación completa del diagrama finalizada');
  });

  test('Consulta directa al backend para verificar datos', async ({ page }) => {
    console.log('🔍 Consultando backend directamente para verificar datos de 3113330727');

    // Navegar a la consola del desarrollador o ejecutar código directamente
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Ejecutar consulta directa al backend via window.eel
    const backendData = await page.evaluate(async () => {
      // Verificar si window.eel está disponible
      if (typeof (window as any).eel === 'undefined') {
        return { error: 'window.eel no está disponible' };
      }
      
      try {
        // Llamada directa al servicio de correlación del backend
        const result = await (window as any).eel.get_correlation_data('3113330727')();
        return result;
      } catch (error) {
        return { error: `Error en llamada backend: ${error}` };
      }
    });
    
    console.log('📊 Datos del backend para 3113330727:', JSON.stringify(backendData, null, 2));
    investigationReport.backendDataCount = Array.isArray(backendData) ? backendData.length : 0;
    
    // Guardar datos del backend
    await fs.writeFile(
      'Backend/diagram_investigation_evidence/backend-data-3113330727.json',
      JSON.stringify(backendData, null, 2)
    );
  });

  test.afterEach(async ({ page }) => {
    console.log('🔚 Finalizando investigación y guardando evidencia');
    
    // Capturar screenshot final del estado de la página
    await page.screenshot({ path: 'Backend/diagram_investigation_evidence/99-final-state.png' });
    
    // Actualizar y guardar reporte final
    investigationReport.consoleMessages = consoleMessages;
    investigationReport.networkRequests = networkRequests;
    await saveInvestigationReport(investigationReport);
  });
});

async function saveInvestigationReport(report: InvestigationReport) {
  const reportPath = 'Backend/diagram_investigation_evidence/investigation-report.json';
  
  try {
    // Crear directorio si no existe
    await fs.mkdir(path.dirname(reportPath), { recursive: true });
    
    // Guardar reporte
    await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
    
    console.log(`💾 Reporte de investigación guardado en: ${reportPath}`);
    
    // Crear resumen ejecutivo
    const summary = `
# REPORTE DE INVESTIGACIÓN - DIAGRAMA CORRELACIÓN
## Número Investigado: ${report.targetNumber}
## Fecha: ${report.capturedAt}

### MÉTRICAS CAPTURADAS:
- Datos del Backend: ${report.backendDataCount} registros
- Nodos en Frontend: ${report.frontendNodesCount} nodos
- Logs de Consola: ${report.consoleMessages.length} mensajes
- Requests de Red: ${report.networkRequests.length} llamadas

### LOGS CRÍTICOS:
${report.consoleMessages.filter(log => 
  log.text.toLowerCase().includes('error') || 
  log.text.toLowerCase().includes('warning') ||
  log.text.includes(report.targetNumber)
).map(log => `- [${log.type}] ${log.text}`).join('\n')}

### REQUESTS DE CORRELACIÓN:
${report.networkRequests.filter(req => 
  req.url.includes('correlation') || req.url.includes('analyze')
).map(req => `- ${req.method} ${req.url} (${req.status})`).join('\n')}

### PROBLEMA IDENTIFICADO:
${report.issueIdentified || 'En análisis...'}

### SOLUCIÓN RECOMENDADA:
${report.recommendedSolution || 'Pendiente de análisis detallado...'}
`;
    
    await fs.writeFile('Backend/diagram_investigation_evidence/investigation-summary.md', summary);
    console.log('📋 Resumen ejecutivo guardado');
    
  } catch (error) {
    console.error('❌ Error guardando reporte de investigación:', error);
  }
}