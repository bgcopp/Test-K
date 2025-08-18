-- =====================================================================================
-- SCRIPT DE OPTIMIZACIÓN AVANZADA PARA CONSULTAS DE CORRELACIÓN - KRONOS SQLite
-- =====================================================================================
--
-- DESCRIPCIÓN: Optimización integral para consultas de correlación entre datos
--              HUNTER (cellular_data) y registros de operadores (operator_call_data)
--              
-- OBJETIVO PRINCIPAL: Optimizar la consulta crítica que busca registros donde
--                     celda_origen o celda_destino estén en una lista de 50+ celdas HUNTER
--
-- ANÁLISIS ACTUAL DE LA BD:
-- - cellular_data: 58 registros (57 celdas únicas HUNTER)  
-- - operator_call_data: 3,395 registros (253 celdas origen, 71 celdas destino)
-- - Tamaño BD: 16.83 MB
-- - Índices existentes: 56 (algunos pueden ser redundantes)
--
-- AUTOR: Sistema de Optimización KRONOS
-- FECHA: 2025-08-18
-- =====================================================================================

-- Configuración avanzada de SQLite para máximo rendimiento
PRAGMA journal_mode = WAL;           -- Write-Ahead Logging para mejor concurrencia
PRAGMA synchronous = NORMAL;         -- Balance seguridad/rendimiento  
PRAGMA cache_size = -65536;          -- 64MB cache (suficiente para BD actual)
PRAGMA temp_store = MEMORY;          -- Tablas temporales en RAM
PRAGMA mmap_size = 134217728;        -- 128MB memory-mapped I/O
PRAGMA query_planner = ON;           -- Habilitar análisis de rendimiento

BEGIN TRANSACTION;

-- =====================================================================================
-- SECCIÓN 1: ÍNDICES CRÍTICOS PARA LA CONSULTA PRINCIPAL DE CORRELACIÓN
-- =====================================================================================
-- Optimizan: WHERE (celda_origen IN (...) OR celda_destino IN (...)) AND mission_id = ?

-- ÍNDICE PRINCIPAL: Correlación por celdas de origen con lista IN()
-- Crítico para la consulta principal con 50+ celdas HUNTER
DROP INDEX IF EXISTS idx_correlation_origen_critical;
CREATE INDEX idx_correlation_origen_critical 
ON operator_call_data(celda_origen, mission_id, fecha_hora_llamada, numero_origen, operator, numero_destino);

-- ÍNDICE PRINCIPAL: Correlación por celdas de destino con lista IN()
DROP INDEX IF EXISTS idx_correlation_destino_critical;
CREATE INDEX idx_correlation_destino_critical 
ON operator_call_data(celda_destino, mission_id, fecha_hora_llamada, numero_destino, operator, numero_origen);

-- ÍNDICE COVERING: Para consultas de agregación (GROUP BY numero, operador)
-- Evita lookups adicionales a la tabla principal
DROP INDEX IF EXISTS idx_covering_correlation_summary;
CREATE INDEX idx_covering_correlation_summary 
ON operator_call_data(numero_origen, numero_destino, operator, mission_id, 
                      celda_origen, celda_destino, fecha_hora_llamada, duracion_segundos);

-- =====================================================================================
-- SECCIÓN 2: ÍNDICES PARA ANÁLISIS TEMPORAL Y FILTRADO
-- =====================================================================================

-- ÍNDICE TEMPORAL: Para filtros de rango de fechas en correlación
-- Optimiza: AND fecha_hora_llamada >= '2021-01-01'
DROP INDEX IF EXISTS idx_temporal_correlation;
CREATE INDEX idx_temporal_correlation 
ON operator_call_data(fecha_hora_llamada, mission_id, celda_origen, celda_destino);

-- ÍNDICE COMPUESTO: Para consultas con múltiples filtros
DROP INDEX IF EXISTS idx_multi_filter_correlation;
CREATE INDEX idx_multi_filter_correlation 
ON operator_call_data(mission_id, operator, fecha_hora_llamada, numero_origen, numero_destino);

-- ÍNDICE ESPECIALIZADO: Para números objetivo (análisis específico)
DROP INDEX IF EXISTS idx_numero_objetivo_optimized;
CREATE INDEX idx_numero_objetivo_optimized 
ON operator_call_data(numero_objetivo, mission_id, celda_objetivo, operator, fecha_hora_llamada)
WHERE numero_objetivo IS NOT NULL AND numero_objetivo != '';

-- =====================================================================================
-- SECCIÓN 3: ÍNDICES PARA DATOS HUNTER (cellular_data)
-- =====================================================================================

-- ÍNDICE HUNTER: Para JOIN con operator_call_data
-- Optimiza: JOIN ON (celda_origen = cell_id OR celda_destino = cell_id)
DROP INDEX IF EXISTS idx_hunter_join_optimized;
CREATE INDEX idx_hunter_join_optimized 
ON cellular_data(cell_id, mission_id, operator, tecnologia, created_at);

-- ÍNDICE COVERING HUNTER: Para consultas que incluyen datos adicionales
DROP INDEX IF EXISTS idx_hunter_covering_analysis;
CREATE INDEX idx_hunter_covering_analysis 
ON cellular_data(mission_id, cell_id, operator, tecnologia, lat, lon, rssi, created_at);

-- =====================================================================================
-- SECCIÓN 4: ÍNDICES PARCIALES PARA OPTIMIZACIÓN ESPECÍFICA
-- =====================================================================================

-- ÍNDICE PARCIAL: Solo registros con celdas válidas (optimización crítica)
-- Evita indexar registros NULL que no participan en correlación
DROP INDEX IF EXISTS idx_partial_valid_cells_origen;
CREATE INDEX idx_partial_valid_cells_origen 
ON operator_call_data(celda_origen, mission_id, numero_origen, fecha_hora_llamada)
WHERE celda_origen IS NOT NULL AND celda_origen != '';

DROP INDEX IF EXISTS idx_partial_valid_cells_destino;
CREATE INDEX idx_partial_valid_cells_destino 
ON operator_call_data(celda_destino, mission_id, numero_destino, fecha_hora_llamada)
WHERE celda_destino IS NOT NULL AND celda_destino != '';

-- ÍNDICE PARCIAL: Números colombianos válidos (patrón 3XXXXXXXXX)
DROP INDEX IF EXISTS idx_partial_colombian_numbers;
CREATE INDEX idx_partial_colombian_numbers 
ON operator_call_data(numero_origen, numero_destino, mission_id, operator, fecha_hora_llamada)
WHERE (numero_origen LIKE '3%' AND LENGTH(numero_origen) = 10) 
   OR (numero_destino LIKE '3%' AND LENGTH(numero_destino) = 10);

-- =====================================================================================
-- SECCIÓN 5: ÍNDICES PARA ESTADÍSTICAS Y AGREGACIONES
-- =====================================================================================

-- ÍNDICE ESTADÍSTICO: Para COUNT(*) GROUP BY numero, operador
-- Optimiza la agregación final de la consulta principal
DROP INDEX IF EXISTS idx_stats_aggregation_calls;
CREATE INDEX idx_stats_aggregation_calls 
ON operator_call_data(numero_origen, operator, mission_id, fecha_hora_llamada, duracion_segundos);

DROP INDEX IF EXISTS idx_stats_aggregation_destino;
CREATE INDEX idx_stats_aggregation_destino 
ON operator_call_data(numero_destino, operator, mission_id, fecha_hora_llamada, duracion_segundos);

-- ÍNDICE FRECUENCIA: Para análisis de celdas más activas
DROP INDEX IF EXISTS idx_stats_cell_frequency;
CREATE INDEX idx_stats_cell_frequency 
ON operator_call_data(celda_origen, celda_destino, operator, mission_id, fecha_hora_llamada);

-- =====================================================================================
-- SECCIÓN 6: OPTIMIZACIÓN DE CONSULTAS CON OR
-- =====================================================================================
-- SQLite puede tener dificultades con OR complejos, creamos índices específicos

-- ÍNDICE UNION: Para optimizar WHERE celda_origen IN (...) OR celda_destino IN (...)
-- SQLite puede usar UNION internamente con estos índices
DROP INDEX IF EXISTS idx_union_origen_cells;
CREATE INDEX idx_union_origen_cells 
ON operator_call_data(celda_origen, numero_origen, mission_id, fecha_hora_llamada, operator);

DROP INDEX IF EXISTS idx_union_destino_cells;
CREATE INDEX idx_union_destino_cells 
ON operator_call_data(celda_destino, numero_destino, mission_id, fecha_hora_llamada, operator);

