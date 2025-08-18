@echo off
REM ============================================================================
REM Script de Configuración del Entorno para Pruebas CLARO E2E
REM 
REM Configura el entorno necesario para ejecutar las pruebas E2E CLARO:
REM - Instala dependencias de Playwright
REM - Configura Python y dependencias del backend
REM - Verifica archivos de datos objetivo
REM - Crea estructura de directorios
REM - Ejecuta verificaciones de compatibilidad
REM
REM Uso: setup-claro-e2e-environment.bat
REM ============================================================================

echo.
echo ========================================================================
echo                   CLARO E2E ENVIRONMENT SETUP
echo                      KRONOS Testing Framework
echo ========================================================================
echo.

set "TIMESTAMP=%date:~10,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "TIMESTAMP=%TIMESTAMP: =0%"

echo [%time%] Iniciando configuración del entorno CLARO E2E...
echo [%time%] Timestamp: %TIMESTAMP%
echo.

REM Verificar Node.js
echo [%time%] =============================================================
echo [%time%] VERIFICANDO DEPENDENCIAS DEL SISTEMA
echo [%time%] =============================================================
echo.

echo [%time%] Verificando Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js no está instalado
    echo [INFO] Instale Node.js desde https://nodejs.org/
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('node --version') do echo [%time%] ✓ Node.js: %%i
)

REM Verificar npm
echo [%time%] Verificando npm...
npm --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm no está disponible
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('npm --version') do echo [%time%] ✓ npm: %%i
)

REM Verificar Python
echo [%time%] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no está instalado
    echo [INFO] Instale Python 3.8+ desde https://python.org/
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('python --version') do echo [%time%] ✓ Python: %%i
)

echo.

REM Instalar dependencias de Node.js
echo [%time%] =============================================================
echo [%time%] INSTALANDO DEPENDENCIAS DE NODE.JS
echo [%time%] =============================================================
echo.

if not exist "package.json" (
    echo [ERROR] package.json no encontrado. Ejecutar desde el directorio raíz del proyecto.
    pause
    exit /b 1
)

echo [%time%] Instalando dependencias npm...
npm install
if errorlevel 1 (
    echo [ERROR] Falló la instalación de dependencias npm
    pause
    exit /b 1
)
echo [%time%] ✓ Dependencias npm instaladas

REM Instalar Playwright
echo [%time%] Instalando Playwright...
npm install @playwright/test
if errorlevel 1 (
    echo [ERROR] Falló la instalación de Playwright
    pause
    exit /b 1
)
echo [%time%] ✓ Playwright instalado

REM Instalar navegadores de Playwright
echo [%time%] Instalando navegadores Playwright (puede tomar varios minutos)...
npx playwright install chromium
if errorlevel 1 (
    echo [ERROR] Falló la instalación de navegadores Playwright
    pause
    exit /b 1
)
echo [%time%] ✓ Navegadores Playwright instalados

echo.

REM Instalar dependencias Python
echo [%time%] =============================================================
echo [%time%] CONFIGURANDO ENTORNO PYTHON
echo [%time%] =============================================================
echo.

if not exist "Backend\requirements.txt" (
    echo [WARNING] Backend\requirements.txt no encontrado
    echo [INFO] Creando requirements.txt básico...
    (
        echo eel
        echo sqlite3
        echo pandas
        echo openpyxl
        echo sqlalchemy
    ) > "Backend\requirements.txt"
)

echo [%time%] Instalando dependencias Python...
cd Backend
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Falló la instalación de dependencias Python
    cd ..
    pause
    exit /b 1
)
cd ..
echo [%time%] ✓ Dependencias Python instaladas

echo.

REM Crear estructura de directorios
echo [%time%] =============================================================
echo [%time%] CREANDO ESTRUCTURA DE DIRECTORIOS
echo [%time%] =============================================================
echo.

set "DIRS=test-results tests\helpers tests\validation tests\artifacts"

for %%d in (%DIRS%) do (
    if not exist "%%d" (
        mkdir "%%d"
        echo [%time%] ✓ Creado: %%d
    ) else (
        echo [%time%] ✓ Existe: %%d
    )
)

echo.

REM Verificar archivos de datos objetivo
echo [%time%] =============================================================
echo [%time%] VERIFICANDO ARCHIVOS DE DATOS OBJETIVO
echo [%time%] =============================================================
echo.

set "DATA_PATH=archivos\envioarchivosparaanalizar (1)"
set "FILES_OK=true"

