# Changelog - KRONOS

Este documento registra todos los cambios y mejoras significativas realizadas en la aplicación KRONOS.

---

## Versión 1.1.0 (Mejoras de Interfaz y Arquitectura)

### ✨ Nuevas Características y Mejoras

*   **Menú Lateral Retráctil:**
    *   Se ha añadido un botón para colapsar y expandir el menú lateral, optimizando el espacio en pantalla.
    *   La información secundaria (nombre y versión) se oculta en el modo colapsado para una interfaz más limpia.

*   **Organización del Menú:**
    *   Los elementos "Usuarios" y "Roles" ahora están agrupados bajo un nuevo menú desplegable de "Configuración".
    *   Los submenús de "Configuración" tienen una sangría visual para mejorar la jerarquía y la legibilidad.

*   **Identidad Visual Mejorada:**
    *   Se reemplazó el texto "KRONOS" por un logo icónico.
    *   El logo evolucionó, probando diferentes diseños (letra 'K', cuadrado redondeado) hasta llegar a un icono de antena, más representativo de la funcionalidad de la aplicación.
    *   Se añadió el nombre "KRONOS" y el número de versión (`1.0.0`) debajo del logo en la vista expandida del menú.

*   **Tabla de "Posibles Objetivos" Funcional:**
    *   Se renombró la pestaña "Análisis de Objetivos" a "Posibles Objetivos" para mayor claridad.
    *   Se añadió la tabla de resultados en la pestaña, que ahora se muestra con datos de ejemplo al hacer clic en el botón de análisis.
    *   Se incorporó una barra de herramientas sobre la tabla de resultados, con acciones de ejemplo como "Exportar CSV", "Generar Reporte" y "Marcar para Revisión".

### 🔧 Arquitectura y Refactorización

*   **Centralización de la API:**
    *   Se creó un servicio de API centralizado en `services/api.ts`. Este archivo ahora gestiona todas las llamadas al backend, haciendo que el código sea más limpio y fácil de mantener. Las URLs de los endpoints están centralizadas para facilitar futuras configuraciones.

*   **Preparación para Backend:**
    *   Los componentes de carga de archivos (`FileUpload`) y las acciones de datos en `MissionDetail.tsx` fueron refactorizados para llamar a las funciones del nuevo servicio de API, preparando la aplicación para una integración completa con un backend real.

*   **Guía de Backend Detallada:**
    *   Se creó y actualizó el archivo `BACKEND_GUIDE.md` para servir como una especificación técnica completa para el equipo de backend.
    *   La guía fue adaptada para especificar una arquitectura basada en **Eel**, reemplazando la propuesta inicial de FastAPI, según los requisitos del proyecto.

---
