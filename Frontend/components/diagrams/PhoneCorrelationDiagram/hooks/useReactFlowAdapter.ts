/**
 * Hook React Flow Adapter - Transforma datos D3.js a React Flow
 * Convierte PhoneNode[] y PhoneLink[] del useDataTransformer a formato React Flow
 * Actualizado: 2025-08-20 por Boris - Adaptador D3→ReactFlow
 */

import { useMemo } from 'react';
import { MarkerType } from '@xyflow/react';
import { 
  PhoneFlowNode, 
  PhoneFlowEdge, 
  ReactFlowAdapterProps,
  ReactFlowAdapterResult,
  ReactFlowVisualConfig
} from '../types/reactflow.types';
import { PhoneNode, PhoneLink } from '../types/diagram.types';
import { useDataTransformer } from './useDataTransformer';
import CustomPhoneNode from '../components/CustomPhoneNode';
import CustomPhoneEdge from '../components/CustomPhoneEdge';

// Configuración visual KRONOS según imagen de referencia
const VISUAL_CONFIG: ReactFlowVisualConfig = {
  node: {
    size: {
      target: 45,      // Radio nodo objetivo
      regular: 35      // Radio nodos regulares
    },
    colors: {
      target: '#ef4444',    // Rojo objetivo - ÚNICO COLOR ESPECIAL
      highCorr: '#6b7280',  // Gris participantes - Correlación alta
      medCorr: '#6b7280',   // Gris participantes - Correlación media
      lowCorr: '#6b7280',   // Gris participantes - Correlación baja
      indirect: '#6b7280'   // Gris participantes - Relación indirecta
      // BORIS: Simplificado - solo 2 colores para investigadores
    }
  },
  edge: {
    width: {
      base: 2,
      strong: 6
    },
    colors: {
      incoming: '#22c55e',   // Verde entrantes - ÚNICO COLOR PERMITIDO
      outgoing: '#ef4444',   // Rojo salientes - ÚNICO COLOR PERMITIDO
      bidirectional: '#8b5cf6' // Púrpura para casos especiales
      // BORIS: Eliminado bidirectional - crear líneas separadas
    }
  },
  theme: {
    background: '#0f172a',
    panel: 'rgba(15, 23, 42, 0.9)',
    border: '#374151',
    text: '#f8fafc',
    textMuted: '#94a3b8'
  }
};

/**
 * Hook principal para adaptar datos D3 a React Flow
 * Transforma PhoneNode[] y PhoneLink[] a formato React Flow
 */
