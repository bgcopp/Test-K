/**
 * NodeEditor - Componente de Edición In-Place para Nodos
 * 
 * Componente especializado para permitir la edición directa de nombres
 * de nodos en el diagrama de correlación. Se activa con doble-click
 * y proporciona una experiencia de edición fluida y accesible.
 * 
 * Características:
 * - Input overlay posicionado sobre el nodo
 * - Validación de entrada (máximo 50 caracteres)
 * - Auto-save al confirmar (Enter)
 * - Cancelación con ESC
 * - Focus automático en activación
 * - Diseño consistente con tema oscuro
 * - Accesibilidad WCAG AA
 * 
 * @author Claude Code asistiendo a Boris
 * @version FASE 3 - Interactividad Avanzada
 */

import React, { useState, useEffect, useRef, useCallback, memo } from 'react';

// ===============================================
// INTERFACES Y TIPOS
// ===============================================

/**
 * Props del componente NodeEditor
 */
interface NodeEditorProps {
    /** ID único del nodo que se está editando */
    nodeId: string;
    
    /** Nombre actual del nodo */
    currentName: string;
    
    /** Posición del editor en el canvas */
    position: { x: number; y: number };
    
    /** Tamaño del nodo para posicionamiento correcto */
    nodeSize: number;
    
    /** Función llamada al guardar el nuevo nombre */
    onSave: (newName: string) => void;
    
    /** Función llamada al cancelar la edición */
    onCancel: () => void;
    
    /** Indica si el nodo es el objetivo central */
    isTarget?: boolean;
}

/**
 * Configuración de validación para nombres
 */
interface ValidationConfig {
    maxLength: number;
    minLength: number;
    allowedCharacters: RegExp;
}

// ===============================================
// CONFIGURACIÓN
// ===============================================

/**
 * Configuración de validación para nombres de nodos
 */
const VALIDATION_CONFIG: ValidationConfig = {
    maxLength: 50,
    minLength: 1,
    allowedCharacters: /^[a-zA-Z0-9\s\-_áéíóúñüÁÉÍÓÚÑÜ]*$/
};

/**
 * Configuración de estilos por tipo de nodo
 */
const EDITOR_STYLES = {
    target: {
        fontSize: '14px',
        fontWeight: '600',
        borderColor: '#3B82F6', // blue-500
        backgroundColor: 'rgba(59, 130, 246, 0.1)'
    },
    related: {
        fontSize: '12px',
        fontWeight: '500',
        borderColor: '#6B7280', // gray-500
        backgroundColor: 'rgba(107, 114, 128, 0.1)'
    }
};

// ===============================================
// COMPONENTE PRINCIPAL
// ===============================================

/**
 * NodeEditor - Componente de edición in-place para nombres de nodos
 * 
 * Implementa las especificaciones de FASE 3:
 * - Activación con doble-click en nodo
 * - Input overlay con posicionamiento preciso
 * - Validación de entrada en tiempo real
 * - Confirmación con Enter, cancelación con ESC
 * - Auto-focus y selección del texto existente
 * - Estilos diferenciados para nodo objetivo vs relacionados
 */
