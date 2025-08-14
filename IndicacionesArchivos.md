# Especificación de Requerimientos - Carga de Datos de Operadores Celulares

## 1. CONTEXTO Y OBJETIVOS

### 1.1 Descripción General
La funcionalidad de "Datos de Operador" permite la carga y procesamiento de archivos de datos de tráfico celular proporcionados por diferentes operadores móviles para misiones de investigación.

### 1.2 Objetivos Específicos
- Implementar carga progresiva de datos por operador y tipo de documento
- Normalizar datos de múltiples operadores en esquema unificado por archivo
- Proporcionar visualización tabular de datos cargados
- Gestionar archivos de forma atómica (todo o nada)
- Prevenir duplicación de registros

## 2. REQUERIMIENTOS GENERALES

### 2.1 Arquitectura Técnica
- **Tipo de Aplicación**: Aplicación de escritorio
- **Backend**: Python
- **Base de Datos**: SQLite
- **Usuarios**: Investigadores
- **Procesamiento**: Tiempo real

### 2.2 Especificaciones de Archivos
- **Formatos Soportados**: XLSX, CSV
- **Tamaño Máximo**: 20 MB
- **Separadores CSV**: ";" o ","
- **Codificación**: UTF-8

### 2.3 Reglas de Negocio Generales
- Procesamiento atómico: el archivo se procesa completamente o se rechaza
- Validación de duplicados antes de inserción
- Agregación incremental de registros por tipo de documento
- Validaciones básicas de formato de columnas
- Notificación de errores y finalización de procesos

## 3. OPERADORES Y DOCUMENTOS

### 3.1 OPERADOR CLARO

#### 3.1.1 Documento: Información de Datos por Celda
**Propósito**: Actividad de datos en celdas celulares por número móvil

**Formatos**: XLSX, CSV
**Columnas Requeridas**:
- `numero` - Número de celular
- `fecha_trafico` - Fecha de actividad (YYYYMMDDHHMMSS)
- `tipo_cdr` - Tipo de actividad
- `celda_decimal` - Identificación de celda
- `lac_decimal` - Número LAC

**Validaciones**:
- Formato numérico para `numero`, `celda_decimal`, `lac_decimal`
- Formato fecha para `fecha_trafico` es => YYYYMMDDHHmmss
- Campo `tipo_cdr` no vacío

**Casos de Testing**:
- Archivo XLSX válido con datos correctos
- Archivo CSV con separador ";"
- Archivo CSV con separador ","
- Archivo con formato de fecha incorrecto
- Archivo con número de celular inválido
- Archivo con columnas faltantes
- Carga múltiple de archivos del mismo tipo
- Detección de registros duplicados


#### 3.1.2 Documento: Información de Llamadas Entrantes
**Propósito**: Actividad de llamadas entrantes por celda. El usuario puede cargar multiples archivos de llamadas.

**Formatos**: XLSX, CSV
**Columnas Requeridas**:
- `celda_inicio_llamada` - Celda de inicio
- `celda_final_llamada` - Celda de finalización
- `originador` - Número originador
- `receptor` - Número receptor
- `fecha_hora` - Fecha y hora de llamada
- `duracion` - Duración en segundos
- `tipo` - Tipo de CDR

**Validaciones**:
- Formato numérico para celdas, números telefónicos y duración
- Formato fecha-hora válido
- Campo `tipo` debe contener "CDR_ENTRANTE"

**Casos de Testing**:
- Archivo con datos de llamadas válidos
- Validación de formato de fecha-hora
- Detección de duplicados por combinación de campos clave
- Archivo XLSX válido con datos correctos
- Archivo CSV con separador ";"
- Archivo CSV con separador ","
- Archivo con formato de fecha incorrecto
- Archivo con número de celular inválido
- Archivo con columnas faltantes
- Carga múltiple de archivos del mismo tipo
- Despues de la carga exitosa de multiples archivos, poder eliminar algun archivo cargado 
- Detección de registros duplicados

#### 3.1.3 Documento: Información de Llamadas Salientes
**Propósito**: Actividad de llamadas salientes por celda. El usuario puede cargar multiples archivos de llamadas.

**Formatos**: XLSX, CSV
**Columnas Requeridas**:
- `celda_inicio_llamada` - Celda de inicio
- `celda_final_llamada` - Celda de finalización
- `originador` - Número originador
- `receptor` - Número receptor
- `fecha_hora` - Fecha y hora de llamada
- `duracion` - Duración en segundos
- `tipo` - Tipo de CDR

**Validaciones**:
- Formato numérico para celdas, números telefónicos y duración
- Formato fecha-hora válido
- Campo `tipo` debe contener "CDR_SALIENTE"

