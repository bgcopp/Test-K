
import React, { useState, useCallback } from 'react';
import { ICONS } from '../../constants';
import Button from './Button';

interface FileUploadProps {
    title: string;
    description: string;
    onUpload: (file: File) => Promise<void>;
    acceptedFileTypes?: string;
}

const FileUpload: React.FC<FileUploadProps> = ({ title, description, onUpload, acceptedFileTypes }) => {
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [dragActive, setDragActive] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const inputRef = React.useRef<HTMLInputElement>(null);

    // Función para obtener el icono según el tipo de archivo
    const getFileIcon = (fileName: string) => {
        const extension = fileName.split('.').pop()?.toLowerCase();
        if (extension === 'xlsx' || extension === 'xls') {
            return (
                <svg className="h-6 w-6 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                </svg>
            );
        } else if (extension === 'csv') {
            return (
                <svg className="h-6 w-6 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                </svg>
            );
        }
        return React.cloneElement(ICONS.document, { className: "h-6 w-6 text-gray-400" });
    };

    // Función para formatear el tamaño del archivo
    const formatFileSize = (bytes: number) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        e.preventDefault();
        if (e.target.files && e.target.files[0]) {
            setSelectedFile(e.target.files[0]);
            setUploadProgress(0);
        }
    };

    const handleUpload = async () => {
        if (!selectedFile) return;
        setIsLoading(true);
        setUploadProgress(0);

        try {
            // Simulación de progreso de carga para mejor UX
            const progressInterval = setInterval(() => {
                setUploadProgress((prev) => {
                    if (prev >= 90) {
                        clearInterval(progressInterval);
                        return 90;
                    }
                    return prev + Math.random() * 20;
                });
            }, 200);

            await onUpload(selectedFile);
            
            clearInterval(progressInterval);
            setUploadProgress(100);
            
            // Pequeño delay para mostrar el 100% antes de resetear
            setTimeout(() => {
                setSelectedFile(null);
                setUploadProgress(0);
            }, 1000);
            
        } catch (error) {
            console.error("La subida falló:", error);
            setUploadProgress(0);
            // Here you could set an error state to display to the user
        } finally {
            setIsLoading(false);
        }
    };
    
    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            setSelectedFile(e.dataTransfer.files[0]);
            setUploadProgress(0);
        }
    };
    
    const onButtonClick = () => {
        inputRef.current?.click();
    };

    return (
        <div className="w-full max-w-2xl mx-auto">
            {/* Área principal de drag & drop con diseño moderno */}
            <div 
                className={`
                    relative overflow-hidden rounded-xl border-2 border-dashed transition-all duration-300 ease-in-out
                    ${dragActive 
                        ? 'border-primary bg-gradient-to-br from-blue-500/10 via-purple-500/5 to-primary/10 scale-[1.02] shadow-lg shadow-primary/20' 
                        : selectedFile 
                            ? 'border-green-500/50 bg-gradient-to-br from-green-500/5 to-secondary-light' 
                            : 'border-gray-500/50 bg-gradient-to-br from-secondary-light to-secondary hover:border-gray-400/70 hover:shadow-md'
                    }
                `}
                onDragEnter={handleDrag} 
                onDragLeave={handleDrag} 
                onDragOver={handleDrag} 
                onDrop={handleDrop}
            >
                {/* Efecto de gradiente de fondo sutil */}
                <div className="absolute inset-0 bg-gradient-to-r from-primary/5 via-transparent to-purple-500/5 opacity-50"></div>
                
                <input
                    ref={inputRef}
                    type="file"
                    className="hidden"
                    onChange={handleFileChange}
                    accept={acceptedFileTypes}
                    aria-label="Selector de archivo"
                />
                
                {!selectedFile ? (
                    /* Estado inicial: Sin archivo seleccionado */
                    <div className="relative px-8 py-12 text-center">
                        {/* Icono animado principal */}
                        <div className={`
                            inline-flex items-center justify-center w-20 h-20 rounded-full mb-6
                            bg-gradient-to-br from-primary/20 to-purple-500/20 backdrop-blur-sm
                            transition-all duration-300 ease-in-out
                            ${dragActive ? 'scale-110 rotate-6' : 'hover:scale-105'}
                        `}>
                            <div className={`
                                transition-all duration-300 ease-in-out text-primary
                                ${dragActive ? 'scale-125 text-blue-400' : ''}
                            `}>
                                {React.cloneElement(ICONS.upload, { 
                                    className: "h-10 w-10",
                                    strokeWidth: 1.5
                                })}
                            </div>
                        </div>

                        {/* Contenido textual mejorado */}
                        <div className="space-y-3">
                            <h3 className="text-2xl font-bold text-light tracking-tight">{title}</h3>
                            <p className="text-medium text-base leading-relaxed max-w-md mx-auto">{description}</p>
                        </div>

                        {/* Indicadores de tipos de archivo */}
                        <div className="flex items-center justify-center space-x-4 mt-6 mb-8">
                            <div className="flex items-center space-x-2 px-3 py-1 bg-green-500/10 rounded-full border border-green-500/20">
                                <svg className="h-4 w-4 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                                </svg>
                                <span className="text-xs font-medium text-green-400">Excel</span>
                            </div>
                            <div className="flex items-center space-x-2 px-3 py-1 bg-blue-500/10 rounded-full border border-blue-500/20">
                                <svg className="h-4 w-4 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                                </svg>
                                <span className="text-xs font-medium text-blue-400">CSV</span>
                            </div>
                        </div>

                        {/* Botón principal con diseño moderno */}
                        <div className="space-y-4">
                            <Button 
                                type="button" 
                                variant="primary" 
                                onClick={onButtonClick}
                                size="lg"
                                className="
                                    bg-gradient-to-r from-primary to-blue-600 hover:from-primary-hover hover:to-blue-700
                                    shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30
                                    transform transition-all duration-200 hover:scale-105
                                    border-0 px-8 py-3
                                "
                                icon={React.cloneElement(ICONS.upload, { className: "h-5 w-5" })}
                            >
                                Seleccionar Archivo
                            </Button>
                            
                            <p className="text-sm text-gray-400">
                                O arrastra y suelta tu archivo aquí
                            </p>
                        </div>
                    </div>
                ) : (
                    /* Estado: Archivo seleccionado - Vista previa elegante */
                    <div className="p-8">
                        {/* Header de archivo seleccionado */}
                        <div className="text-center mb-6">
                            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-500/20 mb-4">
                                {React.cloneElement(ICONS.checkCircle, { 
                                    className: "h-8 w-8 text-green-400" 
                                })}
                            </div>
                            <h4 className="text-lg font-semibold text-light">Archivo Seleccionado</h4>
                        </div>

                        {/* Card de información del archivo */}
                        <div className="bg-gradient-to-r from-secondary to-secondary-light rounded-xl p-6 border border-gray-600/30 shadow-lg">
                            <div className="flex items-start space-x-4">
                                {/* Icono del tipo de archivo */}
                                <div className="flex-shrink-0 w-12 h-12 bg-gray-700/50 rounded-lg flex items-center justify-center">
                                    {getFileIcon(selectedFile.name)}
                                </div>
                                
                                {/* Información del archivo */}
                                <div className="flex-1 min-w-0">
                                    <h5 className="text-light font-medium text-base truncate pr-4">
                                        {selectedFile.name}
                                    </h5>
                                    <div className="flex items-center space-x-4 mt-2">
                                        <span className="text-sm text-medium">
                                            {formatFileSize(selectedFile.size)}
                                        </span>
                                        <span className="text-xs text-gray-400 bg-gray-700/50 px-2 py-1 rounded">
                                            {selectedFile.type || 'Archivo'}
                                        </span>
                                    </div>
                                </div>
                                
                                {/* Botón eliminar archivo */}
                                <button
                                    onClick={() => setSelectedFile(null)}
                                    disabled={isLoading}
                                    className="
                                        flex-shrink-0 w-8 h-8 rounded-full bg-red-500/10 hover:bg-red-500/20
                                        flex items-center justify-center transition-colors duration-200
                                        disabled:opacity-50 disabled:cursor-not-allowed
                                        group
                                    "
                                    aria-label="Eliminar archivo"
                                >
                                    {React.cloneElement(ICONS.close, { 
                                        className: "h-4 w-4 text-red-400 group-hover:text-red-300" 
                                    })}
                                </button>
                            </div>

                            {/* Barra de progreso (visible durante la carga) */}
                            {isLoading && (
                                <div className="mt-4">
                                    <div className="flex items-center justify-between text-sm mb-2">
                                        <span className="text-medium">Procesando...</span>
                                        <span className="text-primary font-medium">{Math.round(uploadProgress)}%</span>
                                    </div>
                                    <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                                        <div 
                                            className="h-full bg-gradient-to-r from-primary to-blue-500 transition-all duration-300 ease-out rounded-full"
                                            style={{ width: `${uploadProgress}%` }}
                                        ></div>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Botones de acción */}
                        <div className="flex space-x-3 mt-6">
                            <Button 
                                onClick={handleUpload} 
                                disabled={isLoading}
                                className="
                                    flex-1 bg-gradient-to-r from-primary to-blue-600 hover:from-primary-hover hover:to-blue-700
                                    shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30
                                    transform transition-all duration-200 hover:scale-[1.02]
                                    disabled:transform-none disabled:shadow-none
                                "
                                icon={isLoading 
                                    ? React.cloneElement(ICONS.loading, { className: "h-5 w-5" })
                                    : React.cloneElement(ICONS.upload, { className: "h-5 w-5" })
                                }
                            >
                                {isLoading ? 'Procesando...' : 'Subir y Procesar'}
                            </Button>
                            
                            <Button 
                                variant="secondary"
                                onClick={onButtonClick}
                                disabled={isLoading}
                                className="
                                    bg-gray-600/50 hover:bg-gray-600/70 border border-gray-500/30
                                    hover:border-gray-400/50 transition-all duration-200
                                "
                                icon={React.cloneElement(ICONS.refresh, { className: "h-5 w-5" })}
                            >
                                Cambiar
                            </Button>
                        </div>
                    </div>
                )}
            </div>

            {/* Mensaje informativo adicional */}
            <div className="mt-4 text-center">
                <p className="text-xs text-gray-400">
                    Tamaño máximo recomendado: 50MB • Formatos soportados: Excel (.xlsx, .xls), CSV
                </p>
            </div>
        </div>
    );
};

export default FileUpload;
