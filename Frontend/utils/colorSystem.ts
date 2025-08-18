/**
 * Sistema de Colores Visual para Correlación HUNTER - Operador
 * 
 * Este módulo implementa un sistema determinístico de colores para mapear
 * puntos HUNTER con sus celdas relacionadas, proporcionando consistencia
 * visual durante toda la sesión.
 * 
 * Características:
 * - Hash determinístico basado en nombre del punto
 * - 16 colores pasteles optimizados para tema oscuro
 * - Contraste WCAG AA+ para accesibilidad
 * - Memoización para performance optimizada
 * - Integración con Tailwind CSS
 */

/**
 * Interfaz para definir un color del sistema
 */
export interface ColorDefinition {
    /** Color de fondo pastel para chips */
    background: string;
    /** Color de borde más saturado */
    border: string;
    /** Color de texto con alto contraste */
    text: string;
    /** Nombre descriptivo del color */
    name: string;
}

/**
 * Paleta de 16 colores pasteles optimizada para tema oscuro
 * Cada color garantiza contraste WCAG AA con background oscuro
 * ACTUALIZACIÓN UX BORIS: Saturación optimizada para compatibilidad CDN Tailwind
 */
const COLOR_PALETTE: ColorDefinition[] = [
    {
        background: 'bg-emerald-100/10',
        border: 'border-emerald-400',
        text: 'text-emerald-200',
        name: 'Esmeralda'
    },
    {
        background: 'bg-blue-100/10',
        border: 'border-blue-400',
        text: 'text-blue-200',
        name: 'Azul Cielo'
    },
    {
        background: 'bg-violet-100/10',
        border: 'border-violet-400',
        text: 'text-violet-200',
        name: 'Violeta'
    },
    {
        background: 'bg-rose-100/10',
        border: 'border-rose-400',
        text: 'text-rose-200',
        name: 'Rosa'
    },
    {
        background: 'bg-amber-100/10',
        border: 'border-amber-400',
        text: 'text-amber-200',
        name: 'Ámbar'
    },
    {
        background: 'bg-teal-100/10',
        border: 'border-teal-400',
        text: 'text-teal-200',
        name: 'Verde Azulado'
    },
    {
        background: 'bg-indigo-100/10',
        border: 'border-indigo-400',
        text: 'text-indigo-200',
        name: 'Índigo'
    },
    {
        background: 'bg-pink-100/10',
        border: 'border-pink-400',
        text: 'text-pink-200',
        name: 'Rosa Claro'
    },
    {
        background: 'bg-lime-100/10',
        border: 'border-lime-400',
        text: 'text-lime-200',
        name: 'Lima'
    },
    {
        background: 'bg-cyan-100/10',
        border: 'border-cyan-400',
        text: 'text-cyan-200',
        name: 'Cian'
    },
    {
        background: 'bg-purple-100/10',
        border: 'border-purple-400',
        text: 'text-purple-200',
        name: 'Púrpura'
    },
    {
        background: 'bg-orange-100/10',
        border: 'border-orange-400',
        text: 'text-orange-200',
        name: 'Naranja'
    },
    {
        background: 'bg-green-100/10',
        border: 'border-green-400',
        text: 'text-green-200',
        name: 'Verde'
    },
    {
        background: 'bg-red-100/10',
        border: 'border-red-400',
        text: 'text-red-200',
        name: 'Rojo'
    },
    {
        background: 'bg-yellow-100/10',
        border: 'border-yellow-400',
        text: 'text-yellow-200',
        name: 'Amarillo'
    },
    {
        background: 'bg-slate-100/10',
        border: 'border-slate-400',
        text: 'text-slate-200',
        name: 'Pizarra'
    }
];

/**
 * Cache para memoizar colores ya calculados
 * Mejora performance evitando recálculos del hash
 */
const colorCache = new Map<string, ColorDefinition>();

/**
 * Cache para ordinales de puntos - Sistema ordinal consistente durante sesión
 * Garantiza numeración consistente basada en orden alfabético case-insensitive
 */
const ordinalCache = new Map<string, number>();
let ordinalCounter = 0;

/**
 * Crear mapa de ordinales para puntos HUNTER con ordenamiento case-insensitive
 * Garantiza numeración consistente durante toda la sesión
 * 
 * @param puntos - Array de nombres de puntos HUNTER únicos
 * @returns Map con punto -> número ordinal
 */
