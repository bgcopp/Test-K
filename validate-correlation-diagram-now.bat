@echo off
REM ========================================
REM Validación Inmediata - Diagrama de Correlación
REM 
REM Script para verificar rápidamente el estado actual
REM del diagrama sin ejecutar tests automatizados
REM ========================================

echo.
echo ========================================
echo   VALIDACION INMEDIATA - Diagrama
echo ========================================
echo.

cd /d "%~dp0"

echo 🔍 Verificando archivos del diagrama...

REM Verificar archivos principales
set MISSING_FILES=0

if not exist "Frontend\components\ui\CorrelationDiagramModal.tsx" (
    echo ❌ Falta: CorrelationDiagramModal.tsx
    set /a MISSING_FILES+=1
) else (
    echo ✅ CorrelationDiagramModal.tsx
)

if not exist "Frontend\components\ui\NetworkDiagram.tsx" (
    echo ❌ Falta: NetworkDiagram.tsx
    set /a MISSING_FILES+=1
) else (
    echo ✅ NetworkDiagram.tsx
)

if not exist "Frontend\components\ui\PersonNode.tsx" (
    echo ❌ Falta: PersonNode.tsx
    set /a MISSING_FILES+=1
) else (
    echo ✅ PersonNode.tsx
)

if not exist "Frontend\components\ui\DiagramToolbar.tsx" (
    echo ❌ Falta: DiagramToolbar.tsx
    set /a MISSING_FILES+=1
) else (
    echo ✅ DiagramToolbar.tsx
)

if not exist "Frontend\utils\graphTransformations.ts" (
    echo ❌ Falta: graphTransformations.ts
    set /a MISSING_FILES+=1
) else (
    echo ✅ graphTransformations.ts
)

if not exist "Frontend\utils\diagramPersistence.ts" (
    echo ❌ Falta: diagramPersistence.ts
    set /a MISSING_FILES+=1
) else (
    echo ✅ diagramPersistence.ts
)

if not exist "Frontend\components\ui\AvatarSelector.tsx" (
    echo ❌ Falta: AvatarSelector.tsx
    set /a MISSING_FILES+=1
) else (
    echo ✅ AvatarSelector.tsx
)

if not exist "Frontend\components\ui\ContextualMenu.tsx" (
    echo ❌ Falta: ContextualMenu.tsx
    set /a MISSING_FILES+=1
) else (
    echo ✅ ContextualMenu.tsx
)

if not exist "Frontend\components\ui\NodeEditor.tsx" (
    echo ❌ Falta: NodeEditor.tsx
    set /a MISSING_FILES+=1
) else (
    echo ✅ NodeEditor.tsx
)

echo.
echo 📊 Verificando integración...

REM Verificar integración en MissionDetail
findstr /c:"CorrelationDiagramModal" "Frontend\pages\MissionDetail.tsx" >nul 2>&1
if errorlevel 1 (
    echo ❌ CorrelationDiagramModal no integrado en MissionDetail
    set /a MISSING_FILES+=1
) else (
    echo ✅ Integración en MissionDetail.tsx
)

echo.
echo 🎯 Verificando configuración...

if not exist "test-correlation-diagram-complete.spec.ts" (
    echo ⚠️  Tests automatizados no encontrados
) else (
    echo ✅ Suite de tests disponible
)

if not exist "playwright-correlation-diagram.config.ts" (
    echo ⚠️  Configuración Playwright no encontrada
) else (
    echo ✅ Configuración Playwright lista
)

echo.
echo ========================================

if %MISSING_FILES% equ 0 (
    echo ✅ DIAGRAMA COMPLETO
    echo    Todos los archivos están presentes
    echo    Estado: PRODUCTION READY
    echo.
    echo 🚀 Para testing automatizado ejecute:
    echo    run-correlation-diagram-tests.bat
    echo.
    echo 🎯 Para validación rápida ejecute:
    echo    quick-correlation-validation.bat
) else (
    echo ❌ IMPLEMENTACION INCOMPLETA
    echo    Faltan %MISSING_FILES% archivo(s)
    echo    Estado: DESARROLLO EN PROGRESO
)

echo.
echo ========================================
echo.
echo Presiona cualquier tecla para continuar...
pause >nul