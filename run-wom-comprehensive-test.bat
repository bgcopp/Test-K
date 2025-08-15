@echo off
REM KRONOS WOM Comprehensive Testing Suite - Easy Launch Script
REM Testing Engineer: Claude Code
REM Purpose: Automated execution of WOM file processing guarantee test

echo.
echo ===============================================================================
echo         KRONOS WOM COMPREHENSIVE TESTING SUITE
echo         100%% Record Processing Guarantee Test
echo ===============================================================================
echo.
echo Target File: PUNTO 1 TRAFICO DATOS WOM.xlsx
echo Expected Records: 17 (Multi-sheet: 9 + 8)
echo Operator: WOM
echo Test Engineer: Claude Code - Specialized Testing Engineer
echo.

REM Check if we're in the correct directory
if not exist "Backend\test_wom_comprehensive_guarantee.py" (
    echo ERROR: Must run from KRONOS project root directory
    echo Current directory: %CD%
    echo Expected file: Backend\test_wom_comprehensive_guarantee.py
    pause
    exit /b 1
)

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please install Python and ensure it's in your PATH
    pause
    exit /b 1
)

REM Check if playwright is installed
python -c "import playwright" >nul 2>&1
if errorlevel 1 (
    echo WARNING: Playwright not detected
    echo Installing Playwright...
    pip install playwright
    playwright install chromium
)

echo ===============================================================================
echo                           PRE-FLIGHT CHECKS
echo ===============================================================================
echo.

REM Check if test file exists
if not exist "archivos\CeldasDiferenteOperador\wom\PUNTO 1 TRAFICO DATOS WOM.xlsx" (
    echo ERROR: WOM test file not found!
    echo Expected: archivos\CeldasDiferenteOperador\wom\PUNTO 1 TRAFICO DATOS WOM.xlsx
    pause
    exit /b 1
) else (
    echo [OK] WOM test file found
)

REM Check if database exists (optional)
if exist "Backend\kronos.db" (
    echo [OK] Database found
) else (
    echo [INFO] Database will be created during test
)

REM Check if frontend dist exists
if exist "Frontend\dist\index.html" (
    echo [OK] Frontend build detected
) else (
    echo [WARNING] Frontend not built - you may need to run: cd Frontend ^&^& npm run build
)

echo.
echo ===============================================================================
echo                            SERVER REQUIREMENTS
echo ===============================================================================
echo.
echo CRITICAL: Before running this test, ensure the following servers are running:
echo.
echo 1. Frontend Development Server:
echo    Command: cd Frontend ^&^& npm run dev
echo    URL: http://localhost:5173
echo.
echo 2. Backend Server:
echo    Command: cd Backend ^&^& python main.py
echo    Port: Backend integration
echo.
echo The test will open a browser window and perform automated testing.
echo Screenshots and reports will be saved in the Backend directory.
echo.

set /p CONFIRM="Are both servers running? (y/N): "
if /i not "%CONFIRM%"=="y" (
    echo.
    echo Test cancelled. Please start the servers first:
    echo   Terminal 1: cd Frontend ^&^& npm run dev
    echo   Terminal 2: cd Backend ^&^& python main.py
    echo.
    pause
    exit /b 0
)

echo.
echo ===============================================================================
echo                         STARTING COMPREHENSIVE TEST
echo ===============================================================================
echo.

REM Change to Backend directory and run test
cd Backend

REM Run the comprehensive test
python test_wom_comprehensive_guarantee.py

REM Check exit code
if errorlevel 1 (
    echo.
    echo ===============================================================================
    echo                              TEST FAILED
    echo ===============================================================================
    echo Check the error messages above and generated logs for details.
) else (
    echo.
    echo ===============================================================================
    echo                          TEST COMPLETED
    echo ===============================================================================
    echo Check the generated reports for detailed results:
    echo - JSON Report: wom_comprehensive_test_report_*.json
    echo - Summary: wom_test_summary_*.txt
    echo - Screenshots: test_evidence_screenshots\
)

echo.
echo Press any key to view generated files...
pause >nul

REM Show generated files
echo.
echo Generated test artifacts:
dir /b wom_comprehensive_test_report_*.json 2>nul
dir /b wom_test_summary_*.txt 2>nul
if exist test_evidence_screenshots (
    echo Screenshots folder: test_evidence_screenshots\
    dir /b test_evidence_screenshots\*.png 2>nul | head -5
    echo ...and more
)

echo.
pause