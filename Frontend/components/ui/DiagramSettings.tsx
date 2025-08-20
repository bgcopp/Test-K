/**
 * DiagramSettings - Panel de Configuraciones Modal - FASE 4
 * 
 * Panel modal para configurar opciones visuales y de comportamiento
 * del diagrama de correlación.
 * 
 * Características:
 * - Modal centrado con overlay
 * - Configuraciones organizadas por secciones
 * - Vista previa en tiempo real de cambios
 * - Auto-save de configuraciones
 * - Reset a valores por defecto
 * - Accesibilidad completa
 * 
 * @author Sistema KRONOS
 * @version 1.0.0 - FASE 4
 */

import React, { useState, useEffect } from 'react';
import { ICONS } from '../../constants';
import Button from './Button';
import { DiagramViewSettings, DiagramState, updateViewSettings } from '../../utils/diagramPersistence';

interface DiagramSettingsProps {
    isOpen: boolean;
    onClose: () => void;
    diagramState: DiagramState;
    onSettingsChange: (newState: DiagramState) => void;
    className?: string;
}

// Configuraciones predefinidas para layouts
const LAYOUT_PRESETS = {
    force: {
        name: 'Fuerza Dirigida',
        description: 'Distribución orgánica basada en fuerzas',
        icon: '🌊'
    },
    hierarchical: {
        name: 'Jerárquico',
        description: 'Estructura de árbol vertical',
        icon: '🌳'
    },
    circular: {
        name: 'Circular',
        description: 'Disposición en círculo',
        icon: '⭕'
    }
};

// Configuraciones de zoom predefinidas
const ZOOM_PRESETS = [
    { value: 0.5, label: '50%' },
    { value: 0.75, label: '75%' },
    { value: 1.0, label: '100%' },
    { value: 1.25, label: '125%' },
    { value: 1.5, label: '150%' },
    { value: 2.0, label: '200%' }
];

/**
 * Configuraciones por defecto del diagrama
 */
const getDefaultSettings = (): DiagramViewSettings => ({
    zoom: 1.0,
    center: { x: 0, y: 0 },
    layout: 'force',
    showCellLabels: true,
    showConfidenceValues: false,
    compactMode: false
});

/**
 * Componente principal del panel de configuraciones
 */
