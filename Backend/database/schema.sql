-- ============================================================================
-- KRONOS Database Schema - SQLite
-- ============================================================================
-- Este esquema está diseñado específicamente para SQLite con optimizaciones
-- para las operaciones de búsqueda y análisis de objetivos de KRONOS.
-- 
-- Características principales:
-- - Esquema normalizado siguiendo mejores prácticas
-- - Índices optimizados para consultas frecuentes
-- - Integridad referencial con CASCADE apropiado
-- - Almacenamiento JSON para permisos complejos
-- - Triggers para auditoría y validación de datos
-- ============================================================================

-- Habilitar foreign keys en SQLite (crítico para integridad referencial)
PRAGMA foreign_keys = ON;

-- ============================================================================
-- TABLA: roles
-- ============================================================================
-- Almacena los roles del sistema con sus permisos en formato JSON
-- Los permisos se almacenan como JSON para flexibilidad en la estructura
CREATE TABLE roles (
    id TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL UNIQUE,
    permissions TEXT NOT NULL, -- JSON con estructura de permisos
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Validaciones
    CHECK (length(trim(name)) > 0),
    CHECK (json_valid(permissions) = 1)
);

-- Índice para búsquedas por nombre (consultas frecuentes)
CREATE INDEX idx_roles_name ON roles(name);

-- ============================================================================
-- TABLA: users
-- ============================================================================
-- Almacena usuarios del sistema con referencia a roles
CREATE TABLE users (
    id TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL, -- BCrypt hash
    role_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    avatar TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    
    -- Relaciones
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE RESTRICT,
    
    -- Validaciones
    CHECK (length(trim(name)) > 0),
    CHECK (length(trim(email)) > 0 AND email LIKE '%@%.%'),
    CHECK (length(password_hash) >= 60), -- BCrypt produce hash de 60 caracteres
    CHECK (status IN ('active', 'inactive'))
);

-- Índices para optimización
CREATE UNIQUE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role_status ON users(role_id, status);
CREATE INDEX idx_users_last_login ON users(last_login);

-- ============================================================================
-- TABLA: missions
-- ============================================================================
-- Información principal de las misiones
CREATE TABLE missions (
    id TEXT PRIMARY KEY NOT NULL,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'Planificación',
    start_date DATE NOT NULL,
    end_date DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    
    -- Relaciones
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    
    -- Validaciones
    CHECK (length(trim(code)) > 0),
    CHECK (length(trim(name)) > 0),
    CHECK (status IN ('Planificación', 'En Progreso', 'Completada', 'Cancelada')),
    CHECK (start_date <= end_date OR end_date IS NULL)
);

-- Índices para optimización
CREATE UNIQUE INDEX idx_missions_code ON missions(code);
CREATE INDEX idx_missions_status_dates ON missions(status, start_date, end_date);
CREATE INDEX idx_missions_created_by ON missions(created_by);

-- ============================================================================
-- TABLA: cellular_data
-- ============================================================================
-- Datos celulares asociados a misiones - optimizada para búsquedas geoespaciales
-- y de señal
CREATE TABLE cellular_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id TEXT NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    signal INTEGER NOT NULL, -- dBm values (negativos)
    operator TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Relaciones
    FOREIGN KEY (mission_id) REFERENCES missions(id) ON DELETE CASCADE,
    
    -- Validaciones para coordenadas válidas
    CHECK (lat >= -90.0 AND lat <= 90.0),
    CHECK (lon >= -180.0 AND lon <= 180.0),
    CHECK (signal <= 0), -- dBm values son típicamente negativos
    CHECK (length(trim(operator)) > 0)
);

-- Índices críticos para análisis de objetivos
CREATE INDEX idx_cellular_mission ON cellular_data(mission_id);
CREATE INDEX idx_cellular_operator ON cellular_data(operator);
CREATE INDEX idx_cellular_signal ON cellular_data(signal);
CREATE INDEX idx_cellular_location ON cellular_data(lat, lon);
CREATE INDEX idx_cellular_mission_operator ON cellular_data(mission_id, operator);

