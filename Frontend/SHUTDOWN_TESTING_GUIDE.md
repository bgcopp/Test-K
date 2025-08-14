# Guía de Testing para Shutdown Coordination Frontend

## Descripción General

Esta guía define las estrategias de testing para validar la coordinación correcta del shutdown entre el frontend React y el backend Python Eel de la aplicación KRONOS.

## Escenarios de Testing

### 1. Shutdown Normal por Cierre de Ventana

**Objetivo**: Verificar que el cierre normal de la ventana de Eel activa el sistema de shutdown correctamente.

**Pasos de Testing**:
```bash
# 1. Ejecutar aplicación completa
cd Backend
python main.py

# 2. En la aplicación:
# - Navegar por diferentes páginas
# - Realizar algunas operaciones (crear usuario, misión, etc.)
# - Cerrar la ventana normalmente

# 3. Verificar en logs:
# - ✅ "=== INICIANDO SHUTDOWN DE APLICACIÓN ===" aparece
# - ✅ Frontend cleanup ejecutado correctamente
# - ✅ Sin errores de JavaScript en console
# - ✅ Backend cierra sin errores
```

**Resultados Esperados**:
- Overlay de shutdown se muestra brevemente
- Requests activas se cancelan correctamente
- Local storage se limpia según configuración
- No hay errores en console del navegador
- Backend termina limpiamente

### 2. Shutdown por Pérdida de Conexión

**Objetivo**: Validar el comportamiento cuando se pierde conexión con el backend.

**Pasos de Testing**:
```bash
# 1. Iniciar aplicación
cd Backend
python main.py

# 2. Forzar desconexión del backend:
# Método A: Cerrar proceso Python manualmente (Ctrl+C)
# Método B: Suspender proceso en Windows Task Manager

# 3. En frontend, observar:
# - Indicador de conexión cambia a "Desconectado"
# - Requests fallan gracefulmente
# - No se muestran alerts de error durante shutdown
```

**Resultados Esperados**:
- Indicador de conexión se actualiza a estado desconectado
- Hook useEelConnection detecta pérdida de conexión
- Requests pendientes se cancelan sin generar errores

### 3. Shutdown Durante Operaciones Largas

**Objetivo**: Verificar cancelación correcta de operaciones que toman tiempo.

**Pasos de Testing**:
```bash
# 1. Iniciar aplicación
# 2. Subir archivo grande a una misión
# 3. Durante la subida, cerrar ventana
# 4. Verificar que:
#    - Upload se cancela correctamente
#    - No hay errores de recursos colgados
```

### 4. Testing de Request Cancellation

**Objetivo**: Validar que AbortController funciona correctamente.

**Código de Testing**:
```typescript
// Test manual en DevTools console:
import { getRequestManager } from './services/api';

// Simular múltiples requests
for (let i = 0; i < 5; i++) {
  window.eel.get_users()()
    .then(() => console.log(`Request ${i} completada`))
    .catch(err => console.log(`Request ${i} cancelada:`, err.message));
}

// Cancelar todas las requests
getRequestManager().initiateShutdown();
```

### 5. Testing de Cleanup Hooks

**Objetivo**: Verificar que los hooks de cleanup funcionan correctamente.

**Código de Testing**:
```typescript
// En DevTools console:
import { useCleanup } from './hooks/useCleanup';

// Simular recursos que necesitan cleanup
const { registerTimeout, registerInterval, getCleanupStats } = useCleanup();

// Crear algunos resources
registerTimeout(() => console.log('Timer ejecutado'), 5000);
registerInterval(() => console.log('Interval ejecutado'), 1000);

// Verificar estadísticas
console.log(getCleanupStats());

// Forzar cleanup
executeCleanup();
```

## Testing Automatizado

### Configuración de Tests

```bash
# Instalar dependencias de testing (si no están)
cd Frontend
npm install --save-dev @testing-library/react @testing-library/jest-dom vitest jsdom
```

### Tests Unitarios

```typescript
// tests/hooks/useEelConnection.test.ts
import { renderHook, act } from '@testing-library/react';
import { useEelConnection } from '../../hooks/useEelConnection';

describe('useEelConnection', () => {
  test('detecta desconexión cuando Eel no está disponible', async () => {
    // Mock window.eel como undefined
    Object.defineProperty(window, 'eel', {
      value: undefined,
      writable: true
    });

    const { result } = renderHook(() => useEelConnection());
    
    await act(async () => {
      const isConnected = await result.current.checkConnection();
      expect(isConnected).toBe(false);
      expect(result.current.isConnected).toBe(false);
    });
  });

  test('marca shutdown correctamente', () => {
    const { result } = renderHook(() => useEelConnection());
    
    act(() => {
      result.current.markShuttingDown();
    });

    expect(result.current.isShuttingDown).toBe(true);
    expect(result.current.isConnected).toBe(false);
  });
});
```

