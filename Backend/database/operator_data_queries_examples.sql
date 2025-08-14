-- ============================================================================
-- KRONOS - Queries de Ejemplo para Módulo de Datos de Operadores Celulares
-- ============================================================================
-- Colección de consultas SQL optimizadas para operaciones comunes en el
-- análisis de datos de operadores celulares. Incluye ejemplos de:
-- 
-- ✓ Búsquedas por número telefónico
-- ✓ Análisis temporal y geoespacial
-- ✓ Estadísticas por operador
-- ✓ Detección de patrones sospechosos
-- ✓ Reportes de calidad de datos
-- ✓ Consultas de performance
-- ============================================================================

-- ============================================================================
-- 1. CONSULTAS DE BÚSQUEDA POR NÚMERO TELEFÓNICO
-- ============================================================================

-- 1.1 Actividad completa de un número objetivo
-- Parámetros: :numero_telefono, :mission_id
SELECT 
    'DATOS' as tipo_actividad,
    ocd.fecha_hora_inicio as timestamp_actividad,
    ocd.operator,
    ocd.celda_id,
    ocd.trafico_total_bytes as valor_numerico,
    'Sesión de datos: ' || ROUND(ocd.trafico_total_bytes/1024.0/1024.0, 2) || ' MB en ' || ocd.tecnologia as descripcion,
    ocd.latitud,
    ocd.longitud
FROM operator_cellular_data ocd
WHERE ocd.numero_telefono = '573001234567'  -- :numero_telefono
  AND ocd.mission_id = 'mission_001'        -- :mission_id

UNION ALL

SELECT 
    'LLAMADA' as tipo_actividad,
    ocall.fecha_hora_llamada as timestamp_actividad,
    ocall.operator,
    ocall.celda_objetivo as celda_id,
    ocall.duracion_segundos as valor_numerico,
    ocall.tipo_llamada || ' - ' || ocall.numero_origen || ' → ' || ocall.numero_destino || ' (' || ocall.duracion_segundos || 's)' as descripcion,
    ocall.latitud_origen as latitud,
    ocall.longitud_origen as longitud
FROM operator_call_data ocall
WHERE ocall.numero_objetivo = '573001234567'  -- :numero_telefono
  AND ocall.mission_id = 'mission_001'        -- :mission_id

ORDER BY timestamp_actividad DESC;

-- 1.2 Resumen de actividad por número con estadísticas
-- Parámetros: :numero_telefono, :mission_id
SELECT 
    numero_telefono,
    operator,
    sesiones_datos,
    ROUND(trafico_total_bytes / 1024.0 / 1024.0, 2) as trafico_total_mb,
    total_llamadas,
    celdas_utilizadas_datos + celdas_utilizadas_llamadas as total_celdas_diferentes,
    primera_actividad_datos,
    ultima_actividad_datos,
    tecnologias_utilizadas
FROM v_numero_actividad_consolidada
WHERE numero_telefono = '573001234567'  -- :numero_telefono
  AND mission_id = 'mission_001';       -- :mission_id

-- 1.3 Números más activos en una misión
-- Parámetros: :mission_id, :limit
SELECT 
    vnac.numero_telefono,
    vnac.operator,
    vnac.sesiones_datos,
    ROUND(vnac.trafico_total_bytes / 1024.0 / 1024.0, 2) as trafico_total_mb,
    vnac.total_llamadas,
    (vnac.sesiones_datos + vnac.total_llamadas) as actividad_total,
    vnac.celdas_utilizadas_datos,
    julianday(vnac.ultima_actividad_datos) - julianday(vnac.primera_actividad_datos) as dias_actividad
FROM v_numero_actividad_consolidada vnac
WHERE vnac.mission_id = 'mission_001'  -- :mission_id
ORDER BY actividad_total DESC, trafico_total_mb DESC
LIMIT 20;  -- :limit

-- ============================================================================
-- 2. ANÁLISIS TEMPORAL
-- ============================================================================

-- 2.1 Actividad por horas del día
-- Parámetros: :mission_id, :fecha_inicio, :fecha_fin
SELECT 
    CAST(strftime('%H', ocd.fecha_hora_inicio) AS INTEGER) as hora_dia,
    COUNT(DISTINCT ocd.numero_telefono) as usuarios_activos,
    COUNT(*) as total_sesiones,
    ROUND(SUM(ocd.trafico_total_bytes) / 1024.0 / 1024.0, 2) as trafico_total_mb,
    ROUND(AVG(ocd.trafico_total_bytes), 0) as trafico_promedio_bytes
