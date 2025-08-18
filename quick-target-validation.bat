@echo off
echo ========================================
echo VALIDACION RAPIDA - NUMEROS OBJETIVO
echo ========================================
echo.
echo Ejecutando validacion rapida de numeros objetivo...
echo.

REM Crear directorios
if not exist "test-results\evidence" mkdir test-results\evidence

REM Ejecutar solo el test critico principal
npx playwright test tests/target-numbers-certification/target-numbers-certification.spec.ts --config=playwright-target-numbers.config.ts --grep="Test de Números Objetivo - CRÍTICO"

echo.
echo ========================================
echo VALIDACION RAPIDA COMPLETADA
echo ========================================

pause