/**
 * Configuración de Playwright para testing completo de PhoneCorrelationViewer
 * Testing MCP solicitado por Boris - 2025-08-21
 * 
 * Validaciones específicas:
 * - Flujo completo de correlación con datos reales de BD
 * - 4 modos de visualización
 * - Controles de zoom, filtros, export
 * - Interactividad (tooltips, clicks, drag&drop)
 * - Performance y responsive
 * - Integración sin afectar funcionalidad existente
 */

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  // Test específico para PhoneCorrelationViewer
  testMatch: '**/test-phonecorrelation-viewer-complete.spec.ts',
  
  // Configuración de timeout para operaciones complejas
  timeout: 120000, // 2 minutos para operaciones complejas
  expect: {
    timeout: 30000 // 30 segundos para assertions
  },
  
  fullyParallel: false, // Secuencial para evitar conflictos de BD
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1,
  workers: 1, // Un solo worker para evitar conflictos de base de datos
  
  reporter: [
    ['html', { 
      outputFolder: 'test-results/phonecorrelation-validation-html-report',
      open: 'never' 
    }],
    ['json', { 
      outputFile: 'test-results/phonecorrelation-validation-results.json' 
    }],
    ['junit', { 
      outputFile: 'test-results/phonecorrelation-validation-junit.xml' 
    }],
    ['list']
  ],
  
  use: {
    // Configuración para aplicación híbrida desktop
    baseURL: 'http://localhost:8000',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    // Configuración específica para diagrama interactivo
    actionTimeout: 30000,
    navigationTimeout: 60000,
    // Viewport grande para diagrama completo
    viewport: { width: 1600, height: 1000 },
    // Configuración de browser para mejor rendimiento
    launchOptions: {
      args: [
        '--disable-web-security',
        '--disable-features=VizDisplayCompositor',
        '--disable-backgrounding-occluded-windows',
        '--disable-background-timer-throttling'
      ]
    }
  },

  projects: [
    {
      name: 'phonecorrelation-validation',
      use: { ...devices['Desktop Chrome'] },
      testDir: './tests',
      testMatch: '**/test-phonecorrelation-viewer-complete.spec.ts'
    }
  ],

  // Global setup para inicializar backend
  globalSetup: require.resolve('./tests/phonecorrelation-global-setup.ts'),
  globalTeardown: require.resolve('./tests/phonecorrelation-global-teardown.ts'),
  
  // Configuración de captura de evidencias
  outputDir: 'test-results/phonecorrelation-artifacts'
});