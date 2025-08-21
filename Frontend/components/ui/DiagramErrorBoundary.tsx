/**
 * Error Boundary Robusto para Diagrama de Correlación
 * Captura y maneja errores de React Flow con logging detallado
 * Creado: 2025-08-20 por Boris - Solución definitiva errores
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  retryCount: number;
}

class DiagramErrorBoundary extends Component<Props, State> {
  private maxRetries = 3;

  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Actualizar el estado para mostrar la UI de error
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Logging detallado del error
    console.error('🚨 DiagramErrorBoundary - Error capturado:', {
      error: {
        name: error.name,
        message: error.message,
        stack: error.stack
      },
      errorInfo: {
        componentStack: errorInfo.componentStack
      },
      timestamp: new Date().toISOString(),
      retryCount: this.state.retryCount
    });

    // Actualizar estado con información del error
    this.setState({
      error,
      errorInfo,
      hasError: true
    });

    // Llamar callback opcional
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Reportar a servicio de logging si está disponible
    if (window.eel && window.eel.log_frontend_error) {
      try {
        window.eel.log_frontend_error({
          error: error.message,
          stack: error.stack,
          component: 'DiagramErrorBoundary',
          timestamp: new Date().toISOString()
        });
      } catch (eelError) {
        console.warn('No se pudo reportar error al backend:', eelError);
      }
    }
  }

  handleRetry = () => {
    if (this.state.retryCount < this.maxRetries) {
      console.log(`🔄 Reintentando carga del diagrama (${this.state.retryCount + 1}/${this.maxRetries})`);
      
      this.setState(prevState => ({
        hasError: false,
        error: null,
        errorInfo: null,
        retryCount: prevState.retryCount + 1
      }));
    }
  };

  handleReset = () => {
    console.log('🔄 Reiniciando error boundary completamente');
    
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0
    });
  };

  render() {
    if (this.state.hasError && this.state.error) {
      const canRetry = this.state.retryCount < this.maxRetries;
      const isReactFlowError = this.state.error.message?.includes('Cannot access') || 
                               this.state.error.message?.includes('before initialization') ||
                               this.state.error.name === 'ReferenceError';

      return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-red-900/90 border border-red-600 rounded-xl p-6 max-w-2xl mx-auto">
            <div className="flex items-center mb-4">
              <div className="text-red-400 text-2xl mr-3">🚨</div>
              <h2 className="text-xl font-semibold text-white">
                Error en Diagrama de Correlación
              </h2>
            </div>

            <div className="bg-red-800/50 rounded-lg p-4 mb-4">
              <div className="text-red-200 text-sm mb-2">
                <strong>Error:</strong> {this.state.error.message}
              </div>
              <div className="text-red-300 text-xs">
                <strong>Tipo:</strong> {this.state.error.name}
              </div>
              {isReactFlowError && (
                <div className="text-yellow-200 text-xs mt-2">
                  <strong>Diagnóstico:</strong> Error de inicialización de React Flow
                </div>
              )}
            </div>

            <div className="text-gray-300 text-sm mb-4">
              <strong>Información técnica:</strong>
              <div className="bg-gray-800 rounded p-2 mt-2 text-xs font-mono">
                Intentos: {this.state.retryCount}/{this.maxRetries}<br/>
                Timestamp: {new Date().toLocaleString()}<br/>
                Componente: DiagramErrorBoundary
              </div>
            </div>

            <div className="flex space-x-3">
              {canRetry && (
                <button
                  onClick={this.handleRetry}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
                >
                  🔄 Reintentar ({this.maxRetries - this.state.retryCount} intentos restantes)
                </button>
              )}
              
              <button
                onClick={this.handleReset}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg text-sm font-medium transition-colors"
              >
                🔧 Reiniciar Completo
              </button>

              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors"
              >
                ↻ Recargar Aplicación
              </button>
            </div>

            <div className="mt-4 text-xs text-gray-400">
              💡 Si el problema persiste, reporta este error al equipo de desarrollo con la información técnica mostrada arriba.
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default DiagramErrorBoundary;