# Guía de Test del Algoritmo de Correlación KRONOS

## Resumen Ejecutivo

Esta guía describe el test específico de Playwright creado para validar el algoritmo de correlación de KRONOS con los números objetivo identificados por Boris. El test se enfoca en el período 2024-08-12 donde se confirmó la presencia de datos reales de operadores.

## Datos Críticos Identificados

### Período de Validación
- **Fecha inicio**: 2024-08-12 20:00:00
- **Fecha fin**: 2024-08-13 02:00:00
- **Razón**: Período confirmado con datos reales de operadores en la BD

### Números Objetivo Críticos
- **3104277553** → **3224274851** (Conexión confirmada en 2024-08-12 23:13:20)
- **3208611034**, **3102715509**, **3143534707**, **3214161903**

### Celdas Específicas
- **3104277553** → Celda **12345**
- **3224274851** → Celda **67890**

## Archivos del Test

### 1. Test Principal
**Archivo**: `tests/correlation-algorithm-validation.spec.ts`

**Propósito**: Test principal que valida todo el flujo del algoritmo de correlación.

**Funcionalidades validadas**:
- Navegación a la sección de análisis
- Configuración de parámetros de correlación
- Ejecución del algoritmo
- Validación de números objetivo específicos
- Verificación de conexiones críticas
- Filtrado de resultados
- Exportación de datos
- Captura de evidencia

### 2. Helpers Reutilizables
**Archivo**: `tests/helpers/test-helpers.ts`

**Propósito**: Funciones utilitarias para testing de KRONOS.

**Funciones principales**:
- `navigateToApplication()`: Navegación inicial
- `loginToKronos()`: Autenticación
- `createTestMission()`: Creación de misión de test
- `uploadScanHunterFile()`: Carga de datos celulares
- `uploadOperatorFile()`: Carga de datos de operadores
- `executeCorrelationAnalysis()`: Ejecución del análisis
- `validateNumberInResults()`: Validación de números específicos
- `captureEvidence()`: Captura de evidencia

### 3. Script de Ejecución
**Archivo**: `run-correlation-algorithm-test.bat`

**Propósito**: Script automatizado para ejecutar el test completo.

**Funcionalidades**:
- Verificación de prerequisitos
- Inicio del backend KRONOS
- Ejecución del test Playwright
- Captura de resultados
- Limpieza y reporte final

### 4. Configuración Específica
**Archivo**: `playwright-correlation.config.ts`

**Propósito**: Configuración optimizada para tests de correlación.

**Características**:
- Timeouts extendidos para análisis largos
- Configuración de evidencia
- Setup específico para KRONOS
- Variables de entorno del test

## Ejecución del Test

### Método Recomendado (Script Automatizado)
```bash
# Desde el directorio raíz de KRONOS
run-correlation-algorithm-test.bat
```

### Método Manual
```bash
# 1. Iniciar backend
cd Backend
python main.py

# 2. En otra terminal, ejecutar test
npx playwright test tests/correlation-algorithm-validation.spec.ts --headed --timeout=300000
```

### Método con Configuración Específica
```bash
npx playwright test --config=playwright-correlation.config.ts
```

## Validaciones Específicas del Test

### 1. Navegación y Setup
- ✅ Aplicación KRONOS carga correctamente
- ✅ Login funciona
- ✅ Misión de test se crea exitosamente
- ✅ Datos SCANHUNTER se cargan
- ✅ Navegación a análisis de correlación

### 2. Configuración del Análisis
- ✅ Selección de modo "Análisis de Correlación"
- ✅ Configuración de fechas del período crítico
- ✅ Configuración de mínimo de coincidencias
- ✅ Botón "Ejecutar Análisis" habilitado

### 3. Ejecución del Algoritmo
- ✅ Análisis se inicia correctamente
- ✅ Estado "Analizando..." se muestra
- ✅ Análisis completa sin errores
- ✅ Dashboard de resultados aparece

### 4. Validación de Números Objetivo
- 🎯 **Número crítico 3104277553** presente en resultados
- 🎯 **Número conectado 3224274851** presente en resultados
- 🎯 **Celda 12345** asociada al número crítico
- 🎯 **Conexión 3104277553 → 3224274851** detectada
- 🎯 Otros números objetivo validados

### 5. Funcionalidades Adicionales
- ✅ Filtrado por número específico funciona
- ✅ Botones de exportación disponibles
- ✅ Paginación funciona correctamente
- ✅ Estadísticas se muestran correctamente

