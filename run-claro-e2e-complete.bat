@echo off
REM ============================================================================
REM Script de Automatización para Pruebas E2E Completas CLARO
REM 
REM Ejecuta la suite completa de pruebas Playwright para validar:
REM - Carga de archivo HUNTER
REM - Carga de 4 archivos CLARO específicos (5,611 registros)
REM - Validación de números objetivo
REM - Algoritmo de correlación
REM - Generación de reportes detallados
REM
REM Uso: run-claro-e2e-complete.bat [--headless|--headed]
REM ============================================================================

echo.
echo ========================================================================
echo                     CLARO E2E COMPLETE VALIDATION SUITE
echo                          KRONOS Testing Framework
echo ========================================================================
echo.

REM Configuración de variables
set "SCRIPT_DIR=%~dp0"
set "TIMESTAMP=%date:~10,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "TIMESTAMP=%TIMESTAMP: =0%"
set "LOG_FILE=test-results\claro-e2e-execution-%TIMESTAMP%.log"
set "REPORT_DIR=test-results\claro-e2e-reports"

REM Crear directorios necesarios
if not exist "test-results" mkdir "test-results"
if not exist "%REPORT_DIR%" mkdir "%REPORT_DIR%"

echo [%time%] Iniciando CLARO E2E Complete Validation Suite...
echo [%time%] Timestamp de ejecucion: %TIMESTAMP%
echo [%time%] Log file: %LOG_FILE%
echo.

REM Verificar archivos objetivo existen
echo [%time%] Verificando archivos objetivo...
set "DATA_PATH=archivos\envioarchivosparaanalizar (1)"

set "FILES_MISSING=false"
if not exist "%DATA_PATH%\1-225211_LLAMADAS_ENTRANTES_POR_CELDA_545612_0.xlsx" (
    echo [ERROR] Archivo faltante: 1-225211_LLAMADAS_ENTRANTES_POR_CELDA_545612_0.xlsx
    set "FILES_MISSING=true"
)
if not exist "%DATA_PATH%\1-225211_LLAMADAS_SALIENTES_POR_CELDA_545613_0.xlsx" (
    echo [ERROR] Archivo faltante: 1-225211_LLAMADAS_SALIENTES_POR_CELDA_545613_0.xlsx
    set "FILES_MISSING=true"
)
if not exist "%DATA_PATH%\2-225211_LLAMADAS_ENTRANTES_POR_CELDA_545614_0.xlsx" (
    echo [ERROR] Archivo faltante: 2-225211_LLAMADAS_ENTRANTES_POR_CELDA_545614_0.xlsx
    set "FILES_MISSING=true"
)
if not exist "%DATA_PATH%\2-225211_LLAMADAS_SALIENTES_POR_CELDA_545615_0.xlsx" (
    echo [ERROR] Archivo faltante: 2-225211_LLAMADAS_SALIENTES_POR_CELDA_545615_0.xlsx
    set "FILES_MISSING=true"
)
if not exist "%DATA_PATH%\SCANHUNTER.xlsx" (
    echo [ERROR] Archivo HUNTER faltante: SCANHUNTER.xlsx
    set "FILES_MISSING=true"
)

if "%FILES_MISSING%"=="true" (
    echo.
    echo [ERROR] Archivos faltantes detectados. Verificar carpeta de datos.
    echo [ERROR] Ruta esperada: %DATA_PATH%
    pause
    exit /b 1
)

echo [%time%] ✓ Todos los archivos objetivo verificados correctamente
echo.

REM Verificar que Playwright está instalado
echo [%time%] Verificando instalación de Playwright...
npx playwright --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Playwright no está instalado. Ejecutando instalación...
    npm install @playwright/test
    npx playwright install chromium
)
echo [%time%] ✓ Playwright verificado
echo.

REM Determinar modo de ejecución
set "PLAYWRIGHT_MODE=--headed"
if "%1"=="--headless" set "PLAYWRIGHT_MODE=--headed=false"
if "%1"=="--headed" set "PLAYWRIGHT_MODE=--headed"

echo [%time%] Modo de ejecución: %PLAYWRIGHT_MODE%
echo.

REM Crear backup de BD antes de las pruebas
echo [%time%] Creando backup de base de datos...
if exist "Backend\kronos.db" (
    copy "Backend\kronos.db" "Backend\kronos.db.backup_%TIMESTAMP%" >nul
    echo [%time%] ✓ Backup creado: kronos.db.backup_%TIMESTAMP%
)
echo.

REM Verificar que el backend puede iniciarse
echo [%time%] Verificando disponibilidad del backend...
cd Backend
python -c "import main; print('Backend dependencies OK')" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Problemas con dependencias del backend Python
    echo [INFO] Instalando dependencias...
    pip install -r requirements.txt
)
cd ..
echo [%time%] ✓ Backend verificado
echo.

REM Ejecutar suite de pruebas Playwright
echo [%time%] =============================================================
echo [%time%] INICIANDO EJECUCIÓN DE PRUEBAS PLAYWRIGHT CLARO E2E
echo [%time%] =============================================================
echo.

