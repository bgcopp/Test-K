import React, { useMemo, useState } from 'react';
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
                
                <div className="overflow-y-auto max-h-64">
                    {filteredSheets.length > 0 ? (
                        <div className="p-2 space-y-2">
                            {filteredSheets.map(sheet => (
                                <div
                                    key={sheet.id}
                                    className={`p-3 rounded border cursor-pointer transition-colors ${
                                        selectedSheetId === sheet.id
                                            ? 'bg-primary/20 border-primary'
                                            : 'bg-secondary border-secondary hover:bg-secondary-light'
                                    }`}
                                    onClick={() => sheet.status === 'completed' ? onSelectSheet(sheet.id) : null}
                                >
                                    <div className="flex items-start justify-between">
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center mb-1">
                                                <span className="mr-2 text-primary text-sm">{ICONS.document}</span>
                                                <span className="text-sm font-medium text-light truncate">
                                                    {sheet.filename}
                                                </span>
                                            </div>
                                            
                                            <div className="space-y-1">
                                                <div className="flex items-center space-x-2">
                                                    <span className="px-2 py-1 text-xs bg-primary/20 text-primary rounded">
                                                        {sheet.operator}
                                                    </span>
                                                    {getStatusBadge(sheet.status)}
                                                </div>
                                                
                                                <div className="text-xs text-medium">
                                                    {sheet.documentType}
                                                </div>
                                                
                                                <div className="text-xs text-medium">
                                                    {(sheet.processedRecords || 0).toLocaleString()} registros
                                                </div>
                                                
                                                <div className="text-xs text-medium">
                                                    {formatDate(sheet.uploadDate)}
                                                </div>
                                            </div>

                                            {sheet.errorMessage && (
                                                <div className="text-xs text-red-400 mt-1 break-words">
                                                    {sheet.errorMessage}
                                                </div>
                                            )}
                                        </div>

                                        <div className="ml-2 flex flex-col space-y-1">
                                            <Button
                                                variant="danger"
                                                size="sm"
                                                icon={ICONS.trash}
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleDeleteSheet(sheet);
                                                }}
                                                disabled={isDeletingSheet === sheet.id}
                                                className="text-xs"
                                            >
                                                {isDeletingSheet === sheet.id ? '...' : ''}
                                            </Button>
                                        </div>
                                    </div>
                                </div>
                            ))}
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