# PLAN DE TESTING PLAYWRIGHT - DIAGNÓSTICO DETALLE DE MISIÓN

## SITUACIÓN CRÍTICA
**Problema**: La aplicación KRONOS queda en blanco al abrir cualquier detalle de misión
**Intentos previos**: Múltiples correcciones sin éxito
**Necesidad**: Diagnóstico empírico con evidencia real usando Playwright

## METODOLOGÍA DE TESTING

### FASE 1: PREPARACIÓN DEL ENTORNO
1. **Iniciar aplicación KRONOS**
   ```bash
   cd Backend
   python main.py
   ```
   - Verificar que el servidor Eel se inicia correctamente
   - Confirmar que el frontend se compila y sirve
   - Validar que no hay errores de inicio

2. **Configurar Playwright**
   - Navegar a la URL de la aplicación (típicamente http://localhost:8000)
   - Configurar captura de screenshots
   - Habilitar logging de consola y network

### FASE 2: TESTING DE FLUJO BASE
1. **Verificar carga inicial**
   - Capturar screenshot de página inicial
   - Verificar que la aplicación carga correctamente
   - Revisar errores en consola

2. **Navegar a lista de misiones**
   - Localizar y hacer clic en sección de misiones
   - Verificar que la lista se carga
   - Capturar estado de la lista

### FASE 3: REPRODUCIR EL PROBLEMA
1. **Identificar misión de prueba**
   - Seleccionar una misión específica de la lista
   - Documentar los datos de la misión seleccionada

2. **Ejecutar acción problemática**
   - Hacer clic en "Ver detalles" o similar
   - Capturar el momento exacto del clic
   - Documentar qué ocurre inmediatamente después

3. **Capturar estado de falla**
   - Screenshot del estado en blanco
   - Logs de consola al momento de la falla
   - Network requests durante la operación

### FASE 4: DIAGNÓSTICO PROFUNDO
1. **Análisis de Frontend**
   - Verificar si React sigue renderizando
   - Revisar el DOM actual vs esperado
   - Identificar componentes que fallan

2. **Análisis de Backend**
   - Capturar logs del servidor Python
   - Verificar qué funciones Eel se llaman
   - Identificar errores o excepciones

3. **Análisis de Comunicación**
   - Revisar requests HTTP/WebSocket
   - Verificar respuestas del servidor
   - Identificar timeouts o fallos

## PUNTOS DE CAPTURA ESPECÍFICOS

### Screenshots Requeridos
1. Estado inicial de la aplicación
2. Lista de misiones cargada
3. Momento del clic en "Ver detalles"
4. Estado en blanco resultante
5. Inspector de elementos del estado en blanco

### Logs Requeridos
1. Logs de inicio del backend
2. Logs durante navegación a misiones
3. Logs durante clic en detalle
4. Errores de consola JavaScript
5. Network activity completa

### Datos a Capturar
1. URL actual cuando se produce el fallo
2. Estado del localStorage/sessionStorage
3. Variables de estado de React (si están disponibles)
4. Respuestas de API específicas

## HIPÓTESIS A VALIDAR

### Hipótesis 1: Error de JavaScript no manejado
- **Test**: Revisar consola por errores JavaScript
- **Evidencia**: Stacktrace específico del error

### Hipótesis 2: Falla en comunicación Eel
- **Test**: Monitorear requests WebSocket/HTTP
- **Evidencia**: Requests fallidos o timeouts

### Hipótesis 3: Error en backend Python
- **Test**: Revisar logs del servidor
- **Evidencia**: Excepciones o errores en logs

### Hipótesis 4: Problema de routing de React
- **Test**: Verificar cambios de URL y routing
- **Evidencia**: URL incorrecta o componente no montado

### Hipótesis 5: Problema de datos/estado
- **Test**: Verificar estructura de datos recibidos
- **Evidencia**: Datos corruptos o faltantes

## EJECUCIÓN DEL PLAN

### Paso 1: Iniciar Aplicación
**Comando**: `cd Backend && python main.py`
**Verificar**: 
- Puerto donde se ejecuta (típicamente 8000)
- Mensajes de inicio exitoso
- Compilación de frontend

### Paso 2: Ejecutar Testing Playwright
```javascript
// Script de testing a ejecutar
async function testMissionDetail() {
  // 1. Navegar a aplicación
  await page.goto('http://localhost:PUERTO');
  
  // 2. Capturar estado inicial
  await page.screenshot({ path: 'estado_inicial.png' });
  
  // 3. Navegar a misiones
  await page.click('[data-testid="missions-link"]'); // O selector real
  
  // 4. Hacer clic en detalle
  await page.click('[data-testid="mission-detail-button"]'); // O selector real
  
  // 5. Capturar estado final
  await page.screenshot({ path: 'estado_final.png' });
  
  // 6. Capturar logs
  const consoleLogs = await page.evaluate(() => console.log);
}
```

### Paso 3: Documentar Resultados
- Compilar todos los screenshots
- Organizar logs por timestamp
- Crear línea de tiempo del problema
- Identificar causa raíz exacta

## ENTREGABLES ESPERADOS

### 1. Documento de Evidencia
- Screenshots cronológicos del problema
- Logs completos con timestamps
- Análisis de causa raíz específica

### 2. Plan de Corrección
- Identificación exacta del problema
- Estrategia de corrección específica
- Steps de implementación detallados

### 3. Testing de Validación
- Plan para verificar que la corrección funciona
- Tests automatizados para prevenir regresión

## PRÓXIMOS PASOS

1. **INMEDIATO**: Iniciar aplicación KRONOS
2. **EJECUTAR**: Testing Playwright según este plan
3. **ANALIZAR**: Evidencia recopilada
4. **CORREGIR**: Implementar fix específico basado en evidencia
5. **VALIDAR**: Confirmar que el problema está resuelto

---

**OBJETIVO**: Obtener evidencia empírica concreta del problema real, no más especulaciones o correcciones teóricas.

**RESULTADO ESPERADO**: Identificación exacta de por qué la aplicación queda en blanco y plan específico para corregirlo.