import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    children?: React.ReactNode;
    variant?: 'primary' | 'secondary' | 'danger' | 'correlation';
    size?: 'sm' | 'md' | 'lg';
    icon?: React.ReactNode;
    loading?: boolean;
}

const Button: React.FC<ButtonProps> = ({ children, variant = 'primary', size = 'md', icon, loading = false, disabled, ...props }) => {
    const baseClasses = 'rounded-md font-semibold inline-flex items-center justify-center transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-dark';
    
    const variantClasses = {
        primary: 'bg-primary text-white hover:bg-primary-hover focus:ring-primary',
        secondary: 'bg-secondary-light text-light hover:bg-gray-600 focus:ring-gray-500',
        danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
        correlation: 'bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700 shadow-lg shadow-purple-500/25 hover:shadow-xl hover:shadow-purple-500/40 transform hover:scale-105 focus:ring-purple-500 relative overflow-hidden group',
    };

    // Función para obtener clases específicas del icono según variante
    const getIconClasses = () => {
        if (variant === 'correlation') {
            return 'transition-all duration-200 group-hover:scale-110 drop-shadow-sm';
        }
        return '';
    };

    const isIconOnly = !children && icon;
    
    const getSizeClasses = () => {
        if (isIconOnly) {
            return size === 'sm' ? 'p-1' : size === 'lg' ? 'p-3' : 'p-2';
        }
        
        switch (size) {
            case 'sm': return 'px-3 py-1 text-xs';
            case 'lg': return 'px-6 py-3 text-base';
            default: return 'px-4 py-2 text-sm';
        }
    };

    // Generar icono de loading con animación giratoria
    const loadingSpinner = (
        <svg className="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
    );

    const isDisabled = disabled || loading;
    const displayIcon = loading ? loadingSpinner : icon;

    return (
        <button 
            className={`${baseClasses} ${getSizeClasses()} ${variantClasses[variant]}`}
            disabled={isDisabled}
            {...props}
        >
            
            {displayIcon && (
                <span className={
                    !isIconOnly ? 
                        variant === 'correlation' ? 
                            `mr-3 -ml-0.5 ${getIconClasses()}` : 
                            "mr-2 -ml-1" 
                        : getIconClasses()
                }>
                    {/* Efecto glow sutil detrás del icono para variante correlation */}
                    {variant === 'correlation' && !loading && (
                        <span className="absolute inset-0 bg-white/10 rounded-full blur-sm scale-150 opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
                    )}
                    <span className="relative z-10">
                        {displayIcon}
                    </span>
                </span>
            )}
            {children}
        </button>
    );
};

export default Button;
