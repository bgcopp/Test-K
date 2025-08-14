# GUÍA PARA AGREGAR UN NUEVO OPERADOR AL SISTEMA KRONOS

**Versión**: 1.0.0  
**Fecha**: Agosto 2025  
**Sistema**: KRONOS - Análisis Forense de Telecomunicaciones  

---

## 📋 INTRODUCCIÓN

Esta guía detalla el proceso paso a paso para agregar un nuevo operador de telecomunicaciones al sistema KRONOS. El sistema está diseñado con una arquitectura modular que permite la incorporación de nuevos operadores sin afectar la funcionalidad existente.

### Operadores Actualmente Soportados:
- **CLARO** - Datos celulares y llamadas
- **MOVISTAR** - Datos celulares y llamadas salientes  
- **TIGO** - Llamadas unificadas (entrantes/salientes)
- **WOM** - Datos celulares y llamadas

---

## 🚀 PASO 1: PREPARACIÓN DE DATOS

### 1.1 Análisis del Formato de Archivo

**Actividades requeridas:**
- Obtener archivo de muestra del nuevo operador
- Documentar estructura completa de columnas
- Identificar tipos de datos (llamadas, datos celulares, SMS, MMS, etc.)
- Mapear campos únicos específicos del operador
- Identificar formato de fechas y timestamps
- Documentar encoding del archivo (UTF-8, Latin-1, etc.)

**Ejemplo para operador "ENTEL":**
```
Archivo: datos_entel_2025.xlsx
Formato: Excel con 2 hojas (Llamadas, Datos)
Encoding: UTF-8

Hoja "Llamadas":
- NUMERO_ORIGEN: Número que origina la llamada
- NUMERO_DESTINO: Número de destino  
- TIMESTAMP: Fecha y hora (YYYY-MM-DD HH:MM:SS)
- CELDA_ORIGEN: ID de celda origen
- CELDA_DESTINO: ID de celda destino
- DURACION: Duración en segundos
- TIPO_LLAMADA: VOZ, SMS, MMS
- COORDENADAS: "lat,lon" formato texto

Hoja "Datos":
- MSISDN: Número telefónico
- FECHA_CONEXION: Timestamp conexión
- BYTES_SUBIDA: Tráfico upload
- BYTES_BAJADA: Tráfico download
- CELDA_ID: Identificador de celda
```

### 1.2 Documentación de Campos Especiales

**Identificar y documentar:**
- Campos con formato no estándar
- Códigos específicos del operador
- Validaciones de integridad requeridas
- Transformaciones necesarias

---

## 🔧 PASO 2: CONFIGURACIÓN BACKEND

### 2.1 Actualizar `services/data_normalizer_service.py`

**Agregar método específico del operador:**

