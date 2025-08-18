# Certificación de Números Objetivo - KRONOS

## Descripción

Esta suite de tests certifica que los números objetivo de Boris aparezcan correctamente en los resultados de correlación de KRONOS después de las correcciones implementadas en el algoritmo.

## Números Objetivo

Los siguientes números deben aparecer en los resultados de correlación:

- **3224274851** (2 coincidencias esperadas)
- **3208611034** (2 coincidencias esperadas)  
- **3143534707** (3 coincidencias esperadas)
- **3102715509** (1 coincidencia esperada)
- **3214161903** (1 coincidencia esperada)

## Configuración de Prueba

- **Misión**: mission_MPFRBNsb
- **Período**: 2021-05-20 10:00:00 a 2021-05-20 15:00:00
- **Mínimo coincidencias**: 1

## Archivos de Tests

### Tests Principales

1. **target-numbers-certification.spec.ts**
   - Test completo de certificación
   - Validación de todos los números objetivo
   - Captura de evidencias
   - Generación de reporte de certificación

2. **detailed-number-validation.spec.ts**
   - Validación individual por número
   - Tests granulares para diagnóstico
   - Verificación de formato (sin prefijo 57)

3. **regression-validation.spec.ts**
   - Tests de regresión
   - Validación de consistencia
   - Tests de estabilidad del algoritmo

4. **diagnostic-test.spec.ts**
   - Test de diagnóstico completo
   - Máxima captura de información para debugging
   - Análisis detallado del flujo

### Archivos de Soporte

- **global-setup.ts** - Configuración inicial
- **global-teardown.ts** - Limpieza final
- **debug-helpers.ts** - Utilidades de debugging

## Ejecución

### Ejecución Completa

```bash
# Ejecutar certificación completa
run-target-numbers-certification.bat

# O manualmente
npx playwright test --config=playwright-target-numbers.config.ts
```

### Ejecución Rápida

```bash
# Solo el test crítico principal
quick-target-validation.bat

# O manualmente
npx playwright test tests/target-numbers-certification/target-numbers-certification.spec.ts --grep="Test de Números Objetivo - CRÍTICO"
```

### Tests Individuales

```bash
# Test de diagnóstico
npx playwright test tests/target-numbers-certification/diagnostic-test.spec.ts

# Validación detallada
npx playwright test tests/target-numbers-certification/detailed-number-validation.spec.ts

# Tests de regresión
npx playwright test tests/target-numbers-certification/regression-validation.spec.ts
```

## Criterios de Éxito

### ✅ Tests PASAN cuando:

1. **Todos los números objetivo están presentes** en los resultados
2. **Formato correcto**: números sin prefijo 57
3. **Resultados consistentes** en múltiples ejecuciones
4. **Análisis completa** en menos de 5 minutos
5. **Interfaz responde** correctamente

### ❌ Tests FALLAN cuando:

1. **Cualquier número objetivo falta** en los resultados
2. **Números con prefijo 57** aparecen en resultados
3. **Pantalla en blanco** después del análisis
4. **Errores de navegación** o configuración
5. **Timeout** en análisis de correlación

## Estructura de Resultados

```
test-results/
├── target-numbers-certification/     # Reporte HTML principal
├── evidence/                         # Screenshots paso a paso
├── certification-report-[timestamp].json  # Reporte de certificación
└── target-numbers-certification-results.json  # Resultados JSON
```

## Evidencias Capturadas

Cada test captura screenshots automáticamente:

- `01_inicio_aplicacion.png` - Pantalla inicial
- `02_pagina_misiones.png` - Lista de misiones
- `03_detalle_mision.png` - Detalles de misión
- `04_configuracion_correlacion.png` - Configuración
- `05_resultados_correlacion.png` - Resultados
- `06-11_[pasos_validacion].png` - Proceso de validación
- `evidence_[numero]_[timestamp].png` - Validaciones específicas

## Debugging

Si los tests fallan:

1. **Revisar screenshots** en `test-results/evidence/`
2. **Verificar reporte JSON** para detalles específicos
3. **Ejecutar test de diagnóstico** para análisis completo:
   ```bash
   npx playwright test tests/target-numbers-certification/diagnostic-test.spec.ts
   ```
4. **Verificar logs** de la aplicación KRONOS
5. **Contactar equipo de desarrollo** con evidencias

## Configuración Técnica

- **Navegador**: Chromium
- **Modo**: Visual (headless: false) para debugging
- **Timeout**: 5 minutos para análisis completo
- **Viewport**: 1920x1080
- **Puerto**: localhost:8000
- **Paralelismo**: Deshabilitado (tests secuenciales)

## Mantenimiento

Para actualizar estos tests:

1. **Modificar números objetivo** en las constantes
2. **Ajustar configuración** de fechas/períodos
3. **Actualizar selectores** si cambia la interfaz
4. **Revisar timeouts** según rendimiento

## Notas Importantes

- Los tests requieren que la aplicación KRONOS esté ejecutándose en localhost:8000
- La base de datos debe contener la misión `mission_MPFRBNsb`
- Los tests NO modifican datos, solo leen resultados
- Cada ejecución genera evidencias únicas con timestamp