/**
 * Tipos TypeScript para el Diagrama de Correlación Telefónica D3.js
 * FASE 1 - Definiciones base para visualización D3
 * Actualizado: 2025-08-20 por Boris - Reemplazo de funcionalidad G6
 */

import { SimulationNodeDatum, SimulationLinkDatum } from 'd3';

// Interface principal para nodos del diagrama telefónico
export interface PhoneNode extends SimulationNodeDatum {
  id: string;                      // Número telefónico
  label: string;                   // Nombre personalizable
  avatar: string;                  // ID del avatar seleccionado
  color: string;                   // Color del nodo
  isTarget: boolean;               // Si es el número objetivo (nodo central)
  stats: {
    incoming: number;              // Llamadas entrantes
    outgoing: number;              // Llamadas salientes
    totalDuration: number;         // Duración total en segundos
    lastContact: Date;             // Última interacción
  };
  // Propiedades D3 heredadas de SimulationNodeDatum
  x?: number; 
  y?: number;        
  fx?: number; 
  fy?: number;      // Posiciones fijas para drag & drop
  vx?: number; 
  vy?: number;      // Velocidades de simulación
}

// Interface para enlaces entre nodos telefónicos
export interface PhoneLink extends SimulationLinkDatum<PhoneNode> {
  source: string | PhoneNode;       // ID nodo origen (D3 lo convierte a objeto)
  target: string | PhoneNode;       // ID nodo destino (D3 lo convierte a objeto)
  cellIds: string[];               // IDs de celdas ["56124", "53591"]
  callCount: number;               // Número de llamadas
  direction: 'incoming' | 'outgoing' | 'bidirectional';
  strength: number;                // Grosor del enlace (1-5)
  color: string;                   // Color basado en direccionalidad
}

// Interface para datos de entrada desde el modal de correlación
export interface UnifiedInteraction {
  // Campos comunes para ambos tipos
  numero_objetivo: string;
  numero_secundario: string;        // Receptor para llamadas, vacío para datos 
  fecha_hora: string;
  duracion_segundos: number;
  operador: string;
  celda_inicio: string;
  celda_final: string;              // Celda destino para llamadas, vacío para datos
  // Campo HUNTER unificado del backend
  punto_hunter?: string;
  lat_hunter?: number;
  lon_hunter?: number;
  // Campos específicos para datos móviles
  trafico_total_bytes?: number;
  tipo_conexion?: string;
  // Tipo de interacción para diferenciación visual
  tipo_interaccion?: 'llamada' | 'datos';
  // Campos direccionales del backend (CORRECCIÓN BORIS)
  hunter_source?: string;           // 'origen_direccional' | 'destino_direccional' | 'origen_fallback' | 'destino_fallback' | 'sin_ubicacion'
  precision_ubicacion?: string;     // 'ALTA' | 'MEDIA' | 'SIN_DATOS'
}

// Props para el componente principal del diagrama
export interface PhoneCorrelationDiagramProps {
  isOpen: boolean;
  onClose: () => void;
  interactions: UnifiedInteraction[];
  targetNumber: string;
}

// Configuración del layout D3
export interface LayoutConfig {
  type: 'force' | 'circular' | 'grid';
  strength: number;
  distance: number;
  iterations: number;
}

// Configuración visual del diagrama
export interface DiagramConfig {
  width: number;
  height: number;
  nodeRadius: {
    target: number;                 // Radio del nodo objetivo
    regular: number;                // Radio de nodos regulares
  };
  linkWidth: {
    base: number;                   // Grosor base de enlaces
    strong: number;                 // Grosor de enlaces fuertes
  };
  colors: {
    target: string;                 // Color del nodo objetivo
    participants: string[];         // Array de colores para participantes
    links: {
      incoming: string;             // Color enlaces entrantes
      outgoing: string;             // Color enlaces salientes
      bidirectional: string;        // Color enlaces bidireccionales
    };
  };
}

// Datos transformados listos para D3
export interface DiagramData {
  nodes: PhoneNode[];
  links: PhoneLink[];
}

// Estado de filtros para el diagrama
export interface DiagramFilters {
  correlationLevels: string[];
  operators: string[];
  interactionTypes: ('llamada' | 'datos' | 'mixed')[];
  minInteractions: number;
  showLabels: boolean;
  showDirections: boolean;
}