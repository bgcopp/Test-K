/**
 * Hook para layout lineal - Flujo temporal secuencial
 * Boris & Claude Code - 2025-08-21
 */

import { useMemo } from 'react';
import { PhoneNode, LinearLayoutConfig } from '../types/correlation.types';
import { LAYOUT_CONSTANTS } from '../utils/layoutCalculations';

interface UseLinearLayoutOptions {
    containerWidth: number;
    containerHeight: number;
    direction?: 'horizontal' | 'vertical';
    sortBy?: 'time' | 'importance' | 'alphabetical' | 'operator';
    timeBasedSpacing?: boolean;
    groupSimilar?: boolean;
    centerAlign?: boolean;
    nodeSpacing?: number;
}

interface UseLinearLayoutResult {
    processedNodes: PhoneNode[];
    config: LinearLayoutConfig;
    totalLength: number;
    nodeSpacing: number;
    timeline?: Array<{
        id: string;
        timestamp: number;
        position: { x: number; y: number };
        label: string;
    }>;
}

/**
 * Hook principal para layout lineal temporal
 */
export function useLinearLayout(
    nodes: PhoneNode[],
    options: UseLinearLayoutOptions
): UseLinearLayoutResult {
    
    return useMemo(() => {
        const {
            containerWidth,
            containerHeight,
            direction = 'horizontal',
            sortBy = 'time',
            timeBasedSpacing = true,
            groupSimilar = false,
            centerAlign = true,
            nodeSpacing = LAYOUT_CONSTANTS.NODE_SPACING
        } = options;

        if (nodes.length === 0) {
            return {
                processedNodes: [],
                config: {
                    startX: 0,
                    startY: 0,
                    direction,
                    nodeSpacing,
                    timeBasedSpacing
                },
                totalLength: 0,
                nodeSpacing,
                timeline: []
            };
        }

        // Ordenar nodos según criterio especificado
        let sortedNodes = [...nodes];
        
        switch (sortBy) {
            case 'time':
                sortedNodes.sort((a, b) => 
                    new Date(a.data.lastInteraction).getTime() - 
                    new Date(b.data.lastInteraction).getTime()
                );
                break;
            case 'importance':
                sortedNodes.sort((a, b) => 
                    b.data.interactionCount - a.data.interactionCount
                );
                break;
            case 'alphabetical':
                sortedNodes.sort((a, b) => 
                    a.data.number.localeCompare(b.data.number)
                );
                break;
            case 'operator':
                sortedNodes.sort((a, b) => {
                    const operatorCompare = a.data.operator.localeCompare(b.data.operator);
                    if (operatorCompare !== 0) return operatorCompare;
                    return b.data.interactionCount - a.data.interactionCount;
                });
                break;
        }

        // Si se agrupa por similitud, reorganizar
        if (groupSimilar && sortBy === 'operator') {
            const grouped = new Map<string, PhoneNode[]>();
            sortedNodes.forEach(node => {
                const key = node.data.operator;
                if (!grouped.has(key)) grouped.set(key, []);
                grouped.get(key)!.push(node);
            });
            sortedNodes = Array.from(grouped.values()).flat();
        }

        // Calcular espaciado
        const baseNodeSize = LAYOUT_CONSTANTS.LINEAR_NODE_SIZE;
        let actualSpacing = nodeSpacing;
        
        if (timeBasedSpacing && sortBy === 'time' && sortedNodes.length > 1) {
            // Espaciado proporcional al tiempo entre interacciones
            const timeSpacings = calculateTimeBasedSpacings(sortedNodes, direction, containerWidth, containerHeight);
            actualSpacing = Math.max(nodeSpacing, timeSpacings.averageSpacing);
        }

        // Calcular dimensiones totales necesarias
        const totalNodes = sortedNodes.length;
        const totalSpaceNeeded = (totalNodes - 1) * actualSpacing + totalNodes * baseNodeSize;
        
        // Calcular posición inicial
        let startX: number, startY: number;
        
        if (direction === 'horizontal') {
            startX = centerAlign 
                ? (containerWidth - totalSpaceNeeded) / 2 + baseNodeSize / 2
                : LAYOUT_CONSTANTS.CONTAINER_PADDING + baseNodeSize / 2;
            startY = containerHeight / 2;
        } else {
            startX = containerWidth / 2;
            startY = centerAlign 
                ? (containerHeight - totalSpaceNeeded) / 2 + baseNodeSize / 2
                : LAYOUT_CONSTANTS.CONTAINER_PADDING + baseNodeSize / 2;
        }

        // Configuración del layout
        const config: LinearLayoutConfig = {
            startX,
            startY,
            direction,
            nodeSpacing: actualSpacing,
            timeBasedSpacing
        };

        // Procesar nodos y calcular posiciones
        const processedNodes: PhoneNode[] = [];
        const timeline: Array<{
            id: string;
            timestamp: number;
            position: { x: number; y: number };
            label: string;
        }> = [];

        sortedNodes.forEach((node, index) => {
            let x = startX;
            let y = startY;

            if (direction === 'horizontal') {
                x = startX + index * (baseNodeSize + actualSpacing);
            } else {
                y = startY + index * (baseNodeSize + actualSpacing);
            }

            // Ajustar tamaño según importancia
            let nodeSize = baseNodeSize;
            if (node.data.isTarget) {
                nodeSize = baseNodeSize * 1.4; // Target más grande
            } else if (node.data.interactionCount > 10) {
                nodeSize = baseNodeSize * 1.2; // Nodos importantes
            } else if (node.data.interactionCount < 3) {
                nodeSize = baseNodeSize * 0.8; // Nodos menos importantes
            }

            processedNodes.push({
                ...node,
                type: 'linearFlow',
                position: { x: x - nodeSize / 2, y: y - nodeSize / 2 },
                style: {
                    ...node.style,
                    width: nodeSize,
                    height: nodeSize,
                    borderRadius: '8px', // Nodos rectangulares redondeados para flujo
                    zIndex: node.data.isTarget ? 100 : 50
                }
            });

            // Agregar a timeline si es ordenamiento temporal
            if (sortBy === 'time') {
                timeline.push({
                    id: node.id,
                    timestamp: new Date(node.data.lastInteraction).getTime(),
                    position: { x, y },
                    label: formatTimeLabel(node.data.lastInteraction)
                });
            }
        });

        return {
            processedNodes,
            config,
            totalLength: totalSpaceNeeded,
            nodeSpacing: actualSpacing,
            timeline: sortBy === 'time' ? timeline : undefined
        };

    }, [nodes, options]);
}

