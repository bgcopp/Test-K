import React, { useRef, useEffect, useState, useCallback } from 'react';
import { Graph, register, ExtensionCategory } from '@antv/g6';
import { ICONS } from '../../constants';
import NetworkDiagramControls from './NetworkDiagramControls';

// Interface para datos del nodo en el diagrama
interface NetworkNode {
    id: string;
    number: string;
    name?: string;
    operator: string;
    correlationLevel: 'target' | 'high' | 'medium' | 'low' | 'indirect';
    interactionCount: number;
    isTarget: boolean;
}

// Interface para enlaces en el diagrama  
interface NetworkEdge {
    id: string;
    source: string;
    target: string;
    cellIds: string[];
    isDirectional: boolean;
    interactionType: 'llamada' | 'datos' | 'mixed';
}

// Interface unificada para props del modal
interface UnifiedInteraction {
    numero_objetivo: string;
    numero_secundario: string;
    fecha_hora: string;
    duracion_segundos: number;
    operador: string;
    celda_inicio: string;
    celda_final: string;
    punto_hunter?: string;
    lat_hunter?: number;
    lon_hunter?: number;
    trafico_total_bytes?: number;
    tipo_conexion?: string;
    tipo_interaccion?: 'llamada' | 'datos';
    hunter_source?: string;
    precision_ubicacion?: string;
}

interface NetworkDiagramModalProps {
    isOpen: boolean;
    onClose: () => void;
    interactions: UnifiedInteraction[];
    targetNumber: string;
}

