# GUÍA RÁPIDA - ALGORITMO DE CORRELACIÓN KRONOS

## INFORMACIÓN DEL DOCUMENTO
**Versión:** 1.0.0  
**Fecha:** 18 de Agosto, 2025  
**Autor:** Sistema de Documentación KRONOS para Boris  
**Propósito:** Referencia rápida para desarrolladores  

---

## RESUMEN EJECUTIVO EN 5 MINUTOS

### ¿Qué es el Algoritmo de Correlación KRONOS?
Sistema que **identifica números telefónicos que han utilizado las mismas celdas que un dispositivo HUNTER** durante períodos específicos.

### Problema Principal Resuelto
**Inflación por Contextos Múltiples:** El algoritmo anterior contaba la misma combinación número-celda múltiples veces debido a diferentes roles en comunicaciones.

**Ejemplo de Corrección:**
```
ANTES (Inflado):  Número 3143534707 = 6 ocurrencias
DESPUÉS (Exacto): Número 3143534707 = 2 ocurrencias reales
```

### Arquitectura en 30 Segundos
```
React Frontend ↔ Python Eel ↔ SQLite Database (31 índices optimizados)
```

---

## CONCEPTOS CLAVE

### 1. Datos HUNTER (cellular_data)
- **Propósito:** Mediciones de celdas realizadas con equipo HUNTER
- **Campo crítico:** `cell_id` - identificador de celda
- **Cantidad típica:** 50-200 celdas por misión

### 2. Datos CDR (operator_call_data)
- **Propósito:** Registros de llamadas de operadores móviles
- **Campos críticos:** `celda_origen`, `celda_destino` - correlacionan con `cell_id`
- **Operadores:** CLARO, MOVISTAR, TIGO, WOM

### 3. Correlación
- **Definición:** Número objetivo que usó celda X = celda detectada por HUNTER
- **Conteo:** 1 ocurrencia por combinación única número-celda
- **Sin inflación:** Misma celda no se cuenta múltiples veces por contextos diferentes

---

## ALGORITMO EN 3 PASOS

### Paso 1: Extraer Celdas HUNTER
```sql
SELECT DISTINCT cell_id 
FROM cellular_data 
WHERE mission_id = :mission_id
```

### Paso 2: Encontrar Números que Contactaron Celdas HUNTER
```sql
SELECT DISTINCT numero_origen as numero, operator 
FROM operator_call_data 
WHERE celda_origen IN (lista_celdas_hunter)
   OR celda_destino IN (lista_celdas_hunter)
```

### Paso 3: Contar Exactamente (Sin Inflación)
```sql
SELECT numero, operador, COUNT(*) as ocurrencias
FROM (
    SELECT DISTINCT numero, operador, celda  -- ← CLAVE: DISTINCT elimina duplicados
    FROM combinaciones_numero_celda
)
GROUP BY numero, operador
```

---

## ARCHIVOS CLAVE

### Backend Principal
```
Backend/services/correlation_service_dynamic.py  ← ALGORITMO PRINCIPAL
Backend/services/data_normalizer_service.py     ← NORMALIZACIÓN DE DATOS
Backend/services/file_processor_service.py      ← PROCESAMIENTO ARCHIVOS
Backend/main.py                                 ← ENDPOINT analyze_correlation()
```

### Base de Datos
```
Backend/kronos.db                               ← BASE DE DATOS SQLITE
Backend/database/correlation_optimization_      ← 31 ÍNDICES OPTIMIZADOS
indexes.sql
```

### Frontend
```
Frontend/pages/MissionDetail.tsx                ← INTERFAZ DE CORRELACIÓN
Frontend/services/api.ts                       ← LLAMADAS AL BACKEND
```

---

## CASOS DE USO RÁPIDOS

### Ejecutar Correlación desde Frontend
```typescript
const result = await window.eel.analyze_correlation(
    missionId, 
    "2021-01-01 00:00:00",     // start_datetime
    "2021-12-31 23:59:59",     // end_datetime  
    1                          // min_occurrences
);
```

### Ejecutar Correlación desde Backend
```python
from services.correlation_service_dynamic import get_correlation_service_dynamic

service = get_correlation_service_dynamic()
result = service.analyze_correlation(
    mission_id="mission_test",
    start_datetime="2021-01-01 00:00:00",
    end_datetime="2021-12-31 23:59:59", 
    min_occurrences=1
)
```

### Resultado Típico
```json
{
  "success": true,
  "data": [
    {
      "targetNumber": "3143534707",
      "operator": "CLARO",
      "occurrences": 2,
      "firstDetection": "2021-05-15 10:30:00",
      "lastDetection": "2021-05-15 11:45:00", 
      "relatedCells": ["16040", "37825"],
      "confidence": 79.0
    }
  ],
  "statistics": {
    "totalFound": 1,
    "processingTime": 0.12
  }
}
```

---

## NÚMEROS DE VALIDACIÓN

