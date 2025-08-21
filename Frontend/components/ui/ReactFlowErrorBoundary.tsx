/**
 * Error Boundary específico para React Flow - Diagrama de Correlación
 * Captura errores como "Cannot access 'V' before initialization" y proporciona fallback
 * Creado: 2025-08-20 por Boris - Debug error misterioso React Flow
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  targetNumber?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  retryCount: number;
}

class ReactFlowErrorBoundary extends Component<Props, State> {
  private maxRetries = 2;

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
    // Actualiza el state para mostrar la UI de error
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log del error para análisis
    console.error('🚨 ReactFlowErrorBoundary capturó un error:', {
      error: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      targetNumber: this.props.targetNumber,
      timestamp: new Date().toISOString(),
      retryCount: this.state.retryCount
    });

    // Verificar si es el error específico de inicialización
    const isInitializationError = error.message.includes('before initialization') ||
                                 error.message.includes('Cannot access') ||
                                 error.message.includes("Cannot read properties of undefined");

    if (isInitializationError) {
      console.error('🎯 Error de inicialización detectado en React Flow:', {
        message: error.message,
        possibleCause: 'Variable hoisting o bundling issue',
        suggestion: 'Verificar orden de imports y declaraciones'
      });
    }

    this.setState({
      error,
      errorInfo,
      hasError: true
    });
  }

  handleRetry = () => {
    if (this.state.retryCount < this.maxRetries) {
      console.log(`🔄 Reintentando render React Flow (intento ${this.state.retryCount + 1}/${this.maxRetries})`);
      
      this.setState(prevState => ({
        hasError: false,
        error: null,
        errorInfo: null,
        retryCount: prevState.retryCount + 1
      }));
    }
  };

  render() {
    if (this.state.hasError && this.state.error) {
      const isInitializationError = this.state.error.message.includes('before initialization') ||
                                   this.state.error.message.includes('Cannot access');

      return (
        <div className="w-full h-full flex items-center justify-center bg-gray-900 rounded-lg border border-red-500">
          <div className="text-center p-8 max-w-md">
            <div className="text-6xl mb-4">⚠️</div>
            
            <h3 className="text-xl font-bold text-white mb-4">
              Error en Diagrama de Correlación
            </h3>
            
            <div className="text-sm text-gray-300 mb-4">
              <div className="bg-red-900/30 rounded-lg p-4 mb-4">
                <div className="font-mono text-xs text-red-300 break-words">
                  {this.state.error.message}
                </div>
              </div>
              
              {isInitializationError && (
                <div className="bg-yellow-900/30 rounded-lg p-3 mb-4">
                  <div className="text-yellow-300 text-xs">
                    <strong>🎯 Error de Inicialización Detectado</strong><br/>
                    Posible problema de bundling o timing en React Flow
                  </div>
                </div>
              )}
              
              <div className="text-gray-400 text-xs">
                Objetivo: <span className="text-cyan-300 font-mono">{this.props.targetNumber || 'N/A'}</span><br/>
                Intentos: {this.state.retryCount}/{this.maxRetries}
              </div>
            </div>

            <div className="space-y-3">
              {this.state.retryCount < this.maxRetries && (
                <button
                  onClick={this.handleRetry}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                >
                  🔄 Reintentar
                </button>
              )}
              
              <div className="text-xs text-gray-500">
                El error ha sido registrado para análisis técnico
              </div>
            </div>

            {/* Debug Info (solo en desarrollo) */}
            {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
              <details className="mt-6 text-left">
                <summary className="cursor-pointer text-xs text-gray-400 hover:text-white">
                  🔧 Información de Debug
                </summary>
                <div className="mt-2 p-3 bg-gray-800 rounded text-xs font-mono text-gray-300 overflow-auto max-h-40">
                  <div className="mb-2">
                    <strong>Stack Trace:</strong>
                    <pre className="text-red-400 whitespace-pre-wrap text-xs mt-1">
                      {this.state.error.stack}
                    </pre>
                  </div>
                  <div>
                    <strong>Component Stack:</strong>
                    <pre className="text-yellow-400 whitespace-pre-wrap text-xs mt-1">
                      {this.state.errorInfo.componentStack}
                    </pre>
                  </div>
                </div>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ReactFlowErrorBoundary;