FROM operator_cellular_data ocd
WHERE ocd.mission_id = 'mission_001'  -- :mission_id
  AND date(ocd.fecha_hora_inicio) BETWEEN '2024-04-19' AND '2024-04-19'  -- :fecha_inicio, :fecha_fin
GROUP BY CAST(strftime('%H', ocd.fecha_hora_inicio) AS INTEGER)
ORDER BY hora_dia;

-- 2.2 Evolución temporal de actividad por operador
-- Parámetros: :mission_id, :intervalo_horas
WITH actividad_temporal AS (
    SELECT 
        datetime(
            strftime('%Y-%m-%d %H:', fecha_hora_inicio) || 
            printf('%02d', (CAST(strftime('%M', fecha_hora_inicio) AS INTEGER) / 60) * 60) || 
            ':00'
        ) as ventana_tiempo,
        operator,
        COUNT(*) as sesiones,
        COUNT(DISTINCT numero_telefono) as usuarios,
        ROUND(SUM(trafico_total_bytes) / 1024.0 / 1024.0, 2) as trafico_mb
    FROM operator_cellular_data
    WHERE mission_id = 'mission_001'  -- :mission_id
    GROUP BY ventana_tiempo, operator
)
SELECT 
    ventana_tiempo,
    operator,
    sesiones,
    usuarios,
    trafico_mb,
    LAG(sesiones, 1) OVER (PARTITION BY operator ORDER BY ventana_tiempo) as sesiones_anterior,
    ROUND(
        (CAST(sesiones AS REAL) - LAG(sesiones, 1) OVER (PARTITION BY operator ORDER BY ventana_tiempo)) /
        NULLIF(LAG(sesiones, 1) OVER (PARTITION BY operator ORDER BY ventana_tiempo), 0) * 100, 
        2
    ) as variacion_porcentual
FROM actividad_temporal
ORDER BY ventana_tiempo, operator;

-- 2.3 Detección de picos de actividad anormales
-- Parámetros: :mission_id, :threshold_desviacion
WITH estadisticas_por_hora AS (
    SELECT 
        CAST(strftime('%H', fecha_hora_inicio) AS INTEGER) as hora,
        COUNT(*) as sesiones_hora,
        AVG(COUNT(*)) OVER () as promedio_general,
        -- Cálculo aproximado de desviación estándar
        (COUNT(*) - AVG(COUNT(*)) OVER ()) * (COUNT(*) - AVG(COUNT(*)) OVER ()) as cuadrado_diferencia
    FROM operator_cellular_data
    WHERE mission_id = 'mission_001'  -- :mission_id
    GROUP BY CAST(strftime('%H', fecha_hora_inicio) AS INTEGER)
)
SELECT 
    hora,
    sesiones_hora,
    ROUND(promedio_general, 2) as promedio_general,
    ROUND(sqrt(AVG(cuadrado_diferencia) OVER ()), 2) as desviacion_std,
    ROUND((sesiones_hora - promedio_general) / NULLIF(sqrt(AVG(cuadrado_diferencia) OVER ()), 0), 2) as z_score,
    CASE 
        WHEN ABS((sesiones_hora - promedio_general) / NULLIF(sqrt(AVG(cuadrado_diferencia) OVER ()), 0)) > 2 
        THEN 'ANORMAL'
        ELSE 'NORMAL'
    END as clasificacion
FROM estadisticas_por_hora
ORDER BY ABS((sesiones_hora - promedio_general) / NULLIF(sqrt(AVG(cuadrado_diferencia) OVER ()), 0)) DESC;

-- ============================================================================
-- 3. ANÁLISIS GEOESPACIAL
-- ============================================================================

