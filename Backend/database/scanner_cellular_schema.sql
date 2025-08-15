-- ============================================================================
-- KRONOS Scanner Cellular Data Schema - Optimized for SCANHUNTER Format
-- ============================================================================
-- Schema específicamente diseñado para datos de medición de scanner celular
-- Compatible con formato SCANHUNTER.xlsx y optimizado para consultas frecuentes
-- ============================================================================

-- Crear tabla principal para datos de scanner celular
-- Esta tabla reemplaza/mejora la tabla cellular_data existente
CREATE TABLE IF NOT EXISTS scanner_cellular_data (
    -- Identificación única
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id TEXT NOT NULL,
    
    -- Información del punto de medición (corresponde a columna 'Punto' en SCANHUNTER)
    punto TEXT NOT NULL,
    measurement_sequence INTEGER, -- Secuencia de medición para el mismo punto
    
    -- Coordenadas geográficas (Latitud/Longitud en SCANHUNTER)
    latitude REAL NOT NULL CHECK (latitude >= -90.0 AND latitude <= 90.0),
    longitude REAL NOT NULL CHECK (longitude >= -180.0 AND longitude <= 180.0),
    coordinate_precision INTEGER DEFAULT 6, -- Precisión de coordenadas (decimales)
    
    -- Información de red celular
    mnc_mcc TEXT NOT NULL CHECK (length(mnc_mcc) >= 5 AND mnc_mcc GLOB '[0-9]*'),
    operator_name TEXT NOT NULL CHECK (length(trim(operator_name)) > 0),
    operator_code TEXT, -- Código interno del operador (derivado de MNC+MCC)
    
    -- Métricas de señal (RSSI en SCANHUNTER)
    rssi_dbm INTEGER NOT NULL CHECK (rssi_dbm <= 0 AND rssi_dbm >= -150),
    signal_quality TEXT GENERATED ALWAYS AS (
        CASE 
            WHEN rssi_dbm >= -70 THEN 'Excelente'
            WHEN rssi_dbm >= -85 THEN 'Buena' 
            WHEN rssi_dbm >= -100 THEN 'Regular'
            ELSE 'Mala'
        END
    ) STORED,
    
    -- Información técnica de celda
    technology TEXT NOT NULL CHECK (
        technology IN ('GSM', 'UMTS', '3G', 'LTE', '4G', '5G NR', '5G', 'UNKNOWN')
    ),
    cell_id TEXT NOT NULL CHECK (length(trim(cell_id)) > 0),
    lac_tac TEXT CHECK (lac_tac IS NULL OR length(trim(lac_tac)) > 0),
    enb_id TEXT CHECK (enb_id IS NULL OR length(trim(enb_id)) > 0),
    
    -- Información de canal/frecuencia
    channel TEXT CHECK (channel IS NULL OR length(trim(channel)) > 0),
    frequency_band TEXT, -- Banda de frecuencia derivada (850, 900, 1800, 2100, etc.)
    
    -- Metadatos de medición
    comentario TEXT,
    measurement_timestamp DATETIME, -- Timestamp de la medición (si está disponible)
    
    -- Auditoría y procesamiento
    file_source TEXT, -- Nombre del archivo fuente (ej: SCANHUNTER.xlsx)
    processing_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_hash TEXT, -- Hash para detectar duplicados
    is_validated BOOLEAN DEFAULT 0, -- Flag para datos validados
    validation_errors TEXT, -- JSON con errores de validación
    
    -- Relaciones
    FOREIGN KEY (mission_id) REFERENCES missions(id) ON DELETE CASCADE
);

-- ============================================================================
-- ÍNDICES OPTIMIZADOS PARA CONSULTAS FRECUENTES
-- ============================================================================

-- Índice principal por misión (consulta más frecuente)
CREATE INDEX IF NOT EXISTS idx_scanner_cellular_mission 
ON scanner_cellular_data(mission_id);

-- Índices para análisis de cobertura
CREATE INDEX IF NOT EXISTS idx_scanner_cellular_operator_tech 
ON scanner_cellular_data(mission_id, operator_name, technology);

