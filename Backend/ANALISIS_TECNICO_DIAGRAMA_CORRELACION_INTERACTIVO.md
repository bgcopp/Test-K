# ANÁLISIS TÉCNICO - DIAGRAMA DE CORRELACIÓN INTERACTIVO

## INFORMACIÓN DEL DOCUMENTO
**Versión:** 1.0.0  
**Fecha:** 18 de Agosto, 2025  
**Autor:** Claude Code para Boris  
**Sistema:** KRONOS - Diagrama de Correlación Interactivo  
**Propósito:** Especificaciones técnicas para implementación de diagrama de red de comunicaciones  

---

## TABLA DE CONTENIDOS

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Arquitectura de Base de Datos](#2-arquitectura-de-base-de-datos)
3. [Consultas SQL Especializadas](#3-consultas-sql-especializadas)
4. [Estructura de Datos para Diagrama](#4-estructura-de-datos-para-diagrama)
5. [API de Servicios Backend](#5-api-de-servicios-backend)
6. [Especificaciones de Frontend](#6-especificaciones-de-frontend)
7. [Optimizaciones de Rendimiento](#7-optimizaciones-de-rendimiento)

---

## 1. RESUMEN EJECUTIVO

### 1.1 Objetivo del Diagrama
Crear un diagrama de red interactivo que visualice las **comunicaciones de un número objetivo** correlacionadas con **datos HUNTER de presencia física en celdas**.

### 1.2 Características Principales
- **Nodos:** Números de teléfono participantes (objetivo + contactos)
- **Aristas:** Comunicaciones (llamadas/datos) con metadatos
- **Filtro HUNTER:** Solo celdas donde el número objetivo estuvo físicamente presente
- **Interactividad:** Zoom, filtros temporales, tipos de comunicación
- **Tiempo Real:** Datos actualizados desde base de datos

### 1.3 Datos de Fuente Actual
```json
{
  "base_datos_actual": {
    "cellular_data": {
      "registros": 58,
      "celdas_hunter_unicas": 57,
      "proposito": "Ubicaciones físicas detectadas por equipo HUNTER"
    },
    "operator_call_data": {
      "registros": 3309,
      "celdas_origen_unicas": 253,
      "celdas_destino_unicas": 71,
      "proposito": "Registros CDR de comunicaciones de operadores"
    }
  }
}
```

---

## 2. ARQUITECTURA DE BASE DE DATOS

### 2.1 Tablas Clave para Diagrama

#### 2.1.1 Tabla `cellular_data` (DATOS HUNTER)
```sql
-- CAMPOS CRÍTICOS PARA CORRELACIÓN
CREATE TABLE cellular_data (
    id INTEGER NOT NULL PRIMARY KEY,
    mission_id VARCHAR NOT NULL,           -- FK: Misión
    cell_id VARCHAR NOT NULL,              -- CLAVE: ID de celda HUNTER
    operator VARCHAR NOT NULL,             -- Operador detectado
    tecnologia VARCHAR NOT NULL,           -- GSM, LTE, 5G, etc.
    lat FLOAT NOT NULL,                    -- Latitud GPS
    lon FLOAT NOT NULL,                    -- Longitud GPS
    rssi INTEGER NOT NULL,                 -- Intensidad señal
    punto VARCHAR NOT NULL,                -- Punto de medición
    created_at DATETIME                    -- Timestamp detección
);
```

**Propósito:** Define las celdas donde el equipo HUNTER detectó presencia física.

#### 2.1.2 Tabla `operator_call_data` (COMUNICACIONES CDR)
```sql
-- CAMPOS CRÍTICOS PARA DIAGRAMA
CREATE TABLE operator_call_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id TEXT NOT NULL,              -- FK: Misión
    operator TEXT NOT NULL,                -- CLARO, MOVISTAR, TIGO, WOM
    
    -- PARTICIPANTES DE COMUNICACIÓN
    numero_origen TEXT NOT NULL,           -- Número que inicia
    numero_destino TEXT NOT NULL,          -- Número que recibe
    numero_objetivo TEXT NOT NULL,         -- Número bajo investigación
    
    -- INFORMACIÓN TEMPORAL
    fecha_hora_llamada DATETIME NOT NULL,  -- Timestamp comunicación
    duracion_segundos INTEGER DEFAULT 0,   -- Duración
    
    -- UBICACIÓN (CORRELACIÓN CON HUNTER)
    celda_origen TEXT,                     -- Celda del originador
    celda_destino TEXT,                    -- Celda del receptor
    celda_objetivo TEXT,                   -- Celda del objetivo
    
    -- METADATOS COMUNICACIÓN
    tipo_llamada TEXT NOT NULL,            -- ENTRANTE, SALIENTE, MIXTA
    tipo_trafico TEXT DEFAULT 'VOZ',       -- VOZ, SMS, MMS, DATOS
    estado_llamada TEXT DEFAULT 'COMPLETADA',
    tecnologia TEXT DEFAULT 'UNKNOWN'
);
```

**Propósito:** Contiene registros de todas las comunicaciones con ubicación de celdas.

### 2.2 Relación de Correlación HUNTER-CDR

```sql
-- CORRELACIÓN CLAVE: cell_id ↔ celda_origen/celda_destino
-- 
-- cellular_data.cell_id = operator_call_data.celda_origen
-- cellular_data.cell_id = operator_call_data.celda_destino
--
-- LÓGICA: Solo mostrar comunicaciones donde al menos una celda
--         coincida con ubicaciones HUNTER detectadas
```

### 2.3 Índices de Optimización Existentes

```sql
-- ÍNDICES PARA CORRELACIÓN (Ya implementados)
CREATE INDEX idx_correlation_origen_critical 
ON operator_call_data(celda_origen, mission_id, fecha_hora_llamada, numero_origen);

CREATE INDEX idx_correlation_destino_critical 
ON operator_call_data(celda_destino, mission_id, fecha_hora_llamada, numero_destino);

-- ÍNDICES HUNTER
CREATE INDEX idx_hunter_cellid_mission 
ON cellular_data(cell_id, mission_id, created_at);

-- ÍNDICES COVERING
CREATE INDEX idx_covering_correlation_summary 
ON operator_call_data(numero_origen, numero_destino, operator, mission_id, 
                      celda_origen, celda_destino, fecha_hora_llamada);
```

---

## 3. CONSULTAS SQL ESPECIALIZADAS

### 3.1 Query Principal: Obtener Red de Comunicaciones

```sql
-- CONSULTA MAESTRA PARA DIAGRAMA DE CORRELACIÓN
-- Obtiene todas las comunicaciones de un número objetivo
-- filtradas por celdas donde estuvo presente según datos HUNTER

WITH hunter_cells AS (
    -- Paso 1: Obtener celdas HUNTER reales de la misión
    SELECT DISTINCT cell_id
    FROM cellular_data 
    WHERE mission_id = :mission_id
),

target_communications AS (
    -- Paso 2: Comunicaciones del número objetivo en celdas HUNTER
    SELECT DISTINCT
        ocd.numero_origen,
        ocd.numero_destino,
        ocd.numero_objetivo,
        ocd.celda_origen,
        ocd.celda_destino,
        ocd.fecha_hora_llamada,
        ocd.duracion_segundos,
        ocd.tipo_llamada,
        ocd.tipo_trafico,
        ocd.estado_llamada,
        ocd.tecnologia,
        ocd.operator,
        
        -- Identificar si es comunicación entrante o saliente para el objetivo
        CASE 
            WHEN ocd.numero_origen = :numero_objetivo THEN 'SALIENTE'
            WHEN ocd.numero_destino = :numero_objetivo THEN 'ENTRANTE'
            ELSE 'UNKNOWN'
        END as direccion_objetivo,
        
        -- Identificar el "otro" participante (no el objetivo)
        CASE 
            WHEN ocd.numero_origen = :numero_objetivo THEN ocd.numero_destino
            WHEN ocd.numero_destino = :numero_objetivo THEN ocd.numero_origen
            ELSE NULL
        END as numero_contacto
        
    FROM operator_call_data ocd
    INNER JOIN hunter_cells hc ON (
        ocd.celda_origen = hc.cell_id OR 
        ocd.celda_destino = hc.cell_id
    )
    WHERE ocd.mission_id = :mission_id
      AND (ocd.numero_origen = :numero_objetivo OR ocd.numero_destino = :numero_objetivo)
      AND DATE(ocd.fecha_hora_llamada) BETWEEN :start_date AND :end_date
      AND ocd.celda_origen IS NOT NULL 
      AND ocd.celda_destino IS NOT NULL
)

-- Paso 3: Resultado final con metadatos de correlación
SELECT 
    tc.*,
    
    -- Metadatos de celdas HUNTER
    hc_origen.lat as lat_celda_origen,
    hc_origen.lon as lon_celda_origen,
    hc_origen.operator as operador_celda_origen,
    hc_origen.tecnologia as tech_celda_origen,
    hc_origen.rssi as rssi_celda_origen,
    
    hc_destino.lat as lat_celda_destino,
    hc_destino.lon as lon_celda_destino,
    hc_destino.operator as operador_celda_destino,
    hc_destino.tecnologia as tech_celda_destino,
    hc_destino.rssi as rssi_celda_destino
    
FROM target_communications tc

-- LEFT JOIN para obtener metadatos de celdas HUNTER (pueden no estar todas)
LEFT JOIN cellular_data hc_origen ON (
    tc.celda_origen = hc_origen.cell_id AND 
    hc_origen.mission_id = :mission_id
)
LEFT JOIN cellular_data hc_destino ON (
    tc.celda_destino = hc_destino.cell_id AND 
    hc_destino.mission_id = :mission_id
)

ORDER BY tc.fecha_hora_llamada DESC;
```

### 3.2 Query de Estadísticas: Resumen de Contactos

```sql
-- ESTADÍSTICAS DE CONTACTOS PARA EL DIAGRAMA
-- Cuenta comunicaciones por contacto para dimensionar nodos

WITH hunter_cells AS (
    SELECT DISTINCT cell_id
    FROM cellular_data 
    WHERE mission_id = :mission_id
),

contact_stats AS (
    SELECT 
        CASE 
            WHEN ocd.numero_origen = :numero_objetivo THEN ocd.numero_destino
            WHEN ocd.numero_destino = :numero_objetivo THEN ocd.numero_origen
        END as numero_contacto,
        
        ocd.operator,
        COUNT(*) as total_comunicaciones,
        COUNT(CASE WHEN ocd.tipo_trafico = 'VOZ' THEN 1 END) as llamadas_voz,
        COUNT(CASE WHEN ocd.tipo_trafico = 'SMS' THEN 1 END) as mensajes_sms,
        COUNT(CASE WHEN ocd.tipo_trafico = 'DATOS' THEN 1 END) as sesiones_datos,
        SUM(ocd.duracion_segundos) as duracion_total_segundos,
        MIN(ocd.fecha_hora_llamada) as primera_comunicacion,
        MAX(ocd.fecha_hora_llamada) as ultima_comunicacion,
        COUNT(DISTINCT ocd.celda_origen) as celdas_origen_unicas,
        COUNT(DISTINCT ocd.celda_destino) as celdas_destino_unicas
        
    FROM operator_call_data ocd
    INNER JOIN hunter_cells hc ON (
        ocd.celda_origen = hc.cell_id OR 
        ocd.celda_destino = hc.cell_id
    )
    WHERE ocd.mission_id = :mission_id
      AND (ocd.numero_origen = :numero_objetivo OR ocd.numero_destino = :numero_objetivo)
      AND DATE(ocd.fecha_hora_llamada) BETWEEN :start_date AND :end_date
    GROUP BY numero_contacto, ocd.operator
)

SELECT 
    numero_contacto,
    operator,
    total_comunicaciones,
    llamadas_voz,
    mensajes_sms,
    sesiones_datos,
    duracion_total_segundos,
    ROUND(duracion_total_segundos / 60.0, 2) as duracion_total_minutos,
    primera_comunicacion,
    ultima_comunicacion,
    celdas_origen_unicas,
    celdas_destino_unicas,
    
    -- Calcular nivel de actividad para dimensionar nodos
    CASE 
        WHEN total_comunicaciones >= 50 THEN 'ALTO'
        WHEN total_comunicaciones >= 10 THEN 'MEDIO'
        ELSE 'BAJO'
    END as nivel_actividad
    
FROM contact_stats
WHERE numero_contacto IS NOT NULL
ORDER BY total_comunicaciones DESC;
```

### 3.3 Query de Celdas HUNTER: Metadatos de Ubicación

```sql
-- METADATOS DE CELDAS HUNTER PARA MAPEO GEOGRÁFICO
-- Proporciona información de ubicación para overlay en mapa

SELECT 
    cd.cell_id,
    cd.operator,
    cd.tecnologia,
    cd.lat,
    cd.lon,
    cd.rssi,
    cd.punto,
    cd.mnc_mcc,
    cd.lac_tac,
    cd.enb,
    cd.channel,
    
    -- Contar cuántas comunicaciones pasaron por esta celda
    COUNT(DISTINCT ocd1.id) as comunicaciones_como_origen,
    COUNT(DISTINCT ocd2.id) as comunicaciones_como_destino,
    (COUNT(DISTINCT ocd1.id) + COUNT(DISTINCT ocd2.id)) as total_comunicaciones
    
FROM cellular_data cd
LEFT JOIN operator_call_data ocd1 ON (
    cd.cell_id = ocd1.celda_origen AND 
    cd.mission_id = ocd1.mission_id AND
    (ocd1.numero_origen = :numero_objetivo OR ocd1.numero_destino = :numero_objetivo)
)
LEFT JOIN operator_call_data ocd2 ON (
    cd.cell_id = ocd2.celda_destino AND 
    cd.mission_id = ocd2.mission_id AND
    (ocd2.numero_origen = :numero_objetivo OR ocd2.numero_destino = :numero_objetivo)
)

WHERE cd.mission_id = :mission_id

GROUP BY cd.cell_id, cd.operator, cd.tecnologia, cd.lat, cd.lon, 
         cd.rssi, cd.punto, cd.mnc_mcc, cd.lac_tac, cd.enb, cd.channel

ORDER BY total_comunicaciones DESC, cd.rssi DESC;
```

---

## 4. ESTRUCTURA DE DATOS PARA DIAGRAMA

### 4.1 Formato JSON de Respuesta del Backend

```json
{
  "success": true,
  "numero_objetivo": "3143534707",
  "periodo": {
    "inicio": "2021-01-01 00:00:00",
    "fin": "2021-12-31 23:59:59"
  },
  "estadisticas": {
    "total_comunicaciones": 45,
    "contactos_unicos": 12,
    "celdas_hunter_involucradas": 8,
    "duracion_total_minutos": 234.5,
    "tipos_trafico": {
      "VOZ": 32,
      "SMS": 8,
      "DATOS": 5
    }
  },
  "nodos": [
    {
      "id": "3143534707",
      "tipo": "objetivo",
      "numero": "3143534707",
      "operador": "CLARO",
      "nivel_actividad": "ALTO",
      "total_comunicaciones": 45,
      "metadata": {
        "es_numero_objetivo": true,
        "primera_comunicacion": "2021-05-15 10:30:00",
        "ultima_comunicacion": "2021-05-15 18:45:00"
      }
    },
    {
      "id": "3104277553",
      "tipo": "contacto",
      "numero": "3104277553",
      "operador": "CLARO",
      "nivel_actividad": "MEDIO",
      "total_comunicaciones": 8,
      "metadata": {
        "es_numero_objetivo": false,
        "primera_comunicacion": "2021-05-15 11:20:00",
        "ultima_comunicacion": "2021-05-15 17:30:00"
      }
    }
  ],
  "aristas": [
    {
      "id": "comm_1",
      "origen": "3143534707",
      "destino": "3104277553",
      "tipo_comunicacion": "VOZ",
      "direccion": "SALIENTE",
      "timestamp": "2021-05-15 11:20:00",
      "duracion_segundos": 120,
      "estado": "COMPLETADA",
      "tecnologia": "LTE",
      "operador": "CLARO",
      "celda_origen": "16040",
      "celda_destino": "37825",
      "metadata": {
        "es_correlacion_hunter": true,
        "celda_origen_hunter": {
          "cell_id": "16040",
          "lat": 4.6582,
          "lon": -74.0919,
          "operador": "CLARO",
          "tecnologia": "LTE",
          "rssi": -75
        },
        "celda_destino_hunter": {
          "cell_id": "37825",
          "lat": 4.6601,
          "lon": -74.0851,
          "operador": "CLARO", 
          "tecnologia": "LTE",
          "rssi": -82
        }
      }
    }
  ],
  "celdas_hunter": [
    {
      "cell_id": "16040",
      "operador": "CLARO",
      "tecnologia": "LTE",
      "lat": 4.6582,
      "lon": -74.0919,
      "rssi": -75,
      "punto_medicion": "PUNTO_1_CENTRO",
      "comunicaciones_origen": 15,
      "comunicaciones_destino": 8,
      "total_actividad": 23
    }
  ],
  "processing_time": 0.156
}
```

### 4.2 Tipos de Nodos

```typescript
// TIPOS DE NODOS PARA EL DIAGRAMA
interface NodoObjetivo {
  id: string;                    // numero_objetivo
  tipo: 'objetivo';
  numero: string;
  operador: string;
  nivel_actividad: 'ALTO' | 'MEDIO' | 'BAJO';
  total_comunicaciones: number;
  metadata: {
    es_numero_objetivo: true;
    primera_comunicacion: string;
    ultima_comunicacion: string;
  };
}

interface NodoContacto {
  id: string;                    // numero_contacto
  tipo: 'contacto';
  numero: string;
  operador: string;
  nivel_actividad: 'ALTO' | 'MEDIO' | 'BAJO';
  total_comunicaciones: number;
  metadata: {
    es_numero_objetivo: false;
    primera_comunicacion: string;
    ultima_comunicacion: string;
  };
}
```

### 4.3 Tipos de Aristas

```typescript
// TIPOS DE ARISTAS (COMUNICACIONES) PARA EL DIAGRAMA
interface AristaComunicacion {
  id: string;                          // comm_N
  origen: string;                      // numero_origen
  destino: string;                     // numero_destino
  tipo_comunicacion: 'VOZ' | 'SMS' | 'MMS' | 'DATOS';
  direccion: 'ENTRANTE' | 'SALIENTE';  // Relativo al número objetivo
  timestamp: string;                   // fecha_hora_llamada
  duracion_segundos: number;
  estado: 'COMPLETADA' | 'NO_CONTESTADA' | 'OCUPADO' | 'ERROR';
  tecnologia: string;
  operador: string;
  celda_origen: string;
  celda_destino: string;
  metadata: {
    es_correlacion_hunter: boolean;     // Al menos una celda está en HUNTER
    celda_origen_hunter?: CeldaHunterInfo;
    celda_destino_hunter?: CeldaHunterInfo;
  };
}

interface CeldaHunterInfo {
  cell_id: string;
  lat: number;
  lon: number;
  operador: string;
  tecnologia: string;
  rssi: number;
}
```

---

## 5. API DE SERVICIOS BACKEND

### 5.1 Nuevo Servicio: `DiagramCorrelationService`

```python
# Backend/services/diagram_correlation_service.py

class DiagramCorrelationService:
    """
    Servicio especializado para generar datos del diagrama de correlación
    
    Funcionalidades:
    1. Obtener red de comunicaciones de un número objetivo
    2. Filtrar por celdas HUNTER reales
    3. Generar estructura de nodos y aristas para frontend
    4. Calcular estadísticas de interacción
    """
    
    def __init__(self):
        self.db_manager = get_database_manager()
        
    def get_correlation_diagram_data(self, 
                                   mission_id: str, 
                                   numero_objetivo: str,
                                   start_datetime: str,
                                   end_datetime: str,
                                   filtros: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Genera datos completos para el diagrama de correlación
        
        Args:
            mission_id: ID de la misión
            numero_objetivo: Número telefónico objetivo
            start_datetime: Inicio período (YYYY-MM-DD HH:MM:SS)
            end_datetime: Fin período (YYYY-MM-DD HH:MM:SS)
            filtros: Filtros opcionales (tipo_trafico, operador, etc.)
            
        Returns:
            Dict con nodos, aristas y metadatos para el diagrama
        """
        
    def _build_communication_network(self, 
                                   session, 
                                   mission_id: str, 
                                   numero_objetivo: str,
                                   start_datetime: str, 
                                   end_datetime: str) -> Dict[str, Any]:
        """
        Construye la red de comunicaciones usando las consultas SQL especializadas
        """
        
    def _generate_nodes(self, comunicaciones: List[Dict]) -> List[Dict]:
        """
        Genera nodos del diagrama (objetivo + contactos)
        """
        
    def _generate_edges(self, comunicaciones: List[Dict]) -> List[Dict]:
        """
        Genera aristas del diagrama (comunicaciones)
        """
        
    def _get_hunter_cells_metadata(self, 
                                  session, 
                                  mission_id: str, 
                                  cell_ids: Set[str]) -> Dict[str, Dict]:
        """
        Obtiene metadatos de celdas HUNTER para correlación geográfica
        """
```

### 5.2 Endpoint Eel para Frontend

```python
# Backend/main.py - Nuevo endpoint para diagrama

@eel.expose
def get_correlation_diagram(mission_id: str, 
                          numero_objetivo: str,
                          start_datetime: str,
                          end_datetime: str,
                          filtros: Dict[str, Any] = None):
    """
    Endpoint Eel para obtener datos del diagrama de correlación
    
    Expuesto al frontend via window.eel.get_correlation_diagram()
    """
    try:
        diagram_service = DiagramCorrelationService()
        result = diagram_service.get_correlation_diagram_data(
            mission_id=mission_id,
            numero_objetivo=numero_objetivo,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            filtros=filtros or {}
        )
        
        logger.info(f"Diagrama generado - Nodos: {len(result.get('nodos', []))}, "
                   f"Aristas: {len(result.get('aristas', []))}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error generando diagrama de correlación: {e}")
        return {
            'success': False,
            'message': f'Error: {str(e)}',
            'nodos': [],
            'aristas': [],
            'estadisticas': {}
        }
```

---

## 6. ESPECIFICACIONES DE FRONTEND

### 6.1 Componente React: `CorrelationDiagram.tsx`

```typescript
// Frontend/components/CorrelationDiagram.tsx

interface CorrelationDiagramProps {
  missionId: string;
  numeroObjetivo: string;
  startDateTime: string;
  endDateTime: string;
  onNodeClick?: (nodo: Nodo) => void;
  onEdgeClick?: (arista: Arista) => void;
}

export const CorrelationDiagram: React.FC<CorrelationDiagramProps> = ({
  missionId,
  numeroObjetivo,
  startDateTime,
  endDateTime,
  onNodeClick,
  onEdgeClick
}) => {
  const [diagramData, setDiagramData] = useState<DiagramData | null>(null);
  const [loading, setLoading] = useState(false);
  const [filtros, setFiltros] = useState<FiltrosDiagrama>({
    tipoTrafico: 'TODOS',
    operador: 'TODOS',
    soloHunterCells: true
  });

  // Cargar datos del diagrama
  const loadDiagramData = async () => {
    setLoading(true);
    try {
      const result = await window.eel.get_correlation_diagram(
        missionId,
        numeroObjetivo,
        startDateTime,
        endDateTime,
        filtros
      )();
      
      if (result.success) {
        setDiagramData(result);
      } else {
        console.error('Error cargando diagrama:', result.message);
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="correlation-diagram-container">
      {/* Controles de filtrado */}
      <DiagramControls filtros={filtros} onFiltrosChange={setFiltros} />
      
      {/* Diagrama de red */}
      {diagramData && (
        <NetworkDiagram
          nodos={diagramData.nodos}
          aristas={diagramData.aristas}
          onNodeClick={onNodeClick}
          onEdgeClick={onEdgeClick}
        />
      )}
      
      {/* Panel de estadísticas */}
      {diagramData && (
        <DiagramStatistics estadisticas={diagramData.estadisticas} />
      )}
    </div>
  );
};
```

### 6.2 Librería de Visualización: D3.js + Force Layout

```typescript
// Frontend/components/NetworkDiagram.tsx

import * as d3 from 'd3';

interface NetworkDiagramProps {
  nodos: Nodo[];
  aristas: Arista[];
  width?: number;
  height?: number;
  onNodeClick?: (nodo: Nodo) => void;
  onEdgeClick?: (arista: Arista) => void;
}

export const NetworkDiagram: React.FC<NetworkDiagramProps> = ({
  nodos,
  aristas,
  width = 800,
  height = 600,
  onNodeClick,
  onEdgeClick
}) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || !nodos.length) return;

    // Configurar D3 Force Simulation
    const simulation = d3.forceSimulation(nodos)
      .force('link', d3.forceLink(aristas).id(d => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2));

    // Renderizar nodos y aristas
    const svg = d3.select(svgRef.current);
    
    // Aristas (comunicaciones)
    const links = svg.selectAll('.edge')
      .data(aristas)
      .enter()
      .append('line')
      .attr('class', 'edge')
      .attr('stroke', d => getEdgeColor(d.tipo_comunicacion))
      .attr('stroke-width', d => getEdgeWidth(d.duracion_segundos))
      .on('click', (event, d) => onEdgeClick?.(d));

    // Nodos (números telefónicos)
    const nodes = svg.selectAll('.node')
      .data(nodos)
      .enter()
      .append('circle')
      .attr('class', 'node')
      .attr('r', d => getNodeRadius(d.nivel_actividad))
      .attr('fill', d => getNodeColor(d.tipo))
      .on('click', (event, d) => onNodeClick?.(d));

    // Etiquetas de nodos
    const labels = svg.selectAll('.label')
      .data(nodos)
      .enter()
      .append('text')
      .attr('class', 'label')
      .text(d => d.numero)
      .attr('text-anchor', 'middle');

    // Actualizar posiciones en cada tick
    simulation.on('tick', () => {
      links
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      nodes
        .attr('cx', d => d.x)
        .attr('cy', d => d.y);

      labels
        .attr('x', d => d.x)
        .attr('y', d => d.y + 5);
    });

  }, [nodos, aristas, width, height]);

  return <svg ref={svgRef} width={width} height={height} />;
};

// Funciones auxiliares para estilos
const getNodeColor = (tipo: string) => {
  switch (tipo) {
    case 'objetivo': return '#ff6b6b';
    case 'contacto': return '#4ecdc4';
    default: return '#95a5a6';
  }
};

const getNodeRadius = (actividad: string) => {
  switch (actividad) {
    case 'ALTO': return 15;
    case 'MEDIO': return 10;
    case 'BAJO': return 6;
    default: return 8;
  }
};

const getEdgeColor = (tipoComunicacion: string) => {
  switch (tipoComunicacion) {
    case 'VOZ': return '#3498db';
    case 'SMS': return '#2ecc71';
    case 'DATOS': return '#f39c12';
    default: return '#95a5a6';
  }
};

const getEdgeWidth = (duracionSegundos: number) => {
  if (duracionSegundos > 300) return 3;      // > 5 minutos
  if (duracionSegundos > 60) return 2;       // > 1 minuto
  return 1;                                  // <= 1 minuto
};
```

---

## 7. OPTIMIZACIONES DE RENDIMIENTO

### 7.1 Índices Adicionales Recomendados

```sql
-- NUEVOS ÍNDICES ESPECÍFICOS PARA DIAGRAMA DE CORRELACIÓN

-- Optimizar búsqueda por número objetivo específico
CREATE INDEX idx_diagram_numero_objetivo_mission 
ON operator_call_data(numero_objetivo, mission_id, fecha_hora_llamada);

-- Optimizar JOIN con celdas HUNTER para filtrado
CREATE INDEX idx_diagram_hunter_correlation 
ON operator_call_data(mission_id, celda_origen, celda_destino, numero_objetivo, numero_origen, numero_destino);

-- Covering index para queries de estadísticas
CREATE INDEX idx_diagram_stats_covering 
ON operator_call_data(numero_objetivo, mission_id, tipo_trafico, duracion_segundos, fecha_hora_llamada, operator);
```

### 7.2 Estrategias de Caching

```python
# Backend/services/diagram_correlation_service.py

class DiagramCorrelationService:
    def __init__(self):
        self.db_manager = get_database_manager()
        self._cache = {}  # Cache en memoria para sesión
        self._cache_timeout = 300  # 5 minutos
        
    def get_correlation_diagram_data(self, mission_id: str, numero_objetivo: str, 
                                   start_datetime: str, end_datetime: str,
                                   filtros: Dict[str, Any] = None) -> Dict[str, Any]:
        
        # Generar clave de cache
        cache_key = f"{mission_id}_{numero_objetivo}_{start_datetime}_{end_datetime}"
        
        # Verificar cache
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_timeout:
                logger.info(f"Datos del diagrama obtenidos desde cache")
                return cached_data
        
        # Generar datos
        result = self._generate_diagram_data(...)
        
        # Guardar en cache
        self._cache[cache_key] = (result, time.time())
        
        return result
```

### 7.3 Paginación y Límites

```python
# Configuración de límites para prevenir sobrecarga del frontend

DIAGRAM_LIMITS = {
    'max_nodes': 100,           # Máximo nodos en el diagrama
    'max_edges': 500,           # Máximo aristas en el diagrama
    'max_time_range_days': 365, # Máximo rango temporal (1 año)
    'pagination_size': 50       # Tamaño de página para comunicaciones
}

def apply_diagram_limits(comunicaciones: List[Dict]) -> Dict[str, Any]:
    """
    Aplica límites de rendimiento al diagrama
    """
    if len(comunicaciones) > DIAGRAM_LIMITS['max_edges']:
        logger.warning(f"Limitando comunicaciones de {len(comunicaciones)} a {DIAGRAM_LIMITS['max_edges']}")
        # Tomar las más recientes
        comunicaciones = sorted(comunicaciones, 
                              key=lambda x: x['timestamp'], 
                              reverse=True)[:DIAGRAM_LIMITS['max_edges']]
    
    return {
        'comunicaciones': comunicaciones,
        'truncated': len(comunicaciones) == DIAGRAM_LIMITS['max_edges'],
        'total_original': len(comunicaciones)
    }
```

---

## CONCLUSIONES Y PRÓXIMOS PASOS

### Puntos Clave del Análisis
1. **Base de Datos Lista:** Estructura existente soporta completamente el diagrama
2. **Consultas Optimizadas:** Índices actuales proporcionan rendimiento adecuado
3. **Correlación HUNTER Validada:** Lógica de filtrado por celdas reales implementada
4. **API Backend Definida:** Especificaciones claras para nuevos servicios

### Implementación Recomendada
1. **Fase 1:** Crear `DiagramCorrelationService` y endpoint Eel
2. **Fase 2:** Implementar componente React con D3.js
3. **Fase 3:** Añadir controles de filtrado y interactividad
4. **Fase 4:** Optimizar rendimiento y añadir overlay geográfico

### Consideraciones de Rendimiento
- **Límites razonables:** Máximo 100 nodos, 500 aristas por diagrama
- **Cache inteligente:** 5 minutos para consultas idénticas
- **Consultas optimizadas:** Aprovechan índices existentes para rendimiento sub-segundo

### Extensiones Futuras
- **Overlay geográfico:** Mapear celdas HUNTER en mapa real
- **Análisis temporal:** Diagrama animado mostrando evolución de comunicaciones
- **Exportación:** Generar reportes PDF/PNG del diagrama
- **Machine Learning:** Detectar patrones anómalos en comunicaciones

---

**Documento generado por Claude Code para Boris**  
**Fecha:** 18 de Agosto, 2025  
**Versión:** 1.0.0 - Especificaciones Técnicas Completas