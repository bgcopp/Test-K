/**
 * Hook para detección inteligente del mejor modo de visualización
 * Boris & Claude Code - 2025-08-21
 */

import { useMemo } from 'react';
import { CallInteraction, VisualizationMode, PhoneNode } from '../types/correlation.types';

interface SmartModeAnalysis {
    recommendedMode: VisualizationMode;
    confidence: number; // 0-100
    reasoning: string;
    alternatives: Array<{
        mode: VisualizationMode;
        score: number;
        reason: string;
    }>;
    dataCharacteristics: {
        nodeCount: number;
        connectionDensity: number;
        timeSpread: number; // en días
        operatorDiversity: number;
        targetCentrality: number; // qué tan central es el target
    };
}

interface UseSmartModeDetectionOptions {
    containerWidth: number;
    containerHeight: number;
    prioritizeReadability?: boolean;
    considerPerformance?: boolean;
    userPreference?: VisualizationMode | null;
}

/**
 * Hook principal para detección inteligente de modo
 */
export function useSmartModeDetection(
    interactions: CallInteraction[],
    targetNumber: string,
    nodes: PhoneNode[],
    options: UseSmartModeDetectionOptions
): SmartModeAnalysis {
    
    return useMemo(() => {
        const {
            containerWidth,
            containerHeight,
            prioritizeReadability = true,
            considerPerformance = true,
            userPreference = null
        } = options;

        // Si hay preferencia del usuario, respetarla con alta confianza
        if (userPreference) {
            return {
                recommendedMode: userPreference,
                confidence: 95,
                reasoning: `Modo seleccionado manualmente por el usuario: ${getModeDisplayName(userPreference)}`,
                alternatives: [],
                dataCharacteristics: analyzeDataCharacteristics(interactions, targetNumber, nodes)
            };
        }

        const characteristics = analyzeDataCharacteristics(interactions, targetNumber, nodes);
        const modeScores = calculateModeScores(characteristics, containerWidth, containerHeight, prioritizeReadability, considerPerformance);
        
        // Ordenar por puntuación
        const sortedModes = modeScores.sort((a, b) => b.score - a.score);
        const recommended = sortedModes[0];
        const alternatives = sortedModes.slice(1, 4); // Top 3 alternativas

        return {
            recommendedMode: recommended.mode,
            confidence: Math.round(recommended.score),
            reasoning: recommended.reason,
            alternatives,
            dataCharacteristics: characteristics
        };

    }, [interactions, targetNumber, nodes, options]);
}

/**
 * Hook para recomendaciones adaptativas basadas en interacción del usuario
 */
export function useAdaptiveModeRecommendation(
    currentMode: VisualizationMode,
    userInteractions: {
        zoomCount: number;
        panCount: number;
        nodeClickCount: number;
        timeSpentSeconds: number;
    },
    dataCharacteristics: SmartModeAnalysis['dataCharacteristics']
) {
    return useMemo(() => {
        const { zoomCount, panCount, nodeClickCount, timeSpentSeconds } = userInteractions;
        const { nodeCount, connectionDensity } = dataCharacteristics;

        // Analizar patrones de uso
        const suggestions: Array<{
            mode: VisualizationMode;
            reason: string;
            priority: 'high' | 'medium' | 'low';
        }> = [];

        // Si hay mucho zoom, posiblemente necesite mejor layout
        if (zoomCount > 5 && timeSpentSeconds > 30) {
            if (currentMode === 'circular' && nodeCount > 12) {
                suggestions.push({
                    mode: 'radial',
                    reason: 'Mucho zoom detectado. El modo radial podría ofrecer mejor visibilidad del target central.',
                    priority: 'high'
                });
            } else if (currentMode === 'radial' && connectionDensity > 0.7) {
                suggestions.push({
                    mode: 'linear',
                    reason: 'Alta densidad de conexiones detectada. El modo lineal podría reducir la superposición.',
                    priority: 'medium'
                });
            }
        }

        // Si hay mucho pan (desplazamiento), el contenido no cabe bien
        if (panCount > 8) {
            if (currentMode !== 'hybrid') {
                suggestions.push({
                    mode: 'hybrid',
                    reason: 'Mucho desplazamiento detectado. El modo híbrido optimiza el uso del espacio disponible.',
                    priority: 'high'
                });
            }
        }

        // Si hace muchos clicks en nodos, está explorando conexiones
        if (nodeClickCount > 5 && currentMode !== 'radial') {
            suggestions.push({
                mode: 'radial',
                reason: 'Alta exploración de nodos detectada. El modo radial facilita ver las conexiones del target.',
                priority: 'medium'
            });
        }

        // Si pasa mucho tiempo sin interactuar, tal vez el layout no es intuitivo
        if (timeSpentSeconds > 120 && userInteractions.nodeClickCount < 2) {
            suggestions.push({
                mode: 'circular',
                reason: 'El modo circular podría ser más intuitivo para una exploración inicial.',
                priority: 'low'
            });
        }

        return suggestions.filter(s => s.mode !== currentMode);

    }, [currentMode, userInteractions, dataCharacteristics]);
}

