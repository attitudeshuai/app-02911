#!/usr/bin/env bash
#
# Run all tests locally
# Usage: bash scripts/run-tests.sh [--gui] [--unit] [--self] [--all]
#
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

RUN_SELF=true
RUN_UNIT=true
RUN_GUI=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --gui) RUN_GUI=true; shift ;;
        --unit) RUN_SELF=false; RUN_GUI=false; shift ;;
        --self) RUN_UNIT=false; RUN_GUI=false; shift ;;
        --all) RUN_SELF=true; RUN_UNIT=true; RUN_GUI=true; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

cd "$BACKEND_DIR"

# Find Python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}Error: Python not found${NC}"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Cargo Commander Test Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

PASS=0
FAIL=0

run_test() {
    local name="$1"
    shift
    echo -e "${YELLOW}[TEST]${NC} $name"
    if "$@"; then
        echo -e "${GREEN}[PASS]${NC} $name"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}[FAIL]${NC} $name"
        FAIL=$((FAIL + 1))
    fi
    echo ""
}

# 1. Import check (fastest, always run)
run_test "Import check" $PYTHON_CMD main.py --check-imports

# 2. Self-test (core logic, no GUI)
if [ "$RUN_SELF" = true ]; then
    run_test "Self-test (no GUI)" $PYTHON_CMD main.py --selftest
fi

# 3. Unit tests
if [ "$RUN_UNIT" = true ]; then
    if $PYTHON_CMD -m pytest --version > /dev/null 2>&1; then
        run_test "Unit tests" $PYTHON_CMD -m pytest tests/test_commands.py -v
    else
        echo -e "${YELLOW}[SKIP]${NC} Unit tests (pytest not installed)"
        echo ""
    fi
fi

# 4. GUI smoke test
if [ "$RUN_GUI" = true ]; then
    # Check if we have a display (or xvfb)
    if [ -n "$DISPLAY" ] || command -v xvfb-run &> /dev/null; then
        if command -v xvfb-run &> /dev/null && [ -z "$DISPLAY" ]; then
            run_test "GUI smoke test (xvfb)" xvfb-run -a $PYTHON_CMD tests/test_gui_smoke.py
        else
            run_test "GUI smoke test" $PYTHON_CMD tests/test_gui_smoke.py
        fi
    else
        echo -e "${YELLOW}[SKIP]${NC} GUI smoke test (no display and xvfb not found)"
        echo ""
    fi
fi

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "  ${GREEN}$PASS passed${NC}, ${RED}$FAIL failed${NC}"
echo -e "${BLUE}========================================${NC}"

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi

exit 0
