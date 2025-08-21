/**
 * Tipos TypeScript específicos para React Flow - Diagrama de Correlación Telefónica
 * Migración D3.js → React Flow
 * Actualizado: 2025-08-20 por Boris - Implementación React Flow
 */

import { Node, Edge, NodeProps, EdgeProps } from '@xyflow/react';

// Datos específicos para nodos de teléfono en React Flow
export interface CustomPhoneNodeData {
  phoneNumber: string;
  isTarget: boolean;
  correlationLevel: number;
  avatar: string;
  color: string;
  stats: {
    incoming: number;
    outgoing: number;
    totalDuration: number;
    lastContact: Date;
  };
}

// Datos específicos para enlaces de teléfono en React Flow
export interface CustomPhoneEdgeData {
  cellIds: string[];
  direction: 'incoming' | 'outgoing' | 'bidirectional';
  callCount: number;
  strength: number;
  color: string;
  labelStrategy?: LabelPositioningStrategy; // Estrategia de posicionamiento de etiquetas
  
  // NUEVO: Sistema de Edición de Rutas - Boris OPCIÓN B
  customControlPoints?: {
    cp1x: number; 
    cp1y: number;
    cp2x: number; 
    cp2y: number;
  };
  isEditable?: boolean; // Indica si esta línea puede ser editada
  originalControlPoints?: { // Backup para "Restaurar Original"
    cp1x: number; 
    cp1y: number;
    cp2x: number; 
    cp2y: number;
  };
}

// Tipos de nodos y enlaces React Flow
export type PhoneFlowNode = Node<CustomPhoneNodeData, 'phoneNode'>;
export type PhoneFlowEdge = Edge<CustomPhoneEdgeData>;

// Props para componente Custom Phone Node
export interface CustomPhoneNodeProps extends NodeProps<CustomPhoneNodeData> {
  data: CustomPhoneNodeData;
}

// Props para componente Custom Phone Edge  
export interface CustomPhoneEdgeProps extends EdgeProps<CustomPhoneEdgeData> {
  data: CustomPhoneEdgeData;
  labelStrategy?: LabelPositioningStrategy; // Estrategia de posicionamiento de etiquetas
  
  // NUEVO: Callback para comunicar cambios de puntos de control - Boris OPCIÓN B
  onControlPointsChange?: (edgeId: string, controlPoints: {
    cp1x: number; 
    cp1y: number;
    cp2x: number; 
    cp2y: number;
  }) => void;
}

// Configuración del layout React Flow
export interface ReactFlowLayoutConfig {
  algorithm: 'force' | 'hierarchical' | 'circular' | 'grid';
  spacing: {
    nodeDistance: number;
    layerDistance: number;
  };
  forces: {
    repulsion: number;
    attraction: number;
    gravity: number;
  };
}

// Configuración visual React Flow
export interface ReactFlowVisualConfig {
  node: {
    size: {
      target: number;      // Radio nodo objetivo
      regular: number;     // Radio nodos regulares  
    };
    colors: {
      target: string;      // Color nodo objetivo
      highCorr: string;    // Alta correlación
      medCorr: string;     // Media correlación
      lowCorr: string;     // Baja correlación
      indirect: string;    // Relación indirecta
    };
  };
  edge: {
    width: {
      base: number;        // Grosor base
      strong: number;      // Grosor fuerte
    };
    colors: {
      incoming: string;    // Enlaces entrantes
      outgoing: string;    // Enlaces salientes
      bidirectional: string; // Enlaces bidireccionales
    };
  };
  theme: {
    background: string;
    panel: string;
    border: string;
    text: string;
    textMuted: string;
  };
}

// Opciones de posicionamiento de etiquetas - Boris UX 4 Estrategias
export type LabelPositioningStrategy = 
  | 'fixed-corners'     // Posiciones fijas en esquinas predefinidas
  | 'inline-offset'     // A lo largo de la línea bezier con offset perpendicular  
  | 'tooltip-hover'     // Solo visible on-hover con tooltip dinámico
  | 'lateral-stack';    // Panel lateral con highlighting bidireccional

// NUEVO: Estado del Modo de Edición - Boris OPCIÓN B
export interface EditModeState {
  isEditMode: boolean;              // Toggle ON/OFF modo edición
  editingEdgeId: string | null;     // ID de la línea siendo editada actualmente
  isDragging: boolean;              // Estado de arrastre activo
  activeControlPoint: 'cp1' | 'cp2' | null; // Punto de control activo
}

// Estado de filtros para React Flow
export interface ReactFlowFilters {
  minCorrelation: number;
  showCellIds: boolean;
  showIsolatedNodes: boolean;
  layoutType: ReactFlowLayoutConfig['algorithm'];
  nodeTypes: string[];
  edgeTypes: string[];
  labelStrategy: LabelPositioningStrategy; // Nueva opción para estrategia de etiquetas
}

// Datos transformados listos para React Flow
export interface ReactFlowDiagramData {
  nodes: PhoneFlowNode[];
  edges: PhoneFlowEdge[];
  config: ReactFlowVisualConfig;
}

// Configuración de exportación
export interface ExportConfig {
  format: 'PNG' | 'SVG' | 'JSON';
  filename: string;
  includeBackground: boolean;
  includeControls: boolean;
  resolution: 72 | 150 | 300; // DPI para PNG
}

// Props para el hook adapter
export interface ReactFlowAdapterProps {
  interactions: any[]; // UnifiedInteraction[] del módulo principal  
  targetNumber: string;
  filters: ReactFlowFilters;
}

// Resultado del hook adapter
export interface ReactFlowAdapterResult {
  nodes: PhoneFlowNode[];
  edges: PhoneFlowEdge[];
  nodeTypes: Record<string, React.ComponentType<any>>;
  edgeTypes: Record<string, React.ComponentType<any>>;
}