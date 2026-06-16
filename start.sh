#!/usr/bin/env bash
#
# Rust Cargo DOS Commander - 跨平台一键启动脚本
# 支持: Windows (Git Bash/WSL), Linux, macOS
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Rust Cargo DOS Commander${NC}"
echo -e "${BLUE}========================================${NC}"

# 检测操作系统
detect_os() {
    case "$(uname -s)" in
        Linux*)     OS="Linux";;
        Darwin*)    OS="macOS";;
        CYGWIN*|MINGW*|MSYS*) OS="Windows";;
        *)          OS="Unknown";;
    esac
    echo -e "${GREEN}[INFO]${NC} 检测到操作系统: $OS"
}

# 检查并安装 Homebrew (macOS)
ensure_homebrew() {
    if ! command -v brew &> /dev/null; then
        echo -e "${YELLOW}[INSTALL]${NC} 未检测到 Homebrew，正在自动安装..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # 添加 Homebrew 到 PATH
        if [ -f "/opt/homebrew/bin/brew" ]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        elif [ -f "/usr/local/bin/brew" ]; then
            eval "$(/usr/local/bin/brew shellenv)"
        fi
        
        if command -v brew &> /dev/null; then
            echo -e "${GREEN}[OK]${NC} Homebrew 安装成功"
        else
            echo -e "${RED}[ERROR]${NC} Homebrew 安装失败，请手动安装: https://brew.sh"
            exit 1
        fi
    else
        echo -e "${GREEN}[OK]${NC} Homebrew 已安装"
    fi
}

# 安装 Homebrew Python with Tcl/Tk (macOS)
install_homebrew_python() {
    echo -e "${YELLOW}[INSTALL]${NC} 正在安装 Homebrew Python (带 Tcl/Tk 支持)..."
    
    # 安装 python-tk (包含完整的 Tcl/Tk 支持)
    brew install python-tk@3.11 2>/dev/null || brew upgrade python-tk@3.11 2>/dev/null || true
    
    # 确定安装路径
    if [ -x "/opt/homebrew/bin/python3.11" ]; then
        PYTHON_CMD="/opt/homebrew/bin/python3.11"
    elif [ -x "/usr/local/bin/python3.11" ]; then
        PYTHON_CMD="/usr/local/bin/python3.11"
    elif [ -x "/opt/homebrew/bin/python3" ]; then
        PYTHON_CMD="/opt/homebrew/bin/python3"
    elif [ -x "/usr/local/bin/python3" ]; then
        PYTHON_CMD="/usr/local/bin/python3"
    else
        echo -e "${RED}[ERROR]${NC} Python 安装失败"
        exit 1
    fi
    
    echo -e "${GREEN}[OK]${NC} Homebrew Python 安装成功"
}

# 检查 Tcl/Tk 版本是否兼容
check_tcltk_compatible() {
    # 尝试创建一个简单的 Tk 窗口来测试兼容性
    $PYTHON_CMD -c "
import tkinter as tk
try:
    root = tk.Tk()
    root.withdraw()
    root.destroy()
    exit(0)
except Exception:
    exit(1)
" 2>/dev/null
    return $?
}

# 检查 Python
check_python() {
    if [ "$OS" = "macOS" ]; then
        # 首先检查 Homebrew Python
        if [ -x "/opt/homebrew/bin/python3.11" ]; then
            PYTHON_CMD="/opt/homebrew/bin/python3.11"
            echo -e "${GREEN}[INFO]${NC} 使用 Homebrew Python 3.11 (Apple Silicon)"
        elif [ -x "/usr/local/bin/python3.11" ]; then
            PYTHON_CMD="/usr/local/bin/python3.11"
            echo -e "${GREEN}[INFO]${NC} 使用 Homebrew Python 3.11 (Intel)"
        elif [ -x "/opt/homebrew/bin/python3" ]; then
            PYTHON_CMD="/opt/homebrew/bin/python3"
            echo -e "${GREEN}[INFO]${NC} 使用 Homebrew Python (Apple Silicon)"
        elif [ -x "/usr/local/bin/python3" ]; then
            PYTHON_CMD="/usr/local/bin/python3"
            echo -e "${GREEN}[INFO]${NC} 使用 Homebrew Python (Intel)"
        elif command -v python3 &> /dev/null; then
            PYTHON_CMD="python3"
            echo -e "${YELLOW}[WARN]${NC} 检测到系统 Python，正在检查 Tcl/Tk 兼容性..."
            
            # 测试 Tcl/Tk 是否兼容
            if ! check_tcltk_compatible; then
                echo -e "${YELLOW}[WARN]${NC} 系统 Python 的 Tcl/Tk 版本不兼容"
                echo -e "${YELLOW}[INFO]${NC} 将自动安装兼容的 Homebrew Python..."
                echo ""
                
                # 自动安装 Homebrew 和 Python
                ensure_homebrew
                install_homebrew_python
            fi
        else
            echo -e "${YELLOW}[INFO]${NC} 未找到 Python，将自动安装..."
            ensure_homebrew
            install_homebrew_python
        fi
    else
        if command -v python3 &> /dev/null; then
            PYTHON_CMD="python3"
        elif command -v python &> /dev/null; then
            PYTHON_CMD="python"
        else
            echo -e "${RED}[ERROR]${NC} 未找到 Python，请先安装 Python 3.8+"
            exit 1
        fi
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    echo -e "${GREEN}[INFO]${NC} Python 版本: $PYTHON_VERSION"
}

# 检查 tkinter
check_tkinter() {
    echo -e "${YELLOW}[CHECK]${NC} 检查 tkinter..."
    if $PYTHON_CMD -c "import tkinter" 2>/dev/null; then
        echo -e "${GREEN}[OK]${NC} tkinter 已安装"
    else
        echo -e "${RED}[ERROR]${NC} tkinter 未安装"
        case "$OS" in
            Linux)
                echo -e "${YELLOW}[TIP]${NC} 请运行: sudo apt-get install python3-tk (Debian/Ubuntu)"
                echo -e "${YELLOW}[TIP]${NC} 或: sudo dnf install python3-tkinter (Fedora)"
                ;;
            macOS)
                echo -e "${YELLOW}[INFO]${NC} 正在自动安装..."
                ensure_homebrew
                install_homebrew_python
                ;;
            Windows)
                echo -e "${YELLOW}[TIP]${NC} 请重新安装 Python 并勾选 tcl/tk 选项"
                ;;
        esac
    fi
}

# 安装依赖
install_deps() {
    echo -e "${YELLOW}[INSTALL]${NC} 检查并安装依赖..."
    if [ -f "$BACKEND_DIR/requirements.txt" ]; then
        $PYTHON_CMD -m pip install -q -r "$BACKEND_DIR/requirements.txt" 2>/dev/null || {
            echo -e "${YELLOW}[WARN]${NC} 依赖安装失败，尝试继续运行..."
        }
    fi
}

# 启动应用
start_app() {
    echo -e "${GREEN}[START]${NC} 启动应用..."
    echo ""
    cd "$BACKEND_DIR"
    $PYTHON_CMD main.py
}

# 主流程
main() {
    detect_os
    check_python
    check_tkinter
    install_deps
    start_app
}

main "$@"
