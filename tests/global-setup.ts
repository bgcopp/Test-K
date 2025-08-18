import { chromium, FullConfig } from '@playwright/test';
import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';

/**
 * Configuración global de Playwright para tests KRONOS
 * Se ejecuta UNA VEZ antes de todos los tests
 * 
 * Responsabilidades:
 * - Verificar dependencias necesarias
 * - Crear backup de base de datos
 * - Generar archivos de prueba CLARO
 * - Validar disponibilidad del puerto 8000
 */
async function globalSetup(config: FullConfig) {
  console.log('\n🚀 KRONOS E2E Tests - Configuración Global');
  console.log('=' * 60);

  // 1. Verificar que Python esté disponible
  try {
    execSync('python --version', { stdio: 'pipe' });
    console.log('✅ Python verificado');
  } catch (error) {
    console.error('❌ Python no encontrado. Instale Python 3.8+');
    process.exit(1);
  }

  // 2. Verificar directorio Backend
  const backendPath = path.join(process.cwd(), 'Backend');
  if (!fs.existsSync(backendPath)) {
    console.error('❌ Directorio Backend no encontrado');
    process.exit(1);
  }
  console.log('✅ Directorio Backend verificado');

  // 3. Crear backup de la base de datos
  const dbPath = path.join(backendPath, 'kronos.db');
  const backupPath = path.join(backendPath, `kronos.db.backup_testing_${Date.now()}`);
  
  if (fs.existsSync(dbPath)) {
    try {
      fs.copyFileSync(dbPath, backupPath);
      console.log(`✅ Backup de BD creado: ${path.basename(backupPath)}`);
    } catch (error) {
      console.error('❌ Error creando backup de BD:', error);
    }
  } else {
    console.log('ℹ️  No existe BD previa, se creará durante tests');
  }

  // 4. Crear directorio de archivos de prueba
  const testDataPath = path.join(process.cwd(), 'test-data');
  if (!fs.existsSync(testDataPath)) {
    fs.mkdirSync(testDataPath, { recursive: true });
    console.log('✅ Directorio test-data creado');
  }

  // 5. Generar archivos CSV de prueba CLARO
  await generateClaroTestFiles(testDataPath);

  // 6. Verificar disponibilidad del puerto 8000
  const isPortAvailable = await checkPort(8000);
  if (!isPortAvailable) {
    console.log('ℹ️  Puerto 8000 en uso - se intentará conexión con servidor existente');
  } else {
    console.log('✅ Puerto 8000 disponible');
  }

  // 7. Instalar dependencias de Playwright si es necesario
  try {
    const browser = await chromium.launch({ headless: true });
    await browser.close();
    console.log('✅ Navegadores Playwright verificados');
  } catch (error) {
    console.log('ℹ️  Instalando navegadores Playwright...');
    execSync('npx playwright install chromium', { stdio: 'inherit' });
  }

  console.log('✅ Configuración global completada\n');
}

/**
 * Genera archivos CSV de prueba para CLARO
 */
async function generateClaroTestFiles(testDataPath: string) {
  console.log('📝 Generando archivos de prueba CLARO...');

  // Números objetivo de Boris
  const targetNumbers = [
    '3224274851', '3208611034', '3104277553', 
    '3102715509', '3143534707', '3214161903'
  ];

  // Generar archivo de llamadas salientes
  const salientes = [
    'tipo,originador,receptor,fecha_hora,duracion,celda_inicio_llamada,celda_final_llamada'
  ];

  targetNumbers.forEach((target, i) => {
    // Llamadas donde el target es originador
    salientes.push(`CDR_SALIENTE,${target},310${5000000 + i},12/08/2024 10:${i.toString().padStart(2, '0')}:00,${60 + i * 10},CELL_${i}_START,CELL_${i}_END`);
    
    // Llamadas donde el target es receptor  
    salientes.push(`CDR_SALIENTE,320${4000000 + i},${target},12/08/2024 11:${i.toString().padStart(2, '0')}:00,${120 + i * 5},CELL_${i}_A,CELL_${i}_B`);
  });

  // Caso específico reportado por Boris
  salientes.push('CDR_SALIENTE,3104277553,3224274851,12/08/2024 23:13:20,0,CELL_BORIS_1,CELL_BORIS_2');

  const salientesPath = path.join(testDataPath, 'test_claro_salientes.csv');
  fs.writeFileSync(salientesPath, salientes.join('\n'));

  // Generar archivo de llamadas entrantes
  const entrantes = [
    'tipo,originador,receptor,fecha_hora,duracion,celda_inicio_llamada,celda_final_llamada'
  ];

  targetNumbers.forEach((target, i) => {
    entrantes.push(`CDR_ENTRANTE,315${6000000 + i},${target},13/08/2024 09:${i.toString().padStart(2, '0')}:00,${180 + i * 15},CELL_IN_${i},CELL_IN_${i}_END`);
  });

  const entrantesPath = path.join(testDataPath, 'test_claro_entrantes.csv');
  fs.writeFileSync(entrantesPath, entrantes.join('\n'));

  // Generar archivo de datos por celda
  const datos = [
    'numero,fecha_trafico,tipo_cdr,celda_decimal,lac_decimal'
  ];

  targetNumbers.forEach((target, i) => {
    // Múltiples registros de datos para cada número
    for (let j = 0; j < 3; j++) {
      datos.push(`${target},2024-08-12 ${10 + j}:${i.toString().padStart(2, '0')}:00,GPRS,${12345 + i * 100 + j},${6789 + i * 10}`);
    }
  });

  const datosPath = path.join(testDataPath, 'test_claro_datos.csv');
  fs.writeFileSync(datosPath, datos.join('\n'));

  console.log(`✅ Archivos de prueba CLARO generados:`);
  console.log(`   - ${path.basename(salientesPath)} (${salientes.length - 1} registros)`);
  console.log(`   - ${path.basename(entrantesPath)} (${entrantes.length - 1} registros)`);
  console.log(`   - ${path.basename(datosPath)} (${datos.length - 1} registros)`);
}

/**
 * Verifica si un puerto está disponible
 */
async function checkPort(port: number): Promise<boolean> {
  try {
    const { createServer } = await import('net');
    return new Promise((resolve) => {
      const server = createServer();
      server.listen(port, () => {
        server.close(() => resolve(true));
      });
      server.on('error', () => resolve(false));
    });
  } catch {
    return false;
  }
}

export default globalSetup;