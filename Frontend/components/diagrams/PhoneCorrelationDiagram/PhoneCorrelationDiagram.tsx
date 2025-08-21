/**
 * Componente Principal del Diagrama de Correlación Telefónica con React Flow
 * Versión estable con todas las mejoras UX implementadas
 * Reconstruido: 2025-08-20 por Boris - Basado en especificaciones exitosas
 */

import React, { useState, useCallback, useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Panel,
  Node,
  Edge,
  ConnectionMode
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { PhoneCorrelationDiagramProps } from './types/diagram.types';
import { useReactFlowAdapter } from './hooks/useReactFlowAdapter';

// Configuración visual KRONOS optimizada
const FLOW_CONFIG = {
  defaultViewport: { x: 0, y: 0, zoom: 0.8 },
  minZoom: 0.3,
  maxZoom: 2,
  attributionPosition: 'bottom-left' as const,
  connectionMode: ConnectionMode.Loose,
  fitViewOptions: {
    padding: 0.2,
    includeHiddenNodes: false,
    minZoom: 0.5,
    maxZoom: 1.5
  }
};

/**
 * Componente principal React Flow con mejoras UX implementadas
 */
const PhoneCorrelationDiagram: React.FC<PhoneCorrelationDiagramProps> = ({
  isOpen,
  onClose,
  interactions,
  targetNumber
}) => {
  // Estados para filtros y configuración
  const [filters, setFilters] = useState({
    minCorrelation: 0,
    showIsolatedNodes: true,
    labelStrategy: 'smart' as 'always' | 'smart' | 'minimal' | 'off'
  });

  const [selectedStrategy, setSelectedStrategy] = useState<'always' | 'smart' | 'minimal' | 'off'>('smart');

  // Hook para adaptar datos a React Flow
  const { nodes, edges, nodeTypes, edgeTypes } = useReactFlowAdapter({
    interactions,
    targetNumber,
    filters: { ...filters, labelStrategy: selectedStrategy }
  });

  // Estados de React Flow
  const [flowNodes, setNodes, onNodesChange] = useNodesState(nodes);
  const [flowEdges, setEdges, onEdgesChange] = useEdgesState(edges);

  // Actualizar nodos y edges cuando cambian los datos
  React.useEffect(() => {
    setNodes(nodes);
    setEdges(edges);
  }, [nodes, edges, setNodes, setEdges]);

  // Funciones de control
  const handleFilterChange = useCallback((newFilters: typeof filters) => {
    setFilters(newFilters);
  }, []);

  const handleStrategyChange = useCallback((strategy: typeof selectedStrategy) => {
    setSelectedStrategy(strategy);
  }, []);

  // Información del diagrama
  const diagramInfo = useMemo(() => ({
    totalNodes: flowNodes.length,
    totalEdges: flowEdges.length,
    targetExists: flowNodes.some(node => node.data?.isTarget),
    targetNode: flowNodes.find(node => node.data?.isTarget)
  }), [flowNodes, flowEdges]);

  // No renderizar si el modal no está abierto
  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div 
        className="bg-secondary rounded-xl shadow-2xl border border-secondary-light"
        style={{ 
          width: '95vw', 
          height: '90vh',
          maxWidth: '1600px',
          maxHeight: '1000px'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header del Modal */}
        <div className="flex items-center justify-between p-4 border-b border-secondary-light">
          <div>
            <h2 className="text-xl font-semibold text-white">
              📊 Diagrama de Correlación Telefónica
            </h2>
            <p className="text-sm text-gray-400 mt-1">
              🎯 Objetivo: <span className="text-cyan-300 font-bold">{targetNumber}</span> | 
              {' '}{diagramInfo.totalNodes} nodos | {diagramInfo.totalEdges} conexiones
            </p>
          </div>
          
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors p-2 hover:bg-secondary-light rounded-lg"
            title="Cerrar diagrama (ESC)"
          >
            <span className="text-xl">✕</span>
          </button>
        </div>

        {/* Container del React Flow */}
        <div className="relative" style={{ height: 'calc(90vh - 120px)' }}>
          {diagramInfo.totalNodes === 0 ? (
            // Estado sin datos
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center text-gray-400">
                <div className="text-4xl mb-4">📱</div>
                <div className="text-lg font-medium text-white">Sin datos para mostrar</div>
                <div className="text-sm mt-2">
                  No se encontraron interacciones para generar el diagrama
                </div>
              </div>
            </div>
          ) : (
            <ReactFlow
              nodes={flowNodes}
              edges={flowEdges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              nodeTypes={nodeTypes}
              edgeTypes={edgeTypes}
              defaultViewport={FLOW_CONFIG.defaultViewport}
              minZoom={FLOW_CONFIG.minZoom}
              maxZoom={FLOW_CONFIG.maxZoom}
              connectionMode={FLOW_CONFIG.connectionMode}
              fitView
              fitViewOptions={FLOW_CONFIG.fitViewOptions}
              proOptions={{ hideAttribution: true }}
            >
              {/* Fondo con patrón */}
              <Background 
                variant="dots" 
                gap={20} 
                size={1} 
                color="#374151"
              />

              {/* Controles de navegación - Estilo KRONOS */}
              <Controls 
                className="react-flow-controls-dark"
                style={{
                  background: '#1f2937',
                  border: '1px solid #4b5563',
                  borderRadius: '8px',
                  padding: '4px'
                }}
              />

              {/* Mini mapa */}
              <MiniMap
                style={{
                  background: '#1f2937',
                  border: '1px solid #4b5563'
                }}
                nodeColor={(node) => node.data?.color || '#6b7280'}
                nodeStrokeWidth={3}
                zoomable
                pannable
              />

              {/* Panel de filtros */}
              <Panel position="top-left" className="bg-gray-800 p-3 rounded-lg border border-gray-600">
                <div className="text-white text-sm font-medium mb-2">🎛️ Filtros</div>
                
                {/* Correlación mínima */}
                <div className="mb-3">
                  <label className="text-xs text-gray-300 block mb-1">
                    Correlación mínima: {filters.minCorrelation}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="10"
                    value={filters.minCorrelation}
                    onChange={(e) => handleFilterChange({
                      ...filters,
                      minCorrelation: parseInt(e.target.value)
                    })}
                    className="w-full"
                  />
                </div>

                {/* Estrategia de etiquetas */}
                <div className="mb-3">
                  <label className="text-xs text-gray-300 block mb-1">
                    Etiquetas de celda
                  </label>
                  <select
                    value={selectedStrategy}
                    onChange={(e) => handleStrategyChange(e.target.value as typeof selectedStrategy)}
                    className="w-full text-xs bg-gray-700 text-white rounded px-2 py-1"
                  >
                    <option value="always">Siempre visible</option>
                    <option value="smart">Inteligente (recomendado)</option>
                    <option value="minimal">Mínimo</option>
                    <option value="off">Ocultar todas</option>
                  </select>
                </div>

                {/* Nodos aislados */}
                <div>
                  <label className="flex items-center text-xs text-gray-300">
                    <input
                      type="checkbox"
                      checked={filters.showIsolatedNodes}
                      onChange={(e) => handleFilterChange({
                        ...filters,
                        showIsolatedNodes: e.target.checked
                      })}
                      className="mr-2"
                    />
                    Mostrar nodos aislados
                  </label>
                </div>
              </Panel>

              {/* Panel de información */}
              <Panel position="top-right" className="bg-gray-800 p-3 rounded-lg border border-gray-600">
                <div className="text-white text-sm font-medium mb-2">📊 Información</div>
                <div className="text-xs text-gray-300 space-y-1">
                  <div>Nodos: {diagramInfo.totalNodes}</div>
                  <div>Conexiones: {diagramInfo.totalEdges}</div>
                  <div className="mt-2 pt-2 border-t border-gray-600">
                    <div className="flex items-center space-x-2 mb-1">
                      <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                      <span>Objetivo</span>
                    </div>
                    <div className="flex items-center space-x-2 mb-1">
                      <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                      <span>Entrante</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                      <span>Saliente</span>
                    </div>
                  </div>
                </div>
              </Panel>
            </ReactFlow>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-secondary-light">
          <div className="flex items-center justify-between text-sm text-gray-400">
            <div>
              🎯 React Flow v12 - Estrategia: {selectedStrategy}
            </div>
            <div>
              Arrastra nodos • Zoom • ESC para cerrar
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PhoneCorrelationDiagram;