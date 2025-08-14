# Guía de Desarrollo del Backend para KRONOS (con Eel)

## 1. Introducción

Este documento detalla las especificaciones para la creación del backend para la aplicación KRONOS utilizando el framework **Eel**. Este enfoque se desvía de una API REST tradicional (como FastAPI) y en su lugar crea una aplicación de escritorio híbrida donde la lógica de Python se expone directamente al frontend de JavaScript.

**El principio más importante es que el backend debe exponer funciones que coincidan con las llamadas definidas en `services/api.ts` del frontend.** Esto asegurará una integración perfecta.

**Stack Requerido:**
*   **Framework:** **Eel** para la comunicación bidireccional entre Python y JavaScript.
*   **Base de Datos:** **SQLite**. La aplicación debe usar un único archivo de base de datos (ej. `kronos.db`).
*   **ORM:** Se recomienda **SQLAlchemy** para la interacción con la base de datos.
*   **Procesamiento de Datos:** **Pandas** y **openpyxl** para leer archivos Excel (`.xlsx`) y CSV.

---

## 2. Configuración Inicial y Estructura del Proyecto

### Entorno Virtual
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate    # Windows
```

### Dependencias
```bash
pip install eel sqlalchemy pandas openpyxl passlib
# passlib: para el hasheo de contraseñas
```

### Estructura del Proyecto
Eel espera que los archivos del frontend residan en una carpeta específica.

```
/
├── main.py             # Script principal de la aplicación Eel
├── web/                # Carpeta que contiene TODOS los archivos del frontend
│   ├── index.html
│   ├── index.tsx
│   ├── App.tsx
│   ├── components/
│   ├── pages/
│   └── ... (todos los demás archivos y carpetas del frontend)
├── database.py         # Configuración de la base de datos y modelos SQLAlchemy
├── initial_data.py     # Lógica para poblar la base de datos la primera vez
└── kronos.db           # El archivo de la base de datos SQLite (se creará automáticamente)
```
**Acción Requerida:** Mover todos los archivos del frontend (React/TS) a una carpeta llamada `web`.

### Script Principal (`main.py`)
Este es el punto de entrada de la aplicación.
```python
import eel

# Inicializa Eel para que apunte a la carpeta del frontend
eel.init('web')

# ---- AQUÍ VAN TODAS LAS FUNCIONES EXPUESTAS CON @eel.expose ----

# Inicia la aplicación
# El tamaño de la ventana se puede ajustar según sea necesario
eel.start('index.html', size=(1440, 900))
```

---

## 3. Gestión de la Base de Datos y Primer Arranque

La lógica de inicialización es **idéntica** a la especificada anteriormente, pero se invoca directamente desde el script de Python antes de iniciar Eel.

**En `main.py`, antes de `eel.start()`:**
1.  Verificar si `kronos.db` existe.
2.  **Si NO existe**, crear la base de datos, las tablas y poblarla con los datos iniciales:
    *   **Rol de Super Administrador** con todos los permisos.
    *   **Usuario `admin@example.com`** con la contraseña `password` (hasheada con `passlib`).
    *   (Recomendado) Poblar con los demás datos de `services/mockData.ts` para facilitar las pruebas.

**Ejemplo conceptual de la lógica de arranque:**
```python
# En main.py
from database import init_db
from initial_data import populate_if_empty

# ... (antes de eel.start)
print("Inicializando la base de datos...")
init_db()  # Crea las tablas si no existen
populate_if_empty() # Función que verifica y puebla la DB
print("Base de datos lista.")

eel.start('index.html', size=(1440, 900))
```

---

## 4. Funciones Expuestas a JavaScript

Todas las funciones que necesiten ser llamadas desde el frontend deben estar decoradas con `@eel.expose`. Estas reemplazan a los endpoints de la API REST.

### 4.1. Autenticación

```python
import eel

@eel.expose
def login(credentials):
    # Lógica para buscar usuario y verificar contraseña hasheada
    # credentials será un diccionario: {"email": "...", "password": "..."}
    is_valid = verify_user_credentials(credentials['email'], credentials['password'])
    if is_valid:
        return {"status": "ok"}
    else:
        # Eel no maneja códigos de error HTTP, por lo que lanzamos una excepción
        # que se puede capturar como un error en la promesa de JavaScript.
        raise ValueError("Credenciales inválidas")
