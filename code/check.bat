@echo off
setlocal enableextensions
cd /d "%~dp0"

REM ============================================================
REM  StaTable check launcher
REM  Place this file in code/ alongside gui_main.py
REM ============================================================

REM --- Optional: activate venv if present ---
if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat" >nul 2>&1
)
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat" >nul 2>&1
)

:menu
cls
echo ============================================================
echo  StaTable check menu
echo ============================================================
echo.
echo   [1] Smoke check         (fast: imports + Mermaid gen)
echo   [2] Unit tests (pytest) (existing test suite)
echo   [3] Full check          (smoke + pytest)
echo   [4] Launch GUI          (gui_main.py)
echo   [0] Exit
echo.
set /p choice=" Choose: "

if "%choice%"=="1" goto smoke
if "%choice%"=="2" goto pytest_only
if "%choice%"=="3" goto full
if "%choice%"=="4" goto gui
if "%choice%"=="0" goto end
goto menu

REM ------------------------------------------------------------
:smoke
cls
echo === Smoke check ===
echo.
python check_smoke.py
echo.
echo Exit code: %ERRORLEVEL%
echo.
pause
goto menu

REM ------------------------------------------------------------
:pytest_only
cls
echo === pytest (code\tests) ===
echo.
python -m pytest code\tests -v --tb=short
echo.
echo Exit code: %ERRORLEVEL%
echo.
pause
goto menu

REM ------------------------------------------------------------
:full
cls
echo === Smoke check ===
echo.
python check_smoke.py
if errorlevel 1 (
    echo.
    echo *** Smoke check failed. Skipping pytest. ***
    pause
    goto menu
)
echo.
echo === pytest (code\tests) ===
echo.
python -m pytest code\tests -v --tb=short
echo.
echo Exit code: %ERRORLEVEL%
echo.
pause
goto menu

REM ------------------------------------------------------------
:gui
cls
echo === Launching GUI ===
echo.
python gui_main.py
echo.
echo GUI exited. Exit code: %ERRORLEVEL%
echo.
pause
goto menu

REM ------------------------------------------------------------
:end
endlocal
exit /b 0