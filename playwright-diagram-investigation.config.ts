/**
 * Configuración Playwright para Investigación del Diagrama de Correlación
 * 
 * Investigación específica del problema reportado por Boris:
 * El número 3113330727 muestra 255 nodos cuando debería mostrar solo interacciones directas
 */

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  // Archivos de test específicos para investigación del diagrama
  testDir: './tests',
  testMatch: '**/diagram-investigation.spec.ts',
  
  // Configuración de timeouts para análisis detallado
  timeout: 600000, // 10 minutos por test (investigación profunda)
  expect: {
    timeout: 60000 // 1 minuto para assertions
  },
  
  // Configuración de paralelización
  fullyParallel: false, // Tests secuenciales para investigación
  forbidOnly: !!process.env.CI,
  retries: 0, // Sin reintentos para capturar errores exactos
  workers: 1, // Un solo worker para análisis detallado
  
  // Configuración de reportes para investigación
  reporter: [
    ['html', { 
      outputFolder: 'Backend/diagram_investigation_report',
      open: 'never' 
    }],
    ['json', { 
      outputFile: 'Backend/diagram_investigation_results.json' 
    }],
    ['list'],
    ['junit', { 
      outputFile: 'Backend/diagram_investigation_junit.xml' 
    }]
  ],
  
  // Configuración global para investigación
  use: {
    // URL base de KRONOS
    baseURL: 'http://localhost:8000',
    
    // Configuración para captura máxima de evidencia
    trace: 'on', // Siempre capturar trazas
    screenshot: 'on', // Siempre capturar screenshots
    video: 'on', // Siempre capturar video
    
    // Timeouts extendidos para investigación
    actionTimeout: 60000,
    navigationTimeout: 60000,
    
    // Viewport para análisis visual
    viewport: { width: 1920, height: 1080 },
    
    // Configuración para aplicación desktop (Eel)
    ignoreHTTPSErrors: true,
    
    // Headers para interceptar requests
    extraHTTPHeaders: {
      'Accept': 'application/json, text/plain, */*',
      'Content-Type': 'application/json'
    }
  },

  // Proyecto específico para investigación del diagrama
  projects: [
    {
      name: 'diagram-investigation',
      use: { 
        ...devices['Desktop Chrome'],
        // Configuración para debugging máximo
        launchOptions: {
          args: [
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--no-sandbox',
            '--enable-logging',
            '--log-level=0', // Log máximo
            '--enable-network-service-logging'
          ],
          // Modo headed para observar el comportamiento
          headless: false,
          slowMo: 1000 // Ralentizar para observar
        }
      },
    }
  ],

  // Configuración del servidor web
  webServer: {
    command: 'cd Backend && python main.py',
    port: 8000,
    timeout: 120000, // 2 minutos para que inicie el backend
    reuseExistingServer: true,
    env: {
      'PYTHONPATH': '.',
      'FLASK_ENV': 'development', // Modo desarrollo para logs
      'DEBUG': 'true'
    }
  },

  // Configuración de output para investigación
  outputDir: 'Backend/diagram_investigation_evidence',
  
  // Metadata de la investigación
  metadata: {
    testSuite: 'Investigación Diagrama de Correlación KRONOS',
    problemNumber: '3113330727',
    reportedIssue: 'Muestra 255 nodos en lugar de interacciones directas',
    investigationGoals: [
      'Capturar logs detallados de consola',
      'Interceptar llamadas de red al backend',
      'Analizar flujo completo de datos',
      'Identificar punto exacto donde se agregan nodos extra',
      'Comparar datos backend vs frontend'
    ],
    expectedBehavior: 'Solo mostrar interacciones directas del número objetivo',
    investigationDate: new Date().toISOString()
  }
});

// Variables de entorno para la investigación
process.env.DIAGRAM_INVESTIGATION_MODE = 'true';
process.env.TARGET_INVESTIGATION_NUMBER = '3113330727';
process.env.CAPTURE_NETWORK_LOGS = 'true';
process.env.CAPTURE_CONSOLE_LOGS = 'true';
process.env.DEBUG_CORRELATION_SERVICE = 'true';