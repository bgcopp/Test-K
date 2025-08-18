# ESQUEMA DE BASE DE DATOS - KRONOS

## INFORMACIÓN DEL DOCUMENTO
**Versión:** 1.0.0  
**Fecha:** 18 de Agosto, 2025  
**Autor:** Sistema de Documentación KRONOS para Boris  
**Base de Datos:** SQLite con optimizaciones avanzadas  
**Archivo:** `kronos.db` (16.83 MB)  

---

## TABLA DE CONTENIDOS

1. [Resumen del Esquema](#1-resumen-del-esquema)
2. [Tablas Principales](#2-tablas-principales)
3. [Índices de Optimización](#3-índices-de-optimización)
4. [Relaciones y Constraints](#4-relaciones-y-constraints)
5. [Procedimientos de Mantenimiento](#5-procedimientos-de-mantenimiento)

---

## 1. RESUMEN DEL ESQUEMA

### 1.1 Estadísticas Generales
```json
{
  "base_datos": {
    "motor": "SQLite 3.x",
    "archivo": "kronos.db", 
    "tamaño_mb": 16.83,
    "modo_journal": "WAL",
    "tablas_principales": 8,
    "indices_optimizacion": 31,
    "constraints_integridad": 45
  }
}
```

### 1.2 Propósito de Cada Tabla
- **`cellular_data`**: Datos de medición HUNTER (celdas detectadas)
- **`operator_call_data`**: Registros CDR de operadores móviles 
- **`missions`**: Gestión de misiones de análisis
- **`users`**: Sistema de usuarios y autenticación
- **`roles`**: Roles y permisos del sistema
- **`operator_data_sheets`**: Metadatos de archivos cargados
- **`file_records`**: Tracking de procesamiento de archivos
- **Sistema de auditoría**: Logs y trazabilidad

---

## 2. TABLAS PRINCIPALES

### 2.1 Tabla: `cellular_data` (DATOS HUNTER)

**Propósito:** Almacena mediciones de celdas realizadas con equipo HUNTER

```sql
CREATE TABLE cellular_data (
    -- Identificación única
    id INTEGER NOT NULL PRIMARY KEY,
    mission_id VARCHAR NOT NULL,
    file_record_id INTEGER,
    
    -- Datos de medición HUNTER
    punto VARCHAR NOT NULL,                    -- Punto de medición
    lat FLOAT NOT NULL,                        -- Latitud GPS (-90.0 a 90.0)
    lon FLOAT NOT NULL,                        -- Longitud GPS (-180.0 a 180.0)
    
    -- Información de celda
    mnc_mcc VARCHAR NOT NULL,                  -- Mobile Network + Country Code
    operator VARCHAR NOT NULL,                 -- Operador detectado
    cell_id VARCHAR NOT NULL,                  -- ID de celda (CAMPO CRÍTICO)
    lac_tac VARCHAR,                          -- Location Area/Tracking Area Code
    enb VARCHAR,                              -- eNodeB identifier
    
    -- Características técnicas
    rssi INTEGER NOT NULL,                     -- Received Signal Strength (-120 a 0)
    tecnologia VARCHAR NOT NULL,               -- GSM, UMTS, 3G, LTE, 4G, 5G NR, 5G
    channel VARCHAR,                          -- Canal de frecuencia
    
    -- Metadatos
    comentario TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints de integridad
    CONSTRAINT ck_cellular_lat_range 
        CHECK (lat >= -90.0 AND lat <= 90.0),
    CONSTRAINT ck_cellular_lon_range 
        CHECK (lon >= -180.0 AND lon <= 180.0),
    CONSTRAINT ck_cellular_punto_not_empty 
        CHECK (length(trim(punto)) > 0),
    CONSTRAINT ck_cellular_mnc_mcc_length 
        CHECK (length(trim(mnc_mcc)) >= 5),
    CONSTRAINT ck_cellular_operator_not_empty 
        CHECK (length(trim(operator)) > 0),
    CONSTRAINT ck_cellular_tecnologia_not_empty 
        CHECK (length(trim(tecnologia)) > 0),
    CONSTRAINT ck_cellular_cell_id_not_empty 
        CHECK (length(trim(cell_id)) > 0),
    CONSTRAINT ck_cellular_rssi_negative 
        CHECK (rssi <= 0),
    CONSTRAINT ck_cellular_tecnologia_values 
        CHECK (tecnologia IN ('GSM', 'UMTS', '3G', 'LTE', '4G', '5G NR', '5G')),
    CONSTRAINT ck_cellular_mnc_mcc_format 
        CHECK (mnc_mcc GLOB '[0-9]*' AND length(mnc_mcc) BETWEEN 5 AND 6),
    CONSTRAINT ck_cellular_lac_tac_valid 
        CHECK (lac_tac IS NULL OR length(trim(lac_tac)) > 0),
    CONSTRAINT ck_cellular_enb_valid 
        CHECK (enb IS NULL OR length(trim(enb)) > 0),
    CONSTRAINT ck_cellular_channel_valid 
        CHECK (channel IS NULL OR length(trim(channel)) > 0),
        
    -- Claves foráneas
    FOREIGN KEY(mission_id) REFERENCES missions (id) ON DELETE CASCADE
);
```

**Estadísticas:** 58 registros, 57 celdas únicas

### 2.2 Tabla: `operator_call_data` (REGISTROS CDR)

**Propósito:** Almacena registros de llamadas (CDR) de operadores móviles

```sql
CREATE TABLE operator_call_data (
    -- Identificación única
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_upload_id TEXT NOT NULL,
    mission_id TEXT NOT NULL,
    
    -- Información básica de llamada
    operator TEXT NOT NULL,                    -- CLARO, MOVISTAR, TIGO, WOM
    tipo_llamada TEXT NOT NULL,               -- ENTRANTE, SALIENTE, MIXTA
    numero_origen TEXT NOT NULL,              -- Número que inicia comunicación
    numero_destino TEXT NOT NULL,             -- Número que recibe comunicación  
    numero_objetivo TEXT NOT NULL,            -- Número bajo investigación
    
    -- Información temporal
    fecha_hora_llamada DATETIME NOT NULL,    -- Timestamp de la comunicación
    duracion_segundos INTEGER DEFAULT 0,     -- Duración en segundos
    
    -- Información de ubicación (CAMPOS CRÍTICOS PARA CORRELACIÓN)
    celda_origen TEXT,                        -- Celda del originador
    celda_destino TEXT,                       -- Celda del receptor
    celda_objetivo TEXT,                      -- Celda del número objetivo
    latitud_origen REAL,                     -- Coordenadas de celda origen
    longitud_origen REAL,
    latitud_destino REAL,                    -- Coordenadas de celda destino
    longitud_destino REAL,
    
    -- Información técnica
    tecnologia TEXT DEFAULT 'UNKNOWN',       -- Tecnología utilizada
    tipo_trafico TEXT DEFAULT 'VOZ',         -- VOZ, SMS, MMS, DATOS
    estado_llamada TEXT DEFAULT 'COMPLETADA', -- Estado final de comunicación
    calidad_senal INTEGER,                   -- Calidad de señal
    
    -- Campos específicos por operador
    cellid_decimal INTEGER,                  -- Cell ID en formato decimal
    lac_decimal INTEGER,                     -- LAC en formato decimal
    operator_specific_data TEXT,             -- JSON con datos específicos
    
    -- Metadatos y control
    record_hash TEXT NOT NULL,               -- Hash único para deduplicación
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints de integridad
    CHECK (tipo_llamada IN ('ENTRANTE', 'SALIENTE', 'MIXTA')),
    CHECK (duracion_segundos >= 0),
    CHECK (length(trim(numero_origen)) >= 7),
    CHECK (length(trim(numero_destino)) >= 7),
    CHECK (length(trim(numero_objetivo)) >= 7),
    CHECK (numero_origen GLOB '[0-9]*'),
    CHECK (numero_destino GLOB '[0-9]*'),
    CHECK (numero_objetivo GLOB '[0-9]*'),
    CHECK (tecnologia IN ('GSM', '2G', 'UMTS', '3G', 'LTE', '4G', '5G NR', '5G', 'UNKNOWN')),
    CHECK (tipo_trafico IN ('VOZ', 'SMS', 'MMS', 'DATOS')),
    CHECK (estado_llamada IN ('COMPLETADA', 'NO_CONTESTADA', 'OCUPADO', 'ERROR', 'TRANSFERIDA')),
    
    -- Claves foráneas
    FOREIGN KEY (file_upload_id) REFERENCES operator_data_sheets(id) ON DELETE CASCADE,
    FOREIGN KEY (mission_id) REFERENCES missions(id) ON DELETE CASCADE,
    
    -- Índice único para evitar duplicados
    UNIQUE (file_upload_id, record_hash)
);
```

**Estadísticas:** 3,395 registros, 253 celdas origen únicas, 71 celdas destino únicas

### 2.3 Tabla: `missions` (GESTIÓN DE MISIONES)

```sql
CREATE TABLE missions (
    -- Identificación
    id VARCHAR NOT NULL PRIMARY KEY,
    code VARCHAR NOT NULL UNIQUE,             -- Código único de misión
    name VARCHAR NOT NULL,                    -- Nombre descriptivo
    description TEXT,                         -- Descripción detallada
    
    -- Estado y fechas
    status VARCHAR NOT NULL,                  -- Estado actual
    start_date VARCHAR NOT NULL,              -- Fecha inicio análisis
    end_date VARCHAR,                         -- Fecha fin análisis
    
    -- Auditoría
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR,
    
    -- Constraints
    CONSTRAINT ck_mission_code_not_empty 
        CHECK (length(trim(code)) > 0),
    CONSTRAINT ck_mission_name_not_empty 
        CHECK (length(trim(name)) > 0),
    CONSTRAINT ck_mission_status_values 
        CHECK (status IN ('Planificación', 'En Progreso', 'Completada', 'Cancelada')),
    
    -- Claves foráneas
    FOREIGN KEY(created_by) REFERENCES users (id)
);
```

### 2.4 Tabla: `users` (GESTIÓN DE USUARIOS)

```sql
CREATE TABLE users (
    -- Identificación
    id VARCHAR NOT NULL PRIMARY KEY,
    name VARCHAR NOT NULL,
    email VARCHAR NOT NULL UNIQUE,
    
    -- Autenticación
    password_hash VARCHAR NOT NULL,           -- Hash bcrypt
    role_id VARCHAR NOT NULL,
    status VARCHAR NOT NULL,                  -- active, inactive
    
    -- Perfil
    avatar VARCHAR,                          -- URL o path del avatar
    last_login DATETIME,
    
    -- Auditoría
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT ck_user_name_not_empty 
        CHECK (length(trim(name)) > 0),
    CONSTRAINT ck_user_email_format 
        CHECK (length(trim(email)) > 0 AND email LIKE '%@%.%'),
    CONSTRAINT ck_user_password_hash_length 
        CHECK (length(password_hash) >= 60),
    CONSTRAINT ck_user_status_values 
        CHECK (status IN ('active', 'inactive')),
    
    -- Claves foráneas
    FOREIGN KEY(role_id) REFERENCES roles (id)
);
```

### 2.5 Tabla: `roles` (SISTEMA DE PERMISOS)

```sql
CREATE TABLE roles (
    -- Identificación
    id VARCHAR NOT NULL PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,
    
    -- Permisos (JSON serializado)
    permissions TEXT NOT NULL,               -- JSON con permisos granulares
    
    -- Auditoría
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT ck_role_name_not_empty 
        CHECK (length(trim(name)) > 0)
);
```

**Estructura de Permisos (JSON):**
```json
{
  "users": {
    "view": true,
    "create": true,
    "edit": true,
    "delete": false
  },
  "roles": {
    "view": true,
    "create": false,
    "edit": false,
    "delete": false
  },
  "missions": {
    "view": true,
    "create": true,
    "edit": true,
    "delete": true,
    "analyze": true
  },
  "reports": {
    "view": true,
    "export": true,
    "advanced": false
  },
  "settings": {
    "view": false,
    "edit": false
  }
}
```

---

## 3. ÍNDICES DE OPTIMIZACIÓN

### 3.1 Índices Críticos para Correlación

#### 3.1.1 Índices Principales (Más Importantes)
```sql
-- CRÍTICO: Optimiza consulta principal con listas de 50+ celdas HUNTER
CREATE INDEX idx_correlation_origen_critical 
ON operator_call_data(celda_origen, mission_id, fecha_hora_llamada, numero_origen, operator, numero_destino);

-- CRÍTICO: Optimiza consulta principal con listas de celdas destino
CREATE INDEX idx_correlation_destino_critical 
ON operator_call_data(celda_destino, mission_id, fecha_hora_llamada, numero_destino, operator, numero_origen);

-- COVERING INDEX: Evita lookups adicionales en agregaciones
CREATE INDEX idx_covering_correlation_summary 
ON operator_call_data(numero_origen, numero_destino, operator, mission_id, 
                      celda_origen, celda_destino, fecha_hora_llamada, duracion_segundos);
```

#### 3.1.2 Índices Temporales
```sql
-- Optimiza filtros por rango de fechas
CREATE INDEX idx_temporal_correlation 
ON operator_call_data(fecha_hora_llamada, mission_id, celda_origen, celda_destino);

-- Consultas con múltiples filtros
CREATE INDEX idx_multi_filter_correlation 
ON operator_call_data(mission_id, operator, fecha_hora_llamada, numero_origen, numero_destino);
```

#### 3.1.3 Índices Parciales (Alta Selectividad)
```sql
-- Solo registros con celdas válidas (excluye NULL y vacíos)
CREATE INDEX idx_partial_valid_cells_origen 
ON operator_call_data(celda_origen, mission_id, numero_origen, fecha_hora_llamada)
WHERE celda_origen IS NOT NULL AND celda_origen != '';

CREATE INDEX idx_partial_valid_cells_destino 
ON operator_call_data(celda_destino, mission_id, numero_destino, fecha_hora_llamada)
WHERE celda_destino IS NOT NULL AND celda_destino != '';

-- Solo números colombianos válidos (patrón 3XXXXXXXXX)
CREATE INDEX idx_partial_colombian_numbers 
ON operator_call_data(numero_origen, numero_destino, mission_id, operator, fecha_hora_llamada)
WHERE (numero_origen LIKE '3%' AND LENGTH(numero_origen) = 10) 
   OR (numero_destino LIKE '3%' AND LENGTH(numero_destino) = 10);
```

### 3.2 Índices para Datos HUNTER

```sql
-- JOIN optimizado entre cellular_data y operator_call_data
CREATE INDEX idx_hunter_join_optimized 
ON cellular_data(cell_id, mission_id, operator, tecnologia, created_at);

-- Covering index para análisis completo de datos HUNTER
CREATE INDEX idx_hunter_covering_analysis 
ON cellular_data(mission_id, cell_id, operator, tecnologia, lat, lon, rssi, created_at);
```

### 3.3 Índices para Estadísticas y Agregaciones

```sql
-- Optimiza COUNT(*) GROUP BY numero, operador
CREATE INDEX idx_stats_aggregation_calls 
ON operator_call_data(numero_origen, operator, mission_id, fecha_hora_llamada, duracion_segundos);

CREATE INDEX idx_stats_aggregation_destino 
ON operator_call_data(numero_destino, operator, mission_id, fecha_hora_llamada, duracion_segundos);

-- Análisis de frecuencia de celdas más activas
CREATE INDEX idx_stats_cell_frequency 
ON operator_call_data(celda_origen, celda_destino, operator, mission_id, fecha_hora_llamada);
```

### 3.4 Índices para Gestión del Sistema

```sql
-- Usuarios y autenticación
CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_users_role_status ON users (role_id, status);
CREATE INDEX idx_users_last_login ON users (last_login);

-- Roles
CREATE INDEX idx_roles_name ON roles (name);

-- Misiones
CREATE INDEX idx_missions_status ON missions (status);
CREATE INDEX idx_missions_dates ON missions (start_date, end_date);
CREATE INDEX idx_missions_created_by ON missions (created_by);
```

---

## 4. RELACIONES Y CONSTRAINTS

### 4.1 Diagrama de Relaciones

```
                    users (Sistema de Usuarios)
                      |
                      | role_id
                      ▼
                    roles (Permisos)
                      
                      
    missions (Gestión)               operator_data_sheets (Metadatos)
           |                                    |
           | mission_id                         | file_upload_id  
           ▼                                    ▼
    cellular_data ◄──────correlación──────► operator_call_data
    (Datos HUNTER)     cell_id = celda_*     (Registros CDR)
                                              
```

### 4.2 Integridad Referencial

#### 4.2.1 Foreign Keys Principales
```sql
-- Relación Misión -> Datos Celulares
FOREIGN KEY(mission_id) REFERENCES missions (id) ON DELETE CASCADE

-- Relación Misión -> Registros de Llamadas  
FOREIGN KEY (mission_id) REFERENCES missions(id) ON DELETE CASCADE

-- Relación Usuario -> Rol
FOREIGN KEY(role_id) REFERENCES roles (id)

-- Relación Archivo -> Registros de Llamadas
FOREIGN KEY (file_upload_id) REFERENCES operator_data_sheets(id) ON DELETE CASCADE
```

#### 4.2.2 Constraints de Dominio Críticos

**Números Telefónicos:**
```sql
-- Mínimo 7 dígitos, solo números
CHECK (length(trim(numero_origen)) >= 7)
CHECK (numero_origen GLOB '[0-9]*')
```

**Coordenadas Geográficas:**
```sql
-- Rango válido de latitud y longitud
CHECK (lat >= -90.0 AND lat <= 90.0)
CHECK (lon >= -180.0 AND lon <= 180.0)
```

**Estados Válidos:**
```sql
-- Estados de misión válidos
CHECK (status IN ('Planificación', 'En Progreso', 'Completada', 'Cancelada'))

-- Tipos de llamada válidos
CHECK (tipo_llamada IN ('ENTRANTE', 'SALIENTE', 'MIXTA'))

-- Tecnologías válidas
CHECK (tecnologia IN ('GSM', '2G', 'UMTS', '3G', 'LTE', '4G', '5G NR', '5G', 'UNKNOWN'))
```

### 4.3 Triggers de Auditoría

```sql
-- Trigger para actualizar updated_at automáticamente
CREATE TRIGGER update_mission_timestamp 
AFTER UPDATE ON missions
BEGIN
    UPDATE missions 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- Trigger para validar hash únicos en operator_call_data
CREATE TRIGGER validate_record_hash 
BEFORE INSERT ON operator_call_data
BEGIN
    SELECT CASE 
        WHEN NEW.record_hash IS NULL OR NEW.record_hash = '' THEN
            RAISE(ABORT, 'record_hash cannot be null or empty')
    END;
END;
```

---

## 5. PROCEDIMIENTOS DE MANTENIMIENTO

### 5.1 Optimización Periódica

#### 5.1.1 Script de Mantenimiento Diario
```sql
-- Ejecutar diariamente a las 3:00 AM
BEGIN TRANSACTION;

-- Actualizar estadísticas del optimizador
ANALYZE operator_call_data;
ANALYZE cellular_data; 
ANALYZE missions;

-- Optimización automática
PRAGMA optimize;

-- Verificación de integridad (rápida)
PRAGMA quick_check;

COMMIT;
```

#### 5.1.2 Script de Mantenimiento Semanal
```sql
-- Ejecutar domingos a las 2:00 AM
BEGIN TRANSACTION;

-- Análisis completo de estadísticas
ANALYZE;

-- Verificación completa de integridad
PRAGMA integrity_check;

-- Reindexar si es necesario (solo si hay fragmentación)
-- REINDEX idx_correlation_origen_critical;
-- REINDEX idx_correlation_destino_critical;

-- Limpieza de datos temporales antiguos (si existen)
DELETE FROM temp_analysis_results 
WHERE created_at < datetime('now', '-30 days');

COMMIT;

-- Compactación de BD (si el crecimiento > 20%)
-- VACUUM;
```

### 5.2 Monitoreo de Rendimiento

#### 5.2.1 Consultas de Monitoreo
```sql
-- Verificar uso de índices en consulta crítica
EXPLAIN QUERY PLAN
SELECT numero_origen, operator, COUNT(*) 
FROM operator_call_data 
WHERE mission_id = 'mission_test'
  AND (celda_origen IN ('10111','10248','10263') 
       OR celda_destino IN ('10111','10248','10263'))
GROUP BY numero_origen, operator;

-- Estadísticas de tamaño de tablas
SELECT 
    name,
    COUNT(*) as record_count,
    AVG(LENGTH(CAST(record_hash AS TEXT))) as avg_hash_length
FROM operator_call_data, sqlite_master 
WHERE type='table' AND name='operator_call_data'
GROUP BY name;

-- Efectividad de índices parciales
SELECT 
    COUNT(*) as total_records,
    COUNT(CASE WHEN celda_origen IS NOT NULL AND celda_origen != '' THEN 1 END) as valid_origen,
    COUNT(CASE WHEN celda_destino IS NOT NULL AND celda_destino != '' THEN 1 END) as valid_destino
FROM operator_call_data;
```

#### 5.2.2 Alertas Automáticas
```sql
-- Query para detectar fragmentación excesiva
SELECT 
    name,
    (SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND tbl_name=name) as index_count,
    (SELECT pgsize FROM dbstat WHERE name=main.name ORDER BY pgsize DESC LIMIT 1) as max_page_size
FROM sqlite_master 
WHERE type='table' 
  AND name IN ('operator_call_data', 'cellular_data')
  AND max_page_size > 4096;  -- Alerta si páginas > 4KB

-- Monitoreo de crecimiento de datos
SELECT 
    DATE(created_at) as date,
    COUNT(*) as records_added
FROM operator_call_data 
WHERE created_at >= date('now', '-7 days')
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

### 5.3 Backup y Recuperación

#### 5.3.1 Estrategia de Backup
```bash
#!/bin/bash
# backup_kronos.sh - Script de backup automático

BACKUP_DIR="/backup/kronos"
DATE_STAMP=$(date +"%Y%m%d_%H%M%S")
DB_FILE="Backend/kronos.db"
BACKUP_FILE="${BACKUP_DIR}/kronos_backup_${DATE_STAMP}.db"

# Crear directorio de backup si no existe
mkdir -p "${BACKUP_DIR}"

# Backup usando WAL checkpoint
sqlite3 "${DB_FILE}" "PRAGMA wal_checkpoint(FULL);"

# Backup completo
cp "${DB_FILE}" "${BACKUP_FILE}"

# Comprimir backup
gzip "${BACKUP_FILE}"

# Verificar integridad del backup
gunzip -t "${BACKUP_FILE}.gz" && \
sqlite3 "${BACKUP_FILE%.*}" "PRAGMA integrity_check;" > /dev/null

if [ $? -eq 0 ]; then
    echo "Backup completado exitosamente: ${BACKUP_FILE}.gz"
    
    # Limpiar backups antiguos (mantener últimos 30 días)
    find "${BACKUP_DIR}" -name "kronos_backup_*.db.gz" -mtime +30 -delete
else
    echo "ERROR: Backup falló la verificación de integridad"
    rm -f "${BACKUP_FILE}.gz"
    exit 1
fi
```

#### 5.3.2 Procedimiento de Recuperación
```bash
#!/bin/bash
# restore_kronos.sh - Script de restauración

BACKUP_FILE="$1"
TARGET_DB="Backend/kronos.db"

if [ -z "$BACKUP_FILE" ]; then
    echo "Uso: $0 <archivo_backup.db.gz>"
    exit 1
fi

# Detener aplicación (si está corriendo)
# systemctl stop kronos

# Crear backup de BD actual antes de restaurar
cp "${TARGET_DB}" "${TARGET_DB}.before_restore_$(date +%Y%m%d_%H%M%S)"

# Descomprimir y restaurar
gunzip -c "${BACKUP_FILE}" > "${TARGET_DB}"

# Verificar integridad
sqlite3 "${TARGET_DB}" "PRAGMA integrity_check;" > integrity_check.log

if grep -q "ok" integrity_check.log; then
    echo "Restauración completada exitosamente"
    
    # Optimizar después de restauración
    sqlite3 "${TARGET_DB}" "ANALYZE; PRAGMA optimize;"
    
    # Reiniciar aplicación
    # systemctl start kronos
else
    echo "ERROR: BD restaurada falló verificación de integridad"
    echo "Ver integrity_check.log para detalles"
    exit 1
fi
```

---

## CONCLUSIONES

### Puntos Críticos del Esquema
1. **Correlación cell_id ↔ celda_origen/celda_destino** es fundamental para el algoritmo
2. **Índices de optimización** son esenciales para rendimiento aceptable
3. **Constraints de integridad** previenen datos inconsistentes que romperían correlaciones
4. **Estrategia de backup** es crítica dado que la BD contiene análisis forenses valiosos

### Recomendaciones de Mantenimiento
- **ANALYZE** mensual es obligatorio para estadísticas precisas del optimizador
- **PRAGMA optimize** semanal mantiene índices en estado óptimo
- **Monitoreo de fragmentación** para detectar cuándo es necesario VACUUM
- **Backup diario** con verificación de integridad automática

---

**Documento generado automáticamente por el Sistema de Documentación KRONOS**  
**Última actualización:** 18 de Agosto, 2025  
**Esquema documentado:** Base completa con 31 índices de optimización