import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    children?: React.ReactNode;
    variant?: 'primary' | 'secondary' | 'danger';
    size?: 'sm' | 'md' | 'lg';
    icon?: React.ReactNode;
}

const Button: React.FC<ButtonProps> = ({ children, variant = 'primary', size = 'md', icon, ...props }) => {
    const baseClasses = 'rounded-md font-semibold inline-flex items-center justify-center transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed';
    
    const variantClasses = {
        primary: 'bg-primary text-white hover:bg-primary-hover',
        secondary: 'bg-secondary-light text-light hover:bg-gray-600',
        danger: 'bg-red-600 text-white hover:bg-red-700',
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

    return (
        <button className={`${baseClasses} ${getSizeClasses()} ${variantClasses[variant]}`} {...props}>
            {icon && <span className={!isIconOnly ? "mr-2 -ml-1" : ""}>{icon}</span>}
            {children}
        </button>
    );
};

export default Button;