-- 3.1 Análisis de cobertura por zona geográfica
-- Parámetros: :lat_centro, :lon_centro, :radio_km, :mission_id
WITH zona_interes AS (
    SELECT 
        *,
        -- Cálculo aproximado de distancia usando fórmula haversine simplificada
        6371.0 * 2 * asin(sqrt(
            pow(sin(radians(latitud - 4.6097) / 2), 2) +  -- :lat_centro = 4.6097 (Bogotá)
            cos(radians(4.6097)) * cos(radians(latitud)) *  -- :lat_centro
            pow(sin(radians(longitud - (-74.0817)) / 2), 2) -- :lon_centro = -74.0817 (Bogotá)
        )) as distancia_km
    FROM operator_cellular_data
    WHERE mission_id = 'mission_001'  -- :mission_id
      AND latitud IS NOT NULL 
      AND longitud IS NOT NULL
)
SELECT 
    operator,
    COUNT(DISTINCT celda_id) as celdas_en_zona,
    COUNT(DISTINCT numero_telefono) as usuarios_activos,
    COUNT(*) as total_registros,
    ROUND(AVG(trafico_total_bytes) / 1024.0 / 1024.0, 2) as trafico_promedio_mb,
    ROUND(MIN(distancia_km), 2) as distancia_minima_km,
    ROUND(MAX(distancia_km), 2) as distancia_maxima_km,
    ROUND(AVG(distancia_km), 2) as distancia_promedio_km,
    MIN(fecha_hora_inicio) as periodo_inicio,
    MAX(fecha_hora_inicio) as periodo_fin
FROM zona_interes
WHERE distancia_km <= 5.0  -- :radio_km
GROUP BY operator
ORDER BY total_registros DESC;

-- 3.2 Celdas más utilizadas con información geográfica
-- Parámetros: :mission_id, :operador
SELECT 
    ocr.operator,
    ocr.celda_id,
    ocr.frecuencia_uso,
    ocr.latitud,
    ocr.longitud,
    ocr.ciudad,
    ocr.tecnologia_predominante,
    ROUND(ocr.calidad_promedio_senal, 1) as rssi_promedio,
    ocr.usuarios_unicos_dia,
    COUNT(DISTINCT ocd.numero_telefono) as usuarios_unicos_actual,
    ROUND(SUM(ocd.trafico_total_bytes) / 1024.0 / 1024.0, 2) as trafico_total_mb
FROM operator_cell_registry ocr
LEFT JOIN operator_cellular_data ocd ON ocr.operator = ocd.operator AND ocr.celda_id = ocd.celda_id
WHERE ocd.mission_id = 'mission_001'  -- :mission_id
  AND ocr.operator = 'CLARO'          -- :operador
GROUP BY ocr.operator, ocr.celda_id, ocr.frecuencia_uso, ocr.latitud, ocr.longitud, 
         ocr.ciudad, ocr.tecnologia_predominante, ocr.calidad_promedio_senal, ocr.usuarios_unicos_dia
ORDER BY frecuencia_uso DESC, trafico_total_mb DESC
LIMIT 25;

-- ============================================================================
-- 4. ANÁLISIS DE PATRONES SOSPECHOSOS
-- ============================================================================

