import React, { useState, useEffect } from 'react';
import { ICONS } from '../../constants';
import { getPointColor } from '../../utils/colorSystem';
import PhoneCorrelationViewer from './PhoneCorrelationViewer';

// Interfaces para TypeScript
interface CallInteraction {
    originador: string;
    receptor: string;
    fecha_hora: string;
    duracion: number;
    operador: string;
    celda_origen: string;
    celda_destino: string;
    latitud_origen?: number;
    longitud_origen?: number;
    latitud_destino?: number;
    longitud_destino?: number;
    // Campos HUNTER opcionales para compatibilidad
    punto_hunter_origen?: string;
    lat_hunter_origen?: number;
    lon_hunter_origen?: number;
    punto_hunter_destino?: string;
    lat_hunter_destino?: number;
    lon_hunter_destino?: number;
    // Campo HUNTER unificado del backend (COALESCE destino, origen)
    punto_hunter?: string;
    // Coordenadas GPS del punto HUNTER unificado
    lat_hunter?: number;
    lon_hunter?: number;
    // Campos direccionales del backend (CORRECCIÓN BORIS)
    hunter_source?: string;        // 'origen_direccional' | 'destino_direccional' | 'origen_fallback' | 'destino_fallback' | 'sin_ubicacion'
    precision_ubicacion?: string;  // 'ALTA' | 'MEDIA' | 'SIN_DATOS'
}

interface TableCorrelationModalProps {
    isOpen: boolean;
    onClose: () => void;
    targetNumber: string;
    missionId: string;
    startDate: string;
    endDate: string;
}

