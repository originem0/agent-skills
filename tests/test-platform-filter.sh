#!/usr/bin/env bash
# install.sh 平台过滤函数的单元测试（metadata.platforms 格式）。
# 用法：bash tests/test-platform-filter.sh；退出码 = 失败用例数。
set -u
cd "$(dirname "$0")/.."

# 只提取被测函数，不执行安装器主体
eval "$(sed -n '/^skill_supports_platform()/,/^}/p' install.sh)"

fixture_dir=$(mktemp -d)
trap 'rm -rf "$fixture_dir"' EXIT

make_fixture() {  # $1=名字 其余=frontmatter 行；输出 fixture 目录路径
    local dir="$fixture_dir/$1"; shift
    mkdir -p "$dir"
    { echo '---'; printf '%s\n' "$@"; echo '---'; echo '# body'; } > "$dir/SKILL.md"
    echo "$dir"
}

pass=0; fail=0
check() {  # $1=描述 $2=期望(y/n) $3=skill目录 $4=平台
    local got
    if skill_supports_platform "$3" "$4"; then got=y; else got=n; fi
    if [ "$got" = "$2" ]; then echo "PASS $1"; pass=$((pass+1))
    else echo "FAIL $1 (got $got want $2)"; fail=$((fail+1)); fi
}

single=$(make_fixture single 'name: a' 'metadata:' '  platforms: claude-code')
multi=$(make_fixture multi 'name: b' 'metadata:' '  platforms: claude-code codex')
quoted=$(make_fixture quoted 'name: c' 'metadata:' '  platforms: "codex"')
nofield=$(make_fixture nofield 'name: d')
legacy=$(make_fixture legacy 'name: e' 'platforms: [claude-code]')

check "单平台命中"                 y "$single" claude-code
check "单平台拒绝其他"             n "$single" codex
check "前缀重叠不误匹配"           n "$single" code
check "多平台命中第二项"           y "$multi" codex
check "带引号的值命中"             y "$quoted" codex
check "无字段=全平台"              y "$nofield" openclaw
check "废弃的顶层格式被忽略=全平台" y "$legacy" codex

# 仓库内真实 skill（迁移后应通过）
check "PEROlearn 装 claude-code"   y skills/PEROlearn claude-code
check "PEROlearn 不装 codex"       n skills/PEROlearn codex
check "crawl4ai 全平台"            y skills/crawl4ai-scraper codex

echo "$pass passed, $fail failed"
exit "$fail"
