/**
 * Hook para layout radial - Target al centro, otros en círculo
 * Boris & Claude Code - 2025-08-21
 */

import { useMemo } from 'react';
import { PhoneNode, RadialLayoutConfig } from '../types/correlation.types';
import { calculateRadialLayout, calculateOptimalRadius, LAYOUT_CONSTANTS } from '../utils/layoutCalculations';

interface UseRadialLayoutOptions {
    containerWidth: number;
    containerHeight: number;
    startAngle?: number;          // Ángulo inicial en radianes
    radiusMultiplier?: number;    // Multiplicador para el radio (0.5 - 2.0)
    centerOffset?: { x: number; y: number }; // Desplazamiento del centro
}

interface UseRadialLayoutResult {
    processedNodes: PhoneNode[];
    config: RadialLayoutConfig;
    radius: number;
    centerPoint: { x: number; y: number };
}

/**
 * Hook para calcular layout radial con target al centro
 */
export function useRadialLayout(
    nodes: PhoneNode[],
    options: UseRadialLayoutOptions
): UseRadialLayoutResult {
    
    return useMemo(() => {
        const {
            containerWidth,
            containerHeight,
            startAngle = 0,
            radiusMultiplier = 1.0,
            centerOffset = { x: 0, y: 0 }
        } = options;

        // Calcular centro del contenedor
        const baseCenterX = containerWidth / 2;
        const baseCenterY = containerHeight / 2;
        const centerX = baseCenterX + centerOffset.x;
        const centerY = baseCenterY + centerOffset.y;

        // Separar nodos target de los demás
        const targetNodes = nodes.filter(node => node.data.isTarget);
        const otherNodes = nodes.filter(node => !node.data.isTarget);

        // Calcular radio óptimo basado en cantidad de nodos
        const baseRadius = calculateOptimalRadius(otherNodes.length);
        const adjustedRadius = Math.max(
            LAYOUT_CONSTANTS.MIN_RADIUS,
            Math.min(
                LAYOUT_CONSTANTS.MAX_RADIUS,
                baseRadius * radiusMultiplier
            )
        );

        // Asegurar que el radio se adapte al contenedor
        const maxPossibleRadius = Math.min(
            (containerWidth - LAYOUT_CONSTANTS.CONTAINER_PADDING * 2) / 2,
            (containerHeight - LAYOUT_CONSTANTS.CONTAINER_PADDING * 2) / 2
        );
        const finalRadius = Math.min(adjustedRadius, maxPossibleRadius);

        // Configuración del layout radial
        const config: RadialLayoutConfig = {
            centerX,
            centerY,
            radius: finalRadius,
            startAngle,
            nodeSpacing: LAYOUT_CONSTANTS.NODE_SPACING
        };

        // Calcular posiciones de nodos
        let processedNodes: PhoneNode[] = [];

        // 1. Posicionar nodo(s) target al centro
        targetNodes.forEach(node => {
            processedNodes.push({
                ...node,
                type: 'radialTarget',
                position: { x: centerX, y: centerY },
                style: {
                    ...node.style,
                    width: LAYOUT_CONSTANTS.TARGET_NODE_SIZE,
                    height: LAYOUT_CONSTANTS.TARGET_NODE_SIZE,
                    zIndex: 100 // Target siempre al frente
                }
            });
        });

        // 2. Posicionar otros nodos en círculo
        if (otherNodes.length > 0) {
            const angleStep = (2 * Math.PI) / otherNodes.length;
            
            // Ordenar nodos por relevancia (cantidad de interacciones)
            const sortedOtherNodes = [...otherNodes].sort((a, b) => 
                b.data.interactionCount - a.data.interactionCount
            );

            sortedOtherNodes.forEach((node, index) => {
                const angle = startAngle + (index * angleStep);
                const x = centerX + finalRadius * Math.cos(angle);
                const y = centerY + finalRadius * Math.sin(angle);

                // Determinar tamaño basado en importancia
                const importance = node.data.interactionCount;
                let nodeSize = LAYOUT_CONSTANTS.NORMAL_NODE_SIZE;
                
                if (importance > 20) {
                    nodeSize = LAYOUT_CONSTANTS.NORMAL_NODE_SIZE * 1.2; // Nodos muy importantes
                } else if (importance > 10) {
                    nodeSize = LAYOUT_CONSTANTS.NORMAL_NODE_SIZE * 1.1; // Nodos importantes
                } else if (importance < 3) {
                    nodeSize = LAYOUT_CONSTANTS.NORMAL_NODE_SIZE * 0.8; // Nodos menos importantes
                }

                processedNodes.push({
                    ...node,
                    type: 'radialSource',
                    position: { x, y },
                    style: {
                        ...node.style,
                        width: nodeSize,
                        height: nodeSize,
                        zIndex: 50 - index // Nodos más importantes al frente
                    }
                });
            });
        }

        return {
            processedNodes,
            config,
            radius: finalRadius,
            centerPoint: { x: centerX, y: centerY }
        };

    }, [nodes, options]);
}

