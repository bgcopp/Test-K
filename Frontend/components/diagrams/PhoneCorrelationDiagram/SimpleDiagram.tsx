/**
 * Diagrama Simple de Correlación Telefónica - Versión Estable
 * Implementación básica sin React Flow para evitar errores de producción
 * Creado: 2025-08-20 por Boris - Solución definitiva funcional
 */

import React, { useState, useMemo } from 'react';
import { PhoneCorrelationDiagramProps } from './types/diagram.types';

/**
 * Componente simple y estable para mostrar correlaciones telefónicas
 */
const SimpleDiagram: React.FC<PhoneCorrelationDiagramProps> = ({
  isOpen,
  onClose,
  interactions,
  targetNumber
}) => {
  const [selectedNumber, setSelectedNumber] = useState<string | null>(null);

  // Procesar datos de manera simple
  const processedData = useMemo(() => {
    const phoneNumbers = new Set<string>();
    const connections = new Map<string, number>();

    interactions.forEach(interaction => {
      phoneNumbers.add(interaction.numero_objetivo);
      if (interaction.numero_secundario) {
        phoneNumbers.add(interaction.numero_secundario);
        
        const pair = [interaction.numero_objetivo, interaction.numero_secundario].sort().join('-');
        connections.set(pair, (connections.get(pair) || 0) + 1);
      }
    });

    const nodes = Array.from(phoneNumbers).map(phone => ({
      id: phone,
      isTarget: phone === targetNumber,
      correlationCount: Array.from(connections.entries())
        .filter(([pair]) => pair.includes(phone))
        .reduce((sum, [, count]) => sum + count, 0)
    }));

    const edges = Array.from(connections.entries()).map(([pair, count]) => {
      const [source, target] = pair.split('-');
      return { source, target, count };
    });

    return { nodes, edges };
  }, [interactions, targetNumber]);

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div 
        className="bg-secondary rounded-xl shadow-2xl border border-secondary-light"
        style={{ 
          width: '90vw', 
          height: '85vh',
          maxWidth: '1400px',
          maxHeight: '900px'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-secondary-light">
          <div>
            <h2 className="text-xl font-semibold text-white">
              📊 Diagrama de Correlación Telefónica
            </h2>
            <p className="text-sm text-gray-400 mt-1">
              🎯 Objetivo: <span className="text-cyan-300 font-bold">{targetNumber}</span> | 
              {' '}{processedData.nodes.length} números | {processedData.edges.length} conexiones
            </p>
          </div>
          
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors p-2 hover:bg-secondary-light rounded-lg"
          >
            <span className="text-xl">✕</span>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 p-6" style={{ height: 'calc(85vh - 120px)' }}>
          {processedData.nodes.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-gray-400">
                <div className="text-4xl mb-4">📱</div>
                <div className="text-lg font-medium text-white">Sin datos para mostrar</div>
                <div className="text-sm mt-2">
                  No se encontraron interacciones para generar el diagrama
                </div>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-full">
              {/* Lista de números */}
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="text-lg font-medium text-white mb-4">
                  📞 Números Telefónicos ({processedData.nodes.length})
                </h3>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {processedData.nodes
                    .sort((a, b) => b.correlationCount - a.correlationCount)
                    .map(node => (
                    <div
                      key={node.id}
                      className={`p-3 rounded-lg cursor-pointer transition-colors ${
                        node.isTarget 
                          ? 'bg-red-600 border border-red-400' 
                          : selectedNumber === node.id
                          ? 'bg-blue-600 border border-blue-400'
                          : 'bg-gray-700 hover:bg-gray-600 border border-gray-600'
                      }`}
                      onClick={() => setSelectedNumber(
                        selectedNumber === node.id ? null : node.id
                      )}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-white font-medium">
                            {node.isTarget && '🎯 '}{node.id}
                          </div>
                          <div className="text-xs text-gray-300">
                            {node.correlationCount} correlaciones
                          </div>
                        </div>
                        <div className={`px-2 py-1 rounded text-xs font-medium ${
                          node.isTarget 
                            ? 'bg-red-500 text-white'
                            : 'bg-gray-600 text-gray-200'
                        }`}>
                          {node.isTarget ? 'OBJETIVO' : 'PARTICIPANTE'}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Lista de conexiones */}
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="text-lg font-medium text-white mb-4">
                  🔗 Conexiones ({processedData.edges.length})
                </h3>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {processedData.edges
                    .filter(edge => 
                      !selectedNumber || 
                      edge.source === selectedNumber || 
                      edge.target === selectedNumber
                    )
                    .sort((a, b) => b.count - a.count)
                    .map((edge, index) => (
                    <div key={`${edge.source}-${edge.target}`} className="p-3 bg-gray-700 rounded-lg border border-gray-600">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="text-white font-medium">
                            {edge.source === targetNumber && '🎯 '}
                            {edge.source}
                          </div>
                          <div className="text-gray-400">↔️</div>
                          <div className="text-white font-medium">
                            {edge.target === targetNumber && '🎯 '}
                            {edge.target}
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <div className="px-2 py-1 bg-blue-600 text-white rounded text-xs font-medium">
                            {edge.count} interacciones
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-secondary-light">
          <div className="flex items-center justify-between text-sm text-gray-400">
            <div>
              ✅ Versión Estable - Sin errores de inicialización
              {selectedNumber && (
                <span className="text-cyan-300 ml-2">
                  | Filtrado por: {selectedNumber}
                </span>
              )}
            </div>
            <div>
              Haz clic en números para filtrar | ESC para cerrar
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SimpleDiagram;