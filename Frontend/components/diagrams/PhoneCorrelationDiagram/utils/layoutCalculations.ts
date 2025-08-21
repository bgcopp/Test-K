/**
 * Utilidades para cálculos de layout del diagrama de correlación
 * Boris & Claude Code - 2025-08-21
 */

import { 
    PhoneNode, 
    PhoneConnection, 
    RadialLayoutConfig, 
    CircularLayoutConfig, 
    LinearLayoutConfig 
} from '../types/correlation.types';

// ==================== CONSTANTES DE LAYOUT ====================

export const LAYOUT_CONSTANTS = {
    // Tamaños de nodos
    TARGET_NODE_SIZE: 80,
    NORMAL_NODE_SIZE: 60,
    AVATAR_NODE_SIZE: 70,
    LINEAR_NODE_SIZE: 50,
    
    // Espaciados
    MIN_RADIUS: 150,
    MAX_RADIUS: 400,
    NODE_SPACING: 20,
    EDGE_OFFSET: 10,
    
    // Márgenes de contenedor
    CONTAINER_PADDING: 50,
    HEADER_HEIGHT: 60,
    CONTROLS_HEIGHT: 80,
    
    // Colores por defecto
    DEFAULT_COLORS: {
        target: '#00D4FF',      // Cyan brillante para target
        normal: '#4F46E5',      // Indigo para nodos normales
        active: '#10B981',      // Verde para nodos activos
        selected: '#F59E0B',    // Ámbar para seleccionados
        background: '#1F2937',  // Gris oscuro de fondo
        border: '#374151'       // Gris medio para bordes
    }
};

// ==================== FUNCIONES DE LAYOUT RADIAL ====================

/**
 * Calcula posiciones para layout radial con target al centro
 */
export function calculateRadialLayout(
    nodes: PhoneNode[],
    config: RadialLayoutConfig
): PhoneNode[] {
    const { centerX, centerY, radius, startAngle = 0, nodeSpacing } = config;
    
    // Separar nodo target de los demás
    const targetNode = nodes.find(node => node.data.isTarget);
    const otherNodes = nodes.filter(node => !node.data.isTarget);
    
    const updatedNodes: PhoneNode[] = [];
    
    // Posicionar nodo target al centro
    if (targetNode) {
        updatedNodes.push({
            ...targetNode,
            position: { x: centerX, y: centerY },
            style: {
                ...targetNode.style,
                width: LAYOUT_CONSTANTS.TARGET_NODE_SIZE,
                height: LAYOUT_CONSTANTS.TARGET_NODE_SIZE
            }
        });
    }
    
    // Posicionar otros nodos en círculo
    const angleStep = (2 * Math.PI) / Math.max(otherNodes.length, 1);
    
    otherNodes.forEach((node, index) => {
        const angle = startAngle + (index * angleStep);
        const x = centerX + radius * Math.cos(angle);
        const y = centerY + radius * Math.sin(angle);
        
        updatedNodes.push({
            ...node,
            position: { x, y },
            style: {
                ...node.style,
                width: LAYOUT_CONSTANTS.NORMAL_NODE_SIZE,
                height: LAYOUT_CONSTANTS.NORMAL_NODE_SIZE
            }
        });
    });
    
    return updatedNodes;
}

/**
 * Calcula radio óptimo basado en cantidad de nodos
 */
export function calculateOptimalRadius(nodeCount: number): number {
    const { MIN_RADIUS, MAX_RADIUS, NODE_SPACING } = LAYOUT_CONSTANTS;
    
    // Fórmula empírica para radio óptimo
    const baseRadius = Math.sqrt(nodeCount) * NODE_SPACING * 3;
    return Math.max(MIN_RADIUS, Math.min(MAX_RADIUS, baseRadius));
}

// ==================== FUNCIONES DE LAYOUT CIRCULAR ====================

/**
 * Calcula posiciones para layout circular con avatares
 */
export function calculateCircularLayout(
    nodes: PhoneNode[],
    config: CircularLayoutConfig
): PhoneNode[] {
    const { centerX, centerY, radius, nodeSize, avatarSpacing } = config;
    
    const updatedNodes: PhoneNode[] = [];
    const angleStep = (2 * Math.PI) / Math.max(nodes.length, 1);
    
    nodes.forEach((node, index) => {
        const angle = index * angleStep;
        const x = centerX + radius * Math.cos(angle);
        const y = centerY + radius * Math.sin(angle);
        
        updatedNodes.push({
            ...node,
            position: { x, y },
            style: {
                ...node.style,
                width: nodeSize,
                height: nodeSize
            }
        });
    });
    
    return updatedNodes;
}

