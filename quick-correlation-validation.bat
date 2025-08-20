@echo off
REM ========================================
REM Validación Rápida - Diagrama de Correlación
REM 
REM Ejecuta tests básicos del diagrama para verificación rápida
REM ========================================

echo.
echo ========================================
echo  VALIDACION RAPIDA - Diagrama Correlacion
echo ========================================
echo.

cd /d "%~dp0"

REM Verificar que la aplicación esté corriendo
echo 🔍 Verificando que la aplicación esté ejecutándose...
curl -s http://localhost:5173 >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: La aplicación no está ejecutándose en http://localhost:5173
    echo    Por favor ejecute 'npm run dev' en el directorio Frontend/
    echo.
    pause
    exit /b 1
)

echo ✅ Aplicación ejecutándose correctamente

REM Ejecutar solo tests críticos
echo.
echo 🧪 Ejecutando tests críticos del diagrama...
echo.

npx playwright test ^
    --config=playwright-correlation-diagram.config.ts ^
    --grep "FASE 1.*modal|FASE 2.*visualización|FASE 3.*drag|FASE 4.*avatar" ^
    --reporter=list ^
    --max-failures=3

set TEST_EXIT_CODE=%errorlevel%

echo.
if %TEST_EXIT_CODE%==0 (
    echo ✅ Validación rápida exitosa!
    echo    El diagrama de correlación está funcionando correctamente.
) else (
    echo ❌ Se encontraron problemas en la validación
    echo    Ejecute 'run-correlation-diagram-tests.bat' para análisis detallado
)

echo.
echo Presiona cualquier tecla para continuar...
pause >nul

exit /b %TEST_EXIT_CODE%