@echo off
setlocal enableextensions
cd /d "%~dp0"

REM ============================================================
REM  gcc syntax check for generated C code
REM  Place this file in code/ alongside gui_main.py
REM  Target: output/ (by_layer structure is expected)
REM ============================================================

REM ---- CONFIG: full path to gcc.exe (WinLibs POSIX UCRT) ----
set "GCC_PATH=C:\Users\user\AppData\Local\Microsoft\WinGet\Packages\BrechtSanders.WinLibs.POSIX.UCRT_Microsoft.Winget.Source_8wekyb3d8bbwe\mingw64\bin\gcc.exe"
REM -----------------------------------------------------------

if not exist "%GCC_PATH%" (
    echo *** gcc not found at: %GCC_PATH%
    echo *** Please edit this file and set GCC_PATH correctly.
    pause
    exit /b 1
)

echo ============================================================
echo  gcc syntax check
echo ============================================================
echo.
echo === gcc version ===
"%GCC_PATH%" --version
echo.

if not exist "output" (
    echo *** output/ not found. Generate C code first. ***
    pause
    exit /b 1
)

REM ---- Build include paths from output/ structure ----
set "INC=-I output"
if exist "output\Driver"        set "INC=%INC% -I output\Driver"
if exist "output\Middleware"    set "INC=%INC% -I output\Middleware"
if exist "output\Application"   set "INC=%INC% -I output\Application"
if exist "output\include"       set "INC=%INC% -I output\include"
if exist "output\src"           set "INC=%INC% -I output\src"
if exist "output\common"        set "INC=%INC% -I output\common"

echo === Include paths ===
echo   %INC%
echo.

echo === Syntax check: output\**\*.c ===
echo.

set FAIL=0
set COUNT=0
set FAILED_FILES=

for /r "output" %%f in (*.c) do (
    set /a COUNT+=1
    echo --- %%f
    "%GCC_PATH%" -std=c99 -fsyntax-only -Wall -Wextra %INC% "%%f" 2>&1
    if errorlevel 1 (
        echo *** FAIL: %%f
        set FAIL=1
        set "FAILED_FILES=!FAILED_FILES! %%f"
    ) else (
        echo     OK
    )
)

echo.
echo ============================================================
echo  Files checked: %COUNT%
if "%FAIL%"=="1" (
    echo  RESULT: FAIL
    echo ============================================================
    echo.
    echo Failed files:
    echo   %FAILED_FILES%
    pause
    exit /b 1
) else (
    echo  RESULT: PASS
    echo ============================================================
    pause
    exit /b 0
)