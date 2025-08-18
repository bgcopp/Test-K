import type { Mission, User, Role, Permissions, OperatorSheet, OperatorCellularRecord, OperatorUploadResponse, TargetRecord, CorrelationResult, CorrelationAnalysisResponse } from '../types';
import { initialUsers, initialRoles, initialMissions } from './mockData';

// Eel types for better autocompletion, assuming eel is exposed to window
declare global {
    interface Window {
        eel: {
            // Authentication & Users
            login(credentials: { email: string, password: string }): () => Promise<{ status: string;  }>;
            get_users(): () => Promise<User[]>;
            create_user(userData: Omit<User, 'id' | 'avatar'>): () => Promise<User>;
            update_user(userId: string, userData: Partial<User>): () => Promise<User>;
            delete_user(userId: string): () => Promise<{ status: string }>;
            
            // Roles
            get_roles(): () => Promise<Role[]>;
            create_role(roleData: { name: string, permissions: Permissions }): () => Promise<Role>;
            update_role(roleId: string, roleData: { name: string, permissions: Permissions }): () => Promise<Role>;
            delete_role(roleId: string): () => Promise<{ status: string }>;
            
            // Missions
            get_missions(): () => Promise<Mission[]>;
            create_mission(missionData: Omit<Mission, 'id' | 'cellularData' | 'operatorData'>): () => Promise<Mission>;
            update_mission(missionId: string, missionData: Partial<Mission>): () => Promise<Mission>;
            delete_mission(missionId: string): () => Promise<{ status: string }>;
            
            // Cellular Data (existing)
            upload_cellular_data(missionId: string, fileData: {name: string, content: string}): () => Promise<Mission>;
            clear_cellular_data(missionId: string): () => Promise<Mission>;
            
            // Analysis
            run_analysis(missionId: string): () => Promise<TargetRecord[]>;
            
            // Correlation Analysis
            analyze_correlation(missionId: string, startDateTime: string, endDateTime: string, minOccurrences: number): () => Promise<CorrelationAnalysisResponse>;
            get_correlation_summary(missionId: string): () => Promise<any>;
            
            // Operator Data
            upload_operator_data(file_data: string, file_name: string, mission_id: string, operator: string, file_type: string, user_id: string): () => Promise<OperatorUploadResponse>;
            get_operator_sheets(missionId: string): () => Promise<OperatorSheet[]>;
            get_operator_sheet_data(sheetId: string, page: number, pageSize: number): () => Promise<{data: OperatorCellularRecord[], total: number, hasMore: boolean, columns?: string[], displayNames?: {[key: string]: string}}>;
            delete_operator_sheet(file_upload_id: string, user_id: string): () => Promise<{status: string}>;
            get_operator_statistics(mission_id?: string): () => Promise<{success: boolean, statistics: any, totals: any, mission_id?: string, error?: string}>;
        }
    }
}

// --- CONFIGURATION ---
// Configuración automática basada en disponibilidad de Eel
let isEelAvailable: boolean | null = null;
let USE_MOCK_API: boolean;
const MOCK_API_DELAY = 500; // ms
const FORCE_MOCK_API = false; // Forzar modo mock para desarrollo

/**
 * Detecta si Eel está disponible en el entorno actual
 */
function detectEelAvailability(): boolean {
    if (isEelAvailable !== null) {
        return isEelAvailable;
    }
    
    try {
        // Verificar si window.eel existe y tiene las propiedades necesarias
        const hasEelObject = typeof window !== 'undefined' && window.eel && typeof window.eel === 'object';
        const hasLoginFunction = hasEelObject && typeof window.eel.login === 'function';
        
        isEelAvailable = hasEelObject && hasLoginFunction;
        
        if (isEelAvailable) {
            console.log('✅ Eel detectado y disponible - Modo backend activo');
        } else {
            console.log('⚠️  Eel no detectado - Modo mock activo (desarrollo)');
            console.log('   - Ejecutándose probablemente con Vite dev server');
            console.log('   - Para usar el backend, ejecuta desde el entorno Eel de Python');
        }
        
        return isEelAvailable;
    } catch (error) {
        console.warn('Error detectando Eel:', error);
        isEelAvailable = false;
        return false;
    }
}