const DiagramSettings: React.FC<DiagramSettingsProps> = ({
    isOpen,
    onClose,
    diagramState,
    onSettingsChange,
    className = ''
}) => {
    const [localSettings, setLocalSettings] = useState<DiagramViewSettings>(diagramState.viewSettings);
    const [hasChanges, setHasChanges] = useState(false);
    const [isResetting, setIsResetting] = useState(false);
    
    // Sincronizar configuraciones locales con el estado del diagrama
    useEffect(() => {
        setLocalSettings(diagramState.viewSettings);
        setHasChanges(false);
    }, [diagramState.viewSettings]);
    
    // Verificar cambios pendientes
    useEffect(() => {
        const changed = JSON.stringify(localSettings) !== JSON.stringify(diagramState.viewSettings);
        setHasChanges(changed);
    }, [localSettings, diagramState.viewSettings]);
    
    // Actualizar configuración local
    const updateLocalSetting = <K extends keyof DiagramViewSettings>(
        key: K,
        value: DiagramViewSettings[K]
    ) => {
        setLocalSettings(prev => ({
            ...prev,
            [key]: value
        }));
    };
    
    // Aplicar cambios al diagrama
    const applyChanges = () => {
        const updatedState = updateViewSettings(diagramState, localSettings);
        onSettingsChange(updatedState);
        setHasChanges(false);
    };
    
    // Descartar cambios
    const discardChanges = () => {
        setLocalSettings(diagramState.viewSettings);
        setHasChanges(false);
    };
    
    // Reset a configuraciones por defecto
    const resetToDefaults = () => {
        setIsResetting(true);
        const defaultSettings = getDefaultSettings();
        setLocalSettings(defaultSettings);
        
        setTimeout(() => {
            const updatedState = updateViewSettings(diagramState, defaultSettings);
            onSettingsChange(updatedState);
            setIsResetting(false);
            setHasChanges(false);
        }, 500);
    };
    
    // Manejar cierre del modal
    const handleClose = () => {
        if (hasChanges) {
            const confirmDiscard = window.confirm(
                '¿Descartar los cambios no guardados?'
            );
            if (!confirmDiscard) return;
            discardChanges();
        }
        onClose();
    };
    
    // Manejar tecla ESC
    useEffect(() => {
        const handleEscape = (event: KeyboardEvent) => {
            if (event.key === 'Escape' && isOpen) {
                handleClose();
            }
        };
        
        if (isOpen) {
            document.addEventListener('keydown', handleEscape);
            return () => document.removeEventListener('keydown', handleEscape);
        }
    }, [isOpen, hasChanges]);
    
    if (!isOpen) return null;
    
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Overlay */}
            <div 
                className="absolute inset-0 bg-black/70 backdrop-blur-sm"
                onClick={handleClose}
            />
            
            {/* Panel principal */}
            <div className={`relative w-full max-w-3xl bg-secondary rounded-lg shadow-2xl border border-secondary-light m-4 max-h-[90vh] overflow-hidden ${className}`}>
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-secondary-light">
                    <div className="flex items-center gap-3">
                        <span className="text-2xl">⚙️</span>
                        <div>
                            <h3 className="text-xl font-bold text-light">Configuraciones del Diagrama</h3>
                            <p className="text-sm text-medium">
                                Personaliza la visualización y comportamiento
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={handleClose}
                        className="text-medium hover:text-light transition-colors"
                        title="Cerrar configuraciones"
                    >
                        <span className="text-2xl">{ICONS.close}</span>
                    </button>
                </div>
                
                {/* Contenido scrolleable */}
                <div className="p-6 space-y-8 overflow-y-auto max-h-[calc(90vh-180px)]">
                    {/* Sección: Layout y Distribución */}
                    <div>
                        <h4 className="text-lg font-semibold text-light mb-4 flex items-center gap-2">
                            <span>📐</span>
                            Layout y Distribución
                        </h4>
                        
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                            {Object.entries(LAYOUT_PRESETS).map(([layoutKey, preset]) => (
                                <button
                                    key={layoutKey}
                                    onClick={() => updateLocalSetting('layout', layoutKey as any)}
                                    className={`p-4 rounded-lg border-2 transition-all text-left ${
                                        localSettings.layout === layoutKey
                                            ? 'border-primary bg-primary/10 text-primary'
                                            : 'border-secondary-light bg-secondary-light text-medium hover:text-light hover:border-secondary'
                                    }`}
                                >
                                    <div className="text-center mb-2">
                                        <span className="text-3xl">{preset.icon}</span>
                                    </div>
                                    <div className="font-semibold">{preset.name}</div>
                                    <div className="text-xs mt-1">{preset.description}</div>
                                </button>
                            ))}
                        </div>
                        
                        {/* Configuración de zoom */}
                        <div className="mb-4">
                            <label className="block text-sm font-medium text-light mb-2">
                                Nivel de Zoom: {(localSettings.zoom * 100).toFixed(0)}%
                            </label>
                            <div className="flex items-center gap-2">
                                <input
                                    type="range"
                                    min="0.25"
                                    max="3"
                                    step="0.25"
                                    value={localSettings.zoom}
                                    onChange={(e) => updateLocalSetting('zoom', parseFloat(e.target.value))}
                                    className="flex-1 h-2 bg-secondary-light rounded-lg appearance-none cursor-pointer"
                                />
                                <div className="flex gap-1">
                                    {ZOOM_PRESETS.map((preset) => (
                                        <button
                                            key={preset.value}
                                            onClick={() => updateLocalSetting('zoom', preset.value)}
                                            className={`px-2 py-1 text-xs rounded transition-colors ${
                                                Math.abs(localSettings.zoom - preset.value) < 0.01
                                                    ? 'bg-primary text-white'
                                                    : 'bg-secondary-light text-medium hover:text-light'
                                            }`}
                                        >
                                            {preset.label}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    {/* Sección: Opciones de Visualización */}
                    <div>
                        <h4 className="text-lg font-semibold text-light mb-4 flex items-center gap-2">
                            <span>👁️</span>
                            Opciones de Visualización
                        </h4>
                        
                        <div className="space-y-4">
                            {/* Mostrar etiquetas de celdas */}
                            <label className="flex items-center gap-3 p-3 bg-secondary-light rounded-lg hover:bg-secondary-light cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={localSettings.showCellLabels}
                                    onChange={(e) => updateLocalSetting('showCellLabels', e.target.checked)}
                                    className="w-4 h-4 text-primary bg-secondary border-secondary-light rounded focus:ring-primary focus:ring-2"
                                />
                                <div className="flex-1">
                                    <div className="text-light font-medium">Mostrar Etiquetas de Celdas</div>
                                    <div className="text-sm text-medium">
                                        Muestra los IDs de las celdas en las conexiones
                                    </div>
                                </div>
                                <span className="text-xl">🏷️</span>
                            </label>
                            
                            {/* Mostrar valores de confianza */}
                            <label className="flex items-center gap-3 p-3 bg-secondary-light rounded-lg hover:bg-secondary-light cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={localSettings.showConfidenceValues}
                                    onChange={(e) => updateLocalSetting('showConfidenceValues', e.target.checked)}
                                    className="w-4 h-4 text-primary bg-secondary border-secondary-light rounded focus:ring-primary focus:ring-2"
                                />
                                <div className="flex-1">
                                    <div className="text-light font-medium">Mostrar Niveles de Confianza</div>
                                    <div className="text-sm text-medium">
                                        Muestra porcentajes de confianza en las conexiones
                                    </div>
                                </div>
                                <span className="text-xl">📊</span>
                            </label>
                            
                            {/* Modo compacto */}
                            <label className="flex items-center gap-3 p-3 bg-secondary-light rounded-lg hover:bg-secondary-light cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={localSettings.compactMode}
                                    onChange={(e) => updateLocalSetting('compactMode', e.target.checked)}
                                    className="w-4 h-4 text-primary bg-secondary border-secondary-light rounded focus:ring-primary focus:ring-2"
                                />
                                <div className="flex-1">
                                    <div className="text-light font-medium">Modo Compacto</div>
                                    <div className="text-sm text-medium">
                                        Reduce el tamaño de nodos y texto para mostrar más información
                                    </div>
                                </div>
                                <span className="text-xl">📱</span>
                            </label>
                        </div>
                    </div>
                    
                    {/* Sección: Información del Estado */}
                    <div>
                        <h4 className="text-lg font-semibold text-light mb-4 flex items-center gap-2">
                            <span>📋</span>
                            Estado Actual
                        </h4>
                        
                        <div className="bg-secondary-light p-4 rounded-lg">
                            <div className="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                    <span className="text-medium">Customizaciones:</span>
                                    <span className="text-light font-medium ml-2">
                                        {diagramState.customizations.length}
                                    </span>
                                </div>
                                <div>
                                    <span className="text-medium">Último guardado:</span>
                                    <span className="text-light font-medium ml-2">
                                        {new Date(diagramState.lastSaved).toLocaleTimeString()}
                                    </span>
                                </div>
                                <div>
                                    <span className="text-medium">Centro actual:</span>
                                    <span className="text-light font-medium ml-2">
                                        ({localSettings.center.x.toFixed(0)}, {localSettings.center.y.toFixed(0)})
                                    </span>
                                </div>
                                <div>
                                    <span className="text-medium">Layout activo:</span>
                                    <span className="text-light font-medium ml-2">
                                        {LAYOUT_PRESETS[localSettings.layout].name}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    {/* Indicador de cambios pendientes */}
                    {hasChanges && (
                        <div className="bg-amber-900/20 border border-amber-700 rounded-lg p-4">
                            <div className="flex items-center gap-2 text-amber-400">
                                <span>⚠️</span>
                                <span className="font-medium">Cambios pendientes</span>
                            </div>
                            <p className="text-sm text-amber-300 mt-1">
                                Hay configuraciones modificadas que no se han aplicado
                            </p>
                        </div>
                    )}
                </div>
                
                {/* Footer con botones */}
                <div className="flex justify-between items-center p-6 border-t border-secondary-light bg-secondary-light/30">
                    <Button
                        variant="secondary"
                        icon="🔄"
                        onClick={resetToDefaults}
                        loading={isResetting}
                        disabled={isResetting}
                        size="sm"
                    >
                        {isResetting ? 'Reseteando...' : 'Restaurar Defecto'}
                    </Button>
                    
                    <div className="flex gap-3">
                        <Button
                            variant="secondary"
                            onClick={handleClose}
                        >
                            {hasChanges ? 'Descartar' : 'Cerrar'}
                        </Button>
                        
                        {hasChanges && (
                            <Button
                                variant="primary"
                                icon="💾"
                                onClick={applyChanges}
                            >
                                Aplicar Cambios
                            </Button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DiagramSettings;