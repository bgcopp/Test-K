# ANÁLISIS CRÍTICO TABLA DE CORRELACIÓN - BORIS
===============================================================================
**Fecha:** 2025-08-19  
**Solicitado por:** Boris  
**Objetivo:** Implementación de funcionalidad "Tabla de Correlación"  
**Estado:** ANÁLISIS COMPLETO REALIZADO

## RESULTADO DEL ANÁLISIS CRÍTICO

### ✅ 1. VERIFICACIÓN TABLA `operator_call_data`

**EXISTE Y ESTÁ COMPLETAMENTE POBLADA:**
- **Total registros:** 3,392 
- **Estructura:** 26 columnas con tipos de datos apropiados
- **Índices:** 17 índices específicos para optimización de consultas
- **Integridad:** Datos válidos y consistentes

**CAMPOS CLAVE IDENTIFICADOS:**
```sql
- numero_origen (TEXT) - NOT NULL ✓
- numero_destino (TEXT) - NOT NULL ✓  
- fecha_hora_llamada (DATETIME) - NOT NULL ✓
- duracion_segundos (INTEGER) - Default 0 ✓
- mission_id (TEXT) - NOT NULL ✓
- operator (TEXT) - NOT NULL ✓
- celda_origen (TEXT) - Nullable
- celda_destino (TEXT) - Nullable
```

### ✅ 2. MAPEO DE CAMPOS A REQUERIMIENTOS

**MAPEO DIRECTO DISPONIBLE:**
- **ORIGINADOR** ← `numero_origen`
- **RECEPTOR** ← `numero_destino`  
- **FECHA_HORA** ← `fecha_hora_llamada`
- **DURACIÓN** ← `duracion_segundos`

### ✅ 3. DATOS DE PRUEBA ESPECÍFICOS ENCONTRADOS

**Para número 3113330727:**
- Como **número origen:** 3 registros ✓
- Como **número destino:** 0 registros
- **Ejemplos reales encontrados:**
  1. `3113330727 → 3214665744` (2021-05-20 12:55:13, 6s)
  2. `3113330727 → 3227863649` (2021-05-20 13:08:43, 29s) 
  3. `3113330727 → 3226506678` (2021-05-20 12:30:31, 11s)

### ✅ 4. RELACIÓN CON CORRELACIONES

**CLAVE DE RELACIÓN IDENTIFICADA:**
```sql
-- Filtro por registro seleccionado de tabla correlación
WHERE mission_id = :mission_id 
  AND (numero_origen = :numero_objetivo OR numero_destino = :numero_objetivo)
  AND fecha_hora_llamada BETWEEN :start_datetime AND :end_datetime
```

### ✅ 5. ÍNDICES EXISTENTES PARA PERFORMANCE

**ÍNDICES CRÍTICOS IDENTIFICADOS:**
- `idx_calls_correlation_origen_full` - Para consultas por número origen
- `idx_calls_correlation_destino_full` - Para consultas por número destino  
- `idx_calls_correlation_objetivo_full` - Para consultas por número objetivo
- `idx_calls_fecha_hora` - Para filtros por fecha
- `idx_calls_mission_operator` - Para filtros por misión y operador

### ✅ 6. ESTADÍSTICAS OPERACIONALES

**DISTRIBUCIÓN DE DATOS:**
- **Operador:** CLARO (3,392 registros)
- **Misión:** mission_MPFRBNsb (única misión activa)
- **Período:** 2021-05-20 10:00:00 a 13:59:50
- **Tipos llamada:** ENTRANTE y SALIENTE
- **Duración:** 0s - 3,909s (promedio: 187.71s)

## QUERY DE IMPLEMENTACIÓN RECOMENDADO

```sql
-- Query optimizado para Tabla de Correlación
SELECT 
    numero_origen as originador,
    numero_destino as receptor,  
    fecha_hora_llamada as fecha_hora,
    duracion_segundos as duracion,
    operator as operador,
    celda_origen,
    celda_destino,
    tipo_llamada
FROM operator_call_data 
WHERE mission_id = :mission_id
  AND (numero_origen = :numero_objetivo OR numero_destino = :numero_objetivo)
  AND fecha_hora_llamada BETWEEN :start_datetime AND :end_datetime
ORDER BY fecha_hora_llamada DESC
```

## PROBLEMAS IDENTIFICADOS: NINGUNO

❌ **NO hay problemas críticos**  
❌ **NO faltan campos requeridos**  
❌ **NO hay problemas de integridad**  
❌ **NO hay limitaciones de performance**

## RECOMENDACIONES PARA IMPLEMENTACIÓN

### 🎯 1. ESTRUCTURA DEL POPUP

```typescript
interface TablaCorrelacionData {
  originador: string;
  receptor: string; 
  fecha_hora: string;
  duracion: number;
  operador: string;
  celda_origen?: string;
  celda_destino?: string;
}
```

### 🎯 2. FILTROS RECOMENDADOS

- **Por registro de correlación:** numero_objetivo
- **Por rango temporal:** start_datetime, end_datetime  
- **Por mission_id:** Automático desde contexto
- **Opcional por operador:** CLARO (único disponible actualmente)

### 🎯 3. FUNCIONES BACKEND NECESARIAS

```python
@eel.expose
def get_interaction_table_data(mission_id: str, numero_objetivo: str, 
                              start_datetime: str, end_datetime: str):
    # Implementar query optimizado
    # Usar índices existentes
    # Retornar datos formateados para tabla
```

### 🎯 4. PERFORMANCE GARANTIZADA

- **Índices existentes:** Consultas sub-100ms esperadas
- **Dataset pequeño:** 3,392 registros total
- **Filtros efectivos:** Por número objetivo muy selectivo

## CONCLUSIÓN

✅ **IMPLEMENTACIÓN 100% VIABLE**  
✅ **Datos completos y consistentes disponibles**  
✅ **Performance optimizada con índices existentes**  
✅ **Mapeo directo de campos a requerimientos**  
✅ **Datos de prueba específicos confirmados**

**RECOMENDACIÓN:** Proceder inmediatamente con la implementación.  
**TIEMPO ESTIMADO:** 2-3 horas para implementación completa.  
**RIESGO:** BAJO - Datos y estructura completamente validados.

---
**Preparado por:** Claude Code  
**Para:** Boris - Proyecto KRONOS  
**Siguiente paso:** Implementación del popup y funciones backend