/**
 * Inicializa la configuración de la API
 */
function initializeApiMode() {
    if (FORCE_MOCK_API) {
        USE_MOCK_API = true;
        console.log('🔧 Modo mock forzado por configuración');
        return;
    }
    
    const eelAvailable = detectEelAvailability();
    USE_MOCK_API = !eelAvailable;
    
    console.log(`🎯 Modo API seleccionado: ${USE_MOCK_API ? 'MOCK' : 'EEL'}`);
}

// Inicializar el modo API
initializeApiMode();

/**
 * Obtiene el estado actual del modo API
 */
export function getApiMode(): { isEelMode: boolean; isMockMode: boolean; eelAvailable: boolean } {
    return {
        isEelMode: !USE_MOCK_API,
        isMockMode: USE_MOCK_API,
        eelAvailable: isEelAvailable ?? false
    };
}

// --- MOCK DATA STORE (resets on logout) ---
let mockUsers: User[] = JSON.parse(JSON.stringify(initialUsers));
let mockRoles: Role[] = JSON.parse(JSON.stringify(initialRoles));
let mockMissions: Mission[] = JSON.parse(JSON.stringify(initialMissions));
let mockOperatorSheets: OperatorSheet[] = [];

/**
 * Resets the mock data to its initial state. Called on logout.
 */
export function resetMockData() {
  if (USE_MOCK_API) {
    mockUsers = JSON.parse(JSON.stringify(initialUsers));
    mockRoles = JSON.parse(JSON.stringify(initialRoles));
    mockMissions = JSON.parse(JSON.stringify(initialMissions));
    mockOperatorSheets = [];
    console.log('🔄 Datos mock reiniciados al estado inicial');
  }
}

/**
 * Fuerza la recarga de la detección de Eel (usado para testing)
 */
export function redetectEel(): boolean {
    isEelAvailable = null;
    const wasEelAvailable = !USE_MOCK_API;
    initializeApiMode();
    const isEelAvailableNow = !USE_MOCK_API;
    
    if (wasEelAvailable !== isEelAvailableNow) {
        console.log(`🔄 Modo API cambiado: ${wasEelAvailable ? 'EEL' : 'MOCK'} → ${isEelAvailableNow ? 'EEL' : 'MOCK'}`);
    }
    
    return isEelAvailableNow;
}

// --- REQUEST CANCELLATION & SHUTDOWN MANAGEMENT ---

/**
 * Controlador global para cancelar todas las requests durante shutdown
 */
class RequestCancellationManager {
    private activeRequests = new Map<string, AbortController>();
    private isShuttingDown = false;

