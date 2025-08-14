-- ============================================================================
-- KRONOS - Esquema Optimizado para Módulo de Datos de Operadores Celulares
-- ============================================================================
-- SQLite Schema diseñado específicamente para el procesamiento eficiente de
-- datos de operadores celulares con soporte para:
-- 
-- ✓ 4 Operadores: CLARO, MOVISTAR, TIGO, WOM
-- ✓ Procesamiento atómico de archivos (todo o nada)
-- ✓ Prevención de duplicados mediante checksum
-- ✓ Soporte para archivos hasta 20MB con miles de registros
-- ✓ Auditoría completa y logs de procesamiento
-- ✓ Normalización avanzada con schema unificado
-- ✓ Índices optimizados para consultas frecuentes
-- ✓ Integridad referencial estricta
-- ============================================================================

-- Habilitar foreign keys y configuración optimizada
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 20000;      -- 20MB cache para archivos grandes
PRAGMA temp_store = MEMORY;
PRAGMA mmap_size = 268435456;   -- 256MB memory mapping
PRAGMA optimize;

-- ============================================================================
-- TABLA: operator_data_sheets
-- ============================================================================
-- Metadatos de archivos cargados por operador
-- Reemplaza y optimiza la tabla operator_sheets existente
CREATE TABLE operator_data_sheets (
    -- Identificación primaria
    id TEXT PRIMARY KEY NOT NULL,
    mission_id TEXT NOT NULL,
    
    -- Información del archivo
    file_name TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    file_checksum TEXT NOT NULL UNIQUE,        -- SHA256 para prevenir duplicados
    file_type TEXT NOT NULL,                   -- 'CELLULAR_DATA' | 'CALL_DATA'
    
    -- Información del operador
    operator TEXT NOT NULL,                    -- 'CLARO' | 'MOVISTAR' | 'TIGO' | 'WOM'
    operator_file_format TEXT NOT NULL,       -- Formato específico del archivo
    
    -- Estado de procesamiento
    processing_status TEXT NOT NULL DEFAULT 'PENDING', -- 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'
    records_processed INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    processing_start_time DATETIME,
    processing_end_time DATETIME,
    processing_duration_seconds INTEGER,
    error_details TEXT,
    
    -- Auditoría
    uploaded_by TEXT NOT NULL,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Relaciones
    FOREIGN KEY (mission_id) REFERENCES missions(id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE RESTRICT,
    
    -- Validaciones
    CHECK (length(trim(file_name)) > 0),
    CHECK (file_size_bytes > 0 AND file_size_bytes <= 20971520), -- Max 20MB
    CHECK (length(file_checksum) = 64), -- SHA256 hex length
    CHECK (file_type IN ('CELLULAR_DATA', 'CALL_DATA')),
    CHECK (operator IN ('CLARO', 'MOVISTAR', 'TIGO', 'WOM')),
    CHECK (processing_status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')),
    CHECK (records_processed >= 0),
    CHECK (records_failed >= 0),
    CHECK (processing_start_time IS NULL OR processing_end_time IS NULL OR processing_start_time <= processing_end_time)
);

-- ============================================================================
-- TABLA: operator_cellular_data
-- ============================================================================
-- Datos celulares normalizados de todos los operadores
-- Esquema unificado optimizado para análisis y búsquedas
CREATE TABLE operator_cellular_data (
    -- Identificación
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_upload_id TEXT NOT NULL,
    mission_id TEXT NOT NULL,
    
    -- Datos normalizados comunes
    operator TEXT NOT NULL,
    numero_telefono TEXT NOT NULL,
    
    -- Información temporal
    fecha_hora_inicio DATETIME NOT NULL,
    fecha_hora_fin DATETIME,
    duracion_segundos INTEGER,
    
    -- Información de celda
    celda_id TEXT NOT NULL,
    lac_tac TEXT,                              -- Location Area Code / Tracking Area Code
    
    -- Datos de tráfico (en bytes)
    trafico_subida_bytes BIGINT DEFAULT 0,
    trafico_bajada_bytes BIGINT DEFAULT 0,
    trafico_total_bytes BIGINT GENERATED ALWAYS AS (trafico_subida_bytes + trafico_bajada_bytes) STORED,
    
    -- Información geográfica
    latitud REAL,
    longitud REAL,
    
    -- Información técnica
    tecnologia TEXT DEFAULT 'UNKNOWN',          -- 'GSM', '3G', 'LTE', '5G', etc.
    tipo_conexion TEXT DEFAULT 'DATOS',         -- 'DATOS', 'SMS', 'MMS'
    calidad_senal INTEGER,                      -- RSSI en dBm (valores negativos)
    
    -- Campos específicos del operador (JSON)
    operator_specific_data TEXT,               -- JSON con campos únicos por operador
    
    -- Control de duplicados y auditoría
    record_hash TEXT NOT NULL,                 -- Hash único para detectar duplicados
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Relaciones
    FOREIGN KEY (file_upload_id) REFERENCES operator_data_sheets(id) ON DELETE CASCADE,
    FOREIGN KEY (mission_id) REFERENCES missions(id) ON DELETE CASCADE,
    
    -- Validaciones geográficas y técnicas
    CHECK (latitud IS NULL OR (latitud >= -90.0 AND latitud <= 90.0)),
    CHECK (longitud IS NULL OR (longitud >= -180.0 AND longitud <= 180.0)),
    CHECK (duracion_segundos IS NULL OR duracion_segundos >= 0),
    CHECK (trafico_subida_bytes >= 0),
    CHECK (trafico_bajada_bytes >= 0),
    CHECK (calidad_senal IS NULL OR calidad_senal <= 0), -- dBm values son negativos
    
    -- Validaciones de formato
    CHECK (length(trim(numero_telefono)) >= 10),
    CHECK (numero_telefono GLOB '[0-9]*'),
    CHECK (length(trim(celda_id)) > 0),
    CHECK (length(trim(operator)) > 0),
    CHECK (tecnologia IN ('GSM', '2G', 'UMTS', '3G', 'LTE', '4G', '5G NR', '5G', 'UNKNOWN')),
    CHECK (tipo_conexion IN ('DATOS', 'SMS', 'MMS')),
    CHECK (operator_specific_data IS NULL OR json_valid(operator_specific_data) = 1),
    
    -- Constraint único para prevenir duplicados exactos
    UNIQUE (file_upload_id, record_hash)
);

-- ============================================================================
-- TABLA: operator_call_data
-- ============================================================================
-- Datos de llamadas normalizados de todos los operadores
-- Diseñada para análisis de patrones de comunicación
CREATE TABLE operator_call_data (
    -- Identificación
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_upload_id TEXT NOT NULL,
    mission_id TEXT NOT NULL,
    
    -- Datos normalizados comunes
    operator TEXT NOT NULL,
    tipo_llamada TEXT NOT NULL,               -- 'ENTRANTE', 'SALIENTE', 'MIXTA'
    
    -- Números involucrados
    numero_origen TEXT NOT NULL,
    numero_destino TEXT NOT NULL,
    numero_objetivo TEXT NOT NULL,            -- El número de interés investigativo
    
    -- Información temporal
    fecha_hora_llamada DATETIME NOT NULL,
    duracion_segundos INTEGER DEFAULT 0,
    
    -- Información de celdas
    celda_origen TEXT,
    celda_destino TEXT,
    celda_objetivo TEXT,                      -- Celda del número objetivo
    
    -- Información geográfica
    latitud_origen REAL,
    longitud_origen REAL,
    latitud_destino REAL,
    longitud_destino REAL,
    
    -- Información técnica
    tecnologia TEXT DEFAULT 'UNKNOWN',
    tipo_trafico TEXT DEFAULT 'VOZ',          -- 'VOZ', 'SMS', 'MMS', 'DATOS'
    estado_llamada TEXT DEFAULT 'COMPLETADA', -- 'COMPLETADA', 'NO_CONTESTADA', 'OCUPADO', 'ERROR'
    
    -- Campos específicos del operador (JSON)
    operator_specific_data TEXT,
    
    -- Control de duplicados y auditoría
    record_hash TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Relaciones
    FOREIGN KEY (file_upload_id) REFERENCES operator_data_sheets(id) ON DELETE CASCADE,
    FOREIGN KEY (mission_id) REFERENCES missions(id) ON DELETE CASCADE,
    
    -- Validaciones
    CHECK (tipo_llamada IN ('ENTRANTE', 'SALIENTE', 'MIXTA')),
    CHECK (duracion_segundos >= 0),
    CHECK (length(trim(numero_origen)) >= 7),
    CHECK (length(trim(numero_destino)) >= 7),
    CHECK (length(trim(numero_objetivo)) >= 7),
    CHECK (numero_origen GLOB '[0-9]*'),
    CHECK (numero_destino GLOB '[0-9]*'),
    CHECK (numero_objetivo GLOB '[0-9]*'),
    
    -- Validaciones geográficas
    CHECK (latitud_origen IS NULL OR (latitud_origen >= -90.0 AND latitud_origen <= 90.0)),
    CHECK (longitud_origen IS NULL OR (longitud_origen >= -180.0 AND longitud_origen <= 180.0)),
    CHECK (latitud_destino IS NULL OR (latitud_destino >= -90.0 AND latitud_destino <= 90.0)),
    CHECK (longitud_destino IS NULL OR (longitud_destino >= -180.0 AND longitud_destino <= 180.0)),
    
    -- Validaciones técnicas
    CHECK (tecnologia IN ('GSM', '2G', 'UMTS', '3G', 'LTE', '4G', '5G NR', '5G', 'UNKNOWN')),
    CHECK (tipo_trafico IN ('VOZ', 'SMS', 'MMS', 'DATOS')),
    CHECK (estado_llamada IN ('COMPLETADA', 'NO_CONTESTADA', 'OCUPADO', 'ERROR', 'TRANSFERIDA')),
    CHECK (operator_specific_data IS NULL OR json_valid(operator_specific_data) = 1),
    
    -- Constraint único para prevenir duplicados
    UNIQUE (file_upload_id, record_hash)
);

-- ============================================================================
-- TABLA: file_processing_logs
-- ============================================================================
-- Logs detallados del procesamiento de archivos
-- Auditoría completa para debugging y monitoreo
CREATE TABLE file_processing_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_upload_id TEXT NOT NULL,
    
    -- Información del log
    log_level TEXT NOT NULL,                  -- 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    log_message TEXT NOT NULL,
    log_details TEXT,                         -- JSON con detalles adicionales
    
    -- Contexto del procesamiento
    processing_step TEXT NOT NULL,           -- 'VALIDATION', 'PARSING', 'TRANSFORMATION', 'INSERTION', 'CLEANUP'
    record_number INTEGER,                   -- Número de registro que causó el log (si aplica)
    error_code TEXT,                         -- Código de error específico
    
    -- Información de performance
    execution_time_ms INTEGER,               -- Tiempo de ejecución del paso
    memory_usage_mb REAL,                    -- Uso de memoria durante el procesamiento
    
    -- Timestamp
    logged_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Relaciones
    FOREIGN KEY (file_upload_id) REFERENCES operator_data_sheets(id) ON DELETE CASCADE,
    
    -- Validaciones
    CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    CHECK (length(trim(log_message)) > 0),
    CHECK (length(trim(processing_step)) > 0),
    CHECK (record_number IS NULL OR record_number > 0),
    CHECK (execution_time_ms IS NULL OR execution_time_ms >= 0),
    CHECK (memory_usage_mb IS NULL OR memory_usage_mb >= 0),
    CHECK (log_details IS NULL OR json_valid(log_details) = 1)
);

-- ============================================================================
-- TABLA: operator_data_audit
-- ============================================================================
-- Auditoría de cambios en datos de operadores
-- Rastrea modificaciones para compliance y debugging
CREATE TABLE operator_data_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Identificación del registro auditado
    table_name TEXT NOT NULL,                -- 'operator_cellular_data' | 'operator_call_data'
    record_id INTEGER NOT NULL,             -- ID del registro modificado
    
    -- Información de la operación
    operation_type TEXT NOT NULL,           -- 'INSERT', 'UPDATE', 'DELETE'
    field_name TEXT,                        -- Campo modificado (para UPDATE)
    old_value TEXT,                         -- Valor anterior (para UPDATE/DELETE)
    new_value TEXT,                         -- Valor nuevo (para INSERT/UPDATE)
    
    -- Contexto de la modificación
    modified_by TEXT NOT NULL,              -- Usuario que realizó el cambio
    modification_reason TEXT,               -- Razón del cambio
    batch_operation_id TEXT,                -- ID de operación en lote (si aplica)
    
    -- Información adicional
    user_agent TEXT,                        -- Cliente que realizó la operación
    ip_address TEXT,                        -- IP de origen
    session_id TEXT,                        -- ID de sesión
    
    -- Timestamp
    audited_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Relaciones
    FOREIGN KEY (modified_by) REFERENCES users(id) ON DELETE RESTRICT,
    
    -- Validaciones
    CHECK (table_name IN ('operator_cellular_data', 'operator_call_data', 'operator_data_sheets')),
    CHECK (operation_type IN ('INSERT', 'UPDATE', 'DELETE')),
    CHECK (record_id > 0),
    CHECK (length(trim(modified_by)) > 0)
);

