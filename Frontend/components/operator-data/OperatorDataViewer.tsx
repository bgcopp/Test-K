import React, { useState, useEffect } from 'react';
import type { OperatorSheet, OperatorCellularRecord } from '../../types';
import FileNavigationPanel from './FileNavigationPanel';
import DataExplorationPanel from './DataExplorationPanel';
import { getOperatorSheetData } from '../../services/api';
import { useConfirmation, confirmationPresets } from '../../hooks/useConfirmation';

interface OperatorDataViewerProps {
    missionId: string;
    sheets: OperatorSheet[];
    onRefresh: () => void;
    onDeleteSheet: (sheetId: string) => Promise<void>;
}

const OperatorDataViewer: React.FC<OperatorDataViewerProps> = ({
    missionId,
    sheets,
    onRefresh,
    onDeleteSheet
}) => {
    const [selectedSheetId, setSelectedSheetId] = useState<string | null>(null);
    const [sheetData, setSheetData] = useState<OperatorCellularRecord[]>([]);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalRecords, setTotalRecords] = useState(0);
    const [hasMore, setHasMore] = useState(false);
    const { showConfirmation } = useConfirmation();
    const [isLoadingData, setIsLoadingData] = useState(false);
    const [columns, setColumns] = useState<string[]>([]);
    const [displayNames, setDisplayNames] = useState<{[key: string]: string}>({});
    const [searchTerm, setSearchTerm] = useState('');
    const [filterOperator, setFilterOperator] = useState<string>('');
    const [filterDocumentType, setFilterDocumentType] = useState<string>('');

    const pageSize = 50;

    // Auto-select first sheet if available and none selected
    useEffect(() => {
        if (sheets.length > 0 && !selectedSheetId) {
            const firstCompletedSheet = sheets.find(sheet => sheet.status === 'completed');
            if (firstCompletedSheet) {
                setSelectedSheetId(firstCompletedSheet.id);
            }
        }
    }, [sheets, selectedSheetId]);

    // Load data when selected sheet changes
    useEffect(() => {
        if (selectedSheetId) {
            loadSheetData(selectedSheetId, 1);
        } else {
            setSheetData([]);
            setCurrentPage(1);
            setTotalRecords(0);
            setHasMore(false);
        }
    }, [selectedSheetId]);

    const loadSheetData = async (sheetId: string, page: number = 1) => {
        setIsLoadingData(true);
        try {
            const response = await getOperatorSheetData(sheetId, page, pageSize);
            
            if (page === 1) {
                setSheetData(response.data);
                // Actualizar columnas dinámicas si están disponibles
                if (response.columns) {
                    setColumns(response.columns);
                }
                if (response.displayNames) {
                    setDisplayNames(response.displayNames);
                }
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

    const handleLoadMore = async () => {
        if (selectedSheetId && hasMore) {
            await loadSheetData(selectedSheetId, currentPage + 1);
        }
    };

    const handleDeleteSheet = async (sheetId: string) => {
        const sheet = sheets.find(s => s.id === sheetId);
        if (!sheet) return;

        const confirmed = await showConfirmation(
            confirmationPresets.deleteDataFile(sheet.filename)
        );
        
        if (!confirmed) return;
        
        try {
            await onDeleteSheet(sheetId);
            
            // If deleted sheet was selected, clear selection
            if (selectedSheetId === sheetId) {
                setSelectedSheetId(null);
            }
            
            onRefresh();
        } catch (error) {
            console.error('Error al eliminar hoja:', error);
            alert(`Error al eliminar: ${(error as Error).message}`);
        }
    };

    const selectedSheet = selectedSheetId ? sheets.find(s => s.id === selectedSheetId) : null;

    return (
        <div className="grid grid-cols-5 gap-6 h-full min-h-[600px]">
            {/* Left Panel - Navigation (40%) */}
            <div className="col-span-2">
                <FileNavigationPanel
                    sheets={sheets}
                    selectedSheetId={selectedSheetId}
                    onSelectSheet={setSelectedSheetId}
                    filterOperator={filterOperator}
                    setFilterOperator={setFilterOperator}
                    filterDocumentType={filterDocumentType}
                    setFilterDocumentType={setFilterDocumentType}
                    onRefresh={onRefresh}
                    onDeleteSheet={handleDeleteSheet}
                />
            </div>
            
            {/* Right Panel - Data View (60%) */}
            <div className="col-span-3">
                <DataExplorationPanel
                    selectedSheet={selectedSheet}
                    sheetData={sheetData}
                    totalRecords={totalRecords}
                    hasMore={hasMore}
                    isLoadingData={isLoadingData}
                    searchTerm={searchTerm}
                    setSearchTerm={setSearchTerm}
                    onLoadMore={handleLoadMore}
                    columns={columns}
                    displayNames={displayNames}
                />
            </div>
        </div>
    );
};

export default OperatorDataViewer;