// ==================== FUNCIONES DE LAYOUT LINEAL ====================

/**
 * Calcula posiciones para layout lineal temporal
 */
export function calculateLinearLayout(
    nodes: PhoneNode[],
    config: LinearLayoutConfig
): PhoneNode[] {
    const { startX, startY, direction, nodeSpacing, timeBasedSpacing } = config;
    
    // Ordenar nodos por tiempo de última interacción si está habilitado
    const sortedNodes = timeBasedSpacing 
        ? [...nodes].sort((a, b) => 
            new Date(a.data.lastInteraction).getTime() - 
            new Date(b.data.lastInteraction).getTime()
          )
        : nodes;
    
    const updatedNodes: PhoneNode[] = [];
    
    sortedNodes.forEach((node, index) => {
        let x = startX;
        let y = startY;
        
        if (direction === 'horizontal') {
            x += index * (LAYOUT_CONSTANTS.LINEAR_NODE_SIZE + nodeSpacing);
        } else {
            y += index * (LAYOUT_CONSTANTS.LINEAR_NODE_SIZE + nodeSpacing);
        }
        
        updatedNodes.push({
            ...node,
            position: { x, y },
            style: {
                ...node.style,
                width: LAYOUT_CONSTANTS.LINEAR_NODE_SIZE,
                height: LAYOUT_CONSTANTS.LINEAR_NODE_SIZE
            }
        });
    });
    
    return updatedNodes;
}

// ==================== FUNCIONES DE LAYOUT HÍBRIDO ====================

/**
 * Determina el mejor modo de layout basado en la cantidad de datos
 */
export function determineOptimalMode(
    nodeCount: number,
    interactionCount: number
): 'radial' | 'circular' | 'linear' | 'hybrid' {
    // Lógica de decisión automática
    if (nodeCount <= 3) {
        return 'linear';        // Pocos nodos -> layout lineal
    } else if (nodeCount <= 8) {
        return 'radial';        // Cantidad media -> layout radial
    } else if (nodeCount <= 15) {
        return 'circular';      // Muchos nodos -> layout circular
    } else {
        return 'hybrid';        // Demasiados -> modo híbrido
    }
}

/**
 * Calcula layout híbrido inteligente
 */
export function calculateHybridLayout(
    nodes: PhoneNode[],
    containerWidth: number,
    containerHeight: number
): PhoneNode[] {
    const centerX = containerWidth / 2;
    const centerY = containerHeight / 2;
    
    // Separar nodos por importancia
    const targetNode = nodes.find(node => node.data.isTarget);
    const highTrafficNodes = nodes.filter(node => 
        !node.data.isTarget && node.data.interactionCount >= 5
    );
    const lowTrafficNodes = nodes.filter(node => 
        !node.data.isTarget && node.data.interactionCount < 5
    );
    
    const updatedNodes: PhoneNode[] = [];
    
    // Target al centro
    if (targetNode) {
        updatedNodes.push({
            ...targetNode,
            position: { x: centerX, y: centerY },
            style: {
                ...targetNode.style,
                width: LAYOUT_CONSTANTS.TARGET_NODE_SIZE,
                height: LAYOUT_CONSTANTS.TARGET_NODE_SIZE
            }
        });
    }
    
    // Nodos de alto tráfico en círculo interno
    if (highTrafficNodes.length > 0) {
        const innerRadius = 120;
        const angleStep = (2 * Math.PI) / highTrafficNodes.length;
        
        highTrafficNodes.forEach((node, index) => {
            const angle = index * angleStep;
            const x = centerX + innerRadius * Math.cos(angle);
            const y = centerY + innerRadius * Math.sin(angle);
            
            updatedNodes.push({
                ...node,
                position: { x, y },
                style: {
                    ...node.style,
                    width: LAYOUT_CONSTANTS.NORMAL_NODE_SIZE,
                    height: LAYOUT_CONSTANTS.NORMAL_NODE_SIZE
                }
            });
        });
    }
    
    // Nodos de bajo tráfico en círculo externo
    if (lowTrafficNodes.length > 0) {
        const outerRadius = 220;
        const angleStep = (2 * Math.PI) / lowTrafficNodes.length;
        
        lowTrafficNodes.forEach((node, index) => {
            const angle = index * angleStep;
            const x = centerX + outerRadius * Math.cos(angle);
            const y = centerY + outerRadius * Math.sin(angle);
            
            updatedNodes.push({
                ...node,
                position: { x, y },
                style: {
                    ...node.style,
                    width: LAYOUT_CONSTANTS.NORMAL_NODE_SIZE * 0.8,
                    height: LAYOUT_CONSTANTS.NORMAL_NODE_SIZE * 0.8
                }
            });
        });
    }
    
    return updatedNodes;
}

