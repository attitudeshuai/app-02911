@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion

:: Rust Cargo DOS Commander - Windows 构建脚本
:: 输出: dist\ 目录下的可执行文件

echo ========================================
echo   Cargo Commander 构建脚本 (Windows)
echo ========================================
echo.

set "SCRIPT_DIR=%~dp0"
set "BACKEND_DIR=%SCRIPT_DIR%backend"
set "DIST_DIR=%SCRIPT_DIR%dist"
set "BUILD_DIR=%SCRIPT_DIR%build"

set "APP_NAME=cargo-commander"

:: 检查 Python
echo [INFO] 检查 Python...
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    where python3 >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] 未找到 Python
        pause
        exit /b 1
    )
    set "PYTHON_CMD=python3"
) else (
    set "PYTHON_CMD=python"
)

for /f "tokens=*" %%i in ('%PYTHON_CMD% --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [INFO] %PYTHON_VERSION%
echo.

:: 清理旧构建
echo [CLEAN] 清理旧的构建产物...
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
if exist "%BACKEND_DIR%\build" rmdir /s /q "%BACKEND_DIR%\build"
if exist "%BACKEND_DIR%\dist" rmdir /s /q "%BACKEND_DIR%\dist"
echo [OK] 清理完成
echo.

:: 安装构建依赖
echo [INSTALL] 安装构建依赖...
cd /d "%BACKEND_DIR%"
%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install pyinstaller
%PYTHON_CMD% -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [ERROR] 依赖安装失败
    pause
    exit /b 1
)
echo [OK] 构建依赖安装完成
echo.

:: 读取版本号（用 Python 解析，避免引号/编码问题）
echo [INFO] 读取版本号...
for /f "delims=" %%v in ('%PYTHON_CMD% -c "import sys; sys.path.insert(0, r'%BACKEND_DIR%'); from app import __version__; print(__version__)"') do (
    set "APP_VERSION=%%v"
)
if "%APP_VERSION%"=="" (
    echo [WARN] 读取版本号失败，使用默认值 0.0.0
    set "APP_VERSION=0.0.0"
)
echo [INFO] 应用版本: %APP_VERSION%
echo.

:: 构建应用
echo [BUILD] 开始构建...
cd /d "%BACKEND_DIR%"
pyinstaller --clean --noconfirm --onefile --windowed ^
    --name %APP_NAME% ^
    --hidden-import=tkinter ^
    --hidden-import=PIL ^
    main.py

if %ERRORLEVEL% neq 0 (
    echo [ERROR] 构建失败
    pause
    exit /b 1
)

:: 复制到输出目录
if not exist "%DIST_DIR%" mkdir "%DIST_DIR%"
copy /y "%BACKEND_DIR%\dist\%APP_NAME%.exe" "%DIST_DIR%\" >nul

echo [OK] 构建成功!
echo [OK] 输出目录: %DIST_DIR%
echo.

:: 验证构建
echo [VERIFY] 验证构建产物...
if exist "%DIST_DIR%\%APP_NAME%.exe" (
    echo [OK] 可执行文件存在
    for %%A in ("%DIST_DIR%\%APP_NAME%.exe") do (
        set "SIZE=%%~zA"
        set /a "SIZE_MB=SIZE/1024/1024"
    )
    echo [INFO] 文件大小: !SIZE_MB! MB
) else (
    echo [ERROR] 可执行文件不存在
    pause
    exit /b 1
)
echo [OK] 构建验证通过
echo.

:: 创建压缩包
echo [PACKAGE] 创建发布包...
set "ARCHIVE_NAME=%APP_NAME%-%APP_VERSION%-windows.zip"
cd /d "%DIST_DIR%"
powershell -Command "Compress-Archive -Path '%APP_NAME%.exe' -DestinationPath '%ARCHIVE_NAME%' -Force"
if %ERRORLEVEL% equ 0 (
    echo [OK] 发布包已创建: %DIST_DIR%\%ARCHIVE_NAME%
)
echo.

echo ========================================
echo   构建完成!
echo ========================================
echo.
pause
endlocal
