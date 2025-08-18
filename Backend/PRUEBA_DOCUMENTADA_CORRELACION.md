# 📋 PRUEBA DOCUMENTADA - ANÁLISIS DE CORRELACIÓN KRONOS

**Proyecto:** KRONOS  
**Módulo:** Análisis de Correlación  
**Autor:** Boris  
**Fecha:** 16 de agosto de 2025  
**Versión:** 1.0.0

---

## 🎯 OBJETIVO DE LA PRUEBA

Validar el funcionamiento completo del algoritmo de correlación para detectar números objetivo mediante la correlación de Cell IDs entre datos HUNTER (scanner) y datos de operadores celulares.

### Números Objetivo a Detectar:
- **3224274851** *(Crítico)*
- **3208611034**
- **3104277553** *(Crítico)*
- **3102715509**
- **3143534707**
- **3214161903**

---

## 📊 DATOS DE PRUEBA

### 1. Datos HUNTER Disponibles
- **Misión:** `mission_MPFRBNsb`
- **Período:** 2021-05-20 10:00:00 a 2021-05-20 15:00:00
- **Total registros:** 58
- **Cell IDs únicos:** 46

### 2. Datos de Operadores
- **Operador:** CLARO
- **Período con datos objetivo:** 2021-05-20 y 2024-08-12
- **Registros totales:** 3,159
- **Cell IDs únicos:** 251

### 3. Configuración de Prueba
```json
{
  "mission_id": "mission_MPFRBNsb",
  "start_date": "2021-05-20 10:00:00",
  "end_date": "2021-05-20 15:00:00",
  "min_coincidences": 1
}
```

---

## 🔄 PROCESO DE PRUEBA PASO A PASO

### PASO 1: Preparación del Entorno

#### 1.1 Verificar Base de Datos
```bash
cd Backend
sqlite3 kronos.db ".tables"
# Debe mostrar: cellular_data, operator_call_data, missions, etc.
```

#### 1.2 Verificar Datos HUNTER
```sql
SELECT COUNT(*) FROM cellular_data WHERE mission_id = 'mission_MPFRBNsb';
-- Resultado esperado: 58 registros
```

#### 1.3 Verificar Números Objetivo
```sql
SELECT numero_origen, numero_destino, fecha_hora_llamada, celda_origen, celda_destino
FROM operator_call_data
WHERE numero_origen IN ('3224274851', '3104277553')
   OR numero_destino IN ('3224274851', '3104277553');
-- Debe mostrar al menos el registro 3104277553 -> 3224274851
```

### PASO 2: Iniciar Aplicación

#### 2.1 Iniciar Backend
```bash
cd Backend
python main.py
# Esperar mensaje: "Aplicación disponible en ventana del navegador"
```

#### 2.2 Verificar Frontend
- Abrir navegador en http://localhost:8000
- Iniciar sesión con credenciales de administrador
- Navegar a Misiones

### PASO 3: Configurar Análisis de Correlación

#### 3.1 Seleccionar Misión
1. Click en "Misiones" en sidebar
2. Seleccionar misión existente o crear nueva
3. Ir a pestaña "Análisis"

#### 3.2 Configurar Parámetros
```
Fecha inicio: 2021-05-20 10:00:00
Fecha fin: 2021-05-20 15:00:00
Mínimo coincidencias: 1
```

#### 3.3 Ejecutar Análisis
1. Click en "Ejecutar Análisis de Correlación"
2. Esperar indicador de progreso
3. Verificar que no aparezca pantalla en blanco

### PASO 4: Validar Resultados

#### 4.1 Resultados Esperados
| Número | Estado Esperado | Celdas Esperadas | Validación |
|--------|----------------|------------------|------------|
| 3224274851 | ✅ Detectado | ['56124', '51438'] | Crítico |
| 3143534707 | ✅ Detectado | ['56124', '51438'] | OK |
| 3208611034 | ✅ Detectado | ['51203'] | OK |
| 3102715509 | ✅ Detectado | ['56124'] | OK |
| 3104277553 | ⚠️ No detectado | - | Fecha diferente |
| 3214161903 | ⚠️ No detectado | - | Celdas no coinciden |

#### 4.2 Verificar en UI
- ✅ Tabla muestra resultados
- ✅ Columna "Número Celular" visible
- ✅ Columna "Total Coincidencias" > 0
- ✅ Columna "Celdas Detectadas" muestra Cell IDs
- ✅ Paginación funciona si hay > 25 resultados
- ✅ Filtro por número funciona

#### 4.3 Verificar Consola del Navegador (F12)
```javascript
// Logs esperados:
"🚀 Iniciando análisis de correlación"
"📥 Resultado del análisis: {...}"
"✅ Datos válidos recibidos: X registros"
"✅ Registros validados: Y de X"
```

### PASO 5: Pruebas de Error

#### 5.1 Probar con Fechas Inválidas
```
Fecha inicio: 2025-01-01
Fecha fin: 2024-01-01
```
**Esperado:** Mensaje de error "Fecha inicio debe ser anterior a fecha fin"

