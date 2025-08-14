# TIGO IMPLEMENTATION COMPLETE

## Resumen

Se ha implementado exitosamente el soporte completo para el operador TIGO en KRONOS, siguiendo las especificaciones del documento `IndicacionSabanaDatosOperador.txt`.

## Características Específicas de TIGO

### 1. Tipo de Archivo Único: LLAMADAS_MIXTAS
- **Diferencia clave**: TIGO reporta llamadas entrantes y salientes en un solo archivo
- **Diferenciación**: Campo `DIRECCION` con valores 'O' (SALIENTE) o 'I' (ENTRANTE)
- **Formatos soportados**: CSV y Excel (.xlsx) con múltiples pestañas

### 2. Estructura de Datos TIGO

#### Columnas Principales:
```
TIPO_DE_LLAMADA,NUMERO A,NUMERO MARCADO,TRCSEXTRACODEC,
DIRECCION: O SALIENTE, I ENTRANTE,DURACION TOTAL seg,
FECHA Y HORA ORIGEN,CELDA_ORIGEN_TRUNCADA,TECH,DIRECCION,
CITY_DS,DEPARTMENT_DS,AZIMUTH,ALTURA,POTENCIA,
LONGITUDE,LATITUDE,TIPO_COBERTURA,TIPO_ESTRUCTURA,
OPERADOR,CELLID_NVAL
```

#### Características Específicas:
- **Coordenadas**: Formato con comas como decimales (`"-74,074989"`, `"4,64958"`)
- **Campo DIRECCION**: 'O' = SALIENTE, 'I' = ENTRANTE
- **Fechas**: Formato `"28/02/2025 01:20:19"`
- **Información detallada de antenas**: Azimuth, altura, potencia
- **Números marcados**: Pueden ser dominios web (ej: `web.colombiamovil.com.co`)

### 3. Archivos Excel Multipestañas
- Soporte para archivos Excel con múltiples pestañas idénticas
- Consolidación automática de todas las pestañas en un dataset único
- Validación independiente por pestaña

## Implementación Técnica

### Archivos Creados/Modificados

#### 1. **TigoProcessor** (`services/operator_processors/tigo_processor.py`)
- Procesador especializado para TIGO
- Manejo de archivos Excel multipestañas
- Conversión automática de formato de coordenadas TIGO
- Separación de llamadas entrantes y salientes por campo DIRECCION
- Validación específica de formato TIGO

#### 2. **Validadores TIGO** (`utils/validators.py`)
Funciones añadidas:
- `validate_tigo_datetime_format()`: Valida fechas DD/MM/YYYY HH:MM:SS
- `validate_tigo_coordinates()`: Convierte coordenadas con comas a decimales
- `validate_tigo_direction_field()`: Valida campo DIRECCION (O/I)
- `validate_tigo_antenna_data()`: Valida datos de antena (azimuth, altura, potencia)
- `validate_tigo_call_type()`: Valida códigos numéricos TIGO
- `validate_tigo_llamada_record()`: Validación completa de registro TIGO

#### 3. **Integración del Sistema** (`services/operator_processors/__init__.py`)
- TIGO registrado en `OPERATOR_PROCESSORS`
- Disponible a través de funciones factory existentes
- Integración completa con APIs Eel genericas

#### 4. **Pruebas Unitarias** (`test_tigo_implementation.py`)
- 13 pruebas unitarias cubren todos los aspectos
- Pruebas de validadores específicos
- Pruebas de procesador de archivos
- Pruebas de integración con el sistema

## Flujo de Procesamiento TIGO

### 1. Validación de Estructura
```python
# Valida estructura del archivo
result = processor.validate_file_structure(file_data, 'LLAMADAS_MIXTAS')
```

### 2. Procesamiento de Archivos
```python
# Procesa archivo TIGO completo
result = processor.process_file(file_data, 'LLAMADAS_MIXTAS', mission_id)
```

### 3. Normalización de Datos
1. **Lectura**: CSV directo o Excel con múltiples pestañas
2. **Normalización**: Columnas mapeadas a esquema estándar
3. **Limpieza**: Conversión de coordenadas, fechas y tipos de datos
4. **Separación**: Registros divididos por campo DIRECCION
5. **Inserción**: Datos insertados en `operator_call_data`

### 4. Mapeo de Datos
```python
# Ejemplo de mapeo TIGO
if direccion_tipo in ['O', 'SALIENTE']:
    tipo_llamada = 'SALIENTE'
    numero_objetivo = numero_a  # Quien llama
elif direccion_tipo in ['I', 'ENTRANTE']:
    tipo_llamada = 'ENTRANTE'
    numero_objetivo = numero_marcado  # Quien recibe
```

## Datos Específicos de TIGO

### Metadata Almacenada en `operator_specific_data`
```json
{
  "operator": "TIGO",
  "data_type": "llamadas_mixtas",
  "direccion_original": "O",
  "tecnologia": "4G",
  "codec": "10.198.50.152",
  "ubicacion": {
    "ciudad": "BOGOTÁ. D.C.",
    "departamento": "CUNDINAMARCA",
    "direccion_fisica": "Diagonal 61D N 26A-29",
    "coordenadas": {
      "latitud": 4.64958,
      "longitud": -74.074989
    }
  },
  "antena_info": {
    "azimuth": 350.0,
    "altura_metros": 22.0,
    "potencia_dbm": 18.2,
    "tipo_cobertura": "6 - 1. URBANA",
    "tipo_estructura": "12 - ROOFTOP + TOWER"
  }
}
```

