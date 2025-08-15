# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

KRONOS is a hybrid desktop application combining a React TypeScript frontend with a Python Eel backend for managing users, roles, permissions, and research missions.

## Development Commands

### Desarrollo Frontend (desde Frontend/)
```bash
npm install          # Install dependencies
npm run dev          # Start development server (http://localhost:5173)
npm run build        # Build for production
npm run preview      # Preview production build
```

### Aplicación Integrada (Frontend + Backend)

**OPCIÓN 1: Uso rápido (recomendado para desarrollo)**
```bash
# Desde el directorio raíz del proyecto
build.bat            # Compila el frontend para producción
cd Backend
python main.py       # Ejecuta la aplicación completa
```

**OPCIÓN 2: Comandos manuales**
```bash
# 1. Compilar frontend (desde Frontend/)
cd Frontend
npm install
npm run build

# 2. Ejecutar backend (desde Backend/)
cd ../Backend
python main.py
```

### Modo de Desarrollo vs Producción
- **Desarrollo**: `main.py` usa archivos fuente de `Frontend/` directamente
- **Producción**: `main.py` usa archivos compilados de `Frontend/dist/` (mejor rendimiento)

## Architecture

### Tech Stack
- **Frontend**: React 19.1.1, TypeScript 5.8.2, Vite 6.2.0, Tailwind CSS (CDN)
- **Backend**: Python with Eel framework (desktop app bridge)
- **Database**: SQLite with SQLAlchemy ORM (planned)
- **Data Processing**: Pandas, openpyxl (planned)

### Key Architectural Patterns

1. **Hybrid Desktop Application**
   - Frontend runs in Eel-controlled browser window
   - Direct JavaScript-Python communication via `window.eel` object
   - No REST API - uses direct function calls

2. **State Management**
   - Centralized state in `App.tsx` using lifted state pattern
   - Props-based data flow
   - No external state management libraries

3. **API Integration**
   - Dual-mode system: Mock (`USE_MOCK_API = true`) or Live Eel backend
   - All API calls centralized in `Frontend/services/api.ts`
   - File uploads use Base64 encoding for Python transfer

### Directory Structure

```
Frontend/
├── components/
│   ├── layout/     # Sidebar, Header, PageWrapper
│   └── ui/         # Button, Modal, Table, FileUpload, etc.
├── pages/          # Dashboard, Users, Roles, Missions, etc.
├── services/       # api.ts (API abstraction), mockData.ts
├── styles/         # theme.ts (color palette)
├── types.ts        # TypeScript interfaces
├── constants.tsx   # Icons, version, app constants
└── App.tsx         # Main app with routing and state
```

## Important Implementation Details

### Reglas generales

- Siempre contesta en español.
- Siempre debes dirigirte hacia mi como "( Boris )"
- No hagas suposiciones, siempre pregunta.
- No te disculpes.
- Preserva en lo posible las estructuras existentes.
- Agrega comentarios para que los puedan ver otros desarrolladores.
- Realiza primero todas la preguntas aclaratorias pertinenetes antes de dar respuestas detalladas.


### Usted debe

- Nunca romper el codigo o funcionalidades existentes.
- Siempre debes agregar comentarios para que los puedan ver otros desarrolladores.
- Siempre debes usar buenas practicas de seguridad.
- Siempre debes usar buenas practicas de performance.
- Siempre debes usar buenas practicas de usabilidad.
- Siempre debes usar buenas practicas de mantenimiento.
- Debe procurar que el codigo sea lo mas limpio y legible posible.
- Debes procurar que el codigo sea lo mas optimo posible. 

### PROFUNDIDAD DEL RAZONAMIENTO

- Desglosar pensamientos complejos en pasos simples
- Aceptar la incertidumbre y la revisión
- Expresar pensamientos en una conversación natural

### Permission System
- Granular permissions defined in `types.ts`
- Role-based access control
- Permissions include: users, roles, missions, reports, settings management

### Mission Management
- Complex data structure supporting cellular and operator data
- File upload supports Excel (.xlsx) and CSV
- Analysis functionality with target search capabilities

### UI Components
- Dark theme with custom color palette
- Reusable component library in `components/ui/`
- HashRouter for client-side routing (desktop app compatible)
- Tab-based detail views for complex entities

### Mock Data
- Development mock data in `services/mockData.ts`
- Includes sample users, roles, and missions
- Toggle with `USE_MOCK_API` constant in `api.ts`

## Spanish Language Project
All documentation, UI text, and comments are in Spanish. Maintain Spanish consistency when adding new features or documentation.

## Backend Integration Points
When implementing Python backend:
- Follow specifications in `Frontend/BACKEND_GUIDE.md`
- Expose Python functions via Eel for JavaScript access
- Handle file uploads as Base64 strings
- Return JSON-serializable data structures

## Version Information
Current version: 1.0.0 (see `constants.tsx`)