```python
def normalize_entel_llamadas(self, df: pd.DataFrame, file_upload_id: str, mission_id: str) -> List[Dict[str, Any]]:
    """
    Normaliza datos de llamadas de ENTEL al esquema estándar.
    
    Args:
        df: DataFrame con datos brutos de ENTEL
        file_upload_id: ID del archivo cargado
        mission_id: ID de la misión
        
    Returns:
        Lista de registros normalizados
    """
    normalized_records = []
    
    for _, row in df.iterrows():
        try:
            # Normalización específica de ENTEL
            normalized_record = {
                'file_upload_id': file_upload_id,
                'mission_id': mission_id,
                'operator': 'ENTEL',
                'tipo_llamada': self._normalize_entel_call_type(row.get('TIPO_LLAMADA')),
                'numero_origen': self._clean_phone_number(row.get('NUMERO_ORIGEN')),
                'numero_destino': self._clean_phone_number(row.get('NUMERO_DESTINO')),
                'numero_objetivo': self._determine_target_number(row),
                'fecha_hora_llamada': self._parse_entel_timestamp(row.get('TIMESTAMP')),
                'duracion_segundos': int(row.get('DURACION', 0)),
                'celda_origen': str(row.get('CELDA_ORIGEN', '')),
                'celda_destino': str(row.get('CELDA_DESTINO', '')),
                'tecnologia': 'UNKNOWN',  # ENTEL no proporciona este campo
                'tipo_trafico': 'VOZ',
                'estado_llamada': 'COMPLETADA',
                'operator_specific_data': self._create_entel_operator_specific_data(row),
                'record_hash': ''  # Se calculará después
            }
            
            # Parsear coordenadas si están disponibles
            if row.get('COORDENADAS'):
                coords = self._parse_entel_coordinates(row.get('COORDENADAS'))
                normalized_record.update(coords)
            
            # Calcular hash del registro
            normalized_record['record_hash'] = self._calculate_record_hash(normalized_record)
            
            normalized_records.append(normalized_record)
            
        except Exception as e:
            self.logger.error(f"Error normalizando registro ENTEL: {e}")
            continue
    
    return normalized_records

def _normalize_entel_call_type(self, call_type: str) -> str:
    """Mapea tipos de llamada ENTEL a tipos estándar."""
    entel_mapping = {
        'VOZ': 'SALIENTE',  # Asumiendo que VOZ es saliente por defecto
        'SMS': 'SALIENTE',
        'MMS': 'SALIENTE',
        'DATOS': 'MIXTA'
    }
    return entel_mapping.get(str(call_type).upper(), 'SALIENTE')

def _parse_entel_timestamp(self, timestamp_str: str) -> str:
    """Convierte timestamp ENTEL a formato estándar."""
    try:
        # ENTEL usa formato YYYY-MM-DD HH:MM:SS
        dt = datetime.strptime(str(timestamp_str), '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def _parse_entel_coordinates(self, coord_str: str) -> Dict[str, float]:
    """Parsea coordenadas formato 'lat,lon' de ENTEL."""
    try:
        if ',' in str(coord_str):
            lat, lon = str(coord_str).split(',')
            return {
                'latitud_origen': float(lat.strip()),
                'longitud_origen': float(lon.strip())
            }
    except:
        pass
    return {}

def _create_entel_operator_specific_data(self, row: pd.Series) -> str:
    """Crea JSON con datos específicos de ENTEL."""
    specific_data = {
        'operator': 'ENTEL',
        'entel_metadata': {
            'data_type': 'CALL_DATA',
            'file_format': 'XLSX',
            'processing_version': '1.0.0'
        },
        'original_fields': {
            'numero_origen': str(row.get('NUMERO_ORIGEN', '')),
            'numero_destino': str(row.get('NUMERO_DESTINO', '')),
            'timestamp': str(row.get('TIMESTAMP', '')),
            'celda_origen': str(row.get('CELDA_ORIGEN', '')),
            'celda_destino': str(row.get('CELDA_DESTINO', '')),
            'duracion': str(row.get('DURACION', '')),
            'tipo_llamada': str(row.get('TIPO_LLAMADA', '')),
            'coordenadas': str(row.get('COORDENADAS', ''))
        }
    }
    
    return json.dumps(specific_data, ensure_ascii=False)
```

**Actualizar método principal:**

```python
def normalize_operator_data(self, operator: str, df: pd.DataFrame, file_upload_id: str, mission_id: str) -> List[Dict[str, Any]]:
    """Método principal que enruta a normalizadores específicos."""
    
    # ... código existente ...
    
    elif operator.upper() == 'ENTEL':
        return self.normalize_entel_llamadas(df, file_upload_id, mission_id)
    
    else:
        raise ValueError(f"Operador no soportado: {operator}")
```

### 2.2 Actualizar `services/file_processor_service.py`

**Agregar método de procesamiento específico:**