echo [%time%] Verificando archivos CLARO en: %DATA_PATH%

REM Lista de archivos requeridos
set FILES[1]="1-225211_LLAMADAS_ENTRANTES_POR_CELDA_545612_0.xlsx"
set FILES[2]="1-225211_LLAMADAS_SALIENTES_POR_CELDA_545613_0.xlsx"
set FILES[3]="2-225211_LLAMADAS_ENTRANTES_POR_CELDA_545614_0.xlsx"
set FILES[4]="2-225211_LLAMADAS_SALIENTES_POR_CELDA_545615_0.xlsx"
set FILES[5]="SCANHUNTER.xlsx"

for /L %%i in (1,1,5) do (
    set "FILE=!FILES[%%i]!"
    set "FILE=!FILE:~1,-1!"
    if exist "%DATA_PATH%\!FILE!" (
        echo [%time%] ✓ !FILE!
    ) else (
        echo [%time%] ✗ FALTANTE: !FILE!
        set "FILES_OK=false"
    )
)

if "%FILES_OK%"=="false" (
    echo.
    echo [WARNING] Algunos archivos de datos objetivo no fueron encontrados
    echo [INFO] Coloque los archivos en: %DATA_PATH%
    echo [INFO] Las pruebas fallarán sin estos archivos
) else (
    echo [%time%] ✓ Todos los archivos objetivo están disponibles
)

echo.

REM Verificar configuración de base de datos
echo [%time%] =============================================================
echo [%time%] VERIFICANDO CONFIGURACIÓN DE BASE DE DATOS
echo [%time%] =============================================================
echo.

if exist "Backend\kronos.db" (
    echo [%time%] ✓ Base de datos existente encontrada: Backend\kronos.db
    echo [%time%] Las pruebas usarán datos existentes (se hará backup automático)
) else (
    echo [%time%] ℹ Base de datos nueva se creará automáticamente
    echo [%time%] KRONOS inicializará la BD en la primera ejecución
)

echo.

REM Ejecutar verificación básica de funcionalidad
echo [%time%] =============================================================
echo [%time%] VERIFICACIÓN DE FUNCIONALIDAD BÁSICA
echo [%time%] =============================================================
echo.

echo [%time%] Verificando importaciones Python básicas...
cd Backend
python -c "
import sys
try:
    import eel
    import sqlite3
    import pandas as pd
    import json
    print('✓ Importaciones básicas exitosas')
except ImportError as e:
    print(f'✗ Error de importación: {e}')
    sys.exit(1)
" 2>&1
if errorlevel 1 (
    echo [ERROR] Verificación básica de Python falló
    cd ..
    pause
    exit /b 1
)
cd ..

echo [%time%] Verificando configuración Playwright...
npx playwright --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Playwright no está configurado correctamente
    pause
    exit /b 1
)
echo [%time%] ✓ Playwright configurado correctamente

echo.

REM Mostrar resumen de configuración
echo [%time%] =============================================================
echo [%time%] RESUMEN DE CONFIGURACIÓN
echo [%time%] =============================================================
echo.

echo [%time%] ✓ Node.js y npm instalados
echo [%time%] ✓ Playwright y navegadores configurados
echo [%time%] ✓ Python y dependencias instaladas
echo [%time%] ✓ Estructura de directorios creada
if "%FILES_OK%"=="true" (
    echo [%time%] ✓ Archivos de datos objetivo disponibles
) else (
    echo [%time%] ⚠ Archivos de datos objetivo faltantes
)
echo [%time%] ✓ Verificación básica de funcionalidad completada

echo.
echo [%time%] =============================================================
echo [%time%] CONFIGURACIÓN COMPLETADA
echo [%time%] =============================================================
echo.

echo [%time%] El entorno CLARO E2E está listo para usar.
echo.
echo [%time%] Comandos disponibles:
echo [%time%] - run-claro-e2e-complete.bat       : Ejecutar suite completa
echo [%time%] - quick-claro-validation.bat       : Validación rápida de BD
echo [%time%] - npx playwright test --config=... : Ejecutar Playwright manualmente
echo.

if "%FILES_OK%"=="false" (
    echo [WARNING] RECORDATORIO: Coloque los archivos de datos en %DATA_PATH%
    echo [WARNING] antes de ejecutar las pruebas.
    echo.
)

echo [%time%] Configuración completa. Presione cualquier tecla para continuar...
pause >nul

exit /b 0