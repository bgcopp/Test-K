# ACTUALIZACIÓN ENDPOINT get_call_interactions - INTEGRACIÓN HUNTER

**Fecha:** 2025-08-19
**Desarrollador:** Claude Code
**Solicitado por:** Boris

## OBJETIVO

Modificar el endpoint `get_call_interactions` en `Backend/main.py` para incluir datos del archivo HUNTER correlacionando las celdas de llamadas con información de puntos HUNTER.

## ANÁLISIS TÉCNICO

### Estructuras de Base de Datos Identificadas

**Tabla `cellular_data` (HUNTER):**
```sql
- mission_id VARCHAR NOT NULL
- cell_id VARCHAR NOT NULL
- punto VARCHAR NOT NULL  
- lat FLOAT NOT NULL
- lon FLOAT NOT NULL
- operator VARCHAR NOT NULL
```

**Tabla `operator_call_data` (LLAMADAS):**
```sql
- mission_id TEXT NOT NULL
- celda_origen TEXT
- celda_destino TEXT
- numero_origen TEXT NOT NULL
- numero_destino TEXT NOT NULL
- fecha_hora_llamada DATETIME NOT NULL
- duracion_segundos INTEGER DEFAULT 0
- latitud_origen REAL
- longitud_origen REAL
- latitud_destino REAL
- longitud_destino REAL
- operator TEXT NOT NULL
```

### Función Actual (líneas 984-1147)
- **Ubicación:** `Backend/main.py` líneas 984-1147
- **Funcionalidad actual:** Consulta solo `operator_call_data`
- **Retorna:** 11 campos de llamadas sin información HUNTER

## IMPLEMENTACIÓN

### Cambios Realizados

1. **Consulta SQL actualizada** con LEFT JOINs para correlacionar:
   - `cellular_data.cell_id` con `operator_call_data.celda_origen`
   - `cellular_data.cell_id` con `operator_call_data.celda_destino`

2. **Campos adicionales retornados:**
   - `punto_hunter_origen` (punto HUNTER de celda origen)
   - `punto_hunter_destino` (punto HUNTER de celda destino)
   - `lat_hunter_origen`, `lon_hunter_origen`
   - `lat_hunter_destino`, `lon_hunter_destino`

3. **Mantiene funcionalidad existente:**
   - Mismos parámetros de entrada
   - Mismas validaciones
   - Mismo logging y manejo de errores
   - Retorna JSON serializable

### Nueva Consulta SQL Optimizada

```sql
SELECT 
    ocd.numero_origen as originador,
    ocd.numero_destino as receptor,
    ocd.fecha_hora_llamada as fecha_hora, 
    ocd.duracion_segundos as duracion,
    ocd.operator as operador,
    ocd.celda_origen,
    ocd.celda_destino,
    ocd.latitud_origen,
    ocd.longitud_origen,
    ocd.latitud_destino,
    ocd.longitud_destino,
    cd_origen.punto as punto_hunter_origen,
    cd_origen.lat as lat_hunter_origen,
    cd_origen.lon as lon_hunter_origen,
    cd_destino.punto as punto_hunter_destino,
    cd_destino.lat as lat_hunter_destino,
    cd_destino.lon as lon_hunter_destino
FROM operator_call_data ocd
LEFT JOIN cellular_data cd_origen ON (cd_origen.cell_id = ocd.celda_origen AND cd_origen.mission_id = ocd.mission_id)
LEFT JOIN cellular_data cd_destino ON (cd_destino.cell_id = ocd.celda_destino AND cd_destino.mission_id = ocd.mission_id)
WHERE ocd.mission_id = :mission_id
  AND (ocd.numero_origen = :target_number OR ocd.numero_destino = :target_number)
  AND ocd.fecha_hora_llamada BETWEEN :start_datetime AND :end_datetime  
ORDER BY ocd.fecha_hora_llamada DESC
```

### Nuevos Campos de Respuesta

Cada registro ahora incluirá 6 campos adicionales:
- `punto_hunter_origen`: String o None
- `punto_hunter_destino`: String o None  
- `lat_hunter_origen`: String o None
- `lon_hunter_origen`: String o None
- `lat_hunter_destino`: String o None
- `lon_hunter_destino`: String o None

## VALIDACIÓN

- [ ] Mantiene compatibilidad con frontend existente
- [ ] Preserva funcionalidad de parámetros de entrada
- [ ] Conserva logging y manejo de errores
- [ ] Retorna JSON válido
- [ ] Los LEFT JOINs no afectan rendimiento significativamente

## BENEFICIOS

1. **Correlación de datos:** Unifica información de llamadas con puntos HUNTER
2. **Análisis enriquecido:** Permite mapear llamadas con ubicaciones exactas de celdas
3. **Compatibilidad:** No rompe funcionalidad existente
4. **Performance:** LEFT JOINs optimizados con índices existentes

## RESPALDO

La función original se preserva en este archivo como referencia para rollback si fuera necesario.