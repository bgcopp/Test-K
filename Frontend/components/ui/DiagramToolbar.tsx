/**
 * DiagramToolbar - Barra de herramientas avanzada para el diagrama de correlación
 * 
 * Implementa las especificaciones de FASE 3 con interactividad avanzada:
 * 
 * ⚙️ **Controles de Zoom Inteligentes:**
 * - Indicador visual con colores semáforo (rojo/amarillo/verde/azul/púrpura)
 * - Límites apropiados (0.2x - 3.0x) con validación
 * - Botones deshabilitados en límites para mejor UX
 * - Descripción textual del nivel de zoom actual
 * 
 * 🗺️ **Navegación Avanzada:**
 * - Centro de vista general con padding inteligente
 * - Navegación directa al nodo objetivo
 * - Modos de visualización: general, normal, enfocada
 * - Persistencia de preferencias de vista
 * 
 * 🏷️ **Controles de Visualización:**
 * - Toggle de etiquetas con feedback visual
 * - Reset de posiciones personalizadas (solo si existen)
 * - Modos de vista con iconografía intuitiva
 * - Estados visuales dinámicos
 * 
 * ✓ **Gestión de Selección:**
 * - Contador en tiempo real de nodos seleccionados
 * - Botón de limpieza de selección (aparece solo cuando necesario)
 * - Indicadores visuales de estado de selección
 * - Multi-selección con feedback claro
 * 
 * 📍 **Indicadores de Estado:**
 * - Número objetivo actual prominente
 * - Estado de posiciones personalizadas
 * - Modo de visualización activo
 * - Feedback visual inmediato de todas las acciones
 * 
 * ♿ **Accesibilidad y UX:**
 * - Tooltips descriptivos con atajos de teclado
 * - Controles agrupados lógicamente
 * - Separadores visuales para organización
 * - Diseño responsive que se adapta al contenido
 * - Consistencia completa con tema oscuro
 * 
 * @author Claude Code asistiendo a Boris
 * @version FASE 3 - Interactividad Avanzada
 */

import React, { useCallback } from 'react';
import ActionButton from './ActionButton';
import { ICONS } from '../../constants';
// FASE 4: Importaciones para funcionalidades avanzadas
import { DiagramState, hasPendingChanges } from '../../utils/diagramPersistence';

// ===============================================
// INTERFACES Y TIPOS
// ===============================================

interface DiagramToolbarProps {
    onZoomIn: () => void;
    onZoomOut: () => void;
    onResetView: () => void;
    onExport: () => void;
    onClose: () => void;
    zoomLevel?: number;
    /** Número de nodos seleccionados */
    selectedCount?: number;
    /** Función para centrar en el nodo objetivo */
    onCenterOnTarget?: () => void;
    /** Estado de visibilidad de etiquetas */
    showLabels?: boolean;
    /** Función para toggle de etiquetas */
    onToggleLabels?: () => void;
    /** Función para resetear posiciones personalizadas */
    onResetPositions?: () => void;
    /** Función para limpiar selección */
    onClearSelection?: () => void;
    /** Indica si hay posiciones personalizadas guardadas */
    hasCustomPositions?: boolean;
    /** Número objetivo actual */
    targetNumber?: string;
    /** Modo de visualización actual */
    viewMode?: 'normal' | 'focus' | 'overview';
    /** Función para cambiar modo de visualización */
    onViewModeChange?: (mode: 'normal' | 'focus' | 'overview') => void;
    // FASE 4: Nuevas props para funcionalidades avanzadas
    /** Estado del diagrama para persistencia */
    diagramState?: DiagramState;
    /** Función para abrir configuraciones */
    onOpenSettings?: () => void;
    /** Función para guardar forzadamente */
    onForceSave?: () => void;
}

/**
 * Tipos de modo de visualización
 */
export type ViewMode = 'normal' | 'focus' | 'overview';

// ===============================================
// CONSTANTES DE CONFIGURACIÓN
// ===============================================

/**
 * Límites de zoom exportados para uso en otros componentes
 */
export const ZOOM_LIMITS = {
    min: 0.2,
    max: 3.0,
    step: 0.2
};

/**
 * Modos de visualización disponibles
 */
export const VIEW_MODES = {
    normal: 'normal',
    focus: 'focus',
    overview: 'overview'
} as const;

