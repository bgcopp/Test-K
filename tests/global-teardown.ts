import { FullConfig } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';

/**
 * Limpieza global de Playwright para tests KRONOS
 * Se ejecuta UNA VEZ después de todos los tests
 * 
 * Responsabilidades:
 * - Limpiar archivos temporales de prueba
 * - Generar reporte consolidado
 * - Opcional: restaurar backup de BD si es necesario
 */
async function globalTeardown(config: FullConfig) {
  console.log('\n🧹 KRONOS E2E Tests - Limpieza Global');
  console.log('=' * 50);

  const testDataPath = path.join(process.cwd(), 'test-data');
  const testResultsPath = path.join(process.cwd(), 'test-results');

  // 1. Limpiar archivos de prueba generados
  if (fs.existsSync(testDataPath)) {
    try {
      fs.rmSync(testDataPath, { recursive: true, force: true });
      console.log('✅ Archivos de prueba limpiados');
    } catch (error) {
      console.log('⚠️  Error limpiando archivos de prueba:', error);
    }
  }

  // 2. Generar timestamp del reporte final
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
  
  // 3. Verificar existencia de reportes
  if (fs.existsSync(testResultsPath)) {
    const files = fs.readdirSync(testResultsPath);
    console.log(`✅ Reportes generados: ${files.length} archivos`);
    
    // Renombrar reporte HTML con timestamp si existe
    const htmlReportPath = path.join(testResultsPath, 'html-report');
    if (fs.existsSync(htmlReportPath)) {
      const newHtmlPath = path.join(testResultsPath, `html-report-${timestamp}`);
      try {
        fs.renameSync(htmlReportPath, newHtmlPath);
        console.log(`✅ Reporte HTML archivado: html-report-${timestamp}`);
      } catch (error) {
        console.log('⚠️  Error archivando reporte HTML:', error);
      }
    }
  }

  // 4. Mostrar resumen de archivos importantes
  console.log('\n📊 Archivos importantes generados:');
  
  const importantFiles = [
    path.join(testResultsPath, 'results.json'),
    path.join(testResultsPath, 'junit.xml'),
    path.join(process.cwd(), 'Backend', 'kronos.db'),
  ];

  importantFiles.forEach(filePath => {
    if (fs.existsSync(filePath)) {
      const stats = fs.statSync(filePath);
      console.log(`   ✅ ${path.basename(filePath)} (${(stats.size / 1024).toFixed(1)} KB)`);
    }
  });

  // 5. Verificar si hay backups de BD que limpiar (mantener solo los más recientes)
  const backendPath = path.join(process.cwd(), 'Backend');
  if (fs.existsSync(backendPath)) {
    const files = fs.readdirSync(backendPath);
    const backups = files
      .filter(file => file.startsWith('kronos.db.backup_testing_'))
      .sort()
      .reverse(); // Más recientes primero

    // Mantener solo los 3 backups más recientes
    if (backups.length > 3) {
      const toDelete = backups.slice(3);
      toDelete.forEach(backup => {
        try {
          fs.unlinkSync(path.join(backendPath, backup));
          console.log(`✅ Backup antiguo eliminado: ${backup}`);
        } catch (error) {
          console.log(`⚠️  Error eliminando backup ${backup}:`, error);
        }
      });
    }
  }

  // 6. Mensaje final con instrucciones
  console.log('\n📋 RESUMEN DE LIMPIEZA:');
  console.log('   ✅ Archivos temporales eliminados');
  console.log('   ✅ Reportes archivados con timestamp');
  console.log('   ✅ Backups de BD optimizados');
  
  console.log('\n📖 Para revisar resultados:');
  console.log('   npm run report                    # Ver reporte interactivo');
  console.log('   cd Backend && python verify_target_numbers.py  # Verificar BD final');
  
  console.log('\n🎯 Limpieza global completada');
}

export default globalTeardown;