```python
def process_entel_llamadas(self, file_bytes: bytes, file_name: str, 
                          file_upload_id: str, mission_id: str) -> Dict[str, Any]:
    """
    Procesa archivos de llamadas de ENTEL.
    
    ENTEL maneja archivos Excel con múltiples hojas:
    - Hoja "Llamadas": Datos de llamadas VOZ/SMS/MMS
    - Hoja "Datos": Sesiones de datos móviles
    
    Args:
        file_bytes: Contenido del archivo ENTEL
        file_name: Nombre del archivo original
        file_upload_id: ID único del archivo cargado
        mission_id: ID de la misión asociada
        
    Returns:
        Dict con resultado del procesamiento
    """
    start_time = datetime.now()
    
    self.logger.info(
        f"Iniciando procesamiento ENTEL: {file_name}",
        extra={'file_upload_id': file_upload_id, 'mission_id': mission_id}
    )
    
    try:
        # Leer archivo Excel con múltiples hojas
        excel_buffer = io.BytesIO(file_bytes)
        excel_file = pd.ExcelFile(excel_buffer)
        
        self.logger.info(f"Archivo ENTEL con {len(excel_file.sheet_names)} hojas: {excel_file.sheet_names}")
        
        total_records_processed = 0
        total_records_failed = 0
        all_failed_records = []
        
        # Procesar hoja de llamadas si existe
        if 'Llamadas' in excel_file.sheet_names:
            df_llamadas = pd.read_excel(excel_buffer, sheet_name='Llamadas')
            self.logger.info(f"Procesando hoja 'Llamadas': {len(df_llamadas)} registros")
            
            # Procesar en chunks
            for chunk_df in self._chunk_dataframe(df_llamadas, self.CHUNK_SIZE):
                chunk_result = self._process_entel_chunk(
                    chunk_df, 'LLAMADAS', file_upload_id, mission_id
                )
                
                total_records_processed += chunk_result.get('records_processed', 0)
                total_records_failed += chunk_result.get('records_failed', 0)
                
                if chunk_result.get('failed_records'):
                    all_failed_records.extend(chunk_result['failed_records'])
        
        # Procesar hoja de datos si existe  
        if 'Datos' in excel_file.sheet_names:
            df_datos = pd.read_excel(excel_buffer, sheet_name='Datos')
            self.logger.info(f"Procesando hoja 'Datos': {len(df_datos)} registros")
            
            # Procesar en chunks (implementar _process_entel_datos_chunk si es necesario)
            # for chunk_df in self._chunk_dataframe(df_datos, self.CHUNK_SIZE):
            #     chunk_result = self._process_entel_datos_chunk(...)
        
        # Resultado final
        processing_time = datetime.now() - start_time
        
        self.logger.info(
            f"Procesamiento ENTEL completado: {total_records_processed} exitosos, {total_records_failed} fallidos",
            extra={'processing_time_seconds': processing_time.total_seconds()}
        )
        
        # Actualizar registro en operator_data_sheets
        self._update_processing_status(file_upload_id, total_records_processed, total_records_failed)
        
        return {
            'success': True,
            'records_processed': total_records_processed,
            'records_failed': total_records_failed,
            'failed_records': all_failed_records[:10],
            'details': {
                'processing_time_seconds': processing_time.total_seconds(),
                'sheets_processed': len([s for s in ['Llamadas', 'Datos'] if s in excel_file.sheet_names])
            }
        }
        
    except Exception as e:
        self.logger.error(f"Error procesando archivo ENTEL: {e}")
        return {
            'success': False,
            'error': str(e),
            'records_processed': 0,
            'records_failed': 0
        }

def _process_entel_chunk(self, df_chunk: pd.DataFrame, data_type: str,
                        file_upload_id: str, mission_id: str) -> Dict[str, Any]:
    """Procesa un chunk de datos ENTEL."""
    try:
        # Normalizar datos usando el servicio correspondiente
        normalizer = get_data_normalizer_service()
        
        if data_type == 'LLAMADAS':
            normalized_records = normalizer.normalize_entel_llamadas(
                df_chunk, file_upload_id, mission_id
            )
        else:
            raise ValueError(f"Tipo de datos ENTEL no soportado: {data_type}")
        
        # Insertar en base de datos
        if normalized_records:
            db_service = get_database_service()
            inserted_count = db_service.insert_operator_call_data_batch(normalized_records)
            
            return {
                'success': True,
                'records_processed': inserted_count,
                'records_failed': len(normalized_records) - inserted_count,
                'failed_records': []
            }
        else:
            return {
                'success': True,
                'records_processed': 0,
                'records_failed': 0,
                'failed_records': []
            }
            
    except Exception as e:
        self.logger.error(f"Error procesando chunk ENTEL {data_type}: {e}")
        return {
            'success': False,
            'records_processed': 0,
            'records_failed': len(df_chunk),
            'failed_records': [{'error': str(e), 'chunk_size': len(df_chunk)}]
        }
```

**Actualizar dispatcher en `services/operator_data_service.py`:**

```python
def upload_operator_data(self, operator: str, file_name: str, file_content: str, mission_id: str) -> Dict[str, Any]:
    """Método principal que enruta el procesamiento por operador."""
    
    # ... código existente ...
    
    elif operator.upper() == 'ENTEL':
        processing_result = service.file_processor.process_entel_llamadas(
            file_bytes, file_name, file_upload_id, mission_id
        )
    
    # ... resto del código ...
```

### 2.3 Configurar Columnas Dinámicas

**Actualizar método `_get_column_configuration` en `operator_data_service.py`:**

```python
def _get_column_configuration(self, operator: str, file_type: str) -> Dict[str, Any]:
    """Configuración de columnas dinámicas por operador."""
    
    if file_type == 'CALL_DATA':
        if operator == 'ENTEL':
            return {
                'columns': [
                    'id', 'numero_origen', 'numero_destino', 'fecha_hora_llamada',
                    'duracion_segundos', 'celda_origen', 'celda_destino', 'tipo_llamada',
                    'latitud_origen', 'longitud_origen'
                ],
                'display_names': {
                    'numero_origen': 'Número Origen',
                    'numero_destino': 'Número Destino', 
                    'fecha_hora_llamada': 'Fecha/Hora',
                    'duracion_segundos': 'Duración (seg)',
                    'celda_origen': 'Celda Origen',
                    'celda_destino': 'Celda Destino',
                    'tipo_llamada': 'Tipo Llamada',
                    'latitud_origen': 'Latitud',
                    'longitud_origen': 'Longitud'
                }
            }
        
        # ... configuraciones existentes para otros operadores ...
```

### 2.4 Actualizar Validaciones

**Agregar validaciones específicas en `utils/validators.py`:**

