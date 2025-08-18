import React, { useState, useEffect } from 'react';
import { ICONS } from '../../constants';

// Interfaces para el componente de loading premium
interface ProcessingStage {
    id: string;
    title: string;
    description: string;
    duration: number; // duración en milisegundos
    icon: React.ReactNode;
}

interface PremiumProcessingOverlayProps {
    isVisible: boolean;
    contextMessage: string; // Ej: "Correlacionando 1,250 registros de CLARO del 20 al 22 de Mayo 2021..."
    onCancel?: () => void;
    onTimeout?: () => void;
    timeoutDuration?: number; // en milisegundos, default 3 minutos
}

// Etapas de procesamiento simuladas para correlación
const CORRELATION_STAGES: ProcessingStage[] = [
    {
        id: 'preparing',
        title: 'Preparando Análisis',
        description: 'Inicializando sistema de correlación y validando parámetros',
        duration: 15000, // 15 segundos
        icon: <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
    },
    {
        id: 'loading-data',
        title: 'Cargando Conjuntos de Datos',
        description: 'Accediendo a registros HUNTER y datos de operadores',
        duration: 20000, // 20 segundos
        icon: <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s8-1.79 8-4" />
        </svg>
    },
    {
        id: 'analyzing',
        title: 'Ejecutando Algoritmos de Correlación',
        description: 'Comparando Cell IDs y patrones temporales',
        duration: 25000, // 25 segundos  
        icon: <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
    },
    {
        id: 'finalizing',
        title: 'Consolidando Resultados',
        description: 'Organizando coincidencias y calculando niveles de confianza',
        duration: 10000, // 10 segundos
        icon: <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
    }
];

