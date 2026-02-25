#!/usr/bin/env bash
# PERO Skills installer for macOS/Linux
# Supports: Claude Code, Codex CLI, OpenClaw
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$SCRIPT_DIR/skills"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[SKIP]${NC} $1"; }
err()   { echo -e "${RED}[ERR]${NC} $1"; }

install_skills() {
    local target_dir="$1"
    local tool_name="$2"

    mkdir -p "$target_dir"
    for skill_dir in "$SKILLS_DIR"/*/; do
        skill_name="$(basename "$skill_dir")"
        target="$target_dir/$skill_name"

        if [ -L "$target" ]; then
            rm "$target"
        fi

        if [ -d "$target" ]; then
            echo "  $skill_name: already exists (not a symlink), skipping. Remove manually to reinstall."
            continue
        fi

        ln -s "$skill_dir" "$target"
        echo "  $skill_name -> $target"
    done
    info "$tool_name skills installed via symlink"
}

echo ""
echo "=== PERO Skills Installer ==="
echo ""

# Claude Code
CLAUDE_SKILLS="$HOME/.claude/skills"
if command -v claude &>/dev/null || [ -d "$HOME/.claude" ]; then
    echo "Claude Code detected"
    install_skills "$CLAUDE_SKILLS" "Claude Code"

    # Clean up old commands format if present
    for old in "$HOME/.claude/commands/PEROlearn.md" "$HOME/.claude/commands/PEROfeynman.md"; do
        if [ -f "$old" ]; then
            rm "$old"
            echo "  Removed old command: $(basename "$old")"
        fi
    done
else
    warn "Claude Code not found, skipping"
fi

echo ""

# Codex CLI
CODEX_SKILLS="$HOME/.codex/skills"
if command -v codex &>/dev/null || [ -d "$HOME/.codex" ]; then
    echo "Codex CLI detected"
    install_skills "$CODEX_SKILLS" "Codex CLI"
else
    warn "Codex CLI not found, skipping"
fi

echo ""

# OpenClaw
OPENCLAW_SKILLS="$HOME/.openclaw/skills"
if command -v openclaw &>/dev/null || [ -d "$HOME/.openclaw" ]; then
    echo "OpenClaw detected"
    install_skills "$OPENCLAW_SKILLS" "OpenClaw"
else
    warn "OpenClaw not found, skipping"
fi

echo ""
info "Done. Skills available: /PEROlearn, /PEROfeynman"
echo ""
echo "Usage:"
echo "  1. cd to your learning project directory"
echo "  2. Run /PEROlearn to start or continue learning"
echo "  3. Run /PEROfeynman to test your understanding"
echo ""