-- ============================================================================
-- TABLA: operator_cell_registry
-- ============================================================================
-- Registro consolidado de celdas por operador
-- Cache optimizada para búsquedas geoespaciales rápidas
CREATE TABLE operator_cell_registry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Identificación de celda
    operator TEXT NOT NULL,
    celda_id TEXT NOT NULL,
    lac_tac TEXT,
    
    -- Información geográfica
    latitud REAL,
    longitud REAL,
    ciudad TEXT,
    departamento TEXT,
    
    -- Información técnica
    tecnologia_predominante TEXT,           -- Tecnología más usada en esta celda
    frecuencia_uso INTEGER DEFAULT 1,      -- Cantidad de veces vista
    calidad_promedio_senal REAL,          -- RSSI promedio en dBm
    
    -- Estadísticas agregadas
    trafico_promedio_mb_dia REAL,         -- Tráfico promedio por día
    usuarios_unicos_dia INTEGER,          -- Usuarios únicos por día promedio
    llamadas_promedio_dia INTEGER,        -- Llamadas promedio por día
    
    -- Metadatos
    primera_deteccion DATETIME,           -- Primera vez que se vio esta celda
    ultima_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Validaciones
    CHECK (operator IN ('CLARO', 'MOVISTAR', 'TIGO', 'WOM')),
    CHECK (length(trim(celda_id)) > 0),
    CHECK (latitud IS NULL OR (latitud >= -90.0 AND latitud <= 90.0)),
    CHECK (longitud IS NULL OR (longitud >= -180.0 AND longitud <= 180.0)),
    CHECK (frecuencia_uso > 0),
    CHECK (calidad_promedio_senal IS NULL OR calidad_promedio_senal <= 0),
    CHECK (trafico_promedio_mb_dia IS NULL OR trafico_promedio_mb_dia >= 0),
    CHECK (usuarios_unicos_dia IS NULL OR usuarios_unicos_dia >= 0),
    CHECK (llamadas_promedio_dia IS NULL OR llamadas_promedio_dia >= 0),
    
    -- Constraint único por operador y celda
    UNIQUE (operator, celda_id)
);

