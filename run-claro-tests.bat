@echo off
REM =====================================
REM KRONOS CLARO E2E Testing Suite
REM Script de ejecucion completa
REM Boris - KRONOS Testing Team
REM =====================================

echo.
echo ====================================
echo    KRONOS CLARO E2E TESTING SUITE
echo ====================================
echo.

REM Verificar Node.js
echo [1/7] Verificando Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js no encontrado. Instale Node.js 18+
    pause
    exit /b 1
)
echo Node.js verificado.

REM Verificar Python
echo [2/7] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado. Instale Python 3.8+
    pause
    exit /b 1
)
echo Python verificado.

REM Instalar dependencias de Playwright si es necesario
echo [3/7] Verificando dependencias de Playwright...
if not exist node_modules (
    echo Instalando dependencias...
    npm install
    if errorlevel 1 (
        echo ERROR: No se pudieron instalar las dependencias
        pause
        exit /b 1
    )
)

REM Instalar navegadores de Playwright
echo [4/7] Verificando navegadores de Playwright...
npx playwright install chromium
if errorlevel 1 (
    echo ERROR: No se pudieron instalar los navegadores
    pause
    exit /b 1
)

REM Crear directorio de resultados
echo [5/7] Preparando directorios...
if not exist test-results mkdir test-results

REM Ejecutar Backend en segundo plano
echo [6/7] Iniciando backend KRONOS...
cd Backend
start /B python main.py
cd ..

REM Esperar a que el backend se inicie
echo Esperando a que el backend se inicie (30 segundos)...
timeout /t 30 /nobreak >nul

REM Ejecutar tests de Playwright
echo [7/7] Ejecutando tests de Playwright...
echo.
echo =====================================
echo    EJECUTANDO TESTS E2E
echo =====================================
echo.

REM Ejecutar tests en orden secuencial
echo Ejecutando: 01 - Carga de archivos CLARO...
npx playwright test tests/claro-upload.spec.ts --reporter=html
set upload_result=%errorlevel%

echo.
echo Ejecutando: 02 - Validacion de numeros objetivo...
npx playwright test tests/claro-validation.spec.ts --reporter=html
set validation_result=%errorlevel%

echo.
echo Ejecutando: 03 - Analisis de correlacion...
npx playwright test tests/claro-correlation.spec.ts --reporter=html
set correlation_result=%errorlevel%

REM Ejecutar validacion final de BD con Python
echo.
echo Ejecutando: 04 - Validacion final de base de datos...
cd tests
python database-validator.py --action generate_report --output ../test-results/final-database-validation.json
set db_validation_result=%errorlevel%
cd ..

echo.
echo =====================================
echo    RESULTADOS DE TESTING
echo =====================================
echo.

if %upload_result%==0 (
    echo [OK] Carga de archivos CLARO
) else (
    echo [FAIL] Carga de archivos CLARO
)

if %validation_result%==0 (
    echo [OK] Validacion de numeros objetivo
) else (
    echo [FAIL] Validacion de numeros objetivo
)

if %correlation_result%==0 (
    echo [OK] Analisis de correlacion
) else (
    echo [FAIL] Analisis de correlacion
)

if %db_validation_result%==0 (
    echo [OK] Validacion de base de datos
) else (
    echo [FAIL] Validacion de base de datos
)

echo.
echo =====================================
echo    ARCHIVOS GENERADOS
echo =====================================
echo.

echo Reportes disponibles:
if exist test-results\html-report echo   - test-results\html-report\index.html (reporte interactivo)
if exist test-results\results.json echo   - test-results\results.json (resultados JSON)
if exist test-results\final-database-validation.json echo   - test-results\final-database-validation.json (validacion BD)

echo.
echo Screenshots y videos:
if exist test-results\artifacts echo   - test-results\artifacts\ (capturas y videos)

echo.
echo =====================================
echo    COMANDOS UTILES
echo =====================================
echo.
echo Para ver reporte interactivo:
echo   npm run report
echo.
echo Para re-ejecutar tests individuales:
echo   npm run test:claro
echo   npm run test:claro-validation
echo   npm run test:claro-correlation
echo.
echo Para validacion manual de BD:
echo   cd Backend ^& python verify_target_numbers.py
echo.

REM Calcular resultado final
set /a total_result=%upload_result%+%validation_result%+%correlation_result%+%db_validation_result%

if %total_result%==0 (
    echo [EXITO TOTAL] Todos los tests pasaron correctamente
    echo.
    echo Los numeros objetivo 3104277553 y 3224274851 han sido validados
    echo en la base de datos. El proceso de carga CLARO funciona al 100%%.
) else (
    echo [ATENCION] Algunos tests fallaron. Revise los reportes para detalles.
)

echo.
echo Testing completado. Presione cualquier tecla para continuar...
pause >nul