```typescript
// tests/services/api.test.ts  
import { getRequestManager } from '../../services/api';

describe('RequestCancellationManager', () => {
  test('cancela todas las requests durante shutdown', () => {
    const manager = getRequestManager();
    
    // Crear algunos controllers
    const controller1 = manager.createController('test1');
    const controller2 = manager.createController('test2');
    
    expect(manager.getStats().activeCount).toBe(2);
    
    // Iniciar shutdown
    manager.initiateShutdown();
    
    expect(controller1.signal.aborted).toBe(true);
    expect(controller2.signal.aborted).toBe(true);
    expect(manager.getStats().activeCount).toBe(0);
    expect(manager.getStats().isShuttingDown).toBe(true);
  });
});
```

### Tests de Integración

```typescript
// tests/integration/shutdown.test.ts
import { render, screen, waitFor } from '@testing-library/react';
import App from '../../App_enhanced';

describe('Shutdown Integration', () => {
  test('muestra overlay de shutdown cuando isShuttingDown es true', async () => {
    // Mock del hook useEelConnection
    jest.mock('../../hooks/useEelConnection', () => ({
      useEelConnection: () => ({
        isConnected: false,
        isShuttingDown: true,
        markShuttingDown: jest.fn()
      })
    }));

    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('Cerrando KRONOS...')).toBeInTheDocument();
    });
  });
});
```

## Testing Manual - Checklist

### Pre-Shutdown Testing
- [ ] Aplicación inicia correctamente
- [ ] Indicador de conexión muestra "Conectado"
- [ ] Todas las funcionalidades básicas funcionan
- [ ] Datos se cargan sin errores

### Durante Shutdown Testing
- [ ] Overlay de shutdown aparece cuando corresponde
- [ ] Indicador de conexión se actualiza correctamente
- [ ] No aparecen alerts de error durante cierre
- [ ] Console del navegador no muestra errores críticos

### Post-Shutdown Testing
- [ ] Backend termina completamente (proceso no queda colgado)
- [ ] No hay archivos de log con errores críticos
- [ ] LocalStorage limpiado según configuración
- [ ] No hay handles de archivos abiertos

## Herramientas de Debugging

### 1. Console Debugging
```typescript
// En DevTools console durante desarrollo:

// Ver estado de conexión
window.eelConnectionState = useEelConnection();

// Ver estadísticas de requests
console.log('Request Stats:', getRequestManager().getStats());

// Ver cleanup handlers registrados
console.log('Cleanup Stats:', useCleanup().getCleanupStats());
```

### 2. Logging Personalizado
```typescript
// Activar logging detallado
localStorage.setItem('KRONOS_DEBUG_SHUTDOWN', 'true');

// Los hooks verificarán esta flag y mostrarán logs adicionales
```

### 3. Network Tab Monitoring
- Monitorear tab Network en DevTools
- Verificar que requests se cancelen correctamente
- No debe haber requests pendientes after shutdown

## Casos Edge

### 1. Múltiples Cierres Rápidos
- Cerrar y reabrir aplicación rápidamente
- Verificar que no hay recursos colgados

### 2. Cierre Durante Navegación
- Cambiar páginas mientras requests están pendientes
- Cerrar durante transición de página

### 3. Shutdown con Datos No Guardados
- Modificar datos sin guardar
- Verificar comportamiento al cerrar (confirmación/pérdida de datos)

## Métricas de Éxito

### Performance
- Tiempo de shutdown < 3 segundos
- Cleanup completo < 1 segundo
- Sin memory leaks después del cierre

### Reliability
- 0% errores críticos durante shutdown normal
- 100% cancelación exitosa de requests pendientes
- 100% limpieza de recursos registrados

### User Experience
- Feedback visual claro durante shutdown
- No diálogos confusos o error messages
- Transición smooth sin colgadas

## Automation Scripts

### Script de Testing Completo
```bash
#!/bin/bash
# test_shutdown.sh

echo "🧪 Iniciando tests de shutdown..."

# 1. Unit tests
npm test -- --grep="shutdown|connection|cleanup"

# 2. Integration tests  
npm test -- tests/integration/

# 3. Manual test helper
echo "🔧 Ejecutando aplicación para testing manual..."
cd Backend
python main.py &
BACKEND_PID=$!

echo "📱 Aplicación iniciada. Presiona cualquier tecla después de testing manual..."
read -n 1

echo "🛑 Cerrando backend..."
kill $BACKEND_PID

echo "✅ Testing completado"
```

## Troubleshooting

### Problemas Comunes

1. **Requests no se cancelan**
   - Verificar que AbortController está siendo usado
   - Comprobar que window.eel existe antes del shutdown

2. **Shutdown colgado**
   - Verificar timeout de emergency exit en backend
   - Comprobar cleanup hooks no tienen loops infinitos

3. **Errores en console**
   - Filtrar errores de shutdown vs errores reales
   - Verificar que componentes manejan estado isShuttingDown

4. **UI no responde durante shutdown**
   - Verificar que overlay se muestra correctamente
   - Comprobar que cleanup no bloquea thread principal

Este sistema de testing garantiza que la coordinación de shutdown entre frontend y backend funcione de manera robusta y proporcione una experiencia de usuario fluida durante el cierre de la aplicación KRONOS.