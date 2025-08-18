@echo off
echo ========================================
echo SETUP - TESTS DE CERTIFICACION KRONOS
echo ========================================
echo.
echo Configurando entorno para tests de certificacion...
echo.

REM Verificar Node.js
echo Verificando Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js no esta instalado
    echo Por favor instala Node.js desde https://nodejs.org/
    pause
    exit /b 1
)

echo ✅ Node.js instalado
node --version

REM Instalar dependencias de Playwright
echo.
echo Instalando Playwright...
npm install -D @playwright/test

echo.
echo Instalando navegadores de Playwright...
npx playwright install

echo.
echo Instalando dependencias adicionales...
npm install -D typescript

REM Crear directorios necesarios
echo.
echo Creando directorios de resultados...
if not exist "test-results" mkdir test-results
if not exist "test-results\evidence" mkdir test-results\evidence
if not exist "test-results\target-numbers-certification" mkdir test-results\target-numbers-certification

echo ✅ Directorios creados

REM Verificar archivos de configuracion
echo.
echo Verificando archivos de configuracion...

if exist "playwright-target-numbers.config.ts" (
    echo ✅ playwright-target-numbers.config.ts
) else (
    echo ❌ playwright-target-numbers.config.ts falta
)

if exist "tests\target-numbers-certification\target-numbers-certification.spec.ts" (
    echo ✅ target-numbers-certification.spec.ts
) else (
    echo ❌ target-numbers-certification.spec.ts falta
)

if exist "run-target-numbers-certification.bat" (
    echo ✅ run-target-numbers-certification.bat
) else (
    echo ❌ run-target-numbers-certification.bat falta
)

echo.
echo ========================================
echo SETUP COMPLETADO
echo ========================================
echo.
echo Para ejecutar los tests:
echo   1. Inicia KRONOS: cd Backend && python main.py
echo   2. Ejecuta: run-target-numbers-certification.bat
echo.
echo Para validacion rapida:
echo   quick-target-validation.bat
echo.
echo Para diagnostico:
echo   npx playwright test diagnostic-test.spec.ts
echo.
echo ========================================

pause