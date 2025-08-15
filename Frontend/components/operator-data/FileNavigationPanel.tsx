import React, { useMemo, useState, useEffect } from 'react';
import Button from '../ui/Button';
import { ICONS } from '../../constants';
import type { OperatorSheet } from '../../types';

interface FileNavigationPanelProps {
    sheets: OperatorSheet[];
    selectedSheetId: string | null;
    onSelectSheet: (sheetId: string | null) => void;
    filterOperator: string;
    setFilterOperator: (value: string) => void;
    filterDocumentType: string;
    setFilterDocumentType: (value: string) => void;
    onRefresh: () => void;
    onDeleteSheet: (sheetId: string) => Promise<void>;
}

const FileNavigationPanel: React.FC<FileNavigationPanelProps> = ({
    sheets,
    selectedSheetId,
    onSelectSheet,
    filterOperator,
    setFilterOperator,
    filterDocumentType,
    setFilterDocumentType,
    onRefresh,
    onDeleteSheet
}) => {
    const [isDeletingSheet, setIsDeletingSheet] = useState<string | null>(null);
    const [windowHeight, setWindowHeight] = useState(window.innerHeight);

    // Hook para detectar cambios en el tamaño de la ventana
    useEffect(() => {
        const handleResize = () => {
            setWindowHeight(window.innerHeight);
        };

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    // Filtros únicos basados en las hojas existentes
    const uniqueOperators = useMemo(() => {
        const operators = Array.from(new Set(sheets.map(sheet => sheet.operator)));
        return operators.sort();
    }, [sheets]);

    const uniqueDocumentTypes = useMemo(() => {
        const types = Array.from(new Set(sheets.map(sheet => sheet.documentType)));
        return types.sort();
    }, [sheets]);

    // Hojas filtradas
    const filteredSheets = useMemo(() => {
        return sheets.filter(sheet => {
            const matchesOperator = !filterOperator || sheet.operator === filterOperator;
            const matchesDocType = !filterDocumentType || sheet.documentType === filterDocumentType;
            return matchesOperator && matchesDocType;
        });
    }, [sheets, filterOperator, filterDocumentType]);

    /**
     * Calcular altura dinámica optimizada basada en el número de archivos
     * Esta función proporciona un crecimiento suave y responsivo de la lista
     * considerando el contenido real y el tamaño de la ventana
     */
    const getDynamicHeightStyles = useMemo(() => {
        const fileCount = filteredSheets.length;
        
        // Estado vacío: altura mínima para el mensaje "no hay archivos"
        if (fileCount === 0) {
            return {
                maxHeight: '12rem', // 192px - equivalente a max-h-48
                minHeight: '8rem',  // 128px - altura mínima para mensaje
                transition: 'max-height 0.3s ease-in-out, min-height 0.3s ease-in-out'
            };
        }
        
        // Cálculo basado en el contenido real de cada archivo
        // Mediciones del DOM actual:
        // - Línea de nombre del archivo: ~24px
        // - Línea de badges (operador + estado): ~28px
        // - Tipo de documento: ~20px  
        // - Número de registros: ~20px
        // - Fecha de subida: ~20px
        // - Padding interno del item: ~24px (p-3)
        // - Margen entre items: ~8px (space-y-2)
        // - Botón de eliminar: incluido en el layout
        const baseItemHeight = 140; // px estimados por archivo
        const containerPadding = 16; // padding del contenedor principal (p-2)
        const itemSpacing = 8; // espacio vertical entre elementos
        
        // Altura estimada basada en contenido
        const estimatedContentHeight = (fileCount * baseItemHeight) + 
                                     containerPadding + 
                                     ((fileCount - 1) * itemSpacing);
        
        // Altura mínima: espacio para al menos 2 archivos (mejor UX)
        const minHeight = Math.max(288, (2 * baseItemHeight) + containerPadding + itemSpacing);
        
        // Altura máxima responsiva: 70% de ventana con límite absoluto
        const maxAllowedHeight = Math.min(600, windowHeight * 0.7);
        
        // Aplicar lógica de crecimiento escalonado para mejor UX
        let finalHeight;
        
        if (fileCount <= 2) {
            // 1-2 archivos: altura compacta y fija
            finalHeight = Math.min(estimatedContentHeight, 300);
        } else if (fileCount <= 5) {
            // 3-5 archivos: crecimiento moderado
            finalHeight = Math.min(estimatedContentHeight, 450);
        } else {
            // 6+ archivos: crecimiento completo hasta el máximo
            finalHeight = Math.min(estimatedContentHeight, maxAllowedHeight);
        }
        
        // Asegurar que no sea menor que la altura mínima
        finalHeight = Math.max(finalHeight, minHeight);
        
        return {
            maxHeight: `${finalHeight}px`,
            minHeight: `${Math.min(minHeight, finalHeight)}px`,
            transition: 'max-height 0.3s ease-in-out, min-height 0.3s ease-in-out'
        };
    }, [filteredSheets.length, windowHeight]);

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('es-ES', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const getStatusBadge = (status: OperatorSheet['status']) => {
        const statusConfig = {
            processing: { color: 'bg-yellow-800 text-yellow-200', label: 'Procesando' },
            completed: { color: 'bg-green-800 text-green-200', label: 'Completado' },
            error: { color: 'bg-red-800 text-red-200', label: 'Error' }
        };
        
        const config = statusConfig[status] || { 
            color: 'bg-gray-800 text-gray-200', 
            label: status || 'Desconocido' 
        };
        
        return (
            <span className={`px-2 py-1 text-xs rounded font-medium ${config.color}`}>
                {config.label}
            </span>
        );
    };

    const handleDeleteSheet = async (sheet: OperatorSheet) => {
        setIsDeletingSheet(sheet.id);
        try {
            await onDeleteSheet(sheet.id);
        } finally {
            setIsDeletingSheet(null);
        }
    };

    return (
        <div className="space-y-4 h-full">
            {/* Summary Statistics */}
            <div className="bg-secondary-light p-4 rounded-lg">
                <h3 className="text-lg font-semibold text-light mb-3">Resumen</h3>
                <div className="grid grid-cols-1 gap-3">
                    <div className="flex justify-between">
                        <span className="text-sm text-medium">Total de Archivos:</span>
                        <span className="text-sm font-bold text-light">{filteredSheets.length}</span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-sm text-medium">Registros Procesados:</span>
                        <span className="text-sm font-bold text-light">
                            {filteredSheets.reduce((sum, sheet) => sum + (sheet.processedRecords || 0), 0).toLocaleString()}
                        </span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-sm text-medium">Operadores:</span>
                        <span className="text-sm font-bold text-light">
                            {new Set(filteredSheets.map(sheet => sheet.operator)).size}
                        </span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-sm text-medium">Completados:</span>
                        <span className="text-sm font-bold text-light">
                            {filteredSheets.filter(sheet => sheet.status === 'completed').length}
                        </span>
                    </div>
                </div>
            </div>

            {/* Filters */}
            <div className="bg-secondary-light p-4 rounded-lg">
                <h4 className="text-md font-medium text-light mb-3">Filtros</h4>
                <div className="space-y-3">
                    {/* Filtro por Operador */}
                    <div>
                        <label className="block text-sm font-medium text-light mb-1">
                            Operador
                        </label>
                        <select
                            value={filterOperator}
                            onChange={(e) => setFilterOperator(e.target.value)}
                            className="w-full px-3 py-2 bg-secondary border border-secondary-light rounded-md text-light text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                        >
                            <option value="">Todos</option>
                            {uniqueOperators.map(operator => (
                                <option key={operator} value={operator}>{operator}</option>
                            ))}
                        </select>
                    </div>

                    {/* Filtro por Tipo de Documento */}
                    <div>
                        <label className="block text-sm font-medium text-light mb-1">
                            Tipo de Documento
                        </label>
                        <select
                            value={filterDocumentType}
                            onChange={(e) => setFilterDocumentType(e.target.value)}
                            className="w-full px-3 py-2 bg-secondary border border-secondary-light rounded-md text-light text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                        >
                            <option value="">Todos</option>
                            {uniqueDocumentTypes.map(type => (
                                <option key={type} value={type}>{type}</option>
                            ))}
                        </select>
                    </div>
                </div>
            </div>

            {/* Refresh Button */}
            <div>
                <Button
                    variant="secondary"
                    icon={ICONS.refresh}
                    onClick={onRefresh}
                    className="w-full"
                >
                    Actualizar Lista
                </Button>
            </div>

            {/* File List */}
            <div className="bg-secondary-light rounded-lg flex-1 min-h-0">
                <div className="p-4 border-b border-secondary">
                    <h4 className="text-md font-medium text-light">Archivos ({filteredSheets.length})</h4>
                </div>
                
                <div 
                    className="overflow-y-auto"
                    style={getDynamicHeightStyles}
                >
                    {filteredSheets.length > 0 ? (
                        <div className="p-3 space-y-3">
                            {filteredSheets.map(sheet => {
                                // Configuración de colores por operador para mejor identificación visual
                                const getOperatorColors = (operator: string) => {
                                    const colors = {
                                        'CLARO': 'from-red-500/10 to-red-600/5 border-red-500/20 text-red-400',
                                        'MOVISTAR': 'from-green-500/10 to-green-600/5 border-green-500/20 text-green-400',
                                        'TIGO': 'from-blue-500/10 to-blue-600/5 border-blue-500/20 text-blue-400',
                                        'WOM': 'from-purple-500/10 to-purple-600/5 border-purple-500/20 text-purple-400'
                                    };
                                    return colors[operator] || 'from-gray-500/10 to-gray-600/5 border-gray-500/20 text-gray-400';
                                };

                                // Configuración de estados con iconos y estilos específicos
                                const getStatusConfig = (status: OperatorSheet['status']) => {
                                    const configs = {
                                        processing: { 
                                            icon: ICONS.loading, 
                                            bgColor: 'bg-gradient-to-r from-yellow-500/20 to-amber-500/10',
                                            borderColor: 'border-yellow-500/30',
                                            textColor: 'text-yellow-400',
                                            label: 'Procesando...',
                                            dotColor: 'bg-yellow-400 animate-pulse'
                                        },
                                        completed: { 
                                            icon: ICONS.checkCircle, 
                                            bgColor: 'bg-gradient-to-r from-green-500/20 to-emerald-500/10',
                                            borderColor: 'border-green-500/30',
                                            textColor: 'text-green-400',
                                            label: 'Completado',
                                            dotColor: 'bg-green-400'
                                        },
                                        error: { 
                                            icon: ICONS.exclamationTriangle, 
                                            bgColor: 'bg-gradient-to-r from-red-500/20 to-rose-500/10',
                                            borderColor: 'border-red-500/30',
                                            textColor: 'text-red-400',
                                            label: 'Error',
                                            dotColor: 'bg-red-400'
                                        }
                                    };
                                    return configs[status] || configs.error;
                                };

                                const operatorColors = getOperatorColors(sheet.operator);
                                const statusConfig = getStatusConfig(sheet.status);
                                const isSelected = selectedSheetId === sheet.id;
                                const isClickable = sheet.status === 'completed';

                                return (
                                    <div
                                        key={sheet.id}
                                        className={`
                                            relative overflow-hidden rounded-xl border transition-all duration-300 ease-out
                                            ${isSelected 
                                                ? 'bg-gradient-to-br from-blue-500/20 to-indigo-600/10 border-blue-500/40 shadow-lg shadow-blue-500/10 scale-[1.02]' 
                                                : 'bg-gradient-to-br from-slate-800/50 to-slate-900/30 border-slate-700/50 hover:from-slate-700/60 hover:to-slate-800/40 hover:border-slate-600/60 hover:shadow-lg hover:shadow-slate-500/5'
                                            }
                                            ${isClickable ? 'cursor-pointer' : 'cursor-default'}
                                            group
                                        `}
                                        onClick={() => isClickable ? onSelectSheet(sheet.id) : null}
                                    >
                                        {/* Línea de estado superior */}
                                        <div className={`h-1 w-full ${statusConfig.bgColor}`}></div>
                                        
                                        <div className="p-4">
                                            {/* Header con nombre de archivo y estado */}
                                            <div className="flex items-start justify-between mb-3">
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center space-x-3 mb-2">
                                                        <div className="flex items-center space-x-2">
                                                            <div className={`w-2 h-2 rounded-full ${statusConfig.dotColor}`}></div>
                                                            <span className="text-slate-400 text-sm">{ICONS.document}</span>
                                                        </div>
                                                        <h4 className="text-base font-semibold text-slate-200 truncate group-hover:text-white transition-colors">
                                                            {sheet.filename}
                                                        </h4>
                                                    </div>

                                                    {/* Badge de estado prominente */}
                                                    <div className="flex items-center space-x-2 mb-3">
                                                        <div className={`
                                                            flex items-center space-x-2 px-3 py-1.5 rounded-lg border
                                                            ${statusConfig.bgColor} ${statusConfig.borderColor}
                                                        `}>
                                                            <span className={`text-sm ${statusConfig.textColor}`}>
                                                                {statusConfig.icon}
                                                            </span>
                                                            <span className={`text-sm font-medium ${statusConfig.textColor}`}>
                                                                {statusConfig.label}
                                                            </span>
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* Botón de eliminar mejorado */}
                                                <div className="ml-3">
                                                    <button
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            handleDeleteSheet(sheet);
                                                        }}
                                                        disabled={isDeletingSheet === sheet.id}
                                                        className={`
                                                            p-2.5 rounded-lg border transition-all duration-200
                                                            ${isDeletingSheet === sheet.id
                                                                ? 'bg-red-500/20 border-red-500/40 text-red-400 cursor-not-allowed'
                                                                : 'bg-slate-800/50 border-slate-700 text-slate-400 hover:bg-red-500/20 hover:border-red-500/40 hover:text-red-400 hover:scale-105'
                                                            }
                                                            group-hover:opacity-100 opacity-70
                                                        `}
                                                        title="Eliminar archivo"
                                                    >
                                                        {isDeletingSheet === sheet.id ? (
                                                            <div className="w-4 h-4">
                                                                {ICONS.loading}
                                                            </div>
                                                        ) : (
                                                            <div className="w-4 h-4">
                                                                {ICONS.trash}
                                                            </div>
                                                        )}
                                                    </button>
                                                </div>
                                            </div>

                                            {/* Información organizada en grid */}
                                            <div className="grid grid-cols-2 gap-4 mb-3">
                                                {/* Operador */}
                                                <div className="space-y-1">
                                                    <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">Operador</p>
                                                    <div className={`
                                                        inline-flex items-center px-3 py-1.5 rounded-lg border bg-gradient-to-r
                                                        ${operatorColors}
                                                    `}>
                                                        <span className="text-sm font-semibold">
                                                            {sheet.operator}
                                                        </span>
                                                    </div>
                                                </div>

                                                {/* Tipo de documento */}
                                                <div className="space-y-1">
                                                    <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">Tipo</p>
                                                    <p className="text-sm font-medium text-slate-300">
                                                        {sheet.documentType}
                                                    </p>
                                                </div>
                                            </div>

                                            {/* Métricas destacadas */}
                                            <div className="grid grid-cols-2 gap-4 mb-3">
                                                {/* Registros procesados */}
                                                <div className="space-y-1">
                                                    <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">Registros</p>
                                                    <div className="flex items-center space-x-2">
                                                        <span className="text-slate-400 text-sm">{ICONS.database}</span>
                                                        <span className="text-lg font-bold text-slate-200">
                                                            {(sheet.processedRecords || 0).toLocaleString()}
                                                        </span>
                                                    </div>
                                                </div>

                                                {/* Fecha de subida */}
                                                <div className="space-y-1">
                                                    <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">Fecha</p>
                                                    <p className="text-sm text-slate-300">
                                                        {formatDate(sheet.uploadDate)}
                                                    </p>
                                                </div>
                                            </div>

                                            {/* Mensaje de error (si existe) */}
                                            {sheet.errorMessage && (
                                                <div className="mt-3 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                                                    <div className="flex items-start space-x-2">
                                                        <span className="text-red-400 text-sm mt-0.5 flex-shrink-0">
                                                            {ICONS.exclamationCircle}
                                                        </span>
                                                        <div>
                                                            <p className="text-xs font-medium text-red-300 mb-1">Error de procesamiento:</p>
                                                            <p className="text-xs text-red-400 break-words leading-relaxed">
                                                                {sheet.errorMessage}
                                                            </p>
                                                        </div>
                                                    </div>
                                                </div>
                                            )}

                                            {/* Indicador de selección/interactividad */}
                                            {isClickable && (
                                                <div className={`
                                                    absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r transition-all duration-300
                                                    ${isSelected 
                                                        ? 'from-blue-500 to-indigo-500 opacity-100' 
                                                        : 'from-slate-600 to-slate-700 opacity-0 group-hover:opacity-100'
                                                    }
                                                `}></div>
                                            )}

                                            {/* Overlay para archivos no clickeables */}
                                            {!isClickable && (
                                                <div className="absolute inset-0 bg-slate-900/20 pointer-events-none rounded-xl"></div>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    ) : (
                        <div className="text-center py-8">
                            <div className="text-4xl text-medium mb-2">{ICONS.document}</div>
                            <p className="text-sm text-medium">
                                {sheets.length === 0 
                                    ? 'No hay archivos cargados'
                                    : 'No hay archivos que coincidan con los filtros'
                                }
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default FileNavigationPanel;