```python
def validate_entel_phone_number(phone: str) -> bool:
    """
    Valida números telefónicos específicos de ENTEL (Chile).
    
    Formatos válidos:
    - +56XXXXXXXXX (internacional)
    - 56XXXXXXXXX (nacional con código país)
    - 9XXXXXXXX (móvil nacional)
    """
    if not phone or not isinstance(phone, str):
        return False
    
    # Limpiar número
    clean_phone = re.sub(r'[^\d]', '', phone)
    
    # Validar longitud
    if len(clean_phone) < 8 or len(clean_phone) > 15:
        return False
    
    # Validar prefijos chilenos
    chile_prefixes = ['56', '569']  # Código país Chile + móviles
    
    if len(clean_phone) >= 11 and clean_phone.startswith('56'):
        return True
    elif len(clean_phone) >= 9 and clean_phone.startswith('9'):
        return True
    
    return False

def validate_entel_call_type(call_type: str) -> bool:
    """Valida tipos de llamada válidos para ENTEL."""
    valid_types = ['VOZ', 'SMS', 'MMS', 'DATOS']
    return str(call_type).upper() in valid_types
```

---

## 🖥️ PASO 3: ACTUALIZACIÓN FRONTEND

### 3.1 Actualizar Constantes

**Modificar `Frontend/constants.tsx`:**

```typescript
// Agregar nuevo operador a la lista
export const OPERATORS = [
  'CLARO',
  'MOVISTAR', 
  'TIGO',
  'WOM',
  'ENTEL'  // ← Nuevo operador
] as const;

export type Operator = typeof OPERATORS[number];

// Agregar configuraciones específicas si es necesario
export const OPERATOR_CONFIG = {
  CLARO: {
    supportedFileTypes: ['.xlsx', '.csv'],
    dataTypes: ['CELLULAR_DATA', 'CALL_DATA']
  },
  MOVISTAR: {
    supportedFileTypes: ['.xlsx', '.csv'],  
    dataTypes: ['CELLULAR_DATA', 'CALL_DATA']
  },
  TIGO: {
    supportedFileTypes: ['.xlsx', '.csv'],
    dataTypes: ['CALL_DATA']
  },
  WOM: {
    supportedFileTypes: ['.xlsx', '.csv'],
    dataTypes: ['CELLULAR_DATA', 'CALL_DATA'] 
  },
  ENTEL: {
    supportedFileTypes: ['.xlsx'],
    dataTypes: ['CALL_DATA', 'DATA_SESSION']
  }
} as const;
```

### 3.2 Verificar Componentes

**Los siguientes componentes se actualizarán automáticamente:**

1. **Selector de Operador** (`components/ui/OperatorSelector.tsx`)
   - Automáticamente incluirá ENTEL en el dropdown

2. **Filtros** (`components/OperatorDataViewer.tsx`)
   - El filtro por operador incluirá ENTEL automáticamente

3. **Tabla de Datos** (`components/DataExplorationPanel.tsx`)
   - Mostrará las columnas configuradas para ENTEL automáticamente

**No se requieren cambios manuales en el frontend** gracias a la arquitectura dinámica.

---

## 🧪 PASO 4: TESTING Y VALIDACIÓN

### 4.1 Crear Tests Unitarios

**Crear archivo `Backend/tests/test_entel_processor.py`:**

