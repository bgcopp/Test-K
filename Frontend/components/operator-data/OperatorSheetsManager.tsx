import React, { useState, useEffect, useMemo } from 'react';
import Button from '../ui/Button';
import Table from '../ui/Table';
import Modal from '../ui/Modal';
import { ICONS } from '../../constants';
import type { OperatorSheet, OperatorCellularRecord } from '../../types';
import { getOperatorSheetData } from '../../services/api';

interface OperatorSheetsManagerProps {
    missionId: string;
    sheets: OperatorSheet[];
    onRefresh: () => void;
    onDeleteSheet: (sheetId: string) => Promise<void>;
}

const OperatorSheetsManager: React.FC<OperatorSheetsManagerProps> = ({
    missionId,
    sheets,
    onRefresh,
    onDeleteSheet
}) => {
    const [filterOperator, setFilterOperator] = useState<string>('');
    const [filterDocumentType, setFilterDocumentType] = useState<string>('');
    const [selectedSheet, setSelectedSheet] = useState<OperatorSheet | null>(null);
    const [sheetData, setSheetData] = useState<OperatorCellularRecord[]>([]);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalRecords, setTotalRecords] = useState(0);
    const [hasMore, setHasMore] = useState(false);
    const [isLoadingData, setIsLoadingData] = useState(false);
    const [showDataModal, setShowDataModal] = useState(false);
    const [isDeletingSheet, setIsDeletingSheet] = useState<string | null>(null);
    
    const pageSize = 50;

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

    const loadSheetData = async (sheet: OperatorSheet, page: number = 1) => {
        setIsLoadingData(true);
        try {
            const response = await getOperatorSheetData(sheet.id, page, pageSize);
            
            if (page === 1) {
                setSheetData(response.data);
            } else {
                setSheetData(prev => [...prev, ...response.data]);
            }
            
            setTotalRecords(response.total);
            setHasMore(response.hasMore);
            setCurrentPage(page);
        } catch (error) {
            console.error('Error al cargar datos de la hoja:', error);
            alert(`Error al cargar datos: ${(error as Error).message}`);
        } finally {
            setIsLoadingData(false);
        }
    };

    const handleViewData = async (sheet: OperatorSheet) => {
        setSelectedSheet(sheet);
        setShowDataModal(true);
        setCurrentPage(1);
        setSheetData([]);
        await loadSheetData(sheet, 1);
    };

    const handleLoadMore = async () => {
        if (selectedSheet && hasMore) {
            await loadSheetData(selectedSheet, currentPage + 1);
        }
    };

    const handleDeleteSheet = async (sheet: OperatorSheet) => {
        if (!window.confirm(`¿Estás seguro de que quieres eliminar el archivo "${sheet.filename}"? Esta acción no se puede deshacer.`)) {
            return;
        }
        
        setIsDeletingSheet(sheet.id);
        try {
            await onDeleteSheet(sheet.id);
            onRefresh();
        } catch (error) {
            console.error('Error al eliminar hoja:', error);
            alert(`Error al eliminar: ${(error as Error).message}`);
        } finally {
            setIsDeletingSheet(null);
        }
    };

    const closeDataModal = () => {
        setShowDataModal(false);
        setSelectedSheet(null);
        setSheetData([]);
        setCurrentPage(1);
    };

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
        
        // Fallback para valores de estado inesperados
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

    return (
        <div className="space-y-6">
            {/* Controles de Filtrado */}
            <div className="flex flex-wrap gap-4 items-center justify-between">
                <div className="flex flex-wrap gap-4">
                    {/* Filtro por Operador */}
                    <div>
                        <label className="block text-sm font-medium text-light mb-1">
                            Operador
                        </label>
                        <select
                            value={filterOperator}
                            onChange={(e) => setFilterOperator(e.target.value)}
                            className="px-3 py-2 bg-secondary border border-secondary-light rounded-md text-light text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                        >
                            <option value="">Todos los operadores</option>
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
                            className="px-3 py-2 bg-secondary border border-secondary-light rounded-md text-light text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                        >
                            <option value="">Todos los tipos</option>
                            {uniqueDocumentTypes.map(type => (
                                <option key={type} value={type}>{type}</option>
                            ))}
                        </select>
                    </div>
                </div>

                <Button
                    variant="secondary"
                    icon={ICONS.refresh}
                    onClick={onRefresh}
                >
                    Actualizar
                </Button>
            </div>

            {/* Resumen */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-secondary-light p-4 rounded-md">
                    <p className="text-sm text-medium">Total de Archivos</p>
                    <p className="text-2xl font-bold text-light">{filteredSheets.length}</p>
                </div>
                <div className="bg-secondary-light p-4 rounded-md">
                    <p className="text-sm text-medium">Registros Procesados</p>
                    <p className="text-2xl font-bold text-light">
                        {filteredSheets.reduce((sum, sheet) => sum + (sheet.processedRecords || 0), 0).toLocaleString()}
                    </p>
                </div>
                <div className="bg-secondary-light p-4 rounded-md">
                    <p className="text-sm text-medium">Archivos Completados</p>
                    <p className="text-2xl font-bold text-light">
                        {filteredSheets.filter(sheet => sheet.status === 'completed').length}
                    </p>
                </div>
            </div>

            {/* Tabla de Archivos */}
            {filteredSheets.length > 0 ? (
                <div className="overflow-x-auto">
                    <Table headers={['Archivo', 'Operador', 'Tipo', 'Estado', 'Registros', 'Fecha', 'Acciones']}>
                        {filteredSheets.map(sheet => (
                            <tr key={sheet.id} className="hover:bg-secondary-light">
                                <td className="px-4 py-3 text-sm text-light font-medium">
                                    <div className="flex items-center">
                                        <span className="mr-2 text-primary">{ICONS.document}</span>
                                        <div>
                                            <div className="font-medium">{sheet.filename}</div>
                                            {sheet.errorMessage && (
                                                <div className="text-xs text-red-400 mt-1">{sheet.errorMessage}</div>
                                            )}
                                        </div>
                                    </div>
                                </td>
                                <td className="px-4 py-3 text-sm text-light">
                                    <span className="px-2 py-1 text-xs bg-primary/20 text-primary rounded">
                                        {sheet.operator}
                                    </span>
                                </td>
                                <td className="px-4 py-3 text-sm text-light">
                                    {sheet.documentType}
                                </td>
                                <td className="px-4 py-3 text-sm">
                                    {getStatusBadge(sheet.status)}
                                </td>
                                <td className="px-4 py-3 text-sm text-light font-mono">
                                    {(sheet.processedRecords || 0).toLocaleString()}
                                </td>
                                <td className="px-4 py-3 text-sm text-medium">
                                    {formatDate(sheet.uploadDate)}
                                </td>
                                <td className="px-4 py-3 text-sm">
                                    <div className="flex space-x-2">
                                        {sheet.status === 'completed' && (
                                            <Button
                                                variant="secondary"
                                                size="sm"
                                                icon={ICONS.eye}
                                                onClick={() => handleViewData(sheet)}
                                            >
                                                Ver Datos
                                            </Button>
                                        )}
                                        <Button
                                            variant="danger"
                                            size="sm"
                                            icon={ICONS.trash}
                                            onClick={() => handleDeleteSheet(sheet)}
                                            disabled={isDeletingSheet === sheet.id}
                                        >
                                            {isDeletingSheet === sheet.id ? 'Eliminando...' : 'Eliminar'}
                                        </Button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </Table>
                </div>
            ) : (
                <div className="text-center py-12">
                    <div className="text-6xl text-medium mb-4">{ICONS.document}</div>
                    <p className="text-medium mb-4">No se han encontrado archivos de datos de operadores</p>
                    <p className="text-sm text-medium">
                        {sheets.length === 0 
                            ? 'Carga tu primer archivo usando el formulario de arriba'
                            : 'Ajusta los filtros para ver más archivos'
                        }
                    </p>
                </div>
            )}

            {/* Modal de Datos */}
            <Modal
                isOpen={showDataModal}
                onClose={closeDataModal}
                title={`Datos del Archivo: ${selectedSheet?.filename}`}
                size="full"
            >
                {selectedSheet && (
                    <div className="space-y-4">
                        {/* Información del Archivo */}
                        <div className="bg-secondary-light p-4 rounded-lg">
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

                        {/* Datos */}
                        {sheetData.length > 0 ? (
                            <div className="space-y-4">
                                <div className="overflow-x-auto max-h-96">
                                    <Table headers={['ID', 'Teléfono', 'IMEI', 'IMSI', 'Cell ID', 'LAC', 'Timestamp', 'Ubicación']}>
                                        {sheetData.map(record => (
                                            <tr key={record.id} className="hover:bg-secondary-light">
                                                <td className="px-4 py-2 text-sm text-light font-mono">{record.id}</td>
                                                <td className="px-4 py-2 text-sm text-light font-mono">
                                                    {record.phoneNumber || '-'}
                                                </td>
                                                <td className="px-4 py-2 text-sm text-light font-mono">
                                                    {record.imei || '-'}
                                                </td>
                                                <td className="px-4 py-2 text-sm text-light font-mono">
                                                    {record.imsi || '-'}
                                                </td>
                                                <td className="px-4 py-2 text-sm text-light font-mono">
                                                    {record.cellId || '-'}
                                                </td>
                                                <td className="px-4 py-2 text-sm text-light font-mono">
                                                    {record.lac || '-'}
                                                </td>
                                                <td className="px-4 py-2 text-sm text-medium">
                                                    {record.timestamp ? new Date(record.timestamp).toLocaleString() : '-'}
                                                </td>
                                                <td className="px-4 py-2 text-sm text-medium">
                                                    {record.location || '-'}
                                                </td>
                                            </tr>
                                        ))}
                                    </Table>
                                </div>

                                {/* Paginación */}
                                <div className="flex justify-between items-center">
                                    <div className="text-sm text-medium">
                                        Mostrando {sheetData.length} de {totalRecords.toLocaleString()} registros
                                    </div>
                                    {hasMore && (
                                        <Button
                                            variant="secondary"
                                            onClick={handleLoadMore}
                                            disabled={isLoadingData}
                                            icon={isLoadingData ? ICONS.loading : ICONS.chevronDown}
                                        >
                                            {isLoadingData ? 'Cargando...' : 'Cargar Más'}
                                        </Button>
                                    )}
                                </div>
                            </div>
                        ) : (
                            <div className="text-center py-8">
                                {isLoadingData ? (
                                    <div className="space-y-2">
                                        <div className="text-4xl text-primary">{ICONS.loading}</div>
                                        <p className="text-medium">Cargando datos...</p>
                                    </div>
                                ) : (
                                    <div className="space-y-2">
                                        <div className="text-4xl text-medium">{ICONS.exclamationCircle}</div>
                                        <p className="text-medium">No se pudieron cargar los datos</p>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}
            </Modal>
        </div>
    );
};

export default OperatorSheetsManager;