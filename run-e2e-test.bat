@echo off
REM Script para ejecutar test end-to-end de Sábanas de Operador
REM Ejecuta el backend y abre la página de test en el navegador

echo ================================================
echo TEST END-TO-END - SABANAS DE OPERADOR
echo ================================================
echo.

echo [INFO] Verificando estructura de directorios...
if not exist "Backend\main.py" (
    echo [ERROR] Backend\main.py no encontrado
    echo [ERROR] Ejecute este script desde el directorio raiz del proyecto
    pause
    exit /b 1
)

if not exist "Frontend\test-e2e-operator-sheets.tsx" (
    echo [ERROR] Test E2E no encontrado
    echo [ERROR] Verifique que Frontend\test-e2e-operator-sheets.tsx existe
    pause
    exit /b 1
)

echo [OK] Estructura verificada
echo.

echo [INFO] Compilando frontend para produccion...
cd Frontend
if exist "dist" rmdir /s /q dist
call npm run build
if errorlevel 1 (
    echo [ERROR] Compilacion fallida
    pause
    exit /b 1
)
echo [OK] Frontend compilado exitosamente
echo.

echo [INFO] Iniciando backend...
cd ..\Backend
echo [INFO] Backend iniciandose en http://localhost:8000
echo [INFO] La pagina de test estara disponible en: http://localhost:8000/#/test-operator-sheets
echo.

echo ================================================
echo INSTRUCCIONES:
echo 1. Espere a que el backend termine de cargar
echo 2. El navegador se abrira automaticamente
echo 3. Navegue a la seccion de test si no se abre automaticamente
echo 4. Haga clic en "Iniciar Test Completo"
echo 5. Observe los resultados en tiempo real
echo ================================================
echo.

REM Esperar 3 segundos y abrir navegador
timeout /t 3 /nobreak >nul
start http://localhost:8000/#/test-operator-sheets

REM Ejecutar backend (esto bloquea hasta que se cierre)
python main.py

echo.
echo [INFO] Test completado. Backend cerrado.
pause