export function createPointOrdinalMap(puntos: string[]): Map<string, number> {
    if (!puntos || puntos.length === 0) {
        return new Map();
    }
    
    // Filtrar y ordenar puntos únicos (case-insensitive)
    const uniquePoints = Array.from(new Set(puntos.filter(p => p && p.trim())))
        .sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()));
    
    const ordinalMap = new Map<string, number>();
    
    uniquePoints.forEach((punto, index) => {
        // Verificar si ya tiene ordinal asignado (consistencia de sesión)
        if (ordinalCache.has(punto)) {
            ordinalMap.set(punto, ordinalCache.get(punto)!);
        } else {
            // Asignar nuevo ordinal basado en orden alfabético
            const ordinal = index + 1;
            ordinalCache.set(punto, ordinal);
            ordinalMap.set(punto, ordinal);
            
            // Actualizar contador global
            ordinalCounter = Math.max(ordinalCounter, ordinal);
        }
    });
    
    return ordinalMap;
}

/**
 * Obtiene el número ordinal de un punto específico
 * 
 * @param punto - Nombre del punto HUNTER
 * @returns Número ordinal o null si no está asignado
 */
export function getPointOrdinal(punto: string): number | null {
    if (!punto || typeof punto !== 'string') {
        return null;
    }
    
    return ordinalCache.get(punto) || null;
}

/**
 * Limpia el cache de ordinales (útil para testing o cambio de misión)
 */
export function clearOrdinalCache(): void {
    ordinalCache.clear();
    ordinalCounter = 0;
}

/**
 * Función hash determinística optimizada
 * Genera un hash consistente para el mismo input
 * 
 * @param input - String para generar hash (nombre del punto)
 * @returns Número hash positivo
 */
function deterministicHash(input: string): number {
    let hash = 0;
    
    // Normalizar input para consistencia
    const normalized = input.toString().toLowerCase().trim();
    
    if (normalized.length === 0) {
        return 0;
    }
    
    // Algoritmo de hash DJB2 modificado para mejor distribución
    for (let i = 0; i < normalized.length; i++) {
        const char = normalized.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32-bit integer
    }
    
    // Asegurar valor positivo
    return Math.abs(hash);
}

/**
 * Obtiene un color determinístico para un punto específico
 * Garantiza que el mismo punto siempre tenga el mismo color
 * durante toda la sesión
 * 
 * @param punto - Nombre del punto HUNTER
 * @returns Definición de color completa
 */
export function getPointColor(punto: string): ColorDefinition {
    // Validación de entrada
    if (!punto || typeof punto !== 'string') {
        return COLOR_PALETTE[0]; // Color por defecto
    }
    
    // Verificar cache primero (memoización)
    if (colorCache.has(punto)) {
        return colorCache.get(punto)!;
    }
    
    // Calcular hash y seleccionar color
    const hash = deterministicHash(punto);
    const colorIndex = hash % COLOR_PALETTE.length;
    const selectedColor = COLOR_PALETTE[colorIndex];
    
    // Guardar en cache para próximas consultas
    colorCache.set(punto, selectedColor);
    
    return selectedColor;
}

/**
 * Obtiene las clases CSS completas para un chip de punto
 * Incluye background pastel, borde saturado y texto con alto contraste
 * 
 * @param punto - Nombre del punto HUNTER
 * @returns String con clases Tailwind CSS
 */
export function getPointChipClasses(punto: string): string {
    const color = getPointColor(punto);
    
    const baseClasses = [
        'inline-flex',
        'items-center',
        'px-2',
        'py-1',
        'text-xs',
        'font-medium',
        'rounded-md',
        'border',
        'transition-all',
        'duration-200',
        'hover:scale-105',
        'hover:shadow-lg',
        'cursor-default'
    ];
    
    return [
        ...baseClasses,
        color.background,
        color.border,
        color.text
    ].join(' ');
}

/**
 * Mapea Cell IDs de correlación a sus puntos HUNTER originales
 * Busca en los datos celulares para establecer la relación
 * 
 * @param cellId - ID de celda a buscar
 * @param cellularData - Array de datos celulares de la misión
 * @returns Nombre del punto HUNTER o null si no se encuentra
 */
