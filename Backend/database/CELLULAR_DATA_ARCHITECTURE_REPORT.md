# REPORTE DE ARQUITECTURA: DISEÑO EXPANDIDO DE DATOS CELULARES - KRONOS

## RESUMEN EJECUTIVO

Como arquitecto de base de datos SQLite especializado, he completado el análisis y diseño de la estructura expandida para almacenar datos celulares en el sistema KRONOS. El diseño propuesto transforma la tabla `cellular_data` existente para soportar todos los campos identificados en los archivos SCANHUNTER, manteniendo la integridad, rendimiento y escalabilidad del sistema.

## ANÁLISIS DE LA ESTRUCTURA ACTUAL

### Fortalezas Identificadas
- ✅ Schema bien normalizado con integridad referencial sólida
- ✅ Índices estratégicos para consultas frecuentes
- ✅ Triggers inteligentes para auditoría y limpieza automática
- ✅ Configuración SQLite optimizada (WAL, cache, mmap)
- ✅ Modelos SQLAlchemy bien estructurados con validaciones

### Limitaciones de la Tabla Actual
```sql
-- ESTRUCTURA ACTUAL (LIMITADA)
CREATE TABLE cellular_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id TEXT NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    signal INTEGER NOT NULL,      -- Solo RSSI
    operator TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Problemas identificados:**
- Solo almacena 5 campos de los 13 identificados en SCANHUNTER
- No captura información técnica crítica (Cell ID, LAC/TAC, ENB)
- Falta contexto del punto de medición
- No diferencia entre tipos de tecnología
- Pérdida de datos valiosos para análisis avanzados

## DISEÑO PROPUESTO: TABLA EXPANDIDA

### Estructura Completa
```sql
CREATE TABLE cellular_data (
    -- Identificación
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id TEXT NOT NULL,
    
    -- Información del punto
    punto TEXT NOT NULL,                    -- Nombre/código del punto
    
    -- Ubicación geográfica
    lat REAL NOT NULL,                     -- Latitud
    lon REAL NOT NULL,                     -- Longitud
    
    -- Información de red
    mnc_mcc TEXT NOT NULL,                 -- Mobile Network Code + Country Code
    operator TEXT NOT NULL,               -- Operador
    
    -- Métricas de señal
    rssi INTEGER NOT NULL,                -- RSSI en dBm
    
    -- Información técnica celular
    tecnologia TEXT NOT NULL,             -- GSM, UMTS, LTE, 5G NR
    cell_id TEXT NOT NULL,               -- ID de celda
    lac_tac TEXT,                        -- Location/Tracking Area Code
    enb TEXT,                            -- eNodeB/gNB ID
    channel TEXT,                        -- Canal de frecuencia
    
    -- Información adicional
    comentario TEXT,                     -- Observaciones
    
    -- Auditoría
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Relaciones y restricciones...
);
```

## JUSTIFICACIÓN TÉCNICA DE DECISIONES ARQUITECTÓNICAS

### 1. Tipos de Datos Elegidos

| Campo | Tipo | Justificación |
|-------|------|---------------|
| `punto` | TEXT | Nombres descriptivos pueden ser largos |
| `lat/lon` | REAL | Precisión decimal necesaria para geolocalización |
| `mnc_mcc` | TEXT | Códigos pueden tener ceros iniciales |
| `rssi` | INTEGER | Valores dBm son típicamente enteros |
| `tecnologia` | TEXT | Enum limitado con CHECK constraint |
| `cell_id` | TEXT | Cell IDs pueden ser muy grandes (>32bit) |
| `lac_tac` | TEXT | Códigos hexadecimales posibles |
| `enb` | TEXT | IDs de eNodeB pueden superar INTEGER |

### 2. Estrategia de Normalización

**Decisión: Mantener estructura desnormalizada**
- ✅ **Ventajas**: Mayor rendimiento para consultas analíticas
- ✅ **SQLite optimizado**: B-tree simple, sin JOINs complejos
- ✅ **Patrón OLAP**: Datos principalmente para lectura/análisis
- ⚠️ **Trade-off**: Ligera redundancia de operadores aceptable

**Alternativa descartada**: Normalizar operadores en tabla separada
- ❌ Overhead de JOINs en todas las consultas
- ❌ Complejidad adicional innecesaria
- ❌ SQLite no optimizado para JOINs complejos

### 3. Estrategia de Índices

**Índices simples (búsquedas directas):**
```sql
CREATE INDEX idx_cellular_mission_id ON cellular_data(mission_id);
CREATE INDEX idx_cellular_operator ON cellular_data(operator);
CREATE INDEX idx_cellular_tecnologia ON cellular_data(tecnologia);
CREATE INDEX idx_cellular_rssi ON cellular_data(rssi);
```

**Índices compuestos (consultas específicas KRONOS):**
```sql
-- Para análisis por misión y operador
CREATE INDEX idx_cellular_mission_operator ON cellular_data(mission_id, operator);