```python
import unittest
import pandas as pd
from unittest.mock import Mock, patch
from datetime import datetime

from services.data_normalizer_service import get_data_normalizer_service
from services.file_processor_service import get_file_processor_service

class TestENTELProcessor(unittest.TestCase):
    """Tests para procesamiento de datos ENTEL."""
    
    def setUp(self):
        self.normalizer = get_data_normalizer_service()
        self.processor = get_file_processor_service()
        
    def test_entel_phone_validation(self):
        """Test validación números telefónicos ENTEL."""
        from utils.validators import validate_entel_phone_number
        
        # Números válidos
        valid_numbers = [
            '56912345678',
            '+56912345678', 
            '912345678'
        ]
        
        for number in valid_numbers:
            self.assertTrue(validate_entel_phone_number(number), 
                          f"Número válido rechazado: {number}")
        
        # Números inválidos
        invalid_numbers = [
            '123456',      # Muy corto
            '123456789012345678',  # Muy largo
            'abc123',      # Contiene letras
            ''             # Vacío
        ]
        
        for number in invalid_numbers:
            self.assertFalse(validate_entel_phone_number(number),
                           f"Número inválido aceptado: {number}")
    
    def test_entel_timestamp_parsing(self):
        """Test parsing de timestamps ENTEL."""
        test_timestamp = "2025-02-15 14:30:25"
        expected = "2025-02-15 14:30:25"
        
        result = self.normalizer._parse_entel_timestamp(test_timestamp)
        self.assertEqual(result, expected)
    
    def test_entel_coordinates_parsing(self):
        """Test parsing de coordenadas ENTEL."""
        test_coords = "-33.4489, -70.6693"  # Santiago, Chile
        expected = {
            'latitud_origen': -33.4489,
            'longitud_origen': -70.6693
        }
        
        result = self.normalizer._parse_entel_coordinates(test_coords)
        self.assertEqual(result, expected)
    
    def test_entel_call_type_normalization(self):
        """Test normalización tipos de llamada ENTEL."""
        test_cases = [
            ('VOZ', 'SALIENTE'),
            ('SMS', 'SALIENTE'),
            ('MMS', 'SALIENTE'), 
            ('DATOS', 'MIXTA'),
            ('UNKNOWN', 'SALIENTE')  # Default
        ]
        
        for input_type, expected in test_cases:
            result = self.normalizer._normalize_entel_call_type(input_type)
            self.assertEqual(result, expected)
    
    def test_entel_data_normalization(self):
        """Test normalización completa de datos ENTEL."""
        # Datos de prueba
        test_data = pd.DataFrame([
            {
                'NUMERO_ORIGEN': '56912345678',
                'NUMERO_DESTINO': '56987654321',
                'TIMESTAMP': '2025-02-15 14:30:25',
                'CELDA_ORIGEN': 'CELL001',
                'CELDA_DESTINO': 'CELL002',
                'DURACION': 120,
                'TIPO_LLAMADA': 'VOZ',
                'COORDENADAS': '-33.4489, -70.6693'
            }
        ])
        
        # Normalizar
        result = self.normalizer.normalize_entel_llamadas(
            test_data, 'test_file_id', 'test_mission_id'
        )
        
        # Verificaciones
        self.assertEqual(len(result), 1)
        record = result[0]
        
        self.assertEqual(record['operator'], 'ENTEL')
        self.assertEqual(record['numero_origen'], '56912345678')
        self.assertEqual(record['numero_destino'], '56987654321')
        self.assertEqual(record['duracion_segundos'], 120)
        self.assertEqual(record['tipo_llamada'], 'SALIENTE')
        self.assertAlmostEqual(record['latitud_origen'], -33.4489)
        self.assertAlmostEqual(record['longitud_origen'], -70.6693)

if __name__ == '__main__':
    unittest.main()
```

### 4.2 Tests de Integración

**Crear archivo `Backend/tests/test_entel_integration.py`:**

```python
import unittest
from unittest.mock import patch, mock_open
import pandas as pd
import io

class TestENTELIntegration(unittest.TestCase):
    """Tests de integración para flujo completo ENTEL."""
    
    def create_test_excel_file(self):
        """Crea archivo Excel de prueba para ENTEL."""
        # Datos de prueba
        llamadas_data = pd.DataFrame([
            {
                'NUMERO_ORIGEN': '56912345678',
                'NUMERO_DESTINO': '56987654321', 
                'TIMESTAMP': '2025-02-15 14:30:25',
                'CELDA_ORIGEN': 'CELL001',
                'CELDA_DESTINO': 'CELL002',
                'DURACION': 120,
                'TIPO_LLAMADA': 'VOZ',
                'COORDENADAS': '-33.4489, -70.6693'
            },
            {
                'NUMERO_ORIGEN': '56998765432',
                'NUMERO_DESTINO': '56912345678',
                'TIMESTAMP': '2025-02-15 15:45:10', 
                'CELDA_ORIGEN': 'CELL003',
                'CELDA_DESTINO': 'CELL001',
                'DURACION': 45,
                'TIPO_LLAMADA': 'SMS',
                'COORDENADAS': '-33.4020, -70.6064'
            }
        ])
        
        # Crear archivo Excel en memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            llamadas_data.to_excel(writer, sheet_name='Llamadas', index=False)
        
        return output.getvalue()
    
    @patch('services.operator_data_service.get_database_service')
    def test_full_entel_processing_flow(self, mock_db_service):
        """Test flujo completo de procesamiento ENTEL."""
        from services.operator_data_service import get_operator_data_service
        
        # Configurar mocks
        mock_db_service.return_value.insert_operator_call_data_batch.return_value = 2
        
        # Crear archivo de prueba
        test_file_content = self.create_test_excel_file()
        
        # Procesar
        service = get_operator_data_service()
        result = service.upload_operator_data(
            operator='ENTEL',
            file_name='test_entel.xlsx',
            file_content=test_file_content,
            mission_id='test_mission'
        )
        
        # Verificar resultado
        self.assertTrue(result['success'])
        self.assertEqual(result['records_processed'], 2)
        self.assertEqual(result['records_failed'], 0)
        
        # Verificar que se llamó a la base de datos
        mock_db_service.return_value.insert_operator_call_data_batch.assert_called()

if __name__ == '__main__':
    unittest.main()
```

### 4.3 Tests con Playwright