export const useReactFlowAdapter = ({
  interactions,
  targetNumber,
  filters
}: ReactFlowAdapterProps): ReactFlowAdapterResult => {

  // Obtener datos transformados desde el hook D3 existente
  const { nodes: d3Nodes, links: d3Links } = useDataTransformer(interactions, targetNumber);

  // Resultado memoizado para optimizar rendimiento
  return useMemo(() => {
    console.log('🔄 useReactFlowAdapter - Iniciando adaptación:', {
      d3NodesCount: d3Nodes.length,
      d3LinksCount: d3Links.length,
      targetNumber,
      filters
    });

    // PASO 1: Transformar nodos D3 a nodos React Flow
    const reactFlowNodes: PhoneFlowNode[] = d3Nodes.map((d3Node: PhoneNode, index) => {
      
      // Calcular nivel de correlación total FUERA del scope de color
      const totalInteractions = d3Node.stats.incoming + d3Node.stats.outgoing;
      
      // BORIS: Sistema simplificado - solo 2 colores para investigadores
      const nodeColor = d3Node.isTarget 
        ? VISUAL_CONFIG.node.colors.target      // Rojo para objetivo
        : VISUAL_CONFIG.node.colors.highCorr;   // Gris para participantes

      // Calcular posición inicial para layout force-directed
      const angle = (index * 2 * Math.PI) / d3Nodes.length;
      const radius = d3Node.isTarget ? 0 : 200 + Math.random() * 100;
      
      const position = d3Node.isTarget 
        ? { x: 400, y: 300 } // Centro para nodo objetivo
        : {
            x: 400 + Math.cos(angle) * radius + (Math.random() - 0.5) * 50,
            y: 300 + Math.sin(angle) * radius + (Math.random() - 0.5) * 50
          };

      return {
        id: d3Node.id,
        type: 'phoneNode',
        position,
        data: {
          phoneNumber: d3Node.id,
          isTarget: d3Node.isTarget,
          correlationLevel: totalInteractions,
          avatar: d3Node.avatar,
          color: nodeColor,
          stats: d3Node.stats
        },
        draggable: true,
        selectable: true,
        deletable: false
      };
    });

    // PASO 2: Transformar enlaces D3 a enlaces React Flow (SEPARAR BIDIRECCIONALES)
    const reactFlowEdges: PhoneFlowEdge[] = [];
    
    d3Links.forEach((d3Link: PhoneLink, index) => {
      // Extraer IDs de source y target (pueden ser string o PhoneNode)
      const sourceId = typeof d3Link.source === 'string' ? d3Link.source : d3Link.source.id;
      const targetId = typeof d3Link.target === 'string' ? d3Link.target : d3Link.target.id;

      // BORIS: Eliminar bidireccional - crear líneas separadas
      if (d3Link.direction === 'bidirectional') {
        
        // Crear línea OUTGOING (source -> target)
        reactFlowEdges.push({
          id: `edge-${sourceId}-${targetId}-out-${index}`,
          type: 'phoneEdge',
          source: sourceId,
          target: targetId,
          data: {
            cellIds: d3Link.cellIds,
            direction: 'outgoing',
            callCount: Math.ceil(d3Link.callCount / 2), // Dividir llamadas
            strength: d3Link.strength,
            color: VISUAL_CONFIG.edge.colors.outgoing, // Rojo fijo
            labelStrategy: filters.labelStrategy // Estrategia de etiquetas Boris UX
          },
          markerEnd: {
            type: MarkerType.Arrow,
            color: VISUAL_CONFIG.edge.colors.outgoing,
            width: 20,
            height: 20
          },
          style: {
            strokeWidth: Math.max(2, d3Link.strength),
            stroke: VISUAL_CONFIG.edge.colors.outgoing
          }
        });

        // Crear línea INCOMING (target -> source) 
        reactFlowEdges.push({
          id: `edge-${targetId}-${sourceId}-in-${index}`,
          type: 'phoneEdge',
          source: targetId,
          target: sourceId,
          data: {
            cellIds: d3Link.cellIds,
            direction: 'incoming',
            callCount: Math.floor(d3Link.callCount / 2), // Dividir llamadas
            strength: d3Link.strength,
            color: VISUAL_CONFIG.edge.colors.incoming, // Verde fijo
            labelStrategy: filters.labelStrategy // Estrategia de etiquetas Boris UX
          },
          markerEnd: {
            type: MarkerType.Arrow,
            color: VISUAL_CONFIG.edge.colors.incoming,
            width: 20,
            height: 20
          },
          style: {
            strokeWidth: Math.max(2, d3Link.strength),
            stroke: VISUAL_CONFIG.edge.colors.incoming
          }
        });

      } else {
        // Líneas direccionales simples - determinar color correcto
        const edgeColor = d3Link.direction === 'incoming' 
          ? VISUAL_CONFIG.edge.colors.incoming 
          : VISUAL_CONFIG.edge.colors.outgoing;

        reactFlowEdges.push({
          id: `edge-${sourceId}-${targetId}-${d3Link.direction}-${index}`,
          type: 'phoneEdge',
          source: sourceId,
          target: targetId,
          data: {
            cellIds: d3Link.cellIds,
            direction: d3Link.direction,
            callCount: d3Link.callCount,
            strength: d3Link.strength,
            color: edgeColor, // Solo verde o rojo
            labelStrategy: filters.labelStrategy // Estrategia de etiquetas Boris UX
          },
          markerEnd: {
            type: MarkerType.Arrow,
            color: edgeColor,
            width: 20,
            height: 20
          },
          style: {
            strokeWidth: Math.max(2, d3Link.strength),
            stroke: edgeColor
          }
        });
      }
    });

    // PASO 3: Aplicar filtros si están definidos
    let filteredNodes = reactFlowNodes;
    let filteredEdges = reactFlowEdges;

    if (filters.minCorrelation > 0) {
      filteredNodes = reactFlowNodes.filter(node => 
        node.data.correlationLevel >= filters.minCorrelation || node.data.isTarget
      );
      
      const nodeIds = new Set(filteredNodes.map(node => node.id));
      filteredEdges = reactFlowEdges.filter(edge => 
        nodeIds.has(edge.source) && nodeIds.has(edge.target)
      );
    }

    if (!filters.showIsolatedNodes) {
      const connectedNodeIds = new Set<string>();
      filteredEdges.forEach(edge => {
        connectedNodeIds.add(edge.source);
        connectedNodeIds.add(edge.target);
      });
      
      filteredNodes = filteredNodes.filter(node => 
        connectedNodeIds.has(node.id) || node.data.isTarget
      );
    }

    // PASO 4: Definir tipos de nodos y enlaces personalizados
    const nodeTypes = {
      phoneNode: CustomPhoneNode
    };

    const edgeTypes = {
      phoneEdge: CustomPhoneEdge
    };

    const result: ReactFlowAdapterResult = {
      nodes: filteredNodes,
      edges: filteredEdges,  
      nodeTypes,
      edgeTypes
    };

    console.log('✅ useReactFlowAdapter - Adaptación completada:', {
      nodesGenerated: filteredNodes.length,
      edgesGenerated: filteredEdges.length,
      targetNodeExists: filteredNodes.some(n => n.data.isTarget),
      sampleNode: filteredNodes[0] ? {
        id: filteredNodes[0].id,
        isTarget: filteredNodes[0].data.isTarget,
        color: filteredNodes[0].data.color,
        correlationLevel: filteredNodes[0].data.correlationLevel
      } : null
    });

    return result;

  }, [d3Nodes, d3Links, filters, targetNumber]);
};

export default useReactFlowAdapter;