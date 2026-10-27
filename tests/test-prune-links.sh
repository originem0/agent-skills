#!/usr/bin/env bash
# install.sh 的 prune_stale_links 单元测试：只清理「指向本仓库 skills/ 且目标已不存在」的链接。
# 用法：bash tests/test-prune-links.sh；退出码 = 失败用例数。
# git-bash 下 ln -s 默认退化为复制，这里强制原生 symlink；环境不支持时报 SKIP（退出 0）。
set -u
cd "$(dirname "$0")/.."
export MSYS=winsymlinks:nativestrict

eval "$(sed -n '/^prune_stale_links()/,/^}/p' install.sh)"

fx=$(mktemp -d); trap 'rm -rf "$fx"' EXIT
SKILLS_DIR="$fx/repo/skills"
tool="$fx/toolskills"
mkdir -p "$SKILLS_DIR/alive" "$SKILLS_DIR/gone" "$fx/repo/skills-other/x" "$fx/elsewhere/y" "$tool/realdir"
if ! ln -s "$SKILLS_DIR/alive/" "$tool/alive" 2>/dev/null || [ ! -L "$tool/alive" ]; then
    echo "SKIP: 当前环境无法创建原生 symlink"; exit 0
fi
ln -s "$SKILLS_DIR/gone/" "$tool/gone"
ln -s "$fx/repo/skills-other/x/" "$tool/prefix"
ln -s "$fx/elsewhere/y/" "$tool/foreign"
rm -rf "$SKILLS_DIR/gone" "$fx/repo/skills-other/x" "$fx/elsewhere/y"

prune_stale_links "$tool" > /dev/null

fail=0
check() { if eval "$2"; then echo "PASS $1"; else echo "FAIL $1"; fail=$((fail+1)); fi; }
check "悬空且指向仓库 skills/ 的链接被清理" '[ ! -L "$tool/gone" ]'
check "有效的仓库链接保留"                 '[ -L "$tool/alive" ]'
check "前缀相同的兄弟目录不误判"           '[ -L "$tool/prefix" ]'
check "指向仓库外的悬空链接不碰"           '[ -L "$tool/foreign" ]'
check "真实目录不碰"                       '[ -d "$tool/realdir" ] && [ ! -L "$tool/realdir" ]'
echo "$((5-fail)) passed, $fail failed"
exit $fail
