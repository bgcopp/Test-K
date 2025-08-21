/**
 * Wrapper Lazy para React Flow - Solución para error "Cannot access 'V' before initialization"
 * 
 * PROBLEMA RESUELTO:
 * - Error 'V' antes de inicialización en React Flow
 * - Fragmentación de imports causando problemas de bundling
 * - Timing de inicialización de componentes
 * 
 * SOLUCIÓN:
 * - Carga lazy de React Flow completo
 * - Centralización de todos los imports de React Flow
 * - Manejo de estado de carga con fallback
 * 
 * Creado: 2025-08-20 por Boris - Debug error React Flow
 */

import React, { Suspense, lazy, useState, useEffect } from 'react';
import { PhoneCorrelationDiagramProps } from './types/diagram.types';

// Importación lazy del componente React Flow completo
const LazyPhoneCorrelationDiagram = lazy(() => 
  import('./PhoneCorrelationDiagram').then(module => ({
    default: module.default
  }))
);

/**
 * Componente de carga para mostrar mientras se inicializa React Flow
 */
const ReactFlowLoadingFallback: React.FC = () => (
  <div className="flex items-center justify-center h-full bg-gray-900 text-white">
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
      <p className="text-sm text-gray-300">Inicializando diagrama de correlación...</p>
      <p className="text-xs text-gray-500 mt-1">Cargando React Flow Engine</p>
    </div>
  </div>
);

/**
 * Componente de error específico para problemas de React Flow
 */
const ReactFlowErrorFallback: React.FC<{ error: Error; onRetry: () => void }> = ({ 
  error, 
  onRetry 
}) => (
  <div className="flex items-center justify-center h-full bg-gray-900 text-white p-6">
    <div className="text-center max-w-md">
      <div className="mb-4">
        <svg className="w-16 h-16 text-red-500 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 15.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
      </div>
      <h3 className="text-lg font-semibold text-red-400 mb-2">
        Error de Inicialización de React Flow
      </h3>
      <p className="text-sm text-gray-300 mb-4">
        {error.message === "Cannot access 'V' before initialization" 
          ? "Error de inicialización de React Flow detectado. Reintentando carga..."
          : `Error: ${error.message}`}
      </p>
      <div className="space-y-2">
        <button
          onClick={onRetry}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm font-medium"
        >
          Reintentar Carga
        </button>
        <p className="text-xs text-gray-500">
          Debug: Problema de bundling/inicialización React Flow
        </p>
      </div>
    </div>
  </div>
);

/**
 * Wrapper principal que maneja la carga lazy y errores de React Flow
 */
const LazyReactFlowWrapper: React.FC<PhoneCorrelationDiagramProps> = (props) => {
  const [retryKey, setRetryKey] = useState(0);
  const [hasError, setHasError] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // Reset del estado de error cuando cambian las props
  useEffect(() => {
    setHasError(false);
    setError(null);
  }, [props.isOpen]);

  const handleRetry = () => {
    setRetryKey(prev => prev + 1);
    setHasError(false);
    setError(null);
  };

  const handleError = (err: Error) => {
    console.error('LazyReactFlowWrapper Error:', err);
    setError(err);
    setHasError(true);
  };

  if (hasError && error) {
    return <ReactFlowErrorFallback error={error} onRetry={handleRetry} />;
  }

  return (
    <React.StrictMode>
      <Suspense fallback={<ReactFlowLoadingFallback />}>
        <ErrorBoundary onError={handleError}>
          <LazyPhoneCorrelationDiagram 
            key={retryKey} 
            {...props} 
          />
        </ErrorBoundary>
      </Suspense>
    </React.StrictMode>
  );
};

/**
 * Error Boundary interno para capturar errores de React Flow
 */
class ErrorBoundary extends React.Component<
  { children: React.ReactNode; onError: (error: Error) => void },
  { hasError: boolean }
> {
  constructor(props: { children: React.ReactNode; onError: (error: Error) => void }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(_: Error) {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ReactFlow Error Boundary Caught:', error, errorInfo);
    this.props.onError(error);
  }

  render() {
    if (this.state.hasError) {
      return null; // El manejo del error se hace en el componente padre
    }

    return this.props.children;
  }
}

export default LazyReactFlowWrapper;