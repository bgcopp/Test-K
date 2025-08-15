import React, { useState, useCallback } from 'react';
import type { NotificationData, NotificationType, FileProcessingResult } from '../types';

// Estado global para notificaciones (singleton pattern)
let globalNotifications: NotificationData[] = [];
let notificationListeners: Set<(notifications: NotificationData[]) => void> = new Set();

const generateId = () => `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

// Función para notificar a todos los listeners
const notifyListeners = () => {
    notificationListeners.forEach(listener => listener([...globalNotifications]));
};

// Funciones globales para gestionar notificaciones
const addNotification = (notification: Omit<NotificationData, 'id' | 'timestamp'>) => {
    const newNotification: NotificationData = {
        ...notification,
        id: generateId(),
        timestamp: new Date(),
        autoClose: notification.autoClose !== false, // default true
        duration: notification.duration || 5000 // default 5 segundos
    };

    globalNotifications.unshift(newNotification);
    
    // Limitar a máximo 5 notificaciones
    if (globalNotifications.length > 5) {
        globalNotifications = globalNotifications.slice(0, 5);
    }

    notifyListeners();

    // Auto-close si está habilitado
    if (newNotification.autoClose) {
        setTimeout(() => {
            removeNotification(newNotification.id);
        }, newNotification.duration);
    }

    return newNotification.id;
};

const removeNotification = (id: string) => {
    globalNotifications = globalNotifications.filter(n => n.id !== id);
    notifyListeners();
};

const clearAllNotifications = () => {
    globalNotifications = [];
    notifyListeners();
};

// Hook principal
export const useNotification = () => {
    const [notifications, setNotifications] = useState<NotificationData[]>([...globalNotifications]);

    // Registrar listener al montar el componente
    React.useEffect(() => {
        notificationListeners.add(setNotifications);
        
        return () => {
            notificationListeners.delete(setNotifications);
        };
    }, []);

    // Función genérica para mostrar notificaciones
    const showNotification = useCallback((
        type: NotificationType,
        title: string,
        message: string,
        options?: {
            details?: string[];
            autoClose?: boolean;
            duration?: number;
        }
    ) => {
        return addNotification({
            type,
            title,
            message,
            details: options?.details,
            autoClose: options?.autoClose,
            duration: options?.duration
        });
    }, []);

    // Funciones específicas por tipo
    const showSuccess = useCallback((title: string, message: string, options?: { details?: string[]; autoClose?: boolean; duration?: number }) => {
        return showNotification('success', title, message, options);
    }, [showNotification]);

    const showError = useCallback((title: string, message: string, options?: { details?: string[]; autoClose?: boolean; duration?: number }) => {
        return showNotification('error', title, message, { ...options, autoClose: false }); // Errores no se auto-cierran
    }, [showNotification]);

    const showWarning = useCallback((title: string, message: string, options?: { details?: string[]; autoClose?: boolean; duration?: number }) => {
        return showNotification('warning', title, message, options);
    }, [showNotification]);

    const showInfo = useCallback((title: string, message: string, options?: { details?: string[]; autoClose?: boolean; duration?: number }) => {
        return showNotification('info', title, message, options);
    }, [showNotification]);

    // Función especializada para resultados de procesamiento de archivos
    const showFileProcessingResult = useCallback((result: FileProcessingResult, success: boolean) => {
        const {
            fileName,
            fileType,
            processedRecords,
            failedRecords = 0,
            duplicatedRecords = 0,     // NUEVO: registros duplicados
            validationFailures = 0,   // NUEVO: errores de validación
            otherErrors = 0,          // NUEVO: otros errores
            totalRecords,
            processingTime,
            warnings = [],
            errors = []
        } = result;

        const total = totalRecords || (processedRecords + failedRecords);
        const successRate = total > 0 ? ((processedRecords / total) * 100).toFixed(1) : '0';
        const timeDisplay = processingTime ? `${(processingTime / 1000).toFixed(1)}s` : '';

        let type: NotificationType;
        let title: string;
        let message: string;
        let details: string[] = [];

        // Determinar tipo de notificación basado en tipos de errores
        if (!success || (total > 0 && processedRecords === 0)) {
            type = 'error';
        } else if ((validationFailures > 0 || otherErrors > 0) || warnings.length > 0) {
            // Solo warning si hay errores reales, no por duplicados
            type = 'warning';
        } else if (duplicatedRecords > 0 && failedRecords === duplicatedRecords) {
            // Si solo hay duplicados, mostrar como success con info adicional
            type = 'success';
        } else {
            type = 'success';
        }

        // Construir título
        title = `KRONOS - ${fileType}`;

        // Construir mensaje principal
        if (type === 'error') {
            message = `Error procesando archivo ${fileName}`;
        } else if (duplicatedRecords > 0 && failedRecords === duplicatedRecords) {
            // Mensaje específico para duplicados
            message = `${processedRecords}/${total} registros únicos procesados${timeDisplay ? ` en ${timeDisplay}` : ''}`;
        } else {
            message = `${processedRecords}/${total} registros procesados${timeDisplay ? ` en ${timeDisplay}` : ''}`;
        }

        // Construir detalles
        details.push(`📄 Archivo: ${fileName}`);
        
        if (type !== 'error') {
            details.push(`✅ Procesados: ${processedRecords.toLocaleString()}`);
            
            // Mostrar información específica sobre duplicados y errores
            if (duplicatedRecords > 0) {
                details.push(`🔄 Duplicados omitidos: ${duplicatedRecords.toLocaleString()}`);
            }
            
            if (validationFailures > 0) {
                details.push(`❌ Errores de validación: ${validationFailures.toLocaleString()}`);
            }
            
            if (otherErrors > 0) {
                details.push(`⚠️ Otros errores: ${otherErrors.toLocaleString()}`);
            }
            
            if (total > 0) {
                details.push(`📊 Tasa de procesamiento: ${successRate}%`);
            }
            
            if (processingTime) {
                details.push(`⏱️ Tiempo: ${timeDisplay}`);
            }
            
            // Explicación especial para duplicados
            if (duplicatedRecords > 0 && failedRecords === duplicatedRecords) {
                details.push(`ℹ️ Los registros duplicados se omiten automáticamente`);
                details.push(`   para mantener la integridad de los datos`);
            }
        }

        // Agregar warnings y errores como detalles
        if (warnings.length > 0) {
            details.push('⚠️ Advertencias:');
            warnings.slice(0, 3).forEach(warning => details.push(`  • ${warning}`));
            if (warnings.length > 3) {
                details.push(`  • ... y ${warnings.length - 3} más`);
            }
        }

        if (errors.length > 0) {
            details.push('❌ Errores:');
            errors.slice(0, 3).forEach(error => details.push(`  • ${error}`));
            if (errors.length > 3) {
                details.push(`  • ... y ${errors.length - 3} más`);
            }
        }

        return showNotification(type, title, message, {
            details,
            autoClose: type === 'success' && failedRecords === 0,
            duration: type === 'success' ? 4000 : 8000
        });
    }, [showNotification]);

    return {
        notifications,
        showNotification,
        showSuccess,
        showError,
        showWarning,
        showInfo,
        showFileProcessingResult,
        removeNotification,
        clearAllNotifications
    };
};

export default useNotification;