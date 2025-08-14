-- ============================================================================
-- MIGRACIÓN: Cambiar validación de duplicados de global a por misión
-- ============================================================================
-- Esta migración permite que el mismo archivo (checksum) pueda existir en 
-- diferentes misiones, pero mantiene la prevención de duplicados dentro de 
-- la misma misión.

-- PASO 1: Crear nueva tabla temporal con el constraint correcto
CREATE TABLE operator_data_sheets_new (
    -- Identificación primaria
    id TEXT PRIMARY KEY NOT NULL,
    mission_id TEXT NOT NULL,
    
    -- Información del archivo
    file_name TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    file_checksum TEXT NOT NULL,               -- Ya no UNIQUE global
    file_type TEXT NOT NULL,                   -- 'CELLULAR_DATA' | 'CALL_DATA'
    
    -- Información del operador
    operator TEXT NOT NULL,                    -- 'CLARO' | 'MOVISTAR' | 'TIGO' | 'WOM'
    format_version TEXT NOT NULL DEFAULT '1.0', -- Versión del formato de datos
    
    -- Estado de procesamiento
    processing_status TEXT NOT NULL DEFAULT 'PENDING',
    processing_start_time TIMESTAMP,
    processing_end_time TIMESTAMP,
    records_processed INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    error_message TEXT,
    
    -- Metadatos de carga
    uploaded_by TEXT NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Validaciones
    CHECK (processing_status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')),
    CHECK (file_type IN ('CELLULAR_DATA', 'CALL_DATA')),
    CHECK (operator IN ('CLARO', 'MOVISTAR', 'TIGO', 'WOM')),
    CHECK (file_size_bytes > 0),
    CHECK (records_processed >= 0),
    CHECK (records_failed >= 0),
    CHECK (length(trim(file_name)) > 0),
    CHECK (length(trim(file_checksum)) = 64), -- SHA256 length
    CHECK (length(trim(uploaded_by)) > 0),
    
    -- Constraint único compuesto: mismo archivo solo una vez por misión
    UNIQUE (file_checksum, mission_id),
    
    -- Claves foráneas
    FOREIGN KEY (mission_id) REFERENCES missions(id) ON DELETE CASCADE
);

-- PASO 2: Copiar datos existentes
INSERT INTO operator_data_sheets_new 
SELECT * FROM operator_data_sheets;

-- PASO 3: Renombrar tablas
DROP TABLE operator_data_sheets;
ALTER TABLE operator_data_sheets_new RENAME TO operator_data_sheets;

-- PASO 4: Recrear índices
CREATE INDEX idx_operator_sheets_mission_operator ON operator_data_sheets(mission_id, operator);
CREATE INDEX idx_operator_sheets_checksum ON operator_data_sheets(file_checksum);
CREATE INDEX idx_operator_sheets_status ON operator_data_sheets(processing_status);
CREATE INDEX idx_operator_sheets_upload_time ON operator_data_sheets(uploaded_at);
CREATE INDEX idx_operator_sheets_processing_time ON operator_data_sheets(processing_start_time, processing_end_time);
CREATE INDEX idx_operator_sheets_mission_checksum ON operator_data_sheets(mission_id, file_checksum);

-- PASO 5: Recrear triggers
CREATE TRIGGER trg_operator_sheets_updated_at
    AFTER UPDATE ON operator_data_sheets
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE operator_data_sheets 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- ============================================================================
-- VERIFICACIÓN POST-MIGRACIÓN
-- ============================================================================

-- Verificar que no hay duplicados por misión
SELECT 
    mission_id,
    file_checksum,
    COUNT(*) as duplicates
FROM operator_data_sheets 
GROUP BY mission_id, file_checksum
HAVING COUNT(*) > 1;

-- Resultado esperado: 0 filas (sin duplicados por misión)