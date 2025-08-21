# PLAN DETALLADO - DIAGRAMA DE CORRELACIÓN TELEFÓNICA KRONOS

**Fecha de Creación**: 2025-08-20  
**Versión**: 1.0  
**Solicitado por**: Boris  
**Análisis realizado por**: ui-data-visualization-expert + ui-ux-enterprise-engineer  

---

## 📋 RESUMEN EJECUTIVO

Implementación de un nuevo diagrama de correlación telefónica que reemplazará la funcionalidad G6 actual, utilizando D3.js para crear una visualización profesional, moderna y ligera que muestre las interacciones telefónicas con nodos personalizables y drag & drop.

### **OBJETIVOS PRINCIPALES**:
1. Reemplazar diagrama G6 por implementación D3.js personalizada
2. Visualizar interacciones telefónicas con nodos circulares y enlaces etiquetados
3. Implementar personalización avanzada (nombres, avatares, posiciones)
4. Mantener diseño profesional consistente con tema dark de KRONOS

---

## 🎯 REQUERIMIENTOS CONFIRMADOS

### **FUNCIONALIDAD BASE**:
- **Ubicación**: Botón "🔗 Diagrama" en TableCorrelationModal existente
- **Datos fuente**: Interacciones de la tabla de correlación (ejemplo: 7 llamadas para 3143534707)
- **Visualización**: Nodos circulares con avatares, enlaces con etiquetas de celda
- **Interactividad**: Drag & drop, edición de nombres, cambio de avatares

### **ESPECIFICACIONES VISUALES**:
- **Nodo central**: Rojo, tamaño aumentado (número objetivo)
- **Nodos periféricos**: Colores únicos (naranja, rosa, verde, púrpura)
- **Enlaces**: Líneas directas con etiquetas de IDs de celdas
- **Direccionalidad**: Colores diferentes para llamadas entrantes/salientes
- **Layout**: Distribución orgánica (no force-directed estricto)

---

## 🛠 ARQUITECTURA TÉCNICA

### **TECNOLOGÍA SELECCIONADA**: D3.js v7

**Justificación**:
- Control total sobre visualización
- Drag & drop nativo integrado
- Performance superior (120KB vs 800KB G6)
- Excelente integración React + TypeScript
- Flexibilidad para personalización avanzada

### **ESTRUCTURA DE DATOS**:

```typescript
// Interfaces principales
interface PhoneNode {
  id: string;                    // Número telefónico
  label: string;                 // Nombre personalizable
  avatar: string;                // ID del avatar seleccionado
  color: string;                 // Color del nodo
  isTarget: boolean;             // Si es el número objetivo
  x?: number; y?: number;        // Posiciones para drag & drop
  fx?: number; fy?: number;      // Posiciones fijas
  stats: {
    incoming: number;            // Llamadas entrantes
    outgoing: number;            // Llamadas salientes
    totalDuration: number;       // Duración total en segundos
    lastContact: Date;           // Última interacción
  };
}

interface PhoneLink {
  source: string;                // ID nodo origen
  target: string;                // ID nodo destino
  cellIds: string[];             // IDs de celdas ["56124", "53591"]
  callCount: number;             // Número de llamadas
  direction: 'incoming' | 'outgoing' | 'bidirectional';
  strength: number;              // Grosor del enlace (1-5)
  color: string;                 // Color basado en direccionalidad
}

// Estado de personalización
interface CustomizationState {
  nodeLabels: Record<string, string>;        // Nombres personalizados
  nodeAvatars: Record<string, string>;       // Avatares seleccionados
  nodePositions: Record<string, {x: number, y: number}>; // Posiciones guardadas
  lastModified: string;                      // Timestamp de última modificación
}
```

---

## 🎨 DISEÑO UX/UI

### **SISTEMA VISUAL - DARK THEME**:

```scss
// Paleta de colores profesional
$colors: (
  // Nodos
  target: #ef4444,           // Rojo vibrante para objetivo
  participant-1: #f97316,    // Naranja
  participant-2: #ec4899,    // Rosa
  participant-3: #22c55e,    // Verde
  participant-4: #8b5cf6,    // Púrpura
  participant-5: #06b6d4,    // Cian
  
  // Enlaces por direccionalidad
  incoming: #3b82f6,         // Azul para entrantes
  outgoing: #10b981,         // Verde para salientes
  bidirectional: #8b5cf6,    // Púrpura para bidireccional
  
  // UI Base
  background: #111827,       // Fondo modal
  surface: #1f2937,          // Superficies elevadas
  border: #374151,           // Bordes
  text-primary: #f9fafb,     // Texto principal
  text-secondary: #9ca3af,   // Texto secundario
  text-muted: #6b7280,       // Texto deshabilitado
);

// Dimensiones y espaciado
$spacing: (
  node-size-target: 40px,    // Tamaño nodo objetivo
  node-size-regular: 32px,   // Tamaño nodos regulares  
  link-width-base: 2px,      // Grosor línea base
  link-width-strong: 4px,    // Grosor línea fuerte
  label-font-size: 11px,     // Tamaño texto etiquetas
  modal-padding: 24px,       // Padding interno modal
);
```

