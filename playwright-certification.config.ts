import { defineConfig, devices } from '@playwright/test';

/**
 * Configuración especial de Playwright para certificación final
 * Asume que KRONOS ya está ejecutándose en puerto 8000
 */
export default defineConfig({
  testDir: './tests',
  testMatch: '**/target-numbers-final-certification.spec.ts',
  
  timeout: 300000, // 5 minutos para el test completo
  retries: 0, // Sin reintentos para certificación final
  workers: 1,
  
  reporter: [
    ['html', { outputFolder: 'test-results/certification-html-report' }],
    ['json', { outputFile: 'test-results/certification-results.json' }],
    ['list']
  ],
  
  use: {
    baseURL: 'http://localhost:8081',
    actionTimeout: 30000,
    navigationTimeout: 60000,
    screenshot: 'always',
    video: 'on',
    trace: 'on',
    viewport: { width: 1280, height: 720 },
    ignoreHTTPSErrors: true,
  },

  projects: [
    {
      name: 'certification-chrome',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
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
  ],

  // NO webServer - asumimos que KRONOS ya está ejecutándose
  outputDir: 'test-results/certification-artifacts',
  
  expect: {
    timeout: 15000,
  },

  preserveOutput: 'always', // Mantener toda la evidencia
});