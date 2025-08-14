@echo off
REM Script para testear el sistema de shutdown de KRONOS
REM Uso: test_shutdown.bat [auto] [timeout]

setlocal
set TIMEOUT=10
set AUTO_MODE=false

REM Procesar parámetros
if "%1"=="auto" (
    set AUTO_MODE=true
    if not "%2"=="" set TIMEOUT=%2
)

echo =====================================
echo KRONOS SHUTDOWN TEST SCRIPT
echo =====================================
echo.

REM Cambiar al directorio del backend
cd /d "%~dp0"

REM Verificar que Python esté disponible
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no está instalado o no está en PATH
    pause
    exit /b 1
)

REM Verificar que el script de test existe
if not exist "test_shutdown.py" (
    echo ERROR: Script test_shutdown.py no encontrado
    pause
    exit /b 1
)

echo Configuración:
echo - Modo automático: %AUTO_MODE%
echo - Timeout: %TIMEOUT% segundos
echo.

if "%AUTO_MODE%"=="true" (
    echo Ejecutando test automático...
    python test_shutdown.py --auto-close --timeout=%TIMEOUT%
) else (
    echo Ejecutando test interactivo...
    echo Presiona Ctrl+C en cualquier momento para probar el manejo de señales
    python test_shutdown.py
)

echo.
echo Test completado. Código de salida: %errorlevel%
if not "%AUTO_MODE%"=="true" pause