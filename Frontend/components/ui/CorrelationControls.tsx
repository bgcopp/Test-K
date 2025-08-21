/**
 * CorrelationControls - Panel lateral de controles para PhoneCorrelationViewer
 * Especificaciones confirmadas por Boris:
 * - Controles de zoom: in, out, reset, fit-to-screen
 * - Filtros: correlación mínima (slider), mostrar/ocultar IDs celda, nodos aislados
 * - Export: PNG, SVG, JSON con metadatos
 * - Información de nodos/edges en tiempo real
 * - Diseño coherente con tema KRONOS
 * 
 * Creado: 2025-08-21 por Claude bajo supervisión de Boris
 */

import React from 'react';

interface CorrelationControlsProps {
  filters: {
    minCorrelation: number;
    showIsolatedNodes: boolean;
    showCellIds: boolean;
    labelStrategy: 'always' | 'smart' | 'minimal' | 'off';
  };
  onFilterChange: (filters: CorrelationControlsProps['filters']) => void;
  diagramStats: {
    totalNodes: number;
    totalEdges: number;
    targetExists: boolean;
    connectedNodes: number;
  };
  onZoomIn: () => void;
  onZoomOut: () => void;
  onZoomReset: () => void;
  onFitToScreen: () => void;
  onExportPNG: () => void;
  onExportSVG: () => void;
  onExportJSON: () => void;
}

