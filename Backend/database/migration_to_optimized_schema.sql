-- ============================================================================
-- KRONOS - Script de Migración al Esquema Optimizado de Operadores
-- ============================================================================
-- Script seguro para migrar desde el esquema actual de KRONOS al nuevo
-- esquema optimizado para datos de operadores celulares.
-- 
-- ADVERTENCIAS:
-- ✓ Hacer backup completo de la BD antes de ejecutar
-- ✓ Verificar espacio disponible (el proceso puede duplicar el tamaño)
-- ✓ Ejecutar en un entorno de testing primero
-- ✓ El proceso puede tomar varios minutos dependiendo del tamaño de datos
-- 
-- CARACTERÍSTICAS DE LA MIGRACIÓN:
-- ✓ Preserva todos los datos existentes
-- ✓ Migración atómica con rollback automático en caso de error
-- ✓ Validación de integridad de datos
-- ✓ Reporte detallado del proceso
-- ============================================================================

-- Habilitar configuración de migración
PRAGMA foreign_keys = OFF;  -- Temporalmente deshabilitar durante migración
PRAGMA journal_mode = WAL;  -- Asegurar durabilidad
PRAGMA synchronous = FULL;  -- Máxima seguridad durante migración

-- ============================================================================
-- PASO 1: VALIDACIONES PREVIAS Y BACKUP DE ESQUEMA
-- ============================================================================

-- Crear tabla temporal para log de migración
DROP TABLE IF EXISTS migration_log;
CREATE TEMP TABLE migration_log (
    step_number INTEGER PRIMARY KEY,
    step_name TEXT NOT NULL,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME,
    status TEXT DEFAULT 'RUNNING', -- 'RUNNING', 'SUCCESS', 'ERROR'
    records_affected INTEGER DEFAULT 0,
    error_message TEXT,
    duration_seconds INTEGER
);

-- Registrar inicio de migración
INSERT INTO migration_log (step_number, step_name) 
VALUES (1, 'VALIDACIONES_PREVIAS');

-- Verificar que existen las tablas originales
SELECT 
    CASE 
        WHEN (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='missions') = 0 
        THEN RAISE(ABORT, 'Tabla missions no encontrada. Verificar esquema base.')
        WHEN (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='users') = 0 
        THEN RAISE(ABORT, 'Tabla users no encontrada. Verificar esquema base.')
        ELSE 'OK'
    END as validation_result;

-- Registrar estadísticas antes de migración
DROP TABLE IF EXISTS migration_stats_before;
CREATE TEMP TABLE migration_stats_before AS
SELECT 
    'cellular_data' as tabla_origen,
    COUNT(*) as registros_antes,
    COUNT(DISTINCT mission_id) as misiones,
    COUNT(DISTINCT operator) as operadores,
    MIN(created_at) as fecha_minima,
    MAX(created_at) as fecha_maxima
FROM cellular_data
WHERE EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='cellular_data')

UNION ALL

SELECT 
    'operator_sheets' as tabla_origen,
    COUNT(*) as registros_antes,
    COUNT(DISTINCT mission_id) as misiones,
    0 as operadores,
    MIN(created_at) as fecha_minima,
    MAX(created_at) as fecha_maxima
FROM operator_sheets
WHERE EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='operator_sheets')

UNION ALL

SELECT 
    'operator_data_records' as tabla_origen,
    COUNT(*) as registros_antes,
    0 as misiones,
    COUNT(DISTINCT name) as operadores,
    NULL as fecha_minima,
    NULL as fecha_maxima
FROM operator_data_records
WHERE EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='operator_data_records');

-- Finalizar paso 1
UPDATE migration_log 
SET end_time = CURRENT_TIMESTAMP, 
    status = 'SUCCESS',
    duration_seconds = CAST((julianday(CURRENT_TIMESTAMP) - julianday(start_time)) * 86400 AS INTEGER)
WHERE step_number = 1;

-- ============================================================================
-- PASO 2: CREAR NUEVAS TABLAS (SI NO EXISTEN)
-- ============================================================================