CREATE INDEX IF NOT EXISTS idx_scanner_cellular_signal_analysis 
ON scanner_cellular_data(mission_id, rssi_dbm, technology);

-- Índices geoespaciales para análisis de ubicación
CREATE INDEX IF NOT EXISTS idx_scanner_cellular_coordinates 
ON scanner_cellular_data(latitude, longitude);

CREATE INDEX IF NOT EXISTS idx_scanner_cellular_geo_operator 
ON scanner_cellular_data(latitude, longitude, operator_name);

-- Índices para búsqueda de celdas específicas
CREATE INDEX IF NOT EXISTS idx_scanner_cellular_cell_lookup 
ON scanner_cellular_data(cell_id, operator_name);

CREATE INDEX IF NOT EXISTS idx_scanner_cellular_lac_tac 
ON scanner_cellular_data(lac_tac, technology);

-- Índice compuesto para análisis de cobertura completo
CREATE INDEX IF NOT EXISTS idx_scanner_cellular_coverage_analysis 
ON scanner_cellular_data(mission_id, operator_name, technology, rssi_dbm, latitude, longitude);

-- Índice para detección de duplicados
CREATE INDEX IF NOT EXISTS idx_scanner_cellular_deduplication 
ON scanner_cellular_data(data_hash);

-- Índice para búsqueda por punto de medición
CREATE INDEX IF NOT EXISTS idx_scanner_cellular_punto 
ON scanner_cellular_data(mission_id, punto);

-- ============================================================================
-- VISTA PARA ANÁLISIS AGREGADO DE COBERTURA
-- ============================================================================

CREATE VIEW IF NOT EXISTS vw_scanner_coverage_summary AS
SELECT 
    mission_id,
    operator_name,
    technology,
    COUNT(*) as total_measurements,
    AVG(rssi_dbm) as avg_rssi,
    MIN(rssi_dbm) as min_rssi,
    MAX(rssi_dbm) as max_rssi,
    COUNT(DISTINCT punto) as unique_points,
    COUNT(DISTINCT cell_id) as unique_cells,
    SUM(CASE WHEN rssi_dbm >= -85 THEN 1 ELSE 0 END) as good_signal_count,
    SUM(CASE WHEN rssi_dbm < -100 THEN 1 ELSE 0 END) as poor_signal_count,
    MIN(latitude) as min_lat,
    MAX(latitude) as max_lat,
    MIN(longitude) as min_lon,
    MAX(longitude) as max_lon
FROM scanner_cellular_data
WHERE is_validated = 1
GROUP BY mission_id, operator_name, technology;

-- ============================================================================
-- VISTA PARA DETECCIÓN DE ANOMALÍAS EN MEDICIONES
-- ============================================================================

CREATE VIEW IF NOT EXISTS vw_scanner_anomalies AS
SELECT 
    scd.*,
    'RSSI_ANOMALY' as anomaly_type,
    'RSSI value outside expected range' as anomaly_description
FROM scanner_cellular_data scd
WHERE scd.rssi_dbm > -30 OR scd.rssi_dbm < -120

UNION ALL

SELECT 
    scd.*,
    'DUPLICATE_MEASUREMENT' as anomaly_type,
    'Potential duplicate measurement detected' as anomaly_description
FROM scanner_cellular_data scd
WHERE EXISTS (
    SELECT 1 FROM scanner_cellular_data scd2 
    WHERE scd2.id != scd.id 
    AND scd2.mission_id = scd.mission_id
    AND scd2.punto = scd.punto
    AND scd2.cell_id = scd.cell_id
    AND ABS(scd2.latitude - scd.latitude) < 0.0001
    AND ABS(scd2.longitude - scd.longitude) < 0.0001
);

-- ============================================================================
-- TABLA DE CONFIGURACIÓN DE OPERADORES
-- ============================================================================

