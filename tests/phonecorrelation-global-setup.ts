/**
 * Global Setup para testing de PhoneCorrelationViewer
 * Inicia aplicación KRONOS con datos reales para testing
 */

import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execAsync = promisify(exec);

async function globalSetup() {
  console.log('🚀 Iniciando setup global para testing PhoneCorrelationViewer...');
  
  try {
    // 1. Compilar frontend para producción
    console.log('📦 Compilando frontend...');
    const frontendPath = path.join(__dirname, '..', 'Frontend');
    
    try {
      await execAsync('npm run build', { 
        cwd: frontendPath,
        timeout: 60000 
      });
      console.log('✅ Frontend compilado exitosamente');
    } catch (buildError) {
      console.log('⚠️ Error en build, continuando con archivos existentes:', buildError);
    }
    
    // 2. Iniciar backend de KRONOS
    console.log('🔧 Iniciando backend KRONOS...');
    const backendPath = path.join(__dirname, '..', 'Backend');
    
    // Ejecutar en background
    const backendProcess = exec('python main.py', { 
      cwd: backendPath 
    });
    
    backendProcess.stdout?.on('data', (data) => {
      if (data.includes('Running on')) {
        console.log('✅ Backend KRONOS iniciado:', data.trim());
      }
    });
    
    backendProcess.stderr?.on('data', (data) => {
      console.error('⚠️ Backend warning:', data.trim());
    });
    
    // Esperar a que el backend esté listo
    let retries = 30;
    while (retries > 0) {
      try {
        await new Promise(resolve => setTimeout(resolve, 1000));
        // Verificar que el backend responde
        const response = await fetch('http://localhost:8000/');
        if (response.ok) {
          console.log('✅ Backend respondiendo correctamente');
          break;
        }
      } catch (e) {
        retries--;
        if (retries === 0) {
          throw new Error('Backend no responde después de 30 intentos');
        }
      }
    }
    
    // 3. Validar que hay datos en la base de datos
    console.log('🔍 Validando datos de testing en BD...');
    // Se validará dentro del test específico
    
    console.log('🎯 Setup completado - Listo para testing PhoneCorrelationViewer');
    
  } catch (error) {
    console.error('❌ Error en setup global:', error);
    throw error;
  }
}

export default globalSetup;