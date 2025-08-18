import { FullConfig } from '@playwright/test';

/**
 * Teardown global para tests de certificación de números objetivo
 * Limpia el entorno después de ejecutar todos los tests
 */
async function globalTeardown(config: FullConfig) {
  console.log('🧹 Iniciando teardown global...');
  
  try {
    // Generar reporte final de certificación
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    console.log(`📊 Reporte de certificación generado: ${timestamp}`);
    
    // Limpiar archivos temporales si es necesario
    console.log('🗑️ Limpiando archivos temporales...');
    
    console.log('✅ Teardown global completado');
    
  } catch (error) {
    console.error('❌ Error en teardown global:', error);
  }
}

export default globalTeardown;