const TableCorrelationModal: React.FC<TableCorrelationModalProps> = ({
    isOpen,
    onClose,
    targetNumber,
    missionId,
    startDate,
    endDate
}) => {
    const [interactions, setInteractions] = useState<CallInteraction[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    
    // Estados para paginación
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 7; // OPTIMIZACIÓN BORIS: Modal más compacto, paginación a partir de 8 registros
    
    // Estado para el diagrama de correlación
    const [showDiagram, setShowDiagram] = useState(false);

    // Calcular paginación
    const totalPages = Math.ceil(interactions.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const paginatedInteractions = interactions.slice(startIndex, startIndex + itemsPerPage);

    // Función para cargar interacciones
    const loadInteractions = async () => {
        setLoading(true);
        setError(null);
        
        try {
            console.log(`🔍 Cargando interacciones para ${targetNumber}`);
            console.log(`📊 Parámetros enviados al backend:`, {
                missionId,
                targetNumber,
                startDate,
                endDate
            });
            
            // Validar parámetros antes de enviar
            if (!missionId || !targetNumber || !startDate || !endDate) {
                throw new Error(`Parámetros inválidos: missionId=${missionId}, targetNumber=${targetNumber}, startDate=${startDate}, endDate=${endDate}`);
            }
            
            // Llamar al endpoint del backend
            const result = await window.eel.get_call_interactions(
                missionId,
                targetNumber,
                startDate,
                endDate
            )();
            
            console.log(`✅ Encontradas ${result.length} interacciones telefónicas`);
            setInteractions(result);
            setCurrentPage(1); // Reset a primera página
            
        } catch (err) {
            console.error('❌ Error al cargar interacciones:', err);
            setError('Error al cargar las interacciones telefónicas');
            setInteractions([]);
        } finally {
            setLoading(false);
        }
    };

    // Cargar datos cuando se abre el modal
    useEffect(() => {
        if (isOpen && targetNumber && missionId) {
            loadInteractions();
        }
    }, [isOpen, targetNumber, missionId, startDate, endDate]);

    // Formatear duración (segundos a mm:ss)
    const formatDuration = (seconds: number): string => {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    };

    // Formatear fecha (DD/MM/YYYY HH:mm)
    const formatDateTime = (dateTimeStr: string): string => {
        try {
            const date = new Date(dateTimeStr);
            const day = date.getDate().toString().padStart(2, '0');
            const month = (date.getMonth() + 1).toString().padStart(2, '0');
            const year = date.getFullYear();
            const hours = date.getHours().toString().padStart(2, '0');
            const minutes = date.getMinutes().toString().padStart(2, '0');
            
            return `${day}/${month}/${year} ${hours}:${minutes}`;
        } catch {
            return dateTimeStr;
        }
    };

    // Determinar si es llamada saliente o entrante
    const getCallDirection = (originador: string, receptor: string) => {
        const isOutgoing = originador === targetNumber;
        return {
            isOutgoing,
            icon: isOutgoing ? '📤' : '📥',
            label: isOutgoing ? 'Saliente' : 'Entrante',
            otherNumber: isOutgoing ? receptor : originador
        };
    };

    // Sistema de mapeo direccional HUNTER - CORRECCIÓN BORIS TOOLTIP DINÁMICO
    const getDirectionalMapping = (hunterSource: string, precisionUbicacion: string) => {
        const sourceMappings = {
            'origen_direccional': {
                type: 'origen' as const,
                icon: '🎯',
                description: 'Ubicación real del objetivo (origen)',
                tooltip: 'El número objetivo estaba en esta ubicación durante la llamada',
                precision: 'ALTA'
            },
            'destino_direccional': {
                type: 'destino' as const,
                icon: '🎯', 
                description: 'Ubicación real del objetivo (destino)',
                tooltip: 'El número objetivo estaba en esta ubicación durante la llamada',
                precision: 'ALTA'
            },
            'origen_fallback': {
                type: 'origen' as const,
                icon: '📍',
                description: 'Fallback a origen (destino sin datos)',
                tooltip: 'Ubicación aproximada - datos de celda origen',
                precision: 'MEDIA'
            },
            'destino_fallback': {
                type: 'destino' as const,
                icon: '📍',
                description: 'Fallback a destino (origen sin datos)', 
                tooltip: 'Ubicación aproximada - datos de celda destino',
                precision: 'MEDIA'
            },
            'sin_ubicacion': {
                type: 'ninguno' as const,
                icon: '❓',
                description: 'Sin datos HUNTER disponibles',
                tooltip: 'No hay información de ubicación disponible',
                precision: 'SIN_DATOS'
            }
        };

        return sourceMappings[hunterSource as keyof typeof sourceMappings] || sourceMappings['sin_ubicacion'];
    };

    // Función mejorada para obtener el punto HUNTER con coordenadas GPS - USA DATOS DIRECCIONALES DEL BACKEND
    // Corrige problema de tooltip hardcodeado usando hunter_source del backend
    const getHunterPoint = (interaction: CallInteraction, targetNumber: string): { 
        point: string; 
        coordinates: string;
        fullDisplay: string;
        source: 'destino' | 'origen' | 'ninguno';
        icon: string;
        tooltip: string;
        hasCoordinates: boolean;
        lat?: number;
        lon?: number;
    } => {
        // Función auxiliar para formatear coordenadas con precisión - MANEJO STRINGS Y NÚMEROS
        const formatCoordinates = (lat?: number | string, lon?: number | string): string => {
            // Convertir strings a números si es necesario (backend retorna strings)
            const latNum = typeof lat === 'string' ? parseFloat(lat) : lat;
            const lonNum = typeof lon === 'string' ? parseFloat(lon) : lon;
            
            // Validación defensiva: verificar que ambos valores existan y sean números válidos
            if (latNum == null || lonNum == null || 
                typeof latNum !== 'number' || typeof lonNum !== 'number' ||
                isNaN(latNum) || isNaN(lonNum)) {
                return '';
            }
            return `(${latNum.toFixed(5)}, ${lonNum.toFixed(5)})`;
        };

        // Prioridad 1: Usar datos direccionales del backend (CORRECCIÓN BORIS)
        if (interaction.punto_hunter) {
            // Obtener mapeo direccional basado en hunter_source del backend
            const hunterSource = interaction.hunter_source || 'sin_ubicacion';
            const precisionUbicacion = interaction.precision_ubicacion || 'SIN_DATOS';
            const directionalInfo = getDirectionalMapping(hunterSource, precisionUbicacion);
            
            const coordinates = formatCoordinates(interaction.lat_hunter, interaction.lon_hunter);
            const hasCoordinates = interaction.lat_hunter !== undefined && interaction.lon_hunter !== undefined;
            
            return {
                point: interaction.punto_hunter,
                coordinates,
                fullDisplay: hasCoordinates ? `${interaction.punto_hunter}\n${coordinates}` : interaction.punto_hunter,
                source: directionalInfo.type,
                icon: directionalInfo.icon,
                tooltip: directionalInfo.tooltip,
                hasCoordinates,
                lat: interaction.lat_hunter,
                lon: interaction.lon_hunter
            };
        }
        
        // Prioridad 2: Lógica manual para compatibilidad (casos donde punto_hunter no existe)
        // Usar sistema direccional también para campos individuales (fallback legacy)
        if (interaction.punto_hunter_destino) {
            const coordinates = formatCoordinates(interaction.lat_hunter_destino, interaction.lon_hunter_destino);
            const hasCoordinates = interaction.lat_hunter_destino !== undefined && interaction.lon_hunter_destino !== undefined;
            const fallbackInfo = getDirectionalMapping('destino_fallback', 'MEDIA');
            
            return {
                point: interaction.punto_hunter_destino,
                coordinates,
                fullDisplay: hasCoordinates ? `${interaction.punto_hunter_destino}\n${coordinates}` : interaction.punto_hunter_destino,
                source: fallbackInfo.type,
                icon: fallbackInfo.icon,
                tooltip: fallbackInfo.tooltip,
                hasCoordinates,
                lat: interaction.lat_hunter_destino,
                lon: interaction.lon_hunter_destino
            };
        }
        
        if (interaction.punto_hunter_origen) {
            const coordinates = formatCoordinates(interaction.lat_hunter_origen, interaction.lon_hunter_origen);
            const hasCoordinates = interaction.lat_hunter_origen !== undefined && interaction.lon_hunter_origen !== undefined;
            const fallbackInfo = getDirectionalMapping('origen_fallback', 'MEDIA');
            
            return {
                point: interaction.punto_hunter_origen,
                coordinates,
                fullDisplay: hasCoordinates ? `${interaction.punto_hunter_origen}\n${coordinates}` : interaction.punto_hunter_origen,
                source: fallbackInfo.type,
                icon: fallbackInfo.icon,
                tooltip: fallbackInfo.tooltip,
                hasCoordinates,
                lat: interaction.lat_hunter_origen,
                lon: interaction.lon_hunter_origen
            };
        }
        
        // Sin datos HUNTER disponibles
        const noDataInfo = getDirectionalMapping('sin_ubicacion', 'SIN_DATOS');
        return {
            point: 'N/A',
            coordinates: '',
            fullDisplay: 'N/A',
            source: noDataInfo.type,
            icon: noDataInfo.icon,
            tooltip: noDataInfo.tooltip,
            hasCoordinates: false
        };
    };

    // Funciones de exportación
    const exportToCSV = () => {
        try {
            const headers = [
                'Dirección',
                'Originador', 
                'Receptor',
                'Fecha y Hora',
                'Duración (s)',
                'Punto HUNTER',
                'Latitud HUNTER',
                'Longitud HUNTER',
                'Operador',
                'Celda Origen',
                'Celda Destino'
            ];
            
            const csvContent = [
                headers.join(','),
                ...interactions.map(interaction => {
                    const direction = getCallDirection(interaction.originador, interaction.receptor);
                    const hunterData = getHunterPoint(interaction, targetNumber);
                    return [
                        `"${direction.label}"`,
                        `"${interaction.originador}"`,
                        `"${interaction.receptor}"`,
                        `"${formatDateTime(interaction.fecha_hora)}"`,
                        `"${formatDuration(interaction.duracion)} (${interaction.duracion}s)"`,
                        `"${hunterData.point}"`,
                        (() => {
                            const latNum = typeof hunterData.lat === 'string' ? parseFloat(hunterData.lat) : hunterData.lat;
                            return latNum !== undefined && !isNaN(latNum) ? latNum.toFixed(5) : '';
                        })(),
                        (() => {
                            const lonNum = typeof hunterData.lon === 'string' ? parseFloat(hunterData.lon) : hunterData.lon;
                            return lonNum !== undefined && !isNaN(lonNum) ? lonNum.toFixed(5) : '';
                        })(),
                        `"${interaction.operador}"`,
                        `"${interaction.celda_origen}"`,
                        `"${interaction.celda_destino}"`
                    ].join(',');
                })
            ].join('\n');
            
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', `tabla_correlacion_${targetNumber}_${new Date().toISOString().split('T')[0]}.csv`);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            console.log(`📊 Exportación CSV completada: ${interactions.length} registros`);
        } catch (error) {
            console.error('❌ Error al exportar CSV:', error);
        }
    };

    const exportToExcel = () => {
        try {
            const headers = [
                'Dirección',
                'Originador', 
                'Receptor',
                'Fecha y Hora',
                'Duración (s)',
                'Punto HUNTER',
                'Latitud HUNTER',
                'Longitud HUNTER',
                'Operador',
                'Celda Origen',
                'Celda Destino'
            ];
            
            const excelData = [
                headers,
                ...interactions.map(interaction => {
                    const direction = getCallDirection(interaction.originador, interaction.receptor);
                    const hunterData = getHunterPoint(interaction, targetNumber);
                    return [
                        direction.label,
                        interaction.originador,
                        interaction.receptor,
                        formatDateTime(interaction.fecha_hora),
                        `"${formatDuration(interaction.duracion)} (${interaction.duracion}s)"`,
                        hunterData.point,
                        (() => {
                            const latNum = typeof hunterData.lat === 'string' ? parseFloat(hunterData.lat) : hunterData.lat;
                            return latNum !== undefined && !isNaN(latNum) ? latNum.toFixed(5) : '';
                        })(),
                        (() => {
                            const lonNum = typeof hunterData.lon === 'string' ? parseFloat(hunterData.lon) : hunterData.lon;
                            return lonNum !== undefined && !isNaN(lonNum) ? lonNum.toFixed(5) : '';
                        })(),
                        interaction.operador,
                        interaction.celda_origen,
                        interaction.celda_destino
                    ];
                })
            ];
            
            // Crear tabla HTML para Excel
            const excelContent = `
                <table>
                    ${excelData.map(row => 
                        `<tr>${row.map(cell => `<td>${cell}</td>`).join('')}</tr>`
                    ).join('')}
                </table>
            `;
            
            const blob = new Blob([excelContent], { type: 'application/vnd.ms-excel' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', `tabla_correlacion_${targetNumber}_${new Date().toISOString().split('T')[0]}.xls`);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            console.log(`📑 Exportación Excel completada: ${interactions.length} registros`);
        } catch (error) {
            console.error('❌ Error al exportar Excel:', error);
        }
    };

    // Manejar tecla ESC
    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                onClose();
            }
        };

        if (isOpen) {
            document.addEventListener('keydown', handleEscape);
        }

        return () => document.removeEventListener('keydown', handleEscape);
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    return (
        <div 
            className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
            onClick={onClose}
        >
            <div 
                className="bg-secondary rounded-xl shadow-2xl w-full max-w-6xl max-h-[90vh] flex flex-col border border-secondary-light"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-secondary-light">
                    <div>
                        <h2 className="text-xl font-semibold text-white">
                            Tabla de Correlación - <span className="text-cyan-300 font-bold">{targetNumber}</span>
                        </h2>
                        <p className="text-sm text-gray-400 mt-1">
                            Interacciones telefónicas encontradas: {interactions.length}
                        </p>
                    </div>
                    
                    {/* Toolbar */}
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => exportToCSV()}
                            disabled={interactions.length === 0 || loading}
                            className="group relative flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <span className="text-sm">📊</span>
                            <span className="text-sm font-medium">CSV</span>
                            
                            {/* Tooltip */}
                            <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
                                Exportar a CSV
                            </div>
                        </button>
                        
                        <button
                            onClick={() => exportToExcel()}
                            disabled={interactions.length === 0 || loading}
                            className="group relative flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <span className="text-sm">📑</span>
                            <span className="text-sm font-medium">Excel</span>
                            
                            {/* Tooltip */}
                            <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
                                Exportar a Excel
                            </div>
                        </button>
                        <button
                            onClick={loadInteractions}
                            disabled={loading}
                            className="group relative flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary-light text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <span className={`text-sm ${loading ? 'animate-spin' : ''}`}>
                                {loading ? '⟳' : '🔄'}
                            </span>
                            <span className="text-sm font-medium">
                                {loading ? 'Cargando...' : 'Refrescar'}
                            </span>
                            
                            {/* Tooltip */}
                            <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
                                Actualizar datos de interacciones
                            </div>
                        </button>
                        
                        <button
                            onClick={() => setShowDiagram(true)}
                            disabled={interactions.length === 0 || loading}
                            className="group relative flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <span className="text-sm">🕸️</span>
                            <span className="text-sm font-medium">Diagrama</span>
                            
                            {/* Tooltip */}
                            <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
                                Visualizar Diagrama de Correlación
                            </div>
                        </button>
                        
                        <button
                            onClick={onClose}
                            className="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-white hover:bg-secondary-light rounded-lg transition-colors"
                        >
                            ✕
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-hidden flex flex-col">
                    {loading ? (
                        <div className="flex-1 flex items-center justify-center">
                            <div className="text-center">
                                <div className="animate-spin text-3xl mb-4">⟳</div>
                                <p className="text-gray-300">Cargando interacciones...</p>
                            </div>
                        </div>
                    ) : error ? (
                        <div className="flex-1 flex items-center justify-center">
                            <div className="text-center">
                                <div className="text-red-400 text-3xl mb-4">⚠️</div>
                                <p className="text-red-300">{error}</p>
                                <button
                                    onClick={loadInteractions}
                                    className="mt-4 px-4 py-2 bg-primary hover:bg-primary-light text-white rounded-lg transition-colors"
                                >
                                    Intentar nuevamente
                                </button>
                            </div>
                        </div>
                    ) : interactions.length === 0 ? (
                        <div className="flex-1 flex items-center justify-center">
                            <div className="text-center">
                                <div className="text-gray-400 text-3xl mb-4">📱</div>
                                <p className="text-gray-300">No se encontraron interacciones telefónicas</p>
                                <p className="text-gray-400 text-sm mt-2">
                                    para el número {targetNumber} en el período seleccionado
                                </p>
                            </div>
                        </div>
                    ) : (
                        <>
                            {/* Tabla */}
                            <div className="flex-1 overflow-auto" style={{ margin: '5px 10px' }}>
                                <table className="w-full">
                                    <thead className="bg-secondary-light sticky top-0">
                                        <tr>
                                            <th className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                                                Dirección
                                            </th>
                                            <th className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                                                Originador
                                            </th>
                                            <th className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                                                Receptor
                                            </th>
                                            <th className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                                                Fecha y Hora
                                            </th>
                                            <th className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider min-w-[120px]">
                                                Duración
                                            </th>
                                            <th className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                                                Punto HUNTER
                                            </th>
                                            <th className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                                                Latitud GPS
                                            </th>
                                            <th className="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                                                Longitud GPS
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-secondary-light">
                                        {paginatedInteractions.map((interaction, index) => {
                                            const direction = getCallDirection(interaction.originador, interaction.receptor);
                                            return (
                                                <tr 
                                                    key={index} 
                                                    className="hover:bg-secondary-light transition-colors"
                                                >
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <div className="flex items-center gap-2">
                                                            <span className="text-lg">{direction.icon}</span>
                                                            <span className={`text-sm font-medium ${
                                                                direction.isOutgoing 
                                                                    ? 'text-green-400' 
                                                                    : 'text-blue-400'
                                                            }`}>
                                                                {direction.label}
                                                            </span>
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <div className={`text-sm font-mono ${
                                                            interaction.originador === targetNumber 
                                                                ? 'text-cyan-300 font-bold' 
                                                                : 'text-white'
                                                        }`}>
                                                            {interaction.originador}
                                                        </div>
                                                        <div className="text-xs text-gray-400">
                                                            {interaction.operador}
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <div className={`text-sm font-mono ${
                                                            interaction.receptor === targetNumber 
                                                                ? 'text-cyan-300 font-bold' 
                                                                : 'text-white'
                                                        }`}>
                                                            {interaction.receptor}
                                                        </div>
                                                        <div className="text-xs text-gray-400">
                                                            Celda: {interaction.celda_destino}
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <div className="text-sm text-white">
                                                            {formatDateTime(interaction.fecha_hora)}
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap min-w-[150px]">
                                                        <div className="text-sm text-white font-mono whitespace-nowrap">
                                                            {formatDuration(interaction.duracion)} ({interaction.duracion}s)
                                                        </div>
                                                    </td>
                                                    <td className="px-6 py-4">
                                                        {(() => {
                                                            const hunterData = getHunterPoint(interaction, targetNumber);
                                                            return (
                                                                <div className="flex items-start gap-2 group relative">
                                                                    {/* Icono indicador del origen del dato */}
                                                                    <span className="text-sm mt-0.5" title={hunterData.tooltip}>
                                                                        {hunterData.icon}
                                                                    </span>
                                                                    
                                                                    {/* Punto HUNTER con coordenadas */}
                                                                    <div className="min-w-0 flex-1">
                                                                        {/* Descripción del punto */}
                                                                        <div className={`text-sm font-medium leading-tight ${
                                                                            hunterData.point === 'N/A' 
                                                                                ? 'text-gray-500' 
                                                                                : getPointColor(hunterData.point).text // Color determinístico del sistema
                                                                        }`}>
                                                                            {hunterData.point}
                                                                        </div>
                                                                        
                                                                        
                                                                    </div>
                                                                    
                                                                    {/* Tooltip explicativo para investigadores */}
                                                                    <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs rounded px-3 py-2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10 shadow-lg">
                                                                        {hunterData.tooltip}
                                                                        {hunterData.point !== 'N/A' && (
                                                                            <div className="text-gray-300 mt-1">
                                                                                Fuente: {direction.isOutgoing ? 'Celda origen' : 'Celda destino'}
                                                                                {hunterData.hasCoordinates && (
                                                                                    <div className="text-gray-400 text-xs font-mono mt-1">
                                                                                        GPS: {hunterData.coordinates}
                                                                                    </div>
                                                                                )}
                                                                            </div>
                                                                        )}
                                                                    </div>
                                                                </div>
                                                            );
                                                        })()}
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        {(() => {
                                                            const hunterData = getHunterPoint(interaction, targetNumber);
                                                            const latNum = typeof hunterData.lat === 'string' ? parseFloat(hunterData.lat) : hunterData.lat;
                                                            return (
                                                                <div className="text-sm font-mono text-white">
                                                                    {latNum !== undefined && !isNaN(latNum) ? latNum.toFixed(5) : 'N/A'}
                                                                </div>
                                                            );
                                                        })()}
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        {(() => {
                                                            const hunterData = getHunterPoint(interaction, targetNumber);
                                                            const lonNum = typeof hunterData.lon === 'string' ? parseFloat(hunterData.lon) : hunterData.lon;
                                                            return (
                                                                <div className="text-sm font-mono text-white">
                                                                    {lonNum !== undefined && !isNaN(lonNum) ? lonNum.toFixed(5) : 'N/A'}
                                                                </div>
                                                            );
                                                        })()}
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>

                            {/* Paginación - SIEMPRE VISIBLE */}
                            <div className="px-6 py-4 border-t border-secondary-light flex items-center justify-between" style={{ margin: '5px 10px 0px 10px' }}>
                                <div className="text-sm text-gray-400">
                                    {interactions.length > 0 ? 
                                        `Mostrando ${startIndex + 1} a ${Math.min(startIndex + itemsPerPage, interactions.length)} de ${interactions.length} registros`
                                        : 'No hay registros para mostrar'
                                    }
                                </div>
                                
                                {totalPages > 1 && (
                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                                            disabled={currentPage === 1}
                                            className="px-3 py-1 bg-secondary-light hover:bg-gray-600 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                        >
                                            ‹
                                        </button>
                                        
                                        <span className="px-3 py-1 text-white">
                                            Página {currentPage} de {totalPages}
                                        </span>
                                        
                                        <button
                                            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                                            disabled={currentPage === totalPages}
                                            className="px-3 py-1 bg-secondary-light hover:bg-gray-600 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                        >
                                            ›
                                        </button>
                                    </div>
                                )}
                            </div>
                        </>
                    )}
                </div>
            </div>

            {/* Modal del Diagrama de Correlación */}
            <PhoneCorrelationViewer
                isOpen={showDiagram}
                onClose={() => setShowDiagram(false)}
                interactions={interactions}
                targetNumber={targetNumber}
            />
        </div>
    );
};

export default TableCorrelationModal;