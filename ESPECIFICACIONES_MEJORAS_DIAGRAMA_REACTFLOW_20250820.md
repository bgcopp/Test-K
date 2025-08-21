# ESPECIFICACIONES TÉCNICAS - MEJORAS DIAGRAMA REACT FLOW
**Fecha**: 2025-08-20  
**Solicitante**: Boris  
**Objetivo**: Resolver problemas de etiquetas superpuestas y visibilidad de flechas

## 1. PROBLEMAS IDENTIFICADOS

### A. ETIQUETAS SUPERPUESTAS
**Archivo afectado**: `CustomPhoneEdge.tsx` (líneas 115-147)
- Las etiquetas de ID de celda se posicionan en el centro exacto de cada línea
- No hay detección de colisiones entre etiquetas cercanas
- Múltiples líneas paralelas causan superposición visual de las cajas negras
- IDs como "63895", "56124", "2523" se solapan en líneas adyacentes

### B. FLECHAS CON POCA VISIBILIDAD
**Archivo afectado**: `CustomPhoneEdge.tsx` (líneas 72-96)
- Flechas triangulares actuales pueden perder contraste
- Tamaño mínimo de 8px puede ser insuficiente en algunos casos
- Geometría triangular compleja vs rectangular simple
- stroke-width de contorno 0.5px puede ser muy delgado

## 2. SOLUCIONES TÉCNICAS PROPUESTAS

### A. SISTEMA ANTI-SUPERPOSICIÓN DE ETIQUETAS

#### A.1. DETECCIÓN DE COLISIONES
```typescript
interface LabelPosition {
  x: number;
  y: number;
  width: number;
  height: number;
  edgeId: string;
}

// Algoritmo de detección de colisiones
const detectCollisions = (positions: LabelPosition[]): CollisionGroup[] => {
  const collisions: CollisionGroup[] = [];
  
  for (let i = 0; i < positions.length; i++) {
    for (let j = i + 1; j < positions.length; j++) {
      const a = positions[i];
      const b = positions[j];
      
      // Verificar superposición con margen de 10px
      const margin = 10;
      if (
        a.x < b.x + b.width + margin &&
        a.x + a.width + margin > b.x &&
        a.y < b.y + b.height + margin &&
        a.y + a.height + margin > b.y
      ) {
        // Hay colisión - agrupar etiquetas
        addToCollisionGroup(collisions, a, b);
      }
    }
  }
  
  return collisions;
};
```

#### A.2. POSICIONAMIENTO INTELIGENTE CON OFFSETS
```typescript
const calculateOptimalPositions = (
  collisionGroups: CollisionGroup[],
  edgePath: string
): LabelPosition[] => {
  return collisionGroups.map(group => {
    if (group.labels.length === 1) {
      // Sin colisión - posición central
      return group.labels[0];
    }
    
    // Múltiples etiquetas - distribuir en espiral
    return group.labels.map((label, index) => {
      const angle = (index * 2 * Math.PI) / group.labels.length;
      const radius = 25 + (index * 8); // Incremento de radio
      
      return {
        ...label,
        x: label.x + Math.cos(angle) * radius,
        y: label.y + Math.sin(angle) * radius
      };
    });
  }).flat();
};
```

#### A.3. IMPLEMENTACIÓN EN CustomPhoneEdge
```typescript
// Nuevo hook para gestión de posiciones
const useLabelCollisionAvoidance = (
  edgeId: string,
  labelX: number,
  labelY: number,
  cellId: string
) => {
  const [adjustedPosition, setAdjustedPosition] = useState({ x: labelX, y: labelY });
  
  useEffect(() => {
    // Registrar posición en store global
    registerLabelPosition(edgeId, { x: labelX, y: labelY, cellId });
    
    // Recalcular posiciones óptimas
    const optimalPosition = calculateOptimalPosition(edgeId);
    setAdjustedPosition(optimalPosition);
  }, [edgeId, labelX, labelY, cellId]);
  
  return adjustedPosition;
};

// En el componente CustomPhoneEdge
const adjustedPosition = useLabelCollisionAvoidance(id, labelX, labelY, primaryCellId);
```

### B. MEJORA DE VISIBILIDAD DE FLECHAS

#### B.1. EVALUACIÓN: FLECHAS RECTANGULARES VS TRIANGULARES

**PROPUESTA**: Implementar flechas rectangulares con mejor contraste:

```typescript
// Flecha rectangular optimizada para investigadores
const createRectangularArrow = (arrowSize: number, color: string, selected: boolean) => {
  const width = arrowSize;
  const height = arrowSize * 0.4; // Proporción rectangular
  
  return (
    <marker
      id={markerId}
      markerWidth={width}
      markerHeight={height}
      refX={width - 1}
      refY={height / 2}
      orient="auto"
      markerUnits="userSpaceOnUse"
    >
      {/* Cuerpo rectangular sólido */}
      <rect
        x="2"
        y="1"
        width={width - 6}
        height={height - 2}
        fill={color}
        stroke="white"
        strokeWidth="1.5" // Contorno más grueso
        opacity={selected ? 1.0 : 0.9}
      />
      
      {/* Punta triangular nítida */}
      <path
        d={`M${width - 4},1 L${width - 1},${height / 2} L${width - 4},${height - 1} z`}
        fill={color}
        stroke="white"
        strokeWidth="1.5"
        opacity={selected ? 1.0 : 0.9}
      />
      
      {/* Sombra para mayor contraste */}
      <filter id="arrow-shadow">
        <feDropShadow dx="1" dy="1" stdDeviation="1" floodColor="black" floodOpacity="0.8"/>
      </filter>
    </marker>
  );
};
```

#### B.2. TAMAÑO ADAPTATIVO MÁS AGRESIVO
```typescript
// Incrementar tamaños mínimos para mejor visibilidad
const calculateArrowSize = (strokeWidth: number, isSelected: boolean) => {
  const baseSize = Math.max(strokeWidth * 3, 12); // Mínimo 12px (antes 8px)
  const selectedMultiplier = isSelected ? 1.4 : 1.0;
  const maxSize = 18; // Máximo aumentado para casos extremos
  
  return Math.min(baseSize * selectedMultiplier, maxSize);
};
```

#### B.3. CONTRASTE MEJORADO CON SOMBRAS
```typescript
const arrowStyle = {
  filter: selected 
    ? `drop-shadow(0 0 4px ${data.color}) drop-shadow(0 2px 4px rgba(0,0,0,0.8))`
    : 'drop-shadow(0 2px 3px rgba(0,0,0,0.6))',
  stroke: '#ffffff',
  strokeWidth: selected ? 2 : 1.5,
  strokeOpacity: 0.9
};
```

## 3. IMPLEMENTACIÓN RECOMENDADA

### FASE 1: ANTI-SUPERPOSICIÓN ETIQUETAS (PRIORIDAD ALTA)
1. Crear hook `useLabelCollisionAvoidance`
2. Implementar store global para posiciones de etiquetas
3. Algoritmo de detección de colisiones con margen de 10px
4. Sistema de offsets en espiral para múltiples colisiones

### FASE 2: MEJORA FLECHAS (PRIORIDAD MEDIA)
1. Implementar flechas rectangulares como opción
2. Incrementar tamaños mínimos (8px → 12px)
3. Mejorar contraste con sombras más pronunciadas
4. A/B test para determinar preferencia investigadores

### FASE 3: OPTIMIZACIONES ADICIONALES (PRIORIDAD BAJA)
1. Rotación de texto si es necesario
2. Animaciones sutiles para transiciones
3. Modo alto contraste para análisis intensivos

## 4. CONSIDERACIONES TÉCNICAS

### RENDIMIENTO
- Detección de colisiones solo cuando cambian los edges
- Debounce para recálculos (300ms)
- Memoización de posiciones calculadas

### USABILIDAD INVESTIGADORES
- Mantener legibilidad de IDs de celda como prioridad #1
- Flechas obviamente direccionales para análisis de comunicación
- Colores consistentes con flujo entrante/saliente

### COMPATIBILIDAD
- Fallback a posición original si algoritmo falla
- Mantener compatibilidad con React Flow v12+
- Testear en diferentes resoluciones de pantalla

## 5. MÉTRICAS DE ÉXITO

### A. ETIQUETAS
- ✅ 0% superposición visual entre etiquetas
- ✅ 100% legibilidad de IDs de celda
- ✅ Distancia mínima 10px entre etiquetas

### B. FLECHAS  
- ✅ Visibilidad clara en todas las líneas
- ✅ Dirección obvia para investigadores
- ✅ Contraste suficiente sobre fondos oscuros

---

**Próximos Pasos**: 
1. ¿Prefieres flechas rectangulares o triangulares mejoradas?
2. ¿Qué prioridad das a cada mejora?
3. ¿Hay restricciones de rendimiento específicas?