/**
 * Hook para calcular layout radial multinivel (anillos concéntricos)
 */
export function useMultiLevelRadialLayout(
    nodes: PhoneNode[],
    containerWidth: number,
    containerHeight: number,
    levels: number = 2
): UseRadialLayoutResult {
    
    return useMemo(() => {
        const centerX = containerWidth / 2;
        const centerY = containerHeight / 2;

        const targetNodes = nodes.filter(node => node.data.isTarget);
        const otherNodes = nodes.filter(node => !node.data.isTarget);

        // Separar nodos por importancia en niveles
        const nodesByLevel: PhoneNode[][] = Array(levels).fill(null).map(() => []);
        
        otherNodes.forEach(node => {
            const importance = node.data.interactionCount;
            let level = 0;
            
            if (importance > 15) {
                level = 0; // Anillo interno - muy importantes
            } else if (importance > 8) {
                level = Math.min(1, levels - 1); // Anillo medio
            } else {
                level = levels - 1; // Anillo externo - menos importantes
            }
            
            nodesByLevel[level].push(node);
        });

        let processedNodes: PhoneNode[] = [];

        // Posicionar target al centro
        targetNodes.forEach(node => {
            processedNodes.push({
                ...node,
                type: 'radialTarget',
                position: { x: centerX, y: centerY },
                style: {
                    ...node.style,
                    width: LAYOUT_CONSTANTS.TARGET_NODE_SIZE,
                    height: LAYOUT_CONSTANTS.TARGET_NODE_SIZE,
                    zIndex: 100
                }
            });
        });

        // Posicionar nodos en anillos concéntricos
        nodesByLevel.forEach((levelNodes, levelIndex) => {
            if (levelNodes.length === 0) return;

            const radius = LAYOUT_CONSTANTS.MIN_RADIUS + (levelIndex * 80);
            const angleStep = (2 * Math.PI) / levelNodes.length;

            levelNodes.forEach((node, nodeIndex) => {
                const angle = nodeIndex * angleStep;
                const x = centerX + radius * Math.cos(angle);
                const y = centerY + radius * Math.sin(angle);

                const nodeSize = LAYOUT_CONSTANTS.NORMAL_NODE_SIZE * (1 - levelIndex * 0.1);

                processedNodes.push({
                    ...node,
                    type: 'radialSource',
                    position: { x, y },
                    style: {
                        ...node.style,
                        width: nodeSize,
                        height: nodeSize,
                        zIndex: 50 - levelIndex * 10 - nodeIndex
                    }
                });
            });
        });

        const config: RadialLayoutConfig = {
            centerX,
            centerY,
            radius: LAYOUT_CONSTANTS.MIN_RADIUS + ((levels - 1) * 80),
            startAngle: 0,
            nodeSpacing: LAYOUT_CONSTANTS.NODE_SPACING
        };

        return {
            processedNodes,
            config,
            radius: config.radius,
            centerPoint: { x: centerX, y: centerY }
        };

    }, [nodes, containerWidth, containerHeight, levels]);
}

/**
 * Hook para optimizar el spacing radial basado en contenido
 */
export function useAdaptiveRadialSpacing(
    nodes: PhoneNode[],
    containerWidth: number,
    containerHeight: number
) {
    return useMemo(() => {
        const nodeCount = nodes.filter(node => !node.data.isTarget).length;
        
        // Calcular espaciado adaptativo
        const baseSpacing = LAYOUT_CONSTANTS.NODE_SPACING;
        let adaptiveSpacing = baseSpacing;
        
        if (nodeCount > 15) {
            // Muchos nodos - reducir espaciado
            adaptiveSpacing = baseSpacing * 0.7;
        } else if (nodeCount < 5) {
            // Pocos nodos - aumentar espaciado
            adaptiveSpacing = baseSpacing * 1.5;
        }

        // Calcular radio adaptativo
        const circumference = nodeCount * (LAYOUT_CONSTANTS.NORMAL_NODE_SIZE + adaptiveSpacing);
        const calculatedRadius = circumference / (2 * Math.PI);
        
        const minRadius = Math.min(containerWidth, containerHeight) * 0.2;
        const maxRadius = Math.min(containerWidth, containerHeight) * 0.4;
        
        const finalRadius = Math.max(minRadius, Math.min(maxRadius, calculatedRadius));

        return {
            radius: finalRadius,
            nodeSpacing: adaptiveSpacing,
            angleStep: (2 * Math.PI) / Math.max(nodeCount, 1)
        };
    }, [nodes, containerWidth, containerHeight]);
}