/**
 * Hook para layout lineal con cronología detallada
 */
export function useTimelineLayout(
    nodes: PhoneNode[],
    containerWidth: number,
    containerHeight: number,
    showTimeMarkers: boolean = true
): UseLinearLayoutResult {
    
    return useMemo(() => {
        if (nodes.length === 0) {
            return {
                processedNodes: [],
                config: {
                    startX: 0,
                    startY: 0,
                    direction: 'horizontal',
                    nodeSpacing: LAYOUT_CONSTANTS.NODE_SPACING,
                    timeBasedSpacing: true
                },
                totalLength: 0,
                nodeSpacing: LAYOUT_CONSTANTS.NODE_SPACING,
                timeline: []
            };
        }

        // Ordenar por tiempo
        const sortedNodes = [...nodes].sort((a, b) => 
            new Date(a.data.lastInteraction).getTime() - 
            new Date(b.data.lastInteraction).getTime()
        );

        // Calcular espaciado temporal proporcional
        const timeRange = getTimeRange(sortedNodes);
        const availableWidth = containerWidth - (2 * LAYOUT_CONSTANTS.CONTAINER_PADDING);
        
        const processedNodes: PhoneNode[] = [];
        const timeline: Array<{
            id: string;
            timestamp: number;
            position: { x: number; y: number };
            label: string;
        }> = [];

        const startX = LAYOUT_CONSTANTS.CONTAINER_PADDING;
        const startY = containerHeight / 2;

        sortedNodes.forEach((node, index) => {
            const timestamp = new Date(node.data.lastInteraction).getTime();
            const timeProgress = timeRange.duration > 0 
                ? (timestamp - timeRange.start) / timeRange.duration 
                : index / (sortedNodes.length - 1);
            
            const x = startX + (timeProgress * availableWidth);
            const nodeSize = node.data.isTarget 
                ? LAYOUT_CONSTANTS.LINEAR_NODE_SIZE * 1.4 
                : LAYOUT_CONSTANTS.LINEAR_NODE_SIZE;

            processedNodes.push({
                ...node,
                type: 'linearFlow',
                position: { x: x - nodeSize / 2, y: startY - nodeSize / 2 },
                style: {
                    ...node.style,
                    width: nodeSize,
                    height: nodeSize,
                    borderRadius: '8px',
                    zIndex: node.data.isTarget ? 100 : 50
                }
            });

            timeline.push({
                id: node.id,
                timestamp,
                position: { x, y: startY },
                label: formatTimeLabel(node.data.lastInteraction)
            });
        });

        return {
            processedNodes,
            config: {
                startX,
                startY,
                direction: 'horizontal',
                nodeSpacing: 0, // No aplica en timeline
                timeBasedSpacing: true
            },
            totalLength: availableWidth,
            nodeSpacing: 0,
            timeline
        };

    }, [nodes, containerWidth, containerHeight, showTimeMarkers]);
}

/**
 * Hook para layout lineal agrupado por categorías
 */
