import { chromium, FullConfig } from '@playwright/test';

/**
 * Setup global para tests de certificación de números objetivo
 * Prepara el entorno de pruebas antes de ejecutar todos los tests
 */
async function globalSetup(config: FullConfig) {
  console.log('🚀 Iniciando setup global para certificación de números objetivo...');
  
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Verificar que la aplicación esté disponible
    console.log('🔍 Verificando disponibilidad de la aplicación en localhost:8000...');
    await page.goto('http://localhost:8000', { timeout: 60000 });
    
    // Verificar que la página principal cargue correctamente
    await page.waitForSelector('body', { timeout: 30000 });
    console.log('✅ Aplicación KRONOS disponible y respondiendo');

    // Verificar que la base de datos tenga datos
    console.log('🗄️ Verificando disponibilidad de datos de prueba...');
    
    // Navegar a misiones para verificar que exista mission_MPFRBNsb
    await page.click('text=Misiones');
    await page.waitForSelector('table', { timeout: 30000 });
    
    // Buscar la misión específica
    const missionExists = await page.locator('text=mission_MPFRBNsb').first().isVisible();
    if (!missionExists) {
      throw new Error('❌ Misión mission_MPFRBNsb no encontrada. Verificar datos de prueba.');
    }
    
    console.log('✅ Misión mission_MPFRBNsb encontrada');
    console.log('✅ Setup global completado exitosamente');
    
  } catch (error) {
    console.error('❌ Error en setup global:', error);
    throw error;
  } finally {
    await browser.close();
  }
}

export default globalSetup;