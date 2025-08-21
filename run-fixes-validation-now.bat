@echo off
echo ===============================================
echo 🎯 VALIDACION CRITICA CORRECCIONES DIAGRAMA D3.js
echo Testing Engineer - Boris Requirements
echo ===============================================
echo.

echo 📋 Verificando entorno de testing...
if not exist node_modules\@playwright\test (
    echo ❌ ERROR: Playwright no instalado
    echo Ejecuta: npm install
    exit /b 1
)

echo 📊 Creando directorio de resultados...
if not exist test-results mkdir test-results

echo 🚀 Ejecutando tests de validacion...
echo.
npx playwright test --config=playwright-fixes-validation.config.ts

echo.
echo 📸 Screenshots de evidencia generados en test-results/
echo 📋 Reporte HTML disponible en test-results/fixes-validation-report/
echo.

if %ERRORLEVEL% EQU 0 (
    echo ✅ VALIDACION COMPLETA: Correcciones Boris 100%% RESUELTAS
    echo 🎉 LISTO PARA PROCEDER CON FASE 2
) else (
    echo ❌ VALIDACION FALLIDA: Revisar correcciones
    echo 🔍 Ver screenshots en test-results/ para debugging
)

echo.
pause