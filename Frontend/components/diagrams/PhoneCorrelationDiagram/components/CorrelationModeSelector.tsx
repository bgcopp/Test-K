/**
 * Componente selector de modos de visualización del diagrama
 * Boris & Claude Code - 2025-08-21
 */

import React, { memo } from 'react';
import { VisualizationMode } from '../types/correlation.types';
import { NODE_COLOR_SCHEME } from '../utils/colorSchemes';

interface CorrelationModeSelectorProps {
    currentMode: VisualizationMode;
    onModeChange: (mode: VisualizationMode) => void;
    isTransitioning?: boolean;
    recommendations?: Array<{
        mode: VisualizationMode;
        score: number;
        reason: string;
        suitable: boolean;
    }>;
    disabled?: boolean;
    className?: string;
}

/**
 * Selector de modos con previsualizaciones visuales y recomendaciones
 */
const CorrelationModeSelector: React.FC<CorrelationModeSelectorProps> = ({
    currentMode,
    onModeChange,
    isTransitioning = false,
    recommendations = [],
    disabled = false,
    className = ''
}) => {
    
    // Configuración de modos con metadatos
    const modeConfigs = [
        {
            mode: 'radial' as VisualizationMode,
            name: 'Radial Central',
            icon: '🎯',
            description: 'Target al centro, contactos alrededor',
            preview: 'radial-preview',
            optimal: 'Ideal para análisis centrado en el objetivo',
            color: NODE_COLOR_SCHEME.target
        },
        {
            mode: 'circular' as VisualizationMode,
            name: 'Circular Avatares',
            icon: '⭕',
            description: 'Todos los contactos en círculo equilibrado',
            preview: 'circular-preview',
            optimal: 'Perfecto para exploración general',
            color: '#10B981'
        },
        {
            mode: 'linear' as VisualizationMode,
            name: 'Flujo Lineal',
            icon: '📈',
            description: 'Secuencia temporal cronológica',
            preview: 'linear-preview',
            optimal: 'Excelente para análisis temporal',
            color: '#3B82F6'
        },
        {
            mode: 'hybrid' as VisualizationMode,
            name: 'Híbrido Inteligente',
            icon: '🧠',
            description: 'Adaptativo según cantidad de datos',
            preview: 'hybrid-preview',
            optimal: 'Óptimo para redes complejas',
            color: '#8B5CF6'
        }
    ];

    // Obtener recomendación para un modo específico
    const getRecommendation = (mode: VisualizationMode) => {
        return recommendations.find(rec => rec.mode === mode);
    };

    // Renderizar minipreview del modo
    const renderModePreview = (config: typeof modeConfigs[0]) => {
        const previewStyle = {
            width: '40px',
            height: '24px',
            background: `linear-gradient(135deg, ${config.color} 0%, rgba(255,255,255,0.1) 100%)`,
            borderRadius: '4px',
            position: 'relative' as const,
            overflow: 'hidden',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
        };

        switch (config.mode) {
            case 'radial':
                return (
                    <div style={previewStyle}>
                        <div style={{
                            width: '6px',
                            height: '6px',
                            background: 'white',
                            borderRadius: '50%',
                            position: 'absolute',
                            top: '50%',
                            left: '50%',
                            transform: 'translate(-50%, -50%)'
                        }} />
                        {[0, 1, 2, 3].map(i => (
                            <div
                                key={i}
                                style={{
                                    width: '3px',
                                    height: '3px',
                                    background: 'rgba(255,255,255,0.8)',
                                    borderRadius: '50%',
                                    position: 'absolute',
                                    top: '50%',
                                    left: '50%',
                                    transform: `translate(-50%, -50%) translateX(12px) rotate(${i * 90}deg) translateX(-12px)`
                                }}
                            />
                        ))}
                    </div>
                );
            
            case 'circular':
                return (
                    <div style={previewStyle}>
                        {[0, 1, 2, 3, 4].map(i => (
                            <div
                                key={i}
                                style={{
                                    width: '4px',
                                    height: '4px',
                                    background: 'white',
                                    borderRadius: '50%',
                                    position: 'absolute',
                                    top: '50%',
                                    left: '50%',
                                    transform: `translate(-50%, -50%) rotate(${i * 72}deg) translateY(-10px)`
                                }}
                            />
                        ))}
                    </div>
                );
            
            case 'linear':
                return (
                    <div style={previewStyle}>
                        {[0, 1, 2, 3, 4].map(i => (
                            <div
                                key={i}
                                style={{
                                    width: '3px',
                                    height: '3px',
                                    background: 'white',
                                    borderRadius: '50%',
                                    position: 'absolute',
                                    left: `${15 + i * 12}%`,
                                    top: '50%',
                                    transform: 'translateY(-50%)'
                                }}
                            />
                        ))}
                    </div>
                );
            
            case 'hybrid':
                return (
                    <div style={previewStyle}>
                        {/* Centro */}
                        <div style={{
                            width: '4px',
                            height: '4px',
                            background: 'white',
                            borderRadius: '50%',
                            position: 'absolute',
                            top: '50%',
                            left: '50%',
                            transform: 'translate(-50%, -50%)'
                        }} />
                        {/* Anillo interno */}
                        {[0, 1].map(i => (
                            <div
                                key={`inner-${i}`}
                                style={{
                                    width: '2px',
                                    height: '2px',
                                    background: 'rgba(255,255,255,0.8)',
                                    borderRadius: '50%',
                                    position: 'absolute',
                                    top: '50%',
                                    left: '50%',
                                    transform: `translate(-50%, -50%) rotate(${i * 180}deg) translateY(-6px)`
                                }}
                            />
                        ))}
                        {/* Anillo externo */}
                        {[0, 1, 2].map(i => (
                            <div
                                key={`outer-${i}`}
                                style={{
                                    width: '2px',
                                    height: '2px',
                                    background: 'rgba(255,255,255,0.6)',
                                    borderRadius: '50%',
                                    position: 'absolute',
                                    top: '50%',
                                    left: '50%',
                                    transform: `translate(-50%, -50%) rotate(${i * 120}deg) translateY(-10px)`
                                }}
                            />
                        ))}
                    </div>
                );
            
            default:
                return <div style={previewStyle} />;
        }
    };

    const handleModeClick = (mode: VisualizationMode) => {
        if (disabled || isTransitioning || mode === currentMode) return;
        onModeChange(mode);
    };

    return (
        <div className={`correlation-mode-selector ${className}`}>
            {/* Contenedor principal de botones */}
            <div style={{
                display: 'flex',
                gap: '8px',
                padding: '12px',
                background: 'rgba(31, 41, 55, 0.95)',
                borderRadius: '12px',
                border: '1px solid #374151',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
                backdropFilter: 'blur(8px)'
            }}>
                {modeConfigs.map(config => {
                    const isActive = currentMode === config.mode;
                    const recommendation = getRecommendation(config.mode);
                    const isRecommended = recommendation && recommendation.score > 70;
                    
                    return (
                        <div
                            key={config.mode}
                            onClick={() => handleModeClick(config.mode)}
                            style={{
                                position: 'relative',
                                cursor: disabled || isTransitioning ? 'not-allowed' : 'pointer',
                                opacity: disabled ? 0.5 : 1,
                                transition: 'all 0.3s ease'
                            }}
                            className="mode-button-container group"
                        >
                            {/* Botón principal */}
                            <div style={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                padding: '12px 16px',
                                borderRadius: '8px',
                                background: isActive 
                                    ? `linear-gradient(135deg, ${config.color} 0%, rgba(255,255,255,0.1) 100%)`
                                    : 'rgba(75, 85, 99, 0.3)',
                                border: `2px solid ${isActive ? config.color : 'transparent'}`,
                                minWidth: '120px',
                                boxShadow: isActive 
                                    ? `0 0 15px ${config.color}40`
                                    : '0 2px 6px rgba(0,0,0,0.2)',
                                transform: isActive ? 'scale(1.05)' : 'scale(1)',
                                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                            }}
                            className={`${isActive ? '' : 'group-hover:bg-gray-600 group-hover:scale-105'}`}
                        >
                            {/* Header con icono y badge */}
                            <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '6px',
                                marginBottom: '8px',
                                position: 'relative'
                            }}>
                                <span style={{ fontSize: '18px' }}>
                                    {config.icon}
                                </span>
                                
                                {/* Badge de recomendación */}
                                {isRecommended && !isActive && (
                                    <div style={{
                                        position: 'absolute',
                                        top: '-6px',
                                        right: '-6px',
                                        background: '#10B981',
                                        borderRadius: '50%',
                                        width: '12px',
                                        height: '12px',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        fontSize: '8px',
                                        border: '2px solid white'
                                    }}>
                                        ✨
                                    </div>
                                )}
                            </div>
                            
                            {/* Preview visual */}
                            <div style={{ marginBottom: '8px' }}>
                                {renderModePreview(config)}
                            </div>
                            
                            {/* Nombre del modo */}
                            <div style={{
                                fontSize: '12px',
                                fontWeight: 'bold',
                                color: isActive ? 'white' : '#D1D5DB',
                                textAlign: 'center',
                                marginBottom: '4px'
                            }}>
                                {config.name}
                            </div>
                            
                            {/* Descripción corta */}
                            <div style={{
                                fontSize: '9px',
                                color: isActive ? 'rgba(255,255,255,0.8)' : '#9CA3AF',
                                textAlign: 'center',
                                lineHeight: 1.2
                            }}>
                                {config.description}
                            </div>
                            
                            {/* Indicador de carga */}
                            {isTransitioning && isActive && (
                                <div style={{
                                    position: 'absolute',
                                    top: '50%',
                                    left: '50%',
                                    transform: 'translate(-50%, -50%)',
                                    background: 'rgba(0, 0, 0, 0.7)',
                                    borderRadius: '50%',
                                    width: '30px',
                                    height: '30px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    fontSize: '14px'
                                }}>
                                    <div style={{
                                        animation: 'spin 1s linear infinite',
                                        transformOrigin: 'center'
                                    }}>
                                        ⟳
                                    </div>
                                </div>
                            )}
                        </div>
                        
                        {/* Tooltip detallado */}
                        <div
                            style={{
                                position: 'absolute',
                                bottom: '110%',
                                left: '50%',
                                transform: 'translateX(-50%)',
                                background: 'rgba(0, 0, 0, 0.95)',
                                color: 'white',
                                padding: '8px 12px',
                                borderRadius: '6px',
                                fontSize: '10px',
                                whiteSpace: 'nowrap' as const,
                                boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                                opacity: 0,
                                pointerEvents: 'none' as const,
                                transition: 'opacity 0.3s ease',
                                zIndex: 1000,
                                maxWidth: '200px',
                                whiteSpace: 'normal' as const
                            }}
                            className="group-hover:opacity-100"
                        >
                            <div style={{ fontWeight: 'bold', marginBottom: '4px', color: config.color }}>
                                {config.name}
                            </div>
                            <div style={{ marginBottom: '4px' }}>
                                {config.optimal}
                            </div>
                            {recommendation && (
                                <div style={{ 
                                    fontSize: '9px', 
                                    color: recommendation.suitable ? '#10B981' : '#F59E0B'
                                }}>
                                    Puntuación: {recommendation.score}/100
                                    {isRecommended && ' ⭐ Recomendado'}
                                </div>
                            )}
                            
                            {/* Flecha del tooltip */}
                            <div
                                style={{
                                    position: 'absolute',
                                    top: '100%',
                                    left: '50%',
                                    transform: 'translateX(-50%)',
                                    width: 0,
                                    height: 0,
                                    borderLeft: '6px solid transparent',
                                    borderRight: '6px solid transparent',
                                    borderTop: '6px solid rgba(0, 0, 0, 0.95)'
                                }}
                            />
                        </div>
                    </div>
                );
            })}
        </div>
        
        {/* Panel de información del modo actual */}
        {currentMode && (
            <div style={{
                marginTop: '12px',
                padding: '8px 12px',
                background: 'rgba(75, 85, 99, 0.3)',
                borderRadius: '6px',
                border: '1px solid #4B5563'
            }}>
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    fontSize: '11px',
                    color: '#D1D5DB'
                }}>
                    <span>Modo actual:</span>
                    <span style={{ 
                        fontWeight: 'bold',
                        color: modeConfigs.find(c => c.mode === currentMode)?.color || 'white'
                    }}>
                        {modeConfigs.find(c => c.mode === currentMode)?.name}
                    </span>
                    {recommendations.find(r => r.mode === currentMode) && (
                        <span style={{ 
                            fontSize: '10px',
                            color: '#9CA3AF',
                            marginLeft: 'auto'
                        }}>
                            {recommendations.find(r => r.mode === currentMode)?.reason}
                        </span>
                    )}
                </div>
            </div>
        )}
        
        {/* Animaciones CSS */}
        <style jsx>{`
            @keyframes spin {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }
        `}</style>
    </div>
    );
};

export default memo(CorrelationModeSelector);