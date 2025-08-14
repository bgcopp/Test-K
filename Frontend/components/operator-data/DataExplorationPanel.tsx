import React, { useMemo } from 'react';
import Button from '../ui/Button';
import Table from '../ui/Table';
import { ICONS } from '../../constants';
import type { OperatorSheet, OperatorCellularRecord } from '../../types';

interface DataExplorationPanelProps {
    selectedSheet: OperatorSheet | null;
    sheetData: OperatorCellularRecord[];
    totalRecords: number;
    hasMore: boolean;
    isLoadingData: boolean;
    searchTerm: string;
    setSearchTerm: (value: string) => void;
    onLoadMore: () => void;
    columns: string[];
    displayNames: {[key: string]: string};
}

const DataExplorationPanel: React.FC<DataExplorationPanelProps> = ({
    selectedSheet,
    sheetData,
    totalRecords,
    hasMore,
    isLoadingData,
    searchTerm,
    setSearchTerm,
    onLoadMore,
    columns,
    displayNames
}) => {
    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('es-ES', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const formatCellValue = (column: string, value: any) => {
        if (value === null || value === undefined || value === '') {
            return '-';
        }
        
        // Formatear fechas
        if (column.includes('fecha_hora') || column.includes('timestamp')) {
            try {
                return new Date(value).toLocaleString('es-ES', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                });
            } catch {
                return value;
            }
        }
        
        // Formatear números de duración en segundos
        if (column.includes('duracion_segundos')) {
            const seconds = parseInt(value);
            if (!isNaN(seconds)) {
                return `${seconds}s`;
            }
        }
        
        // Formatear coordenadas con precisión limitada
        if (column.includes('latitud') || column.includes('longitud')) {
            const coord = parseFloat(value);
            if (!isNaN(coord)) {
                return coord.toFixed(6);
            }
        }
        
        return value.toString();
    };

    // Filter data based on search term (using dynamic columns)
    const filteredData = useMemo(() => {
        if (!searchTerm.trim()) return sheetData;
        
        const term = searchTerm.toLowerCase();
        return sheetData.filter(record => 
            columns.some(col => {
                const value = (record as any)[col];
                return value && value.toString().toLowerCase().includes(term);
            })
        );
    }, [sheetData, searchTerm, columns]);

    const exportData = () => {
        if (!selectedSheet || filteredData.length === 0) return;

        // Create CSV content using dynamic columns
        const headers = columns.map(col => displayNames[col] || col);
        const csvContent = [
            headers.join(','),
            ...filteredData.map(record => 
                columns.map(col => (record as any)[col] || '').map(field => `"${field}"`).join(',')
            )
        ].join('\n');

        // Download file
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `${selectedSheet.filename}_data.csv`;
        link.click();
    };

    if (!selectedSheet) {
        return (
            <div className="bg-secondary-light rounded-lg h-full flex items-center justify-center">
                <div className="text-center">
                    <div className="text-6xl text-medium mb-4">{ICONS.document}</div>
                    <h3 className="text-lg font-medium text-light mb-2">Selecciona un Archivo</h3>
                    <p className="text-medium">
                        Elige un archivo de la lista de la izquierda para ver sus datos
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-4 h-full flex flex-col">
            {/* File Header */}
            <div className="bg-secondary-light p-4 rounded-lg">
                <div className="flex items-center justify-between mb-3">
                    <h3 className="text-lg font-semibold text-light flex items-center">
                        <span className="mr-2 text-primary">{ICONS.document}</span>
                        {selectedSheet.filename}
                    </h3>
                    <div className="flex space-x-2">
                        <Button
                            variant="secondary"
                            size="sm"
                            icon={ICONS.download}
                            onClick={exportData}
                            disabled={filteredData.length === 0}
                        >
                            Exportar
                        </Button>
                    </div>
                </div>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                        <span className="text-medium">Operador:</span>
                        <div className="font-medium text-light">{selectedSheet.operator}</div>
                    </div>
                    <div>
                        <span className="text-medium">Tipo:</span>
                        <div className="font-medium text-light">{selectedSheet.documentType}</div>
                    </div>
                    <div>
                        <span className="text-medium">Registros:</span>
                        <div className="font-medium text-light">{(selectedSheet.processedRecords || 0).toLocaleString()}</div>
                    </div>
                    <div>
                        <span className="text-medium">Fecha:</span>
                        <div className="font-medium text-light">{formatDate(selectedSheet.uploadDate)}</div>
                    </div>
                </div>
            </div>

            {/* Search and Filter Controls */}
            <div className="bg-secondary-light p-4 rounded-lg">
                <div className="flex items-center space-x-4">
                    <div className="flex-1">
                        <div className="relative">
                            <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-medium">
                                {ICONS.search}
                            </span>
                            <input
                                type="text"
                                placeholder={`Buscar en ${columns.map(col => displayNames[col] || col).join(', ')}...`}
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full pl-10 pr-4 py-2 bg-secondary border border-secondary-light rounded-md text-light text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                            />
                        </div>
                    </div>
                    {searchTerm && (
                        <Button
                            variant="secondary"
                            size="sm"
                            icon={ICONS.x}
                            onClick={() => setSearchTerm('')}
                        >
                            Limpiar
                        </Button>
                    )}
                </div>
                
                {searchTerm && (
                    <div className="mt-2 text-sm text-medium">
                        Mostrando {filteredData.length} de {sheetData.length} registros
                    </div>
                )}
            </div>

            {/* Data Display */}
            <div className="bg-secondary-light rounded-lg flex-1 min-h-0 flex flex-col">
                {selectedSheet.status !== 'completed' ? (
                    <div className="flex-1 flex items-center justify-center">
                        <div className="text-center">
                            {selectedSheet.status === 'processing' ? (
                                <>
                                    <div className="text-4xl text-primary mb-2">{ICONS.loading}</div>
                                    <p className="text-medium">Archivo en procesamiento...</p>
                                </>
                            ) : (
                                <>
                                    <div className="text-4xl text-red-400 mb-2">{ICONS.exclamationCircle}</div>
                                    <p className="text-medium mb-2">Error en el procesamiento</p>
                                    {selectedSheet.errorMessage && (
                                        <p className="text-sm text-red-400 mt-2 max-w-md">
                                            {selectedSheet.errorMessage}
                                        </p>
                                    )}
                                </>
                            )}
                        </div>
                    </div>
                ) : filteredData.length > 0 ? (
                    <>
                        <div className="p-4 border-b border-secondary">
                            <h4 className="text-md font-medium text-light">
                                Datos del Archivo
                                {searchTerm && ` (${filteredData.length} filtrados)`}
                            </h4>
                        </div>
                        
                        <div className="flex-1 overflow-auto">
                            <Table headers={columns.map(col => displayNames[col] || col)}>
                                {filteredData.map(record => (
                                    <tr key={record.id} className="hover:bg-secondary">
                                        {columns.map(col => (
                                            <td key={col} className="px-4 py-2 text-sm text-light font-mono">
                                                {formatCellValue(col, (record as any)[col])}
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                            </Table>
                        </div>

                        {/* Pagination Controls */}
                        <div className="p-4 border-t border-secondary">
                            <div className="flex justify-between items-center">
                                <div className="text-sm text-medium">
                                    Mostrando {sheetData.length} de {totalRecords.toLocaleString()} registros
                                </div>
                                {hasMore && !searchTerm && (
                                    <Button
                                        variant="secondary"
                                        onClick={onLoadMore}
                                        disabled={isLoadingData}
                                        icon={isLoadingData ? ICONS.loading : ICONS.chevronDown}
                                    >
                                        {isLoadingData ? 'Cargando...' : 'Cargar Más'}
                                    </Button>
                                )}
                            </div>
                        </div>
                    </>
                ) : (
                    <div className="flex-1 flex items-center justify-center">
                        <div className="text-center">
                            {isLoadingData ? (
                                <>
                                    <div className="text-4xl text-primary mb-2">{ICONS.loading}</div>
                                    <p className="text-medium">Cargando datos...</p>
                                </>
                            ) : searchTerm ? (
                                <>
                                    <div className="text-4xl text-medium mb-2">{ICONS.search}</div>
                                    <p className="text-medium mb-2">No se encontraron resultados</p>
                                    <p className="text-sm text-medium">
                                        Intenta con otros términos de búsqueda
                                    </p>
                                </>
                            ) : (
                                <>
                                    <div className="text-4xl text-medium mb-2">{ICONS.exclamationCircle}</div>
                                    <p className="text-medium">No se pudieron cargar los datos</p>
                                </>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default DataExplorationPanel;