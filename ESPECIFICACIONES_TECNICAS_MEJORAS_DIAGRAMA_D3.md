# ESPECIFICACIONES TÉCNICAS - MEJORAS CRÍTICAS DIAGRAMA CORRELACIÓN D3.js

## Metadata del Proyecto
- **Proyecto**: KRONOS - Sistema de Correlación Telefónica
- **Componente**: PhoneCorrelationDiagram.tsx
- **Tecnología**: D3.js + React TypeScript
- **Fecha**: 2025-08-20
- **Solicitante**: Boris
- **Arquitecto**: Claude Code Senior UI/UX Engineer

---

## ANÁLISIS DE PROBLEMAS IDENTIFICADOS

### Estado Actual del Código
```typescript
// Ubicación: Frontend/components/diagrams/PhoneCorrelationDiagram/PhoneCorrelationDiagram.tsx
// Líneas críticas: 184-200 (nodos), 144-171 (enlaces), 13-35 (configuración)
```

### Problemas Identificados en Imagen Actual vs Especificación

**PROBLEMA 1**: ❌ Números truncados ("3208", "1203", "8601")
**PROBLEMA 2**: ❌ Falta avatares SVG (solo círculos de colores)
**PROBLEMA 3**: ❌ Sin flechas direccionales en enlaces
**PROBLEMA 4**: ❌ Diagrama pequeño + paleta de colores no corporativa

---

## 🎯 ESPECIFICACIÓN 1: NÚMEROS COMPLETOS EN NODOS

### **A. Análisis del Problema**
```typescript
// LÍNEA 200 ACTUAL - TRUNCADO:
.text(d => d.label);  // ❌ Muestra solo parte del número
```

### **B. Solución Técnica**
```typescript
// NUEVA IMPLEMENTACIÓN:
.text(d => {
  const fullNumber = d.id;
  const radius = d.isTarget ? DEFAULT_CONFIG.nodeRadius.target : DEFAULT_CONFIG.nodeRadius.regular;
  const avgCharWidth = 6; // Ancho promedio carácter en 10px font
  const maxChars = Math.floor((radius * 2 - 10) / avgCharWidth);
  
  // Estrategia: Últimos 4 dígitos si no cabe completo
  if (fullNumber.length > maxChars) {
    return '...' + fullNumber.slice(-4);
  }
  return fullNumber;
})
```

### **C. Parámetros de Configuración**
```typescript
// AGREGAR A DEFAULT_CONFIG:
text: {
  fontSize: {
    target: '11px',    // Nodo objetivo más grande
    regular: '10px'    // Nodos regulares
  },
  fontWeight: 'bold',
  color: '#ffffff',
  strategy: 'last4digits' // 'full' | 'last4digits' | 'truncate'
}
```

---

## 🎨 ESPECIFICACIÓN 2: INTEGRACIÓN AVATARES SVG

### **A. Asset Disponible**
```
Path: C:\Soluciones\BGC\claude\KNSOft\Frontend\images\avatar\avatarMale.svg
Dimensiones: 800x800px (escalable)
Formato: SVG con gradientes y estilos CSS
```

### **B. Implementación SVG en D3.js**
```typescript
// NUEVA FUNCIÓN PARA CARGAR SVG:
const loadAvatarSVG = async (avatarPath: string): Promise<string> => {
  try {
    const response = await fetch(avatarPath);
    const svgText = await response.text();
    return svgText;
  } catch (error) {
    console.warn('Avatar SVG not found:', avatarPath);
    return ''; // Fallback a círculo plano
  }
};

// IMPLEMENTACIÓN EN NODOS (REEMPLAZAR LÍNEAS 183-189):
const nodeGroups = nodeSelection
  .append('g')
  .attr('class', 'node-content');

// Background circle (mantener para fallback)
nodeGroups
  .append('circle')
  .attr('r', d => d.isTarget ? DEFAULT_CONFIG.nodeRadius.target : DEFAULT_CONFIG.nodeRadius.regular)
  .attr('fill', d => d.color)
  .attr('stroke', '#ffffff')
  .attr('stroke-width', d => d.isTarget ? 3 : 2);

// SVG Avatar overlay
nodeGroups.each(async function(d) {
  const avatarSize = (d.isTarget ? DEFAULT_CONFIG.nodeRadius.target : DEFAULT_CONFIG.nodeRadius.regular) * 1.8;
  
  try {
    const svgContent = await loadAvatarSVG('/images/avatar/avatarMale.svg');
    if (svgContent) {
      d3.select(this)
        .append('g')
        .attr('class', 'avatar-container')
        .html(svgContent)
        .select('svg')
        .attr('width', avatarSize)
        .attr('height', avatarSize)
        .attr('x', -avatarSize/2)
        .attr('y', -avatarSize/2)
        .style('clip-path', `circle(${(d.isTarget ? DEFAULT_CONFIG.nodeRadius.target : DEFAULT_CONFIG.nodeRadius.regular)}px)`);
    }
  } catch (error) {
    console.warn('Fallback to colored circle for:', d.id);
  }
});
```