-- Para análisis geográfico
CREATE INDEX idx_cellular_location ON cellular_data(lat, lon);

-- Para análisis de cobertura avanzado
CREATE INDEX idx_cellular_geo_analysis ON cellular_data(mission_id, operator, lat, lon, rssi);
```

**Justificación de índices compuestos:**
- Consultas típicas filtran por misión + operador
- Análisis geográfico requiere lat/lon juntos
- SQLite B-tree optimizado para índices compuestos ordenados

## VALIDACIONES Y RESTRICCIONES

### 1. Validaciones Geográficas
```sql
CHECK (lat >= -90.0 AND lat <= 90.0)
CHECK (lon >= -180.0 AND lon <= 180.0)
```

### 2. Validaciones de Telecomunicaciones
```sql
-- RSSI típicamente negativo
CHECK (rssi <= 0)

-- MNC+MCC formato estándar
CHECK (mnc_mcc GLOB '[0-9]*' AND length(mnc_mcc) BETWEEN 5 AND 6)

-- Tecnologías conocidas
CHECK (tecnologia IN ('GSM', 'UMTS', '3G', 'LTE', '4G', '5G NR', '5G'))
```

### 3. Validaciones de Integridad
```sql
-- Campos obligatorios no vacíos
CHECK (length(trim(punto)) > 0)
CHECK (length(trim(operator)) > 0)

