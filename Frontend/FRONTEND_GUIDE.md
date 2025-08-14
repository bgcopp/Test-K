# Guía de Desarrollo del Frontend para KRONOS

## 1. Introducción

Este documento sirve como una guía completa para entender, mantener y extender el frontend de la aplicación KRONOS. Describe la arquitectura, tecnologías y patrones de diseño utilizados. El objetivo es mantener un panel de administración profesional, mantenible y escalable.

## 2. Puesta en Marcha

El frontend de KRONOS está diseñado para funcionar como la interfaz de usuario de una aplicación de escritorio híbrida construida con **Eel**.

1.  **Entorno de Ejecución:** El frontend **no está diseñado para ejecutarse de forma independiente**. Debe ser servido por el servidor Python de Eel, que se encarga de proporcionar el archivo `index.html` y, de forma crucial, el script de comunicación `/eel.js`.
2.  **Lanzamiento:** Para iniciar la aplicación, se debe ejecutar el script principal de Python (ej. `main.py`) que inicializa Eel y abre la ventana de la aplicación.

## 3. Tecnologías y Principios Clave

-   **React:** Se utiliza como la biblioteca principal para construir la interfaz de usuario de forma declarativa y basada en componentes.
-   **TypeScript:** Se utiliza en todo el proyecto para un tipado estático robusto, lo que mejora la mantenibilidad del código, la detección temprana de errores y la experiencia del desarrollador.
-   **Eel (Integración con Backend):** La comunicación con el backend de Python no se realiza a través de una API REST. En su lugar, el frontend invoca directamente funciones de Python expuestas a través del objeto `window.eel`.
-   **Enrutamiento del Lado del Cliente:** La aplicación se implementa como una Single Page Application (SPA) utilizando `react-router-dom` (`HashRouter`), donde la navegación entre vistas no recarga la página completa.
-   **Tailwind CSS:** Se utiliza como framework CSS "utility-first" para un diseño rápido, responsivo y personalizable. La configuración del tema (colores, etc.) está definida directamente en `index.html`.

## 4. Arquitectura y Estructura del Proyecto

El proyecto sigue una estructura modular y organizada para facilitar la escalabilidad y el mantenimiento.

```
/
├── components/
│   ├── layout/       # Componentes de estructura visual (Sidebar, Header)
│   └── ui/           # Componentes de UI reusables (Button, Modal, Table, etc.)
├── pages/            # Componentes que representan las vistas principales
├── services/         # Lógica de comunicación con el backend (API)
│   ├── api.ts
│   └── mockData.ts
├── types.ts          # Definiciones de tipos y interfaces de TypeScript
├── constants.tsx     # Constantes (ej. SVGs de iconos, versión de la app)
├── App.tsx           # Componente raíz, orquestación y enrutamiento
├── index.html        # Archivo HTML principal
└── index.tsx         # Punto de entrada de React
```

### 4.1. Gestión de Estado

La gestión del estado se basa en los hooks de React y un patrón de "estado elevado" (lifted state).

-   **Estado Centralizado en `App.tsx`:** El componente `AppContent` actúa como la fuente de verdad para los datos globales de la aplicación (usuarios, roles, misiones). Al iniciar sesión, obtiene estos datos y los almacena en su estado.
-   **Flujo de Datos Unidireccional:** Los datos se pasan desde `App.tsx` hacia abajo a los componentes de página a través de props. Las funciones para modificar el estado (ej. `setUsers`) también se pasan como props, permitiendo que los componentes hijos soliciten cambios en el estado central.
-   **Estado Local:** Los componentes individuales manejan su propio estado efímero (ej. visibilidad de un modal, contenido de un campo de búsqueda) utilizando el hook `useState`.

### 4.2. Flujo de Datos con Eel

1.  **Inicialización:** Al autenticarse, `App.tsx` llama a las funciones del `services/api.ts` (ej. `getUsers`, `getRoles`) para obtener los datos iniciales.
2.  **Abstracción de API:** El módulo `services/api.ts` actúa como una capa de abstracción. Traduce las llamadas de la aplicación a invocaciones de `window.eel`, manejando la comunicación con Python. También se encarga de tareas como la conversión de archivos a `base64` antes de enviarlos al backend.
3.  **Acciones del Usuario:** Una interacción del usuario (ej. hacer clic en "Guardar Usuario") desencadena una llamada a una función en `services/api.ts`.
4.  **Llamada a Python:** El servicio invoca la función de Python correspondiente (ej. `eel.update_user(...)`).
5.  **Actualización de Estado:** Al recibir una respuesta exitosa del backend, la función del servicio devuelve los datos actualizados. El componente de página utiliza entonces la función `set...` (recibida por props) para actualizar el estado central en `App.tsx`.
6.  **Re-renderizado:** React detecta el cambio de estado y vuelve a renderizar eficientemente los componentes afectados para reflejar los nuevos datos.

## 5. Componentes y Funcionalidades Clave

### 5.1. Layout (`components/layout`)

