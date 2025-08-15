import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { ConfirmationConfig, ConfirmationContextType } from '../types';
import ConfirmationModal from '../components/ui/ConfirmationModal';

/**
 * Contexto para el sistema de confirmación global de KRONOS
 * Permite mostrar modales de confirmación desde cualquier componente
 */
const ConfirmationContext = createContext<ConfirmationContextType | undefined>(undefined);

interface ConfirmationProviderProps {
    children: ReactNode;
}

/**
 * Provider del contexto de confirmación
 * Debe envolver la aplicación principal para proporcionar funcionalidad global
 */
export const ConfirmationProvider: React.FC<ConfirmationProviderProps> = ({ children }) => {
    const [isVisible, setIsVisible] = useState(false);
    const [config, setConfig] = useState<ConfirmationConfig | null>(null);
    const [resolvePromise, setResolvePromise] = useState<((value: boolean) => void) | null>(null);

    /**
     * Muestra un modal de confirmación y retorna una Promise<boolean>
     * @param confirmationConfig - Configuración del modal de confirmación
     * @returns Promise que resuelve true si se confirma, false si se cancela
     */
    const showConfirmation = useCallback((confirmationConfig: ConfirmationConfig): Promise<boolean> => {
        return new Promise((resolve) => {
            setConfig(confirmationConfig);
            setResolvePromise(() => resolve);
            setIsVisible(true);
        });
    }, []);

    /**
     * Oculta el modal de confirmación actual
     */
    const hideConfirmation = useCallback(() => {
        setIsVisible(false);
        setConfig(null);
        if (resolvePromise) {
            resolvePromise(false);
            setResolvePromise(null);
        }
    }, [resolvePromise]);

    /**
     * Maneja la confirmación del usuario
     */
    const handleConfirm = useCallback(async () => {
        if (config?.onConfirm) {
            try {
                await config.onConfirm();
            } catch (error) {
                console.error('Error en onConfirm:', error);
            }
        }

        if (resolvePromise) {
            resolvePromise(true);
            setResolvePromise(null);
        }
        
        setIsVisible(false);
        setConfig(null);
    }, [config, resolvePromise]);

    /**
     * Maneja la cancelación del usuario
     */
    const handleCancel = useCallback(() => {
        if (config?.onCancel) {
            try {
                config.onCancel();
            } catch (error) {
                console.error('Error en onCancel:', error);
            }
        }

        if (resolvePromise) {
            resolvePromise(false);
            setResolvePromise(null);
        }
        
        setIsVisible(false);
        setConfig(null);
    }, [config, resolvePromise]);

    const contextValue: ConfirmationContextType = {
        showConfirmation,
        hideConfirmation,
        isVisible
    };

    return (
        <ConfirmationContext.Provider value={contextValue}>
            {children}
            <ConfirmationModal
                isOpen={isVisible}
                config={config}
                onConfirm={handleConfirm}
                onCancel={handleCancel}
            />
        </ConfirmationContext.Provider>
    );
};

/**
 * Hook para usar el sistema de confirmación
 * @returns Objeto con funciones para mostrar/ocultar confirmaciones
 * 
 * @example
 * ```tsx
 * const { showConfirmation } = useConfirmation();
 * 
 * const handleDelete = async () => {
 *   const confirmed = await showConfirmation({
 *     type: 'destructive',
 *     title: 'Eliminar Misión',
 *     message: '¿Estás seguro de que deseas eliminar esta misión?',
 *     details: 'Esta acción no se puede deshacer. Todos los datos asociados se perderán permanentemente.',
 *     confirmText: 'Eliminar',
 *     cancelText: 'Cancelar'
 *   });
 *   
 *   if (confirmed) {
 *     // Proceder con la eliminación
 *   }
 * };
 * ```
 */
export const useConfirmation = (): ConfirmationContextType => {
    const context = useContext(ConfirmationContext);
    
    if (context === undefined) {
        throw new Error('useConfirmation debe ser usado dentro de un ConfirmationProvider');
    }
    
    return context;
};

/**
 * Funciones de utilidad para confirmaciones comunes en KRONOS
 */
export const confirmationPresets = {
    /**
     * Confirmación para eliminar misiones
     */
    deleteMission: (missionName: string): ConfirmationConfig => ({
        type: 'destructive',
        title: 'Eliminar Misión',
        message: `¿Estás seguro de que deseas eliminar la misión "${missionName}"?`,
        details: 'Esta acción no se puede deshacer. Todos los datos celulares y archivos asociados se perderán permanentemente.',
        confirmText: 'Eliminar Misión',
        cancelText: 'Cancelar',
        confirmButtonVariant: 'danger'
    }),

    /**
     * Confirmación para eliminar usuarios
     */
    deleteUser: (userName: string): ConfirmationConfig => ({
        type: 'destructive',
        title: 'Eliminar Usuario',
        message: `¿Estás seguro de que deseas eliminar al usuario "${userName}"?`,
        details: 'Esta acción no se puede deshacer. El usuario perderá acceso al sistema inmediatamente.',
        confirmText: 'Eliminar Usuario',
        cancelText: 'Cancelar',
        confirmButtonVariant: 'danger'
    }),

    /**
     * Confirmación para eliminar roles
     */
    deleteRole: (roleName: string): ConfirmationConfig => ({
        type: 'destructive',
        title: 'Eliminar Rol',
        message: `¿Estás seguro de que deseas eliminar el rol "${roleName}"?`,
        details: 'Esta acción no se puede deshacer. Los usuarios asignados a este rol perderán sus permisos asociados.',
        confirmText: 'Eliminar Rol',
        cancelText: 'Cancelar',
        confirmButtonVariant: 'danger'
    }),

    /**
     * Confirmación para eliminar archivos de datos
     */
    deleteDataFile: (fileName: string): ConfirmationConfig => ({
        type: 'warning',
        title: 'Eliminar Archivo de Datos',
        message: `¿Estás seguro de que deseas eliminar el archivo "${fileName}"?`,
        details: 'Esta acción no se puede deshacer. Todos los registros procesados de este archivo se perderán.',
        confirmText: 'Eliminar Archivo',
        cancelText: 'Cancelar',
        confirmButtonVariant: 'warning'
    }),

    /**
     * Confirmación para borrar datos celulares
     */
    clearCellularData: (recordCount: number): ConfirmationConfig => ({
        type: 'destructive',
        title: 'Borrar Datos Celulares',
        message: `¿Estás seguro de que deseas borrar ${recordCount} registros de datos celulares?`,
        details: 'Esta acción no se puede deshacer. Todos los datos de análisis y mediciones se perderán permanentemente.',
        confirmText: 'Borrar Datos',
        cancelText: 'Cancelar',
        confirmButtonVariant: 'danger'
    }),

    /**
     * Confirmación para operaciones de advertencia
     */
    warning: (title: string, message: string, details?: string): ConfirmationConfig => ({
        type: 'warning',
        title,
        message,
        details,
        confirmText: 'Continuar',
        cancelText: 'Cancelar',
        confirmButtonVariant: 'warning'
    }),

    /**
     * Confirmación para información general
     */
    info: (title: string, message: string, details?: string): ConfirmationConfig => ({
        type: 'info',
        title,
        message,
        details,
        confirmText: 'Aceptar',
        cancelText: 'Cancelar',
        confirmButtonVariant: 'primary'
    })
};