-- Campos opcionales válidos si presentes
CHECK (lac_tac IS NULL OR length(trim(lac_tac)) > 0)
```

## ESTRATEGIA DE MIGRACIÓN

### Fase 1: Migración Segura de Datos
```sql
-- 1. Crear tabla temporal con nueva estructura
-- 2. Migrar datos existentes con valores por defecto
-- 3. Intercambiar tablas atómicamente
-- 4. Recrear índices y triggers
```

### Fase 2: Actualización de Aplicación
1. **Backend**: Actualizar modelo SQLAlchemy
2. **Frontend**: Actualizar interfaces TypeScript
3. **API**: Modificar servicios de importación/exportación
4. **Testing**: Validar compatibilidad end-to-end

## OPTIMIZACIONES DE RENDIMIENTO

### 1. Configuración SQLite Optimizada
```sql
PRAGMA journal_mode = WAL;           -- Concurrencia mejorada
PRAGMA synchronous = NORMAL;         -- Balance rendimiento/seguridad
PRAGMA cache_size = 10000;          -- 10MB cache
PRAGMA mmap_size = 268435456;       -- 256MB memory mapping
```

### 2. Estrategias de Consulta
- **Preparar statements** para consultas repetitivas
- **Usar índices covering** cuando sea posible
- **Batch inserts** para importación masiva
- **ANALYZE** periódico para estadísticas actualizadas

### 3. Estimaciones de Capacidad

| Escenario | Registros | Tamaño aprox. | Rendimiento |
|-----------|-----------|---------------|-------------|
| Misión pequeña | 1,000 | 150 KB | Excelente |
| Misión mediana | 50,000 | 7.5 MB | Muy bueno |
| Misión grande | 500,000 | 75 MB | Bueno |
| Múltiples misiones | 2,000,000 | 300 MB | Aceptable* |

*Con índices apropiados y configuración optimizada

## CONSIDERACIONES DE SEGURIDAD

### 1. Prevención de SQL Injection
- ✅ Usar parámetros bound en todas las consultas
- ✅ Validación estricta en modelos SQLAlchemy
- ✅ Sanitización de datos de importación

### 2. Integridad de Datos
- ✅ Foreign keys habilitadas (PRAGMA foreign_keys=ON)
- ✅ Transacciones ACID para operaciones críticas
- ✅ Backup automático antes de migraciones

## RECOMENDACIONES DE IMPLEMENTACIÓN

### 1. Orden de Implementación Sugerido
1. **Ejecutar migración SQL** en entorno de desarrollo
2. **Actualizar modelo SQLAlchemy** con validaciones
3. **Crear interfaces TypeScript expandidas**
4. **Modificar servicios de importación**
5. **Actualizar componentes frontend**
6. **Testing exhaustivo** con datos reales
7. **Despliegue en producción** con backup completo

### 2. Monitoreo Post-Implementación
- Monitorear rendimiento de consultas frecuentes
- Validar integridad de datos importados
- Ajustar configuración SQLite según uso real
- Ejecutar ANALYZE periódicamente

### 3. Mantenimiento Recomendado
```sql
-- Semanal
PRAGMA optimize;

-- Mensual  
ANALYZE cellular_data;

-- Según necesidad
VACUUM; -- Solo si hay muchas eliminaciones
```

## BENEFICIOS ESPERADOS

### 1. Funcionales
- ✅ **Datos completos**: Todos los campos SCANHUNTER capturados
- ✅ **Análisis avanzado**: Correlaciones por tecnología, cell ID, etc.
- ✅ **Trazabilidad**: Información completa del punto de medición
- ✅ **Compatibilidad**: Soporte para importación directa de archivos

### 2. Técnicos
- ✅ **Rendimiento mantenido**: Índices optimizados para consultas específicas
- ✅ **Escalabilidad**: Diseño soporta millones de registros
- ✅ **Integridad**: Validaciones exhaustivas a nivel de BD
- ✅ **Mantenibilidad**: Estructura clara y documentada

### 3. De Negocio
- ✅ **Análisis más precisos**: Mayor granularidad de datos
- ✅ **Reportes enriquecidos**: Información técnica detallada
- ✅ **Eficiencia operativa**: Importación automática sin pérdida de datos
- ✅ **Competitividad**: Capacidades analíticas superiores

## ARCHIVOS ENTREGABLES

| Archivo | Propósito |
|---------|-----------|
| `cellular_data_migration.sql` | Script de migración completo |
| `models.py` (actualizado) | Modelo SQLAlchemy expandido |
| `cellular-data-expanded.ts` | Interfaces TypeScript |
| `cellular_data_queries.sql` | Consultas optimizadas de ejemplo |
| `CELLULAR_DATA_ARCHITECTURE_REPORT.md` | Este documento |

## CONCLUSIONES

El diseño propuesto transforma la tabla `cellular_data` de KRONOS de una estructura básica a una plataforma robusta para análisis avanzados de datos celulares. La arquitectura mantiene los principios de rendimiento de SQLite mientras expande significativamente las capacidades analíticas del sistema.

La migración propuesta es segura, reversible y mantiene la compatibilidad con el sistema existente durante la transición. Los beneficios funcionales y técnicos justifican ampliamente la inversión en esta expansión de arquitectura.

**Recomendación final**: Proceder con la implementación siguiendo el orden sugerido, comenzando con un entorno de desarrollo para validar el comportamiento antes del despliegue en producción.