## Evidencia Capturada

### Screenshots Automáticos
El test captura evidencia en `Backend/test_evidence_screenshots/`:

- `correlation_analysis_initial_*.png`: Pantalla inicial del análisis
- `correlation_config_*.png`: Configuración del análisis
- `correlation_results_*.png`: Resultados del análisis
- `target_numbers_validation_*.png`: Validación de números objetivo
- `filter_validation_*.png`: Prueba de filtrado
- `export_options_*.png`: Opciones de exportación
- `final_validation_results_*.png`: Resultados finales

### Reportes de Test
- `correlation-test-results.json`: Resultados en formato JSON
- `correlation-test-results.xml`: Resultados en formato JUnit
- `playwright-report/`: Reporte HTML detallado

## Interpretación de Resultados

### Resultado Exitoso
```
✅ TEST COMPLETADO EXITOSAMENTE

📊 Resumen de Validación:
   ✓ Navegación a análisis de correlación
   ✓ Configuración de parámetros de correlación
   ✓ Ejecución del algoritmo
   ✓ Validación de números objetivo específicos
   ✓ Verificación de conexiones 3104277553 -> 3224274851
   ✓ Captura de evidencia y screenshots
```

### Resultado con Problemas
```
❌ TEST FALLÓ

🔍 Posibles causas:
   • Backend no está ejecutándose correctamente
   • Base de datos no contiene los números objetivo esperados
   • Período de fechas configurado no tiene datos
   • Interfaz de usuario cambió (selectores desactualizados)
```

## Troubleshooting

### Problema: Backend no inicia
**Solución**:
```bash
cd Backend
python --version  # Verificar Python
pip install -r requirements.txt  # Instalar dependencias
python main.py  # Iniciar manualmente
```

### Problema: Test no encuentra números objetivo
**Verificación**:
1. Revisar BD tiene datos del período: `Backend/kronos.db`
2. Verificar tabla `operator_cellular_data` tiene registros de 2024-08-12
3. Ejecutar consulta manual:
```sql
SELECT * FROM operator_cellular_data 
WHERE timestamp LIKE '2024-08-12%' 
AND phone_number IN ('3104277553', '3224274851');
```

### Problema: Selectores desactualizados
**Solución**:
1. Ejecutar test en modo debug: `--debug`
2. Revisar elementos de la interfaz cambiaron
3. Actualizar selectores en `correlation-algorithm-validation.spec.ts`

### Problema: Timeout del análisis
**Configuración**:
- Aumentar timeout en `playwright-correlation.config.ts`
- Verificar que la BD no esté corrupta
- Optimizar consultas de correlación

## Mantenimiento del Test

### Actualización de Números Objetivo
Para cambiar los números objetivo a validar:

1. Editar `CORRELATION_TEST_CONFIG` en el test principal
2. Actualizar variables de entorno en `playwright-correlation.config.ts`
3. Modificar documentación si es necesario

### Actualización de Período de Tiempo
Para cambiar el período de análisis:

1. Modificar `startDate` y `endDate` en `CORRELATION_TEST_CONFIG`
2. Asegurar que la BD tiene datos para el nuevo período
3. Ejecutar test de validación

### Actualización de Selectores
Si la interfaz de KRONOS cambia:

1. Revisar elementos afectados con `npx playwright codegen`
2. Actualizar selectores en test principal y helpers
3. Probar en modo headed para verificar

## Integración Continua

### Para CI/CD
```yaml
- name: Run Correlation Algorithm Test
  run: |
    cd Backend && python main.py &
    sleep 10
    npx playwright test --config=playwright-correlation.config.ts --reporter=json
```

### Criterios de Éxito
- ✅ Test completa sin errores de timeout
- ✅ Al menos 1 número objetivo encontrado en resultados
- ✅ Número crítico 3104277553 validado
- ✅ Evidencia capturada correctamente

## Contacto y Soporte

Para problemas con este test específico:

1. **Revisar logs**: `Backend/kronos_backend.log`
2. **Revisar evidencia**: `Backend/test_evidence_screenshots/`
3. **Ejecutar en modo debug**: `npx playwright test --debug`
4. **Consultar documentación**: Este archivo

---

**Nota**: Este test fue diseñado específicamente para validar el algoritmo de correlación con los datos reales identificados por Boris en el período 2024-08-12. Los números objetivo y configuraciones están basados en análisis previos de la base de datos de KRONOS.