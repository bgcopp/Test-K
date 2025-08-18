/**
 * Componente CorrelationLegend - Leyenda del Sistema Visual de Correlación
 * 
 * Este componente muestra una leyenda completa del sistema visual de correlación,
 * explicando los colores de roles (originador/receptor) y los bordes de puntos HUNTER.
 */

import React, { useState } from 'react';
import PointChip from './PointChip';
import CorrelationCellBadge from './CorrelationCellBadge';
import { getColorSystemStats, createPointOrdinalMap, getPointOrdinal } from '../../utils/colorSystem';
import { ICONS } from '../../constants';

interface CorrelationLegendProps {
    /** Datos celulares para mostrar ejemplos reales */
    cellularData?: Array<{ cellId: string; punto: string }>;
    /** Resultados de correlación reales para extraer puntos HUNTER únicos */
    correlationResults?: Array<{ relatedCells: string[] }>;
    /** Si debe mostrar estadísticas del sistema de colores */
    showStats?: boolean;
    /** Si debe ser colapsable */
    collapsible?: boolean;
    /** Estado inicial (expandido/colapsado) */
    defaultExpanded?: boolean;
}

/**
 * Componente CorrelationLegend
 * 
 * Renderiza una leyenda interactiva que explica:
 * - Colores de rol (azul/violeta) para originador/receptor
 * - Bordes de colores de puntos HUNTER
 * - Ejemplos con datos reales cuando están disponibles
 * - Estadísticas del sistema de colores (opcional)
 */