-- 4.1 Detección de números con actividad sospechosa
-- (Alta movilidad, múltiples operadores, patrones inusuales)
-- Parámetros: :mission_id, :min_celdas, :min_operadores
WITH patrones_numero AS (
    SELECT 
        numero_telefono,
        COUNT(DISTINCT operator) as operadores_diferentes,
        COUNT(DISTINCT celda_id) as celdas_diferentes,
        COUNT(*) as total_sesiones,
        ROUND(SUM(trafico_total_bytes) / 1024.0 / 1024.0, 2) as trafico_total_mb,
        COUNT(DISTINCT DATE(fecha_hora_inicio)) as dias_activos,
        MIN(fecha_hora_inicio) as primera_actividad,
        MAX(fecha_hora_inicio) as ultima_actividad,
        
        -- Calcular movilidad: promedio de celdas por día
        ROUND(
            CAST(COUNT(DISTINCT celda_id) AS REAL) / 
            NULLIF(COUNT(DISTINCT DATE(fecha_hora_inicio)), 0), 
            2
        ) as celdas_por_dia,
        
        -- Actividad nocturna (22:00 - 06:00)
        COUNT(CASE WHEN CAST(strftime('%H', fecha_hora_inicio) AS INTEGER) >= 22 
                    OR CAST(strftime('%H', fecha_hora_inicio) AS INTEGER) <= 6 
                   THEN 1 END) as sesiones_nocturnas,
                   
        ROUND(
            CAST(COUNT(CASE WHEN CAST(strftime('%H', fecha_hora_inicio) AS INTEGER) >= 22 
                             OR CAST(strftime('%H', fecha_hora_inicio) AS INTEGER) <= 6 
                            THEN 1 END) AS REAL) / COUNT(*) * 100, 
            2
        ) as porcentaje_nocturno
        
    FROM operator_cellular_data
    WHERE mission_id = 'mission_001'  -- :mission_id
    GROUP BY numero_telefono
),
llamadas_asociadas AS (
    SELECT 
        numero_objetivo,
        COUNT(*) as total_llamadas,
        COUNT(DISTINCT numero_origen) as origenes_diferentes,
        COUNT(DISTINCT numero_destino) as destinos_diferentes,
        AVG(duracion_segundos) as duracion_promedio
    FROM operator_call_data
    WHERE mission_id = 'mission_001'  -- :mission_id
    GROUP BY numero_objetivo
)
SELECT 
    pn.numero_telefono,
    pn.operadores_diferentes,
    pn.celdas_diferentes,
    pn.total_sesiones,
    pn.trafico_total_mb,
    pn.celdas_por_dia,
    pn.porcentaje_nocturno,
    COALESCE(la.total_llamadas, 0) as total_llamadas,
    COALESCE(la.origenes_diferentes, 0) as contactos_origen,
    COALESCE(la.destinos_diferentes, 0) as contactos_destino,
    
    -- Puntuación de sospecha (0-100)
    ROUND(
        (pn.operadores_diferentes * 10) +  -- Múltiples operadores
        (CASE WHEN pn.celdas_por_dia > 5 THEN 20 ELSE pn.celdas_por_dia * 2 END) + -- Alta movilidad
        (CASE WHEN pn.porcentaje_nocturno > 50 THEN 15 ELSE pn.porcentaje_nocturno * 0.3 END) + -- Actividad nocturna
        (CASE WHEN COALESCE(la.origenes_diferentes, 0) > 10 THEN 15 ELSE COALESCE(la.origenes_diferentes, 0) * 1.5 END) + -- Múltiples contactos
        (CASE WHEN pn.trafico_total_mb > 1000 THEN 10 ELSE pn.trafico_total_mb * 0.01 END), -- Alto tráfico
        1
    ) as puntuacion_sospecha,
    
    pn.primera_actividad,
    pn.ultima_actividad
    
FROM patrones_numero pn
LEFT JOIN llamadas_asociadas la ON pn.numero_telefono = la.numero_objetivo
WHERE pn.celdas_diferentes >= 5      -- :min_celdas
  AND pn.operadores_diferentes >= 2  -- :min_operadores
ORDER BY puntuacion_sospecha DESC, pn.total_sesiones DESC
LIMIT 50;

-- 4.2 Análisis de comunicaciones entre números objetivos
-- Parámetros: :mission_id, :min_llamadas
WITH numeros_objetivo AS (
    SELECT DISTINCT numero_telefono
    FROM operator_cellular_data
    WHERE mission_id = 'mission_001'  -- :mission_id
),
comunicaciones_internas AS (
    SELECT 
        ocall.numero_origen,
        ocall.numero_destino,
        COUNT(*) as total_llamadas,
        SUM(ocall.duracion_segundos) as duracion_total,
        ROUND(AVG(ocall.duracion_segundos), 1) as duracion_promedio,
        MIN(ocall.fecha_hora_llamada) as primera_comunicacion,
        MAX(ocall.fecha_hora_llamada) as ultima_comunicacion,
        COUNT(DISTINCT DATE(ocall.fecha_hora_llamada)) as dias_comunicacion,
        GROUP_CONCAT(DISTINCT ocall.operator) as operadores_utilizados
    FROM operator_call_data ocall
    INNER JOIN numeros_objetivo no1 ON ocall.numero_origen = no1.numero_telefono
    INNER JOIN numeros_objetivo no2 ON ocall.numero_destino = no2.numero_telefono
    WHERE ocall.mission_id = 'mission_001'  -- :mission_id
      AND ocall.numero_origen != ocall.numero_destino
    GROUP BY ocall.numero_origen, ocall.numero_destino
)
SELECT 
    ci.numero_origen,
    ci.numero_destino,
    ci.total_llamadas,
    ci.duracion_total,
    ci.duracion_promedio,
    ci.dias_comunicacion,
    ci.operadores_utilizados,
    ci.primera_comunicacion,
    ci.ultima_comunicacion,
    
    -- Verificar reciprocidad (si B también llama a A)
    CASE WHEN EXISTS (
        SELECT 1 FROM comunicaciones_internas ci2 
        WHERE ci2.numero_origen = ci.numero_destino 
          AND ci2.numero_destino = ci.numero_origen
    ) THEN 'BIDIRECCIONAL' ELSE 'UNIDIRECCIONAL' END as tipo_relacion,
    
    julianday(ci.ultima_comunicacion) - julianday(ci.primera_comunicacion) as periodo_comunicacion_dias
    
