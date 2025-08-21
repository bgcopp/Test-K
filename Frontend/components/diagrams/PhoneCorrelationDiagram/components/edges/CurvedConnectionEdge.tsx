/**
 * Componente de edge curvo para conexiones suaves
 * Boris & Claude Code - 2025-08-21
 */

import React, { memo } from 'react';
import { EdgeProps, getStraightPath } from 'reactflow';
import { ConnectionData } from '../../types/correlation.types';
import { getConnectionColor, EDGE_COLOR_SCHEME } from '../../utils/colorSchemes';

interface CurvedConnectionEdgeProps extends EdgeProps<ConnectionData> {
    selected?: boolean;
    onClick?: (edgeId: string) => void;
    showLabels?: boolean;
    showCellIds?: boolean;
}

/**
 * Edge curvo optimizado para conexiones suaves y elegantes
 */
const CurvedConnectionEdge: React.FC<CurvedConnectionEdgeProps> = ({
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
    showCellIds = false
}) => {
    if (!data) return null;

    const {
        callCount,
        totalDuration,
        direction,
        strengthWeight,
        cellIds,
        timeRange
    } = data;

    // Calcular curvatura basada en distancia y dirección
    const dx = targetX - sourceX;
    const dy = targetY - sourceY;
    const distance = Math.sqrt(dx * dx + dy * dy);
    
    // Curvatura adaptativa: más curva para distancias cortas
    const curvature = Math.min(0.5, Math.max(0.1, 0.3 - (distance / 1000)));
    
    // Calcular puntos de control para la curva
    const controlPointOffset = distance * curvature;
    const angle = Math.atan2(dy, dx);
    const perpAngle = angle + Math.PI / 2;
    
    const cpX1 = sourceX + Math.cos(perpAngle) * controlPointOffset * 0.3;
    const cpY1 = sourceY + Math.sin(perpAngle) * controlPointOffset * 0.3;
    const cpX2 = targetX - Math.cos(perpAngle) * controlPointOffset * 0.3;
    const cpY2 = targetY - Math.sin(perpAngle) * controlPointOffset * 0.3;

    // Colores y estilos dinámicos
    const strokeColor = getConnectionColor(strengthWeight, direction, selected);
    const strokeWidth = Math.max(2, Math.min(12, strengthWeight * 1.2));
    const opacity = selected ? 1 : Math.max(0.6, strengthWeight / 10);

    // Crear path curvo con Bézier cúbica
    const edgePath = `M ${sourceX},${sourceY} C ${cpX1},${cpY1} ${cpX2},${cpY2} ${targetX},${targetY}`;

    // Calcular punto medio para etiquetas
    const t = 0.5; // Parámetro para punto medio en curva Bézier
    const labelX = Math.pow(1 - t, 3) * sourceX + 
                   3 * Math.pow(1 - t, 2) * t * cpX1 + 
                   3 * (1 - t) * Math.pow(t, 2) * cpX2 + 
                   Math.pow(t, 3) * targetX;
    const labelY = Math.pow(1 - t, 3) * sourceY + 
                   3 * Math.pow(1 - t, 2) * t * cpY1 + 
                   3 * (1 - t) * Math.pow(t, 2) * cpY2 + 
                   Math.pow(t, 3) * targetY;

    // Formatear duración
    const formatDuration = (seconds: number): string => {
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        if (hours > 0) return `${hours}h ${minutes % 60}m`;
        return `${minutes}m`;
    };

    // Formatear rango temporal
    const formatTimeRange = (): string => {
        try {
            const start = new Date(timeRange.first);
            const end = new Date(timeRange.last);
            const startStr = start.toLocaleDateString('es-ES', { month: '2-digit', day: '2-digit' });
            const endStr = end.toLocaleDateString('es-ES', { month: '2-digit', day: '2-digit' });
            return startStr === endStr ? startStr : `${startStr} - ${endStr}`;
        } catch {
            return 'N/A';
        }
    };

    const handleClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        onClick?.(id);
    };

    return (
        <g onClick={handleClick} style={{ cursor: 'pointer' }}>
            {/* Path principal de la conexión */}
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
                    filter: selected ? 'drop-shadow(0 0 8px rgba(245, 158, 11, 0.6))' : 'none'
                }}
            />

            {/* Path de resplandor para selección */}
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

            {/* Flecha direccional */}
            {direction !== 'bidirectional' && (
                <g>
                    {/* Calcular posición y rotación de la flecha */}
                    {(() => {
                        const arrowT = direction === 'outgoing' ? 0.9 : 0.1;
                        const arrowX = Math.pow(1 - arrowT, 3) * sourceX + 
                                      3 * Math.pow(1 - arrowT, 2) * arrowT * cpX1 + 
                                      3 * (1 - arrowT) * Math.pow(arrowT, 2) * cpX2 + 
                                      Math.pow(arrowT, 3) * targetX;
                        const arrowY = Math.pow(1 - arrowT, 3) * sourceY + 
                                      3 * Math.pow(1 - arrowT, 2) * arrowT * cpY1 + 
                                      3 * (1 - arrowT) * Math.pow(arrowT, 2) * cpY2 + 
                                      Math.pow(arrowT, 3) * targetY;
                        
                        // Calcular tangente para orientación
                        const tangentT = arrowT + 0.01;
                        const tangentX = Math.pow(1 - tangentT, 3) * sourceX + 
                                        3 * Math.pow(1 - tangentT, 2) * tangentT * cpX1 + 
                                        3 * (1 - tangentT) * Math.pow(tangentT, 2) * cpX2 + 
                                        Math.pow(tangentT, 3) * targetX;
                        const tangentY = Math.pow(1 - tangentT, 3) * sourceY + 
                                        3 * Math.pow(1 - tangentT, 2) * tangentT * cpY1 + 
                                        3 * (1 - tangentT) * Math.pow(tangentT, 2) * cpY2 + 
                                        Math.pow(tangentT, 3) * targetY;
                        
                        const arrowAngle = Math.atan2(tangentY - arrowY, tangentX - arrowX);
                        const arrowSize = Math.max(6, strokeWidth * 0.8);

                        return (
                            <polygon
                                points={`0,0 -${arrowSize},-${arrowSize/2} -${arrowSize},${arrowSize/2}`}
                                fill={strokeColor}
                                transform={`translate(${arrowX}, ${arrowY}) rotate(${arrowAngle * 180 / Math.PI})`}
                                opacity={opacity}
                            />
                        );
                    })()}
                </g>
            )}

            {/* Flechas bidireccionales */}
            {direction === 'bidirectional' && (
                <g>
                    {/* Flecha hacia target */}
                    {(() => {
                        const arrowT = 0.85;
                        const arrowX = Math.pow(1 - arrowT, 3) * sourceX + 
                                      3 * Math.pow(1 - arrowT, 2) * arrowT * cpX1 + 
                                      3 * (1 - arrowT) * Math.pow(arrowT, 2) * cpX2 + 
                                      Math.pow(arrowT, 3) * targetX;
                        const arrowY = Math.pow(1 - arrowT, 3) * sourceY + 
                                      3 * Math.pow(1 - arrowT, 2) * arrowT * cpY1 + 
                                      3 * (1 - arrowT) * Math.pow(arrowT, 2) * cpY2 + 
                                      Math.pow(arrowT, 3) * targetY;
                        
                        const tangentT = arrowT + 0.01;
                        const tangentX = Math.pow(1 - tangentT, 3) * sourceX + 
                                        3 * Math.pow(1 - tangentT, 2) * tangentT * cpX1 + 
                                        3 * (1 - tangentT) * Math.pow(tangentT, 2) * cpX2 + 
                                        Math.pow(tangentT, 3) * targetX;
                        const tangentY = Math.pow(1 - tangentT, 3) * sourceY + 
                                        3 * Math.pow(1 - tangentT, 2) * tangentT * cpY1 + 
                                        3 * (1 - tangentT) * Math.pow(tangentT, 2) * cpY2 + 
                                        Math.pow(tangentT, 3) * targetY;
                        
                        const arrowAngle = Math.atan2(tangentY - arrowY, tangentX - arrowX);
                        const arrowSize = Math.max(5, strokeWidth * 0.6);

                        return (
                            <polygon
                                points={`0,0 -${arrowSize},-${arrowSize/2} -${arrowSize},${arrowSize/2}`}
                                fill={strokeColor}
                                transform={`translate(${arrowX}, ${arrowY}) rotate(${arrowAngle * 180 / Math.PI})`}
                                opacity={opacity}
                            />
                        );
                    })()}

                    {/* Flecha hacia source */}
                    {(() => {
                        const arrowT = 0.15;
                        const arrowX = Math.pow(1 - arrowT, 3) * sourceX + 
                                      3 * Math.pow(1 - arrowT, 2) * arrowT * cpX1 + 
                                      3 * (1 - arrowT) * Math.pow(arrowT, 2) * cpX2 + 
                                      Math.pow(arrowT, 3) * targetX;
                        const arrowY = Math.pow(1 - arrowT, 3) * sourceY + 
                                      3 * Math.pow(1 - arrowT, 2) * arrowT * cpY1 + 
                                      3 * (1 - arrowT) * Math.pow(arrowT, 2) * cpY2 + 
                                      Math.pow(arrowT, 3) * targetY;
                        
                        const tangentT = arrowT - 0.01;
                        const tangentX = Math.pow(1 - tangentT, 3) * sourceX + 
                                        3 * Math.pow(1 - tangentT, 2) * tangentT * cpX1 + 
                                        3 * (1 - tangentT) * Math.pow(tangentT, 2) * cpX2 + 
                                        Math.pow(tangentT, 3) * targetX;
                        const tangentY = Math.pow(1 - tangentT, 3) * sourceY + 
                                        3 * Math.pow(1 - tangentT, 2) * tangentT * cpY1 + 
                                        3 * (1 - tangentT) * Math.pow(tangentT, 2) * cpY2 + 
                                        Math.pow(tangentT, 3) * targetY;
                        
                        const arrowAngle = Math.atan2(tangentY - arrowY, tangentX - arrowX);
                        const arrowSize = Math.max(5, strokeWidth * 0.6);

                        return (
                            <polygon
                                points={`0,0 -${arrowSize},-${arrowSize/2} -${arrowSize},${arrowSize/2}`}
                                fill={strokeColor}
                                transform={`translate(${arrowX}, ${arrowY}) rotate(${arrowAngle * 180 / Math.PI})`}
                                opacity={opacity}
                            />
                        );
                    })()}
                </g>
            )}

            {/* Etiqueta principal */}
            {showLabels && (
                <g>
                    {/* Fondo de la etiqueta */}
                    <rect
                        x={labelX - 25}
                        y={labelY - 12}
                        width={50}
                        height={24}
                        rx={12}
                        fill="rgba(0, 0, 0, 0.8)"
                        stroke={strokeColor}
                        strokeWidth={1}
                        opacity={selected ? 1 : 0.9}
                    />
                    
                    {/* Texto principal - cantidad de llamadas */}
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
                    
                    {/* Texto secundario - duración */}
                    <text
                        x={labelX}
                        y={labelY + 8}
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
                        x={labelX - 30}
                        y={labelY + 20}
                        width={60}
                        height={16}
                        rx={8}
                        fill="rgba(75, 85, 99, 0.9)"
                        stroke="#9CA3AF"
                        strokeWidth={1}
                    />
                    <text
                        x={labelX}
                        y={labelY + 30}
                        textAnchor="middle"
                        fontSize="8"
                        fill="white"
                    >
                        {cellIds.length > 2 ? `${cellIds.length} celdas` : cellIds.join(', ')}
                    </text>
                </g>
            )}

            {/* Tooltip en hover */}
            <g
                opacity={0}
                style={{
                    transition: 'opacity 0.3s ease',
                    pointerEvents: 'none'
                }}
                className="hover-tooltip"
            >
                <rect
                    x={labelX - 60}
                    y={labelY - 80}
                    width={120}
                    height={60}
                    rx={8}
                    fill="rgba(0, 0, 0, 0.95)"
                    stroke={strokeColor}
                    strokeWidth={2}
                />
                
                {/* Información detallada */}
                <text x={labelX} y={labelY - 60} textAnchor="middle" fontSize="10" fontWeight="bold" fill="white">
                    {callCount} llamadas
                </text>
                <text x={labelX} y={labelY - 48} textAnchor="middle" fontSize="9" fill="#D1D5DB">
                    Duración: {formatDuration(totalDuration)}
                </text>
                <text x={labelX} y={labelY - 36} textAnchor="middle" fontSize="8" fill="#9CA3AF">
                    {formatTimeRange()}
                </text>
                <text x={labelX} y={labelY - 24} textAnchor="middle" fontSize="8" fill={strokeColor}>
                    {direction === 'incoming' ? 'Entrantes' : 
                     direction === 'outgoing' ? 'Salientes' : 'Bidireccional'}
                </text>
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

export default memo(CurvedConnectionEdge);