### **LAYOUT Y COMPONENTES**:

```
┌─────────────────────────────────────────────────────┐
│ Modal Header                                        │
│ ┌─ "Diagrama de Correlación - [3143534707]" ──┐ ┌─X─┐ │
│ │ 📞 5 contactos | 🔗 12 llamadas | 📍 4 celdas   │ │ │
│ └─────────────────────────────────────────────┘ └───┘ │
├─────────────────────────────────────────────────────┤
│ Toolbar                                             │
│ 🎨 Temas | 📝 Editar | 📋 Exportar | 🔄 Reset | 📐 │
├─────────────────────────────────────────────────────┤
│ Diagram Area (SVG Container)                        │
│                                                     │
│     🟠 EVER MOSCOSO        🔴 NERU           │
│     (3104277553)        (3224274851)         │
│           │  53591        /    \              │
│           │            51438   53591         │
│           │             /      \             │
│     🟣 YESSICA CRUZ ──56124─── 🟢 PT SUAREZ   │
│     (3143534707)              (3208611034)   │
│                                               │
├─────────────────────────────────────────────────────┤
│ Status Bar                                          │
│ Nodo: NERU | Celdas: 51438, 53591 | Pos: (250,180) │
└─────────────────────────────────────────────────────┘
```

---

## 📁 ESTRUCTURA DE COMPONENTES

```
Frontend/components/diagrams/
├── PhoneCorrelationDiagram/
│   ├── index.tsx                     # Exportación principal
│   ├── PhoneCorrelationDiagram.tsx   # Componente principal
│   ├── hooks/
│   │   ├── useD3Simulation.ts       # Simulación física D3
│   │   ├── useDragBehavior.ts       # Drag & drop behavior
│   │   ├── useNodeCustomization.ts  # Gestión personalización
│   │   └── useDataTransformer.ts    # Transformación datos
│   ├── components/
│   │   ├── DiagramNode.tsx          # Renderizado individual nodos
│   │   ├── DiagramLink.tsx          # Renderizado enlaces
│   │   ├── NodeEditor.tsx           # Editor inline nombres
│   │   ├── AvatarSelector.tsx       # Selector avatares
│   │   ├── DiagramToolbar.tsx       # Barra herramientas
│   │   ├── DiagramLegend.tsx        # Leyenda colores
│   │   └── StatusBar.tsx            # Barra estado
│   ├── utils/
│   │   ├── dataTransformer.ts       # Lógica transformación
│   │   ├── colorSystem.ts           # Sistema colores
│   │   ├── layoutEngine.ts          # Motor de layout
│   │   ├── persistenceManager.ts    # LocalStorage manager
│   │   └── exportUtils.ts           # Exportación PNG/SVG
│   └── types/
│       ├── diagram.types.ts         # Interfaces TypeScript
│       └── customization.types.ts   # Tipos personalización
```

---

## ⚙️ PLAN DE IMPLEMENTACIÓN POR FASES

### **FASE 1: SETUP Y VISUALIZACIÓN BÁSICA** (6-8 horas)
**Objetivo**: Reemplazar diagrama G6 con visualización D3 básica funcional

#### **Tareas Técnicas**:
1. **Instalación dependencias**:
   ```bash
   npm install d3 @types/d3
   npm install lodash @types/lodash  # Para utilidades
   ```

2. **Estructura base de componentes**:
   - Crear `PhoneCorrelationDiagram.tsx` principal
   - Implementar `useDataTransformer.ts` para convertir `UnifiedInteraction[]` → `{nodes, links}`
   - Setup SVG container con dimensiones responsivas

3. **Renderizado inicial**:
   - Nodos circulares con colores básicos
   - Enlaces simples sin etiquetas
   - Posicionamiento automático (layout fijo inicial)

4. **Integración con modal existente**:
   - Reemplazar `<NetworkDiagramModal>` con `<PhoneCorrelationDiagram>`
   - Mantener mismas props de entrada
   - Verificar que botón "🔗 Diagrama" abre nueva implementación

#### **Criterios de Aceptación Fase 1**:
- [ ] Modal se abre sin errores TypeScript
- [ ] Se muestran nodos coloreados (mínimo 3-5 nodos)
- [ ] Enlaces conectan nodos correctamente
- [ ] Nodo target es visualmente distinto (color rojo, tamaño mayor)
- [ ] Layout es legible y no hay solapamientos