-- ============================================================================
-- TABLA: operator_sheets
-- ============================================================================
-- Hojas de datos de operadores (metadatos)
CREATE TABLE operator_sheets (
    id TEXT PRIMARY KEY NOT NULL,
    mission_id TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Relaciones
    FOREIGN KEY (mission_id) REFERENCES missions(id) ON DELETE CASCADE,
    
    -- Validaciones
    CHECK (length(trim(name)) > 0)
);

-- Índices
CREATE INDEX idx_operator_sheets_mission ON operator_sheets(mission_id);
CREATE INDEX idx_operator_sheets_name ON operator_sheets(name);

-- ============================================================================
-- TABLA: operator_data_records
-- ============================================================================
-- Registros individuales de datos de operadores
CREATE TABLE operator_data_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sheet_id TEXT NOT NULL,
    operator_id TEXT NOT NULL, -- ID del operador del registro
    name TEXT NOT NULL, -- Nombre del operador
    towers INTEGER NOT NULL,
    coverage TEXT NOT NULL, -- Formato: "XX.X%"
    
    -- Relaciones
    FOREIGN KEY (sheet_id) REFERENCES operator_sheets(id) ON DELETE CASCADE,
    
    -- Validaciones
    CHECK (length(trim(operator_id)) > 0),
    CHECK (length(trim(name)) > 0),
    CHECK (towers > 0),
    CHECK (coverage GLOB '*%' AND length(coverage) >= 3)
);

-- Índices para análisis cruzado
CREATE INDEX idx_operator_records_sheet ON operator_data_records(sheet_id);
CREATE INDEX idx_operator_records_operator ON operator_data_records(name);
CREATE INDEX idx_operator_records_towers ON operator_data_records(towers);

-- ============================================================================
-- TABLA: target_records
-- ============================================================================
-- Resultados de análisis de objetivos - tabla desnormalizada para performance
CREATE TABLE target_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    operator TEXT NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    signal INTEGER NOT NULL,
    towers INTEGER NOT NULL,
    coverage TEXT NOT NULL,
    source_sheet TEXT NOT NULL,
    analysis_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Relaciones
    FOREIGN KEY (mission_id) REFERENCES missions(id) ON DELETE CASCADE,
    
    -- Validaciones
    CHECK (lat >= -90.0 AND lat <= 90.0),
    CHECK (lon >= -180.0 AND lon <= 180.0),
    CHECK (signal <= 0),
    CHECK (towers > 0),
    CHECK (length(trim(target_id)) > 0),
    CHECK (length(trim(operator)) > 0),
    CHECK (length(trim(source_sheet)) > 0)
);

-- Índices para consultas de análisis
CREATE UNIQUE INDEX idx_target_records_unique ON target_records(mission_id, target_id);
CREATE INDEX idx_target_records_mission ON target_records(mission_id);
CREATE INDEX idx_target_records_operator ON target_records(operator);
CREATE INDEX idx_target_records_signal ON target_records(signal);
CREATE INDEX idx_target_records_location ON target_records(lat, lon);
CREATE INDEX idx_target_records_analysis_date ON target_records(analysis_date);

-- ============================================================================
-- TRIGGERS DE AUDITORÍA
-- ============================================================================

-- Trigger para actualizar updated_at en roles
CREATE TRIGGER trg_roles_updated_at
    AFTER UPDATE ON roles
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE roles SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger para actualizar updated_at en users
CREATE TRIGGER trg_users_updated_at
    AFTER UPDATE ON users
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger para actualizar updated_at en missions
CREATE TRIGGER trg_missions_updated_at
    AFTER UPDATE ON missions
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE missions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ============================================================================
-- TRIGGER DE LIMPIEZA DE ANÁLISIS
-- ============================================================================
-- Cuando se actualizan datos celulares u operadores, invalidar análisis previos
-- OPTIMIZADO: Solo eliminar análisis afectados, no todos los de la misión
CREATE TRIGGER trg_clean_analysis_on_cellular_change
    AFTER INSERT ON cellular_data
    FOR EACH ROW
