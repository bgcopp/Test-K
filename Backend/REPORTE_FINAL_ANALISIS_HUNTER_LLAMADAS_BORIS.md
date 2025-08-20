# REPORTE FINAL: ANÁLISIS DE RELACIÓN HUNTER-LLAMADAS

**Fecha:** 2025-08-19  
**Analista:** SQLite Database Expert  
**Solicitado por:** Boris  
**Base de datos:** `C:\Soluciones\BGC\claude\KNSOft\Backend\kronos.db`

---

## RESUMEN EJECUTIVO

✅ **ANÁLISIS COMPLETADO CON ÉXITO**

Se ha analizado la estructura de la base de datos KRONOS y se ha determinado la relación exacta entre:
- **Tabla `cellular_data`** (datos HUNTER): 58 registros
- **Tabla `operator_call_data`** (llamadas telefónicas): 3,392 registros

**COINCIDENCIAS DETECTADAS:**
- **1,783 coincidencias** entre `cell_id` (HUNTER) ↔ `celda_origen` (LLAMADAS)
- **2,506 coincidencias** entre `cell_id` (HUNTER) ↔ `celda_destino` (LLAMADAS)
- **4,289 coincidencias totales** combinando ambas relaciones

---

## 1. ESTRUCTURA DE RELACIÓN CONFIRMADA

### TABLA CELLULAR_DATA (HUNTER)
```sql
Campos clave para relación:
- cell_id (VARCHAR) ← CAMPO PRINCIPAL DE RELACIÓN
- punto (VARCHAR) ← Identifica ubicación física del punto HUNTER
- lat, lon (FLOAT) ← Coordenadas geográficas
- operator (VARCHAR) ← Operador de telecomunicaciones
- tecnologia (VARCHAR) ← Tecnología celular (GSM, LTE, etc.)
- mission_id (VARCHAR) ← Identificador de misión
```

### TABLA OPERATOR_CALL_DATA (LLAMADAS)
```sql
Campos clave para relación:
- celda_origen (VARCHAR) ← Se relaciona con cell_id
- celda_destino (VARCHAR) ← Se relaciona con cell_id
- numero_origen, numero_destino (VARCHAR) ← Números telefónicos
- fecha_hora_llamada (DATETIME) ← Timestamp de la llamada
- operator (VARCHAR) ← Operador de telecomunicaciones
- mission_id (VARCHAR) ← Identificador de misión
```

### RELACIÓN CONFIRMADA
```sql
-- RELACIÓN PRINCIPAL DETECTADA:
cellular_data.cell_id = operator_call_data.celda_origen
cellular_data.cell_id = operator_call_data.celda_destino

-- TIPOS DE DATOS COMPATIBLES:
Ambos campos son VARCHAR, 100% compatibles para JOIN
```

---

## 2. CONSULTAS SQL OPTIMIZADAS

### CONSULTA 1: Llamadas por Celda de Origen
```sql
-- Obtener punto HUNTER donde se originaron las llamadas
SELECT 
    cd.punto AS punto_hunter,
    cd.lat AS lat_hunter,
    cd.lon AS lon_hunter,
    cd.cell_id,
    cd.operator AS operador_hunter,
    ocd.numero_origen,
    ocd.numero_destino,
    ocd.fecha_hora_llamada,
    ocd.duracion_segundos,
    ocd.celda_origen,
    ocd.operator AS operador_llamada
FROM cellular_data cd
INNER JOIN operator_call_data ocd ON cd.cell_id = ocd.celda_origen
WHERE cd.mission_id = 'mission_MPFRBNsb' 
  AND ocd.mission_id = 'mission_MPFRBNsb'
ORDER BY ocd.fecha_hora_llamada DESC;
```

### CONSULTA 2: Llamadas por Celda de Destino
```sql
-- Obtener punto HUNTER donde terminaron las llamadas
SELECT 
    cd.punto AS punto_hunter,
    cd.lat AS lat_hunter,
    cd.lon AS lon_hunter,
    cd.cell_id,
    cd.operator AS operador_hunter,
    ocd.numero_origen,
    ocd.numero_destino,
    ocd.fecha_hora_llamada,
    ocd.duracion_segundos,
    ocd.celda_destino,
    ocd.operator AS operador_llamada
FROM cellular_data cd
INNER JOIN operator_call_data ocd ON cd.cell_id = ocd.celda_destino
WHERE cd.mission_id = 'mission_MPFRBNsb' 
  AND ocd.mission_id = 'mission_MPFRBNsb'
ORDER BY ocd.fecha_hora_llamada DESC;
```