---

### **FASE 2: DRAG & DROP + INTERACTIVIDAD** (4-6 horas)
**Objetivo**: Implementar drag & drop fluido con feedback visual

#### **Tareas Técnicas**:
1. **Sistema drag & drop**:
   - Implementar `useDragBehavior.ts` con D3 drag behavior
   - Fijar posiciones en localStorage al soltar
   - Visual feedback durante arrastre (opacity, shadow)

2. **Interactividad básica**:
   - Hover effects para nodos (escala, brillo)
   - Click handler para selección de nodos
   - Estados visuales claros (hover, active, selected)

3. **Etiquetas de enlaces**:
   - Renderizar IDs de celdas en centro de enlaces
   - Rotación automática de texto según ángulo enlace
   - Prevenir solapamiento de etiquetas

4. **Responsive container**:
   - Auto-resize del SVG según dimensiones modal
   - Zoom/pan básico para navegación
   - Touch-friendly para dispositivos móviles

#### **Criterios de Aceptación Fase 2**:
- [ ] Nodos se pueden arrastrar fluidamente
- [ ] Posiciones se guardan y restauran correctamente
- [ ] Etiquetas de celdas son legibles en todos los ángulos
- [ ] Hover effects son suaves y profesionales
- [ ] Funciona correctamente en touch devices

---

### **FASE 3: PERSONALIZACIÓN AVANZADA** (6-8 horas)
**Objetivo**: Sistema completo de personalización con editor inline y avatares

#### **Tareas Técnicas**:
1. **Editor de nombres inline**:
   - Click derecho abre editor contextual
   - Input field con validación
   - Auto-save en localStorage
   - ESC para cancelar, Enter para confirmar

2. **Sistema de avatares**:
   - Galería de 10-15 avatares predefinidos
   - Renderizado dentro de nodos circulares
   - Selector dropdown elegante
   - Preview en tiempo real

3. **Persistencia avanzada**:
   - `persistenceManager.ts` para LocalStorage
   - Versionado de datos guardados
   - Migración automática entre versiones
   - Reset a valores por defecto

4. **Toolbar funcional**:
   - Botones: Editar modo, Reset posiciones, Exportar
   - Estados activo/inactivo según contexto
   - Tooltips informativos

#### **Criterios de Aceptación Fase 3**:
- [ ] Click derecho abre editor nombres funcionalmente
- [ ] Cambio de avatar se refleja inmediatamente
- [ ] Personalizaciones persisten entre sesiones
- [ ] Reset restaura estado inicial correctamente
- [ ] Toolbar responde a acciones del usuario

---

### **FASE 4: PULIMENTO Y OPTIMIZACIÓN** (4-6 horas)
**Objetivo**: Optimizaciones finales, exportación y testing exhaustivo

#### **Tareas Técnicas**:
1. **Sistema de exportación**:
   - PNG con alta resolución (2x, 3x)
   - SVG con texto editable
   - JSON de configuración completa
   - Watermark opcional "Generado por KRONOS"

2. **Optimizaciones performance**:
   - Debouncing para actualizaciones frequentes
   - Lazy loading para avatares
   - Memory cleanup en unmount
   - Throttling para eventos drag

3. **Estados edge y errores**:
   - Manejo sin datos (mensaje informativo)
   - Loading states durante procesamiento
   - Error boundaries para fallos inesperados
   - Mensajes de usuario amigables

4. **Accesibilidad**:
   - Navegación por teclado (Tab, Enter, Space, Arrow keys)
   - ARIA labels para screen readers  
   - Contraste WCAG AA en todos los elementos
   - Focus indicators claros

#### **Criterios de Aceptación Fase 4**:
- [ ] Exportación PNG/SVG genera archivos válidos
- [ ] Performance es fluida con 20+ nodos
- [ ] Maneja gracefully casos de error
- [ ] Accesible por teclado completamente
- [ ] Todos los tests automatizados pasan

---

## 🧪 STRATEGY DE TESTING

### **TESTING UNITARIO**:
```typescript
// Ejemplos de tests críticos
describe('PhoneCorrelationDiagram', () => {
  test('transforma datos correctamente', () => {
    const interactions = mockInteractions;
    const {nodes, links} = transformInteractionData(interactions, '3143534707');
    expect(nodes).toHaveLength(5);
    expect(nodes.find(n => n.isTarget)).toBeDefined();
    expect(links.every(l => l.cellIds.length > 0)).toBe(true);
  });

  test('drag & drop actualiza posiciones', () => {
    const node = {id: '3143534707', x: 100, y: 100};
    const newPosition = {x: 200, y: 150};
    updateNodePosition(node.id, newPosition);
    expect(getPersistedPosition(node.id)).toEqual(newPosition);
  });

  test('personalización persiste correctamente', () => {
    setNodeCustomization('3143534707', {
      label: 'Boris García',
      avatar: 'user-male'
    });
    const customization = getNodeCustomization('3143534707');
    expect(customization.label).toBe('Boris García');
  });
});
```