    /**
     * Crea un AbortController para una nueva request
     */
    createController(operationName: string): AbortController {
        if (this.isShuttingDown) {
            throw new Error('Sistema en proceso de cierre - no se pueden iniciar nuevas operaciones');
        }

        const controller = new AbortController();
        const requestId = `${operationName}_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
        
        this.activeRequests.set(requestId, controller);
        
        // Limpiar automáticamente cuando la request termine
        const cleanup = () => this.activeRequests.delete(requestId);
        controller.signal.addEventListener('abort', cleanup, { once: true });
        
        return controller;
    }

    /**
     * Cancela todas las requests activas
     */
    cancelAllRequests(): void {
        console.log(`🚫 Cancelando ${this.activeRequests.size} requests activas`);
        
        for (const [requestId, controller] of this.activeRequests) {
            try {
                controller.abort('Shutdown iniciado');
                console.log(`   ✅ Request cancelada: ${requestId}`);
            } catch (error) {
                console.warn(`   ⚠️  Error cancelando request ${requestId}:`, error);
            }
        }
        
        this.activeRequests.clear();
    }

    /**
     * Marca el inicio del shutdown
     */
    initiateShutdown(): void {
        console.log('🔄 Iniciando shutdown de RequestCancellationManager');
        this.isShuttingDown = true;
        this.cancelAllRequests();
    }

    /**
     * Obtiene estadísticas de requests activas
     */
    getStats(): { activeCount: number; isShuttingDown: boolean } {
        return {
            activeCount: this.activeRequests.size,
            isShuttingDown: this.isShuttingDown
        };
    }
}

// Instancia global del manager
const requestManager = new RequestCancellationManager();

/**
 * Exponer el manager para uso en hooks de conexión
 */
export function getRequestManager(): RequestCancellationManager {
    return requestManager;
}

// --- HELPERS ---
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
const generateId = () => `id_${new Date().getTime()}_${Math.random().toString(36).substr(2, 9)}`;

/**
 * Maneja las respuestas de Eel con mejor gestión de errores, cancellation y fallback automático
 */
async function handleEelResponse<T>(
    fn: () => Promise<T>, 
    operationName?: string,
    allowCancellation: boolean = true
): Promise<T> {
    // Crear controller para esta operación si se permite cancelación
    let controller: AbortController | null = null;
    if (allowCancellation && operationName) {
        try {
            controller = requestManager.createController(operationName);
        } catch (error) {
            // Sistema en shutdown, rechazar inmediatamente
            throw error;
        }
    }
    // Verificar disponibilidad de Eel
    if (!detectEelAvailability()) {
        const errorMessage = `Eel no está disponible para la operación: ${operationName || 'desconocida'}`;
        console.error('❌', errorMessage);
        console.error('   - Asegúrate de que el backend esté ejecutándose');
        console.error('   - Verifica que "/eel.js" se haya cargado correctamente');
        console.error('   - Si estás en desarrollo, el modo mock se activará automáticamente');
        throw new Error(errorMessage);
    }
    
    // Verificar que window.eel esté presente
    if (!window.eel) {
        console.error('❌ window.eel no está definido después de la detección');
        throw new Error('Error interno: window.eel no disponible');
    }
    
    try {
        console.log(`🚀 Ejecutando operación Eel: ${operationName || 'desconocida'}`);
        
        // Si tenemos un controller, crear una promise que se rechace si se cancela
        if (controller) {
            const operationPromise = fn();
            const cancellationPromise = new Promise<never>((_, reject) => {
                controller!.signal.addEventListener('abort', () => {
                    reject(new Error(`Operación cancelada: ${operationName}`));
                }, { once: true });
            });
            
            const result = await Promise.race([operationPromise, cancellationPromise]);
            console.log(`✅ Operación Eel completada: ${operationName || 'desconocida'}`);
            return result;
        } else {
            const result = await fn();
            console.log(`✅ Operación Eel completada: ${operationName || 'desconocida'}`);
            return result;
        }
    } catch (error) {
        // Si es un error de cancelación, logearlo diferente
        if (error instanceof Error && error.message.includes('cancelada')) {
            console.log(`🚫 Operación cancelada: ${operationName || 'desconocida'}`);
            throw error;
        }
        console.error(`❌ Error en operación Eel (${operationName || 'desconocida'}):`, error);
        
        // Extraer mensaje de error más descriptivo
        let errorMessage = 'Error de comunicación con el backend';
        if (error && typeof error === 'object') {
            if ('message' in error && typeof error.message === 'string') {
                errorMessage = error.message;
            } else if ('error' in error && typeof error.error === 'string') {
                errorMessage = error.error;
            }
        } else if (typeof error === 'string') {
            errorMessage = error;
        }
        
        throw new Error(errorMessage);
    }
}

/**
 * Convierte un archivo a Base64 para envío al backend Python
 */
function toBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    try {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        const result = reader.result as string;
        console.log(`📁 Archivo convertido a Base64: ${file.name} (${file.size} bytes)`);
        resolve(result);
      };
      reader.onerror = error => {
        console.error('❌ Error convirtiendo archivo a Base64:', error);
        reject(new Error('Error procesando archivo'));
      };
    } catch (error) {
      console.error('❌ Error inesperado convirtiendo archivo:', error);
      reject(error);
    }
  });
}

// --- API IMPLEMENTATIONS ---

export const login = async (credentials: {email: string, password: string}) => {
    if (USE_MOCK_API) {
        await sleep(MOCK_API_DELAY);
        console.log('🎭 Autenticación mock:', credentials.email);
        if (credentials.email === 'admin@example.com' && credentials.password === 'password') {
            console.log('✅ Autenticación mock exitosa');
            return { status: 'ok' };
        }
        console.log('❌ Credenciales mock inválidas');
        throw new Error('Credenciales inválidas');
    }
    return handleEelResponse(() => window.eel.login(credentials)(), 'login');
};

export const getUsers = async () => {
    if (USE_MOCK_API) {
        await sleep(MOCK_API_DELAY);
        console.log('📊 Obteniendo usuarios mock:', mockUsers.length, 'usuarios');
        return JSON.parse(JSON.stringify(mockUsers));
    }
    return handleEelResponse(() => window.eel.get_users()(), 'obtener usuarios');
};

export const createUser = async (userData: Omit<User, 'id' | 'avatar'>) => {
    if (USE_MOCK_API) {
        await sleep(MOCK_API_DELAY);
        const newUser: User = {
            ...userData,
            id: generateId(),
            avatar: `https://picsum.photos/seed/${generateId()}/100/100`
        };
        mockUsers.push(newUser);
        console.log('👤 Usuario mock creado:', newUser.name);
        return newUser;
    }
    return handleEelResponse(() => window.eel.create_user(userData)(), 'crear usuario');
};

