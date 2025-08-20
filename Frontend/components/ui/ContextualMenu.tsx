/**
 * ContextualMenu - Menú Contextual para Nodos - FASE 4
 * 
 * Componente de menú desplegable que aparece al hacer right-click
 * en nodos del diagrama de correlación.
 * 
 * Características:
 * - Aparición inmediata al right-click
 * - Posicionamiento inteligente (evita overflow)
 * - Opciones contextualies por tipo de nodo
 * - Diseño consistente con tema oscuro
 * - Cierre automático al hacer click fuera
 * - Accesibilidad con teclado
 * 
 * @author Sistema KRONOS
 * @version 1.0.0 - FASE 4
 */

import React, { useEffect, useRef, useState } from 'react';
import { ICONS } from '../../constants';

// Tipos para las opciones del menú
export interface MenuOption {
    id: string;
    label: string;
    icon: string;
    action: string;
    disabled?: boolean;
    divider?: boolean;
    shortcut?: string;
}

// Tipos para el contexto del nodo
export interface NodeContext {
    nodeId: string;
    phoneNumber?: string;
    isTarget?: boolean;
    isHidden?: boolean;
    hasCustomizations?: boolean;
    nodeType?: 'person' | 'organization' | 'unknown';
}

interface ContextualMenuProps {
    isVisible: boolean;
    position: { x: number; y: number };
    nodeContext: NodeContext | null;
    onOptionSelect: (action: string, nodeContext: NodeContext) => void;
    onClose: () => void;
    containerRef?: React.RefObject<HTMLElement>;
}

/**
 * Genera opciones del menú según el contexto del nodo
 */
const getMenuOptions = (nodeContext: NodeContext | null): MenuOption[] => {
    if (!nodeContext) return [];
    
    const baseOptions: MenuOption[] = [
        {
            id: 'edit-name',
            label: 'Editar nombre',
            icon: ICONS.edit,
            action: 'edit-name'
        },
        {
            id: 'change-avatar',
            label: 'Cambiar avatar',
            icon: '👤',
            action: 'change-avatar'
        },
        {
            id: 'change-color',
            label: 'Cambiar color',
            icon: '🎨',
            action: 'change-color'
        },
        {
            id: 'divider-1',
            label: '',
            icon: '',
            action: '',
            divider: true
        },
        {
            id: 'hide-node',
            label: nodeContext.isHidden ? 'Mostrar nodo' : 'Ocultar nodo',
            icon: nodeContext.isHidden ? ICONS.eye : '👁️‍🗨️',
            action: 'toggle-visibility'
        },
        {
            id: 'center-view',
            label: 'Centrar vista',
            icon: ICONS.target,
            action: 'center-view'
        }
    ];
    
    // Opciones adicionales para nodos objetivo
    if (nodeContext.isTarget) {
        baseOptions.push(
            {
                id: 'divider-2',
                label: '',
                icon: '',
                action: '',
                divider: true
            },
            {
                id: 'mark-important',
                label: 'Marcar importante',
                icon: '⭐',
                action: 'mark-important'
            },
            {
                id: 'add-note',
                label: 'Agregar nota',
                icon: '📝',
                action: 'add-note'
            }
        );
    }
    
    // Opciones de limpieza si hay customizaciones
    if (nodeContext.hasCustomizations) {
        baseOptions.push(
            {
                id: 'divider-3',
                label: '',
                icon: '',
                action: '',
                divider: true
            },
            {
                id: 'reset-customizations',
                label: 'Restaurar original',
                icon: '🔄',
                action: 'reset-customizations'
            }
        );
    }
    
    return baseOptions;
};

/**
 * Calcula la posición óptima del menú para evitar overflow
 */
const calculateMenuPosition = (
    mousePosition: { x: number; y: number },
    menuSize: { width: number; height: number },
    containerRef?: React.RefObject<HTMLElement>
): { x: number; y: number } => {
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    
    // Obtener límites del contenedor si se proporciona
    let containerBounds = { left: 0, top: 0, right: viewportWidth, bottom: viewportHeight };
    if (containerRef?.current) {
        const rect = containerRef.current.getBoundingClientRect();
        containerBounds = {
            left: rect.left,
            top: rect.top,
            right: rect.right,
            bottom: rect.bottom
        };
    }
    
    let { x, y } = mousePosition;
    
    // Ajustar horizontalmente
    if (x + menuSize.width > containerBounds.right) {
        x = containerBounds.right - menuSize.width - 8; // 8px de margen
    }
    if (x < containerBounds.left) {
        x = containerBounds.left + 8;
    }
    
    // Ajustar verticalmente
    if (y + menuSize.height > containerBounds.bottom) {
        y = containerBounds.bottom - menuSize.height - 8;
    }
    if (y < containerBounds.top) {
        y = containerBounds.top + 8;
    }
    
    return { x, y };
};

/**
 * Componente principal del menú contextual
 */