**Crear archivo `Backend/test_entel_playwright.py`:**

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test E2E para ENTEL usando Playwright
====================================
Valida el flujo completo desde carga de archivo hasta visualización.
"""

import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import io
import base64
from pathlib import Path

async def create_test_file():
    """Crear archivo de prueba ENTEL."""
    test_data = pd.DataFrame([
        {
            'NUMERO_ORIGEN': '56912345678',
            'NUMERO_DESTINO': '56987654321',
            'TIMESTAMP': '2025-02-15 14:30:25',
            'CELDA_ORIGEN': 'CELL001', 
            'CELDA_DESTINO': 'CELL002',
            'DURACION': 120,
            'TIPO_LLAMADA': 'VOZ',
            'COORDENADAS': '-33.4489, -70.6693'
        }
    ])
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        test_data.to_excel(writer, sheet_name='Llamadas', index=False)
    
    # Guardar archivo temporal
    test_file_path = Path(__file__).parent / 'test_data' / 'entel_test.xlsx'
    test_file_path.parent.mkdir(exist_ok=True)
    
    with open(test_file_path, 'wb') as f:
        f.write(output.getvalue())
    
    return test_file_path

async def test_entel_upload():
    """Test carga de archivo ENTEL via interfaz web."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Navegar a la aplicación
            await page.goto('http://localhost:8081')
            
            # Login
            await page.fill('input[type="email"]', 'admin@example.com')
            await page.fill('input[type="password"]', 'password')
            await page.click('button[type="submit"]')
            
            # Navegar a misiones
            await page.click('a[href="#/missions"]')
            await page.wait_for_load_state('networkidle')
            
            # Seleccionar una misión de prueba
            await page.click('text=Ver Detalles')
            await page.wait_for_load_state('networkidle')
            
            # Ir a pestaña Datos de Operador
            await page.click('text=Datos de Operador')
            await page.wait_for_timeout(1000)
            
            # Seleccionar operador ENTEL
            await page.click('button:has-text("ENTEL")')
            
            # Crear y cargar archivo de prueba
            test_file = await create_test_file()
            
            # Configurar file input
            file_input = page.locator('input[type="file"]')
            await file_input.set_input_files(str(test_file))
            
            # Hacer clic en Cargar Datos
            await page.click('button:has-text("Cargar Datos")')
            
            # Esperar procesamiento
            await page.wait_for_timeout(5000)
            
            # Verificar que aparece en la lista
            await page.wait_for_selector('text=entel_test.xlsx')
            
            # Verificar contadores actualizados
            registros_element = page.locator('text=Registros Procesados:')
            await registros_element.wait_for()
            
            # Hacer clic en el archivo para ver datos
            await page.click('text=entel_test.xlsx')
            await page.wait_for_timeout(2000)
            
            # Verificar que aparece la tabla con columnas ENTEL
            await page.wait_for_selector('th:has-text("Número Origen")')
            await page.wait_for_selector('th:has-text("Número Destino")')
            await page.wait_for_selector('th:has-text("Duración (seg)")')
            
            # Verificar datos en la tabla
            await page.wait_for_selector('td:has-text("56912345678")')
            await page.wait_for_selector('td:has-text("120s")')
            
            print("✅ Test ENTEL E2E completado exitosamente")
            
        except Exception as e:
            print(f"❌ Error en test ENTEL: {e}")
            await page.screenshot(path='entel_test_error.png')
            raise
        
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(test_entel_upload())
```

---

## 📚 PASO 5: DOCUMENTACIÓN

### 5.1 Actualizar BACKEND_GUIDE.md

**Agregar sección específica de ENTEL:**

```markdown
### Operador ENTEL (Chile)

#### Características:
- **País**: Chile
- **Formatos soportados**: Excel (.xlsx)
- **Hojas**: Llamadas, Datos  
- **Encoding**: UTF-8

#### Estructura de Datos:

**Hoja "Llamadas":**
- `NUMERO_ORIGEN`: Número que origina (formato: 56XXXXXXXXX)
- `NUMERO_DESTINO`: Número destino
- `TIMESTAMP`: Fecha/hora (YYYY-MM-DD HH:MM:SS)
- `CELDA_ORIGEN`: ID celda origen
- `CELDA_DESTINO`: ID celda destino  
- `DURACION`: Duración en segundos
- `TIPO_LLAMADA`: VOZ, SMS, MMS, DATOS
- `COORDENADAS`: "lat,lon" (formato texto)

#### Casos Especiales:
- Coordenadas en formato "lat,lon" separadas por coma
- Números con código país chileno (+56)
- Timestamps en formato ISO sin zona horaria

