# KRONOS - Guía de Optimización de Performance para Módulo de Operadores

## Índice

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Arquitectura de Performance](#arquitectura-de-performance)
3. [Configuración SQLite Optimizada](#configuración-sqlite-optimizada)
4. [Estrategias de Indexación](#estrategias-de-indexación)
5. [Optimización de Consultas](#optimización-de-consultas)
6. [Procesamiento de Archivos Grandes](#procesamiento-de-archivos-grandes)
7. [Monitoreo y Mantenimiento](#monitoreo-y-mantenimiento)
8. [Benchmarks y Métricas](#benchmarks-y-métricas)
9. [Solución de Problemas Comunes](#solución-de-problemas-comunes)

---

## Resumen Ejecutivo

### Objetivos de Performance

El esquema optimizado de KRONOS está diseñado para manejar eficientemente:

- **Archivos hasta 20MB** con miles de registros
- **Búsquedas por número telefónico** en < 50ms
- **Consultas por rango de fechas** en < 100ms
- **Agregaciones por operador/celda** en < 200ms
- **Detección de duplicados** en tiempo real
- **Procesamiento concurrente** de múltiples archivos

### Métricas Objetivo

| Operación | Tiempo Objetivo | Registros Procesados |
|-----------|-----------------|---------------------|
| Inserción de archivo 20MB | < 30 segundos | 50,000 registros |
| Búsqueda por número | < 50ms | Cualquier cantidad |
| Consulta temporal (1 mes) | < 100ms | 1M+ registros |
| Análisis de cobertura | < 200ms | 500K+ registros |
| Detección de duplicados | < 10ms | Por registro |

---

## Arquitectura de Performance

### Diseño de Tabla Optimizado

```sql
-- Estrategia de particionamiento conceptual por operador
-- SQLite no soporta particionamiento nativo, pero usamos índices optimizados

-- Tabla principal con campos calculados para performance
CREATE TABLE operator_cellular_data (
    -- Campos de alta frecuencia de consulta al principio
    mission_id TEXT NOT NULL,
    numero_telefono TEXT NOT NULL,
    fecha_hora_inicio DATETIME NOT NULL,
    operator TEXT NOT NULL,
    
    -- Campo calculado para evitar SUM en consultas frecuentes
    trafico_total_bytes BIGINT GENERATED ALWAYS AS 
        (trafico_subida_bytes + trafico_bajada_bytes) STORED,
    
    -- Otros campos...
);
```

### Jerarquía de Índices

```
Nivel 1: Índices primarios (búsquedas más frecuentes)
├── idx_cellular_numero_mission (numero_telefono, mission_id)
├── idx_cellular_mission_operator (mission_id, operator)
└── idx_cellular_fecha_hora (fecha_hora_inicio)

Nivel 2: Índices secundarios (consultas específicas)
├── idx_cellular_celda_id (celda_id)
├── idx_cellular_tecnologia (tecnologia)
└── idx_cellular_geolocation (latitud, longitud)

Nivel 3: Índices compuestos (análisis complejos)
├── idx_cellular_numero_fecha (numero_telefono, fecha_hora_inicio)
├── idx_cellular_operator_fecha (operator, fecha_hora_inicio)
└── idx_cellular_geo_analysis (mission_id, operator, latitud, longitud, rssi)
```

---

## Configuración SQLite Optimizada

### Configuración de Inicio

```sql
-- Configuración crítica para performance
PRAGMA foreign_keys = ON;           -- Integridad referencial
PRAGMA journal_mode = WAL;          -- Concurrencia de lectura
PRAGMA synchronous = NORMAL;        -- Balance seguridad/velocidad
PRAGMA cache_size = 20000;          -- 20MB cache (para archivos grandes)
PRAGMA temp_store = MEMORY;         -- Operaciones temporales en RAM
PRAGMA mmap_size = 268435456;       -- 256MB memory mapping
PRAGMA auto_vacuum = INCREMENTAL;   -- Mantenimiento automático
```

### Configuración por Tipo de Carga

#### Para Inserción Masiva (Procesamiento de Archivos)
```sql
-- Configuración temporal durante inserción
PRAGMA synchronous = OFF;           -- Máxima velocidad (usar con cuidado)
PRAGMA journal_mode = MEMORY;       -- Journal en memoria
PRAGMA cache_size = 50000;          -- Cache más grande (50MB)
PRAGMA temp_store = MEMORY;
-- IMPORTANTE: Restaurar configuración normal después
```

#### Para Consultas Analíticas
```sql
-- Configuración para análisis complejos
PRAGMA cache_size = 30000;          -- Cache grande para joins
PRAGMA temp_store = MEMORY;
PRAGMA mmap_size = 536870912;       -- 512MB memory mapping
PRAGMA optimize;                    -- Actualizar estadísticas
```

#### Para Operaciones Concurrentes
```sql
-- Configuración para múltiples lectores
PRAGMA journal_mode = WAL;          -- Esencial para concurrencia
PRAGMA synchronous = NORMAL;
PRAGMA wal_autocheckpoint = 1000;   -- Checkpoint cada 1000 páginas
PRAGMA wal_checkpoint(TRUNCATE);    -- Limpiar WAL periódicamente
```

---

## Estrategias de Indexación

### Índices por Frecuencia de Uso

#### Alta Frecuencia (Creados automáticamente)
```sql
-- Búsquedas por número telefónico (90% de consultas)
CREATE INDEX idx_cellular_numero_telefono ON operator_cellular_data(numero_telefono);
CREATE INDEX idx_cellular_numero_mission ON operator_cellular_data(numero_telefono, mission_id);

-- Filtros por misión y operador (80% de consultas)
CREATE INDEX idx_cellular_mission_operator ON operator_cellular_data(mission_id, operator);

-- Consultas temporales (70% de consultas)
CREATE INDEX idx_cellular_fecha_hora ON operator_cellular_data(fecha_hora_inicio);
```

#### Media Frecuencia
```sql
-- Análisis por celda (50% de consultas)
CREATE INDEX idx_cellular_celda_id ON operator_cellular_data(celda_id);

-- Filtros por tecnología (30% de consultas)
CREATE INDEX idx_cellular_tecnologia ON operator_cellular_data(tecnologia);

-- Análisis geoespacial (20% de consultas)
CREATE INDEX idx_cellular_geolocation ON operator_cellular_data(latitud, longitud) 
    WHERE latitud IS NOT NULL AND longitud IS NOT NULL;
```

#### Baja Frecuencia (Crear según necesidad)
```sql
-- Análisis de tráfico (10% de consultas)
CREATE INDEX idx_cellular_trafico_total ON operator_cellular_data(trafico_total_bytes);

-- Análisis de calidad de señal (5% de consultas)
CREATE INDEX idx_cellular_calidad_senal ON operator_cellular_data(calidad_senal)
    WHERE calidad_senal IS NOT NULL;
```

### Índices Compuestos Estratégicos

#### Para Análisis Temporal por Usuario
```sql
-- Optimiza: SELECT * FROM data WHERE numero = ? AND fecha BETWEEN ? AND ?
CREATE INDEX idx_cellular_numero_fecha ON operator_cellular_data(
    numero_telefono, fecha_hora_inicio
);

-- Con datos adicionales para evitar lookup
CREATE INDEX idx_cellular_numero_fecha_covering ON operator_cellular_data(
    numero_telefono, fecha_hora_inicio, operator, celda_id, trafico_total_bytes
);
```

#### Para Análisis Geoespacial
```sql
-- Optimiza consultas de cobertura por zona
CREATE INDEX idx_cellular_geo_analysis ON operator_cellular_data(
    mission_id, operator, latitud, longitud, calidad_senal
) WHERE latitud IS NOT NULL AND longitud IS NOT NULL;
```

#### Para Análisis de Performance
```sql
-- Para reportes de calidad de datos
CREATE INDEX idx_cellular_file_quality ON operator_cellular_data(
    file_upload_id, latitud, trafico_total_bytes
);
```

### Mantenimiento de Índices

```sql
-- Script de mantenimiento semanal
REINDEX;                            -- Reconstruir índices fragmentados
ANALYZE;                            -- Actualizar estadísticas del optimizador
PRAGMA optimize;                    -- Optimización automática
PRAGMA integrity_check;             -- Verificar integridad
```

---

## Optimización de Consultas

### Patrones de Consulta Optimizados

#### 1. Búsqueda por Número Telefónico
```sql
-- ✅ OPTIMIZADO: Usa índice específico
SELECT * FROM operator_cellular_data 
WHERE numero_telefono = ?
  AND mission_id = ?
ORDER BY fecha_hora_inicio DESC
LIMIT 100;

-- ❌ EVITAR: Búsqueda con LIKE sin prefijo
SELECT * FROM operator_cellular_data 
WHERE numero_telefono LIKE '%1234567';

-- ✅ ALTERNATIVA: Usar índice con prefijo
SELECT * FROM operator_cellular_data 
WHERE numero_telefono LIKE '5730%';
```

#### 2. Consultas Temporales
```sql
-- ✅ OPTIMIZADO: Rango de fechas con índice
SELECT numero_telefono, COUNT(*) as sesiones
FROM operator_cellular_data 
WHERE fecha_hora_inicio BETWEEN ? AND ?
  AND mission_id = ?
GROUP BY numero_telefono;

-- ❌ EVITAR: Funciones en WHERE
SELECT * FROM operator_cellular_data 
WHERE DATE(fecha_hora_inicio) = '2024-04-19';

-- ✅ ALTERNATIVA: Usar rangos
SELECT * FROM operator_cellular_data 
WHERE fecha_hora_inicio >= '2024-04-19 00:00:00'
  AND fecha_hora_inicio < '2024-04-20 00:00:00';
```

#### 3. Agregaciones Optimizadas
```sql
-- ✅ OPTIMIZADO: Con índice compuesto
SELECT 
    operator,
    COUNT(*) as total_registros,
    SUM(trafico_total_bytes) as trafico_total,
    COUNT(DISTINCT numero_telefono) as usuarios_unicos
FROM operator_cellular_data 
WHERE mission_id = ?
GROUP BY operator;

-- ✅ MÁS OPTIMIZADO: Con WHERE índice específico
SELECT 
    COUNT(*) as registros_claro,
    SUM(trafico_total_bytes) as trafico_claro,
    COUNT(DISTINCT numero_telefono) as usuarios_claro
FROM operator_cellular_data 
WHERE mission_id = ? AND operator = 'CLARO';
```

### Uso de Vistas Materializadas (Simuladas)

```sql
-- Crear tabla de estadísticas pre-calculadas
CREATE TABLE stats_daily_activity AS
SELECT 
    DATE(fecha_hora_inicio) as fecha,
    mission_id,
    operator,
    COUNT(*) as total_sesiones,
    COUNT(DISTINCT numero_telefono) as usuarios_activos,
    SUM(trafico_total_bytes) as trafico_total,
    AVG(trafico_total_bytes) as trafico_promedio
FROM operator_cellular_data
GROUP BY DATE(fecha_hora_inicio), mission_id, operator;

-- Índice para consultas rápidas en estadísticas
CREATE INDEX idx_stats_fecha_mission ON stats_daily_activity(fecha, mission_id);

-- Trigger para mantener actualizada la tabla de estadísticas
CREATE TRIGGER update_stats_on_insert
    AFTER INSERT ON operator_cellular_data
BEGIN
    INSERT OR REPLACE INTO stats_daily_activity (...)
    -- Lógica de actualización...
END;
```

### Query Hints y Optimización Forzada

```sql
-- Forzar uso de índice específico con INDEXED BY
SELECT * FROM operator_cellular_data INDEXED BY idx_cellular_numero_telefono
WHERE numero_telefono = '573001234567';

-- Usar EXPLAIN QUERY PLAN para verificar
EXPLAIN QUERY PLAN 
SELECT numero_telefono, COUNT(*) 
FROM operator_cellular_data 
WHERE mission_id = ? AND fecha_hora_inicio >= ?
GROUP BY numero_telefono;
```

---

## Procesamiento de Archivos Grandes

### Estrategia de Procesamiento por Lotes

```python
# Ejemplo en Python para procesamiento optimizado
def process_large_file(file_path, batch_size=1000):
    """
    Procesar archivos grandes en lotes para optimizar memoria y performance
    """
    connection = sqlite3.connect('kronos.db')
    
    # Configuración temporal para inserción masiva
    connection.execute("PRAGMA synchronous = OFF")
    connection.execute("PRAGMA journal_mode = MEMORY")
    connection.execute("PRAGMA cache_size = 50000")
    
    try:
        with connection:
            batch = []
            for row in read_csv_streaming(file_path):
                processed_row = transform_row(row)
                batch.append(processed_row)
                
                if len(batch) >= batch_size:
                    insert_batch(connection, batch)
                    batch = []
            
            # Insertar último lote
            if batch:
                insert_batch(connection, batch)
                
    finally:
        # Restaurar configuración normal
        connection.execute("PRAGMA synchronous = NORMAL")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("ANALYZE")
```

### Prevención de Duplicados Eficiente

```sql
-- 1. Usar INSERT OR IGNORE para evitar duplicados
INSERT OR IGNORE INTO operator_cellular_data (
    file_upload_id, record_hash, numero_telefono, ...
) VALUES (?, ?, ?, ...);

-- 2. Verificación previa con EXISTS (para casos críticos)
INSERT INTO operator_cellular_data (...)
SELECT ?, ?, ?, ...
WHERE NOT EXISTS (
    SELECT 1 FROM operator_cellular_data 
    WHERE file_upload_id = ? AND record_hash = ?
);

-- 3. Usar tabla temporal para verificación masiva
CREATE TEMP TABLE temp_new_records AS 
SELECT * FROM csv_import_table;

-- Eliminar duplicados usando LEFT JOIN
DELETE FROM temp_new_records 
WHERE rowid IN (
    SELECT tnr.rowid 
    FROM temp_new_records tnr
    LEFT JOIN operator_cellular_data ocd ON tnr.record_hash = ocd.record_hash
    WHERE ocd.id IS NOT NULL
);

-- Insertar solo registros únicos
INSERT INTO operator_cellular_data SELECT * FROM temp_new_records;
```

### Validación de Datos Durante Inserción

```sql
-- Crear tabla de errores para logging
CREATE TABLE data_validation_errors (
    file_upload_id TEXT,
    row_number INTEGER,
    field_name TEXT,
    field_value TEXT,
    error_type TEXT,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Usar CHECK constraints para validación automática
INSERT INTO operator_cellular_data (...)
SELECT 
    file_upload_id,
    CASE 
        WHEN LENGTH(numero_telefono) < 10 THEN NULL
        ELSE numero_telefono
    END,
    -- Validaciones adicionales...
FROM temp_csv_data
WHERE numero_telefono GLOB '[0-9]*'  -- Solo números válidos
  AND latitud BETWEEN -90 AND 90     -- Coordenadas válidas
  AND longitud BETWEEN -180 AND 180;
```

---

## Monitoreo y Mantenimiento

### Métricas de Performance

#### Consultas de Monitoreo Automático

```sql
-- 1. Estadísticas de uso de base de datos
SELECT 
    'database_size_mb' as metric,
    ROUND((SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()) / 1024.0 / 1024.0, 2) as value
UNION ALL
SELECT 
    'free_pages',
    (SELECT freelist_count FROM pragma_freelist_count())
UNION ALL
SELECT 
    'cache_hit_ratio_percent',
    ROUND((SELECT cache_hit FROM pragma_cache_spill(-1)) * 100, 2);

-- 2. Performance de consultas frecuentes
.timer ON
SELECT COUNT(*) FROM operator_cellular_data WHERE numero_telefono = '573001234567';
.timer OFF

-- 3. Análisis de fragmentación de índices
SELECT 
    name,
    (SELECT COUNT(*) FROM pragma_index_info(name)) as columns,
    (SELECT COUNT(*) FROM pragma_index_list(tbl_name) WHERE name = sqlite_master.name) as on_table
FROM sqlite_master 
WHERE type = 'index' AND name LIKE 'idx_%'
ORDER BY name;
```

#### Scripts de Mantenimiento Automatizado

```sql
-- Script de mantenimiento diario
CREATE TABLE maintenance_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    maintenance_type TEXT NOT NULL,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME,
    status TEXT DEFAULT 'RUNNING',
    details TEXT
);

-- Rutina de limpieza automática
DELETE FROM file_processing_logs 
WHERE logged_at < datetime('now', '-30 days');

DELETE FROM operator_data_audit 
WHERE audited_at < datetime('now', '-90 days');

-- Actualización de estadísticas del optimizador
ANALYZE operator_cellular_data;
ANALYZE operator_call_data;
ANALYZE operator_data_sheets;

-- Limpieza de WAL si es muy grande
PRAGMA wal_checkpoint(TRUNCATE);
```

### Alertas de Performance

```sql
-- Detectar consultas lentas potenciales
SELECT 
    'large_table_scan' as alert_type,
    COUNT(*) as records,
    'operator_cellular_data may need index optimization' as message
FROM operator_cellular_data
WHERE COUNT(*) > 1000000

UNION ALL

SELECT 
    'high_fragmentation',
    (SELECT freelist_count FROM pragma_freelist_count()),
    'Database may need VACUUM' as message
WHERE (SELECT freelist_count FROM pragma_freelist_count()) > 1000;
```

---

## Benchmarks y Métricas

### Test de Performance Estándar

```sql
-- 1. Test de inserción (1000 registros)
.timer ON
INSERT INTO operator_cellular_data (mission_id, numero_telefono, fecha_hora_inicio, operator, ...)
WITH RECURSIVE test_data(n) AS (
    SELECT 1
    UNION ALL
    SELECT n + 1 FROM test_data WHERE n < 1000
)
SELECT 
    'test_mission',
    '57300' || printf('%07d', n),
    datetime('2024-04-19 08:00:00', '+' || (n * 3) || ' seconds'),
    'CLARO',
    ...
FROM test_data;
.timer OFF

-- 2. Test de búsqueda por número
.timer ON
SELECT * FROM operator_cellular_data 
WHERE numero_telefono = '573001234567' AND mission_id = 'test_mission';
.timer OFF

-- 3. Test de agregación
.timer ON
SELECT 
    operator,
    COUNT(*) as total,
    SUM(trafico_total_bytes) as trafico_total
FROM operator_cellular_data 
WHERE mission_id = 'test_mission'
GROUP BY operator;
.timer OFF
```

### Métricas Objetivo por Operación

| Operación | Registros | Tiempo Objetivo | Comando de Test |
|-----------|-----------|-----------------|-----------------|
| Inserción individual | 1 | < 1ms | `INSERT INTO ... VALUES (...)` |
| Inserción por lotes | 1,000 | < 100ms | `INSERT INTO ... SELECT ... UNION ALL ...` |
| Búsqueda por número | Cualquiera | < 50ms | `SELECT * WHERE numero_telefono = ?` |
| Agregación por operador | 100K+ | < 200ms | `SELECT operator, COUNT(*) GROUP BY operator` |
| Consulta geoespacial | 50K+ | < 300ms | `SELECT * WHERE latitud BETWEEN ? AND ?` |

---

## Solución de Problemas Comunes

### Problema 1: Consultas Lentas

#### Síntomas
- Consultas que toman más de 1 segundo
- Alta utilización de CPU durante consultas
- Aplicación no responsiva

#### Diagnóstico
```sql
-- Verificar plan de consulta
EXPLAIN QUERY PLAN 
SELECT numero_telefono, COUNT(*) 
FROM operator_cellular_data 
WHERE mission_id = 'slow_mission'
GROUP BY numero_telefono;

-- Verificar uso de índices
.schema operator_cellular_data
```

#### Soluciones
```sql
-- 1. Crear índice específico si no existe
CREATE INDEX IF NOT EXISTS idx_cellular_mission_numero 
ON operator_cellular_data(mission_id, numero_telefono);

-- 2. Actualizar estadísticas
ANALYZE operator_cellular_data;

-- 3. Verificar fragmentación
PRAGMA integrity_check;
REINDEX operator_cellular_data;
```

### Problema 2: Base de Datos Crece Demasiado

#### Síntomas
- Archivo .db mayor a 1GB sin datos proporcionales
- Operaciones de inserción lentas
- Mucho espacio libre reportado

#### Diagnóstico
```sql
-- Verificar páginas libres
SELECT 
    (SELECT page_count FROM pragma_page_count()) as total_pages,
    (SELECT freelist_count FROM pragma_freelist_count()) as free_pages,
    ROUND((SELECT freelist_count FROM pragma_freelist_count()) * 100.0 / 
          (SELECT page_count FROM pragma_page_count()), 2) as fragmentation_percent;
```

#### Soluciones
```sql
-- 1. VACUUM completo (requiere espacio temporal)
VACUUM;

-- 2. VACUUM incremental (más seguro)
PRAGMA auto_vacuum = INCREMENTAL;
PRAGMA incremental_vacuum(1000);

-- 3. Configurar auto-vacuum para el futuro
PRAGMA auto_vacuum = INCREMENTAL;
```

### Problema 3: Errores de Foreign Key

#### Síntomas
- Errores "FOREIGN KEY constraint failed"
- No se pueden insertar registros
- Problemas durante migración

#### Diagnóstico
```sql
-- Verificar integridad referencial
PRAGMA foreign_key_check;

-- Verificar estado de foreign keys
PRAGMA foreign_keys;

-- Verificar constrains específicos
SELECT * FROM operator_cellular_data 
WHERE mission_id NOT IN (SELECT id FROM missions);
```

#### Soluciones
```sql
-- 1. Limpiar registros huérfanos antes de habilitar FK
DELETE FROM operator_cellular_data 
WHERE mission_id NOT IN (SELECT id FROM missions);

-- 2. Deshabilitar temporalmente para limpieza
PRAGMA foreign_keys = OFF;
-- Ejecutar operaciones de limpieza
PRAGMA foreign_keys = ON;

-- 3. Verificar orden de inserción
-- Siempre insertar en orden: missions -> users -> operator_data_sheets -> cellular_data
```

### Problema 4: WAL File Muy Grande

#### Síntomas
- Archivo .db-wal mayor a 100MB
- Performance degradada en consultas
- Espacio en disco insuficiente

#### Diagnóstico
```sql
-- Verificar tamaño de WAL
.dbinfo

-- Verificar configuración de checkpoint
PRAGMA wal_autocheckpoint;
```

#### Soluciones
```sql
-- 1. Checkpoint manual inmediato
PRAGMA wal_checkpoint(TRUNCATE);

-- 2. Configurar checkpoint automático más frecuente
PRAGMA wal_autocheckpoint = 1000;

-- 3. Cambiar a modo DELETE temporalmente
PRAGMA journal_mode = DELETE;
PRAGMA journal_mode = WAL;  -- Regresa a WAL con WAL limpio
```

---

## Configuración de Producción Recomendada

### Configuración Inicial de Base de Datos

```sql
-- Configuración óptima para producción
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 20000;           -- 20MB
PRAGMA temp_store = MEMORY;
PRAGMA mmap_size = 268435456;        -- 256MB
PRAGMA auto_vacuum = INCREMENTAL;
PRAGMA wal_autocheckpoint = 1000;
PRAGMA optimize;
```

### Script de Mantenimiento Semanal

```bash
#!/bin/bash
# maintenance_weekly.sh

echo "Starting KRONOS database maintenance..."

sqlite3 kronos.db << EOF
-- Actualizar estadísticas
ANALYZE;

-- Limpieza de logs antiguos
DELETE FROM file_processing_logs WHERE logged_at < datetime('now', '-30 days');
DELETE FROM operator_data_audit WHERE audited_at < datetime('now', '-90 days');

-- Checkpoint WAL
PRAGMA wal_checkpoint(TRUNCATE);

-- Vacuum incremental si es necesario
PRAGMA incremental_vacuum(1000);

-- Verificar integridad
PRAGMA integrity_check;

-- Optimización final
PRAGMA optimize;

SELECT 'Maintenance completed at ' || datetime('now');
EOF

echo "Maintenance completed."
```

### Monitoreo de Alerts

```sql
-- Query para dashboard de monitoring
SELECT 
    'db_size_mb' as metric,
    ROUND((SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()) / 1024.0 / 1024.0, 2) as value,
    CASE WHEN ROUND((SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()) / 1024.0 / 1024.0, 2) > 1000 THEN 'WARNING' ELSE 'OK' END as status
UNION ALL
SELECT 
    'fragmentation_percent',
    ROUND((SELECT freelist_count FROM pragma_freelist_count()) * 100.0 / (SELECT page_count FROM pragma_page_count()), 2),
    CASE WHEN ROUND((SELECT freelist_count FROM pragma_freelist_count()) * 100.0 / (SELECT page_count FROM pragma_page_count()), 2) > 10 THEN 'WARNING' ELSE 'OK' END
UNION ALL
SELECT 
    'total_records',
    (SELECT COUNT(*) FROM operator_cellular_data),
    'INFO'
UNION ALL
SELECT 
    'daily_inserts_last_7d',
    (SELECT COUNT(*) FROM operator_cellular_data WHERE created_at > datetime('now', '-7 days')),
    'INFO';
```

Esta guía proporciona una base sólida para optimizar el performance del módulo de datos de operadores en KRONOS. La implementación de estas estrategias debería resultar en un sistema capaz de manejar eficientemente grandes volúmenes de datos de operadores celulares con tiempos de respuesta óptimos.