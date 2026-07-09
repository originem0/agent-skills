#!/usr/bin/env bash
# Agent Skills installer for macOS/Linux
# Supports: Claude Code, Codex CLI, OpenClaw
# Respects the `metadata.platforms` field in SKILL.md frontmatter
# (docs/skill-authoring.md) for per-skill filtering.
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
# Reads `metadata.platforms` (space-separated string) from SKILL.md frontmatter.
# Per docs/skill-authoring.md §1 the key lives under `metadata:`, so the scan is
# anchored to that block: only an indented `platforms:` line after a top-level
# `metadata:` line (and before the next top-level key / frontmatter end) counts.
# Anchoring matters because folded `description: >` blocks produce identically
# indented lines — a description mentioning "platforms: ..." must not shadow the
# real config. No field = all platforms. Top-level `platforms:` is the retired
# format and is deliberately ignored. An empty value denies all platforms
# (misconfiguration → conservative).
skill_supports_platform() {
    local skill_dir="$1"
    local platform="$2"
    local skill_file="$skill_dir/SKILL.md"

    if [ ! -f "$skill_file" ]; then
        return 0  # no SKILL.md → allow
    fi

    local platforms_line
    platforms_line=$(awk '
        /^---$/ { fm++; if (fm == 2) exit; next }
        fm != 1 { next }
        /^metadata:[[:space:]]*$/ { in_meta = 1; next }
        /^[^[:space:]]/ { in_meta = 0 }
        in_meta && /^[[:space:]]+platforms:/ { print; exit }
    ' "$skill_file")

    if [ -z "$platforms_line" ]; then
        return 0  # no metadata.platforms field → all platforms
    fi

    # Parse the value and compare exactly (-x whole line, -F literal) —
    # substring matching would break with prefix-overlapping platform names
    # (e.g. "code" vs "claude-code")
    if echo "$platforms_line" | sed 's/^[[:space:]]*platforms:[[:space:]]*//' | tr -d '"' | tr ' ' '\n' | grep -qxF "$platform"; then
        return 0
    fi
    return 1
}

# No platform filtering here on purpose: remove any link we own, so links
# left behind by an older `platforms` config also get cleaned up.
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
echo "=== Agent Skills Installer ==="
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
    skill_list=$(for d in "$SKILLS_DIR"/*/; do printf '/%s ' "$(basename "$d")"; done)
    info "Done. Skills in this repo: $skill_list"
    echo ""
    echo "Per-tool availability is platform-filtered (see output above)."
    echo "Usage of each skill: see README.md"
    echo ""
    echo "To uninstall: ./install.sh --uninstall"
fi
echo ""
