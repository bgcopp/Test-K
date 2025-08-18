# 🧪 KRONOS CLARO E2E Testing Suite

Suite completa de tests End-to-End para validar el proceso de carga de archivos CLARO en la aplicación KRONOS.

## 🚀 Ejecución Rápida

```batch
# Ejecutar suite completa (recomendado)
run-claro-tests.bat
```

## 📋 Qué hace esta suite

Esta suite automatiza y valida completamente:

1. **Carga de archivos CLARO** a través de la interfaz de usuario
2. **Validación de números objetivo** en la base de datos
3. **Análisis de correlación** post-carga
4. **Verificación del caso específico** 3104277553 → 3224274851

## 🎯 Números Objetivo Validados

- **3224274851** ⭐ (Crítico)
- **3208611034**
- **3104277553** ⭐ (Crítico)
- **3102715509**
- **3143534707**
- **3214161903**

## 📦 Prerrequisitos

- **Node.js** 18+
- **Python** 3.8+
- **KRONOS** Backend corriendo en puerto 8000

## 🛠️ Instalación

```bash
# 1. Instalar dependencias NPM
npm install

# 2. Instalar navegadores Playwright
npx playwright install chromium
```

## 🧪 Ejecución de Tests

### Opción 1: Suite Completa (Recomendada)

```batch
run-claro-tests.bat
```

### Opción 2: Tests Individuales

```bash
# Test de carga de archivos
npm run test:claro

# Test de validación de números
npm run test:claro-validation

# Test de análisis de correlación
npm run test:claro-correlation
```

### Opción 3: Ejecución Manual

```bash
# Ejecutar todos los tests
npm test

# Ejecutar con interfaz visible (debugging)
npm run test:headed

# Ejecutar con debugging paso a paso
npm run test:debug
```

## 📊 Validación Rápida

Después de ejecutar los tests, valida los resultados:

```bash
# Validación básica
cd tests
python run-quick-validation.py

# Validación detallada con estadísticas
python run-quick-validation.py --detailed

# Generar reporte JSON
python run-quick-validation.py --json resultado.json
```

## 📈 Resultados Esperados

### ✅ Éxito Total

```
====================================
   KRONOS CLARO E2E TESTING SUITE
====================================

[OK] Carga de archivos CLARO
[OK] Validacion de numeros objetivo  
[OK] Analisis de correlacion
[OK] Validacion de base de datos

[EXITO TOTAL] Todos los tests pasaron correctamente

Los números objetivo 3104277553 y 3224274851 han sido validados
en la base de datos. El proceso de carga CLARO funciona al 100%.
```

## 📁 Archivos Generados

Después de la ejecución encontrarás:

- **`test-results/html-report/index.html`** - Reporte interactivo
- **`test-results/results.json`** - Resultados detallados
- **`test-results/artifacts/`** - Screenshots y videos
- **Reportes de validación JSON** - Métricas específicas

## 📖 Ver Reportes

```bash
# Abrir reporte interactivo
npm run report

# Ver resultados en JSON
cat test-results/results.json

# Ver screenshots
ls test-results/artifacts/
```

## 🔧 Comandos Útiles

```bash
# Solo instalar navegadores
npx playwright install

# Ver versión de Playwright
npx playwright --version

# Generar código de test (grabador)
npx playwright codegen localhost:8000

# Limpiar resultados anteriores
rm -rf test-results/
```

## 🚨 Solución de Problemas

### Puerto 8000 ocupado
```bash
# Cerrar aplicación KRONOS y re-ejecutar
taskkill /f /im python.exe
run-claro-tests.bat
```

### Python no encontrado
```bash
# Verificar Python en PATH
python --version

# Si falla, instalar Python 3.8+ y agregar al PATH
```

### Tests fallan por timeout
- Verificar que KRONOS esté corriendo
- Cerrar otras aplicaciones pesadas
- Re-ejecutar con `run-claro-tests.bat`

### Base de datos vacía
```bash
# Validar manualmente
cd Backend
python verify_target_numbers.py
```

## 📋 Estructura de Tests

```
📁 tests/
├── 🧪 claro-upload.spec.ts      # Tests E2E carga UI
├── 🧪 claro-validation.spec.ts  # Validación números objetivo  
├── 🧪 claro-correlation.spec.ts # Tests análisis correlación
├── 🐍 database-validator.py     # Validador BD especializado
└── 🐍 run-quick-validation.py   # Validación rápida
```

## 🎯 Casos de Test Clave

1. **Carga archivo llamadas salientes** - Valida upload CSV salientes
2. **Carga archivo llamadas entrantes** - Valida upload CSV entrantes  
3. **Carga archivo datos por celda** - Valida upload CSV datos celulares
4. **Verificación números críticos** - 3104277553 y 3224274851 en BD
5. **Caso comunicación Boris** - 3104277553 → 3224274851
6. **Análisis de correlación** - Funcionalidad post-carga

## 🔍 Debugging

```bash
# Ejecutar con navegador visible
npx playwright test --headed

# Ejecutar modo debug paso a paso
npx playwright test --debug

# Ejecutar test específico
npx playwright test tests/claro-upload.spec.ts

# Ver logs detallados
npx playwright test --reporter=line
```

## 📞 Soporte

Si encuentras problemas:

1. **Revisa prerrequisitos** - Node.js 18+, Python 3.8+
2. **Verifica KRONOS** - Debe estar corriendo en puerto 8000
3. **Consulta logs** - `test-results/` contiene información detallada
4. **Re-ejecuta suite** - `run-claro-tests.bat` es más robusto

## 📊 Métricas de Validación

La suite verifica:

- ✅ **Cobertura números objetivo**: ≥ 90%
- ✅ **Números críticos presentes**: 100%
- ✅ **Tiempo de carga**: < 2 minutos por archivo
- ✅ **Integridad de datos**: > 95% campos válidos
- ✅ **Evidencia visual**: Screenshots de todos los pasos

---

**¿Necesitas ayuda?** Revisa el reporte detallado en `CLARO_E2E_TESTING_SUITE_IMPLEMENTATION_REPORT.md`