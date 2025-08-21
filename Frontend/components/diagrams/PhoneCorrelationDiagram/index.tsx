/**
 * Exportación principal del Diagrama de Correlación Telefónica D3.js
 * FASE 1 - Punto de entrada único para el componente
 * Actualizado: 2025-08-20 por Boris - Reemplazo de funcionalidad G6
 */

// Exportación del componente principal
export { default as PhoneCorrelationDiagram } from './PhoneCorrelationDiagram';

// Exportación de tipos para uso externo
export type {
  PhoneCorrelationDiagramProps,
  UnifiedInteraction,
  PhoneNode,
  PhoneLink,
  DiagramData
} from './types/diagram.types';

// Exportación del hook de transformación de datos
export { useDataTransformer } from './hooks/useDataTransformer';

// Re-exportación por defecto del componente principal
export { default } from './PhoneCorrelationDiagram';