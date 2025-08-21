# PLAN UX/UI COMPLETO: DIAGRAMA DE CORRELACIÓN TELEFÓNICA HÍBRIDO
**Fecha**: 2025-08-21  
**Responsable**: Especialista UX/UI Senior  
**Solicitante**: Boris  
**Proyecto**: KRONOS - Sistema de Investigación Telefónica  

---

## 📋 ÍNDICE
1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Análisis UX de Modelos Existentes](#análisis-ux)
3. [Estrategia de Combinación Híbrida](#estrategia-combinación)
4. [Arquitectura de Componentes](#arquitectura-componentes)
5. [Wireframes y Layouts Detallados](#wireframes)
6. [Sistema de Colores y Semántica Visual](#sistema-colores)
7. [Especificaciones de Interacción](#especificaciones-interacción)
8. [Responsive Design y Accesibilidad](#responsive-accesibilidad)
9. [Flujo de Usuario Completo](#flujo-usuario)
10. [Tareas Detalladas por Equipo](#tareas-equipos)

---

## 1. RESUMEN EJECUTIVO {#resumen-ejecutivo}

### OBJETIVO PRINCIPAL
Implementar un sistema de visualización de correlación telefónica con **4 modos específicos confirmados**: Radial Central (predeterminado), Circular con Avatares, Flujo Lineal, e Híbrido Inteligente, permitiendo alternancia instantánea para optimizar diferentes tipos de análisis forense.

### BENEFICIOS ESPERADOS
- **Flexibilidad Visual**: Adaptación a diferentes tipos de análisis forense
- **Experiencia Profesional**: Interface digna para investigadores especializados  
- **Usabilidad Optimizada**: Transición fluida entre modelos según necesidades
- **Escalabilidad**: Soporte para redes complejas (50+ nodos)
- **Consistencia KRONOS**: Integración perfecta con la aplicación existente

### ALCANCE DEL PROYECTO
- Refactorización completa del componente `PhoneCorrelationDiagram`
- Sistema de alternancia de layouts visuales
- Controles avanzados de visualización
- Mejoras en accesibilidad e internacionalización
- Testing integral de usabilidad

---

## 2. ANÁLISIS UX DE MODELOS EXISTENTES {#análisis-ux}

### MODELO 1: CIRCULAR CON AVATARES
#### ✅ FORTALEZAS
| Aspecto | Descripción | Impacto UX |
|---------|-------------|------------|
| **Familiaridad** | Los avatares circulares son universalmente reconocibles | **Alto** - Aprendizaje inmediato |
| **Humanización** | Representa personas reales detrás de los números | **Medio** - Conexión emocional con datos |
| **Force-Directed** | Agrupación natural por correlación | **Alto** - Insights visuales automáticos |
| **Colores Semánticos** | Bordes distintivos por nivel de correlación | **Alto** - Identificación rápida de relevancia |

#### ❌ DEBILIDADES
| Aspecto | Descripción | Impacto UX |
|---------|-------------|------------|
| **Complejidad Visual** | Muchos elementos gráficos simultáneos | **Alto** - Fatiga visual en análisis largos |
| **Precisión Limitada** | Flechas curvas menos precisas | **Medio** - Ambigüedad en direccionalidad |
| **Densidad Problemática** | Superposición con muchos nodos | **Alto** - Pérdida de legibilidad |
| **Mantenimiento** | Avatares requieren gestión de recursos | **Bajo** - Complejidad técnica |

### MODELO 2: RECTANGULAR RECTILÍNEO
#### ✅ FORTALEZAS
| Aspecto | Descripción | Impacto UX |
|---------|-------------|------------|
| **Claridad Máxima** | Líneas rectas y cajas estructuradas | **Alto** - Análisis preciso de conexiones |
| **Escalabilidad** | Mejor rendimiento con muchos nodos | **Alto** - Mantiene usabilidad en casos complejos |
| **Profesionalismo** | Estética apropiada para contexto forense | **Alto** - Credibilidad en presentaciones |
| **Precisión Geométrica** | Flechas rectilíneas inequívocas | **Alto** - Claridad direccional absoluta |

#### ❌ DEBILIDADES
| Aspecto | Descripción | Impacto UX |
|---------|-------------|------------|
| **Frialdad Visual** | Puede parecer demasiado técnico | **Medio** - Barrera de entrada para usuarios nuevos |
| **Monotonía** | Falta de variedad visual | **Medio** - Posible aburrimiento en sesiones largas |
| **Rigidez** | Menos flexibilidad de layout | **Medio** - Limitaciones en casos específicos |

---

## 3. ESTRATEGIA DE COMBINACIÓN HÍBRIDA {#estrategia-combinación}

### FILOSOFÍA DE DISEÑO
**"Progressive Enhancement Visual"**: Comenzar con claridad profesional (Modelo 2) y agregar elementos familiares (Modelo 1) según contexto y preferencias del usuario.

### SISTEMA DE ALTERNANCIA INTELIGENTE

#### 3.1 MODOS DE VISUALIZACIÓN (CONFIRMADOS POR BORIS)
```typescript
type VisualizationMode = 
  | 'radial-central'  // MODO 1: Predeterminado - Target central con disposición radial
  | 'circular-avatars' // MODO 2: Circular con avatares y force-directed
  | 'linear-flow'      // MODO 3: Flujo lineal/secuencial vertical
  | 'hybrid-smart'     // MODO 4: Selección automática inteligente
```

#### 3.2 ESPECIFICACIONES DETALLADAS DE LOS 4 MODOS

##### MODO 1: RADIAL CENTRAL (Predeterminado)
- **Disposición**: Nodo "Target" en el centro, "Sources" en disposición radial
- **Nodos**: Rectangulares redondeados estilo profesional
- **Conexiones**: Curvas Bezier elegantes convergiendo al centro
- **IDs Celda**: Visibles en las conexiones con anti-colisión
- **Colores**: Distintivos según nivel de correlación
- **Uso**: Modo por defecto para máxima claridad del objetivo

##### MODO 2: CIRCULAR CON AVATARES
- **Disposición**: Layout force-directed distribuido
- **Nodos**: Circulares con iconos avatarMale.svg
- **Etiquetas**: Números telefónicos como etiquetas debajo
- **Colores**: Bordes por correlación (rojo, naranja, verde)
- **Conexiones**: Flechas direccionales con IDs de celda
- **Uso**: Humanización de datos, familiaridad visual

##### MODO 3: FLUJO LINEAL
- **Disposición**: Vertical/secuencial de nodos
- **Conexiones**: Rectilíneas directas
- **Estados**: Visuales claros (activo, procesado)
- **Bifurcaciones**: Para múltiples destinos
- **Uso**: Cronología de llamadas, flujos secuenciales

##### MODO 4: HÍBRIDO INTELIGENTE
- **Selección automática** según:
  - Número de nodos (pocos=radial, muchos=circular)
  - Densidad de conexiones
  - Tipo de análisis requerido
- **Combinación** de elementos de otros modos
- **Adaptación** dinámica al contexto

#### 3.3 REGLAS DE ALTERNANCIA AUTOMÁTICA (MODO 4)
| Condición | Modo Activado | Justificación |
|-----------|---------------|---------------|
| ≤ 8 nodos | `radial-central` | Claridad máxima con pocos elementos |
| 9-20 nodos | `circular-avatars` | Balance familiaridad/funcionalidad |
| ≥ 21 nodos | `linear-flow` | Mejor organización para muchos elementos |
| Presentación activada | `radial-central` | Máximo profesionalismo |
| Primera vez usuario | `circular-avatars` | Reducir barrera de entrada |

#### 3.3 ELEMENTOS HÍBRIDOS CORE

##### A. NODOS ADAPTATIVOS
```typescript
interface AdaptiveNodeConfig {
  // Geometría base
  shape: 'circle' | 'rounded-rect' | 'hexagon';  
  
  // Avatar
  showAvatar: boolean;
  avatarType: 'male' | 'female' | 'generic' | 'initial';
  
  // Labeling  
  labelPosition: 'below' | 'inside' | 'floating';
  
  // Indicadores de estado
  correlationIndicator: 'border' | 'background' | 'icon' | 'combined';
}
```

##### B. CONEXIONES ADAPTATIVAS
```typescript
interface AdaptiveEdgeConfig {
  // Geometría de línea
  pathType: 'curved' | 'straight' | 'stepped' | 'smart';
  
  // Flechas
  arrowStyle: 'triangular' | 'rectangular' | 'diamond' | 'adaptive';
  
  // Etiquetas de celda
  labelStrategy: 'always' | 'smart' | 'hover-only' | 'minimal';
  
  // Animaciones
  animateFlow: boolean;
}
```

---

## 4. ARQUITECTURA DE COMPONENTES {#arquitectura-componentes}

### ESTRUCTURA MODULAR PROPUESTA

```
📁 components/diagrams/HybridCorrelationDiagram/
├── 📄 HybridCorrelationDiagram.tsx          # Componente principal
├── 📁 core/
│   ├── 📄 DiagramEngine.tsx                 # Motor de renderizado
│   ├── 📄 ModeManager.tsx                   # Gestión de modos visuales
│   └── 📄 DataTransformer.tsx               # Adaptación de datos
├── 📁 nodes/
│   ├── 📄 AdaptivePhoneNode.tsx             # Nodo híbrido base
│   ├── 📄 CircularAvatarNode.tsx            # Nodo circular (Modelo 1)
│   ├── 📄 RectangularProfessionalNode.tsx   # Nodo rectangular (Modelo 2)
│   └── 📄 NodeFactory.tsx                   # Factory pattern para nodos
├── 📁 edges/
│   ├── 📄 AdaptivePhoneEdge.tsx             # Edge híbrido base  
│   ├── 📄 CurvedAvatarEdge.tsx              # Edge curvo (Modelo 1)
│   ├── 📄 StraightProfessionalEdge.tsx      # Edge rectilíneo (Modelo 2)
│   └── 📄 EdgeFactory.tsx                   # Factory pattern para edges
├── 📁 controls/
│   ├── 📄 ModeToggle.tsx                    # Selector de modo visual
│   ├── 📄 AdvancedFilters.tsx               # Filtros extendidos
│   ├── 📄 ExportControls.tsx                # Controles de exportación
│   └── 📄 AccessibilityControls.tsx         # Controles a11y
├── 📁 panels/
│   ├── 📄 InfoPanel.tsx                     # Panel de información
│   ├── 📄 LegendPanel.tsx                   # Leyenda visual
│   ├── 📄 StatisticsPanel.tsx               # Estadísticas en tiempo real
│   └── 📄 SettingsPanel.tsx                 # Configuración avanzada
├── 📁 hooks/
│   ├── 📄 useHybridDiagram.ts               # Hook principal
│   ├── 📄 useModeTransition.ts              # Transiciones suaves
│   ├── 📄 usePerformanceOptimization.ts     # Optimización rendimiento
│   └── 📄 useAccessibilityFeatures.ts       # Características a11y
├── 📁 utils/
│   ├── 📄 layoutAlgorithms.ts               # Algoritmos de layout
│   ├── 📄 collisionDetection.ts             # Detección de colisiones
│   ├── 📄 colorSystemHybrid.ts              # Sistema de colores híbrido
│   └── 📄 exportUtilities.ts                # Utilidades de exportación
└── 📁 types/
    ├── 📄 hybrid.types.ts                   # Tipos híbridos
    ├── 📄 visualization.types.ts            # Tipos de visualización
    └── 📄 interaction.types.ts              # Tipos de interacción
```

### IMPLEMENTACIÓN DE FACTORY PATTERNS

#### NodeFactory Implementation
```typescript
class NodeFactory {
  static createNode(
    data: PhoneNodeData, 
    mode: VisualizationMode,
    config: AdaptiveNodeConfig
  ): Node {
    switch(mode) {
      case 'professional':
        return new RectangularProfessionalNode(data, config);
      case 'familiar':
        return new CircularAvatarNode(data, config);
      case 'hybrid-smart':
        return this.createSmartHybridNode(data, config);
      case 'hybrid-custom':
        return new AdaptivePhoneNode(data, config);
      default:
        return new AdaptivePhoneNode(data, config);
    }
  }
  
  private static createSmartHybridNode(
    data: PhoneNodeData, 
    config: AdaptiveNodeConfig
  ): Node {
    // Lógica inteligente basada en contexto
    const nodeCount = data.totalNodes;
    const isTarget = data.isTarget;
    
    if (nodeCount <= 8 && !isTarget) {
      return new CircularAvatarNode(data, config);
    } else if (isTarget || nodeCount > 20) {
      return new RectangularProfessionalNode(data, config);
    } else {
      return new AdaptivePhoneNode(data, config);
    }
  }
}
```

---

## 5. WIREFRAMES Y LAYOUTS DETALLADOS {#wireframes}

### 5.1 LAYOUT PRINCIPAL - MODAL HÍBRIDO (95vw x 90vh)

```
┌─────────────────────────────────────────────────────────────┐
│ 📊 Diagrama de Correlación Telefónica - Modo: Híbrido    ✕ │
│ 🎯 Objetivo: 3143534707 | 12 nodos | 18 conexiones         │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────┐                                   ┌───────┐ │
│ │ 🎛️ CONTROLES │                                   │ 📊 INFO │ │
│ │             │                                   │       │ │
│ │ [Modo]      │          ÁREA DE DIAGRAMA         │ Nodos │ │
│ │ ◉ Híbrido   │                                   │ 12    │ │
│ │ ○ Prof.     │     [Visualización React Flow]    │       │ │
│ │ ○ Familiar  │                                   │ Edges │ │
│ │             │                                   │ 18    │ │
│ │ [Filtros]   │                                   │       │ │
│ │ Min Corr: 3 │                                   │ ⚫⚫⚫  │ │
│ │ ────────○── │                                   │ ⚫⚫⚪  │ │
│ │             │                                   │ ⚪⚪⚪  │ │
│ │ ☑ IDs Celda │                                   │       │ │
│ │ ☑ Aislados  │                                   └───────┘ │
│ │             │                                             │
│ │ [Export]    │                 ┌─────────────────────────┐ │
│ │ 📷 PNG      │                 │ 🎨 LEYENDA              │ │
│ │ 🎨 SVG      │                 │ ⚫ Objetivo  ⚫ Entrante │ │
│ │ 📋 JSON     │                 │ ⚫ Saliente  ⚪ Normal   │ │
│ └─────────────┘                 └─────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ 🎯 React Flow v12 | Modo: Híbrido Smart | ESC: Cerrar      │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 MODO 1: RADIAL CENTRAL (PREDETERMINADO)

```
Distribución Radial Central:

                    📞 3112345678
                   ┌──────────────┐
              ╭─56124─╮ │ 🟢 ENTRANTE  │
             ╱         ╲│ Media Corr   │
            ╱           ╲──────────────┘
           ╱             ╲
          ╱               ╲
┌──────────────┐           ╲    ┌──────────────┐
│ 📞 3009876543│            ╲   │ 📞 3201234567│
│ SALIENTE     │◄────2523────╲──│ BIDIRECCIONAL│
│ 🔵 Baja Corr │              ╲ │ 🟡 Alta Corr │
└──────────────┘               ╲└──────────────┘
                                ╲
                    ┌──────────────┐
                    │ 📱 3143534707│ ◄─ CENTRO
                    │ OBJETIVO     │
                    │ 🔴 Target    │
                    └──────────────┘
                                ╱
               ╭─17483─╮       ╱
              ╱         ╲     ╱
             ╱           ╲   ╱
   📞 3XX4567890          ╲ ╱
  ┌──────────────┐        ╲╱
  │ SECUNDARIO   │        ╱╲
  │ 🟠 Med Corr  │       ╱  ╲
  └──────────────┘      ╱    ╲

Características MODO 1:
- Target: SIEMPRE en el centro, destacado en rojo
- Sources: Distribución radial equilibrada alrededor
- Conexiones: Curvas Bezier elegantes convergiendo al centro
- Nodos: Rectangulares redondeados profesionales
- IDs Celda: Sobre las conexiones con anti-colisión
- Layout: Radial automático con espaciado inteligente
```

### 5.3 MODO 2: CIRCULAR CON AVATARES

```
Distribución Force-Directed con Avatares:

     👤 3143534707           👤 3112345678
    ●─────────────●    ╭─56124─╮    ●─────────────●
    │  🔴 OBJETIVO │◄──╴       ╶──►│ 🟢 ENTRANTE │
    │  avatarMale  │              │  avatarMale │
    └─────────────┘              └─────────────┘
           ╲                            ╱
      ╭─2523─╮ ╲                      ╱ ╭─63895─╮
             ╲  ╲                    ╱  ╱
              ╲  ╲    👤 3009876543 ╱  ╱
               ╲  ╲  ●─────────────● ╱
                ╲  ╲ │ 🔵 SALIENTE │╱
                 ╲  ╲│  avatarMale │
                  ╲  ╲─────────────┘
                   ╲  ╲      ╱
                    ╲  ╲    ╱ ╭─17483─╮
                     ╲  ╲  ╱
                      ╲  ╲╱    👤 3201234567
                       ╲ ●─────────────●
                        ╲│🟡 BIDIRECC. │
                         │  avatarMale │
                         └─────────────┘

Características MODO 2:
- Nodos: Círculos con iconos avatarMale.svg
- Etiquetas: Números telefónicos debajo del avatar
- Colores: Bordes distintivos por correlación
- Flechas: Direccionales con IDs de celda
- Layout: Force-directed natural con agrupación
- Humanización: Representación visual de personas
```

### 5.4 MODO 3: FLUJO LINEAL

```
Distribución Lineal/Secuencial:

┌──────────────┐  
│ 📱 3143534707│  ◄─ INICIO (Target)
│ OBJETIVO     │  
│ 🔴 Target    │  
└──────┬───────┘  
       │ 56124 (Saliente)
       ▼
┌──────────────┐  
│ 📞 3112345678│  
│ PRIMERA CONN │  
│ 🟢 Procesado │  
└──────┬───────┘  
       │ 63895 (Bidireccional)
       ▼
┌──────────────┐     ┌──────────────┐
│ 📞 3009876543│────►│ 📞 3201234567│
│ BIFURCACIÓN  │2523 │ TERMINAL     │
│ 🔵 Activo    │     │ 🟡 Completo  │
└──────────────┘     └──────────────┘
       │ 17483
       ▼
┌──────────────┐  
│ 📞 3XX4567890│  
│ FINAL        │  
│ 🟠 Pendiente │  
└──────────────┘  

Características MODO 3:
- Layout: Vertical/secuencial organizado
- Conexiones: Rectilíneas directas y claras
- Estados: Visuales (activo, procesado, pendiente, completo)
- Bifurcaciones: Para múltiples destinos desde un nodo
- Cronología: Ideal para mostrar secuencia temporal
- Simplicidad: Fácil seguimiento de flujo de comunicaciones
```

### 5.5 MODO 4: HÍBRIDO INTELIGENTE

```
Selección Automática Según Contexto:

ESCENARIO A: Pocos nodos (≤8) → RADIAL CENTRAL
                    📞 3112345678
               ╭─56124─╮ │ ENTRANTE │
              ╱         ╲──────────┘
   ┌─TARGET─┐╱           ╲┌─OTRO─┐
   │3143... ││   CENTRO   ││3201..│
   └────────┘╲           ╱└──────┘
              ╲         ╱
               ╲╭─2523─╮╱
                📞 3009876543

ESCENARIO B: Muchos nodos (≥21) → CIRCULAR AVATARES
    👤       👤       👤
  ●─────● ●─────● ●─────●
   ╲   ╱   ╲   ╱   ╲   ╱
    ╲ ╱     ╲ ╱     ╲ ╱
     👤       👤       👤
   TARGET   ●─────● ●─────●
           DISTRIBUCIÓN NATURAL

ESCENARIO C: Secuencia temporal → FLUJO LINEAL
┌─START─┐ → ┌─MID1─┐ → ┌─MID2─┐ → ┌─END─┐
│Target │   │ Paso1│   │ Paso2│   │Final│
└───────┘   └──────┘   └──────┘   └─────┘

Reglas de Selección Inteligente:
- Analiza número de nodos y densidad de conexiones
- Detecta patrones temporales vs correlacionales
- Considera tipo de investigación (correlación vs cronología)
- Adapta automáticamente pero permite override manual
```

---

## 6. SISTEMA DE COLORES Y SEMÁNTICA VISUAL {#sistema-colores}

### 6.1 PALETA DE COLORES HÍBRIDA

#### COLORES PRIMARIOS (Modelo 1 Compatible)
```typescript
const CORRELATION_COLORS = {
  // Niveles de Correlación
  TARGET: '#dc2626',        // Rojo intenso - Objetivo principal
  HIGH: '#ea580c',          // Naranja - Alta correlación  
  MEDIUM_HIGH: '#d946ef',   // Rosa/Magenta - Media-alta correlación
  MEDIUM: '#16a34a',        // Verde - Media correlación
  LOW: '#7c3aed',           // Morado - Baja correlación
  INDIRECT: '#6b7280',      // Gris - Relaciones indirectas
  
  // Estados de Comunicación
  INCOMING: '#10b981',      // Verde esmeralda - Llamadas entrantes
  OUTGOING: '#3b82f6',      // Azul - Llamadas salientes  
  BIDIRECTIONAL: '#f59e0b', // Ámbar - Comunicación bidireccional
  
  // Estados de Interfaz
  SELECTED: '#06b6d4',      // Cyan - Elemento seleccionado
  HOVER: '#8b5cf6',         // Púrpura - Hover state
  DISABLED: '#374151',      // Gris oscuro - Deshabilitado
};
```

#### COLORES PROFESIONALES (Modelo 2 Compatible)
```typescript
const PROFESSIONAL_COLORS = {
  // Versión sobria para presentaciones
  TARGET: '#991b1b',        // Rojo profundo
  HIGH: '#c2410c',          // Naranja profundo
  MEDIUM_HIGH: '#a21caf',   // Rosa profundo
  MEDIUM: '#15803d',        // Verde profundo
  LOW: '#6d28d9',           // Morado profundo
  INDIRECT: '#4b5563',      // Gris medio
  
  // Backgrounds y bordes
  NODE_BG: '#1f2937',       // Fondo de nodos
  NODE_BORDER: '#374151',   // Bordes de nodos
  EDGE_DEFAULT: '#6b7280',  // Color de edges por defecto
  EDGE_HIGHLIGHT: '#ffffff',// Color de edges resaltados
};
```

### 6.2 SISTEMA DE ICONOGRAFÍA

#### AVATARES GENÉRICOS
```typescript
const AVATAR_SYSTEM = {
  male: 'avatarMale.svg',           // Avatar masculino genérico
  female: 'avatarFemale.svg',       // Avatar femenino genérico  
  generic: 'avatarGeneric.svg',     // Avatar neutro
  initial: 'avatarInitial.svg',     // Avatar con iniciales
  operator: 'avatarOperator.svg',   // Avatar específico por operador
  
  // Fallback system
  fallback: {
    shape: 'circle',
    background: CORRELATION_COLORS.INDIRECT,
    text: '📱',
    fontSize: '24px'
  }
};
```

#### ICONOS DE ESTADO
```typescript
const STATUS_ICONS = {
  target: '🎯',           // Número objetivo
  incoming: '📞',         // Llamada entrante
  outgoing: '📱',         // Llamada saliente
  bidirectional: '🔄',    // Comunicación bidireccional
  high_activity: '🔥',    // Alta actividad
  low_activity: '❄️',     // Baja actividad
  operator_claro: '🟡',   // Operador Claro
  operator_movistar: '🔴', // Operador Movistar
  operator_tigo: '🔵',    // Operador Tigo
  operator_wom: '🟣',     // Operador WOM
};
```

### 6.3 TIPOGRAFÍA Y TAMAÑOS

```typescript
const TYPOGRAPHY_SYSTEM = {
  // Tamaños de fuente adaptativos
  node_label: {
    small: '11px',      // <10 nodos
    medium: '10px',     // 10-20 nodos  
    large: '9px',       // >20 nodos
    xlarge: '8px'       // >50 nodos
  },
  
  edge_label: {
    small: '10px',      // Menos de 10 edges
    medium: '9px',      // 10-30 edges
    large: '8px',       // >30 edges
  },
  
  // Pesos de fuente
  weights: {
    target: '700',      // Bold para objetivos
    normal: '500',      // Medium para nodos normales
    secondary: '400',   // Regular para información adicional
  },
  
  // Familias de fuente
  families: {
    primary: '"Inter", sans-serif',
    monospace: '"JetBrains Mono", monospace', // Para IDs técnicos
    display: '"Inter", sans-serif'
  }
};
```

---

## 7. ESPECIFICACIONES DE INTERACCIÓN {#especificaciones-interacción}

### 7.1 INTERACCIONES DE NODOS

#### Estados de Interacción
```typescript
interface NodeInteractionStates {
  default: {
    opacity: 1.0,
    scale: 1.0,
    borderWidth: 2,
    elevation: 0
  },
  
  hover: {
    opacity: 1.0,
    scale: 1.05,
    borderWidth: 3,
    elevation: 4,
    transition: 'all 150ms cubic-bezier(0.4, 0, 0.2, 1)'
  },
  
  selected: {
    opacity: 1.0,
    scale: 1.1,
    borderWidth: 4,
    elevation: 8,
    glow: `0 0 20px ${CORRELATION_COLORS.SELECTED}`,
    transition: 'all 200ms cubic-bezier(0.4, 0, 0.2, 1)'
  },
  
  connected_highlight: {
    opacity: 1.0,
    scale: 1.02,
    borderWidth: 3,
    elevation: 2,
    borderColor: CORRELATION_COLORS.SELECTED
  },
  
  dimmed: {
    opacity: 0.3,
    scale: 0.95,
    borderWidth: 1,
    elevation: 0
  }
}
```

#### Acciones en Nodos
| Acción | Trigger | Respuesta Visual | Funcionalidad |
|--------|---------|------------------|---------------|
| **Hover** | Mouse enter | Escala 1.05x, bordes resaltados | Mostrar tooltip con info básica |
| **Click** | Mouse click | Selección persistente | Abrir panel de detalles del número |
| **Double Click** | Double click | Zoom y centrado | Enfocar nodo y conexiones directas |
| **Right Click** | Context menu | Menú contextual | Opciones: copiar, analizar, exportar |
| **Drag Start** | Mouse down + move | Semi-transparencia | Iniciar reorganización manual |
| **Drag End** | Mouse up | Restaurar opacidad | Fijar nueva posición |

### 7.2 INTERACCIONES DE EDGES

#### Estados de Conexiones
```typescript
interface EdgeInteractionStates {
  default: {
    strokeWidth: 2,
    opacity: 0.8,
    markerSize: 8
  },
  
  hover: {
    strokeWidth: 4,
    opacity: 1.0,
    markerSize: 12,
    dropShadow: '0 2px 8px rgba(0,0,0,0.4)'
  },
  
  selected: {
    strokeWidth: 5,
    opacity: 1.0,
    markerSize: 14,
    animated: true,
    dropShadow: '0 4px 12px rgba(0,0,0,0.6)'
  },
  
  related_highlight: {
    strokeWidth: 3,
    opacity: 0.9,
    markerSize: 10
  },
  
  dimmed: {
    strokeWidth: 1,
    opacity: 0.2,
    markerSize: 6
  }
}
```

#### Acciones en Conexiones
| Acción | Trigger | Respuesta Visual | Funcionalidad |
|--------|---------|------------------|---------------|
| **Hover** | Mouse enter edge | Grosor aumentado, sombra | Tooltip con detalles de comunicación |
| **Click** | Mouse click | Resaltado persistente | Panel lateral con historial de llamadas |
| **Hover Label** | Mouse enter ID celda | Label expandido | Info detallada de la celda |
| **Click Label** | Click en ID celda | Destacar todas las conexiones de esa celda | Análisis de celda específica |

### 7.3 CONTROLES AVANZADOS

#### Barra de Controles de Modo (SEPARADA)
```typescript
interface ModeToggleControl {
  component: 'ModeToggle',
  position: 'top-center', // Barra separada para cambio de modo
  layout: 'horizontal-tabs',
  options: [
    {
      value: 'radial-central',
      label: '🎯 Radial Central',
      description: 'Target central con distribución radial (Predeterminado)',
      shortcut: '1',
      isDefault: true
    },
    {
      value: 'circular-avatars', 
      label: '👤 Circular Avatares',
      description: 'Nodos circulares con avatares y force-directed',
      shortcut: '2'
    },
    {
      value: 'linear-flow',
      label: '📈 Flujo Lineal',
      description: 'Disposición vertical/secuencial de nodos',
      shortcut: '3'
    },
    {
      value: 'hybrid-smart',
      label: '🧠 Híbrido Inteligente',
      description: 'Selección automática según contexto',
      shortcut: '4'
    }
  ],
  
  transitions: {
    type: 'instant', // Sin animaciones según especificación Boris
    stagger: 'none'
  },
  
  styling: {
    appearance: 'tab-bar',
    activeIndicator: 'underline',
    spacing: 'comfortable'
  }
}
```

#### Panel de Filtros Avanzados
```typescript
interface AdvancedFiltersPanel {
  component: 'AdvancedFilters',
  position: 'top-left',
  collapsed: false,
  
  filters: {
    correlationRange: {
      type: 'range-slider',
      min: 0,
      max: 100,
      default: [0, 100],
      step: 1,
      label: 'Rango de Correlación (%)'
    },
    
    timeRange: {
      type: 'date-range',
      label: 'Rango de Fechas',
      format: 'YYYY-MM-DD',
      default: 'all'
    },
    
    operatorFilter: {
      type: 'multi-select',
      options: ['Claro', 'Movistar', 'Tigo', 'WOM', 'Otros'],
      default: [],
      label: 'Operadores'
    },
    
    connectionTypes: {
      type: 'checkbox-group',
      options: [
        { value: 'incoming', label: '📞 Entrantes', checked: true },
        { value: 'outgoing', label: '📱 Salientes', checked: true },
        { value: 'bidirectional', label: '🔄 Bidireccionales', checked: true }
      ]
    },
    
    nodeDisplay: {
      type: 'checkbox-group', 
      options: [
        { value: 'showIsolated', label: 'Mostrar nodos aislados', checked: true },
        { value: 'showCellIds', label: 'Mostrar IDs de celda', checked: true },
        { value: 'showOperatorIcons', label: 'Iconos de operador', checked: false }
      ]
    }
  }
}
```

### 7.4 GESTOS MULTI-TOUCH Y TECLADO

#### Soporte Multi-Touch (Tablets/Touchscreens)
```typescript
interface TouchGestures {
  pinchToZoom: {
    enabled: true,
    sensitivity: 1.2,
    minZoom: 0.1,
    maxZoom: 3.0
  },
  
  panToMove: {
    enabled: true,
    momentum: true,
    resistance: 0.8
  },
  
  tapToSelect: {
    enabled: true,
    doubleTapToFit: true,
    longPressContextMenu: true,
    longPressDuration: 500
  },
  
  rotateToOrganize: {
    enabled: false, // Disabled por defecto en contexto profesional
    twoFingerRotation: false
  }
}
```

#### Atajos de Teclado
```typescript
interface KeyboardShortcuts {
  // Navegación
  'Space': 'Fit view to content',
  'F': 'Toggle fullscreen',
  'Escape': 'Close modal',
  
  // Modos de visualización (4 confirmados)
  '1': 'Switch to Radial Central mode (predeterminado)',
  '2': 'Switch to Circular Avatares mode',
  '3': 'Switch to Linear Flow mode', 
  '4': 'Switch to Hybrid Smart mode',
  'R': 'Quick toggle to Radial Central',
  'C': 'Quick toggle to Circular Avatares',
  
  // Filtros
  '1-5': 'Quick correlation filter (1=0-20%, 2=20-40%, etc)',
  'I': 'Toggle isolated nodes',
  'L': 'Toggle cell ID labels',
  'O': 'Toggle operator icons',
  
  // Exportación
  'Ctrl+E': 'Export as PNG',
  'Ctrl+Shift+E': 'Export as SVG',
  'Ctrl+J': 'Export as JSON',
  
  // Selección
  'Ctrl+A': 'Select all nodes',
  'Ctrl+D': 'Deselect all',
  'Delete': 'Hide selected nodes temporarily',
  
  // Layout
  'R': 'Randomize layout',
  'G': 'Grid layout',
  'F': 'Force-directed layout',
  'T': 'Tree layout'
}
```

---

## 8. RESPONSIVE DESIGN Y ACCESIBILIDAD {#responsive-accesibilidad}

### 8.1 BREAKPOINTS RESPONSIVOS

#### Configuración de Tamaños de Pantalla
```typescript
const RESPONSIVE_BREAKPOINTS = {
  // Desktop Large (>1400px)
  xl: {
    modalSize: { width: '95vw', height: '90vh' },
    panelLayout: 'sidebar',
    nodeSize: { min: 40, default: 60, max: 100 },
    fontSize: { node: '12px', edge: '10px' },
    controlsPosition: 'floating'
  },
  
  // Desktop (1024px - 1400px)  
  lg: {
    modalSize: { width: '90vw', height: '85vh' },
    panelLayout: 'sidebar',
    nodeSize: { min: 35, default: 50, max: 80 },
    fontSize: { node: '11px', edge: '9px' },
    controlsPosition: 'floating'
  },
  
  // Tablet (768px - 1024px)
  md: {
    modalSize: { width: '95vw', height: '80vh' },
    panelLayout: 'overlay',
    nodeSize: { min: 30, default: 45, max: 70 },
    fontSize: { node: '10px', edge: '8px' },
    controlsPosition: 'bottom-sheet'
  },
  
  // Mobile Large (480px - 768px)
  sm: {
    modalSize: { width: '100vw', height: '100vh' },
    panelLayout: 'bottom-sheet',
    nodeSize: { min: 25, default: 40, max: 60 },
    fontSize: { node: '9px', edge: '7px' },
    controlsPosition: 'bottom-sheet'
  },
  
  // Mobile Small (<480px)
  xs: {
    modalSize: { width: '100vw', height: '100vh' },
    panelLayout: 'bottom-sheet',
    nodeSize: { min: 20, default: 35, max: 50 },
    fontSize: { node: '8px', edge: '6px' },
    controlsPosition: 'bottom-sheet',
    simplifiedMode: true
  }
};
```

#### Adaptaciones de Layout Móvil
```typescript
interface MobileOptimizations {
  // Gestos táctiles optimizados
  touchTargets: {
    minSize: '44px',           // Tamaño mínimo recomendado iOS/Android
    spacing: '8px',            // Espaciado entre elementos tocables
    feedbackDuration: '100ms'  // Duración de feedback táctil
  },
  
  // Simplificación de interfaz
  simplifications: {
    hideSecondaryControls: true,
    combinePanels: true,
    prioritizeMainActions: true,
    reducedAnimations: true
  },
  
  // Optimización de rendimiento
  performance: {
    maxVisibleNodes: 25,       // Límite en móviles
    simplifiedEdges: true,     // Edges más simples
    reducedShadows: true,      // Menos efectos visuales
    lazyRendering: true        // Renderizado bajo demanda
  }
}
```

### 8.2 ACCESIBILIDAD (WCAG 2.1 AA)

#### Navegación por Teclado
```typescript
interface KeyboardNavigation {
  focusManagement: {
    // Orden de tabulación lógico
    tabIndex: {
      modeToggle: 1,
      filterControls: 2,
      diagramArea: 3,
      exportControls: 4,
      closeButton: 5
    },
    
    // Indicadores visuales de foco
    focusIndicator: {
      outline: '3px solid #06b6d4',
      outlineOffset: '2px',
      borderRadius: '4px',
      boxShadow: '0 0 0 1px rgba(255,255,255,0.5)'
    },
    
    // Navegación dentro del diagrama
    diagramNavigation: {
      arrowKeys: 'move-between-nodes',
      enterKey: 'select-node',
      spaceKey: 'activate-node',
      escapeKey: 'deselect-all'
    }
  },
  
  // Atajos específicos de accesibilidad
  a11yShortcuts: {
    'Alt+1': 'Jump to mode controls',
    'Alt+2': 'Jump to filters',
    'Alt+3': 'Jump to diagram',
    'Alt+4': 'Jump to export',
    'Alt+H': 'Show help overlay',
    'Alt+S': 'Read diagram summary'
  }
}
```

#### Lectores de Pantalla
```typescript
interface ScreenReaderSupport {
  // Etiquetas ARIA completas
  ariaLabels: {
    diagram: 'Diagrama de correlación telefónica interactivo',
    node: (nodeData) => 
      `Número ${nodeData.phone}, correlación ${nodeData.correlation}%, 
       ${nodeData.connectionCount} conexiones`,
    edge: (edgeData) => 
      `Conexión desde ${edgeData.source} hacia ${edgeData.target}, 
       celda ${edgeData.cellId}`,
    controls: 'Controles de visualización del diagrama'
  },
  
  // Descripciones estructuradas
  descriptions: {
    diagramSummary: (stats) => 
      `Diagrama con ${stats.nodeCount} números telefónicos y 
       ${stats.edgeCount} conexiones. Número objetivo: ${stats.target}`,
    modeChange: (newMode) => 
      `Modo de visualización cambiado a ${newMode}`,
    filterUpdate: (filterName, value) => 
      `Filtro ${filterName} actualizado a ${value}`
  },
  
  // Navegación por elementos
  landmarks: {
    main: 'main',
    controls: 'region',
    diagram: 'application',
    info: 'complementary'
  },
  
  // Actualizaciones en vivo
  liveRegions: {
    status: 'polite',    // Para cambios de estado
    alerts: 'assertive', // Para errores críticos
    updates: 'polite'    // Para actualizaciones de datos
  }
}
```

#### Contraste de Colores y Visibilidad
```typescript
interface VisualAccessibility {
  // Ratios de contraste WCAG AA
  contrastRatios: {
    normalText: {
      minimum: 4.5,        // AA standard
      enhanced: 7.0        // AAA standard
    },
    largeText: {
      minimum: 3.0,        // AA standard  
      enhanced: 4.5        // AAA standard
    }
  },
  
  // Modo alto contraste
  highContrastMode: {
    enabled: false,
    toggle: 'Alt+Shift+H',
    colorScheme: {
      background: '#000000',
      foreground: '#ffffff', 
      accent: '#ffff00',
      error: '#ff0000',
      success: '#00ff00'
    }
  },
  
  // Alternativas visuales para daltonismo
  colorBlindSupport: {
    patterns: true,         // Usar patrones además de colores
    shapes: true,           // Formas distintivas por tipo
    labels: true,           // Etiquetas textuales siempre
    alternatives: {
      red: { pattern: 'diagonal-lines', shape: 'square' },
      green: { pattern: 'dots', shape: 'circle' },
      blue: { pattern: 'horizontal-lines', shape: 'triangle' }
    }
  },
  
  // Reducción de movimiento
  reducedMotion: {
    respectPreference: true, // Respetar prefers-reduced-motion
    fallbacks: {
      animations: 'instant',
      transitions: 'instant',
      autoPlay: false
    }
  }
}
```

#### Soporte Multi-idioma
```typescript
interface InternationalizationSupport {
  // Idiomas soportados
  supportedLocales: ['es-ES', 'en-US', 'pt-BR'],
  defaultLocale: 'es-ES',
  
  // Strings localizables
  i18nKeys: {
    // Títulos y etiquetas principales
    'diagram.title': 'Diagrama de Correlación Telefónica',
    'diagram.target': 'Objetivo',
    'diagram.nodes': 'Nodos',
    'diagram.connections': 'Conexiones',
    
    // Controles
    'controls.mode': 'Modo de Visualización',
    'controls.filters': 'Filtros',
    'controls.export': 'Exportar',
    
    // Estados y acciones
    'state.loading': 'Cargando diagrama...',
    'state.error': 'Error al cargar datos',
    'action.close': 'Cerrar',
    'action.reset': 'Restablecer',
    
    // Ayuda y descripciones
    'help.navigation': 'Usa las flechas para navegar entre nodos',
    'help.zoom': 'Ctrl + rueda del mouse para hacer zoom'
  },
  
  // Formatos específicos por región
  formatting: {
    numbers: {
      'es-ES': { thousands: '.', decimal: ',' },
      'en-US': { thousands: ',', decimal: '.' },
      'pt-BR': { thousands: '.', decimal: ',' }
    },
    dates: {
      'es-ES': 'DD/MM/YYYY',
      'en-US': 'MM/DD/YYYY', 
      'pt-BR': 'DD/MM/YYYY'
    }
  }
}
```

---

## 9. FLUJO DE USUARIO COMPLETO {#flujo-usuario}

### 9.1 USER JOURNEY - INVESTIGADOR PRINCIPAL

#### Fase 1: Acceso y Contexto (0-30 segundos)
```
🎯 OBJETIVO: Visualizar correlaciones de un número objetivo específico

[Login] → [Dashboard] → [Misiones] → [Seleccionar Misión] → [Detalle de Misión]
   ↓
[Ejecutar Correlación] → [Tabla de Resultados] → [🔍 Ver Diagrama de Correlación]
   ↓
[Modal se abre en modo 'hybrid-smart' por defecto]

Estados mentales del usuario:
✅ "Necesito ver las conexiones visualmente"
✅ "La tabla tiene muchos datos, prefiero un mapa visual"  
⚠️ "Espero que sea intuitivo y no requiera aprendizaje"
```

#### Fase 2: Primera Impresión (30-60 segundos)
```
[Modal abierto - Modo Híbrido Inteligente]
   ↓
🎯 Usuario ve inmediatamente:
   - Nodo objetivo destacado (rojo, más grande)
   - 8-12 nodos conectados con avatares familiares
   - Líneas claras con IDs de celda visibles
   - Controles obvios en la izquierda

Reacciones esperadas:
✅ "Entiendo inmediatamente qué representa cada elemento"
✅ "Puedo identificar el número objetivo sin esfuerzo"
✅ "Los IDs de celda están donde los espero"
⚠️ "¿Puedo hacer zoom para ver mejor los detalles?"
```

#### Fase 3: Exploración Inicial (1-3 minutos)
```
Acciones típicas del usuario:

1. HOVER sobre nodos objetivo
   → Ve tooltip con información de correlación
   → Observa resaltado de conexiones relacionadas

2. CLICK en un nodo secundario  
   → Panel lateral se abre con detalles
   → Puede ver historial de llamadas con el objetivo

3. ZOOM IN usando controles
   → IDs de celda se mantienen legibles
   → Animación suave, sin pérdida de contexto

4. CAMBIAR a modo Profesional
   → Transición fluida a nodos rectangulares
   → Mayor claridad en casos complejos

Feedback mental:
✅ "Es intuitivo, puedo explorar sin instrucciones"
✅ "Los detalles aparecen cuando los necesito"
✅ "Puedo alternar modos según mi preferencia"
```

#### Fase 4: Análisis Profundo (3-10 minutos)
```
Tareas de investigación avanzada:

1. FILTRAR por correlación mínima
   [Slider: 0 → 5] 
   → Nodos con baja correlación se ocultan
   → Diagrama se simplifica, foco en casos relevantes

2. SELECCIONAR múltiples nodos
   [Ctrl + Click en varios nodos]
   → Puede comparar patrones de comunicación
   → Panel lateral muestra análisis comparativo

3. EXAMINAR celda específica
   [Click en ID "56124" en una conexión]
   → Todas las conexiones que usan esa celda se resaltan
   → Panel muestra ubicación geográfica de la celda

4. EXPORTAR hallazgos
   [Click en "📷 PNG"]
   → Descarga imagen para incluir en reporte
   → Calidad adecuada para presentaciones oficiales

Insights del usuario:
✅ "Puedo encontrar patrones que no eran obvios en la tabla"
✅ "El análisis por celdas añade una dimensión geográfica"
✅ "Puedo documentar mis hallazgos fácilmente"
```

#### Fase 5: Presentación y Reporte (10+ minutos)
```
Preparación de evidencia para presentación:

1. MODO PROFESIONAL para capturas finales
   → Layout más limpio y formal
   → Adecuado para documentos oficiales

2. CONFIGURAR filtros para mostrar solo lo relevante
   → Ocultar nodos aislados
   → Correlación mínima del 30%
   → Solo conexiones bidireccionales

3. CAPTURAR múltiples vistas
   → Vista general (PNG de alta resolución)
   → Vista detallada de cluster principal
   → Exportar datos (JSON) para análisis posteriores

4. DOCUMENTAR hallazgos
   → Copiar números de teléfono relevantes
   → Anotar IDs de celdas críticas
   → Identificar patrones temporales

Validación de objetivos:
✅ "Tengo evidencia visual clara y profesional"
✅ "Puedo explicar las conexiones a terceros"
✅ "La herramienta facilitó el descubrimiento de patrones"
✅ "Mi reporte será más convincente con estas visualizaciones"
```

### 9.2 USER JOURNEY - INVESTIGADOR JUNIOR

#### Flujo Simplificado para Usuarios Nuevos
```
PRIMER USO - Modo de Descubrimiento:

[Acceso al diagrama] → [Modal se abre en modo 'familiar']
   ↓
Sistema detecta que es primera vez del usuario
   ↓
[Tooltip de bienvenida]: 
"👋 ¡Bienvenido al Diagrama de Correlación!
 - Los círculos representan números telefónicos
 - Las líneas muestran comunicaciones entre ellos
 - Click en cualquier elemento para ver detalles"

Progresión natural:
Minuto 1: Exploración básica (hover, click)
Minuto 3: Descubre filtros simples
Minuto 5: Experimenta con zoom
Minuto 10: Intenta cambiar a modo profesional
Minuto 15: Confianza para análisis independiente

Métricas de adopción esperadas:
- 95% comprende funcionalidad básica en <2 minutos
- 80% usa filtros en primera sesión
- 60% experimenta con diferentes modos visuales
- 40% exporta su primera imagen
```

### 9.3 ESCENARIOS DE EDGE CASE

#### Escenario A: Red Muy Compleja (50+ nodos)
```
PROBLEMA: Diagrama saturado, pérdida de legibilidad

SOLUCIÓN AUTOMÁTICA:
1. Sistema detecta >30 nodos
2. Cambia automáticamente a modo 'professional'
3. Aplica filtro de correlación mínima al 40%
4. Agrupa nodos menos relevantes
5. Muestra notificación: "Red compleja detectada. Aplicando filtros automáticos para mejor visualización"

ACCIONES DISPONIBLES:
- Ajustar filtros manualmente
- Usar modo "cluster" para agrupar nodos similares
- Navegación por "pages" de nodos
- Búsqueda por número específico
```

#### Escenario B: Sin Datos de Correlación
```
PROBLEMA: No hay interacciones para mostrar

RESPUESTA ELEGANTE:
1. Mostrar estado vacío informativo
2. Sugerir acciones: "Ejecutar análisis de correlación primero"
3. Ofrecer datos de ejemplo para explorar funcionalidad
4. Link directo a la sección de carga de datos

DISEÑO DE ESTADO VACÍO:
┌─────────────────────────────────┐
│           📱 📞 📱              │
│                                 │
│   Sin datos de correlación      │
│                                 │
│ [🔄 Ejecutar Análisis]          │
│ [👁️ Ver Ejemplo]                │
│ [📚 Ayuda]                      │
└─────────────────────────────────┘
```

#### Escenario C: Dispositivo con Rendimiento Limitado
```
DETECCIÓN AUTOMÁTICA:
- Monitores de frame rate <30fps
- Detecta dispositivos móviles antiguos
- Identifica conexiones lentas

OPTIMIZACIONES AUTOMÁTICAS:
1. Reduce efectos visuales (sombras, animaciones)
2. Limita nodos visibles simultáneos
3. Simplifica geometría de edges
4. Aplica debounce más agresivo a interacciones
5. Notifica: "Modo de rendimiento activado para mejor experiencia"

CONTROLES ADICIONALES:
- Toggle manual "Modo de rendimiento"
- Opción "Calidad vs Velocidad"
- Estadísticas de rendimiento en tiempo real
```

---

## 10. TAREAS DETALLADAS POR EQUIPO {#tareas-equipos}

### 10.1 EQUIPO FRONTEND - REACT/TYPESCRIPT

#### 🏗️ ARQUITECTURA CORE
**Responsable**: Senior Frontend Developer  
**Estimación**: 3-4 semanas  
**Prioridad**: Crítica  

##### Tareas Específicas:
```typescript
// Tarea F1: Refactorización del componente principal
interface TaskF1 {
  title: "Crear HybridCorrelationDiagram.tsx con 4 modos confirmados",
  description: "Componente principal que maneja alternancia entre modos específicos",
  deliverables: [
    "Estructura modular con factory patterns",
    "Sistema de props unificado para 4 modos",
    "Gestión de estado sin pérdida en transiciones",
    "Error boundaries robustos",
    "Modo predeterminado: Radial Central"
  ],
  acceptanceCriteria: [
    "Alterna entre 4 modos específicos: Radial Central, Circular Avatares, Flujo Lineal, Híbrido Inteligente",
    "Transiciones instantáneas (sin animaciones)",
    "Mantiene compatibilidad con avatarMale.svg",
    "Preserva funcionalidades de export/filtros en todos los modos",
    "Maneja hasta 50 nodos simultáneos"
  ],
  files: [
    "HybridCorrelationDiagram.tsx",
    "DiagramEngine.tsx", 
    "ModeManager.tsx (4 modos específicos)",
    "DataTransformer.tsx"
  ]
}

// Tarea F2: Factory de Nodos (4 Modos Específicos)
interface TaskF2 {
  title: "Implementar NodeFactory para 4 modos confirmados",
  description: "Sistema factory para nodos específicos por modo",
  deliverables: [
    "NodeFactory.tsx con 4 tipos específicos",
    "RadialCentralNode.tsx (rectangulares centro-radial)",
    "CircularAvatarNode.tsx (círculos con avatarMale.svg)",
    "LinearFlowNode.tsx (estados visuales secuenciales)",
    "HybridSmartNode.tsx (selección automática)"
  ],
  acceptanceCriteria: [
    "Compatibilidad total con avatarMale.svg",
    "Nodos rectangulares profesionales para modo Radial Central",
    "Nodos circulares con avatares para modo Circular",
    "Estados visuales claros para modo Flujo Lineal",
    "Transiciones instantáneas entre tipos",
    "Colores distintivos por correlación en todos los modos"
  ],
  dependencies: ["TaskF1"]
}

// Tarea F3: Factory de Edges (Conexiones por Modo)
interface TaskF3 {
  title: "Implementar EdgeFactory para tipos de conexión específicos",
  description: "Sistema factory para conexiones adaptadas por modo",
  deliverables: [
    "EdgeFactory.tsx con 4 tipos de conexión",
    "RadialBezierEdge.tsx (curvas convergentes al centro)",
    "CircularDirectionalEdge.tsx (flechas force-directed)", 
    "LinearRectangularEdge.tsx (conexiones rectilíneas)",
    "HybridAdaptiveEdge.tsx (automático según contexto)",
    "Sistema anti-colisión de IDs de celda"
  ],
  acceptanceCriteria: [
    "Curvas Bezier elegantes para modo Radial Central",
    "Flechas direccionales claras para modo Circular",
    "Conexiones rectilíneas directas para modo Lineal",
    "IDs de celda visibles sin superposición",
    "Cambios instantáneos entre tipos (sin animaciones)",
    "Tooltips informativos en hover para todos los modos"
  ],
  dependencies: ["TaskF2"]
}
```

##### Testing Unitario Frontend:
```typescript
// Cobertura mínima requerida: 90%
const testingSuite = {
  unitTests: [
    "NodeFactory creation logic",
    "EdgeFactory rendering",
    "Mode transition state management", 
    "Data transformation accuracy",
    "Color system consistency"
  ],
  
  integrationTests: [
    "React Flow integration",
    "Multi-mode transitions",
    "Performance with large datasets",
    "Accessibility compliance"
  ],
  
  e2eTests: [
    "Complete user workflow",
    "Cross-browser compatibility", 
    "Mobile responsiveness",
    "Export functionality"
  ]
}
```

#### 🎨 CONTROLES DE INTERFAZ
**Responsable**: UI/UX Developer  
**Estimación**: 2-3 semanas  
**Prioridad**: Alta  

##### Tareas Específicas:
```typescript
// Tarea F4: Panel de Controles Principal
interface TaskF4 {
  title: "Crear ModeToggle y controles de visualización",
  description: "Panel principal de alternancia de modos con UX optimizada",
  deliverables: [
    "ModeToggle.tsx con radio buttons estilizados",
    "AdvancedFilters.tsx con sliders y checkboxes",
    "ExportControls.tsx con preview",
    "AccessibilityControls.tsx"
  ],
  acceptanceCriteria: [
    "Transiciones visuales smooth entre modos",
    "Feedback inmediato en todos los controles",
    "Atajos de teclado funcionales",
    "Estado persistente en localStorage"
  ],
  designSystem: [
    "Componentes consistent con tema KRONOS",
    "Paleta de colores híbrida aplicada",
    "Tipografía responsive",
    "Iconografía semántica"
  ]
}

// Tarea F5: Paneles Informativos
interface TaskF5 {
  title: "Crear InfoPanel, LegendPanel y StatisticsPanel",
  description: "Paneles laterales con información contextual",
  deliverables: [
    "InfoPanel.tsx tiempo real",
    "LegendPanel.tsx adaptativa",
    "StatisticsPanel.tsx con métricas", 
    "SettingsPanel.tsx personalización"
  ],
  acceptanceCriteria: [
    "Actualización en tiempo real sin lag",
    "Layout responsive para mobile",
    "Información estructurada y clara",
    "Configuración persistente"
  ],
  dependencies: ["TaskF4"]
}
```

#### 📱 RESPONSIVE Y ACCESIBILIDAD
**Responsable**: Accessibility Specialist  
**Estimación**: 2 semanas  
**Prioridad**: Alta  

##### Tareas Específicas:
```typescript
// Tarea F6: Implementación Responsive
interface TaskF6 {
  title: "Adaptar toda la interfaz para dispositivos móviles",
  description: "Responsive design completo con optimizaciones móviles",
  deliverables: [
    "Breakpoints responsivos implementados",
    "Bottom sheets para móvil",
    "Gestos touch optimizados",
    "Simplificación automática en pantallas pequeñas"
  ],
  acceptanceCriteria: [
    "Usable en pantallas desde 320px",
    "Targets táctiles mínimo 44px",
    "Performance 60fps en móviles",
    "Orientación portrait/landscape"
  ],
  testDevices: [
    "iPhone SE (375x667)",
    "Samsung Galaxy S21 (360x800)",
    "iPad (768x1024)",
    "iPad Pro (1024x1366)"
  ]
}

// Tarea F7: WCAG 2.1 AA Compliance
interface TaskF7 {
  title: "Implementar características de accesibilidad",
  description: "Cumplimiento completo WCAG 2.1 AA",
  deliverables: [
    "Navegación por teclado completa",
    "Screen reader support",
    "Alto contraste opcional",
    "Reducción de movimiento"
  ],
  acceptanceCriteria: [
    "100% navegable por teclado",
    "Lectores de pantalla functional",
    "Contraste 4.5:1 mínimo",
    "Prefers-reduced-motion respected"
  ],
  tools: [
    "axe-core testing",
    "NVDA screen reader testing",
    "Keyboard navigation testing",
    "Color contrast validation"
  ]
}
```

### 10.2 EQUIPO BACKEND - PYTHON/EEL

#### 🔧 SERVICIOS DE DATOS
**Responsable**: Backend Developer  
**Estimación**: 1-2 semanas  
**Prioridad**: Media  

##### Tareas Específicas:
```python
# Tarea B1: Optimización del servicio de correlación
class TaskB1:
    title = "Optimizar diagram_correlation_service.py"
    description = "Mejorar performance y añadir nuevas capacidades"
    
    deliverables = [
        "Caching inteligente de resultados",
        "Paginación para redes grandes", 
        "Filtros de datos en backend",
        "Exportación optimizada"
    ]
    
    acceptance_criteria = [
        "Respuesta <2s para 50 nodos",
        "Caching efectivo (90% hit rate)",
        "Memoria usage optimizada",
        "Logs detallados para debugging"
    ]
    
    new_endpoints = [
        "@eel.expose get_correlation_data_paginated",
        "@eel.expose get_filtered_interactions", 
        "@eel.expose export_diagram_data",
        "@eel.expose get_diagram_statistics"
    ]

# Tarea B2: Gestión de avatares y recursos
class TaskB2:
    title = "Servicio de gestión de avatares"
    description = "Sistema de avatares optimizado para el modo familiar"
    
    deliverables = [
        "Avatar service con caching",
        "SVG optimization",
        "Fallback system robusto",
        "Preload de recursos críticos"
    ]
    
    implementation = """
    @eel.expose
    def get_avatar_for_phone(phone_number, gender_hint=None):
        # Determina el avatar apropiado basado en datos disponibles
        # Implementa caching para evitar re-cálculos
        # Retorna SVG optimizado
        pass
    
    @eel.expose  
    def preload_avatar_resources():
        # Pre-carga avatares más comunes
        # Optimiza memoria del navegador
        pass
    """
```

#### 📊 ANALYTICS Y EXPORTACIÓN
**Responsable**: Data Engineer  
**Estimación**: 1 semana  
**Prioridad**: Baja  

##### Tareas Específicas:
```python
# Tarea B3: Sistema de analytics
class TaskB3:
    title = "Implementar analytics del diagrama"
    description = "Métricas de uso y performance para optimización"
    
    deliverables = [
        "Usage analytics (modos más usados)",
        "Performance metrics",
        "Error tracking avanzado",
        "User behavior insights"
    ]
    
    metrics_collected = [
        "mode_usage_frequency",
        "average_session_duration", 
        "most_used_filters",
        "export_format_preferences",
        "performance_bottlenecks"
    ]
    
    acceptance_criteria = [
        "Analytics no afectan performance",
        "Privacy compliant (GDPR)",
        "Dashboard para admin",
        "Alertas automáticas de problemas"
    ]
```

### 10.3 EQUIPO QA/TESTING

#### 🧪 TESTING INTEGRAL
**Responsable**: QA Lead  
**Estimación**: 2-3 semanas  
**Prioridad**: Crítica  

##### Plan de Testing Específico:
```typescript
// Testing Matrix Completa
interface TestingMatrix {
  functionalTesting: {
    modeTransitions: [
      "Professional → Familiar transition",
      "Familiar → Hybrid transition", 
      "Hybrid → Professional transition",
      "State preservation during transitions"
    ],
    
    interactivity: [
      "Node hover and selection",
      "Edge click and hover",
      "Multi-node selection",
      "Keyboard navigation"
    ],
    
    filters: [
      "Correlation slider functionality",
      "Operator filter combinations",
      "Date range filtering",
      "Real-time filter application"
    ],
    
    export: [
      "PNG export quality verification",
      "SVG export completeness",
      "JSON export data integrity",
      "Export filename conventions"
    ]
  },
  
  performanceTesting: {
    loadTesting: [
      "5 nodes - baseline performance",
      "15 nodes - typical usage", 
      "30 nodes - heavy usage",
      "50+ nodes - stress testing"
    ],
    
    memoryTesting: [
      "Memory usage during mode transitions",
      "Memory leaks in long sessions",
      "Garbage collection efficiency",
      "Resource cleanup on modal close"
    ]
  },
  
  accessibilityTesting: {
    keyboardOnly: [
      "Full navigation without mouse",
      "Focus management",
      "Skip links functionality",
      "Shortcut key responsiveness"
    ],
    
    screenReader: [
      "NVDA compatibility",
      "JAWS compatibility", 
      "VoiceOver (macOS) compatibility",
      "Aria labels accuracy"
    ],
    
    visualImpairment: [
      "High contrast mode",
      "Color blindness simulation",
      "Text scaling (up to 200%)",
      "Reduced motion preferences"
    ]
  }
}
```

##### Criterios de Aceptación Final:
```typescript
interface FinalAcceptanceCriteria {
  functionalRequirements: {
    modesWork: "✅ Los 4 modos visuales funcionan correctamente",
    transitionsSmooth: "✅ Transiciones fluidas sin pérdida de estado",
    interactionsResponsive: "✅ Todas las interacciones responden <200ms",
    filtersAccurate: "✅ Filtros aplican correctamente y en tiempo real",
    exportWorks: "✅ Export en PNG, SVG, JSON funcional"
  },
  
  performanceRequirements: {
    smallDatasets: "✅ <5 nodos: 60fps constante",
    mediumDatasets: "✅ 5-20 nodos: 45fps mínimo",
    largeDatasets: "✅ 20-50 nodos: 30fps mínimo", 
    memoryUsage: "✅ <100MB RAM usage",
    loadTime: "✅ Modal abre en <2 segundos"
  },
  
  accessibilityRequirements: {
    wcagAA: "✅ WCAG 2.1 AA compliant (auditado)",
    keyboardNav: "✅ 100% navegable por teclado",
    screenReader: "✅ Compatible con lectores principales",
    contrast: "✅ Ratio de contraste 4.5:1 mínimo"
  },
  
  usabilityRequirements: {
    intuitive: "✅ 90% usuarios completan tarea sin ayuda",
    learnability: "✅ 80% usuarios switch modes en primera sesión",
    efficiency: "✅ Investigadores expertos 50% más rápidos",
    satisfaction: "✅ >8/10 en encuesta de satisfacción"
  }
}
```

### 10.4 CRONOGRAMA DE IMPLEMENTACIÓN

#### SPRINT 1 (Semana 1-2): FUNDACIÓN
```
🏗️ ARQUITECTURA CORE
[Frontend] Tarea F1: HybridCorrelationDiagram.tsx
[Frontend] Tarea F2: NodeFactory + componentes base
[Backend]  Tarea B1: Optimización servicio correlación

ENTREGABLES SPRINT 1:
✅ Estructura modular completa
✅ Modo Radial Central (predeterminado) funcional
✅ Modo Circular Avatares con avatarMale.svg
✅ Sistema factory para 4 modos
✅ Backend optimizado

CRITERIOS DE ACEPTACIÓN SPRINT 1:
- Modal abre con modo Radial Central por defecto
- Puede alternar entre 4 modos específicos
- Transiciones instantáneas funcionando
- Performance baseline establecida
```

#### SPRINT 2 (Semana 3-4): INTERFAZ AVANZADA
```
🎨 CONTROLES E INTERACCIÓN
[Frontend] Tarea F3: EdgeFactory + anti-colisión
[Frontend] Tarea F4: Controles principales
[Frontend] Tarea F5: Paneles informativos
[Backend]  Tarea B2: Gestión de avatares

ENTREGABLES SPRINT 2:
✅ 4 modos visuales completamente funcionales
✅ Barra de controles de modo separada
✅ Modo Flujo Lineal y Híbrido Inteligente
✅ Sistema de etiquetas sin colisiones
✅ Compatibilidad total con avatarMale.svg

CRITERIOS DE ACEPTACIÓN SPRINT 2:
- 4 modos específicos 100% operativos
- Cambios instantáneos entre modos
- Barra de modo separada funcional
- Filtros/exports preservados en todos los modos
```

#### SPRINT 3 (Semana 5-6): RESPONSIVE & ACCESIBILIDAD
```
📱 OPTIMIZACIÓN FINAL
[Frontend] Tarea F6: Implementación responsive
[Frontend] Tarea F7: WCAG 2.1 AA compliance
[Backend]  Tarea B3: Analytics sistema
[QA]       Testing integral

ENTREGABLES SPRINT 3:
✅ Mobile responsive completo
✅ Accesibilidad WCAG AA
✅ Analytics implementado
✅ Suite de testing completa

CRITERIOS DE ACEPTACIÓN SPRINT 3:
- Usable en móviles desde 320px
- Auditoria a11y aprobada
- Testing coverage >90%
```

#### SPRINT 4 (Semana 7): PULIMIENTO Y RELEASE
```
🚀 PREPARACIÓN PARA PRODUCCIÓN
[Todos] Bug fixes de testing
[Todos] Optimizaciones de performance
[Docs]  Documentación técnica y usuario
[QA]    Validation final

ENTREGABLES SPRINT 4:
✅ Zero bugs críticos
✅ Performance optimizada
✅ Documentación completa
✅ Release notes

CRITERIOS DE RELEASE:
- Todos los acceptance criteria cumplidos
- Performance benchmarks alcanzados
- Documentación aprobada por Boris
```

---

## 📋 RESUMEN DE ENTREGABLES

### COMPONENTES PRINCIPALES
- ✅ `HybridCorrelationDiagram.tsx` - Componente principal híbrido
- ✅ `NodeFactory.tsx` - Factory de nodos adaptativos  
- ✅ `EdgeFactory.tsx` - Factory de conexiones optimizadas
- ✅ `ModeToggle.tsx` - Controles de alternancia visual
- ✅ `AdvancedFilters.tsx` - Filtros profesionales completos

### CARACTERÍSTICAS CORE
- ✅ **4 Modos Específicos**: Radial Central, Circular Avatares, Flujo Lineal, Híbrido Inteligente
- ✅ **Compatibilidad avatarMale.svg**: Integración completa con iconos existentes
- ✅ **Transiciones Instantáneas**: Cambios de modo sin animaciones
- ✅ **Barra de Controles Separada**: UI optimizada para cambio de modo
- ✅ **Funcionalidades Preservadas**: Export/filtros disponibles en todos los modos
- ✅ **Responsive Design**: Desde móviles 320px hasta pantallas 4K
- ✅ **WCAG 2.1 AA**: Accesibilidad completa para investigadores
- ✅ **Performance**: 60fps hasta 50 nodos, degradación elegante

### MÉTRICAS DE ÉXITO
- ✅ **UX**: 90% comprensión inmediata sin training
- ✅ **Performance**: <2s tiempo de carga, 60fps transiciones
- ✅ **Accesibilidad**: 100% navegable por teclado
- ✅ **Escalabilidad**: Soporte hasta 50 nodos simultáneos
- ✅ **Compatibilidad**: Chrome, Firefox, Safari, Edge

---

## 🎯 PRÓXIMOS PASOS RECOMENDADOS

1. **APROBACIÓN DE ESPECIFICACIONES** (Boris)
   - Revisar wireframes y flujos de usuario
   - Validar paleta de colores y sistema visual
   - Confirmar prioridades de características

2. **SETUP DE EQUIPO DE DESARROLLO**
   - Asignar roles específicos por tarea
   - Configurar ambiente de desarrollo híbrido
   - Establecer pipeline de testing automatizado

3. **PROTOTIPO INICIAL** (Semana 1)
   - Implementar modal básico con modo professional
   - Validar integración con React Flow actual
   - Proof of concept de factory pattern

4. **ITERACIÓN CON FEEDBACK DE USUARIOS**
   - Testing con investigadores reales (Semana 3)
   - Ajustes basados en feedback de usabilidad
   - Optimización de flujos de trabajo específicos

Boris, este plan actualizado incorpora todas las especificaciones confirmadas para los 4 modos de visualización específicos:

**CONFIRMACIONES IMPLEMENTADAS:**
- ✅ **Modo Radial Central** como predeterminado
- ✅ **Transiciones instantáneas** sin animaciones
- ✅ **Barra de controles separada** para cambio de modo
- ✅ **Compatibilidad completa** con avatarMale.svg
- ✅ **Preservación de funcionalidades** export/filtros en todos los modos
- ✅ **4 modos específicos** con características detalladas

El documento proporciona una hoja de ruta completa para implementar el sistema de diagrama de correlación más profesional y adaptable para investigación forense. ¿Te gustaría que profundicemos en alguna sección específica o iniciemos con la implementación del prototipo?