npx playwright test --config=playwright-claro-e2e.config.ts %PLAYWRIGHT_MODE% --reporter=html,json,junit --output-dir="%REPORT_DIR%\artifacts" > "%LOG_FILE%" 2>&1

set "PLAYWRIGHT_EXIT_CODE=%errorlevel%"

echo [%time%] Pruebas Playwright completadas con código: %PLAYWRIGHT_EXIT_CODE%
echo.

REM Ejecutar validador Python de resultados
echo [%time%] =============================================================
echo [%time%] EJECUTANDO VALIDADOR DE RESULTADOS PYTHON
echo [%time%] =============================================================
echo.

python tests\validation\claro-results-validator.py Backend\kronos.db
set "VALIDATOR_EXIT_CODE=%errorlevel%"

echo [%time%] Validador Python completado con código: %VALIDATOR_EXIT_CODE%
echo.

REM Generar reporte de resumen
echo [%time%] =============================================================
echo [%time%] GENERANDO REPORTE DE RESUMEN FINAL
echo [%time%] =============================================================

set "SUMMARY_FILE=%REPORT_DIR%\execution-summary-%TIMESTAMP%.txt"

echo CLARO E2E COMPLETE VALIDATION - EXECUTION SUMMARY > "%SUMMARY_FILE%"
echo ================================================= >> "%SUMMARY_FILE%"
echo. >> "%SUMMARY_FILE%"
echo Execution Timestamp: %TIMESTAMP% >> "%SUMMARY_FILE%"
echo Log File: %LOG_FILE% >> "%SUMMARY_FILE%"
echo Playwright Exit Code: %PLAYWRIGHT_EXIT_CODE% >> "%SUMMARY_FILE%"
echo Python Validator Exit Code: %VALIDATOR_EXIT_CODE% >> "%SUMMARY_FILE%"
echo. >> "%SUMMARY_FILE%"

if %PLAYWRIGHT_EXIT_CODE%==0 (
    echo Playwright Tests: PASSED >> "%SUMMARY_FILE%"
) else (
    echo Playwright Tests: FAILED >> "%SUMMARY_FILE%"
)

if %VALIDATOR_EXIT_CODE%==0 (
    echo Results Validation: PASSED >> "%SUMMARY_FILE%"
) else (
    echo Results Validation: FAILED >> "%SUMMARY_FILE%"
)

echo. >> "%SUMMARY_FILE%"
echo Expected Outcomes: >> "%SUMMARY_FILE%"
echo - HUNTER file loaded successfully >> "%SUMMARY_FILE%"
echo - 4 CLARO files loaded (5,611 total records) >> "%SUMMARY_FILE%"
echo - Target numbers found in data >> "%SUMMARY_FILE%"
echo - Correlation algorithm executed >> "%SUMMARY_FILE%"
echo. >> "%SUMMARY_FILE%"
echo Generated Reports: >> "%SUMMARY_FILE%"
echo - HTML Report: test-results/claro-e2e-html-report/index.html >> "%SUMMARY_FILE%"
echo - JSON Results: test-results/claro-e2e-results.json >> "%SUMMARY_FILE%"
echo - Python Validation: test-results/claro_validation_report_*.json >> "%SUMMARY_FILE%"
echo. >> "%SUMMARY_FILE%"

REM Mostrar resultados finales
echo [%time%] =============================================================
echo [%time%] RESULTADOS FINALES
echo [%time%] =============================================================
echo.

if %PLAYWRIGHT_EXIT_CODE%==0 (
    echo [%time%] ✓ Pruebas Playwright: EXITOSAS
) else (
    echo [%time%] ✗ Pruebas Playwright: FALLIDAS
)

if %VALIDATOR_EXIT_CODE%==0 (
    echo [%time%] ✓ Validación de Resultados: EXITOSA
) else (
    echo [%time%] ✗ Validación de Resultados: FALLIDA
)

echo.
echo [%time%] Reportes generados:
echo [%time%] - Resumen: %SUMMARY_FILE%
echo [%time%] - Log de ejecución: %LOG_FILE%
echo [%time%] - Reporte HTML: test-results\claro-e2e-html-report\index.html
echo [%time%] - Artifacts: %REPORT_DIR%\artifacts\
echo.

REM Abrir reportes automáticamente si las pruebas fueron exitosas
if %PLAYWRIGHT_EXIT_CODE%==0 if %VALIDATOR_EXIT_CODE%==0 (
    echo [%time%] ¡PRUEBAS COMPLETADAS EXITOSAMENTE!
    echo [%time%] Abriendo reporte HTML...
    start test-results\claro-e2e-html-report\index.html
) else (
    echo [%time%] PRUEBAS FALLIDAS - Revisar logs para detalles
)

echo.
echo [%time%] Ejecución completa. Presione cualquier tecla para salir...
pause >nul

REM Salir con código de error si alguna validación falló
if %PLAYWRIGHT_EXIT_CODE%==0 if %VALIDATOR_EXIT_CODE%==0 (
    exit /b 0
) else (
    exit /b 1
)