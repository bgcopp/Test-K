@echo off
REM Script de ejecución para Test de Validación del Algoritmo de Correlación
REM Validación específica de números objetivo identificados por Boris

echo ========================================
echo   KRONOS - Test Algoritmo Correlación  
echo   Validación Números Objetivo Boris    
echo ========================================
echo.

REM Verificar si está en el directorio correcto
if not exist "Backend\main.py" (
    echo ❌ ERROR: Ejecutar desde el directorio raíz del proyecto KRONOS
    echo    Directorio actual: %CD%
    echo    Directorio esperado: C:\Soluciones\BGC\claude\KNSOft
    pause
    exit /b 1
)

REM Verificar si existe el test
if not exist "tests\correlation-algorithm-validation.spec.ts" (
    echo ❌ ERROR: Test de correlación no encontrado
    echo    Archivo esperado: tests\correlation-algorithm-validation.spec.ts
    pause
    exit /b 1
)

echo 🔧 Verificando prerequisitos...

REM Verificar Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Node.js no está instalado o no está en PATH
    echo    Instalar Node.js desde: https://nodejs.org/
    pause
    exit /b 1
)

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python no está instalado o no está en PATH
    echo    Instalar Python desde: https://python.org/
    pause
    exit /b 1
)

echo ✅ Prerequisitos verificados

echo.
echo 🚀 Iniciando Backend KRONOS...

REM Iniciar backend en segundo plano
start /B "KRONOS Backend" cmd /c "cd Backend && python main.py"

REM Esperar que el backend inicie
echo ⏳ Esperando que el backend esté disponible...
timeout /t 10 /nobreak >nul

REM Verificar que el backend responde
echo 🔍 Verificando conectividad del backend...
curl -s http://localhost:8000 >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Backend no responde inmediatamente, esperando más tiempo...
    timeout /t 10 /nobreak >nul
)

echo.
echo 📋 Configuración del test:
echo    • Período: 2024-08-12 20:00:00 - 2024-08-13 02:00:00
echo    • Números objetivo: 3224274851, 3208611034, 3104277553, 3102715509, 3143534707, 3214161903
echo    • Número crítico: 3104277553 -> 3224274851
echo    • Celdas esperadas: 12345 -> 67890
echo    • Min coincidencias: 2
echo.

echo 🎭 Ejecutando test Playwright de Algoritmo de Correlación...
echo.

REM Ejecutar test específico
npx playwright test tests/correlation-algorithm-validation.spec.ts --headed --timeout=300000

REM Capturar resultado del test
set TEST_RESULT=%errorlevel%

echo.
if %TEST_RESULT% equ 0 (
    echo ✅ TEST COMPLETADO EXITOSAMENTE
    echo.
    echo 📊 Resumen de Validación:
    echo    ✓ Navegación a análisis de correlación
    echo    ✓ Configuración de parámetros de correlación
    echo    ✓ Ejecución del algoritmo
    echo    ✓ Validación de números objetivo específicos
    echo    ✓ Verificación de conexiones 3104277553 -> 3224274851
    echo    ✓ Captura de evidencia y screenshots
    echo.
    echo 📁 Evidencia capturada en: Backend\test_evidence_screenshots\
) else (
    echo ❌ TEST FALLÓ
    echo.
    echo 🔍 Posibles causas:
    echo    • Backend no está ejecutándose correctamente
    echo    • Base de datos no contiene los números objetivo esperados
    echo    • Período de fechas configurado no tiene datos
    echo    • Interfaz de usuario cambió (selectores desactualizados)
    echo.
    echo 💡 Recomendaciones:
    echo    1. Verificar que Backend\kronos.db contiene datos del período 2024-08-12
    echo    2. Revisar logs en Backend\kronos_backend.log
    echo    3. Ejecutar test individual: npx playwright test tests\correlation-algorithm-validation.spec.ts --debug
)

echo.
echo 📁 Archivos de evidencia generados:
if exist "Backend\test_evidence_screenshots\" (
    dir "Backend\test_evidence_screenshots\*correlation*" /b 2>nul
    dir "Backend\test_evidence_screenshots\*target*" /b 2>nul
    dir "Backend\test_evidence_screenshots\*validation*" /b 2>nul
)

echo.
echo 🛑 Deteniendo backend...
taskkill /F /IM python.exe >nul 2>&1

echo.
echo ========================================
echo   Test de Algoritmo de Correlación    
echo   Completado - Revise los resultados   
echo ========================================

if %TEST_RESULT% neq 0 (
    echo.
    echo ⚠️  Para análisis detallado del fallo:
    echo    npx playwright test tests\correlation-algorithm-validation.spec.ts --debug --headed
    echo.
)

pause
exit /b %TEST_RESULT%