FROM comunicaciones_internas ci
WHERE ci.total_llamadas >= 3  -- :min_llamadas
ORDER BY ci.total_llamadas DESC, ci.duracion_total DESC;

-- ============================================================================
-- 5. ANÁLISIS DE CALIDAD DE DATOS
-- ============================================================================

-- 5.1 Reporte completo de calidad por archivo procesado
-- Parámetros: :mission_id
SELECT 
    vdqr.file_upload_id,
    vdqr.file_name,
    vdqr.operator,
    vdqr.processing_status,
    vdqr.records_processed,
    vdqr.records_failed,
    vdqr.success_rate_percent,
    vdqr.error_count,
    vdqr.warning_count,
    vdqr.registros_sin_coordenadas,
    vdqr.registros_sin_trafico,
    vdqr.records_per_second,
    
    -- Métricas adicionales de calidad
    (SELECT COUNT(DISTINCT numero_telefono) FROM operator_cellular_data ocd 
     WHERE ocd.file_upload_id = vdqr.file_upload_id) as usuarios_unicos,
    (SELECT COUNT(DISTINCT celda_id) FROM operator_cellular_data ocd 
     WHERE ocd.file_upload_id = vdqr.file_upload_id) as celdas_diferentes,
    (SELECT GROUP_CONCAT(DISTINCT tecnologia) FROM operator_cellular_data ocd 
     WHERE ocd.file_upload_id = vdqr.file_upload_id) as tecnologias_encontradas,
     
    -- Distribución temporal
    (SELECT COUNT(DISTINCT DATE(fecha_hora_inicio)) FROM operator_cellular_data ocd 
     WHERE ocd.file_upload_id = vdqr.file_upload_id) as dias_cubiertos,
    (SELECT MIN(fecha_hora_inicio) FROM operator_cellular_data ocd 
     WHERE ocd.file_upload_id = vdqr.file_upload_id) as fecha_minima,
    (SELECT MAX(fecha_hora_inicio) FROM operator_cellular_data ocd 
     WHERE ocd.file_upload_id = vdqr.file_upload_id) as fecha_maxima,
     
    vdqr.uploaded_at,
    vdqr.processing_start_time,
    vdqr.processing_end_time
    
FROM v_data_quality_report vdqr
INNER JOIN operator_data_sheets ods ON vdqr.file_upload_id = ods.id
WHERE ods.mission_id = 'mission_001'  -- :mission_id
ORDER BY vdqr.uploaded_at DESC;

-- 5.2 Identificación de registros problemáticos
-- Parámetros: :mission_id, :operador
SELECT 
    'COORDENADAS_INVALIDAS' as tipo_problema,
    COUNT(*) as cantidad,
    'Registros con coordenadas fuera de rango válido' as descripcion
FROM operator_cellular_data
WHERE mission_id = 'mission_001'  -- :mission_id
  AND operator = 'CLARO'          -- :operador
  AND (latitud IS NOT NULL AND (latitud < -90 OR latitud > 90))
  OR (longitud IS NOT NULL AND (longitud < -180 OR longitud > 180))

UNION ALL

SELECT 
    'NUMEROS_TELEFONO_INVALIDOS' as tipo_problema,
    COUNT(*) as cantidad,
    'Números telefónicos con formato incorrecto' as descripcion
FROM operator_cellular_data
WHERE mission_id = 'mission_001'  -- :mission_id
  AND operator = 'CLARO'          -- :operador
  AND (LENGTH(numero_telefono) < 10 OR numero_telefono NOT GLOB '[0-9]*')

UNION ALL

SELECT 
    'FECHAS_FUTURAS' as tipo_problema,
    COUNT(*) as cantidad,
    'Registros con fechas futuras (posibles errores de timestamp)' as descripcion
FROM operator_cellular_data
WHERE mission_id = 'mission_001'  -- :mission_id
  AND operator = 'CLARO'          -- :operador
  AND fecha_hora_inicio > datetime('now')

UNION ALL

