import React, { useState, useMemo, useEffect } from 'react';
import { useParams, Navigate } from 'react-router-dom';
import type { Mission, TargetRecord, OperatorSheet, OperatorUploadResponse } from '../types';
import Button from '../components/ui/Button';
import Table from '../components/ui/Table';
import FileUpload from '../components/ui/FileUpload';
import { OperatorDataUpload, OperatorSheetsManager, OperatorDataViewer } from '../components/operator-data';
import { ICONS } from '../constants';
import { uploadCellularData, clearCellularDataApi, runAnalysis, getOperatorSheets, deleteOperatorSheet } from '../services/api';

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
            try {
                const updatedMission = await uploadCellularData(mission.id, file);
                updateMissionState(updatedMission);
            } catch (error) {
                console.error('Error al subir datos celulares:', error);
                alert(`Error al subir: ${(error as Error).message}`);
            }
        }
    };
    

    const handleClearCellularData = async () => {
        if(mission && window.confirm(`¿Estás seguro de que quieres borrar todos los datos celulares de esta misión? Esta acción no se puede deshacer.`)){
            try {
                const updatedMission = await clearCellularDataApi(mission.id);
                updateMissionState(updatedMission);
            } catch (error) {
                console.error('Error al limpiar datos celulares:', error);
                alert(`Error al limpiar: ${(error as Error).message}`);
            }
        }
    };

    const handleRunAnalysis = async () => {
        if (!mission.id) return;
        
        setIsAnalysisRunning(true);
        try {
            const results = await runAnalysis(mission.id);
            setAnalysisResults(results);
        } catch (error) {
            alert(`Error en análisis: ${(error as Error).message}`);
        } finally {
            setIsAnalysisRunning(false);
        }
    };

    // Handlers para datos de operador
    const handleOperatorUploadSuccess = (response: OperatorUploadResponse) => {
        console.log('🎉 MISSION DETAIL: handleOperatorUploadSuccess llamado');
        console.log('📥 MISSION DETAIL: Response completa:', response);
        console.log('📊 MISSION DETAIL: processedRecords value:', response.processedRecords);
        console.log('📊 MISSION DETAIL: processedRecords type:', typeof response.processedRecords);
        console.log('📊 MISSION DETAIL: response.success:', response.success);
        console.log('📊 MISSION DETAIL: response.message:', response.message);
        console.log('📊 MISSION DETAIL: response.error:', response.error);
        
        // Usar el mensaje apropiado según el estado de la respuesta
        const message = response.success ? response.message : response.error;
        const icon = response.success ? '✅' : '❌';
        
        alert(`${icon} ${message}\nRegistros procesados: ${response.processedRecords || 0}`);
        loadOperatorSheets(); // Recargar la lista de hojas
    };

    const handleOperatorUploadError = (error: string) => {
        alert(`❌ Error en la carga: ${error}`);
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
                {hasData ? (
                    <div className="overflow-x-auto">
                        <Table headers={['Punto', 'Coordenadas', 'MNC/MCC', 'Operador', 'RSSI', 'Tecnología', 'Cell ID', 'LAC/TAC', 'eNB', 'Canal', 'Comentario']}>
                            {mission.cellularData!.map(d => (
                                <tr key={d.id} className="hover:bg-secondary-light">
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