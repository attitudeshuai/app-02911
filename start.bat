@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion

:: Rust Cargo DOS Commander - Windows 启动脚本

echo ========================================
echo   Rust Cargo DOS Commander
echo ========================================

:: 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
set "BACKEND_DIR=%SCRIPT_DIR%backend"

:: 检查 Python
echo [INFO] 检查 Python...
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    where python3 >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] 未找到 Python，请先安装 Python 3.8+
        pause
        exit /b 1
    )
    set "PYTHON_CMD=python3"
) else (
    set "PYTHON_CMD=python"
)

:: 显示 Python 版本
for /f "tokens=*" %%i in ('%PYTHON_CMD% --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [INFO] %PYTHON_VERSION%

:: 检查 tkinter
echo [CHECK] 检查 tkinter...
%PYTHON_CMD% -c "import tkinter" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] tkinter 未安装
    echo [TIP] 请重新安装 Python 并勾选 tcl/tk 选项
    pause
    exit /b 1
)
echo [OK] tkinter 已安装

:: 安装依赖
echo [INSTALL] 检查并安装依赖...
if exist "%BACKEND_DIR%\requirements.txt" (
    %PYTHON_CMD% -m pip install -q -r "%BACKEND_DIR%\requirements.txt" >nul 2>&1
)

:: 启动应用
echo [START] 启动应用...
echo.
cd /d "%BACKEND_DIR%"
%PYTHON_CMD% main.py

endlocal
