#!/usr/bin/env bash
#
# Rust Cargo DOS Commander - 跨平台构建脚本
# 支持: macOS, Linux
# 输出: dist/ 目录下的可执行文件
#
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
DIST_DIR="$SCRIPT_DIR/dist"
BUILD_DIR="$SCRIPT_DIR/build"

APP_NAME="cargo-commander"
APP_VERSION=$(grep '__version__' "$BACKEND_DIR/app/__init__.py" | head -1 | sed "s/.*['\"]\(.*\)['\"].*/\1/")

detect_os() {
    case "$(uname -s)" in
        Linux*)     OS="linux";;
        Darwin*)    OS="macos";;
        CYGWIN*|MINGW*|MSYS*) OS="windows";;
        *)          OS="unknown";;
    esac
    echo -e "${BLUE}[INFO]${NC} 操作系统: $OS"
}

check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo -e "${RED}[ERROR]${NC} 未找到 Python"
        exit 1
    fi
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    echo -e "${BLUE}[INFO]${NC} Python 版本: $PYTHON_VERSION"
}

install_build_deps() {
    echo -e "${YELLOW}[INSTALL]${NC} 安装构建依赖..."
    cd "$BACKEND_DIR"
    $PYTHON_CMD -m pip install --upgrade pip
    $PYTHON_CMD -m pip install pyinstaller
    $PYTHON_CMD -m pip install -r requirements.txt
    echo -e "${GREEN}[OK]${NC} 构建依赖安装完成"
}

clean_build() {
    echo -e "${YELLOW}[CLEAN]${NC} 清理旧的构建产物..."
    rm -rf "$DIST_DIR"
    rm -rf "$BUILD_DIR"
    rm -rf "$BACKEND_DIR/build"
    rm -rf "$BACKEND_DIR/dist"
    echo -e "${GREEN}[OK]${NC} 清理完成"
}

build_app() {
    echo -e "${YELLOW}[BUILD]${NC} 开始构建 (版本: $APP_VERSION)..."
    cd "$BACKEND_DIR"

    if [ "$OS" = "macos" ]; then
        pyinstaller --clean --noconfirm cargo_commander.spec
        OUTPUT_PATH="$BACKEND_DIR/dist/Cargo Commander.app"
    elif [ "$OS" = "linux" ]; then
        pyinstaller --clean --noconfirm --onefile --windowed \
            --name "$APP_NAME" \
            --hidden-import=tkinter \
            --hidden-import=PIL \
            main.py
        OUTPUT_PATH="$BACKEND_DIR/dist/$APP_NAME"
    else
        echo -e "${RED}[ERROR]${NC} 不支持的操作系统: $OS"
        exit 1
    fi

    if [ ! -e "$OUTPUT_PATH" ]; then
        echo -e "${RED}[ERROR]${NC} 构建失败，未找到输出文件"
        exit 1
    fi

    mkdir -p "$DIST_DIR"
    cp -R "$OUTPUT_PATH" "$DIST_DIR/"

    echo -e "${GREEN}[OK]${NC} 构建成功!"
    echo -e "${GREEN}[OK]${NC} 输出目录: $DIST_DIR"
}

verify_build() {
    echo -e "${YELLOW}[VERIFY]${NC} 验证构建产物..."
    cd "$BACKEND_DIR"

    if [ "$OS" = "macos" ]; then
        APP_BUNDLE="$DIST_DIR/Cargo Commander.app"
        if [ -d "$APP_BUNDLE" ]; then
            echo -e "${GREEN}[OK]${NC} macOS app bundle 存在"
            echo -e "${BLUE}[INFO]${NC} Bundle 大小: $(du -sh "$APP_BUNDLE" | cut -f1)"
        else
            echo -e "${RED}[ERROR]${NC} macOS app bundle 不存在"
            exit 1
        fi
    elif [ "$OS" = "linux" ]; then
        APP_BIN="$DIST_DIR/$APP_NAME"
        if [ -f "$APP_BIN" ]; then
            echo -e "${GREEN}[OK]${NC} Linux 二进制存在"
            echo -e "${BLUE}[INFO]${NC} 文件大小: $(du -sh "$APP_BIN" | cut -f1)"
            chmod +x "$APP_BIN"
        else
            echo -e "${RED}[ERROR]${NC} Linux 二进制不存在"
            exit 1
        fi
    fi

    echo -e "${GREEN}[OK]${NC} 构建验证通过"
}

create_archive() {
    echo -e "${YELLOW}[PACKAGE]${NC} 创建发布包..."
    cd "$DIST_DIR"

    if [ "$OS" = "macos" ]; then
        ARCHIVE_NAME="${APP_NAME}-${APP_VERSION}-macos.tar.gz"
        tar -czf "$ARCHIVE_NAME" "Cargo Commander.app"
    elif [ "$OS" = "linux" ]; then
        ARCHIVE_NAME="${APP_NAME}-${APP_VERSION}-linux.tar.gz"
        tar -czf "$ARCHIVE_NAME" "$APP_NAME"
    fi

    echo -e "${GREEN}[OK]${NC} 发布包已创建: $DIST_DIR/$ARCHIVE_NAME"
    echo -e "${BLUE}[INFO]${NC} 包大小: $(du -sh "$DIST_DIR/$ARCHIVE_NAME" | cut -f1)"
}

main() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Cargo Commander 构建脚本${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    detect_os
    check_python
    clean_build
    install_build_deps
    build_app
    verify_build
    create_archive

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  构建完成!${NC}"
    echo -e "${GREEN}========================================${NC}"
}

main "$@"
