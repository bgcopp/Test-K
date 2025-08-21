/**
 * Componente de nodo source para modo radial
 * Boris & Claude Code - 2025-08-21
 */

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { PhoneNodeData } from '../../types/correlation.types';
import { getNodeColor, getOperatorColor } from '../../utils/colorSchemes';

interface RadialSourceNodeProps extends NodeProps<PhoneNodeData> {
    selected?: boolean;
    onClick?: (nodeId: string) => void;
    onDoubleClick?: (nodeId: string) => void;
}

/**
 * Nodo source periférico para layout radial
 */
const RadialSourceNode: React.FC<RadialSourceNodeProps> = ({
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
        coordinates
    } = data;

    // Determinar nivel de actividad
    const isHighActivity = interactionCount > 10;
    const isMediumActivity = interactionCount > 5;
    const isRecentActivity = new Date(lastInteraction) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000); // últimos 7 días

    // Calcular tamaño basado en importancia
    const baseSize = 60;
    const importance = Math.min(1.5, 1 + (interactionCount / 30));
    const nodeSize = baseSize * importance;

    // Color principal del nodo
    const nodeColor = getNodeColor(false, selected, isRecentActivity, interactionCount);
    const operatorColor = getOperatorColor(operator);

    // Formatear duración
    const formatDuration = (seconds: number): string => {
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        if (hours > 0) return `${hours}h ${minutes % 60}m`;
        return `${minutes}m`;
    };

    // Formatear fecha relativa
    const formatRelativeTime = (dateStr: string): string => {
        try {
            const date = new Date(dateStr);
            const now = new Date();
            const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
            
            if (diffDays === 0) return 'Hoy';
            if (diffDays === 1) return 'Ayer';
            if (diffDays < 7) return `${diffDays}d`;
            if (diffDays < 30) return `${Math.floor(diffDays / 7)}sem`;
            return `${Math.floor(diffDays / 30)}mes`;
        } catch {
            return 'N/A';
        }
    };

    // Estilos dinámicos del nodo
    const nodeStyles = {
        width: `${nodeSize}px`,
        height: `${nodeSize}px`,
        background: selected 
            ? `linear-gradient(135deg, #F59E0B 0%, ${nodeColor} 100%)`
            : `linear-gradient(135deg, ${nodeColor} 0%, rgba(255,255,255,0.1) 100%)`,
        border: `2px solid ${selected ? '#F59E0B' : operatorColor}`,
        borderRadius: '50%',
        boxShadow: selected 
            ? '0 0 20px #F59E0B66, inset 0 2px 8px rgba(255,255,255,0.1)'
            : isHighActivity 
                ? '0 0 15px rgba(239, 68, 68, 0.3), inset 0 2px 8px rgba(255,255,255,0.1)'
                : '0 4px 12px rgba(0,0,0,0.2), inset 0 2px 8px rgba(255,255,255,0.1)',
        cursor: 'pointer',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        position: 'relative' as const,
        display: 'flex',
        flexDirection: 'column' as const,
        alignItems: 'center',
        justifyContent: 'center',
        color: 'white',
        overflow: 'hidden',
        transform: selected ? 'scale(1.1)' : 'scale(1)',
        zIndex: selected ? 10 : isHighActivity ? 5 : 1
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
            <Handle
                type="target"
                position={Position.Top}
                id="target-top"
                style={{ opacity: 0 }}
            />
            <Handle
                type="target"
                position={Position.Right}
                id="target-right"
                style={{ opacity: 0 }}
            />
            <Handle
                type="target"
                position={Position.Bottom}
                id="target-bottom"
                style={{ opacity: 0 }}
            />
            <Handle
                type="target"
                position={Position.Left}
                id="target-left"
                style={{ opacity: 0 }}
            />
            <Handle
                type="source"
                position={Position.Top}
                id="source-top"
                style={{ opacity: 0 }}
            />
            <Handle
                type="source"
                position={Position.Right}
                id="source-right"
                style={{ opacity: 0 }}
            />
            <Handle
                type="source"
                position={Position.Bottom}
                id="source-bottom"
                style={{ opacity: 0 }}
            />
            <Handle
                type="source"
                position={Position.Left}
                id="source-left"
                style={{ opacity: 0 }}
            />

            <div
                style={nodeStyles}
                onClick={handleClick}
                onDoubleClick={handleDoubleClick}
                className="group"
            >
                {/* Indicador de actividad reciente */}
                {isRecentActivity && (
                    <div
                        style={{
                            position: 'absolute',
                            top: '-3px',
                            right: '-3px',
                            width: '12px',
                            height: '12px',
                            background: '#10B981',
                            borderRadius: '50%',
                            border: '2px solid white',
                            boxShadow: '0 0 10px rgba(16, 185, 129, 0.5)'
                        }}
                        title="Actividad reciente"
                    />
                )}

                {/* Contenido principal */}
                <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    height: '100%',
                    textAlign: 'center',
                    padding: '4px'
                }}>
                    {/* Número telefónico truncado */}
                    <div style={{
                        fontSize: nodeSize > 70 ? '10px' : '8px',
                        fontWeight: 'bold',
                        lineHeight: 1.1,
                        marginBottom: '1px',
                        wordBreak: 'break-all' as const
                    }}>
                        {number.length > 8 ? `${number.slice(-8)}` : number}
                    </div>

                    {/* Indicador de operador */}
                    <div style={{
                        fontSize: nodeSize > 70 ? '7px' : '6px',
                        opacity: 0.8,
                        fontWeight: 'normal',
                        marginBottom: '2px'
                    }}>
                        {operator.slice(0, 4)}
                    </div>

                    {/* Contador de interacciones */}
                    <div style={{
                        fontSize: nodeSize > 70 ? '8px' : '7px',
                        fontWeight: 'bold',
                        opacity: 0.9
                    }}>
                        {interactionCount}
                    </div>
                </div>

                {/* Badge de nivel de actividad */}
                {isHighActivity && (
                    <div style={{
                        position: 'absolute',
                        top: '-2px',
                        left: '-2px',
                        background: '#EF4444',
                        color: 'white',
                        fontSize: '8px',
                        fontWeight: 'bold',
                        borderRadius: '50%',
                        width: '16px',
                        height: '16px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        border: '1px solid white'
                    }}>
                        🔥
                    </div>
                )}

                {/* Indicador de ubicación GPS */}
                {coordinates && (
                    <div style={{
                        position: 'absolute',
                        bottom: '-2px',
                        left: '-2px',
                        background: '#8B5CF6',
                        color: 'white',
                        fontSize: '8px',
                        borderRadius: '50%',
                        width: '14px',
                        height: '14px',
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
                        fontSize: '11px',
                        whiteSpace: 'nowrap' as const,
                        boxShadow: '0 4px 16px rgba(0,0,0,0.4)',
                        opacity: 0,
                        pointerEvents: 'none' as const,
                        transition: 'opacity 0.3s',
                        zIndex: 1000,
                        maxWidth: '220px'
                    }}
                    className="group-hover:opacity-100"
                >
                    <div style={{ fontWeight: 'bold', marginBottom: '6px', color: '#00D4FF' }}>
                        📱 {number}
                    </div>
                    
                    <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '4px 8px', fontSize: '10px' }}>
                        <span>📊 Interacciones:</span>
                        <span style={{ fontWeight: 'bold' }}>{interactionCount}</span>
                        
                        <span>⏱️ Duración total:</span>
                        <span>{formatDuration(callDuration)}</span>
                        
                        <span>📡 Operador:</span>
                        <span style={{ color: operatorColor }}>{operator}</span>
                        
                        <span>📞 Entrantes/Salientes:</span>
                        <span>{connections.incoming} / {connections.outgoing}</span>
                        
                        <span>🕐 Última actividad:</span>
                        <span style={{ color: isRecentActivity ? '#10B981' : '#9CA3AF' }}>
                            {formatRelativeTime(lastInteraction)}
                        </span>
                    </div>

                    {hunterPoints.length > 0 && (
                        <div style={{ 
                            marginTop: '6px', 
                            paddingTop: '6px', 
                            borderTop: '1px solid #374151',
                            fontSize: '9px',
                            color: '#D1D5DB'
                        }}>
                            📍 {hunterPoints.length} ubicación{hunterPoints.length > 1 ? 'es' : ''} HUNTER
                            {coordinates && (
                                <div style={{ marginTop: '2px', fontFamily: 'monospace' }}>
                                    GPS: {coordinates.lat.toFixed(4)}, {coordinates.lon.toFixed(4)}
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
                            borderLeft: '6px solid transparent',
                            borderRight: '6px solid transparent',
                            borderTop: '6px solid rgba(0, 0, 0, 0.95)'
                        }}
                    />
                </div>

                {/* Efecto hover */}
                <div
                    style={{
                        position: 'absolute',
                        inset: 0,
                        borderRadius: '50%',
                        background: 'rgba(255, 255, 255, 0.1)',
                        opacity: 0,
                        transition: 'opacity 0.2s'
                    }}
                    className="group-hover:opacity-100"
                />
            </div>
        </>
    );
};

export default memo(RadialSourceNode);