### **TESTING E2E CON PLAYWRIGHT**:
```typescript
// Escenarios principales
test('diagrama se abre y muestra datos', async ({page}) => {
  await page.goto('http://localhost:8000');
  await page.click('[data-testid="correlation-analysis"]');
  await page.click('[data-testid="diagram-button"]');
  
  await expect(page.locator('[data-testid="phone-diagram"]')).toBeVisible();
  await expect(page.locator('.diagram-node')).toHaveCount.greaterThan(2);
  await expect(page.locator('.diagram-link')).toHaveCount.greaterThan(1);
});

test('drag & drop funciona correctamente', async ({page}) => {
  await openDiagram(page);
  const node = page.locator('.diagram-node').first();
  const initialPos = await node.boundingBox();
  
  await node.dragTo(page.locator('#diagram-svg'), {
    targetPosition: {x: initialPos.x + 100, y: initialPos.y + 50}
  });
  
  const finalPos = await node.boundingBox();
  expect(finalPos.x).toBeGreaterThan(initialPos.x + 80);
});
```

### **TESTING DE INTEGRACIÓN**:
- Verificar que datos del backend se procesan correctamente
- Validar que personalización persiste entre sesiones
- Comprobar responsive behavior en diferentes tamaños
- Testing de performance con datasets grandes (20-50 nodos)

---

## 📊 CRITERIOS DE ÉXITO

### **FUNCIONALIDAD**:
- [ ] Reemplaza completamente funcionalidad G6 anterior
- [ ] Visualiza correctamente todas las interacciones telefónicas
- [ ] Drag & drop funciona fluidamente sin lag
- [ ] Personalización (nombres/avatares) persiste correctamente
- [ ] Exportación genera archivos de calidad profesional

### **UX/UI**:
- [ ] Diseño consistente con tema dark KRONOS
- [ ] Interacciones intuitivas sin necesidad de training
- [ ] Responsive en desktop, tablet y móvil
- [ ] Tiempo de carga < 2 segundos para datasets típicos
- [ ] Accesible según estándares WCAG AA

### **TÉCNICO**:
- [ ] Cero errores TypeScript en build
- [ ] Cobertura de testing > 80%
- [ ] Bundle size optimizado (< 200KB adicionales)
- [ ] Performance testing con Chrome DevTools satisfactorio
- [ ] Compatible con navegadores modernos (Chrome 90+, Firefox 88+, Safari 14+)

### **BUSINESS**:
- [ ] Mejora significativa vs diagrama G6 anterior
- [ ] Feedback positivo de Boris en review sesión
- [ ] No introduce regresiones en funcionalidades existentes
- [ ] Documentación completa para mantenimiento futuro

---

## 📝 NOTAS DE IMPLEMENTACIÓN

### **LIBRERÍAS ADICIONALES RECOMENDADAS**:
```json
{
  "d3": "^7.8.5",
  "@types/d3": "^7.4.0",
  "lodash": "^4.17.21",
  "@types/lodash": "^4.14.195",
  "html2canvas": "^1.4.1",  // Para exportación PNG
  "file-saver": "^2.0.5"     // Para descarga archivos
}
```

### **CONFIGURACIONES ESPECIALES**:
- Vite config para optimizar bundle D3
- TypeScript strict mode compatible
- ESLint rules para D3 patterns
- Prettier config para código legible

### **CONSIDERACIONES DE MAINTENANCE**:
- Código documentado con JSDoc
- README específico del componente
- Changelog de versiones
- Migration guide desde G6

---

## 🎯 ENTREGABLES FINALES

1. **Componente funcional completo**: `PhoneCorrelationDiagram` integrado en KRONOS
2. **Documentación técnica**: README, JSDoc, comments inline
3. **Test suite completo**: Unitarios, integración, E2E con Playwright
4. **Guía de usuario**: Instrucciones para uso del diagrama
5. **Plan de migración**: Estrategia para deprecar G6 gradualmente

---

**Este plan detallado proporciona la base completa para que los agentes especializados (frontend-vite-expert, ui-ux-enterprise-engineer, code-reviewer, testing-engineer-vite-python) puedan ejecutar la implementación sin ambigüedades.**

**Próximo paso**: Ejecutar Fase 1 con agente frontend-vite-expert para setup inicial y visualización básica.