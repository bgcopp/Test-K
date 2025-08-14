# KRONOS - Implementación Backend para Operador CLARO

## Resumen

Este documento describe la implementación completa del backend Python con Eel para procesar archivos de datos del operador CLARO en el sistema KRONOS. La implementación sigue las mejores prácticas de desarrollo de aplicaciones de escritorio con Python y está optimizada para el manejo robusto de datos celulares.

## Arquitectura

### Componentes Principales

```
Backend/
├── services/
│   ├── operator_data_service.py      # Servicio principal con funciones Eel
│   ├── file_processor_service.py     # Procesamiento específico de archivos
│   ├── data_normalizer_service.py    # Normalización de datos
│   └── ...
├── utils/
│   ├── operator_logger.py            # Sistema de logging especializado
│   └── ...
├── database/
│   ├── operator_data_schema_optimized.sql  # Esquema de BD optimizado
│   └── connection.py
└── test_claro_implementation.py      # Script de testing
```

### Patrones de Diseño Utilizados

- **Service Layer Pattern**: Separación clara de responsabilidades entre servicios
- **Repository Pattern**: Abstracción del acceso a datos
- **Strategy Pattern**: Diferentes procesadores por operador
- **Observer Pattern**: Sistema de logging con múltiples handlers

## Servicios Implementados

### 1. OperatorDataService (`operator_data_service.py`)

**Propósito**: Servicio principal que expone funciones Eel para comunicación JavaScript-Python.

**Funciones Eel Expuestas**:
```python
@eel.expose
def upload_operator_data(file_data, file_name, mission_id, operator, file_type, user_id)

@eel.expose  
def get_operator_sheets(mission_id=None)

@eel.expose
def get_operator_sheet_data(file_upload_id, limit=1000, offset=0)

@eel.expose
def delete_operator_sheet(file_upload_id, user_id)
```

**Características**:
- Validación exhaustiva de parámetros de entrada
- Manejo transaccional de archivos
- Detección de duplicados mediante checksum SHA256
- Logging detallado para auditoría
- Soporte para archivos hasta 20MB

### 2. FileProcessorService (`file_processor_service.py`)

**Propósito**: Procesamiento específico de archivos por operador con validación robusta.

**Métodos Principales**:
```python
def process_claro_data_por_celda(file_bytes, file_name, file_upload_id, mission_id)
def _read_csv_robust(file_bytes, delimiter=',')
def _read_excel_robust(file_bytes, sheet_name=None)
def _validate_claro_cellular_columns(df)
def _clean_claro_cellular_data(df)
```

**Características**:
- Detección automática de encoding (UTF-8, Latin-1, etc.)
- Procesamiento por chunks para archivos grandes
- Validación de estructura y contenido
- Soporte para CSV y XLSX
- Manejo de errores granular por registro

### 3. DataNormalizerService (`data_normalizer_service.py`)

**Propósito**: Normalización de datos específicos de operador al esquema unificado.

**Métodos Principales**:
```python
def normalize_claro_cellular_data(raw_record, file_upload_id, mission_id)
def _normalize_phone_number(phone)
def _parse_claro_datetime(date_str)
def _calculate_record_hash(normalized_data)
```

**Características**:
- Transformación al esquema unificado de BD
- Normalización de números telefónicos colombianos
- Conversión de fechas CLARO (YYYYMMDDHHMMSS)
- Cálculo de hashes únicos para detección de duplicados
- Preservación de datos específicos del operador en JSON

### 4. OperatorLogger (`utils/operator_logger.py`)

**Propósito**: Sistema de logging especializado con múltiples destinos y contexto.