-- ============================================================================
-- ÍNDICES OPTIMIZADOS PARA CONSULTAS FRECUENTES
-- ============================================================================

-- Índices para operator_data_sheets
CREATE INDEX idx_operator_sheets_mission_operator ON operator_data_sheets(mission_id, operator);
CREATE INDEX idx_operator_sheets_checksum ON operator_data_sheets(file_checksum);
CREATE INDEX idx_operator_sheets_status ON operator_data_sheets(processing_status);
CREATE INDEX idx_operator_sheets_upload_time ON operator_data_sheets(uploaded_at);
CREATE INDEX idx_operator_sheets_processing_time ON operator_data_sheets(processing_start_time, processing_end_time);

-- Índices para operator_cellular_data (optimizados para análisis de objetivos)
CREATE INDEX idx_cellular_mission_operator ON operator_cellular_data(mission_id, operator);
CREATE INDEX idx_cellular_numero_telefono ON operator_cellular_data(numero_telefono);
CREATE INDEX idx_cellular_numero_mission ON operator_cellular_data(numero_telefono, mission_id);
CREATE INDEX idx_cellular_fecha_hora ON operator_cellular_data(fecha_hora_inicio);
CREATE INDEX idx_cellular_celda_id ON operator_cellular_data(celda_id);
CREATE INDEX idx_cellular_trafico_total ON operator_cellular_data(trafico_total_bytes);
CREATE INDEX idx_cellular_tecnologia ON operator_cellular_data(tecnologia);
CREATE INDEX idx_cellular_geolocation ON operator_cellular_data(latitud, longitud) WHERE latitud IS NOT NULL AND longitud IS NOT NULL;