### Casos de Prueba Principales
- **3143534707** - Caso de corrección de inflación (2 ocurrencias, no 6)
- **3104277553** - Caso de normalización prefijo 57 (4 ocurrencias)
- **3243182028** - Caso de alta actividad (8 ocurrencias correctas)
- **3009120093** - Caso MOVISTAR con conversión Cell ID (3 ocurrencias)
- **3124390973** - Caso TIGO multi-sheet (5 ocurrencias)

### Validar Corrección Manualmente
```sql
-- Query de validación directa para 3143534707
SELECT numero_origen, numero_destino, celda_origen, celda_destino, 
       fecha_hora_llamada, operator
FROM operator_call_data 
WHERE (numero_origen = '3143534707' OR numero_destino = '3143534707')
  AND mission_id = 'mission_MPFRBNsb'
ORDER BY fecha_hora_llamada;

-- Debe mostrar registros que explican exactamente 2 ocurrencias
```

---

## TROUBLESHOOTING RÁPIDO

### Problema: "No correlaciones encontradas"
**Causas posibles:**
1. No hay celdas HUNTER en la misión → Cargar datos celulares
2. Formato de celdas incompatible → Verificar conversión decimal/hex
3. Período temporal incorrecto → Ampliar rango de fechas
4. Números con prefijo 57 → Algoritmo normaliza automáticamente

### Problema: "Consulta muy lenta"
**Soluciones:**
1. Verificar que índices están activos: `PRAGMA index_list('operator_call_data');`
2. Actualizar estadísticas: `ANALYZE;`
3. Reducir período temporal o min_occurrences

### Problema: "Números inflados (muy altos)"
**Verificación:**
- Usar algoritmo v2.0 (CorrelationServiceDynamic)
- Confirmar que usa `GROUP BY numero, operador, celda`
- Validar strategy='DynamicCorrected_v2.0' en resultado

---

## COMANDOS DE MANTENIMIENTO

### Optimizar Base de Datos
```bash
# Desde Backend/
sqlite3 kronos.db "ANALYZE; PRAGMA optimize;"
```

### Verificar Integridad
```bash
sqlite3 kronos.db "PRAGMA integrity_check;"
```

### Backup
```bash
cp kronos.db kronos_backup_$(date +%Y%m%d_%H%M%S).db
```

### Ver Estadísticas
```sql
SELECT COUNT(*) as cellular_records FROM cellular_data;
SELECT COUNT(*) as operator_records FROM operator_call_data;
SELECT COUNT(*) as missions FROM missions;
```

---

## CONFIGURACIÓN RÁPIDA

### Inicializar Proyecto
```bash
# 1. Backend
cd Backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Frontend  
cd ../Frontend
npm install
npm run build

# 3. Base de datos
cd ../Backend
sqlite3 kronos.db < database/correlation_optimization_indexes.sql
```

### Ejecutar Aplicación
```bash
# Desde Backend/
python main.py
```

---

## MÉTRICAS DE RENDIMIENTO

### Tiempos Típicos
- **Extracción celdas HUNTER:** < 20ms
- **Correlación principal:** < 150ms  
- **Agregación final:** < 30ms
- **Total end-to-end:** < 200ms

### Límites Prácticos
- **Celdas HUNTER:** Hasta 500 celdas sin degradación
- **Registros CDR:** Hasta 100K registros por misión
- **Números objetivo:** Sin límite práctico
- **Memoria:** Típicamente < 50MB

---

## CHECKLIST DE VALIDACIÓN

### ✅ Verificaciones Básicas
- [ ] Datos celulares cargados en la misión
- [ ] Datos de operador cargados y procesados
- [ ] Período temporal incluye actividad objetivo
- [ ] min_occurrences apropiado (típicamente 1-3)

### ✅ Verificaciones de Calidad
- [ ] Resultados no inflados (strategy='DynamicCorrected_v2.0')
- [ ] Números normalizados sin prefijo 57
- [ ] Celdas en formato compatible Hunter↔Operador
- [ ] Tiempo de respuesta < 2 segundos

### ✅ Verificaciones de Producción
- [ ] Índices activos y optimizados
- [ ] Base de datos < 1GB para rendimiento óptimo
- [ ] Backup reciente disponible
- [ ] Logs sin errores críticos

---

## CONTACTO Y SOPORTE

### Para Desarrolladores
- **Documentación completa:** `/documentacion/ALGORITMO_CORRELACION_KRONOS_DOCUMENTACION_TECNICA.md`
- **Casos de validación:** `/documentacion/CASOS_USO_VALIDACION_ALGORITMO.md`
- **Esquema BD:** `/documentacion/ESQUEMA_BASE_DATOS_KRONOS.md`

### Para Debugging
1. Activar logs detallados en `correlation_service_dynamic.py`
2. Usar números de validación conocidos (3143534707, 3104277553)
3. Verificar con query SQL manual
4. Comparar con resultados esperados documentados

---

**¿Necesitas más detalles?** Consulta la documentación técnica completa en la carpeta `/documentacion/`

---

**Documento generado automáticamente por el Sistema de Documentación KRONOS**  
**Última actualización:** 18 de Agosto, 2025  
**Versión de referencia rápida:** v1.0.0