export const updateUser = async (userId: string, userData: Partial<User>) => {
    if (USE_MOCK_API) {
        await sleep(MOCK_API_DELAY);
        const userIndex = mockUsers.findIndex(u => u.id === userId);
        if (userIndex === -1) throw new Error("Usuario no encontrado");
        mockUsers[userIndex] = { ...mockUsers[userIndex], ...userData };
        console.log('✏️ Usuario mock actualizado:', mockUsers[userIndex].name);
        return mockUsers[userIndex];
    }
    return handleEelResponse(() => window.eel.update_user(userId, userData)(), 'actualizar usuario');
};

export const deleteUser = async (userId: string) => {
    if (USE_MOCK_API) {
        await sleep(MOCK_API_DELAY);
        const userToDelete = mockUsers.find(u => u.id === userId);
        mockUsers = mockUsers.filter(u => u.id !== userId);
        console.log('🗑️ Usuario mock eliminado:', userToDelete?.name || 'desconocido');
        return { status: 'ok' };
    }
    return handleEelResponse(() => window.eel.delete_user(userId)(), 'eliminar usuario');
};

export const getRoles = async () => {
    if (USE_MOCK_API) {
        await sleep(MOCK_API_DELAY);
        console.log('👮 Obteniendo roles mock:', mockRoles.length, 'roles');
        return JSON.parse(JSON.stringify(mockRoles));
    }
    return handleEelResponse(() => window.eel.get_roles()(), 'obtener roles');
};

export const createRole = async (roleData: { name: string, permissions: Permissions }) => {
    if (USE_MOCK_API) {
        await sleep(MOCK_API_DELAY);
        const newRole: Role = { ...roleData, id: generateId() };
        mockRoles.push(newRole);
        console.log('👮 Rol mock creado:', newRole.name);
        return newRole;
    }
    return handleEelResponse(() => window.eel.create_role(roleData)(), 'crear rol');
};

export const updateRole = async (roleId: string, roleData: { name: string, permissions: Permissions }) => {
    if (USE_MOCK_API) {
        await sleep(MOCK_API_DELAY);
        const roleIndex = mockRoles.findIndex(r => r.id === roleId);
        if (roleIndex === -1) throw new Error("Rol no encontrado");
        mockRoles[roleIndex] = { ...mockRoles[roleIndex], ...roleData };
        console.log('✏️ Rol mock actualizado:', mockRoles[roleIndex].name);
        return mockRoles[roleIndex];
    }
    return handleEelResponse(() => window.eel.update_role(roleId, roleData)(), 'actualizar rol');
};

export const deleteRole = async (roleId: string) => {
    if (USE_MOCK_API) {
        await sleep(MOCK_API_DELAY);
        const roleToDelete = mockRoles.find(r => r.id === roleId);
        mockRoles = mockRoles.filter(r => r.id !== roleId);
        console.log('🗑️ Rol mock eliminado:', roleToDelete?.name || 'desconocido');
        return { status: 'ok' };
    }
    return handleEelResponse(() => window.eel.delete_role(roleId)(), 'eliminar rol');
};

