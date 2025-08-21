/**
 * Esquemas de colores para el diagrama de correlación telefónica
 * Consistente con el tema KRONOS
 * Boris & Claude Code - 2025-08-21
 */

import { NodeColorScheme, EdgeColorScheme } from '../types/correlation.types';

// ==================== PALETA DE COLORES KRONOS ====================

export const KRONOS_COLORS = {
    // Colores primarios del tema KRONOS
    primary: '#00D4FF',         // Cyan brillante
    primaryDark: '#0099CC',     // Cyan oscuro
    secondary: '#1F2937',       // Gris oscuro
    secondaryLight: '#374151',  // Gris medio
    accent: '#10B981',          // Verde éxito
    warning: '#F59E0B',         // Ámbar
    danger: '#EF4444',          // Rojo
    info: '#3B82F6',           // Azul
    
    // Grises del sistema
    gray900: '#111827',
    gray800: '#1F2937',
    gray700: '#374151',
    gray600: '#4B5563',
    gray500: '#6B7280',
    gray400: '#9CA3AF',
    gray300: '#D1D5DB',
    
    // Colores de operadores telefónicos
    operators: {
        CLARO: '#FF0000',       // Rojo Claro
        MOVISTAR: '#00A651',    // Verde Movistar
        TIGO: '#0078D4',        // Azul Tigo
        ETB: '#FFD700',         // Dorado ETB
        AVANTEL: '#8A2BE2',     // Violeta Avantel
        VIRGIN: '#DC143C',      // Rojo Virgin
        DEFAULT: '#6B7280'      // Gris por defecto
    }
};

// ==================== ESQUEMAS DE COLORES PARA NODOS ====================

/**
 * Esquema de colores principal para nodos
 */
export const NODE_COLOR_SCHEME: NodeColorScheme = {
    target: KRONOS_COLORS.primary,          // Cyan para target
    active: KRONOS_COLORS.accent,           // Verde para activos
    inactive: KRONOS_COLORS.gray600,        // Gris para inactivos
    selected: KRONOS_COLORS.warning,        // Ámbar para seleccionados
    background: KRONOS_COLORS.gray800,      // Fondo gris oscuro
    border: KRONOS_COLORS.gray600           // Borde gris medio
};

/**
 * Esquema de colores alternativo (tema claro)
 */
export const NODE_COLOR_SCHEME_LIGHT: NodeColorScheme = {
    target: '#0066CC',
    active: '#00AA44',
    inactive: '#999999',
    selected: '#FF8800',
    background: '#FFFFFF',
    border: '#CCCCCC'
};

// ==================== ESQUEMAS DE COLORES PARA CONEXIONES ====================

/**
 * Esquema de colores principal para conexiones
 */
export const EDGE_COLOR_SCHEME: EdgeColorScheme = {
    incoming: '#3B82F6',                    // Azul para entrantes
    outgoing: '#10B981',                    // Verde para salientes
    bidirectional: '#8B5CF6',              // Violeta para bidireccionales
    selected: KRONOS_COLORS.warning,        // Ámbar para seleccionadas
    weak: '#6B7280',                        // Gris para conexiones débiles
    strong: '#F59E0B'                       // Ámbar para conexiones fuertes
};

// ==================== FUNCIONES DE UTILIDAD ====================

/**
 * Obtiene color basado en el operador telefónico
 */
export function getOperatorColor(operator: string): string {
    const upperOperator = operator.toUpperCase();
    return KRONOS_COLORS.operators[upperOperator as keyof typeof KRONOS_COLORS.operators] 
        || KRONOS_COLORS.operators.DEFAULT;
}

/**
 * Genera color determinístico basado en número telefónico
 */
export function getPhoneNumberColor(phoneNumber: string): string {
    // Algoritmo determinístico para generar color consistente
    let hash = 0;
    for (let i = 0; i < phoneNumber.length; i++) {
        const char = phoneNumber.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convertir a 32-bit integer
    }
    
    // Palette de colores complementarios
    const colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', 
        '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F',
        '#BB8FCE', '#85C1E9', '#F8C471', '#82E0AA'
    ];
    
    const index = Math.abs(hash) % colors.length;
    return colors[index];
}

/**
 * Calcula color de conexión basado en fuerza y dirección
 */
export function getConnectionColor(
    strength: number, 
    direction: 'incoming' | 'outgoing' | 'bidirectional',
    isSelected: boolean = false
): string {
    if (isSelected) {
        return EDGE_COLOR_SCHEME.selected;
    }
    
    // Color base según dirección
    let baseColor: string;
    switch (direction) {
        case 'incoming':
            baseColor = EDGE_COLOR_SCHEME.incoming;
            break;
        case 'outgoing':
            baseColor = EDGE_COLOR_SCHEME.outgoing;
            break;
        case 'bidirectional':
            baseColor = EDGE_COLOR_SCHEME.bidirectional;
            break;
        default:
            baseColor = EDGE_COLOR_SCHEME.weak;
    }
    
    // Ajustar intensidad según fuerza (1-10)
    const opacity = Math.max(0.3, Math.min(1.0, strength / 10));
    return `${baseColor}${Math.round(opacity * 255).toString(16).padStart(2, '0')}`;
}

