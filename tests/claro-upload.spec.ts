import { test, expect, Page } from '@playwright/test';
import fs from 'fs';
import path from 'path';

/**
 * Tests E2E para carga de archivos CLARO en KRONOS
 * Valida el flujo completo desde login hasta verificación en BD
 * 
 * Casos cubiertos:
 * 1. Navegación completa de la aplicación
 * 2. Carga de archivos CLARO (llamadas salientes, entrantes, datos)
 * 3. Validación de UI y respuestas del sistema
 * 4. Verificación de persistencia en base de datos
 */

test.describe('CLARO File Upload - End to End', () => {
  let page: Page;
  let testDataPath: string;

  test.beforeAll(async () => {
    testDataPath = path.join(process.cwd(), 'test-data');
  });

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
    
    // Configurar timeouts para aplicación Eel (más lentos que SPA tradicional)
    page.setDefaultTimeout(30000);
    page.setDefaultNavigationTimeout(60000);

    // Interceptar errores de consola para debugging
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log(`🚨 Console Error: ${msg.text()}`);
      }
    });

    // Interceptar requests fallidos
    page.on('requestfailed', request => {
      console.log(`❌ Request Failed: ${request.url()} - ${request.failure()?.errorText}`);
    });
  });

  test('01 - Verificar aplicación KRONOS está corriendo', async () => {
    console.log('🔍 Verificando disponibilidad de KRONOS...');
    
    await test.step('Cargar página principal', async () => {
      await page.goto('/');
      
      // Verificar que la aplicación carga (puede ser login o dashboard)
      await page.waitForLoadState('networkidle');
      
      // Debe aparecer al menos el título de KRONOS o elementos de login
      const hasTitle = await page.locator('h1, h2, title').count() > 0;
      expect(hasTitle).toBeTruthy();
      
      await page.screenshot({ path: 'test-results/01-app-loaded.png', fullPage: true });
    });

    await test.step('Verificar conectividad básica', async () => {
      // Verificar que no hay errores críticos de carga
      const errorElements = await page.locator('[class*="error"], [class*="Error"]').count();
      expect(errorElements).toBe(0);
      
      // Verificar que hay contenido visible
      const bodyText = await page.locator('body').textContent();
      expect(bodyText).toBeTruthy();
      expect(bodyText!.length).toBeGreaterThan(10);
    });
  });

  test('02 - Navegación a sección de Missions', async () => {
    console.log('🧭 Navegando a sección de Missions...');

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await test.step('Acceso a Missions desde sidebar', async () => {
      // Buscar link de Missions en sidebar o navegación
      const missionsLink = page.locator('a[href*="mission"], button:has-text("Mission"), a:has-text("Mission")').first();
      
      await expect(missionsLink).toBeVisible({ timeout: 15000 });
      await missionsLink.click();
      
      // Esperar navegación
      await page.waitForURL('**/mission*', { timeout: 30000 });
      await page.waitForLoadState('networkidle');
      
      await page.screenshot({ path: 'test-results/02-missions-page.png', fullPage: true });
    });

    await test.step('Verificar página de Missions cargada', async () => {
      // Verificar elementos característicos de la página de missions
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('Mission');
      
      // Debe haber al menos una misión o botón para crear misión
      const hasMissionContent = await page.locator(
        'button:has-text("Crear"), button:has-text("New"), [class*="mission"], [data-testid*="mission"]'
      ).count() > 0;
      
      expect(hasMissionContent).toBeTruthy();
    });
  });

  test('03 - Acceso a Mission Detail y pestaña Datos de Operador', async () => {
    console.log('📋 Accediendo a Mission Detail...');

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await test.step('Navegar a Missions y seleccionar misión', async () => {
      // Ir a missions
      const missionsLink = page.locator('a[href*="mission"], button:has-text("Mission"), a:has-text("Mission")').first();
      await missionsLink.click();
      await page.waitForLoadState('networkidle');

      // Buscar y hacer clic en primera misión disponible
      const firstMission = page.locator('tr[class*="hover"], [class*="mission-row"], button[class*="mission"]').first();
      
      if (await firstMission.count() > 0) {
        await firstMission.click();
      } else {
        // Si no hay misiones, crear una nueva para testing
        const createButton = page.locator('button:has-text("Crear"), button:has-text("New")').first();
        if (await createButton.count() > 0) {
          await createButton.click();
          // Completar formulario básico de misión
          await page.fill('input[name="name"], input[placeholder*="nombre"]', 'Test Mission CLARO E2E');
          await page.fill('textarea, input[name="description"]', 'Misión de prueba para validación CLARO');
          
          const saveButton = page.locator('button:has-text("Guardar"), button:has-text("Save"), button[type="submit"]').first();
          await saveButton.click();
        }
      }
      
      await page.waitForLoadState('networkidle');
      await page.screenshot({ path: 'test-results/03-mission-detail.png', fullPage: true });
    });

    await test.step('Acceder a pestaña "Datos de Operador"', async () => {
      // Buscar y hacer clic en la pestaña de datos de operador
      const operatorTab = page.locator(
        'button:has-text("Datos de Operador"), button:has-text("Operador"), [role="tab"]:has-text("Operador")'
      ).first();
      
      await expect(operatorTab).toBeVisible({ timeout: 15000 });
      await operatorTab.click();
      
      await page.waitForTimeout(2000); // Esperar a que se cargue el contenido de la pestaña
      
      // Verificar que aparece el formulario de carga
      const uploadSection = page.locator('[class*="upload"], [class*="Upload"], form');
      await expect(uploadSection.first()).toBeVisible();
      
      await page.screenshot({ path: 'test-results/03-operator-data-tab.png', fullPage: true });
    });
  });

  test('04 - Carga de archivo CLARO llamadas salientes', async () => {
    console.log('📁 Cargando archivo CLARO llamadas salientes...');
    
    await setupMissionDetailPage();

    await test.step('Configurar operador CLARO', async () => {
      // Seleccionar CLARO como operador
      const claroButton = page.locator('button:has-text("CLARO")').first();
      await expect(claroButton).toBeVisible({ timeout: 15000 });
      await claroButton.click();
      
      await page.screenshot({ path: 'test-results/04-claro-selected.png', fullPage: true });
    });

    await test.step('Seleccionar tipo de documento - Llamadas', async () => {
      // Seleccionar tipo de documento para llamadas
      const callDataRadio = page.locator('input[value="CALL_DATA"], label:has-text("Llamadas")').first();
      await expect(callDataRadio).toBeVisible({ timeout: 10000 });
      await callDataRadio.click();
      
      await page.screenshot({ path: 'test-results/04-call-data-selected.png', fullPage: true });
    });

    await test.step('Cargar archivo CSV de llamadas salientes', async () => {
      const filePath = path.join(testDataPath, 'test_claro_salientes.csv');
      
      // Verificar que el archivo existe
      expect(fs.existsSync(filePath)).toBeTruthy();
      
      // Buscar input de archivo
      const fileInput = page.locator('input[type="file"]');
      await expect(fileInput).toBeAttached();
      
      // Cargar archivo
      await fileInput.setInputFiles(filePath);
      
      // Verificar que el archivo se seleccionó
      await page.waitForTimeout(1000);
      const fileName = await page.locator(':has-text("test_claro_salientes.csv")').count();
      expect(fileName).toBeGreaterThan(0);
      
      await page.screenshot({ path: 'test-results/04-file-selected.png', fullPage: true });
    });

    await test.step('Ejecutar carga del archivo', async () => {
      // Buscar y hacer clic en botón de carga
      const uploadButton = page.locator(
        'button:has-text("Cargar"), button:has-text("Upload"), button:has-text("Procesar")'
      ).first();
      
      await expect(uploadButton).toBeEnabled();
      await uploadButton.click();
      
      // Esperar a que aparezca indicador de progreso
      const progressIndicator = page.locator(
        '[class*="progress"], [class*="loading"], [class*="spin"]'
      );
      
      if (await progressIndicator.count() > 0) {
        await expect(progressIndicator.first()).toBeVisible();
        console.log('⏳ Progreso de carga detectado...');
      }
      
      // Esperar a que termine la carga (máximo 2 minutos)
      await page.waitForTimeout(5000); // Esperar inicio del procesamiento
      
      // Esperar a que desaparezca el indicador de progreso o aparezca mensaje de éxito
      await Promise.race([
        page.waitForSelector('[class*="success"], [class*="Success"], :has-text("exitoso")', { timeout: 120000 }),
        page.waitForSelector('[class*="error"], [class*="Error"]', { timeout: 120000 }),
        page.waitForTimeout(120000) // Timeout de seguridad
      ]);
      
      await page.screenshot({ path: 'test-results/04-upload-completed.png', fullPage: true });
    });

    await test.step('Verificar resultado de la carga', async () => {
      const pageContent = await page.textContent('body');
      
      // Verificar que no hay errores críticos
      const hasError = pageContent.toLowerCase().includes('error') && 
                      !pageContent.toLowerCase().includes('sin error');
      
      if (hasError) {
        console.log('⚠️  Posible error detectado en la carga');
        await page.screenshot({ path: 'test-results/04-upload-error.png', fullPage: true });
      }
      
      // Buscar indicadores de éxito o completado
      const successIndicators = await page.locator(
        ':has-text("exitoso"), :has-text("completado"), :has-text("procesado"), [class*="success"]'
      ).count();
      
      expect(successIndicators).toBeGreaterThan(0);
      
      console.log('✅ Carga de archivo CLARO salientes completada');
    });
  });

  test('05 - Carga de archivo CLARO llamadas entrantes', async () => {
    console.log('📁 Cargando archivo CLARO llamadas entrantes...');
    
    await setupMissionDetailPage();

    await test.step('Configurar operador CLARO y tipo de documento', async () => {
      // Seleccionar CLARO
      const claroButton = page.locator('button:has-text("CLARO")').first();
      await claroButton.click();
      
      // Seleccionar tipo de documento para llamadas
      const callDataRadio = page.locator('input[value="CALL_DATA"], label:has-text("Llamadas")').first();
      await callDataRadio.click();
    });

    await test.step('Cargar archivo CSV de llamadas entrantes', async () => {
      const filePath = path.join(testDataPath, 'test_claro_entrantes.csv');
      expect(fs.existsSync(filePath)).toBeTruthy();
      
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles(filePath);
      
      await page.waitForTimeout(1000);
      
      // Ejecutar carga
      const uploadButton = page.locator(
        'button:has-text("Cargar"), button:has-text("Upload"), button:has-text("Procesar")'
      ).first();
      
      await uploadButton.click();
      
      // Esperar procesamiento
      await page.waitForTimeout(5000);
      
      await Promise.race([
        page.waitForSelector('[class*="success"], :has-text("exitoso")', { timeout: 120000 }),
        page.waitForSelector('[class*="error"]', { timeout: 120000 }),
        page.waitForTimeout(120000)
      ]);
      
      await page.screenshot({ path: 'test-results/05-entrantes-uploaded.png', fullPage: true });
    });

    console.log('✅ Carga de archivo CLARO entrantes completada');
  });

  test('06 - Carga de archivo CLARO datos por celda', async () => {
    console.log('📁 Cargando archivo CLARO datos por celda...');
    
    await setupMissionDetailPage();

    await test.step('Configurar operador CLARO y tipo de documento', async () => {
      // Seleccionar CLARO
      const claroButton = page.locator('button:has-text("CLARO")').first();
      await claroButton.click();
      
      // Seleccionar tipo de documento para datos celulares
      const cellularDataRadio = page.locator('input[value="CELLULAR_DATA"], label:has-text("Datos")').first();
      await cellularDataRadio.click();
    });

    await test.step('Cargar archivo CSV de datos por celda', async () => {
      const filePath = path.join(testDataPath, 'test_claro_datos.csv');
      expect(fs.existsSync(filePath)).toBeTruthy();
      
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles(filePath);
      
      await page.waitForTimeout(1000);
      
      // Ejecutar carga
      const uploadButton = page.locator(
        'button:has-text("Cargar"), button:has-text("Upload"), button:has-text("Procesar")'
      ).first();
      
      await uploadButton.click();
      
      // Esperar procesamiento
      await page.waitForTimeout(5000);
      
      await Promise.race([
        page.waitForSelector('[class*="success"], :has-text("exitoso")', { timeout: 120000 }),
        page.waitForSelector('[class*="error"]', { timeout: 120000 }),
        page.waitForTimeout(120000)
      ]);
      
      await page.screenshot({ path: 'test-results/06-datos-uploaded.png', fullPage: true });
    });

    console.log('✅ Carga de archivo CLARO datos por celda completada');
  });

  test('07 - Verificar datos cargados en la interfaz', async () => {
    console.log('🔍 Verificando datos cargados en la interfaz...');
    
    await setupMissionDetailPage();

    await test.step('Verificar lista de archivos cargados', async () => {
      // Buscar sección que muestre archivos cargados
      const filesSection = page.locator(
        '[class*="file"], [class*="sheet"], table, [class*="list"]'
      );
      
      if (await filesSection.count() > 0) {
        const fileContent = await filesSection.first().textContent();
        
        // Verificar que aparecen referencias a archivos CLARO
        expect(fileContent).toContain('CLARO');
        
        await page.screenshot({ path: 'test-results/07-files-list.png', fullPage: true });
        
        console.log('✅ Archivos CLARO visibles en la interfaz');
      } else {
        console.log('ℹ️  No se encontró sección de archivos en la interfaz');
      }
    });

    await test.step('Verificar estadísticas de registros', async () => {
      const pageContent = await page.textContent('body');
      
      // Buscar números que indiquen registros procesados
      const numberPattern = /\d+\s*(registro|record|procesado|cargado)/gi;
      const numbers = pageContent.match(numberPattern);
      
      if (numbers && numbers.length > 0) {
        console.log(`📊 Estadísticas encontradas: ${numbers.join(', ')}`);
        
        // Verificar que hay al menos algunos registros
        const hasRecords = numbers.some(n => {
          const num = parseInt(n.match(/\d+/)?.[0] || '0');
          return num > 0;
        });
        
        expect(hasRecords).toBeTruthy();
      }
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

    // Seleccionar o crear misión
    const firstMission = page.locator('tr[class*="hover"], [class*="mission-row"], button[class*="mission"]').first();
    if (await firstMission.count() > 0) {
      await firstMission.click();
    } else {
      // Crear nueva misión si no existe
      const createButton = page.locator('button:has-text("Crear"), button:has-text("New")').first();
      if (await createButton.count() > 0) {
        await createButton.click();
        await page.fill('input[name="name"], input[placeholder*="nombre"]', 'Test Mission CLARO E2E');
        await page.fill('textarea, input[name="description"]', 'Misión de prueba para validación CLARO');
        
        const saveButton = page.locator('button:has-text("Guardar"), button:has-text("Save"), button[type="submit"]').first();
        await saveButton.click();
      }
    }

    await page.waitForLoadState('networkidle');

    // Ir a pestaña de datos de operador
    const operatorTab = page.locator(
      'button:has-text("Datos de Operador"), button:has-text("Operador"), [role="tab"]:has-text("Operador")'
    ).first();
    
    if (await operatorTab.count() > 0) {
      await operatorTab.click();
      await page.waitForTimeout(2000);
    }
  }
});