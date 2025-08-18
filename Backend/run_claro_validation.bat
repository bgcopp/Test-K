@echo off
echo =======================================================
echo KRONOS - VALIDACION COMPLETA DE CARGA CLARO
echo =======================================================
echo.
echo Ejecutando validacion exhaustiva de carga CLARO...
echo Verificando:
echo - Carga completa de 5,611 registros
echo - Normalizacion correcta de numeros (sin prefijo 57)
echo - Presencia de numeros objetivo en BD
echo - Filtrado correcto por operador CLARO
echo.

cd /d "%~dp0"

python validate_claro_loading_complete.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =======================================================
    echo VALIDACION COMPLETADA EXITOSAMENTE
    echo =======================================================
    echo Todos los checks pasaron. La carga CLARO es correcta.
) else (
    echo.
    echo =======================================================
    echo VALIDACION FALLIDA - SE ENCONTRARON PROBLEMAS
    echo =======================================================
    echo Revise el archivo de resultados JSON para detalles.
    echo Ejecute las correcciones necesarias antes de continuar.
)

echo.
echo Presione cualquier tecla para salir...
pause > nul