#### 5.2 Probar con Período > 365 días
```
Fecha inicio: 2020-01-01
Fecha fin: 2022-01-01
```
**Esperado:** Mensaje de error "El rango no puede exceder 365 días"

#### 5.3 Probar sin Datos HUNTER
- Usar misión sin datos HUNTER
**Esperado:** Mensaje "No hay datos HUNTER para el período"

---

## 📈 RESULTADOS DE LA PRUEBA

### ✅ ÉXITOS
- [ ] Backend inicia correctamente
- [ ] Frontend carga sin errores
- [ ] Análisis se ejecuta sin pantalla en blanco
- [ ] 4 de 6 números objetivo detectados
- [ ] Paginación funciona
- [ ] Filtros funcionan
- [ ] Exportación funciona

### ⚠️ PROBLEMAS ENCONTRADOS
- [ ] Documentar cualquier error
- [ ] Capturar screenshots
- [ ] Registrar logs de consola

### 📊 MÉTRICAS DE RENDIMIENTO
- **Tiempo de análisis:** ___ segundos
- **Memoria utilizada:** ___ MB
- **CPU máximo:** ___%
- **Registros procesados:** ___
- **Correlaciones encontradas:** ___

---

## 🔍 VALIDACIÓN BACKEND DIRECTA

### Script de Validación Python
```python
# test_correlacion_mision_actual.py
from services.correlation_analysis_service import CorrelationAnalysisService
import json

service = CorrelationAnalysisService()
result = service.analyze_correlation(
    start_date='2021-05-20 10:00:00',
    end_date='2021-05-20 15:00:00',
    min_coincidences=1,
    mission_id='mission_MPFRBNsb'
)

print(f"Total correlaciones: {len(result.get('correlations', []))}")
print(f"Tiempo procesamiento: {result.get('analysis_time', 0)}")

# Verificar números objetivo
target_numbers = ['3224274851', '3208611034', '3104277553', 
                  '3102715509', '3143534707', '3214161903']

for number in target_numbers:
    found = any(c['numero_celular'] == number 
                for c in result.get('correlations', []))
    print(f"{number}: {'✅ Encontrado' if found else '❌ No encontrado'}")
```

---

## 📝 CHECKLIST DE VALIDACIÓN

### Pre-Requisitos
- [ ] Base de datos con datos de prueba
- [ ] Backend Python ejecutándose
- [ ] Frontend accesible en navegador
- [ ] Usuario con permisos de análisis

### Funcionalidad Core
- [ ] Login exitoso
- [ ] Navegación a misiones
- [ ] Selección de misión
- [ ] Configuración de parámetros
- [ ] Ejecución sin errores
- [ ] Visualización de resultados

### Validación de Datos
- [ ] Números objetivo aparecen
- [ ] Cell IDs correctos
- [ ] Coincidencias calculadas
- [ ] Operadores identificados
- [ ] Fechas dentro del rango

### Manejo de Errores
- [ ] No hay pantalla en blanco
- [ ] Mensajes de error claros
- [ ] Recuperación de errores
- [ ] Logging en consola

### Performance
- [ ] Tiempo < 5 segundos
- [ ] Sin congelamiento UI
- [ ] Paginación fluida
- [ ] Exportación rápida

---

## 🚨 TROUBLESHOOTING

### Problema: Pantalla en Blanco
**Solución:**
1. Abrir consola (F12)
2. Buscar errores en rojo
3. Verificar backend está corriendo
4. Recargar página (F5)

### Problema: No hay resultados
**Solución:**
1. Verificar período tiene datos
2. Revisar misión seleccionada
3. Confirmar min_coincidencias = 1
4. Verificar datos HUNTER existen

### Problema: Error de timeout
**Solución:**
1. Reducir rango de fechas
2. Aumentar timeout en frontend
3. Verificar performance backend
4. Optimizar consultas SQL

---

## 📊 REPORTE FINAL

### Resumen Ejecutivo
- **Estado:** [✅ APROBADO / ❌ FALLIDO]
- **Fecha prueba:** ___________
- **Ejecutado por:** ___________
- **Versión probada:** ___________

### Números Objetivo Detectados
- 3224274851: [✅/❌]
- 3208611034: [✅/❌]
- 3104277553: [✅/❌]
- 3102715509: [✅/❌]
- 3143534707: [✅/❌]
- 3214161903: [✅/❌]

### Observaciones
_[Documentar cualquier observación relevante]_

### Recomendaciones
_[Documentar mejoras sugeridas]_

---

## 📎 ANEXOS

### A. Screenshots
- [ ] Login
- [ ] Configuración análisis
- [ ] Resultados
- [ ] Errores (si hay)

### B. Logs
- [ ] Backend Python
- [ ] Consola navegador
- [ ] Base de datos

### C. Archivos de Prueba
- [ ] Backup BD antes
- [ ] Backup BD después
- [ ] Configuración usada
- [ ] Resultados exportados

---

**FIN DEL DOCUMENTO DE PRUEBA**