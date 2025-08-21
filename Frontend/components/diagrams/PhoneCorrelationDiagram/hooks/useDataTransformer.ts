/**
 * Hook para transformación de datos UnifiedInteraction[] a formato D3.js
 * FASE 1 - Transformación básica de datos telefónicos para visualización
 * Actualizado: 2025-08-20 por Boris - Sistema de correlación inteligente
 */

import { useMemo } from 'react';
import { UnifiedInteraction, PhoneNode, PhoneLink, DiagramData } from '../types/diagram.types';

// Paleta de colores profesional para participantes (excluye el color target rojo)
const PARTICIPANT_COLORS = [
  '#f97316', // Naranja
  '#ec4899', // Rosa
  '#22c55e', // Verde
  '#8b5cf6', // Púrpura
  '#06b6d4', // Cian
  '#eab308', // Amarillo
  '#ef4444', // Rojo claro (diferente al target)
  '#84cc16', // Lima
  '#a855f7', // Violeta
  '#f59e0b', // Ámbar
];

// Colores para enlaces basados en direccionalidad
const LINK_COLORS = {
  incoming: '#3b82f6',     // Azul para llamadas entrantes
  outgoing: '#10b981',     // Verde para llamadas salientes
  bidirectional: '#8b5cf6' // Púrpura para bidireccionales
};

/**
 * Hook principal para transformar datos de interacciones telefónicas a formato D3
 * @param interactions - Array de interacciones unificadas del backend
 * @param targetNumber - Número telefónico objetivo (nodo central)
 * @returns DiagramData con nodos y enlaces listos para D3
 */
