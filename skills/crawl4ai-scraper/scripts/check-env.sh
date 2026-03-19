#!/usr/bin/env bash
# Check Crawl4AI environment readiness.
set -e

echo "=== Crawl4AI Environment Check ==="

# Check Python
if command -v python3 &>/dev/null; then
    echo "[OK] Python: $(python3 --version 2>&1)"
elif command -v python &>/dev/null; then
    echo "[OK] Python: $(python --version 2>&1)"
else
    echo "[FAIL] Python not found. Need Python 3.10+"
    exit 1
fi

# Check crawl4ai CLI
if command -v crwl &>/dev/null; then
    echo "[OK] Crawl4AI CLI available"
else
    echo "[FAIL] Crawl4AI not installed."
    echo "  Fix: pip install -U crawl4ai && crawl4ai-setup"
    exit 1
fi

# Check crawl4ai package
if python3 -c "import crawl4ai" 2>/dev/null || python -c "import crawl4ai" 2>/dev/null; then
    echo "[OK] crawl4ai Python package importable"
else
    echo "[WARN] crawl4ai package not importable (Python API won't work)"
fi

# Check browser
if crawl4ai-doctor 2>&1 | grep -qi "error\|fail"; then
    echo "[WARN] Browser issues detected. Fix: python -m playwright install --with-deps chromium"
else
    echo "[OK] Browser dependencies look good"
fi

echo "=== Done ==="
