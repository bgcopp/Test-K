# ESPECIFICACIONES TÉCNICAS: HISTORIAL DE COMUNICACIONES ENTRE NÚMEROS
# KRONOS - Análisis Forense de Comunicaciones

**Fecha:** 2025-08-21  
**Desarrollador:** Boris  
**Contexto:** Funcionalidad activada desde diagrama de correlación React Flow  

---

## 📊 ANÁLISIS DE INFRAESTRUCTURA EXISTENTE

### ✅ **ESTRUCTURA DE DATOS YA DISPONIBLE**

La base de datos `kronos.db` ya contiene toda la información necesaria:

- **3,392 registros** en `operator_call_data` con historial completo
- **Correlación automática** con datos HUNTER en `cellular_data`  
- **15+ índices especializados** para consultas optimizadas
- **Función Eel operativa:** `get_call_interactions` con lógica bidireccional

### 🎯 **OBJETIVO DEL DESARROLLO**

Crear funciones especializadas para el frontend React que permitan:

1. **Historial bidireccional** entre números específicos desde el diagrama
2. **Análisis temporal** de patrones de comunicación
3. **Correlación geográfica** con datos HUNTER reales
4. **Estadísticas forenses** para investigadores

---

## 🔧 ARQUITECTURA PROPUESTA

### **1. NUEVAS FUNCIONES EEL ESPECIALIZADAS**

#### **A) `get_communication_history` - Función Principal**

```python
@eel.expose
def get_communication_history(mission_id: str, number_a: str, number_b: str, 
                            date_range: dict = None, filters: dict = None) -> dict:
```

**Propósito:** Obtener historial completo entre dos números específicos  
**Optimización:** Query bidireccional con UNION para máximo rendimiento  
**Salida:** Timeline completo con estadísticas y correlación HUNTER  

**Query SQL Optimizada:**
```sql
-- Consulta bidireccional eficiente usando UNION
SELECT * FROM (
    -- Llamadas A → B
    SELECT numero_origen as caller, numero_destino as receiver, 'A_TO_B' as direction,
           fecha_hora_llamada, duracion_segundos, operator, celda_origen, celda_destino,
           cd_origen.punto as origin_hunter, cd_destino.punto as dest_hunter
    FROM operator_call_data ocd
    LEFT JOIN cellular_data cd_origen ON cd_origen.cell_id = ocd.celda_origen 
    LEFT JOIN cellular_data cd_destino ON cd_destino.cell_id = ocd.celda_destino
    WHERE mission_id = ? AND numero_origen = ? AND numero_destino = ?
    
    UNION ALL
    
    -- Llamadas B → A  
    SELECT numero_origen as caller, numero_destino as receiver, 'B_TO_A' as direction,
           fecha_hora_llamada, duracion_segundos, operator, celda_origen, celda_destino,
           cd_origen.punto as origin_hunter, cd_destino.punto as dest_hunter
    FROM operator_call_data ocd
    LEFT JOIN cellular_data cd_origen ON cd_origen.cell_id = ocd.celda_origen
    LEFT JOIN cellular_data cd_destino ON cd_destino.cell_id = ocd.celda_destino  
    WHERE mission_id = ? AND numero_origen = ? AND numero_destino = ?
)
ORDER BY fecha_hora_llamada DESC;
```

**Datos de Salida:**
```json
{
    "success": true,
    "total_calls": 47,
    "total_duration_minutes": 156.8,
    "date_range": {"first": "2021-05-20T08:15:22", "last": "2021-05-25T19:42:15"},
    "calls": [
        {
            "call_id": "operator_call_data:1234",
            "direction": "A_TO_B",
            "timestamp": "2021-05-20T10:02:26", 
            "duration_seconds": 91,
            "duration_formatted": "01:31",
            "operator": "CLARO",
            "call_type": "ENTRANTE",
            "call_status": "COMPLETADA",
            "technology": "LTE",
            "origin_cell": "20264",
            "destination_cell": "20264", 
            "cell_locations": {
                "origin": {"lat": 4.6482, "lon": -74.0648, "hunter_point": "HUNTER_001"},
                "destination": {"lat": 4.6482, "lon": -74.0648, "hunter_point": "HUNTER_001"}
            },
            "estimated_distance_km": 0.0,
            "location_precision": "ALTA"
        }
    ],
    "statistics": {
        "calls_by_direction": {"A_TO_B": 25, "B_TO_A": 22},
        "calls_by_operator": {"CLARO": 47, "MOVISTAR": 0},
        "calls_by_hour": {"08": 3, "10": 8, "14": 12, "18": 15, "20": 9},
        "average_duration_minutes": 3.34,
        "peak_activity_hour": "18:00",
        "unique_cells_used": 8
    },
    "timeline": [
        {
            "date": "2021-05-20",
            "total_calls": 15,
            "total_duration_minutes": 45.2,
            "first_call": "08:15:22",
            "last_call": "19:42:15"
        }
    ]
}
```

