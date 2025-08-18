import React, { useState, useMemo, useEffect } from 'react';
import { useParams, Navigate } from 'react-router-dom';
import type { Mission, TargetRecord, OperatorSheet, OperatorUploadResponse, FileProcessingResult, CorrelationResult, CorrelationAnalysisResponse } from '../types';
import Button from '../components/ui/Button';
import Table from '../components/ui/Table';
import FileUpload from '../components/ui/FileUpload';
import CellularDataStats from '../components/ui/CellularDataStats';
import PremiumProcessingOverlay from '../components/ui/PremiumProcessingOverlay';
import PointChip from '../components/ui/PointChip';
import Pagination from '../components/ui/Pagination';
import { CorrelationCellBadgeGroup } from '../components/ui/CorrelationCellBadge';
import CorrelationLegend from '../components/ui/CorrelationLegend';
import { OperatorDataUpload, OperatorSheetsManager, OperatorDataViewer } from '../components/operator-data';
import { ICONS } from '../constants';
import { uploadCellularData, clearCellularDataApi, runAnalysis, getOperatorSheets, deleteOperatorSheet, analyzeCorrelation } from '../services/api';
import { useNotification } from '../hooks/useNotification';
import { useConfirmation, confirmationPresets } from '../hooks/useConfirmation';
import { useProcessingOverlay } from '../hooks/useProcessingOverlay';
import { exportCorrelationResultsToCSV, getExportStats } from '../utils/exportUtils';

interface MissionDetailProps {
    missions: Mission[];
    setMissions: React.Dispatch<React.SetStateAction<Mission[]>>;
}

// Función utilitaria para determinar el rol de una celda (originador/receptor)
// Utiliza hash determinístico basado en targetNumber + cellId para consistencia visual
const getCellRole = (targetNumber: string, cellId: string): 'originator' | 'receptor' => {
    const combined = `${targetNumber}-${cellId}`;
    let hash = 0;
    for (let i = 0; i < combined.length; i++) {
        const char = combined.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash) % 2 === 0 ? 'originator' : 'receptor';
};