export const getMissions = async () => {
    if (USE_MOCK_API) {
        await sleep(MOCK_API_DELAY);
        console.log('🎯 Obteniendo misiones mock:', mockMissions.length, 'misiones');
        return JSON.parse(JSON.stringify(mockMissions));
    }
    return handleEelResponse(() => window.eel.get_missions()(), 'obtener misiones');
};

export const createMission = async (missionData: Omit<Mission, 'id' | 'cellularData'>) => {
    if (USE_MOCK_API) {
        await sleep(MOCK_API_DELAY);
        const newMission: Mission = { ...missionData, id: generateId(), cellularData: [] };
        mockMissions.push(newMission);
        console.log('🎯 Misión mock creada:', newMission.code);
        return newMission;
    }
    return handleEelResponse(() => window.eel.create_mission(missionData)(), 'crear misión');
};

export const updateMission = async (missionId: string, missionData: Partial<Mission>) => {
    if (USE_MOCK_API) {
        await sleep(MOCK_API_DELAY);
        const missionIndex = mockMissions.findIndex(m => m.id === missionId);
        if (missionIndex === -1) throw new Error("Misión no encontrada");
        mockMissions[missionIndex] = { ...mockMissions[missionIndex], ...missionData };
        console.log('✏️ Misión mock actualizada:', mockMissions[missionIndex].code);
        return mockMissions[missionIndex];
    }
    return handleEelResponse(() => window.eel.update_mission(missionId, missionData)(), 'actualizar misión');
};

export const deleteMission = async (missionId: string) => {
    if (USE_MOCK_API) {
        await sleep(MOCK_API_DELAY);
        const missionToDelete = mockMissions.find(m => m.id === missionId);
        mockMissions = mockMissions.filter(m => m.id !== missionId);
        console.log('🗑️ Misión mock eliminada:', missionToDelete?.code || 'desconocida');
        return { status: 'ok' };
    }
    return handleEelResponse(() => window.eel.delete_mission(missionId)(), 'eliminar misión');
};

export const uploadCellularData = async (missionId: string, file: File) => {
    if (USE_MOCK_API) {
        await sleep(MOCK_API_DELAY * 2);
        const missionIndex = mockMissions.findIndex(m => m.id === missionId);
        if (missionIndex === -1) throw new Error("Misión no encontrada");
        mockMissions[missionIndex].cellularData = initialMissions[0].cellularData;
        console.log('📡 Datos celulares mock cargados:', file.name);
        return mockMissions[missionIndex];
    }
    const content = await toBase64(file);
    return handleEelResponse(() => window.eel.upload_cellular_data(missionId, { name: file.name, content })(), 'cargar datos celulares');
};


export const clearCellularDataApi = async (missionId: string) => {
    if (USE_MOCK_API) {
        await sleep(MOCK_API_DELAY);
        const missionIndex = mockMissions.findIndex(m => m.id === missionId);
        if (missionIndex === -1) throw new Error("Misión no encontrada");
        mockMissions[missionIndex].cellularData = [];
        console.log('🧹 Datos celulares mock limpiados para misión:', mockMissions[missionIndex].code);
        return mockMissions[missionIndex];
    }
    return handleEelResponse(() => window.eel.clear_cellular_data(missionId)(), 'limpiar datos celulares');
};

// Analysis functions
export const runAnalysis = async (missionId: string) => {
    if (USE_MOCK_API) {
        await sleep(MOCK_API_DELAY * 3); // Simular análisis más largo
        
        // Mock analysis results
        const mockResults: TargetRecord[] = [
            {
                id: '1',
                missionId: missionId,
                targetNumber: '3001234567',
                matchingCells: ['12345', '67890'],
                confidence: 0.85,
                status: 'active' as const,
                lastSeen: '2024-01-15T10:30:00Z',
                notes: 'Alto nivel de confianza en la coincidencia'
            },
            {
                id: '2', 
                missionId: missionId,
                targetNumber: '3009876543',
                matchingCells: ['54321'],
                confidence: 0.72,
                status: 'active' as const, 
                lastSeen: '2024-01-15T09:15:00Z',
                notes: 'Coincidencia parcial detectada'
            }
        ];
        
        console.log('🎯 Análisis mock completado:', mockResults.length, 'objetivos encontrados');
        return mockResults;
    }
    return handleEelResponse(() => window.eel.run_analysis(missionId)(), 'ejecutar análisis');
};