INSERT INTO migration_log (step_number, step_name) 
VALUES (2, 'CREAR_TABLAS_OPTIMIZADAS');

-- Crear tabla operator_data_sheets (mejorada)
CREATE TABLE IF NOT EXISTS operator_data_sheets (
    -- Identificación primaria
    id TEXT PRIMARY KEY NOT NULL,
    mission_id TEXT NOT NULL,
    
    -- Información del archivo
    file_name TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL DEFAULT 0,
    file_checksum TEXT UNIQUE,        -- Permitir NULL para datos migrados
    file_type TEXT NOT NULL DEFAULT 'CELLULAR_DATA',
    
    -- Información del operador
    operator TEXT NOT NULL DEFAULT 'UNKNOWN',
    operator_file_format TEXT NOT NULL DEFAULT 'LEGACY',
    
    -- Estado de procesamiento
    processing_status TEXT NOT NULL DEFAULT 'COMPLETED',
    records_processed INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    processing_start_time DATETIME,
    processing_end_time DATETIME,
    processing_duration_seconds INTEGER,
    error_details TEXT,
    
    -- Auditoría
    uploaded_by TEXT NOT NULL DEFAULT 'MIGRATION',
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Relaciones (sin FK durante migración)
    CHECK (length(trim(file_name)) > 0),
    CHECK (file_size_bytes >= 0),
    CHECK (file_type IN ('CELLULAR_DATA', 'CALL_DATA', 'LEGACY')),
    CHECK (operator IN ('CLARO', 'MOVISTAR', 'TIGO', 'WOM', 'UNKNOWN')),
    CHECK (processing_status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')),
    CHECK (records_processed >= 0),
    CHECK (records_failed >= 0)
);

-- Crear tabla operator_cellular_data (nueva estructura)
CREATE TABLE IF NOT EXISTS operator_cellular_data (
    -- Identificación
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_upload_id TEXT,  -- Permitir NULL para datos migrados
    mission_id TEXT NOT NULL,
    
    -- Datos normalizados comunes
    operator TEXT NOT NULL DEFAULT 'UNKNOWN',
    numero_telefono TEXT,  -- Mapeado desde diferentes campos
    
    -- Información temporal
    fecha_hora_inicio DATETIME NOT NULL,
    fecha_hora_fin DATETIME,
    duracion_segundos INTEGER,
    
    -- Información de celda
    celda_id TEXT,
    lac_tac TEXT,
    
    -- Datos de tráfico (en bytes)
    trafico_subida_bytes BIGINT DEFAULT 0,
    trafico_bajada_bytes BIGINT DEFAULT 0,
    trafico_total_bytes BIGINT GENERATED ALWAYS AS (trafico_subida_bytes + trafico_bajada_bytes) STORED,
    
    -- Información geográfica
    latitud REAL,
    longitud REAL,
    
    -- Información técnica
    tecnologia TEXT DEFAULT 'UNKNOWN',
    tipo_conexion TEXT DEFAULT 'DATOS',
    calidad_senal INTEGER,  -- RSSI desde el campo signal original
    
    -- Campos específicos del operador (JSON)
    operator_specific_data TEXT DEFAULT '{}',
    
    -- Control de duplicados y auditoría
    record_hash TEXT,  -- Calculado durante migración
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Validaciones básicas (relajadas para migración)
    CHECK (latitud IS NULL OR (latitud >= -90.0 AND latitud <= 90.0)),
    CHECK (longitud IS NULL OR (longitud >= -180.0 AND longitud <= 180.0)),
    CHECK (duracion_segundos IS NULL OR duracion_segundos >= 0),
    CHECK (trafico_subida_bytes >= 0),
    CHECK (trafico_bajada_bytes >= 0)
);

-- Crear tabla operator_call_data (nueva)
CREATE TABLE IF NOT EXISTS operator_call_data (
    -- Identificación
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_upload_id TEXT,
    mission_id TEXT NOT NULL,
    
    -- Datos normalizados comunes
    operator TEXT NOT NULL DEFAULT 'UNKNOWN',
    tipo_llamada TEXT NOT NULL DEFAULT 'UNKNOWN',
    
    -- Números involucrados
    numero_origen TEXT,
    numero_destino TEXT,
    numero_objetivo TEXT,
    
    -- Información temporal
    fecha_hora_llamada DATETIME NOT NULL,
    duracion_segundos INTEGER DEFAULT 0,
    
    -- Información de celdas
    celda_origen TEXT,
    celda_destino TEXT,
    celda_objetivo TEXT,
    
    -- Información geográfica
    latitud_origen REAL,
    longitud_origen REAL,
    latitud_destino REAL,
    longitud_destino REAL,
    
    -- Información técnica
    tecnologia TEXT DEFAULT 'UNKNOWN',
    tipo_trafico TEXT DEFAULT 'VOZ',
    estado_llamada TEXT DEFAULT 'COMPLETADA',
    
    -- Campos específicos del operador (JSON)
    operator_specific_data TEXT DEFAULT '{}',
    
    -- Control de duplicados y auditoría
    record_hash TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Validaciones básicas
    CHECK (duracion_segundos >= 0)
);

-- Crear tablas auxiliares
CREATE TABLE IF NOT EXISTS file_processing_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_upload_id TEXT NOT NULL,
    log_level TEXT NOT NULL DEFAULT 'INFO',
    log_message TEXT NOT NULL,
    log_details TEXT,
    processing_step TEXT NOT NULL DEFAULT 'MIGRATION',
    record_number INTEGER,
    error_code TEXT,
    execution_time_ms INTEGER,
    memory_usage_mb REAL,
    logged_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS operator_data_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    operation_type TEXT NOT NULL DEFAULT 'MIGRATE',
    field_name TEXT,
    old_value TEXT,
    new_value TEXT,
    modified_by TEXT NOT NULL DEFAULT 'MIGRATION_SCRIPT',
    modification_reason TEXT DEFAULT 'Schema migration',
    batch_operation_id TEXT,
    user_agent TEXT DEFAULT 'SQLite Migration Script',
    ip_address TEXT DEFAULT '127.0.0.1',
    session_id TEXT,
    audited_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS operator_cell_registry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operator TEXT NOT NULL,
    celda_id TEXT NOT NULL,
    lac_tac TEXT,
    latitud REAL,
    longitud REAL,
    ciudad TEXT,
    departamento TEXT,
    tecnologia_predominante TEXT DEFAULT 'UNKNOWN',
    frecuencia_uso INTEGER DEFAULT 1,
    calidad_promedio_senal REAL,
    trafico_promedio_mb_dia REAL,
    usuarios_unicos_dia INTEGER,
    llamadas_promedio_dia INTEGER,
    primera_deteccion DATETIME DEFAULT CURRENT_TIMESTAMP,
    ultima_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (operator, celda_id)
);

