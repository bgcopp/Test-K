import { useState, useEffect, useRef, useCallback } from 'react';
import { getApiMode } from '../services/api';

interface ConnectionState {
  isConnected: boolean;
  isShuttingDown: boolean;
  lastHeartbeat: Date | null;
  error: string | null;
}

interface UseEelConnectionResult extends ConnectionState {
  checkConnection: () => Promise<boolean>;
  markShuttingDown: () => void;
}

/**
 * Hook personalizado para monitorear el estado de conexión con el backend Eel
 * 
 * Características:
 * - Detección automática de pérdida de conexión
 * - Heartbeat periódico para verificar estado del backend
 * - Manejo graceful del proceso de shutdown
 * - Prevención de errores durante desconexión
 */
export function useEelConnection(): UseEelConnectionResult {
    const [connectionState, setConnectionState] = useState<ConnectionState>({
        isConnected: false,
        isShuttingDown: false,
        lastHeartbeat: null,
        error: null
    });

    const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
    const isCheckingRef = useRef(false);
    const shutdownInitiatedRef = useRef(false);

    /**
     * Verifica si la conexión con Eel está activa
     */
    const checkConnection = useCallback(async (): Promise<boolean> => {
        // Evitar múltiples verificaciones simultáneas
        if (isCheckingRef.current || shutdownInitiatedRef.current) {
            return connectionState.isConnected;
        }

        isCheckingRef.current = true;

        try {
            const { isEelMode, eelAvailable } = getApiMode();
            
            // En modo mock, siempre consideramos conectado
            if (!isEelMode) {
                setConnectionState(prev => ({
                    ...prev,
                    isConnected: true,
                    lastHeartbeat: new Date(),
                    error: null
                }));
                isCheckingRef.current = false;
                return true;
            }

            // Verificar disponibilidad básica de Eel
            if (!eelAvailable || !window.eel) {
                throw new Error('Eel no está disponible');
            }

            // Intentar una operación simple para verificar conectividad
            // Usamos una función que debería responder rápidamente
            await Promise.race([
                window.eel.get_users()(),
                new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('Timeout de conexión')), 2000)
                )
            ]);

            setConnectionState(prev => ({
                ...prev,
                isConnected: true,
                lastHeartbeat: new Date(),
                error: null
            }));

            isCheckingRef.current = false;
            return true;

        } catch (error) {
            console.warn('🔌 Pérdida de conexión con backend detectada:', error);
            
            setConnectionState(prev => ({
                ...prev,
                isConnected: false,
                error: error instanceof Error ? error.message : 'Error de conexión desconocido'
            }));

            isCheckingRef.current = false;
            return false;
        }
    }, [connectionState.isConnected]);

    /**
     * Marca que el shutdown ha sido iniciado
     */
    const markShuttingDown = useCallback(() => {
        console.log('🔄 Iniciando proceso de shutdown frontend');
        shutdownInitiatedRef.current = true;
        
        // Limpiar heartbeat
        if (heartbeatIntervalRef.current) {
            clearInterval(heartbeatIntervalRef.current);
            heartbeatIntervalRef.current = null;
        }

        setConnectionState(prev => ({
            ...prev,
            isShuttingDown: true,
            isConnected: false
        }));
    }, []);

    /**
     * Inicializar monitoreo de conexión
     */
    useEffect(() => {
        // Verificación inicial
        checkConnection();

        // Configurar heartbeat cada 30 segundos
        const startHeartbeat = () => {
            if (heartbeatIntervalRef.current) {
                clearInterval(heartbeatIntervalRef.current);
            }

            heartbeatIntervalRef.current = setInterval(() => {
                if (!shutdownInitiatedRef.current) {
                    checkConnection().catch(err => {
                        console.warn('❌ Error en heartbeat:', err);
                    });
                }
            }, 30000);
        };

        startHeartbeat();

        // Cleanup al desmontar
        return () => {
            if (heartbeatIntervalRef.current) {
                clearInterval(heartbeatIntervalRef.current);
                heartbeatIntervalRef.current = null;
            }
        };
    }, [checkConnection]);

    /**
     * Detectar cambios en la ventana para iniciar shutdown
     */
    useEffect(() => {
        const handleBeforeUnload = (event: BeforeUnloadEvent) => {
            // Solo prevenir si hay cambios no guardados
            // En Eel, generalmente no queremos prevenir el cierre
            if (connectionState.isShuttingDown) {
                return; // Permitir cierre durante shutdown
            }

            // Opcional: mostrar confirmación solo si hay datos no guardados
            // event.preventDefault();
            // return (event.returnValue = '¿Estás seguro de que quieres cerrar KRONOS?');
        };

        const handleUnload = () => {
            markShuttingDown();
        };

        // Agregar listeners solo en entorno Eel (no durante desarrollo)
        if (typeof window !== 'undefined' && window.eel) {
            window.addEventListener('beforeunload', handleBeforeUnload);
            window.addEventListener('unload', handleUnload);
        }

        return () => {
            if (typeof window !== 'undefined') {
                window.removeEventListener('beforeunload', handleBeforeUnload);
                window.removeEventListener('unload', handleUnload);
            }
        };
    }, [connectionState.isShuttingDown, markShuttingDown]);

    return {
        ...connectionState,
        checkConnection,
        markShuttingDown
    };
}

/**
 * Hook simplificado para componentes que solo necesitan saber el estado de conexión
 */
export function useConnectionStatus(): { isConnected: boolean; isShuttingDown: boolean } {
    const { isConnected, isShuttingDown } = useEelConnection();
    return { isConnected, isShuttingDown };
}