const CorrelationControls: React.FC<CorrelationControlsProps> = ({
  filters,
  onFilterChange,
  diagramStats,
  onZoomIn,
  onZoomOut,
  onZoomReset,
  onFitToScreen,
  onExportPNG,
  onExportSVG,
  onExportJSON
}) => {
  
  const handleFilterChange = (key: keyof typeof filters, value: any) => {
    onFilterChange({
      ...filters,
      [key]: value
    });
  };

  return (
    <div className="h-full flex flex-col p-4 space-y-6 overflow-y-auto">
      
      {/* Sección de Controles de Zoom */}
      <div>
        <h3 className="text-white font-medium mb-3 flex items-center gap-2">
          🔍 Controles de Zoom
        </h3>
        
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={onZoomIn}
            className="flex items-center justify-center gap-2 p-2 bg-secondary-light hover:bg-gray-600 text-white rounded-lg transition-colors text-sm"
            title="Acercar (Zoom In)"
          >
            <span>🔍</span>
            <span>+</span>
          </button>
          
          <button
            onClick={onZoomOut}
            className="flex items-center justify-center gap-2 p-2 bg-secondary-light hover:bg-gray-600 text-white rounded-lg transition-colors text-sm"
            title="Alejar (Zoom Out)"
          >
            <span>🔍</span>
            <span>-</span>
          </button>
          
          <button
            onClick={onZoomReset}
            className="flex items-center justify-center gap-2 p-2 bg-secondary-light hover:bg-gray-600 text-white rounded-lg transition-colors text-sm"
            title="Restablecer Zoom"
          >
            <span>🎯</span>
            <span>1:1</span>
          </button>
          
          <button
            onClick={onFitToScreen}
            className="flex items-center justify-center gap-2 p-2 bg-primary hover:bg-primary-light text-white rounded-lg transition-colors text-sm"
            title="Ajustar a Pantalla"
          >
            <span>📐</span>
            <span>Fit</span>
          </button>
        </div>
      </div>

      {/* Sección de Filtros */}
      <div>
        <h3 className="text-white font-medium mb-3 flex items-center gap-2">
          🎛️ Filtros Avanzados
        </h3>
        
        {/* Correlación mínima */}
        <div className="mb-4">
          <label className="block text-sm text-gray-300 mb-2">
            Correlación mínima: <span className="text-cyan-300 font-bold">{filters.minCorrelation}</span> interacciones
          </label>
          <input
            type="range"
            min="0"
            max="20"
            value={filters.minCorrelation}
            onChange={(e) => handleFilterChange('minCorrelation', parseInt(e.target.value))}
            className="w-full h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer slider-thumb"
          />
          <div className="flex justify-between text-xs text-gray-400 mt-1">
            <span>0</span>
            <span>10</span>
            <span>20+</span>
          </div>
        </div>

        {/* Estrategia de etiquetas de celda */}
        <div className="mb-4">
          <label className="block text-sm text-gray-300 mb-2">
            Etiquetas de celda
          </label>
          <select
            value={filters.labelStrategy}
            onChange={(e) => handleFilterChange('labelStrategy', e.target.value)}
            className="w-full bg-secondary-light text-white text-sm rounded-lg px-3 py-2 border border-gray-600 focus:border-cyan-400 focus:outline-none"
          >
            <option value="always">📋 Siempre visible</option>
            <option value="smart">🧠 Inteligente (recomendado)</option>
            <option value="minimal">📌 Mínimo necesario</option>
            <option value="off">🚫 Ocultar todas</option>
          </select>
          
          {/* Descripción de la estrategia */}
          <div className="text-xs text-gray-400 mt-1">
            {filters.labelStrategy === 'always' && 'Muestra todas las etiquetas de celda'}
            {filters.labelStrategy === 'smart' && 'Muestra etiquetas según relevancia y espacio'}
            {filters.labelStrategy === 'minimal' && 'Solo etiquetas del nodo objetivo'}
            {filters.labelStrategy === 'off' && 'Oculta todas las etiquetas de celda'}
          </div>
        </div>

        {/* Checkboxes de filtros */}
        <div className="space-y-3">
          <label className="flex items-center space-x-3 text-sm text-gray-300 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.showCellIds}
              onChange={(e) => handleFilterChange('showCellIds', e.target.checked)}
              className="form-checkbox h-4 w-4 text-cyan-500 bg-secondary-light border-gray-600 rounded focus:ring-cyan-400 focus:ring-2"
            />
            <span>📡 Mostrar IDs de celda</span>
          </label>
          
          <label className="flex items-center space-x-3 text-sm text-gray-300 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.showIsolatedNodes}
              onChange={(e) => handleFilterChange('showIsolatedNodes', e.target.checked)}
              className="form-checkbox h-4 w-4 text-cyan-500 bg-secondary-light border-gray-600 rounded focus:ring-cyan-400 focus:ring-2"
            />
            <span>🏝️ Mostrar nodos aislados</span>
          </label>
        </div>
      </div>

      {/* Sección de Información del Diagrama */}
      <div>
        <h3 className="text-white font-medium mb-3 flex items-center gap-2">
          📊 Información del Diagrama
        </h3>
        
        <div className="bg-secondary-light rounded-lg p-3 space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-300">Nodos totales:</span>
            <span className="text-white font-mono">{diagramStats.totalNodes}</span>
          </div>
          
          <div className="flex justify-between text-sm">
            <span className="text-gray-300">Conexiones:</span>
            <span className="text-white font-mono">{diagramStats.totalEdges}</span>
          </div>
          
          <div className="flex justify-between text-sm">
            <span className="text-gray-300">Nodos conectados:</span>
            <span className="text-white font-mono">{diagramStats.connectedNodes}</span>
          </div>
          
          <div className="flex justify-between text-sm">
            <span className="text-gray-300">Objetivo presente:</span>
            <span className={`font-bold ${diagramStats.targetExists ? 'text-green-400' : 'text-red-400'}`}>
              {diagramStats.targetExists ? '✅ Sí' : '❌ No'}
            </span>
          </div>
        </div>

        {/* Leyenda de colores */}
        <div className="mt-3">
          <div className="text-sm text-gray-300 mb-2">Leyenda:</div>
          <div className="space-y-2 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-red-500 rounded-full"></div>
              <span className="text-gray-300">Nodo objetivo</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-gray-500 rounded-full"></div>
              <span className="text-gray-300">Participantes</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-0.5 bg-green-500"></div>
              <span className="text-gray-300">Llamadas entrantes</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-0.5 bg-red-500"></div>
              <span className="text-gray-300">Llamadas salientes</span>
            </div>
          </div>
        </div>
      </div>

      {/* Sección de Exportación */}
      <div>
        <h3 className="text-white font-medium mb-3 flex items-center gap-2">
          💾 Exportar Diagrama
        </h3>
        
        <div className="space-y-2">
          <button
            onClick={onExportPNG}
            className="w-full flex items-center justify-center gap-2 p-3 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors text-sm font-medium"
            title="Exportar como imagen PNG"
          >
            <span>🖼️</span>
            <span>Exportar PNG</span>
          </button>
          
          <button
            onClick={onExportSVG}
            className="w-full flex items-center justify-center gap-2 p-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm font-medium"
            title="Exportar como gráfico vectorial SVG"
          >
            <span>📄</span>
            <span>Exportar SVG</span>
          </button>
          
          <button
            onClick={onExportJSON}
            className="w-full flex items-center justify-center gap-2 p-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors text-sm font-medium"
            title="Exportar datos y configuración como JSON"
          >
            <span>📊</span>
            <span>Exportar JSON</span>
          </button>
        </div>
        
        <div className="text-xs text-gray-400 mt-2">
          • PNG: Imagen del diagrama actual<br/>
          • SVG: Gráfico vectorial escalable<br/>
          • JSON: Datos y configuración completa
        </div>
      </div>

      {/* Sección de Ayuda */}
      <div>
        <h3 className="text-white font-medium mb-3 flex items-center gap-2">
          ❓ Ayuda Rápida
        </h3>
        
        <div className="text-xs text-gray-400 space-y-1">
          <div>• <strong>Arrastrar nodos:</strong> Reposicionar manualmente</div>
          <div>• <strong>Scroll:</strong> Hacer zoom in/out</div>
          <div>• <strong>Click nodo:</strong> Ver información detallada</div>
          <div>• <strong>Click enlace:</strong> Ver comunicaciones</div>
          <div>• <strong>ESC:</strong> Cerrar diagrama</div>
        </div>
      </div>

    </div>
  );
};

export default CorrelationControls;