**Casos de Testing**:
- Archivo con datos de llamadas válidos
- Validación de formato de fecha-hora
- Detección de duplicados por combinación de campos clave
- Archivo XLSX válido con datos correctos
- Archivo CSV con separador ";"
- Archivo CSV con separador ","
- Archivo con formato de fecha incorrecto
- Archivo con número de celular inválido
- Archivo con columnas faltantes
- Carga múltiple de archivos del mismo tipo
- Despues de la carga exitosa de multiples archivos, poder eliminar algun archivo cargado 
- Detección de registros duplicados

### 3.2 OPERADOR MOVISTAR

#### 3.2.1 Documento: Información de Datos por Celda
**Propósito**: Actividad de datos en celdas celulares con información geográfica extendida

**Formatos**: XLSX, CSV
**Columnas Requeridas**:
- `numero_que_navega` - Número móvil
- `ruta_entrante` - Ruta de entrada
- `celda` - Identificación de celda
- `trafico_de_subida` - Bytes subidos
- `trafico_de_bajada` - Bytes descargados
- `fecha_hora_inicio_sesion` - Inicio de sesión
- `duracion` - Duración en segundos
- `tipo_tecnologia` - Tipo de tecnología
- `fecha_hora_fin_sesion` - Fin de sesión
- `departamento` - Departamento
- `localidad` - Localidad
- `region` - Región
- `latitud_n` - Latitud
- `longitud_w` - Longitud
- `proveedor` - Proveedor
- `tecnologia` - Tecnología
- `descripcion` - Descripción
- `direccion` - Dirección
- `celda_` - Identificador alternativo de celda

**Validaciones**:
- Formato numérico para tráfico, duración, coordenadas
- Formato fecha-hora para sesiones
- Campos geográficos no vacíos

**Casos de Testing**:
- Archivo XLSX válido con datos correctos
- Archivo CSV con separador ";"
- Archivo CSV con separador ","
- Archivo con formato de fecha incorrecto
- Archivo con número de celular inválido
- Archivo con columnas faltantes
- Detección de registros duplicados

#### 3.2.2 Documento: Información de Llamadas Salientes
**Propósito**: Actividad de llamadas salientes con información detallada de red

**Formatos**: XLSX, CSV
**Columnas Requeridas**: (25 campos incluyendo información de red, geolocalización y routing)

**Validaciones**:
- Validación de números telefónicos
- Formato de coordenadas geográficas
- Campos de duración y routing

**Casos de Testing**:
- Procesamiento de archivo con múltiples campos
- Archivo XLSX válido con datos correctos
- Archivo CSV con separador ";"
- Archivo CSV con separador ","
- Archivo con formato de fecha incorrecto
- Archivo con número de celular inválido
- Archivo con columnas faltantes
- Procesamiento de archivo XLSX multi-pestaña
- Carga múltiple de archivos del mismo tipo
- Despues de la carga exitosa de multiples archivos, poder eliminar algun archivo cargado 
- Detección de registros duplicados


### 3.3 OPERADOR TIGO

#### 3.3.1 Documento: Información de Llamadas
**Propósito**: Información unificada de llamadas (entrantes y salientes)

**Formatos**: XLSX (3 pestañas), CSV
**Columnas Requeridas**:
- `TIPO_DE_LLAMADA` - Tipo de llamada
- `NUMERO A` - Número destino
- `NUMERO MARCADO` - Número marcado
- `TRCSEXTRACODEC` - Información técnica
- `DIRECCION: O SALIENTE, I ENTRANTE` - Dirección de llamada
- `DURACION TOTAL seg` - Duración total
- `FECHA Y HORA ORIGEN` - Fecha y hora
- `CELDA_ORIGEN_TRUNCADA` - Celda origen
- `TECH` - Tecnología
- Campos geográficos y técnicos adicionales

**Validaciones**:
- Validación de dirección (O/I)
- Formato de coordenadas
- Duración numérica

**Casos de Testing**:
- Procesamiento de archivo XLSX multi-pestaña
- Archivo XLSX válido con datos correctos
- Archivo CSV con separador ";"
- Archivo CSV con separador ","
- Archivo con formato de fecha incorrecto
- Archivo con número de celular inválido
- Archivo con columnas faltantes
- Carga múltiple de archivos del mismo tipo
- Despues de la carga exitosa de multiples archivos, poder eliminar algun archivo cargado 
- Detección de registros duplicados
- Separación lógica entre entrantes y salientes

### 3.4 OPERADOR WOM

#### 3.4.1 Documento: Información de Datos por Celda
**Propósito**: Actividad de datos con información técnica detallada

