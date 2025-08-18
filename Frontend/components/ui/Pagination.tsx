import React from 'react';
import { ICONS } from '../../constants';

interface PaginationProps {
    currentPage: number;
    totalItems: number;
    itemsPerPage: number;
    onPageChange: (page: number) => void;
    onItemsPerPageChange: (items: number) => void;
    showItemsPerPage?: boolean;
    className?: string;
}

const Pagination: React.FC<PaginationProps> = ({
    currentPage,
    totalItems,
    itemsPerPage,
    onPageChange,
    onItemsPerPageChange,
    showItemsPerPage = true,
    className = ''
}) => {
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    
    // Validaciones
    if (totalItems === 0) {
        return null;
    }
    
    // Calcular rango de elementos mostrados
    const startItem = Math.min((currentPage - 1) * itemsPerPage + 1, totalItems);
    const endItem = Math.min(currentPage * itemsPerPage, totalItems);
    
    // Calcular páginas a mostrar (lógica de ventana deslizante)
    const getPageNumbers = () => {
        const delta = 2; // Número de páginas a mostrar a cada lado de la página actual
        const range = [];
        const rangeWithDots = [];

        // Siempre mostrar la primera página
        range.push(1);
        
        // Calcular rango alrededor de la página actual
        for (let i = Math.max(2, currentPage - delta); i <= Math.min(totalPages - 1, currentPage + delta); i++) {
            range.push(i);
        }
        
        // Siempre mostrar la última página (si hay más de una)
        if (totalPages > 1) {
            range.push(totalPages);
        }
        
        // Agregar puntos suspensivos donde sea necesario
        let prev = 0;
        range.forEach(num => {
            if (num - prev === 2) {
                rangeWithDots.push(prev + 1);
            } else if (num - prev !== 1) {
                rangeWithDots.push('...');
            }
            rangeWithDots.push(num);
            prev = num;
        });
        
        return rangeWithDots;
    };
    
    const pageNumbers = getPageNumbers();
    
    // Opciones para elementos por página
    const itemsPerPageOptions = [10, 25, 50, 100];
    
    return (
        <div className={`flex flex-col sm:flex-row items-center justify-between gap-4 p-4 bg-secondary-light rounded-lg ${className}`}>
            {/* Información de elementos mostrados */}
            <div className="flex items-center gap-4 text-sm text-medium">
                <span>
                    Mostrando {startItem.toLocaleString()}-{endItem.toLocaleString()} de {totalItems.toLocaleString()} resultados
                </span>
                
                {showItemsPerPage && (
                    <div className="flex items-center gap-2">
                        <label className="whitespace-nowrap">Mostrar:</label>
                        <select
                            value={itemsPerPage}
                            onChange={(e) => {
                                const newItemsPerPage = parseInt(e.target.value);
                                // Ajustar página actual para mantener al usuario en contexto similar
                                const newPage = Math.ceil(startItem / newItemsPerPage);
                                onItemsPerPageChange(newItemsPerPage);
                                onPageChange(newPage);
                            }}
                            className="px-2 py-1 bg-secondary border border-secondary-light rounded text-light text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                        >
                            {itemsPerPageOptions.map(option => (
                                <option key={option} value={option}>
                                    {option}
                                </option>
                            ))}
                        </select>
                        <span className="text-xs text-medium">por página</span>
                    </div>
                )}
            </div>
            
            {/* Controles de navegación */}
            <div className="flex items-center gap-1">
                {/* Botón Primera Página */}
                <button
                    onClick={() => onPageChange(1)}
                    disabled={currentPage === 1}
                    className="px-3 py-2 text-sm rounded-md border border-secondary-light bg-secondary text-light hover:bg-secondary-light disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    title="Primera página"
                >
                    <span className="hidden sm:inline">Primera</span>
                    <span className="sm:hidden">«</span>
                </button>
                
                {/* Botón Página Anterior */}
                <button
                    onClick={() => onPageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                    className="px-3 py-2 text-sm rounded-md border border-secondary-light bg-secondary text-light hover:bg-secondary-light disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    title="Página anterior"
                >
                    <span className="hidden sm:inline">Anterior</span>
                    <span className="sm:hidden">‹</span>
                </button>
                
                {/* Números de página */}
                <div className="hidden sm:flex items-center gap-1 mx-2">
                    {pageNumbers.map((pageNum, index) => (
                        <React.Fragment key={index}>
                            {pageNum === '...' ? (
                                <span className="px-3 py-2 text-sm text-medium">...</span>
                            ) : (
                                <button
                                    onClick={() => onPageChange(pageNum as number)}
                                    className={`px-3 py-2 text-sm rounded-md border transition-colors ${
                                        currentPage === pageNum
                                            ? 'bg-primary text-white border-primary'
                                            : 'border-secondary-light bg-secondary text-light hover:bg-secondary-light'
                                    }`}
                                >
                                    {pageNum}
                                </button>
                            )}
                        </React.Fragment>
                    ))}
                </div>
                
                {/* Indicador de página actual en móvil */}
                <div className="sm:hidden flex items-center px-3 py-2 text-sm text-light bg-secondary-light rounded-md">
                    {currentPage} de {totalPages}
                </div>
                
                {/* Botón Página Siguiente */}
                <button
                    onClick={() => onPageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    className="px-3 py-2 text-sm rounded-md border border-secondary-light bg-secondary text-light hover:bg-secondary-light disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    title="Página siguiente"
                >
                    <span className="hidden sm:inline">Siguiente</span>
                    <span className="sm:hidden">›</span>
                </button>
                
                {/* Botón Última Página */}
                <button
                    onClick={() => onPageChange(totalPages)}
                    disabled={currentPage === totalPages}
                    className="px-3 py-2 text-sm rounded-md border border-secondary-light bg-secondary text-light hover:bg-secondary-light disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    title="Última página"
                >
                    <span className="hidden sm:inline">Última</span>
                    <span className="sm:hidden">»</span>
                </button>
            </div>
        </div>
    );
};

export default Pagination;