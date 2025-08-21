@echo off
echo ========================================
echo TESTING COMPLETO PHONECORRELATIONVIEWER
echo Solicitado por Boris - 2025-08-21
echo ========================================
echo.

echo 🚀 Iniciando testing MCP Playwright completo...

REM Crear directorio para screenshots si no existe
if not exist ".playwright-mcp" mkdir .playwright-mcp

echo 📦 Verificando dependencias...
call npm install --silent 2>NUL

echo 🎭 Ejecutando tests con configuración específica...
call npx playwright test --config=playwright-phonecorrelation-validation.config.ts --reporter=html,json,junit

echo.
echo ✅ Testing completado!
echo 📊 Revisa los reportes en:
echo    - test-results/phonecorrelation-validation-html-report/index.html
echo    - test-results/phonecorrelation-validation-results.json  
echo    - .playwright-mcp/ (screenshots de evidencia)
echo.

pause