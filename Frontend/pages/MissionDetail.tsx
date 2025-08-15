import React, { useState, useMemo, useEffect } from 'react';
import { useParams, Navigate } from 'react-router-dom';
import type { Mission, TargetRecord, OperatorSheet, OperatorUploadResponse, FileProcessingResult } from '../types';
import Button from '../components/ui/Button';
import Table from '../components/ui/Table';
import FileUpload from '../components/ui/FileUpload';
import CellularDataStats from '../components/ui/CellularDataStats';
import { OperatorDataUpload, OperatorSheetsManager, OperatorDataViewer } from '../components/operator-data';
import { ICONS } from '../constants';
import { uploadCellularData, clearCellularDataApi, runAnalysis, getOperatorSheets, deleteOperatorSheet } from '../services/api';
import { useNotification } from '../hooks/useNotification';
import { useConfirmation, confirmationPresets } from '../hooks/useConfirmation';

interface MissionDetailProps {
    missions: Mission[];
    setMissions: React.Dispatch<React.SetStateAction<Mission[]>>;
}

const MissionDetail: React.FC<MissionDetailProps> = ({ missions, setMissions }) => {
    const { missionId } = useParams<{ missionId: string }>();
    const [activeTab, setActiveTab] = useState<'summary' | 'cellular' | 'analysis' | 'operator-data'>('summary');
    const [analysisResults, setAnalysisResults] = useState<TargetRecord[]>([]);
    const [isAnalysisRunning, setIsAnalysisRunning] = useState(false);
    const [operatorSheets, setOperatorSheets] = useState<OperatorSheet[]>([]);
    const [isLoadingOperatorSheets, setIsLoadingOperatorSheets] = useState(false);
    
    const { showFileProcessingResult, showError, showSuccess } = useNotification();
    const { showConfirmation } = useConfirmation();

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
                                    <td className="px-4 py-3 text-sm text-light font-medium whitespace-nowrap">{d.punto}</td>
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
                        {mission.cellularData && mission.cellularData.length > 0 && (
                            <TabButton tabId="analysis">Posibles Objetivos</TabButton>
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
                </div>
            </div>
        </div>
    );
};

export default MissionDetail;