// ==================== FUNCIONES AUXILIARES ====================

/**
 * Analiza las características de los datos para determinar el mejor modo
 */
function analyzeDataCharacteristics(
    interactions: CallInteraction[],
    targetNumber: string,
    nodes: PhoneNode[]
): SmartModeAnalysis['dataCharacteristics'] {
    const nodeCount = nodes.length;
    
    // Calcular densidad de conexiones
    const maxPossibleConnections = (nodeCount * (nodeCount - 1)) / 2;
    const actualConnections = countUniqueConnections(interactions);
    const connectionDensity = maxPossibleConnections > 0 ? actualConnections / maxPossibleConnections : 0;
    
    // Calcular spread temporal
    const timestamps = interactions.map(int => new Date(int.fecha_hora).getTime());
    const timeSpread = timestamps.length > 0 
        ? (Math.max(...timestamps) - Math.min(...timestamps)) / (1000 * 60 * 60 * 24) // días
        : 0;
    
    // Diversidad de operadores
    const uniqueOperators = new Set(interactions.map(int => int.operador)).size;
    const operatorDiversity = uniqueOperators / Math.max(nodeCount, 1);
    
    // Centralidad del target (qué porcentaje de interacciones involucra al target)
    const targetInteractions = interactions.filter(int => 
        int.originador === targetNumber || int.receptor === targetNumber
    ).length;
    const targetCentrality = interactions.length > 0 ? targetInteractions / interactions.length : 0;

    return {
        nodeCount,
        connectionDensity,
        timeSpread,
        operatorDiversity,
        targetCentrality
    };
}

/**
 * Calcula puntuaciones para cada modo de visualización
 */
function calculateModeScores(
    characteristics: SmartModeAnalysis['dataCharacteristics'],
    containerWidth: number,
    containerHeight: number,
    prioritizeReadability: boolean,
    considerPerformance: boolean
): Array<{ mode: VisualizationMode; score: number; reason: string }> {
    const { nodeCount, connectionDensity, timeSpread, operatorDiversity, targetCentrality } = characteristics;
    
    const scores: Array<{ mode: VisualizationMode; score: number; reason: string }> = [];

    // ========== MODO RADIAL ==========
    let radialScore = 50; // Base score
    let radialReason = '';

    // Muy bueno para targets centrales
    if (targetCentrality > 0.6) {
        radialScore += 25;
        radialReason += 'Target muy central. ';
    }

    // Bueno para cantidades medias de nodos
    if (nodeCount >= 4 && nodeCount <= 12) {
        radialScore += 20;
        radialReason += 'Cantidad óptima de nodos. ';
    } else if (nodeCount > 12) {
        radialScore -= 10; // Penalizar muchos nodos
        radialReason += 'Muchos nodos pueden crear superposición. ';
    }

    // Penalizar alta densidad de conexiones
    if (connectionDensity > 0.7) {
        radialScore -= 15;
        radialReason += 'Alta densidad puede crear confusión visual. ';
    }

    scores.push({
        mode: 'radial',
        score: Math.max(0, Math.min(100, radialScore)),
        reason: radialReason || 'Modo radial estándar con target central.'
    });

    // ========== MODO CIRCULAR ==========
    let circularScore = 50;
    let circularReason = '';

    // Excelente para muchos nodos
    if (nodeCount > 8) {
        circularScore += 20;
        circularReason += 'Maneja bien muchos nodos. ';
    }

    // Bueno para alta diversidad de operadores
    if (operatorDiversity > 0.4) {
        circularScore += 15;
        circularReason += 'Facilita agrupación por operador. ';
    }

    // Bueno para baja centralidad del target
    if (targetCentrality < 0.4) {
        circularScore += 10;
        circularReason += 'Target no dominante, vista equilibrada. ';
    }

    // Beneficio para contenedores anchos
    if (containerWidth > containerHeight * 1.2) {
        circularScore += 10;
        circularReason += 'Aprovecha bien el espacio horizontal. ';
    }

    scores.push({
        mode: 'circular',
        score: Math.max(0, Math.min(100, circularScore)),
        reason: circularReason || 'Modo circular equilibrado para múltiples nodos.'
    });

    // ========== MODO LINEAL ==========
    let linearScore = 50;
    let linearReason = '';

    // Excelente para análisis temporal
    if (timeSpread > 7) { // Más de una semana
        linearScore += 25;
        linearReason += 'Amplio rango temporal ideal para cronología. ';
    }

    // Muy bueno para pocos nodos
    if (nodeCount <= 6) {
        linearScore += 20;
        linearReason += 'Pocos nodos, secuencia clara. ';
    }

    // Bueno para baja densidad de conexiones
    if (connectionDensity < 0.3) {
        linearScore += 15;
        linearReason += 'Pocas conexiones, secuencia limpia. ';
    }

    // Beneficio para contenedores largos
    if (containerWidth > containerHeight * 2) {
        linearScore += 10;
        linearReason += 'Formato panorámico ideal. ';
    }

    // Penalizar muchos nodos
    if (nodeCount > 10) {
        linearScore -= 20;
        linearReason += 'Demasiados nodos para secuencia lineal. ';
    }

    scores.push({
        mode: 'linear',
        score: Math.max(0, Math.min(100, linearScore)),
        reason: linearReason || 'Modo lineal para análisis secuencial.'
    });

    // ========== MODO HÍBRIDO ==========
    let hybridScore = 60; // Ligeramente mejor base
    let hybridReason = '';

    // Excelente para casos complejos
    if (nodeCount > 15) {
        hybridScore += 20;
        hybridReason += 'Muchos nodos requieren organización inteligente. ';
    }

    if (connectionDensity > 0.6) {
        hybridScore += 15;
        hybridReason += 'Alta densidad necesita agrupación por niveles. ';
    }

    // Bueno para contenedores pequeños
    if (containerWidth < 800 || containerHeight < 600) {
        hybridScore += 10;
        hybridReason += 'Optimiza espacio limitado. ';
    }

    // Beneficio para consideraciones de performance
    if (considerPerformance && nodeCount > 20) {
        hybridScore += 15;
        hybridReason += 'Optimizado para performance con muchos elementos. ';
    }

    scores.push({
        mode: 'hybrid',
        score: Math.max(0, Math.min(100, hybridScore)),
        reason: hybridReason || 'Modo híbrido inteligente para casos complejos.'
    });

    // Ajustes por prioridades
    if (prioritizeReadability) {
        // Boost modos más legibles
        scores.forEach(score => {
            if (score.mode === 'radial' || score.mode === 'linear') {
                score.score += 5;
            }
        });
    }

    if (considerPerformance) {
        // Penalizar modos costosos para muchos nodos
        scores.forEach(score => {
            if (nodeCount > 25 && (score.mode === 'circular' || score.mode === 'radial')) {
                score.score -= 10;
            }
        });
    }

    return scores;
}

