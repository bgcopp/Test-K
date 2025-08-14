import React, { useState, useEffect } from 'react';
import { NavLink, Link, useLocation } from 'react-router-dom';
import { ICONS, APP_VERSION } from '../../constants';

interface SidebarProps {
    onLogout: () => void;
    isCollapsed: boolean;
    onToggleCollapse: () => void;
}

interface NavItemProps {
    to: string;
    icon: React.ReactNode;
    label: string;
    isCollapsed: boolean;
    isSubItem?: boolean;
}

const NavItem: React.FC<NavItemProps> = ({ to, icon, label, isCollapsed, isSubItem = false }) => {
    return (
        <NavLink
            to={to}
            className={({ isActive }) =>
                `flex items-center px-4 py-3 text-medium transition-colors duration-200 transform rounded-lg ${
                    isActive ? 'bg-secondary-light text-light' : 'hover:bg-secondary-light hover:text-light'
                } ${isCollapsed ? 'justify-center' : ''} ${isSubItem && !isCollapsed ? 'pl-8' : ''}`
            }
        >
            {icon}
            {!isCollapsed && <span className="mx-4 font-medium">{label}</span>}
        </NavLink>
    );
};

const Sidebar: React.FC<SidebarProps> = ({ onLogout, isCollapsed, onToggleCollapse }) => {
    const [isSettingsOpen, setSettingsOpen] = useState(false);
    const location = useLocation();

    useEffect(() => {
        if (isCollapsed) {
            setSettingsOpen(false);
        }
    }, [isCollapsed]);

    useEffect(() => {
        if (location.pathname.startsWith('/users') || location.pathname.startsWith('/roles')) {
            setSettingsOpen(true);
        }
    }, [location.pathname]);

    return (
        <aside className={`flex flex-col h-screen py-8 bg-secondary border-r border-secondary-light transition-all duration-300 ease-in-out ${isCollapsed ? 'w-20 px-2' : 'w-64 px-4'}`}>
            <div className="px-2">
                <div className="flex flex-col items-center">
                    <Link to="/dashboard" className="flex items-center justify-center" aria-label="KRONOS - Ir al panel de control">
                        <svg className="h-9 w-9" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <rect width="24" height="24" rx="4" fill="#9ca3af" />
                            <path d="M5 12.55a11 11 0 0 1 14.08 0" stroke="#1f2937" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            <path d="M1.42 9a16 16 0 0 1 21.16 0" stroke="#1f2937" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            <path d="M8.53 16.11a6 6 0 0 1 6.95 0" stroke="#1f2937" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            <line x1="12" y1="20" x2="12" y2="12" stroke="#1f2937" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                    </Link>
                    <div className={`text-center transition-opacity duration-200 ease-in-out ${isCollapsed ? 'opacity-0 h-0 invisible' : 'opacity-100 h-auto visible mt-2'}`}>
                        <h2 className="text-xl font-semibold text-light">KRONOS</h2>
                        <p className="text-xs text-medium">Versión {APP_VERSION}</p>
                    </div>
                </div>
            </div>

            <div className="flex flex-col justify-between flex-1 mt-6">
                <nav className="space-y-2">
                    <NavItem to="/dashboard" icon={ICONS.dashboard} label="Panel de Control" isCollapsed={isCollapsed} />
                    
                    <div>
                        <button
                            onClick={() => setSettingsOpen(!isSettingsOpen)}
                            className={`flex items-center w-full px-4 py-3 text-medium transition-colors duration-200 transform rounded-lg hover:bg-secondary-light hover:text-light ${isCollapsed ? 'justify-center' : ''}`}
                        >
                            {ICONS.settings}
                            {!isCollapsed && <span className="mx-4 font-medium">Configuración</span>}
                            {!isCollapsed && <span className={`ml-auto transform transition-transform duration-200 ${isSettingsOpen ? 'rotate-180' : ''}`}>{ICONS.chevronDown}</span>}
                        </button>
                        <div className={`transition-all duration-300 ease-in-out overflow-hidden ${isSettingsOpen && !isCollapsed ? 'max-h-40' : 'max-h-0'}`}>
                            <div className="pt-2 space-y-2">
                                <NavItem to="/users" icon={ICONS.users} label="Usuarios" isCollapsed={isCollapsed} isSubItem />
                                <NavItem to="/roles" icon={ICONS.roles} label="Roles" isCollapsed={isCollapsed} isSubItem />
                            </div>
                        </div>
                    </div>
                    
                    <NavItem to="/missions" icon={ICONS.missions} label="Misiones" isCollapsed={isCollapsed} />
                    
                </nav>

                <div className="space-y-2">
                    <button
                        onClick={onToggleCollapse}
                        className={`flex items-center w-full px-4 py-3 text-medium transition-colors duration-200 transform rounded-lg hover:bg-secondary-light hover:text-light ${isCollapsed ? 'justify-center' : ''}`}
                    >
                        {isCollapsed ? ICONS.chevronRight : ICONS.chevronLeft}
                        {!isCollapsed && <span className="mx-4 font-medium">Colapsar</span>}
                    </button>
                    <button
                        onClick={onLogout}
                        className={`flex items-center w-full px-4 py-3 text-medium transition-colors duration-200 transform rounded-lg hover:bg-red-600 hover:text-white ${isCollapsed ? 'justify-center' : ''}`}
                    >
                        {ICONS.logout}
                        {!isCollapsed && <span className="mx-4 font-medium">Cerrar Sesión</span>}
                    </button>
                </div>
            </div>
        </aside>
    );
};

export default Sidebar;