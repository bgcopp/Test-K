# Guía Completa de Pruebas E2E CLARO - KRONOS

## 🎯 Objetivo

Esta suite de pruebas valida completamente la funcionalidad de carga de archivos CLARO y el algoritmo de correlación en KRONOS, garantizando:

- ✅ Carga exacta de 5,611 registros CLARO (4 archivos específicos)
- ✅ Carga correcta de archivo HUNTER 
- ✅ Identificación de 6 números objetivo específicos
- ✅ Funcionamiento del algoritmo de correlación
- ✅ Generación de reportes detallados de cada paso

## 📁 Archivos de Prueba Requeridos

### Ubicación Esperada
```
C:\Soluciones\BGC\claude\KNSOft\archivos\envioarchivosparaanalizar (1)\
```

### Archivos CLARO (Total: 5,611 registros)
1. **1-225211_LLAMADAS_ENTRANTES_POR_CELDA_545612_0.xlsx** (973 registros)
2. **1-225211_LLAMADAS_SALIENTES_POR_CELDA_545613_0.xlsx** (961 registros)
3. **2-225211_LLAMADAS_ENTRANTES_POR_CELDA_545614_0.xlsx** (1,939 registros)
4. **2-225211_LLAMADAS_SALIENTES_POR_CELDA_545615_0.xlsx** (1,738 registros)

### Archivo HUNTER
- **SCANHUNTER.xlsx** (archivo base para correlación)

### Números Objetivo para Correlación
- 3224274851
- 3208611034
- 3104277553
- 3102715509
- 3143534707
- 3214161903

## 🚀 Instalación y Configuración

### Paso 1: Configurar Entorno Automáticamente
```batch
setup-claro-e2e-environment.bat
```

Este script:
- Verifica Node.js y Python
- Instala dependencias npm y Playwright
- Instala dependencias Python del backend
- Crea estructura de directorios necesaria
- Verifica archivos de datos objetivo

### Paso 2: Configuración Manual (Alternativa)

#### Instalar Playwright
```bash
npm install @playwright/test
npx playwright install chromium
```

#### Instalar Dependencias Python
```bash
cd Backend
pip install -r requirements.txt
```

#### Crear Directorios
```bash
mkdir test-results tests\helpers tests\validation
```

## 🧪 Ejecución de Pruebas

### Opción 1: Suite Completa (Recomendada)
```batch
run-claro-e2e-complete.bat
```

**Ejecuta:**
- Validación previa de archivos objetivo
- Suite completa Playwright E2E
- Validación Python de resultados de BD
- Generación de reportes detallados

### Opción 2: Solo Playwright
```bash
npx playwright test --config=playwright-claro-e2e.config.ts
```

### Opción 3: Solo Validación de BD
```batch
quick-claro-validation.bat
```

**Útil para:**
- Verificar estado después de cargas manuales
- Debug rápido de contenido de BD
- Validación sin ejecutar UI

## 📊 Estructura de Archivos Generados

```
C:\Soluciones\BGC\claude\KNSOft\
├── playwright-claro-e2e.config.ts              # Configuración Playwright
├── tests\
│   ├── claro-e2e-complete-validation.spec.ts   # Suite principal de pruebas
│   ├── helpers\
│   │   └── database-validator.ts               # Helper de validación BD
│   └── validation\
│       └── claro-results-validator.py          # Validador Python
├── test-results\
│   ├── claro-e2e-html-report\                  # Reporte HTML Playwright
│   ├── claro-e2e-results.json                  # Resultados JSON
│   ├── claro-e2e-artifacts\                    # Screenshots y videos
│   └── claro_validation_report_*.json          # Reporte Python detallado
└── run-claro-e2e-complete.bat                  # Script principal
```

## 🔍 Flujo de Pruebas Detallado

### Fase 1: Verificación Inicial
1. **Verificar disponibilidad de KRONOS**
2. **Crear misión de prueba**
3. **Validar archivos objetivo existen**

### Fase 2: Carga de Datos Base
4. **Cargar archivo HUNTER**
5. **Validar carga HUNTER en BD**

### Fase 3: Carga Secuencial CLARO
6. **Archivo 1 - Entrantes (973 registros)**
7. **Archivo 1 - Salientes (961 registros)**
8. **Archivo 2 - Entrantes (1,939 registros)**
9. **Archivo 2 - Salientes (1,738 registros)**
10. **Validación incremental después de cada archivo**

### Fase 4: Validaciones Finales
11. **Validar total exacto: 5,611 registros**
12. **Validar distribución por tipo y dirección**
13. **Buscar números objetivo en datos cargados**

### Fase 5: Correlación y Análisis
14. **Configurar período de correlación: 2021-05-20 10:00 - 14:30**
15. **Ejecutar algoritmo de correlación**
16. **Validar resultados de correlación**

### Fase 6: Reporte Final
17. **Generar reporte ejecutivo completo**
18. **Validar criterios de éxito**

## 📈 Criterios de Éxito

### Criterios Críticos (Deben Cumplirse)
- ✅ **Archivo HUNTER cargado**: scanner_cellular_data > 0 registros
- ✅ **4 archivos CLARO cargados**: Exactamente 5,611 registros CLARO
- ✅ **Distribución correcta**: Entrantes (2,912) + Salientes (2,699)
- ✅ **Base de datos consistente**: Sin errores de integridad