export function getCellIdToPointMapping(
    cellId: string,
    cellularData: Array<{ cellId: string; punto: string }>
): string | null {
    // Validar parámetros
    if (!cellId || !cellularData || cellularData.length === 0) {
        return null;
    }
    
    // Buscar coincidencia exacta primero
    const exactMatch = cellularData.find(record => record.cellId === cellId);
    if (exactMatch) {
        return exactMatch.punto;
    }
    
    // Buscar coincidencia parcial (útil para formatos variables)
    const partialMatch = cellularData.find(record => 
        record.cellId && record.cellId.includes(cellId)
    );
    
    return partialMatch ? partialMatch.punto : null;
}

/**
 * Obtiene el color de borde para una celda relacionada
 * basado en su punto HUNTER de origen
 * 
 * @param cellId - ID de la celda
 * @param cellularData - Datos celulares para el mapeo
 * @returns String con clase CSS de borde o string vacío si no hay mapeo
 */
export function getCellBorderColor(
    cellId: string,
    cellularData: Array<{ cellId: string; punto: string }>
): string {
    const punto = getCellIdToPointMapping(cellId, cellularData);
    
    if (!punto) {
        return ''; // Sin borde adicional si no hay mapeo
    }
    
    const color = getPointColor(punto);
    return color.border;
}

/**
 * Genera clases CSS para badges de celdas relacionadas
 * Combina el color de rol (azul/violeta) con borde del punto
 * 
 * ACTUALIZACIÓN UX BORIS: Colores suaves amables a la vista, consistentes con roles de comunicación
 * 
 * @param cellId - ID de la celda
 * @param role - Rol de la celda ('originator' | 'receptor')
 * @param cellularData - Datos celulares para el mapeo
 * @returns String con clases CSS completas
 */
export function getCorrelationCellClasses(
    cellId: string,
    role: 'originator' | 'receptor',
    cellularData: Array<{ cellId: string; punto: string }>
): string {
    // Clases base según el rol - ACTUALIZACIÓN UX BORIS: Colores suaves /20 para fondos amables
    const baseClasses = role === 'originator'
        ? 'px-2 py-1 text-xs bg-blue-500/20 text-blue-300 border border-blue-400/30 rounded font-mono transition-all duration-200 hover:bg-blue-500/30 hover:scale-105 hover:shadow-lg cursor-pointer'
        : 'px-2 py-1 text-xs bg-purple-500/20 text-purple-300 border border-purple-400/30 rounded font-mono transition-all duration-200 hover:bg-purple-500/30 hover:scale-105 hover:shadow-lg cursor-pointer';
    
    // Obtener color de borde del punto
    const borderColor = getCellBorderColor(cellId, cellularData);
    
    if (borderColor) {
        // ACTUALIZACIÓN UX BORIS: Bordes 2px del punto HUNTER para identificación clara
        return `${baseClasses} border-2 ${borderColor} shadow-lg`;
    }
    
    // Si no hay mapeo, usar borde gris suave consistente con el nuevo sistema
    return `${baseClasses} border-2 border-gray-400/30 shadow-lg`;
}

/**
 * Estadísticas del sistema de colores para debugging
 * Útil para monitorear el uso de la paleta de colores
 * 
 * @returns Objeto con estadísticas del cache
 */
export function getColorSystemStats(): {
    totalCachedPoints: number;
    colorsInUse: number;
    cacheHitRate: number;
} {
    const uniqueColors = new Set(Array.from(colorCache.values()).map(c => c.name));
    
    return {
        totalCachedPoints: colorCache.size,
        colorsInUse: uniqueColors.size,
        cacheHitRate: colorCache.size > 0 ? (colorCache.size / COLOR_PALETTE.length) * 100 : 0
    };
}

/**
 * Limpia el cache de colores
 * Útil para testing o cuando se cambia de misión
 */
export function clearColorCache(): void {
    colorCache.clear();
}

/**
 * Limpia todos los caches (colores y ordinales)
 * Función de conveniencia para reset completo
 */
export function clearAllCaches(): void {
    clearColorCache();
    clearOrdinalCache();
}

/**
 * Exporta la paleta completa para casos especiales
 * No recomendado para uso directo, preferir getPointColor()
 */
export { COLOR_PALETTE };