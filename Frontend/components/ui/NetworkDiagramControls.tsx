import React, { useState } from 'react';
import { ICONS } from '../../constants';

// Interfaces para los controles del diagrama
interface NetworkNode {
    id: string;
    number: string;
    name?: string;
    operator: string;
    correlationLevel: 'target' | 'high' | 'medium' | 'low' | 'indirect';
    interactionCount: number;
    isTarget: boolean;
}

interface NetworkEdge {
    id: string;
    source: string;
    target: string;
    cellIds: string[];
    isDirectional: boolean;
    interactionType: 'llamada' | 'datos' | 'mixed';
}

interface DiagramFilters {
    correlationLevels: string[];
    operators: string[];
    interactionTypes: string[];
    minInteractions: number;
    showLabels: boolean;
    showDirections: boolean;
}

interface LayoutConfig {
    type: 'force' | 'circular' | 'grid' | 'hierarchy';
    strength: number;
    distance: number;
    iterations: number;
}

interface NetworkDiagramControlsProps {
    nodes: NetworkNode[];
    edges: NetworkEdge[];
    onLayoutChange: (layout: LayoutConfig) => void;
    onFilterChange: (filters: DiagramFilters) => void;
    onExport: (type: 'png' | 'svg' | 'json') => void;
}

const NetworkDiagramControls: React.FC<NetworkDiagramControlsProps> = ({
    nodes,
    edges,
    onLayoutChange,
    onFilterChange,
    onExport
}) => {
    // Estados para controles
    const [isExpanded, setIsExpanded] = useState(false);
    const [layout, setLayout] = useState<LayoutConfig>({
        type: 'force',
        strength: 0.5,
        distance: 100,
        iterations: 100
    });
    
    const [filters, setFilters] = useState<DiagramFilters>({
        correlationLevels: ['target', 'high', 'medium', 'low', 'indirect'],
        operators: [],
        interactionTypes: ['llamada', 'datos', 'mixed'],
        minInteractions: 1,
        showLabels: true,
        showDirections: true
    });

    // Obtener operadores únicos de los nodos
    const uniqueOperators = Array.from(new Set(nodes.map(n => n.operator))).sort();
    
    // Estadísticas del diagrama
    const stats = {
        totalNodes: nodes.length,
        totalEdges: edges.length,
        visibleNodes: nodes.filter(n => 
            filters.correlationLevels.includes(n.correlationLevel) &&
            n.interactionCount >= filters.minInteractions &&
            (filters.operators.length === 0 || filters.operators.includes(n.operator))
        ).length
    };

    const handleLayoutChange = (key: keyof LayoutConfig, value: string | number) => {
        const newLayout = { ...layout, [key]: value };
        setLayout(newLayout);
        onLayoutChange(newLayout);
    };

    const handleFilterChange = (key: keyof DiagramFilters, value: any) => {
        const newFilters = { ...filters, [key]: value };
        setFilters(newFilters);
        onFilterChange(newFilters);
    };

    const toggleCorrelationLevel = (level: string) => {
        const newLevels = filters.correlationLevels.includes(level)
            ? filters.correlationLevels.filter(l => l !== level)
            : [...filters.correlationLevels, level];
        handleFilterChange('correlationLevels', newLevels);
    };

    const toggleOperator = (operator: string) => {
        const newOperators = filters.operators.includes(operator)
            ? filters.operators.filter(o => o !== operator)
            : [...filters.operators, operator];
        handleFilterChange('operators', newOperators);
    };

    const resetFilters = () => {
        const defaultFilters: DiagramFilters = {
            correlationLevels: ['target', 'high', 'medium', 'low', 'indirect'],
            operators: [],
            interactionTypes: ['llamada', 'datos', 'mixed'],
            minInteractions: 1,
            showLabels: true,
            showDirections: true
        };
        setFilters(defaultFilters);
        onFilterChange(defaultFilters);
    };

    return (
        <div className="bg-secondary-light border-b border-secondary p-4">
            {/* Barra de controles principales */}
            <div className="flex items-center justify-between">
                {/* Controles de layout */}
                <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                        <span className="text-sm text-gray-300">Layout:</span>
                        <select
                            value={layout.type}
                            onChange={(e) => handleLayoutChange('type', e.target.value)}
                            className="bg-secondary text-white text-sm rounded px-3 py-1 border border-secondary-light focus:border-cyan-400 focus:outline-none"
                        >
                            <option value="force">Fuerza dirigida</option>
                            <option value="circular">Circular</option>
                            <option value="grid">Grilla</option>
                            <option value="hierarchy">Jerárquico</option>
                        </select>
                    </div>

                    {/* Configuración de fuerza (solo para force layout) */}
                    {layout.type === 'force' && (
                        <>
                            <div className="flex items-center space-x-2">
                                <span className="text-sm text-gray-300">Fuerza:</span>
                                <input
                                    type="range"
                                    min="0.1"
                                    max="1"
                                    step="0.1"
                                    value={layout.strength}
                                    onChange={(e) => handleLayoutChange('strength', parseFloat(e.target.value))}
                                    className="w-16"
                                />
                                <span className="text-xs text-gray-400 w-8">{layout.strength}</span>
                            </div>
                            
                            <div className="flex items-center space-x-2">
                                <span className="text-sm text-gray-300">Distancia:</span>
                                <input
                                    type="range"
                                    min="50"
                                    max="200"
                                    step="10"
                                    value={layout.distance}
                                    onChange={(e) => handleLayoutChange('distance', parseInt(e.target.value))}
                                    className="w-16"
                                />
                                <span className="text-xs text-gray-400 w-10">{layout.distance}</span>
                            </div>
                        </>
                    )}
                </div>

                {/* Estadísticas y controles de vista */}
                <div className="flex items-center space-x-4">
                    <div className="text-sm text-gray-300">
                        <span className="text-cyan-300 font-bold">{stats.visibleNodes}</span>/{stats.totalNodes} nodos
                        {' | '}
                        <span className="text-yellow-300 font-bold">{stats.totalEdges}</span> conexiones
                    </div>

                    <button
                        onClick={() => setIsExpanded(!isExpanded)}
                        className="text-gray-400 hover:text-white transition-colors p-1 hover:bg-secondary rounded"
                        title={isExpanded ? "Ocultar filtros" : "Mostrar filtros"}
                    >
                        <span className={`transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
                            {ICONS.chevronDown}
                        </span>
                    </button>
                </div>
            </div>

            {/* Panel expandible de filtros y exportación */}
            {isExpanded && (
                <div className="mt-4 pt-4 border-t border-secondary">
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* Filtros por nivel de correlación */}
                        <div>
                            <h4 className="text-sm font-medium text-white mb-3">Niveles de Correlación</h4>
                            <div className="space-y-2">
                                {[
                                    { key: 'target', label: 'Objetivo', color: 'text-red-300' },
                                    { key: 'high', label: 'Alta', color: 'text-orange-300' },
                                    { key: 'medium', label: 'Media', color: 'text-yellow-300' },
                                    { key: 'low', label: 'Baja', color: 'text-green-300' },
                                    { key: 'indirect', label: 'Indirecta', color: 'text-purple-300' }
                                ].map(({ key, label, color }) => (
                                    <label key={key} className="flex items-center space-x-2 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={filters.correlationLevels.includes(key)}
                                            onChange={() => toggleCorrelationLevel(key)}
                                            className="rounded border-gray-600 bg-secondary text-cyan-500 focus:ring-cyan-500"
                                        />
                                        <span className={`text-sm ${color}`}>{label}</span>
                                        <span className="text-xs text-gray-400">
                                            ({nodes.filter(n => n.correlationLevel === key).length})
                                        </span>
                                    </label>
                                ))}
                            </div>
                        </div>

                        {/* Filtros por operador */}
                        <div>
                            <h4 className="text-sm font-medium text-white mb-3">Operadores</h4>
                            <div className="space-y-2 max-h-32 overflow-y-auto">
                                {uniqueOperators.map(operator => (
                                    <label key={operator} className="flex items-center space-x-2 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={filters.operators.length === 0 || filters.operators.includes(operator)}
                                            onChange={() => toggleOperator(operator)}
                                            className="rounded border-gray-600 bg-secondary text-cyan-500 focus:ring-cyan-500"
                                        />
                                        <span className="text-sm text-gray-300">{operator}</span>
                                        <span className="text-xs text-gray-400">
                                            ({nodes.filter(n => n.operator === operator).length})
                                        </span>
                                    </label>
                                ))}
                            </div>
                            {uniqueOperators.length > 0 && (
                                <button
                                    onClick={() => handleFilterChange('operators', [])}
                                    className="text-xs text-cyan-400 hover:text-cyan-300 mt-2"
                                >
                                    Mostrar todos
                                </button>
                            )}
                        </div>

                        {/* Configuración de vista y exportación */}
                        <div>
                            <h4 className="text-sm font-medium text-white mb-3">Vista y Exportación</h4>
                            <div className="space-y-3">
                                {/* Filtro por cantidad mínima de interacciones */}
                                <div>
                                    <label className="text-sm text-gray-300 block mb-1">
                                        Mín. interacciones: {filters.minInteractions}
                                    </label>
                                    <input
                                        type="range"
                                        min="1"
                                        max="20"
                                        value={filters.minInteractions}
                                        onChange={(e) => handleFilterChange('minInteractions', parseInt(e.target.value))}
                                        className="w-full"
                                    />
                                </div>

                                {/* Opciones de visualización */}
                                <div className="space-y-2">
                                    <label className="flex items-center space-x-2 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={filters.showLabels}
                                            onChange={(e) => handleFilterChange('showLabels', e.target.checked)}
                                            className="rounded border-gray-600 bg-secondary text-cyan-500"
                                        />
                                        <span className="text-sm text-gray-300">Mostrar etiquetas</span>
                                    </label>
                                    
                                    <label className="flex items-center space-x-2 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={filters.showDirections}
                                            onChange={(e) => handleFilterChange('showDirections', e.target.checked)}
                                            className="rounded border-gray-600 bg-secondary text-cyan-500"
                                        />
                                        <span className="text-sm text-gray-300">Mostrar direcciones</span>
                                    </label>
                                </div>

                                {/* Botones de exportación */}
                                <div className="pt-2 border-t border-secondary">
                                    <div className="flex space-x-2">
                                        <button
                                            onClick={() => onExport('png')}
                                            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-xs px-3 py-1 rounded transition-colors"
                                        >
                                            PNG
                                        </button>
                                        <button
                                            onClick={() => onExport('svg')}
                                            className="flex-1 bg-green-600 hover:bg-green-700 text-white text-xs px-3 py-1 rounded transition-colors"
                                        >
                                            SVG
                                        </button>
                                        <button
                                            onClick={() => onExport('json')}
                                            className="flex-1 bg-purple-600 hover:bg-purple-700 text-white text-xs px-3 py-1 rounded transition-colors"
                                        >
                                            JSON
                                        </button>
                                    </div>
                                </div>

                                {/* Reset filters */}
                                <button
                                    onClick={resetFilters}
                                    className="w-full bg-gray-600 hover:bg-gray-700 text-white text-xs px-3 py-1 rounded transition-colors"
                                >
                                    Resetear filtros
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default NetworkDiagramControls;