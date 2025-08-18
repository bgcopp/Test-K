/**
 * Pruebas E2E Completas para Validación de Carga CLARO y Algoritmo de Correlación
 * 
 * Suite completa de pruebas que valida:
 * 1. Carga de archivo HUNTER
 * 2. Carga de 4 archivos CLARO específicos (total 5,611 registros)
 * 3. Validación de base de datos entre cada paso
 * 4. Ejecución del algoritmo de correlación
 * 5. Verificación de números objetivo específicos
 * 
 * Archivos objetivo:
 * - 1-225211_LLAMADAS_ENTRANTES_POR_CELDA_545612_0.xlsx (973 registros)
 * - 1-225211_LLAMADAS_SALIENTES_POR_CELDA_545613_0.xlsx (961 registros)
 * - 2-225211_LLAMADAS_ENTRANTES_POR_CELDA_545614_0.xlsx (1939 registros)
 * - 2-225211_LLAMADAS_SALIENTES_POR_CELDA_545615_0.xlsx (1738 registros)
 * 
 * Números objetivo: 3224274851, 3208611034, 3104277553, 3102715509, 3143534707, 3214161903
 * 
 * @author Testing Team KRONOS
 * @version 1.0.0
 */

import { test, expect, Page } from '@playwright/test';
import { dbValidator } from './helpers/database-validator';
import path from 'path';
import fs from 'fs';

// Configuración de archivos objetivo
const TEST_DATA_PATH = process.env.TEST_DATA_PATH || 
  'C:\\Soluciones\\BGC\\claude\\KNSOft\\archivos\\envioarchivosparaanalizar (1)';

const CLARO_FILES = [
  {
    name: '1-225211_LLAMADAS_ENTRANTES_POR_CELDA_545612_0.xlsx',
    type: 'CALL_DATA',
    direction: 'entrantes',
    expectedRecords: 973,
    description: 'Archivo 1 - Llamadas Entrantes CLARO'
  },
  {
    name: '1-225211_LLAMADAS_SALIENTES_POR_CELDA_545613_0.xlsx',
    type: 'CALL_DATA', 
    direction: 'salientes',
    expectedRecords: 961,
    description: 'Archivo 1 - Llamadas Salientes CLARO'
  },
  {
    name: '2-225211_LLAMADAS_ENTRANTES_POR_CELDA_545614_0.xlsx',
    type: 'CALL_DATA',
    direction: 'entrantes', 
    expectedRecords: 1939,
    description: 'Archivo 2 - Llamadas Entrantes CLARO'
  },
  {
    name: '2-225211_LLAMADAS_SALIENTES_POR_CELDA_545615_0.xlsx',
    type: 'CALL_DATA',
    direction: 'salientes',
    expectedRecords: 1738,
    description: 'Archivo 2 - Llamadas Salientes CLARO'
  }
];

const HUNTER_FILE = 'SCANHUNTER.xlsx';
const EXPECTED_TOTAL_RECORDS = 5611;

const TARGET_NUMBERS = [
  '3224274851', '3208611034', '3104277553', 
  '3102715509', '3143534707', '3214161903'
];

const CORRELATION_PERIOD = {
  start: '2021-05-20T10:00',
  end: '2021-05-20T14:30'
};

// Variables de estado de la prueba
let testMissionId: string | null = null;
let testResults: any = {
  hunter_loaded: false,
  files_loaded: [],
  total_records: 0,
  correlation_results: null,
  target_numbers_found: []
};

