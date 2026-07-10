#!/usr/bin/env bash
# 逐轮模拟学习者-tutor 对话。学习者消息来自固定剧本（--- 分隔），
# 每轮将 skill 全文 + 对话历史 + 新消息发给 claude -p，追加 tutor 回复到 transcript。
# 用法: run-dialogue.sh <skill.md> <script.md> <out-transcript.md> [fixture-claude-md.md]
set -euo pipefail
SKILL_FILE="$1"; SCRIPT_FILE="$2"; OUT="$3"; FIXTURE="${4:-}"

SKILL_TEXT=$(cat "$SKILL_FILE")
FIXTURE_BLOCK=""
if [ -n "$FIXTURE" ]; then
    FIXTURE_BLOCK="===== 当前目录的 CLAUDE.md 内容 =====
$(cat "$FIXTURE")
"
fi

: > "$OUT"
turn=0
msg=""
flush_turn() {
    [ -z "$msg" ] && return
    turn=$((turn+1))
    echo "## 学习者（第 ${turn} 轮）" >> "$OUT"
    echo "$msg" >> "$OUT"; echo >> "$OUT"
    prompt="你正在扮演下面这个 skill 定义的角色，严格遵循其全部规则行动。不要解释你在扮演，直接以角色身份输出。

===== SKILL =====
${SKILL_TEXT}
=====
${FIXTURE_BLOCK}
===== 到目前为止的对话 =====
$(cat "$OUT")
=====
以角色身份回复学习者的最新消息。只输出回复正文。"
    reply=$(echo "$prompt" | claude -p --model opus 2>&1 | head -c 2000)
    echo "## 教练（第 ${turn} 轮）" >> "$OUT"
    echo "$reply" >> "$OUT"; echo >> "$OUT"
    echo "  turn $turn done" >&2
    msg=""
}
while IFS= read -r line; do
    if [ "$line" = "---" ]; then flush_turn; else msg="${msg}${line}
"; fi
done < "$SCRIPT_FILE"
flush_turn
echo "transcript: $OUT ($turn turns)" >&2
