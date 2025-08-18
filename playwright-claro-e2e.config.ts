/**
 * Configuración Playwright específica para Pruebas E2E CLARO
 * 
 * Configuración optimizada para testing completo de carga de archivos CLARO
 * y validación del algoritmo de correlación con números objetivo específicos
 * 
 * Archivos objetivo:
 * - 4 archivos CLARO con total de 5,611 registros
 * - 1 archivo HUNTER para correlación
 * - Validación de 6 números objetivo específicos
 * 
 * @author Testing Team KRONOS
 * @version 1.0.0
 */

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  // Archivos de test específicos para CLARO E2E completo
  testDir: './tests',
  testMatch: '**/claro-e2e-complete-validation.spec.ts',
  
  // Configuración de timeouts específica para carga masiva de archivos
  timeout: 600000, // 10 minutos por test (carga de 4 archivos + correlación)
  expect: {
    timeout: 45000 // 45 segundos para assertions
  },
  
  // Configuración de paralelización
  fullyParallel: false, // Los tests CLARO deben ejecutarse secuencialmente
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1, // Reintentos en caso de fallo
  workers: 1, // Un solo worker para evitar conflictos de base de datos
  
  // Configuración de reportes detallados
  reporter: [
    ['html', { 
      outputFolder: 'test-results/claro-e2e-html-report',
      open: 'never' 
    }],
    ['json', { 
      outputFile: 'test-results/claro-e2e-results.json' 
    }],
    ['list'],
    ['junit', { 
      outputFile: 'test-results/claro-e2e-results.xml' 
    }]
  ],
  
  // Configuración global para tests
  use: {
    // URL base de KRONOS
    baseURL: 'http://localhost:8000',
    
    // Configuración de trazas y capturas para evidencia
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    
    // Timeouts específicos para carga de archivos
    actionTimeout: 45000, // 45 segundos para acciones individuales
    navigationTimeout: 60000, // 1 minuto para navegación
    
    // Configuración de viewport para evidencia completa
    viewport: { width: 1920, height: 1080 },
    
    // Configuración para aplicación desktop (Eel)
    ignoreHTTPSErrors: true,
    
    // Headers personalizados para testing
    extraHTTPHeaders: {
      'Accept': 'application/json, text/plain, */*',
      'Content-Type': 'application/json',
      'X-Test-Suite': 'CLARO-E2E-Complete'
    }
  },

  // Configuración de proyectos de testing
  projects: [
    {
      name: 'claro-e2e-complete-chrome',
      use: { 
        ...devices['Desktop Chrome'],
        // Configuración específica para carga masiva de archivos
        launchOptions: {
          args: [
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--max-old-space-size=4096' // Aumentar memoria para archivos grandes
          ]
        }
      },
    }
  ],

  // Setup global para tests de CLARO E2E
  globalSetup: './tests/global-setup.ts',
  globalTeardown: './tests/global-teardown.ts',

  // Configuración del servidor web
  webServer: {
    command: 'cd Backend && python main.py',
    port: 8000,
    timeout: 180000, // 3 minutos para que inicie el backend
    reuseExistingServer: true, // Reutilizar servidor si ya está corriendo
    env: {
      'PYTHONPATH': '.',
      'TESTING_MODE': 'true',
      'LOG_LEVEL': 'INFO'
    }
  },

  // Configuración de output
  outputDir: 'test-results/claro-e2e-artifacts',
  
  // Configuración específica para captura de evidencia
  metadata: {
    testSuite: 'Validación Completa E2E CLARO KRONOS',
    
    // Archivos objetivo para prueba
    targetFiles: [
      '1-225211_LLAMADAS_ENTRANTES_POR_CELDA_545612_0.xlsx', // 973 registros
      '1-225211_LLAMADAS_SALIENTES_POR_CELDA_545613_0.xlsx', // 961 registros
      '2-225211_LLAMADAS_ENTRANTES_POR_CELDA_545614_0.xlsx', // 1939 registros
      '2-225211_LLAMADAS_SALIENTES_POR_CELDA_545615_0.xlsx'  // 1738 registros
    ],
    
    hunterFile: 'SCANHUNTER.xlsx',
    
    expectedTotalRecords: 5611, // Suma exacta de todos los archivos CLARO
    
    // Números objetivo para correlación
    targetNumbers: [
      '3224274851', '3208611034', '3104277553', 
      '3102715509', '3143534707', '3214161903'
    ],
    
    // Configuración de correlación
    correlationPeriod: {
      start: '2021-05-20T10:00',
      end: '2021-05-20T14:30'
    },
    
    // Criterios de éxito
    successCriteria: {
      minRecordsLoaded: 5611,
      maxRecordsLoaded: 5611,
      minTargetNumbersFound: 6,
      requireAllTargetNumbers: true
    }
  }
});

// Configuración de variables de entorno específicas para el test
process.env.CLARO_E2E_TEST_MODE = 'true';
process.env.TEST_DATA_PATH = 'C:\\Soluciones\\BGC\\claude\\KNSOft\\archivos\\envioarchivosparaanalizar (1)';
process.env.EXPECTED_TOTAL_RECORDS = '5611';
process.env.TARGET_NUMBERS = '3224274851,3208611034,3104277553,3102715509,3143534707,3214161903';
process.env.CORRELATION_START = '2021-05-20T10:00';
process.env.CORRELATION_END = '2021-05-20T14:30';