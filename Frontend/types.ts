export interface PermissionSet {
    create: boolean;
    read: boolean;
    update: boolean;
    delete: boolean;
}

export interface Permissions {
    users: PermissionSet;
    roles: PermissionSet;
    missions: PermissionSet;
    dashboard: Pick<PermissionSet, 'read'>;
    targetAnalysis: {
        execute: boolean;
    };
}

export interface Role {
    id: string;
    name: string;
    permissions: Permissions;
}

export interface User {
    id:string;
    name: string;
    email: string;
    roleId: string;
    status: 'active' | 'inactive';
    avatar: string;
}

export enum MissionStatus {
    PLANNING = 'Planificación',
    IN_PROGRESS = 'En Progreso',
    COMPLETED = 'Completada',
    CANCELLED = 'Cancelada',
}

export interface CellularDataRecord {
    id?: number; // ID autoincremental de la BD (interno, opcional para display)
    fileRecordId?: number; // ID original del archivo (ej: columna "Id" de SCANHUNTER.xlsx)
    punto: string; // punto de medición
    lat: string;
    lon: string;
    mncMcc: string; // MNC+MCC
    operador: string;
    rssi: number; // señal RSSI
    tecnologia: string; // GSM, UMTS, LTE, 5G, etc
    cellId: string;
    lacTac?: string; // opcional
    enb?: string; // opcional
    channel?: string; // opcional
    comentario?: string; // opcional
}



// Interfaces para datos de operadores
export interface OperatorSheet {
    id: string;
    filename: string;
    operator: string;
    documentType: string;
    uploadDate: string;
    processedRecords: number;
    status: 'processing' | 'completed' | 'error';
    errorMessage?: string;
    missionId: string;
}

export interface OperatorCellularRecord {
    id: number;
    sheetId: string;
    phoneNumber?: string;
    imei?: string;
    imsi?: string;
    cellId?: string;
    lac?: string;
    timestamp?: string;
    location?: string;
    operator: string;
    documentType: string;
    rawData: Record<string, any>; // Datos originales del archivo
}

export interface ProcessingLog {
    id: string;
    sheetId: string;
    level: 'info' | 'warning' | 'error';
    message: string;
    timestamp: string;
    details?: Record<string, any>;
}

export interface OperatorUploadResponse {
    success: boolean;
    sheetId?: string;
    message?: string;         // Para respuestas de éxito
    error?: string;           // Para respuestas de error
    processedRecords?: number;
    records_failed?: number;
    records_duplicated?: number;      // NUEVO: registros duplicados
    records_validation_failed?: number; // NUEVO: errores de validación
    records_other_errors?: number;    // NUEVO: otros errores
    success_rate?: number;
    warnings?: string[];
    errors?: string[];
    details?: {
        duplicate_analysis?: {
            detected_duplicates: number;
            validation_failures: number;
            other_failures: number;
            duplicate_percentage: number;
        };
    };
}

export interface DocumentTypeConfig {
    id: string;
    name: string;
    description: string;
    formats: string;
    columns: string[];
}

export interface OperatorConfig {
    name: string;
    documentTypes: DocumentTypeConfig[];
}

export interface Mission {
    id: string;
    code: string;
    name: string;
    description: string;
    status: MissionStatus;
    startDate: string;
    endDate: string;
    cellularData?: CellularDataRecord[];
    operatorSheets?: OperatorSheet[];
}

// Tipos para el sistema de notificaciones profesional
export type NotificationType = 'success' | 'error' | 'warning' | 'info';

export interface NotificationData {
    id: string;
    type: NotificationType;
    title: string;
    message: string;
    details?: string[];
    autoClose?: boolean;
    duration?: number; // en milisegundos
    timestamp: Date;
}

export interface FileProcessingResult {
    fileName: string;
    fileType: string; // 'SCANHUNTER', 'CLARO', 'MOVISTAR', 'TIGO', 'WOM', etc.
    processedRecords: number;
    failedRecords?: number;
    duplicatedRecords?: number;      // NUEVO: registros duplicados
    validationFailures?: number;     // NUEVO: errores de validación
    otherErrors?: number;           // NUEVO: otros errores
    totalRecords?: number;
    processingTime?: number; // en milisegundos
    warnings?: string[];
    errors?: string[];
    additionalInfo?: Record<string, any>;
}

// Tipos para el sistema de confirmación modal
export type ConfirmationType = 'destructive' | 'warning' | 'info' | 'danger';

export interface ConfirmationConfig {
    type: ConfirmationType;
    title: string;
    message: string;
    details?: string;
    confirmText?: string;
    cancelText?: string;
    confirmButtonVariant?: 'danger' | 'warning' | 'primary' | 'secondary';
    showIcon?: boolean;
    allowBackdropClick?: boolean;
    onConfirm?: () => void | Promise<void>;
    onCancel?: () => void;
}

export interface ConfirmationContextType {
    showConfirmation: (config: ConfirmationConfig) => Promise<boolean>;
    hideConfirmation: () => void;
    isVisible: boolean;
}

// Interfaz para registros objetivo del análisis clásico
export interface TargetRecord {
    id: string;
    targetNumber: string;
    matchingCells: string[];
    confidence: number;
    status: 'active' | 'inactive';
    lastSeen: Date;
    notes: string;
}

// Interfaz para resultados de correlación
export interface CorrelationResult {
    targetNumber: string;
    operator: string;
    occurrences: number;
    firstDetection: string;
    lastDetection: string;
    relatedCells: string[];
    confidence: number;
}

// Interfaz para respuesta de análisis de correlación
export interface CorrelationAnalysisResponse {
    success: boolean;
    data: CorrelationResult[];
    statistics: {
        totalAnalyzed: number;
        totalFound: number;
        processingTime: number;
    };
    error?: string;
}