// --- OPERATOR DATA FUNCTIONS ---

export const uploadOperatorData = async (missionId: string, operator: string, documentType: string, file: File, userId?: string): Promise<OperatorUploadResponse> => {
    if (USE_MOCK_API) {
        await sleep(MOCK_API_DELAY * 2);
        
        const newSheet: OperatorSheet = {
            id: generateId(),
            filename: file.name,
            operator,
            documentType,
            uploadDate: new Date().toISOString(),
            processedRecords: Math.floor(Math.random() * 1000) + 100,
            status: 'completed',
            missionId
        };
        
        mockOperatorSheets.push(newSheet);
        
        const response: OperatorUploadResponse = {
            success: true,
            sheetId: newSheet.id,
            message: `Archivo ${file.name} procesado exitosamente`,
            processedRecords: newSheet.processedRecords,
            warnings: [],
            errors: []
        };
        
        console.log('📊 Datos de operador mock cargados:', file.name, 'para operador:', operator);
        return response;
    }
    
    const content = await toBase64(file);
    // Extraer solo el contenido Base64 sin el prefijo "data:..."
    const base64Data = content.split(',')[1] || content;
    
    // Usar userId por defecto si no se proporciona (usar el primer usuario disponible para testing)
    // En producción, esto debería venir del estado de sesión del usuario autenticado
    const defaultUserId = userId || 'admin';
    
    // Logging detallado de los parámetros enviados
    console.log('🔍 FRONTEND: Enviando solicitud al backend:', {
        fileName: file.name,
        missionId,
        operator,
        documentType,
        userId: defaultUserId,
        fileSize: file.size
    });
    
    // Corregir el orden de parámetros según la función backend:
    // upload_operator_data(file_data, file_name, mission_id, operator, file_type, user_id)
    const backendResponse = await handleEelResponse(() => window.eel.upload_operator_data(
        base64Data,      // file_data: contenido Base64 del archivo
        file.name,       // file_name: nombre original del archivo
        missionId,       // mission_id: ID de la misión
        operator,        // operator: operador celular
        documentType,    // file_type: tipo de documento/datos
        defaultUserId    // user_id: ID del usuario que sube el archivo
    )(), 'cargar datos de operador');
    
    // Logging detallado de la respuesta del backend
    console.log('📥 FRONTEND: Respuesta del backend recibida:', backendResponse);
    console.log('📊 FRONTEND: processedRecords en respuesta:', backendResponse?.processedRecords);
    console.log('📊 FRONTEND: Tipo de processedRecords:', typeof backendResponse?.processedRecords);
    
    return backendResponse;
};

export const getOperatorSheets = async (missionId: string): Promise<OperatorSheet[]> => {
    if (USE_MOCK_API) {
        await sleep(MOCK_API_DELAY);
        const sheets = mockOperatorSheets.filter(sheet => sheet.missionId === missionId);
        console.log('📊 Obteniendo hojas de operador mock:', sheets.length, 'hojas para misión:', missionId);
        return JSON.parse(JSON.stringify(sheets));
    }
    
    const response = await handleEelResponse(() => window.eel.get_operator_sheets(missionId)(), 'obtener hojas de operador');
    
    console.log('🔍 FRONTEND: Respuesta de get_operator_sheets:', response);
    
    // El backend retorna { success: true, data: [...], total_count: number }
    // Necesitamos extraer el array 'data' y mapear los campos
    if (response && typeof response === 'object' && 'data' in response && Array.isArray(response.data)) {
        const mappedSheets: OperatorSheet[] = response.data.map((backendSheet: any) => {
            console.log('🔍 FRONTEND: Mapeando sheet desde backend:', backendSheet);
            
            const mappedSheet: OperatorSheet = {
                id: backendSheet.id || '',
                filename: backendSheet.file_name || 'Archivo desconocido',
                operator: backendSheet.operator || 'DESCONOCIDO',
                documentType: backendSheet.file_type || 'DESCONOCIDO',
                uploadDate: backendSheet.uploaded_at || new Date().toISOString(),
                processedRecords: backendSheet.records_processed || 0,
                status: mapBackendStatus(backendSheet.processing_status),
                errorMessage: backendSheet.error_details || undefined,
                missionId: backendSheet.mission_id || missionId
            };
            
            console.log('🔍 FRONTEND: Sheet mapeado:', mappedSheet);
            return mappedSheet;
        });
        
        console.log('✅ FRONTEND: Total sheets mapeados:', mappedSheets.length);
        return mappedSheets;
    }
    
    // Fallback: si la respuesta no tiene la estructura esperada, asumir que es el array directamente
    if (Array.isArray(response)) {
        console.warn('⚠️ FRONTEND: Respuesta es array directo, intentando mapear...');
        return response.map((item: any) => ({
            id: item.id || '',
            filename: item.file_name || item.filename || 'Archivo desconocido',
            operator: item.operator || 'DESCONOCIDO',
            documentType: item.file_type || item.documentType || 'DESCONOCIDO',
            uploadDate: item.uploaded_at || item.uploadDate || new Date().toISOString(),
            processedRecords: item.records_processed || item.processedRecords || 0,
            status: mapBackendStatus(item.processing_status || item.status),
            errorMessage: item.error_details || item.errorMessage || undefined,
            missionId: item.mission_id || item.missionId || missionId
        }));
    }
    
    // Si nada funciona, retornar array vacío
    console.warn('⚠️ Respuesta inesperada de get_operator_sheets:', response);
    return [];
};