**Formatos**: XLSX (2 pestañas), CSV
**Columnas Requeridas**: (24 campos incluyendo información técnica de red)

**Validaciones**:
- Validación de operador tecnología
- Formato de IMSI e IMEI
- Coordenadas geográficas

**Casos de Testing**:
- Procesamiento multi-pestaña
- Validación de identificadores técnicos
- Verificación de datos de sesión

#### 3.4.2 Documento: Información de Llamadas Entrantes
**Propósito**: Llamadas entrantes con información técnica de red

**Formatos**: XLSX (2 pestañas), CSV
**Columnas Requeridas**: (23 campos técnicos y geográficos)

**Validaciones**:
- Validación de sentido de llamada
- Información geográfica

**Casos de Testing**:
- Procesamiento de archivo XLSX multi-pestaña
- Archivo XLSX válido con datos correctos
- Archivo CSV con separador ";"
- Archivo CSV con separador ","
- Archivo con formato de fecha incorrecto
- Archivo con número de celular inválido
- Archivo con columnas faltantes
- Carga múltiple de archivos del mismo tipo
- Despues de la carga exitosa de multiples archivos, poder eliminar algun archivo cargado 
- Detección de registros duplicados
- Separación lógica entre entrantes y salientes

## 4. PLAN DE IMPLEMENTACIÓN POR FASES

### Fase 1: CLARO
1. **Subsfase 1.1**: Información de Datos por Celda
2. **Subsfase 1.2**: Información de Llamadas Entrantes
3. **Subsfase 1.3**: Información de Llamadas Salientes

### Fase 2: MOVISTAR
1. **Subsfase 2.1**: Información de Datos por Celda
2. **Subsfase 2.2**: Información de Llamadas Salientes

### Fase 3: TIGO
1. **Subsfase 3.1**: Información de Llamadas (Unificado)

### Fase 4: WOM
1. **Subsfase 4.1**: Información de Datos por Celda
2. **Subsfase 4.2**: Información de Llamadas Entrantes

## 5. MAPEO DE CAMPOS ESTÁNDAR

### 5.1 Tabla Estándar: Datos por Celda
- `operador` - Identificador del operador
- `numero_telefono` - Número de teléfono normalizado
- `celda_id` - Identificador de celda normalizado
- `fecha_hora_inicio` - Timestamp de inicio normalizado
- `fecha_hora_fin` - Timestamp de fin normalizado
- `duracion_segundos` - Duración en segundos
- `trafico_subida_bytes` - Bytes de subida
- `trafico_bajada_bytes` - Bytes de bajada
- `ubicacion_lat` - Latitud
- `ubicacion_lon` - Longitud
- `tecnologia` - Tipo de tecnología
- `fecha_carga` - Timestamp de carga del registro

### 5.2 Tabla Estándar: Llamadas
- `operador` - Identificador del operador
- `tipo_llamada` - ENTRANTE/SALIENTE
- `numero_origen` - Número originador
- `numero_destino` - Número destino
- `celda_origen` - Celda de origen
- `celda_destino` - Celda de destino
- `fecha_hora_inicio` - Timestamp de inicio
- `fecha_hora_fin` - Timestamp de fin
- `duracion_segundos` - Duración en segundos
- `ubicacion_lat` - Latitud
- `ubicacion_lon` - Longitud
- `tecnologia` - Tipo de tecnología
- `fecha_carga` - Timestamp de carga del registro

## 6. CASOS DE TESTING GENERALES

### 6.1 Testing de Frontend
- Carga de archivos por tipo y operador
- Validación de formatos de archivo
- Visualización de progreso de carga
- Mostrar errores de validación
- Listar archivos cargados por misión
- Visualizar datos en formato tabular
- Eliminar archivos de la misión

### 6.2 Testing de Backend
- Validación de estructura de archivos
- Normalización de datos por operador
- Detección de duplicados
- Inserción atómica de registros
- Manejo de errores de base de datos
- Logging de operaciones

### 6.3 Testing de Integración
- Flujo completo de carga por operador
- Consistencia de datos entre frontend y backend
- Performance con archivos de diferentes tamaños
- Manejo de sesiones concurrentes

## 7. CRITERIOS DE ACEPTACIÓN

### 7.1 Por Cada Fase de Operador
- Carga exitosa de todos los tipos de documento
- Validación correcta de formatos específicos
- Normalización precisa a esquema estándar
- Prevención de duplicados
- Visualización correcta de datos

### 7.2 Generales
- Procesamiento de archivos hasta 20MB
- Tiempo de respuesta menor a 30 segundos para archivos grandes
- Notificaciones claras de errores y éxitos
- Interfaz intuitiva para investigadores
- Logs detallados para debugging