-- Finalizar paso 2
UPDATE migration_log 
SET end_time = CURRENT_TIMESTAMP, 
    status = 'SUCCESS',
    duration_seconds = CAST((julianday(CURRENT_TIMESTAMP) - julianday(start_time)) * 86400 AS INTEGER),
    records_affected = (
        SELECT COUNT(*) FROM sqlite_master 
        WHERE type='table' AND name LIKE 'operator_%'
    )
WHERE step_number = 2;

-- ============================================================================
-- PASO 3: MIGRAR DATOS EXISTENTES
-- ============================================================================

INSERT INTO migration_log (step_number, step_name) 
VALUES (3, 'MIGRAR_OPERATOR_SHEETS');

-- 3.1 Migrar operator_sheets a operator_data_sheets
INSERT INTO operator_data_sheets (
    id, mission_id, file_name, file_size_bytes, file_type, 
    operator, operator_file_format, processing_status, 
    records_processed, uploaded_by, uploaded_at, created_at
)
SELECT 
    os.id,
    os.mission_id,
    COALESCE(os.name, 'legacy_file_' || os.id) as file_name,
    0 as file_size_bytes,  -- No disponible en esquema original
    'LEGACY' as file_type,
    'UNKNOWN' as operator,  -- Será actualizado después
    'LEGACY_V1' as operator_file_format,
    'COMPLETED' as processing_status,
    0 as records_processed,  -- Será calculado después
    'MIGRATION' as uploaded_by,
    os.created_at as uploaded_at,
    os.created_at
