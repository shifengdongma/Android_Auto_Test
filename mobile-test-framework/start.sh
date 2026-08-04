#!/bin/bash
# ============================================================
# LATM - Mobile Test Framework Startup Script (Linux/macOS/Git Bash)
# ============================================================
# Usage:
#   source start.sh
#   bash start.sh
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SCRIPT_DIR"

# --- Set Android SDK environment ---
export ANDROID_HOME="$PROJECT_ROOT"
export ANDROID_SDK_ROOT="$PROJECT_ROOT"
export PATH="$PROJECT_ROOT/platform-tools:$PATH"

echo ""
echo "============================================================"
echo "  LATM - Mobile Test Framework"
echo "  Low-Altitude Airspace Management System"
echo "============================================================"
echo ""
echo "[ENV] ANDROID_HOME=$ANDROID_HOME"
echo ""

# --- Activate virtual environment ---
if [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "[ERROR] .venv not found. Run: python -m venv .venv"
    return 1 2>/dev/null || exit 1
fi
echo "[OK] Virtual environment activated (.venv)"

# --- Python info ---
python --version

# --- ADB check ---
if command -v adb &> /dev/null; then
    echo "[OK] ADB ready"
    adb devices
else
    echo "[WARN] ADB not found"
fi

echo ""
echo "============================================================"
echo "  Common Commands:"
echo "============================================================"
echo ""
echo "  Start server:"
echo "    appium &"
echo ""
echo "  Run tests:"
echo "    python run_tests.py --smoke       # Smoke tests"
echo "    python run_tests.py --report      # All tests + report"
echo "    python run_tests.py --module login # Login module"
echo ""
echo "  Manual test:"
echo "    python -i manual_test.py          # Interactive mode"
echo ""
echo "  Report:"
echo "    allure serve reports/allure-results"
echo ""
echo "============================================================"
echo ""
echo "  Virtual env is active. Run commands directly."
echo "  Type 'deactivate' to exit."
echo ""
