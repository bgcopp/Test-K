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
import NotificationSystem from './components/ui/NotificationSystem';

// 🎯 NUEVA IMPORTACIÓN REQUERIDA
import { ConfirmationProvider } from './hooks/useConfirmation';

import type { User, Role, Mission } from './types';
import { getUsers, getRoles, getMissions, resetMockData } from './services/api';
import { useNotification } from './hooks/useNotification';

const AppContent: React.FC<{ onLogout: () => void }> = ({ onLogout }) => {
    const location = useLocation();
    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
    
    const [users, setUsers] = useState<User[]>([]);
    const [roles, setRoles] = useState<Role[]>([]);
    const [missions, setMissions] = useState<Mission[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    
    const { showError } = useNotification();

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
                showError("Error de Inicialización", `Error al cargar datos iniciales: ${(error as Error).message}`);
            } finally {
                setIsLoading(false);
            }
        };
        fetchInitialData();
    }, []);

    const getTitle = (pathname: string): string => {
        switch (pathname) {
            case '/dashboard': return 'Dashboard';
            case '/users': return 'Gestión de Usuarios';
            case '/roles': return 'Gestión de Roles';
            case '/missions': return 'Gestión de Misiones';
            default: return 'KRONOS';
        }
    };

    const updateUser = useCallback((updatedUser: User) => {
        setUsers(prev => prev.map(u => u.id === updatedUser.id ? updatedUser : u));
    }, []);

    const updateRole = useCallback((updatedRole: Role) => {
        setRoles(prev => prev.map(r => r.id === updatedRole.id ? updatedRole : r));
    }, []);

    const updateMission = useCallback((updatedMission: Mission) => {
        setMissions(prev => prev.map(m => m.id === updatedMission.id ? updatedMission : m));
    }, []);

    if (isLoading) {
        return (
            <div className="min-h-screen bg-dark flex items-center justify-center">
                <div className="text-light">Cargando...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-dark flex">
            <Sidebar isCollapsed={isSidebarCollapsed} onToggle={() => setIsSidebarCollapsed(!isSidebarCollapsed)} />
            <div className="flex-1 flex flex-col overflow-hidden">
                <Header 
                    title={getTitle(location.pathname)} 
                    onLogout={onLogout}
                />
                <main className="flex-1 overflow-y-auto">
                    <Routes>
                        <Route path="/" element={<Navigate to="/dashboard" replace />} />
                        <Route path="/dashboard" element={<Dashboard missions={missions} />} />
                        <Route 
                            path="/users" 
                            element={
                                <Users 
                                    users={users} 
                                    roles={roles} 
                                    onUpdateUser={updateUser}
                                />
                            } 
                        />
                        <Route 
                            path="/roles" 
                            element={
                                <Roles 
                                    roles={roles} 
                                    onUpdateRole={updateRole}
                                />
                            } 
                        />
                        <Route 
                            path="/missions" 
                            element={
                                <Missions 
                                    missions={missions} 
                                    onUpdateMission={updateMission}
                                />
                            } 
                        />
                        <Route 
                            path="/missions/:id" 
                            element={
                                <MissionDetail 
                                    missions={missions}
                                    onUpdateMission={updateMission}
                                />
                            } 
                        />
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
        resetMockData();
        setIsAuthenticated(false);
    }, []);

    if (!isAuthenticated) {
        return (
            // 🎯 ENVOLVER TAMBIÉN EL LOGIN CON EL PROVIDER PARA CONFIRMACIONES GLOBALES
            <ConfirmationProvider>
                <Login onLogin={handleLogin} />
            </ConfirmationProvider>
        );
    }

    return (
        // 🎯 ENVOLVER TODA LA APLICACIÓN CON ConfirmationProvider
        <ConfirmationProvider>
            <HashRouter>
                <AppContent onLogout={handleLogout} />
            </HashRouter>
        </ConfirmationProvider>
    );
};

export default App;

/**
 * 🔧 INSTRUCCIONES DE INTEGRACIÓN:
 * 
 * 1. Reemplaza el contenido de tu App.tsx actual con este código
 * 2. La única diferencia son las líneas marcadas con 🎯
 * 3. Esto habilita el sistema de confirmación en toda la aplicación
 * 4. Los componentes individuales ahora pueden usar useConfirmation()
 * 
 * PRÓXIMOS PASOS:
 * - Actualizar componentes de Missions para usar confirmationPresets.deleteMission()
 * - Actualizar componentes de Users para usar confirmationPresets.deleteUser()
 * - Actualizar componentes de Roles para usar confirmationPresets.deleteRole()
 * - Reemplazar window.confirm() existentes con showConfirmation()
 */