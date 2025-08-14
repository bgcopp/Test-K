import React, { useState, useCallback, useEffect } from 'react';
import { HashRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Users from './pages/Users';
import Roles from './pages/Roles';
import Missions from './pages/Missions';
import MissionDetail from './pages/MissionDetail';
import Sidebar from './components/layout/Sidebar';
import Header from './components/layout/Header';
import { ShutdownOverlay, ConnectionStatusIndicator } from './components/ui/ShutdownOverlay';

import type { User, Role, Mission } from './types';
import { getUsers, getRoles, getMissions, resetMockData, getRequestManager } from './services/api';
import { useEelConnection } from './hooks/useEelConnection';
import { useCleanup, useStorageCleanup } from './hooks/useCleanup';

const AppContent: React.FC<{ onLogout: () => void }> = ({ onLogout }) => {
    const location = useLocation();
    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
    
    const [users, setUsers] = useState<User[]>([]);
    const [roles, setRoles] = useState<Role[]>([]);
    const [missions, setMissions] = useState<Mission[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    
    // Hooks de shutdown coordination
    const { isConnected, isShuttingDown, markShuttingDown } = useEelConnection();
    const { registerCleanup } = useCleanup();
    const { registerStorageCleanup } = useStorageCleanup();

    useEffect(() => {
        const fetchInitialData = async () => {
            try {
                setIsLoading(true);
                const [usersData, rolesData, missionsData] = await Promise.all([
                    getUsers(),
                    getRoles(),
                    getMissions(),
                ]);
                setUsers(usersData);
                setRoles(rolesData);
                setMissions(missionsData);
            } catch (error) {
                console.error("Failed to fetch initial data:", error);
                
                // Solo mostrar alert si no estamos en shutdown
                if (!isShuttingDown) {
                    alert(`Error al cargar datos iniciales: ${(error as Error).message}`);
                }
            } finally {
                setIsLoading(false);
            }
        };
        fetchInitialData();
    }, [isShuttingDown]);
    
    // Configurar cleanup de recursos específicos de la app
    useEffect(() => {
        // Registrar cleanup del request manager
        registerCleanup(
            'request-manager',
            () => getRequestManager().initiateShutdown(),
            'high',
            'Cancelación de requests activas'
        );
        
        // Registrar cleanup de localStorage para datos sensibles
        registerStorageCleanup(['auth_token', 'user_session'], 'localStorage');
        
        // Registrar cleanup de datos temporales
        registerStorageCleanup(['temp_mission_data', 'draft_analysis'], 'sessionStorage');
    }, [registerCleanup, registerStorageCleanup]);
    
    // Manejar shutdown graceful cuando se detecta desconexión
    useEffect(() => {
        if (isShuttingDown) {
            console.log('🔄 Shutdown detectado - iniciando cleanup de AppContent');
            
            // Limpiar datos en memoria que puedan ser sensibles
            setUsers([]);
            setRoles([]);
            setMissions([]);
        }
    }, [isShuttingDown]);

    const getTitle = (pathname: string): string => {
        if (pathname.startsWith('/missions/')) {
            const missionId = pathname.split('/')[2];
            const mission = missions.find(m => m.id === missionId);
            return mission ? `Misión: ${mission.code}` : 'Detalles de la Misión';
        }
        if (pathname.startsWith('/missions')) return 'Misiones';
        if (pathname.startsWith('/users')) return 'Usuarios';
        if (pathname.startsWith('/roles')) return 'Roles';
        if (pathname.startsWith('/dashboard')) return 'Panel de Control';
        return 'KRONOS';
    };

    const handleToggleSidebar = () => {
        setIsSidebarCollapsed(prev => !prev);
    };

    if (isLoading) {
        return (
            <div className="flex justify-center items-center h-screen bg-dark text-light">
                <div className="text-center">
                    <p className="text-2xl">Cargando KRONOS...</p>
                </div>
            </div>
        );
    }

    return (
        <>
            <div className="flex h-screen bg-dark relative">
                <Sidebar 
                    onLogout={onLogout}
                    isCollapsed={isSidebarCollapsed}
                    onToggleCollapse={handleToggleSidebar}
                />
                <div className="flex-1 flex flex-col overflow-hidden">
                    <Header title={getTitle(location.pathname)} />
                    
                    {/* Indicador de conexión en el header */}
                    <div className="px-6 py-1 bg-secondary border-b border-medium">
                        <ConnectionStatusIndicator 
                            isConnected={isConnected}
                            isShuttingDown={isShuttingDown}
                            className="justify-end"
                        />
                    </div>
                    
                    <main className="flex-1 overflow-x-hidden overflow-y-auto bg-dark p-6">
                        {!isShuttingDown ? (
                            <Routes>
                                <Route path="/" element={<Navigate replace to="/dashboard" />} />
                                <Route path="/dashboard" element={<Dashboard users={users} roles={roles} missions={missions}/>} />
                                <Route path="/users" element={<Users users={users} setUsers={setUsers} roles={roles} />} />
                                <Route path="/roles" element={<Roles roles={roles} setRoles={setRoles} />} />
                                <Route path="/missions" element={<Missions missions={missions} setMissions={setMissions} />} />
                                <Route path="/missions/:missionId" element={<MissionDetail missions={missions} setMissions={setMissions} />} />
                            </Routes>
                        ) : (
                            <div className="flex items-center justify-center h-full">
                                <div className="text-center text-medium">
                                    <p className="text-lg mb-2">Cerrando aplicación...</p>
                                    <p className="text-sm">Guardando datos y limpiando recursos</p>
                                </div>
                            </div>
                        )}
                    </main>
                </div>
            </div>
            
            {/* Overlay de shutdown */}
            <ShutdownOverlay 
                isVisible={isShuttingDown}
                message="Cerrando KRONOS..."
            />
        </>
    );
};


const App: React.FC = () => {
    const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);

    const handleLogin = useCallback(() => {
        setIsAuthenticated(true);
    }, []);

    const handleLogout = useCallback(() => {
        console.log('🚪 Iniciando logout...');
        
        // Iniciar shutdown del request manager
        try {
            getRequestManager().initiateShutdown();
        } catch (error) {
            console.warn('⚠️ Error durante shutdown de request manager:', error);
        }
        
        // Reset the mock data store on logout to ensure a clean state for the next session.
        resetMockData();
        setIsAuthenticated(false);
        
        console.log('✅ Logout completado');
    }, []);

    if (!isAuthenticated) {
        return <Login onLogin={handleLogin} />;
    }

    return (
        <HashRouter>
            <AppContent onLogout={handleLogout} />
        </HashRouter>
    );
};

export default App;