// Función auxiliar para mapear estados del backend al frontend
function mapBackendStatus(backendStatus?: string): 'processing' | 'completed' | 'error' {
    if (!backendStatus) return 'error';
    
    switch (backendStatus.toUpperCase()) {
        case 'COMPLETED':
            return 'completed';
        case 'PROCESSING':
        case 'IN_PROGRESS':
            return 'processing';
        case 'FAILED':
        case 'ERROR':
        default:
            return 'error';
    }
}

export const getOperatorSheetData = async (sheetId: string, page: number = 1, pageSize: number = 50): Promise<{data: OperatorCellularRecord[], total: number, hasMore: boolean, columns?: string[], displayNames?: {[key: string]: string}}> => {
    if (USE_MOCK_API) {
        await sleep(MOCK_API_DELAY);
        
        // Generar datos mock
        const total = Math.floor(Math.random() * 500) + 50;
        const startIndex = (page - 1) * pageSize;
        const endIndex = Math.min(startIndex + pageSize, total);
        const hasMore = endIndex < total;
        
        const data: OperatorCellularRecord[] = [];
        for (let i = startIndex; i < endIndex; i++) {
            data.push({
                id: i + 1,
                sheetId,
                phoneNumber: `300${Math.floor(Math.random() * 9999999).toString().padStart(7, '0')}`,
                imei: `${Math.floor(Math.random() * 999999999999999)}`,
                imsi: `732${Math.floor(Math.random() * 999999999999)}`,
                cellId: Math.floor(Math.random() * 99999).toString(),
                lac: Math.floor(Math.random() * 9999).toString(),
                timestamp: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
                location: `Ubicación ${i + 1}`,
                operator: 'CLARO',
                documentType: 'CDR',
                rawData: {
                    original_column_1: `valor_${i + 1}`,
                    original_column_2: Math.random() * 100
                }
            });
        }
        
        console.log('📊 Obteniendo datos de hoja mock:', sheetId, 'página:', page, 'registros:', data.length);
        return { data, total, hasMore };
    }
    
    return handleEelResponse(() => window.eel.get_operator_sheet_data(sheetId, page, pageSize)(), 'obtener datos de hoja de operador');
};

export const deleteOperatorSheet = async (missionId: string, sheetId: string, userId?: string): Promise<{status: string}> => {
    if (USE_MOCK_API) {
        await sleep(MOCK_API_DELAY);
        const sheetToDelete = mockOperatorSheets.find(sheet => sheet.id === sheetId);
        mockOperatorSheets = mockOperatorSheets.filter(sheet => sheet.id !== sheetId);
        console.log('🗑️ Hoja de operador mock eliminada:', sheetToDelete?.filename || 'desconocida');
        return { status: 'ok' };
    }
    
    // El backend espera (file_upload_id, user_id), no (missionId, sheetId)
    // Usar userId por defecto si no se proporciona
    const defaultUserId = userId || 'admin';
    
    console.log('🗑️ FRONTEND: Eliminando archivo:', {
        sheetId,
        userId: defaultUserId
    });
    
    return handleEelResponse(() => window.eel.delete_operator_sheet(sheetId, defaultUserId)(), 'eliminar hoja de operador');
};

