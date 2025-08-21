/**
 * Componente Custom Phone Edge para React Flow - 4 OPCIONES DE ETIQUETAS UX
 * Enlace personalizado con curvas bezier, flechas direccionales y etiquetas de celda
 * 
 * ACTUALIZACIONES:
 * - 2025-08-20 por Boris: Implementación React Flow inicial
 * - 2025-08-20 por Boris: Optimización de flechas direccionales adaptativas
 * - 2025-08-20 por Boris: Sistema anti-superposición HASH DETERMINÍSTICO
 * - 2025-08-20 por Boris: IMPLEMENTACIÓN 4 OPCIONES UX ETIQUETAS:
 *   * OPCIÓN 1: Posicionamiento fijo en esquinas predefinidas
 *   * OPCIÓN 2: Etiquetas en línea con offset perpendicular
 *   * OPCIÓN 3: Sistema tooltip interactivo (hover-only)
 *   * OPCIÓN 4: Stack vertical lateral con highlighting bidireccional
 */

import React, { memo, useMemo, useState, useCallback } from 'react';
import { BaseEdge, EdgeLabelRenderer, getBezierPath } from '@xyflow/react';
import { CustomPhoneEdgeProps, LabelPositioningStrategy } from '../types/reactflow.types';

/**
 * =============================================================================
 * OPCIÓN 1: POSICIONAMIENTO FIJO EN ESQUINAS PREDEFINIDAS
 * Posiciones fijas alrededor del viewport para distribución uniforme
 * =============================================================================
 */

const FIXED_CORNER_POSITIONS = [
  { x: -80, y: -60 },   // top-left
  { x: 80, y: -60 },    // top-right  
  { x: -80, y: 60 },    // bottom-left
  { x: 80, y: 60 },     // bottom-right
  { x: 0, y: -80 },     // top-center
  { x: 0, y: 80 },      // bottom-center
  { x: -100, y: 0 },    // left-center
  { x: 100, y: 0 },     // right-center
  { x: -60, y: -30 },   // top-left-inner
  { x: 60, y: -30 },    // top-right-inner
  { x: -60, y: 30 },    // bottom-left-inner
  { x: 60, y: 30 }      // bottom-right-inner
];

/**
 * Función hash simple para distribución uniforme
 */
const simpleHash = (str: string): number => {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash);
};

/**
 * OPCIÓN 1: Algoritmo de posicionamiento en esquinas fijas
 */
const getFixedCornerPosition = (
  baseX: number,
  baseY: number,
  edgeId: string,
  sourceId: string,
  targetId: string
): { x: number; y: number } => {
  const hashInput = `${edgeId}-${sourceId}-${targetId}`;
  const edgeHash = simpleHash(hashInput);
  const cornerIndex = edgeHash % FIXED_CORNER_POSITIONS.length;
  const cornerOffset = FIXED_CORNER_POSITIONS[cornerIndex];
  
  return {
    x: baseX + cornerOffset.x,
    y: baseY + cornerOffset.y
  };
};

/**
 * =============================================================================
 * OPCIÓN 2: ETIQUETAS EN LÍNEA CON OFFSET PERPENDICULAR
 * Posicionar a lo largo de la curva bezier con offset perpendicular
 * =============================================================================
 */

/**
 * Calcular posición a lo largo de la curva bezier
 */
const getBezierPointAtT = (
  sourceX: number,
  sourceY: number,
  targetX: number,
  targetY: number,
  t: number = 0.5
): { x: number; y: number; tangentX: number; tangentY: number } => {
  // Control points para curva bezier cúbica
  const cp1x = sourceX;
  const cp1y = sourceY + (targetY - sourceY) * 0.5;
  const cp2x = targetX;
  const cp2y = targetY - (targetY - sourceY) * 0.5;
  
  // Posición en curva
  const x = Math.pow(1-t, 3) * sourceX + 
            3 * Math.pow(1-t, 2) * t * cp1x + 
            3 * (1-t) * Math.pow(t, 2) * cp2x + 
            Math.pow(t, 3) * targetX;
            
  const y = Math.pow(1-t, 3) * sourceY + 
            3 * Math.pow(1-t, 2) * t * cp1y + 
            3 * (1-t) * Math.pow(t, 2) * cp2y + 
            Math.pow(t, 3) * targetY;
  
  // Vector tangente para calcular perpendicular
  const tangentX = 3 * Math.pow(1-t, 2) * (cp1x - sourceX) + 
                   6 * (1-t) * t * (cp2x - cp1x) + 
                   3 * Math.pow(t, 2) * (targetX - cp2x);
                   
  const tangentY = 3 * Math.pow(1-t, 2) * (cp1y - sourceY) + 
                   6 * (1-t) * t * (cp2y - cp1y) + 
                   3 * Math.pow(t, 2) * (targetY - cp2y);
  
  return { x, y, tangentX, tangentY };
};