export const useDataTransformer = (
  interactions: UnifiedInteraction[], 
  targetNumber: string
): DiagramData => {
  
  return useMemo(() => {
    console.log('🔄 useDataTransformer - Iniciando transformación:', {
      interactionsCount: interactions.length,
      targetNumber,
      sampleInteraction: interactions[0]
    });

    // Maps para análisis y agregación de datos
    const phoneNumberMap = new Map<string, {
      interactions: UnifiedInteraction[];
      incoming: number;
      outgoing: number;
      totalDuration: number;
      lastContact: Date;
      operators: Set<string>;
      partners: Set<string>;
    }>();

    const connectionMap = new Map<string, {
      source: string;
      target: string;
      cellIds: Set<string>;
      callCount: number;
      interactions: UnifiedInteraction[];
      directions: Set<'incoming' | 'outgoing'>;
    }>();

    // PASO 1: Análisis inicial de interacciones
    interactions.forEach(interaction => {
      const originNumber = interaction.numero_objetivo;
      const destinyNumber = interaction.numero_secundario;
      const interactionDate = new Date(interaction.fecha_hora);
      const duration = interaction.duracion_segundos || 0;

      // Procesar número origen
      if (!phoneNumberMap.has(originNumber)) {
        phoneNumberMap.set(originNumber, {
          interactions: [],
          incoming: 0,
          outgoing: 0,
          totalDuration: 0,
          lastContact: interactionDate,
          operators: new Set(),
          partners: new Set()
        });
      }

      const originData = phoneNumberMap.get(originNumber)!;
      originData.interactions.push(interaction);
      originData.totalDuration += duration;
      originData.lastContact = new Date(Math.max(originData.lastContact.getTime(), interactionDate.getTime()));
      originData.operators.add(interaction.operador);

      // Determinar direccionalidad basada en targetNumber
      if (originNumber === targetNumber) {
        originData.outgoing++;
      } else {
        originData.incoming++;
      }

      // Procesar número destino si existe (no aplica para datos móviles)
      if (destinyNumber && interaction.tipo_interaccion === 'llamada') {
        originData.partners.add(destinyNumber);

        if (!phoneNumberMap.has(destinyNumber)) {
          phoneNumberMap.set(destinyNumber, {
            interactions: [],
            incoming: 0,
            outgoing: 0,
            totalDuration: 0,
            lastContact: interactionDate,
            operators: new Set(),
            partners: new Set()
          });
        }

        const destinyData = phoneNumberMap.get(destinyNumber)!;
        destinyData.interactions.push(interaction);
        destinyData.totalDuration += duration;
        destinyData.lastContact = new Date(Math.max(destinyData.lastContact.getTime(), interactionDate.getTime()));
        destinyData.operators.add(interaction.operador);
        destinyData.partners.add(originNumber);

        // Direccionalidad inversa para el destino
        if (destinyNumber === targetNumber) {
          destinyData.outgoing++;
        } else {
          destinyData.incoming++;
        }

        // PASO 2: Crear conexiones entre nodos
        const connectionKey = [originNumber, destinyNumber].sort().join('↔');
        
        if (!connectionMap.has(connectionKey)) {
          connectionMap.set(connectionKey, {
            source: originNumber,
            target: destinyNumber,
            cellIds: new Set(),
            callCount: 0,
            interactions: [],
            directions: new Set()
          });
        }

        const connectionData = connectionMap.get(connectionKey)!;
        connectionData.callCount++;
        connectionData.interactions.push(interaction);
        
        // Agregar IDs de celdas
        if (interaction.celda_inicio) connectionData.cellIds.add(interaction.celda_inicio);
        if (interaction.celda_final) connectionData.cellIds.add(interaction.celda_final);
        
        // Determinar dirección del enlace
        if (originNumber === targetNumber) {
          connectionData.directions.add('outgoing');
        } else if (destinyNumber === targetNumber) {
          connectionData.directions.add('incoming');
        }
      }
    });

    // PASO 3: Generar nodos D3 con colores únicos
    const nodes: PhoneNode[] = [];
    const phoneNumbers = Array.from(phoneNumberMap.keys());
    
    phoneNumbers.forEach((phoneNumber, index) => {
      const data = phoneNumberMap.get(phoneNumber)!;
      const isTarget = phoneNumber === targetNumber;
      
      // Asignar color: rojo para target, colores únicos para participantes
      let nodeColor: string;
      if (isTarget) {
        nodeColor = '#ef4444'; // Rojo vibrante para objetivo
      } else {
        // Asignar color cíclico de la paleta para participantes
        const colorIndex = (index - (phoneNumbers.indexOf(targetNumber) >= 0 ? 1 : 0)) % PARTICIPANT_COLORS.length;
        nodeColor = PARTICIPANT_COLORS[colorIndex];
      }

      nodes.push({
        id: phoneNumber,
        label: phoneNumber.slice(-4), // Mostrar últimos 4 dígitos por defecto
        avatar: 'default', // Avatar por defecto, personalizable en FASE 3
        color: nodeColor,
        isTarget: isTarget,
        stats: {
          incoming: data.incoming,
          outgoing: data.outgoing,
          totalDuration: data.totalDuration,
          lastContact: data.lastContact
        },
        // Posición inicial básica (será mejorada por simulación D3)
        x: undefined,
        y: undefined,
        fx: null,
        fy: null
      });
    });

    // PASO 4: Generar enlaces D3
    const links: PhoneLink[] = [];
    
    connectionMap.forEach((connectionData, connectionKey) => {
      // Determinar direccionalidad del enlace
      let direction: 'incoming' | 'outgoing' | 'bidirectional';
      if (connectionData.directions.size === 2) {
        direction = 'bidirectional';
      } else if (connectionData.directions.has('incoming')) {
        direction = 'incoming';
      } else {
        direction = 'outgoing';
      }

      // Calcular strength basado en número de llamadas (1-5 scale)
      const strength = Math.min(Math.max(Math.ceil(connectionData.callCount / 2), 1), 5);

      links.push({
        source: connectionData.source, // D3 lo convertirá a objeto PhoneNode
        target: connectionData.target, // D3 lo convertirá a objeto PhoneNode
        cellIds: Array.from(connectionData.cellIds),
        callCount: connectionData.callCount,
        direction: direction,
        strength: strength,
        color: LINK_COLORS[direction]
      });
    });

    const result = { nodes, links };
    
    console.log('✅ useDataTransformer - Transformación completada:', {
      nodesGenerated: nodes.length,
      linksGenerated: links.length,
      targetNodeExists: nodes.some(n => n.isTarget),
      nodesSample: nodes.slice(0, 3).map(n => ({
        id: n.id,
        isTarget: n.isTarget,
        color: n.color,
        stats: n.stats
      })),
      linksSample: links.slice(0, 3).map(l => ({
        source: typeof l.source === 'string' ? l.source : l.source.id,
        target: typeof l.target === 'string' ? l.target : l.target.id,
        direction: l.direction,
        cellIds: l.cellIds
      }))
    });

    return result;
  }, [interactions, targetNumber]);
};

export default useDataTransformer;