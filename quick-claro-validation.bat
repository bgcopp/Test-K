@echo off
REM ============================================================================
REM Script Rápido de Validación CLARO - Solo Validación de BD
REM 
REM Ejecuta únicamente el validador Python para verificar estado actual
REM de los datos CLARO sin ejecutar Playwright. Útil para verificaciones
REM rápidas después de cargas manuales o debugging.
REM
REM Uso: quick-claro-validation.bat
REM ============================================================================

echo.
echo ========================================================================
echo                     CLARO QUICK DATABASE VALIDATION
echo                          KRONOS Testing Framework
echo ========================================================================
echo.

set "TIMESTAMP=%date:~10,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "TIMESTAMP=%TIMESTAMP: =0%"

echo [%time%] Ejecutando validación rápida de BD CLARO...
echo [%time%] Timestamp: %TIMESTAMP%
echo.

REM Verificar que existe la BD
if not exist "Backend\kronos.db" (
    echo [ERROR] Base de datos no encontrada: Backend\kronos.db
    echo [INFO] Asegúrese de que KRONOS haya sido ejecutado al menos una vez
    pause
    exit /b 1
)

echo [%time%] ✓ Base de datos encontrada
echo.

REM Crear directorio para reportes si no existe
if not exist "test-results" mkdir "test-results"

REM Ejecutar validador
echo [%time%] Ejecutando validador Python...
echo.

python tests\validation\claro-results-validator.py Backend\kronos.db

set "EXIT_CODE=%errorlevel%"

echo.
echo [%time%] =============================================================
echo [%time%] RESULTADO DE VALIDACIÓN RÁPIDA
echo [%time%] =============================================================

if %EXIT_CODE%==0 (
    echo [%time%] ✓ VALIDACIÓN EXITOSA - Todos los criterios cumplidos
    echo [%time%] Los datos CLARO están correctamente cargados
) else (
    echo [%time%] ✗ VALIDACIÓN FALLIDA - Revisar detalles arriba
    echo [%time%] Algunos criterios no se cumplieron
)

echo.
echo [%time%] Reporte detallado disponible en: test-results\claro_validation_report_*.json
echo.

pause

exit /b %EXIT_CODE%