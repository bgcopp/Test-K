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

import type { User, Role, Mission } from './types';
import { getUsers, getRoles, getMissions, resetMockData } from './services/api';

const AppContent: React.FC<{ onLogout: () => void }> = ({ onLogout }) => {
    const location = useLocation();
    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
    
    const [users, setUsers] = useState<User[]>([]);
    const [roles, setRoles] = useState<Role[]>([]);
    const [missions, setMissions] = useState<Mission[]>([]);
    const [isLoading, setIsLoading] = useState(true);

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
                alert(`Error al cargar datos iniciales: ${(error as Error).message}`);
            } finally {
                setIsLoading(false);
            }
        };
        fetchInitialData();
    }, []);

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
        <div className="flex h-screen bg-dark">
            <Sidebar 
                onLogout={onLogout}
                isCollapsed={isSidebarCollapsed}
                onToggleCollapse={handleToggleSidebar}
            />
            <div className="flex-1 flex flex-col overflow-hidden">
                <Header title={getTitle(location.pathname)} />
                <main className="flex-1 overflow-x-hidden overflow-y-auto bg-dark p-6">
                    <Routes>
                        <Route path="/" element={<Navigate replace to="/dashboard" />} />
                        <Route path="/dashboard" element={<Dashboard users={users} roles={roles} missions={missions}/>} />
                        <Route path="/users" element={<Users users={users} setUsers={setUsers} roles={roles} />} />
                        <Route path="/roles" element={<Roles roles={roles} setRoles={setRoles} />} />
                        <Route path="/missions" element={<Missions missions={missions} setMissions={setMissions} />} />
                        <Route path="/missions/:missionId" element={<MissionDetail missions={missions} setMissions={setMissions} />} />
                    </Routes>
                </main>
            </div>
        </div>
    );
};


const App: React.FC = () => {
    const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);

    const handleLogin = useCallback(() => {
        setIsAuthenticated(true);
    }, []);

    const handleLogout = useCallback(() => {
        // Reset the mock data store on logout to ensure a clean state for the next session.
        resetMockData();
        setIsAuthenticated(false);
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