export const getOperatorStatistics = async (missionId?: string): Promise<{success: boolean, statistics: any, totals: any, mission_id?: string, error?: string}> => {
    if (USE_MOCK_API) {
        await sleep(MOCK_API_DELAY);
        
        // Mock statistics
        const mockStats = {
            'TIGO': {
                total_files: 2,
                total_records: 5000,
                total_failed: 50,
                completed_files: 2,
                failed_files: 0,
                success_rate: 100
            },
            'CLARO': {
                total_files: 3,
                total_records: 3000,
                total_failed: 0,
                completed_files: 3,
                failed_files: 0,
                success_rate: 100
            }
        };
        
        const mockTotals = {
            total_files: 5,
            total_records: 8000,
            total_failed: 50,
            completed_files: 5,
            failed_files: 0,
            success_rate: 100
        };
        
        console.log('📊 Estadísticas de operador mock:', mockTotals);
        return {
            success: true,
            statistics: mockStats,
            totals: mockTotals,
            mission_id: missionId
        };
    }
    
    return handleEelResponse(() => window.eel.get_operator_statistics(missionId)(), 'obtener estadísticas de operador');
};

// ============================================================================
// ANÁLISIS DE CORRELACIÓN
// ============================================================================

/**
 * Ejecuta análisis de correlación entre datos HUNTER y operadores
 */
export const analyzeCorrelation = async (
    missionId: string, 
    startDateTime: string, 
    endDateTime: string, 
    minOccurrences: number = 1
): Promise<CorrelationAnalysisResponse> => {
    if (USE_MOCK_API) {
        await sleep(MOCK_API_DELAY * 2); // Simular procesamiento más largo
        
        // Mock de resultados de correlación
        const mockResults: CorrelationResult[] = [
            {
                targetNumber: "3224274851",
                operator: "CLARO",
                occurrences: 5,
                firstDetection: "2024-01-15T10:30:00",
                lastDetection: "2024-01-15T14:45:00",
                relatedCells: ["56124", "51438", "51203"],
                confidence: 85.5
            },
            {
                targetNumber: "3104277553",
                operator: "MOVISTAR",
                occurrences: 3,
                firstDetection: "2024-01-15T11:15:00",
                lastDetection: "2024-01-15T13:20:00",
                relatedCells: ["56124", "63095"],
                confidence: 72.0
            },
            {
                targetNumber: "3143534707",
                operator: "CLARO",
                occurrences: 8,
                firstDetection: "2024-01-15T09:00:00",
                lastDetection: "2024-01-15T15:30:00",
                relatedCells: ["51203", "51438", "56124", "22504"],
                confidence: 92.3
            }
        ];
        
        return {
            success: true,
            data: mockResults,
            statistics: {
                totalAnalyzed: 1500,
                totalFound: mockResults.length,
                processingTime: 2.5
            }
        };
    }
    
    return handleEelResponse(
        () => window.eel.analyze_correlation(missionId, startDateTime, endDateTime, minOccurrences)(),
        'ejecutar análisis de correlación'
    );
};

/**
 * Obtiene resumen de correlación para una misión
 */
export const getCorrelationSummary = async (missionId: string): Promise<any> => {
    if (USE_MOCK_API) {
        await sleep(MOCK_API_DELAY);
        
        return {
            success: true,
            summary: {
                totalTargets: 15,
                highConfidence: 5,
                mediumConfidence: 7,
                lowConfidence: 3,
                topOperators: ["CLARO", "MOVISTAR"],
                dateRange: {
                    start: "2024-01-15T00:00:00",
                    end: "2024-01-15T23:59:59"
                }
            }
        };
    }
    
    return handleEelResponse(
        () => window.eel.get_correlation_summary(missionId)(),
        'obtener resumen de correlación'
    );
};



