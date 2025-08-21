/**
 * CONFIGURACIÓN PLAYWRIGHT PARA VALIDACIÓN DE CORRECCIONES CRÍTICAS
 * Testing Engineer - Boris Requirements Validation
 * FECHA: 2025-08-20
 */

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: '.',
  testMatch: 'test-correlation-diagram-fixes-validation.spec.ts',
  
  // Configuración de timeouts extendidos para simulación D3
  timeout: 60000, // 60 segundos por test
  expect: {
    timeout: 15000 // 15 segundos para assertions
  },
  
  // Configuración de reportes para Boris
  reporter: [
    ['list'],
    ['html', { 
      outputFolder: 'test-results/fixes-validation-report',
      open: 'never'
    }],
    ['junit', { 
      outputFile: 'test-results/fixes-validation-junit.xml' 
    }]
  ],
  
  outputDir: 'test-results/',
  
  // Configuración global
  use: {
    // URL base de KRONOS
    baseURL: 'http://localhost:8000',
    
    // Configuración de browser
    headless: false, // Visible para debugging
    viewport: { width: 1920, height: 1080 },
    
    // Screenshots y videos para evidencia
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
    
    // Configuración de timeouts
    actionTimeout: 10000,
    navigationTimeout: 30000
  },

  // Configuración de workers para testing paralelo
  workers: 1, // Secuencial para mejor debugging
  
  // Configuración de reintentos
  retries: 1, // Un reintento en caso de falla
  
  // Proyectos de testing
  projects: [
    {
      name: 'chromium-fixes-validation',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 }
      },
    }
  ],

  // Configuración del servidor (KRONOS ya está ejecutándose)
  webServer: undefined, // No iniciar servidor, usar el existente
  
  // Configuración de directorios
  testIgnore: ['node_modules/**'],
  
  // Configuración específica para testing D3.js
  globalSetup: undefined,
  globalTeardown: undefined
});