/**
 * OPCIÓN 2: Algoritmo de posicionamiento en línea con offset
 */
const getInlineOffsetPosition = (
  sourceX: number,
  sourceY: number,
  targetX: number,
  targetY: number,
  edgeId: string,
  sourceId: string,
  targetId: string
): { x: number; y: number } => {
  const hashInput = `${edgeId}-${sourceId}-${targetId}`;
  const edgeHash = simpleHash(hashInput);
  
  // Posición a lo largo de la curva (25%, 50%, 75%)
  const tPositions = [0.25, 0.5, 0.75];
  const t = tPositions[edgeHash % tPositions.length];
  
  const { x, y, tangentX, tangentY } = getBezierPointAtT(sourceX, sourceY, targetX, targetY, t);
  
  // Vector perpendicular normalizado
  const tangentLength = Math.sqrt(tangentX * tangentX + tangentY * tangentY);
  const perpX = -tangentY / tangentLength;
  const perpY = tangentX / tangentLength;
  
  // Offset perpendicular (alternar lado basado en hash)
  const offsetDistance = 40 + (edgeHash % 20); // 40-60px
  const side = (edgeHash % 2) === 0 ? 1 : -1;
  
  return {
    x: x + perpX * offsetDistance * side,
    y: y + perpY * offsetDistance * side
  };
};

/**
 * =============================================================================
 * OPCIÓN 3: SISTEMA TOOLTIP INTERACTIVO (HOVER-ONLY)
 * Solo visible on-hover con tooltip dinámico
 * =============================================================================
 */

interface TooltipHoverProps {
  edgeId: string;
  labelText: string;
  x: number;
  y: number;
  isVisible: boolean;
  onMouseEnter: () => void;
  onMouseLeave: () => void;
}

const TooltipHover: React.FC<TooltipHoverProps> = ({
  edgeId,
  labelText,
  x,
  y,
  isVisible,
  onMouseEnter,
  onMouseLeave
}) => (
  <>
    {/* Indicador visual (punto) en centro de línea */}
    <div
      style={{
        position: 'absolute',
        transform: `translate(-50%, -50%) translate(${x}px, ${y}px)`,
        pointerEvents: 'all',
      }}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      className="react-flow__edge-indicator"
    >
      <div 
        className="w-2 h-2 rounded-full bg-white border border-gray-400 cursor-pointer hover:scale-125 transition-transform"
        style={{
          boxShadow: '0 2px 4px rgba(0,0,0,0.3)'
        }}
      />
    </div>

    {/* Tooltip dinámico */}
    {isVisible && (
      <div
        style={{
          position: 'absolute',
          transform: `translate(-50%, -50%) translate(${x}px, ${y - 40}px)`,
          pointerEvents: 'none',
          zIndex: 1000
        }}
        className="react-flow__edge-tooltip"
      >
        <div 
          className="px-3 py-2 rounded-lg text-xs font-mono text-white bg-black border border-white/30"
          style={{
            backdropFilter: 'blur(8px)',
            backgroundColor: 'rgba(0, 0, 0, 0.9)',
            fontSize: '11px',
            minWidth: 'max-content',
            boxShadow: '0 4px 12px rgba(0,0,0,0.5)'
          }}
        >
          {labelText}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-black" />
        </div>
      </div>
    )}
  </>
);

/**
 * =============================================================================
 * OPCIÓN 4: STACK VERTICAL LATERAL - PLACEHOLDER
 * Esta opción será implementada a nivel del diagrama principal
 * ya que requiere un panel lateral independiente
 * =============================================================================
 */

/**
 * =============================================================================
 * SISTEMA DE EDICIÓN DE RUTAS - BORIS OPCIÓN B
 * Puntos de control arrastrables para edición visual de curvas bezier
 * =============================================================================
 */

