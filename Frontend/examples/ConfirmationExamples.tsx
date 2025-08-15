import React from 'react';
import { useConfirmation, confirmationPresets } from '../hooks/useConfirmation';
import { ICONS } from '../constants';

/**
 * Ejemplos de uso del sistema de confirmación de KRONOS
 * Este archivo muestra cómo reemplazar window.confirm() con el nuevo sistema
 * 
 * IMPORTANTE: Este archivo es solo para referencia y documentación.
 * Eliminar después de implementar en los componentes reales.
 */

const ConfirmationExamples: React.FC = () => {
    const { showConfirmation } = useConfirmation();

    /**
     * EJEMPLO 1: Eliminación de misión con preset
     */
    const handleDeleteMissionWithPreset = async () => {
        const confirmed = await showConfirmation(
            confirmationPresets.deleteMission("Misión Norte 2024")
        );
        
        if (confirmed) {
            console.log('Misión eliminada');
            // Aquí iría la lógica de eliminación
        }
    };

    /**
     * EJEMPLO 2: Confirmación personalizada para eliminar usuario
     */
    const handleDeleteUserCustom = async () => {
        const confirmed = await showConfirmation({
            type: 'destructive',
            title: 'Eliminar Usuario',
            message: '¿Estás seguro de que deseas eliminar al usuario "Boris González"?',
            details: 'Esta acción es irreversible. El usuario perderá acceso inmediatamente y todos sus datos de sesión se borrarán.',
            confirmText: 'Sí, Eliminar',
            cancelText: 'No, Cancelar',
            confirmButtonVariant: 'danger',
            onConfirm: () => {
                // Lógica adicional antes de resolver la promesa
                console.log('Ejecutando onConfirm...');
            },
            onCancel: () => {
                console.log('Cancelación confirmada');
            }
        });

        if (confirmed) {
            console.log('Usuario eliminado');
        }
    };

    /**
     * EJEMPLO 3: Confirmación de warning para datos celulares
     */
    const handleClearCellularData = async () => {
        const confirmed = await showConfirmation(
            confirmationPresets.clearCellularData(1250)
        );
        
        if (confirmed) {
            console.log('Datos celulares borrados');
        }
    };

    /**
     * EJEMPLO 4: Confirmación de información
     */
    const handleInfoConfirmation = async () => {
        const confirmed = await showConfirmation({
            type: 'info',
            title: 'Exportar Datos',
            message: '¿Deseas exportar los datos actuales a Excel?',
            details: 'Se generará un archivo con todos los registros filtrados actualmente visibles en la tabla.',
            confirmText: 'Exportar',
            cancelText: 'Cancelar',
            confirmButtonVariant: 'primary'
        });
        
        if (confirmed) {
            console.log('Exportando datos...');
        }
    };

    /**
     * EJEMPLO 5: Reemplazo directo de window.confirm()
     * 
     * ANTES:
     * if (window.confirm('¿Eliminar este archivo?')) {
     *   deleteFile();
     * }
     * 
     * DESPUÉS:
     */
    const handleReplaceWindowConfirm = async () => {
        const confirmed = await showConfirmation({
            type: 'warning',
            title: 'Confirmar Acción',
            message: '¿Eliminar este archivo?',
            confirmText: 'Sí',
            cancelText: 'No'
        });
        
        if (confirmed) {
            console.log('Archivo eliminado');
        }
    };

    /**
     * EJEMPLO 6: Confirmación con backdrop click deshabilitado
     */
    const handleImportantAction = async () => {
        const confirmed = await showConfirmation({
            type: 'danger',
            title: 'Acción Crítica',
            message: 'Esta operación afectará permanentemente la base de datos.',
            details: 'Por favor, confirma explícitamente esta acción. No es posible cancelar haciendo clic fuera del modal.',
            confirmText: 'Entiendo, Continuar',
            cancelText: 'Cancelar',
            allowBackdropClick: false, // Deshabilitado para acciones críticas
            showIcon: true
        });
        
        if (confirmed) {
            console.log('Acción crítica confirmada');
        }
    };

    return (
        <div className="p-6 bg-slate-900 min-h-screen">
            <div className="max-w-4xl mx-auto">
                <h1 className="text-2xl font-bold text-slate-100 mb-6">
                    Ejemplos del Sistema de Confirmación KRONOS
                </h1>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <button
                        onClick={handleDeleteMissionWithPreset}
                        className="p-4 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors flex items-center gap-2"
                    >
                        {ICONS.trash}
                        Eliminar Misión (Preset)
                    </button>

                    <button
                        onClick={handleDeleteUserCustom}
                        className="p-4 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors flex items-center gap-2"
                    >
                        {ICONS.trash}
                        Eliminar Usuario (Personalizado)
                    </button>

                    <button
                        onClick={handleClearCellularData}
                        className="p-4 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg transition-colors flex items-center gap-2"
                    >
                        {ICONS.database}
                        Borrar Datos Celulares
                    </button>

                    <button
                        onClick={handleInfoConfirmation}
                        className="p-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center gap-2"
                    >
                        {ICONS.download}
                        Exportar Datos (Info)
                    </button>

                    <button
                        onClick={handleReplaceWindowConfirm}
                        className="p-4 bg-slate-600 hover:bg-slate-700 text-white rounded-lg transition-colors flex items-center gap-2"
                    >
                        {ICONS.document}
                        Reemplazo window.confirm()
                    </button>

                    <button
                        onClick={handleImportantAction}
                        className="p-4 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors flex items-center gap-2"
                    >
                        {ICONS.shield}
                        Acción Crítica
                    </button>
                </div>

                {/* Documentación de código */}
                <div className="mt-8 bg-slate-800 rounded-lg p-6">
                    <h2 className="text-lg font-semibold text-slate-100 mb-4">
                        Cómo Integrar en App.tsx
                    </h2>
                    <pre className="bg-slate-900 rounded p-4 text-sm text-slate-300 overflow-x-auto">
{`// En App.tsx, envuelve tu aplicación con ConfirmationProvider:

import { ConfirmationProvider } from './hooks/useConfirmation';

function App() {
  return (
    <ConfirmationProvider>
      <div className="App">
        {/* Tu aplicación aquí */}
        <HashRouter>
          <Routes>
            {/* Tus rutas */}
          </Routes>
        </HashRouter>
      </div>
    </ConfirmationProvider>
  );
}

export default App;`}
                    </pre>
                </div>

                <div className="mt-6 bg-slate-800 rounded-lg p-6">
                    <h2 className="text-lg font-semibold text-slate-100 mb-4">
                        Uso en Componentes
                    </h2>
                    <pre className="bg-slate-900 rounded p-4 text-sm text-slate-300 overflow-x-auto">
{`// En cualquier componente:

import { useConfirmation, confirmationPresets } from '../hooks/useConfirmation';

const MissionList = () => {
  const { showConfirmation } = useConfirmation();

  const handleDeleteMission = async (mission) => {
    const confirmed = await showConfirmation(
      confirmationPresets.deleteMission(mission.name)
    );
    
    if (confirmed) {
      // Eliminar misión
      await deleteMission(mission.id);
    }
  };

  return (
    // Tu JSX aquí
  );
};`}
                    </pre>
                </div>
            </div>
        </div>
    );
};

export default ConfirmationExamples;