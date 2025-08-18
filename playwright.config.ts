import { defineConfig, devices } from '@playwright/test';

/**
 * Configuración de Playwright para pruebas E2E de KRONOS
 * Aplicación híbrida Python Eel + React TypeScript
 * Puerto: http://localhost:8000
 */
export default defineConfig({
  // Directorio de tests
  testDir: './tests',
  
  // Configuración de archivos de prueba
  testMatch: '**/*.spec.ts',
  
  // Tiempo límite global para tests
  timeout: 120000, // 2 minutos para operaciones de carga de archivos
  
  // Configuración de intentos en caso de fallo
  retries: process.env.CI ? 2 : 1,
  
  // Configuración de paralelismo
  workers: 1, // Ejecutar de manera secuencial para evitar conflictos de BD
  
  // Configuración de reportes
  reporter: [
    ['html', { outputFolder: 'test-results/html-report' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    ['list']
  ],
  
  // Configuración global de pruebas
  use: {
    // URL base de la aplicación KRONOS
    baseURL: 'http://localhost:8000',
    
    // Configuración de timeouts
    actionTimeout: 30000, // 30 segundos para acciones individuales
    navigationTimeout: 60000, // 1 minuto para navegación
    
    // Configuración de capturas
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
    
    // Configuración de viewport para aplicación desktop
    viewport: { width: 1280, height: 720 },
    
    // Ignorar errores HTTPS para desarrollo local
    ignoreHTTPSErrors: true,
    
    // Configuración de usuario agente para desktop
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 KRONOS-E2E-Test'
  },

  // Configuración de proyectos (navegadores)
  projects: [
    {
      name: 'chromium-desktop',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
        // Configuración específica para aplicación Eel
        launchOptions: {
          args: [
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--no-sandbox',
            '--disable-setuid-sandbox'
          ]
        }
      },
    },
    
    // Solo Chrome para evitar problemas con aplicación Eel
    // (Eel está optimizado para Chrome/Chromium)
  ],

  // Configuración de servidor local
  webServer: {
    command: 'cd Backend && python main.py',
    port: 8000,
    timeout: 180000, // 3 minutos para inicialización completa
    reuseExistingServer: !process.env.CI,
    
    // Variables de entorno para testing
    env: {
      'TESTING_MODE': 'true',
      'LOG_LEVEL': 'INFO'
    }
  },

  // Configuración de directorios
  outputDir: 'test-results/artifacts',
  
  // Configuración de espera global
  expect: {
    timeout: 15000, // 15 segundos para assertions
  },

  // Configuración de artefactos y limpieza
  preserveOutput: 'failures-only',
  
  // Hook de configuración global
  globalSetup: require.resolve('./tests/global-setup.ts'),
  globalTeardown: require.resolve('./tests/global-teardown.ts'),
});