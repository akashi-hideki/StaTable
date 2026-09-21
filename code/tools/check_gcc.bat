@echo off
setlocal enableextensions
cd /d "%~dp0"

REM ============================================================
REM  gcc syntax check for generated C code
REM  Location: code/tools/check_gcc.bat
REM  Target:   code/output/ (by_layer structure is expected)
REM ============================================================

REM ---- CONFIG: gcc.exe path ----
REM Priority: 1) environment variable GCC_PATH
REM           2) `where gcc` in PATH
REM           3) manual fallback below
if not defined GCC_PATH (
    for /f "delims=" %%i in ('where gcc 2^>nul') do (
        set "GCC_PATH=%%i"
        goto :gcc_found
    )
    REM Fallback (edit for your environment)
    set "GCC_PATH=C:\msys64\ucrt64\bin\gcc.exe"
)
:gcc_found
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

if not exist "..\output" (
    echo *** code/output/ not found. Generate C code first. ***
    pause
    exit /b 1
)

REM ---- Build include paths from code/output/ structure ----
set "INC=-I ..\output"
if exist "..\output\Driver"        set "INC=%INC% -I ..\output\Driver"
if exist "..\output\Middleware"    set "INC=%INC% -I ..\output\Middleware"
if exist "..\output\Application"   set "INC=%INC% -I ..\output\Application"
if exist "..\output\include"       set "INC=%INC% -I ..\output\include"
if exist "..\output\src"           set "INC=%INC% -I ..\output\src"
if exist "..\output\common"        set "INC=%INC% -I ..\output\common"

echo === Include paths ===
echo   %INC%
echo.

echo === Syntax check: code\output\**\*.c ===
echo.

set FAIL=0
set COUNT=0
set FAILED_FILES=

for /r "..\output" %%f in (*.c) do (
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