/**
 * Cuenta conexiones únicas entre números
 */
function countUniqueConnections(interactions: CallInteraction[]): number {
    const connections = new Set<string>();
    
    interactions.forEach(int => {
        const connection = int.originador < int.receptor 
            ? `${int.originador}-${int.receptor}`
            : `${int.receptor}-${int.originador}`;
        connections.add(connection);
    });
    
    return connections.size;
}

/**
 * Obtiene nombre de display para el modo
 */
function getModeDisplayName(mode: VisualizationMode): string {
    const names = {
        radial: 'Radial Central',
        circular: 'Circular con Avatares',
        linear: 'Flujo Lineal',
        hybrid: 'Híbrido Inteligente'
    };
    return names[mode];
}

/**
 * Hook para validar si un modo es viable con los datos actuales
 */
export function useModeViability(
    mode: VisualizationMode,
    nodes: PhoneNode[],
    containerWidth: number,
    containerHeight: number
) {
    return useMemo(() => {
        const nodeCount = nodes.length;
        const issues: string[] = [];
        let viable = true;

        switch (mode) {
            case 'radial':
                if (nodeCount > 20) {
                    issues.push('Demasiados nodos para layout radial legible');
                    viable = false;
                }
                if (containerWidth < 400 || containerHeight < 400) {
                    issues.push('Contenedor muy pequeño para layout radial');
                }
                break;

            case 'circular':
                if (nodeCount > 30) {
                    issues.push('Demasiados nodos para layout circular');
                    viable = false;
                }
                break;

            case 'linear':
                if (nodeCount > 15) {
                    issues.push('Demasiados nodos para secuencia lineal clara');
                    viable = false;
                }
                const maxLinearLength = Math.max(containerWidth, containerHeight);
                const requiredLength = nodeCount * 80; // Estimación
                if (requiredLength > maxLinearLength) {
                    issues.push('No hay suficiente espacio para layout lineal');
                }
                break;

            case 'hybrid':
                // Híbrido generalmente es viable, pero puede tener limitaciones de performance
                if (nodeCount > 50) {
                    issues.push('Rendimiento puede degradarse con tantos nodos');
                }
                break;
        }

        return {
            viable,
            issues,
            recommendation: viable 
                ? `Modo ${getModeDisplayName(mode)} es viable`
                : `Considere usar modo híbrido o filtrar datos`
        };

    }, [mode, nodes, containerWidth, containerHeight]);
}