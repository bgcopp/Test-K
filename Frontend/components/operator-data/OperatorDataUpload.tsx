import React, { useState, useRef } from 'react';
import Button from '../ui/Button';
import { ICONS } from '../../constants';
import type { OperatorUploadResponse, OperatorConfig, DocumentTypeConfig } from '../../types';
import { uploadOperatorData } from '../../services/api';

interface OperatorDataUploadProps {
    missionId: string;
    onUploadSuccess: (response: OperatorUploadResponse) => void;
    onUploadStart?: () => void;
    onUploadError?: (error: string) => void;
}

// Configuración de operadores y tipos de documentos
const OPERATORS: Record<string, OperatorConfig> = {
    CLARO: {
        name: 'CLARO',
        documentTypes: [
            { 
                id: 'CELLULAR_DATA', 
                name: 'Información de Datos por Celda', 
                description: 'Actividad de datos en celdas celulares por número móvil. Incluye: número, fecha_trafico, tipo_cdr, celda_decimal, lac_decimal.',
                formats: 'XLSX, CSV',
                columns: ['numero', 'fecha_trafico', 'tipo_cdr', 'celda_decimal', 'lac_decimal']
            },
            { 
                id: 'CALL_DATA', 
                name: 'Información de Llamadas (Entrantes y Salientes)', 
                description: 'Actividad de llamadas por celda. El sistema detecta automáticamente si son entrantes o salientes. Incluye: celda_inicio_llamada, celda_final_llamada, originador, receptor, fecha_hora, duracion, tipo.',
                formats: 'XLSX, CSV',
                columns: ['celda_inicio_llamada', 'celda_final_llamada', 'originador', 'receptor', 'fecha_hora', 'duracion', 'tipo']
            }
        ]
    },
    MOVISTAR: {
        name: 'MOVISTAR',
        documentTypes: [
            { 
                id: 'CELLULAR_DATA', 
                name: 'Información de Datos por Celda', 
                description: 'Actividad de datos en celdas celulares con información geográfica extendida. Incluye información de ubicación, tecnología y tráfico de datos.',
                formats: 'XLSX, CSV',
                columns: ['numero_que_navega', 'ruta_entrante', 'celda', 'trafico_de_subida', 'trafico_de_bajada', 'fecha_hora_inicio_sesion', 'duracion', 'tipo_tecnologia', 'departamento', 'localidad', 'latitud_n', 'longitud_w']
            },
            { 
                id: 'CALL_DATA', 
                name: 'Información de Llamadas Salientes', 
                description: 'Actividad de llamadas salientes con información detallada de red y geolocalización (25 campos técnicos).',
                formats: 'XLSX, CSV',
                columns: ['Múltiples campos de red y geolocalización']
            }
        ]
    },
    TIGO: {
        name: 'TIGO',
        documentTypes: [
            { 
                id: 'CALL_DATA', 
                name: 'Información de Llamadas (Unificadas)', 
                description: 'Información unificada de llamadas (entrantes y salientes). Archivos XLSX con 3 pestañas o CSV. El campo DIRECCION indica O=SALIENTE, I=ENTRANTE.',
                formats: 'XLSX (3 pestañas), CSV',
                columns: ['TIPO_DE_LLAMADA', 'NUMERO A', 'NUMERO MARCADO', 'DIRECCION: O SALIENTE, I ENTRANTE', 'DURACION TOTAL seg', 'FECHA Y HORA ORIGEN', 'CELDA_ORIGEN_TRUNCADA', 'TECH']
            }
        ]
    },
    WOM: {
        name: 'WOM',
        documentTypes: [
            { 
                id: 'CELLULAR_DATA', 
                name: 'Información de Datos por Celda', 
                description: 'Actividad de datos con información técnica detallada (24 campos). Archivos XLSX con 2 pestañas o CSV.',
                formats: 'XLSX (2 pestañas), CSV',
                columns: ['24 campos técnicos incluyendo IMSI, IMEI, coordenadas y datos de sesión']
            },
            { 
                id: 'CALL_DATA', 
                name: 'Información de Llamadas (Unificadas)', 
                description: 'Llamadas entrantes y salientes con información técnica de red (23 campos). Archivos XLSX con 2 pestañas o CSV. El campo SENTIDO indica el tipo.',
                formats: 'XLSX (2 pestañas), CSV',
                columns: ['23 campos técnicos y geográficos para llamadas']
            }
        ]
    }
};