#### **B) `get_call_details` - Detalles Técnicos**

```python
@eel.expose  
def get_call_details(mission_id: str, call_id: str) -> dict:
```

**Propósito:** Análisis forense detallado de llamada específica  
**Características:**
- Metadatos técnicos completos
- Correlación HUNTER precisa  
- Indicadores de patrones
- Contexto temporal (actividad relacionada)

#### **C) `get_related_communications` - Análisis Avanzado**

```python
@eel.expose
def get_related_communications(mission_id: str, number_a: str, number_b: str, 
                             analysis_type: str = "extended") -> dict:
```

**Propósito:** Detectar patrones y conexiones indirectas  
**Análisis incluidos:**
- Contactos comunes (intermediarios potenciales)
- Correlaciones temporales
- Celdas compartidas  
- Movimiento sincronizado

---

## 🚀 OPTIMIZACIONES DE RENDIMIENTO

### **NUEVOS ÍNDICES ESPECIALIZADOS**

```sql
-- 1. HISTORIAL BIDIRECCIONAL OPTIMIZADO
CREATE INDEX idx_calls_bidirectional_history 
ON operator_call_data(mission_id, numero_origen, numero_destino, fecha_hora_llamada DESC);

-- 2. BÚSQUEDA INVERSA PARA EFICIENCIA
CREATE INDEX idx_calls_bidirectional_inverse 
ON operator_call_data(mission_id, numero_destino, numero_origen, fecha_hora_llamada DESC);

-- 3. ANÁLISIS TEMPORAL AVANZADO
CREATE INDEX idx_calls_temporal_analysis 
ON operator_call_data(fecha_hora_llamada, mission_id, numero_origen, numero_destino, duracion_segundos);

-- 4. CORRELACIÓN GEOGRÁFICA
CREATE INDEX idx_calls_geographic_correlation 
ON operator_call_data(mission_id, celda_origen, celda_destino, fecha_hora_llamada);

-- 5. ESTADÍSTICAS POR OPERADOR
CREATE INDEX idx_calls_operator_participants 
ON operator_call_data(operator, mission_id, numero_origen, numero_destino);
```

### **ESTRATEGIAS DE OPTIMIZACIÓN**

1. **Query Bidireccional con UNION:** Evita múltiples consultas
2. **LEFT JOINs Condicionales:** Solo cuando se necesita correlación HUNTER
3. **Índices Compuestos:** Cubren consultas completas sin table scan
4. **Prepared Statements:** Reutilización de planes de ejecución
5. **Paginación Inteligente:** Para historiales extensos (>500 llamadas)

---

## 💡 INTEGRACIÓN CON FRONTEND REACT

### **ACTIVACIÓN DESDE DIAGRAMA**

El frontend React Flow detectará clicks en enlaces del diagrama y llamará:

```javascript
// Desde componente React Flow
const handleLinkClick = async (linkData) => {
    const { numberA, numberB, missionId } = linkData;
    
    // Llamar nueva función Eel
    const history = await window.eel.get_communication_history(
        missionId, 
        numberA, 
        numberB,
        { start: "2021-05-20 00:00:00", end: "2021-05-25 23:59:59" },
        { operators: ["CLARO"], min_duration: 10 }
    )();
    
    // Mostrar en modal o página dedicada
    showCommunicationHistoryModal(history);
};
```

### **COMPONENTES UI SUGERIDOS**

1. **`CommunicationHistoryModal`** - Modal principal con timeline
2. **`CallDetailPanel`** - Panel lateral con detalles técnicos  
3. **`GeographicVisualization`** - Mapa con ubicaciones HUNTER
4. **`PatternAnalysisChart`** - Gráficos de patrones temporales
5. **`StatisticsPanel`** - Métricas forenses resumidas

