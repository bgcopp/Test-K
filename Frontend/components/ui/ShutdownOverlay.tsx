import React from 'react';

interface ShutdownOverlayProps {
  isVisible: boolean;
  message?: string;
  progress?: number;
}

/**
 * Componente overlay que muestra el estado de shutdown de la aplicación
 * 
 * Proporciona retroalimentación visual al usuario durante el proceso de cierre,
 * evitando confusión sobre si la aplicación está funcionando correctamente.
 */
export const ShutdownOverlay: React.FC<ShutdownOverlayProps> = ({
  isVisible,
  message = "Cerrando KRONOS...",
  progress
}) => {
  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-dark bg-opacity-95 z-50 flex items-center justify-center">
      <div className="bg-secondary-light border border-medium rounded-lg p-8 max-w-md mx-4 text-center">
        {/* Icono de cierre */}
        <div className="flex justify-center mb-6">
          <div className="relative">
            <div className="w-16 h-16 border-4 border-medium border-t-primary rounded-full animate-spin"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <svg 
                className="w-6 h-6 text-primary" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" 
                />
              </svg>
            </div>
          </div>
        </div>

        {/* Mensaje principal */}
        <h2 className="text-xl font-semibold text-light mb-4">
          {message}
        </h2>

        {/* Barra de progreso si se proporciona */}
        {typeof progress === 'number' && (
          <div className="w-full bg-secondary-light rounded-full h-2 mb-4">
            <div 
              className="bg-primary h-2 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
            />
          </div>
        )}

        {/* Mensaje explicativo */}
        <p className="text-medium text-sm">
          Guardando cambios y cerrando conexiones...
          <br />
          Por favor, no cierre la ventana manualmente.
        </p>
      </div>
    </div>
  );
};

interface ConnectionStatusIndicatorProps {
  isConnected: boolean;
  isShuttingDown: boolean;
  className?: string;
}

/**
 * Indicador discreto del estado de conexión en la UI
 */
export const ConnectionStatusIndicator: React.FC<ConnectionStatusIndicatorProps> = ({
  isConnected,
  isShuttingDown,
  className = ""
}) => {
  const getStatusInfo = () => {
    if (isShuttingDown) {
      return {
        color: 'bg-yellow-500',
        text: 'Cerrando...',
        icon: (
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
          </svg>
        )
      };
    } else if (isConnected) {
      return {
        color: 'bg-green-500',
        text: 'Conectado',
        icon: (
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        )
      };
    } else {
      return {
        color: 'bg-red-500',
        text: 'Desconectado',
        icon: (
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        )
      };
    }
  };

  const status = getStatusInfo();

  return (
    <div className={`flex items-center gap-2 text-xs ${className}`}>
      <div className={`w-2 h-2 rounded-full ${status.color} ${isShuttingDown ? 'animate-pulse' : ''}`} />
      <div className="flex items-center gap-1 text-medium">
        {status.icon}
        <span>{status.text}</span>
      </div>
    </div>
  );
};

interface ShutdownProgressProps {
  stages: Array<{
    name: string;
    completed: boolean;
    inProgress: boolean;
    error?: boolean;
  }>;
  className?: string;
}

/**
 * Componente que muestra el progreso detallado del shutdown
 */
export const ShutdownProgress: React.FC<ShutdownProgressProps> = ({ 
  stages,
  className = ""
}) => {
  return (
    <div className={`space-y-2 ${className}`}>
      {stages.map((stage, index) => (
        <div key={index} className="flex items-center gap-3">
          {/* Indicador de estado */}
          <div className="flex-shrink-0">
            {stage.error ? (
              <div className="w-4 h-4 bg-red-500 rounded-full flex items-center justify-center">
                <svg className="w-2 h-2 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </div>
            ) : stage.completed ? (
              <div className="w-4 h-4 bg-green-500 rounded-full flex items-center justify-center">
                <svg className="w-2 h-2 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              </div>
            ) : stage.inProgress ? (
              <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            ) : (
              <div className="w-4 h-4 border-2 border-medium rounded-full" />
            )}
          </div>

          {/* Nombre de la etapa */}
          <span className={`text-sm ${
            stage.error ? 'text-red-400' : 
            stage.completed ? 'text-green-400' : 
            stage.inProgress ? 'text-primary' : 
            'text-medium'
          }`}>
            {stage.name}
          </span>
        </div>
      ))}
    </div>
  );
};