BEGIN
    -- Solo eliminar análisis que podrían verse afectados por el nuevo operador
    DELETE FROM target_records 
    WHERE mission_id = NEW.mission_id 
    AND operator = NEW.operator;
END;

CREATE TRIGGER trg_clean_analysis_on_cellular_update
    AFTER UPDATE ON cellular_data
    FOR EACH ROW
BEGIN
    -- Eliminar análisis afectados por el cambio
    DELETE FROM target_records 
    WHERE mission_id = NEW.mission_id 
    AND (operator = NEW.operator OR operator = OLD.operator);
END;

CREATE TRIGGER trg_clean_analysis_on_cellular_delete
    AFTER DELETE ON cellular_data
    FOR EACH ROW
BEGIN
    -- Solo eliminar análisis del operador eliminado si no hay más datos de ese operador
    DELETE FROM target_records 
    WHERE mission_id = OLD.mission_id 
    AND operator = OLD.operator
    AND NOT EXISTS (
        SELECT 1 FROM cellular_data 
        WHERE mission_id = OLD.mission_id 
        AND operator = OLD.operator
    );
END;

CREATE TRIGGER trg_clean_analysis_on_operator_change
    AFTER INSERT ON operator_data_records
    FOR EACH ROW
BEGIN
    -- Solo eliminar análisis del operador específico
    DELETE FROM target_records 
    WHERE mission_id = (
        SELECT mission_id FROM operator_sheets WHERE id = NEW.sheet_id
    )
    AND operator = NEW.name;
END;

-- ============================================================================
-- VIEWS PARA CONSULTAS COMUNES
-- ============================================================================

-- Vista con información completa de usuarios
CREATE VIEW v_users_complete AS
SELECT 
    u.id,
    u.name,
    u.email,
    u.status,
    u.avatar,
    u.created_at,
    u.updated_at,
    u.last_login,
    r.id as role_id,
    r.name as role_name,
    r.permissions
FROM users u
JOIN roles r ON u.role_id = r.id;

-- Vista con estadísticas de misiones
CREATE VIEW v_mission_stats AS
SELECT 
    m.id,
    m.code,
    m.name,
    m.status,
    m.start_date,
    m.end_date,
    COUNT(DISTINCT cd.id) as cellular_records_count,
    COUNT(DISTINCT os.id) as operator_sheets_count,
    COUNT(DISTINCT odr.id) as operator_records_count,
    COUNT(DISTINCT tr.id) as target_records_count
FROM missions m
LEFT JOIN cellular_data cd ON m.id = cd.mission_id
LEFT JOIN operator_sheets os ON m.id = os.mission_id
LEFT JOIN operator_data_records odr ON os.id = odr.sheet_id
LEFT JOIN target_records tr ON m.id = tr.mission_id
GROUP BY m.id, m.code, m.name, m.status, m.start_date, m.end_date;

-- ============================================================================
-- CONFIGURACIÓN DE RENDIMIENTO
-- ============================================================================

-- Configurar SQLite para mejor rendimiento
PRAGMA journal_mode = WAL;           -- Write-Ahead Logging para mejor concurrencia
PRAGMA synchronous = NORMAL;         -- Balance entre seguridad y velocidad
PRAGMA cache_size = 10000;          -- 10MB de cache
PRAGMA temp_store = MEMORY;          -- Usar memoria para tablas temporales
PRAGMA mmap_size = 268435456;       -- 256MB para memory mapping

-- Análisis inicial de estadísticas para el optimizador
PRAGMA optimize;