const MissionDetail: React.FC<MissionDetailProps> = ({ missions, setMissions }) => {
    const { missionId } = useParams<{ missionId: string }>();
    const [activeTab, setActiveTab] = useState<'summary' | 'cellular' | 'analysis' | 'operator-data' | 'correlation'>('summary');
    const [analysisResults, setAnalysisResults] = useState<TargetRecord[]>([]);
    const [isAnalysisRunning, setIsAnalysisRunning] = useState(false);
    const [operatorSheets, setOperatorSheets] = useState<OperatorSheet[]>([]);
    const [isLoadingOperatorSheets, setIsLoadingOperatorSheets] = useState(false);
    
    // Estados para análisis de correlación
    const [correlationResults, setCorrelationResults] = useState<CorrelationResult[]>([]);
    const [isCorrelationRunning, setIsCorrelationRunning] = useState(false);
    const [correlationStartDate, setCorrelationStartDate] = useState('2021-05-20T10:00');
    const [correlationEndDate, setCorrelationEndDate] = useState('2021-05-20T14:30');
    const [minOccurrences, setMinOccurrences] = useState(1);
    const [phoneFilter, setPhoneFilter] = useState('');
    const [cellFilter, setCellFilter] = useState('');
    
    // Estados para paginación
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(25);
    
    const { showFileProcessingResult, showError, showSuccess } = useNotification();
    const { showConfirmation } = useConfirmation();
    
    // Hook para el overlay de procesamiento premium
    const {
        isProcessing,
        contextMessage,
        startProcessing,
        stopProcessing,
        handleCancel,
        handleTimeout,
        createCorrelationContext
    } = useProcessingOverlay();

    const mission = useMemo(() => missions.find(m => m.id === missionId), [missions, missionId]);

    // Cargar hojas de operador cuando cambie la misión
    useEffect(() => {
        if (mission?.id) {
            loadOperatorSheets();
        }
    }, [mission?.id]);

    const loadOperatorSheets = async () => {
        if (!mission?.id) return;
        
        setIsLoadingOperatorSheets(true);
        try {
            const sheets = await getOperatorSheets(mission.id);
            setOperatorSheets(sheets);
        } catch (error) {
            console.error('Error al cargar hojas de operador:', error);
        } finally {
            setIsLoadingOperatorSheets(false);
        }
    };

    const updateMissionState = (updatedMission: Mission) => {
        setMissions(currentMissions => 
            currentMissions.map(m => m.id === updatedMission.id ? updatedMission : m)
        );
    };

    const handleCellularUpload = async (file: File) => {
        if (mission) {
            const startTime = Date.now();
            try {
                const updatedMission = await uploadCellularData(mission.id, file);
                const processingTime = Date.now() - startTime;
                
                // Crear resultado del procesamiento para la notificación
                const result: FileProcessingResult = {
                    fileName: file.name,
                    fileType: 'SCANHUNTER',
                    processedRecords: updatedMission.cellularData?.length || 0,
                    failedRecords: 0,
                    processingTime
                };
                
                showFileProcessingResult(result, true);
                updateMissionState(updatedMission);
            } catch (error) {
                const processingTime = Date.now() - startTime;
                console.error('Error al subir datos celulares:', error);
                
                const result: FileProcessingResult = {
                    fileName: file.name,
                    fileType: 'SCANHUNTER',
                    processedRecords: 0,
                    failedRecords: 0,
                    processingTime,
                    errors: [(error as Error).message]
                };
                
                showFileProcessingResult(result, false);
            }
        }
    };
    

    const handleClearCellularData = async () => {
        if (!mission) return;
        
        const recordCount = mission.cellularData?.length || 0;
        const confirmed = await showConfirmation(
            confirmationPresets.clearCellularData(recordCount)
        );
        
        if (confirmed) {
            try {
                const updatedMission = await clearCellularDataApi(mission.id);
                updateMissionState(updatedMission);
                showSuccess("Datos Eliminados", "Los datos celulares han sido eliminados exitosamente");
            } catch (error) {
                console.error('Error al limpiar datos celulares:', error);
                showError("Error al Limpiar", `Error al limpiar datos: ${(error as Error).message}`);
            }
        }
    };

    const handleRunAnalysis = async () => {
        if (!mission.id) return;
        
        setIsAnalysisRunning(true);
        const startTime = Date.now();
        
        try {
            const results = await runAnalysis(mission.id);
            const processingTime = Date.now() - startTime;
            
            setAnalysisResults(results);
            
            if (results.length > 0) {
                showSuccess(
                    "Análisis Completado", 
                    `Se encontraron ${results.length} posible(s) objetivo(s) en ${(processingTime / 1000).toFixed(1)}s`
                );
            } else {
                showSuccess(
                    "Análisis Completado", 
                    `No se encontraron objetivos potenciales. Tiempo: ${(processingTime / 1000).toFixed(1)}s`
                );
            }
        } catch (error) {
            showError("Error en Análisis", `Error al ejecutar análisis: ${(error as Error).message}`);
        } finally {
            setIsAnalysisRunning(false);
        }
    };

    // Handlers para datos de operador
    const handleOperatorUploadSuccess = (response: OperatorUploadResponse) => {
        console.log('🎉 MISSION DETAIL: handleOperatorUploadSuccess llamado');
        console.log('📥 MISSION DETAIL: Response completa:', response);
        
        // Extraer información para crear el resultado
        const fileName = response.sheetId || 'archivo_operador';
        const processedRecords = response.processedRecords || 0;
        const failedRecords = response.records_failed || response.errors?.length || 0;
        const duplicatedRecords = response.records_duplicated || 0;
        const validationFailures = response.records_validation_failed || 0;
        const otherErrors = response.records_other_errors || 0;
        const warnings = response.warnings || [];
        const errors = response.errors || [];
        
        const result: FileProcessingResult = {
            fileName,
            fileType: 'OPERADOR',
            processedRecords,
            failedRecords,
            duplicatedRecords,      // NUEVO: incluir duplicados
            validationFailures,     // NUEVO: incluir errores de validación
            otherErrors,           // NUEVO: incluir otros errores
            processingTime: 0, // No tenemos tiempo en la respuesta
            warnings: warnings.length > 0 ? warnings : undefined,
            errors: errors.length > 0 ? errors : undefined,
            additionalInfo: response.details  // Incluir análisis de duplicados
        };
        
        showFileProcessingResult(result, response.success);
        loadOperatorSheets(); // Recargar la lista de hojas
    };

    const handleOperatorUploadError = (error: string) => {
        showError("Error de Carga de Operador", error);
    };

    const handleDeleteOperatorSheet = async (sheetId: string) => {
        if (!mission?.id) return;
        await deleteOperatorSheet(mission.id, sheetId);
    };

    // Función auxiliar para normalizar datos del backend (snake_case a camelCase)
    const normalizeCorrelationResult = (rawResult: any): CorrelationResult => {
        return {
            // Mapear campos del backend dinámico (snake_case) al frontend (camelCase)
            targetNumber: rawResult.targetNumber || rawResult.numero_objetivo || 'N/A',
            operator: rawResult.operator || rawResult.operador || 'DESCONOCIDO',
            occurrences: rawResult.occurrences || rawResult.ocurrencias || 0,
            firstDetection: rawResult.firstDetection || rawResult.primera_deteccion || new Date().toISOString(),
            lastDetection: rawResult.lastDetection || rawResult.ultima_deteccion || new Date().toISOString(),
            relatedCells: rawResult.relatedCells || rawResult.celdas_relacionadas || [],
            confidence: rawResult.confidence || rawResult.nivel_confianza || 0
        };
    };

    // Función para manejar el análisis de correlación
    const handleRunCorrelation = async () => {
        if (!mission.id) return;
        
        // Validar campos de fecha
        if (!correlationStartDate || !correlationEndDate) {
            showError("Campos Requeridos", "Por favor ingrese las fechas de inicio y fin");
            return;
        }
        
        // Validar que fecha fin sea mayor que fecha inicio
        if (new Date(correlationEndDate) <= new Date(correlationStartDate)) {
            showError("Rango Inválido", "La fecha de fin debe ser posterior a la fecha de inicio");
            return;
        }
        
        // Validar rango máximo de 7 días
        const diffTime = Math.abs(new Date(correlationEndDate).getTime() - new Date(correlationStartDate).getTime());
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        if (diffDays > 7) {
            showError("Rango Muy Amplio", "El rango de fechas no debe exceder 7 días para un mejor rendimiento");
            return;
        }
        
        setIsCorrelationRunning(true);
        
        // Calcular información contextual para el overlay
        const totalRecords = operatorSheets.reduce((sum, sheet) => sum + sheet.processedRecords, 0);
        const primaryOperator = operatorSheets.length > 0 ? operatorSheets[0].operator : 'MÚLTIPLES';
        
        // Crear contexto para el overlay premium
        const processingContext = createCorrelationContext(
            totalRecords,
            primaryOperator,
            correlationStartDate,
            correlationEndDate,
            minOccurrences > 1 ? minOccurrences : undefined
        );
        
        // Iniciar overlay de procesamiento
        startProcessing(processingContext);
        
        const startTime = Date.now();
        
        try {
            // Formatear fechas para el backend (agregar segundos)
            const startDateTime = correlationStartDate.replace('T', ' ') + ':00';
            const endDateTime = correlationEndDate.replace('T', ' ') + ':00';
            
            console.log('🔍 FRONTEND: Enviando solicitud de correlación:', {
                missionId: mission.id,
                startDateTime,
                endDateTime,
                minOccurrences
            });
            
            const response = await analyzeCorrelation(mission.id, startDateTime, endDateTime, minOccurrences);
            const processingTime = Date.now() - startTime;
            
            console.log('📥 FRONTEND: Respuesta recibida del backend:', response);
            
            if (response.success) {
                // Normalizar datos del backend antes de guardar en estado
                const normalizedResults = (response.data || []).map(normalizeCorrelationResult);
                
                console.log('✅ FRONTEND: Datos normalizados:', normalizedResults.slice(0, 3)); // Solo primeros 3 para debug
                
                setCorrelationResults(normalizedResults);
                
                if (normalizedResults.length > 0) {
                    showSuccess(
                        "Correlación Completada", 
                        `Se encontraron ${normalizedResults.length} objetivo(s) correlacionados en ${(processingTime / 1000).toFixed(1)}s`
                    );
                } else {
                    showSuccess(
                        "Correlación Completada", 
                        `No se encontraron objetivos en el período especificado. Tiempo: ${(processingTime / 1000).toFixed(1)}s`
                    );
                }
            } else {
                showError("Error en Correlación", response.error || "Error desconocido al ejecutar la correlación");
            }
        } catch (error) {
            console.error('❌ FRONTEND: Error en correlación:', error);
            showError("Error en Correlación", `Error al ejecutar correlación: ${(error as Error).message}`);
        } finally {
            setIsCorrelationRunning(false);
            stopProcessing(); // Detener overlay de procesamiento premium
        }
    };

    // Función helper para obtener color del badge del operador
    const getOperatorBadgeColor = (operator: string): string => {
        const colors: {[key: string]: string} = {
            'CLARO': 'bg-blue-800 text-blue-200',
            'MOVISTAR': 'bg-green-800 text-green-200',
            'TIGO': 'bg-purple-800 text-purple-200',
            'WOM': 'bg-orange-800 text-orange-200',
            'MULTIPLE': 'bg-gray-800 text-gray-200'
        };
        return colors[operator] || 'bg-gray-800 text-gray-200';
    };

    // Función helper para obtener color del nivel de confianza
    const getConfidenceColor = (confidence: number): string => {
        if (confidence >= 80) return 'bg-green-600';
        if (confidence >= 60) return 'bg-yellow-600';
        return 'bg-red-600';
    };

    // Función helper para formatear fecha/hora
    const formatDateTime = (dateStr: string): string => {
        const date = new Date(dateStr);
        return date.toLocaleString('es-ES', { 
            day: '2-digit', 
            month: '2-digit', 
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    // Función para filtrar resultados de correlación con validación defensiva
    const getFilteredResults = (): CorrelationResult[] => {
        let filtered = [...correlationResults];
        
        // Filtrar por números de teléfono
        if (phoneFilter.trim()) {
            const phoneNumbers = phoneFilter.split(',').map(p => p.trim().toLowerCase());
            filtered = filtered.filter(result => 
                phoneNumbers.some(phone => 
                    result.targetNumber?.toLowerCase().includes(phone) || false
                )
            );
        }
        
        // Filtrar por celdas con validación defensiva
        if (cellFilter.trim()) {
            const cells = cellFilter.split(',').map(c => c.trim().toLowerCase());
            filtered = filtered.filter(result => 
                cells.some(cell => 
                    (result.relatedCells || []).some(relatedCell => 
                        relatedCell?.toLowerCase().includes(cell) || false
                    )
                )
            );
        }
        
        return filtered;
    };

    // Función para obtener resultados paginados
    const getPaginatedResults = (): CorrelationResult[] => {
        const filteredResults = getFilteredResults();
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = startIndex + itemsPerPage;
        return filteredResults.slice(startIndex, endIndex);
    };

    // Función para manejar cambio de página
    const handlePageChange = (page: number) => {
        setCurrentPage(page);
        // Opcional: scroll suave al inicio de la tabla
        document.querySelector('[data-correlation-table]')?.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
        });
    };

    // Función para manejar cambio de elementos por página
    const handleItemsPerPageChange = (items: number) => {
        setItemsPerPage(items);
        // Reset a página 1 cuando cambie el número de elementos
        setCurrentPage(1);
    };

    // Función para manejar exportación completa (independiente de paginación)
    const handleExportResults = () => {
        const allResults = correlationResults; // TODOS los resultados (sin paginar)
        const filteredResults = getFilteredResults(); // Resultados filtrados
        
        try {
            const exportInfo = exportCorrelationResultsToCSV(allResults, filteredResults);
            
            if (exportInfo) {
                const stats = getExportStats(allResults, filteredResults);
                
                // Mostrar notificación de éxito con detalles
                showSuccess(
                    "Exportación Completada", 
                    `Se exportaron ${exportInfo.exportedRecords} registros${
                        stats.isFiltered ? ` (de ${stats.totalOriginalResults} totales, aplicando filtros)` : ''
                    } al archivo ${exportInfo.filename}`
                );
                
                console.log('📊 Estadísticas de exportación:', stats);
            }
        } catch (error) {
            console.error('❌ Error en exportación:', error);
            showError("Error de Exportación", `Error al exportar datos: ${(error as Error).message}`);
        }
    };

    // Reset página cuando cambien los filtros
    useEffect(() => {
        setCurrentPage(1);
    }, [phoneFilter, cellFilter]);

    if (!mission) {
        return <Navigate to="/missions" replace />;
    }

    const TabButton: React.FC<{ tabId: typeof activeTab; children: React.ReactNode }> = ({ tabId, children }) => (
        <button
            onClick={() => setActiveTab(tabId)}
            className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${activeTab === tabId ? 'bg-primary text-white' : 'text-medium hover:bg-secondary-light'}`}
        >
            {children}
        </button>
    );
    
    const renderCellularDataContent = () => {
        const hasData = mission.cellularData && mission.cellularData.length > 0;
        return (
            <div>
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-xl font-semibold text-light">Datos de Recorrido de Red Celular</h3>
                    {hasData && <Button variant="danger" icon={ICONS.trash} onClick={handleClearCellularData}>Limpiar Datos</Button>}
                </div>
                
                {/* Indicadores estadísticos */}
                <CellularDataStats data={mission.cellularData || []} />
                
                {hasData ? (
                    <div className="overflow-x-auto">
                        <Table headers={['ID BD', 'ID Archivo', 'Punto', 'Coordenadas', 'MNC/MCC', 'Operador', 'RSSI', 'Tecnología', 'Cell ID', 'LAC/TAC', 'eNB', 'Canal', 'Comentario']}>
                            {mission.cellularData!.map(d => (
                                <tr key={d.id || d.fileRecordId} className="hover:bg-secondary-light">
                                    <td className="px-4 py-3 text-sm text-medium font-mono whitespace-nowrap">{d.id}</td>
                                    <td className="px-4 py-3 text-sm text-light font-medium whitespace-nowrap">{d.fileRecordId ?? '-'}</td>
                                    <td className="px-4 py-3 text-sm whitespace-nowrap">
                                        <PointChip 
                                            punto={d.punto}
                                            size="sm"
                                            showTooltip={true}
                                            tooltipInfo={`Punto HUNTER: ${d.punto} | Cell ID: ${d.cellId}`}
                                            showOrdinal={true}
                                        />
                                    </td>
                                    <td className="px-4 py-3 text-sm text-light">
                                        <div className="flex flex-col">
                                            <span className="font-mono text-xs">{d.lat}</span>
                                            <span className="font-mono text-xs text-medium">{d.lon}</span>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3 text-sm text-light font-mono whitespace-nowrap">{d.mncMcc}</td>
                                    <td className="px-4 py-3 text-sm text-light whitespace-nowrap">{d.operador}</td>
                                    <td className="px-4 py-3 text-sm text-light">
                                        <span className={`px-2 py-1 text-xs rounded font-medium ${d.rssi >= -70 ? 'bg-green-800 text-green-200' : d.rssi >= -85 ? 'bg-yellow-800 text-yellow-200' : 'bg-red-800 text-red-200'}`}>
                                            {d.rssi} dBm
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 text-sm text-light">
                                        <span className={`px-2 py-1 text-xs rounded ${d.tecnologia === '5G' ? 'bg-purple-800 text-purple-200' : d.tecnologia === 'LTE' ? 'bg-blue-800 text-blue-200' : d.tecnologia === 'UMTS' ? 'bg-orange-800 text-orange-200' : 'bg-gray-800 text-gray-200'}`}>
                                            {d.tecnologia}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 text-sm text-light font-mono whitespace-nowrap">{d.cellId}</td>
                                    <td className="px-4 py-3 text-sm text-medium font-mono">{d.lacTac || '-'}</td>
                                    <td className="px-4 py-3 text-sm text-medium font-mono">{d.enb || '-'}</td>
                                    <td className="px-4 py-3 text-sm text-medium font-mono">{d.channel || '-'}</td>
                                    <td className="px-4 py-3 text-sm text-medium max-w-xs truncate" title={d.comentario}>{d.comentario || '-'}</td>
                                </tr>
                            ))}
                        </Table>
                    </div>
                ) : (
                    <FileUpload 
                        title="Subir Sábana de Datos Celulares"
                        description="Arrastra y suelta o selecciona un archivo Excel/CSV para procesar."
                        onUpload={handleCellularUpload}
                        acceptedFileTypes=".csv,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    />
                )}
            </div>
        )
    }




    return (
        <div className="space-y-6">
            <div className="bg-secondary p-6 rounded-lg shadow-lg border border-secondary-light">
                <h2 className="text-2xl font-bold text-light">{mission.name}</h2>
                <p className="text-sm font-mono text-primary mt-1">{mission.code}</p>
                <p className="text-medium mt-2">{mission.description}</p>
            </div>

            <div className="bg-secondary rounded-lg shadow-lg border border-secondary-light">
                <div className="flex justify-between items-center p-4 border-b border-secondary-light">
                    <div className="flex space-x-2">
                        <TabButton tabId="summary">Resumen</TabButton>
                        <TabButton tabId="cellular">Datos Celulares</TabButton>
                        <TabButton tabId="operator-data">Datos de Operador</TabButton>
                        
                        {mission.cellularData && mission.cellularData.length > 0 && operatorSheets.length > 0 && (
                            <TabButton tabId="correlation">Análisis de Correlación</TabButton>
                        )}
                    </div>
                </div>

                <div className="p-6">
                    {activeTab === 'summary' && (
                        <div>
                            <h3 className="text-xl font-semibold text-light mb-4">Resumen de Datos</h3>
                            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                                <div className="bg-secondary-light p-4 rounded-md">
                                    <p className="text-sm text-medium">Registros de Datos Celulares</p>
                                    <p className="text-2xl font-bold text-light">{mission.cellularData?.length || 0}</p>
                                </div>
                                <div className="bg-secondary-light p-4 rounded-md">
                                    <p className="text-sm text-medium">Archivos de Operador</p>
                                    <p className="text-2xl font-bold text-light">{operatorSheets.length}</p>
                                </div>
                                <div className="bg-secondary-light p-4 rounded-md">
                                    <p className="text-sm text-medium">Registros de Operador</p>
                                    <p className="text-2xl font-bold text-light">
                                        {operatorSheets.reduce((sum, sheet) => sum + sheet.processedRecords, 0).toLocaleString()}
                                    </p>
                                </div>
                                <div className="bg-secondary-light p-4 rounded-md">
                                    <p className="text-sm text-medium">Operadores</p>
                                    <p className="text-2xl font-bold text-light">
                                        {new Set(operatorSheets.map(sheet => sheet.operator)).size}
                                    </p>
                                </div>
                            </div>
                            <div className="mt-6 space-y-2">
                                <p className="text-medium">
                                    Usa la pestaña "Datos Celulares" para subir archivos de recorridos de red celular.
                                </p>
                                <p className="text-medium">
                                    Usa la pestaña "Datos de Operador" para cargar y gestionar archivos CDR y de ubicación de operadores móviles.
                                </p>
                            </div>
                        </div>
                    )}

                    {activeTab === 'cellular' && renderCellularDataContent()}

                    {activeTab === 'operator-data' && (
                        <div className="space-y-6">
                            {/* Upload Section */}
                            <div className="bg-secondary-light p-4 rounded-lg">
                                <h3 className="text-lg font-semibold text-light mb-2">Cargar Datos de Operador</h3>
                                <p className="text-medium mb-4">
                                    Carga archivos CDR y de ubicación de operadores móviles como CLARO, MOVISTAR, TIGO y WOM.
                                </p>
                                <OperatorDataUpload
                                    missionId={mission.id}
                                    onUploadSuccess={handleOperatorUploadSuccess}
                                    onUploadError={handleOperatorUploadError}
                                />
                            </div>
                            
                            {/* Enhanced Data Viewer */}
                            <div>
                                <h3 className="text-xl font-semibold text-light mb-4">Archivos y Datos</h3>
                                {isLoadingOperatorSheets ? (
                                    <div className="text-center py-12">
                                        <div className="text-4xl text-primary mb-2">{ICONS.loading}</div>
                                        <p className="text-medium">Cargando archivos...</p>
                                    </div>
                                ) : (
                                    <OperatorDataViewer
                                        missionId={mission.id}
                                        sheets={operatorSheets}
                                        onRefresh={loadOperatorSheets}
                                        onDeleteSheet={handleDeleteOperatorSheet}
                                    />
                                )}
                            </div>
                        </div>
                    )}

                    {activeTab === 'analysis' && (
                        <div>
                            <div className="flex justify-between items-center mb-6">
                                <h3 className="text-xl font-semibold text-light">Análisis de Posibles Objetivos</h3>
                                <Button 
                                    variant="primary" 
                                    icon={ICONS.search} 
                                    onClick={handleRunAnalysis}
                                    disabled={isAnalysisRunning}
                                >
                                    {isAnalysisRunning ? 'Analizando...' : 'Ejecutar Análisis'}
                                </Button>
                            </div>

                            {analysisResults.length > 0 ? (
                                <div className="overflow-x-auto">
                                    <Table headers={['Número', 'Celdas Coincidentes', 'Confianza', 'Estado', 'Última Actividad', 'Notas']}>
                                        {analysisResults.map(target => (
                                            <tr key={target.id} className="hover:bg-secondary-light">
                                                <td className="px-4 py-3 text-sm text-light font-mono whitespace-nowrap">{target.targetNumber}</td>
                                                <td className="px-4 py-3 text-sm text-light">
                                                    <div className="flex flex-wrap gap-1">
                                                        {target.matchingCells.map((cell, idx) => (
                                                            <span key={idx} className="px-2 py-1 text-xs bg-primary/20 text-primary rounded">
                                                                {cell}
                                                            </span>
                                                        ))}
                                                    </div>
                                                </td>
                                                <td className="px-4 py-3 text-sm text-light">
                                                    <div className="flex items-center">
                                                        <div className="w-full bg-secondary-light rounded-full h-2 mr-3">
                                                            <div 
                                                                className={`h-2 rounded-full ${target.confidence >= 0.8 ? 'bg-green-600' : target.confidence >= 0.6 ? 'bg-yellow-600' : 'bg-red-600'}`}
                                                                style={{ width: `${target.confidence * 100}%` }}
                                                            />
                                                        </div>
                                                        <span className="text-xs font-mono">
                                                            {(target.confidence * 100).toFixed(0)}%
                                                        </span>
                                                    </div>
                                                </td>
                                                <td className="px-4 py-3 text-sm">
                                                    <span className={`px-2 py-1 text-xs rounded font-medium ${target.status === 'active' ? 'bg-green-800 text-green-200' : 'bg-gray-800 text-gray-200'}`}>
                                                        {target.status}
                                                    </span>
                                                </td>
                                                <td className="px-4 py-3 text-sm text-medium font-mono whitespace-nowrap">
                                                    {new Date(target.lastSeen).toLocaleDateString()}
                                                </td>
                                                <td className="px-4 py-3 text-sm text-medium max-w-xs truncate" title={target.notes}>
                                                    {target.notes || '-'}
                                                </td>
                                            </tr>
                                        ))}
                                    </Table>
                                </div>
                            ) : (
                                <div className="text-center py-12">
                                    <div className="text-6xl text-medium mb-4">{ICONS.search}</div>
                                    <p className="text-medium mb-4">No se han encontrado posibles objetivos</p>
                                    <p className="text-sm text-medium">Ejecuta el análisis para cruzar datos celulares con la base de datos de objetivos</p>
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === 'correlation' && (
                        <div>
                            {/* Header con título */}
                            <div className="mb-6">
                                <h3 className="text-xl font-semibold text-light mb-2">Análisis de Correlación</h3>
                                <p className="text-sm text-medium">Correlaciona datos HUNTER con registros de operadores para identificar objetivos potenciales</p>
                            </div>

                            {/* Formulario de parámetros */}
                            <div className="bg-secondary-light p-6 rounded-lg mb-6">
                                <h4 className="text-lg font-medium text-light mb-4">Parámetros de Correlación</h4>
                                
                                {/* ACTUALIZACIÓN UX BORIS: Cambio de grid a flexbox para alineación baseline */}
                                <div className="flex flex-wrap gap-4 mb-4 items-end">
                                    {/* Campo Fecha/Hora Inicio */}
                                    <div>
                                        <label className="block text-sm font-medium text-light mb-2">
                                            Fecha y Hora de Inicio
                                        </label>
                                        <input
                                            type="datetime-local"
                                            value={correlationStartDate}
                                            onChange={(e) => setCorrelationStartDate(e.target.value)}
                                            className="w-full px-3 py-2 bg-secondary border border-secondary-light rounded-md text-light focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                                        />
                                    </div>
                                    
                                    {/* Campo Fecha/Hora Fin */}
                                    <div>
                                        <label className="block text-sm font-medium text-light mb-2">
                                            Fecha y Hora de Fin
                                        </label>
                                        <input
                                            type="datetime-local"
                                            value={correlationEndDate}
                                            onChange={(e) => setCorrelationEndDate(e.target.value)}
                                            className="w-full px-3 py-2 bg-secondary border border-secondary-light rounded-md text-light focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                                        />
                                    </div>
                                    
                                    {/* Campo Mínimo de Ocurrencias */}
                                    <div>
                                        <label className="block text-sm font-medium text-light mb-2">
                                            Mínimo de Ocurrencias
                                        </label>
                                        <input
                                            type="number"
                                            min="1"
                                            value={minOccurrences}
                                            onChange={(e) => setMinOccurrences(parseInt(e.target.value) || 1)}
                                            className="w-full px-3 py-2 bg-secondary border border-secondary-light rounded-md text-light focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                                        />
                                    </div>
                                    
                                    {/* ACTUALIZACIÓN UX BORIS: Mismo estilo que "Exportar Resultados" */}
                                    <Button 
                                        variant="primary" 
                                        icon={ICONS.correlation}
                                        size="sm"
                                        onClick={handleRunCorrelation}
                                        loading={isCorrelationRunning}
                                        disabled={isCorrelationRunning}
                                    >
                                        {isCorrelationRunning ? 'Correlacionando...' : 'Ejecutar Correlación'}
                                    </Button>
                                </div>
                                
                                {/* Información adicional */}
                                <div className="text-sm text-medium space-y-1">
                                    <p>• La correlación analiza coincidencias entre Cell IDs de datos HUNTER y operadores</p>
                                    <p>• Se recomienda un período máximo de 7 días para mejor rendimiento</p>
                                    <p>• El mínimo de ocurrencias filtra resultados con pocas coincidencias</p>
                                </div>
                            </div>

                            {/* Resultados de correlación */}
                            {isCorrelationRunning && !isProcessing ? (
                                /* Loading básico solo si no está activo el overlay premium */
                                <div className="text-center py-16">
                                    <div className="text-6xl text-primary mb-4 animate-spin">{ICONS.loading}</div>
                                    <h4 className="text-xl font-semibold text-light mb-2">Procesando Correlación</h4>
                                    <p className="text-medium">Analizando datos HUNTER y operadores...</p>
                                </div>
                            ) : correlationResults.length > 0 ? (
                                <div>
                                    <div className="mb-4">
                                        <div className="flex justify-between items-center mb-4">
                                            <h4 className="text-lg font-medium text-light">
                                                Resultados: {getFilteredResults().length} de {correlationResults.length} objetivos
                                            </h4>
                                            <Button 
                                                variant="secondary" 
                                                icon={ICONS.download}
                                                size="sm"
                                                onClick={handleExportResults}
                                            >
                                                Exportar Resultados
                                            </Button>
                                        </div>
                                        
                                        {/* Filtros de búsqueda */}
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-secondary-light p-4 rounded-lg">
                                            <div>
                                                <label className="block text-sm font-medium text-light mb-2">
                                                    Filtrar por Números (separados por coma)
                                                </label>
                                                <input
                                                    type="text"
                                                    value={phoneFilter}
                                                    onChange={(e) => setPhoneFilter(e.target.value)}
                                                    placeholder="Ej: 3224274851, 3104277553"
                                                    className="w-full px-3 py-2 bg-secondary border border-secondary-light rounded-md text-light placeholder-medium focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                                                />
                                            </div>
                                            
                                            <div>
                                                <label className="block text-sm font-medium text-light mb-2">
                                                    Filtrar por Celdas (separadas por coma)
                                                </label>
                                                <input
                                                    type="text"
                                                    value={cellFilter}
                                                    onChange={(e) => setCellFilter(e.target.value)}
                                                    placeholder="Ej: 56124, 51438, 51203"
                                                    className="w-full px-3 py-2 bg-secondary border border-secondary-light rounded-md text-light placeholder-medium focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                                                />
                                            </div>
                                        </div>
                                        
                                        {/* Mensaje cuando no hay resultados después de filtrar */}
                                        {getFilteredResults().length === 0 && (phoneFilter || cellFilter) && (
                                            <div className="text-center py-4 text-medium">
                                                <p>No se encontraron resultados con los filtros aplicados</p>
                                                <button 
                                                    onClick={() => { setPhoneFilter(''); setCellFilter(''); }}
                                                    className="text-primary hover:underline mt-2"
                                                >
                                                    Limpiar filtros
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                    
                                    {/* Leyenda del Sistema Visual de Correlación - CORREGIDA UX */}
                                    {getFilteredResults().length > 0 && (
                                        <CorrelationLegend
                                            cellularData={mission.cellularData || []}
                                            correlationResults={getFilteredResults()}  // NUEVA PROP: Pasar resultados reales
                                            showStats={true}
                                            collapsible={true}
                                            defaultExpanded={true}
                                        />
                                    )}
                                    
                                    {/* Paginación superior */}
                                    <div className="mb-4">
                                        <Pagination
                                            currentPage={currentPage}
                                            totalItems={getFilteredResults().length}
                                            itemsPerPage={itemsPerPage}
                                            onPageChange={handlePageChange}
                                            onItemsPerPageChange={handleItemsPerPageChange}
                                        />
                                    </div>

                                    <div className="overflow-x-auto" data-correlation-table>
                                        <Table headers={[
                                            'Número Objetivo', 
                                            'Operador', 
                                            'Ocurrencias', 
                                            'Primera Detección', 
                                            'Última Detección', 
                                            'Celdas Relacionadas'
                                            // 'Nivel de Confianza' - OCULTA POR SOLICITUD DE BORIS
                                        ]}>
                                            {getPaginatedResults().map((result, index) => (
                                                <tr key={index} className="hover:bg-secondary-light">
                                                    {/* Número Objetivo */}
                                                    <td className="px-4 py-3 text-sm text-light font-mono font-bold">
                                                        {result.targetNumber}
                                                    </td>
                                                    
                                                    {/* Operador */}
                                                    <td className="px-4 py-3 text-sm text-light">
                                                        <span className={`px-2 py-1 text-xs rounded font-medium ${getOperatorBadgeColor(result.operator)}`}>
                                                            {result.operator}
                                                        </span>
                                                    </td>
                                                    
                                                    {/* Ocurrencias */}
                                                    <td className="px-4 py-3 text-sm text-center">
                                                        <span className="bg-primary/20 text-white px-2 py-1 rounded font-bold">
                                                            {result.occurrences}
                                                        </span>
                                                    </td>
                                                    
                                                    {/* Primera Detección */}
                                                    <td className="px-4 py-3 text-sm text-medium font-mono">
                                                        {formatDateTime(result.firstDetection)}
                                                    </td>
                                                    
                                                    {/* Última Detección */}
                                                    <td className="px-4 py-3 text-sm text-medium font-mono">
                                                        {formatDateTime(result.lastDetection)}
                                                    </td>
                                                    
                                                    {/* Celdas Relacionadas - Sistema visual con colores de puntos HUNTER */}
                                                    <td className="px-4 py-3 text-sm">
                                                        <CorrelationCellBadgeGroup
                                                            cellIds={result.relatedCells || []}
                                                            targetNumber={result.targetNumber}
                                                            cellularData={mission.cellularData || []}
                                                            maxDisplay={8}
                                                            getCellRole={getCellRole}
                                                            onCellClick={(cellId, punto) => {
                                                                console.log(`Clicked cell: ${cellId}, punto: ${punto}`);
                                                                // Aquí puedes agregar lógica adicional como resaltar filas relacionadas
                                                            }}
                                                        />
                                                    </td>
                                                    
                                                    {/* Nivel de Confianza - OCULTA POR SOLICITUD DE BORIS */}
                                                    {/* 
                                                    <td className="px-4 py-3 text-sm">
                                                        <div className="flex items-center">
                                                            <div className="w-16 bg-secondary-light rounded-full h-2 mr-2">
                                                                <div 
                                                                    className={`h-2 rounded-full ${getConfidenceColor(result.confidence)}`}
                                                                    style={{ width: `${result.confidence}%` }}
                                                                />
                                                            </div>
                                                            <span className="text-xs font-mono min-w-[3rem]">
                                                                {result.confidence.toFixed(1)}%
                                                            </span>
                                                        </div>
                                                    </td>
                                                    */}
                                                </tr>
                                            ))}
                                        </Table>
                                    </div>

                                    {/* Paginación inferior */}
                                    <div className="mt-4">
                                        <Pagination
                                            currentPage={currentPage}
                                            totalItems={getFilteredResults().length}
                                            itemsPerPage={itemsPerPage}
                                            onPageChange={handlePageChange}
                                            onItemsPerPageChange={handleItemsPerPageChange}
                                            showItemsPerPage={false} // Solo mostrar selector en la paginación superior
                                        />
                                    </div>
                                </div>
                            ) : (
                                <div className="text-center py-12">
                                    <div className="text-6xl text-medium mb-4">{ICONS.search}</div>
                                    <p className="text-medium mb-4">No se han ejecutado correlaciones</p>
                                    <p className="text-sm text-medium">Configure los parámetros y ejecute el análisis para encontrar correlaciones</p>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
            
            {/* Overlay de procesamiento premium */}
            <PremiumProcessingOverlay
                isVisible={isProcessing}
                contextMessage={contextMessage}
                onCancel={handleCancel}
                onTimeout={handleTimeout}
                timeoutDuration={180000} // 3 minutos
            />
        </div>
    );
};

export default MissionDetail;