SELECT 
    'TRAFICO_EXCESIVO' as tipo_problema,
    COUNT(*) as cantidad,
    'Registros con tráfico superior a 1GB (posibles errores de unidades)' as descripcion
FROM operator_cellular_data
WHERE mission_id = 'mission_001'  -- :mission_id
  AND operator = 'CLARO'          -- :operador
  AND trafico_total_bytes > 1073741824  -- 1GB

UNION ALL

SELECT 
    'DURACION_NEGATIVA' as tipo_problema,
    COUNT(*) as cantidad,
    'Registros con duración negativa' as descripcion
FROM operator_cellular_data
WHERE mission_id = 'mission_001'  -- :mission_id
  AND operator = 'CLARO'          -- :operador
  AND duracion_segundos < 0

ORDER BY cantidad DESC;

-- ============================================================================
-- 6. CONSULTAS DE PERFORMANCE Y MONITOREO
-- ============================================================================

-- 6.1 Estadísticas de uso de índices
-- (Requiere EXPLAIN QUERY PLAN en consultas específicas)
EXPLAIN QUERY PLAN
SELECT numero_telefono, COUNT(*) as sesiones
FROM operator_cellular_data 
WHERE mission_id = 'mission_001' 
  AND fecha_hora_inicio >= '2024-04-19 08:00:00'
GROUP BY numero_telefono
ORDER BY sesiones DESC;

-- 6.2 Tamaño y estadísticas de tablas
SELECT 
    name as tabla,
    
    -- Información general
    (SELECT COUNT(*) FROM sqlite_master sm WHERE sm.name = sqlite_master.name) as existe,
    
    -- Para tablas principales, obtener conteos
    CASE 
        WHEN name = 'operator_cellular_data' THEN (SELECT COUNT(*) FROM operator_cellular_data)
        WHEN name = 'operator_call_data' THEN (SELECT COUNT(*) FROM operator_call_data)
        WHEN name = 'operator_data_sheets' THEN (SELECT COUNT(*) FROM operator_data_sheets)
        WHEN name = 'file_processing_logs' THEN (SELECT COUNT(*) FROM file_processing_logs)
        WHEN name = 'operator_data_audit' THEN (SELECT COUNT(*) FROM operator_data_audit)
        WHEN name = 'operator_cell_registry' THEN (SELECT COUNT(*) FROM operator_cell_registry)
        ELSE 0
    END as total_registros
    
FROM sqlite_master 
WHERE type = 'table' 
  AND name LIKE 'operator_%'
ORDER BY name;

-- 6.3 Análisis de fragmentación y recomendaciones de mantenimiento
SELECT 
    'DATABASE_SIZE' as metrica,
    (SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()) as valor,
    'bytes' as unidad,
    'Tamaño total de la base de datos' as descripcion

UNION ALL

SELECT 
    'FREE_PAGES' as metrica,
    (SELECT freelist_count FROM pragma_freelist_count()) as valor,
    'pages' as unidad,
    'Páginas libres (fragmentación)' as descripcion

UNION ALL

SELECT 
    'CACHE_HIT_RATIO' as metrica,
    ROUND(
        (SELECT cache_hit FROM pragma_cache_hit_ratio()) * 100, 2
    ) as valor,
    'percent' as unidad,
    'Ratio de aciertos en caché' as descripcion

UNION ALL

SELECT 
    'TOTAL_INDEXES' as metrica,
    (SELECT COUNT(*) FROM sqlite_master WHERE type = 'index' AND name LIKE 'idx_%') as valor,
    'count' as unidad,
    'Número total de índices creados' as descripcion;

-- ============================================================================
-- 7. CONSULTAS PARA REPORTES EJECUTIVOS
-- ============================================================================

