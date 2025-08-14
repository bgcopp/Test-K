import { useEffect, useRef, useCallback } from 'react';

interface CleanupHandler {
    id: string;
    cleanup: () => void;
    priority: 'high' | 'medium' | 'low';
    description?: string;
}

/**
 * Hook para gestión centralizada de cleanup de recursos React
 * 
 * Maneja la limpieza ordenada de:
 * - Timers (setTimeout, setInterval)
 * - Event listeners
 * - Subscriptions
 * - AbortControllers
 * - Referencias DOM
 * - Cualquier recurso personalizado
 */
export function useCleanup() {
    const cleanupHandlers = useRef<Map<string, CleanupHandler>>(new Map());
    const isCleaningUp = useRef(false);

    /**
     * Registra un handler de cleanup
     */
    const registerCleanup = useCallback((
        id: string,
        cleanup: () => void,
        priority: CleanupHandler['priority'] = 'medium',
        description?: string
    ) => {
        if (isCleaningUp.current) {
            console.warn(`⚠️ Intento de registrar cleanup durante limpieza: ${id}`);
            return;
        }

        cleanupHandlers.current.set(id, {
            id,
            cleanup,
            priority,
            description
        });

        console.log(`🧹 Cleanup registrado: ${id} (${priority}) - ${description || 'Sin descripción'}`);
    }, []);

    /**
     * Desregistra un handler de cleanup específico
     */
    const unregisterCleanup = useCallback((id: string) => {
        const removed = cleanupHandlers.current.delete(id);
        if (removed) {
            console.log(`🗑️ Cleanup desregistrado: ${id}`);
        }
        return removed;
    }, []);

    /**
     * Ejecuta cleanup de forma ordenada por prioridad
     */
    const executeCleanup = useCallback(() => {
        if (isCleaningUp.current) {
            return;
        }

        isCleaningUp.current = true;
        const handlers = Array.from(cleanupHandlers.current.values());
        
        if (handlers.length === 0) {
            console.log('🧹 No hay handlers de cleanup para ejecutar');
            return;
        }

        // Ordenar por prioridad: high -> medium -> low
        const priorityOrder = { high: 3, medium: 2, low: 1 };
        const sortedHandlers = handlers.sort((a, b) => 
            priorityOrder[b.priority] - priorityOrder[a.priority]
        );

        console.log(`🧹 Ejecutando cleanup de ${handlers.length} handlers`);

        for (const handler of sortedHandlers) {
            try {
                console.log(`   🔧 Limpiando: ${handler.id} (${handler.priority})`);
                handler.cleanup();
                console.log(`   ✅ Completado: ${handler.id}`);
            } catch (error) {
                console.error(`   ❌ Error en cleanup ${handler.id}:`, error);
            }
        }

        cleanupHandlers.current.clear();
        console.log('🧹 Cleanup completado');
    }, []);

    /**
     * Hook de conveniencia para registrar un timeout
     */
    const registerTimeout = useCallback((
        callback: () => void,
        delay: number,
        id?: string
    ): string => {
        const timeoutId = id || `timeout_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
        const timerId = setTimeout(callback, delay);

        registerCleanup(
            timeoutId,
            () => clearTimeout(timerId),
            'medium',
            `Timeout de ${delay}ms`
        );

        return timeoutId;
    }, [registerCleanup]);

    /**
     * Hook de conveniencia para registrar un interval
     */
    const registerInterval = useCallback((
        callback: () => void,
        delay: number,
        id?: string
    ): string => {
        const intervalId = id || `interval_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
        const timerId = setInterval(callback, delay);

        registerCleanup(
            intervalId,
            () => clearInterval(timerId),
            'high',
            `Interval de ${delay}ms`
        );

        return intervalId;
    }, [registerCleanup]);

    /**
     * Hook de conveniencia para registrar un event listener
     */
    const registerEventListener = useCallback((
        target: EventTarget,
        event: string,
        listener: EventListener,
        options?: AddEventListenerOptions,
        id?: string
    ): string => {
        const listenerId = id || `listener_${event}_${Date.now()}`;
        
        target.addEventListener(event, listener, options);

        registerCleanup(
            listenerId,
            () => target.removeEventListener(event, listener),
            'medium',
            `Event listener: ${event}`
        );

        return listenerId;
    }, [registerCleanup]);

    /**
     * Hook de conveniencia para registrar un AbortController
     */
    const registerAbortController = useCallback((
        controller: AbortController,
        id?: string,
        reason?: string
    ): string => {
        const controllerId = id || `controller_${Date.now()}`;

        registerCleanup(
            controllerId,
            () => {
                if (!controller.signal.aborted) {
                    controller.abort(reason || 'Cleanup durante shutdown');
                }
            },
            'high',
            `AbortController: ${reason || 'Sin razón'}`
        );

        return controllerId;
    }, [registerCleanup]);

    /**
     * Obtiene estadísticas de cleanup
     */
    const getCleanupStats = useCallback(() => {
        const handlers = Array.from(cleanupHandlers.current.values());
        const byPriority = handlers.reduce((acc, handler) => {
            acc[handler.priority] = (acc[handler.priority] || 0) + 1;
            return acc;
        }, {} as Record<string, number>);

        return {
            total: handlers.length,
            byPriority,
            isCleaningUp: isCleaningUp.current,
            handlers: handlers.map(h => ({ id: h.id, priority: h.priority, description: h.description }))
        };
    }, []);

    // Cleanup automático al desmontar el componente
    useEffect(() => {
        return () => {
            executeCleanup();
        };
    }, [executeCleanup]);

    return {
        registerCleanup,
        unregisterCleanup,
        executeCleanup,
        registerTimeout,
        registerInterval,
        registerEventListener,
        registerAbortController,
        getCleanupStats
    };
}

/**
 * Hook específico para cleanup de timers
 */
export function useTimerCleanup() {
    const { registerTimeout, registerInterval, executeCleanup } = useCleanup();

    const safeSetTimeout = useCallback((callback: () => void, delay: number, id?: string) => {
        return registerTimeout(callback, delay, id);
    }, [registerTimeout]);

    const safeSetInterval = useCallback((callback: () => void, delay: number, id?: string) => {
        return registerInterval(callback, delay, id);
    }, [registerInterval]);

    return {
        safeSetTimeout,
        safeSetInterval,
        cleanup: executeCleanup
    };
}

/**
 * Hook para recursos de almacenamiento local
 */
export function useStorageCleanup() {
    const { registerCleanup } = useCleanup();

    const registerStorageCleanup = useCallback((
        keys: string[],
        storage: 'localStorage' | 'sessionStorage' = 'localStorage'
    ) => {
        const storageObj = storage === 'localStorage' ? localStorage : sessionStorage;
        
        registerCleanup(
            `storage_${storage}_${keys.join('_')}`,
            () => {
                keys.forEach(key => {
                    try {
                        storageObj.removeItem(key);
                        console.log(`🗑️ ${storage} limpiado: ${key}`);
                    } catch (error) {
                        console.warn(`⚠️ Error limpiando ${storage} key "${key}":`, error);
                    }
                });
            },
            'low',
            `${storage} keys: ${keys.join(', ')}`
        );
    }, [registerCleanup]);

    return { registerStorageCleanup };
}