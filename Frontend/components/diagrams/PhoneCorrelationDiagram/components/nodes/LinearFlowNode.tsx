/**
 * Componente de nodo lineal para modo de flujo temporal
 * Boris & Claude Code - 2025-08-21
 */

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { PhoneNodeData } from '../../types/correlation.types';
import { getNodeColor, getOperatorColor, NODE_COLOR_SCHEME } from '../../utils/colorSchemes';

interface LinearFlowNodeProps extends NodeProps<PhoneNodeData> {
    selected?: boolean;
    onClick?: (nodeId: string) => void;
    onDoubleClick?: (nodeId: string) => void;
    orientation?: 'horizontal' | 'vertical';
    showTimestamp?: boolean;
}

/**
 * Nodo lineal optimizado para análisis secuencial y temporal
 */
const LinearFlowNode: React.FC<LinearFlowNodeProps> = ({
    id,
    data,
    selected = false,
    onClick,
    onDoubleClick,
    orientation = 'horizontal',
    showTimestamp = true
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

    // Características del nodo
    const isHighActivity = interactionCount > 8;
    const isMediumActivity = interactionCount > 3;
    const isRecentActivity = new Date(lastInteraction) > new Date(Date.now() - 24 * 60 * 60 * 1000); // últimas 24h

    // Tamaño dinámico basado en importancia
    const baseWidth = isTarget ? 120 : 100;
    const baseHeight = isTarget ? 70 : 50;
    const activityMultiplier = isHighActivity ? 1.2 : isMediumActivity ? 1.1 : 1;
    
    const nodeWidth = baseWidth * activityMultiplier;
    const nodeHeight = baseHeight * activityMultiplier;

    // Colores
    const nodeColor = isTarget 
        ? NODE_COLOR_SCHEME.target 
        : getNodeColor(false, selected, isRecentActivity, interactionCount);
    const operatorColor = getOperatorColor(operator);

    // Formateo de datos
    const formatNumber = (num: string): string => {
        if (num.length <= 10) return num;
        return `${num.slice(0, 3)} ${num.slice(3, 6)} ${num.slice(6)}`;
    };

    const formatTimestamp = (dateStr: string): string => {
        try {
            const date = new Date(dateStr);
            return date.toLocaleString('es-ES', {
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return 'N/A';
        }
    };

    const formatDuration = (seconds: number): string => {
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        if (hours > 0) return `${hours}h ${minutes % 60}m`;
        return `${minutes}m`;
    };

    // Determinar dirección predominante
    const getConnectionDirection = (): 'incoming' | 'outgoing' | 'balanced' => {
        const total = connections.incoming + connections.outgoing;
        if (total === 0) return 'balanced';
        
        const incomingRatio = connections.incoming / total;
        if (incomingRatio > 0.7) return 'incoming';
        if (incomingRatio < 0.3) return 'outgoing';
        return 'balanced';
    };

    const connectionDirection = getConnectionDirection();

    // Estilos del nodo
    const nodeStyles = {
        width: `${nodeWidth}px`,
        height: `${nodeHeight}px`,
        background: selected 
            ? `linear-gradient(135deg, ${NODE_COLOR_SCHEME.selected} 0%, ${nodeColor} 100%)`
            : isTarget
                ? `linear-gradient(135deg, ${nodeColor} 0%, rgba(0, 212, 255, 0.8) 100%)`
                : `linear-gradient(135deg, ${nodeColor} 0%, rgba(255,255,255,0.1) 100%)`,
        border: `2px solid ${selected ? NODE_COLOR_SCHEME.selected : operatorColor}`,
        borderRadius: isTarget ? '12px' : '8px',
        boxShadow: selected 
            ? `0 0 20px ${NODE_COLOR_SCHEME.selected}66, inset 0 2px 8px rgba(255,255,255,0.15)`
            : isTarget
                ? '0 0 15px rgba(0, 212, 255, 0.3), inset 0 2px 8px rgba(255,255,255,0.15)'
                : '0 4px 12px rgba(0,0,0,0.2), inset 0 2px 8px rgba(255,255,255,0.15)',
        cursor: 'pointer',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        position: 'relative' as const,
        display: 'flex',
        flexDirection: orientation === 'horizontal' ? 'row' as const : 'column' as const,
        alignItems: 'center',
        justifyContent: 'space-between',
        color: 'white',
        overflow: 'visible',
        transform: selected ? 'scale(1.05)' : 'scale(1)',
        zIndex: selected ? 15 : isTarget ? 10 : 5,
        padding: '8px 12px'
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
                {/* Indicador de target */}
                {isTarget && (
                    <div style={{
                        position: 'absolute',
                        top: '-6px',
                        left: '-6px',
                        background: NODE_COLOR_SCHEME.target,
                        borderRadius: '50%',
                        width: '20px',
                        height: '20px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '10px',
                        border: '2px solid white',
                        boxShadow: '0 0 10px rgba(0, 212, 255, 0.5)'
                    }}>
                        🎯
                    </div>
                )}

                {/* Contenido principal */}
                <div style={{
                    display: 'flex',
                    flexDirection: orientation === 'horizontal' ? 'row' : 'column',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    width: '100%',
                    height: '100%'
                }}>
                    {/* Sección izquierda/superior - Información del número */}
                    <div style={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: orientation === 'horizontal' ? 'flex-start' : 'center',
                        flex: 1,
                        minWidth: 0
                    }}>
                        {/* Número telefónico */}
                        <div style={{
                            fontSize: isTarget ? '11px' : '9px',
                            fontWeight: 'bold',
                            lineHeight: 1.1,
                            marginBottom: '2px',
                            textOverflow: 'ellipsis',
                            overflow: 'hidden',
                            whiteSpace: 'nowrap' as const,
                            maxWidth: '100%'
                        }}>
                            {isTarget ? formatNumber(number) : number.slice(-8)}
                        </div>

                        {/* Operador */}
                        <div style={{
                            fontSize: '7px',
                            opacity: 0.8,
                            color: operatorColor,
                            fontWeight: 'bold'
                        }}>
                            {operator}
                        </div>
                    </div>

                    {/* Sección central - Estadísticas */}
                    <div style={{
                        display: 'flex',
                        flexDirection: orientation === 'horizontal' ? 'column' : 'row',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '2px',
                        margin: orientation === 'horizontal' ? '0 8px' : '4px 0'
                    }}>
                        {/* Contador de interacciones */}
                        <div style={{
                            background: isHighActivity ? '#EF4444' : isMediumActivity ? '#F59E0B' : '#6B7280',
                            color: 'white',
                            fontSize: '8px',
                            fontWeight: 'bold',
                            padding: '2px 6px',
                            borderRadius: '10px',
                            minWidth: '18px',
                            textAlign: 'center'
                        }}>
                            {interactionCount}
                        </div>

                        {/* Indicador de dirección */}
                        <div style={{ fontSize: '10px' }}>
                            {connectionDirection === 'incoming' ? '📥' : 
                             connectionDirection === 'outgoing' ? '📤' : '🔄'}
                        </div>
                    </div>

                    {/* Sección derecha/inferior - Tiempo */}
                    <div style={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: orientation === 'horizontal' ? 'flex-end' : 'center',
                        fontSize: '7px',
                        opacity: 0.9,
                        textAlign: orientation === 'horizontal' ? 'right' : 'center'
                    }}>
                        {showTimestamp && (
                            <div style={{ marginBottom: '1px', fontWeight: 'bold' }}>
                                {formatTimestamp(lastInteraction)}
                            </div>
                        )}
                        <div style={{ color: '#D1D5DB' }}>
                            {formatDuration(callDuration)}
                        </div>
                    </div>
                </div>

                {/* Badges de estado */}
                
                {/* Badge de actividad reciente */}
                {isRecentActivity && (
                    <div style={{
                        position: 'absolute',
                        top: '-4px',
                        right: '-4px',
                        background: '#10B981',
                        borderRadius: '50%',
                        width: '10px',
                        height: '10px',
                        border: '1px solid white',
                        boxShadow: '0 0 8px rgba(16, 185, 129, 0.6)'
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
                        fontSize: '6px',
                        borderRadius: '50%',
                        width: '12px',
                        height: '12px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        border: '1px solid white'
                    }}>
                        📍
                    </div>
                )}

                {/* Tooltip detallado */}
                <div
                    style={{
                        position: 'absolute',
                        bottom: '110%',
                        left: '50%',
                        transform: 'translateX(-50%)',
                        background: 'rgba(0, 0, 0, 0.95)',
                        color: 'white',
                        padding: '10px 12px',
                        borderRadius: '8px',
                        fontSize: '10px',
                        whiteSpace: 'nowrap' as const,
                        boxShadow: '0 4px 16px rgba(0,0,0,0.4)',
                        opacity: 0,
                        pointerEvents: 'none' as const,
                        transition: 'opacity 0.3s ease',
                        zIndex: 1000,
                        maxWidth: '220px',
                        minWidth: '180px'
                    }}
                    className="group-hover:opacity-100"
                >
                    {/* Header */}
                    <div style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        marginBottom: '6px',
                        paddingBottom: '4px',
                        borderBottom: '1px solid #374151'
                    }}>
                        <span style={{ fontSize: '14px', marginRight: '6px' }}>
                            {isTarget ? '🎯' : '📱'}
                        </span>
                        <div>
                            <div style={{ 
                                fontWeight: 'bold', 
                                color: isTarget ? '#00D4FF' : '#FFFFFF',
                                fontSize: '11px'
                            }}>
                                {formatNumber(number)}
                                {isTarget && <span style={{ color: '#F59E0B', marginLeft: '4px' }}>TARGET</span>}
                            </div>
                        </div>
                    </div>
                    
                    {/* Timeline info */}
                    <div style={{ 
                        display: 'grid', 
                        gridTemplateColumns: 'auto 1fr', 
                        gap: '3px 8px', 
                        fontSize: '9px'
                    }}>
                        <span>📊 Interacciones:</span>
                        <span style={{ fontWeight: 'bold' }}>{interactionCount}</span>
                        
                        <span>⏱️ Duración total:</span>
                        <span>{formatDuration(callDuration)}</span>
                        
                        <span>📡 Operador:</span>
                        <span style={{ color: operatorColor }}>{operator}</span>
                        
                        <span>🕐 Última actividad:</span>
                        <span style={{ color: isRecentActivity ? '#10B981' : '#9CA3AF' }}>
                            {formatTimestamp(lastInteraction)}
                        </span>
                        
                        <span>📞 Dirección:</span>
                        <span>
                            {connections.incoming} entrantes / {connections.outgoing} salientes
                        </span>
                    </div>

                    {/* Ubicación si existe */}
                    {(coordinates || hunterPoints.length > 0) && (
                        <div style={{ 
                            borderTop: '1px solid #374151',
                            paddingTop: '4px',
                            marginTop: '6px',
                            fontSize: '8px',
                            color: '#D1D5DB'
                        }}>
                            {coordinates && (
                                <div>📍 GPS: {coordinates.lat.toFixed(4)}, {coordinates.lon.toFixed(4)}</div>
                            )}
                            {hunterPoints.length > 0 && (
                                <div>🗺️ {hunterPoints.length} ubicación{hunterPoints.length > 1 ? 'es' : ''} HUNTER</div>
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
                            borderLeft: '6px solid transparent',
                            borderRight: '6px solid transparent',
                            borderTop: '6px solid rgba(0, 0, 0, 0.95)'
                        }}
                    />
                </div>

                {/* Línea temporal inferior (opcional) */}
                {showTimestamp && (
                    <div style={{
                        position: 'absolute',
                        bottom: '-15px',
                        left: '50%',
                        transform: 'translateX(-50%)',
                        fontSize: '7px',
                        color: '#9CA3AF',
                        whiteSpace: 'nowrap' as const,
                        pointerEvents: 'none' as const
                    }}>
                        {formatTimestamp(lastInteraction)}
                    </div>
                )}
            </div>
        </>
    );
};

export default memo(LinearFlowNode);