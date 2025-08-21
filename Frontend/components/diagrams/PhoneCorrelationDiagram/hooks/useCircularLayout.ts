/**
 * Hook para layout circular - Todos los nodos en círculo con avatares
 * Boris & Claude Code - 2025-08-21
 */

import { useMemo } from 'react';
import { PhoneNode, CircularLayoutConfig } from '../types/correlation.types';
import { LAYOUT_CONSTANTS } from '../utils/layoutCalculations';

interface UseCircularLayoutOptions {
    containerWidth: number;
    containerHeight: number;
    startAngle?: number;              // Ángulo inicial en radianes
    radiusMultiplier?: number;        // Multiplicador para el radio
    equalSpacing?: boolean;           // Espaciado igual vs. basado en importancia
    targetHighlight?: boolean;        // Destacar nodo target con mayor tamaño
    centerOffset?: { x: number; y: number }; // Desplazamiento del centro
}

interface UseCircularLayoutResult {
    processedNodes: PhoneNode[];
    config: CircularLayoutConfig;
    radius: number;
    centerPoint: { x: number; y: number };
    nodePositions: Array<{
        id: string;
        angle: number;
        importance: number;
        position: { x: number; y: number };
    }>;
}

/**
 * Hook principal para layout circular con avatares
 */
export function useCircularLayout(
    nodes: PhoneNode[],
    options: UseCircularLayoutOptions
): UseCircularLayoutResult {
    
    return useMemo(() => {
        const {
            containerWidth,
            containerHeight,
            startAngle = -Math.PI / 2, // Empezar arriba
            radiusMultiplier = 1.0,
            equalSpacing = true,
            targetHighlight = true,
            centerOffset = { x: 0, y: 0 }
        } = options;

        if (nodes.length === 0) {
            return {
                processedNodes: [],
                config: {
                    centerX: containerWidth / 2,
                    centerY: containerHeight / 2,
                    radius: LAYOUT_CONSTANTS.MIN_RADIUS,
                    nodeSize: LAYOUT_CONSTANTS.AVATAR_NODE_SIZE,
                    avatarSpacing: LAYOUT_CONSTANTS.NODE_SPACING
                },
                radius: LAYOUT_CONSTANTS.MIN_RADIUS,
                centerPoint: { x: containerWidth / 2, y: containerHeight / 2 },
                nodePositions: []
            };
        }

        // Calcular centro del contenedor
        const baseCenterX = containerWidth / 2;
        const baseCenterY = containerHeight / 2;
        const centerX = baseCenterX + centerOffset.x;
        const centerY = baseCenterY + centerOffset.y;

        // Calcular radio óptimo basado en cantidad de nodos y tamaño del contenedor
        const nodeSize = LAYOUT_CONSTANTS.AVATAR_NODE_SIZE;
        const spacing = LAYOUT_CONSTANTS.NODE_SPACING;
        
        // Circunferencia necesaria para acomodar todos los nodos
        const totalCircumference = nodes.length * (nodeSize + spacing);
        const calculatedRadius = totalCircumference / (2 * Math.PI);
        
        // Límites del contenedor
        const maxRadius = Math.min(
            (containerWidth - LAYOUT_CONSTANTS.CONTAINER_PADDING * 2 - nodeSize) / 2,
            (containerHeight - LAYOUT_CONSTANTS.CONTAINER_PADDING * 2 - nodeSize) / 2
        );
        
        const finalRadius = Math.min(
            maxRadius,
            Math.max(LAYOUT_CONSTANTS.MIN_RADIUS, calculatedRadius * radiusMultiplier)
        );

        // Configuración del layout
        const config: CircularLayoutConfig = {
            centerX,
            centerY,
            radius: finalRadius,
            nodeSize,
            avatarSpacing: spacing
        };

        // Ordenar nodos por importancia si no se usa espaciado igual
        let orderedNodes = [...nodes];
        if (!equalSpacing) {
            // Ordenar por: target primero, luego por cantidad de interacciones
            orderedNodes.sort((a, b) => {
                if (a.data.isTarget && !b.data.isTarget) return -1;
                if (!a.data.isTarget && b.data.isTarget) return 1;
                return b.data.interactionCount - a.data.interactionCount;
            });
        } else {
            // Para espaciado igual, target al inicio
            const targetNodes = nodes.filter(node => node.data.isTarget);
            const otherNodes = nodes.filter(node => !node.data.isTarget);
            orderedNodes = [...targetNodes, ...otherNodes];
        }

        // Calcular posiciones y crear nodos procesados
        const processedNodes: PhoneNode[] = [];
        const nodePositions: Array<{
            id: string;
            angle: number;
            importance: number;
            position: { x: number; y: number };
        }> = [];

        const angleStep = (2 * Math.PI) / nodes.length;

        orderedNodes.forEach((node, index) => {
            const angle = startAngle + (index * angleStep);
            const x = centerX + finalRadius * Math.cos(angle);
            const y = centerY + finalRadius * Math.sin(angle);

            // Determinar tamaño del nodo
            let currentNodeSize = nodeSize;
            if (targetHighlight && node.data.isTarget) {
                currentNodeSize = nodeSize * 1.3; // Target más grande
            } else if (!equalSpacing) {
                // Tamaño basado en importancia
                const importance = node.data.interactionCount;
                if (importance > 15) {
                    currentNodeSize = nodeSize * 1.1;
                } else if (importance < 3) {
                    currentNodeSize = nodeSize * 0.9;
                }
            }

            // Crear nodo procesado
            processedNodes.push({
                ...node,
                type: 'circularAvatar',
                position: { x, y },
                style: {
                    ...node.style,
                    width: currentNodeSize,
                    height: currentNodeSize,
                    borderRadius: '50%',
                    zIndex: node.data.isTarget ? 100 : 50
                }
            });

            // Guardar información de posición
            nodePositions.push({
                id: node.id,
                angle,
                importance: node.data.interactionCount,
                position: { x, y }
            });
        });

        return {
            processedNodes,
            config,
            radius: finalRadius,
            centerPoint: { x: centerX, y: centerY },
            nodePositions
        };

    }, [nodes, options]);
}