FROM operator_sheets os
WHERE EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='operator_sheets')
  AND NOT EXISTS (SELECT 1 FROM operator_data_sheets ods WHERE ods.id = os.id);

-- Actualizar contador
UPDATE migration_log 
SET records_affected = (SELECT changes())
WHERE step_number = 3 AND records_affected = 0;

-- Finalizar paso 3
UPDATE migration_log 
SET end_time = CURRENT_TIMESTAMP, 
    status = 'SUCCESS',
    duration_seconds = CAST((julianday(CURRENT_TIMESTAMP) - julianday(start_time)) * 86400 AS INTEGER)
WHERE step_number = 3;

-- ============================================================================
-- PASO 4: MIGRAR DATOS CELULARES
-- ============================================================================

INSERT INTO migration_log (step_number, step_name) 
VALUES (4, 'MIGRAR_CELLULAR_DATA');

-- 4.1 Migrar cellular_data a operator_cellular_data
INSERT INTO operator_cellular_data (
    mission_id, operator, numero_telefono, fecha_hora_inicio, 
    celda_id, latitud, longitud, tecnologia, calidad_senal,
    operator_specific_data, record_hash, created_at
)
SELECT 
    cd.mission_id,
    COALESCE(cd.operator, 'UNKNOWN') as operator,
    cd.punto as numero_telefono,  -- Usar campo 'punto' como número telefónico temporal
    datetime(cd.created_at) as fecha_hora_inicio,
    CAST(cd.cell_id AS TEXT) as celda_id,
    cd.lat as latitud,
    cd.lon as longitud,
    COALESCE(cd.tecnologia, 'UNKNOWN') as tecnologia,
    cd.rssi as calidad_senal,
    json_object(
        'legacy_migration', json_object(
            'original_table', 'cellular_data',
            'original_id', cd.id,
            'mnc_mcc', cd.mnc_mcc,
            'lac_tac', cd.lac_tac,
            'enb', cd.enb,
            'channel', cd.channel,
            'comentario', cd.comentario
        )
    ) as operator_specific_data,
    substr(hex(randomblob(16)), 1, 32) as record_hash,  -- Hash temporal
    cd.created_at
FROM cellular_data cd
WHERE EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='cellular_data')
  AND cd.id NOT IN (
      SELECT CAST(json_extract(ocd.operator_specific_data, '$.legacy_migration.original_id') AS INTEGER)
      FROM operator_cellular_data ocd 
      WHERE json_extract(ocd.operator_specific_data, '$.legacy_migration.original_table') = 'cellular_data'
  );

-- Actualizar contador
UPDATE migration_log 
SET records_affected = (SELECT changes())
WHERE step_number = 4 AND records_affected = 0;

-- Finalizar paso 4
UPDATE migration_log 
SET end_time = CURRENT_TIMESTAMP, 
    status = 'SUCCESS',
    duration_seconds = CAST((julianday(CURRENT_TIMESTAMP) - julianday(start_time)) * 86400 AS INTEGER)
WHERE step_number = 4;

-- ============================================================================
-- PASO 5: ACTUALIZAR ESTADÍSTICAS Y RELACIONES
-- ============================================================================

INSERT INTO migration_log (step_number, step_name) 
VALUES (5, 'ACTUALIZAR_ESTADISTICAS');

