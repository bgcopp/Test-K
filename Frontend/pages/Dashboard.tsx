
import React, { useEffect, useState } from 'react';
import Card from '../components/ui/Card';
import { ICONS } from '../constants';
import type { User, Role, Mission } from '../types';
import { MissionStatus } from '../types';
import { getOperatorStatistics } from '../services/api';

interface DashboardProps {
    users: User[];
    roles: Role[];
    missions: Mission[];
}

interface OperatorStats {
    success: boolean;
    statistics: any;
    totals: {
        total_files: number;
        total_records: number;
        completed_files: number;
        failed_files: number;
        success_rate: number;
    };
    error?: string;
}

const Dashboard: React.FC<DashboardProps> = ({ users, roles, missions }) => {
    const [operatorStats, setOperatorStats] = useState<OperatorStats | null>(null);
    const [loading, setLoading] = useState(true);
    
    const activeMissions = missions.filter(m => m.status === MissionStatus.IN_PROGRESS).length;

    useEffect(() => {
        const loadOperatorStatistics = async () => {
            try {
                setLoading(true);
                const stats = await getOperatorStatistics();
                setOperatorStats(stats);
            } catch (error) {
                console.error('Error cargando estadísticas de operadores:', error);
                // Establecer valores por defecto en caso de error
                setOperatorStats({
                    success: false,
                    statistics: {},
                    totals: {
                        total_files: 0,
                        total_records: 0,
                        completed_files: 0,
                        failed_files: 0,
                        success_rate: 0
                    },
                    error: 'Error cargando datos'
                });
            } finally {
                setLoading(false);
            }
        };

        loadOperatorStatistics();
    }, []);

    // Obtener valores seguros de las estadísticas
    const totalFiles = operatorStats?.totals?.total_files || 0;
    const totalRecords = operatorStats?.totals?.total_records || 0;
    const completedFiles = operatorStats?.totals?.completed_files || 0;

    return (
        <div>
            {/* Tarjetas principales del sistema */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <Card title="Usuarios Totales" value={users.length} icon={ICONS.users} />
                <Card title="Roles Totales" value={roles.length} icon={ICONS.roles} />
                <Card title="Misiones Activas" value={activeMissions} icon={ICONS.missions} />
            </div>

            {/* Nueva sección: Estadísticas de Archivos de Operadores */}
            <div className="mt-8">
                <h2 className="text-xl font-semibold text-light mb-4">Archivos de Operadores Procesados</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <Card 
                        title="Total Archivos" 
                        value={loading ? '...' : totalFiles} 
                        icon={ICONS.upload} 
                    />
                    <Card 
                        title="Total Registros Procesados" 
                        value={loading ? '...' : totalRecords.toLocaleString()} 
                        icon={ICONS.database} 
                    />
                    <Card 
                        title="Archivos Completados" 
                        value={loading ? '...' : completedFiles} 
                        icon={ICONS.checkCircle} 
                    />
                    <Card 
                        title="Tasa de Éxito" 
                        value={loading ? '...' : `${operatorStats?.totals?.success_rate || 0}%`} 
                        icon={ICONS.check} 
                    />
                </div>
                
                {operatorStats?.error && (
                    <div className="mt-4 bg-red-900/20 border border-red-800 rounded-lg p-4">
                        <p className="text-red-400">
                            <strong>Error:</strong> {operatorStats.error}
                        </p>
                    </div>
                )}
            </div>

            {/* Información de bienvenida */}
            <div className="mt-8 bg-secondary rounded-lg shadow-xl p-6 border border-secondary-light">
                 <h2 className="text-xl font-semibold text-light mb-4">Bienvenido al Panel de Administración</h2>
                 <p className="text-medium">
                     Este es tu centro de control para gestionar todos los aspectos de la aplicación. 
                     Usa la navegación de la izquierda para administrar usuarios, definir roles con permisos granulares 
                     y supervisar misiones de investigación críticas.
                 </p>
                 <p className="text-medium mt-4">
                     Las estadísticas de archivos de operadores muestran el progreso del procesamiento de datos 
                     CDR y de ubicación de operadores móviles como CLARO, MOVISTAR, TIGO y WOM.
                 </p>
            </div>
        </div>
    );
};

export default Dashboard;
