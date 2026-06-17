#!/usr/bin/env bash
# ============================================
#  Cargo Commander - macOS / Linux Build Script
# ============================================
#  Builds a standalone application using PyInstaller.
#  macOS output: dist/Cargo Commander.app
#  Linux output: dist/CargoCommander
#
#  Features:
#    - Validates build environment versions before building
#    - Runs smoke test on the BUILT executable (not just source)
#    - Verifies the app actually starts and core commands work
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "========================================"
echo "  Cargo Commander - Build ($(uname -s))"
echo "========================================"
echo ""

# Detect Python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "[ERROR] Python not found. Please install Python 3.12.10"
    exit 1
fi

PYTHON_VERSION="$($PYTHON_CMD --version 2>&1)"
echo "[INFO] $PYTHON_VERSION"

# Step 1: Validate build environment
echo ""
echo "[CHECK] Validating build environment..."
$PYTHON_CMD validate_build_env.py
if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Build environment validation failed."
    echo "[TIP]   Run: pip install -r build-requirements.txt"
    exit 1
fi
echo "[OK] Environment validated"

# Step 2: Check tkinter
echo ""
echo "[CHECK] Checking tkinter..."
$PYTHON_CMD -c "import tkinter; print('tkinter OK')" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "[ERROR] tkinter not available."
    echo ""
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "On macOS, install via Homebrew:"
        echo "  brew install python-tk@3.12"
    else
        echo "On Linux, install via package manager:"
        echo "  sudo apt-get install python3-tk"
        echo "  sudo yum install python3-tkinter"
    fi
    exit 1
fi
echo "[OK] tkinter available"

# Step 3: Install build dependencies from locked versions
echo ""
echo "[INSTALL] Installing locked build dependencies..."
$PYTHON_CMD -m pip install --no-deps -r build-requirements.txt > /dev/null 2>&1 || \
$PYTHON_CMD -m pip install -r build-requirements.txt
echo "[OK] Dependencies installed"

# Step 4: Run source smoke test first (catch issues early)
echo ""
echo "[TEST] Running source smoke test..."
$PYTHON_CMD main.py --smoke-test
if [ $? -ne 0 ]; then
    echo "[ERROR] Source smoke test failed - fix before building"
    exit 1
fi
echo "[OK] Source smoke test passed"

# Step 5: Clean previous build
echo ""
echo "[CLEAN] Cleaning previous build artifacts..."
rm -rf build dist
echo "[OK] Cleaned"

# Step 6: Build
echo ""
echo "[BUILD] Building application (this may take a minute)..."
echo ""
$PYTHON_CMD -m PyInstaller --clean --noconfirm cargo_commander.spec

echo ""
echo "[OK] Build completed"

# Step 7: Verify the output exists
echo ""
echo "[VERIFY] Checking output..."

EXE_PATH=""
if [[ "$OSTYPE" == "darwin"* ]]; then
    if [ -d "dist/Cargo Commander.app" ]; then
        EXE_PATH="dist/Cargo Commander.app/Contents/MacOS/CargoCommander"
        SIZE=$(du -sh "dist/Cargo Commander.app" | cut -f1)
        echo "[OK] App bundle: dist/Cargo Commander.app ($SIZE)"
    else
        echo "[ERROR] App bundle not found"
        exit 1
    fi
else
    if [ -f "dist/CargoCommander" ]; then
        EXE_PATH="dist/CargoCommander"
        SIZE=$(du -sh "dist/CargoCommander" | cut -f1)
        echo "[OK] Binary: dist/CargoCommander ($SIZE)"
    else
        echo "[ERROR] Binary not found"
        exit 1
    fi
fi

# Step 8: RUN SMOKE TEST ON THE BUILT EXECUTABLE
echo ""
echo "[TEST] Running smoke test on BUILT executable..."
echo "        (verifying the packaged app can start and run commands)"
echo ""

if [ -n "$EXE_PATH" ]; then
    "$EXE_PATH" --smoke-test
    if [ $? -ne 0 ]; then
        echo ""
        echo "[ERROR] BUILT EXECUTABLE smoke test FAILED!"
        echo "         The packaged app does not work correctly."
        exit 1
    fi
    echo ""
    echo "[OK] Built executable smoke test PASSED ✓"

    # Step 9: Verify --version works too
    echo "[TEST] Verifying --version flag..."
    VER_OUTPUT=$("$EXE_PATH" --version 2>&1 || true)
    if [ -z "$VER_OUTPUT" ]; then
        echo "[WARN] --version produced no output"
    else
        echo "[OK] Version output: $VER_OUTPUT"
    fi
fi

echo ""
echo "========================================"
echo "  Build Complete & Verified! ✓"
echo "========================================"
echo ""
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "  Output: dist/Cargo Commander.app"
    echo ""
    echo "  Verify: 'dist/Cargo Commander.app/Contents/MacOS/CargoCommander' --smoke-test"
    echo "  Run:    open 'dist/Cargo Commander.app'"
else
    echo "  Output: dist/CargoCommander"
    echo ""
    echo "  Verify: ./dist/CargoCommander --smoke-test"
    echo "  Run:    ./dist/CargoCommander"
fi
echo ""
