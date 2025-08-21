/**
 * PhoneCorrelationViewer - Modal principal para visualizar diagrama de correlación telefónica
 * Especificaciones confirmadas por Boris:
 * - Modal separado 90% x 85% con overlay
 * - Integración React Flow con 4 modos de visualización
 * - Header con título y selector de modos
 * - Panel lateral con controles avanzados
 * - Sistema de tooltips para nodos y edges
 * - Funcionalidad de export completa
 * 
 * Creado: 2025-08-21 por Claude bajo supervisión de Boris
 */

import React, { useState, useCallback, useEffect, useMemo } from 'react';
import {
  ReactFlow,
  Background,
  useNodesState,
  useEdgesState,
  ReactFlowProvider,
  Node,
  Edge,
  useReactFlow,
  Panel
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

// Static import de html-to-image para resolver error de inicialización
import { toPng, toSvg } from 'html-to-image';

// Importar hooks y componentes existentes
import { useReactFlowAdapter } from '../diagrams/PhoneCorrelationDiagram/hooks/useReactFlowAdapter';
import { UnifiedInteraction } from '../diagrams/PhoneCorrelationDiagram/types/diagram.types';

// Importar componentes de UI
import CorrelationControls from './CorrelationControls';

// Types para las interacciones (reutilizando de TableCorrelationModal)
interface CallInteraction {
  originador: string;
  receptor: string;
  fecha_hora: string;
  duracion: number;
  operador: string;
  celda_origen: string;
  celda_destino: string;
  latitud_origen?: number;
  longitud_origen?: number;
  latitud_destino?: number;
  longitud_destino?: number;
  punto_hunter_origen?: string;
  lat_hunter_origen?: number;
  lon_hunter_origen?: number;
  punto_hunter_destino?: string;
  lat_hunter_destino?: number;
  lon_hunter_destino?: number;
  punto_hunter?: string;
  lat_hunter?: number;
  lon_hunter?: number;
  hunter_source?: string;
  precision_ubicacion?: string;
}

interface PhoneCorrelationViewerProps {
  isOpen: boolean;
  onClose: () => void;
  interactions: CallInteraction[];
  targetNumber: string;
}

// Tipos de modo de visualización
type VisualizationMode = 'radial_central' | 'circular_avatares' | 'flujo_lineal' | 'hibrido_inteligente';

// Configuración de modos
const VISUALIZATION_MODES = {
  radial_central: {
    id: 'radial_central',
    name: 'Radial Central',
    description: 'Objetivo en el centro, conexiones radiales',
    icon: '🎯'
  },
  circular_avatares: {
    id: 'circular_avatares',
    name: 'Circular Avatares',
    description: 'Disposición circular con avatares grandes',
    icon: '👥'
  },
  flujo_lineal: {
    id: 'flujo_lineal',
    name: 'Flujo Lineal',
    description: 'Vista cronológica de izquierda a derecha',
    icon: '➡️'
  },
  hibrido_inteligente: {
    id: 'hibrido_inteligente',
    name: 'Híbrido Inteligente',
    description: 'Detecta automáticamente el mejor layout',
    icon: '🧠'
  }
} as const;

/**
 * Adaptador para convertir CallInteraction[] a UnifiedInteraction[]
 * Compatible con el sistema existente de useDataTransformer
 */
const adaptCallInteractionsToUnified = (
  interactions: CallInteraction[], 
  targetNumber: string
): UnifiedInteraction[] => {
  return interactions.map(interaction => ({
    // Campos comunes para ambos tipos
    numero_objetivo: interaction.originador,
    numero_secundario: interaction.receptor,
    fecha_hora: interaction.fecha_hora,
    duracion_segundos: interaction.duracion,
    operador: interaction.operador,
    celda_inicio: interaction.celda_origen,
    celda_final: interaction.celda_destino,
    
    // Campo HUNTER unificado del backend
    punto_hunter: interaction.punto_hunter,
    lat_hunter: interaction.lat_hunter,
    lon_hunter: interaction.lon_hunter,
    
    // Campos específicos para datos móviles (vacíos para llamadas)
    trafico_total_bytes: undefined,
    tipo_conexion: undefined,
    
    // Tipo de interacción
    tipo_interaccion: 'llamada' as const,
    
    // Campos direccionales del backend
    hunter_source: interaction.hunter_source,
    precision_ubicacion: interaction.precision_ubicacion
  }));
};

/**
 * Componente interno del diagrama que usa ReactFlow
 */
const PhoneCorrelationDiagramContent: React.FC<PhoneCorrelationViewerProps> = ({
  isOpen,
  onClose,
  interactions,
  targetNumber
}) => {
  // Estados principales
  const [currentMode, setCurrentMode] = useState<VisualizationMode>('radial_central');
  const [filters, setFilters] = useState({
    minCorrelation: 0,
    showIsolatedNodes: true,
    showCellIds: true,
    labelStrategy: 'smart' as 'always' | 'smart' | 'minimal' | 'off'
  });


  // Adaptar CallInteraction[] a UnifiedInteraction[]
  const unifiedInteractions = useMemo(() => 
    adaptCallInteractionsToUnified(interactions, targetNumber), 
    [interactions, targetNumber]
  );

  // Hook para adaptar datos a React Flow
  const { nodes, edges, nodeTypes, edgeTypes } = useReactFlowAdapter({
    interactions: unifiedInteractions,
    targetNumber,
    filters
  });



  // Estados de React Flow
  const [flowNodes, setNodes, onNodesChange] = useNodesState(nodes);
  const [flowEdges, setEdges, onEdgesChange] = useEdgesState(edges);
  
  // Hook de React Flow para controles
  const { fitView, getZoom, setViewport, getViewport, toObject, getNode, getEdge } = useReactFlow();
  
  // Estados para tooltips
  const [nodeTooltip, setNodeTooltip] = useState<{
    node: any;
    position: { x: number; y: number };
  } | null>(null);
  
  const [edgeTooltip, setEdgeTooltip] = useState<{
    edge: any;
    interactions: CallInteraction[];
    position: { x: number; y: number };
  } | null>(null);

  // Actualizar nodos y edges cuando cambian
  useEffect(() => {
    setNodes(nodes);
    setEdges(edges);
  }, [nodes, edges, setNodes, setEdges]);

  // Aplicar layout según el modo seleccionado
  useEffect(() => {
    if (flowNodes.length === 0) return;

    const applyLayout = () => {
      let layoutNodes = [...flowNodes];

      switch (currentMode) {
        case 'radial_central':
          // Aplicar layout radial con objetivo en el centro
          layoutNodes = layoutNodes.map(node => {
            if (node.data.isTarget) {
              return { ...node, position: { x: 400, y: 300 } };
            }
            
            const index = flowNodes.findIndex(n => n.id === node.id);
            const angle = (index * 2 * Math.PI) / (flowNodes.length - 1);
            const radius = 200;
            
            return {
              ...node,
              position: {
                x: 400 + Math.cos(angle) * radius,
                y: 300 + Math.sin(angle) * radius
              }
            };
          });
          break;

        case 'circular_avatares':
          // Layout circular con todos los nodos distribuidos uniformemente
          layoutNodes = layoutNodes.map((node, index) => {
            const angle = (index * 2 * Math.PI) / flowNodes.length;
            const radius = 250;
            
            return {
              ...node,
              position: {
                x: 400 + Math.cos(angle) * radius,
                y: 300 + Math.sin(angle) * radius
              }
            };
          });
          break;

        case 'flujo_lineal':
          // Layout lineal horizontal
          layoutNodes = layoutNodes.map((node, index) => {
            return {
              ...node,
              position: {
                x: 100 + index * 150,
                y: 300 + (Math.random() - 0.5) * 100
              }
            };
          });
          break;

        case 'hibrido_inteligente':
          // Detectar automáticamente basado en número de nodos
          if (flowNodes.length <= 5) {
            // Pocos nodos: usar circular
            layoutNodes = layoutNodes.map((node, index) => {
              const angle = (index * 2 * Math.PI) / flowNodes.length;
              const radius = 200;
              
              return {
                ...node,
                position: {
                  x: 400 + Math.cos(angle) * radius,
                  y: 300 + Math.sin(angle) * radius
                }
              };
            });
          } else {
            // Muchos nodos: usar radial con objetivo central
            layoutNodes = layoutNodes.map(node => {
              if (node.data.isTarget) {
                return { ...node, position: { x: 400, y: 300 } };
              }
              
              const index = flowNodes.findIndex(n => n.id === node.id);
              const angle = (index * 2 * Math.PI) / (flowNodes.length - 1);
              const radius = 250;
              
              return {
                ...node,
                position: {
                  x: 400 + Math.cos(angle) * radius,
                  y: 300 + Math.sin(angle) * radius
                }
              };
            });
          }
          break;

      }

      setNodes(layoutNodes);
      
      // Fit view después de aplicar layout
      setTimeout(() => {
        fitView({ padding: 0.2, duration: 500 });
      }, 100);
    };

    applyLayout();
  }, [currentMode, setNodes, fitView, flowNodes.length]);

  // Handlers
  const handleModeChange = useCallback((mode: VisualizationMode) => {
    setCurrentMode(mode);
  }, []);

  const handleFilterChange = useCallback((newFilters: typeof filters) => {
    setFilters(newFilters);
  }, []);


  const handleZoomIn = useCallback(() => {
    const currentZoom = getZoom();
    setViewport({ x: 0, y: 0, zoom: Math.min(currentZoom * 1.2, 2) }, { duration: 300 });
  }, [getZoom, setViewport]);

  const handleZoomOut = useCallback(() => {
    const currentZoom = getZoom();
    setViewport({ x: 0, y: 0, zoom: Math.max(currentZoom * 0.8, 0.3) }, { duration: 300 });
  }, [getZoom, setViewport]);

  const handleZoomReset = useCallback(() => {
    setViewport({ x: 0, y: 0, zoom: 1 }, { duration: 500 });
  }, [setViewport]);

  const handleFitToScreen = useCallback(() => {
    fitView({ padding: 0.2, duration: 500 });
  }, [fitView]);

  // Event handlers para tooltips
  const handleNodeClick = useCallback((event: React.MouseEvent, node: any) => {
    const rect = (event.target as HTMLElement).getBoundingClientRect();
    setNodeTooltip({
      node,
      position: { x: rect.left + rect.width / 2, y: rect.top - 10 }
    });
    setEdgeTooltip(null); // Cerrar tooltip de edge
  }, []);

  const handleEdgeClick = useCallback((event: React.MouseEvent, edge: any) => {
    // Encontrar interacciones relacionadas con este edge
    const edgeInteractions = interactions.filter(interaction => {
      const sourceNode = edge.source;
      const targetNode = edge.target;
      return (
        (interaction.originador === sourceNode && interaction.receptor === targetNode) ||
        (interaction.originador === targetNode && interaction.receptor === sourceNode)
      );
    });

    const rect = (event.target as HTMLElement).getBoundingClientRect();
    setEdgeTooltip({
      edge,
      interactions: edgeInteractions,
      position: { x: rect.left + rect.width / 2, y: rect.top - 10 }
    });
    setNodeTooltip(null); // Cerrar tooltip de nodo
  }, [interactions]);

  const handlePaneClick = useCallback(() => {
    // Cerrar todos los tooltips al hacer click en el área vacía
    setNodeTooltip(null);
    setEdgeTooltip(null);
  }, []);

  // Export functionality
  const handleExportPNG = useCallback(async () => {
    try {
      console.log('🖼️ Iniciando exportación PNG...');
      
      const viewport = getViewport();
      const reactFlowElement = document.querySelector('.react-flow') as HTMLElement;
      if (!reactFlowElement) {
        throw new Error('No se encontró el elemento React Flow');
      }

      const dataUrl = await toPng(reactFlowElement, {
        backgroundColor: '#0f172a',
        width: reactFlowElement.offsetWidth,
        height: reactFlowElement.offsetHeight,
        style: {
          width: reactFlowElement.offsetWidth + 'px',
          height: reactFlowElement.offsetHeight + 'px',
        }
      });

      // Crear link de descarga
      const link = document.createElement('a');
      link.download = `diagrama_correlacion_${targetNumber}_${new Date().toISOString().split('T')[0]}.png`;
      link.href = dataUrl;
      link.click();

      console.log('✅ Exportación PNG completada');
    } catch (error) {
      console.error('❌ Error al exportar PNG:', error);
      alert('Error al exportar como PNG. Intente nuevamente.');
    }
  }, [getViewport, targetNumber]);

  const handleExportSVG = useCallback(async () => {
    try {
      console.log('📄 Iniciando exportación SVG...');
      
      // Buscar el elemento del React Flow
      const reactFlowElement = document.querySelector('.react-flow') as HTMLElement;
      if (!reactFlowElement) {
        throw new Error('No se encontró el elemento React Flow');
      }

      // Generar SVG
      const dataUrl = await toSvg(reactFlowElement, {
        backgroundColor: '#0f172a',
        width: reactFlowElement.offsetWidth,
        height: reactFlowElement.offsetHeight,
      });

      // Crear link de descarga
      const link = document.createElement('a');
      link.download = `diagrama_correlacion_${targetNumber}_${new Date().toISOString().split('T')[0]}.svg`;
      link.href = dataUrl;
      link.click();

      console.log('✅ Exportación SVG completada');
    } catch (error) {
      console.error('❌ Error al exportar SVG:', error);
      alert('Error al exportar como SVG. Intente nuevamente.');
    }
  }, [targetNumber]);

  const handleExportJSON = useCallback(() => {
    const exportData = {
      metadata: {
        timestamp: new Date().toISOString(),
        targetNumber,
        totalNodes: flowNodes.length,
        totalEdges: flowEdges.length,
        mode: currentMode,
        filters
      },
      nodes: flowNodes,
      edges: flowEdges
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { 
      type: 'application/json' 
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `diagrama_correlacion_${targetNumber}_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);

    console.log('📊 Diagrama exportado como JSON');
  }, [flowNodes, flowEdges, targetNumber, currentMode, filters]);

  // Estadísticas del diagrama
  const diagramStats = useMemo(() => ({
    totalNodes: flowNodes.length,
    totalEdges: flowEdges.length,
    targetExists: flowNodes.some(node => node.data?.isTarget),
    connectedNodes: new Set([
      ...flowEdges.map(edge => edge.source),
      ...flowEdges.map(edge => edge.target)
    ]).size
  }), [flowNodes, flowEdges]);

  // Manejar ESC para cerrar
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
    }

    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  return (
    <div className="w-full h-full flex flex-col">
      {/* Header con selector de modos */}
      <div className="flex items-center justify-between p-4 border-b border-secondary-light">
        <div className="flex-1">
          <h2 className="text-xl font-semibold text-white mb-2">
            🕸️ Diagrama de Correlación Telefónica
          </h2>
          <p className="text-sm text-gray-400">
            🎯 Objetivo: <span className="text-cyan-300 font-bold">{targetNumber}</span>
            {' '} | {diagramStats.totalNodes} nodos | {diagramStats.totalEdges} conexiones
          </p>
        </div>

        {/* Selector de modos */}
        <div className="flex items-center gap-2 mx-4">
          <span className="text-sm text-gray-400">Modo:</span>
          <select
            value={currentMode}
            onChange={(e) => handleModeChange(e.target.value as VisualizationMode)}
            className="bg-secondary-light text-white text-sm rounded px-3 py-1 border border-gray-600 focus:border-cyan-400 focus:outline-none"
          >
            {Object.values(VISUALIZATION_MODES).map(mode => (
              <option key={mode.id} value={mode.id}>
                {mode.icon} {mode.name}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white transition-colors p-2 hover:bg-secondary-light rounded-lg"
          title="Cerrar diagrama (ESC)"
        >
          <span className="text-xl">✕</span>
        </button>
      </div>

      {/* Contenedor principal con React Flow y panel lateral */}
      <div className="flex-1 flex overflow-hidden">
        {/* Área del diagrama React Flow */}
        <div className="flex-1 relative">
          {diagramStats.totalNodes === 0 ? (
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
              onNodeClick={handleNodeClick}
              onEdgeClick={handleEdgeClick}
              onPaneClick={handlePaneClick}
              nodeTypes={nodeTypes}
              edgeTypes={edgeTypes}
              defaultViewport={{ x: 0, y: 0, zoom: 0.8 }}
              minZoom={0.3}
              maxZoom={2}
              fitView
              fitViewOptions={{ padding: 0.2 }}
              proOptions={{ hideAttribution: true }}
              nodesDraggable={true}
              nodesConnectable={false}
              elementsSelectable={true}
            >
              {/* Fondo con patrón */}
              <Background 
                variant="dots" 
                gap={20} 
                size={1} 
                color="#374151"
              />

              {/* Panel de información del modo actual */}
              <Panel position="top-left" className="bg-gray-800/90 backdrop-blur-sm p-3 rounded-lg border border-gray-600">
                <div className="text-white text-sm font-medium mb-1">
                  {VISUALIZATION_MODES[currentMode].icon} {VISUALIZATION_MODES[currentMode].name}
                </div>
                <div className="text-xs text-gray-300">
                  {VISUALIZATION_MODES[currentMode].description}
                </div>
              </Panel>
            </ReactFlow>
          )}

          {/* Tooltips */}
          {nodeTooltip && (
            <div 
              className="fixed z-50 bg-gray-800 border border-gray-600 rounded-lg p-3 text-white text-sm shadow-lg pointer-events-none"
              style={{
                left: nodeTooltip.position.x - 100,
                top: nodeTooltip.position.y - 100,
                transform: 'translateX(-50%)'
              }}
            >
              <div className="font-bold text-cyan-300 mb-2">
                📱 {nodeTooltip.node.data.phoneNumber}
              </div>
              <div className="space-y-1 text-xs">
                <div>Tipo: {nodeTooltip.node.data.isTarget ? '🎯 Objetivo' : '👤 Participante'}</div>
                <div>Correlación: <span className="font-mono">{nodeTooltip.node.data.correlationLevel}</span> interacciones</div>
                <div>Entrantes: <span className="text-green-400">{nodeTooltip.node.data.stats.incoming}</span></div>
                <div>Salientes: <span className="text-red-400">{nodeTooltip.node.data.stats.outgoing}</span></div>
                <div>Duración total: <span className="font-mono">{Math.round(nodeTooltip.node.data.stats.totalDuration / 60)}min</span></div>
              </div>
              
              {/* Flecha del tooltip */}
              <div 
                className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-800"
              />
            </div>
          )}

          {edgeTooltip && (
            <div 
              className="fixed z-50 bg-gray-800 border border-gray-600 rounded-lg p-3 text-white text-sm shadow-lg pointer-events-none max-w-xs"
              style={{
                left: edgeTooltip.position.x - 150,
                top: edgeTooltip.position.y - 120,
                transform: 'translateX(-50%)'
              }}
            >
              <div className="font-bold text-cyan-300 mb-2">
                🔗 Comunicaciones
              </div>
              <div className="space-y-1 text-xs">
                <div>Total llamadas: <span className="font-mono text-yellow-400">{edgeTooltip.interactions.length}</span></div>
                <div>Dirección: <span className="font-bold">{edgeTooltip.edge.data.direction === 'incoming' ? '📥 Entrante' : edgeTooltip.edge.data.direction === 'outgoing' ? '📤 Saliente' : '↔️ Bidireccional'}</span></div>
                {edgeTooltip.edge.data.cellIds.length > 0 && (
                  <div>Celdas: <span className="font-mono text-gray-300">{edgeTooltip.edge.data.cellIds.slice(0, 3).join(', ')}</span>{edgeTooltip.edge.data.cellIds.length > 3 && '...'}</div>
                )}
                
                {/* Muestra detalles de las primeras 3 interacciones */}
                {edgeTooltip.interactions.slice(0, 3).map((interaction, idx) => (
                  <div key={idx} className="mt-2 pt-2 border-t border-gray-600">
                    <div className="text-gray-300">
                      {new Date(interaction.fecha_hora).toLocaleDateString('es-ES')} {new Date(interaction.fecha_hora).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}
                    </div>
                    <div>Duración: {Math.floor(interaction.duracion / 60)}:{(interaction.duracion % 60).toString().padStart(2, '0')}</div>
                  </div>
                ))}
                
                {edgeTooltip.interactions.length > 3 && (
                  <div className="text-xs text-gray-400 mt-2">
                    ... y {edgeTooltip.interactions.length - 3} más
                  </div>
                )}
              </div>
              
              {/* Flecha del tooltip */}
              <div 
                className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-800"
              />
            </div>
          )}
        </div>

        {/* Panel lateral de controles */}
        <div className="w-80 border-l border-secondary-light bg-secondary">
          <CorrelationControls
            filters={filters}
            onFilterChange={handleFilterChange}
            diagramStats={diagramStats}
            onZoomIn={handleZoomIn}
            onZoomOut={handleZoomOut}
            onZoomReset={handleZoomReset}
            onFitToScreen={handleFitToScreen}
            onExportPNG={handleExportPNG}
            onExportSVG={handleExportSVG}
            onExportJSON={handleExportJSON}
          />
        </div>
      </div>

      {/* Footer con información */}
      <div className="px-4 py-3 border-t border-secondary-light">
        <div className="flex items-center justify-between text-sm text-gray-400">
          <div>
            🎯 React Flow v12 - Modo: {VISUALIZATION_MODES[currentMode].name}
          </div>
          <div>
            Arrastra nodos • Zoom con scroll • ESC para cerrar
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * Componente principal con ReactFlowProvider wrapper
 */
const PhoneCorrelationViewer: React.FC<PhoneCorrelationViewerProps> = (props) => {
  if (!props.isOpen) return null;

  return (
    <div 
      className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      onClick={props.onClose}
    >
      <div 
        className="bg-secondary rounded-xl shadow-2xl border border-secondary-light overflow-hidden"
        style={{ 
          width: '90vw', 
          height: '85vh',
          maxWidth: '1600px',
          maxHeight: '1000px'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <ReactFlowProvider>
          <PhoneCorrelationDiagramContent {...props} />
        </ReactFlowProvider>
      </div>
    </div>
  );
};

export default PhoneCorrelationViewer;