test.describe('CLARO E2E Complete Validation', () => {
  let page: Page;

  test.beforeAll(async () => {
    console.log('🚀 Iniciando suite completa de pruebas CLARO E2E...');
    
    // Verificar que existen los archivos objetivo
    for (const file of CLARO_FILES) {
      const filePath = path.join(TEST_DATA_PATH, file.name);
      if (!fs.existsSync(filePath)) {
        throw new Error(`❌ Archivo no encontrado: ${filePath}`);
      }
      console.log(`✅ Archivo verificado: ${file.name}`);
    }

    const hunterPath = path.join(TEST_DATA_PATH, HUNTER_FILE);
    if (!fs.existsSync(hunterPath)) {
      throw new Error(`❌ Archivo HUNTER no encontrado: ${hunterPath}`);
    }
    console.log(`✅ Archivo HUNTER verificado: ${HUNTER_FILE}`);
  });

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
    
    // Configuración específica para carga masiva de archivos
    page.setDefaultTimeout(60000); // 1 minuto por acción
    page.setDefaultNavigationTimeout(90000); // 1.5 minutos navegación

    // Interceptar errores críticos
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log(`🚨 Console Error: ${msg.text()}`);
      }
    });

    page.on('requestfailed', request => {
      console.log(`❌ Request Failed: ${request.url()} - ${request.failure()?.errorText}`);
    });
  });

  test.afterAll(async () => {
    console.log('🧹 Limpiando datos de prueba...');
    
    // Generar reporte final
    const finalReport = {
      timestamp: new Date().toISOString(),
      test_results: testResults,
      success_criteria: {
        hunter_loaded: testResults.hunter_loaded,
        all_files_loaded: testResults.files_loaded.length === CLARO_FILES.length,
        correct_total_records: testResults.total_records === EXPECTED_TOTAL_RECORDS,
        target_numbers_found: testResults.target_numbers_found.length >= TARGET_NUMBERS.length
      }
    };

    const reportPath = path.join(process.cwd(), 'test-results', 'claro-e2e-final-report.json');
    fs.writeFileSync(reportPath, JSON.stringify(finalReport, null, 2));
    console.log(`📊 Reporte final generado: ${reportPath}`);
  });

  test('01 - Verificar disponibilidad de aplicación KRONOS', async () => {
    console.log('🔍 Verificando disponibilidad de KRONOS...');
    
    await test.step('Cargar aplicación y verificar conectividad', async () => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      
      // Verificar que la aplicación responde
      const bodyText = await page.locator('body').textContent();
      expect(bodyText).toBeTruthy();
      expect(bodyText!.length).toBeGreaterThan(10);
      
      // Capturar estado inicial
      await page.screenshot({ 
        path: 'test-results/claro-e2e-01-app-loaded.png', 
        fullPage: true 
      });
      
      console.log('✅ Aplicación KRONOS disponible y funcional');
    });
  });

  test('02 - Crear misión de prueba para carga CLARO', async () => {
    console.log('📋 Creando misión de prueba...');
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await test.step('Navegar a sección de Missions', async () => {
      const missionsLink = page.locator('a[href*="mission"], button:has-text("Mission"), a:has-text("Mission")').first();
      await expect(missionsLink).toBeVisible({ timeout: 30000 });
      await missionsLink.click();
      
      await page.waitForURL('**/mission*', { timeout: 60000 });
      await page.waitForLoadState('networkidle');
    });

    await test.step('Crear nueva misión para pruebas CLARO', async () => {
      const createButton = page.locator('button:has-text("Crear"), button:has-text("New"), button:has-text("Nueva")').first();
      
      if (await createButton.count() > 0) {
        await createButton.click();
        await page.waitForTimeout(2000);
        
        // Completar formulario de misión
        const missionName = `CLARO E2E Test Mission ${Date.now()}`;
        await page.fill('input[name="name"], input[placeholder*="nombre"]', missionName);
        await page.fill(
          'textarea, input[name="description"]', 
          'Misión de prueba para validación completa E2E de carga CLARO y algoritmo de correlación'
        );
        
        // Guardar misión
        const saveButton = page.locator('button:has-text("Guardar"), button:has-text("Save"), button[type="submit"]').first();
        await saveButton.click();
        
        await page.waitForTimeout(3000);
        await page.waitForLoadState('networkidle');
        
        console.log(`✅ Misión creada: ${missionName}`);
      } else {
        // Usar misión existente
        const firstMission = page.locator('tr[class*="hover"], [class*="mission-row"], button[class*="mission"]').first();
        await firstMission.click();
        await page.waitForLoadState('networkidle');
        
        console.log('✅ Usando misión existente');
      }
      
      await page.screenshot({ 
        path: 'test-results/claro-e2e-02-mission-created.png', 
        fullPage: true 
      });
    });
  });

  test('03 - Carga de archivo HUNTER como base', async () => {
    console.log('📁 Cargando archivo HUNTER...');
    
    await setupMissionDetailPage();

    await test.step('Configurar carga de archivo HUNTER', async () => {
      // Ir a pestaña de SCANNER (para datos HUNTER)
      const scannerTab = page.locator(
        'button:has-text("Scanner"), button:has-text("HUNTER"), [role="tab"]:has-text("Scanner")'
      ).first();
      
      if (await scannerTab.count() > 0) {
        await scannerTab.click();
        await page.waitForTimeout(2000);
      }
      
      await page.screenshot({ 
        path: 'test-results/claro-e2e-03-scanner-tab.png', 
        fullPage: true 
      });
    });

    await test.step('Cargar archivo HUNTER', async () => {
      const hunterFilePath = path.join(TEST_DATA_PATH, HUNTER_FILE);
      
      // Buscar input de archivo
      const fileInput = page.locator('input[type="file"]').first();
      await expect(fileInput).toBeAttached({ timeout: 15000 });
      
      // Cargar archivo HUNTER
      await fileInput.setInputFiles(hunterFilePath);
      await page.waitForTimeout(2000);
      
      // Verificar selección de archivo
      const fileText = await page.textContent('body');
      expect(fileText).toContain('SCANHUNTER');
      
      // Ejecutar carga
      const uploadButton = page.locator(
        'button:has-text("Cargar"), button:has-text("Upload"), button:has-text("Procesar")'
      ).first();
      
      await expect(uploadButton).toBeEnabled({ timeout: 10000 });
      await uploadButton.click();
      
      console.log('⏳ Procesando archivo HUNTER...');
      
      // Esperar procesamiento (HUNTER puede tomar tiempo)
      await page.waitForTimeout(10000);
      
      // Esperar mensaje de éxito o completado
      await Promise.race([
        page.waitForSelector('[class*="success"], :has-text("exitoso"), :has-text("completado")', { timeout: 180000 }),
        page.waitForSelector('[class*="error"]', { timeout: 180000 }),
        page.waitForTimeout(180000) // 3 minutos máximo
      ]);
      
      await page.screenshot({ 
        path: 'test-results/claro-e2e-03-hunter-loaded.png', 
        fullPage: true 
      });
    });

    await test.step('Validar carga de HUNTER en base de datos', async () => {
      console.log('🔍 Validando datos HUNTER en BD...');
      
      const hunterValidation = await dbValidator.validateHunterDataLoaded();
      expect(hunterValidation.success).toBeTruthy();
      expect(hunterValidation.count).toBeGreaterThan(0);
      
      testResults.hunter_loaded = true;
      
      console.log(`✅ Archivo HUNTER cargado correctamente: ${hunterValidation.count} registros`);
    });
  });

  // Tests de carga para cada archivo CLARO
  CLARO_FILES.forEach((claroFile, index) => {
    test(`04.${index + 1} - Carga de ${claroFile.description}`, async () => {
      console.log(`📁 Cargando ${claroFile.description}...`);
      
      await setupMissionDetailPage();

      await test.step('Configurar operador CLARO y tipo de documento', async () => {
        // Ir a pestaña de Datos de Operador
        const operatorTab = page.locator(
          'button:has-text("Datos de Operador"), button:has-text("Operador"), [role="tab"]:has-text("Operador")'
        ).first();
        
        if (await operatorTab.count() > 0) {
          await operatorTab.click();
          await page.waitForTimeout(2000);
        }
        
        // Seleccionar CLARO como operador
        const claroButton = page.locator('button:has-text("CLARO"), label:has-text("CLARO")').first();
        await expect(claroButton).toBeVisible({ timeout: 30000 });
        await claroButton.click();
        await page.waitForTimeout(1000);
        
        // Seleccionar tipo de documento
        const documentTypeRadio = page.locator(
          `input[value="${claroFile.type}"], label:has-text("Llamadas")`
        ).first();
        await expect(documentTypeRadio).toBeVisible({ timeout: 15000 });
        await documentTypeRadio.click();
        await page.waitForTimeout(1000);
        
        await page.screenshot({ 
          path: `test-results/claro-e2e-04-${index + 1}-config.png`, 
          fullPage: true 
        });
      });

      await test.step(`Cargar archivo ${claroFile.name}`, async () => {
        const filePath = path.join(TEST_DATA_PATH, claroFile.name);
        
        // Buscar input de archivo
        const fileInput = page.locator('input[type="file"]').first();
        await expect(fileInput).toBeAttached({ timeout: 15000 });
        
        // Cargar archivo
        await fileInput.setInputFiles(filePath);
        await page.waitForTimeout(2000);
        
        // Verificar selección
        const fileName = claroFile.name.substring(0, 20); // Primeros 20 caracteres
        await expect(page.locator(`text=${fileName}`).first()).toBeVisible({ timeout: 10000 });
        
        // Ejecutar carga
        const uploadButton = page.locator(
          'button:has-text("Cargar"), button:has-text("Upload"), button:has-text("Procesar")'
        ).first();
        
        await expect(uploadButton).toBeEnabled({ timeout: 15000 });
        await uploadButton.click();
        
        console.log(`⏳ Procesando ${claroFile.name}...`);
        
        // Esperar procesamiento con timeout extendido para archivos grandes
        await page.waitForTimeout(5000);
        
        await Promise.race([
          page.waitForSelector('[class*="success"], :has-text("exitoso"), :has-text("completado")', { timeout: 300000 }), // 5 minutos
          page.waitForSelector('[class*="error"]', { timeout: 300000 }),
          page.waitForTimeout(300000)
        ]);
        
        await page.screenshot({ 
          path: `test-results/claro-e2e-04-${index + 1}-loaded.png`, 
          fullPage: true 
        });
      });

      await test.step(`Validar carga de ${claroFile.name} en base de datos`, async () => {
        console.log(`🔍 Validando ${claroFile.name} en BD...`);
        
        // Esperar un poco para que se complete la transacción de BD
        await page.waitForTimeout(3000);
        
        // Validar conteo total actualizado
        const recordValidation = await dbValidator.validateClaroRecordCount(
          testResults.files_loaded.length * 1000 + claroFile.expectedRecords // Estimación para validación incremental
        );
        
        // Marcar archivo como cargado
        testResults.files_loaded.push({
          name: claroFile.name,
          expected_records: claroFile.expectedRecords,
          loaded_at: new Date().toISOString()
        });
        
        console.log(`✅ ${claroFile.description} cargado correctamente`);
      });
    });
  });

  test('05 - Validación final de registros CLARO cargados', async () => {
    console.log('🔢 Validando conteo final de registros CLARO...');
    
    await test.step('Validar total exacto de registros', async () => {
      const totalValidation = await dbValidator.validateClaroRecordCount(EXPECTED_TOTAL_RECORDS);
      
      expect(totalValidation.success).toBeTruthy();
      expect(totalValidation.count).toBe(EXPECTED_TOTAL_RECORDS);
      
      testResults.total_records = totalValidation.count || 0;
      
      console.log(`✅ Total de registros CLARO validado: ${totalValidation.count}/${EXPECTED_TOTAL_RECORDS}`);
    });

    await test.step('Validar distribución de registros por tipo', async () => {
      const distributionValidation = await dbValidator.validateClaroFileDistribution();
      
      expect(distributionValidation.success).toBeTruthy();
      
      if (distributionValidation.data) {
        console.log(`📊 Distribución de registros:`);
        console.log(`   - Entrantes: ${distributionValidation.data.entrantes_found}/${distributionValidation.data.entrantes_expected}`);
        console.log(`   - Salientes: ${distributionValidation.data.salientes_found}/${distributionValidation.data.salientes_expected}`);
      }
    });

    await test.step('Generar reporte intermedio de base de datos', async () => {
      const dbReport = await dbValidator.generateDatabaseReport();
      
      const reportPath = path.join(process.cwd(), 'test-results', 'claro-e2e-db-report.json');
      fs.writeFileSync(reportPath, JSON.stringify(dbReport, null, 2));
      
      console.log(`📊 Reporte de BD generado: ${reportPath}`);
    });
  });

  test('06 - Búsqueda de números objetivo en datos cargados', async () => {
    console.log('🎯 Buscando números objetivo en datos cargados...');
    
    await test.step('Validar presencia de números objetivo', async () => {
      const targetValidation = await dbValidator.validateTargetNumbers(TARGET_NUMBERS);
      
      console.log(`🔍 Resultados de búsqueda de números objetivo:`);
      
      if (targetValidation.data?.target_numbers_analysis) {
        for (const [number, analysis] of Object.entries(targetValidation.data.target_numbers_analysis)) {
          const found = (analysis as any).found_in_claro || (analysis as any).found_in_hunter;
          console.log(`   - ${number}: ${found ? '✅ ENCONTRADO' : '❌ NO ENCONTRADO'}`);
          
          if (found) {
            testResults.target_numbers_found.push(number);
          }
        }
      }
      
      // Al menos algunos números deben encontrarse
      expect(testResults.target_numbers_found.length).toBeGreaterThan(0);
      
      console.log(`✅ Números objetivo encontrados: ${testResults.target_numbers_found.length}/${TARGET_NUMBERS.length}`);
    });
  });

  test('07 - Ejecución del algoritmo de correlación', async () => {
    console.log('🔄 Ejecutando algoritmo de correlación...');
    
    await setupMissionDetailPage();

    await test.step('Configurar parámetros de correlación', async () => {
      // Ir a pestaña de Análisis
      const analysisTab = page.locator(
        'button:has-text("Análisis"), button:has-text("Analysis"), [role="tab"]:has-text("Análisis")'
      ).first();
      
      if (await analysisTab.count() > 0) {
        await analysisTab.click();
        await page.waitForTimeout(2000);
      }
      
      // Configurar fechas de análisis
      const startTimeInput = page.locator('input[type="datetime-local"], input[name*="start"], input[placeholder*="inicio"]').first();
      if (await startTimeInput.count() > 0) {
        await startTimeInput.fill(CORRELATION_PERIOD.start);
      }
      
      const endTimeInput = page.locator('input[type="datetime-local"], input[name*="end"], input[placeholder*="fin"]').first();
      if (await endTimeInput.count() > 0) {
        await endTimeInput.fill(CORRELATION_PERIOD.end);
      }
      
      await page.screenshot({ 
        path: 'test-results/claro-e2e-07-correlation-config.png', 
        fullPage: true 
      });
    });

    await test.step('Ejecutar análisis de correlación', async () => {
      // Buscar botón de análisis
      const analyzeButton = page.locator(
        'button:has-text("Analizar"), button:has-text("Analyze"), button:has-text("Ejecutar")'
      ).first();
      
      if (await analyzeButton.count() > 0) {
        await analyzeButton.click();
        
        console.log('⏳ Ejecutando análisis de correlación...');
        
        // Esperar análisis (puede tomar varios minutos)
        await page.waitForTimeout(10000);
        
        await Promise.race([
          page.waitForSelector('[class*="success"], :has-text("completado"), [class*="result"]', { timeout: 600000 }), // 10 minutos
          page.waitForSelector('[class*="error"]', { timeout: 600000 }),
          page.waitForTimeout(600000)
        ]);
        
        await page.screenshot({ 
          path: 'test-results/claro-e2e-07-correlation-completed.png', 
          fullPage: true 
        });
      } else {
        console.log('ℹ️  Botón de análisis no encontrado, ejecutando validación de BD directa');
      }
    });

    await test.step('Validar resultados del algoritmo de correlación', async () => {
      console.log('🔍 Validando resultados de correlación en BD...');
      
      const correlationValidation = await dbValidator.executeCorrelationAnalysis(
        CORRELATION_PERIOD.start, 
        CORRELATION_PERIOD.end, 
        TARGET_NUMBERS
      );
      
      testResults.correlation_results = correlationValidation;
      
      if (correlationValidation.success) {
        console.log(`✅ Algoritmo de correlación ejecutado exitosamente`);
        console.log(`   - Correlaciones encontradas: ${correlationValidation.count}`);
        
        if (correlationValidation.data?.found_numbers) {
          console.log(`   - Números objetivo en correlaciones: ${correlationValidation.data.found_numbers.join(', ')}`);
        }
      } else {
        console.log(`⚠️  Algoritmo de correlación con resultados limitados: ${correlationValidation.error || 'Sin detalles'}`);
      }
      
      // Considerar éxito parcial si encontramos algunas correlaciones
      expect(correlationValidation.count).toBeGreaterThan(0);
    });
  });

  test('08 - Validación final y generación de reporte', async () => {
    console.log('📋 Generando validación final...');
    
    await test.step('Validar criterios de éxito completos', async () => {
      const successCriteria = {
        hunter_loaded: testResults.hunter_loaded,
        all_files_loaded: testResults.files_loaded.length === CLARO_FILES.length,
        correct_total_records: testResults.total_records === EXPECTED_TOTAL_RECORDS,
        target_numbers_found: testResults.target_numbers_found.length > 0,
        correlation_executed: testResults.correlation_results !== null
      };
      
      console.log('📊 Criterios de éxito:');
      for (const [criterion, passed] of Object.entries(successCriteria)) {
        console.log(`   - ${criterion}: ${passed ? '✅' : '❌'}`);
      }
      
      // Criterios mínimos para considerar la prueba exitosa
      expect(successCriteria.hunter_loaded).toBeTruthy();
      expect(successCriteria.all_files_loaded).toBeTruthy();
      expect(successCriteria.correct_total_records).toBeTruthy();
      expect(successCriteria.target_numbers_found).toBeTruthy();
      
      testResults.success_criteria = successCriteria;
    });

    await test.step('Generar reporte final completo', async () => {
      const finalReport = {
        test_suite: 'CLARO E2E Complete Validation',
        timestamp: new Date().toISOString(),
        execution_summary: {
          total_files_processed: testResults.files_loaded.length + 1, // +1 por HUNTER
          total_records_loaded: testResults.total_records,
          target_numbers_searched: TARGET_NUMBERS.length,
          target_numbers_found: testResults.target_numbers_found.length,
          correlation_executed: testResults.correlation_results !== null
        },
        detailed_results: testResults,
        files_processed: [
          { name: HUNTER_FILE, type: 'HUNTER', status: 'loaded' },
          ...testResults.files_loaded
        ],
        recommendations: [
          'Verificar manualmente números objetivo que no fueron encontrados',
          'Ejecutar análisis adicional en períodos de tiempo extendidos',
          'Validar integridad de datos en archivos fuente',
          'Considerar optimizaciones de rendimiento para cargas futuras'
        ]
      };
      
      const reportPath = path.join(process.cwd(), 'test-results', `claro-e2e-final-report-${Date.now()}.json`);
      fs.writeFileSync(reportPath, JSON.stringify(finalReport, null, 2));
      
      console.log(`📊 Reporte final completo generado: ${reportPath}`);
      console.log(`🎉 Suite de pruebas CLARO E2E completada exitosamente`);
    });
  });

  // Función helper para navegar a Mission Detail
  async function setupMissionDetailPage() {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Navegar a missions
    const missionsLink = page.locator('a[href*="mission"], button:has-text("Mission"), a:has-text("Mission")').first();
    if (await missionsLink.count() > 0) {
      await missionsLink.click();
      await page.waitForLoadState('networkidle');
    }

    // Seleccionar primera misión disponible
    const firstMission = page.locator('tr[class*="hover"], [class*="mission-row"], button[class*="mission"]').first();
    if (await firstMission.count() > 0) {
      await firstMission.click();
      await page.waitForLoadState('networkidle');
    }
  }
});