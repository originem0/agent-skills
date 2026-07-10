#!/usr/bin/env bash
# 用法: score-transcript.sh <transcript.md> <out.json>
set -euo pipefail
prompt="$(cat "$(dirname "$0")/scorer-prompt.md")

===== TRANSCRIPT =====
$(cat "$1")"
echo "$prompt" | claude -p --model opus 2>&1 > "$2"
cat "$2"
