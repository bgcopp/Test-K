/**
 * Hook para manejar el selector de modos de visualización
 * Boris & Claude Code - 2025-08-21
 */

import { useState, useCallback, useEffect } from 'react';
import { VisualizationMode, PhoneNode } from '../types/correlation.types';

interface UseModeSelector {
    currentMode: VisualizationMode;
    setMode: (mode: VisualizationMode) => void;
    isTransitioning: boolean;
    previousMode: VisualizationMode | null;
    modeHistory: VisualizationMode[];
    canUndo: boolean;
    canRedo: boolean;
    undo: () => void;
    redo: () => void;
    resetToDefault: () => void;
    cycleMode: () => void;
}

interface UseModeOptions {
    defaultMode?: VisualizationMode;
    onModeChange?: (mode: VisualizationMode, previousMode: VisualizationMode | null) => void;
    transitionDuration?: number; // en milisegundos
    enableHistory?: boolean;
    maxHistorySize?: number;
}

/**
 * Hook principal para manejo del selector de modos
 */
export function useModeSelector(options: UseModeOptions = {}): UseModeSelector {
    const {
        defaultMode = 'radial',
        onModeChange,
        transitionDuration = 300,
        enableHistory = true,
        maxHistorySize = 10
    } = options;

    // Estados principales
    const [currentMode, setCurrentMode] = useState<VisualizationMode>(defaultMode);
    const [isTransitioning, setIsTransitioning] = useState(false);
    const [previousMode, setPreviousMode] = useState<VisualizationMode | null>(null);
    
    // Historial de modos (para undo/redo)
    const [modeHistory, setModeHistory] = useState<VisualizationMode[]>([defaultMode]);
    const [historyIndex, setHistoryIndex] = useState(0);

    // Función para cambiar modo con transición
    const setMode = useCallback((newMode: VisualizationMode) => {
        if (newMode === currentMode || isTransitioning) return;

        setIsTransitioning(true);
        const oldMode = currentMode;
        
        // Actualizar estados
        setPreviousMode(oldMode);
        setCurrentMode(newMode);

        // Agregar al historial si está habilitado
        if (enableHistory) {
            setModeHistory(prev => {
                const newHistory = [...prev.slice(0, historyIndex + 1), newMode];
                return newHistory.slice(-maxHistorySize); // Mantener tamaño máximo
            });
            setHistoryIndex(prev => Math.min(prev + 1, maxHistorySize - 1));
        }

        // Callback de cambio
        onModeChange?.(newMode, oldMode);

        // Finalizar transición después del tiempo especificado
        setTimeout(() => {
            setIsTransitioning(false);
        }, transitionDuration);

    }, [currentMode, isTransitioning, onModeChange, transitionDuration, enableHistory, maxHistorySize, historyIndex]);

    // Funciones de navegación en historial
    const canUndo = enableHistory && historyIndex > 0;
    const canRedo = enableHistory && historyIndex < modeHistory.length - 1;

    const undo = useCallback(() => {
        if (!canUndo) return;
        
        const targetIndex = historyIndex - 1;
        const targetMode = modeHistory[targetIndex];
        
        setHistoryIndex(targetIndex);
        setPreviousMode(currentMode);
        setCurrentMode(targetMode);
        
        onModeChange?.(targetMode, currentMode);
    }, [canUndo, historyIndex, modeHistory, currentMode, onModeChange]);

    const redo = useCallback(() => {
        if (!canRedo) return;
        
        const targetIndex = historyIndex + 1;
        const targetMode = modeHistory[targetIndex];
        
        setHistoryIndex(targetIndex);
        setPreviousMode(currentMode);
        setCurrentMode(targetMode);
        
        onModeChange?.(targetMode, currentMode);
    }, [canRedo, historyIndex, modeHistory, currentMode, onModeChange]);

    // Resetear a modo por defecto
    const resetToDefault = useCallback(() => {
        setMode(defaultMode);
    }, [setMode, defaultMode]);

    // Ciclar entre modos
    const cycleMode = useCallback(() => {
        const modes: VisualizationMode[] = ['radial', 'circular', 'linear', 'hybrid'];
        const currentIndex = modes.indexOf(currentMode);
        const nextIndex = (currentIndex + 1) % modes.length;
        setMode(modes[nextIndex]);
    }, [currentMode, setMode]);

    return {
        currentMode,
        setMode,
        isTransitioning,
        previousMode,
        modeHistory,
        canUndo,
        canRedo,
        undo,
        redo,
        resetToDefault,
        cycleMode
    };
}