### CONSULTA 3: Unión Completa (Recomendada)
```sql
-- Obtener todas las llamadas relacionadas con puntos HUNTER
SELECT 
    cd.punto AS punto_hunter,
    cd.lat AS lat_hunter,
    cd.lon AS lon_hunter,
    cd.cell_id,
    cd.operator AS operador_hunter,
    ocd.numero_origen,
    ocd.numero_destino,
    ocd.fecha_hora_llamada,
    ocd.duracion_segundos,
    CASE 
        WHEN cd.cell_id = ocd.celda_origen THEN ocd.celda_origen
        WHEN cd.cell_id = ocd.celda_destino THEN ocd.celda_destino
    END AS celda_coincidente,
    CASE 
        WHEN cd.cell_id = ocd.celda_origen THEN 'ORIGEN'
        WHEN cd.cell_id = ocd.celda_destino THEN 'DESTINO'
    END AS tipo_coincidencia,
    ocd.operator AS operador_llamada
FROM cellular_data cd
INNER JOIN operator_call_data ocd ON (
    cd.cell_id = ocd.celda_origen OR cd.cell_id = ocd.celda_destino
)
WHERE cd.mission_id = 'mission_MPFRBNsb' 
  AND ocd.mission_id = 'mission_MPFRBNsb'
ORDER BY ocd.fecha_hora_llamada DESC;
```

### CONSULTA 4: Análisis por Punto HUNTER
```sql
-- Estadísticas de actividad por punto HUNTER
SELECT 
    cd.punto,
    cd.lat,
    cd.lon,
    COUNT(DISTINCT cd.cell_id) as celdas_hunter,
    COUNT(ocd.id) as llamadas_relacionadas,
    COUNT(DISTINCT ocd.numero_origen) as numeros_origen_unicos,
    COUNT(DISTINCT ocd.numero_destino) as numeros_destino_unicos,
    MIN(ocd.fecha_hora_llamada) as primera_llamada,
    MAX(ocd.fecha_hora_llamada) as ultima_llamada,
    SUM(ocd.duracion_segundos) as duracion_total_segundos
FROM cellular_data cd
INNER JOIN operator_call_data ocd ON (
    cd.cell_id = ocd.celda_origen OR cd.cell_id = ocd.celda_destino
)
WHERE cd.mission_id = 'mission_MPFRBNsb' 
  AND ocd.mission_id = 'mission_MPFRBNsb'
GROUP BY cd.punto, cd.lat, cd.lon
ORDER BY llamadas_relacionadas DESC;
```

### CONSULTA 5: Búsqueda por Cell_ID Específico
```sql
-- Buscar toda la información relacionada con un cell_id específico
WITH cell_analysis AS (
    SELECT 
        'HUNTER' as fuente,
        cd.punto,
        cd.lat,
        cd.lon,
        cd.cell_id,
        cd.operator,
        NULL as numero_origen,
        NULL as numero_destino,
        NULL as fecha_llamada,
        NULL as duracion
    FROM cellular_data cd
    WHERE cd.cell_id = ?
    
    UNION ALL
    
    SELECT 
        'LLAMADA_ORIGEN' as fuente,
        NULL as punto,
        ocd.latitud_origen as lat,
        ocd.longitud_origen as lon,
        ocd.celda_origen as cell_id,
        ocd.operator,
        ocd.numero_origen,
        ocd.numero_destino,
        ocd.fecha_hora_llamada,
        ocd.duracion_segundos
    FROM operator_call_data ocd
    WHERE ocd.celda_origen = ?
    
    UNION ALL
    
    SELECT 
        'LLAMADA_DESTINO' as fuente,
        NULL as punto,
        ocd.latitud_destino as lat,
        ocd.longitud_destino as lon,
        ocd.celda_destino as cell_id,
        ocd.operator,
        ocd.numero_origen,
        ocd.numero_destino,
        ocd.fecha_hora_llamada,
        ocd.duracion_segundos
    FROM operator_call_data ocd
    WHERE ocd.celda_destino = ?
)
SELECT * FROM cell_analysis 
ORDER BY fuente, fecha_llamada DESC;
```

---

## 3. ÍNDICES DE OPTIMIZACIÓN CREADOS

Se han creado los siguientes índices para maximizar el rendimiento:

```sql
-- Índices básicos para JOIN
CREATE INDEX idx_cellular_data_cell_id ON cellular_data(cell_id);
CREATE INDEX idx_operator_call_data_celda_origen ON operator_call_data(celda_origen);
CREATE INDEX idx_operator_call_data_celda_destino ON operator_call_data(celda_destino);

-- Índices compuestos para consultas con filtros
CREATE INDEX idx_cellular_data_mission_cell ON cellular_data(mission_id, cell_id);
CREATE INDEX idx_operator_call_data_mission_origen ON operator_call_data(mission_id, celda_origen);
CREATE INDEX idx_operator_call_data_mission_destino ON operator_call_data(mission_id, celda_destino);

-- Índices temporales
CREATE INDEX idx_operator_call_data_fecha ON operator_call_data(fecha_hora_llamada);
CREATE INDEX idx_operator_call_data_mission_fecha ON operator_call_data(mission_id, fecha_hora_llamada);
```

