# KRONOS Backend

Backend completo para la aplicación desktop KRONOS implementado con Python, Eel, SQLAlchemy y SQLite.

## Características Principales

- **Aplicación Desktop Híbrida**: Implementada con Eel para comunicación Python-JavaScript
- **Base de Datos SQLite**: Con SQLAlchemy ORM para persistencia de datos
- **Procesamiento de Archivos**: Soporte para Excel (.xlsx) y CSV con Pandas
- **Sistema de Autenticación**: Manejo seguro de usuarios y contraseñas con bcrypt
- **Análisis de Datos**: Cruce de datos celulares y de operador para análisis de objetivos
- **Arquitectura Modular**: Servicios organizados por funcionalidad
- **Validaciones Exhaustivas**: Validación completa de datos de entrada
- **Logging Detallado**: Registro completo de operaciones y errores

## Estructura del Proyecto

```
Backend/
├── main.py                 # Script principal de la aplicación Eel
├── requirements.txt        # Dependencias de Python
├── kronos.db              # Base de datos SQLite (se crea automáticamente)
├── kronos_backend.log     # Archivo de logs (se crea automáticamente)
├── database/
│   ├── __init__.py
│   ├── connection.py      # Gestor de conexión a BD
│   └── models.py          # Modelos SQLAlchemy
├── services/
│   ├── __init__.py
│   ├── auth_service.py    # Servicio de autenticación
│   ├── user_service.py    # Gestión de usuarios
│   ├── role_service.py    # Gestión de roles
│   ├── mission_service.py # Gestión de misiones
│   ├── file_processor.py  # Procesamiento de archivos
│   └── analysis_service.py# Análisis de objetivos
└── utils/
    ├── __init__.py
    ├── validators.py      # Validaciones de datos
    └── helpers.py         # Funciones auxiliares
```

## Instalación

### 1. Prerrequisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### 2. Instalar Dependencias

```bash
cd Backend
pip install -r requirements.txt
```

### 3. Verificar Instalación

```bash
python -c "import eel, pandas, sqlalchemy; print('Dependencias instaladas correctamente')"
```

## Uso

### Iniciar la Aplicación

```bash
cd Backend
python main.py
```

La aplicación:
1. Inicializará la base de datos automáticamente si no existe
2. Cargará datos iniciales (usuarios, roles, misiones de ejemplo)
3. Abrirá una ventana del navegador con la interfaz
4. Estará disponible en `http://localhost:8080`

### Datos de Acceso Inicial

- **Email**: `admin@example.com`
- **Contraseña**: `password`

### Estructura de la Base de Datos

Al iniciarse por primera vez, se crean:

- **3 Roles**: Super Administrador, Editor de Misiones, Visualizador
- **6 Usuarios**: Incluye admin y usuarios de ejemplo
- **4 Misiones**: Misiones de ejemplo con diferentes estados

## API Expuesta

### Funciones disponibles para el frontend:

#### Autenticación
- `login(credentials)` - Autenticar usuario

#### Gestión de Usuarios
- `get_users()` - Obtener todos los usuarios
- `create_user(userData)` - Crear nuevo usuario
- `update_user(userId, userData)` - Actualizar usuario
- `delete_user(userId)` - Eliminar usuario

#### Gestión de Roles
- `get_roles()` - Obtener todos los roles
- `create_role(roleData)` - Crear nuevo rol
- `update_role(roleId, roleData)` - Actualizar rol
- `delete_role(roleId)` - Eliminar rol

#### Gestión de Misiones
- `get_missions()` - Obtener todas las misiones
- `create_mission(missionData)` - Crear nueva misión
- `update_mission(missionId, missionData)` - Actualizar misión
- `delete_mission(missionId)` - Eliminar misión

#### Gestión de Datos
- `upload_cellular_data(missionId, fileData)` - Cargar datos celulares
- `upload_operator_data(missionId, sheetName, fileData)` - Cargar datos de operador
- `clear_cellular_data(missionId)` - Limpiar datos celulares
- `delete_operator_sheet(missionId, sheetId)` - Eliminar hoja de operador

#### Análisis
- `run_analysis(missionId)` - Ejecutar análisis de objetivos

## Configuración

### Variables de Configuración

Pueden modificarse en `database/connection.py`:
- `DEFAULT_DB_PATH` - Ruta de la base de datos
- Configuración de SQLite (pragma settings)
- Configuración de logging

### Personalización de Datos Iniciales

Los datos iniciales se pueden modificar en `database/connection.py` en los métodos:
- `_create_initial_roles()`
- `_create_initial_users()`
- `_create_initial_missions()`

## Logging

El sistema genera logs detallados en:
- **Archivo**: `kronos_backend.log`
- **Consola**: Output en tiempo real

Niveles de log configurados:
- INFO: Operaciones normales
- WARNING: Advertencias de validación
- ERROR: Errores de operación

## Desarrollo

### Estructura de Servicios

Cada servicio sigue el patrón:
1. **Validación** de datos de entrada
2. **Operación** en base de datos
3. **Mapeo** a formato frontend
4. **Logging** de la operación
5. **Manejo** robusto de errores

### Agregar Nuevas Funcionalidades

1. **Modelo**: Agregar en `database/models.py`
2. **Servicio**: Crear en `services/`
3. **Validaciones**: Agregar en `utils/validators.py`
4. **Función Eel**: Exponer en `main.py`
5. **Logging**: Configurar logging apropiado

### Testing

Para desarrollo, se puede usar el modo mock del frontend:
- En `Frontend/services/api.ts`, cambiar `USE_MOCK_API = true`

## Solución de Problemas

### Error: "Base de datos bloqueada"
```bash
# Verificar que no haya otras instancias ejecutándose
# Eliminar archivo de bloqueo si existe
rm kronos.db-wal kronos.db-shm
```

### Error: "Puerto 8080 en uso"
- Modificar el puerto en `main.py`:
```python
eel.start('index.html', port=8081)
```

### Error: "Frontend no encontrado"
- Verificar que la carpeta `Frontend/` existe
- Verificar que `Frontend/index.html` existe
- Ajustar la ruta en `main.py` si es necesario

### Problemas de Dependencias
```bash
# Reinstalar dependencias
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

## Licencia

Este proyecto está desarrollado para uso interno. Todos los derechos reservados.

## Contacto

Para soporte técnico o reportar errores, contactar al equipo de desarrollo de KRONOS.