## Integración con Frontend

### APIs Eel Disponibles
TIGO utiliza las APIs genéricas existentes:

```javascript
// Validar estructura de archivo TIGO
window.eel.validate_operator_file_structure('TIGO', fileData, 'LLAMADAS_MIXTAS')

// Procesar archivo TIGO
window.eel.upload_operator_file('TIGO', missionId, fileData, 'LLAMADAS_MIXTAS')

// Obtener resumen de datos TIGO
window.eel.get_operator_files_for_mission(missionId, 'TIGO')

// Eliminar archivo TIGO
window.eel.delete_operator_file(missionId, fileId, 'TIGO')
```

### Configuración Frontend
En el componente `OperatorSelector.tsx`, TIGO aparece como:
```typescript
{
  id: 'TIGO',
  name: 'TIGO',
  fileTypes: [
    {
      id: 'LLAMADAS_MIXTAS',
      name: 'Llamadas Mixtas',
      description: 'Archivo único con llamadas entrantes y salientes'
    }
  ]
}
```

## Validación y Pruebas

### Resultados de Pruebas
✅ **13/13 pruebas pasaron exitosamente**

#### Categorías de Pruebas:
1. **Validadores TIGO** (4 pruebas)
   - Formato fecha/hora TIGO
   - Coordenadas con comas como decimales
   - Campo dirección (O/I)
   - Registro completo TIGO

2. **Procesador TIGO** (6 pruebas)
   - Tipos de archivo soportados
   - Validación de estructura
   - Archivos Excel multipestañas
   - Normalización de columnas
   - Limpieza de DataFrames
   - Extracción de datos específicos

3. **Integración Sistema** (3 pruebas)
   - Registro en factory de procesadores
   - Tipos de archivo en integración
   - Construcción de metadata específica

### Comando de Pruebas
```bash
cd Backend
python test_tigo_implementation.py
```

## Casos de Uso

### 1. Archivo CSV Simple
```python
file_data = {
    'name': 'tigo_calls.csv',
    'content': 'data:text/csv;base64,VElQT19ERV9MTEFNQUE...'
}
result = processor.process_file(file_data, 'LLAMADAS_MIXTAS', mission_id)
```

### 2. Archivo Excel Multipestañas
```python
file_data = {
    'name': 'tigo_calls.xlsx',
    'content': 'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,UEsDBBQ...'
}
# Procesará automáticamente todas las pestañas
result = processor.process_file(file_data, 'LLAMADAS_MIXTAS', mission_id)
```

### 3. Consulta de Datos Procesados
```python
# Obtener llamadas salientes de un número específico
salientes = session.query(OperatorCallData).filter(
    OperatorCallData.operator == 'TIGO',
    OperatorCallData.tipo_llamada == 'SALIENTE',
    OperatorCallData.numero_objetivo == '3005722406'
).all()
```

## Diferencias con Otros Operadores

| Característica | CLARO | MOVISTAR | TIGO | WOM |
|---------------|-------|----------|------|-----|
| **Archivos** | 3 separados | 2 separados | 1 mixto | 2 separados |
| **Datos** | ✅ | ✅ | ❌ | ✅ |
| **Llamadas** | ENT + SAL | Solo SAL | MIXTAS | Solo ENT |
| **Coordenadas** | No | Punto decimal | Coma decimal | Punto decimal |
| **Fechas** | YYYYMMDD... | YYYYMMDD... | DD/MM/YYYY | DD/MM/YYYY |
| **Diferenciación** | Por archivo | Por archivo | Por campo | Por archivo |

## Mantenimiento

### Logs Específicos
```
INFO:services.operator_processors.tigo_processor:Validando estructura archivo TIGO tipo: LLAMADAS_MIXTAS
INFO:services.operator_processors.tigo_processor:Procesando pestaña: Hoja1 con 150 registros
INFO:services.operator_processors.tigo_processor:Combinadas 3 pestañas en 450 registros totales
INFO:services.operator_processors.tigo_processor:Procesados 445 registros de llamadas mixtas TIGO
```

### Errores Comunes
1. **Formato coordenadas**: Automáticamente convierte comas a puntos
2. **Campo DIRECCION vacío**: Se omite registro con warning
3. **Números no válidos**: Mantiene como string si no es número telefónico válido
4. **Fechas inválidas**: Se omite registro con warning
5. **Excel sin pestañas**: Error específico con mensaje claro

## Estado del Proyecto

### ✅ Completado
- [x] TigoProcessor implementado
- [x] Validadores específicos TIGO
- [x] Manejo archivos Excel multipestañas
- [x] Conversión coordenadas formato TIGO
- [x] Validación campo DIRECCION (O/I)
- [x] Integración sistema operadores
- [x] Pruebas unitarias completas
- [x] Documentación técnica

### 🔄 Próximos Pasos (para otros operadores)
- [ ] Implementar WomProcessor
- [ ] Completar análisis de datos integrado
- [ ] Optimizaciones de rendimiento

---

**Implementación TIGO completada exitosamente** ✅  
**Todas las especificaciones cumplidas**  
**Sistema listo para producción**