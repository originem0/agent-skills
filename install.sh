#!/usr/bin/env bash
# Agent Skills installer for macOS/Linux
# Supports: Claude Code, Codex CLI, OpenClaw
# Respects `platforms` field in SKILL.md frontmatter for per-skill filtering.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$SCRIPT_DIR/skills"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[SKIP]${NC} $1"; }

UNINSTALL=false
if [[ "${1:-}" == "--uninstall" ]]; then
    UNINSTALL=true
fi

# Check if a skill supports the given platform.
# Reads `platforms:` from SKILL.md frontmatter. No field = all platforms.
skill_supports_platform() {
    local skill_dir="$1"
    local platform="$2"
    local skill_file="$skill_dir/SKILL.md"

    if [ ! -f "$skill_file" ]; then
        return 0  # no SKILL.md → allow
    fi

    # Extract platforms line from YAML frontmatter (between --- delimiters)
    local platforms_line
    platforms_line=$(sed -n '/^---$/,/^---$/{ /^platforms:/p }' "$skill_file")

    if [ -z "$platforms_line" ]; then
        return 0  # no platforms field → all platforms
    fi

    if echo "$platforms_line" | grep -q "$platform"; then
        return 0
    fi
    return 1
}

uninstall_skills() {
    local target_dir="$1"
    local tool_name="$2"

    if [ ! -d "$target_dir" ]; then
        warn "$tool_name skills directory not found"
        return
    fi

    for skill_dir in "$SKILLS_DIR"/*/; do
        skill_name="$(basename "$skill_dir")"
        target="$target_dir/$skill_name"

        if [ -L "$target" ]; then
            rm "$target"
            echo "  Removed: $skill_name"
        elif [ -d "$target" ]; then
            echo "  $skill_name: not a symlink, skipping (remove manually if needed)"
        fi
    done
    info "$tool_name skills uninstalled"
}

install_skills() {
    local target_dir="$1"
    local tool_name="$2"
    local platform="$3"

    mkdir -p "$target_dir"
    for skill_dir in "$SKILLS_DIR"/*/; do
        skill_name="$(basename "$skill_dir")"

        if ! skill_supports_platform "$skill_dir" "$platform"; then
            echo "  $skill_name: not supported on $tool_name, skipping"
            continue
        fi

        target="$target_dir/$skill_name"

        if [ -L "$target" ]; then
            existing_source="$(readlink "$target")"
            if [ "$existing_source" = "$skill_dir" ]; then
                echo "  $skill_name: already linked (up to date)"
                continue
            fi
            echo "  $skill_name: updating symlink (was -> $existing_source)"
            rm "$target"
        elif [ -d "$target" ]; then
            echo "  $skill_name: real directory exists, skipping (remove manually to reinstall)"
            continue
        fi

        ln -s "$skill_dir" "$target"
        echo "  $skill_name -> $target"
    done
    info "$tool_name skills installed"
}

echo ""
echo "=== PERO Skills Installer ==="
echo ""

if $UNINSTALL; then
    echo "Mode: uninstall"
    echo ""
fi

# Claude Code
CLAUDE_SKILLS="$HOME/.claude/skills"
if command -v claude &>/dev/null || [ -d "$HOME/.claude" ]; then
    echo "Claude Code detected"
    if $UNINSTALL; then
        uninstall_skills "$CLAUDE_SKILLS" "Claude Code"
    else
        install_skills "$CLAUDE_SKILLS" "Claude Code" "claude-code"

        for old in "$HOME/.claude/commands/PEROlearn.md" "$HOME/.claude/commands/PEROfeynman.md"; do
            if [ -f "$old" ]; then
                echo "  Found old command format: $(basename "$old")"
                read -p "  Remove? [y/N] " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    rm "$old"
                    echo "  Removed: $(basename "$old")"
                fi
            fi
        done
    fi
else
    warn "Claude Code not found, skipping"
fi

echo ""

# Codex CLI
CODEX_SKILLS="$HOME/.codex/skills"
if command -v codex &>/dev/null || [ -d "$HOME/.codex" ]; then
    echo "Codex CLI detected"
    if $UNINSTALL; then
        uninstall_skills "$CODEX_SKILLS" "Codex CLI"
    else
        install_skills "$CODEX_SKILLS" "Codex CLI" "codex"
    fi
else
    warn "Codex CLI not found, skipping"
fi

echo ""

# OpenClaw
OPENCLAW_SKILLS="$HOME/.openclaw/skills"
if command -v openclaw &>/dev/null || [ -d "$HOME/.openclaw" ]; then
    echo "OpenClaw detected"
    if $UNINSTALL; then
        uninstall_skills "$OPENCLAW_SKILLS" "OpenClaw"
    else
        install_skills "$OPENCLAW_SKILLS" "OpenClaw" "openclaw"
    fi
else
    warn "OpenClaw not found, skipping"
fi

echo ""
if $UNINSTALL; then
    info "Uninstall complete"
else
    info "Done. Skills available: /PEROlearn, /PEROfeynman"
    echo ""
    echo "Usage:"
    echo "  1. cd to your learning project directory"
    echo "  2. Run /PEROlearn to start or continue learning"
    echo "  3. Run /PEROfeynman to test your understanding"
    echo ""
    echo "To uninstall: ./install.sh --uninstall"
fi
echo ""
