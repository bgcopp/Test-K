/**
 * Hook para transformar datos CallInteraction[] a formato React Flow
 * Boris & Claude Code - 2025-08-21
 */

import { useMemo } from 'react';
import { 
    CallInteraction, 
    PhoneNode, 
    PhoneConnection, 
    DiagramFilters,
    PhoneNodeData,
    ConnectionData 
} from '../types/correlation.types';
import { getPhoneNumberColor, getOperatorColor, getConnectionColor } from '../utils/colorSchemes';

interface UseCorrelationDataResult {
    nodes: PhoneNode[];
    edges: PhoneConnection[];
    stats: {
        totalNumbers: number;
        totalInteractions: number;
        averageCallDuration: number;
        mostActiveNumber: string;
        operatorDistribution: Record<string, number>;
    };
}

/**
 * Hook principal para procesar datos de correlación telefónica
 */
export function useCorrelationData(
    interactions: CallInteraction[],
    targetNumber: string,
    filters: DiagramFilters
): UseCorrelationDataResult {
    
    return useMemo(() => {
        if (!interactions.length) {
            return {
                nodes: [],
                edges: [],
                stats: {
                    totalNumbers: 0,
                    totalInteractions: 0,
                    averageCallDuration: 0,
                    mostActiveNumber: '',
                    operatorDistribution: {}
                }
            };
        }

        // ==================== PROCESAMIENTO DE NÚMEROS ÚNICOS ====================
        
        const phoneNumberMap = new Map<string, {
            interactions: CallInteraction[];
            totalDuration: number;
            incomingCount: number;
            outgoingCount: number;
            operators: Set<string>;
            lastInteraction: string;
            hunterPoints: Set<string>;
            coordinates: { lat: number; lon: number; count: number } | null;
        }>();

        // Procesar cada interacción para agregar datos por número
        interactions.forEach(interaction => {
            const { originador, receptor, duracion, operador, fecha_hora } = interaction;
            
            // Procesar originador
            if (!phoneNumberMap.has(originador)) {
                phoneNumberMap.set(originador, {
                    interactions: [],
                    totalDuration: 0,
                    incomingCount: 0,
                    outgoingCount: 0,
                    operators: new Set(),
                    lastInteraction: fecha_hora,
                    hunterPoints: new Set(),
                    coordinates: null
                });
            }
            
            const originadorData = phoneNumberMap.get(originador)!;
            originadorData.interactions.push(interaction);
            originadorData.totalDuration += duracion;
            originadorData.operators.add(operador);
            originadorData.outgoingCount += (originador === targetNumber ? 1 : 0);
            originadorData.incomingCount += (originador !== targetNumber ? 1 : 0);
            
            // Actualizar última interacción
            if (new Date(fecha_hora) > new Date(originadorData.lastInteraction)) {
                originadorData.lastInteraction = fecha_hora;
            }
            
            // Agregar puntos HUNTER
            if (interaction.punto_hunter) {
                originadorData.hunterPoints.add(interaction.punto_hunter);
            }
            if (interaction.punto_hunter_origen) {
                originadorData.hunterPoints.add(interaction.punto_hunter_origen);
            }
            
            // Procesar coordenadas GPS (promedio ponderado)
            if (interaction.lat_hunter && interaction.lon_hunter) {
                if (!originadorData.coordinates) {
                    originadorData.coordinates = {
                        lat: interaction.lat_hunter,
                        lon: interaction.lon_hunter,
                        count: 1
                    };
                } else {
                    const { lat, lon, count } = originadorData.coordinates;
                    originadorData.coordinates = {
                        lat: (lat * count + interaction.lat_hunter) / (count + 1),
                        lon: (lon * count + interaction.lon_hunter) / (count + 1),
                        count: count + 1
                    };
                }
            }
            
            // Procesar receptor (similar al originador)
            if (!phoneNumberMap.has(receptor)) {
                phoneNumberMap.set(receptor, {
                    interactions: [],
                    totalDuration: 0,
                    incomingCount: 0,
                    outgoingCount: 0,
                    operators: new Set(),
                    lastInteraction: fecha_hora,
                    hunterPoints: new Set(),
                    coordinates: null
                });
            }
            
            const receptorData = phoneNumberMap.get(receptor)!;
            receptorData.interactions.push(interaction);
            receptorData.totalDuration += duracion;
            receptorData.operators.add(operador);
            receptorData.incomingCount += (receptor === targetNumber ? 1 : 0);
            receptorData.outgoingCount += (receptor !== targetNumber ? 1 : 0);
            
            // Actualizar última interacción
            if (new Date(fecha_hora) > new Date(receptorData.lastInteraction)) {
                receptorData.lastInteraction = fecha_hora;
            }
            
            // Agregar puntos HUNTER
            if (interaction.punto_hunter) {
                receptorData.hunterPoints.add(interaction.punto_hunter);
            }
            if (interaction.punto_hunter_destino) {
                receptorData.hunterPoints.add(interaction.punto_hunter_destino);
            }
            
            // Procesar coordenadas GPS para receptor
            if (interaction.lat_hunter && interaction.lon_hunter) {
                if (!receptorData.coordinates) {
                    receptorData.coordinates = {
                        lat: interaction.lat_hunter,
                        lon: interaction.lon_hunter,
                        count: 1
                    };
                } else {
                    const { lat, lon, count } = receptorData.coordinates;
                    receptorData.coordinates = {
                        lat: (lat * count + interaction.lat_hunter) / (count + 1),
                        lon: (lon * count + interaction.lon_hunter) / (count + 1),
                        count: count + 1
                    };
                }
            }
        });

        // ==================== APLICAR FILTROS ====================
        
        const filteredNumbers = Array.from(phoneNumberMap.entries()).filter(([number, data]) => {
            const totalInteractions = data.interactions.length;
            
            // Filtro de correlación mínima
            if (totalInteractions < filters.minCorrelation) {
                return false;
            }
            
            // Filtro de llamadas recientes (últimos 30 días si está habilitado)
            if (filters.onlyRecentCalls) {
                const thirtyDaysAgo = new Date();
                thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
                const lastInteractionDate = new Date(data.lastInteraction);
                
                if (lastInteractionDate < thirtyDaysAgo) {
                    return false;
                }
            }
            
            return true;
        });

        // ==================== GENERAR NODOS ====================
        
        const nodes: PhoneNode[] = filteredNumbers.map(([number, data]) => {
            const isTarget = number === targetNumber;
            const interactionCount = data.interactions.length;
            const primaryOperator = Array.from(data.operators)[0] || 'UNKNOWN';
            
            const nodeData: PhoneNodeData = {
                number,
                isTarget,
                operator: primaryOperator,
                interactionCount,
                lastInteraction: data.lastInteraction,
                callDuration: data.totalDuration,
                hunterPoints: Array.from(data.hunterPoints),
                coordinates: data.coordinates ? {
                    lat: data.coordinates.lat,
                    lon: data.coordinates.lon
                } : undefined,
                connections: {
                    incoming: data.incomingCount,
                    outgoing: data.outgoingCount
                }
            };

            return {
                id: number,
                type: 'default', // Se actualizará según el modo de visualización
                position: { x: 0, y: 0 }, // Se calculará en el layout
                data: nodeData,
                style: {
                    background: getPhoneNumberColor(number),
                    border: `2px solid ${getOperatorColor(primaryOperator)}`,
                    color: 'white',
                    fontSize: '12px',
                    fontWeight: isTarget ? 'bold' : 'normal',
                    width: isTarget ? 80 : 60,
                    height: isTarget ? 80 : 60,
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    textAlign: 'center',
                    boxShadow: isTarget ? '0 0 20px rgba(0, 212, 255, 0.5)' : 'none'
                }
            };
        });

        // ==================== GENERAR CONEXIONES ====================
        
        const connectionMap = new Map<string, {
            interactions: CallInteraction[];
            totalDuration: number;
            callCount: number;
            directions: Set<'incoming' | 'outgoing'>;
            cellIds: Set<string>;
            timeRange: { first: string; last: string };
        }>();

        // Procesar interacciones para crear conexiones
        interactions.forEach(interaction => {
            const { originador, receptor, duracion, fecha_hora, celda_origen, celda_destino } = interaction;
            
            // Crear clave única para la conexión (orden alfabético para bidireccionalidad)
            const connectionKey = originador < receptor 
                ? `${originador}-${receptor}` 
                : `${receptor}-${originador}`;
            
            if (!connectionMap.has(connectionKey)) {
                connectionMap.set(connectionKey, {
                    interactions: [],
                    totalDuration: 0,
                    callCount: 0,
                    directions: new Set(),
                    cellIds: new Set(),
                    timeRange: { first: fecha_hora, last: fecha_hora }
                });
            }
            
            const connectionData = connectionMap.get(connectionKey)!;
            connectionData.interactions.push(interaction);
            connectionData.totalDuration += duracion;
            connectionData.callCount += 1;
            
            // Determinar dirección de la llamada
            if (originador === targetNumber) {
                connectionData.directions.add('outgoing');
            } else if (receptor === targetNumber) {
                connectionData.directions.add('incoming');
            }
            
            // Agregar IDs de celda
            connectionData.cellIds.add(celda_origen);
            connectionData.cellIds.add(celda_destino);
            
            // Actualizar rango temporal
            if (new Date(fecha_hora) < new Date(connectionData.timeRange.first)) {
                connectionData.timeRange.first = fecha_hora;
            }
            if (new Date(fecha_hora) > new Date(connectionData.timeRange.last)) {
                connectionData.timeRange.last = fecha_hora;
            }
        });

        const edges: PhoneConnection[] = Array.from(connectionMap.entries())
            .filter(([connectionKey, data]) => {
                // Filtrar conexiones que cumplen con los criterios
                return data.callCount >= filters.minCorrelation;
            })
            .map(([connectionKey, data]) => {
                const [sourceNumber, targetNumberConnection] = connectionKey.split('-');
                
                // Determinar dirección principal
                let direction: 'incoming' | 'outgoing' | 'bidirectional';
                if (data.directions.size > 1) {
                    direction = 'bidirectional';
                } else if (data.directions.has('incoming')) {
                    direction = 'incoming';
                } else {
                    direction = 'outgoing';
                }
                
                // Calcular peso de la conexión (1-10)
                const strengthWeight = Math.min(10, Math.max(1, data.callCount * 2));
                
                const connectionData: ConnectionData = {
                    interactions: data.interactions,
                    totalDuration: data.totalDuration,
                    callCount: data.callCount,
                    direction,
                    cellIds: Array.from(data.cellIds),
                    timeRange: data.timeRange,
                    strengthWeight
                };

                return {
                    id: connectionKey,
                    source: sourceNumber,
                    target: targetNumberConnection,
                    type: 'default', // Se actualizará según el modo
                    data: connectionData,
                    style: {
                        stroke: getConnectionColor(strengthWeight, direction),
                        strokeWidth: Math.max(2, Math.min(8, strengthWeight)),
                        strokeDasharray: direction === 'bidirectional' ? 'none' : '5,5'
                    },
                    label: filters.showCellIds ? data.cellIds.size > 2 
                        ? `${data.callCount} llamadas` 
                        : Array.from(data.cellIds).join(', ')
                        : `${data.callCount}`,
                    labelBgStyle: { fill: '#374151', fillOpacity: 0.8 },
                    labelStyle: { fontSize: '10px', color: 'white' }
                };
            });

        // ==================== CALCULAR ESTADÍSTICAS ====================
        
        const totalNumbers = filteredNumbers.length;
        const totalInteractions = interactions.length;
        const averageCallDuration = totalInteractions > 0 
            ? interactions.reduce((sum, int) => sum + int.duracion, 0) / totalInteractions 
            : 0;
        
        // Encontrar número más activo
        let mostActiveNumber = targetNumber;
        let maxInteractions = 0;
        filteredNumbers.forEach(([number, data]) => {
            if (data.interactions.length > maxInteractions) {
                maxInteractions = data.interactions.length;
                mostActiveNumber = number;
            }
        });
        
        // Distribución por operador
        const operatorDistribution: Record<string, number> = {};
        interactions.forEach(interaction => {
            const operator = interaction.operador;
            operatorDistribution[operator] = (operatorDistribution[operator] || 0) + 1;
        });

        return {
            nodes,
            edges,
            stats: {
                totalNumbers,
                totalInteractions,
                averageCallDuration,
                mostActiveNumber,
                operatorDistribution
            }
        };

    }, [interactions, targetNumber, filters]);
}