// ===============================================
// COMPONENTE PRINCIPAL
// ===============================================

/**
 * DiagramToolbar - Barra de herramientas avanzada para el diagrama de correlación
 * 
 * Implementa todas las funcionalidades de FASE 3 con interfaz intuitiva,
 * controles inteligentes y feedback visual en tiempo real.
 */
const DiagramToolbar: React.FC<DiagramToolbarProps> = ({
    onZoomIn,
    onZoomOut,
    onResetView,
    onExport,
    onClose,
    zoomLevel = 1,
    selectedCount = 0,
    onCenterOnTarget,
    showLabels = true,
    onToggleLabels,
    onResetPositions,
    onClearSelection,
    hasCustomPositions = false,
    targetNumber,
    viewMode = 'normal',
    onViewModeChange,
    // FASE 4: Nuevas props
    diagramState,
    onOpenSettings,
    onForceSave
}) => {
    
    /**
     * Calcula el color del indicador de zoom basado en el nivel
     */
    const getZoomIndicatorColor = useCallback((zoom: number): string => {
        if (zoom < 0.5) return 'text-red-400'; // Muy alejado
        if (zoom < 0.8) return 'text-yellow-400'; // Alejado
        if (zoom <= 1.2) return 'text-green-400'; // Óptimo
        if (zoom <= 2) return 'text-blue-400'; // Cerca
        return 'text-purple-400'; // Muy cerca
    }, []);
    
    /**
     * Genera el texto de descripción del zoom
     */
    const getZoomDescription = useCallback((zoom: number): string => {
        if (zoom < 0.5) return 'Vista general';
        if (zoom < 0.8) return 'Vista amplia';
        if (zoom <= 1.2) return 'Vista normal';
        if (zoom <= 2) return 'Vista detalle';
        return 'Vista macro';
    }, []);
    
    /**
     * Maneja el cambio de modo de visualización
     */
    const handleViewModeChange = useCallback((mode: ViewMode) => {
        if (onViewModeChange) {
            onViewModeChange(mode);
        }
    }, [onViewModeChange]);

    // FASE 4: Funciones para nuevas funcionalidades
    
    /**
     * Determina si hay cambios pendientes en el diagrama
     */
    const isDirty = diagramState ? hasPendingChanges(diagramState) : false;
    
    /**
     * Obtiene el número de customizaciones activas
     */
    const customizationsCount = diagramState?.customizations.length || 0;
    
    /**
     * Maneja el guardado forzado del diagrama
     */
    const handleForceSave = useCallback(() => {
        if (onForceSave && isDirty) {
            onForceSave();
        }
    }, [onForceSave, isDirty]);
    
    /**
     * Maneja la apertura del panel de configuraciones
     */
    const handleOpenSettings = useCallback(() => {
        if (onOpenSettings) {
            onOpenSettings();
        }
    }, [onOpenSettings]);

    return (
        <div className="flex items-center justify-between p-4 bg-gray-900 border-b border-gray-700 shadow-lg">
            {/* Grupo izquierdo: Controles de zoom y navegación */}
            <div className="flex items-center space-x-3">
                {/* Controles de Zoom Avanzados */}
                <div className="flex items-center space-x-2 bg-gray-800 rounded-lg p-2 border border-gray-700">
                    <button
                        onClick={onZoomOut}
                        disabled={zoomLevel <= ZOOM_LIMITS.min}
                        className={`p-2 text-sm rounded transition-all duration-200 ${
                            zoomLevel <= ZOOM_LIMITS.min
                                ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                                : 'bg-gray-600 hover:bg-gray-500 text-white'
                        }`}
                        title="Disminuir zoom (-)"
                        aria-label="Disminuir zoom"
                    >
                        🔍-
                    </button>
                    
                    {/* Indicador de zoom mejorado */}
                    <div className="flex flex-col items-center px-3 py-1">
                        <div className={`text-sm font-mono font-semibold ${getZoomIndicatorColor(zoomLevel)}`}>
                            {Math.round(zoomLevel * 100)}%
                        </div>
                        <div className="text-xs text-gray-400">
                            {getZoomDescription(zoomLevel)}
                        </div>
                    </div>
                    
                    <button
                        onClick={onZoomIn}
                        disabled={zoomLevel >= ZOOM_LIMITS.max}
                        className={`p-2 text-sm rounded transition-all duration-200 ${
                            zoomLevel >= ZOOM_LIMITS.max
                                ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                                : 'bg-gray-600 hover:bg-gray-500 text-white'
                        }`}
                        title="Aumentar zoom (+)"
                        aria-label="Aumentar zoom"
                    >
                        🔍+
                    </button>
                </div>

                {/* Separador visual */}
                <div className="w-px h-8 bg-gray-700"></div>

                {/* Controles de Navegación */}
                <div className="flex items-center space-x-1">
                    <button
                        onClick={onResetView}
                        className="px-3 py-2 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded-lg border border-blue-500 transition-all duration-200"
                        title="Centrar vista (0)"
                    >
                        🎯 Centrar
                    </button>
                    
                    {onCenterOnTarget && (
                        <button
                            onClick={onCenterOnTarget}
                            className="px-3 py-2 text-xs bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg border border-yellow-500 transition-all duration-200"
                            title={`Ir al objetivo: ${targetNumber || 'N/A'}`}
                        >
                            🏹 Objetivo
                        </button>
                    )}
                </div>

                {/* Separador visual */}
                <div className="w-px h-8 bg-gray-700"></div>

                {/* Modos de Visualización */}
                <div className="flex items-center space-x-1 bg-gray-800 rounded-lg p-1 border border-gray-700">
                    <button
                        onClick={() => handleViewModeChange('overview')}
                        className={`px-2 py-1 text-xs rounded transition-colors duration-200 ${
                            viewMode === 'overview' 
                                ? 'bg-blue-600 text-white' 
                                : 'text-gray-300 hover:bg-gray-700'
                        }`}
                        title="Vista general"
                    >
                        🗺️
                    </button>
                    <button
                        onClick={() => handleViewModeChange('normal')}
                        className={`px-2 py-1 text-xs rounded transition-colors duration-200 ${
                            viewMode === 'normal' 
                                ? 'bg-blue-600 text-white' 
                                : 'text-gray-300 hover:bg-gray-700'
                        }`}
                        title="Vista normal"
                    >
                        🔍
                    </button>
                    <button
                        onClick={() => handleViewModeChange('focus')}
                        className={`px-2 py-1 text-xs rounded transition-colors duration-200 ${
                            viewMode === 'focus' 
                                ? 'bg-blue-600 text-white' 
                                : 'text-gray-300 hover:bg-gray-700'
                        }`}
                        title="Vista enfocada"
                    >
                        🎯
                    </button>
                </div>

                {/* Separador visual */}
                <div className="w-px h-8 bg-gray-700"></div>

                {/* Controles de Visualización */}
                <div className="flex items-center space-x-1">
                    {onToggleLabels && (
                        <button
                            onClick={onToggleLabels}
                            className={`px-3 py-2 text-xs rounded-lg border transition-all duration-200 ${
                                showLabels 
                                    ? 'bg-green-600 hover:bg-green-700 border-green-500 text-white' 
                                    : 'bg-gray-700 hover:bg-gray-600 border-gray-600 text-gray-300'
                            }`}
                            title={`${showLabels ? 'Ocultar' : 'Mostrar'} etiquetas`}
                        >
                            <span className="flex items-center space-x-1">
                                <span>{showLabels ? "🏷️" : "📝"}</span>
                                <span>{showLabels ? 'Etiquetas' : 'Sin etiquetas'}</span>
                            </span>
                        </button>
                    )}
                    
                    {onResetPositions && hasCustomPositions && (
                        <button
                            onClick={onResetPositions}
                            className="px-3 py-2 text-xs rounded-lg border bg-orange-600 hover:bg-orange-700 border-orange-500 text-white transition-all duration-200"
                            title="Resetear posiciones personalizadas"
                        >
                            <span className="flex items-center space-x-1">
                                <span>🔄</span>
                                <span>Reset</span>
                            </span>
                        </button>
                    )}
                </div>
            </div>

            {/* Grupo centro: Información del diagrama */}
            <div className="flex-1 text-center px-4">
                <h3 className="text-lg font-semibold text-white flex items-center justify-center space-x-2">
                    <span>🕸️</span>
                    <span>Diagrama de Correlación</span>
                    {targetNumber && (
                        <span className="text-sm font-mono text-blue-300 bg-blue-900/30 px-2 py-1 rounded border border-blue-700">
                            {targetNumber}
                        </span>
                    )}
                    {/* FASE 4: Indicador de estado de guardado */}
                    {diagramState && (
                        <span className="flex items-center space-x-1">
                            <span className={`w-2 h-2 rounded-full ${isDirty ? 'bg-red-400' : 'bg-green-400'}`} />
                            <span className="text-xs text-gray-400">
                                {isDirty ? 'Sin guardar' : 'Guardado'}
                            </span>
                        </span>
                    )}
                </h3>
                <div className="flex items-center justify-center space-x-4 text-xs text-gray-400 mt-1">
                    <span>Vista interactiva de correlaciones detectadas</span>
                    
                    {/* Indicadores de estado */}
                    {selectedCount > 0 && (
                        <span className="flex items-center space-x-1 bg-yellow-900/30 text-yellow-300 px-2 py-1 rounded border border-yellow-700">
                            <span>✓</span>
                            <span>{selectedCount} seleccionado{selectedCount !== 1 ? 's' : ''}</span>
                        </span>
                    )}
                    
                    {hasCustomPositions && (
                        <span className="flex items-center space-x-1 bg-purple-900/30 text-purple-300 px-2 py-1 rounded border border-purple-700">
                            <span>📍</span>
                            <span>Posiciones personalizadas</span>
                        </span>
                    )}

                    {/* FASE 4: Indicador de customizaciones */}
                    {customizationsCount > 0 && (
                        <span className="flex items-center space-x-1 bg-green-900/30 text-green-300 px-2 py-1 rounded border border-green-700">
                            <span>✨</span>
                            <span>{customizationsCount} customización{customizationsCount !== 1 ? 'es' : ''}</span>
                        </span>
                    )}
                </div>
            </div>

            {/* Grupo derecho: Acciones y controles */}
            <div className="flex items-center space-x-2">
                {/* Controles de selección */}
                {selectedCount > 0 && onClearSelection && (
                    <button
                        onClick={onClearSelection}
                        className="px-3 py-2 text-xs bg-red-600 hover:bg-red-700 text-white rounded-lg border border-red-500 transition-all duration-200"
                        title="Limpiar selección"
                    >
                        ❌ Limpiar
                    </button>
                )}
                
                {/* Separador */}
                {selectedCount > 0 && <div className="w-px h-6 bg-gray-700"></div>}

                {/* FASE 4: Botón de guardado forzado */}
                {isDirty && onForceSave && (
                    <button
                        onClick={handleForceSave}
                        className="px-3 py-2 text-xs bg-orange-600 hover:bg-orange-700 text-white rounded-lg border border-orange-500 transition-all duration-200"
                        title="Guardar cambios ahora"
                    >
                        💾 Guardar
                    </button>
                )}

                {/* FASE 4: Botón de configuraciones */}
                {onOpenSettings && (
                    <button
                        onClick={handleOpenSettings}
                        className="px-3 py-2 text-xs bg-gray-600 hover:bg-gray-700 text-white rounded-lg border border-gray-500 transition-all duration-200"
                        title="Configuraciones del diagrama"
                    >
                        ⚙️ Config
                    </button>
                )}
                
                {/* Separador para acciones principales */}
                <div className="w-px h-6 bg-gray-700"></div>

                {/* Export */}
                <ActionButton
                    icon={ICONS.export}
                    onClick={onExport}
                    tooltip="Exportar diagrama"
                    size="sm"
                    variant="secondary"
                />
                
                {/* Botón de cierre */}
                <ActionButton
                    icon={ICONS.close}
                    onClick={onClose}
                    tooltip="Cerrar diagrama"
                    size="md"
                    variant="default"
                />
            </div>
        </div>
    );
};

/**
 * Props por defecto para el componente
 */
DiagramToolbar.defaultProps = {
    zoomLevel: 1,
    selectedCount: 0,
    showLabels: true,
    hasCustomPositions: false,
    viewMode: 'normal'
};

export default DiagramToolbar;

/**
 * Tipos exportados para uso en otros componentes
 */
export type { DiagramToolbarProps };