-- Índices compuestos para análisis temporal
CREATE INDEX idx_cellular_numero_fecha ON operator_cellular_data(numero_telefono, fecha_hora_inicio);
CREATE INDEX idx_cellular_celda_fecha ON operator_cellular_data(celda_id, fecha_hora_inicio);
CREATE INDEX idx_cellular_operator_fecha ON operator_cellular_data(operator, fecha_hora_inicio);

-- Índices para operator_call_data (optimizados para análisis de comunicaciones)
CREATE INDEX idx_calls_mission_operator ON operator_call_data(mission_id, operator);
CREATE INDEX idx_calls_numero_objetivo ON operator_call_data(numero_objetivo);
CREATE INDEX idx_calls_numero_origen ON operator_call_data(numero_origen);
CREATE INDEX idx_calls_numero_destino ON operator_call_data(numero_destino);
CREATE INDEX idx_calls_objetivo_mission ON operator_call_data(numero_objetivo, mission_id);
CREATE INDEX idx_calls_fecha_hora ON operator_call_data(fecha_hora_llamada);
CREATE INDEX idx_calls_duracion ON operator_call_data(duracion_segundos);
CREATE INDEX idx_calls_tipo ON operator_call_data(tipo_llamada);
CREATE INDEX idx_calls_celda_origen ON operator_call_data(celda_origen);