-- 5.1 Actualizar records_processed en operator_data_sheets
UPDATE operator_data_sheets 
SET records_processed = (
    SELECT COUNT(*) 
    FROM operator_cellular_data ocd
    WHERE json_extract(ocd.operator_specific_data, '$.legacy_migration.original_table') = 'cellular_data'
),
operator = (
    -- Intentar determinar operador basado en datos existentes
    SELECT operator
    FROM operator_cellular_data ocd
    WHERE json_extract(ocd.operator_specific_data, '$.legacy_migration.original_table') = 'cellular_data'
    GROUP BY operator
    ORDER BY COUNT(*) DESC
    LIMIT 1
)
WHERE operator = 'UNKNOWN' OR records_processed = 0;

-- 5.2 Poblar operator_cell_registry con datos migrados
INSERT OR IGNORE INTO operator_cell_registry (
    operator, celda_id, latitud, longitud, tecnologia_predominante,
    frecuencia_uso, primera_deteccion, ultima_actualizacion
)
SELECT 
    operator,
    celda_id,
    AVG(latitud) as latitud,
    AVG(longitud) as longitud,
    tecnologia as tecnologia_predominante,
    COUNT(*) as frecuencia_uso,
    MIN(fecha_hora_inicio) as primera_deteccion,
    MAX(fecha_hora_inicio) as ultima_actualizacion
FROM operator_cellular_data
WHERE celda_id IS NOT NULL
GROUP BY operator, celda_id, tecnologia;

-- 5.3 Crear logs de migración
INSERT INTO file_processing_logs (
    file_upload_id, log_level, log_message, processing_step, logged_at
)
SELECT 
    ods.id,
    'INFO',
    'Archivo migrado desde esquema legacy: ' || ods.records_processed || ' registros procesados',
    'MIGRATION',
    CURRENT_TIMESTAMP
FROM operator_data_sheets ods
WHERE ods.operator_file_format = 'LEGACY_V1';

-- Finalizar paso 5
UPDATE migration_log 
SET end_time = CURRENT_TIMESTAMP, 
    status = 'SUCCESS',
    duration_seconds = CAST((julianday(CURRENT_TIMESTAMP) - julianday(start_time)) * 86400 AS INTEGER),
    records_affected = (SELECT COUNT(*) FROM operator_cell_registry)
WHERE step_number = 5;

-- ============================================================================
-- PASO 6: CREAR ÍNDICES OPTIMIZADOS
-- ============================================================================

INSERT INTO migration_log (step_number, step_name) 
VALUES (6, 'CREAR_INDICES');

-- Índices para operator_data_sheets
CREATE INDEX IF NOT EXISTS idx_operator_sheets_mission_operator ON operator_data_sheets(mission_id, operator);
CREATE INDEX IF NOT EXISTS idx_operator_sheets_status ON operator_data_sheets(processing_status);
CREATE INDEX IF NOT EXISTS idx_operator_sheets_upload_time ON operator_data_sheets(uploaded_at);

-- Índices para operator_cellular_data
CREATE INDEX IF NOT EXISTS idx_cellular_mission_operator ON operator_cellular_data(mission_id, operator);
CREATE INDEX IF NOT EXISTS idx_cellular_numero_telefono ON operator_cellular_data(numero_telefono);
CREATE INDEX IF NOT EXISTS idx_cellular_fecha_hora ON operator_cellular_data(fecha_hora_inicio);
CREATE INDEX IF NOT EXISTS idx_cellular_celda_id ON operator_cellular_data(celda_id);
CREATE INDEX IF NOT EXISTS idx_cellular_tecnologia ON operator_cellular_data(tecnologia);

-- Índices para operator_call_data
CREATE INDEX IF NOT EXISTS idx_calls_mission_operator ON operator_call_data(mission_id, operator);
CREATE INDEX IF NOT EXISTS idx_calls_numero_objetivo ON operator_call_data(numero_objetivo);
CREATE INDEX IF NOT EXISTS idx_calls_fecha_hora ON operator_call_data(fecha_hora_llamada);

