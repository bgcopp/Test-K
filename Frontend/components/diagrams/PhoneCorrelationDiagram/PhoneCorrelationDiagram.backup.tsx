/**
 * Componente Principal del Diagrama de Correlación Telefónica con D3.js
 * FASE 1 - Implementación básica con visualización de nodos y enlaces
 * Actualizado: 2025-08-20 por Boris - Reemplazo completo de funcionalidad G6
 */

import React, { useRef, useEffect, useState, useCallback } from 'react';
import * as d3 from 'd3';
import { PhoneCorrelationDiagramProps, PhoneNode, PhoneLink, DiagramConfig } from './types/diagram.types';
import { useDataTransformer } from './hooks/useDataTransformer';

// Configuración visual por defecto del diagrama
const DEFAULT_CONFIG: DiagramConfig = {
  width: 800,
  height: 600,
  nodeRadius: {
    target: 20,      // Nodo objetivo más grande
    regular: 15      // Nodos regulares
  },
  linkWidth: {
    base: 2,         // Grosor base de enlaces
    strong: 4        // Enlaces con más interacciones
  },
  colors: {
    target: '#ef4444',  // Rojo para nodo objetivo
    participants: [
      '#f97316', '#ec4899', '#22c55e', '#8b5cf6', '#06b6d4'
    ],
    links: {
      incoming: '#3b82f6',     // Azul para entrantes
      outgoing: '#10b981',     // Verde para salientes  
      bidirectional: '#8b5cf6'  // Púrpura para bidireccionales
    }
  }
};

/**
 * Componente principal que renderiza el diagrama de correlación telefónica usando D3.js
 */
