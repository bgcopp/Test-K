
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
    const inputRef = React.useRef<HTMLInputElement>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        e.preventDefault();
        if (e.target.files && e.target.files[0]) {
            setSelectedFile(e.target.files[0]);
        }
    };

    const handleUpload = async () => {
        if (!selectedFile) return;
        setIsLoading(true);
        try {
            await onUpload(selectedFile);
            setSelectedFile(null); // Reset after successful upload
        } catch (error) {
            console.error("La subida falló:", error);
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
        }
    };
    
    const onButtonClick = () => {
        inputRef.current?.click();
    };

    return (
        <div className={`text-center p-8 border-2 border-dashed rounded-lg bg-secondary-light transition-colors ${dragActive ? 'border-primary' : 'border-gray-600'}`} onDragEnter={handleDrag} onDragLeave={handleDrag} onDragOver={handleDrag} onDrop={handleDrop}>
            <input
                ref={inputRef}
                type="file"
                className="hidden"
                onChange={handleFileChange}
                accept={acceptedFileTypes}
            />
            
            <div className="flex flex-col items-center justify-center">
                <span className="text-primary">{React.cloneElement(ICONS.upload, { className: "h-12 w-12" })}</span>
                <h3 className="text-xl font-semibold text-light mt-4">{title}</h3>
                <p className="text-medium mt-1">{description}</p>
                
                {!selectedFile && (
                    <Button type="button" variant="secondary" onClick={onButtonClick} className="mt-6">
                        Seleccionar Archivo
                    </Button>
                )}
            </div>

            {selectedFile && (
                <div className="mt-6 p-4 bg-secondary rounded-md text-left w-full max-w-md mx-auto">
                    <p className="text-light font-medium">Archivo Seleccionado:</p>
                    <div className="flex justify-between items-center mt-2 text-sm text-medium">
                        <span className="truncate pr-4">{selectedFile.name}</span>
                        <span>{(selectedFile.size / 1024).toFixed(2)} KB</span>
                    </div>
                    <div className="flex space-x-2 mt-4">
                        <Button 
                            onClick={handleUpload} 
                            disabled={isLoading}
                            className="w-full"
                        >
                            {isLoading ? 'Procesando...' : 'Subir y Procesar'}
                        </Button>
                        <Button 
                            variant="secondary"
                            onClick={() => setSelectedFile(null)}
                            disabled={isLoading}
                        >
                            Limpiar
                        </Button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default FileUpload;