-- Índices compuestos para análisis de patrones
CREATE INDEX idx_calls_objetivo_fecha ON operator_call_data(numero_objetivo, fecha_hora_llamada);
CREATE INDEX idx_calls_origen_destino ON operator_call_data(numero_origen, numero_destino);
CREATE INDEX idx_calls_tipo_fecha ON operator_call_data(tipo_llamada, fecha_hora_llamada);

-- Índices para file_processing_logs
CREATE INDEX idx_logs_file_upload ON file_processing_logs(file_upload_id);
CREATE INDEX idx_logs_level_time ON file_processing_logs(log_level, logged_at);
CREATE INDEX idx_logs_step ON file_processing_logs(processing_step);
CREATE INDEX idx_logs_error_code ON file_processing_logs(error_code) WHERE error_code IS NOT NULL;

-- Índices para operator_data_audit
CREATE INDEX idx_audit_table_record ON operator_data_audit(table_name, record_id);
CREATE INDEX idx_audit_modified_by ON operator_data_audit(modified_by);
CREATE INDEX idx_audit_time ON operator_data_audit(audited_at);
CREATE INDEX idx_audit_operation ON operator_data_audit(operation_type);
CREATE INDEX idx_audit_batch ON operator_data_audit(batch_operation_id) WHERE batch_operation_id IS NOT NULL;

-- Índices para operator_cell_registry
CREATE INDEX idx_cell_registry_operator_celda ON operator_cell_registry(operator, celda_id);
CREATE INDEX idx_cell_registry_geolocation ON operator_cell_registry(latitud, longitud) WHERE latitud IS NOT NULL AND longitud IS NOT NULL;
CREATE INDEX idx_cell_registry_frecuencia ON operator_cell_registry(frecuencia_uso);
CREATE INDEX idx_cell_registry_tecnologia ON operator_cell_registry(tecnologia_predominante);
CREATE INDEX idx_cell_registry_ciudad ON operator_cell_registry(ciudad);

-- ============================================================================
-- TRIGGERS PARA AUDITORÍA Y MANTENIMIENTO AUTOMÁTICO
-- ============================================================================

-- Trigger para updated_at en operator_data_sheets
CREATE TRIGGER trg_operator_sheets_updated_at
    AFTER UPDATE ON operator_data_sheets
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE operator_data_sheets 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- Trigger para auditoría de operator_cellular_data
CREATE TRIGGER trg_cellular_data_audit_insert
    AFTER INSERT ON operator_cellular_data
    FOR EACH ROW
BEGIN
    INSERT INTO operator_data_audit (
        table_name, record_id, operation_type,
        modified_by, audited_at
    ) VALUES (
        'operator_cellular_data', NEW.id, 'INSERT',
        'SYSTEM', CURRENT_TIMESTAMP
    );
END;

CREATE TRIGGER trg_cellular_data_audit_update
    AFTER UPDATE ON operator_cellular_data
    FOR EACH ROW
