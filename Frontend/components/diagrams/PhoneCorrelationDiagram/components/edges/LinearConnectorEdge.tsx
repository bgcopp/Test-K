/**
 * Componente de edge lineal para conexiones directas y limpias
 * Boris & Claude Code - 2025-08-21
 */

import React, { memo } from 'react';
import { EdgeProps, getStraightPath } from 'reactflow';
import { ConnectionData } from '../../types/correlation.types';
import { getConnectionColor, EDGE_COLOR_SCHEME } from '../../utils/colorSchemes';

interface LinearConnectorEdgeProps extends EdgeProps<ConnectionData> {
    selected?: boolean;
    onClick?: (edgeId: string) => void;
    showLabels?: boolean;
    showCellIds?: boolean;
    minimalist?: boolean;
}

/**
 * Edge lineal optimizado para layouts secuenciales y minimalistas
 */
const LinearConnectorEdge: React.FC<LinearConnectorEdgeProps> = ({
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
    minimalist = false
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

    // Colores y estilos para modo minimalista
    const strokeColor = minimalist 
        ? (selected ? EDGE_COLOR_SCHEME.selected : '#6B7280')
        : getConnectionColor(strengthWeight, direction, selected);
    
    const strokeWidth = minimalist 
        ? (selected ? 4 : 2)
        : Math.max(2, Math.min(10, strengthWeight * 1.2));
    
    const opacity = selected ? 1 : (minimalist ? 0.6 : Math.max(0.6, strengthWeight / 10));

    // Calcular distancia para determinar estilo
    const distance = Math.sqrt(Math.pow(targetX - sourceX, 2) + Math.pow(targetY - sourceY, 2));
    const isShortConnection = distance < 100;

    // Formatear datos
    const formatDuration = (seconds: number): string => {
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return `${minutes}m`;
        const hours = Math.floor(minutes / 60);
        return `${hours}h ${minutes % 60}m`;
    };

    const formatCompactTime = (): string => {
        try {
            const start = new Date(timeRange.first);
            const end = new Date(timeRange.last);
            
            if (start.toDateString() === end.toDateString()) {
                return start.toLocaleDateString('es-ES', { month: '2-digit', day: '2-digit' });
            }
            
            const daysDiff = Math.floor((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
            if (daysDiff <= 7) return `${daysDiff}d`;
            if (daysDiff <= 30) return `${Math.floor(daysDiff / 7)}sem`;
            return `${Math.floor(daysDiff / 30)}mes`;
        } catch {
            return '';
        }
    };

    // Calcular ángulo para orientación de elementos
    const angle = Math.atan2(targetY - sourceY, targetX - sourceX);
    const degrees = (angle * 180) / Math.PI;

    // Determinar si debe mostrar flecha simple
    const showArrow = !minimalist && direction !== 'bidirectional';
    const arrowSize = Math.max(6, strokeWidth * 0.8);

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
                    filter: selected ? 'drop-shadow(0 0 8px rgba(245, 158, 11, 0.5))' : 'none'
                }}
                strokeDasharray={direction === 'bidirectional' && !minimalist ? "8,4" : "none"}
            />

            {/* Path de selección */}
            {selected && (
                <path
                    d={edgePath}
                    stroke={EDGE_COLOR_SCHEME.selected}
                    strokeWidth={strokeWidth + 4}
                    fill="none"
                    opacity={0.3}
                    strokeLinecap="round"
                />
            )}

            {/* Línea de intensidad para conexiones fuertes */}
            {!minimalist && strengthWeight > 6 && (
                <path
                    d={edgePath}
                    stroke="rgba(255, 255, 255, 0.15)"
                    strokeWidth={strokeWidth + 2}
                    fill="none"
                    opacity={0.4}
                    strokeLinecap="round"
                />
            )}

            {/* Flecha direccional simple */}
            {showArrow && (
                <g>
                    {(() => {
                        const arrowT = direction === 'outgoing' ? 0.85 : 0.15;
                        const arrowX = sourceX + (targetX - sourceX) * arrowT;
                        const arrowY = sourceY + (targetY - sourceY) * arrowT;
                        
                        return (
                            <polygon
                                points={`0,0 -${arrowSize},-${arrowSize/2} -${arrowSize},${arrowSize/2}`}
                                fill={strokeColor}
                                transform={`translate(${arrowX}, ${arrowY}) rotate(${degrees})`}
                                opacity={opacity}
                            />
                        );
                    })()}
                </g>
            )}

            {/* Indicadores de bidireccionalidad */}
            {!minimalist && direction === 'bidirectional' && (
                <g>
                    {/* Flecha hacia target */}
                    <polygon
                        points={`0,0 -${arrowSize},-${arrowSize/2} -${arrowSize},${arrowSize/2}`}
                        fill={EDGE_COLOR_SCHEME.outgoing}
                        transform={`translate(${sourceX + (targetX - sourceX) * 0.8}, ${sourceY + (targetY - sourceY) * 0.8}) rotate(${degrees})`}
                        opacity={opacity * 0.8}
                    />
                    
                    {/* Flecha hacia source */}
                    <polygon
                        points={`0,0 -${arrowSize},-${arrowSize/2} -${arrowSize},${arrowSize/2}`}
                        fill={EDGE_COLOR_SCHEME.incoming}
                        transform={`translate(${sourceX + (targetX - sourceX) * 0.2}, ${sourceY + (targetY - sourceY) * 0.2}) rotate(${degrees + 180})`}
                        opacity={opacity * 0.8}
                    />
                </g>
            )}

            {/* Etiqueta compacta */}
            {showLabels && !isShortConnection && (
                <g>
                    {minimalist ? (
                        /* Etiqueta minimalista */
                        <g>
                            <circle
                                cx={labelX}
                                cy={labelY}
                                r={10}
                                fill={selected ? EDGE_COLOR_SCHEME.selected : 'rgba(0, 0, 0, 0.7)'}
                                stroke={strokeColor}
                                strokeWidth={1}
                                opacity={0.9}
                            />
                            <text
                                x={labelX}
                                y={labelY + 3}
                                textAnchor="middle"
                                fontSize="9"
                                fontWeight="bold"
                                fill="white"
                            >
                                {callCount}
                            </text>
                        </g>
                    ) : (
                        /* Etiqueta estándar */
                        <g>
                            <rect
                                x={labelX - 20}
                                y={labelY - 10}
                                width={40}
                                height={20}
                                rx={10}
                                fill="rgba(0, 0, 0, 0.8)"
                                stroke={strokeColor}
                                strokeWidth={1}
                                opacity={selected ? 1 : 0.9}
                            />
                            
                            {/* Contador principal */}
                            <text
                                x={labelX}
                                y={labelY - 2}
                                textAnchor="middle"
                                fontSize="10"
                                fontWeight="bold"
                                fill="white"
                            >
                                {callCount}
                            </text>
                            
                            {/* Información temporal compacta */}
                            <text
                                x={labelX}
                                y={labelY + 7}
                                textAnchor="middle"
                                fontSize="7"
                                fill="#D1D5DB"
                            >
                                {formatCompactTime()}
                            </text>
                        </g>
                    )}
                </g>
            )}

            {/* Badge de intensidad para conexiones fuertes */}
            {!minimalist && strengthWeight > 8 && (
                <g>
                    <circle
                        cx={labelX + 15}
                        cy={labelY - 8}
                        r={6}
                        fill="#EF4444"
                        stroke="white"
                        strokeWidth={1}
                    />
                    <text
                        x={labelX + 15}
                        y={labelY - 5}
                        textAnchor="middle"
                        fontSize="8"
                        fill="white"
                    >
                        ⚡
                    </text>
                </g>
            )}

            {/* Etiqueta de IDs de celda (compacta) */}
            {showCellIds && cellIds.length > 0 && !minimalist && (
                <g>
                    <rect
                        x={labelX - 25}
                        y={labelY + 15}
                        width={50}
                        height={14}
                        rx={7}
                        fill="rgba(75, 85, 99, 0.8)"
                        stroke="#9CA3AF"
                        strokeWidth={1}
                    />
                    <text
                        x={labelX}
                        y={labelY + 24}
                        textAnchor="middle"
                        fontSize="7"
                        fill="white"
                    >
                        {cellIds.length === 1 ? cellIds[0] : `${cellIds.length} celdas`}
                    </text>
                </g>
            )}

            {/* Puntos de intensidad para conexiones muy fuertes */}
            {!minimalist && strengthWeight > 7 && (
                <g>
                    {Array.from({ length: Math.min(3, Math.floor(strengthWeight / 3)) }, (_, i) => {
                        const dotT = 0.3 + (i * 0.2);
                        const dotX = sourceX + (targetX - sourceX) * dotT;
                        const dotY = sourceY + (targetY - sourceY) * dotT;
                        
                        return (
                            <circle
                                key={`dot-${i}`}
                                cx={dotX}
                                cy={dotY}
                                r={1.5}
                                fill={strokeColor}
                                opacity={opacity * 0.7}
                            >
                                <animate
                                    attributeName="r"
                                    values="1.5;2.5;1.5"
                                    dur="2s"
                                    repeatCount="indefinite"
                                    begin={`${i * 0.5}s`}
                                />
                            </circle>
                        );
                    })}
                </g>
            )}

            {/* Tooltip simplificado en hover */}
            {!minimalist && (
                <g
                    opacity={0}
                    style={{
                        transition: 'opacity 0.3s ease',
                        pointerEvents: 'none'
                    }}
                    className="hover-tooltip"
                >
                    <rect
                        x={labelX - 50}
                        y={labelY - 60}
                        width={100}
                        height={50}
                        rx={8}
                        fill="rgba(0, 0, 0, 0.95)"
                        stroke={strokeColor}
                        strokeWidth={2}
                    />
                    
                    {/* Información esencial */}
                    <text x={labelX} y={labelY - 40} textAnchor="middle" fontSize="10" fontWeight="bold" fill="white">
                        {callCount} llamadas
                    </text>
                    <text x={labelX} y={labelY - 28} textAnchor="middle" fontSize="9" fill="#D1D5DB">
                        {formatDuration(totalDuration)}
                    </text>
                    <text x={labelX} y={labelY - 16} textAnchor="middle" fontSize="8" fill={strokeColor}>
                        {direction === 'incoming' ? 'Entrantes' : 
                         direction === 'outgoing' ? 'Salientes' : 'Bidireccional'}
                    </text>
                    
                    {/* Flecha del tooltip */}
                    <polygon
                        points={`${labelX},${labelY - 10} ${labelX - 5},${labelY - 5} ${labelX + 5},${labelY - 5}`}
                        fill="rgba(0, 0, 0, 0.95)"
                    />
                </g>
            )}

            {/* CSS para mostrar tooltip en hover */}
            <style jsx>{`
                g:hover .hover-tooltip {
                    opacity: 1 !important;
                }
            `}</style>
        </g>
    );
};

export default memo(LinearConnectorEdge);