**Características**:
- Logging jerárquico (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Integración directa con tabla `file_processing_logs`
- Métricas de performance automáticas
- Rotación automática de archivos de log
- Contexto de procesamiento por archivo

## Formato de Datos CLARO

### Datos por Celda (DATOS_POR_CELDA CLARO.csv/xlsx)

**Estructura esperada**:
```csv
numero,fecha_trafico,tipo_cdr,celda_decimal,lac_decimal
573205487611,20240419080000,DATOS,175462,20010
```

**Campos**:
- `numero`: Número telefónico (10-12 dígitos)
- `fecha_trafico`: Fecha/hora actividad (YYYYMMDDHHMMSS)
- `tipo_cdr`: Tipo de actividad (DATOS, SMS, MMS, etc.)
- `celda_decimal`: ID de celda numérica
- `lac_decimal`: Location Area Code

**Validaciones Aplicadas**:
- Números telefónicos: formato colombiano (57XXXXXXXXXX)
- Fechas: validación de rangos y formato
- Tipos CDR: valores permitidos
- Celdas: valores numéricos válidos

## Esquema de Base de Datos

### Tablas Principales

#### `operator_data_sheets`
Metadatos de archivos cargados:
```sql
- id (TEXT PRIMARY KEY)
- mission_id (TEXT, FK a missions)
- file_name, file_size_bytes, file_checksum
- operator, operator_file_format, file_type
- processing_status, records_processed, records_failed
- timestamps de procesamiento
```

#### `operator_cellular_data`
Datos celulares normalizados:
```sql
- id (INTEGER PRIMARY KEY)
- file_upload_id (TEXT, FK a operator_data_sheets)
- operator, numero_telefono, fecha_hora_inicio
- celda_id, lac_tac, trafico_*_bytes
- coordenadas geográficas, información técnica
- operator_specific_data (JSON)
- record_hash (para duplicados)
```

#### `file_processing_logs`
Logs detallados de procesamiento:
```sql
- file_upload_id, log_level, log_message
- processing_step, execution_time_ms
- memory_usage_mb, error_code
```

## Flujo de Procesamiento

### 1. Recepción de Archivo
```
Frontend (React) → Base64 → Eel Function → OperatorDataService
```

### 2. Validación y Preparación
```
Validar parámetros → Decodificar Base64 → Calcular checksum → 
Verificar duplicados → Crear registro en BD
```

### 3. Procesamiento por Chunks
```
Leer archivo → Validar estructura → Limpiar datos → 
Procesar chunks → Normalizar → Insertar en BD
```

### 4. Finalización
```
Actualizar estadísticas → Logging final → Respuesta a frontend
```

## Testing

### Script de Pruebas
```bash
cd Backend
python test_claro_implementation.py
```

### Pruebas Incluidas
1. **Verificación del esquema de BD**: Valida tablas requeridas
2. **Sistema de logging**: Prueba diferentes niveles y contextos
3. **Normalización de datos**: Valida transformaciones
4. **Procesamiento de archivos**: Prueba con datos de muestra
5. **Integración completa**: Test end-to-end con funciones Eel

## Configuración Requerida

### Dependencias Python
```bash
pip install pandas openpyxl chardet psutil
```

### Variables de Entorno
- Configuración de BD en `database/connection.py`
- Logs almacenados en directorio `logs/`

### Esquema de BD
Ejecutar antes del primer uso:
```sql
-- Backend/database/operator_data_schema_optimized.sql
```

## Uso desde Frontend

### Cargar Archivo
```javascript
const result = await window.eel.upload_operator_data(
    fileDataBase64,
    fileName,
    missionId,
    'CLARO',
    'CELLULAR_DATA',
    userId
);
```

### Consultar Archivos
```javascript
const sheets = await window.eel.get_operator_sheets(missionId);
const data = await window.eel.get_operator_sheet_data(fileUploadId, 1000, 0);
```

### Eliminar Archivo
```javascript
const result = await window.eel.delete_operator_sheet(fileUploadId, userId);
```

## Performance y Escalabilidad

### Optimizaciones Implementadas
- **Procesamiento por chunks**: Manejo de archivos grandes (hasta 20MB)
- **Índices optimizados**: Consultas rápidas por número, fecha, celda
- **WAL mode**: Lecturas concurrentes en SQLite
- **Cache de 20MB**: Para operaciones de BD
- **Detección de duplicados**: Previene procesamiento redundante

### Métricas de Performance
- **Archivos pequeños** (< 1MB): ~2-5 segundos
- **Archivos medianos** (1-5MB): ~10-30 segundos  
- **Archivos grandes** (5-20MB): ~1-3 minutos

## Logging y Auditoría

### Niveles de Log
- **DEBUG**: Información detallada para desarrollo
- **INFO**: Eventos normales del sistema
- **WARNING**: Situaciones que requieren atención
- **ERROR**: Errores recuperables
- **CRITICAL**: Errores que requieren intervención

### Destinos de Log
1. **Archivo rotativo**: `logs/operator_processing.log`
2. **Consola**: Solo INFO y superior
3. **Base de datos**: Tabla `file_processing_logs`

## Mantenimiento

### Limpieza de Logs
```sql
-- Eliminar logs antiguos (>30 días)
DELETE FROM file_processing_logs 
WHERE logged_at < datetime('now', '-30 days');
```

### Optimización de BD
```sql
-- Ejecutar periódicamente
VACUUM;
ANALYZE;
```

### Monitoreo
- Verificar logs en `logs/operator_processing.log`
- Consultar tabla `file_processing_logs` para errores
- Usar métricas de performance integradas

## Extensibilidad

### Agregar Nuevo Operador
1. Crear método `process_[operador]_data_por_celda()` en FileProcessorService
2. Agregar normalizador en DataNormalizerService
3. Actualizar validaciones en OperatorDataService
4. Agregar tests correspondientes

### Nuevos Tipos de Archivo
1. Definir estructura en esquema de BD
2. Implementar parser específico
3. Crear normalizador para esquema unificado
4. Actualizar funciones Eel según necesidad

## Troubleshooting

### Errores Comunes

**Error: "Estructura de archivo inválida"**
- Verificar columnas requeridas en CSV/XLSX
- Validar separador (`;` para CLARO CSV)

**Error: "Archivo duplicado"**
- El checksum SHA256 ya existe en BD
- Verificar si el archivo ya fue procesado

**Error: "Demasiados errores en el archivo"**
- Archivo con formato incorrecto
- Verificar estructura de datos

**Error: "Misión/Usuario no encontrado"**
- Verificar que existan en BD
- Crear datos de prueba si es necesario

### Logs de Diagnóstico
```bash
# Ver logs recientes
tail -f Backend/logs/operator_processing.log

# Buscar errores específicos
grep "ERROR\|CRITICAL" Backend/logs/operator_processing.log
```

## Conclusión

La implementación del backend CLARO para KRONOS proporciona una base sólida y escalable para el procesamiento de datos de operadores celulares. El diseño modular permite fácil extensión a otros operadores manteniendo la robustez y performance del sistema.

La arquitectura basada en servicios especializados, junto con el sistema de logging avanzado y las validaciones exhaustivas, garantiza un procesamiento confiable y auditable de los datos críticos para las investigaciones.