-- 7.1 Dashboard ejecutivo por misión
-- Parámetros: :mission_id
WITH mission_summary AS (
    SELECT 
        COUNT(DISTINCT ods.operator) as operadores_procesados,
        SUM(ods.records_processed) as total_registros,
        COUNT(DISTINCT ods.id) as archivos_procesados,
        SUM(ods.file_size_bytes) / 1024.0 / 1024.0 as total_mb_procesados,
        MIN(ods.uploaded_at) as primer_archivo,
        MAX(ods.processing_end_time) as ultimo_procesamiento
    FROM operator_data_sheets ods
    WHERE ods.mission_id = 'mission_001'  -- :mission_id
      AND ods.processing_status = 'COMPLETED'
),
data_summary AS (
    SELECT 
        COUNT(DISTINCT numero_telefono) as usuarios_unicos,
        COUNT(*) as sesiones_datos,
        ROUND(SUM(trafico_total_bytes) / 1024.0 / 1024.0 / 1024.0, 2) as total_gb,
        COUNT(DISTINCT celda_id) as celdas_diferentes,
        COUNT(DISTINCT DATE(fecha_hora_inicio)) as dias_actividad,
        MIN(fecha_hora_inicio) as periodo_inicio,
        MAX(fecha_hora_inicio) as periodo_fin
    FROM operator_cellular_data
    WHERE mission_id = 'mission_001'  -- :mission_id
),
calls_summary AS (
    SELECT 
        COUNT(DISTINCT numero_objetivo) as usuarios_con_llamadas,
        COUNT(*) as total_llamadas,
        ROUND(SUM(duracion_segundos) / 3600.0, 1) as total_horas_llamadas,
        COUNT(DISTINCT numero_origen || '|' || numero_destino) as pares_comunicacion_unicos
    FROM operator_call_data
    WHERE mission_id = 'mission_001'  -- :mission_id
)
SELECT 
    ms.operadores_procesados,
    ms.archivos_procesados,
    ms.total_registros,
    ROUND(ms.total_mb_procesados, 1) as total_mb_archivos,
    
    ds.usuarios_unicos,
    ds.sesiones_datos,
    ds.total_gb as trafico_total_gb,
    ds.celdas_diferentes,
    ds.dias_actividad,
    
    cs.usuarios_con_llamadas,
    cs.total_llamadas,
    cs.total_horas_llamadas,
    cs.pares_comunicacion_unicos,
    
    ms.primer_archivo,
    ms.ultimo_procesamiento,
    ds.periodo_inicio as datos_desde,
    ds.periodo_fin as datos_hasta
    
FROM mission_summary ms, data_summary ds, calls_summary cs;

-- 7.2 Comparativa entre operadores
-- Parámetros: :mission_id
SELECT 
    voms.operator,
    voms.archivos_procesados,
    voms.total_registros,
    voms.registros_datos,
    voms.usuarios_unicos_datos,
    voms.celdas_diferentes_datos,
    voms.registros_llamadas,
    voms.usuarios_unicos_llamadas,
    
    -- Métricas de calidad
    ROUND(
        (voms.registros_datos + voms.registros_llamadas) / 
        CAST(voms.total_registros AS REAL) * 100, 
        2
    ) as porcentaje_exito,
    
    -- Coverage intensity (registros por celda)
    ROUND(
        CAST(voms.registros_datos AS REAL) / 
        NULLIF(voms.celdas_diferentes_datos, 0), 
        1
    ) as registros_por_celda,
    
    -- User activity intensity
    ROUND(
        CAST(voms.registros_datos AS REAL) / 
        NULLIF(voms.usuarios_unicos_datos, 0), 
        1
    ) as sesiones_por_usuario,
    
    voms.periodo_inicio,
    voms.periodo_fin,
    
    julianday(voms.periodo_fin) - julianday(voms.periodo_inicio) as dias_cobertura
    
FROM v_operator_mission_stats voms
WHERE voms.mission_id = 'mission_001'  -- :mission_id
ORDER BY voms.total_registros DESC;

-- ============================================================================
-- NOTAS DE USO Y OPTIMIZACIÓN
-- ============================================================================
/*
INSTRUCCIONES PARA USO EFICIENTE:

1. PARÁMETROS:
   - Reemplazar valores hardcodeados con parámetros bindeados (:parametro)
   - Usar EXPLAIN QUERY PLAN para verificar uso de índices
   - Ajustar LIMIT según necesidades de paginación

2. PERFORMANCE:
   - Consultas complejas pueden requerir índices adicionales
   - Usar vistas materializadas para consultas frecuentes
   - Considerar ANALYZE después de cargas grandes de datos

3. MODIFICACIONES RECOMENDADAS:
   - Agregar filtros de fecha para datasets grandes
   - Implementar paginación en consultas que devuelven muchos registros
   - Usar transacciones para operaciones de escritura múltiples

4. MONITOREO:
   - Ejecutar consultas de performance regularmente
   - Monitorear tamaños de tablas y fragmentación
   - Verificar logs de procesamiento para errores recurrentes
*/