BEGIN
    INSERT INTO operator_data_audit (
        table_name, record_id, operation_type,
        field_name, old_value, new_value,
        modified_by, audited_at
    ) VALUES (
        'operator_cellular_data', NEW.id, 'UPDATE',
        'BULK_UPDATE', 
        json_object('old_record', json_object(
            'numero_telefono', OLD.numero_telefono,
            'fecha_hora_inicio', OLD.fecha_hora_inicio,
            'celda_id', OLD.celda_id
        )),
        json_object('new_record', json_object(
            'numero_telefono', NEW.numero_telefono,
            'fecha_hora_inicio', NEW.fecha_hora_inicio,
            'celda_id', NEW.celda_id
        )),
        'SYSTEM', CURRENT_TIMESTAMP
    );
END;

-- Trigger para mantener operator_cell_registry actualizado
CREATE TRIGGER trg_update_cell_registry_cellular
    AFTER INSERT ON operator_cellular_data
    FOR EACH ROW
    WHEN NEW.celda_id IS NOT NULL
BEGIN
    INSERT OR REPLACE INTO operator_cell_registry (
        operator, celda_id, lac_tac, latitud, longitud,
        tecnologia_predominante, frecuencia_uso,
        primera_deteccion, ultima_actualizacion
    ) VALUES (
        NEW.operator, NEW.celda_id, NEW.lac_tac,
        NEW.latitud, NEW.longitud, NEW.tecnologia,
        COALESCE((SELECT frecuencia_uso + 1 FROM operator_cell_registry 
                  WHERE operator = NEW.operator AND celda_id = NEW.celda_id), 1),
        COALESCE((SELECT primera_deteccion FROM operator_cell_registry 
                  WHERE operator = NEW.operator AND celda_id = NEW.celda_id), 
                 NEW.fecha_hora_inicio),
        CURRENT_TIMESTAMP
    );
END;

-- Trigger para mantener estadísticas en operator_data_sheets
CREATE TRIGGER trg_update_processing_stats_cellular
    AFTER INSERT ON operator_cellular_data
    FOR EACH ROW
BEGIN
    UPDATE operator_data_sheets 
    SET records_processed = records_processed + 1,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.file_upload_id;
END;

CREATE TRIGGER trg_update_processing_stats_calls
    AFTER INSERT ON operator_call_data
    FOR EACH ROW
BEGIN
    UPDATE operator_data_sheets 
    SET records_processed = records_processed + 1,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.file_upload_id;
END;

-- ============================================================================
-- VISTAS PARA CONSULTAS COMUNES Y REPORTES
-- ============================================================================

-- Vista consolidada de actividad por número objetivo
CREATE VIEW v_numero_actividad_consolidada AS
SELECT 
    cd.mission_id,
    cd.numero_telefono,
    cd.operator,
    
    -- Estadísticas de datos
    COUNT(cd.id) as sesiones_datos,
    SUM(cd.trafico_total_bytes) as trafico_total_bytes,
    ROUND(AVG(cd.trafico_total_bytes), 2) as trafico_promedio_bytes,
    COUNT(DISTINCT cd.celda_id) as celdas_utilizadas_datos,
    MIN(cd.fecha_hora_inicio) as primera_actividad_datos,
    MAX(COALESCE(cd.fecha_hora_fin, cd.fecha_hora_inicio)) as ultima_actividad_datos,
    
    -- Estadísticas de llamadas
    (SELECT COUNT(*) FROM operator_call_data ocall 
     WHERE ocall.numero_objetivo = cd.numero_telefono 
     AND ocall.mission_id = cd.mission_id 
     AND ocall.operator = cd.operator) as total_llamadas,
    
    (SELECT COUNT(DISTINCT celda_origen) FROM operator_call_data ocall 
     WHERE ocall.numero_objetivo = cd.numero_telefono 
     AND ocall.mission_id = cd.mission_id 
     AND ocall.operator = cd.operator) as celdas_utilizadas_llamadas,
    
    -- Ubicaciones más frecuentes
    (SELECT GROUP_CONCAT(DISTINCT cd2.celda_id, '|') 
     FROM operator_cellular_data cd2 
     WHERE cd2.numero_telefono = cd.numero_telefono 
     AND cd2.mission_id = cd.mission_id 
     AND cd2.operator = cd.operator 
     GROUP BY cd2.celda_id 
     ORDER BY COUNT(*) DESC LIMIT 3) as celdas_mas_frecuentes,
     
    -- Tecnologías utilizadas
    GROUP_CONCAT(DISTINCT cd.tecnologia) as tecnologias_utilizadas

