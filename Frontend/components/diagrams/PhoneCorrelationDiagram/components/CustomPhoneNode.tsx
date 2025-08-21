/**
 * Componente Custom Phone Node para React Flow
 * Nodo personalizado con avatar SVG circular y badge de número telefónico
 * Actualizado: 2025-08-20 por Boris - Implementación React Flow
 */

import React, { memo, useCallback, useState, useEffect } from 'react';
import { Handle, Position } from '@xyflow/react';
import { CustomPhoneNodeProps } from '../types/reactflow.types';

// Import estático del avatar SVG para garantizar path correcto en Vite
import avatarMaleUrl from '/images/avatar/avatarMale.svg?url';

/**
 * Componente de nodo personalizado para números telefónicos
 * Estructura: Avatar circular (40px) + Badge número debajo
 */
const CustomPhoneNode: React.FC<CustomPhoneNodeProps> = memo(({ 
  data,
  selected
}) => {
  const [avatarContent, setAvatarContent] = useState<string | null>(null);
  const [isHovered, setIsHovered] = useState(false);

  // Cargar avatar SVG de forma asíncrona con path correcto
  useEffect(() => {
    const loadAvatar = async () => {
      try {
        // Usar import estático para garantizar path correcto en Vite
        const response = await fetch(avatarMaleUrl);
        if (response.ok) {
          const svgText = await response.text();
          setAvatarContent(svgText);
          console.log('✅ Avatar SVG cargado correctamente:', avatarMaleUrl);
        } else {
          console.warn('⚠️ Error HTTP al cargar avatar:', response.status, response.statusText);
        }
      } catch (error) {
        console.warn('❌ Error de red al cargar avatar:', error);
        console.log('🔄 Intentando path fallback...');
        
        // Fallback: intentar path relativo
        try {
          const fallbackResponse = await fetch('./images/avatar/avatarMale.svg');
          if (fallbackResponse.ok) {
            const svgText = await fallbackResponse.text();
            setAvatarContent(svgText);
            console.log('✅ Avatar SVG cargado con fallback path');
          }
        } catch (fallbackError) {
          console.warn('❌ Fallback también falló, usando emoji:', fallbackError);
        }
      }
    };

    loadAvatar();
  }, []);

  // Handlers para interacciones
  const handleMouseEnter = useCallback(() => {
    setIsHovered(true);
  }, []);

  const handleMouseLeave = useCallback(() => {
    setIsHovered(false);
  }, []);

  // Calcular estilos dinámicos
  const nodeSize = data.isTarget ? 45 : 35; // Radio del nodo
  const scale = isHovered ? 1.1 : 1;
  
  // Determinar color del borde basado en estado
  const getBorderColor = () => {
    if (selected) return '#fbbf24'; // Amarillo dorado para seleccionado
    return '#ffffff'; // Blanco por defecto
  };

  const getBorderWidth = () => {
    if (selected) return 4;
    if (data.isTarget) return 3;
    return 2;
  };

  // Formatear número telefónico para mostrar
  const formatPhoneNumber = (number: string) => {
    const cleaned = number.replace(/\D/g, '');
    if (cleaned.length <= 10) return cleaned;
    return `...${cleaned.slice(-4)}`;
  };

  return (
    <div 
      className="relative group"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      style={{ 
        transform: `scale(${scale})`,
        transition: 'transform 0.2s ease-in-out'
      }}
    >
      {/* Handles para conexiones (invisibles pero funcionales) */}
      <Handle
        type="target"
        position={Position.Top}
        className="opacity-0"
        isConnectable={false}
      />
      <Handle
        type="source"  
        position={Position.Bottom}
        className="opacity-0"
        isConnectable={false}
      />

      {/* Contenedor principal del nodo */}
      <div className="flex flex-col items-center">
        
        {/* Avatar circular con SVG */}
        <div 
          className="relative rounded-full flex items-center justify-center overflow-hidden"
          style={{
            width: `${nodeSize * 2}px`,
            height: `${nodeSize * 2}px`,
            backgroundColor: data.color,
            border: `${getBorderWidth()}px solid ${getBorderColor()}`,
            boxShadow: selected 
              ? '0 0 20px rgba(251, 191, 36, 0.6)' 
              : isHovered 
                ? `0 0 15px ${data.color}50`
                : '0 4px 8px rgba(0, 0, 0, 0.3)'
          }}
        >
          {/* Avatar SVG */}
          {avatarContent ? (
            <div 
              className="w-full h-full flex items-center justify-center"
              dangerouslySetInnerHTML={{ __html: avatarContent }}
              style={{
                // Preservar colores originales del SVG (tonos piel, cabello, etc.)
                // Remover filter que hacía todo blanco: brightness(0) invert(1)
                transform: 'scale(0.85)', // Ajustar tamaño para mejor fit circular
              }}
            />
          ) : (
            // Fallback si no carga el SVG
            <div 
              className="text-white text-xl font-bold"
              style={{ fontSize: `${nodeSize * 0.6}px` }}
            >
              👤
            </div>
          )}

          {/* Indicador de nodo objetivo */}
          {data.isTarget && (
            <div className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center">
              <span className="text-white text-xs font-bold">🎯</span>
            </div>
          )}
        </div>

        {/* Badge con número telefónico */}
        <div 
          className="mt-2 px-2 py-1 rounded-lg text-white text-xs font-mono"
          style={{
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            border: '1px solid rgba(255, 255, 255, 0.3)',
            backdropFilter: 'blur(4px)',
            minWidth: '60px',
            textAlign: 'center'
          }}
        >
          <div className="flex items-center justify-center gap-1">
            <span>📱</span>
            <span>{formatPhoneNumber(data.phoneNumber)}</span>
          </div>
        </div>

        {/* Stats hover tooltip */}
        {isHovered && (
          <div 
            className="absolute top-full mt-2 left-1/2 transform -translate-x-1/2 z-50 
                       bg-gray-900 text-white text-xs rounded-lg p-2 shadow-lg min-w-max
                       border border-gray-600"
            style={{ pointerEvents: 'none' }}
          >
            <div className="font-bold mb-1">{data.phoneNumber}</div>
            <div className="space-y-1">
              <div className="flex justify-between gap-3">
                <span className="text-green-400">📥 Entrantes:</span>
                <span>{data.stats.incoming}</span>
              </div>
              <div className="flex justify-between gap-3">
                <span className="text-red-400">📤 Salientes:</span>
                <span>{data.stats.outgoing}</span>
              </div>
              <div className="flex justify-between gap-3">
                <span className="text-blue-400">⏱️ Duración:</span>
                <span>{Math.round(data.stats.totalDuration / 60)}m</span>
              </div>
              <div className="flex justify-between gap-3">
                <span className="text-gray-400">📅 Último:</span>
                <span>{data.stats.lastContact.toLocaleDateString()}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
});

CustomPhoneNode.displayName = 'CustomPhoneNode';

export default CustomPhoneNode;