const PhoneCorrelationDiagram: React.FC<PhoneCorrelationDiagramProps> = ({
  isOpen,
  onClose,
  interactions,
  targetNumber
}) => {
  // Referencias DOM
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  
  // Estado local del componente
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  
  // Transformar datos usando el hook personalizado
  const { nodes, links } = useDataTransformer(interactions, targetNumber);
  
  // Debug logging para FASE 1
  console.log('🎨 PhoneCorrelationDiagram - Renderizando con datos:', {
    isOpen,
    targetNumber,
    nodesCount: nodes.length,
    linksCount: links.length,
    interactionsCount: interactions.length,
    dimensions
  });

  /**
   * Función para actualizar las dimensiones del contenedor de manera responsiva
   * CORRECCIÓN BORIS: Mejorado para prevenir desbordamiento del contenedor
   */
  const updateDimensions = useCallback(() => {
    if (containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      // CORRECCIÓN: Padding incrementado a 60px para mejor contenimiento
      const padding = 60;
      const newWidth = Math.max(400, rect.width - padding);  // Mínimo reducido para mejor responsividad
      const newHeight = Math.max(300, rect.height - padding); // Mínimo reducido para mejor responsividad
      
      if (newWidth !== dimensions.width || newHeight !== dimensions.height) {
        setDimensions({ width: newWidth, height: newHeight });
        console.log('📏 PhoneCorrelationDiagram - Dimensiones actualizadas (CORRECCIÓN BORIS):', { width: newWidth, height: newHeight, padding });
      }
    }
  }, [dimensions]);

  /**
   * Función principal para inicializar y renderizar el diagrama D3
   */
  const initializeDiagram = useCallback(() => {
    if (!svgRef.current || !isOpen || nodes.length === 0) {
      console.log('⏸️ PhoneCorrelationDiagram - Saltando inicialización:', { 
        svgExists: !!svgRef.current, 
        isOpen, 
        nodesCount: nodes.length 
      });
      return;
    }

    console.log('🚀 PhoneCorrelationDiagram - Inicializando diagrama D3...');

    // Limpiar contenido SVG anterior
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    // Configurar dimensiones del SVG
    svg
      .attr('width', dimensions.width)
      .attr('height', dimensions.height)
      .style('background-color', '#111827'); // Fondo oscuro consistente con KRONOS

    // Crear grupo principal para zoom/pan (FASE 2)
    const mainGroup = svg.append('g').attr('class', 'main-group');

    // PASO 1: Configurar simulación de fuerzas D3
    // CORRECCIÓN BORIS: Agregada fuerza boundary para contenimiento
    const simulation = d3.forceSimulation<PhoneNode>(nodes)
      .force('link', d3.forceLink<PhoneNode, PhoneLink>(links)
        .id(d => d.id)
        .distance(80) // Distancia base entre nodos conectados
        .strength(0.5)
      )
      .force('charge', d3.forceManyBody()
        .strength(-300) // Repulsión entre nodos
      )
      .force('center', d3.forceCenter(dimensions.width / 2, dimensions.height / 2))
      .force('collision', d3.forceCollide()
        .radius((d: any) => ((d as PhoneNode).isTarget ? DEFAULT_CONFIG.nodeRadius.target : DEFAULT_CONFIG.nodeRadius.regular) + 5)
        .strength(0.7)
      )
      // CORRECCIÓN BORIS: Nueva fuerza boundary para prevenir desbordamiento
      .force('boundary', () => {
        const padding = 30; // Padding mínimo desde los bordes
        nodes.forEach(node => {
          if (node.x) {
            node.x = Math.max(padding, Math.min(dimensions.width - padding, node.x));
          }
          if (node.y) {
            node.y = Math.max(padding, Math.min(dimensions.height - padding, node.y));
          }
        });
      });

    // PASO 2: Renderizar enlaces (líneas entre nodos)
    const linkSelection = mainGroup
      .selectAll('.phone-link')
      .data(links)
      .enter()
      .append('line')
      .attr('class', 'phone-link')
      .attr('stroke', d => d.color)
      .attr('stroke-width', d => d.strength * DEFAULT_CONFIG.linkWidth.base)
      .attr('stroke-opacity', 0.7)
      .style('cursor', 'pointer');

    // CORRECCIÓN BORIS - ISSUE 1: Agregar etiquetas de números celulares en enlaces
    const linkLabelsSelection = mainGroup
      .selectAll('.phone-link-label')
      .data(links)
      .enter()
      .append('text')
      .attr('class', 'phone-link-label')
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .style('fill', '#ffffff')
      .style('font-size', '9px')
      .style('font-weight', '500')
      .style('pointer-events', 'none')
      .style('user-select', 'none')
      .style('text-shadow', '1px 1px 2px rgba(0,0,0,0.8)') // Mejor legibilidad
      .text(d => d.cellIds.length > 0 ? d.cellIds[0] : '') // Mostrar primera celda si existe
      .style('opacity', 0.9);

    // PASO 3: Renderizar nodos (círculos para números telefónicos)
    const nodeSelection = mainGroup
      .selectAll('.phone-node')
      .data(nodes)
      .enter()
      .append('g')
      .attr('class', 'phone-node')
      .style('cursor', 'pointer');

    // Círculos de los nodos
    nodeSelection
      .append('circle')
      .attr('r', d => d.isTarget ? DEFAULT_CONFIG.nodeRadius.target : DEFAULT_CONFIG.nodeRadius.regular)
      .attr('fill', d => d.color)
      .attr('stroke', '#ffffff')
      .attr('stroke-width', d => d.isTarget ? 3 : 2)
      .attr('stroke-opacity', 0.8);

    // Etiquetas de texto con los números telefónicos
    nodeSelection
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '.35em')
      .style('fill', '#ffffff')
      .style('font-size', '10px')
      .style('font-weight', 'bold')
      .style('pointer-events', 'none')
      .text(d => d.label);

    // PASO 4: Configurar interacciones básicas
    
    // Click en nodos
    nodeSelection.on('click', (event, d) => {
      event.stopPropagation();
      const newSelected = selectedNode === d.id ? null : d.id;
      setSelectedNode(newSelected);
      
      console.log('🖱️ PhoneCorrelationDiagram - Nodo clickeado:', {
        nodeId: d.id,
        isTarget: d.isTarget,
        selected: newSelected !== null
      });
      
      // Destacar nodo seleccionado
      nodeSelection.selectAll('circle')
        .attr('stroke-width', (node: any) => {
          const phoneNode = node as PhoneNode;
          if (phoneNode.id === newSelected) return phoneNode.isTarget ? 4 : 3;
          return phoneNode.isTarget ? 3 : 2;
        })
        .attr('stroke', (node: any) => (node as PhoneNode).id === newSelected ? '#fbbf24' : '#ffffff');
    });

    // Hover effects en nodos
    nodeSelection
      .on('mouseenter', (event, d) => {
        // Escalar nodo en hover
        d3.select(event.currentTarget)
          .select('circle')
          .transition()
          .duration(200)
          .attr('r', (d.isTarget ? DEFAULT_CONFIG.nodeRadius.target : DEFAULT_CONFIG.nodeRadius.regular) * 1.2);
          
        console.log('🔍 PhoneCorrelationDiagram - Hover nodo:', d.id);
      })
      .on('mouseleave', (event, d) => {
        // Restaurar tamaño original
        d3.select(event.currentTarget)
          .select('circle')
          .transition()
          .duration(200)
          .attr('r', d.isTarget ? DEFAULT_CONFIG.nodeRadius.target : DEFAULT_CONFIG.nodeRadius.regular);
      });

    // PASO 5: Callback de actualización durante la simulación
    // CORRECCIÓN BORIS: Agregada actualización de etiquetas de celdas con rotación
    simulation.on('tick', () => {
      // Actualizar posiciones de enlaces
      linkSelection
        .attr('x1', d => (d.source as PhoneNode).x!)
        .attr('y1', d => (d.source as PhoneNode).y!)
        .attr('x2', d => (d.target as PhoneNode).x!)
        .attr('y2', d => (d.target as PhoneNode).y!);

      // CORRECCIÓN BORIS: Actualizar posiciones y rotación de etiquetas de celdas
      linkLabelsSelection
        .attr('x', d => {
          const source = d.source as PhoneNode;
          const target = d.target as PhoneNode;
          return (source.x! + target.x!) / 2;
        })
        .attr('y', d => {
          const source = d.source as PhoneNode;
          const target = d.target as PhoneNode;
          return (source.y! + target.y!) / 2;
        })
        .attr('transform', d => {
          // Calcular ángulo y aplicar rotación condicional para mejor legibilidad
          const source = d.source as PhoneNode;
          const target = d.target as PhoneNode;
          const dx = target.x! - source.x!;
          const dy = target.y! - source.y!;
          const angle = Math.atan2(dy, dx) * 180 / Math.PI;
          const centerX = (source.x! + target.x!) / 2;
          const centerY = (source.y! + target.y!) / 2;
          
          // Solo rotar si el ángulo no es muy vertical para mantener legibilidad
          if (Math.abs(angle) > 45 && Math.abs(angle) < 135) {
            return `rotate(${angle}, ${centerX}, ${centerY})`;
          }
          return '';
        });

      // Actualizar posiciones de nodos
      nodeSelection
        .attr('transform', d => `translate(${d.x}, ${d.y})`);
    });

    // Configurar duración de la simulación para FASE 1 (simulación básica)
    simulation.alpha(1).restart();
    
    // Detener simulación después de cierto tiempo para rendimiento
    setTimeout(() => {
      simulation.stop();
      console.log('⏸️ PhoneCorrelationDiagram - Simulación completada');
    }, 3000);

    console.log('✅ PhoneCorrelationDiagram - Diagrama D3 inicializado exitosamente');

  }, [nodes, links, dimensions, isOpen, selectedNode]);

  // Effect para actualizar dimensiones cuando se abre el modal
  useEffect(() => {
    if (isOpen) {
      updateDimensions();
      const handleResize = () => updateDimensions();
      window.addEventListener('resize', handleResize);
      return () => window.removeEventListener('resize', handleResize);
    }
  }, [isOpen, updateDimensions]);

  // Effect para inicializar el diagrama cuando cambian los datos o dimensiones
  useEffect(() => {
    if (isOpen) {
      // Pequeño delay para asegurar que el DOM está listo
      const timer = setTimeout(initializeDiagram, 100);
      return () => clearTimeout(timer);
    }
  }, [isOpen, initializeDiagram]);

  // Manejo de tecla ESC para cerrar
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden'; // Prevenir scroll del body
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

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
          width: '90vw', 
          height: '85vh',
          maxWidth: '1400px',
          maxHeight: '900px'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header del Modal */}
        <div className="flex items-center justify-between p-6 border-b border-secondary-light">
          <div>
            <h2 className="text-xl font-semibold text-white">
              Diagrama de Correlación Telefónica
            </h2>
            <p className="text-sm text-gray-400 mt-1">
              📞 Objetivo: <span className="text-cyan-300 font-bold">{targetNumber}</span> | 
              {' '}{nodes.length} nodos | {links.length} conexiones | 
              {' '}{interactions.length} interacciones
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

        {/* Container del Diagrama D3 */}
        <div className="flex-1 p-4" style={{ height: 'calc(85vh - 120px)' }}>
          <div 
            ref={containerRef}
            className="w-full h-full bg-gray-900 rounded-lg border border-secondary-light relative overflow-hidden"
          >
            {nodes.length === 0 ? (
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
              // SVG para renderizado D3
              <svg
                ref={svgRef}
                className="w-full h-full"
                style={{ background: '#111827' }}
              />
            )}
          </div>
        </div>

        {/* Footer con información adicional - FASE 1 básico */}
        <div className="px-6 py-4 border-t border-secondary-light">
          <div className="flex items-center justify-between text-sm text-gray-400">
            <div>
              🎯 Fase 1 - Visualización básica D3.js | 
              {selectedNode && (
                <span className="text-cyan-300 ml-2">
                  Seleccionado: {selectedNode}
                </span>
              )}
            </div>
            <div>
              Haz clic en los nodos para seleccionar | ESC para cerrar
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PhoneCorrelationDiagram;