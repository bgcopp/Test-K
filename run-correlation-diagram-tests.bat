@echo off
REM ========================================
REM Script de Testing Completo - Diagrama de Correlación
REM 
REM Ejecuta toda la suite de tests del diagrama interactivo
REM con reportes detallados y métricas de performance
REM ========================================

echo.
echo ========================================
echo  KRONOS - Testing Diagrama de Correlacion
echo ========================================
echo.

REM Verificar que Node.js está instalado
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Node.js no está instalado o no está en PATH
    echo    Instalar Node.js desde https://nodejs.org/
    pause
    exit /b 1
)

REM Verificar que npm está disponible
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: npm no está disponible
    pause
    exit /b 1
)

REM Cambiar al directorio del proyecto
cd /d "%~dp0"

echo 📦 Verificando dependencias...

REM Verificar si existe package.json en el directorio raíz
if not exist "package.json" (
    echo ⚠️  package.json no encontrado en directorio raíz
    echo    Inicializando proyecto para Playwright...
    npm init -y
    npm install @playwright/test@latest
)

REM Verificar si Playwright está instalado
if not exist "node_modules\@playwright\test" (
    echo 📥 Instalando Playwright...
    npm install @playwright/test@latest
)

REM Instalar navegadores si es necesario
echo 🌐 Verificando navegadores de Playwright...
npx playwright install chromium edge

REM Crear directorios de resultados si no existen
if not exist "test-results" mkdir test-results
if not exist "test-results\screenshots" mkdir test-results\screenshots
if not exist "test-results\videos" mkdir test-results\videos
if not exist "test-results\html-report" mkdir test-results\html-report

echo.
echo 🚀 Iniciando tests del diagrama de correlación...
echo.

REM Ejecutar tests con configuración específica
npx playwright test --config=playwright-correlation-diagram.config.ts --reporter=html

set TEST_EXIT_CODE=%errorlevel%

echo.
if %TEST_EXIT_CODE%==0 (
    echo ✅ Todos los tests pasaron exitosamente!
    echo.
    echo 📊 Reportes generados:
    echo    - HTML Report: test-results\html-report\index.html
    echo    - JSON Results: test-results\correlation-diagram-results.json
    echo    - Screenshots: test-results\screenshots\
    echo    - Videos: test-results\videos\
    echo.
    echo 🌐 Abriendo reporte HTML...
    start "" "test-results\html-report\index.html"
) else (
    echo ❌ Algunos tests fallaron (código de salida: %TEST_EXIT_CODE%)
    echo.
    echo 🔍 Revisar detalles en:
    echo    - HTML Report: test-results\html-report\index.html
    echo    - Screenshots de fallos: test-results\screenshots\
    echo    - Videos de fallos: test-results\videos\
    echo.
    echo 🌐 Abriendo reporte de fallos...
    start "" "test-results\html-report\index.html"
)

echo.
echo ========================================
echo  Testing completado
echo ========================================
echo.
echo Presiona cualquier tecla para continuar...
pause >nul

exit /b %TEST_EXIT_CODE%