#### Configuración de Columnas:
```json
{
  "columns": ["id", "numero_origen", "numero_destino", "fecha_hora_llamada", 
             "duracion_segundos", "celda_origen", "celda_destino", "tipo_llamada",
             "latitud_origen", "longitud_origen"],
  "display_names": {
    "numero_origen": "Número Origen",
    "numero_destino": "Número Destino", 
    "fecha_hora_llamada": "Fecha/Hora",
    "duracion_segundos": "Duración (seg)",
    "celda_origen": "Celda Origen",
    "celda_destino": "Celda Destino",
    "tipo_llamada": "Tipo Llamada",
    "latitud_origen": "Latitud",
    "longitud_origen": "Longitud"
  }
}
```
```

### 5.2 Crear Documentación Específica

**Crear archivo `ENTEL_OPERATOR_GUIDE.md`:**

```markdown
# GUÍA ESPECÍFICA - OPERADOR ENTEL

## Información General

**Operador**: ENTEL Chile  
**Región**: Chile  
**Tipo de datos**: Llamadas VOZ, SMS, MMS, Datos móviles  
**Formatos soportados**: Excel (.xlsx)  

## Estructura de Archivos

### Archivo Típico: `datos_entel_YYYYMM.xlsx`

**Hojas incluidas:**
1. **Llamadas** - Registros de llamadas VOZ/SMS/MMS
2. **Datos** - Sesiones de datos móviles (opcional)

### Campos por Hoja

#### Hoja "Llamadas"
| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| NUMERO_ORIGEN | String | Número que origina | 56912345678 |
| NUMERO_DESTINO | String | Número destino | 56987654321 |
| TIMESTAMP | DateTime | Fecha y hora | 2025-02-15 14:30:25 |
| CELDA_ORIGEN | String | ID celda origen | CELL001 |
| CELDA_DESTINO | String | ID celda destino | CELL002 |
| DURACION | Integer | Duración en segundos | 120 |
| TIPO_LLAMADA | String | Tipo: VOZ/SMS/MMS/DATOS | VOZ |
| COORDENADAS | String | "lat,lon" | -33.4489, -70.6693 |

## Validaciones Específicas

### Números Telefónicos
- **Formato nacional**: 9XXXXXXXX (móviles)
- **Formato internacional**: +56XXXXXXXXX
- **Código país**: 56 (Chile)

### Tipos de Llamada
- `VOZ` → Mapeado a `SALIENTE`
- `SMS` → Mapeado a `SALIENTE` 
- `MMS` → Mapeado a `SALIENTE`
- `DATOS` → Mapeado a `MIXTA`

### Coordenadas
- **Formato**: "latitud, longitud" (separado por coma)
- **Rango válido**: Chile continental
- **Ejemplo**: "-33.4489, -70.6693"

## Casos Especiales

### Manejo de Errores Comunes
1. **Coordenadas inválidas**: Se omiten sin fallar el registro
2. **Timestamps malformados**: Se usa timestamp actual como fallback
3. **Números no chilenos**: Se validan pero se procesan si están en formato válido
4. **Duraciones negativas**: Se convierten a 0

### Optimizaciones
- Procesamiento en chunks de 1000 registros
- Validación previa de estructura de hojas
- Manejo de memoria optimizado para archivos grandes

## Testing

### Archivos de Prueba
- **Archivo pequeño**: 10-50 registros para validación rápida
- **Archivo medio**: 1000-5000 registros para performance
- **Archivo grande**: 10000+ registros para stress testing

### Scenarios de Test
1. **Formato estándar**: Archivo con todas las columnas correctas
2. **Coordenadas faltantes**: Registros sin coordenadas
3. **Timestamps diversos**: Diferentes formatos de fecha
4. **Números internacionales**: Números no chilenos válidos
5. **Hojas múltiples**: Excel con hojas Llamadas y Datos

## Troubleshooting

### Errores Comunes

**Error**: "Hoja 'Llamadas' no encontrada"
- **Causa**: Archivo Excel sin hoja correcta
- **Solución**: Verificar nombre exacto de la hoja

**Error**: "NUMERO_ORIGEN inválido"  
- **Causa**: Formato de número no reconocido
- **Solución**: Verificar que números incluyan código país 56

**Error**: "Timestamp parsing failed"
- **Causa**: Formato de fecha no estándar
- **Solución**: Convertir a formato YYYY-MM-DD HH:MM:SS

### Logs Útiles
```
INFO:entel_processor:Archivo ENTEL con 2 hojas: ['Llamadas', 'Datos']
INFO:entel_processor:Procesando hoja 'Llamadas': 1500 registros
INFO:entel_processor:Chunk 1/2 procesado: 1000 exitosos, 0 fallidos
INFO:entel_processor:Procesamiento ENTEL completado: 1500 exitosos, 0 fallidos
```

## Contacto y Soporte