/**
 * Hook para layout circular con agrupación por operador
 */
export function useCircularGroupedLayout(
    nodes: PhoneNode[],
    containerWidth: number,
    containerHeight: number,
    groupByOperator: boolean = true
): UseCircularLayoutResult {
    
    return useMemo(() => {
        const centerX = containerWidth / 2;
        const centerY = containerHeight / 2;

        if (!groupByOperator) {
            // Fallback al layout circular normal
            return useCircularLayout(nodes, {
                containerWidth,
                containerHeight,
                equalSpacing: true
            });
        }

        // Agrupar nodos por operador
        const nodesByOperator = new Map<string, PhoneNode[]>();
        nodes.forEach(node => {
            const operator = node.data.operator;
            if (!nodesByOperator.has(operator)) {
                nodesByOperator.set(operator, []);
            }
            nodesByOperator.get(operator)!.push(node);
        });

        const groups = Array.from(nodesByOperator.entries());
        const processedNodes: PhoneNode[] = [];
        const nodePositions: Array<{
            id: string;
            angle: number;
            importance: number;
            position: { x: number; y: number };
        }> = [];

        // Calcular radio base
        const nodeSize = LAYOUT_CONSTANTS.AVATAR_NODE_SIZE;
        const totalCircumference = nodes.length * (nodeSize + LAYOUT_CONSTANTS.NODE_SPACING);
        const radius = Math.max(
            LAYOUT_CONSTANTS.MIN_RADIUS,
            totalCircumference / (2 * Math.PI)
        );

        // Distribuir grupos por sectores
        const totalAngle = 2 * Math.PI;
        let currentAngle = -Math.PI / 2; // Empezar arriba

        groups.forEach(([operator, groupNodes]) => {
            const groupSize = groupNodes.length;
            const groupAngleSpan = (groupSize / nodes.length) * totalAngle;
            const nodeAngleStep = groupAngleSpan / groupSize;
            
            // Ordenar nodos del grupo (target primero)
            const sortedGroupNodes = [...groupNodes].sort((a, b) => {
                if (a.data.isTarget && !b.data.isTarget) return -1;
                if (!a.data.isTarget && b.data.isTarget) return 1;
                return b.data.interactionCount - a.data.interactionCount;
            });

            sortedGroupNodes.forEach((node, nodeIndex) => {
                const angle = currentAngle + (nodeIndex * nodeAngleStep);
                const x = centerX + radius * Math.cos(angle);
                const y = centerY + radius * Math.sin(angle);

                const currentNodeSize = node.data.isTarget ? nodeSize * 1.3 : nodeSize;

                processedNodes.push({
                    ...node,
                    type: 'circularAvatar',
                    position: { x, y },
                    style: {
                        ...node.style,
                        width: currentNodeSize,
                        height: currentNodeSize,
                        borderRadius: '50%',
                        zIndex: node.data.isTarget ? 100 : 50
                    }
                });

                nodePositions.push({
                    id: node.id,
                    angle,
                    importance: node.data.interactionCount,
                    position: { x, y }
                });
            });

            currentAngle += groupAngleSpan;
        });

        const config: CircularLayoutConfig = {
            centerX,
            centerY,
            radius,
            nodeSize,
            avatarSpacing: LAYOUT_CONSTANTS.NODE_SPACING
        };

        return {
            processedNodes,
            config,
            radius,
            centerPoint: { x: centerX, y: centerY },
            nodePositions
        };

    }, [nodes, containerWidth, containerHeight, groupByOperator]);
}

