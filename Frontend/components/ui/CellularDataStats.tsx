import React, { useMemo } from 'react';
import type { CellularDataRecord } from '../../types';

interface CellularDataStatsProps {
    data: CellularDataRecord[];
}

const CellularDataStats: React.FC<CellularDataStatsProps> = ({ data }) => {
    const stats = useMemo(() => {
        if (!data || data.length === 0) return null;

        // Cálculos básicos
        const totalRecords = data.length;
        const uniquePoints = new Set(data.map(d => d.punto)).size;
        
        // Distribución por operador
        const operatorCounts = data.reduce((acc, d) => {
            acc[d.operador] = (acc[d.operador] || 0) + 1;
            return acc;
        }, {} as Record<string, number>);

        // Distribución por tecnología
        const techCounts = data.reduce((acc, d) => {
            acc[d.tecnologia] = (acc[d.tecnologia] || 0) + 1;
            return acc;
        }, {} as Record<string, number>);

        // Estadísticas RSSI
        const rssiValues = data.map(d => d.rssi).filter(r => r !== null && r !== undefined);
        const minRssi = Math.min(...rssiValues);
        const maxRssi = Math.max(...rssiValues);
        const avgRssi = rssiValues.length > 0 ? Math.round(rssiValues.reduce((sum, r) => sum + r, 0) / rssiValues.length) : 0;

        // Calidad de señal categorizada
        const signalQuality = rssiValues.reduce((acc, rssi) => {
            if (rssi >= -60) acc.excelente++;
            else if (rssi >= -70) acc.buena++;
            else if (rssi >= -85) acc.regular++;
            else acc.pobre++;
            return acc;
        }, { excelente: 0, buena: 0, regular: 0, pobre: 0 });

        // Distribución por ID archivo (si hay múltiples)
        const fileIdCounts = data.reduce((acc, d) => {
            const fileId = d.fileRecordId ?? 'sin_id';
            acc[fileId] = (acc[fileId] || 0) + 1;
            return acc;
        }, {} as Record<string | number, number>);

        return {
            totalRecords,
            uniquePoints,
            operatorCounts,
            techCounts,
            rssi: { min: minRssi, max: maxRssi, avg: avgRssi },
            signalQuality,
            fileIdCounts,
            hasMultipleFileIds: Object.keys(fileIdCounts).length > 1
        };
    }, [data]);

    if (!stats) {
        return (
            <div className="bg-secondary-light p-6 rounded-lg border border-secondary mb-6">
                <div className="text-center py-8">
                    <div className="text-4xl text-medium mb-3">📊</div>
                    <p className="text-medium text-lg">No hay datos celulares para mostrar estadísticas</p>
                    <p className="text-sm text-medium mt-2">Carga un archivo SCANHUNTER para ver los indicadores</p>
                </div>
            </div>
        );
    }

    const getOperatorColor = (operator: string) => {
        const colors: Record<string, string> = {
            'CLARO': 'bg-red-600',
            'MOVISTAR': 'bg-green-600', 
            'TIGO': 'bg-blue-600',
            'WOM': 'bg-purple-600',
            'ENTEL': 'bg-orange-600'
        };
        return colors[operator] || 'bg-gray-600';
    };

    const getTechColor = (tech: string) => {
        const colors: Record<string, string> = {
            '5G': 'bg-purple-600',
            'LTE': 'bg-blue-600',
            '4G': 'bg-blue-600',
            'UMTS': 'bg-orange-600',
            '3G': 'bg-orange-600',
            'GSM': 'bg-gray-600',
            '2G': 'bg-gray-600'
        };
        return colors[tech] || 'bg-gray-600';
    };

    const getRssiQualityColor = (avgRssi: number) => {
        if (avgRssi >= -60) return 'border-green-600 bg-green-900/20';
        if (avgRssi >= -70) return 'border-blue-600 bg-blue-900/20';
        if (avgRssi >= -85) return 'border-yellow-600 bg-yellow-900/20';
        return 'border-red-600 bg-red-900/20';
    };

    const getRssiQualityText = (avgRssi: number) => {
        if (avgRssi >= -60) return 'Excelente';
        if (avgRssi >= -70) return 'Buena';
        if (avgRssi >= -85) return 'Regular';
        return 'Pobre';
    };

    return (
        <div className="space-y-6 mb-6">
            {/* Indicadores Principales */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Total Registros */}
                <div className="bg-secondary-light p-4 rounded-lg border-l-4 border-purple-600 bg-purple-900/20 hover:bg-opacity-80 transition-all">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-medium">Total Registros</p>
                            <p className="text-2xl font-bold text-light">{stats.totalRecords.toLocaleString()}</p>
                        </div>
                        <div className="text-3xl text-purple-400">📊</div>
                    </div>
                </div>

                {/* Puntos Únicos */}
                <div className="bg-secondary-light p-4 rounded-lg border-l-4 border-green-600 bg-green-900/20 hover:bg-opacity-80 transition-all">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-medium">Puntos Únicos</p>
                            <p className="text-2xl font-bold text-light">{stats.uniquePoints}</p>
                        </div>
                        <div className="text-3xl text-green-400">📍</div>
                    </div>
                </div>

                {/* Rango RSSI */}
                <div className={`bg-secondary-light p-4 rounded-lg border-l-4 hover:bg-opacity-80 transition-all ${getRssiQualityColor(stats.rssi.avg)}`}>
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-medium">Calidad Señal</p>
                            <p className="text-lg font-bold text-light">{getRssiQualityText(stats.rssi.avg)}</p>
                            <p className="text-xs text-medium">{stats.rssi.min} a {stats.rssi.max} dBm</p>
                        </div>
                        <div className="text-3xl text-yellow-400">📶</div>
                    </div>
                </div>

                {/* Operadores */}
                <div className="bg-secondary-light p-4 rounded-lg border-l-4 border-blue-600 bg-blue-900/20 hover:bg-opacity-80 transition-all">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-medium">Operadores</p>
                            <p className="text-2xl font-bold text-light">{Object.keys(stats.operatorCounts).length}</p>
                        </div>
                        <div className="text-3xl text-blue-400">📡</div>
                    </div>
                </div>
            </div>

            {/* Distribuciones Detalladas */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Distribución por Operador */}
                <div className="bg-secondary-light p-4 rounded-lg border border-secondary">
                    <h3 className="text-lg font-semibold text-light mb-4 flex items-center">
                        <span className="mr-2">📡</span>
                        Distribución por Operador
                    </h3>
                    <div className="space-y-3">
                        {Object.entries(stats.operatorCounts)
                            .sort(([,a], [,b]) => b - a)
                            .map(([operator, count]) => {
                                const percentage = (count / stats.totalRecords * 100).toFixed(1);
                                return (
                                    <div key={operator} className="flex items-center justify-between">
                                        <div className="flex items-center">
                                            <div className={`w-3 h-3 rounded-full mr-2 ${getOperatorColor(operator)}`}></div>
                                            <span className="text-sm text-light font-medium">{operator}</span>
                                        </div>
                                        <div className="flex items-center space-x-2">
                                            <div className="w-20 bg-secondary rounded-full h-2">
                                                <div 
                                                    className={`h-2 rounded-full ${getOperatorColor(operator)}`}
                                                    style={{ width: `${percentage}%` }}
                                                ></div>
                                            </div>
                                            <span className="text-xs text-medium w-16 text-right">{count} ({percentage}%)</span>
                                        </div>
                                    </div>
                                );
                            })}
                    </div>
                </div>

                {/* Distribución por Tecnología */}
                <div className="bg-secondary-light p-4 rounded-lg border border-secondary">
                    <h3 className="text-lg font-semibold text-light mb-4 flex items-center">
                        <span className="mr-2">🔧</span>
                        Distribución por Tecnología
                    </h3>
                    <div className="grid grid-cols-2 gap-3">
                        {Object.entries(stats.techCounts)
                            .sort(([,a], [,b]) => b - a)
                            .map(([tech, count]) => {
                                const percentage = (count / stats.totalRecords * 100).toFixed(1);
                                return (
                                    <div key={tech} className="text-center">
                                        <div className={`${getTechColor(tech)} text-white text-xs px-2 py-1 rounded-full mb-1`}>
                                            {tech}
                                        </div>
                                        <div className="text-sm text-light font-medium">{count}</div>
                                        <div className="text-xs text-medium">{percentage}%</div>
                                    </div>
                                );
                            })}
                    </div>
                </div>

                {/* Estadísticas RSSI */}
                <div className="bg-secondary-light p-4 rounded-lg border border-secondary">
                    <h3 className="text-lg font-semibold text-light mb-4 flex items-center">
                        <span className="mr-2">📶</span>
                        Calidad de Señal (RSSI)
                    </h3>
                    <div className="space-y-3">
                        <div className="grid grid-cols-3 gap-2 text-center">
                            <div>
                                <div className="text-xs text-medium">Mín</div>
                                <div className="text-sm font-medium text-light">{stats.rssi.min} dBm</div>
                            </div>
                            <div>
                                <div className="text-xs text-medium">Prom</div>
                                <div className="text-sm font-medium text-light">{stats.rssi.avg} dBm</div>
                            </div>
                            <div>
                                <div className="text-xs text-medium">Máx</div>
                                <div className="text-sm font-medium text-light">{stats.rssi.max} dBm</div>
                            </div>
                        </div>
                        <div className="space-y-2">
                            {[
                                { key: 'excelente', label: 'Excelente', color: 'bg-green-600', range: '≥ -60 dBm' },
                                { key: 'buena', label: 'Buena', color: 'bg-blue-600', range: '-60 a -70 dBm' },
                                { key: 'regular', label: 'Regular', color: 'bg-yellow-600', range: '-70 a -85 dBm' },
                                { key: 'pobre', label: 'Pobre', color: 'bg-red-600', range: '< -85 dBm' }
                            ].map(({ key, label, color, range }) => {
                                const count = stats.signalQuality[key as keyof typeof stats.signalQuality];
                                const percentage = count > 0 ? (count / stats.totalRecords * 100).toFixed(1) : '0.0';
                                return (
                                    <div key={key} className="flex items-center justify-between">
                                        <div className="flex items-center">
                                            <div className={`w-2 h-2 rounded-full mr-2 ${color}`}></div>
                                            <span className="text-xs text-light">{label}</span>
                                        </div>
                                        <span className="text-xs text-medium">{count} ({percentage}%)</span>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>
            </div>

            {/* Distribución por ID de Archivo (solo si hay múltiples) */}
            {stats.hasMultipleFileIds && (
                <div className="bg-secondary-light p-4 rounded-lg border border-secondary">
                    <h3 className="text-lg font-semibold text-light mb-4 flex items-center">
                        <span className="mr-2">📄</span>
                        Distribución por ID de Archivo
                    </h3>
                    <div className="grid grid-cols-3 md:grid-cols-6 gap-4">
                        {Object.entries(stats.fileIdCounts)
                            .sort(([a], [b]) => {
                                if (a === 'sin_id') return 1;
                                if (b === 'sin_id') return -1;
                                return Number(a) - Number(b);
                            })
                            .map(([fileId, count]) => {
                                const percentage = (count / stats.totalRecords * 100).toFixed(1);
                                return (
                                    <div key={fileId} className="text-center bg-secondary p-3 rounded">
                                        <div className="text-lg font-bold text-light">{fileId === 'sin_id' ? '–' : fileId}</div>
                                        <div className="text-sm text-medium">{count} registros</div>
                                        <div className="text-xs text-medium">{percentage}%</div>
                                    </div>
                                );
                            })}
                    </div>
                </div>
            )}
        </div>
    );
};

export default CellularDataStats;