### Criterios de Calidad (Deseables)
- ✅ **Números objetivo encontrados**: Al menos 3 de 6 números
- ✅ **Correlaciones detectadas**: Algoritmo encuentra coincidencias
- ✅ **Rendimiento aceptable**: Carga completa < 10 minutos
- ✅ **Sin errores de UI**: Todas las acciones completan exitosamente

## 🔧 Configuración Avanzada

### Timeouts Personalizados
```javascript
// En playwright-claro-e2e.config.ts
timeout: 600000, // 10 minutos por test
expect: { timeout: 45000 } // 45 segundos para assertions
```

### Variables de Entorno
```batch
set TEST_DATA_PATH=C:\ruta\alternativa\datos
set EXPECTED_TOTAL_RECORDS=5611
set TARGET_NUMBERS=3224274851,3208611034,3104277553,3102715509,3143534707,3214161903
```

### Modos de Ejecución
```batch
# Modo con interfaz visible (debugging)
run-claro-e2e-complete.bat --headed

# Modo headless (CI/CD)
run-claro-e2e-complete.bat --headless
```

## 📋 Reportes Generados

### 1. Reporte HTML Playwright
- **Ubicación**: `test-results/claro-e2e-html-report/index.html`
- **Contenido**: 
  - Timeline de ejecución de pruebas
  - Screenshots de cada paso
  - Videos de pruebas fallidas
  - Traces detallados para debugging

### 2. Reporte JSON de Resultados
- **Ubicación**: `test-results/claro-e2e-results.json`
- **Contenido**:
  - Resultados estructurados de cada test
  - Métricas de tiempo de ejecución
  - Estado de cada validación

### 3. Reporte Python de Validación
- **Ubicación**: `test-results/claro_validation_report_YYYYMMDD_HHMMSS.json`
- **Contenido**:
  - Análisis detallado de base de datos
  - Validación de números objetivo
  - Estado de correlaciones
  - Recomendaciones ejecutivas

### 4. Reporte de Resumen Ejecutivo
- **Ubicación**: `test-results/execution-summary-TIMESTAMP.txt`
- **Contenido**:
  - Resultado general (PASSED/FAILED)
  - Códigos de salida de cada componente
  - Links a reportes detallados
  - Métricas clave

## 🐛 Troubleshooting

### Problema: Archivos no encontrados
```
[ERROR] Archivo faltante: 1-225211_LLAMADAS_ENTRANTES_POR_CELDA_545612_0.xlsx
```
**Solución**: Verificar que todos los archivos estén en `archivos\envioarchivosparaanalizar (1)\`

### Problema: Base de datos bloqueada
```
[ERROR] database is locked
```
**Solución**: 
1. Cerrar KRONOS completamente
2. Eliminar archivos `.db-wal` y `.db-shm`
3. Reiniciar pruebas

### Problema: Playwright timeout
```
[ERROR] Test timeout of 600000ms exceeded
```
**Solución**:
1. Verificar que KRONOS esté ejecutándose en puerto 8000
2. Aumentar timeout en configuración
3. Ejecutar con `--headed` para observar el proceso

### Problema: Números objetivo no encontrados
```
[WARNING] Target numbers found: 0/6
```
**Posibles causas**:
1. Archivos CLARO no contienen los números esperados
2. Formato de números diferente en archivos
3. Período de correlación incorrecto

**Solución**:
1. Ejecutar `quick-claro-validation.bat` para análisis detallado
2. Revisar formato de números en archivos fuente
3. Ajustar período de correlación

## 📞 Números de Prueba Específicos

Los siguientes números deben encontrarse en los datos:

| Número | Esperado en | Estado |
|--------|-------------|--------|
| 3224274851 | CLARO/HUNTER | 🎯 Objetivo crítico |
| 3208611034 | CLARO/HUNTER | 🎯 Objetivo crítico |
| 3104277553 | CLARO/HUNTER | 🎯 Objetivo crítico |
| 3102715509 | CLARO/HUNTER | 🎯 Objetivo crítico |
| 3143534707 | CLARO/HUNTER | 🎯 Objetivo crítico |
| 3214161903 | CLARO/HUNTER | 🎯 Objetivo crítico |

## 🚨 Alertas de Calidad

### ⚠️ Advertencias Importantes
- **Backup automático**: Se crea backup de BD antes de cada ejecución
- **Datos existentes**: Las pruebas pueden usar datos previos en BD
- **Tiempo de ejecución**: Suite completa puede tomar 10-15 minutos
- **Recursos del sistema**: Requiere memoria suficiente para procesar 5,611 registros

### 🔒 Consideraciones de Seguridad
- Los archivos de prueba contienen datos reales anonimizados
- Los reportes pueden contener números de teléfono
- Mantener confidencialidad de archivos de datos

## 📝 Historial de Cambios

### v1.0.0 (2025-01-18)
- ✅ Suite completa de pruebas E2E CLARO
- ✅ Validación de 5,611 registros exactos
- ✅ Algoritmo de correlación integrado
- ✅ Reportes detallados multi-formato
- ✅ Scripts de automatización completos
- ✅ Documentación comprehensiva

## 🤝 Soporte

Para problemas o preguntas sobre esta suite de pruebas:

1. **Revisar logs detallados** en `test-results/`
2. **Ejecutar validación rápida** con `quick-claro-validation.bat`
3. **Verificar configuración** con `setup-claro-e2e-environment.bat`
4. **Consultar troubleshooting** en esta documentación

---

**Autor**: Testing Team KRONOS  
**Versión**: 1.0.0  
**Última actualización**: 18 de Enero, 2025