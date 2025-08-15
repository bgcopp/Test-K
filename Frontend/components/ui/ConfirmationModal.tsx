import React, { useEffect } from 'react';
import { ConfirmationConfig, ConfirmationType } from '../../types';
import { ICONS } from '../../constants';

interface ConfirmationModalProps {
    isOpen: boolean;
    config: ConfirmationConfig | null;
    onConfirm: () => void;
    onCancel: () => void;
}

/**
 * Componente modal de confirmación moderno y profesional para KRONOS
 * Reemplaza los window.confirm() básicos con una interfaz enterprise elegante
 * 
 * Características:
 * - Diseño moderno con tema oscuro
 * - Diferentes tipos de confirmación (destructive, warning, info, danger)
 * - Iconos contextuales apropiados
 * - Animaciones suaves de entrada/salida
 * - Accesibilidad completa (A11y)
 * - Responsive design
 * - Escape key y backdrop click opcionales
 */
const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
    isOpen,
    config,
    onConfirm,
    onCancel
}) => {
    // Manejar tecla Escape
    useEffect(() => {
        const handleEscape = (event: KeyboardEvent) => {
            if (event.key === 'Escape' && isOpen) {
                onCancel();
            }
        };

        if (isOpen) {
            document.addEventListener('keydown', handleEscape);
            // Prevenir scroll del body cuando el modal está abierto
            document.body.style.overflow = 'hidden';
        }

        return () => {
            document.removeEventListener('keydown', handleEscape);
            document.body.style.overflow = 'unset';
        };
    }, [isOpen, onCancel]);

    if (!isOpen || !config) return null;

    /**
     * Obtiene el icono apropiado según el tipo de confirmación
     */
    const getIcon = (type: ConfirmationType) => {
        switch (type) {
            case 'destructive':
            case 'danger':
                return ICONS.alertTriangle;
            case 'warning':
                return ICONS.alertCircle;
            case 'info':
                return ICONS.info;
            default:
                return ICONS.alertCircle;
        }
    };

    /**
     * Obtiene las clases CSS para el icono según el tipo
     */
    const getIconClasses = (type: ConfirmationType) => {
        switch (type) {
            case 'destructive':
            case 'danger':
                return 'text-red-500 bg-red-100 dark:bg-red-900/20';
            case 'warning':
                return 'text-yellow-500 bg-yellow-100 dark:bg-yellow-900/20';
            case 'info':
                return 'text-blue-500 bg-blue-100 dark:bg-blue-900/20';
            default:
                return 'text-yellow-500 bg-yellow-100 dark:bg-yellow-900/20';
        }
    };

    /**
     * Obtiene las clases CSS para el botón de confirmar según el tipo
     */
    const getConfirmButtonClasses = (type: ConfirmationType) => {
        const variant = config.confirmButtonVariant;
        
        if (variant) {
            switch (variant) {
                case 'danger':
                    return 'bg-red-600 hover:bg-red-700 focus:ring-red-500';
                case 'warning':
                    return 'bg-yellow-600 hover:bg-yellow-700 focus:ring-yellow-500';
                case 'primary':
                    return 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500';
                case 'secondary':
                    return 'bg-slate-600 hover:bg-slate-700 focus:ring-slate-500';
                default:
                    return 'bg-red-600 hover:bg-red-700 focus:ring-red-500';
            }
        }

        // Fallback basado en el tipo de confirmación
        switch (type) {
            case 'destructive':
            case 'danger':
                return 'bg-red-600 hover:bg-red-700 focus:ring-red-500';
            case 'warning':
                return 'bg-yellow-600 hover:bg-yellow-700 focus:ring-yellow-500';
            case 'info':
                return 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500';
            default:
                return 'bg-red-600 hover:bg-red-700 focus:ring-red-500';
        }
    };

    /**
     * Manejar click en el backdrop
     */
    const handleBackdropClick = (event: React.MouseEvent) => {
        if (event.target === event.currentTarget && config.allowBackdropClick !== false) {
            onCancel();
        }
    };

    return (
        <div 
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            style={{ backgroundColor: 'rgba(0, 0, 0, 0.75)' }}
            onClick={handleBackdropClick}
            role="dialog"
            aria-modal="true"
            aria-labelledby="confirmation-title"
            aria-describedby="confirmation-message"
        >
            {/* Modal Container con animación */}
            <div 
                className="bg-slate-800 rounded-xl shadow-2xl border border-slate-700 w-full max-w-md transform transition-all duration-300 ease-out scale-100 opacity-100"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header con icono */}
                <div className="p-6 pb-4">
                    <div className="flex items-center gap-4">
                        {config.showIcon !== false && (
                            <div className={`p-3 rounded-full ${getIconClasses(config.type)}`}>
                                {getIcon(config.type)}
                            </div>
                        )}
                        <div className="flex-1">
                            <h3 
                                id="confirmation-title"
                                className="text-lg font-semibold text-slate-100"
                            >
                                {config.title}
                            </h3>
                        </div>
                    </div>
                </div>

                {/* Content */}
                <div className="px-6 pb-6">
                    <p 
                        id="confirmation-message"
                        className="text-slate-300 text-sm leading-relaxed mb-4"
                    >
                        {config.message}
                    </p>
                    
                    {config.details && (
                        <div className="bg-slate-900 rounded-lg p-3 mb-6">
                            <p className="text-slate-400 text-xs leading-relaxed">
                                {config.details}
                            </p>
                        </div>
                    )}

                    {/* Botones de acción */}
                    <div className="flex gap-3 justify-end">
                        <button
                            type="button"
                            onClick={onCancel}
                            className="px-4 py-2 text-sm font-medium text-slate-300 bg-slate-700 hover:bg-slate-600 border border-slate-600 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 focus:ring-offset-slate-800"
                        >
                            {config.cancelText || 'Cancelar'}
                        </button>
                        
                        <button
                            type="button"
                            onClick={onConfirm}
                            className={`px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-800 ${getConfirmButtonClasses(config.type)}`}
                            autoFocus
                        >
                            {config.confirmText || 'Confirmar'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ConfirmationModal;