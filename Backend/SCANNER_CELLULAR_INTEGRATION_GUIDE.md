# KRONOS Scanner Cellular Data - Guía de Integración Completa

## Resumen Ejecutivo

Esta guía proporciona instrucciones completas para integrar el nuevo sistema optimizado de datos de scanner celular (SCANHUNTER) con la arquitectura existente de KRONOS.

## Arquitectura de la Solución

### Componentes Principales

```
Frontend (React/TypeScript)
├── Interfaz de carga de archivos SCANHUNTER
├── Visualización de datos de scanner
└── Análisis de cobertura celular

Backend (Python/Eel)
├── ScannerDataProcessor - Procesamiento y validación
├── Scanner Cellular Models - ORM optimizado
├── Database Schema - Estructura optimizada
└── API Integration - Endpoints especializados

Database (SQLite)
├── scanner_cellular_data - Tabla principal
├── cellular_operators - Configuración de operadores
├── Optimized Indexes - Rendimiento de consultas
└── Views & Triggers - Mantenimiento automático
```

## Instalación y Configuración

### 1. Ejecutar Migración de Base de Datos

```bash
# Desde Backend/
python database/migration_scanner_cellular_v1.py kronos.db

# Con backup (recomendado para producción)
python database/migration_scanner_cellular_v1.py kronos.db --backup
```

### 2. Verificar Migración

```python
# Verificar que las tablas se crearon correctamente
import sqlite3

with sqlite3.connect('kronos.db') as conn:
    cursor = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name IN ('scanner_cellular_data', 'cellular_operators')
    """)
    tables = cursor.fetchall()
    print(f"Tablas creadas: {[t[0] for t in tables]}")
```

### 3. Instalar Dependencias Python

```bash
pip install pandas openpyxl numpy hashlib
```

## Integración con Backend Existente

### 1. Actualizar Modelos SQLAlchemy

El archivo `Backend/database/models.py` debe incluir el nuevo modelo:

```python
# Agregar al final de models.py
from .scanner_models import ScannerCellularData, CellularOperator

# Actualizar función get_all_models()
def get_all_models():
    return [Role, User, Mission, CellularData, TargetRecord, 
            ScannerCellularData, CellularOperator]
```

### 2. Crear Modelo SQLAlchemy Actualizado

Crear archivo `Backend/database/scanner_models.py`:

```python
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from .models import Base, BaseModel

class ScannerCellularData(Base, BaseModel):
    __tablename__ = 'scanner_cellular_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    mission_id = Column(String, ForeignKey('missions.id'), nullable=False)
    punto = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    mnc_mcc = Column(String, nullable=False)
    operator_name = Column(String, nullable=False)
    rssi_dbm = Column(Integer, nullable=False)
    technology = Column(String, nullable=False)
    cell_id = Column(String, nullable=False)
    lac_tac = Column(String)
    enb_id = Column(String)
    channel = Column(String)
    comentario = Column(Text)
    file_source = Column(String)
    processing_timestamp = Column(DateTime)
    is_validated = Column(Boolean, default=True)
    
    # Relación con Mission
    mission = relationship("Mission")
    
    def to_dict(self):
        result = super().to_dict()
        # Mapeo para compatibilidad con frontend
        frontend_mapping = {
            'mnc_mcc': 'mncMcc',
            'operator_name': 'operador',
            'rssi_dbm': 'rssi',
            'cell_id': 'cellId',
            'lac_tac': 'lacTac',
            'enb_id': 'enb'
        }
        
        for backend_key, frontend_key in frontend_mapping.items():
            if backend_key in result:
                result[frontend_key] = result.pop(backend_key)
        
        return result

class CellularOperator(Base, BaseModel):
    __tablename__ = 'cellular_operators'
    
    id = Column(Integer, primary_key=True)
    operator_name = Column(String, nullable=False, unique=True)
    mnc_codes = Column(Text)  # JSON string
    frequency_bands = Column(Text)  # JSON string
    technologies = Column(Text)  # JSON string
```

### 3. Crear Servicio de Scanner Data

Crear archivo `Backend/services/scanner_cellular_service.py`:

```python
import eel
from typing import List, Dict, Any, Optional
from services.scanner_data_processor import ScannerDataProcessor
from database.connection import get_db_session
from database.scanner_models import ScannerCellularData

class ScannerCellularService:
    
    @staticmethod
    @eel.expose
    def upload_scanner_file(mission_id: str, file_data: str, filename: str) -> Dict[str, Any]:
        """
        Procesa archivo SCANHUNTER subido desde frontend
        """
        try:
            # Decodificar archivo base64 y procesarlo
            processor = ScannerDataProcessor(mission_id)
            
            # Procesar archivo (implementar decodificación base64)
            processed_df, stats, validations = processor.process_file_from_base64(
                file_data, filename
            )
            
            # Guardar en base de datos
            with get_db_session() as session:
                for _, row in processed_df.iterrows():
                    scanner_data = ScannerCellularData(**row.to_dict())
                    session.add(scanner_data)
                session.commit()
            
            return {
                'success': True,
                'stats': {
                    'totalRows': stats.total_rows,
                    'validRows': stats.valid_rows,
                    'invalidRows': stats.invalid_rows,
                    'warnings': stats.warnings,
                    'errors': stats.errors
                },
                'validations': [
                    {
                        'row': v.row_index,
                        'field': v.field,
                        'severity': v.severity.value,
                        'message': v.message
                    } for v in validations[:50]  # Limitar a 50 para evitar overflow
                ]
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    @eel.expose
    def get_scanner_data(mission_id: str, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Obtiene datos de scanner para una misión
        """
        try:
            with get_db_session() as session:
                query = session.query(ScannerCellularData).filter(
                    ScannerCellularData.mission_id == mission_id
                )
                
                # Aplicar filtros opcionales
                if filters:
                    if 'operator' in filters:
                        query = query.filter(
                            ScannerCellularData.operator_name == filters['operator']
                        )
                    if 'technology' in filters:
                        query = query.filter(
                            ScannerCellularData.technology == filters['technology']
                        )
                    if 'minRssi' in filters:
                        query = query.filter(
                            ScannerCellularData.rssi_dbm >= filters['minRssi']
                        )
                
                results = query.all()
                return [record.to_dict() for record in results]
                
        except Exception as e:
            print(f"Error obteniendo datos scanner: {str(e)}")
            return []
    
    @staticmethod
    @eel.expose
    def get_coverage_analysis(mission_id: str) -> Dict[str, Any]:
        """
        Genera análisis de cobertura para una misión
        """
        try:
            with get_db_session() as session:
                # Usar vista optimizada para análisis
                results = session.execute("""
                    SELECT * FROM vw_scanner_coverage_summary 
                    WHERE mission_id = ?
                """, (mission_id,)).fetchall()
                
                coverage_data = []
                for row in results:
                    coverage_data.append({
                        'operator': row.operator_name,
                        'technology': row.technology,
                        'totalMeasurements': row.total_measurements,
                        'avgRssi': round(row.avg_rssi, 2),
                        'minRssi': row.min_rssi,
                        'maxRssi': row.max_rssi,
                        'uniquePoints': row.unique_points,
                        'uniqueCells': row.unique_cells,
                        'goodSignalPercent': round(
                            (row.good_signal_count / row.total_measurements) * 100, 1
                        ),
                        'coverageArea': {
                            'minLat': row.min_lat,
                            'maxLat': row.max_lat,
                            'minLon': row.min_lon,
                            'maxLon': row.max_lon
                        }
                    })
                
                return {
                    'missionId': mission_id,
                    'coverageData': coverage_data,
                    'generatedAt': datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"Error en análisis de cobertura: {str(e)}")
            return {'error': str(e)}
```

### 4. Integración con Frontend

#### Actualizar types.ts

```typescript
// Agregar interfaces para datos de scanner
export interface ScannerCellularRecord {
    id: number;
    punto: string;
    lat: string;
    lon: string;
    mncMcc: string;
    operador: string;
    rssi: number;
    tecnologia: string;
    cellId: string;
    lacTac?: string;
    enb?: string;
    channel?: string;
    comentario?: string;
    fileSource?: string;
    processingTimestamp?: string;
}

export interface ScannerUploadResponse {
    success: boolean;
    stats?: {
        totalRows: number;
        validRows: number;
        invalidRows: number;
        warnings: number;
        errors: number;
    };
    validations?: Array<{
        row: number;
        field: string;
        severity: 'info' | 'warning' | 'error' | 'critical';
        message: string;
    }>;
    error?: string;
}

export interface CoverageAnalysis {
    missionId: string;
    coverageData: Array<{
        operator: string;
        technology: string;
        totalMeasurements: number;
        avgRssi: number;
        minRssi: number;
        maxRssi: number;
        uniquePoints: number;
        uniqueCells: number;
        goodSignalPercent: number;
        coverageArea: {
            minLat: number;
            maxLat: number;
            minLon: number;
            maxLon: number;
        };
    }>;
    generatedAt: string;
}
```

#### Actualizar api.ts

```typescript
// Agregar funciones para scanner data
export const uploadScannerFile = async (
    missionId: string,
    fileData: string,
    filename: string
): Promise<ScannerUploadResponse> => {
    if (USE_MOCK_API) {
        // Mock implementation
        return {
            success: true,
            stats: {
                totalRows: 58,
                validRows: 56,
                invalidRows: 2,
                warnings: 3,
                errors: 2
            }
        };
    }
    
    return window.eel.upload_scanner_file(missionId, fileData, filename)();
};

export const getScannerData = async (
    missionId: string,
    filters?: {
        operator?: string;
        technology?: string;
        minRssi?: number;
    }
): Promise<ScannerCellularRecord[]> => {
    if (USE_MOCK_API) {
        return mockScannerData;
    }
    
    return window.eel.get_scanner_data(missionId, filters)();
};

export const getCoverageAnalysis = async (
    missionId: string
): Promise<CoverageAnalysis> => {
    if (USE_MOCK_API) {
        return mockCoverageAnalysis;
    }
    
    return window.eel.get_coverage_analysis(missionId)();
};
```

## Casos de Uso Principales

### 1. Carga de Archivo SCANHUNTER

```typescript
// Componente FileUpload especializado
const handleScannerFileUpload = async (file: File) => {
    try {
        const fileData = await convertFileToBase64(file);
        const result = await uploadScannerFile(
            currentMissionId, 
            fileData, 
            file.name
        );
        
        if (result.success) {
            showNotification(`Archivo procesado: ${result.stats.validRows} registros válidos`);
            if (result.validations && result.validations.length > 0) {
                showValidationResults(result.validations);
            }
        } else {
            showError(`Error procesando archivo: ${result.error}`);
        }
    } catch (error) {
        showError(`Error cargando archivo: ${error.message}`);
    }
};
```

### 2. Visualización de Datos Scanner

```typescript
// Componente para mostrar datos de scanner
const ScannerDataTable: React.FC<{missionId: string}> = ({missionId}) => {
    const [scannerData, setScannerData] = useState<ScannerCellularRecord[]>([]);
    const [filters, setFilters] = useState({});
    
    useEffect(() => {
        const loadData = async () => {
            const data = await getScannerData(missionId, filters);
            setScannerData(data);
        };
        loadData();
    }, [missionId, filters]);
    
    return (
        <div>
            <ScannerFilters onFiltersChange={setFilters} />
            <Table
                data={scannerData}
                columns={[
                    {key: 'punto', title: 'Punto'},
                    {key: 'operador', title: 'Operador'},
                    {key: 'tecnologia', title: 'Tecnología'},
                    {key: 'rssi', title: 'RSSI (dBm)'},
                    {key: 'cellId', title: 'Cell ID'},
                    {key: 'lat', title: 'Latitud'},
                    {key: 'lon', title: 'Longitud'}
                ]}
            />
        </div>
    );
};
```

### 3. Análisis de Cobertura

```typescript
// Componente para análisis de cobertura
const CoverageAnalysisView: React.FC<{missionId: string}> = ({missionId}) => {
    const [analysis, setAnalysis] = useState<CoverageAnalysis | null>(null);
    
    useEffect(() => {
        const loadAnalysis = async () => {
            const result = await getCoverageAnalysis(missionId);
            setAnalysis(result);
        };
        loadAnalysis();
    }, [missionId]);
    
    if (!analysis) return <div>Cargando análisis...</div>;
    
    return (
        <div className="coverage-analysis">
            {analysis.coverageData.map((coverage, index) => (
                <div key={index} className="coverage-card">
                    <h3>{coverage.operator} - {coverage.technology}</h3>
                    <div className="stats">
                        <div>Mediciones: {coverage.totalMeasurements}</div>
                        <div>RSSI Promedio: {coverage.avgRssi} dBm</div>
                        <div>Buena Señal: {coverage.goodSignalPercent}%</div>
                        <div>Puntos Únicos: {coverage.uniquePoints}</div>
                        <div>Celdas Únicas: {coverage.uniqueCells}</div>
                    </div>
                </div>
            ))}
        </div>
    );
};
```

## Consideraciones de Rendimiento

### 1. Límites de Archivo
- Máximo 10MB por archivo SCANHUNTER
- Máximo 50,000 registros por archivo
- Procesamiento en chunks de 1,000 registros

### 2. Cache de Consultas
- Implementar cache en memoria para datos frecuentes
- TTL de 5 minutos para análisis de cobertura
- Invalidar cache al subir nuevos archivos

### 3. Paginación
- Paginar resultados de más de 1,000 registros
- Implementar scroll virtual para tablas grandes
- Lazy loading para mapas con muchos puntos

## Monitoreo y Debugging

### 1. Logging
```python
# Configurar logging detallado
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scanner_cellular.log'),
        logging.StreamHandler()
    ]
)
```

### 2. Métricas Clave
- Tiempo de procesamiento por archivo
- Tasa de errores de validación
- Uso de memoria durante procesamiento
- Performance de consultas de base de datos

### 3. Alertas
- Archivos con >20% de errores de validación
- Consultas que toman >5 segundos
- Uso de memoria >80% durante procesamiento

## Troubleshooting Común

### Error: "Columnas requeridas faltantes"
**Solución**: Verificar formato del archivo SCANHUNTER y mapeo de columnas

### Error: "RSSI fuera de rango"
**Solución**: Verificar que valores RSSI sean negativos (dBm)

### Consultas lentas
**Solución**: Verificar que indices estén creados correctamente

### Duplicados detectados
**Solución**: Revisar lógica de generación de hash único

## Roadmap de Mejoras

### Versión 1.1
- Soporte para múltiples formatos de scanner
- Visualización geográfica interactiva
- Exportación de análisis a PDF

### Versión 1.2  
- Machine learning para detección de anomalías
- API REST para integración externa
- Dashboard en tiempo real

### Versión 2.0
- Soporte para datos de drive test
- Análisis predictivo de cobertura
- Integración con sistemas GIS

---

**Soporte**: Para problemas técnicos, revisar logs en `Backend/scanner_cellular.log` y consultar esta documentación.