/**
 * Obtiene gradiente para nodos target
 */
export function getTargetNodeGradient(): string {
    return `linear-gradient(135deg, ${KRONOS_COLORS.primary} 0%, ${KRONOS_COLORS.primaryDark} 100%)`;
}

/**
 * Obtiene estilo de sombra para nodos seleccionados
 */
export function getSelectedNodeShadow(): string {
    return `0 0 20px ${KRONOS_COLORS.warning}66`; // 40% opacity
}

/**
 * Calcula color de nodo basado en estado y tipo
 */
export function getNodeColor(
    isTarget: boolean,
    isSelected: boolean,
    isActive: boolean,
    interactionCount: number
): string {
    if (isSelected) {
        return NODE_COLOR_SCHEME.selected;
    }
    
    if (isTarget) {
        return NODE_COLOR_SCHEME.target;
    }
    
    if (isActive && interactionCount > 5) {
        return NODE_COLOR_SCHEME.active;
    }
    
    // Color basado en intensidad de interacciones
    if (interactionCount > 10) {
        return '#FF6B6B'; // Rojo intenso para muy activos
    } else if (interactionCount > 5) {
        return '#FFD93D'; // Amarillo para moderadamente activos
    } else if (interactionCount > 1) {
        return '#6BCF7F'; // Verde para poco activos
    } else {
        return NODE_COLOR_SCHEME.inactive; // Gris para inactivos
    }
}

// ==================== ESQUEMAS TEMÁTICOS ====================

/**
 * Esquema de colores para modo nocturno
 */
export const NIGHT_MODE_SCHEME = {
    nodes: {
        ...NODE_COLOR_SCHEME,
        background: '#0F172A',
        border: '#334155'
    },
    edges: {
        ...EDGE_COLOR_SCHEME,
        incoming: '#60A5FA',
        outgoing: '#34D399',
        weak: '#475569'
    },
    background: '#0F172A'
};

/**
 * Esquema de colores para alta visibilidad
 */
export const HIGH_CONTRAST_SCHEME = {
    nodes: {
        target: '#FFFF00',      // Amarillo brillante
        active: '#00FF00',      // Verde brillante
        inactive: '#FFFFFF',    // Blanco
        selected: '#FF0000',    // Rojo brillante
        background: '#000000',  // Negro
        border: '#FFFFFF'       // Blanco
    },
    edges: {
        incoming: '#00FFFF',    // Cyan
        outgoing: '#FF00FF',    // Magenta
        bidirectional: '#FFFF00', // Amarillo
        selected: '#FF0000',    // Rojo
        weak: '#808080',        // Gris
        strong: '#FFFFFF'       // Blanco
    },
    background: '#000000'
};

/**
 * Paleta de colores para análisis forense
 */
export const FORENSIC_ANALYSIS_COLORS = {
    suspect: '#FF4444',         // Rojo para sospechosos
    witness: '#44FF44',         // Verde para testigos  
    victim: '#4444FF',          // Azul para víctimas
    unknown: '#FFFF44',         // Amarillo para desconocidos
    critical: '#FF0000',        // Rojo crítico
    evidence: '#800080',        // Púrpura para evidencia
    timeline: '#FFA500'         // Naranja para línea temporal
};

// ==================== FUNCIONES DE INTERPOLACIÓN ====================

/**
 * Interpola entre dos colores basado en un factor (0-1)
 */
export function interpolateColor(color1: string, color2: string, factor: number): string {
    // Convertir colores hex a RGB
    const hex2rgb = (hex: string) => {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : { r: 0, g: 0, b: 0 };
    };
    
    const rgb1 = hex2rgb(color1);
    const rgb2 = hex2rgb(color2);
    
    // Interpolar componentes RGB
    const r = Math.round(rgb1.r + (rgb2.r - rgb1.r) * factor);
    const g = Math.round(rgb1.g + (rgb2.g - rgb1.g) * factor);
    const b = Math.round(rgb1.b + (rgb2.b - rgb1.b) * factor);
    
    // Convertir de vuelta a hex
    return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
}

/**
 * Genera escala de colores para intensidad de conexiones
 */
export function generateIntensityColorScale(steps: number = 10): string[] {
    const scale: string[] = [];
    const lowColor = '#6B7280';   // Gris para baja intensidad
    const highColor = '#EF4444';  // Rojo para alta intensidad
    
    for (let i = 0; i < steps; i++) {
        const factor = i / (steps - 1);
        scale.push(interpolateColor(lowColor, highColor, factor));
    }
    
    return scale;
}