interface ControlPointProps {
  x: number;
  y: number;
  color: string;
  isActive: boolean;
  onMouseDown: (event: React.MouseEvent) => void;
}

/**
 * Componente de Punto de Control Arrastrable
 */
const ControlPoint: React.FC<ControlPointProps> = ({
  x,
  y,
  color,
  isActive,
  onMouseDown
}) => (
  <div
    style={{
      position: 'absolute',
      transform: `translate(-50%, -50%) translate(${x}px, ${y}px)`,
      pointerEvents: 'all',
      cursor: 'grab',
      zIndex: 1000
    }}
    onMouseDown={onMouseDown}
    className="react-flow__control-point"
  >
    <div 
      className={`w-4 h-4 rounded-full border-2 transition-all duration-200 ${
        isActive ? 'border-white shadow-lg scale-125' : 'border-gray-400 hover:border-white hover:scale-110'
      }`}
      style={{
        backgroundColor: isActive ? color : 'white',
        boxShadow: isActive 
          ? `0 0 12px ${color}80, 0 4px 8px rgba(0,0,0,0.6)` 
          : '0 2px 4px rgba(0,0,0,0.3)',
        backdropFilter: 'blur(2px)'
      }}
    />
    
    {/* Etiqueta del punto de control */}
    <div
      className={`absolute top-full mt-1 left-1/2 transform -translate-x-1/2 text-xs font-mono px-1 rounded transition-opacity ${
        isActive ? 'opacity-100' : 'opacity-0 hover:opacity-100'
      }`}
      style={{
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        color: 'white',
        fontSize: '9px',
        pointerEvents: 'none'
      }}
    >
      CP
    </div>
  </div>
);

/**
 * Calcular curva bezier custom o usar defaults de React Flow
 */
const getCustomBezierPath = (
  sourceX: number,
  sourceY: number,
  targetX: number,
  targetY: number,
  customControlPoints?: {
    cp1x: number; 
    cp1y: number;
    cp2x: number; 
    cp2y: number;
  }
): string => {
  if (customControlPoints) {
    // Usar puntos de control personalizados
    return `M${sourceX},${sourceY} C${customControlPoints.cp1x},${customControlPoints.cp1y} ${customControlPoints.cp2x},${customControlPoints.cp2y} ${targetX},${targetY}`;
  } else {
    // Usar curva bezier por defecto de React Flow
    const cp1x = sourceX;
    const cp1y = sourceY + (targetY - sourceY) * 0.5;
    const cp2x = targetX;
    const cp2y = targetY - (targetY - sourceY) * 0.5;
    
    return `M${sourceX},${sourceY} C${cp1x},${cp1y} ${cp2x},${cp2y} ${targetX},${targetY}`;
  }
};

/**
 * =============================================================================
 * COMPONENTE PRINCIPAL: CUSTOM PHONE EDGE CON 4 OPCIONES
 * =============================================================================
 */

