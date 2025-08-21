/**
 * Tipos TypeScript para el Diagrama de Correlación Telefónica
 * Compatible con CallInteraction del TableCorrelationModal
 * Boris & Claude Code - 2025-08-21
 */

import { Node, Edge } from 'reactflow';

// ==================== TIPOS BASE ====================

/**
 * Interface de interacción telefónica (reutilizada de TableCorrelationModal)
 */
export interface CallInteraction {
    originador: string;
    receptor: string;
    fecha_hora: string;
    duracion: number;
    operador: string;
    celda_origen: string;
    celda_destino: string;
    latitud_origen?: number;
    longitud_origen?: number;
    latitud_destino?: number;
    longitud_destino?: number;
    punto_hunter_origen?: string;
    lat_hunter_origen?: number;
    lon_hunter_origen?: number;
    punto_hunter_destino?: string;
    lat_hunter_destino?: number;
    lon_hunter_destino?: number;
    punto_hunter?: string;
    lat_hunter?: number;
    lon_hunter?: number;
    hunter_source?: string;
    precision_ubicacion?: string;
}

/**
 * Modos de visualización del diagrama
 */
export type VisualizationMode = 
    | 'radial'      // Target al centro, otros en círculo
    | 'circular'    // Todos en círculo con avatares
    | 'linear'      // Flujo temporal lineal
    | 'hybrid';     // Automático según cantidad de datos

/**
 * Configuración de filtros del diagrama
 */
export interface DiagramFilters {
    minCorrelation: number;     // Mínimo número de interacciones para mostrar
    showCellIds: boolean;       // Mostrar IDs de celda en las conexiones
    showTimeLabels: boolean;    // Mostrar etiquetas de tiempo
    onlyRecentCalls: boolean;   // Solo llamadas recientes
}

/**
 * Configuración de exportación
 */
export interface ExportConfig {
    format: 'png' | 'svg' | 'json';
    quality: number;            // Calidad 0.1 - 1.0
    width?: number;             // Ancho personalizado
    height?: number;            // Alto personalizado
}

// ==================== TIPOS DE NODOS ====================

/**
 * Tipos de nodos personalizados
 */
export type PhoneNodeType = 
    | 'radialTarget'    // Nodo central target
    | 'radialSource'    // Nodos radiales normales
    | 'circularAvatar'  // Nodos circulares con avatar
    | 'linearFlow';     // Nodos de flujo lineal

/**
 * Datos base de un nodo telefónico
 */
export interface PhoneNodeData {
    number: string;             // Número telefónico
    isTarget: boolean;          // Es el número objetivo
    operator: string;           // Operador (CLARO, MOVISTAR, etc.)
    interactionCount: number;   // Cantidad de interacciones
    lastInteraction: string;    // Fecha de última interacción
    callDuration: number;       // Duración total de llamadas (segundos)
    hunterPoints: string[];     // Puntos HUNTER relacionados
    coordinates?: {             // Coordenadas GPS promedio
        lat: number;
        lon: number;
    };
    connections: {              // Información de conexiones
        incoming: number;       // Llamadas entrantes
        outgoing: number;       // Llamadas salientes
    };
}

/**
 * Nodo telefónico completo para React Flow
 */
export type PhoneNode = Node<PhoneNodeData, PhoneNodeType>;

// ==================== TIPOS DE CONEXIONES ====================

/**
 * Tipos de conexiones personalizadas
 */
export type ConnectionType = 
    | 'curved'          // Conexión curva suave
    | 'directional'     // Flecha direccional
    | 'linear';         // Conexión lineal

/**
 * Datos de una conexión telefónica
 */
export interface ConnectionData {
    interactions: CallInteraction[];   // Interacciones que forman esta conexión
    totalDuration: number;             // Duración total en segundos
    callCount: number;                 // Número de llamadas
    direction: 'bidirectional' | 'outgoing' | 'incoming';
    cellIds: string[];                 // IDs de celdas involucradas
    timeRange: {                       // Rango temporal
        first: string;
        last: string;
    };
    strengthWeight: number;            // Peso de la conexión (1-10)
}

/**
 * Conexión telefónica completa para React Flow
 */
export type PhoneConnection = Edge<ConnectionData>;

// ==================== TIPOS DE LAYOUTS ====================

/**
 * Configuración de layout radial
 */
export interface RadialLayoutConfig {
    centerX: number;
    centerY: number;
    radius: number;
    startAngle: number;         // Ángulo inicial en radianes
    nodeSpacing: number;        // Espaciado entre nodos
}

/**
 * Configuración de layout circular
 */
export interface CircularLayoutConfig {
    centerX: number;
    centerY: number;
    radius: number;
    nodeSize: number;           // Tamaño de los nodos
    avatarSpacing: number;      // Espaciado entre avatares
}

/**
 * Configuración de layout lineal
 */
export interface LinearLayoutConfig {
    startX: number;
    startY: number;
    direction: 'horizontal' | 'vertical';
    nodeSpacing: number;
    timeBasedSpacing: boolean;  // Espaciado basado en tiempo
}

// ==================== TIPOS DE ESTADO ====================

/**
 * Estado del diagrama de correlación
 */
export interface CorrelationDiagramState {
    mode: VisualizationMode;
    filters: DiagramFilters;
    nodes: PhoneNode[];
    edges: PhoneConnection[];
    selectedNode: string | null;
    selectedEdge: string | null;
    isLoading: boolean;
    error: string | null;
}

/**
 * Estadísticas del diagrama
 */
export interface DiagramStats {
    totalNumbers: number;
    totalInteractions: number;
    averageCallDuration: number;
    mostActiveNumber: string;
    timeSpan: {
        start: string;
        end: string;
    };
    operatorDistribution: Record<string, number>;
}

// ==================== TIPOS DE COLORES ====================

/**
 * Esquema de colores para nodos
 */
export interface NodeColorScheme {
    target: string;             // Color del nodo objetivo
    active: string;             // Color de nodos activos
    inactive: string;           // Color de nodos inactivos
    selected: string;           // Color de nodo seleccionado
    background: string;         // Color de fondo del nodo
    border: string;             // Color del borde
}

/**
 * Esquema de colores para conexiones
 */
export interface EdgeColorScheme {
    incoming: string;           // Color para llamadas entrantes
    outgoing: string;           // Color para llamadas salientes
    bidirectional: string;      // Color para conexiones bidireccionales
    selected: string;           // Color de conexión seleccionada
    weak: string;               // Color para conexiones débiles
    strong: string;             // Color para conexiones fuertes
}

// ==================== TIPOS DE EVENTOS ====================

/**
 * Eventos del diagrama
 */
export interface DiagramEvents {
    onNodeClick?: (node: PhoneNode) => void;
    onNodeDoubleClick?: (node: PhoneNode) => void;
    onEdgeClick?: (edge: PhoneConnection) => void;
    onModeChange?: (mode: VisualizationMode) => void;
    onFiltersChange?: (filters: DiagramFilters) => void;
    onExport?: (config: ExportConfig) => void;
}

/**
 * Props del componente principal del diagrama
 */
export interface PhoneCorrelationViewerProps {
    interactions: CallInteraction[];
    targetNumber: string;
    isOpen: boolean;
    onClose: () => void;
    events?: DiagramEvents;
    initialMode?: VisualizationMode;
    className?: string;
}