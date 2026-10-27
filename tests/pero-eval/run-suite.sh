#!/usr/bin/env bash
# 并行跑完整 6 剧本（L1-L4 用 learn skill、F1-F2 用 feynman skill + v3 fixture）并逐个评分。
# 用法: run-suite.sh <learn-skill.md> <feynman-skill.md> <out-dir>
# 产物: <out-dir>/<剧本>.md（transcript）与 <剧本>-scores.json
set -euo pipefail
LEARN="$1"; FEYN="$2"; OUT="$3"
HERE="$(cd "$(dirname "$0")" && pwd)"; REPO="$(cd "$HERE/../.." && pwd)"
mkdir -p "$OUT"
run_one() {  # <skill> <script-path> <name> [fixture]
    bash "$HERE/run-dialogue.sh" "$1" "$2" "$OUT/$3.md" ${4:-} 2>/dev/null
    # 轮数校验：评分器对残缺 transcript 也会给出看似正常的分数，必须在这里拦住
    local want got
    want=$(( $(tr -d '' < "$2" | grep -c '^---$') + 1 ))
    got=$(grep -c '^## 教练' "$OUT/$3.md")
    if [ "$got" -ne "$want" ]; then echo "FAIL $3: $got/$want 轮" >&2; return 1; fi
    bash "$HERE/score-transcript.sh" "$OUT/$3.md" "$OUT/$3-scores.json" > /dev/null
    echo "done $3"
}
for s in L1-normal-novice L2-answer-seeker L3-illusion-of-knowing L4-confident-error; do
    run_one "$LEARN" "$REPO/skills/pero-learn/evals/scripts/$s.md" "$s" &
done
for s in F1-normal F2-answer-fisher; do
    run_one "$FEYN" "$REPO/skills/pero-feynman/evals/scripts/$s.md" "$s" "$HERE/fixture-claude-md-v3.md" &
done
wait