export function useCategorizedLinearLayout(
    nodes: PhoneNode[],
    containerWidth: number,
    containerHeight: number,
    groupBy: 'operator' | 'importance' = 'operator'
): UseLinearLayoutResult {
    
    return useMemo(() => {
        // Agrupar nodos
        const groups = new Map<string, PhoneNode[]>();
        
        nodes.forEach(node => {
            let key: string;
            if (groupBy === 'operator') {
                key = node.data.operator;
            } else {
                // Agrupar por importancia
                const importance = node.data.interactionCount;
                if (importance > 15) key = 'Alto';
                else if (importance > 5) key = 'Medio';
                else key = 'Bajo';
            }
            
            if (!groups.has(key)) groups.set(key, []);
            groups.get(key)!.push(node);
        });

        const processedNodes: PhoneNode[] = [];
        const groupPositions: Array<{ group: string; startY: number; endY: number }> = [];
        
        const availableHeight = containerHeight - (2 * LAYOUT_CONSTANTS.CONTAINER_PADDING);
        const groupHeight = availableHeight / groups.size;
        const nodeSpacing = LAYOUT_CONSTANTS.NODE_SPACING;
        
        let currentY = LAYOUT_CONSTANTS.CONTAINER_PADDING;

        Array.from(groups.entries()).forEach(([groupName, groupNodes], groupIndex) => {
            const groupStartY = currentY;
            const groupCenterY = currentY + groupHeight / 2;
            
            // Ordenar nodos del grupo por importancia
            const sortedGroupNodes = [...groupNodes].sort((a, b) => 
                b.data.interactionCount - a.data.interactionCount
            );

            // Calcular espaciado horizontal para el grupo
            const totalGroupWidth = sortedGroupNodes.length * (LAYOUT_CONSTANTS.LINEAR_NODE_SIZE + nodeSpacing);
            const groupStartX = (containerWidth - totalGroupWidth) / 2;

            sortedGroupNodes.forEach((node, nodeIndex) => {
                const x = groupStartX + nodeIndex * (LAYOUT_CONSTANTS.LINEAR_NODE_SIZE + nodeSpacing);
                const nodeSize = node.data.isTarget 
                    ? LAYOUT_CONSTANTS.LINEAR_NODE_SIZE * 1.3 
                    : LAYOUT_CONSTANTS.LINEAR_NODE_SIZE;

                processedNodes.push({
                    ...node,
                    type: 'linearFlow',
                    position: { x, y: groupCenterY - nodeSize / 2 },
                    style: {
                        ...node.style,
                        width: nodeSize,
                        height: nodeSize,
                        borderRadius: '8px',
                        zIndex: node.data.isTarget ? 100 : 50
                    }
                });
            });

            groupPositions.push({
                group: groupName,
                startY: groupStartY,
                endY: currentY + groupHeight
            });

            currentY += groupHeight;
        });

        return {
            processedNodes,
            config: {
                startX: LAYOUT_CONSTANTS.CONTAINER_PADDING,
                startY: LAYOUT_CONSTANTS.CONTAINER_PADDING,
                direction: 'horizontal',
                nodeSpacing,
                timeBasedSpacing: false
            },
            totalLength: containerWidth,
            nodeSpacing
        };

    }, [nodes, containerWidth, containerHeight, groupBy]);
}

// ==================== FUNCIONES AUXILIARES ====================

/**
 * Calcula espaciado basado en tiempo entre interacciones
 */
function calculateTimeBasedSpacings(
    nodes: PhoneNode[],
    direction: 'horizontal' | 'vertical',
    containerWidth: number,
    containerHeight: number
) {
    const timestamps = nodes.map(node => new Date(node.data.lastInteraction).getTime());
    const timeDiffs = timestamps.slice(1).map((time, index) => time - timestamps[index]);
    
    const maxDiff = Math.max(...timeDiffs);
    const minDiff = Math.min(...timeDiffs);
    
    const maxContainer = direction === 'horizontal' ? containerWidth : containerHeight;
    const availableSpace = maxContainer - (2 * LAYOUT_CONSTANTS.CONTAINER_PADDING);
    
    const maxSpacing = Math.min(100, availableSpace / nodes.length);
    const minSpacing = LAYOUT_CONSTANTS.NODE_SPACING;
    
    const averageSpacing = timeDiffs.length > 0
        ? timeDiffs.reduce((sum, diff) => {
            const normalized = (diff - minDiff) / (maxDiff - minDiff);
            return sum + (minSpacing + normalized * (maxSpacing - minSpacing));
        }, 0) / timeDiffs.length
        : LAYOUT_CONSTANTS.NODE_SPACING;

    return {
        averageSpacing: Math.max(minSpacing, Math.min(maxSpacing, averageSpacing)),
        maxSpacing,
        minSpacing
    };
}

/**
 * Obtiene rango temporal de los nodos
 */
function getTimeRange(nodes: PhoneNode[]) {
    const timestamps = nodes.map(node => new Date(node.data.lastInteraction).getTime());
    const start = Math.min(...timestamps);
    const end = Math.max(...timestamps);
    
    return {
        start,
        end,
        duration: end - start
    };
}

/**
 * Formatea etiqueta de tiempo para el timeline
 */
function formatTimeLabel(dateStr: string): string {
    try {
        const date = new Date(dateStr);
        const now = new Date();
        const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) {
            return date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
        } else if (diffDays < 7) {
            return `${diffDays}d`;
        } else if (diffDays < 30) {
            return `${Math.floor(diffDays / 7)}sem`;
        } else {
            return date.toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit' });
        }
    } catch {
        return dateStr;
    }
}