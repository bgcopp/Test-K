# KRONOS - Mapeo de Campos por Operador

## Documentación Completa del Mapeo de Datos Heterogéneos

Esta documentación define cómo se mapean los campos específicos de cada operador (CLARO, MOVISTAR, TIGO, WOM) al esquema normalizado de KRONOS.

---

## TABLA DE CONTENIDOS

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Campos Unificados](#campos-unificados)
3. [Mapeo por Operador - Datos Celulares](#mapeo-por-operador---datos-celulares)
4. [Mapeo por Operador - Llamadas](#mapeo-por-operador---llamadas)
5. [Campos Específicos en JSON](#campos-específicos-en-json)
6. [Validaciones y Transformaciones](#validaciones-y-transformaciones)
7. [Ejemplos de Procesamiento](#ejemplos-de-procesamiento)

---

## RESUMEN EJECUTIVO

### Estrategia de Normalización

- **Campos Comunes**: Extraídos y normalizados en columnas específicas
- **Campos Específicos**: Almacenados en JSON para preservar información única
- **Transformaciones**: Aplicadas para homogenizar formatos y tipos de datos
- **Validaciones**: Implementadas para garantizar calidad de datos

### Operadores Soportados

| Operador | Tipos de Archivos | Características Especiales |
|----------|-------------------|---------------------------|
| CLARO | Datos, Llamadas E/S | Formato decimal para celdas |
| MOVISTAR | Datos, Llamadas Salientes | Coordenadas con precisión decimal |
| TIGO | Llamadas Mixtas | Formato truncado de celdas |
| WOM | Datos, Llamadas E/S | Bytes de tráfico detallados |

---

## CAMPOS UNIFICADOS

### Tabla: `operator_cellular_data`

| Campo Unificado | Tipo | Descripción | Fuente |
|----------------|------|-------------|---------|
| `numero_telefono` | TEXT | Número que consume datos | Normalizado de campos específicos |
| `fecha_hora_inicio` | DATETIME | Inicio de sesión de datos | Convertido a ISO format |
| `fecha_hora_fin` | DATETIME | Fin de sesión | Calculado o extraído |
| `duracion_segundos` | INTEGER | Duración de sesión | Calculado o convertido |
| `celda_id` | TEXT | Identificador de celda | Normalizado a string |
| `lac_tac` | TEXT | Location/Tracking Area Code | Extraído según tecnología |
| `trafico_subida_bytes` | BIGINT | Tráfico de subida | Convertido a bytes |
| `trafico_bajada_bytes` | BIGINT | Tráfico de bajada | Convertido a bytes |
| `latitud` | REAL | Coordenada geográfica | Convertido a decimal |
| `longitud` | REAL | Coordenada geográfica | Convertido a decimal |
| `tecnologia` | TEXT | Tecnología celular | Normalizado (LTE, 4G, 5G, etc.) |

### Tabla: `operator_call_data`

| Campo Unificado | Tipo | Descripción | Fuente |
|----------------|------|-------------|---------|
| `tipo_llamada` | TEXT | ENTRANTE/SALIENTE/MIXTA | Determinado por contexto |
| `numero_origen` | TEXT | Quien origina la llamada | Campo específico |
| `numero_destino` | TEXT | Quien recibe la llamada | Campo específico |
| `numero_objetivo` | TEXT | Número de interés investigativo | Calculado |
| `fecha_hora_llamada` | DATETIME | Timestamp de la llamada | Convertido a ISO |
| `duracion_segundos` | INTEGER | Duración de llamada | Convertido a segundos |
| `celda_origen` | TEXT | Celda donde inicia llamada | Normalizado |
| `celda_destino` | TEXT | Celda donde termina llamada | Normalizado |
| `celda_objetivo` | TEXT | Celda del número objetivo | Determinado |

---

## MAPEO POR OPERADOR - DATOS CELULARES

### CLARO - Archivos de Datos

**Archivo:** `DATOS_POR_CELDA CLARO.csv`

**Formato Original:**
```
numero,fecha_trafico,tipo_cdr,celda_decimal,lac_decimal
573205487611,20240419080000,DATOS,175462,20010
```

**Mapeo a Campos Unificados:**

| Campo Original | Campo Unificado | Transformación |
|---------------|-----------------|----------------|
| `numero` | `numero_telefono` | Directo |
| `fecha_trafico` | `fecha_hora_inicio` | `STRFTIME('%Y-%m-%d %H:%M:%S', fecha_trafico)` |
| `celda_decimal` | `celda_id` | `CAST(celda_decimal AS TEXT)` |
| `lac_decimal` | `lac_tac` | `CAST(lac_decimal AS TEXT)` |
| `tipo_cdr` | `tipo_conexion` | Valor: "DATOS" |

**Campos Específicos (JSON):**
```json
{
  "tipo_cdr": "DATOS",
  "celda_decimal_original": 175462,
  "lac_decimal_original": 20010,
  "formato_original": "claro_datos_v1"
}
```

**Valores Por Defecto:**
- `trafico_subida_bytes`: 0 (no disponible)
- `trafico_bajada_bytes`: 0 (no disponible)
- `duracion_segundos`: NULL
- `tecnologia`: "UNKNOWN"

---

### MOVISTAR - Archivos de Datos

**Archivo:** `jgd202410754_00007301_datos_ MOVISTAR.csv`

**Formato Original:**
```
numero_que_navega,ruta_entrante,celda,trafico_de_subida,trafico_de_bajada,fecha_hora_inicio_sesion,duracion,tipo_tecnologia,fecha_hora_fin_sesion,departamento,localidad,region,latitud_n,longitud_w,proveedor,tecnologia,descripcion,direccion,celda_
```

**Mapeo a Campos Unificados:**

| Campo Original | Campo Unificado | Transformación |
|---------------|-----------------|----------------|
| `numero_que_navega` | `numero_telefono` | Directo |
| `fecha_hora_inicio_sesion` | `fecha_hora_inicio` | `STRFTIME('%Y-%m-%d %H:%M:%S', ...)` |
| `fecha_hora_fin_sesion` | `fecha_hora_fin` | `STRFTIME('%Y-%m-%d %H:%M:%S', ...)` |
| `duracion` | `duracion_segundos` | Directo |
| `celda` | `celda_id` | `PRINTF('%06d', CAST(celda AS INTEGER))` |
| `trafico_de_subida` | `trafico_subida_bytes` | Directo |
| `trafico_de_bajada` | `trafico_bajada_bytes` | Directo |
| `latitud_n` | `latitud` | `CAST(REPLACE(latitud_n, ',', '.') AS REAL)` |
| `longitud_w` | `longitud` | `CAST(REPLACE(longitud_w, ',', '.') AS REAL) * -1` |
| `tecnologia` | `tecnologia` | Directo |

**Campos Específicos (JSON):**
```json
{
  "ruta_entrante": "01",
  "tipo_tecnologia": 6,
  "departamento": "BOGOTA D.C",
  "localidad": "BOGOTA, D.C.",
  "region": "BOGOTA",
  "proveedor": "HUAWEI",
  "descripcion": "BOG0115 - CENTRO NARIÑO",
  "direccion": "Diagonal 22 A # 43-65",
  "celda_original": "000073-01"
}
```

---

### TIGO - Archivos de Llamadas

**Archivo:** `Reporte TIGO.csv`

**Formato Original:**
```
TIPO_DE_LLAMADA,NUMERO A,NUMERO MARCADO,TRCSEXTRACODEC,DIRECCION: O SALIENTE/ I ENTRANTE,DURACION TOTAL seg,FECHA Y HORA ORIGEN,CELDA_ORIGEN_TRUNCADA,TECH,DIRECCION,CITY_DS,DEPARTMENT_DS,AZIMUTH,ALTURA,POTENCIA,LONGITUDE,LATITUDE,TIPO_COBERTURA,TIPO_ESTRUCTURA,OPERADOR,CELLID_NVAL
```

**Mapeo a Campos Unificados:**

| Campo Original | Campo Unificado | Transformación |
|---------------|-----------------|----------------|
| `NUMERO A` | `numero_objetivo` | Directo |
| `NUMERO MARCADO` | `numero_destino` | Directo (si saliente) |
| `DURACION TOTAL seg` | `duracion_segundos` | Directo |
| `FECHA Y HORA ORIGEN` | `fecha_hora_llamada` | `STRFTIME('%Y-%m-%d %H:%M:%S', ...)` |
| `CELDA_ORIGEN_TRUNCADA` | `celda_origen` | Directo |
| `TECH` | `tecnologia` | Directo |
| `LATITUDE` | `latitud_origen` | `CAST(REPLACE(LATITUDE, ',', '.') AS REAL)` |
| `LONGITUDE` | `longitud_origen` | `CAST(REPLACE(LONGITUDE, ',', '.') AS REAL)` |

**Lógica de Determinación:**
```sql
-- Tipo de llamada
CASE 
  WHEN "DIRECCION: O SALIENTE, I ENTRANTE" = 'O' THEN 'SALIENTE'
  WHEN "DIRECCION: O SALIENTE, I ENTRANTE" = 'I' THEN 'ENTRANTE'
  ELSE 'MIXTA'
END

-- Número origen/destino
CASE tipo_llamada
  WHEN 'SALIENTE' THEN numero_origen = "NUMERO A", numero_destino = "NUMERO MARCADO"
  WHEN 'ENTRANTE' THEN numero_origen = "NUMERO MARCADO", numero_destino = "NUMERO A"
END
```

**Campos Específicos (JSON):**
```json
{
  "tipo_de_llamada": 200,
  "trcsextracodec": "10.198.50.152",
  "city_ds": "BOGOTÁ. D.C.",
  "department_ds": "CUNDINAMARCA",
  "azimuth": 350,
  "altura": 22,
  "potencia": "18,2",
  "tipo_cobertura": "6 - 1. URBANA",
  "tipo_estructura": "12 - ROOFTOP + TOWER",
  "cellid_nval": 1
}
```

---

### WOM - Archivos de Datos

**Archivo:** `PUNTO 1 TRÁFICO DATOS WOM.csv`

**Formato Original:**
```
OPERADOR_TECNOLOGIA,BTS_ID,TAC,CELL_ID_VOZ,SECTOR,FECHA_HORA_INICIO,FECHA_HORA_FIN,OPERADOR_RAN,NUMERO_ORIGEN,DURACION_SEG,UP_DATA_BYTES,DOWN_DATA_BYTES,IMSI,LOCALIZACION_USUARIO,NOMBRE_ANTENA,DIRECCION,LATITUD,LONGITUD,LOCALIDAD,CIUDAD,DEPARTAMENTO,REGIONAL,ENTORNO_GEOGRAFICO,ULI
```

**Mapeo a Campos Unificados:**

| Campo Original | Campo Unificado | Transformación |
|---------------|-----------------|----------------|
| `NUMERO_ORIGEN` | `numero_telefono` | Directo |
| `FECHA_HORA_INICIO` | `fecha_hora_inicio` | `STRFTIME('%Y-%m-%d %H:%M:%S', ...)` |
| `FECHA_HORA_FIN` | `fecha_hora_fin` | `STRFTIME('%Y-%m-%d %H:%M:%S', ...)` |
| `DURACION_SEG` | `duracion_segundos` | Directo |
| `CELL_ID_VOZ` | `celda_id` | `CAST(CELL_ID_VOZ AS TEXT)` |
| `TAC` | `lac_tac` | `CAST(TAC AS TEXT)` |
| `UP_DATA_BYTES` | `trafico_subida_bytes` | Directo |
| `DOWN_DATA_BYTES` | `trafico_bajada_bytes` | Directo |
| `LATITUD` | `latitud` | `CAST(REPLACE(LATITUD, ',', '.') AS REAL)` |
| `LONGITUD` | `longitud` | `CAST(REPLACE(LONGITUD, ',', '.') AS REAL)` |
| `OPERADOR_TECNOLOGIA` | `tecnologia` | `SUBSTR(OPERADOR_TECNOLOGIA, 5)` -- "WOM 4G" -> "4G" |

**Campos Específicos (JSON):**
```json
{
  "bts_id": 11648,
  "sector": 7,
  "operador_ran": "WOM",
  "imsi": "732360130234793",
  "localizacion_usuario": "823702630a9d370263002d8007",
  "nombre_antena": "BTA Ciudad Bachue I",
  "direccion": "Cr 95 G 86 B 21",
  "localidad": "Engativa",
  "ciudad": "Bogota",
  "departamento": "Cundinamarca",
  "regional": "Center",
  "entorno_geografico": "Urbano",
  "uli": "73236027172981895"
}
```

---

## CAMPOS ESPECÍFICOS EN JSON

### Estructura del Campo `operator_specific_data`

Cada registro almacena campos únicos del operador en formato JSON para preservar la información original y permitir consultas específicas.

#### Esquema Base para Todos los Operadores:

```json
{
  "formato_original": "string",      // Identificador del formato de datos
  "version_procesamiento": "1.0",    // Versión del procesador de datos
  "fecha_procesamiento": "datetime", // Cuándo se procesó el archivo
  "validaciones_aplicadas": [],      // Lista de validaciones ejecutadas
  "transformaciones": {},            // Registro de transformaciones aplicadas
  "campos_originales": {}            // Campos específicos del operador
}
```

### Campos Específicos por Operador:

#### CLARO
```json
{
  "formato_original": "claro_datos_v1",
  "tipo_cdr": "DATOS|LLAMADAS_E|LLAMADAS_S",
  "celda_decimal_original": 175462,
  "lac_decimal_original": 20010,
  "calidad_estimada": "ALTA|MEDIA|BAJA"
}
```

#### MOVISTAR
```json
{
  "formato_original": "movistar_datos_v1",
  "ruta_entrante": "01",
  "tipo_tecnologia": 6,
  "proveedor": "HUAWEI|ERICSSON|NOKIA",
  "descripcion_celda": "BOG0115 - CENTRO NARIÑO",
  "direccion_antena": "Diagonal 22 A # 43-65",
  "datos_administrativos": {
    "departamento": "BOGOTA D.C",
    "localidad": "BOGOTA, D.C.",
    "region": "BOGOTA"
  }
}
```

#### TIGO
```json
{
  "formato_original": "tigo_llamadas_v1",
  "tipo_de_llamada": 200,
  "trcsextracodec": "10.198.50.152",
  "datos_antena": {
    "azimuth": 350,
    "altura": 22,
    "potencia": "18,2"
  },
  "clasificacion_cobertura": {
    "tipo_cobertura": "6 - 1. URBANA",
    "tipo_estructura": "12 - ROOFTOP + TOWER"
  },
  "cellid_nval": 1
}
```

#### WOM
```json
{
  "formato_original": "wom_datos_v1",
  "bts_id": 11648,
  "sector": 7,
  "identificadores": {
    "imsi": "732360130234793",
    "uli": "73236027172981895"
  },
  "localizacion": {
    "localizacion_usuario": "823702630a9d370263002d8007",
    "nombre_antena": "BTA Ciudad Bachue I",
    "entorno_geografico": "Urbano"
  },
  "datos_administrativos": {
    "regional": "Center"
  }
}
```

---

## VALIDACIONES Y TRANSFORMACIONES

### Validaciones Aplicadas por Campo

#### Números Telefónicos
```sql
-- Validación de formato
CHECK (LENGTH(TRIM(numero_telefono)) >= 10)
CHECK (numero_telefono GLOB '[0-9]*')

-- Transformaciones comunes
CASE 
  WHEN numero LIKE '57%' THEN numero
  WHEN LENGTH(numero) = 10 THEN '57' || numero
  WHEN LENGTH(numero) = 7 THEN '571' || numero  -- Bogotá
  ELSE numero
END
```

#### Fechas y Timestamps
```sql
-- Formatos soportados
'YYYYMMDDHHMMSS'    -- CLARO: 20240419080000
'DD/MM/YYYY HH:MM'  -- TIGO: 28/02/2025 01:20:19
'YYYY-MM-DD HH:MM:SS' -- Estándar ISO

-- Transformación unificada
STRFTIME('%Y-%m-%d %H:%M:%S', fecha_original)
```

#### Coordenadas Geográficas
```sql
-- Conversión de formato europeo (coma decimal)
CAST(REPLACE(latitud_str, ',', '.') AS REAL)

-- Corrección de signos (longitud oeste)
CASE 
  WHEN longitud > 0 AND operador = 'MOVISTAR' THEN longitud * -1
  ELSE longitud
END

-- Validación de rangos
CHECK (latitud BETWEEN -90.0 AND 90.0)
CHECK (longitud BETWEEN -180.0 AND 180.0)
```

#### Tráfico de Datos
```sql
-- Conversión a bytes (si está en otros formatos)
CASE unidad
  WHEN 'KB' THEN valor * 1024
  WHEN 'MB' THEN valor * 1048576
  WHEN 'GB' THEN valor * 1073741824
  ELSE valor  -- Asumir bytes
END

-- Validación de rangos realistas
CHECK (trafico_total_bytes < 107374182400)  -- < 100GB
```

### Transformaciones de Celdas

#### Normalización de IDs de Celda
```sql
-- CLARO: decimal a string con padding
PRINTF('%06d', CAST(celda_decimal AS INTEGER))

-- MOVISTAR: formato compuesto
celda || '-' || ruta_entrante

-- TIGO: usar celda truncada directamente
CELDA_ORIGEN_TRUNCADA

-- WOM: cell_id_voz como string
CAST(CELL_ID_VOZ AS TEXT)
```

#### Tecnologías Normalizadas
```sql
CASE UPPER(tecnologia_original)
  WHEN 'LTE' THEN 'LTE'
  WHEN '4G' THEN 'LTE'
  WHEN '5G NR' THEN '5G'
  WHEN '5G' THEN '5G'
  WHEN 'UMTS' THEN '3G'
  WHEN 'GSM' THEN '2G'
  ELSE 'UNKNOWN'
END
```

---

## EJEMPLOS DE PROCESAMIENTO

### Ejemplo 1: Procesamiento de Archivo CLARO - Datos

```sql
-- Inserción desde archivo CSV de CLARO
INSERT INTO operator_cellular_data (
    file_upload_id,
    mission_id,
    operator,
    numero_telefono,
    fecha_hora_inicio,
    celda_id,
    lac_tac,
    tipo_conexion,
    operator_specific_data,
    created_at
)
SELECT 
    :file_upload_id,
    :mission_id,
    'CLARO',
    numero,
    DATETIME(
        SUBSTR(fecha_trafico, 1, 4) || '-' ||
        SUBSTR(fecha_trafico, 5, 2) || '-' ||
        SUBSTR(fecha_trafico, 7, 2) || ' ' ||
        SUBSTR(fecha_trafico, 9, 2) || ':' ||
        SUBSTR(fecha_trafico, 11, 2) || ':' ||
        SUBSTR(fecha_trafico, 13, 2)
    ),
    PRINTF('%06d', CAST(celda_decimal AS INTEGER)),
    CAST(lac_decimal AS TEXT),
    'DATOS',
    JSON_OBJECT(
        'formato_original', 'claro_datos_v1',
        'tipo_cdr', tipo_cdr,
        'celda_decimal_original', celda_decimal,
        'lac_decimal_original', lac_decimal
    ),
    CURRENT_TIMESTAMP
FROM csv_temp_claro_datos;
```

### Ejemplo 2: Procesamiento de Archivo MOVISTAR - Datos

```sql
INSERT INTO operator_cellular_data (
    file_upload_id,
    mission_id,
    operator,
    numero_telefono,
    fecha_hora_inicio,
    fecha_hora_fin,
    duracion_segundos,
    celda_id,
    trafico_subida_bytes,
    trafico_bajada_bytes,
    latitud,
    longitud,
    tecnologia,
    operator_specific_data
)
SELECT 
    :file_upload_id,
    :mission_id,
    'MOVISTAR',
    numero_que_navega,
    STRFTIME('%Y-%m-%d %H:%M:%S', 
        SUBSTR(fecha_hora_inicio_sesion, 1, 4) || '-' ||
        SUBSTR(fecha_hora_inicio_sesion, 5, 2) || '-' ||
        SUBSTR(fecha_hora_inicio_sesion, 7, 2) || ' ' ||
        SUBSTR(fecha_hora_inicio_sesion, 9, 2) || ':' ||
        SUBSTR(fecha_hora_inicio_sesion, 11, 2) || ':' ||
        SUBSTR(fecha_hora_inicio_sesion, 13, 2)
    ),
    STRFTIME('%Y-%m-%d %H:%M:%S', 
        SUBSTR(fecha_hora_fin_sesion, 1, 4) || '-' ||
        SUBSTR(fecha_hora_fin_sesion, 5, 2) || '-' ||
        SUBSTR(fecha_hora_fin_sesion, 7, 2) || ' ' ||
        SUBSTR(fecha_hora_fin_sesion, 9, 2) || ':' ||
        SUBSTR(fecha_hora_fin_sesion, 11, 2) || ':' ||
        SUBSTR(fecha_hora_fin_sesion, 13, 2)
    ),
    duracion,
    PRINTF('%06d-%s', CAST(celda AS INTEGER), ruta_entrante),
    trafico_de_subida,
    trafico_de_bajada,
    CAST(REPLACE(latitud_n, ',', '.') AS REAL),
    CAST(REPLACE(longitud_w, ',', '.') AS REAL) * -1,  -- Corregir signo oeste
    CASE UPPER(tecnologia)
        WHEN 'LTE' THEN 'LTE'
        WHEN '4G' THEN 'LTE'
        ELSE tecnologia
    END,
    JSON_OBJECT(
        'formato_original', 'movistar_datos_v1',
        'ruta_entrante', ruta_entrante,
        'tipo_tecnologia', tipo_tecnologia,
        'proveedor', proveedor,
        'descripcion', descripcion,
        'direccion', direccion,
        'datos_administrativos', JSON_OBJECT(
            'departamento', departamento,
            'localidad', localidad,
            'region', region
        )
    )
FROM csv_temp_movistar_datos;
```

### Ejemplo 3: Consulta de Datos Unificados

```sql
-- Consulta de actividad por número objetivo
SELECT 
    ocd.numero_telefono,
    COUNT(*) as sesiones_datos,
    SUM(ocd.trafico_subida_bytes + ocd.trafico_bajada_bytes) as trafico_total_bytes,
    COUNT(DISTINCT ocd.celda_id) as celdas_utilizadas,
    MIN(ocd.fecha_hora_inicio) as primera_actividad,
    MAX(COALESCE(ocd.fecha_hora_fin, ocd.fecha_hora_inicio)) as ultima_actividad,
    
    -- Datos específicos de MOVISTAR (ejemplo de uso de JSON)
    COUNT(CASE WHEN JSON_EXTRACT(ocd.operator_specific_data, '$.proveedor') = 'HUAWEI' THEN 1 END) as sesiones_huawei,
    
    -- Estadísticas de llamadas correlacionadas
    (SELECT COUNT(*) FROM operator_call_data ocall 
     WHERE ocall.numero_objetivo = ocd.numero_telefono 
     AND ocall.mission_id = ocd.mission_id) as llamadas_totales

FROM operator_cellular_data ocd
WHERE ocd.mission_id = :mission_id
  AND ocd.numero_telefono = :numero_objetivo
GROUP BY ocd.numero_telefono
ORDER BY trafico_total_bytes DESC;
```

### Ejemplo 4: Análisis Cross-Operador

```sql
-- Comparación de cobertura entre operadores
WITH cobertura_por_operador AS (
    SELECT 
        ocr.operator,
        COUNT(DISTINCT ocr.celda_id) as celdas_totales,
        COUNT(DISTINCT ocr.ciudad) as ciudades_cubiertas,
        AVG(ocr.frecuencia_uso) as uso_promedio_celda,
        
        -- Datos específicos de tráfico
        (SELECT AVG(trafico_subida_bytes + trafico_bajada_bytes) 
         FROM operator_cellular_data ocd 
         WHERE ocd.operator = ocr.operator) as trafico_promedio,
         
        -- Tecnologías predominantes
        (SELECT tecnologia 
         FROM operator_cellular_data ocd2 
         WHERE ocd2.operator = ocr.operator 
         GROUP BY tecnologia 
         ORDER BY COUNT(*) DESC 
         LIMIT 1) as tecnologia_principal
         
    FROM operator_cell_registry ocr
    GROUP BY ocr.operator
)
SELECT 
    operator,
    celdas_totales,
    ciudades_cubiertas,
    ROUND(uso_promedio_celda, 2) as uso_promedio_celda,
    ROUND(trafico_promedio / 1024.0 / 1024.0, 2) as trafico_promedio_mb,
    tecnologia_principal
FROM cobertura_por_operador
ORDER BY celdas_totales DESC;
```

---

## CONSIDERACIONES ESPECIALES

### Manejo de Datos Faltantes

1. **Coordenadas Geográficas**: Si no están disponibles, se mantienen como NULL
2. **Tráfico de Datos**: Si no está disponible, se establece en 0
3. **Duración**: Si no está disponible, se calcula como diferencia de timestamps
4. **Tecnología**: Si no está especificada, se marca como "UNKNOWN"

### Detección de Duplicados

- **Criterio Cellular**: `file_upload_id + numero_telefono + fecha_hora_inicio + celda_id`
- **Criterio Llamadas**: `file_upload_id + numero_origen + numero_destino + fecha_hora_llamada`

### Performance y Optimización

- Utilizar transacciones para inserciones masivas
- Aplicar validaciones después de carga completa
- Usar índices temporales durante procesamiento
- Ejecutar `ANALYZE` después de cargas grandes

---

Esta documentación debe actualizarse cada vez que se agreguen nuevos operadores o se modifiquen los formatos de datos existentes.