import React from 'react';
import { ICONS } from '../../constants';

// Interface para los datos del nodo de persona
interface PersonNodeProps {
    id: string;
    number: string;
    name?: string;
    operator: string;
    correlationLevel: 'target' | 'high' | 'medium' | 'low' | 'indirect';
    interactionCount: number;
    isTarget: boolean;
    isSelected?: boolean;
    isHighlighted?: boolean;
    onClick?: (nodeId: string) => void;
    onDoubleClick?: (nodeId: string) => void;
    onHover?: (nodeId: string, hovered: boolean) => void;
}

// Configuración de colores y estilos por nivel de correlación
const correlationStyles = {
    target: {
        bg: 'bg-red-500',
        border: 'border-red-400',
        shadow: 'shadow-red-500/30',
        text: 'text-white',
        ring: 'ring-red-400',
        pulse: true
    },
    high: {
        bg: 'bg-orange-500',
        border: 'border-orange-400',
        shadow: 'shadow-orange-500/20',
        text: 'text-white',
        ring: 'ring-orange-400',
        pulse: false
    },
    medium: {
        bg: 'bg-yellow-500',
        border: 'border-yellow-400',
        shadow: 'shadow-yellow-500/20',
        text: 'text-white',
        ring: 'ring-yellow-400',
        pulse: false
    },
    low: {
        bg: 'bg-green-500',
        border: 'border-green-400',
        shadow: 'shadow-green-500/20',
        text: 'text-white',
        ring: 'ring-green-400',
        pulse: false
    },
    indirect: {
        bg: 'bg-purple-500',
        border: 'border-purple-400',
        shadow: 'shadow-purple-500/20',
        text: 'text-white',
        ring: 'ring-purple-400',
        pulse: false
    }
};

// Iconos por operador (mapeo de operadores colombianos conocidos)
const operatorIcons = {
    'CLARO': '📱',
    'MOVISTAR': '📶', 
    'TIGO': '🔵',
    'WOM': '🟣',
    'ETB': '🟢',
    'AVANTEL': '🔴',
    'VIRGIN': '❤️',
    'Default': '📞'
};

// Generar iniciales del nombre o número para avatar
const generateInitials = (name?: string, number?: string): string => {
    if (name) {
        const words = name.trim().split(' ');
        if (words.length >= 2) {
            return (words[0][0] + words[1][0]).toUpperCase();
        }
        return name.substring(0, 2).toUpperCase();
    }
    
    if (number) {
        // Para números, tomar los últimos 2 dígitos
        const cleanNumber = number.replace(/\D/g, '');
        return cleanNumber.slice(-2) || '??';
    }
    
    return '??';
};

const PersonNode: React.FC<PersonNodeProps> = ({
    id,
    number,
    name,
    operator,
    correlationLevel,
    interactionCount,
    isTarget,
    isSelected = false,
    isHighlighted = false,
    onClick,
    onDoubleClick,
    onHover
}) => {
    const style = correlationStyles[correlationLevel];
    const operatorIcon = operatorIcons[operator as keyof typeof operatorIcons] || operatorIcons.Default;
    const initials = generateInitials(name, number);
    
    // Formatear número para display (ej: +57 301 234 5678)
    const formatNumber = (num: string): string => {
        const cleaned = num.replace(/\D/g, '');
        if (cleaned.length === 10) {
            return `${cleaned.slice(0, 3)} ${cleaned.slice(3, 6)} ${cleaned.slice(6)}`;
        }
        if (cleaned.length === 12 && cleaned.startsWith('57')) {
            return `+57 ${cleaned.slice(2, 5)} ${cleaned.slice(5, 8)} ${cleaned.slice(8)}`;
        }
        return num;
    };

    const handleClick = () => {
        onClick?.(id);
    };

    const handleDoubleClick = () => {
        onDoubleClick?.(id);
    };

    const handleMouseEnter = () => {
        onHover?.(id, true);
    };

    const handleMouseLeave = () => {
        onHover?.(id, false);
    };

    return (
        <div
            className={`
                relative group cursor-pointer transform transition-all duration-200 hover:scale-110
                ${isHighlighted ? 'z-20' : 'z-10'}
            `}
            onClick={handleClick}
            onDoubleClick={handleDoubleClick}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
        >
            {/* Círculo principal del nodo */}
            <div
                className={`
                    w-16 h-16 rounded-full flex items-center justify-center
                    border-3 shadow-lg transition-all duration-300
                    ${style.bg} ${style.border} ${style.shadow}
                    ${isSelected ? `ring-4 ${style.ring} ring-opacity-60` : ''}
                    ${isHighlighted ? `ring-2 ${style.ring} ring-opacity-40` : ''}
                    ${style.pulse ? 'animate-pulse' : ''}
                    hover:shadow-xl hover:brightness-110
                `}
            >
                {/* Avatar con iniciales */}
                <span className={`font-bold text-sm ${style.text}`}>
                    {initials}
                </span>
                
                {/* Indicador de objetivo en esquina superior derecha */}
                {isTarget && (
                    <div className="absolute -top-1 -right-1 w-6 h-6 bg-red-600 rounded-full flex items-center justify-center border-2 border-white">
                        <span className="text-xs text-white font-bold">{ICONS.target}</span>
                    </div>
                )}
            </div>

            {/* Badge del operador */}
            <div className="absolute -bottom-2 -right-2 bg-gray-800 text-white text-xs px-2 py-1 rounded-full border border-gray-600 shadow-md">
                <span className="mr-1">{operatorIcon}</span>
                {operator}
            </div>

            {/* Contador de interacciones */}
            {interactionCount > 1 && (
                <div className="absolute -top-2 -left-2 bg-blue-600 text-white text-xs font-bold w-6 h-6 rounded-full flex items-center justify-center border-2 border-white shadow-md">
                    {interactionCount > 99 ? '99+' : interactionCount}
                </div>
            )}

            {/* Tooltip con información detallada */}
            <div className="absolute bottom-20 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white text-xs rounded-lg px-3 py-2 shadow-xl border border-gray-700 opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-30 whitespace-nowrap">
                <div className="font-semibold">{name || 'Sin nombre'}</div>
                <div className="text-cyan-300">{formatNumber(number)}</div>
                <div className="text-gray-400">{operator}</div>
                <div className="text-yellow-400">
                    {interactionCount} interaccion{interactionCount !== 1 ? 'es' : ''}
                </div>
                <div className={`font-medium capitalize ${
                    correlationLevel === 'target' ? 'text-red-300' :
                    correlationLevel === 'high' ? 'text-orange-300' :
                    correlationLevel === 'medium' ? 'text-yellow-300' :
                    correlationLevel === 'low' ? 'text-green-300' :
                    'text-purple-300'
                }`}>
                    {correlationLevel === 'target' ? 'Objetivo' :
                     correlationLevel === 'high' ? 'Correlación alta' :
                     correlationLevel === 'medium' ? 'Correlación media' :
                     correlationLevel === 'low' ? 'Correlación baja' :
                     'Correlación indirecta'}
                </div>
                
                {/* Punta del tooltip */}
                <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
            </div>

            {/* Efecto de resplandor para nodos seleccionados */}
            {isSelected && (
                <div className={`absolute inset-0 rounded-full ${style.bg} opacity-20 animate-ping`}></div>
            )}
        </div>
    );
};

export default PersonNode;