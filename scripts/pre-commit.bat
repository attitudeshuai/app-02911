@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion

:: Pre-commit hook - runs basic checks before commit
:: Install: copy scripts\pre-commit.bat .git\hooks\pre-commit.bat

echo Running pre-commit checks...
echo.

set "PASS=0"
set "FAIL=0"

set "REPO_ROOT=%~dp0.."
set "BACKEND_DIR=%REPO_ROOT%\backend"

cd /d "%BACKEND_DIR%"

:: Find Python
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PYTHON_CMD=python"
) else (
    where python3 >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        set "PYTHON_CMD=python3"
    ) else (
        echo Python not found, skipping pre-commit checks
        exit /b 0
    )
)

:: Check 1: Imports
echo [1/3] Checking imports...
%PYTHON_CMD% main.py --check-imports >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo   [PASS] imports
    set /a PASS+=1
) else (
    echo   [FAIL] imports
    set /a FAIL+=1
    %PYTHON_CMD% main.py --check-imports
    echo.
)

:: Check 2: Self-test
echo [2/3] Running self-test...
%PYTHON_CMD% main.py --selftest >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo   [PASS] selftest
    set /a PASS+=1
) else (
    echo   [FAIL] selftest
    set /a FAIL+=1
    %PYTHON_CMD% main.py --selftest
    echo.
)

:: Check 3: Unit tests
echo [3/3] Running unit tests...
%PYTHON_CMD% -m pytest --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    %PYTHON_CMD% -m pytest tests/test_commands.py -q >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        echo   [PASS] unit tests
        set /a PASS+=1
    ) else (
        echo   [FAIL] unit tests
        set /a FAIL+=1
        %PYTHON_CMD% -m pytest tests/test_commands.py -q
        echo.
    )
) else (
    echo   [SKIP] unit tests (pytest not installed)
)

:: Summary
echo.
echo ========================================
echo   %PASS% passed, %FAIL% failed
echo ========================================

if %FAIL% gtr 0 (
    echo.
    echo Commit blocked: fix the issues above first
    echo Tip: You can skip with git commit --no-verify
    exit /b 1
)

exit /b 0
endlocal