```

### 4.2. CRUD Genérico
Este patrón se repetirá para Usuarios, Roles y Misiones.

```python
# Ejemplo para Usuarios
@eel.expose
def get_users():
    # Lógica para consultar y devolver todos los usuarios de la DB
    return session.query(User).all()

@eel.expose
def create_user(user_data):
    # Lógica para crear, hashear contraseña, guardar y devolver el nuevo usuario
    # user_data es un diccionario
    new_user = User(**user_data) # Simplificado
    session.add(new_user)
    session.commit()
    return new_user

@eel.expose
def update_user(user_id, user_data):
    # Lógica para buscar por user_id, actualizar y devolver el usuario actualizado
    user = session.query(User).filter_by(id=user_id).first()
    # ... actualizar campos ...
    session.commit()
    return user

@eel.expose
def delete_user(user_id):
    # Lógica para eliminar el usuario por user_id
    user = session.query(User).filter_by(id=user_id).first()
    session.delete(user)
    session.commit()
    return {"status": "ok"}
```

### 4.3. Gestión de Datos de Misión (Manejo de Archivos)

La carga de archivos en Eel se realiza enviando el contenido del archivo como una cadena **base64** desde el frontend.

**Flujo:**
1.  **Frontend:** Lee el archivo usando `FileReader` como `readAsDataURL`. Envía el string base64 a la función de Python.
2.  **Backend:** Recibe el string, lo decodifica y lo procesa con Pandas.

```python
import base64
import io
import pandas as pd

@eel.expose
def upload_cellular_data(mission_id, file_data):
    # file_data será: {"name": "...", "content": "data:mime/type;base64,..."}
    try:
        content_type, content_string = file_data['content'].split(',')
        decoded = base64.b64decode(content_string)
        
        # Usar io.BytesIO para que pandas lo lea como un archivo en memoria
        file_like_object = io.BytesIO(decoded)
        
        # Leer con pandas (manejar CSV o Excel)
        if file_data['name'].endswith('.csv'):
            df = pd.read_csv(file_like_object)
        else:
            df = pd.read_excel(file_like_object)
        
        # ... Lógica para procesar el DataFrame y actualizar la misión ...
        updated_mission = process_and_save_cellular_data(mission_id, df)
        
        return updated_mission # Devolver el objeto de misión completo y actualizado
    except Exception as e:
        raise ValueError(f"Error al procesar el archivo: {e}")


@eel.expose
def upload_operator_data(mission_id, sheet_name, file_data):
    # Misma lógica que upload_cellular_data, pero usando el sheet_name
    # ...
    updated_mission = process_and_save_operator_data(mission_id, sheet_name, df)
    return updated_mission

@eel.expose
def clear_cellular_data(mission_id):
    # Lógica para borrar los datos celulares de la misión
    updated_mission = ...
    return updated_mission

@eel.expose
def delete_operator_sheet(mission_id, sheet_id):
    # Lógica para borrar una sábana de datos de operador específica
    updated_mission = ...
    return updated_mission
```

### 4.4. Análisis de Objetivos

```python
@eel.expose
def run_analysis(mission_id):
    # Lógica para cruzar los datos celulares y de operador de la misión
    # y devolver la lista de TargetRecord
    found_targets = perform_target_analysis(mission_id)
    return found_targets
```

---

## 5. Resumen de Funciones a Exponer

El backend debe implementar y exponer con `@eel.expose` las siguientes funciones, que se corresponden con las exportaciones de `services/api.ts`:

-   `login(credentials)`
-   `get_users()`
-   `create_user(user_data)`
-   `update_user(user_id, user_data)`
-   `delete_user(user_id)`
-   `get_roles()`
-   `create_role(role_data)`
-   `update_role(role_id, role_data)`
-   `delete_role(role_id)`
-   `get_missions()`
-   `create_mission(mission_data)`
-   `update_mission(mission_id, mission_data)`
-   `delete_mission(mission_id)`
-   `upload_cellular_data(mission_id, file_data)`
-   `upload_operator_data(mission_id, sheet_name, file_data)`
-   `clear_cellular_data(mission_id)`
-   `delete_operator_sheet(mission_id, sheet_id)`
-   `run_analysis(mission_id)`

Siguiendo esta guía, el equipo de backend podrá construir una aplicación robusta con Eel que se integre perfectamente con el frontend de KRONOS.