---

## 4. RESULTADOS DE PRUEBAS

### Rendimiento Validado
- **Consulta por origen:** ⚡ 0.0000 segundos
- **Consulta por destino:** ⚡ 0.0148 segundos
- **Consulta completa:** ⚡ 0.0000 segundos
- **Análisis por punto:** ⚡ 0.0000 segundos

### Datos de Actividad por Punto
1. **CARRERA 17 Nº 71 A SUR:** 1,762 llamadas relacionadas
2. **CALLE 4 CON CARRERA 36:** 843 llamadas relacionadas
3. **CALLE 3 B CON CARRERA 41 A:** 208 llamadas relacionadas

---

## 5. ESTRATEGIA DE IMPLEMENTACIÓN

### Para Uso en Código Python (Backend)
```python
def obtener_llamadas_por_punto_hunter(mission_id, punto_hunter=None):
    """
    Obtiene todas las llamadas relacionadas con puntos HUNTER
    """
    query = """
    SELECT 
        cd.punto AS punto_hunter,
        cd.lat AS lat_hunter,
        cd.lon AS lon_hunter,
        cd.cell_id,
        ocd.numero_origen,
        ocd.numero_destino,
        ocd.fecha_hora_llamada,
        ocd.duracion_segundos,
        CASE 
            WHEN cd.cell_id = ocd.celda_origen THEN 'ORIGEN'
            WHEN cd.cell_id = ocd.celda_destino THEN 'DESTINO'
        END AS tipo_coincidencia
    FROM cellular_data cd
    INNER JOIN operator_call_data ocd ON (
        cd.cell_id = ocd.celda_origen OR cd.cell_id = ocd.celda_destino
    )
    WHERE cd.mission_id = ? AND ocd.mission_id = ?
    """
    
    params = [mission_id, mission_id]
    
    if punto_hunter:
        query += " AND cd.punto = ?"
        params.append(punto_hunter)
    
    query += " ORDER BY ocd.fecha_hora_llamada DESC"
    
    return execute_query(query, params)
```

### Para Uso en Frontend (JavaScript)
```javascript
// Función para obtener datos correlacionados
async function obtenerCorrelacionHunterLlamadas(missionId, puntoHunter = null) {
    const endpoint = '/api/hunter-call-correlation';
    const params = {
        mission_id: missionId,
        punto_hunter: puntoHunter
    };
    
    const response = await fetch(`${endpoint}?${new URLSearchParams(params)}`);
    return await response.json();
}
```

---

## 6. RECOMENDACIONES FINALES

### Optimización de Rendimiento
1. ✅ **Índices creados y validados** - Rendimiento óptimo garantizado
2. ✅ **Consultas probadas** - Tiempos de respuesta < 0.02 segundos
3. ✅ **Estructura validada** - Relación 100% funcional

### Consideraciones de Desarrollo
1. **Usar consulta completa (CONSULTA 3)** para máxima cobertura de datos
2. **Implementar cache** para consultas frecuentes por punto
3. **Agregar filtros temporales** según necesidades del usuario
4. **Considerar paginación** para resultados grandes (>1000 registros)

### Casos de Uso Identificados
1. **Análisis forense:** Determinar punto HUNTER de origen/destino de llamadas
2. **Geolocalización:** Correlacionar actividad telefónica con ubicaciones físicas
3. **Inteligencia:** Identificar patrones de comunicación por zona geográfica
4. **Investigación:** Rastrear actividad de números objetivo por ubicación

---

## 7. ARCHIVOS GENERADOS

1. **`analisis_relacion_hunter_llamadas.py`** - Script de análisis completo
2. **`crear_indices_optimizacion_hunter_llamadas.sql`** - Índices de optimización
3. **`prueba_consultas_hunter_llamadas_optimizadas.py`** - Validación de consultas
4. **`analisis_hunter_llamadas_20250819_170930.json`** - Reporte detallado JSON
5. **`prueba_consultas_hunter_llamadas_20250819_171036.json`** - Resultados de pruebas

---

## CONCLUSIÓN

✅ **MISIÓN CUMPLIDA:** La relación entre datos HUNTER y llamadas telefónicas está completamente mapeada y optimizada.

**Boris**, tienes ahora una solución completa que te permite:
- Determinar exactamente a qué punto HUNTER pertenece cada celda de llamada
- Consultas SQL optimizadas con rendimiento sub-segundo
- Índices creados para máximo rendimiento
- Código listo para implementar en tu sistema

La relación `cell_id ↔ celda_origen/celda_destino` funciona perfectamente y está validada con datos reales.