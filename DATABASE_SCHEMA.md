# KRONOS - Esquema de Base de Datos

Este documento describe el esquema completo de la base de datos SQLite utilizada por KRONOS, incluyendo todas las tablas, relaciones, índices y validaciones.

## Información General

- **Motor**: SQLite 3
- **Archivo**: `Backend/kronos.db`
- **ORM**: SQLAlchemy
- **Codificación**: UTF-8
- **Integridad Referencial**: Habilitada

## Estructura de Tablas

### 1. **roles** - Gestión de Roles y Permisos

```sql
CREATE TABLE roles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    permissions TEXT NOT NULL,  -- JSON string con permisos
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Campos:**
- `id`: Identificador único del rol (ej: `role_abc123`)
- `name`: Nombre descriptivo del rol (ej: "Administrador", "Analista")
- `permissions`: JSON con estructura de permisos granulares
- `created_at`, `updated_at`: Timestamps de auditoría

**Validaciones:**
- `name` no puede estar vacío
- `permissions` debe ser JSON válido

**Índices:**
- `idx_roles_name` en `name`

### 2. **users** - Usuarios del Sistema

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role_id TEXT NOT NULL REFERENCES roles(id),
    status TEXT NOT NULL DEFAULT 'active',
    avatar TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME
);
```

**Campos:**
- `id`: Identificador único del usuario (ej: `user_xyz789`)
- `name`: Nombre completo del usuario
- `email`: Email único para autenticación
- `password_hash`: Hash BCrypt de la contraseña (60+ caracteres)
- `role_id`: FK al rol asignado
- `status`: Estado (`active` | `inactive`)
- `avatar`: URL o path del avatar (opcional)
- `last_login`: Timestamp del último login

**Validaciones:**
- `name` no puede estar vacío
- `email` debe tener formato válido (`%@%.%`)
- `password_hash` mínimo 60 caracteres
- `status` debe ser `active` o `inactive`

**Índices:**
- `idx_users_email` en `email`
- `idx_users_role_status` en `role_id, status`
- `idx_users_last_login` en `last_login`

### 3. **missions** - Misiones de Investigación

```sql
CREATE TABLE missions (
    id TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'Planificación',
    start_date TEXT NOT NULL,  -- ISO string para compatibilidad frontend
    end_date TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT REFERENCES users(id)
);
```

**Campos:**
- `id`: Identificador único de la misión (ej: `mission_def456`)
- `code`: Código alfanumérico único (ej: "PX-001", "OP-2024-01")
- `name`: Nombre descriptivo de la misión
- `description`: Descripción detallada (opcional)
- `status`: Estado de la misión
- `start_date`, `end_date`: Fechas como strings ISO
- `created_by`: FK al usuario creador

**Estados Válidos:**
- `Planificación`, `En Progreso`, `Completada`, `Cancelada`

**Validaciones:**
- `code` y `name` no pueden estar vacíos
- `status` debe ser uno de los valores válidos

**Índices:**
- `idx_missions_code` en `code`
- `idx_missions_status_dates` en `status, start_date, end_date`
- `idx_missions_created_by` en `created_by`

### 4. **cellular_data** - Datos de Recorrido Celular (SCANHUNTER)

