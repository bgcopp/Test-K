import { defineConfig, devices } from '@playwright/test';

/**
 * Configuración específica para tests de certificación de números objetivo
 * Valida que los números objetivo aparezcan correctamente en KRONOS
 * después de las correcciones implementadas en el algoritmo de correlación
 */
export default defineConfig({
  // Directorio de tests específicos para números objetivo
  testDir: './tests/target-numbers-certification',
  
  // Configuración de timeouts extendidos para análisis de correlación
  timeout: 5 * 60 * 1000, // 5 minutos para análisis completo
  expect: {
    timeout: 30 * 1000 // 30 segundos para verificaciones
  },

  // Configuración de ejecución
  fullyParallel: false, // Secuencial para evitar conflictos de datos
  retries: 0, // Sin reintentos para tests de certificación
  workers: 1, // Un solo worker para mantener consistencia

  // Configuración de reportes
  reporter: [
    ['html', { open: 'never', outputFolder: 'test-results/target-numbers-certification' }],
    ['json', { outputFile: 'test-results/target-numbers-certification-results.json' }],
    ['junit', { outputFile: 'test-results/target-numbers-certification.xml' }]
  ],

  // Configuración global
  use: {
    // URL base de la aplicación KRONOS
    baseURL: 'http://localhost:8000',
    
    // Configuración de navegador
    headless: false, // Modo visual para debugging
    viewport: { width: 1920, height: 1080 },
    
    // Screenshots automáticos
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    
    // Configuración de timeouts
    actionTimeout: 30 * 1000,
    navigationTimeout: 60 * 1000,
    
    // Configuración de trazas
    trace: 'retain-on-failure'
  },

  // Configuración de proyecto específico
  projects: [
    {
      name: 'target-numbers-certification',
      use: { 
        ...devices['Desktop Chrome'],
        channel: 'chrome'
      },
    }
  ],

  // Setup global antes de todos los tests
  globalSetup: require.resolve('./tests/target-numbers-certification/global-setup.ts'),
  
  // Teardown global después de todos los tests
  globalTeardown: require.resolve('./tests/target-numbers-certification/global-teardown.ts'),

  // Configuración del servidor web (si es necesario)
  webServer: {
    command: 'cd Backend && python main.py',
    port: 8000,
    timeout: 120 * 1000,
    reuseExistingServer: !process.env.CI,
  }
});