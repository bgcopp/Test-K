/**
 * Global Teardown para testing de PhoneCorrelationViewer
 * Limpia procesos y recursos después del testing
 */

import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

async function globalTeardown() {
  console.log('🧹 Iniciando teardown global...');
  
  try {
    // Matar procesos de Python (backend KRONOS)
    if (process.platform === 'win32') {
      await execAsync('taskkill /f /im python.exe', { timeout: 5000 }).catch(() => {
        console.log('⚠️ No hay procesos Python para terminar');
      });
    } else {
      await execAsync('pkill -f "python main.py"', { timeout: 5000 }).catch(() => {
        console.log('⚠️ No hay procesos Python para terminar');
      });
    }
    
    console.log('✅ Teardown completado');
    
  } catch (error) {
    console.error('⚠️ Error en teardown (no crítico):', error);
  }
}

export default globalTeardown;