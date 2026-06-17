#!/bin/bash
# Docker entrypoint for Cargo Commander test image
# Supports different test modes: smoke, test, all

set -e

MODE="${1:-all}"

echo "========================================"
echo "  Cargo Commander - Docker CI"
echo "  Mode: $MODE"
echo "========================================"
echo ""

cd /app

run_smoke() {
    echo "[Smoke Test]"
    python smoke_test.py --verbose
    echo ""
}

run_unit() {
    echo "[Unit Tests]"
    python -m pytest tests/ -v --tb=short
    echo ""
}

run_coverage() {
    echo "[Coverage Report]"
    python -m pytest tests/ --cov=app --cov-report=term-missing
    echo ""
}

case "$MODE" in
    smoke)
        run_smoke
        ;;
    test)
        run_unit
        ;;
    all)
        run_smoke
        run_unit
        run_coverage
        ;;
    *)
        echo "Unknown mode: $MODE"
        echo "Usage: docker run --rm <image> [smoke|test|all]"
        exit 1
        ;;
esac

echo "========================================"
echo "  All checks passed ✓"
echo "========================================"