```sql
CREATE TABLE cellular_data (
    -- Identificación
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id TEXT NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    
    -- Información del punto de medición
    punto TEXT NOT NULL,  -- Nombre o código del punto
    
    -- Ubicación geográfica
    lat REAL NOT NULL,    -- Latitud (grados decimales)
    lon REAL NOT NULL,    -- Longitud (grados decimales)
    
    -- Información de red
    mnc_mcc TEXT NOT NULL,     -- Mobile Network Code + Mobile Country Code
    operator TEXT NOT NULL,    -- Nombre del operador
    
    -- Métricas de señal
    rssi INTEGER NOT NULL,     -- RSSI en dBm (valores negativos)
    
    -- Información técnica celular
    tecnologia TEXT NOT NULL,  -- GSM, UMTS, LTE, 5G NR, etc.
    cell_id TEXT NOT NULL,     -- Identificador de celda
    lac_tac TEXT,             -- LAC (2G/3G) o TAC (4G/5G)
    enb TEXT,                 -- eNodeB ID (LTE) o gNB ID (5G)
    channel TEXT,             -- Canal de frecuencia
    
    -- Información adicional
    comentario TEXT,          -- Observaciones, contexto temporal
    
    -- Auditoría
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Campos Obligatorios:**
- `punto`: Identificador del punto de medición (ej: "PT-001", "Punto Centro")
- `lat`, `lon`: Coordenadas geográficas decimales
- `mnc_mcc`: Código de red móvil (5-6 dígitos, ej: "732101")
- `operator`: Nombre del operador (ej: "CLARO", "MOVISTAR")
- `rssi`: Intensidad de señal en dBm (ej: -78, -85)
- `tecnologia`: Tecnología celular utilizada
- `cell_id`: Identificador único de la celda

**Campos Opcionales:**
- `lac_tac`: Location Area Code o Tracking Area Code
- `enb`: eNodeB ID para LTE/5G
- `channel`: Canal de frecuencia utilizado
- `comentario`: Observaciones adicionales

**Validaciones Críticas:**
- `lat` entre -90.0 y 90.0
- `lon` entre -180.0 y 180.0
- `mnc_mcc` solo números, 5-6 dígitos
- `rssi` debe ser negativo (≤ 0)
- `tecnologia` en: GSM, UMTS, 3G, LTE, 4G, 5G NR, 5G
- Campos obligatorios no pueden estar vacíos

**Índices de Rendimiento:**
```sql
-- Índices simples
CREATE INDEX idx_cellular_mission_id ON cellular_data(mission_id);
CREATE INDEX idx_cellular_operator ON cellular_data(operator);
CREATE INDEX idx_cellular_tecnologia ON cellular_data(tecnologia);
CREATE INDEX idx_cellular_rssi ON cellular_data(rssi);
CREATE INDEX idx_cellular_punto ON cellular_data(punto);
CREATE INDEX idx_cellular_cell_id ON cellular_data(cell_id);
CREATE INDEX idx_cellular_mnc_mcc ON cellular_data(mnc_mcc);