FROM operator_cellular_data cd
GROUP BY cd.mission_id, cd.numero_telefono, cd.operator;

-- Vista de estadísticas por operador y misión
CREATE VIEW v_operator_mission_stats AS
SELECT 
    ods.mission_id,
    ods.operator,
    
    -- Estadísticas de archivos
    COUNT(DISTINCT ods.id) as archivos_procesados,
    SUM(ods.records_processed) as total_registros,
    SUM(ods.file_size_bytes) as total_bytes_procesados,
    ROUND(AVG(ods.processing_duration_seconds), 2) as tiempo_promedio_procesamiento,
    
    -- Estadísticas de datos celulares
    (SELECT COUNT(*) FROM operator_cellular_data ocd 
     WHERE ocd.mission_id = ods.mission_id AND ocd.operator = ods.operator) as registros_datos,
    (SELECT COUNT(DISTINCT numero_telefono) FROM operator_cellular_data ocd 
     WHERE ocd.mission_id = ods.mission_id AND ocd.operator = ods.operator) as usuarios_unicos_datos,
    (SELECT COUNT(DISTINCT celda_id) FROM operator_cellular_data ocd 
     WHERE ocd.mission_id = ods.mission_id AND ocd.operator = ods.operator) as celdas_diferentes_datos,
    
    -- Estadísticas de llamadas
    (SELECT COUNT(*) FROM operator_call_data ocall 
     WHERE ocall.mission_id = ods.mission_id AND ocall.operator = ods.operator) as registros_llamadas,
    (SELECT COUNT(DISTINCT numero_objetivo) FROM operator_call_data ocall 
     WHERE ocall.mission_id = ods.mission_id AND ocall.operator = ods.operator) as usuarios_unicos_llamadas,
    
    -- Período de tiempo cubierto
    (SELECT MIN(fecha_hora_inicio) FROM operator_cellular_data ocd 
     WHERE ocd.mission_id = ods.mission_id AND ocd.operator = ods.operator) as periodo_inicio,
    (SELECT MAX(COALESCE(fecha_hora_fin, fecha_hora_inicio)) FROM operator_cellular_data ocd 
     WHERE ocd.mission_id = ods.mission_id AND ocd.operator = ods.operator) as periodo_fin

FROM operator_data_sheets ods
WHERE ods.processing_status = 'COMPLETED'
GROUP BY ods.mission_id, ods.operator;

-- Vista de calidad de datos por archivo
CREATE VIEW v_data_quality_report AS
SELECT 
    ods.id as file_upload_id,
    ods.file_name,
    ods.operator,
    ods.processing_status,
    ods.records_processed,
    ods.records_failed,
    
    -- Métricas de calidad
    ROUND((CAST(ods.records_processed AS REAL) / 
           NULLIF(ods.records_processed + ods.records_failed, 0)) * 100, 2) as success_rate_percent,
    
    -- Problemas detectados en logs
    (SELECT COUNT(*) FROM file_processing_logs fpl 
     WHERE fpl.file_upload_id = ods.id AND fpl.log_level = 'ERROR') as error_count,
    (SELECT COUNT(*) FROM file_processing_logs fpl 
     WHERE fpl.file_upload_id = ods.id AND fpl.log_level = 'WARNING') as warning_count,
    
    -- Validaciones específicas de datos celulares
    (SELECT COUNT(*) FROM operator_cellular_data ocd 
     WHERE ocd.file_upload_id = ods.id AND ocd.latitud IS NULL) as registros_sin_coordenadas,
    (SELECT COUNT(*) FROM operator_cellular_data ocd 
     WHERE ocd.file_upload_id = ods.id AND ocd.trafico_total_bytes = 0) as registros_sin_trafico,
    
    -- Performance
    ods.processing_duration_seconds,
    ROUND(CAST(ods.records_processed AS REAL) / 
          NULLIF(ods.processing_duration_seconds, 0), 2) as records_per_second,
    
    -- Timestamps
    ods.uploaded_at,
    ods.processing_start_time,
    ods.processing_end_time