CREATE TABLE IF NOT EXISTS cellular_operators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operator_name TEXT NOT NULL UNIQUE,
    mnc_codes TEXT NOT NULL, -- JSON array de códigos MNC
    country_code TEXT DEFAULT '732', -- MCC para Colombia
    frequency_bands TEXT, -- JSON array de bandas de frecuencia
    technologies TEXT, -- JSON array de tecnologías soportadas
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Insertar operadores colombianos conocidos
INSERT OR IGNORE INTO cellular_operators (operator_name, mnc_codes, frequency_bands, technologies) VALUES
('CLARO', '["101", "102", "103", "123"]', '["850", "1900", "1700", "2600"]', '["GSM", "UMTS", "LTE", "5G"]'),
('MOVISTAR', '["111", "123"]', '["850", "1900", "1700"]', '["GSM", "UMTS", "LTE"]'),
('TIGO', '["103", "111"]', '["850", "1900", "1700"]', '["GSM", "UMTS", "LTE"]'),
('WOM', '["130", "130"]', '["1700", "2600"]', '["LTE", "5G"]'),
('PARTNERS', '["154"]', '["1900"]', '["LTE"]'),
('ETB', '["103"]', '["1700"]', '["LTE"]');

-- ============================================================================
-- TRIGGERS PARA MANTENIMIENTO AUTOMÁTICO
-- ============================================================================

-- Trigger para generar hash de datos automáticamente
CREATE TRIGGER IF NOT EXISTS trg_scanner_cellular_data_hash
    BEFORE INSERT ON scanner_cellular_data
    FOR EACH ROW
BEGIN
    UPDATE scanner_cellular_data SET data_hash = hex(
        printf('%s|%s|%s|%s|%s|%s|%s|%s', 
            NEW.mission_id, NEW.punto, NEW.latitude, NEW.longitude, 
            NEW.cell_id, NEW.operator_name, NEW.rssi_dbm, NEW.technology
        )
    ) WHERE id = NEW.id;
END;

-- Trigger para actualizar timestamp de procesamiento
CREATE TRIGGER IF NOT EXISTS trg_scanner_cellular_data_processing_time
    BEFORE UPDATE ON scanner_cellular_data
    FOR EACH ROW
BEGIN
    UPDATE scanner_cellular_data SET processing_timestamp = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- ============================================================================
-- PROCEDIMIENTOS ALMACENADOS (Simulados con vistas complejas)
-- ============================================================================

-- Vista para estadísticas rápidas de misión
CREATE VIEW IF NOT EXISTS vw_mission_scanner_stats AS
SELECT 
    m.id as mission_id,
    m.name as mission_name,
    COUNT(scd.id) as total_measurements,
    COUNT(DISTINCT scd.operator_name) as operators_count,
    COUNT(DISTINCT scd.technology) as technologies_count,
    COUNT(DISTINCT scd.punto) as measurement_points,
    AVG(scd.rssi_dbm) as avg_signal_strength,
    MIN(scd.processing_timestamp) as first_upload,
    MAX(scd.processing_timestamp) as last_upload
FROM missions m
LEFT JOIN scanner_cellular_data scd ON m.id = scd.mission_id
GROUP BY m.id, m.name;

-- ============================================================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- ============================================================================

/*
MAPEO DE COLUMNAS SCANHUNTER.xlsx -> scanner_cellular_data:
- Id -> id (auto-increment)
- Punto -> punto  
- Latitud -> latitude
- Longitud -> longitude
- MNC+MCC -> mnc_mcc
- OPERADOR -> operator_name
- RSSI -> rssi_dbm
- TECNOLOGIA -> technology
- CELLID -> cell_id
- LAC o TAC -> lac_tac
- ENB -> enb_id
- Comentario -> comentario
- CHANNEL -> channel

MEJORAS IMPLEMENTADAS:
1. Campos calculados automáticos (signal_quality)
2. Validaciones robustas con CHECK constraints
3. Índices optimizados para consultas frecuentes
4. Vistas para análisis agregado
5. Sistema de detección de duplicados
6. Configuración de operadores
7. Triggers para mantenimiento automático
8. Soporte para metadatos de procesamiento
*/