const PremiumProcessingOverlay: React.FC<PremiumProcessingOverlayProps> = ({
    isVisible,
    contextMessage,
    onCancel,
    onTimeout,
    timeoutDuration = 180000 // 3 minutos por defecto
}) => {
    const [currentStageIndex, setCurrentStageIndex] = useState(0);
    const [elapsedTime, setElapsedTime] = useState(0);
    const [progress, setProgress] = useState(0);
    const [isTimeout, setIsTimeout] = useState(false);

    // Reset cuando se muestra el overlay
    useEffect(() => {
        if (isVisible) {
            setCurrentStageIndex(0);
            setElapsedTime(0);
            setProgress(0);
            setIsTimeout(false);
        }
    }, [isVisible]);

    // Timer principal para controlar progreso y timeout
    useEffect(() => {
        if (!isVisible) return;

        const interval = setInterval(() => {
            setElapsedTime(prev => {
                const newTime = prev + 1000;
                
                // Verificar timeout
                if (newTime >= timeoutDuration) {
                    setIsTimeout(true);
                    onTimeout?.();
                    return prev;
                }

                // Calcular progreso basado en etapas
                let accumulatedTime = 0;
                let currentIndex = 0;
                
                for (let i = 0; i < CORRELATION_STAGES.length; i++) {
                    if (newTime >= accumulatedTime + CORRELATION_STAGES[i].duration) {
                        accumulatedTime += CORRELATION_STAGES[i].duration;
                        currentIndex = Math.min(i + 1, CORRELATION_STAGES.length - 1);
                    } else {
                        break;
                    }
                }
                
                setCurrentStageIndex(currentIndex);
                
                // Calcular progreso total (máximo 95% para evitar completar antes de la respuesta real)
                const totalDuration = CORRELATION_STAGES.reduce((sum, stage) => sum + stage.duration, 0);
                const progressPercent = Math.min((newTime / totalDuration) * 95, 95);
                setProgress(progressPercent);
                
                return newTime;
            });
        }, 1000);

        return () => clearInterval(interval);
    }, [isVisible, timeoutDuration, onTimeout]);

    if (!isVisible) return null;

    const currentStage = CORRELATION_STAGES[currentStageIndex];
    const formattedTime = Math.floor(elapsedTime / 1000);

    return (
        <div className="fixed inset-0 z-50 overflow-y-auto animate-fadeIn">
            <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center">
                {/* Backdrop mejorado con blur */}
                <div className="fixed inset-0 processing-overlay-backdrop transition-opacity" />
                
                {/* Modal content con sombras premium */}
                <div className="relative inline-block w-full max-w-2xl p-8 bg-secondary rounded-2xl processing-modal-shadow border border-secondary-light transform transition-all animate-slideIn">
                    {/* Header con contexto */}
                    <div className="text-center mb-8">
                        <div className="flex items-center justify-center mb-4">
                            <div className="relative">
                                {/* Spinner principal con múltiples anillos mejorado */}
                                <div className="w-20 h-20 relative">
                                    <div className="absolute inset-0 rounded-full border-4 border-primary/30 animate-pulse-slow"></div>
                                    <div className="absolute inset-2 rounded-full border-4 border-primary/50 animate-spin border-t-transparent"></div>
                                    <div className="absolute inset-4 rounded-full border-4 border-primary animate-ping opacity-75"></div>
                                    <div className="absolute inset-6 flex items-center justify-center">
                                        <div className="w-8 h-8 text-primary animate-pulse-slow">
                                            {ICONS.correlation}
                                        </div>
                                    </div>
                                    {/* Efecto de brillo giratorio */}
                                    <div className="absolute inset-0 rounded-full bg-gradient-to-r from-transparent via-primary/20 to-transparent animate-rotate-slow"></div>
                                </div>
                            </div>
                        </div>
                        
                        <h2 className="text-2xl font-bold text-light mb-2">
                            {isTimeout ? 'Procesamiento Extendido' : 'Análisis de Correlación en Progreso'}
                        </h2>
                        
                        <p className="text-medium text-sm leading-relaxed max-w-lg mx-auto">
                            {isTimeout ? 'El análisis está tomando más tiempo del esperado. Esto puede ocurrir con conjuntos de datos complejos.' : contextMessage}
                        </p>
                    </div>

                    {!isTimeout ? (
                        <>
                            {/* Barra de progreso premium */}
                            <div className="mb-8">
                                <div className="flex justify-between items-center mb-3">
                                    <span className="text-sm font-medium text-light">Progreso General</span>
                                    <span className="text-sm font-mono text-primary">{progress.toFixed(1)}%</span>
                                </div>
                                <div className="w-full bg-secondary-light rounded-full h-3 relative overflow-hidden">
                                    {/* BORIS: Shimmer effects removed to eliminate screen-wide gradient movement */}
                                    <div 
                                        className="bg-gradient-to-r from-primary to-blue-500 h-3 rounded-full transition-all duration-1000 ease-out relative overflow-hidden animate-progress-glow"
                                        style={{ width: `${progress}%` }}
                                    >
                                        {/* BORIS: Shimmer effect removed - kept pulse effect only */}
                                        <div className="absolute inset-0 bg-gradient-to-r from-primary/50 to-blue-500/50 rounded-full animate-pulse-slow"></div>
                                    </div>
                                </div>
                            </div>

                            {/* Etapa actual */}
                            <div className="bg-secondary-light rounded-xl p-6 mb-6">
                                <div className="flex items-center mb-3">
                                    <div className="w-10 h-10 bg-primary/20 rounded-full flex items-center justify-center mr-4 animate-progress-glow">
                                        <div className="text-primary animate-pulse-slow">
                                            {currentStage.icon}
                                        </div>
                                    </div>
                                    <div className="flex-1">
                                        <h3 className="text-lg font-semibold text-light">{currentStage.title}</h3>
                                        <p className="text-sm text-medium mt-1">{currentStage.description}</p>
                                    </div>
                                </div>
                                
                                {/* Indicador de actividad */}
                                <div className="flex items-center mt-4">
                                    <div className="flex space-x-1">
                                        <div className="w-2 h-2 bg-primary rounded-full animate-bounce-delayed"></div>
                                        <div className="w-2 h-2 bg-primary rounded-full animate-bounce-delayed" style={{ animationDelay: '0.2s' }}></div>
                                        <div className="w-2 h-2 bg-primary rounded-full animate-bounce-delayed" style={{ animationDelay: '0.4s' }}></div>
                                    </div>
                                    <span className="text-xs text-medium ml-3 font-mono">
                                        Tiempo transcurrido: {Math.floor(formattedTime / 60)}m {formattedTime % 60}s
                                    </span>
                                </div>
                            </div>

                            {/* Lista de etapas */}
                            <div className="mb-6">
                                <h4 className="text-sm font-medium text-light mb-3">Etapas del Proceso</h4>
                                <div className="space-y-2">
                                    {CORRELATION_STAGES.map((stage, index) => (
                                        <div 
                                            key={stage.id}
                                            className={`flex items-center p-3 rounded-lg processing-stage-item ${
                                                index < currentStageIndex ? 'bg-green-900/30 border border-green-700/50' :
                                                index === currentStageIndex ? 'bg-primary/20 border border-primary/50 animate-progress-glow' :
                                                'bg-secondary-light/50 border border-secondary-light/50'
                                            }`}
                                        >
                                            <div className={`w-6 h-6 rounded-full flex items-center justify-center mr-3 ${
                                                index < currentStageIndex ? 'bg-green-600' :
                                                index === currentStageIndex ? 'bg-primary animate-pulse' :
                                                'bg-secondary-light'
                                            }`}>
                                                {index < currentStageIndex ? (
                                                    <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                                                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                                    </svg>
                                                ) : (
                                                    <span className={`text-xs font-bold ${
                                                        index === currentStageIndex ? 'text-white' : 'text-medium'
                                                    }`}>
                                                        {index + 1}
                                                    </span>
                                                )}
                                            </div>
                                            <div className="flex-1">
                                                <span className={`text-sm font-medium ${
                                                    index <= currentStageIndex ? 'text-light' : 'text-medium'
                                                }`}>
                                                    {stage.title}
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </>
                    ) : (
                        /* Vista de timeout */
                        <div className="text-center mb-6">
                            <div className="w-16 h-16 mx-auto mb-4 text-yellow-500">
                                {ICONS.exclamationTriangle}
                            </div>
                            <p className="text-medium mb-4">
                                El análisis está tomando más tiempo del esperado. Esto puede deberse a la complejidad de los datos o la carga del sistema.
                            </p>
                            <div className="text-xs text-medium font-mono bg-secondary-light p-2 rounded">
                                Tiempo transcurrido: {Math.floor(formattedTime / 60)}m {formattedTime % 60}s
                            </div>
                        </div>
                    )}

                    {/* Botones de acción */}
                    <div className="flex justify-center space-x-4">
                        {onCancel && (
                            <button
                                onClick={onCancel}
                                className="px-6 py-2 text-sm font-medium text-medium hover:text-light border border-secondary-light hover:border-light rounded-md transition-colors"
                            >
                                {isTimeout ? 'Cancelar' : 'Cancelar Proceso'}
                            </button>
                        )}
                        {isTimeout && (
                            <button
                                className="px-6 py-2 text-sm font-medium text-primary hover:text-primary-hover border border-primary hover:border-primary-hover rounded-md transition-colors"
                            >
                                Continuar Esperando
                            </button>
                        )}
                    </div>

                    {/* Información técnica */}
                    <div className="mt-6 pt-4 border-t border-secondary-light">
                        <p className="text-xs text-medium text-center">
                            Sistema correlacionando registros de telecomunicaciones • KRONOS v1.0
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PremiumProcessingOverlay;