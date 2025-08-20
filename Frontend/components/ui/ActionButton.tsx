import React from 'react';

interface ActionButtonProps {
    icon: string;
    onClick: () => void;
    tooltip: string;
    size?: 'sm' | 'md' | 'lg';
    variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
    disabled?: boolean;
    className?: string;
}

const ActionButton: React.FC<ActionButtonProps> = ({
    icon,
    onClick,
    tooltip,
    size = 'md',
    variant = 'primary',
    disabled = false,
    className = ''
}) => {
    const sizeClasses = {
        sm: 'w-8 h-8 text-sm',
        md: 'w-10 h-10 text-base',
        lg: 'w-12 h-12 text-lg'
    };

    const variantClasses = {
        primary: 'bg-primary hover:bg-primary-light text-white',
        secondary: 'bg-secondary-light hover:bg-gray-600 text-white',
        success: 'bg-green-600 hover:bg-green-700 text-white',
        warning: 'bg-yellow-600 hover:bg-yellow-700 text-white',
        danger: 'bg-red-600 hover:bg-red-700 text-white'
    };

    return (
        <div className="relative group">
            <button
                onClick={onClick}
                disabled={disabled}
                className={`
                    ${sizeClasses[size]} 
                    ${variantClasses[variant]}
                    rounded-lg flex items-center justify-center
                    transition-all duration-200 ease-in-out
                    disabled:opacity-50 disabled:cursor-not-allowed
                    hover:scale-105 active:scale-95
                    ${className}
                `}
            >
                <span className="flex items-center justify-center">
                    {icon}
                </span>
            </button>
            
            {/* Tooltip */}
            <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
                {tooltip}
                <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-800"></div>
            </div>
        </div>
    );
};

export default ActionButton;