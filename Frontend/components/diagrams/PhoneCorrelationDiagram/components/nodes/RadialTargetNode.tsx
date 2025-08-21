/**
 * Componente de nodo target central para modo radial
 * Boris & Claude Code - 2025-08-21
 */

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { PhoneNodeData } from '../../types/correlation.types';
import { NODE_COLOR_SCHEME, getOperatorColor } from '../../utils/colorSchemes';

interface RadialTargetNodeProps extends NodeProps<PhoneNodeData> {
    selected?: boolean;
    onClick?: (nodeId: string) => void;
    onDoubleClick?: (nodeId: string) => void;
}

/**
 * Nodo target central optimizado para layout radial
 */
const RadialTargetNode: React.FC<RadialTargetNodeProps> = ({
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
        hunterPoints
    } = data;

    // Formatear duración de llamadas
    const formatDuration = (seconds: number): string => {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        if (hours > 0) return `${hours}h ${minutes}m`;
        return `${minutes}m`;
    };

    // Calcular tamaño dinámico basado en importancia
    const baseSize = 80;
    const sizeMultiplier = Math.min(1.5, 1 + (interactionCount / 50));
    const nodeSize = baseSize * sizeMultiplier;

    // Estilos dinámicos
    const nodeStyles = {
        width: `${nodeSize}px`,
        height: `${nodeSize}px`,
        background: selected 
            ? `linear-gradient(135deg, ${NODE_COLOR_SCHEME.selected} 0%, ${NODE_COLOR_SCHEME.target} 100%)`
            : `linear-gradient(135deg, ${NODE_COLOR_SCHEME.target} 0%, rgba(0, 212, 255, 0.8) 100%)`,
        border: `3px solid ${getOperatorColor(operator)}`,
        borderRadius: '50%',
        boxShadow: selected 
            ? `0 0 25px ${NODE_COLOR_SCHEME.selected}66, inset 0 2px 10px rgba(255,255,255,0.2)`
            : '0 0 20px rgba(0, 212, 255, 0.4), inset 0 2px 10px rgba(255,255,255,0.2)',
        cursor: 'pointer',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        position: 'relative' as const,
        display: 'flex',
        flexDirection: 'column' as const,
        alignItems: 'center',
        justifyContent: 'center',
        color: 'white',
        fontWeight: 'bold',
        overflow: 'hidden'
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
            {/* Handles para conexiones - múltiples posiciones para mejor distribución */}
            <Handle
                type="target"
                position={Position.Top}
                id="top"
                style={{ opacity: 0 }}
            />
            <Handle
                type="target"
                position={Position.Right}
                id="right"
                style={{ opacity: 0 }}
            />
            <Handle
                type="target"
                position={Position.Bottom}
                id="bottom"
                style={{ opacity: 0 }}
            />
            <Handle
                type="target"
                position={Position.Left}
                id="left"
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
                {/* Anillo exterior para target */}
                <div
                    style={{
                        position: 'absolute',
                        top: '-8px',
                        left: '-8px',
                        right: '-8px',
                        bottom: '-8px',
                        border: `2px solid ${NODE_COLOR_SCHEME.target}40`,
                        borderRadius: '50%',
                        animation: selected ? 'pulse 2s infinite' : 'none'
                    }}
                />

                {/* Contenido principal del nodo */}
                <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    height: '100%',
                    textAlign: 'center',
                    padding: '4px'
                }}>
                    {/* Icono de target */}
                    <div style={{
                        fontSize: nodeSize > 60 ? '18px' : '14px',
                        marginBottom: '2px',
                        opacity: 0.9
                    }}>
                        🎯
                    </div>

                    {/* Número telefónico */}
                    <div style={{
                        fontSize: nodeSize > 80 ? '11px' : '9px',
                        fontWeight: 'bold',
                        lineHeight: 1.1,
                        marginBottom: '1px',
                        wordBreak: 'break-all' as const
                    }}>
                        {number.length > 10 ? `${number.slice(0, 10)}...` : number}
                    </div>

                    {/* Operador */}
                    <div style={{
                        fontSize: nodeSize > 80 ? '8px' : '7px',
                        opacity: 0.8,
                        fontWeight: 'normal'
                    }}>
                        {operator}
                    </div>

                    {/* Badge de interacciones */}
                    <div style={{
                        position: 'absolute',
                        top: '-2px',
                        right: '-2px',
                        background: '#FF6B6B',
                        color: 'white',
                        fontSize: '10px',
                        fontWeight: 'bold',
                        borderRadius: '50%',
                        width: '20px',
                        height: '20px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        border: '2px solid white',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                    }}>
                        {interactionCount > 99 ? '99+' : interactionCount}
                    </div>
                </div>

                {/* Tooltip con información detallada */}
                <div
                    style={{
                        position: 'absolute',
                        bottom: '110%',
                        left: '50%',
                        transform: 'translateX(-50%)',
                        background: 'rgba(0, 0, 0, 0.9)',
                        color: 'white',
                        padding: '8px 12px',
                        borderRadius: '6px',
                        fontSize: '12px',
                        whiteSpace: 'nowrap' as const,
                        boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                        opacity: 0,
                        pointerEvents: 'none' as const,
                        transition: 'opacity 0.2s',
                        zIndex: 1000
                    }}
                    className="group-hover:opacity-100"
                >
                    <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
                        📱 {number} (TARGET)
                    </div>
                    <div style={{ marginBottom: '2px' }}>
                        📊 {interactionCount} interacciones
                    </div>
                    <div style={{ marginBottom: '2px' }}>
                        ⏱️ {formatDuration(callDuration)} total
                    </div>
                    <div style={{ marginBottom: '2px' }}>
                        📡 {operator}
                    </div>
                    <div>
                        📞 {connections.incoming}↓ / {connections.outgoing}↑
                    </div>
                    {hunterPoints.length > 0 && (
                        <div style={{ marginTop: '4px', fontSize: '10px', opacity: 0.8 }}>
                            📍 {hunterPoints.length} ubicaciones HUNTER
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
                            borderTop: '6px solid rgba(0, 0, 0, 0.9)'
                        }}
                    />
                </div>
            </div>

            {/* Estilos CSS para animaciones */}
            <style jsx>{`
                @keyframes pulse {
                    0% { opacity: 0.4; transform: scale(1); }
                    50% { opacity: 0.8; transform: scale(1.05); }
                    100% { opacity: 0.4; transform: scale(1); }
                }
            `}</style>
        </>
    );
};

export default memo(RadialTargetNode);