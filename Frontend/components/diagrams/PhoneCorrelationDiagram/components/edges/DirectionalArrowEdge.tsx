/**
 * Componente de edge direccional con flechas prominentes
 * Boris & Claude Code - 2025-08-21
 */

import React, { memo } from 'react';
import { EdgeProps, getStraightPath } from 'reactflow';
import { ConnectionData } from '../../types/correlation.types';
import { getConnectionColor, EDGE_COLOR_SCHEME } from '../../utils/colorSchemes';

interface DirectionalArrowEdgeProps extends EdgeProps<ConnectionData> {
    selected?: boolean;
    onClick?: (edgeId: string) => void;
    showLabels?: boolean;
    showCellIds?: boolean;
    animated?: boolean;
}

/**
 * Edge direccional con flechas prominentes para flujos claros
 */
const DirectionalArrowEdge: React.FC<DirectionalArrowEdgeProps> = ({
    id,
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    data,
    selected = false,
    onClick,
    showLabels = true,
    showCellIds = false,
    animated = false
}) => {
    if (!data) return null;

    const {
        callCount,
        totalDuration,
        direction,
        strengthWeight,
        cellIds,
        timeRange,
        interactions
    } = data;

    // Calcular path recto
    const [edgePath, labelX, labelY] = getStraightPath({
        sourceX,
        sourceY,
        sourcePosition,
        targetX,
        targetY,
        targetPosition
    });

    // Colores y estilos dinámicos
    const strokeColor = getConnectionColor(strengthWeight, direction, selected);
    const strokeWidth = Math.max(3, Math.min(15, strengthWeight * 1.5));
    const opacity = selected ? 1 : Math.max(0.7, strengthWeight / 10);

    // Calcular ángulo de la línea para orientar flechas
    const angle = Math.atan2(targetY - sourceY, targetX - sourceX);
    const degrees = (angle * 180) / Math.PI;

    // Tamaño de flechas basado en importancia
    const arrowSize = Math.max(8, Math.min(20, strokeWidth * 1.2));
    const arrowSpacing = Math.max(40, distance / 4);

    // Calcular distancia
    const distance = Math.sqrt(Math.pow(targetX - sourceX, 2) + Math.pow(targetY - sourceY, 2));

    // Formatear datos
    const formatDuration = (seconds: number): string => {
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        if (hours > 0) return `${hours}h ${minutes % 60}m`;
        return `${minutes}m`;
    };

    const formatTimeRange = (): string => {
        try {
            const start = new Date(timeRange.first);
            const end = new Date(timeRange.last);
            if (start.toDateString() === end.toDateString()) {
                return start.toLocaleDateString('es-ES', { 
                    month: '2-digit', 
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            }
            return `${start.toLocaleDateString('es-ES', { month: '2-digit', day: '2-digit' })} - ${end.toLocaleDateString('es-ES', { month: '2-digit', day: '2-digit' })}`;
        } catch {
            return 'N/A';
        }
    };

    // Calcular múltiples flechas para conexiones fuertes
    const getArrows = () => {
        const arrows: JSX.Element[] = [];
        const maxArrows = Math.min(5, Math.floor(strengthWeight / 2) + 1);
        
        for (let i = 0; i < maxArrows; i++) {
            const t = direction === 'outgoing' 
                ? 0.7 + (i * 0.1) 
                : direction === 'incoming'
                    ? 0.3 - (i * 0.1)
                    : 0.5 + (i % 2 === 0 ? i * 0.1 : -(i + 1) * 0.1);
            
            if (t < 0.1 || t > 0.9) continue;

            const arrowX = sourceX + (targetX - sourceX) * t;
            const arrowY = sourceY + (targetY - sourceY) * t;
            
            const currentArrowSize = arrowSize * (1 - i * 0.1);
            const arrowOpacity = opacity * (1 - i * 0.15);

            arrows.push(
                <polygon
                    key={`arrow-${i}`}
                    points={`0,0 -${currentArrowSize},-${currentArrowSize/2.5} -${currentArrowSize * 0.7},0 -${currentArrowSize},${currentArrowSize/2.5}`}
                    fill={strokeColor}
                    transform={`translate(${arrowX}, ${arrowY}) rotate(${degrees})`}
                    opacity={arrowOpacity}
                    style={{
                        filter: selected ? 'drop-shadow(0 0 4px rgba(245, 158, 11, 0.8))' : 'none'
                    }}
                />
            );
        }
        return arrows;
    };

    // Flechas bidireccionales
    const getBidirectionalArrows = () => {
        const arrows: JSX.Element[] = [];
        
        // Flechas hacia target
        const forwardArrows = Math.ceil(strengthWeight / 3);
        for (let i = 0; i < forwardArrows; i++) {
            const t = 0.6 + (i * 0.15);
            if (t > 0.9) break;
            
            const arrowX = sourceX + (targetX - sourceX) * t;
            const arrowY = sourceY + (targetY - sourceY) * t;
            
            arrows.push(
                <polygon
                    key={`forward-${i}`}
                    points={`0,0 -${arrowSize},-${arrowSize/2.5} -${arrowSize * 0.7},0 -${arrowSize},${arrowSize/2.5}`}
                    fill={EDGE_COLOR_SCHEME.outgoing}
                    transform={`translate(${arrowX}, ${arrowY}) rotate(${degrees})`}
                    opacity={opacity * 0.9}
                />
            );
        }
        
        // Flechas hacia source
        const backwardArrows = Math.ceil(strengthWeight / 3);
        for (let i = 0; i < backwardArrows; i++) {
            const t = 0.4 - (i * 0.15);
            if (t < 0.1) break;
            
            const arrowX = sourceX + (targetX - sourceX) * t;
            const arrowY = sourceY + (targetY - sourceY) * t;
            
            arrows.push(
                <polygon
                    key={`backward-${i}`}
                    points={`0,0 -${arrowSize},-${arrowSize/2.5} -${arrowSize * 0.7},0 -${arrowSize},${arrowSize/2.5}`}
                    fill={EDGE_COLOR_SCHEME.incoming}
                    transform={`translate(${arrowX}, ${arrowY}) rotate(${degrees + 180})`}
                    opacity={opacity * 0.9}
                />
            );
        }
        
        return arrows;
    };

    const handleClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        onClick?.(id);
    };

    return (
        <g onClick={handleClick} style={{ cursor: 'pointer' }}>
            {/* Path principal */}
            <path
                d={edgePath}
                stroke={strokeColor}
                strokeWidth={strokeWidth}
                fill="none"
                opacity={opacity}
                strokeLinecap="round"
                strokeLinejoin="round"
                style={{
                    transition: 'all 0.3s ease',
                    filter: selected ? 'drop-shadow(0 0 10px rgba(245, 158, 11, 0.6))' : 'none'
                }}
                strokeDasharray={animated ? "10,5" : "none"}
            >
                {animated && (
                    <animate
                        attributeName="stroke-dashoffset"
                        values="0;15;0"
                        dur="2s"
                        repeatCount="indefinite"
                    />
                )}
            </path>

            {/* Path de resplandor para selección */}
            {selected && (
                <path
                    d={edgePath}
                    stroke={EDGE_COLOR_SCHEME.selected}
                    strokeWidth={strokeWidth + 6}
                    fill="none"
                    opacity={0.4}
                    strokeLinecap="round"
                />
            )}

            {/* Línea de fondo más gruesa para conexiones fuertes */}
            {strengthWeight > 7 && (
                <path
                    d={edgePath}
                    stroke="rgba(255, 255, 255, 0.1)"
                    strokeWidth={strokeWidth + 4}
                    fill="none"
                    opacity={0.5}
                    strokeLinecap="round"
                />
            )}

            {/* Renderizar flechas según dirección */}
            {direction === 'bidirectional' ? getBidirectionalArrows() : getArrows()}

            {/* Indicador de intensidad (puntos sobre la línea) */}
            {strengthWeight > 5 && (
                <g>
                    {Array.from({ length: Math.min(5, Math.floor(strengthWeight / 2)) }, (_, i) => {
                        const t = 0.2 + (i * 0.15);
                        const dotX = sourceX + (targetX - sourceX) * t;
                        const dotY = sourceY + (targetY - sourceY) * t;
                        
                        return (
                            <circle
                                key={`intensity-dot-${i}`}
                                cx={dotX}
                                cy={dotY}
                                r={2 + (strengthWeight / 5)}
                                fill={strokeColor}
                                opacity={opacity * 0.6}
                            />
                        );
                    })}
                </g>
            )}

            {/* Etiqueta principal */}
            {showLabels && (
                <g>
                    {/* Fondo de la etiqueta */}
                    <rect
                        x={labelX - 30}
                        y={labelY - 15}
                        width={60}
                        height={30}
                        rx={15}
                        fill="rgba(0, 0, 0, 0.85)"
                        stroke={strokeColor}
                        strokeWidth={2}
                        opacity={selected ? 1 : 0.9}
                    />
                    
                    {/* Texto principal - cantidad de llamadas */}
                    <text
                        x={labelX}
                        y={labelY - 3}
                        textAnchor="middle"
                        fontSize="11"
                        fontWeight="bold"
                        fill="white"
                    >
                        {callCount}
                    </text>
                    
                    {/* Icono direccional */}
                    <text
                        x={labelX - 15}
                        y={labelY - 2}
                        textAnchor="middle"
                        fontSize="12"
                        fill={strokeColor}
                    >
                        {direction === 'incoming' ? '📥' : 
                         direction === 'outgoing' ? '📤' : '🔄'}
                    </text>
                    
                    {/* Texto secundario - duración */}
                    <text
                        x={labelX}
                        y={labelY + 9}
                        textAnchor="middle"
                        fontSize="8"
                        fill="#D1D5DB"
                    >
                        {formatDuration(totalDuration)}
                    </text>
                </g>
            )}

            {/* Etiqueta de IDs de celda */}
            {showCellIds && cellIds.length > 0 && (
                <g>
                    <rect
                        x={labelX - 35}
                        y={labelY + 25}
                        width={70}
                        height={18}
                        rx={9}
                        fill="rgba(75, 85, 99, 0.9)"
                        stroke="#9CA3AF"
                        strokeWidth={1}
                    />
                    <text
                        x={labelX - 25}
                        y={labelY + 31}
                        textAnchor="start"
                        fontSize="7"
                        fill="#D1D5DB"
                    >
                        Celdas:
                    </text>
                    <text
                        x={labelX - 25}
                        y={labelY + 39}
                        textAnchor="start"
                        fontSize="8"
                        fontWeight="bold"
                        fill="white"
                    >
                        {cellIds.length > 2 ? `${cellIds.length} ubicaciones` : cellIds.join(' → ')}
                    </text>
                </g>
            )}

            {/* Badge de frecuencia para conexiones muy activas */}
            {callCount > 10 && (
                <g>
                    <circle
                        cx={labelX + 25}
                        cy={labelY - 10}
                        r={8}
                        fill="#EF4444"
                        stroke="white"
                        strokeWidth={2}
                    />
                    <text
                        x={labelX + 25}
                        y={labelY - 7}
                        textAnchor="middle"
                        fontSize="8"
                        fontWeight="bold"
                        fill="white"
                    >
                        🔥
                    </text>
                </g>
            )}

            {/* Tooltip detallado en hover */}
            <g
                opacity={0}
                style={{
                    transition: 'opacity 0.3s ease',
                    pointerEvents: 'none'
                }}
                className="hover-tooltip"
            >
                <rect
                    x={labelX - 80}
                    y={labelY - 100}
                    width={160}
                    height={80}
                    rx={10}
                    fill="rgba(0, 0, 0, 0.95)"
                    stroke={strokeColor}
                    strokeWidth={2}
                />
                
                {/* Header del tooltip */}
                <text x={labelX} y={labelY - 80} textAnchor="middle" fontSize="12" fontWeight="bold" fill={strokeColor}>
                    {direction === 'incoming' ? '📥 Llamadas Entrantes' : 
                     direction === 'outgoing' ? '📤 Llamadas Salientes' : '🔄 Comunicación Bidireccional'}
                </text>
                
                {/* Estadísticas detalladas */}
                <text x={labelX - 70} y={labelY - 60} fontSize="10" fill="white">
                    📊 Total: {callCount} llamadas
                </text>
                <text x={labelX - 70} y={labelY - 48} fontSize="10" fill="white">
                    ⏱️ Duración: {formatDuration(totalDuration)}
                </text>
                <text x={labelX - 70} y={labelY - 36} fontSize="10" fill="white">
                    📅 Período: {formatTimeRange()}
                </text>
                <text x={labelX - 70} y={labelY - 24} fontSize="10" fill="white">
                    🎯 Intensidad: {strengthWeight}/10
                </text>
                
                {cellIds.length > 0 && (
                    <text x={labelX - 70} y={labelX - 12} fontSize="9" fill="#D1D5DB">
                        📡 Celdas: {cellIds.slice(0, 3).join(', ')}{cellIds.length > 3 ? '...' : ''}
                    </text>
                )}

                {/* Flecha del tooltip */}
                <polygon
                    points={`${labelX},${labelY - 20} ${labelX - 8},${labelY - 12} ${labelX + 8},${labelY - 12}`}
                    fill="rgba(0, 0, 0, 0.95)"
                />
            </g>

            {/* CSS para mostrar tooltip en hover */}
            <style jsx>{`
                g:hover .hover-tooltip {
                    opacity: 1 !important;
                }
            `}</style>
        </g>
    );
};

export default memo(DirectionalArrowEdge);