/**
 * Hook para layout circular dinámico que se adapta al zoom
 */
export function useDynamicCircularLayout(
    nodes: PhoneNode[],
    containerWidth: number,
    containerHeight: number,
    zoomLevel: number = 1
): UseCircularLayoutResult {
    
    return useMemo(() => {
        const baseOptions: UseCircularLayoutOptions = {
            containerWidth,
            containerHeight,
            radiusMultiplier: zoomLevel,
            equalSpacing: true,
            targetHighlight: true
        };

        // Ajustar espaciado basado en zoom
        if (zoomLevel > 1.5) {
            // Zoom alto - más detalles
            baseOptions.equalSpacing = false;
        } else if (zoomLevel < 0.7) {
            // Zoom bajo - simplificar
            baseOptions.targetHighlight = false;
        }

        return useCircularLayout(nodes, baseOptions);

    }, [nodes, containerWidth, containerHeight, zoomLevel]);
}

/**
 * Hook para calcular posiciones de etiquetas en layout circular
 */
export function useCircularLabels(
    nodePositions: Array<{
        id: string;
        angle: number;
        importance: number;
        position: { x: number; y: number };
    }>,
    centerX: number,
    centerY: number,
    radius: number
) {
    return useMemo(() => {
        return nodePositions.map(nodePos => {
            const { angle, id, position } = nodePos;
            
            // Calcular posición de etiqueta (fuera del círculo)
            const labelRadius = radius + 30;
            const labelX = centerX + labelRadius * Math.cos(angle);
            const labelY = centerY + labelRadius * Math.sin(angle);
            
            // Determinar alineación del texto basada en posición
            let textAlign: 'left' | 'center' | 'right' = 'center';
            if (labelX < centerX - 20) {
                textAlign = 'right';
            } else if (labelX > centerX + 20) {
                textAlign = 'left';
            }

            return {
                id,
                position: { x: labelX, y: labelY },
                textAlign,
                angle: angle * (180 / Math.PI), // Convertir a grados
                isOnRightSide: labelX > centerX
            };
        });
    }, [nodePositions, centerX, centerY, radius]);
}