### **C. Sistema de Cache y Performance**
```typescript
// CACHE GLOBAL PARA AVATARES:
const avatarCache = new Map<string, string>();

const getCachedAvatar = async (avatarId: string): Promise<string> => {
  if (avatarCache.has(avatarId)) {
    return avatarCache.get(avatarId)!;
  }
  
  const svgContent = await loadAvatarSVG(`/images/avatar/${avatarId}.svg`);
  avatarCache.set(avatarId, svgContent);
  return svgContent;
};
```

---

## 🎯 ESPECIFICACIÓN 3: FLECHAS DIRECCIONALES

### **A. Definición de Markers SVG**
```typescript
// AGREGAR DESPUÉS DE LÍNEA 112 (mainGroup):
// Definir markers para flechas direccionales
const defs = svg.append('defs');

// Flecha verde (salientes)
defs.append('marker')
  .attr('id', 'arrow-outgoing')
  .attr('viewBox', '0 -5 10 10')
  .attr('refX', 8)
  .attr('refY', 0)
  .attr('markerWidth', 6)
  .attr('markerHeight', 6)
  .attr('orient', 'auto')
  .append('path')
  .attr('d', 'M0,-5L10,0L0,5')
  .attr('fill', DEFAULT_CONFIG.colors.links.outgoing);

// Flecha azul (entrantes)  
defs.append('marker')
  .attr('id', 'arrow-incoming')
  .attr('viewBox', '0 -5 10 10')
  .attr('refX', 8)
  .attr('refY', 0)
  .attr('markerWidth', 6)
  .attr('markerHeight', 6)
  .attr('orient', 'auto')
  .append('path')
  .attr('d', 'M0,-5L10,0L0,5')
  .attr('fill', DEFAULT_CONFIG.colors.links.incoming);

// Flecha naranja (bidireccionales)
defs.append('marker')
  .attr('id', 'arrow-bidirectional')
  .attr('viewBox', '0 -5 10 10')
  .attr('refX', 8)
  .attr('refY', 0)
  .attr('markerWidth', 6)
  .attr('markerHeight', 6)
  .attr('orient', 'auto')
  .append('path')
  .attr('d', 'M0,-5L10,0L0,5')
  .attr('fill', DEFAULT_CONFIG.colors.links.bidirectional);
```

### **B. Aplicación de Flechas a Enlaces**
```typescript
// MODIFICAR LÍNEAS 144-153 (linkSelection):
const linkSelection = mainGroup
  .selectAll('.phone-link')
  .data(links)
  .enter()
  .append('line')
  .attr('class', 'phone-link')
  .attr('stroke', d => d.color)
  .attr('stroke-width', d => d.strength * DEFAULT_CONFIG.linkWidth.base)
  .attr('stroke-opacity', 0.8)
  .attr('marker-end', d => {
    // Asignar marker basado en dirección
    switch(d.direction) {
      case 'outgoing': return 'url(#arrow-outgoing)';
      case 'incoming': return 'url(#arrow-incoming)';
      case 'bidirectional': return 'url(#arrow-bidirectional)';
      default: return 'none';
    }
  })
  .style('cursor', 'pointer');
```

---

## 🎨 ESPECIFICACIÓN 4: ESCALADO Y PALETA KRONOS

### **A. Nueva Configuración de Tamaño**
```typescript
// REEMPLAZAR DEFAULT_CONFIG (LÍNEAS 13-35):
const DEFAULT_CONFIG: DiagramConfig = {
  // ✅ TAMAÑO AUMENTADO SIGNIFICANTLY
  width: 1200,   // +400px (era 800)
  height: 800,   // +200px (era 600)
  
  nodeRadius: {
    target: 35,      // +15px (era 20) - Nodo objetivo MÁS GRANDE
    regular: 25      // +10px (era 15) - Nodos regulares más grandes
  },
  
  linkWidth: {
    base: 3,         // +1px (era 2)
    strong: 6        // +2px (era 4)  
  },
  
  // ✅ PALETA KRONOS PROFESIONAL DARK THEME
  colors: {
    target: '#ff4444',          // Rojo vibrante objetivo (✅ mantenido)
    participants: [
      '#ff8c42',  // Naranja corporativo KRONOS
      '#e91e63',  // Rosa corporativo KRONOS
      '#4caf50',  // Verde corporativo KRONOS
      '#9c27b0',  // Púrpura corporativo KRONOS  
      '#2196f3',  // Azul corporativo KRONOS
      '#ff9800',  // Naranja secundario
      '#00bcd4'   // Cyan corporativo
    ],
    links: {
      incoming: '#2196f3',      // Azul corporativo para entrantes
      outgoing: '#4caf50',      // Verde corporativo para salientes  
      bidirectional: '#ff9800'  // Naranja corporativo para bidireccionales
    },
    // ✅ NUEVOS COLORES DE SOPORTE
    background: '#0f172a',      // Fondo ultra dark
    nodeStroke: '#f8fafc',      // Blanco stroke nodos
    textColor: '#ffffff',       // Texto blanco puro
    labelBackground: 'rgba(0,0,0,0.7)' // Fondo semi-transparente labels
  }
};
```