// ==================== FUNCIONES DE CONEXIONES ====================

/**
 * Calcula puntos de control para conexiones curvas
 */
export function calculateCurveControlPoints(
    startX: number,
    startY: number,
    endX: number,
    endY: number,
    curvature: number = 0.25
): { cp1x: number; cp1y: number; cp2x: number; cp2y: number } {
    const dx = endX - startX;
    const dy = endY - startY;
    
    // Calcular puntos de control para curva suave
    const cp1x = startX + dx * curvature;
    const cp1y = startY + dy * curvature + (dx * 0.1); // Ligera curvatura
    const cp2x = endX - dx * curvature;
    const cp2y = endY - dy * curvature - (dx * 0.1);
    
    return { cp1x, cp1y, cp2x, cp2y };
}

/**
 * Calcula el grosor de la conexión basado en la fuerza
 */
export function calculateConnectionWidth(strength: number): number {
    // Mapear fuerza (1-10) a grosor (2-8 pixels)
    return Math.max(2, Math.min(8, strength * 0.6 + 1.4));
}

// ==================== FUNCIONES DE UTILIDAD ====================

/**
 * Calcula dimensiones del contenedor basado en cantidad de nodos
 */
export function calculateContainerDimensions(
    nodeCount: number,
    availableWidth: number,
    availableHeight: number
): { width: number; height: number } {
    const { CONTAINER_PADDING, HEADER_HEIGHT, CONTROLS_HEIGHT } = LAYOUT_CONSTANTS;
    
    // Usar 90% del espacio disponible con padding
    const maxWidth = availableWidth * 0.9;
    const maxHeight = (availableHeight - HEADER_HEIGHT - CONTROLS_HEIGHT) * 0.9;
    
    // Calcular dimensiones mínimas basadas en contenido
    const minWidth = Math.max(400, nodeCount * 50);
    const minHeight = Math.max(300, nodeCount * 40);
    
    return {
        width: Math.min(maxWidth, Math.max(minWidth, 600)),
        height: Math.min(maxHeight, Math.max(minHeight, 400))
    };
}

/**
 * Verifica si dos nodos se superponen
 */
export function checkNodeOverlap(
    node1: PhoneNode,
    node2: PhoneNode,
    margin: number = 10
): boolean {
    const dx = Math.abs(node1.position.x - node2.position.x);
    const dy = Math.abs(node1.position.y - node2.position.y);
    
    const minDistance = (
        (node1.style?.width || LAYOUT_CONSTANTS.NORMAL_NODE_SIZE) + 
        (node2.style?.width || LAYOUT_CONSTANTS.NORMAL_NODE_SIZE)
    ) / 2 + margin;
    
    return Math.sqrt(dx * dx + dy * dy) < minDistance;
}

/**
 * Ajusta posiciones para evitar superposiciones
 */
export function resolveNodeOverlaps(nodes: PhoneNode[]): PhoneNode[] {
    const resolvedNodes = [...nodes];
    let iterations = 0;
    const maxIterations = 50;
    
    while (iterations < maxIterations) {
        let hasOverlap = false;
        
        for (let i = 0; i < resolvedNodes.length; i++) {
            for (let j = i + 1; j < resolvedNodes.length; j++) {
                if (checkNodeOverlap(resolvedNodes[i], resolvedNodes[j])) {
                    hasOverlap = true;
                    
                    // Separar nodos superpuestos
                    const dx = resolvedNodes[j].position.x - resolvedNodes[i].position.x;
                    const dy = resolvedNodes[j].position.y - resolvedNodes[i].position.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    
                    if (distance === 0) {
                        // Si están exactamente superpuestos, mover uno aleatoriamente
                        resolvedNodes[j].position.x += Math.random() * 40 - 20;
                        resolvedNodes[j].position.y += Math.random() * 40 - 20;
                    } else {
                        // Mover nodos en direcciones opuestas
                        const moveDistance = 30;
                        const unitX = dx / distance;
                        const unitY = dy / distance;
                        
                        resolvedNodes[i].position.x -= unitX * moveDistance;
                        resolvedNodes[i].position.y -= unitY * moveDistance;
                        resolvedNodes[j].position.x += unitX * moveDistance;
                        resolvedNodes[j].position.y += unitY * moveDistance;
                    }
                }
            }
        }
        
        if (!hasOverlap) break;
        iterations++;
    }
    
    return resolvedNodes;
}