---

## 🔒 CONSIDERACIONES DE SEGURIDAD

### **VALIDACIÓN DE ENTRADA**
- Sanitización de números telefónicos
- Validación de rangos de fechas
- Verificación de permisos por misión
- Prevención de SQL injection (parametros preparados)

### **CONTROL DE ACCESO**
- Verificar que usuario tiene acceso a la misión específica  
- Auditoría de consultas sensibles
- Rate limiting para prevenir abuso
- Logs forenses para trazabilidad

### **PRIVACIDAD DE DATOS**
- Ofuscación opcional de números (según configuración)
- Exportación controlada de resultados
- Cumplimiento con regulaciones locales

---

## 📈 MÉTRICAS DE RENDIMIENTO ESPERADAS

### **CONSULTAS BASE (Sin Optimización)**
- Historial 100 llamadas: ~150ms
- Historial 1,000 llamadas: ~800ms  
- Análisis correlación: ~2,500ms

### **CONSULTAS OPTIMIZADAS (Con Índices Propuestos)**
- Historial 100 llamadas: ~45ms
- Historial 1,000 llamadas: ~180ms
- Análisis correlación: ~450ms

### **MEJORA ESPERADA**
- **Reducción 70%** en tiempo de respuesta
- **Escalabilidad** para datasets grandes
- **Concurrencia** mejorada para múltiples usuarios

---

## 🚀 PLAN DE IMPLEMENTACIÓN

### **FASE 1: Funciones Base (2-3 días)**
1. Implementar `get_communication_history`
2. Crear índices especializados
3. Testing básico con datos existentes

### **FASE 2: Análisis Avanzado (2-3 días)**  
1. Implementar `get_call_details`
2. Implementar `get_related_communications`
3. Optimizar queries complejas

### **FASE 3: Integración Frontend (1-2 días)**
1. Conectar con React Flow diagram
2. Crear componentes UI especializados
3. Testing de integración completa

### **FASE 4: Optimización y Testing (1-2 días)**
1. Profiling de rendimiento
2. Testing de carga con datasets grandes
3. Documentación final para usuarios

---

## 📝 ARCHIVOS A CREAR/MODIFICAR

### **Backend Python:**
- `services/communication_history_service.py` (NUEVO)
- `main.py` (MODIFICAR - agregar funciones Eel)
- `database/migration_history_indexes.sql` (NUEVO)

### **Frontend React:**
- `components/ui/CommunicationHistoryModal.tsx` (NUEVO)
- `components/diagrams/NetworkDiagram.tsx` (MODIFICAR)
- `services/api.ts` (MODIFICAR - nuevos endpoints)

### **Base de Datos:**
- Script SQL para nuevos índices
- Testing de rendimiento pre/post optimización

---

## 🎯 BENEFICIOS ESPERADOS

### **PARA INVESTIGADORES:**
- **Historial completo** entre números específicos
- **Correlación geográfica** automática con datos HUNTER
- **Patrones temporales** visualizados claramente
- **Análisis forense** con detalles técnicos completos

### **PARA EL SISTEMA:**
- **Reutilización** de infraestructura existente
- **Escalabilidad** para datasets grandes
- **Mantenibilidad** con servicios modulares
- **Rendimiento** optimizado para investigación en tiempo real

---

## ⚠️ CONSIDERACIONES CRÍTICAS

1. **No afectar funcionalidad existente** de correlación
2. **Mantener compatibilidad** con estructura actual
3. **Optimizar para investigación forense** (precisión > velocidad)
4. **Preparar para escalabilidad** futura (millones de registros)

---

**PRÓXIMOS PASOS RECOMENDADOS:**

1. ✅ Revisar y aprobar especificaciones
2. 🔄 Implementar `get_communication_history` como función base
3. 🔄 Crear índices especializados de rendimiento
4. 🔄 Testing con datos reales de la misión actual
5. 🔄 Integración con React Flow para activación desde diagrama

**Boris, esta arquitectura leverages tu infraestructura existente mientras añade las capacidades específicas de historial que necesitas para el diagrama de correlación. ¿Te parece adecuado el enfoque o quieres que ajuste algún aspecto específico?**