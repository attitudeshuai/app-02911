# Rust Cargo DOS Commander 🦀

一个模拟 DOS 命令行界面的桌面应用程序，专为 Rust/Cargo 项目管理而设计。
支持项目创建、编译、运行，以及常用 DOS 命令。

## How to Run

### 环境要求

- Python 3.10+
- Tkinter（macOS/Linux 通常自带，Windows 自带）
- Rust & Cargo（用于实际执行 Rust 命令）：https://rustup.rs/

### 一键启动（推荐）

| 平台 | 命令 |
|------|------|
| macOS / Linux | `./start.sh` 或 `bash start.sh` |
| Windows | 双击 `start.bat` 或命令行执行 `start.bat` |
| Windows (Git Bash/WSL) | `./start.sh` |

启动脚本会自动：
- 检测操作系统和 Python 环境
- 验证 tkinter 是否可用
- 安装依赖并启动应用

前期检查
    本项目用的是 Xcode Command Line Tools 自带的 Python 3.9.6，检查 tkinter 和你的 macOS 版本是否兼容。

    用 Homebrew 安装独立的 Python

    brew install python@3.12 python-tk@3.12
    安装完后用这个运行：

    /opt/homebrew/bin/python3.12 main.py
    或者如果你是 Intel Mac：

    /usr/local/bin/python3.12 main.py
    如果没装 Homebrew，先装一下：

    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    装完 Python 后可以设为默认：

    echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
    source ~/.zshrc
    然后直接 python3 main.py 就能用了。

### 脚本启动(推荐)
    平台	                脚本	            使用方式
macOS / Linux	        start.sh	        bash start.sh
Windows	                start.bat	    双击运行 或 命令行执行 start.bat
Windows (Git Bash/WSL)	start.sh	           $_start.sh

### 手动启动

```bash
# 1. 进入项目目录
cd backend

# 2. 安装 Python 依赖
pip3 install -r requirements.txt

# 3. 启动应用
python3 main.py

cd ~/rust_projects  # 或者你项目实际所在的路径
cd backend
/opt/homebrew/bin/python3.12 main.py

```

### Docker 构建验证（可选）

> 注意：本项目是桌面 GUI 应用，Docker 仅用于构建验证和 CI 测试。

```bash
docker-compose up --build -d
```

## Services

| 服务 | 说明 | 端口 |
|------|------|------|
| backend | Cargo DOS Commander (Python/Tkinter GUI) | 9999 (Docker CI) |

## 测试账号

本项目为本地桌面应用，无需登录账号。直接运行即可使用。

## 题目内容

> python开发一个模拟dos命令行.创建rust cargo命令行命令项目创建.编译.运行.带界面程序.

## 功能说明

### 支持的 Cargo 命令

| 命令 | 说明 |
|------|------|
| `cargo new <name>` | 创建新 Rust 项目（支持 --bin / --lib） |
| `cargo build` | 编译当前项目 |
| `cargo run` | 运行当前项目 |
| `cargo test` | 运行测试 |
| `cargo check` | 检查代码错误 |
| `cargo clean` | 清理构建产物 |
| `cargo fmt` | 格式化代码 |
| `cargo clippy` | 代码静态分析 |

### 支持的 DOS 命令

| 命令 | 说明 |
|------|------|
| `dir` / `ls` | 列出目录内容 |
| `cd <path>` | 切换目录 |
| `cls` / `clear` | 清屏 |
| `type` / `cat` | 查看文件内容 |
| `mkdir` / `md` | 创建目录 |
| `rmdir` / `rd` | 删除目录 |
| `del` / `rm` | 删除文件 |
| `tree` | 显示目录树 |
| `echo` | 输出文本 |
| `ver` | 显示版本信息 |
| `help` | 显示帮助 |
| `exit` | 退出程序 |

### GUI 功能

- DOS 风格黑底绿字终端界面
- 工具栏快捷按钮（新建/编译/运行/测试/检查/清理）
- 新建项目对话框（支持选择 bin/lib 类型）
- 命令历史（上下键浏览）
- 状态栏显示当前目录和 Rust 版本
- 彩色输出（错误红色、警告黄色、信息青色、成功绿色）
- 异步命令执行（编译/运行时不阻塞界面）
- Ctrl+C 取消运行中的进程

## 使用指南

### 命令输入方式

1. **终端直接输入** - 在 DOS 风格的终端界面中直接输入命令，按 Enter 执行
2. **工具栏快捷按钮** - 界面顶部有快捷按钮可以一键执行常用操作（新建/编译/运行/测试/检查/清理）

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| Tab | 命令自动补全 |
| ↑/↓ | 浏览命令历史 |
| Ctrl+C | 取消运行/清除输入 |
| Ctrl+L | 清屏 |
| Ctrl+T | 新建终端标签 |
| Ctrl+B | 切换文件浏览器 |

## 常见问题

### macOS: "macOS 26 (2602) or later required" 错误

如果运行时出现类似以下错误：

```
macOS 26 (2602) or later required, have instead 16 (1602) !
zsh: abort      python3 main.py
```

这是因为系统自带的 Python（Xcode Command Line Tools）的 tkinter 版本与 macOS 不兼容。

**解决方案：使用 Homebrew 安装 Python**

```bash
# 1. 安装 Homebrew（如果没有）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. 安装 Python 和 tkinter
brew install python@3.12 python-tk@3.12

# 3. 使用 Homebrew 的 Python 运行
/opt/homebrew/bin/python3.12 main.py   # Apple Silicon Mac
# 或
/usr/local/bin/python3.12 main.py      # Intel Mac
```

**设为默认 Python（可选）：**

```bash
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
# 之后直接用 python3 main.py 即可
```

**检查当前 Python 来源：**

```bash
python3 -c "import sys; print(sys.executable); print(sys.version)"
```

如果输出包含 `/Library/Developer/CommandLineTools/`，说明用的是系统自带版本，需要切换到 Homebrew 版本。

### 'cargo' is not recognized as an internal or external command

这个错误说明系统还没有安装 Rust 和 Cargo。请按以下步骤安装：

```bash
# 安装 Rust & Cargo
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 安装完成后，重启终端或运行
source ~/.cargo/env

# 验证安装
cargo --version
```

看到版本号输出就说明安装成功了，之后再启动应用就能正常使用 `cargo` 命令。
