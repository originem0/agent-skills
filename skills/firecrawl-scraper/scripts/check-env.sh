#!/usr/bin/env bash
# Check Firecrawl CLI environment readiness.
set -e

echo "=== Firecrawl Environment Check ==="

# Check Node.js
if command -v node &>/dev/null; then
    NODE_VER=$(node --version)
    echo "[OK] Node.js: $NODE_VER"
    # Check minimum version (20.6+)
    MAJOR=$(echo "$NODE_VER" | sed 's/v//' | cut -d. -f1)
    if [ "$MAJOR" -lt 20 ]; then
        echo "[WARN] Node.js 20.6+ recommended, current: $NODE_VER"
    fi
else
    echo "[FAIL] Node.js not found. Need Node.js 20.6+"
    exit 1
fi

# Check firecrawl CLI
if command -v firecrawl &>/dev/null; then
    echo "[OK] Firecrawl CLI: $(firecrawl --version 2>&1 || echo 'installed')"
else
    echo "[FAIL] Firecrawl CLI not installed."
    echo "  Fix: npm install -g firecrawl-cli"
    exit 1
fi

# Check auth
if firecrawl whoami &>/dev/null; then
    echo "[OK] Firecrawl authenticated"
else
    echo "[FAIL] Not authenticated."
    echo "  Fix: firecrawl login --browser"
    echo "  Or:  firecrawl login --api-key fc-YOUR_API_KEY"
    exit 1
fi

echo "=== Done ==="