Para problemas específicos con archivos ENTEL:
1. Verificar formato de archivo según esta guía
2. Validar estructura de hojas y columnas
3. Consultar logs de procesamiento
4. Crear issue con archivo de ejemplo si persiste el problema
```

---

## 🔄 PASO 6: PROCESO DE DESPLIEGUE

### 6.1 Lista de Verificación Pre-Despliegue

**Backend:**
- [ ] Métodos de normalización implementados y testeados
- [ ] Métodos de procesamiento implementados y testeados  
- [ ] Configuración de columnas dinámicas agregada
- [ ] Validaciones específicas implementadas
- [ ] Tests unitarios pasando
- [ ] Tests de integración pasando

**Frontend:**
- [ ] Constantes actualizadas con nuevo operador
- [ ] Verificación de funcionamiento automático de componentes
- [ ] Build de producción generado

**Testing:**
- [ ] Tests unitarios ejecutados exitosamente
- [ ] Tests de integración ejecutados exitosamente
- [ ] Test E2E con Playwright ejecutado exitosamente
- [ ] Archivo de prueba real procesado correctamente

**Documentación:**
- [ ] BACKEND_GUIDE.md actualizado
- [ ] Guía específica del operador creada
- [ ] Casos especiales documentados
- [ ] Troubleshooting documentado

### 6.2 Comandos de Despliegue

```bash
# 1. Frontend build
cd Frontend
npm run build

# 2. Tests backend
cd ../Backend
python -m pytest tests/test_entel_*.py -v

# 3. Test E2E
python test_entel_playwright.py

# 4. Reiniciar aplicación
python main.py
```

### 6.3 Validación Post-Despliegue

1. **Verificar UI**: Confirmar que ENTEL aparece en dropdowns
2. **Test carga**: Cargar archivo de prueba ENTEL
3. **Verificar tabla**: Confirmar columnas específicas ENTEL
4. **Verificar datos**: Confirmar datos reales en tabla
5. **Test exportación**: Verificar funcionalidad de exportación

---

## 📈 PASO 7: MONITOREO Y MANTENIMIENTO

### 7.1 Métricas a Monitorear

**Performance:**
- Tiempo de procesamiento por archivo ENTEL
- Tasa de éxito de procesamiento 
- Memoria utilizada durante procesamiento
- Registros procesados por segundo

**Calidad de Datos:**
- Registros fallidos por tipo de error
- Validaciones de números telefónicos fallidas
- Parsing de timestamps fallidos
- Coordenadas inválidas detectadas

### 7.2 Alertas Recomendadas

**Críticas:**
- Tasa de fallo > 5% en procesamiento ENTEL
- Tiempo de procesamiento > 5 minutos para archivos < 10MB
- Errores de validación > 10% de registros

**Informativas:**
- Nuevo tipo de archivo ENTEL detectado
- Coordenadas fuera de rango Chile detectadas
- Números no chilenos en archivos ENTEL

### 7.3 Evolución Futura

**Mejoras Planificadas:**
- Soporte para hoja "Datos" (sesiones de datos móviles)
- Validaciones geográficas avanzadas (regiones Chile)
- Detección automática de nuevos formatos ENTEL
- Integración con APIs ENTEL en tiempo real

---

## 🎯 RESUMEN EJECUTIVO

### Archivos Modificados

**Backend (4 archivos principales):**
1. `services/data_normalizer_service.py` - Lógica normalización ENTEL
2. `services/file_processor_service.py` - Procesamiento archivos ENTEL
3. `services/operator_data_service.py` - Configuración columnas dinámicas
4. `utils/validators.py` - Validaciones números chilenos

**Frontend (1 archivo):**
1. `constants.tsx` - Agregar ENTEL a lista operadores

**Tests (3 archivos nuevos):**
1. `tests/test_entel_processor.py` - Tests unitarios
2. `tests/test_entel_integration.py` - Tests integración
3. `test_entel_playwright.py` - Tests E2E

**Documentación (2 archivos nuevos):**
1. `ENTEL_OPERATOR_GUIDE.md` - Guía específica ENTEL
2. `BACKEND_GUIDE.md` - Actualizado con sección ENTEL

### Tiempo Estimado de Implementación

- **Análisis y preparación**: 2-4 horas
- **Desarrollo backend**: 4-6 horas  
- **Testing**: 2-3 horas
- **Documentación**: 1-2 horas
- **Validación**: 1-2 horas

**Total: 10-17 horas** (1-2 días de desarrollo)

### Beneficios de la Arquitectura Modular

1. **Escalabilidad**: Agregar operadores sin afectar existentes
2. **Mantenibilidad**: Código específico encapsulado por operador
3. **Flexibilidad**: Configuraciones dinámicas por tipo de dato
4. **Robustez**: Validaciones y manejo de errores específicos
5. **Usabilidad**: Frontend se adapta automáticamente

---

**Documento creado**: Agosto 2025  
**Versión**: 1.0.0  
**Sistema**: KRONOS - Análisis Forense de Telecomunicaciones  
**Mantenedor**: Equipo de Desarrollo KRONOS  