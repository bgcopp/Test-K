@echo off
echo ========================================
echo   KRONOS - Build Frontend para Produccion
echo ========================================
echo.

REM Cambiar al directorio Frontend
cd "%~dp0Frontend" 2>nul
if errorlevel 1 (
    echo ERROR: No se encontro el directorio Frontend
    echo Asegurate de ejecutar este script desde el directorio raiz del proyecto
    pause
    exit /b 1
)

echo Directorio actual: %CD%
echo.

REM Verificar que package.json existe
if not exist "package.json" (
    echo ERROR: No se encontro package.json en el directorio Frontend
    echo Verifica que estas en el directorio correcto
    pause
    exit /b 1
)

REM Verificar que node_modules existe, sino instalar dependencias
if not exist "node_modules" (
    echo Las dependencias no estan instaladas. Instalando...
    echo Ejecutando: npm install
    npm install
    if errorlevel 1 (
        echo ERROR: Fallo la instalacion de dependencias
        pause
        exit /b 1
    )
    echo Dependencias instaladas exitosamente.
    echo.
)

REM Limpiar build anterior si existe
if exist "dist" (
    echo Limpiando build anterior...
    rmdir /s /q "dist"
    echo Build anterior eliminado.
    echo.
)

REM Construir aplicacion para produccion
echo Construyendo aplicacion para produccion...
echo Ejecutando: npm run build
npm run build
if errorlevel 1 (
    echo ERROR: Fallo el build de la aplicacion
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completado exitosamente!
echo ========================================
echo.
echo El frontend ha sido compilado en: Frontend/dist/
echo.
echo Para ejecutar la aplicacion completa:
echo   1. cd Backend
echo   2. python main.py
echo.
echo La aplicacion se abrira automaticamente en una ventana.
echo ========================================
pause