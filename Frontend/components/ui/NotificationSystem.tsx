import React, { useState, useEffect } from 'react';
import type { NotificationData } from '../../types';
import { useNotification } from '../../hooks/useNotification';

interface NotificationItemProps {
    notification: NotificationData;
    onRemove: (id: string) => void;
}

const NotificationItem: React.FC<NotificationItemProps> = ({ notification, onRemove }) => {
    const [isVisible, setIsVisible] = useState(false);
    const [showDetails, setShowDetails] = useState(false);
    const [timeRemaining, setTimeRemaining] = useState(notification.duration || 5000);

    // Animación de entrada
    useEffect(() => {
        const timer = setTimeout(() => setIsVisible(true), 100);
        return () => clearTimeout(timer);
    }, []);

    // Countdown para auto-close
    useEffect(() => {
        if (!notification.autoClose) return;

        const interval = setInterval(() => {
            setTimeRemaining(prev => {
                if (prev <= 100) {
                    handleRemove();
                    return 0;
                }
                return prev - 100;
            });
        }, 100);

        return () => clearInterval(interval);
    }, [notification.autoClose]);

    const handleRemove = () => {
        setIsVisible(false);
        setTimeout(() => onRemove(notification.id), 300);
    };

    const getIcon = () => {
        const iconMap = {
            success: '✅',
            error: '❌', 
            warning: '⚠️',
            info: 'ℹ️'
        };
        return iconMap[notification.type];
    };

    const getColorClasses = () => {
        const colorMap = {
            success: 'border-green-600 bg-green-900/20',
            error: 'border-red-600 bg-red-900/20',
            warning: 'border-yellow-600 bg-yellow-900/20',
            info: 'border-blue-600 bg-blue-900/20'
        };
        return colorMap[notification.type];
    };

    const getProgressColor = () => {
        const colorMap = {
            success: 'bg-green-600',
            error: 'bg-red-600',
            warning: 'bg-yellow-600',
            info: 'bg-blue-600'
        };
        return colorMap[notification.type];
    };

    const progressPercentage = notification.autoClose && notification.duration 
        ? ((timeRemaining / notification.duration) * 100) 
        : 0;

    return (
        <div
            className={`
                relative bg-secondary-light border-l-4 rounded-lg shadow-lg transition-all duration-300 ease-in-out
                ${isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-full'}
                ${getColorClasses()}
                w-full max-w-md mb-3
            `}
        >
            {/* Barra de progreso para auto-close */}
            {notification.autoClose && (
                <div className="absolute top-0 left-0 right-0 h-1 bg-secondary rounded-t-lg overflow-hidden">
                    <div
                        className={`h-full transition-all duration-100 ease-linear ${getProgressColor()}`}
                        style={{ width: `${progressPercentage}%` }}
                    />
                </div>
            )}

            <div className="p-4 pt-5">
                {/* Header */}
                <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center">
                        <span className="text-xl mr-3">{getIcon()}</span>
                        <div>
                            <h4 className="text-light font-semibold text-sm">{notification.title}</h4>
                            <p className="text-medium text-sm mt-1">{notification.message}</p>
                        </div>
                    </div>
                    <button
                        onClick={handleRemove}
                        className="text-medium hover:text-light transition-colors ml-2 flex-shrink-0"
                    >
                        ✕
                    </button>
                </div>

                {/* Detalles expandibles */}
                {notification.details && notification.details.length > 0 && (
                    <div className="mt-3">
                        <button
                            onClick={() => setShowDetails(!showDetails)}
                            className="text-xs text-medium hover:text-light transition-colors flex items-center"
                        >
                            <span className={`mr-1 transition-transform duration-200 ${showDetails ? 'rotate-90' : ''}`}>
                                ▶
                            </span>
                            {showDetails ? 'Ocultar detalles' : 'Ver detalles'}
                        </button>
                        
                        {showDetails && (
                            <div className="mt-2 p-3 bg-secondary rounded text-xs text-medium max-h-32 overflow-y-auto">
                                {notification.details.map((detail, index) => (
                                    <div key={index} className="mb-1 last:mb-0">
                                        {detail}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Timestamp */}
                <div className="mt-3 text-xs text-medium opacity-70">
                    {notification.timestamp.toLocaleTimeString()}
                </div>
            </div>
        </div>
    );
};

const NotificationSystem: React.FC = () => {
    const { notifications, removeNotification, clearAllNotifications } = useNotification();

    if (notifications.length === 0) return null;

    return (
        <div className="fixed top-4 right-4 z-50 max-w-md w-full">
            {/* Header con botón limpiar todo (solo si hay múltiples notificaciones) */}
            {notifications.length > 1 && (
                <div className="mb-3 flex justify-end">
                    <button
                        onClick={clearAllNotifications}
                        className="text-xs text-medium hover:text-light bg-secondary hover:bg-secondary-light 
                                 px-3 py-1 rounded transition-colors"
                    >
                        Limpiar todas ({notifications.length})
                    </button>
                </div>
            )}

            {/* Lista de notificaciones */}
            <div className="space-y-0">
                {notifications.map(notification => (
                    <NotificationItem
                        key={notification.id}
                        notification={notification}
                        onRemove={removeNotification}
                    />
                ))}
            </div>
        </div>
    );
};

export default NotificationSystem;