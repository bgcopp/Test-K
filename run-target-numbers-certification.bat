@echo off
echo ========================================
echo KRONOS - CERTIFICACION NUMEROS OBJETIVO
echo ========================================
echo.
echo Boris, este script ejecuta la certificacion completa
echo de los numeros objetivo en KRONOS.
echo.
echo NUMEROS OBJETIVO A VALIDAR:
echo - 3224274851 (2 coincidencias esperadas)
echo - 3208611034 (2 coincidencias esperadas)  
echo - 3143534707 (3 coincidencias esperadas)
echo - 3102715509 (1 coincidencia esperada)
echo - 3214161903 (1 coincidencia esperada)
echo.
echo ========================================

REM Verificar que Node.js este instalado
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js no esta instalado
    echo Por favor instala Node.js antes de continuar
    pause
    exit /b 1
)

REM Verificar que Playwright este instalado
npx playwright --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando Playwright...
    npm install -D @playwright/test
    npx playwright install
)

REM Crear directorios necesarios
if not exist "test-results" mkdir test-results
if not exist "test-results\evidence" mkdir test-results\evidence

echo.
echo Iniciando aplicacion KRONOS en el backend...
cd Backend
start /B python main.py
cd ..

echo Esperando a que la aplicacion este lista...
timeout /t 10 /nobreak >nul

echo.
echo ========================================
echo EJECUTANDO CERTIFICACION COMPLETA
echo ========================================

REM Ejecutar tests de certificacion
npx playwright test --config=playwright-target-numbers.config.ts --reporter=html

echo.
echo ========================================
echo CERTIFICACION COMPLETADA
echo ========================================

REM Verificar resultados
if exist "test-results\target-numbers-certification-results.json" (
    echo.
    echo ✅ Archivo de resultados generado
    echo 📄 Ubicacion: test-results\target-numbers-certification-results.json
) else (
    echo.
    echo ❌ No se genero archivo de resultados
)

if exist "test-results\evidence" (
    echo ✅ Evidencias capturadas en: test-results\evidence\
) else (
    echo ❌ No se capturaron evidencias
)

echo.
echo Abriendo reporte HTML...
if exist "test-results\target-numbers-certification\index.html" (
    start test-results\target-numbers-certification\index.html
) else (
    echo ❌ Reporte HTML no encontrado
)

echo.
echo ========================================
echo RESUMEN DE CERTIFICACION
echo ========================================
echo.
echo Si todos los tests pasaron ✅:
echo   - Todos los numeros objetivo estan presentes
echo   - Formato correcto (sin prefijo 57)
echo   - Algoritmo funcionando correctamente
echo.
echo Si algun test fallo ❌:
echo   - Revisar test-results\evidence\ para screenshots
echo   - Verificar logs en test-results\
echo   - Contactar equipo de desarrollo
echo.
echo ========================================

pause