-- =====================================================================================
-- SECCIÓN 7: LIMPIEZA DE ÍNDICES REDUNDANTES
-- =====================================================================================
-- Eliminar índices que podrían ser redundantes con las nuevas optimizaciones

-- Verificar si estos índices son redundantes después de las optimizaciones
-- (Comentados para evaluación manual)
-- DROP INDEX IF EXISTS idx_calls_correlation_origen_full;
-- DROP INDEX IF EXISTS idx_calls_correlation_destino_full;
-- DROP INDEX IF EXISTS idx_calls_mission_operator;  -- Podría ser redundante

-- Mantener índices críticos existentes que siguen siendo útiles:
-- - idx_calls_numero_objetivo (específico)
-- - idx_calls_fecha_hora (temporal general)
-- - idx_cellular_cell_id (HUNTER básico)
-- - idx_cellular_mission_id (misión básico)

-- =====================================================================================
-- SECCIÓN 8: FINALIZACIÓN Y ESTADÍSTICAS
-- =====================================================================================

COMMIT;

-- Actualizar estadísticas críticas para el optimizador de consultas
ANALYZE operator_call_data;
ANALYZE cellular_data;
ANALYZE;

-- Configuración final optimizada
PRAGMA optimize;

-- =====================================================================================
-- SECCIÓN 9: CONSULTAS DE VALIDACIÓN DE RENDIMIENTO
-- =====================================================================================
-- Usar estas consultas para verificar que los índices se están utilizando

-- CONSULTA PRINCIPAL OPTIMIZADA - Usar con EXPLAIN QUERY PLAN
/*
EXPLAIN QUERY PLAN
SELECT 
    ocd.numero_origen,
    ocd.numero_destino,
    ocd.operator,
    COUNT(*) as total_registros,
    MIN(ocd.fecha_hora_llamada) as primera_llamada,
    MAX(ocd.fecha_hora_llamada) as ultima_llamada
FROM operator_call_data ocd
WHERE ocd.mission_id = 'mission_MPFRBNsb'
  AND (ocd.celda_origen IN ('10111','10248','10263','10753','11713','20264','37825') 
       OR ocd.celda_destino IN ('10111','10248','10263','10753','11713','20264','37825'))
  AND ocd.fecha_hora_llamada >= '2021-01-01'
GROUP BY ocd.numero_origen, ocd.numero_destino, ocd.operator
ORDER BY total_registros DESC
LIMIT 100;
*/

-- CONSULTA DE CORRELACIÓN HUNTER-OPERADOR
/*
EXPLAIN QUERY PLAN
SELECT DISTINCT
    cd.cell_id,
    cd.operator as hunter_operator,
    ocd.operator as call_operator,
    COUNT(ocd.id) as total_correlaciones
FROM cellular_data cd
JOIN operator_call_data ocd ON (
    (ocd.celda_origen = cd.cell_id OR ocd.celda_destino = cd.cell_id)
    AND ocd.mission_id = cd.mission_id
)
WHERE cd.mission_id = 'mission_MPFRBNsb'
GROUP BY cd.cell_id, cd.operator, ocd.operator
ORDER BY total_correlaciones DESC;
*/

-- =====================================================================================
-- SECCIÓN 10: DOCUMENTACIÓN TÉCNICA Y RECOMENDACIONES
-- =====================================================================================

