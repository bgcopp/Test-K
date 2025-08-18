import { Page } from '@playwright/test';

/**
 * Utilidades de debugging para tests de certificación
 */

export class DebugHelper {
  constructor(private page: Page) {}

  async captureFullPageState(stepName: string) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `debug_${stepName}_${timestamp}`;
    
    // Screenshot completo
    await this.page.screenshot({ 
      path: `test-results/evidence/${filename}.png`,
      fullPage: true 
    });
    
    // HTML de la página
    const html = await this.page.content();
    const fs = require('fs');
    fs.writeFileSync(`test-results/evidence/${filename}.html`, html);
    
    // Console logs
    const logs = await this.page.evaluate(() => {
      return (window as any).debugLogs || [];
    });
    
    if (logs.length > 0) {
      fs.writeFileSync(`test-results/evidence/${filename}_console.json`, JSON.stringify(logs, null, 2));
    }
    
    console.log(`🐛 Debug capturado: ${filename}`);
  }

  async logTableContent() {
    try {
      const table = this.page.locator('table.correlation-results, .results-table').first();
      
      if (await table.isVisible()) {
        const rows = table.locator('tbody tr');
        const rowCount = await rows.count();
        
        console.log(`📊 Tabla encontrada con ${rowCount} filas`);
        
        for (let i = 0; i < Math.min(rowCount, 10); i++) {
          const cells = rows.nth(i).locator('td');
          const cellCount = await cells.count();
          const rowData = [];
          
          for (let j = 0; j < cellCount; j++) {
            const cellText = await cells.nth(j).textContent();
            rowData.push(cellText?.trim() || '');
          }
          
          console.log(`📋 Fila ${i + 1}: ${rowData.join(' | ')}`);
        }
        
        if (rowCount > 10) {
          console.log(`📋 ... y ${rowCount - 10} filas más`);
        }
      } else {
        console.log('❌ No se encontró tabla de resultados');
      }
    } catch (error) {
      console.error('❌ Error logging table content:', error);
    }
  }

  async searchForTargetNumbers() {
    const targetNumbers = ['3224274851', '3208611034', '3143534707', '3102715509', '3214161903'];
    
    console.log('🔍 Buscando números objetivo en toda la página...');
    
    for (const number of targetNumbers) {
      try {
        // Buscar en cualquier elemento de la página
        const elements = this.page.locator(`*:has-text("${number}")`);
        const count = await elements.count();
        
        console.log(`🎯 ${number}: ${count} elementos encontrados`);
        
        if (count > 0) {
          for (let i = 0; i < Math.min(count, 3); i++) {
            const element = elements.nth(i);
            const text = await element.textContent();
            const tagName = await element.evaluate(el => el.tagName);
            console.log(`  - ${tagName}: "${text?.trim()}"`);
          }
        }
      } catch (error) {
        console.error(`❌ Error buscando ${number}:`, error);
      }
    }
  }

  async waitForStableContent(timeout = 30000) {
    console.log('⏳ Esperando contenido estable...');
    
    let previousContent = '';
    let stableCount = 0;
    const maxStableCount = 3;
    const checkInterval = 1000;
    const maxChecks = timeout / checkInterval;
    
    for (let i = 0; i < maxChecks; i++) {
      const currentContent = await this.page.locator('body').textContent();
      
      if (currentContent === previousContent) {
        stableCount++;
        if (stableCount >= maxStableCount) {
          console.log('✅ Contenido estabilizado');
          return;
        }
      } else {
        stableCount = 0;
        previousContent = currentContent || '';
      }
      
      await this.page.waitForTimeout(checkInterval);
    }
    
    console.log('⚠️ Timeout esperando contenido estable');
  }

  async injectDebugScript() {
    await this.page.addInitScript(() => {
      // Script de debugging que se ejecuta en el navegador
      (window as any).debugLogs = [];
      
      const originalLog = console.log;
      const originalError = console.error;
      
      console.log = (...args) => {
        (window as any).debugLogs.push({ type: 'log', args, timestamp: Date.now() });
        originalLog.apply(console, args);
      };
      
      console.error = (...args) => {
        (window as any).debugLogs.push({ type: 'error', args, timestamp: Date.now() });
        originalError.apply(console, args);
      };
      
      // Interceptar llamadas AJAX/Fetch
      const originalFetch = window.fetch;
      window.fetch = async (...args) => {
        (window as any).debugLogs.push({ type: 'fetch', url: args[0], timestamp: Date.now() });
        return originalFetch.apply(window, args);
      };
    });
  }

  async generateDebugReport() {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const reportData = {
      timestamp,
      url: this.page.url(),
      title: await this.page.title(),
      viewport: await this.page.viewportSize(),
      userAgent: await this.page.evaluate(() => navigator.userAgent),
      tableFound: await this.page.locator('table.correlation-results, .results-table').isVisible(),
      formElements: await this.page.locator('input, select, button').count(),
      errorElements: await this.page.locator('.error, .alert-error, .text-red').count()
    };
    
    const fs = require('fs');
    fs.writeFileSync(`test-results/evidence/debug_report_${timestamp}.json`, JSON.stringify(reportData, null, 2));
    
    console.log(`📊 Reporte de debug generado: debug_report_${timestamp}.json`);
    
    return reportData;
  }
}

export default DebugHelper;