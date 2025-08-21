# IMPLEMENTACIÓN DIAGRAMA DE CORRELACIÓN TELEFÓNICA - REACT FLOW
## Fecha: 2025-08-21
## Desarrollador: Claude Code + Boris

### OBJETIVO
Implementar diagrama interactivo de correlación telefónica con 4 modos de visualización usando React Flow 11.11.4 ya instalado.

### ANÁLISIS INICIAL
- TableCorrelationModal.tsx ubicado en: `Frontend/components/ui/TableCorrelationModal.tsx`
- Toolbar en líneas 457-501 con botones CSV, Excel, Refrescar
- Interface CallInteraction completa (líneas 6-33)
- Función backend: `window.eel.get_call_interactions()`
- React Flow ya instalado: reactflow: ^11.11.4

### DATOS DE ENTRADA
```typescript
interface CallInteraction {
    originador: string;          // ej: "3132035363"
    receptor: string;            // ej: "3125996000"
    fecha_hora: string;          // ej: "20/05/2021 13:44"
    duracion: number;            // en segundos
    operador: string;            // ej: "CLARO"
    celda_origen: string;        // ej: "51438"
    celda_destino: string;       // ej: "22504"
    punto_hunter?: string;       // ej: "CARRERA 17 N° 71 A SUR"
    lat_hunter?: number;         // latitud GPS
    lon_hunter?: number;         // longitud GPS
    // ... campos adicionales
}
```

### PLAN DE IMPLEMENTACIÓN

#### FASE 1: ESTRUCTURA BASE
1. ✅ Crear directorio: `Frontend/components/diagrams/PhoneCorrelationDiagram/`
2. ✅ Agregar botón "Diagrama" al toolbar de TableCorrelationModal.tsx
3. ✅ Crear tipos TypeScript base
4. ✅ Crear componente modal principal para diagrama

#### FASE 2: TRANSFORMACIÓN DE DATOS
1. ✅ Hook para convertir CallInteraction[] → React Flow data
2. ✅ Funciones de análisis de números únicos
3. ✅ Generación de nodos y edges
4. ✅ Sistema de identificación de target central

#### FASE 3: MODOS DE VISUALIZACIÓN
1. ✅ Modo 1: Radial Central (target al centro, otros radiales)
2. ✅ Modo 2: Circular con Avatares (disposición circular)
3. ✅ Modo 3: Flujo Lineal (secuencia temporal)
4. ✅ Modo 4: Híbrido Inteligente (automático según cantidad)

#### FASE 4: COMPONENTES REACT FLOW
1. ✅ Nodos personalizados (RadialTargetNode, CircularAvatarNode, etc.)
2. ✅ Edges personalizados (curvas, flechas direccionales)
3. ✅ Layouts algorítmicos para cada modo
4. ✅ Sistema de colores y estilos

#### FASE 5: CONTROLES Y UX
1. ✅ Selector de modos (4 botones)
2. ✅ Controles de zoom y vista
3. ✅ Filtros (correlación mínima, IDs celda)
4. ✅ Export PNG/SVG/JSON
5. ✅ Sistema responsive

#### FASE 6: INTEGRACIÓN Y TESTING
1. ✅ Integración con modal existente
2. ✅ Testing con datos reales
3. ✅ Optimización de performance
4. ✅ Validación UX/UI

### ESTRUCTURA DE ARCHIVOS
```
Frontend/components/diagrams/PhoneCorrelationDiagram/
├── types/
│   └── correlation.types.ts
├── components/
│   ├── PhoneCorrelationViewer.tsx
│   ├── CorrelationModeSelector.tsx
│   ├── CorrelationControls.tsx
│   ├── nodes/
│   │   ├── RadialTargetNode.tsx
│   │   ├── RadialSourceNode.tsx
│   │   ├── CircularAvatarNode.tsx
│   │   └── LinearFlowNode.tsx
│   └── edges/
│       ├── CurvedConnectionEdge.tsx
│       ├── DirectionalArrowEdge.tsx
│       └── LinearConnectorEdge.tsx
├── hooks/
│   ├── useCorrelationData.ts
│   ├── useModeSelector.ts
│   ├── useRadialLayout.ts
│   ├── useCircularLayout.ts
│   ├── useLinearLayout.ts
│   └── useSmartModeDetection.ts
├── utils/
│   ├── layoutCalculations.ts
│   └── colorSchemes.ts
└── index.ts
```

### CARACTERÍSTICAS TÉCNICAS
- **React Flow**: 11.11.4 (ya instalado)
- **Modos**: 4 tipos de visualización
- **Target**: Número principal al centro/destacado
- **Filtros**: Correlación mínima, mostrar IDs celda
- **Export**: PNG, SVG, JSON
- **Responsive**: 90% x 85% del modal
- **Performance**: Memoización y optimización

### SEGUIMIENTO DE CAMBIOS
#### 2025-08-21 - Inicio
- [ ] Análisis de TableCorrelationModal.tsx completado
- [ ] Plan de implementación definido
- [ ] Estructura de archivos diseñada

#### PRÓXIMOS PASOS
1. Agregar botón diagrama al toolbar
2. Crear estructura de directorios
3. Implementar tipos TypeScript
4. Desarrollar componente principal

### NOTAS IMPORTANTES
- Mantener compatibilidad con CallInteraction existente
- No afectar funcionalidad actual del modal
- Seguir patrones de código KRONOS
- Usar avatarMale.svg para nodos circulares
- Implementar error boundaries