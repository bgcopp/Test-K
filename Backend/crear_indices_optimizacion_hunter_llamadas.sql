-- CREACIÓN DE ÍNDICES PARA OPTIMIZACIÓN DE CONSULTAS HUNTER-LLAMADAS
-- Boris - Optimización de rendimiento para relaciones entre cellular_data y operator_call_data
-- Fecha: 2025-08-19

-- ==================================================
-- 1. ÍNDICES BÁSICOS PARA JOIN OPERATIONS
-- ==================================================

-- Índice para cell_id en tabla HUNTER (cellular_data)
CREATE INDEX IF NOT EXISTS idx_cellular_data_cell_id 
ON cellular_data(cell_id);

-- Índice para celda_origen en tabla LLAMADAS (operator_call_data)
CREATE INDEX IF NOT EXISTS idx_operator_call_data_celda_origen 
ON operator_call_data(celda_origen);

-- Índice para celda_destino en tabla LLAMADAS (operator_call_data)
CREATE INDEX IF NOT EXISTS idx_operator_call_data_celda_destino 
ON operator_call_data(celda_destino);

-- ==================================================
-- 2. ÍNDICES COMPUESTOS PARA CONSULTAS CON FILTROS
-- ==================================================

-- Índice compuesto para filtrar por misión y buscar por cell_id
CREATE INDEX IF NOT EXISTS idx_cellular_data_mission_cell 
ON cellular_data(mission_id, cell_id);

-- Índice compuesto para filtrar por misión y buscar por celda_origen
CREATE INDEX IF NOT EXISTS idx_operator_call_data_mission_origen 
ON operator_call_data(mission_id, celda_origen);

-- Índice compuesto para filtrar por misión y buscar por celda_destino
CREATE INDEX IF NOT EXISTS idx_operator_call_data_mission_destino 
ON operator_call_data(mission_id, celda_destino);

-- ==================================================
-- 3. ÍNDICES PARA CONSULTAS TEMPORALES
-- ==================================================

-- Índice para ordenamiento por fecha de llamadas
CREATE INDEX IF NOT EXISTS idx_operator_call_data_fecha 
ON operator_call_data(fecha_hora_llamada);

-- Índice compuesto para filtrar por misión y ordenar por fecha
CREATE INDEX IF NOT EXISTS idx_operator_call_data_mission_fecha 
ON operator_call_data(mission_id, fecha_hora_llamada);

-- ==================================================
-- 4. ÍNDICES PARA BÚSQUEDAS POR OPERADOR
-- ==================================================

-- Índice para filtros por operador en datos HUNTER
CREATE INDEX IF NOT EXISTS idx_cellular_data_operator 
ON cellular_data(operator);

-- Índice para filtros por operador en llamadas
CREATE INDEX IF NOT EXISTS idx_operator_call_data_operator 
ON operator_call_data(operator);

-- ==================================================
-- 5. ÍNDICES PARA BÚSQUEDAS GEOGRÁFICAS
-- ==================================================

-- Índice compuesto para consultas geográficas en HUNTER
CREATE INDEX IF NOT EXISTS idx_cellular_data_coords 
ON cellular_data(lat, lon);

-- Índice para búsquedas por punto específico
CREATE INDEX IF NOT EXISTS idx_cellular_data_punto 
ON cellular_data(punto);

-- ==================================================
-- 6. ANÁLISIS DE ESTADÍSTICAS
-- ==================================================

-- Actualizar estadísticas de la base de datos para optimizar el query planner
ANALYZE cellular_data;
ANALYZE operator_call_data;

-- ==================================================
-- VERIFICACIÓN DE ÍNDICES CREADOS
-- ==================================================

-- Consulta para verificar todos los índices creados
SELECT 
    name as indice_nombre,
    tbl_name as tabla,
    sql as definicion_sql
FROM sqlite_master 
WHERE type = 'index' 
    AND tbl_name IN ('cellular_data', 'operator_call_data')
    AND name LIKE 'idx_%'
ORDER BY tbl_name, name;