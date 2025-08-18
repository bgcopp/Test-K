/**
 * Componente CorrelationCellBadge - Badge para Celdas Relacionadas
 * 
 * Este componente renderiza badges para celdas relacionadas en el análisis
 * de correlación, combinando el color de rol (originador/receptor) con el
 * borde del punto HUNTER de origen para crear una conexión visual clara.
 */

import React from 'react';
import { getCorrelationCellClasses, getCellIdToPointMapping, getPointColor, getPointOrdinal } from '../../utils/colorSystem';

interface CorrelationCellBadgeProps {
    /** ID de la celda */
    cellId: string;
    /** Rol de la celda en la comunicación */
    role: 'originator' | 'receptor';
    /** Datos celulares para el mapeo Cell ID → Punto */
    cellularData: Array<{ cellId: string; punto: string }>;
    /** Texto a mostrar (por defecto es el cellId) */
    displayText?: string;
    /** Si debe mostrar tooltip con información completa */
    showTooltip?: boolean;
    /** Clases CSS adicionales */
    className?: string;
    /** Callback cuando se hace clic */
    onClick?: (cellId: string, punto: string | null) => void;
}

/**
 * Componente CorrelationCellBadge
 * 
 * Renderiza un badge que muestra:
 * - Color interno según rol (azul para originador, violeta para receptor)
 * - Borde del color del punto HUNTER asociado
 * - Tooltip con información completa
 */
const CorrelationCellBadge: React.FC<CorrelationCellBadgeProps> = ({
    cellId,
    role,
    cellularData,
    displayText,
    showTooltip = true,
    className = '',
    onClick
}) => {
    // Validar entrada
    if (!cellId) {
        return (
            <span className="px-2 py-1 text-xs bg-gray-800 text-gray-200 border border-gray-600 rounded font-mono">
                N/A
            </span>
        );
    }

    // Mapear Cell ID al punto HUNTER
    const puntoHunter = getCellIdToPointMapping(cellId, cellularData || []);
    
    // Obtener clases CSS con el sistema de colores
    const badgeClasses = getCorrelationCellClasses(cellId, role, cellularData || []);
    
    // Combinar con clases adicionales
    const finalClasses = [badgeClasses, className].filter(Boolean).join(' ');

    // Texto a mostrar
    const text = displayText || cellId;

    // Información del tooltip
    let tooltipText = '';
    if (showTooltip) {
        const roleLabel = role === 'originator' ? 'Originador' : 'Receptor';
        const hunterInfo = puntoHunter ? `\nPunto HUNTER: ${puntoHunter}` : '\nSin punto HUNTER asociado';
        const colorInfo = puntoHunter ? `\nColor: ${getPointColor(puntoHunter).name}` : '';
        
        tooltipText = `${roleLabel}: ${cellId}${hunterInfo}${colorInfo}`;
    }

    // Handler de clic
    const handleClick = () => {
        if (onClick) {
            onClick(cellId, puntoHunter);
        }
    };

    // Determinar si es clickeable
    const isClickable = Boolean(onClick);

    // ACTUALIZACIÓN UX BORIS: Obtener número ordinal del punto
    const ordinal = puntoHunter ? getPointOrdinal(puntoHunter) : null;

    return (
        <span
            className={`${finalClasses} ${isClickable ? 'cursor-pointer' : 'cursor-default'} flex items-center gap-1`}
            title={tooltipText}
            onClick={isClickable ? handleClick : undefined}
            role={isClickable ? 'button' : undefined}
            tabIndex={isClickable ? 0 : undefined}
            onKeyDown={isClickable ? (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    handleClick();
                }
            } : undefined}
        >
            {/* ACTUALIZACIÓN UX BORIS: Número ordinal a la izquierda con círculo fijo w-5 h-5 */}
            {ordinal && (
                <div className="w-5 h-5 bg-gray-600 text-gray-200 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">
                    {ordinal}
                </div>
            )}
            <span className="flex-1">{text}</span>
        </span>
    );
};

/**
 * Componente para mostrar múltiples badges de celdas relacionadas
 * Útil para la tabla de correlación
 */
interface CorrelationCellBadgeGroupProps {
    /** Array de cell IDs */
    cellIds: string[];
    /** Número objetivo para determinar roles */
    targetNumber: string;
    /** Datos celulares para mapeo */
    cellularData: Array<{ cellId: string; punto: string }>;
    /** Máximo número de badges a mostrar */
    maxDisplay?: number;
    /** Callback para clic en badge individual */
    onCellClick?: (cellId: string, punto: string | null) => void;
    /** Función para determinar el rol (debe coincidir con la del componente padre) */
    getCellRole?: (targetNumber: string, cellId: string) => 'originator' | 'receptor';
}

export const CorrelationCellBadgeGroup: React.FC<CorrelationCellBadgeGroupProps> = ({
    cellIds,
    targetNumber,
    cellularData,
    maxDisplay = 10,
    onCellClick,
    getCellRole
}) => {
    // Validar entrada
    if (!cellIds || cellIds.length === 0) {
        return (
            <span className="px-2 py-1 text-xs bg-gray-800 text-gray-200 rounded">
                Sin celdas
            </span>
        );
    }

    // Determinar rol usando la función proporcionada o una por defecto
    const determineCellRole = (cellId: string): 'originator' | 'receptor' => {
        if (getCellRole) {
            return getCellRole(targetNumber, cellId);
        }
        
        // Función por defecto (hash determinístico)
        const combined = `${targetNumber}-${cellId}`;
        let hash = 0;
        for (let i = 0; i < combined.length; i++) {
            const char = combined.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        return Math.abs(hash) % 2 === 0 ? 'originator' : 'receptor';
    };

    // Limitar número de badges mostrados
    const displayCells = cellIds.slice(0, maxDisplay);
    const hiddenCount = Math.max(0, cellIds.length - maxDisplay);

    return (
        <div className="flex flex-wrap gap-1 max-w-md">
            {displayCells.map((cellId, idx) => (
                <CorrelationCellBadge
                    key={idx}
                    cellId={cellId}
                    role={determineCellRole(cellId)}
                    cellularData={cellularData}
                    onClick={onCellClick}
                />
            ))}
            
            {hiddenCount > 0 && (
                <span 
                    className="px-2 py-1 text-xs bg-gray-700 text-gray-300 border border-gray-500 rounded font-mono"
                    title={`${hiddenCount} celda${hiddenCount > 1 ? 's' : ''} adicional${hiddenCount > 1 ? 'es' : ''}`}
                >
                    +{hiddenCount}
                </span>
            )}
        </div>
    );
};

export default CorrelationCellBadge;