const MAX_FILE_SIZE = 20 * 1024 * 1024; // 20MB
const ACCEPTED_EXTENSIONS = ['.csv', '.xlsx', '.xls'];

const OperatorDataUpload: React.FC<OperatorDataUploadProps> = ({
    missionId,
    onUploadSuccess,
    onUploadStart,
    onUploadError
}) => {
    const [selectedOperator, setSelectedOperator] = useState<string>('');
    const [selectedDocumentType, setSelectedDocumentType] = useState<string>('');
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [dragActive, setDragActive] = useState(false);
    const [errors, setErrors] = useState<string[]>([]);
    
    const fileInputRef = useRef<HTMLInputElement>(null);

    const validateFile = (file: File): string[] => {
        const errors: string[] = [];
        
        // Validar tamaño
        if (file.size > MAX_FILE_SIZE) {
            errors.push(`El archivo es muy grande. Tamaño máximo: ${MAX_FILE_SIZE / (1024 * 1024)}MB`);
        }
        
        // Validar extensión
        const extension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
        if (!ACCEPTED_EXTENSIONS.includes(extension)) {
            errors.push(`Formato no soportado. Formatos aceptados: ${ACCEPTED_EXTENSIONS.join(', ')}`);
        }
        
        return errors;
    };

    const handleFileSelect = (file: File) => {
        const validationErrors = validateFile(file);
        setErrors(validationErrors);
        
        if (validationErrors.length === 0) {
            setSelectedFile(file);
        } else {
            setSelectedFile(null);
        }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            handleFileSelect(e.target.files[0]);
        }
    };

    const handleDragEnter = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(true);
    };

    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    };

    const handleUpload = async () => {
        if (!selectedFile || !selectedOperator || !selectedDocumentType) {
            return;
        }
        
        setIsUploading(true);
        setUploadProgress(0);
        onUploadStart?.();
        
        try {
            // Simular progreso
            const progressInterval = setInterval(() => {
                setUploadProgress(prev => {
                    if (prev >= 90) {
                        clearInterval(progressInterval);
                        return 90;
                    }
                    return prev + 10;
                });
            }, 200);
            
            console.log('🔍 UPLOAD COMPONENT: Iniciando upload con:', {
                selectedOperator,
                selectedDocumentType,
                fileName: selectedFile.name
            });
            
            // Usar la función de API importada estáticamente
            const response = await uploadOperatorData(missionId, selectedOperator, selectedDocumentType, selectedFile);
            
            console.log('📥 UPLOAD COMPONENT: Respuesta recibida:', response);
            console.log('📊 UPLOAD COMPONENT: processedRecords:', response?.processedRecords);
            console.log('📊 UPLOAD COMPONENT: Tipo processedRecords:', typeof response?.processedRecords);
            
            clearInterval(progressInterval);
            setUploadProgress(100);
            
            // Resetear formulario
            setSelectedFile(null);
            setSelectedOperator('');
            setSelectedDocumentType('');
            setErrors([]);
            
            onUploadSuccess(response);
            
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Error desconocido';
            setErrors([errorMessage]);
            onUploadError?.(errorMessage);
        } finally {
            setIsUploading(false);
            setUploadProgress(0);
        }
    };

    const clearSelection = () => {
        setSelectedFile(null);
        setErrors([]);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const canUpload = selectedFile && selectedOperator && selectedDocumentType && !isUploading && errors.length === 0;

    return (
        <div className="space-y-6">
            {/* Selector de Operador */}
            <div>
                <label className="block text-sm font-medium text-light mb-2">
                    Operador *
                </label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {Object.entries(OPERATORS).map(([key, operator]) => (
                        <button
                            key={key}
                            type="button"
                            onClick={() => {
                                setSelectedOperator(key);
                                setSelectedDocumentType(''); // Reset document type when operator changes
                            }}
                            className={`p-3 rounded-lg border-2 transition-all text-center ${
                                selectedOperator === key
                                    ? 'border-primary bg-primary/20 text-primary'
                                    : 'border-secondary-light bg-secondary text-light hover:border-primary/50'
                            }`}
                        >
                            <div className="font-medium">{operator.name}</div>
                        </button>
                    ))}
                </div>
            </div>

            {/* Selector de Tipo de Documento */}
            {selectedOperator && (
                <div>
                    <label className="block text-sm font-medium text-light mb-2">
                        Tipo de Documento *
                    </label>
                    <div className="space-y-2">
                        {OPERATORS[selectedOperator as keyof typeof OPERATORS].documentTypes.map((docType) => (
                            <label
                                key={docType.id}
                                className={`flex items-center p-3 rounded-lg border cursor-pointer transition-all ${
                                    selectedDocumentType === docType.id
                                        ? 'border-primary bg-primary/10'
                                        : 'border-secondary-light bg-secondary hover:border-primary/50'
                                }`}
                            >
                                <input
                                    type="radio"
                                    name="documentType"
                                    value={docType.id}
                                    checked={selectedDocumentType === docType.id}
                                    onChange={(e) => setSelectedDocumentType(e.target.value)}
                                    className="sr-only"
                                />
                                <div className={`w-4 h-4 rounded-full border-2 mr-3 flex-shrink-0 ${
                                    selectedDocumentType === docType.id
                                        ? 'border-primary bg-primary'
                                        : 'border-medium'
                                }`}>
                                    {selectedDocumentType === docType.id && (
                                        <div className="w-full h-full rounded-full bg-white scale-50"></div>
                                    )}
                                </div>
                                <div className="flex-1">
                                    <div className="font-medium text-light">{docType.name}</div>
                                    <div className="text-sm text-medium mt-1">{docType.description}</div>
                                    <div className="text-xs text-medium mt-2 space-y-1">
                                        <div><span className="font-medium">Formatos:</span> {docType.formats}</div>
                                        <div><span className="font-medium">Columnas principales:</span> {docType.columns.slice(0, 3).join(', ')}{docType.columns.length > 3 ? '...' : ''}</div>
                                    </div>
                                </div>
                            </label>
                        ))}
                    </div>
                </div>
            )}

            {/* Área de Carga de Archivos */}
            {selectedOperator && selectedDocumentType && (
                <div>
                    <label className="block text-sm font-medium text-light mb-2">
                        Archivo de Datos *
                    </label>
                    
                    <div
                        className={`border-2 border-dashed rounded-lg p-8 text-center transition-all ${
                            dragActive
                                ? 'border-primary bg-primary/10'
                                : errors.length > 0
                                ? 'border-red-500 bg-red-500/10'
                                : 'border-secondary-light bg-secondary'
                        }`}
                        onDragEnter={handleDragEnter}
                        onDragLeave={handleDragLeave}
                        onDragOver={handleDragOver}
                        onDrop={handleDrop}
                    >
                        <input
                            ref={fileInputRef}
                            type="file"
                            className="hidden"
                            accept=".csv,.xlsx,.xls"
                            onChange={handleFileChange}
                        />
                        
                        {!selectedFile ? (
                            <div className="space-y-4">
                                <div className="text-primary text-6xl">
                                    {ICONS.upload}
                                </div>
                                <div>
                                    <h3 className="text-lg font-semibold text-light">
                                        Selecciona o arrastra un archivo
                                    </h3>
                                    <p className="text-medium mt-1">
                                        Formatos soportados: CSV, Excel (.xlsx, .xls)
                                    </p>
                                    <p className="text-sm text-medium mt-1">
                                        Tamaño máximo: 20MB
                                    </p>
                                </div>
                                <Button
                                    type="button"
                                    variant="secondary"
                                    onClick={() => fileInputRef.current?.click()}
                                >
                                    Seleccionar Archivo
                                </Button>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                <div className="text-green-500 text-4xl">
                                    {ICONS.checkCircle}
                                </div>
                                <div>
                                    <h3 className="text-lg font-semibold text-light">
                                        {selectedFile.name}
                                    </h3>
                                    <p className="text-medium">
                                        {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                                    </p>
                                </div>
                                <div className="flex space-x-2 justify-center">
                                    <Button
                                        variant="secondary"
                                        onClick={clearSelection}
                                        disabled={isUploading}
                                    >
                                        Cambiar Archivo
                                    </Button>
                                </div>
                            </div>
                        )}
                    </div>
                    
                    {/* Errores de Validación */}
                    {errors.length > 0 && (
                        <div className="mt-4 p-4 bg-red-900/20 border border-red-500 rounded-lg">
                            <div className="flex items-center text-red-400 mb-2">
                                <span className="mr-2">{ICONS.exclamationTriangle}</span>
                                <span className="font-medium">Errores de validación:</span>
                            </div>
                            <ul className="list-disc list-inside text-sm text-red-300 space-y-1">
                                {errors.map((error, index) => (
                                    <li key={index}>{error}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            )}

            {/* Barra de Progreso */}
            {isUploading && (
                <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                        <span className="text-light">Procesando archivo...</span>
                        <span className="text-medium">{uploadProgress}%</span>
                    </div>
                    <div className="w-full bg-secondary-light rounded-full h-2">
                        <div
                            className="bg-primary h-2 rounded-full transition-all duration-300"
                            style={{ width: `${uploadProgress}%` }}
                        />
                    </div>
                </div>
            )}

            {/* Sección de Carga Mejorada */}
            <div className="pt-6 border-t border-secondary-light">
                {/* Resumen de información previa al upload */}
                {canUpload && !isUploading && (
                    <div className="mb-6 p-4 bg-gradient-to-r from-blue-900/30 to-indigo-900/30 border border-blue-500/30 rounded-lg">
                        <div className="flex items-center space-x-3 mb-3">
                            <div className="p-2 bg-blue-500/20 rounded-lg">
                                <span className="text-blue-400">{ICONS.info}</span>
                            </div>
                            <div>
                                <h3 className="text-sm font-semibold text-blue-200">Resumen de Carga</h3>
                                <p className="text-xs text-blue-300">Verificá los datos antes de procesar</p>
                            </div>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                            <div className="flex items-center space-x-2">
                                <span className="text-blue-400">{ICONS.database}</span>
                                <span className="text-light font-medium">Operador:</span>
                                <span className="text-blue-200">{OPERATORS[selectedOperator as keyof typeof OPERATORS]?.name}</span>
                            </div>
                            <div className="flex items-center space-x-2">
                                <span className="text-blue-400">{ICONS.document}</span>
                                <span className="text-light font-medium">Tipo:</span>
                                <span className="text-blue-200">
                                    {OPERATORS[selectedOperator as keyof typeof OPERATORS]?.documentTypes.find(dt => dt.id === selectedDocumentType)?.name?.split(' ')[0]}
                                </span>
                            </div>
                            <div className="flex items-center space-x-2">
                                <span className="text-blue-400">{ICONS.upload}</span>
                                <span className="text-light font-medium">Archivo:</span>
                                <span className="text-blue-200 truncate">{selectedFile?.name}</span>
                            </div>
                        </div>
                    </div>
                )}

                {/* Botón de Carga Rediseñado */}
                <div className="flex justify-center">
                    <div className="relative group">
                        {/* Efectos de fondo animados */}
                        <div className={`absolute -inset-1 rounded-xl transition-all duration-500 ${
                            canUpload && !isUploading 
                                ? 'bg-gradient-to-r from-blue-500/50 via-indigo-500/50 to-purple-500/50 opacity-75 group-hover:opacity-100 blur-sm group-hover:blur-none'
                                : 'bg-gray-600/20 opacity-30'
                        }`}></div>
                        
                        {/* Botón principal */}
                        <button
                            onClick={handleUpload}
                            disabled={!canUpload}
                            className={`relative flex flex-col items-center justify-center px-12 py-6 rounded-xl font-semibold transition-all duration-300 transform ${
                                canUpload && !isUploading
                                    ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-2xl shadow-blue-500/25 hover:shadow-blue-500/40 hover:scale-[1.02] active:scale-[0.98]'
                                    : 'bg-gray-700 text-gray-400 cursor-not-allowed'
                            }`}
                            aria-label={`${isUploading ? 'Procesando' : 'Cargar'} datos de ${selectedOperator || 'operador'}`}
                        >
                            {/* Contenido del botón */}
                            <div className="flex items-center space-x-3">
                                {/* Icono con animaciones */}
                                <div className={`transition-all duration-300 ${
                                    isUploading ? 'text-blue-300' : canUpload ? 'text-white group-hover:text-blue-100' : 'text-gray-400'
                                }`}>
                                    {isUploading ? (
                                        <div className="relative">
                                            <span className="text-2xl">{ICONS.loading}</span>
                                            <div className="absolute inset-0 bg-blue-400/20 rounded-full animate-pulse"></div>
                                        </div>
                                    ) : canUpload ? (
                                        <div className="relative">
                                            <span className="text-2xl transform group-hover:scale-110 transition-transform duration-200">
                                                {ICONS.upload}
                                            </span>
                                            {/* Efecto de destello en hover */}
                                            <div className="absolute inset-0 bg-white/0 group-hover:bg-white/20 rounded-full transition-all duration-300"></div>
                                        </div>
                                    ) : (
                                        <span className="text-2xl">{ICONS.upload}</span>
                                    )}
                                </div>
                                
                                {/* Texto principal */}
                                <div className="flex flex-col items-start">
                                    <span className={`text-lg font-bold ${
                                        isUploading ? 'text-blue-100' : canUpload ? 'text-white' : 'text-gray-400'
                                    }`}>
                                        {isUploading ? 'Procesando Archivo...' : 'Cargar Datos'}
                                    </span>
                                    <span className={`text-xs mt-1 ${
                                        isUploading ? 'text-blue-200' : canUpload ? 'text-blue-100 group-hover:text-white' : 'text-gray-500'
                                    }`}>
                                        {isUploading ? 'No cierre la aplicación' : canUpload ? 'Iniciar procesamiento seguro' : 'Complete todos los campos requeridos'}
                                    </span>
                                </div>
                            </div>

                            {/* Indicador de progreso integrado */}
                            {isUploading && (
                                <div className="absolute bottom-0 left-0 right-0 h-1 bg-blue-800/50 rounded-b-xl overflow-hidden">
                                    <div 
                                        className="h-full bg-gradient-to-r from-blue-300 to-cyan-300 transition-all duration-300 shadow-lg shadow-blue-300/50"
                                        style={{ width: `${uploadProgress}%` }}
                                    ></div>
                                </div>
                            )}

                            {/* Efecto de éxito */}
                            {canUpload && !isUploading && (
                                <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                                </div>
                            )}
                        </button>

                        {/* Información adicional en estado de carga */}
                        {isUploading && (
                            <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 text-center">
                                <div className="flex items-center space-x-2 text-xs text-blue-300">
                                    <span className="w-1 h-1 bg-blue-400 rounded-full animate-bounce"></span>
                                    <span className="w-1 h-1 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></span>
                                    <span className="w-1 h-1 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                                </div>
                                <p className="text-xs text-medium mt-1">Validando y procesando datos...</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Mensaje de seguridad */}
                {canUpload && !isUploading && (
                    <div className="mt-6 flex items-center justify-center space-x-2 text-xs text-medium">
                        <span className="text-green-400">{ICONS.shield}</span>
                        <span>Procesamiento seguro y confidencial de datos</span>
                    </div>
                )}
            </div>
        </div>
    );
};

export default OperatorDataUpload;