/*
RESUMEN DE OPTIMIZACIONES IMPLEMENTADAS PARA KRONOS:

=== ÍNDICES CRÍTICOS CREADOS ===

1. CONSULTA PRINCIPAL (Query con IN 50+ celdas):
   ✓ idx_correlation_origen_critical    - Optimiza celda_origen IN (...)
   ✓ idx_correlation_destino_critical   - Optimiza celda_destino IN (...)
   ✓ idx_covering_correlation_summary   - Covering index para GROUP BY

2. OPTIMIZACIÓN TEMPORAL:
   ✓ idx_temporal_correlation           - Filtros por fecha_hora_llamada
   ✓ idx_multi_filter_correlation       - Consultas con múltiples filtros

3. DATOS HUNTER:
   ✓ idx_hunter_join_optimized          - JOIN optimizado con operator_call_data
   ✓ idx_hunter_covering_analysis       - Covering para análisis completo

4. ÍNDICES PARCIALES:
   ✓ idx_partial_valid_cells_origen     - Solo celdas válidas (no NULL)
   ✓ idx_partial_valid_cells_destino    - Solo celdas válidas (no NULL)
   ✓ idx_partial_colombian_numbers      - Solo números colombianos (3XXXXXXXXX)

5. ESTADÍSTICAS Y AGREGACIÓN:
   ✓ idx_stats_aggregation_calls        - Optimiza COUNT(*) GROUP BY
   ✓ idx_stats_cell_frequency          - Análisis de frecuencia de celdas

6. OPTIMIZACIÓN OR:
   ✓ idx_union_origen_cells            - Manejo eficiente de OR complejos
   ✓ idx_union_destino_cells           - Manejo eficiente de OR complejos

=== IMPACTO ESPERADO EN RENDIMIENTO ===

CONSULTA PRINCIPAL (celda_origen IN (...) OR celda_destino IN (...)):
- Antes: Escaneo completo de 3,395 registros
- Después: Búsqueda por índice O(log n) + merge
- Mejora esperada: 20-100x más rápida

AGREGACIÓN (GROUP BY numero_origen, numero_destino, operator):
- Antes: Sort temporal de resultados filtrados
- Después: Covering index evita acceso a tabla principal
- Mejora esperada: 5-20x más rápida

JOIN HUNTER-OPERADOR:
- Antes: Nested loop join
- Después: Index lookup join
- Mejora esperada: 10-50x más rápida

=== CONSIDERACIONES DE MANTENIMIENTO ===

TAMAÑO DE BASE DE DATOS:
- Actual: 16.83 MB
- Después de índices: ~22-25 MB (+30-50%)
- Acceptable para el rendimiento ganado

IMPACTO EN INSERCIONES:
- Degradación: ~10-15% más lentas
- Justificado por mejoras en consultas

RECOMENDACIONES OPERACIONALES:

1. ANÁLISIS PERIÓDICO:
   - Ejecutar ANALYZE después de cargas masivas (>1000 registros)
   - Frecuencia recomendada: Semanalmente o después de imports grandes

2. MONITOREO DE RENDIMIENTO:
   - Usar EXPLAIN QUERY PLAN para verificar uso de índices
   - Monitorear tiempo de respuesta de consultas críticas

3. LIMPIEZA DE ÍNDICES:
   - Evaluar índices redundantes después de 1 mes de operación
   - Considerar eliminar índices no utilizados según logs de query planner

=== COMANDOS DE MANTENIMIENTO ===

-- Actualizar estadísticas (ejecutar mensualmente)
ANALYZE;

-- Optimización general (ejecutar semanalmente)  
PRAGMA optimize;

-- Verificar fragmentación (ejecutar cuando sea necesario)
PRAGMA integrity_check;

-- Compactar BD si es necesario (ejecutar trimestralmente)
VACUUM;

=== QUERIES DE MONITOREO ===

-- Verificar uso de índices en consulta principal:
EXPLAIN QUERY PLAN SELECT ...

-- Ver estadísticas de índices:
SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name LIKE '%correlation%';

-- Verificar tamaño de índices:
SELECT name, pgsize FROM dbstat WHERE name LIKE '%idx_%' ORDER BY pgsize DESC;

=== CONFIGURACIÓN RECOMENDADA DE APLICACIÓN ===

-- En conexión a BD (ejecutar en cada apertura):
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = -65536;  -- 64MB cache
PRAGMA temp_store = MEMORY;
PRAGMA mmap_size = 134217728; -- 128MB mmap

=== VALIDACIÓN POST-IMPLEMENTACIÓN ===

1. Ejecutar consulta principal con EXPLAIN QUERY PLAN
2. Verificar que usa idx_correlation_origen_critical o idx_correlation_destino_critical
3. Confirmar tiempo de respuesta < 100ms para consultas típicas
4. Validar que agregaciones usan covering indexes

Boris, este script optimiza específicamente tu consulta crítica de correlación.
Los índices están diseñados para manejar eficientemente listas de 50+ celdas HUNTER
y las agregaciones por número y operador que necesitas.

*/

-- =====================================================================================
-- FIN DEL SCRIPT DE OPTIMIZACIÓN
-- =====================================================================================