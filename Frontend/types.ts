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
    id: number;
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
    warnings?: string[];
    errors?: string[];
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


