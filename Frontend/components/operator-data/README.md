# Componentes de Datos de Operador

Esta carpeta contiene los componentes React para la gestión de datos de operadores móviles en KRONOS.

## Componentes

### OperatorDataUpload
Componente para cargar archivos de datos de operadores móviles (CDR, ubicación, IMEI).

**Características:**
- Selector de operador (CLARO, MOVISTAR, TIGO, WOM)
- Selector de tipo de documento por operador
- Área de drag & drop para archivos
- Validación de formato (CSV/XLSX) y tamaño (20MB)
- Barra de progreso durante carga
- Manejo de errores user-friendly

### OperatorSheetsManager
Componente para gestionar archivos de datos de operadores ya cargados.

**Características:**
- Lista de archivos cargados con metadatos
- Filtros por operador y tipo de documento
- Vista paginada de datos de archivos
- Opción para eliminar archivos
- Modal para visualizar datos detallados

## Uso

```tsx
import { OperatorDataUpload, OperatorSheetsManager } from '../components/operator-data';

// Componente de carga
<OperatorDataUpload
    missionId={missionId}
    onUploadSuccess={handleUploadSuccess}
    onUploadError={handleUploadError}
/>

// Componente de gestión
<OperatorSheetsManager
    missionId={missionId}
    sheets={operatorSheets}
    onRefresh={loadOperatorSheets}
    onDeleteSheet={handleDeleteSheet}
/>
```

## API Backend

Los componentes se integran con las siguientes funciones del backend Python:

- `upload_operator_data(mission_id, operator, document_type, file_data)`
- `get_operator_sheets(mission_id)`
- `get_operator_sheet_data(sheet_id, page, page_size)`
- `delete_operator_sheet(mission_id, sheet_id)`

## Tipos de Operadores y Documentos

### CLARO
- CDR (Call Detail Records)
- Datos de Ubicación
- Registros IMEI

### MOVISTAR, TIGO, WOM
- CDR (Call Detail Records)
- Datos de Ubicación

## Validaciones

- **Formato de archivo:** Solo CSV, XLSX, XLS
- **Tamaño máximo:** 20MB
- **Operador:** Obligatorio
- **Tipo de documento:** Obligatorio según operador

## Estados de Procesamiento

- `processing`: Archivo siendo procesado
- `completed`: Procesamiento exitoso
- `error`: Error en el procesamiento