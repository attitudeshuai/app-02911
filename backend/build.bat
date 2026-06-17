@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion

:: ============================================
::  Cargo Commander - Windows Build Script
:: ============================================
::  Builds a standalone Windows executable using PyInstaller.
::  Output: dist\CargoCommander.exe
::
::  Features:
::    - Validates build environment versions before building
::    - Runs smoke test on the BUILT executable (not just source)
::    - Verifies the exe actually starts and core commands work
:: ============================================

echo.
echo ========================================
echo   Cargo Commander - Windows Build
echo ========================================
echo.

:: Get script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: Check Python
echo [INFO] Checking Python...
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    where python3 >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Python not found. Please install Python 3.12.10
        pause
        exit /b 1
    )
    set "PYTHON_CMD=python3"
) else (
    set "PYTHON_CMD=python"
)

for /f "tokens=*" %%i in ('%PYTHON_CMD% --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [INFO] %PYTHON_VERSION%

:: Step 1: Validate build environment
echo.
echo [CHECK] Validating build environment...
%PYTHON_CMD% validate_build_env.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Build environment validation failed.
    echo [TIP]   Run: pip install -r build-requirements.txt
    pause
    exit /b 1
)
echo [OK] Environment validated

:: Step 2: Install build dependencies from locked versions
echo.
echo [INSTALL] Installing locked build dependencies...
%PYTHON_CMD% -m pip install --no-deps -r build-requirements.txt >nul 2>&1
if %ERRORLEVEL% neq 0 (
    %PYTHON_CMD% -m pip install -r build-requirements.txt
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
)
echo [OK] Dependencies installed

:: Step 3: Run source smoke test first (catch issues early)
echo.
echo [TEST] Running source smoke test...
%PYTHON_CMD% main.py --smoke-test
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Source smoke test failed - fix before building
    pause
    exit /b 1
)
echo [OK] Source smoke test passed

:: Step 4: Clean previous build
echo.
echo [CLEAN] Cleaning previous build artifacts...
if exist "build" rmdir /s /q build 2>nul
if exist "dist" rmdir /s /q dist 2>nul
echo [OK] Cleaned

:: Step 5: Build
echo.
echo [BUILD] Building executable (this may take a minute)...
echo.
%PYTHON_CMD% -m PyInstaller --clean --noconfirm cargo_commander.spec
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)
echo.
echo [OK] Build completed

:: Step 6: Verify the executable exists
echo.
echo [VERIFY] Checking output...
if exist "dist\CargoCommander.exe" (
    for %%I in ("dist\CargoCommander.exe") do set SIZE=%%~zI
    set /a SIZE_MB=!SIZE! / 1048576
    echo [OK] Executable: dist\CargoCommander.exe (!SIZE_MB! MB)
) else (
    echo [ERROR] Executable not found at dist\CargoCommander.exe
    pause
    exit /b 1
)

:: Step 7: RUN SMOKE TEST ON THE BUILT EXECUTABLE
:: This is the real test - does the packaged app actually work?
echo.
echo [TEST] Running smoke test on BUILT executable...
echo        (verifying the packaged app can start and run commands)
echo.
dist\CargoCommander.exe --smoke-test
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] BUILT EXECUTABLE smoke test FAILED!
    echo         The packaged app does not work correctly.
    pause
    exit /b 1
)
echo.
echo [OK] Built executable smoke test PASSED ✓

:: Step 8: Verify --version works too
echo [TEST] Verifying --version flag...
for /f "delims=" %%i in ('dist\CargoCommander.exe --version 2^>^&1') do set VER_OUTPUT=%%i
if "!VER_OUTPUT!"=="" (
    echo [WARN] --version produced no output
) else (
    echo [OK] Version output: !VER_OUTPUT!
)

echo.
echo ========================================
echo   Build Complete & Verified! ✓
echo ========================================
echo.
echo   Output: dist\CargoCommander.exe
echo.
echo   Verify: dist\CargoCommander.exe --smoke-test
echo   Run:    dist\CargoCommander.exe
echo.
pause
endlocal