-   **`Sidebar.tsx`**: Una barra de navegación lateral persistente y **retráctil**.
    -   **Logo y Branding:** Muestra un logo de antena, el nombre "KRONOS" y la versión de la app cuando está expandida.
    -   **Menú Agrupado:** Agrupa "Usuarios" y "Roles" bajo un menú desplegable de "Configuración".
    -   **Navegación Intuitiva:** Los submenús están indentados para una mejor jerarquía visual.
-   **`Header.tsx`**: Muestra dinámicamente el título de la página actual.

### 5.2. UI Reutilizable (`components/ui`)

-   `Button`, `Input`, `Modal`, `Table`, `Card`, `Checkbox`: Componentes genéricos que aseguran una apariencia consistente en toda la aplicación.
-   **`FileUpload.tsx`**: Un componente avanzado que encapsula la lógica para la carga de archivos.
    -   Soporta la selección de archivos y la funcionalidad de arrastrar y soltar (drag-and-drop).
    -   Muestra una vista previa del archivo seleccionado y su tamaño.
    -   Gestiona un estado de carga mientras se procesa el archivo.

### 5.3. Páginas (`pages`)

-   **`Login.tsx`**: Pantalla de inicio de sesión funcional que se comunica con el backend para verificar las credenciales. Muestra mensajes de error si la autenticación falla.
-   **`Dashboard.tsx`**: Página de bienvenida que muestra tarjetas con estadísticas clave.
-   **`Users.tsx`, `Roles.tsx`, `Missions.tsx`**: Páginas de gestión con funcionalidad **CRUD completa** (Crear, Leer, Actualizar, Eliminar). Utilizan modales para la creación/edición y se comunican directamente con el backend para persistir los cambios.
-   **`MissionDetail.tsx`**: La página más compleja, que ofrece una gestión detallada de una misión específica.
    -   **Interfaz por Pestañas:** Organiza la información en "Resumen", "Datos Celulares", "Datos de Operador" y "Posibles Objetivos".
    -   **Gestión de Datos:** Permite la carga de archivos de datos (celulares y de operador) y su eliminación.
    -   **Análisis de Objetivos:** La pestaña "Posibles Objetivos" aparece condicionalmente. Un botón inicia el análisis en el backend, mostrando un estado de carga. Los resultados se muestran en una tabla con una **barra de herramientas** que contiene acciones adicionales (exportar, etc.).

## 6. Tipos y Constantes

-   **`types.ts`**: Archivo central que define las interfaces de TypeScript (`User`, `Role`, `Mission`, `TargetRecord`, etc.). Actúa como un contrato de datos para toda la aplicación y el backend.
-   **`constants.tsx`**: Centraliza valores constantes, como las cadenas de texto de los iconos SVG y la versión de la aplicación (`APP_VERSION`), para facilitar su reutilización y mantenimiento.

## 7. Modo de Desarrollo y Configuración de API

Para facilitar el desarrollo y las demostraciones sin necesidad de un backend activo, la aplicación está equipada con un sistema de API dual que puede operar en modo **Mock** (simulado) o **Live** (en vivo).

### Cómo Cambiar Entre Modos

La selección del modo se controla mediante una única constante en el archivo `services/api.ts`.

**Archivo a modificar:** `services/api.ts`

**Constante:** `USE_MOCK_API`

```typescript
// services/api.ts

// --- CONFIGURATION ---
// Set to `true` to use the mock API for development without a backend.
// Set to `false` to connect to the live Eel backend.
const USE_MOCK_API = true; // <-- CAMBIA ESTE VALOR
```

### Descripción de los Modos

#### Modo Mock (`USE_MOCK_API = true`)

-   **Comportamiento:** La aplicación **no** intentará comunicarse con el backend de Eel. En su lugar, utilizará un conjunto de datos simulados definidos en `services/mockData.ts`.
-   **Características:**
    -   **Persistencia de Sesión:** Las operaciones CRUD (crear, actualizar, eliminar) modificarán el estado de los datos simulados, pero solo durante la sesión actual del navegador.
    -   **Reinicio en Logout:** Al cerrar sesión, todos los datos simulados se restablecen a su estado inicial, garantizando una demostración limpia y predecible cada vez.
    -   **Simulación de Latencia:** Todas las llamadas a la API simulada tienen un retraso artificial (`MOCK_API_DELAY`) para imitar las condiciones de una red real.
-   **Uso Ideal:** Desarrollo del frontend, pruebas de componentes de UI, demostraciones a stakeholders sin necesidad de ejecutar el backend.

#### Modo Live (`USE_MOCK_API = false`)

-   **Comportamiento:** La aplicación se comunicará directamente con el backend de Python a través de las funciones expuestas por Eel (`window.eel`).
-   **Requisitos:** El backend de Eel debe estar en ejecución para que la aplicación funcione correctamente.
-   **Uso Ideal:** Pruebas de integración, uso en producción y cuando se necesita persistencia de datos real en la base de datos.
