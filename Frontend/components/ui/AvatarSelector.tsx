/**
 * AvatarSelector - Selector de Avatares Unicode - FASE 4
 * 
 * Componente para seleccionar avatares emoji Unicode para personalización
 * de nodos en diagramas de correlación.
 * 
 * Características:
 * - Emojis Unicode nativos (sin imágenes)
 * - Tamaño uniforme (60px)
 * - Categorías organizadas
 * - Preview en tiempo real
 * - Búsqueda por nombre
 * - Responsive design
 * 
 * @author Sistema KRONOS
 * @version 1.0.0 - FASE 4
 */

import React, { useState, useMemo } from 'react';

// Definición de avatares organizados por categoría
export const AVATAR_ICONS = {
    // Personas básicas
    people: {
        male: { emoji: '👨', name: 'Hombre', keywords: ['hombre', 'masculino', 'varón'] },
        female: { emoji: '👩', name: 'Mujer', keywords: ['mujer', 'femenino'] },
        neutral: { emoji: '👤', name: 'Neutral', keywords: ['persona', 'neutro', 'genérico'] },
        young_male: { emoji: '👦', name: 'Joven', keywords: ['joven', 'niño', 'adolescente'] },
        young_female: { emoji: '👧', name: 'Joven', keywords: ['joven', 'niña', 'adolescente'] },
        elder_male: { emoji: '👴', name: 'Adulto Mayor', keywords: ['adulto', 'mayor', 'anciano'] },
        elder_female: { emoji: '👵', name: 'Adulta Mayor', keywords: ['adulta', 'mayor', 'anciana'] },
    },
    
    // Profesiones y roles
    professions: {
        police: { emoji: '👮', name: 'Policía', keywords: ['policía', 'seguridad', 'autoridad'] },
        medical: { emoji: '⚕️', name: 'Médico', keywords: ['médico', 'salud', 'doctor'] },
        government: { emoji: '🏛️', name: 'Gobierno', keywords: ['gobierno', 'oficial', 'funcionario'] },
        business: { emoji: '👔', name: 'Ejecutivo', keywords: ['ejecutivo', 'negocio', 'empresario'] },
        teacher: { emoji: '👨‍🏫', name: 'Professor', keywords: ['profesor', 'educador', 'maestro'] },
        engineer: { emoji: '👨‍💻', name: 'Técnico', keywords: ['técnico', 'ingeniero', 'programador'] },
        lawyer: { emoji: '⚖️', name: 'Abogado', keywords: ['abogado', 'justicia', 'legal'] },
    },
    
    // Organizaciones
    organizations: {
        company: { emoji: '🏢', name: 'Empresa', keywords: ['empresa', 'corporación', 'negocio'] },
        bank: { emoji: '🏦', name: 'Banco', keywords: ['banco', 'financiero', 'dinero'] },
        hospital: { emoji: '🏥', name: 'Hospital', keywords: ['hospital', 'clínica', 'salud'] },
        school: { emoji: '🏫', name: 'Escuela', keywords: ['escuela', 'educación', 'universidad'] },
        church: { emoji: '⛪', name: 'Iglesia', keywords: ['iglesia', 'religioso', 'templo'] },
    },
    
    // Estados y situaciones
    states: {
        unknown: { emoji: '❓', name: 'Desconocido', keywords: ['desconocido', 'interrogante', 'duda'] },
        important: { emoji: '⭐', name: 'Importante', keywords: ['importante', 'estrella', 'destacado'] },
        warning: { emoji: '⚠️', name: 'Advertencia', keywords: ['advertencia', 'cuidado', 'alerta'] },
        location: { emoji: '📍', name: 'Ubicación', keywords: ['ubicación', 'lugar', 'posición'] },
        phone: { emoji: '📱', name: 'Teléfono', keywords: ['teléfono', 'móvil', 'celular'] },
        target: { emoji: '🎯', name: 'Objetivo', keywords: ['objetivo', 'blanco', 'meta'] },
    }
};

// Tipos para el componente
interface AvatarOption {
    emoji: string;
    name: string;
    keywords: string[];
    category: string;
    key: string;
}

interface AvatarSelectorProps {
    selectedAvatar?: string;
    onAvatarSelect: (emoji: string) => void;
    size?: 'sm' | 'md' | 'lg';
    showSearch?: boolean;
    maxDisplayed?: number;
    className?: string;
}

/**
 * Convierte la estructura de avatares en una lista plana para búsqueda
 */
const getAvatarOptions = (): AvatarOption[] => {
    const options: AvatarOption[] = [];
    
    Object.entries(AVATAR_ICONS).forEach(([category, avatars]) => {
        Object.entries(avatars).forEach(([key, avatar]) => {
            options.push({
                ...avatar,
                category,
                key: `${category}_${key}`
            });
        });
    });
    
    return options;
};

/**
 * Componente principal del selector de avatares
 */
