# ANÁLISIS DE DEBUG: DIAGRAMA DE CORRELACIÓN VACÍO

## PROBLEMA IDENTIFICADO
El diagrama G6 aparece vacío porque existen varios problemas críticos en la implementación.

## ANÁLISIS EXHAUSTIVO - CAUSAS RAÍZ ENCONTRADAS

### 🚨 PROBLEMA #1: API G6 v5 INCOMPATIBLE CON CÓDIGO v4
**CRÍTICO**: El código usa sintaxis de G6 v4, pero el paquete es v5.0.49

**Errores detectados:**
```typescript
// ❌ INCORRECTO - Sintaxis v4
const graph = new Graph({
    container: diagramContainerRef.current,
    width: diagramContainerRef.current.clientWidth,
    height: diagramContainerRef.current.clientHeight,
    layout: g6LayoutConfig, // <- PROBLEMA: layout ya no va en constructor v5
    modes: {
        default: ['drag-canvas', 'zoom-canvas', 'drag-node', 'click-select'] // <- PROBLEMA: sintaxis cambiada
    }
});

// ❌ INCORRECTO - Sintaxis v4  
graph.data(g6Data); // <- PROBLEMA: método cambiado en v5
graph.render(); // <- PROBLEMA: método cambiado en v5
```

**Solución requerida:**
```typescript
// ✅ CORRECTO - Sintaxis v5
const graph = new Graph({
    container: diagramContainerRef.current,
    width: diagramContainerRef.current.clientWidth,
    height: diagramContainerRef.current.clientHeight,
    data: g6Data, // <- CORRECTO: data va en constructor v5
    // layout se configura separadamente
    // behaviors se configuran separadamente
});
```

### 🚨 PROBLEMA #2: FILTROS EXCESIVAMENTE RESTRICTIVOS
**CRÍTICO**: Filtros por defecto pueden ocultar todos los nodos

**Código problemático (líneas 314-324):**
```typescript
const filteredNodes = nodes.filter(node => {
    return filters.correlationLevels.includes(node.correlationLevel) &&
           node.interactionCount >= filters.minInteractions &&
           (filters.operators.length === 0 || filters.operators.includes(node.operator));
});
```

**Problemas:**
1. Si `filters.operators` tiene valores pero no coinciden = 0 nodos
2. Si `minInteractions` es muy alto = 0 nodos  
3. Si datos del backend no tienen `correlationLevel` correcto = 0 nodos

### 🚨 PROBLEMA #3: ALGORITMO CORRELACIÓN PUEDE FALLAR
**CRÍTICO**: transformDataForDiagram() puede generar arrays vacíos

**Posibles fallas:**
1. `interactions` array vacío o malformado
2. `targetNumber` no coincide con datos
3. Fechas inválidas causan errores en Date()
4. Números secundarios undefined/null

### 🚨 PROBLEMA #4: INICIALIZACIÓN ASÍNCRONA PROBLEMÁTICA
**MEDIO**: Timing de inicialización G6 vs DOM ready

**Código problemático:**
```typescript
useEffect(() => {
    if (isOpen && diagramContainerRef.current) {
        const timer = setTimeout(initializeGraph, 100); // <- Timing arbitrario
        return () => clearTimeout(timer);
    }
}, [isOpen, initializeGraph]);
```

### 🚨 PROBLEMA #5: IMPORTS G6 INCOMPLETOS
**BAJO**: Falta importar funciones específicas v5

## DATOS DE EJEMPLO PARA TESTING

### Datos de entrada típicos:
```typescript
// Ejemplo de interactions[] que recibe el modal:
const sampleInteractions = [
    {
        numero_objetivo: "3001234567",
        numero_secundario: "3009876543", 
        fecha_hora: "2024-01-15T10:30:00",
        duracion_segundos: 120,
        operador: "CLARO",
        celda_inicio: "LAC123_CELL456",
        celda_final: "LAC124_CELL789",
        tipo_interaccion: "llamada",
        punto_hunter: "ZONA_CENTRO_01",
        lat_hunter: 6.2442,
        lon_hunter: -75.5812
    }
];
```

## PLAN DE ACCIÓN INMEDIATA

### ✅ PASO 1: Agregar debugging exhaustivo
```typescript
console.log("🔍 DEBUG: Datos recibidos en NetworkDiagramModal:", {
    interactions: interactions.length,
    targetNumber,
    sampleInteraction: interactions[0]
});

const { nodes, edges } = transformDataForDiagram();
console.log("🔍 DEBUG: Datos transformados:", {
    nodesCount: nodes.length,
    edgesCount: edges.length,
    sampleNode: nodes[0],
    sampleEdge: edges[0]
});

console.log("🔍 DEBUG: Filtros aplicados:", {
    filteredNodesCount: filteredNodes.length,
    filteredEdgesCount: filteredEdges.length,
    filters
});
```

### ✅ PASO 2: Migrar a G6 v5 API
- Actualizar constructor Graph()
- Cambiar data() por configuración en constructor
- Actualizar behaviors y layouts
- Corregir métodos de renderizado

### ✅ PASO 3: Implementar fallbacks defensivos
- Validar datos de entrada
- Manejar arrays vacíos
- Filtros menos restrictivos por defecto
- Mostrar mensajes informativos

### ✅ PASO 4: Testing progresivo
1. Verificar datos llegan al modal
2. Verificar transformación genera nodos/edges
3. Verificar filtros no excluyen todo
4. Verificar G6 se inicializa correctamente

## ARCHIVOS A MODIFICAR

1. **NetworkDiagramModal.tsx** - Migración API G6 v5 + debugging
2. **TableCorrelationModal.tsx** - Validación datos enviados
3. **NetworkDiagramControls.tsx** - Filtros menos restrictivos

## TIEMPO ESTIMADO SOLUCIÓN
- **Crítico**: 2-3 horas para migración G6 v5
- **Medio**: 1 hora para debugging y validaciones  
- **Testing**: 1 hora para verificación completa

**TOTAL**: ~4-5 horas

## PRIORIDAD DE IMPLEMENTACIÓN
1. 🔥 **INMEDIATO**: Debugging para identificar punto exacto de falla
2. 🔥 **INMEDIATO**: Migración API G6 v5 
3. 🟡 **ALTO**: Filtros defensivos y fallbacks
4. 🟢 **MEDIO**: Optimizaciones de performance

---
**Reporte generado**: 2025-08-20
**Analista**: Claude Code (Depurador especializado)