/**
 * Hook para obtener estadísticas resumidas del diagrama
 */
export function useCorrelationStats(
    interactions: CallInteraction[],
    targetNumber: string
) {
    return useMemo(() => {
        if (!interactions.length) {
            return {
                totalCalls: 0,
                totalDuration: 0,
                uniqueNumbers: 0,
                dateRange: { start: '', end: '' },
                topOperators: [],
                callDirections: { incoming: 0, outgoing: 0 }
            };
        }

        const totalCalls = interactions.length;
        const totalDuration = interactions.reduce((sum, int) => sum + int.duracion, 0);
        
        const uniqueNumbers = new Set([
            ...interactions.map(int => int.originador),
            ...interactions.map(int => int.receptor)
        ]).size;

        const dates = interactions.map(int => new Date(int.fecha_hora)).sort((a, b) => a.getTime() - b.getTime());
        const dateRange = {
            start: dates[0]?.toISOString().split('T')[0] || '',
            end: dates[dates.length - 1]?.toISOString().split('T')[0] || ''
        };

        // Top operadores
        const operatorCounts: Record<string, number> = {};
        interactions.forEach(int => {
            operatorCounts[int.operador] = (operatorCounts[int.operador] || 0) + 1;
        });
        const topOperators = Object.entries(operatorCounts)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 3)
            .map(([operator, count]) => ({ operator, count }));

        // Direcciones de llamadas
        const callDirections = {
            incoming: interactions.filter(int => int.receptor === targetNumber).length,
            outgoing: interactions.filter(int => int.originador === targetNumber).length
        };

        return {
            totalCalls,
            totalDuration,
            uniqueNumbers,
            dateRange,
            topOperators,
            callDirections
        };
    }, [interactions, targetNumber]);
}