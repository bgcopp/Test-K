/**
 * Componente de nodo circular con avatar para modo circular
 * Boris & Claude Code - 2025-08-21
 */

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { PhoneNodeData } from '../../types/correlation.types';
import { getNodeColor, getOperatorColor, NODE_COLOR_SCHEME } from '../../utils/colorSchemes';

interface CircularAvatarNodeProps extends NodeProps<PhoneNodeData> {
    selected?: boolean;
    onClick?: (nodeId: string) => void;
    onDoubleClick?: (nodeId: string) => void;
}

/**
 * Nodo circular con avatar para layout circular
 */
const CircularAvatarNode: React.FC<CircularAvatarNodeProps> = ({
    id,
    data,
    selected = false,
    onClick,
    onDoubleClick
}) => {
    const {
        number,
        operator,
        interactionCount,
        callDuration,
        connections,
        lastInteraction,
        hunterPoints,
        coordinates,
        isTarget
    } = data;

    // Determinar características del nodo
    const isHighActivity = interactionCount > 15;
    const isMediumActivity = interactionCount > 5;
    const isRecentActivity = new Date(lastInteraction) > new Date(Date.now() - 3 * 24 * 60 * 60 * 1000); // últimos 3 días

    // Calcular tamaño dinámico
    const baseSize = isTarget ? 85 : 70;
    const activityMultiplier = isHighActivity ? 1.15 : isMediumActivity ? 1.05 : 1;
    const nodeSize = baseSize * activityMultiplier;

    // Colores dinámicos
    const nodeColor = isTarget 
        ? NODE_COLOR_SCHEME.target 
        : getNodeColor(false, selected, isRecentActivity, interactionCount);
    const operatorColor = getOperatorColor(operator);

    // Determinar emoji de avatar basado en características
    const getAvatarEmoji = (): string => {
        if (isTarget) return '🎯';
        if (isHighActivity) return '🔥';
        if (coordinates) return '📍';
        if (operator === 'CLARO') return '🔴';
        if (operator === 'MOVISTAR') return '🟢';
        if (operator === 'TIGO') return '🔵';
        return '📱';
    };

    // Formatear número para display
    const formatNumber = (num: string): string => {
        if (num.length <= 10) return num;
        return `${num.slice(0, 3)} ${num.slice(3, 6)} ${num.slice(6)}`;
    };

    // Formatear tiempo relativo
    const formatRelativeTime = (dateStr: string): string => {
        try {
            const date = new Date(dateStr);
            const now = new Date();
            const diffHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
            
            if (diffHours < 1) return 'Ahora';
            if (diffHours < 24) return `${diffHours}h`;
            if (diffHours < 168) return `${Math.floor(diffHours / 24)}d`;
            return `${Math.floor(diffHours / 168)}sem`;
        } catch {
            return 'N/A';
        }
    };

    // Estilos del nodo
    const nodeStyles = {
        width: `${nodeSize}px`,
        height: `${nodeSize}px`,
        background: selected 
            ? `linear-gradient(135deg, ${NODE_COLOR_SCHEME.selected} 0%, ${nodeColor} 100%)`
            : isTarget
                ? `linear-gradient(135deg, ${nodeColor} 0%, rgba(0, 212, 255, 0.8) 100%)`
                : `linear-gradient(135deg, ${nodeColor} 0%, rgba(255,255,255,0.15) 100%)`,
        border: `3px solid ${selected ? NODE_COLOR_SCHEME.selected : operatorColor}`,
        borderRadius: '50%',
        boxShadow: selected 
            ? `0 0 25px ${NODE_COLOR_SCHEME.selected}66, inset 0 3px 10px rgba(255,255,255,0.2)`
            : isTarget
                ? '0 0 20px rgba(0, 212, 255, 0.4), inset 0 3px 10px rgba(255,255,255,0.2)'
                : '0 6px 15px rgba(0,0,0,0.25), inset 0 3px 10px rgba(255,255,255,0.2)',
        cursor: 'pointer',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        position: 'relative' as const,
        display: 'flex',
        flexDirection: 'column' as const,
        alignItems: 'center',
        justifyContent: 'center',
        color: 'white',
        overflow: 'visible',
        transform: selected ? 'scale(1.1)' : 'scale(1)',
        zIndex: selected ? 15 : isTarget ? 10 : isHighActivity ? 5 : 1
    };

    const handleClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        onClick?.(id);
    };

    const handleDoubleClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        onDoubleClick?.(id);
    };

    return (
        <>
            {/* Handles para conexiones */}
            <Handle type="target" position={Position.Top} id="t-top" style={{ opacity: 0 }} />
            <Handle type="target" position={Position.Right} id="t-right" style={{ opacity: 0 }} />
            <Handle type="target" position={Position.Bottom} id="t-bottom" style={{ opacity: 0 }} />
            <Handle type="target" position={Position.Left} id="t-left" style={{ opacity: 0 }} />
            <Handle type="source" position={Position.Top} id="s-top" style={{ opacity: 0 }} />
            <Handle type="source" position={Position.Right} id="s-right" style={{ opacity: 0 }} />
            <Handle type="source" position={Position.Bottom} id="s-bottom" style={{ opacity: 0 }} />
            <Handle type="source" position={Position.Left} id="s-left" style={{ opacity: 0 }} />

            <div
                style={nodeStyles}
                onClick={handleClick}
                onDoubleClick={handleDoubleClick}
                className="group"
            >
                {/* Anillo exterior animado para target */}
                {isTarget && (
                    <div
                        style={{
                            position: 'absolute',
                            top: '-12px',
                            left: '-12px',
                            right: '-12px',
                            bottom: '-12px',
                            border: `2px solid ${NODE_COLOR_SCHEME.target}60`,
                            borderRadius: '50%',
                            animation: 'rotate 10s linear infinite'
                        }}
                    />
                )}

                {/* Avatar principal */}
                <div style={{
                    fontSize: isTarget ? '24px' : nodeSize > 75 ? '20px' : '16px',
                    marginBottom: isTarget ? '4px' : '2px',
                    filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))'
                }}>
                    {getAvatarEmoji()}
                </div>

                {/* Número telefónico */}
                <div style={{
                    fontSize: isTarget ? '9px' : nodeSize > 75 ? '8px' : '7px',
                    fontWeight: 'bold',
                    lineHeight: 1,
                    marginBottom: '1px',
                    textAlign: 'center',
                    maxWidth: '90%',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                }}>
                    {isTarget ? formatNumber(number) : number.slice(-4)}
                </div>

                {/* Operador */}
                <div style={{
                    fontSize: isTarget ? '7px' : '6px',
                    opacity: 0.8,
                    fontWeight: 'normal',
                    textAlign: 'center'
                }}>
                    {operator.slice(0, isTarget ? 6 : 4)}
                </div>

                {/* Badges de estado */}
                
                {/* Badge de interacciones */}
                <div style={{
                    position: 'absolute',
                    top: '-4px',
                    right: '-4px',
                    background: isHighActivity ? '#EF4444' : isMediumActivity ? '#F59E0B' : '#6B7280',
                    color: 'white',
                    fontSize: '9px',
                    fontWeight: 'bold',
                    borderRadius: '50%',
                    width: '18px',
                    height: '18px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    border: '2px solid white',
                    boxShadow: '0 2px 6px rgba(0,0,0,0.3)'
                }}>
                    {interactionCount > 99 ? '99+' : interactionCount}
                </div>

                {/* Badge de actividad reciente */}
                {isRecentActivity && (
                    <div style={{
                        position: 'absolute',
                        top: '-4px',
                        left: '-4px',
                        background: '#10B981',
                        borderRadius: '50%',
                        width: '12px',
                        height: '12px',
                        border: '2px solid white',
                        boxShadow: '0 0 10px rgba(16, 185, 129, 0.6)',
                        animation: 'pulse-green 2s infinite'
                    }}
                    title="Actividad reciente"
                    />
                )}

                {/* Badge de ubicación GPS */}
                {coordinates && (
                    <div style={{
                        position: 'absolute',
                        bottom: '-4px',
                        right: '-4px',
                        background: '#8B5CF6',
                        color: 'white',
                        fontSize: '8px',
                        borderRadius: '50%',
                        width: '14px',
                        height: '14px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        border: '2px solid white'
                    }}>
                        📍
                    </div>
                )}

                {/* Badge de tipo de conexión */}
                {connections.incoming > connections.outgoing ? (
                    <div style={{
                        position: 'absolute',
                        bottom: '-4px',
                        left: '-4px',
                        background: '#3B82F6',
                        color: 'white',
                        fontSize: '8px',
                        borderRadius: '50%',
                        width: '14px',
                        height: '14px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        border: '2px solid white'
                    }}>
                        📥
                    </div>
                ) : connections.outgoing > connections.incoming ? (
                    <div style={{
                        position: 'absolute',
                        bottom: '-4px',
                        left: '-4px',
                        background: '#10B981',
                        color: 'white',
                        fontSize: '8px',
                        borderRadius: '50%',
                        width: '14px',
                        height: '14px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        border: '2px solid white'
                    }}>
                        📤
                    </div>
                ) : null}

                {/* Tooltip avanzado */}
                <div
                    style={{
                        position: 'absolute',
                        bottom: '120%',
                        left: '50%',
                        transform: 'translateX(-50%)',
                        background: 'rgba(0, 0, 0, 0.95)',
                        color: 'white',
                        padding: '12px 14px',
                        borderRadius: '10px',
                        fontSize: '11px',
                        whiteSpace: 'nowrap' as const,
                        boxShadow: '0 6px 20px rgba(0,0,0,0.4)',
                        opacity: 0,
                        pointerEvents: 'none' as const,
                        transition: 'opacity 0.3s ease, transform 0.3s ease',
                        zIndex: 1000,
                        maxWidth: '250px',
                        transform: selected 
                            ? 'translateX(-50%) translateY(-5px) scale(1.02)' 
                            : 'translateX(-50%)'
                    }}
                    className="group-hover:opacity-100"
                >
                    {/* Header del tooltip */}
                    <div style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        marginBottom: '8px',
                        paddingBottom: '6px',
                        borderBottom: '1px solid #374151'
                    }}>
                        <span style={{ fontSize: '16px', marginRight: '8px' }}>
                            {getAvatarEmoji()}
                        </span>
                        <div>
                            <div style={{ 
                                fontWeight: 'bold', 
                                color: isTarget ? '#00D4FF' : '#FFFFFF',
                                fontSize: '12px'
                            }}>
                                {formatNumber(number)}
                                {isTarget && <span style={{ color: '#F59E0B', marginLeft: '4px' }}>TARGET</span>}
                            </div>
                            <div style={{ 
                                fontSize: '9px', 
                                color: operatorColor,
                                marginTop: '2px'
                            }}>
                                {operator}
                            </div>
                        </div>
                    </div>
                    
                    {/* Estadísticas en grid */}
                    <div style={{ 
                        display: 'grid', 
                        gridTemplateColumns: 'auto 1fr', 
                        gap: '4px 10px', 
                        fontSize: '10px',
                        marginBottom: '8px'
                    }}>
                        <span>📊 Interacciones:</span>
                        <span style={{ 
                            fontWeight: 'bold',
                            color: isHighActivity ? '#EF4444' : isMediumActivity ? '#F59E0B' : '#FFFFFF'
                        }}>
                            {interactionCount}
                        </span>
                        
                        <span>📞 Entrantes:</span>
                        <span style={{ color: '#3B82F6' }}>{connections.incoming}</span>
                        
                        <span>📞 Salientes:</span>
                        <span style={{ color: '#10B981' }}>{connections.outgoing}</span>
                        
                        <span>⏱️ Total llamadas:</span>
                        <span>{Math.floor(callDuration / 60)}m {callDuration % 60}s</span>
                        
                        <span>🕐 Última actividad:</span>
                        <span style={{ 
                            color: isRecentActivity ? '#10B981' : '#9CA3AF',
                            fontWeight: isRecentActivity ? 'bold' : 'normal'
                        }}>
                            {formatRelativeTime(lastInteraction)}
                        </span>
                    </div>

                    {/* Información de ubicación */}
                    {(coordinates || hunterPoints.length > 0) && (
                        <div style={{ 
                            borderTop: '1px solid #374151',
                            paddingTop: '6px',
                            fontSize: '9px',
                            color: '#D1D5DB'
                        }}>
                            {coordinates && (
                                <div style={{ marginBottom: '3px' }}>
                                    📍 GPS: {coordinates.lat.toFixed(4)}, {coordinates.lon.toFixed(4)}
                                </div>
                            )}
                            {hunterPoints.length > 0 && (
                                <div>
                                    🗺️ {hunterPoints.length} ubicación{hunterPoints.length > 1 ? 'es' : ''} HUNTER
                                </div>
                            )}
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
                            borderLeft: '8px solid transparent',
                            borderRight: '8px solid transparent',
                            borderTop: '8px solid rgba(0, 0, 0, 0.95)'
                        }}
                    />
                </div>
            </div>

            {/* Estilos CSS para animaciones */}
            <style jsx>{`
                @keyframes rotate {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
                
                @keyframes pulse-green {
                    0% { opacity: 1; transform: scale(1); }
                    50% { opacity: 0.7; transform: scale(1.1); }
                    100% { opacity: 1; transform: scale(1); }
                }
            `}</style>
        </>
    );
};

export default memo(CircularAvatarNode);