/**
 * Hook para recomendaciones de modo basadas en datos
 */
export function useModeRecommendations(
    nodes: PhoneNode[],
    containerWidth: number,
    containerHeight: number
) {
    const [recommendations, setRecommendations] = useState<Array<{
        mode: VisualizationMode;
        score: number;
        reason: string;
        suitable: boolean;
    }>>([]);

    useEffect(() => {
        const nodeCount = nodes.length;
        const aspectRatio = containerWidth / containerHeight;
        
        const newRecommendations = [
            {
                mode: 'radial' as VisualizationMode,
                score: calculateRadialScore(nodeCount, aspectRatio),
                reason: getRadialReason(nodeCount),
                suitable: nodeCount <= 15
            },
            {
                mode: 'circular' as VisualizationMode,
                score: calculateCircularScore(nodeCount, aspectRatio),
                reason: getCircularReason(nodeCount),
                suitable: nodeCount <= 25
            },
            {
                mode: 'linear' as VisualizationMode,
                score: calculateLinearScore(nodeCount, aspectRatio),
                reason: getLinearReason(nodeCount, aspectRatio),
                suitable: nodeCount <= 12
            },
            {
                mode: 'hybrid' as VisualizationMode,
                score: calculateHybridScore(nodeCount),
                reason: getHybridReason(nodeCount),
                suitable: true // Siempre adecuado
            }
        ].sort((a, b) => b.score - a.score);

        setRecommendations(newRecommendations);
    }, [nodes, containerWidth, containerHeight]);

    return recommendations;
}

/**
 * Hook para preferencias persistentes del usuario
 */
export function useUserModePreferences(storageKey: string = 'kronos-diagram-mode-preferences') {
    const [preferences, setPreferences] = useState<{
        favoriteMode: VisualizationMode | null;
        modeUsageCount: Record<VisualizationMode, number>;
        lastUsedMode: VisualizationMode | null;
    }>(() => {
        try {
            const stored = localStorage.getItem(storageKey);
            return stored ? JSON.parse(stored) : {
                favoriteMode: null,
                modeUsageCount: { radial: 0, circular: 0, linear: 0, hybrid: 0 },
                lastUsedMode: null
            };
        } catch {
            return {
                favoriteMode: null,
                modeUsageCount: { radial: 0, circular: 0, linear: 0, hybrid: 0 },
                lastUsedMode: null
            };
        }
    });

    const updateModeUsage = useCallback((mode: VisualizationMode) => {
        setPreferences(prev => {
            const newPrefs = {
                ...prev,
                modeUsageCount: {
                    ...prev.modeUsageCount,
                    [mode]: prev.modeUsageCount[mode] + 1
                },
                lastUsedMode: mode
            };

            // Determinar modo favorito basado en uso
            const mostUsedMode = Object.entries(newPrefs.modeUsageCount)
                .sort(([,a], [,b]) => b - a)[0][0] as VisualizationMode;
            
            if (newPrefs.modeUsageCount[mostUsedMode] >= 3) {
                newPrefs.favoriteMode = mostUsedMode;
            }

            // Persistir en localStorage
            try {
                localStorage.setItem(storageKey, JSON.stringify(newPrefs));
            } catch (error) {
                console.warn('No se pudo guardar preferencias de modo:', error);
            }

            return newPrefs;
        });
    }, [storageKey]);

    const setFavoriteMode = useCallback((mode: VisualizationMode | null) => {
        setPreferences(prev => {
            const newPrefs = { ...prev, favoriteMode: mode };
            try {
                localStorage.setItem(storageKey, JSON.stringify(newPrefs));
            } catch (error) {
                console.warn('No se pudo guardar modo favorito:', error);
            }
            return newPrefs;
        });
    }, [storageKey]);

    const resetPreferences = useCallback(() => {
        const defaultPrefs = {
            favoriteMode: null,
            modeUsageCount: { radial: 0, circular: 0, linear: 0, hybrid: 0 },
            lastUsedMode: null
        };
        setPreferences(defaultPrefs);
        try {
            localStorage.setItem(storageKey, JSON.stringify(defaultPrefs));
        } catch (error) {
            console.warn('No se pudo resetear preferencias:', error);
        }
    }, [storageKey]);

    return {
        preferences,
        updateModeUsage,
        setFavoriteMode,
        resetPreferences
    };
}

