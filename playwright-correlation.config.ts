/**
 * Configuración Playwright específica para Test de Algoritmo de Correlación
 * 
 * Configuración optimizada para testing del algoritmo de correlación
 * con números objetivo específicos identificados por Boris
 */

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  // Archivos de test específicos para correlación
  testDir: './tests',
  testMatch: '**/correlation-algorithm-validation.spec.ts',
  
  // Configuración de timeouts específica para análisis de correlación
  timeout: 300000, // 5 minutos por test (análisis puede tomar tiempo)
  expect: {
    timeout: 30000 // 30 segundos para assertions
  },
  
  // Configuración de paralelización
  fullyParallel: false, // Los tests de correlación deben ejecutarse secuencialmente
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1, // Reintentos en caso de fallo
  workers: 1, // Un solo worker para evitar conflictos de base de datos
  
  // Configuración de reportes
  reporter: [
    ['html', { 
      outputFolder: 'Backend/test_evidence_screenshots/playwright-report',
      open: 'never' 
    }],
    ['json', { 
      outputFile: 'Backend/test_evidence_screenshots/correlation-test-results.json' 
    }],
    ['list'],
    ['junit', { 
      outputFile: 'Backend/test_evidence_screenshots/correlation-test-results.xml' 
    }]
  ],
  
  // Configuración global para tests
  use: {
    // URL base de KRONOS
    baseURL: 'http://localhost:8000',
    
    // Configuración de trazas y capturas
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    
    // Timeouts específicos para correlación
    actionTimeout: 30000,
    navigationTimeout: 30000,
    
    // Configuración de viewport para evidencia
    viewport: { width: 1920, height: 1080 },
    
    // Configuración para aplicación desktop (Eel)
    ignoreHTTPSErrors: true,
    
    // Headers personalizados si son necesarios
    extraHTTPHeaders: {
      'Accept': 'application/json, text/plain, */*',
      'Content-Type': 'application/json'
    }
  },

  // Configuración de proyectos de testing
  projects: [
    {
      name: 'correlation-validation-chrome',
      use: { 
        ...devices['Desktop Chrome'],
        // Configuración específica para algoritmo de correlación
        launchOptions: {
          args: [
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--no-sandbox'
          ]
        }
      },
    },
    
    // Proyecto específico para validación en modo headless
    {
      name: 'correlation-validation-headless',
      use: { 
        ...devices['Desktop Chrome'],
        headless: true,
        launchOptions: {
          args: ['--no-sandbox', '--disable-setuid-sandbox']
        }
      },
    }
  ],

  // Setup global para tests de correlación
  globalSetup: './tests/global-setup.ts',
  globalTeardown: './tests/global-teardown.ts',

  // Configuración del servidor web (si necesario)
  webServer: {
    command: 'cd Backend && python main.py',
    port: 8000,
    timeout: 120000, // 2 minutos para que inicie el backend
    reuseExistingServer: true, // Reutilizar servidor si ya está corriendo
    env: {
      'PYTHONPATH': '.',
      'FLASK_ENV': 'testing'
    }
  },

  // Configuración de output
  outputDir: 'Backend/test_evidence_screenshots/test-results',
  
  // Configuración específica para captura de evidencia
  metadata: {
    testSuite: 'Validación Algoritmo de Correlación KRONOS',
    targetNumbers: [
      '3224274851', '3208611034', '3104277553', 
      '3102715509', '3143534707', '3214161903'
    ],
    criticalConnection: '3104277553 -> 3224274851',
    testPeriod: '2024-08-12 20:00:00 - 2024-08-13 02:00:00',
    expectedCells: '12345 -> 67890',
    minCoincidences: 2
  }
});

// Configuración de variables de entorno para el test
process.env.CORRELATION_TEST_MODE = 'true';
process.env.TEST_TARGET_NUMBERS = '3224274851,3208611034,3104277553,3102715509,3143534707,3214161903';
process.env.TEST_CRITICAL_NUMBER = '3104277553';
process.env.TEST_CONNECTED_NUMBER = '3224274851';
process.env.TEST_PERIOD_START = '2024-08-12T20:00';
process.env.TEST_PERIOD_END = '2024-08-13T02:00';