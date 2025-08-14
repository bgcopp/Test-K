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

            {/* Botón de Carga */}
            <div className="flex justify-end pt-4">
                <Button
                    onClick={handleUpload}
                    disabled={!canUpload}
                    icon={isUploading ? ICONS.loading : ICONS.upload}
                    className="min-w-32"
                >
                    {isUploading ? 'Procesando...' : 'Cargar Datos'}
                </Button>
            </div>
        </div>
    );
};

export default OperatorDataUpload;