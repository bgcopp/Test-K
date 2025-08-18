import { useState, useCallback } from 'react';

// Interface para el contexto del procesamiento
interface ProcessingContext {
    operation: string;
    recordCount?: number;
    operator?: string;
    dateRange?: {
        start: string;
        end: string;
    };
    additionalInfo?: string;
}

// Interface para el estado del procesamiento
interface ProcessingState {
    isVisible: boolean;
    contextMessage: string;
    startTime: number | null;
}

// Hook personalizado para manejar el overlay de procesamiento premium
export const useProcessingOverlay = () => {
    const [processingState, setProcessingState] = useState<ProcessingState>({
        isVisible: false,
        contextMessage: '',
        startTime: null
    });

    // Función para generar mensaje contextual dinámico
    const generateContextMessage = useCallback((context: ProcessingContext): string => {
        const { operation, recordCount, operator, dateRange, additionalInfo } = context;

        let message = `${operation}`;
        
        if (recordCount) {
            message += ` ${recordCount.toLocaleString()} registros`;
        }
        
        if (operator) {
            message += ` de ${operator.toUpperCase()}`;
        }
        
        if (dateRange) {
            const startDate = new Date(dateRange.start);
            const endDate = new Date(dateRange.end);
            
            // Formatear fechas en español
            const formatDate = (date: Date) => {
                const months = [
                    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
                ];
                
                return `${date.getDate()} de ${months[date.getMonth()]} ${date.getFullYear()}`;
            };
            
            if (startDate.toDateString() === endDate.toDateString()) {
                message += ` del ${formatDate(startDate)}`;
            } else {
                message += ` del ${formatDate(startDate)} al ${formatDate(endDate)}`;
            }
        }
        
        if (additionalInfo) {
            message += ` ${additionalInfo}`;
        }
        
        return message + '...';
    }, []);

    // Función para iniciar el procesamiento
    const startProcessing = useCallback((context: ProcessingContext) => {
        const contextMessage = generateContextMessage(context);
        
        setProcessingState({
            isVisible: true,
            contextMessage,
            startTime: Date.now()
        });
    }, [generateContextMessage]);

    // Función para detener el procesamiento
    const stopProcessing = useCallback(() => {
        setProcessingState(prev => ({
            ...prev,
            isVisible: false
        }));
        
        // Limpiar estado después de la animación de salida
        setTimeout(() => {
            setProcessingState({
                isVisible: false,
                contextMessage: '',
                startTime: null
            });
        }, 300);
    }, []);

    // Función para manejo de cancelación
    const handleCancel = useCallback(() => {
        // Aquí se podría implementar lógica para cancelar la operación en el backend
        console.log('🚫 Procesamiento cancelado por el usuario');
        stopProcessing();
    }, [stopProcessing]);

    // Función para manejo de timeout
    const handleTimeout = useCallback(() => {
        console.log('⏱️ Timeout alcanzado en el procesamiento');
        // El overlay permanece visible pero cambia a estado de timeout
        // La función stopProcessing debe ser llamada manualmente o cuando llegue la respuesta
    }, []);

    // Función helper para crear contexto de correlación específico
    const createCorrelationContext = useCallback((
        recordCount: number,
        operator: string,
        startDate: string,
        endDate: string,
        minOccurrences?: number
    ): ProcessingContext => {
        let additionalInfo = '';
        if (minOccurrences && minOccurrences > 1) {
            additionalInfo = `con mínimo ${minOccurrences} ocurrencias`;
        }

        return {
            operation: 'Correlacionando',
            recordCount,
            operator,
            dateRange: {
                start: startDate,
                end: endDate
            },
            additionalInfo
        };
    }, []);

    // Función helper para otros tipos de procesamiento
    const createProcessingContext = useCallback((
        operation: string,
        details?: Partial<ProcessingContext>
    ): ProcessingContext => {
        return {
            operation,
            ...details
        };
    }, []);

    return {
        // Estado
        isProcessing: processingState.isVisible,
        contextMessage: processingState.contextMessage,
        startTime: processingState.startTime,
        
        // Acciones
        startProcessing,
        stopProcessing,
        handleCancel,
        handleTimeout,
        
        // Helpers
        createCorrelationContext,
        createProcessingContext,
        
        // Estado completo para el componente
        processingState
    };
};

export default useProcessingOverlay;