const CorrelationLegend: React.FC<CorrelationLegendProps> = ({
    cellularData = [],
    correlationResults = [],
    showStats = false,
    collapsible = true,
    defaultExpanded = true
}) => {
    const [isExpanded, setIsExpanded] = useState(defaultExpanded);

    // Obtener estadísticas del sistema de colores
    const colorStats = showStats ? getColorSystemStats() : null;

    // **ACTUALIZACIÓN UX BORIS**: Extraer puntos HUNTER únicos REALES con sistema ordinal
    const extractUniqueHunterPoints = () => {
        if (!correlationResults || correlationResults.length === 0) {
            return [];
        }
        
        // Obtener todas las celdas relacionadas de los resultados de correlación
        const allRelatedCells = new Set<string>();
        correlationResults.forEach(result => {
            (result.relatedCells || []).forEach(cellId => allRelatedCells.add(cellId));
        });
        
        // Mapear Cell IDs a sus puntos HUNTER originales usando cellularData
        const cellIdToPointMap = new Map<string, string>();
        cellularData.forEach(data => {
            cellIdToPointMap.set(data.cellId, data.punto);
        });
        
        // Extraer puntos únicos encontrados en correlación
        const realHunterPoints = Array.from(allRelatedCells)
            .map(cellId => cellIdToPointMap.get(cellId))
            .filter((punto): punto is string => punto !== undefined);
        
        const uniquePoints = Array.from(new Set(realHunterPoints));
        
        // NUEVO: Crear mapa ordinal para consistencia durante sesión
        const ordinalMap = createPointOrdinalMap(uniquePoints);
        
        return uniquePoints;
    };
    
    const realHunterPoints = extractUniqueHunterPoints();
    
    // Crear datos para mostrar en la leyenda (máximo 5 puntos para no saturar UI)
    const displayData = realHunterPoints.slice(0, 5).map((punto, index) => {
        // Encontrar un Cell ID ejemplo para este punto
        const sampleCellData = cellularData.find(data => data.punto === punto);
        return {
            cellId: sampleCellData?.cellId || `ejemplo_${index}`,
            punto: punto
        };
    });
    
    // Datos de fallback solo si no hay resultados reales
    const fallbackData = [
        { cellId: '12345', punto: 'Punto_Ejemplo_A' },
        { cellId: '67890', punto: 'Punto_Ejemplo_B' }
    ];
    
    const finalDisplayData = displayData.length > 0 ? displayData : fallbackData;

    const toggleExpanded = () => {
        if (collapsible) {
            setIsExpanded(!isExpanded);
        }
    };

    return (
        <div className="mb-4 bg-secondary/50 rounded-lg border border-secondary-light overflow-hidden">
            {/* Header */}
            <div 
                className={`p-3 flex items-center justify-between ${
                    collapsible ? 'cursor-pointer hover:bg-secondary/70' : ''
                }`}
                onClick={collapsible ? toggleExpanded : undefined}
            >
                <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-light">
                        Sistema Visual de Correlación
                    </span>
                    {showStats && colorStats && (
                        <span className="px-2 py-1 text-xs bg-primary/20 text-primary rounded">
                            {colorStats.colorsInUse} colores activos
                        </span>
                    )}
                </div>
                
                {collapsible && (
                    <div className={`text-medium transition-transform duration-200 ${
                        isExpanded ? 'rotate-180' : ''
                    }`}>
                        {ICONS.chevronDown}
                    </div>
                )}
            </div>

            {/* Content */}
            {isExpanded && (
                <div className="px-3 pb-3 space-y-4">
                    {/* Explicación de roles */}
                    <div>
                        <h4 className="text-xs font-medium text-light mb-2">
                            Roles de Comunicación:
                        </h4>
                        <div className="flex items-center gap-6">
                            <div className="flex items-center gap-2">
                                <span className="px-2 py-1 text-xs bg-blue-500/20 text-blue-300 border border-blue-400/30 rounded font-mono">
                                    Originador
                                </span>
                                <span className="text-xs text-medium">Inició la llamada</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="px-2 py-1 text-xs bg-purple-500/20 text-purple-300 border border-purple-400/30 rounded font-mono">
                                    Receptor
                                </span>
                                <span className="text-xs text-medium">Recibió la llamada</span>
                            </div>
                        </div>
                    </div>

                    {/* Explicación de puntos HUNTER */}
                    <div>
                        <h4 className="text-xs font-medium text-light mb-2">
                            Identificación de Puntos HUNTER (Sistema Ordinal):
                        </h4>
                        <div className="space-y-2">
                            <div className="flex flex-wrap items-center gap-2">
                                {finalDisplayData.map((data, idx) => {
                                    const ordinal = getPointOrdinal(data.punto);
                                    return (
                                        <div key={idx} className="flex items-center gap-1">
                                            {/* Círculo ordinal - ACTUALIZACIÓN UX BORIS: w-5 h-5 fijo */}
                                            <div className="w-5 h-5 bg-gray-600 text-gray-200 rounded-full flex items-center justify-center text-xs font-bold">
                                                {ordinal || (idx + 1)}
                                            </div>
                                            <span className="text-xs text-light font-medium">
                                                {data.punto}
                                            </span>
                                            <PointChip 
                                                punto={data.punto}
                                                size="xs"
                                                showTooltip={false}
                                                showOrdinal={false}
                                            />
                                        </div>
                                    );
                                })}
                                {realHunterPoints.length === 0 && (
                                    <span className="text-xs text-medium italic">
                                        (Puntos de ejemplo - ejecute correlación para ver datos reales)
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Explicación de bordes de celdas - MEJORADA */}
                    <div>
                        <h4 className="text-xs font-medium text-light mb-2">
                            Conexión Visual Cell ID ↔ Punto HUNTER:
                        </h4>
                        <div className="space-y-2">
                            <div className="flex flex-wrap items-center gap-2">
                                {finalDisplayData.map((data, idx) => (
                                    <CorrelationCellBadge
                                        key={idx}
                                        cellId={data.cellId}
                                        role={idx % 2 === 0 ? 'originator' : 'receptor'}
                                        cellularData={cellularData}
                                        showTooltip={true}
                                        className="border-2" // **CORRECCIÓN UX**: Bordes más gruesos (2px) con mayor saturación
                                    />
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Estadísticas del sistema modernizadas - MEJORA UX BORIS */}
                    {showStats && colorStats && (
                        <div className="pt-3 border-t border-secondary-light">
                            <h4 className="text-sm font-medium text-light mb-3 flex items-center gap-2">
                                {ICONS.stats}
                                Estadísticas del Sistema
                            </h4>
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                                {/* Puntos HUNTER */}
                                <div className="bg-secondary-light/80 rounded-lg p-4 border border-secondary-light/50 hover:bg-secondary-light/90 transition-colors group">
                                    <div className="flex items-center justify-between mb-2">
                                        <div className="w-8 h-8 bg-blue-500/20 rounded-full flex items-center justify-center group-hover:bg-blue-500/30 transition-colors">
                                            {ICONS.target}
                                        </div>
                                        <div className="text-right">
                                            <div className="text-2xl font-bold text-blue-400 font-mono">{realHunterPoints.length}</div>
                                            <div className="text-xs text-medium -mt-1">puntos</div>
                                        </div>
                                    </div>
                                    <div className="text-sm font-medium text-light">Puntos HUNTER</div>
                                    <div className="text-xs text-medium">Identificados en correlación</div>
                                </div>

                                {/* Colores Activos */}
                                <div className="bg-secondary-light/80 rounded-lg p-4 border border-secondary-light/50 hover:bg-secondary-light/90 transition-colors group">
                                    <div className="flex items-center justify-between mb-2">
                                        <div className="w-8 h-8 bg-green-500/20 rounded-full flex items-center justify-center group-hover:bg-green-500/30 transition-colors">
                                            {ICONS.palette}
                                        </div>
                                        <div className="text-right">
                                            <div className="text-2xl font-bold text-green-400 font-mono">{colorStats.colorsInUse}</div>
                                            <div className="text-xs text-medium -mt-1">colores</div>
                                        </div>
                                    </div>
                                    <div className="text-sm font-medium text-light">Colores Activos</div>
                                    <div className="text-xs text-medium">Sistema visual ordenado</div>
                                </div>

                                {/* Objetivos Detectados */}
                                <div className="bg-secondary-light/80 rounded-lg p-4 border border-secondary-light/50 hover:bg-secondary-light/90 transition-colors group">
                                    <div className="flex items-center justify-between mb-2">
                                        <div className="w-8 h-8 bg-purple-500/20 rounded-full flex items-center justify-center group-hover:bg-purple-500/30 transition-colors">
                                            {ICONS.analysis}
                                        </div>
                                        <div className="text-right">
                                            <div className="text-2xl font-bold text-purple-400 font-mono">{correlationResults?.length || 0}</div>
                                            <div className="text-xs text-medium -mt-1">objetivos</div>
                                        </div>
                                    </div>
                                    <div className="text-sm font-medium text-light">Objetivos Detectados</div>
                                    <div className="text-xs text-medium">Correlaciones encontradas</div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default CorrelationLegend;