const CustomPhoneEdge: React.FC<CustomPhoneEdgeProps> = memo(({
  id,
  source,
  target,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  selected,
  onControlPointsChange
}) => {
  // Estado para tooltip hover (OPCIÓN 3)
  const [showTooltip, setShowTooltip] = useState(false);
  
  // NUEVO: Estado para edición de rutas - Boris OPCIÓN B
  const [isDragging, setIsDragging] = useState(false);
  const [activeControlPoint, setActiveControlPoint] = useState<'cp1' | 'cp2' | null>(null);

  // NUEVO: Calcular puntos de control por defecto o usar custom - Boris OPCIÓN B
  const defaultControlPoints = useMemo(() => ({
    cp1x: sourceX,
    cp1y: sourceY + (targetY - sourceY) * 0.5,
    cp2x: targetX,
    cp2y: targetY - (targetY - sourceY) * 0.5
  }), [sourceX, sourceY, targetX, targetY]);

  const currentControlPoints = data.customControlPoints || defaultControlPoints;

  // Calcular path bezier (custom o por defecto)
  const edgePath = useMemo(() => {
    return getCustomBezierPath(sourceX, sourceY, targetX, targetY, data.customControlPoints);
  }, [sourceX, sourceY, targetX, targetY, data.customControlPoints]);

  // Posición de label usando React Flow original como fallback
  const [, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  // Determinar grosor basado en strength
  const strokeWidth = Math.max(2, Math.min(6, data.strength * 1.5));
  
  // Flecha RECTANGULAR más visible para investigadores
  const arrowSize = Math.min(Math.max(strokeWidth * 3, 12), 18);
  const arrowHeight = Math.round(arrowSize * 0.7);
  
  // Determinar opacidad basada en selección
  const opacity = selected ? 1.0 : 0.8;

  // Obtener primer ID de celda para mostrar (si existe)
  const primaryCellId = data.cellIds.length > 0 ? data.cellIds[0] : '';

  // Generar texto completo de la etiqueta
  const labelText = useMemo(() => {
    let text = primaryCellId;
    if (data.callCount > 1) {
      text += ` (${data.callCount}x)`;
    }
    return text;
  }, [primaryCellId, data.callCount]);

  // Obtener estrategia de posicionamiento (por defecto fixed-corners)
  const strategy: LabelPositioningStrategy = data.labelStrategy || 'fixed-corners';

  // Calcular posición de etiqueta según estrategia seleccionada
  const labelPosition = useMemo(() => {
    switch (strategy) {
      case 'fixed-corners':
        return getFixedCornerPosition(labelX, labelY, id, source, target);
      
      case 'inline-offset':
        return getInlineOffsetPosition(sourceX, sourceY, targetX, targetY, id, source, target);
      
      case 'tooltip-hover':
        return { x: labelX, y: labelY }; // Posición base para indicador
      
      case 'lateral-stack':
        return { x: 0, y: 0 }; // No renderizar etiqueta (panel lateral)
      
      default:
        return getFixedCornerPosition(labelX, labelY, id, source, target);
    }
  }, [strategy, labelX, labelY, sourceX, sourceY, targetX, targetY, id, source, target]);

  // Obtener icono según dirección
  const getDirectionIcon = () => {
    switch (data.direction) {
      case 'incoming': return '📥';
      case 'outgoing': return '📤';  
      case 'bidirectional': return '🔄';
      default: return '📱';
    }
  };

  // NUEVO: Handlers para arrastre de puntos de control - Boris OPCIÓN B
  const handleControlPointMouseDown = useCallback((controlPoint: 'cp1' | 'cp2') => (event: React.MouseEvent) => {
    event.stopPropagation();
    event.preventDefault();
    
    if (!data.isEditable || !onControlPointsChange) return;
    
    setActiveControlPoint(controlPoint);
    setIsDragging(true);
    
    const startCoords = {
      x: event.clientX,
      y: event.clientY
    };
    
    const handleMouseMove = (e: MouseEvent) => {
      if (!data.isEditable) return;
      
      // Calcular el delta del movimiento
      const deltaX = e.clientX - startCoords.x;
      const deltaY = e.clientY - startCoords.y;
      
      // Aplicar el delta a los puntos de control actuales
      const newControlPoints = { ...currentControlPoints };
      
      if (controlPoint === 'cp1') {
        newControlPoints.cp1x = currentControlPoints.cp1x + deltaX;
        newControlPoints.cp1y = currentControlPoints.cp1y + deltaY;
      } else {
        newControlPoints.cp2x = currentControlPoints.cp2x + deltaX;
        newControlPoints.cp2y = currentControlPoints.cp2y + deltaY;
      }
      
      // Validar que los endpoints no cambien (sourceX, sourceY, targetX, targetY preservados)
      // Los puntos de control pueden moverse libremente pero no afectan endpoints
      
      // Comunicar cambio al componente padre
      onControlPointsChange(id, newControlPoints);
      
      console.log(`✏️ Editando ${controlPoint}:`, newControlPoints);
    };
    
    const handleMouseUp = () => {
      setIsDragging(false);
      setActiveControlPoint(null);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      
      console.log('🎯 Finalizó edición de punto de control');
    };
    
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  }, [data.isEditable, onControlPointsChange, id, currentControlPoints]);

  // Generar ID único para el marker
  const markerId = `marker-${id}`;

  return (
    <>
      {/* Definición de marker para flecha profesional adaptativa */}
      <defs>
        <marker
          id={markerId}
          markerWidth={arrowSize}
          markerHeight={arrowHeight} 
          refX={arrowSize - 0.5}
          refY={arrowHeight / 2}
          orient="auto"
          markerUnits="userSpaceOnUse"
          viewBox={`0 0 ${arrowSize} ${arrowHeight}`}
        >
          {/* Flecha RECTANGULAR optimizada para investigadores */}
          <rect
            x="1"
            y={arrowHeight * 0.25}
            width={arrowSize - 2}
            height={arrowHeight * 0.5}
            fill={data.color}
            stroke="white"
            strokeWidth="1.5"
            opacity={opacity}
            rx="1"
            style={{
              filter: selected 
                ? `drop-shadow(0 0 5px ${data.color}) brightness(1.2)` 
                : 'drop-shadow(0 2px 4px rgba(0,0,0,0.4))'
            }}
          />
          {/* Punta de flecha rectangular */}
          <polygon
            points={`${arrowSize - 4},${arrowHeight * 0.1} ${arrowSize - 1},${arrowHeight / 2} ${arrowSize - 4},${arrowHeight * 0.9}`}
            fill={data.color}
            stroke="white"
            strokeWidth="1.5"
            opacity={opacity}
            style={{
              filter: selected 
                ? `drop-shadow(0 0 5px ${data.color}) brightness(1.2)` 
                : 'drop-shadow(0 2px 4px rgba(0,0,0,0.4))'
            }}
          />
        </marker>
      </defs>

      {/* Enlace bezier principal */}
      <BaseEdge
        id={id}
        path={edgePath}
        style={{
          stroke: data.color,
          strokeWidth: strokeWidth,
          strokeLinecap: 'round',
          strokeLinejoin: 'round',
          opacity: opacity,
          filter: selected 
            ? `drop-shadow(0 0 8px ${data.color}80)` 
            : 'drop-shadow(0 1px 2px rgba(0, 0, 0, 0.2))'
        }}
        markerEnd={`url(#${markerId})`}
      />

      {/* NUEVO: Puntos de Control Arrastrables - Solo en modo edición - Boris OPCIÓN B */}
      {data.isEditable && (
        <EdgeLabelRenderer>
          <ControlPoint
            x={currentControlPoints.cp1x}
            y={currentControlPoints.cp1y}
            color={data.color}
            isActive={activeControlPoint === 'cp1'}
            onMouseDown={handleControlPointMouseDown('cp1')}
          />
          <ControlPoint
            x={currentControlPoints.cp2x}
            y={currentControlPoints.cp2y}
            color={data.color}
            isActive={activeControlPoint === 'cp2'}
            onMouseDown={handleControlPointMouseDown('cp2')}
          />
        </EdgeLabelRenderer>
      )}

      {/* Renderizado condicional según estrategia de etiquetas */}
      {primaryCellId && strategy !== 'lateral-stack' && (
        <EdgeLabelRenderer>
          {/* OPCIÓN 1 y 2: Etiquetas estáticas */}
          {(strategy === 'fixed-corners' || strategy === 'inline-offset') && (
            <div
              style={{
                position: 'absolute',
                transform: `translate(-50%, -50%) translate(${labelPosition.x}px, ${labelPosition.y}px)`,
                pointerEvents: 'all',
              }}
              className="react-flow__edge-label"
            >
              <div 
                className="px-2 py-1 rounded text-xs font-mono text-white flex items-center gap-1"
                style={{
                  backgroundColor: 'rgba(0, 0, 0, 0.8)',
                  border: '1px solid rgba(255, 255, 255, 0.3)',
                  backdropFilter: 'blur(4px)',
                  fontSize: '10px',
                  minWidth: 'max-content',
                  transition: 'all 0.2s ease-in-out'
                }}
              >
                <span className="text-xs">{getDirectionIcon()}</span>
                <span>{primaryCellId}</span>
                {data.callCount > 1 && (
                  <span className="text-gray-300 ml-1">
                    ({data.callCount}x)
                  </span>
                )}
              </div>
            </div>
          )}

          {/* OPCIÓN 3: Sistema tooltip interactivo */}
          {strategy === 'tooltip-hover' && (
            <TooltipHover
              edgeId={id}
              labelText={`${getDirectionIcon()} ${labelText}`}
              x={labelPosition.x}
              y={labelPosition.y}
              isVisible={showTooltip}
              onMouseEnter={() => setShowTooltip(true)}
              onMouseLeave={() => setShowTooltip(false)}
            />
          )}
        </EdgeLabelRenderer>
      )}
    </>
  );
});

CustomPhoneEdge.displayName = 'CustomPhoneEdge';

export default CustomPhoneEdge;