const AvatarSelector: React.FC<AvatarSelectorProps> = ({
    selectedAvatar,
    onAvatarSelect,
    size = 'md',
    showSearch = true,
    maxDisplayed = 24,
    className = ''
}) => {
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedCategory, setSelectedCategory] = useState<string>('all');
    
    const allAvatars = useMemo(() => getAvatarOptions(), []);
    const categories = useMemo(() => 
        ['all', ...Object.keys(AVATAR_ICONS)], 
        []
    );
    
    // Filtrar avatares según búsqueda y categoría
    const filteredAvatars = useMemo(() => {
        let filtered = allAvatars;
        
        // Filtrar por categoría
        if (selectedCategory !== 'all') {
            filtered = filtered.filter(avatar => avatar.category === selectedCategory);
        }
        
        // Filtrar por término de búsqueda
        if (searchTerm.trim()) {
            const searchLower = searchTerm.toLowerCase();
            filtered = filtered.filter(avatar => 
                avatar.name.toLowerCase().includes(searchLower) ||
                avatar.keywords.some(keyword => keyword.includes(searchLower))
            );
        }
        
        return filtered.slice(0, maxDisplayed);
    }, [allAvatars, selectedCategory, searchTerm, maxDisplayed]);
    
    // Configuración de tamaños
    const sizeConfig = {
        sm: { container: 'w-8 h-8', emoji: 'text-xl' },
        md: { container: 'w-12 h-12', emoji: 'text-3xl' },
        lg: { container: 'w-16 h-16', emoji: 'text-4xl' }
    };
    
    const currentSize = sizeConfig[size];
    
    // Traducir nombres de categorías
    const categoryNames: Record<string, string> = {
        all: 'Todos',
        people: 'Personas',
        professions: 'Profesiones',
        organizations: 'Organizaciones',
        states: 'Estados'
    };
    
    return (
        <div className={`bg-secondary rounded-lg p-4 ${className}`}>
            {/* Header con búsqueda y categorías */}
            {showSearch && (
                <div className="mb-4 space-y-3">
                    {/* Campo de búsqueda */}
                    <div>
                        <input
                            type="text"
                            placeholder="Buscar avatar..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full px-3 py-2 bg-secondary-light border border-secondary-light rounded-md text-light placeholder-medium focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent text-sm"
                        />
                    </div>
                    
                    {/* Selector de categorías */}
                    <div className="flex flex-wrap gap-2">
                        {categories.map(category => (
                            <button
                                key={category}
                                onClick={() => setSelectedCategory(category)}
                                className={`px-3 py-1 text-xs rounded-full transition-colors ${
                                    selectedCategory === category
                                        ? 'bg-primary text-white'
                                        : 'bg-secondary-light text-medium hover:bg-secondary-light hover:text-light'
                                }`}
                            >
                                {categoryNames[category] || category}
                            </button>
                        ))}
                    </div>
                </div>
            )}
            
            {/* Grid de avatares */}
            <div className="grid grid-cols-6 sm:grid-cols-8 gap-2 max-h-64 overflow-y-auto">
                {filteredAvatars.map((avatar) => (
                    <button
                        key={avatar.key}
                        onClick={() => onAvatarSelect(avatar.emoji)}
                        className={`${currentSize.container} flex items-center justify-center rounded-lg transition-all hover:bg-secondary-light hover:scale-110 ${
                            selectedAvatar === avatar.emoji
                                ? 'bg-primary/20 ring-2 ring-primary scale-105'
                                : 'bg-secondary-light/50 hover:bg-secondary-light'
                        }`}
                        title={avatar.name}
                    >
                        <span className={`${currentSize.emoji} select-none`}>
                            {avatar.emoji}
                        </span>
                    </button>
                ))}
            </div>
            
            {/* Mensaje cuando no hay resultados */}
            {filteredAvatars.length === 0 && (
                <div className="text-center py-8 text-medium">
                    <div className="text-4xl mb-2">🔍</div>
                    <p className="text-sm">No se encontraron avatares</p>
                    {searchTerm && (
                        <button
                            onClick={() => setSearchTerm('')}
                            className="text-xs text-primary hover:underline mt-1"
                        >
                            Limpiar búsqueda
                        </button>
                    )}
                </div>
            )}
            
            {/* Información de resultados */}
            <div className="mt-3 pt-3 border-t border-secondary-light">
                <p className="text-xs text-medium text-center">
                    {filteredAvatars.length} de {allAvatars.length} avatares
                    {maxDisplayed && filteredAvatars.length === maxDisplayed && ' (máximo alcanzado)'}
                </p>
            </div>
        </div>
    );
};

/**
 * Hook para obtener información de un avatar específico
 */
export const useAvatarInfo = (emoji: string) => {
    return useMemo(() => {
        const allAvatars = getAvatarOptions();
        return allAvatars.find(avatar => avatar.emoji === emoji) || null;
    }, [emoji]);
};

/**
 * Función helper para obtener un avatar por defecto según contexto
 */
export const getDefaultAvatar = (context?: 'person' | 'organization' | 'unknown'): string => {
    switch (context) {
        case 'person':
            return AVATAR_ICONS.people.neutral.emoji;
        case 'organization':
            return AVATAR_ICONS.organizations.company.emoji;
        case 'unknown':
        default:
            return AVATAR_ICONS.states.unknown.emoji;
    }
};

/**
 * Componente simplificado para mostrar un avatar con tamaño fijo
 */
export const AvatarDisplay: React.FC<{
    emoji: string;
    size?: 'sm' | 'md' | 'lg';
    className?: string;
    title?: string;
}> = ({ emoji, size = 'md', className = '', title }) => {
    const sizeConfig = {
        sm: 'w-8 h-8 text-xl',
        md: 'w-12 h-12 text-3xl',
        lg: 'w-16 h-16 text-4xl'
    };
    
    return (
        <div 
            className={`${sizeConfig[size]} flex items-center justify-center rounded-lg bg-secondary-light select-none ${className}`}
            title={title}
        >
            <span>{emoji}</span>
        </div>
    );
};

export default AvatarSelector;