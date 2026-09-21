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