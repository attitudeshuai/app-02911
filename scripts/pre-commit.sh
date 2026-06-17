#!/usr/bin/env bash
#
# Pre-commit hook - runs basic checks before commit
# Install: cp scripts/pre-commit.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get repo root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"

cd "$BACKEND_DIR"

echo -e "${YELLOW}Running pre-commit checks...${NC}"
echo ""

PASS=0
FAIL=0

run_check() {
    local name="$1"
    shift
    echo -n "  [$name] "
    if "$@" > /tmp/precommit_$$.log 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}FAIL${NC}"
        FAIL=$((FAIL + 1))
        echo ""
        echo "  --- Output ---"
        sed 's/^/    /' /tmp/precommit_$$.log
        echo "  --------------"
        echo ""
    fi
    rm -f /tmp/precommit_$$.log
}

# Check Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${RED}Python not found, skipping pre-commit checks${NC}"
    exit 0
fi

PYTHON_CMD="python3"
command -v python3 &> /dev/null || PYTHON_CMD="python"

# Check 1: Imports
run_check "imports" $PYTHON_CMD main.py --check-imports

# Check 2: Self-test (core logic, no GUI)
run_check "selftest" $PYTHON_CMD main.py --selftest

# Check 3: Unit tests
if $PYTHON_CMD -m pytest --version > /dev/null 2>&1; then
    run_check "unit tests" $PYTHON_CMD -m pytest tests/test_commands.py -q
else
    echo "  [unit tests] ${YELLOW}SKIP${NC} (pytest not installed)"
fi

# Summary
echo ""
echo "========================================"
echo -e "  ${GREEN}$PASS passed${NC}, ${RED}$FAIL failed${NC}"
echo "========================================"

if [ "$FAIL" -gt 0 ]; then
    echo ""
    echo -e "${RED}Commit blocked: fix the issues above first${NC}"
    echo -e "${YELLOW}Tip: You can skip with git commit --no-verify${NC}"
    exit 1
fi

exit 0
