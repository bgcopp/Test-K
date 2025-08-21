/**
 * Hook useExportFunctionality - Maneja exportación de diagramas React Flow
 * Soporta formatos PNG, SVG y JSON
 * Actualizado: 2025-08-20 por Boris - Funcionalidad de exportación completa
 */

import { useCallback } from 'react';
import { toPng, toSvg } from 'html-to-image';
import { useReactFlow } from '@xyflow/react';
import { ExportConfig, PhoneFlowNode, PhoneFlowEdge } from '../types/reactflow.types';

interface ExportFunctionalityProps {
  nodes: PhoneFlowNode[];
  edges: PhoneFlowEdge[];
  targetNumber: string;
}

/**
 * Hook para manejar todas las funcionalidades de exportación
 */
export const useExportFunctionality = ({
  nodes,
  edges,
  targetNumber
}: ExportFunctionalityProps) => {
  
  const { getViewport } = useReactFlow();

  /**
   * Generar nombre de archivo con timestamp
   */
  const generateFileName = useCallback((format: string, prefix: string = 'diagrama-correlacion') => {
    const timestamp = new Date().toISOString().slice(0, 19).replace(/[:]/g, '-');
    return `${prefix}_${targetNumber}_${timestamp}.${format.toLowerCase()}`;
  }, [targetNumber]);

  /**
   * Exportar diagrama como imagen PNG
   */
  const exportToPNG = useCallback(async (config?: Partial<ExportConfig>) => {
    try {
      const defaultConfig: ExportConfig = {
        format: 'PNG',
        filename: generateFileName('png'),
        includeBackground: true,
        includeControls: false,
        resolution: 150
      };

      const finalConfig = { ...defaultConfig, ...config };

      // Obtener el elemento del contenedor React Flow
      const reactFlowElement = document.querySelector('.react-flow') as HTMLElement;
      if (!reactFlowElement) {
        throw new Error('No se encontró el elemento React Flow');
      }

      // Configurar opciones de captura (tamaño estándar)
      const captureOptions = {
        backgroundColor: finalConfig.includeBackground ? '#0f172a' : 'transparent',
        width: 1400, // Ancho fijo del contenedor
        height: 800, // Alto fijo del contenedor
        pixelRatio: finalConfig.resolution / 72, // Convertir DPI a pixel ratio
        filter: (node: Element) => {
          // Excluir controles si se especifica
          if (!finalConfig.includeControls) {
            return !node.classList?.contains('react-flow__controls') &&
                   !node.classList?.contains('react-flow__panel');
          }
          return true;
        }
      };

      console.log('🖼️ Exportando PNG:', {
        filename: finalConfig.filename,
        dimensions: `${captureOptions.width}x${captureOptions.height}`,
        resolution: finalConfig.resolution
      });

      // Generar imagen PNG
      const dataUrl = await toPng(reactFlowElement, captureOptions);
      
      // Descargar archivo
      const link = document.createElement('a');
      link.download = finalConfig.filename;
      link.href = dataUrl;
      link.click();

      console.log('✅ PNG exportado exitosamente');
      return { success: true, filename: finalConfig.filename };

    } catch (error) {
      console.error('❌ Error exportando PNG:', error);
      return { success: false, error: error.message };
    }
  }, [nodes, generateFileName]);

  /**
   * Exportar diagrama como SVG vectorial
   */
  const exportToSVG = useCallback(async (config?: Partial<ExportConfig>) => {
    try {
      const defaultConfig: ExportConfig = {
        format: 'SVG',
        filename: generateFileName('svg'),
        includeBackground: true,
        includeControls: false,
        resolution: 150
      };

      const finalConfig = { ...defaultConfig, ...config };

      // Obtener el elemento del contenedor React Flow
      const reactFlowElement = document.querySelector('.react-flow') as HTMLElement;
      if (!reactFlowElement) {
        throw new Error('No se encontró el elemento React Flow');
      }

      // Configurar opciones de captura SVG
      const captureOptions = {
        backgroundColor: finalConfig.includeBackground ? '#0f172a' : 'transparent',
        filter: (node: Element) => {
          if (!finalConfig.includeControls) {
            return !node.classList?.contains('react-flow__controls') &&
                   !node.classList?.contains('react-flow__panel');
          }
          return true;
        }
      };

      console.log('🖼️ Exportando SVG:', {
        filename: finalConfig.filename
      });

      // Generar imagen SVG
      const dataUrl = await toSvg(reactFlowElement, captureOptions);
      
      // Descargar archivo
      const link = document.createElement('a');
      link.download = finalConfig.filename;
      link.href = dataUrl;
      link.click();

      console.log('✅ SVG exportado exitosamente');
      return { success: true, filename: finalConfig.filename };

    } catch (error) {
      console.error('❌ Error exportando SVG:', error);
      return { success: false, error: error.message };
    }
  }, [generateFileName]);

  /**
   * Exportar datos del diagrama como JSON
   */
  const exportToJSON = useCallback(async (config?: Partial<ExportConfig>) => {
    try {
      const defaultConfig: ExportConfig = {
        format: 'JSON',
        filename: generateFileName('json'),
        includeBackground: false,
        includeControls: false,
        resolution: 72
      };

      const finalConfig = { ...defaultConfig, ...config };

      // Preparar datos para exportación
      const exportData = {
        metadata: {
          exportDate: new Date().toISOString(),
          targetNumber: targetNumber,
          totalNodes: nodes.length,
          totalEdges: edges.length,
          format: 'KRONOS Diagram JSON v1.0'
        },
        viewport: getViewport(),
        nodes: nodes.map(node => ({
          id: node.id,
          position: node.position,
          data: {
            phoneNumber: node.data.phoneNumber,
            isTarget: node.data.isTarget,
            correlationLevel: node.data.correlationLevel,
            color: node.data.color,
            stats: node.data.stats
          }
        })),
        edges: edges.map(edge => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          data: {
            cellIds: edge.data.cellIds,
            direction: edge.data.direction,
            callCount: edge.data.callCount,
            strength: edge.data.strength,
            color: edge.data.color
          }
        }))
      };

      console.log('📄 Exportando JSON:', {
        filename: finalConfig.filename,
        dataSize: `${JSON.stringify(exportData).length} characters`
      });

      // Convertir a JSON string
      const jsonString = JSON.stringify(exportData, null, 2);
      
      // Crear blob y descargar
      const blob = new Blob([jsonString], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.download = finalConfig.filename;
      link.href = url;
      link.click();
      
      // Limpiar URL
      URL.revokeObjectURL(url);

      console.log('✅ JSON exportado exitosamente');
      return { success: true, filename: finalConfig.filename, data: exportData };

    } catch (error) {
      console.error('❌ Error exportando JSON:', error);
      return { success: false, error: error.message };
    }
  }, [nodes, edges, targetNumber, generateFileName, getViewport]);

  /**
   * Función unificada de exportación que maneja todos los formatos
   */
  const exportDiagram = useCallback(async (format: 'PNG' | 'SVG' | 'JSON', config?: Partial<ExportConfig>) => {
    switch (format) {
      case 'PNG':
        return await exportToPNG(config);
      case 'SVG':
        return await exportToSVG(config);
      case 'JSON':
        return await exportToJSON(config);
      default:
        throw new Error(`Formato no soportado: ${format}`);
    }
  }, [exportToPNG, exportToSVG, exportToJSON]);

  return {
    exportToPNG,
    exportToSVG,
    exportToJSON,
    exportDiagram,
    generateFileName
  };
};

export default useExportFunctionality;