-- Índices compuestos para análisis
CREATE INDEX idx_cellular_mission_operator ON cellular_data(mission_id, operator);
CREATE INDEX idx_cellular_geo_analysis ON cellular_data(mission_id, operator, lat, lon, rssi);
CREATE INDEX idx_cellular_coverage_analysis ON cellular_data(mission_id, tecnologia, operator, rssi);
```

### 5. **operator_sheets** - Hojas de Datos de Operador

```sql
CREATE TABLE operator_sheets (
    id TEXT PRIMARY KEY,
    mission_id TEXT NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Campos:**
- `id`: Identificador único de la hoja (ej: `sheet_ghi789`)
- `mission_id`: FK a la misión parent
- `name`: Nombre descriptivo de la hoja
- `created_at`: Timestamp de creación

### 6. **operator_data_records** - Registros de Datos de Operador

```sql
CREATE TABLE operator_data_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sheet_id TEXT NOT NULL REFERENCES operator_sheets(id) ON DELETE CASCADE,
    operator_id TEXT NOT NULL,
    name TEXT NOT NULL,
    towers INTEGER NOT NULL,
    coverage TEXT NOT NULL
);
```

**Campos:**
- `sheet_id`: FK a la hoja de operador
- `operator_id`: ID interno del operador
- `name`: Nombre del operador
- `towers`: Número de torres/antenas
- `coverage`: Descripción de cobertura

### 7. **target_records** - Registros de Análisis de Objetivos

```sql
CREATE TABLE target_records (
    id TEXT PRIMARY KEY,
    mission_id TEXT NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    cellular_id INTEGER NOT NULL REFERENCES cellular_data(id),
    operator_id TEXT NOT NULL,
    match_type TEXT NOT NULL,
    confidence REAL NOT NULL,
    source_sheet TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Campos:**
- `id`: Identificador único del objetivo
- `mission_id`: FK a la misión
- `cellular_id`: FK al registro celular
- `operator_id`: ID del operador objetivo
- `match_type`: Tipo de coincidencia encontrada
- `confidence`: Nivel de confianza (0.0-1.0)
- `source_sheet`: Hoja de origen de los datos

## Relaciones entre Tablas

### Diagrama de Relaciones

```
users (1) ──────── (N) missions
   │                     │
   │                     ├── (N) cellular_data
   │                     ├── (N) operator_sheets ── (N) operator_data_records
   │                     └── (N) target_records
   │
   └── (N) roles (1)
```

### Relaciones Detalladas

1. **users ↔ roles**: Muchos a Uno
   - Un usuario pertenece a un rol
   - Un rol puede tener múltiples usuarios

2. **users ↔ missions**: Uno a Muchos (creador)
   - Un usuario puede crear múltiples misiones
   - Una misión tiene un creador (opcional)

3. **missions ↔ cellular_data**: Uno a Muchos
   - Una misión puede tener múltiples registros celulares
   - Cada registro pertenece a una misión
   - **Cascada**: Al eliminar misión, se eliminan datos celulares

4. **missions ↔ operator_sheets**: Uno a Muchos
   - Una misión puede tener múltiples hojas de operador
   - Cada hoja pertenece a una misión
   - **Cascada**: Al eliminar misión, se eliminan hojas

5. **operator_sheets ↔ operator_data_records**: Uno a Muchos
   - Una hoja puede tener múltiples registros
   - Cada registro pertenece a una hoja
   - **Cascada**: Al eliminar hoja, se eliminan registros

6. **missions ↔ target_records**: Uno a Muchos
   - Una misión puede tener múltiples objetivos
   - Cada objetivo pertenece a una misión

## Datos Iniciales

### Roles por Defecto

1. **Administrador**: Permisos completos
2. **Analista**: Permisos de lectura y análisis
3. **Operador**: Permisos básicos de operación

### Usuarios por Defecto

- **admin@kronos.com**: Administrador principal
- **analista@kronos.com**: Usuario analista
- **operador@kronos.com**: Usuario operador

### Misiones de Ejemplo

- **PX-001**: Proyecto PHOENIX - Análisis urbano
- **OP-001**: Operación GUARDIAN - Monitoreo rural
- **SC-001**: SCANHUNTER Test - Validación técnica

## Consultas Frecuentes

### 1. Datos Celulares por Misión

```sql
SELECT 
    cd.punto,
    cd.operator,
    cd.tecnologia,
    cd.rssi,
    cd.lat,
    cd.lon
FROM cellular_data cd
WHERE cd.mission_id = ?
ORDER BY cd.punto;
```

### 2. Análisis de Cobertura por Operador

```sql
SELECT 
    cd.operator,
    cd.tecnologia,
    COUNT(*) as total_mediciones,
    AVG(cd.rssi) as rssi_promedio,
    MIN(cd.rssi) as rssi_minimo,
    MAX(cd.rssi) as rssi_maximo
FROM cellular_data cd
WHERE cd.mission_id = ?
GROUP BY cd.operator, cd.tecnologia
ORDER BY cd.operator, cd.tecnologia;
```

### 3. Puntos con Señal Débil

```sql
SELECT 
    cd.punto,
    cd.operator,
    cd.tecnologia,
    cd.rssi
FROM cellular_data cd
WHERE cd.mission_id = ? AND cd.rssi < -90
ORDER BY cd.rssi ASC;
```

## Mantenimiento y Optimización

### Índices de Rendimiento

Los índices están optimizados para consultas frecuentes:
- Búsquedas por misión
- Filtros por operador y tecnología
- Análisis geográficos
- Consultas de calidad de señal

### Limpieza de Datos

```sql
-- Eliminar registros huérfanos (si existen)
DELETE FROM cellular_data 
WHERE mission_id NOT IN (SELECT id FROM missions);

-- Estadísticas de tabla
SELECT 
    COUNT(*) as total_records,
    COUNT(DISTINCT mission_id) as missions_with_data,
    COUNT(DISTINCT operator) as unique_operators,
    MIN(created_at) as oldest_record,
    MAX(created_at) as newest_record
FROM cellular_data;
```

### Respaldos

Se recomienda respaldar el archivo `kronos.db` regularmente:

```bash
# Respaldo con timestamp
cp kronos.db "kronos_backup_$(date +%Y%m%d_%H%M%S).db"

# Respaldo SQL
sqlite3 kronos.db .dump > kronos_backup.sql
```

## Migración y Versionado

- **Versión Actual**: 2.0 (con campos SCANHUNTER expandidos)
- **Script de Migración**: `Backend/database/migrate_cellular_data.py`
- **Compatibilidad**: Hacia atrás con versión 1.0

## Consideraciones de Seguridad

1. **Passwords**: Hasheadas con BCrypt
2. **Inyección SQL**: Prevenida por SQLAlchemy ORM
3. **Integridad**: Foreign Keys habilitadas
4. **Validación**: Constraints a nivel de BD y aplicación
5. **Permisos**: Sistema granular basado en roles

## Rendimiento

### Métricas Típicas

- **Inserción**: ~1000 registros/segundo para datos celulares
- **Consultas**: Sub-segundo para misiones con <10K registros
- **Índices**: Optimizados para operaciones OLAP
- **Tamaño**: ~1KB por registro celular completo

### Escalabilidad

- **SQLite límites**: 281TB teóricos, 1M registros recomendados por tabla
- **Índices**: Mantenimiento automático
- **Concurrencia**: Lecturas ilimitadas, escritura única

---

*Documentación actualizada: $(date)*
*Versión del esquema: 2.0*
*Proyecto: KRONOS - Sistema de Gestión de Misiones*