const NetworkDiagramModal: React.FC<NetworkDiagramModalProps> = ({
    isOpen,
    onClose,
    interactions,
    targetNumber
}) => {
    const diagramContainerRef = useRef<HTMLDivElement>(null);
    const graphRef = useRef<Graph | null>(null);
    const [selectedNode, setSelectedNode] = useState<string | null>(null);
    const [layoutConfig, setLayoutConfig] = useState({
        type: 'force' as const,
        strength: 0.5,
        distance: 100,
        iterations: 100
    });
    const [filters, setFilters] = useState({
        correlationLevels: ['target', 'high', 'medium', 'low', 'indirect'],
        operators: [],
        interactionTypes: ['llamada', 'datos', 'mixed'],
        minInteractions: 1,
        showLabels: true,
        showDirections: true
    });

    // Manejo del cierre con tecla Escape
    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                onClose();
            }
        };

        if (isOpen) {
            document.addEventListener('keydown', handleEscape);
            // Prevenir scroll del body cuando modal está abierto
            document.body.style.overflow = 'hidden';
        }

        return () => {
            document.removeEventListener('keydown', handleEscape);
            document.body.style.overflow = 'unset';
        };
    }, [isOpen, onClose]);

    // Algoritmo avanzado de correlación automática - FASE 3
    const transformDataForDiagram = () => {
        // 🔍 DEBUG: Verificar datos de entrada
        console.log('🔍 DEBUG NetworkDiagramModal - Datos de entrada:', {
            interactionsCount: interactions.length,
            targetNumber,
            sampleInteraction: interactions[0],
            allInteractions: interactions.slice(0, 3) // Primeras 3 para debugging
        });
        
        const nodes: NetworkNode[] = [];
        const edges: NetworkEdge[] = [];
        
        // Mapas para análisis avanzado de correlación
        const numberInteractionMap = new Map<string, {
            count: number;
            operators: Set<string>;
            interactionTypes: Set<string>;
            firstSeen: Date;
            lastSeen: Date;
            callDirections: { incoming: number; outgoing: number; data: number };
            uniquePartners: Set<string>;
            avgDuration: number;
            totalDuration: number;
            geoLocations: Array<{lat?: number; lon?: number}>;
        }>();

        // Análisis inicial de interacciones para correlación inteligente
        interactions.forEach(interaction => {
            const targetNum = interaction.numero_objetivo;
            const secondaryNum = interaction.numero_secundario;
            const interactionDate = new Date(interaction.fecha_hora);
            const duration = interaction.duracion_segundos || 0;

            // Procesar número objetivo
            if (!numberInteractionMap.has(targetNum)) {
                numberInteractionMap.set(targetNum, {
                    count: 0,
                    operators: new Set(),
                    interactionTypes: new Set(),
                    firstSeen: interactionDate,
                    lastSeen: interactionDate,
                    callDirections: { incoming: 0, outgoing: 0, data: 0 },
                    uniquePartners: new Set(),
                    avgDuration: 0,
                    totalDuration: 0,
                    geoLocations: []
                });
            }

            const targetData = numberInteractionMap.get(targetNum)!;
            targetData.count++;
            targetData.operators.add(interaction.operador);
            targetData.interactionTypes.add(interaction.tipo_interaccion || 'llamada');
            targetData.firstSeen = new Date(Math.min(targetData.firstSeen.getTime(), interactionDate.getTime()));
            targetData.lastSeen = new Date(Math.max(targetData.lastSeen.getTime(), interactionDate.getTime()));
            targetData.totalDuration += duration;
            
            // Añadir ubicación GPS si disponible
            if (interaction.lat_hunter && interaction.lon_hunter) {
                targetData.geoLocations.push({
                    lat: typeof interaction.lat_hunter === 'string' ? parseFloat(interaction.lat_hunter) : interaction.lat_hunter,
                    lon: typeof interaction.lon_hunter === 'string' ? parseFloat(interaction.lon_hunter) : interaction.lon_hunter
                });
            }

            // Análisis direccional
            if (interaction.tipo_interaccion === 'datos') {
                targetData.callDirections.data++;
            } else {
                // Para llamadas, usar targetNumber para determinar dirección
                if (targetNum === targetNumber) {
                    targetData.callDirections.outgoing++;
                } else {
                    targetData.callDirections.incoming++;
                }
            }

            // Añadir partner único si existe
            if (secondaryNum) {
                targetData.uniquePartners.add(secondaryNum);
                
                // Procesar número secundario también
                if (!numberInteractionMap.has(secondaryNum)) {
                    numberInteractionMap.set(secondaryNum, {
                        count: 0,
                        operators: new Set(),
                        interactionTypes: new Set(),
                        firstSeen: interactionDate,
                        lastSeen: interactionDate,
                        callDirections: { incoming: 0, outgoing: 0, data: 0 },
                        uniquePartners: new Set(),
                        avgDuration: 0,
                        totalDuration: 0,
                        geoLocations: []
                    });
                }

                const secondaryData = numberInteractionMap.get(secondaryNum)!;
                secondaryData.count++;
                secondaryData.operators.add(interaction.operador);
                secondaryData.interactionTypes.add(interaction.tipo_interaccion || 'llamada');
                secondaryData.uniquePartners.add(targetNum);
                secondaryData.totalDuration += duration;
                
                // Dirección opuesta para número secundario
                if (interaction.tipo_interaccion === 'datos') {
                    secondaryData.callDirections.data++;
                } else {
                    if (secondaryNum === targetNumber) {
                        secondaryData.callDirections.outgoing++;
                    } else {
                        secondaryData.callDirections.incoming++;
                    }
                }
            }
        });

        // Calcular promedios y crear nodos con correlación inteligente
        Array.from(numberInteractionMap.entries()).forEach(([number, data]) => {
            data.avgDuration = data.count > 0 ? data.totalDuration / data.count : 0;
            const isTarget = number === targetNumber;
            
            // Algoritmo de correlación automática avanzada
            let correlationLevel: NetworkNode['correlationLevel'] = 'indirect';
            
            if (isTarget) {
                correlationLevel = 'target';
            } else {
                // Factores de correlación ponderados
                const frequencyScore = Math.min(data.count / 10, 1); // 0-1
                const partnerScore = Math.min(data.uniquePartners.size / 5, 1); // 0-1
                const durationScore = Math.min(data.avgDuration / 300, 1); // 0-1 (5 min max)
                const operatorScore = data.operators.size > 1 ? 0.3 : 0; // Multi-operador bonus
                const geoScore = data.geoLocations.length > 0 ? 0.2 : 0; // GPS data bonus
                
                // Puntuación final ponderada
                const totalScore = (
                    frequencyScore * 0.4 + 
                    partnerScore * 0.3 + 
                    durationScore * 0.2 + 
                    operatorScore + 
                    geoScore
                );
                
                // Clasificación por umbrales adaptativos
                if (totalScore >= 0.8) correlationLevel = 'high';
                else if (totalScore >= 0.6) correlationLevel = 'medium';
                else if (totalScore >= 0.3) correlationLevel = 'low';
                else correlationLevel = 'indirect';
            }

            // Obtener operador principal (más frecuente)
            const operatorArray = Array.from(data.operators);
            const operator = operatorArray[0] || 'Desconocido';

            nodes.push({
                id: number,
                number,
                name: undefined, // TODO: Integrar con directorio de contactos
                operator,
                correlationLevel,
                interactionCount: data.count,
                isTarget
            });
        });

        // Crear enlaces agrupados y optimizados
        const edgeMap = new Map<string, {
            source: string;
            target: string;
            cellIds: Set<string>;
            interactions: UnifiedInteraction[];
            types: Set<string>;
        }>();

        interactions.forEach(interaction => {
            if (!interaction.numero_secundario) return; // Skip datos sin secundario
            
            // Crear clave bidireccional para agrupar enlaces
            const edgeKey = [interaction.numero_objetivo, interaction.numero_secundario]
                .sort()
                .join('-');
            
            if (!edgeMap.has(edgeKey)) {
                edgeMap.set(edgeKey, {
                    source: interaction.numero_objetivo,
                    target: interaction.numero_secundario,
                    cellIds: new Set(),
                    interactions: [],
                    types: new Set()
                });
            }

            const edgeData = edgeMap.get(edgeKey)!;
            edgeData.interactions.push(interaction);
            edgeData.types.add(interaction.tipo_interaccion || 'llamada');
            
            // Añadir IDs de celdas únicas
            if (interaction.celda_inicio) edgeData.cellIds.add(interaction.celda_inicio);
            if (interaction.celda_final) edgeData.cellIds.add(interaction.celda_final);
        });

        // Convertir a edges finales
        Array.from(edgeMap.entries()).forEach(([edgeKey, data]) => {
            const interactionType: 'llamada' | 'datos' | 'mixed' = 
                data.types.size > 1 ? 'mixed' : 
                data.types.has('datos') ? 'datos' : 'llamada';

            edges.push({
                id: edgeKey,
                source: data.source,
                target: data.target,
                cellIds: Array.from(data.cellIds),
                isDirectional: true,
                interactionType
            });
        });

        // 🔍 DEBUG: Verificar datos transformados
        console.log('🔍 DEBUG NetworkDiagramModal - Datos transformados:', {
            nodesGenerated: nodes.length,
            edgesGenerated: edges.length,
            sampleNode: nodes[0],
            sampleEdge: edges[0],
            allNodes: nodes.map(n => ({ id: n.id, correlationLevel: n.correlationLevel, interactionCount: n.interactionCount }))
        });
        
        return { nodes, edges };
    };

    const { nodes, edges } = transformDataForDiagram();

    // ✅ CORRECCIÓN: Filtrar nodos con validación defensiva
    const filteredNodes = nodes.filter(node => {
        // Validación defensiva de propiedades
        if (!node || typeof node.correlationLevel === 'undefined') {
            console.warn('⚠️ WARNING: Nodo con correlationLevel inválido:', node);
            return false;
        }
        
        const correlationMatch = filters.correlationLevels.includes(node.correlationLevel);
        const interactionMatch = (node.interactionCount || 0) >= filters.minInteractions;
        const operatorMatch = filters.operators.length === 0 || filters.operators.includes(node.operator || '');
        
        return correlationMatch && interactionMatch && operatorMatch;
    });

    // Filtrar edges para incluir solo los nodos visibles
    const visibleNodeIds = new Set(filteredNodes.map(n => n.id));
    const filteredEdges = edges.filter(edge => 
        visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target)
    );
    
    // 🔍 DEBUG: Verificar filtrado
    console.log('🔍 DEBUG NetworkDiagramModal - Datos después de filtros:', {
        originalNodes: nodes.length,
        filteredNodes: filteredNodes.length,
        originalEdges: edges.length,
        filteredEdges: filteredEdges.length,
        filtersApplied: filters,
        nodesSample: filteredNodes.slice(0, 3)
    });

    // Estadísticas del diagrama
    const stats = {
        totalNodes: nodes.length,
        totalEdges: edges.length,
        visibleNodes: filteredNodes.length,
        visibleEdges: filteredEdges.length,
        targetNode: nodes.find(n => n.isTarget),
        correlationDistribution: {
            high: filteredNodes.filter(n => n.correlationLevel === 'high').length,
            medium: filteredNodes.filter(n => n.correlationLevel === 'medium').length,
            low: filteredNodes.filter(n => n.correlationLevel === 'low').length,
            indirect: filteredNodes.filter(n => n.correlationLevel === 'indirect').length
        }
    };

    // Inicialización y configuración de G6
    const initializeGraph = useCallback(async () => {
        if (!diagramContainerRef.current || !isOpen) return;

        // Limpiar gráfico anterior si existe
        if (graphRef.current) {
            graphRef.current.destroy();
            graphRef.current = null;
        }

        // Configuración de estilos para nodos por correlación
        const nodeStyles = {
            target: { fill: '#ef4444', stroke: '#dc2626', size: 30 },
            high: { fill: '#f97316', stroke: '#ea580c', size: 25 },
            medium: { fill: '#eab308', stroke: '#ca8a04', size: 22 },
            low: { fill: '#22c55e', stroke: '#16a34a', size: 20 },
            indirect: { fill: '#a855f7', stroke: '#9333ea', size: 18 }
        };

        // Transformar datos a formato G6
        const g6Data = {
            nodes: filteredNodes.map(node => ({
                id: node.id,
                label: filters.showLabels ? 
                    (node.name || node.number.slice(-4)) : '',
                style: {
                    ...nodeStyles[node.correlationLevel],
                    labelCfg: {
                        style: {
                            fill: '#ffffff',
                            fontSize: 10,
                            fontWeight: 'bold',
                            textAlign: 'center',
                            textBaseline: 'middle'
                        }
                    }
                },
                // Datos adicionales para tooltips e interacción
                data: {
                    number: node.number,
                    name: node.name,
                    operator: node.operator,
                    correlationLevel: node.correlationLevel,
                    interactionCount: node.interactionCount,
                    isTarget: node.isTarget
                }
            })),
            edges: filteredEdges.map(edge => ({
                id: edge.id,
                source: edge.source,
                target: edge.target,
                style: {
                    stroke: edge.interactionType === 'datos' ? '#06b6d4' : 
                           edge.interactionType === 'mixed' ? '#8b5cf6' : '#10b981',
                    lineWidth: 2,
                    opacity: 0.6,
                    endArrow: filters.showDirections ? {
                        path: 'M 0,0 L 8,4 L 8,-4 Z',
                        fill: edge.interactionType === 'datos' ? '#06b6d4' : 
                              edge.interactionType === 'mixed' ? '#8b5cf6' : '#10b981'
                    } : undefined
                },
                data: {
                    cellIds: edge.cellIds,
                    interactionType: edge.interactionType,
                    isDirectional: edge.isDirectional
                }
            }))
        };

        // 🔍 DEBUG: Verificar datos G6 antes de crear graph
        console.log('🔍 DEBUG NetworkDiagramModal - Datos G6:', {
            g6DataNodes: g6Data.nodes.length,
            g6DataEdges: g6Data.edges.length,
            containerDimensions: {
                width: diagramContainerRef.current.clientWidth,
                height: diagramContainerRef.current.clientHeight
            },
            layoutType: layoutConfig.type
        });
        
        // Validación crítica: No crear graph si no hay nodos
        if (g6Data.nodes.length === 0) {
            console.warn('⚠️ WARNING NetworkDiagramModal - No hay nodos para mostrar');
            return;
        }
        
        // Configurar layout según tipo seleccionado - G6 v5 API CORREGIDA
        let g6LayoutConfig;
        switch (layoutConfig.type) {
            case 'force':
                g6LayoutConfig = {
                    type: 'force',
                    center: [diagramContainerRef.current.clientWidth / 2, diagramContainerRef.current.clientHeight / 2],
                    linkDistance: layoutConfig.distance,
                    nodeStrength: layoutConfig.strength * 1000,
                    edgeStrength: 0.2,
                    nodeSize: 30,
                    preventOverlap: true,
                    animation: true
                };
                break;
            case 'circular':
                g6LayoutConfig = {
                    type: 'circular',
                    center: [diagramContainerRef.current.clientWidth / 2, diagramContainerRef.current.clientHeight / 2],
                    radius: Math.min(diagramContainerRef.current.clientWidth, diagramContainerRef.current.clientHeight) * 0.3,
                    ordering: 'topology'
                };
                break;
            case 'grid':
                g6LayoutConfig = {
                    type: 'grid',
                    center: [diagramContainerRef.current.clientWidth / 2, diagramContainerRef.current.clientHeight / 2],
                    cols: Math.ceil(Math.sqrt(filteredNodes.length)),
                    rows: Math.ceil(Math.sqrt(filteredNodes.length)),
                    nodeSize: 40
                };
                break;
            default:
                g6LayoutConfig = {
                    type: 'force',
                    center: [diagramContainerRef.current.clientWidth / 2, diagramContainerRef.current.clientHeight / 2]
                };
        }

        // 🔥 CORRECCIÓN DEFINITIVA G6 v5 - PLAN A
        console.log('🔍 DEBUG NetworkDiagramModal - Creando Graph G6 v5 con datos:', {
            nodesCount: g6Data.nodes.length,
            edgesCount: g6Data.edges.length,
            containerSize: {
                width: diagramContainerRef.current.clientWidth,
                height: diagramContainerRef.current.clientHeight
            }
        });

        const graph = new Graph({
            container: diagramContainerRef.current,
            width: diagramContainerRef.current.clientWidth,
            height: diagramContainerRef.current.clientHeight,
            background: '#111827',
            
            // G6 v5: Sin data en constructor, se añade después
            layout: {
                type: layoutConfig.type === 'force' ? 'force2' : layoutConfig.type,  // G6 v5 usa 'force2'
                ...(layoutConfig.type === 'force' && {
                    center: [diagramContainerRef.current.clientWidth / 2, diagramContainerRef.current.clientHeight / 2],
                    linkDistance: layoutConfig.distance,
                    nodeStrength: -layoutConfig.strength * 1000,  // G6 v5: Fuerza negativa
                    edgeStrength: 0.2,
                    preventOverlap: true,
                    nodeSize: 30
                }),
                ...(layoutConfig.type === 'circular' && {
                    center: [diagramContainerRef.current.clientWidth / 2, diagramContainerRef.current.clientHeight / 2],
                    radius: Math.min(diagramContainerRef.current.clientWidth, diagramContainerRef.current.clientHeight) * 0.3
                })
            },
            
            modes: {
                default: ['drag-canvas', 'zoom-canvas', 'drag-node', 'click-select']  // G6 v5: Mantener modes
            },
            
            defaultNode: {
                type: 'circle',
                style: {
                    fill: '#6b7280',
                    stroke: '#374151',
                    lineWidth: 2,
                    size: 20
                }
            },
            
            defaultEdge: {
                type: 'line',
                style: {
                    stroke: '#6b7280',
                    lineWidth: 1,
                    opacity: 0.6
                }
            }
        });

        // G6 v5: Cargar datos y renderizar por separado (CORRECCIÓN DEFINITIVA)
        try {
            console.log('🔍 DEBUG NetworkDiagramModal - Cargando datos con setData()...');
            graph.setData(g6Data);  // G6 v5: setData() es el método correcto
            console.log('✅ DEBUG NetworkDiagramModal - Datos cargados exitosamente con setData()');
            
            // Renderizar (asíncrono en G6 v5)
            await graph.render();
            console.log('✅ DEBUG NetworkDiagramModal - Graph renderizado exitosamente');
            
        } catch (error) {
            console.error('❌ ERROR CRÍTICO G6 v5 - No se pudo cargar/renderizar:', error);
            // Mostrar error en el DOM
            const errorDiv = document.createElement('div');
            errorDiv.innerHTML = `
                <div style="color: #ef4444; text-align: center; padding: 40px;">
                    <div style="font-size: 24px; margin-bottom: 16px;">❌</div>
                    <div style="font-weight: bold; margin-bottom: 8px;">Error G6 v5</div>
                    <div style="font-size: 14px; opacity: 0.8;">
                        ${error.message || 'Error desconocido'}
                    </div>
                </div>
            `;
            diagramContainerRef.current.appendChild(errorDiv);
        }

        // Event listeners para G6 v5
        graph.on('node:click', (e) => {
            const nodeId = e.target?.id || e.itemId;
            if (nodeId) {
                setSelectedNode(nodeId === selectedNode ? null : nodeId);
                console.log('🔍 DEBUG NetworkDiagramModal - Nodo clickeado:', nodeId);
            }
        });

        graph.on('node:pointerenter', (e) => {
            const nodeId = e.target?.id || e.itemId;
            if (nodeId) {
                console.log('🔍 DEBUG NetworkDiagramModal - Mouse enter nodo:', nodeId);
            }
        });

        graph.on('node:pointerleave', (e) => {
            const nodeId = e.target?.id || e.itemId;
            if (nodeId) {
                console.log('🔍 DEBUG NetworkDiagramModal - Mouse leave nodo:', nodeId);
            }
        });

        graphRef.current = graph;
        console.log('✅ DEBUG NetworkDiagramModal - Diagrama G6 v5 inicializado completamente');

    }, [isOpen, filteredNodes, filteredEdges, layoutConfig, filters, selectedNode]);

    // Efecto para inicializar G6 cuando se abre el modal
    useEffect(() => {
        if (isOpen && diagramContainerRef.current) {
            // Delay para permitir que el DOM se renderice completamente
            const timer = setTimeout(() => {
                initializeGraph().catch(error => {
                    console.error('❌ ERROR en initializeGraph:', error);
                });
            }, 100);
            return () => clearTimeout(timer);
        }
    }, [isOpen, initializeGraph]);

    // Efecto para limpiar el gráfico al cerrar
    useEffect(() => {
        return () => {
            if (graphRef.current) {
                graphRef.current.destroy();
                graphRef.current = null;
            }
        };
    }, []);

    // Callbacks para controles
    const handleLayoutChange = useCallback((newLayout: any) => {
        setLayoutConfig(newLayout);
    }, []);

    const handleFilterChange = useCallback((newFilters: any) => {
        setFilters(newFilters);
    }, []);

    const handleExport = useCallback((type: 'png' | 'svg' | 'json') => {
        if (!graphRef.current) return;

        switch (type) {
            case 'png':
                graphRef.current.downloadFullImage('network-diagram', 'image/png');
                break;
            case 'svg':
                // TODO: Implementar exportación SVG
                console.log('SVG export not implemented yet');
                break;
            case 'json':
                const data = {
                    nodes: filteredNodes,
                    edges: filteredEdges,
                    metadata: {
                        targetNumber,
                        timestamp: new Date().toISOString(),
                        stats
                    }
                };
                const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `network-diagram-${targetNumber}-${Date.now()}.json`;
                a.click();
                URL.revokeObjectURL(url);
                break;
        }
    }, [filteredNodes, filteredEdges, targetNumber, stats]);

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
                            Diagrama de Correlación de Red
                        </h2>
                        <p className="text-sm text-gray-400 mt-1">
                            Objetivo: <span className="text-cyan-300 font-bold">{targetNumber}</span> | 
                            {' '}{stats.visibleNodes}/{stats.totalNodes} nodos | {stats.visibleEdges} conexiones
                        </p>
                    </div>
                    
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-white transition-colors p-2 hover:bg-secondary-light rounded-lg"
                        title="Cerrar diagrama"
                    >
                        <span className="text-xl">{ICONS.close}</span>
                    </button>
                </div>

                {/* Controles del Diagrama */}
                <NetworkDiagramControls
                    nodes={nodes}
                    edges={edges}
                    onLayoutChange={handleLayoutChange}
                    onFilterChange={handleFilterChange}
                    onExport={handleExport}
                />

                {/* Container del Diagrama */}
                <div className="flex-1 p-4" style={{ height: 'calc(85vh - 180px)' }}>
                    <div 
                        ref={diagramContainerRef}
                        className="w-full h-full bg-gray-900 rounded-lg border border-secondary-light relative overflow-hidden"
                    >
                        {/* G6 se inicializa aquí automáticamente */}
                        {stats.visibleNodes === 0 && (
                            <div className="absolute inset-0 flex items-center justify-center">
                                <div className="text-center text-gray-400">
                                    <div className="text-4xl mb-4">🔍</div>
                                    <div className="text-lg font-medium text-white">Sin datos para mostrar</div>
                                    <div className="text-sm mt-2">
                                        Ajusta los filtros para ver el diagrama de red
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default NetworkDiagramModal;