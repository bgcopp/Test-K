/**
 * Configuración de Playwright para Testing del Diagrama de Correlación
 * 
 * Configuración optimizada específicamente para testing del diagrama interactivo
 * con ajustes de performance, timeouts y reportes detallados.
 */

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  // Directorio de tests
  testDir: './',
  
  // Archivos de test específicos para diagrama
  testMatch: [
    'test-correlation-diagram-complete.spec.ts',
    'tests/correlation-diagram/**/*.spec.ts'
  ],
  
  // Configuración de ejecución
  fullyParallel: false, // Secuencial para mejor debugging
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1,
  workers: process.env.CI ? 1 : 1, // Un worker para evitar conflictos
  
  // Timeouts optimizados para diagrama interactivo
  timeout: 60000, // 60s para tests individuales
  expect: {
    timeout: 10000 // 10s para assertions
  },
  
  // Configuración global
  use: {
    // URL base de la aplicación
    baseURL: 'http://localhost:5173',
    
    // Configuración de navegador
    viewport: { width: 1400, height: 900 }, // Viewport óptimo para diagrama
    
    // Configuración de interacciones
    actionTimeout: 15000,
    navigationTimeout: 30000,
    
    // Configuración de traces y videos
    trace: 'on-first-retry',
    video: 'retain-on-failure',
    screenshot: 'only-on-failure',
    
    // Headers para desarrollo
    extraHTTPHeaders: {
      'Accept': 'application/json',
    },
    
    // Configuración de red
    ignoreHTTPSErrors: true,
  },

  // Configuración de proyectos (navegadores)
  projects: [
    {
      name: 'chromium-desktop',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1400, height: 900 },
        launchOptions: {
          args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--force-device-scale-factor=1'
          ]
        }
      },
    },
    
    {
      name: 'edge-desktop',
      use: { 
        ...devices['Desktop Edge'],
        viewport: { width: 1400, height: 900 },
        channel: 'msedge'
      },
    },
    
    // Firefox solo para tests de compatibilidad específicos
    {
      name: 'firefox-desktop',
      use: { 
        ...devices['Desktop Firefox'],
        viewport: { width: 1400, height: 900 }
      },
      testIgnore: ['**/performance/**', '**/memory-leak/**'], // Firefox tiene diferentes métricas
    },
    
    // Proyecto específico para testing mobile responsive (opcional)
    {
      name: 'mobile-chrome',
      use: { 
        ...devices['Pixel 5'],
        // Viewport mobile para testing responsive del diagrama
      },
      testIgnore: ['**/drag-drop/**'], // Drag-drop diferente en mobile
    },
  ],

  // Configuración del servidor web de desarrollo
  webServer: {
    command: 'cd Frontend && npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 120000, // 2 minutos para que Vite compile
    stdout: 'ignore',
    stderr: 'pipe',
  },

  // Configuración de reportes
  reporter: [
    // Reporte en consola con detalles
    ['list', { printSteps: true }],
    
    // Reporte HTML interactivo
    ['html', { 
      outputFolder: 'test-results/html-report',
      open: 'never'
    }],
    
    // Reporte JSON para análisis posterior
    ['json', { 
      outputFile: 'test-results/correlation-diagram-results.json' 
    }],
    
    // Reporte JUnit para CI/CD
    ['junit', { 
      outputFile: 'test-results/correlation-diagram-junit.xml' 
    }],
    
    // Reporte personalizado para métricas del diagrama
    ['./utils/correlation-diagram-reporter.ts']
  ],

  // Configuración de salida
  outputDir: 'test-results/artifacts',
  
  // Configuración de screenshots y videos
  use: {
    ...devices['Desktop Chrome'].use,
    screenshot: {
      mode: 'only-on-failure',
      fullPage: true
    },
    video: {
      mode: 'retain-on-failure',
      size: { width: 1400, height: 900 }
    }
  },

  // Configuración específica para el diagrama
  globalSetup: './utils/global-setup-correlation.ts',
  globalTeardown: './utils/global-teardown-correlation.ts',
});