// ==================== FUNCIONES AUXILIARES ====================

function calculateRadialScore(nodeCount: number, aspectRatio: number): number {
    let score = 50;
    
    // Óptimo para 4-12 nodos
    if (nodeCount >= 4 && nodeCount <= 12) score += 30;
    else if (nodeCount > 12) score -= (nodeCount - 12) * 2;
    else if (nodeCount < 4) score -= (4 - nodeCount) * 5;
    
    // Funciona bien en contenedores cuadrados
    if (aspectRatio >= 0.8 && aspectRatio <= 1.2) score += 10;
    
    return Math.max(0, Math.min(100, score));
}

function calculateCircularScore(nodeCount: number, aspectRatio: number): number {
    let score = 50;
    
    // Bueno para muchos nodos
    if (nodeCount >= 8 && nodeCount <= 25) score += 25;
    else if (nodeCount > 25) score -= (nodeCount - 25) * 1.5;
    else if (nodeCount < 8) score -= (8 - nodeCount) * 3;
    
    // Prefiere contenedores más anchos
    if (aspectRatio > 1.2) score += 10;
    
    return Math.max(0, Math.min(100, score));
}

function calculateLinearScore(nodeCount: number, aspectRatio: number): number {
    let score = 50;
    
    // Ideal para pocos nodos
    if (nodeCount <= 8) score += 30;
    else score -= (nodeCount - 8) * 3;
    
    // Excelente para contenedores panorámicos
    if (aspectRatio > 2) score += 20;
    else if (aspectRatio < 0.5) score += 20; // También vertical
    
    return Math.max(0, Math.min(100, score));
}

function calculateHybridScore(nodeCount: number): number {
    let score = 60; // Base más alta
    
    // Mejor para muchos nodos
    if (nodeCount > 15) score += 20;
    if (nodeCount > 25) score += 10;
    
    return Math.max(0, Math.min(100, score));
}

function getRadialReason(nodeCount: number): string {
    if (nodeCount <= 6) return 'Ideal para mostrar target central con pocos contactos';
    if (nodeCount <= 12) return 'Buena visualización de target central con contactos moderados';
    return 'Puede ser confuso con muchos nodos, considere modo híbrido';
}

function getCircularReason(nodeCount: number): string {
    if (nodeCount <= 8) return 'Distribución equilibrada para exploración general';
    if (nodeCount <= 20) return 'Excelente para muchos contactos con vista balanceada';
    return 'Óptimo para grandes redes sin nodo dominante';
}

function getLinearReason(nodeCount: number, aspectRatio: number): string {
    if (nodeCount <= 6) return 'Perfecto para análisis secuencial o temporal';
    if (aspectRatio > 2) return 'Aprovecha bien el formato panorámico';
    return 'Bueno para análisis paso a paso, pero limitado con muchos nodos';
}

function getHybridReason(nodeCount: number): string {
    if (nodeCount > 20) return 'Optimizado para redes grandes y complejas';
    return 'Combina lo mejor de otros modos según el contexto';
}