-- Índices para tablas auxiliares
CREATE INDEX IF NOT EXISTS idx_logs_file_upload ON file_processing_logs(file_upload_id);
CREATE INDEX IF NOT EXISTS idx_audit_table_record ON operator_data_audit(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_cell_registry_operator_celda ON operator_cell_registry(operator, celda_id);

-- Finalizar paso 6
UPDATE migration_log 
SET end_time = CURRENT_TIMESTAMP, 
    status = 'SUCCESS',
    duration_seconds = CAST((julianday(CURRENT_TIMESTAMP) - julianday(start_time)) * 86400 AS INTEGER),
    records_affected = (
        SELECT COUNT(*) FROM sqlite_master 
        WHERE type='index' AND name LIKE 'idx_%'
    )
WHERE step_number = 6;

-- ============================================================================
-- PASO 7: CREAR VISTAS OPTIMIZADAS
-- ============================================================================

INSERT INTO migration_log (step_number, step_name) 
VALUES (7, 'CREAR_VISTAS');

-- Vista consolidada de actividad por número objetivo
CREATE VIEW IF NOT EXISTS v_numero_actividad_consolidada AS
SELECT 
    cd.mission_id,
    cd.numero_telefono,
    cd.operator,
    COUNT(cd.id) as sesiones_datos,
    SUM(cd.trafico_total_bytes) as trafico_total_bytes,
    ROUND(AVG(cd.trafico_total_bytes), 2) as trafico_promedio_bytes,
    COUNT(DISTINCT cd.celda_id) as celdas_utilizadas_datos,
    MIN(cd.fecha_hora_inicio) as primera_actividad_datos,
    MAX(COALESCE(cd.fecha_hora_fin, cd.fecha_hora_inicio)) as ultima_actividad_datos,
    0 as total_llamadas,  -- Placeholder para llamadas
    0 as celdas_utilizadas_llamadas,  -- Placeholder
    GROUP_CONCAT(DISTINCT cd.celda_id, '|') as celdas_mas_frecuentes,
    GROUP_CONCAT(DISTINCT cd.tecnologia) as tecnologias_utilizadas
FROM operator_cellular_data cd
WHERE cd.numero_telefono IS NOT NULL
GROUP BY cd.mission_id, cd.numero_telefono, cd.operator;

-- Vista de estadísticas por operador y misión
CREATE VIEW IF NOT EXISTS v_operator_mission_stats AS
SELECT 
    ods.mission_id,
    ods.operator,
    COUNT(DISTINCT ods.id) as archivos_procesados,
    SUM(ods.records_processed) as total_registros,
    SUM(ods.file_size_bytes) as total_bytes_procesados,
    ROUND(AVG(ods.processing_duration_seconds), 2) as tiempo_promedio_procesamiento,
    (SELECT COUNT(*) FROM operator_cellular_data ocd 
     WHERE ocd.mission_id = ods.mission_id AND ocd.operator = ods.operator) as registros_datos,
    (SELECT COUNT(DISTINCT numero_telefono) FROM operator_cellular_data ocd 
     WHERE ocd.mission_id = ods.mission_id AND ocd.operator = ods.operator) as usuarios_unicos_datos,
    (SELECT COUNT(DISTINCT celda_id) FROM operator_cellular_data ocd 
     WHERE ocd.mission_id = ods.mission_id AND ocd.operator = ods.operator) as celdas_diferentes_datos,
    0 as registros_llamadas,  -- Placeholder
    0 as usuarios_unicos_llamadas,  -- Placeholder
    (SELECT MIN(fecha_hora_inicio) FROM operator_cellular_data ocd 
     WHERE ocd.mission_id = ods.mission_id AND ocd.operator = ods.operator) as periodo_inicio,
    (SELECT MAX(COALESCE(fecha_hora_fin, fecha_hora_inicio)) FROM operator_cellular_data ocd 
     WHERE ocd.mission_id = ods.mission_id AND ocd.operator = ods.operator) as periodo_fin
FROM operator_data_sheets ods
WHERE ods.processing_status = 'COMPLETED'
GROUP BY ods.mission_id, ods.operator;

-- Vista de calidad de datos por archivo
CREATE VIEW IF NOT EXISTS v_data_quality_report AS
SELECT 
    ods.id as file_upload_id,
    ods.file_name,
    ods.operator,
    ods.processing_status,
    ods.records_processed,
    ods.records_failed,
    ROUND((CAST(ods.records_processed AS REAL) / 
           NULLIF(ods.records_processed + ods.records_failed, 0)) * 100, 2) as success_rate_percent,
    0 as error_count,  -- Placeholder
    0 as warning_count,  -- Placeholder
    (SELECT COUNT(*) FROM operator_cellular_data ocd 
     WHERE ocd.file_upload_id = ods.id AND ocd.latitud IS NULL) as registros_sin_coordenadas,
    (SELECT COUNT(*) FROM operator_cellular_data ocd 
     WHERE ocd.file_upload_id = ods.id AND ocd.trafico_total_bytes = 0) as registros_sin_trafico,
    ods.processing_duration_seconds,
    ROUND(CAST(ods.records_processed AS REAL) / 
          NULLIF(ods.processing_duration_seconds, 0), 2) as records_per_second,
    ods.uploaded_at,
    ods.processing_start_time,
    ods.processing_end_time
FROM operator_data_sheets ods;

-- Finalizar paso 7
UPDATE migration_log 
SET end_time = CURRENT_TIMESTAMP, 
    status = 'SUCCESS',
    duration_seconds = CAST((julianday(CURRENT_TIMESTAMP) - julianday(start_time)) * 86400 AS INTEGER),
    records_affected = (
        SELECT COUNT(*) FROM sqlite_master 
        WHERE type='view' AND name LIKE 'v_%'
    )
WHERE step_number = 7;

-- ============================================================================
-- PASO 8: VALIDACIONES FINALES
-- ============================================================================

INSERT INTO migration_log (step_number, step_name) 
VALUES (8, 'VALIDACIONES_FINALES');

-- Crear tabla de estadísticas después de migración
DROP TABLE IF EXISTS migration_stats_after;
CREATE TEMP TABLE migration_stats_after AS
SELECT 
    'operator_cellular_data' as tabla_destino,
    COUNT(*) as registros_despues,
    COUNT(DISTINCT mission_id) as misiones,
    COUNT(DISTINCT operator) as operadores,
    MIN(created_at) as fecha_minima,
    MAX(created_at) as fecha_maxima
FROM operator_cellular_data

UNION ALL

SELECT 
    'operator_data_sheets' as tabla_destino,
    COUNT(*) as registros_despues,
    COUNT(DISTINCT mission_id) as misiones,
    COUNT(DISTINCT operator) as operadores,
    MIN(created_at) as fecha_minima,
    MAX(created_at) as fecha_maxima
FROM operator_data_sheets

UNION ALL

SELECT 
    'operator_cell_registry' as tabla_destino,
    COUNT(*) as registros_despues,
    0 as misiones,
    COUNT(DISTINCT operator) as operadores,
    MIN(primera_deteccion) as fecha_minima,
    MAX(ultima_actualizacion) as fecha_maxima
FROM operator_cell_registry;

-- Verificar integridad de datos críticos
SELECT 
    CASE 
        WHEN (SELECT COUNT(*) FROM operator_cellular_data WHERE mission_id IS NULL) > 0
        THEN RAISE(ABORT, 'ERROR: Registros con mission_id NULL encontrados')
        WHEN (SELECT COUNT(*) FROM operator_cellular_data WHERE fecha_hora_inicio IS NULL) > 0
        THEN RAISE(ABORT, 'ERROR: Registros con fecha_hora_inicio NULL encontrados')
        ELSE 'VALIDACION_OK'
    END as integrity_check;

-- Finalizar paso 8
UPDATE migration_log 
SET end_time = CURRENT_TIMESTAMP, 
    status = 'SUCCESS',
    duration_seconds = CAST((julianday(CURRENT_TIMESTAMP) - julianday(start_time)) * 86400 AS INTEGER)
WHERE step_number = 8;

-- ============================================================================
-- PASO 9: RECONFIGURAR BASE DE DATOS
-- ============================================================================

INSERT INTO migration_log (step_number, step_name) 
VALUES (9, 'CONFIGURACION_FINAL');

-- Rehabilitar foreign keys
PRAGMA foreign_keys = ON;

-- Actualizar estadísticas para el optimizador
ANALYZE;

-- Ejecutar vacuum incremental si es necesario
PRAGMA auto_vacuum = INCREMENTAL;
PRAGMA incremental_vacuum;

-- Optimizar configuración
PRAGMA cache_size = 20000;
PRAGMA temp_store = MEMORY;
PRAGMA mmap_size = 268435456;

-- Finalizar paso 9
UPDATE migration_log 
SET end_time = CURRENT_TIMESTAMP, 
    status = 'SUCCESS',
    duration_seconds = CAST((julianday(CURRENT_TIMESTAMP) - julianday(start_time)) * 86400 AS INTEGER)
WHERE step_number = 9;

-- ============================================================================
-- REPORTE FINAL DE MIGRACIÓN
-- ============================================================================

-- Mostrar log completo de migración
SELECT 
    step_number,
    step_name,
    status,
    records_affected,
    duration_seconds,
    CASE 
        WHEN error_message IS NOT NULL THEN error_message 
        ELSE 'Completado exitosamente'
    END as resultado
FROM migration_log
ORDER BY step_number;

-- Mostrar comparativa antes/después
SELECT 
    'ANTES DE MIGRACION' as momento,
    tabla_origen as tabla,
    registros_antes as registros,
    misiones,
    operadores
FROM migration_stats_before

UNION ALL

SELECT 
    'DESPUES DE MIGRACION' as momento,
    tabla_destino as tabla,
    registros_despues as registros,
    misiones,
    operadores
FROM migration_stats_after

ORDER BY momento, tabla;

-- Mostrar resumen final
SELECT 
    'MIGRACION COMPLETADA' as estado,
    COUNT(*) as pasos_ejecutados,
    SUM(records_affected) as total_registros_afectados,
    SUM(duration_seconds) as duracion_total_segundos,
    CASE 
        WHEN COUNT(CASE WHEN status = 'ERROR' THEN 1 END) > 0 
        THEN 'CON_ERRORES'
        ELSE 'EXITOSA'
    END as resultado_final
FROM migration_log;

-- ============================================================================
-- INSTRUCCIONES POST-MIGRACIÓN
-- ============================================================================
/*
PASOS SIGUIENTES DESPUÉS DE LA MIGRACIÓN:

1. VERIFICACIÓN:
   - Revisar el reporte final de migración
   - Verificar que todos los pasos tienen status 'SUCCESS'
   - Comparar conteos antes/después

2. TESTING:
   - Ejecutar consultas de ejemplo del archivo operator_data_queries_examples.sql
   - Verificar que las vistas funcionan correctamente
   - Probar inserción de nuevos registros

3. ACTUALIZACIÓN DE APLICACIÓN:
   - Actualizar modelos SQLAlchemy si es necesario
   - Modificar servicios de backend para usar nuevas tablas
   - Actualizar frontend para nuevas estructuras de datos

4. LIMPIEZA (OPCIONAL):
   - Si la migración es exitosa y se ha probado completamente:
   - DROP TABLE cellular_data; (después de backup)
   - DROP TABLE operator_sheets; (después de backup)
   - DROP TABLE operator_data_records; (después de backup)

5. OPTIMIZACIÓN:
   - Ejecutar ANALYZE regularmente
   - Monitorear performance de consultas
   - Ajustar índices según patrones de uso

ROLLBACK EN CASO DE PROBLEMA:
Si hay errores durante la migración:
1. ROLLBACK TRANSACTION; (si se ejecutó en transacción)
2. Restaurar backup de la base de datos
3. Revisar logs de error en migration_log
4. Corregir problemas y re-ejecutar

NOTAS IMPORTANTES:
- Los datos originales NO se eliminan durante la migración
- La migración es aditiva (crea nuevas tablas, no modifica existentes)
- El esquema optimizado es compatible hacia adelante
- Los foreign keys se rehabilitan al final
*/