const ContextualMenu: React.FC<ContextualMenuProps> = ({
    isVisible,
    position,
    nodeContext,
    onOptionSelect,
    onClose,
    containerRef
}) => {
    const menuRef = useRef<HTMLDivElement>(null);
    const [menuPosition, setMenuPosition] = useState(position);
    const [isAnimating, setIsAnimating] = useState(false);
    
    const menuOptions = getMenuOptions(nodeContext);
    
    // Actualizar posición cuando cambie la posición inicial
    useEffect(() => {
        if (isVisible && menuRef.current) {
            const menuRect = menuRef.current.getBoundingClientRect();
            const optimalPosition = calculateMenuPosition(
                position,
                { width: menuRect.width || 200, height: menuRect.height || 300 },
                containerRef
            );
            setMenuPosition(optimalPosition);
        }
    }, [isVisible, position, containerRef]);
    
    // Manejar animación de entrada
    useEffect(() => {
        if (isVisible) {
            setIsAnimating(true);
            const timer = setTimeout(() => setIsAnimating(false), 150);
            return () => clearTimeout(timer);
        }
    }, [isVisible]);
    
    // Cerrar menú al hacer click fuera
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                onClose();
            }
        };
        
        const handleEscape = (event: KeyboardEvent) => {
            if (event.key === 'Escape') {
                onClose();
            }
        };
        
        if (isVisible) {
            document.addEventListener('mousedown', handleClickOutside);
            document.addEventListener('keydown', handleEscape);
            
            return () => {
                document.removeEventListener('mousedown', handleClickOutside);
                document.removeEventListener('keydown', handleEscape);
            };
        }
    }, [isVisible, onClose]);
    
    // Manejar selección de opción
    const handleOptionClick = (option: MenuOption) => {
        if (option.disabled || option.divider || !nodeContext) return;
        
        onOptionSelect(option.action, nodeContext);
        onClose();
    };
    
    // Manejar navegación con teclado
    const handleKeyDown = (event: React.KeyboardEvent) => {
        // Aquí se puede implementar navegación con flechas si es necesario
        if (event.key === 'Enter' || event.key === ' ') {
            // Implementar selección con teclado si se requiere
        }
    };
    
    if (!isVisible || !nodeContext) {
        return null;
    }
    
    return (
        <div
            ref={menuRef}
            className={`fixed z-50 bg-secondary border border-secondary-light rounded-lg shadow-2xl backdrop-blur-sm min-w-[180px] ${
                isAnimating ? 'animate-in fade-in-0 zoom-in-95 duration-150' : ''
            }`}
            style={{
                left: `${menuPosition.x}px`,
                top: `${menuPosition.y}px`
            }}
            onKeyDown={handleKeyDown}
            role="menu"
            tabIndex={-1}
        >
            {/* Header del menú con información del nodo */}
            <div className="px-3 py-2 border-b border-secondary-light bg-secondary-light/50">
                <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-light">
                        {nodeContext.phoneNumber || `Nodo ${nodeContext.nodeId}`}
                    </span>
                    {nodeContext.isTarget && (
                        <span className="text-xs px-1.5 py-0.5 bg-primary/20 text-primary rounded">
                            Objetivo
                        </span>
                    )}
                </div>
            </div>
            
            {/* Lista de opciones */}
            <div className="py-1">
                {menuOptions.map((option) => {
                    if (option.divider) {
                        return (
                            <div
                                key={option.id}
                                className="h-px bg-secondary-light mx-2 my-1"
                                role="separator"
                            />
                        );
                    }
                    
                    return (
                        <button
                            key={option.id}
                            onClick={() => handleOptionClick(option)}
                            disabled={option.disabled}
                            className={`w-full flex items-center gap-3 px-3 py-2 text-sm text-left transition-colors ${
                                option.disabled
                                    ? 'text-medium cursor-not-allowed opacity-50'
                                    : 'text-light hover:bg-secondary-light hover:text-white'
                            }`}
                            role="menuitem"
                            tabIndex={option.disabled ? -1 : 0}
                        >
                            <span className="w-4 text-center flex-shrink-0">
                                {option.icon}
                            </span>
                            <span className="flex-1">
                                {option.label}
                            </span>
                            {option.shortcut && (
                                <span className="text-xs text-medium">
                                    {option.shortcut}
                                </span>
                            )}
                        </button>
                    );
                })}
            </div>
            
            {/* Footer del menú */}
            <div className="px-3 py-1 border-t border-secondary-light bg-secondary-light/30">
                <p className="text-xs text-medium text-center">
                    Click fuera para cerrar
                </p>
            </div>
        </div>
    );
};

/**
 * Hook para manejar el estado del menú contextual
 */
export const useContextualMenu = () => {
    const [isVisible, setIsVisible] = useState(false);
    const [position, setPosition] = useState({ x: 0, y: 0 });
    const [nodeContext, setNodeContext] = useState<NodeContext | null>(null);
    
    const showMenu = (
        event: React.MouseEvent | MouseEvent,
        context: NodeContext
    ) => {
        event.preventDefault();
        setPosition({ x: event.clientX, y: event.clientY });
        setNodeContext(context);
        setIsVisible(true);
    };
    
    const hideMenu = () => {
        setIsVisible(false);
        // Pequeño delay antes de limpiar el contexto para permitir animaciones
        setTimeout(() => {
            setNodeContext(null);
        }, 150);
    };
    
    return {
        isVisible,
        position,
        nodeContext,
        showMenu,
        hideMenu
    };
};

export default ContextualMenu;