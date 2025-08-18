/**
 * Componente PointChip - Chip Visual para Puntos HUNTER
 * 
 * Este componente renderiza chips consistentes visualmente para identificar
 * puntos HUNTER en la interfaz de usuario. Cada punto mantiene el mismo
 * color durante toda la sesión usando un sistema determinístico.
 */

import React from 'react';
import { getPointColor, getPointChipClasses, getPointOrdinal } from '../../utils/colorSystem';

interface PointChipProps {
    /** Nombre del punto HUNTER */
    punto: string;
    /** Texto a mostrar (por defecto es el nombre del punto) */
    displayText?: string;
    /** Tamaño del chip */
    size?: 'xs' | 'sm' | 'md' | 'lg';
    /** Si debe mostrar tooltip con información adicional */
    showTooltip?: boolean;
    /** Información adicional para el tooltip */
    tooltipInfo?: string;
    /** Clases CSS adicionales */
    className?: string;
    /** Callback cuando se hace clic en el chip */
    onClick?: () => void;
    /** Si el chip es clickeable */
    clickable?: boolean;
    /** ACTUALIZACIÓN UX BORIS: Si debe mostrar número ordinal */
    showOrdinal?: boolean;
}

/**
 * Obtiene las clases CSS para diferentes tamaños
 */
const getSizeClasses = (size: PointChipProps['size'] = 'sm'): string => {
    const sizeMap = {
        xs: 'px-1.5 py-0.5 text-xs',
        sm: 'px-2 py-1 text-xs',
        md: 'px-3 py-1.5 text-sm',
        lg: 'px-4 py-2 text-sm'
    };
    
    return sizeMap[size];
};

/**
 * Componente PointChip
 * 
 * Renderiza un chip visual que identifica consistentemente un punto HUNTER
 * con colores determinísticos y alto contraste para tema oscuro.
 */
const PointChip: React.FC<PointChipProps> = ({
    punto,
    displayText,
    size = 'sm',
    showTooltip = true,
    tooltipInfo,
    className = '',
    onClick,
    clickable = false,
    showOrdinal = false
}) => {
    // Validar entrada
    if (!punto || typeof punto !== 'string') {
        return (
            <span className="inline-flex items-center px-2 py-1 text-xs bg-gray-800 text-gray-400 rounded-md border border-gray-600">
                N/A
            </span>
        );
    }

    // ACTUALIZACIÓN UX BORIS: Obtener color, clases base y número ordinal
    const color = getPointColor(punto);
    const baseClasses = getPointChipClasses(punto);
    const sizeClasses = getSizeClasses(size);
    const ordinal = showOrdinal ? getPointOrdinal(punto) : null;
    
    // Combinar clases
    const combinedClasses = [
        baseClasses,
        sizeClasses,
        clickable && onClick ? 'cursor-pointer hover:scale-105' : 'cursor-default',
        clickable ? 'hover:shadow-sm' : '',
        className
    ].filter(Boolean).join(' ');

    // Texto a mostrar
    const text = displayText || punto;

    // ACTUALIZACIÓN UX BORIS: Información del tooltip con número ordinal
    const tooltipText = showTooltip 
        ? tooltipInfo || `${ordinal ? `${ordinal}. ` : ''}Punto HUNTER: ${punto} (${color.name})`
        : undefined;

    // Handler de clic
    const handleClick = () => {
        if (clickable && onClick) {
            onClick();
        }
    };

    return (
        <span
            className={`${combinedClasses} ${showOrdinal ? 'flex items-center gap-1' : ''}`}
            title={tooltipText}
            onClick={handleClick}
            role={clickable ? 'button' : undefined}
            tabIndex={clickable ? 0 : undefined}
            onKeyDown={clickable ? (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    handleClick();
                }
            } : undefined}
        >
            {/* ACTUALIZACIÓN UX BORIS: Número ordinal opcional con círculo fijo w-5 h-5 */}
            {showOrdinal && ordinal && (
                <div className="w-5 h-5 bg-gray-600 text-gray-200 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">
                    {ordinal}
                </div>
            )}
            <span className={showOrdinal && ordinal ? 'flex-1' : ''}>{text}</span>
        </span>
    );
};

export default PointChip;