FROM operator_data_sheets ods;

-- ============================================================================
-- FUNCIONES DE UTILIDAD (VIA QUERIES PREPARADOS)
-- ============================================================================

-- Template para búsqueda rápida por número telefónico
-- Uso: BIND :numero_telefono, :mission_id
/*
SELECT 
    'DATOS' as tipo_actividad,
    fecha_hora_inicio as timestamp_actividad,
    operator, celda_id, trafico_total_bytes as valor_numerico,
    'Sesión de datos: ' || ROUND(trafico_total_bytes/1024.0/1024.0, 2) || ' MB' as descripcion
FROM operator_cellular_data 
WHERE numero_telefono = :numero_telefono 
  AND mission_id = :mission_id
UNION ALL
SELECT 
    'LLAMADA' as tipo_actividad,
    fecha_hora_llamada as timestamp_actividad,
    operator, celda_objetivo as celda_id, duracion_segundos as valor_numerico,
    tipo_llamada || ' - Duración: ' || duracion_segundos || 's' as descripcion
FROM operator_call_data 
WHERE numero_objetivo = :numero_telefono 
  AND mission_id = :mission_id
ORDER BY timestamp_actividad DESC;
*/

-- Template para análisis de cobertura por zona geográfica
-- Uso: BIND :lat_min, :lat_max, :lon_min, :lon_max, :mission_id
/*
SELECT 
    operator,
    COUNT(DISTINCT celda_id) as celdas_en_zona,
    COUNT(DISTINCT numero_telefono) as usuarios_activos,
    COUNT(*) as total_registros,
    ROUND(AVG(trafico_total_bytes), 2) as trafico_promedio,
    MIN(fecha_hora_inicio) as periodo_inicio,
    MAX(fecha_hora_inicio) as periodo_fin
FROM operator_cellular_data 
WHERE mission_id = :mission_id
  AND latitud BETWEEN :lat_min AND :lat_max
  AND longitud BETWEEN :lon_min AND :lon_max
  AND latitud IS NOT NULL 
  AND longitud IS NOT NULL
GROUP BY operator
ORDER BY total_registros DESC;
*/

-- ============================================================================
-- CONFIGURACIÓN FINAL Y OPTIMIZACIONES
-- ============================================================================

-- Actualizar estadísticas para optimizador de consultas
ANALYZE;

-- Configurar auto-vacuum para mantener el tamaño de la BD
PRAGMA auto_vacuum = INCREMENTAL;

-- ============================================================================
-- DOCUMENTACIÓN DE USO
-- ============================================================================
/*
INSTRUCCIONES DE USO:

1. PROCESAMIENTO DE ARCHIVOS:
   - Crear registro en operator_data_sheets con status 'PENDING'
   - Calcular checksum SHA256 del archivo para prevenir duplicados
   - Cambiar status a 'PROCESSING' antes de empezar
   - Insertar datos en operator_cellular_data o operator_call_data
   - Actualizar status a 'COMPLETED' o 'FAILED'
   - Logs detallados en file_processing_logs

2. PREVENCIÓN DE DUPLICADOS:
   - Usar file_checksum en operator_data_sheets (único)
   - Usar record_hash en tablas de datos (calculado por archivo + contenido)
   - Constraint UNIQUE previene duplicados exactos

3. CONSULTAS DE PERFORMANCE:
   - Usar índices compuestos para consultas multi-campo
   - EXPLAIN QUERY PLAN para verificar uso de índices
   - Usar vistas materializadas para reportes complejos

4. MANTENIMIENTO:
   - VACUUM INCREMENTAL periódico
   - ANALYZE después de cargas grandes de datos
   - Limpieza de logs antiguos según políticas de retención

5. ESCALABILIDAD:
   - WAL mode permite lecturas concurrentes
   - Cache de 20MB para archivos grandes
   - Índices optimizados para consultas frecuentes

LIMITACIONES CONOCIDAS:
- Archivos máximo 20MB (modificable en CHECK constraint)
- SQLite single-writer (mitigado con WAL)
- JSON fields requieren funciones específicas para consultas complejas

CONSIDERACIONES DE SEGURIDAD:
- Foreign keys habilitadas para integridad referencial
- Validaciones estrictas en CHECK constraints
- Auditoría completa de cambios en operator_data_audit
*/