### **B. Ajustes Responsivos**
```typescript
// MODIFICAR updateDimensions (LÍNEAS 71-84):
const updateDimensions = useCallback(() => {
  if (containerRef.current) {
    const rect = containerRef.current.getBoundingClientRect();
    const padding = 40; // Reducido para aprovechar mejor el espacio
    
    // ✅ ESCALADO PROPORCIONAL MEJORADO
    const newWidth = Math.max(1200, rect.width - padding);  // Mínimo 1200px
    const newHeight = Math.max(800, rect.height - padding); // Mínimo 800px
    
    // Mantener aspect ratio 3:2 aproximadamente
    const aspectRatio = 1.5;
    const adjustedHeight = Math.min(newHeight, newWidth / aspectRatio);
    const finalHeight = Math.max(600, adjustedHeight); // Mínimo absoluto
    
    if (newWidth !== dimensions.width || finalHeight !== dimensions.height) {
      setDimensions({ width: newWidth, height: finalHeight });
      console.log('📏 PhoneCorrelationDiagram - KRONOS Scale:', { 
        width: newWidth, 
        height: finalHeight, 
        aspectRatio: (newWidth/finalHeight).toFixed(2) 
      });
    }
  }
}, [dimensions]);
```

---

## 🔧 IMPLEMENTACIÓN PASO A PASO

### **PASO 1: Backup y Preparación**
```bash
# Crear backup del componente actual
cp Frontend/components/diagrams/PhoneCorrelationDiagram/PhoneCorrelationDiagram.tsx \
   Frontend/components/diagrams/PhoneCorrelationDiagram/PhoneCorrelationDiagram.backup.tsx
```

### **PASO 2: Modificaciones por Problema**

#### **IMPLEMENTAR PROBLEMA 1** (Números completos)
- **Archivo**: `PhoneCorrelationDiagram.tsx`
- **Líneas**: 192-200
- **Acción**: Reemplazar lógica de texto en nodos

#### **IMPLEMENTAR PROBLEMA 2** (Avatares SVG) 
- **Archivo**: `PhoneCorrelationDiagram.tsx`
- **Líneas**: 183-189
- **Acción**: Agregar carga asíncrona de SVG

#### **IMPLEMENTAR PROBLEMA 3** (Flechas direccionales)
- **Archivo**: `PhoneCorrelationDiagram.tsx` 
- **Líneas**: 112 (defs), 144-153 (enlaces)
- **Acción**: Definir markers y aplicar a enlaces

#### **IMPLEMENTAR PROBLEMA 4** (Tamaño y colores)
- **Archivo**: `PhoneCorrelationDiagram.tsx`
- **Líneas**: 13-35, 71-84
- **Acción**: Actualizar configuración y responsive

---

## 📊 MÉTRICAS DE ÉXITO

### **Visual**
- ✅ Números telefónicos legibles (completos o últimos 4)
- ✅ Avatares SVG visibles en todos los nodos
- ✅ Flechas direccionales coloreadas en todos los enlaces  
- ✅ Diagrama 50% más grande (1200x800 vs 800x600)
- ✅ Paleta KRONOS aplicada consistentemente

### **Technical**
- ✅ Performance mantenida (simulación < 3s)
- ✅ Responsive design preservado
- ✅ Fallbacks implementados (SVG loading errors)
- ✅ TypeScript strict mode compliance
- ✅ Arquitectura D3.js existente mantenida

### **UX**
- ✅ Legibilidad mejorada en números y etiquetas
- ✅ Identidad visual KRONOS aplicada
- ✅ Direccionalidad de llamadas clara
- ✅ Información visual más rica

---

## ⚠️ CONSIDERACIONES CRÍTICAS

### **Performance**
```typescript
// SVG Async Loading - evitar bloqueo UI
const MAX_CONCURRENT_LOADS = 5;
const loadingQueue = new Map();
```

### **Fallbacks**
```typescript  
// Si SVG falla, mantener círculo coloreado
// Si fuente muy pequeña, usar '...' + últimos 4 dígitos
// Si conexión lenta, mostrar loading estado
```

### **Browser Compatibility**
```typescript
// SVG inline support: IE11+ ✅
// D3 markers: Todos los browsers modernos ✅
// Fetch API: Polyfill para IE si necesario
```

### **Accessibility**
```typescript
// ARIA labels para screen readers
.attr('aria-label', d => `Número ${d.id}, ${d.stats.incoming + d.stats.outgoing} interacciones`)
```

---

## 🚀 PLAN DE ROLLOUT

1. **IMPLEMENTACIÓN SECUENCIAL**: Un problema a la vez para testing
2. **TESTING**: Browser compatibility (Chrome, Firefox, Edge)
3. **FALLBACKS**: Verificar degradación elegante
4. **PERFORMANCE**: Validar no más de 500ms carga inicial
5. **UX VALIDATION**: Boris review visual final

**TIEMPO ESTIMADO**: 2-3 horas implementación + 1 hora testing

---

*Especificaciones técnicas generadas por Claude Code Senior UI/UX Engineer para proyecto KRONOS - 2025-08-20*