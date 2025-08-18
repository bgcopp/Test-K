import type { CorrelationResult } from '../types';

/**
 * Función utilitaria para exportar resultados de correlación a CSV
 * IMPORTANTE: Esta función exporta TODOS los datos, independiente de la paginación
 * @param results - Array completo de resultados de correlación (sin paginar)
 * @param filteredResults - Array filtrado de resultados (puede ser diferente si hay filtros activos)
 * @param filename - Nombre del archivo (opcional)
 */
export const exportCorrelationResultsToCSV = (
    results: CorrelationResult[],
    filteredResults: CorrelationResult[],
    filename: string = `correlacion_resultados_${new Date().toISOString().split('T')[0]}.csv`
) => {
    // Usar todos los resultados si no hay filtros, o los filtrados si los hay
    const dataToExport = filteredResults.length === results.length ? results : filteredResults;
    
    if (dataToExport.length === 0) {
        console.warn('No hay datos para exportar');
        return;
    }
    
    // Headers CSV
    const csvHeaders = [
        'Número Objetivo',
        'Operador', 
        'Ocurrencias',
        'Primera Detección',
        'Última Detección',
        'Celdas Relacionadas',
        'Nivel de Confianza'
    ];
    
    // Convertir datos a formato CSV
    const csvData = dataToExport.map(result => [
        result.targetNumber,
        result.operator,
        result.occurrences,
        new Date(result.firstDetection).toLocaleString('es-ES'),
        new Date(result.lastDetection).toLocaleString('es-ES'),
        (result.relatedCells || []).join('; '), // Unir celdas con punto y coma
        `${result.confidence.toFixed(1)}%`
    ]);
    
    // Crear contenido CSV completo
    const csvContent = [
        csvHeaders.join(','),
        ...csvData.map(row => 
            row.map(cell => 
                // Escapar celdas que contengan comas, comillas o saltos de línea
                typeof cell === 'string' && (cell.includes(',') || cell.includes('"') || cell.includes('\n'))
                    ? `"${cell.replace(/"/g, '""')}"` // Escapar comillas duplicándolas
                    : cell
            ).join(',')
        )
    ].join('\n');
    
    // Crear y descargar archivo
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Limpiar URL objeto
    URL.revokeObjectURL(url);
    
    console.log(`✅ Exportación completada: ${dataToExport.length} registros exportados a ${filename}`);
    
    return {
        exportedRecords: dataToExport.length,
        totalRecords: results.length,
        isFiltered: filteredResults.length !== results.length,
        filename
    };
};

/**
 * Función para formatear fechas de manera consistente
 */
export const formatDateForExport = (dateStr: string): string => {
    const date = new Date(dateStr);
    return date.toLocaleString('es-ES', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
};

/**
 * Función helper para obtener estadísticas de exportación
 */
export const getExportStats = (results: CorrelationResult[], filteredResults: CorrelationResult[]) => {
    const operatorStats = filteredResults.reduce((acc, result) => {
        acc[result.operator] = (acc[result.operator] || 0) + 1;
        return acc;
    }, {} as Record<string, number>);
    
    const totalOccurrences = filteredResults.reduce((sum, result) => sum + result.occurrences, 0);
    
    return {
        totalResults: filteredResults.length,
        totalOriginalResults: results.length,
        isFiltered: filteredResults.length !== results.length,
        operatorStats,
        totalOccurrences,
        averageOccurrences: filteredResults.length > 0 ? (totalOccurrences / filteredResults.length).toFixed(2) : '0',
        dateRange: {
            earliest: filteredResults.length > 0 ? 
                new Date(Math.min(...filteredResults.map(r => new Date(r.firstDetection).getTime()))).toLocaleString('es-ES') : null,
            latest: filteredResults.length > 0 ?
                new Date(Math.max(...filteredResults.map(r => new Date(r.lastDetection).getTime()))).toLocaleString('es-ES') : null
        }
    };
};