const NodeEditor: React.FC<NodeEditorProps> = memo(({
    nodeId,
    currentName,
    position,
    nodeSize,
    onSave,
    onCancel,
    isTarget = false
}) => {
    // Estados locales
    const [inputValue, setInputValue] = useState(currentName);
    const [isValid, setIsValid] = useState(true);
    const [validationMessage, setValidationMessage] = useState('');
    
    // Referencias
    const inputRef = useRef<HTMLInputElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    // Configuración de estilos basada en tipo de nodo
    const editorStyle = isTarget ? EDITOR_STYLES.target : EDITOR_STYLES.related;

    // ===============================================
    // EFECTOS
    // ===============================================

    /**
     * Auto-focus y selección del texto al montar el componente
     */
    useEffect(() => {
        if (inputRef.current) {
            inputRef.current.focus();
            inputRef.current.select();
        }
    }, []);

    /**
     * Validación en tiempo real del input
     */
    useEffect(() => {
        validateInput(inputValue);
    }, [inputValue]);

    /**
     * Manejo de clicks fuera del editor para confirmar
     */
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
                if (isValid && inputValue.trim() !== '') {
                    handleSave();
                } else {
                    handleCancel();
                }
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [inputValue, isValid]);

    // ===============================================
    // FUNCIONES DE VALIDACIÓN
    // ===============================================

    /**
     * Valida el input según las reglas establecidas
     */
    const validateInput = useCallback((value: string) => {
        const trimmedValue = value.trim();
        
        // Validar longitud
        if (trimmedValue.length < VALIDATION_CONFIG.minLength) {
            setIsValid(false);
            setValidationMessage('El nombre no puede estar vacío');
            return;
        }
        
        if (trimmedValue.length > VALIDATION_CONFIG.maxLength) {
            setIsValid(false);
            setValidationMessage(`Máximo ${VALIDATION_CONFIG.maxLength} caracteres`);
            return;
        }
        
        // Validar caracteres permitidos
        if (!VALIDATION_CONFIG.allowedCharacters.test(trimmedValue)) {
            setIsValid(false);
            setValidationMessage('Solo se permiten letras, números, espacios y guiones');
            return;
        }
        
        // Todo válido
        setIsValid(true);
        setValidationMessage('');
    }, []);

    // ===============================================
    // MANEJADORES DE EVENTOS
    // ===============================================

    /**
     * Maneja el cambio en el input
     */
    const handleInputChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
        const newValue = event.target.value;
        setInputValue(newValue);
    }, []);

    /**
     * Maneja las teclas especiales
     */
    const handleKeyDown = useCallback((event: React.KeyboardEvent<HTMLInputElement>) => {
        switch (event.key) {
            case 'Enter':
                event.preventDefault();
                if (isValid && inputValue.trim() !== '') {
                    handleSave();
                }
                break;
                
            case 'Escape':
                event.preventDefault();
                handleCancel();
                break;
                
            case 'Tab':
                event.preventDefault();
                if (isValid && inputValue.trim() !== '') {
                    handleSave();
                } else {
                    handleCancel();
                }
                break;
        }
    }, [inputValue, isValid]);

    /**
     * Guarda el nuevo nombre
     */
    const handleSave = useCallback(() => {
        const trimmedValue = inputValue.trim();
        if (isValid && trimmedValue !== '' && trimmedValue !== currentName) {
            onSave(trimmedValue);
        } else {
            onCancel();
        }
    }, [inputValue, isValid, currentName, onSave, onCancel]);

    /**
     * Cancela la edición
     */
    const handleCancel = useCallback(() => {
        onCancel();
    }, [onCancel]);

    // ===============================================
    // CÁLCULOS DE POSICIONAMIENTO
    // ===============================================

    // Calcular posición del editor centrada sobre el nodo
    const editorPosition = {
        left: position.x - (nodeSize * 0.75),
        top: position.y - (nodeSize * 0.1),
        width: nodeSize * 1.5,
        minWidth: '120px'
    };

    // ===============================================
    // RENDER
    // ===============================================

    return (
        <div
            ref={containerRef}
            className="fixed z-[10000] pointer-events-auto"
            style={{
                left: editorPosition.left,
                top: editorPosition.top,
                width: editorPosition.width,
                minWidth: editorPosition.minWidth
            }}
        >
            {/* Container del editor */}
            <div className="relative">
                {/* Input principal */}
                <input
                    ref={inputRef}
                    type="text"
                    value={inputValue}
                    onChange={handleInputChange}
                    onKeyDown={handleKeyDown}
                    className={`
                        w-full
                        px-3
                        py-2
                        text-center
                        bg-gray-800/95
                        backdrop-blur-sm
                        border-2
                        rounded-lg
                        text-white
                        placeholder-gray-400
                        shadow-2xl
                        transition-all
                        duration-200
                        ${isValid 
                            ? 'border-blue-500 focus:border-blue-400' 
                            : 'border-red-500 focus:border-red-400'
                        }
                        focus:outline-none
                        focus:ring-2
                        ${isValid 
                            ? 'focus:ring-blue-500/20' 
                            : 'focus:ring-red-500/20'
                        }
                    `}
                    style={{
                        fontSize: editorStyle.fontSize,
                        fontWeight: editorStyle.fontWeight
                    }}
                    placeholder="Escriba el nombre..."
                    maxLength={VALIDATION_CONFIG.maxLength}
                    aria-label={`Editar nombre del nodo ${nodeId}`}
                    aria-invalid={!isValid}
                    aria-describedby={!isValid ? `${nodeId}-validation` : undefined}
                />

                {/* Indicador de validación */}
                {!isValid && validationMessage && (
                    <div 
                        id={`${nodeId}-validation`}
                        className="absolute top-full mt-1 left-0 right-0 bg-red-900/90 backdrop-blur-sm border border-red-600 rounded px-2 py-1 text-xs text-red-200 shadow-lg"
                        role="alert"
                    >
                        {validationMessage}
                    </div>
                )}

                {/* Contador de caracteres */}
                <div className="absolute top-full mt-1 right-0 text-xs text-gray-400 font-mono">
                    {inputValue.length}/{VALIDATION_CONFIG.maxLength}
                </div>

                {/* Instrucciones de teclas */}
                <div className="absolute top-full mt-6 left-0 right-0 text-xs text-gray-500 text-center">
                    <div>Enter para guardar • ESC para cancelar</div>
                </div>
            </div>

            {/* Indicador visual de edición activa */}
            <div 
                className="absolute inset-0 -m-2 border-2 border-dashed border-blue-400/50 rounded-lg pointer-events-none animate-pulse"
                aria-hidden="true"
            />
        </div>
    );
});

NodeEditor.displayName = 'NodeEditor';

export default NodeEditor;