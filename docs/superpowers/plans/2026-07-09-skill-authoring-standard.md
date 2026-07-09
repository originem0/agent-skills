# Skill 编写规范（子项目 1）实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立本仓库的 skill 编写与验收规范 `docs/skill-authoring.md`，并完成 `platforms` → `metadata.platforms` 的破坏性迁移（frontmatter + 双安装脚本 + 测试 + 真实验证）。

**Architecture:** 规范文档是纯 Markdown 交付物，内容框架来自已批准的 spec（`docs/superpowers/specs/2026-07-09-skill-authoring-standard-design.md`）。platforms 迁移是数据（3 个 SKILL.md frontmatter）+ 解析器（install.sh / install.ps1 各一个函数）+ 回归测试（`tests/` 下两个可重复执行的测试脚本）三位一体，bash 侧和 PowerShell 侧各成一个任务，最后真实运行安装器做端到端验证。

**Tech Stack:** Markdown、Bash（git-bash on Windows）、PowerShell 5+。无新依赖。

## Global Constraints

- `metadata.platforms` 值为**空格分隔的字符串**（如 `claude-code codex`），两空格缩进于 `metadata:` 下，可带双引号；可选值 `claude-code` / `codex` / `openclaw`；缺省 = 全平台。
- 安装脚本是逐行解析器，不是完整 YAML 解析器——frontmatter 中 `platforms:` 键只允许出现在 metadata 下（带缩进）。顶层 `platforms:` 是废弃格式，解析器**不识别、不兼容**（等同无字段 = 全平台），这是已确认的破坏性变更。
- 平台名比较必须是解析列表后的精确比较，禁止子串/正则包含匹配（前缀重叠平台名会误伤，如 `code` vs `claude-code`）。
- 不引入新工具链依赖（无 skills-ref、无 YAML 库）。
- 规范文档语言：中文；代码注释遵循仓库现状（中英混合，说明"为什么"）。
- Task 2 与 Task 3 之间存在不一致窗口（frontmatter 已迁移但 install.ps1 未更新），两个任务必须在同一次执行中连续完成，不可只做其一。
- 已知遗留（本子项目不处理）：`PEROlearn`/`PEROfeynman` 的 name 含大写，违反规范 §1 的小写规则——留给子项目 3（PERO 重设计可能整体改名）；爬虫 skill 的 `allowed-tools` YAML 列表格式、widget-viewer 的 `reference/`→`references/`、`templates/`→`assets/` 改名——留给子项目 2。

## File Structure

| 文件 | 动作 | 职责 |
|------|------|------|
| `docs/skill-authoring.md` | 新建 | 规范文档本体，含验收检查单 |
| `tests/test-platform-filter.sh` | 新建 | install.sh 平台过滤函数的单元测试（fixture + 真实 skill 双覆盖） |
| `tests/test-platform-filter.ps1` | 新建 | install.ps1 平台过滤函数的单元测试（同上） |
| `install.sh` | 修改（24-45 行函数） | 解析 `metadata.platforms`（缩进行） |
| `install.ps1` | 修改（48-61 行函数） | 同上 |
| `skills/PEROlearn/SKILL.md` | 修改（frontmatter） | `platforms: [claude-code]` → `metadata.platforms` |
| `skills/PEROfeynman/SKILL.md` | 修改（frontmatter） | 同上 |
| `skills/widget-viewer/SKILL.md` | 修改（frontmatter） | 同上 |
| `README.md` | 修改（"添加新技能"节） | platforms 字段文档改为新格式 |

---

### Task 1: 规范文档 docs/skill-authoring.md

**Files:**
- Create: `docs/skill-authoring.md`

**Interfaces:**
- Consumes: spec 文档 `docs/superpowers/specs/2026-07-09-skill-authoring-standard-design.md` 的内容框架。
- Produces: 规范全文。后续任务与子项目 2/3 以其 §1 的 `metadata.platforms` 格式定义、附录检查单为准。

- [ ] **Step 1: 写入规范全文**

创建 `docs/skill-authoring.md`，内容如下（完整正文，直接写入）：

````markdown
# Skill 编写规范

本仓库所有 skill 的编写与验收标准。依据：[agentskills.io 规范](https://agentskills.io/specification)、[Anthropic skill 写作最佳实践](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)。新增或重构 skill 时逐项核对，PR 以本文件为验收清单。

## 1. Frontmatter

**必填字段：**

- `name`：≤64 字符，仅小写字母、数字、连字符；不以连字符开头或结尾，无连续连字符；必须与目录名一致。
- `description`：≤1024 字符，第三人称。模板：

  ```yaml
  description: >
    <做什么：第三人称动词开头，一到两句。>
    Use when <何时用：具体触发场景>。
    触发词：<中文关键词>, <english keywords>。
  ```

  禁止第一/第二人称（"我可以帮你""你可以用这个"）。中英双语触发词都要有——两种语言的请求都必须能命中。

**可选字段（只在需要时写）：**

- `compatibility`：≤500 字符，环境硬性要求（OS、外部依赖、网络）。多数 skill 不需要。
- `allowed-tools`：**空格分隔字符串**，如 `allowed-tools: Read Write Bash`。不是 YAML 列表。
- `metadata.platforms`（本仓库扩展）：安装平台过滤，空格分隔字符串，缺省 = 全平台安装。

  ```yaml
  metadata:
    platforms: claude-code            # 多平台写 "claude-code codex"
  ```

  可选值：`claude-code` / `codex` / `openclaw`。
  格式约束（安装脚本是逐行解析器，不是完整 YAML 解析器）：
  - 必须写在 `metadata:` 下，两空格缩进，单独一行；
  - 值为纯字符串或双引号字符串，**不用 `[]` 列表**；
  - `platforms:` 键不得出现在 frontmatter 的其他位置（顶层 `platforms:` 是废弃格式，安装脚本不识别）。

## 2. 结构与 progressive disclosure

- SKILL.md 正文 < 500 行。接近上限就拆文件。
- 子目录定名（官方约定 + 本仓库补充）：
  - `references/` — 文档资料（不是 `reference/`）
  - `scripts/` — 可执行脚本
  - `assets/` — 模板与静态资源（不是 `templates/`）
  - `examples/` — 可运行示例代码（本仓库补充）
  - `evals/` — 评估场景（本仓库补充，见 §4）
- 文件引用只允许一层深：所有子文件直接从 SKILL.md 链接，子文件不再链接其他子文件。
- 超过 100 行的 references 文件顶部加内容目录（Contents 列表），保证部分读取时可见全貌。
- 引用 scripts 时写明意图："运行 `scripts/x.sh`"（执行，产物进上下文）或"参考 `scripts/x.py` 的算法"（阅读，代码进上下文）。
- 路径一律正斜杠，包括面向 Windows 的 skill。
- 时效性内容（版本号、日期相关行为差异）不进主流程，放 gotchas 或折叠的"旧模式"区。

## 3. 指令有效性

- **假设模型已聪明**：不解释模型已知的概念（什么是 PDF、库怎么装）。每段内容自问："这段对得起它的 token 成本吗？"
- **自由度分级**：
  - 脆弱、必须精确的操作 → 给确切命令，注明"不要修改参数"（低自由度）。
  - 有判断空间的任务 → 给方向和启发式，信任模型选路（高自由度）。
  - 默认给一个方案 + 逃生舱（"X 场景改用 Y"），不并列多个等价选项让模型自己挑。
- **复杂流程用 checklist**：给出可复制的清单，让模型逐项勾选推进。
- **质量关键路径用 feedback loop**：校验 → 修复 → 重校验，通过才继续；写明"校验失败时回到第 N 步"。
- 术语一致：同一事物全文只用一个名字。
- 示例具体不抽象：给真实的输入/输出对，不给"诸如此类"。

## 4. 验收（评估驱动）

- 每个 skill 至少 3 个评估场景，放在该 skill 的 `evals/` 目录，每个场景一个 JSON 文件：

  ```json
  {
    "query": "用户会说的原话",
    "files": ["可选：测试用的输入文件路径"],
    "expected_behavior": [
      "可观察的行为断言 1",
      "可观察的行为断言 2",
      "可观察的行为断言 3"
    ]
  }
  ```

- 重构流程：先跑基线（无 skill 时模型对同一组场景的表现）→ 重构 → 用同一组场景验证改进。**无基线不重构。**
- 真实执行验证：
  - 工具类 skill：实际执行核心命令（抓真实网页、渲染真实 widget），不以"命令看起来对"为准。
  - 对话类 skill（PERO 系列）：子代理模拟用户对话，检验指令保真度（该问时问、该停时停）。

## 附：新增/重构 skill 检查单

- [ ] name 合法（小写/数字/连字符）且与目录名一致
- [ ] description 第三人称，含"做什么 + 何时用 + 中英双语触发词"
- [ ] allowed-tools（如有）为空格分隔字符串
- [ ] 平台受限时使用 metadata.platforms（新格式）
- [ ] SKILL.md < 500 行，文件引用一层深
- [ ] 子目录命名符合 §2
- [ ] 无时效性内容混入主流程
- [ ] evals/ 有 ≥3 个场景，且有基线记录
- [ ] 真实执行验证通过
````

- [ ] **Step 2: 对照 spec 核查**

逐项确认规范文档覆盖 spec 的四个章节（Frontmatter / 结构 / 指令有效性 / 验收）和四项裁决（metadata.platforms、allowed-tools 字符串格式、目录定名、description 模板）。缺一项补一项。

- [ ] **Step 3: Commit**

```bash
git add docs/skill-authoring.md
git commit -m "docs: skill 编写规范 v1

依据 agentskills.io 规范与 Anthropic 最佳实践，
含 metadata.platforms 约定、progressive disclosure 结构、
自由度分级、评估驱动验收标准。"
```

---

### Task 2: bash 侧迁移 — frontmatter ×3 + install.sh + 测试 + README

**Files:**
- Create: `tests/test-platform-filter.sh`
- Modify: `install.sh:22-45`（`skill_supports_platform` 函数）
- Modify: `skills/PEROlearn/SKILL.md:1-7`、`skills/PEROfeynman/SKILL.md:1-7`、`skills/widget-viewer/SKILL.md:1-10`（frontmatter）
- Modify: `README.md`（"添加新技能"节的 platforms 示例）
- Test: `tests/test-platform-filter.sh`

**Interfaces:**
- Consumes: 规范 §1 的 `metadata.platforms` 格式（Task 1）。
- Produces: `skill_supports_platform <skill_dir> <platform>` 返回 0/1，识别缩进的 `platforms:` 行；3 个 skill 的新 frontmatter（Task 3 的 ps1 测试直接引用这些真实文件）。

- [ ] **Step 1: 写失败测试**

创建 `tests/test-platform-filter.sh`：

```bash
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
```

- [ ] **Step 2: 运行确认失败**

Run: `bash tests/test-platform-filter.sh`
Expected: FAIL —— 至少"单平台命中"等 fixture 用例失败（旧解析器只识别顶层 `^platforms:`，不识别缩进行），"废弃的顶层格式被忽略"也失败（旧解析器仍识别它）。退出码 > 0。

- [ ] **Step 3: 迁移 3 个 frontmatter**

`skills/PEROlearn/SKILL.md` frontmatter 改为（删除原 `platforms: [claude-code]` 行，description 之后加 metadata 块）：

```yaml
---
name: PEROlearn
description: >
  PERO 学习系统教练。通过 Priming → Encoding → Reference → Retrieval 四阶段引导学习者
  构建可迁移的解释模型。触发关键词：学习、复习、PERO、继续学、知识地图、深度理解。
metadata:
  platforms: claude-code
---
```

`skills/PEROfeynman/SKILL.md` frontmatter 改为：

```yaml
---
name: PEROfeynman
description: >
  PERO 学习系统费曼检验官。扮演较真的学生，检验学习者是否形成了可迁移的解释模型。
  基于 CLAUDE.md 数据制定攻击计划。触发关键词：费曼检验、检验、测试理解。
metadata:
  platforms: claude-code
---
```

`skills/widget-viewer/SKILL.md` frontmatter 改为：

```yaml
---
name: widget-viewer
description: >
  Use when the user asks for charts, diagrams, visualizations, interactive explanations,
  data plots, UI mockups, or any visual content better shown graphically than as text.
  Triggers: "画图", "图表", "可视化", "展示", "visualize", "chart", "diagram", "plot",
  "show me", "draw", "interactive". Renders widget HTML in a native WebView2 window
  via claude-widget-viewer.exe.
metadata:
  platforms: claude-code
---
```

正文一律不动。

- [ ] **Step 4: 更新 install.sh 解析函数**

将 `install.sh` 中 `skill_supports_platform` 函数（含其上方注释，原 22-45 行）整体替换为：

```bash
# Check if a skill supports the given platform.
# Reads `metadata.platforms` (space-separated string) from SKILL.md frontmatter;
# per docs/skill-authoring.md §1 the key is an indented `platforms:` line and
# may only appear under `metadata:`. No field = all platforms.
# Top-level `platforms:` is the retired format and is deliberately ignored.
skill_supports_platform() {
    local skill_dir="$1"
    local platform="$2"
    local skill_file="$skill_dir/SKILL.md"

    if [ ! -f "$skill_file" ]; then
        return 0  # no SKILL.md → allow
    fi

    local platforms_line
    platforms_line=$(sed -n '/^---$/,/^---$/{ /^[[:space:]]\{1,\}platforms:/p }' "$skill_file" | head -n 1)

    if [ -z "$platforms_line" ]; then
        return 0  # no platforms field → all platforms
    fi

    # Parse the value and compare exactly — substring matching would break with
    # prefix-overlapping platform names (e.g. "code" vs "claude-code")
    if echo "$platforms_line" | sed 's/^[[:space:]]*platforms:[[:space:]]*//' | tr -d '"' | tr ' ' '\n' | grep -qx "$platform"; then
        return 0
    fi
    return 1
}
```

- [ ] **Step 5: 运行测试确认通过**

Run: `bash tests/test-platform-filter.sh`
Expected: `10 passed, 0 failed`，退出码 0。

- [ ] **Step 6: 同步 README**

`README.md` "添加新技能"节中的 platforms 示例块：

```yaml
---
name: my-skill
platforms: [claude-code]   # 可选值：claude-code / codex / openclaw
description: ...
---
```

替换为：

```yaml
---
name: my-skill
description: ...
metadata:
  platforms: claude-code   # 空格分隔多个；可选值：claude-code / codex / openclaw
---
```

并在该示例块后加一行：`完整规范见 [docs/skill-authoring.md](docs/skill-authoring.md)。`

- [ ] **Step 7: Commit**

```bash
git add tests/test-platform-filter.sh install.sh skills/PEROlearn/SKILL.md skills/PEROfeynman/SKILL.md skills/widget-viewer/SKILL.md README.md
git commit -m "feat: platforms 迁移至 metadata.platforms（bash 侧）

- 3 个 skill frontmatter 迁移到规范格式（空格分隔字符串）
- install.sh 解析缩进的 metadata.platforms 行，顶层旧格式不再识别
- 新增可重复执行的单元测试 tests/test-platform-filter.sh
- README platforms 示例同步

注意：install.ps1 在下一提交更新，两者需一同合入。"
```

---

### Task 3: PowerShell 侧迁移 — install.ps1 + 测试

**Files:**
- Create: `tests/test-platform-filter.ps1`
- Modify: `install.ps1:48-61`（`Test-SkillSupportsPlatform` 函数）
- Test: `tests/test-platform-filter.ps1`

**Interfaces:**
- Consumes: Task 2 迁移后的 3 个真实 SKILL.md frontmatter；规范 §1 格式。
- Produces: `Test-SkillSupportsPlatform -SkillDir <dir> -Platform <p>` 返回 `$true/$false`，与 bash 版行为完全一致（同一组用例双实现验证）。

- [ ] **Step 1: 写失败测试**

创建 `tests/test-platform-filter.ps1`：

```powershell
# install.ps1 平台过滤函数的单元测试（metadata.platforms 格式）。
# 用法：powershell -NoProfile -ExecutionPolicy Bypass -File tests/test-platform-filter.ps1
# 退出码 = 失败用例数。
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path $PSScriptRoot -Parent
$src = Get-Content (Join-Path $RepoRoot "install.ps1") -Raw
if ($src -notmatch '(?s)(function Test-SkillSupportsPlatform \{.*?\n\})') {
    Write-Host "EXTRACT FAIL: function not found in install.ps1"; exit 1
}
Invoke-Expression $Matches[1]

$fixtures = Join-Path ([System.IO.Path]::GetTempPath()) ("skilltest-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $fixtures | Out-Null

function New-Fixture([string]$name, [string[]]$fm) {
    $dir = Join-Path $fixtures $name
    New-Item -ItemType Directory -Path $dir | Out-Null
    @('---') + $fm + @('---', '# body') | Set-Content (Join-Path $dir "SKILL.md")
    return $dir
}

$single  = New-Fixture "single"  @('name: a', 'metadata:', '  platforms: claude-code')
$multi   = New-Fixture "multi"   @('name: b', 'metadata:', '  platforms: claude-code codex')
$quoted  = New-Fixture "quoted"  @('name: c', 'metadata:', '  platforms: "codex"')
$nofield = New-Fixture "nofield" @('name: d')
$legacy  = New-Fixture "legacy"  @('name: e', 'platforms: [claude-code]')

$cases = @(
    @("单平台命中",                 $single,  "claude-code", $true),
    @("单平台拒绝其他",             $single,  "codex",       $false),
    @("前缀重叠不误匹配",           $single,  "code",        $false),
    @("多平台命中第二项",           $multi,   "codex",       $true),
    @("带引号的值命中",             $quoted,  "codex",       $true),
    @("无字段=全平台",              $nofield, "openclaw",    $true),
    @("废弃的顶层格式被忽略=全平台", $legacy,  "codex",       $true),
    @("PEROlearn 装 claude-code",   (Join-Path $RepoRoot "skills/PEROlearn"),        "claude-code", $true),
    @("PEROlearn 不装 codex",       (Join-Path $RepoRoot "skills/PEROlearn"),        "codex",       $false),
    @("crawl4ai 全平台",            (Join-Path $RepoRoot "skills/crawl4ai-scraper"), "codex",       $true)
)
$failCount = 0
foreach ($c in $cases) {
    $got = Test-SkillSupportsPlatform $c[1] $c[2]
    if ($got -eq $c[3]) { Write-Host "PASS $($c[0])" }
    else { Write-Host "FAIL $($c[0]) (got $got want $($c[3]))"; $failCount++ }
}
Remove-Item $fixtures -Recurse -Force
Write-Host "failures: $failCount"
exit $failCount
```

- [ ] **Step 2: 运行确认失败**

Run: `powershell -NoProfile -ExecutionPolicy Bypass -File tests/test-platform-filter.ps1`
Expected: FAIL —— fixture 用例和真实 skill 用例失败（旧解析器只匹配顶层 `^platforms:`，而 frontmatter 已在 Task 2 迁移），退出码 > 0。

- [ ] **Step 3: 更新 install.ps1 解析函数**

将 `install.ps1` 中 `Test-SkillSupportsPlatform` 函数整体替换为：

```powershell
function Test-SkillSupportsPlatform {
    # Reads `metadata.platforms` (space-separated string) from SKILL.md frontmatter;
    # per docs/skill-authoring.md §1 the key is an indented `platforms:` line and
    # may only appear under `metadata:`. No field = all platforms.
    # Top-level `platforms:` is the retired format and is deliberately ignored.
    param([string]$SkillDir, [string]$Platform)
    $skillFile = Join-Path $SkillDir "SKILL.md"
    if (-not (Test-Path $skillFile)) { return $true }
    $inFrontmatter = $false
    foreach ($line in Get-Content $skillFile) {
        if ($line -eq '---' -and -not $inFrontmatter) { $inFrontmatter = $true; continue }
        if ($line -eq '---' -and $inFrontmatter) { break }
        if ($inFrontmatter -and $line -match '^\s+platforms:\s*(.+)$') {
            # Exact list compare — substring matching would break with
            # prefix-overlapping platform names (e.g. "code" vs "claude-code")
            $list = ($Matches[1] -replace '"', '') -split '\s+' | Where-Object { $_ }
            return $list -contains $Platform
        }
    }
    return $true  # no platforms field → all platforms
}
```

- [ ] **Step 4: 运行测试确认通过**

Run: `powershell -NoProfile -ExecutionPolicy Bypass -File tests/test-platform-filter.ps1`
Expected: 10 个 PASS，`failures: 0`，退出码 0。

- [ ] **Step 5: 回归 bash 测试**

Run: `bash tests/test-platform-filter.sh`
Expected: `10 passed, 0 failed`（确认 Task 3 未破坏 bash 侧）。

- [ ] **Step 6: Commit**

```bash
git add tests/test-platform-filter.ps1 install.ps1
git commit -m "feat: platforms 迁移至 metadata.platforms（PowerShell 侧）

install.ps1 与 install.sh 行为对齐，同一组用例双实现验证。"
```

---

### Task 4: 端到端真实验证

**Files:**
- 无代码改动（验证任务）；如发现缺陷，修复归入对应文件并单独提交。

**Interfaces:**
- Consumes: Task 2/3 的完整迁移结果。
- Produces: 真实安装器运行记录，作为子项目 1 的验收证据。

- [ ] **Step 1: 真实运行 Windows 安装器**

Run: `powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1`
Expected:
- "Claude Code detected"，5 个 skill 全部链接（claude-code 平台：PERO ×2、widget-viewer、双爬虫都命中或无字段）。
- 收尾输出动态列出全部 skill：`Done. Skills in this repo: /PEROfeynman, /PEROlearn, /crawl4ai-scraper, /firecrawl-scraper, /widget-viewer`。
- 无 `[ERR]`。

- [ ] **Step 2: 验证链接落地**

Run: `ls ~/.claude/skills | sort`
Expected: 包含 `PEROfeynman`、`PEROlearn`、`crawl4ai-scraper`、`firecrawl-scraper`、`widget-viewer` 五项（junction/symlink）。

- [ ] **Step 3: 验证平台过滤的真实行为**

若 `~/.codex` 存在：检查安装器输出中 PERO ×2 与 widget-viewer 显示 `not supported on Codex CLI, skipping`，且 `~/.codex/skills` 下只有双爬虫。
若 `~/.codex` 不存在：跳过（codex 过滤逻辑已由两套单元测试覆盖），在执行记录中注明。

- [ ] **Step 4: 全量测试收尾**

Run: `bash tests/test-platform-filter.sh && powershell -NoProfile -ExecutionPolicy Bypass -File tests/test-platform-filter.ps1`
Expected: 两套各 10 PASS，退出码 0。

- [ ] **Step 5: 收尾提交（如有）**

验证全绿且无改动 → 无需提交。发现并修复了缺陷 → 修复与对应测试一起提交：

```bash
git add -A
git commit -m "fix: 端到端验证发现的缺陷修复"
```

---

## Self-Review 记录

1. **Spec 覆盖**：规范文档四章节 → Task 1；四项裁决全部写入规范正文（其中 allowed-tools/目录名裁决由子项目 2/3 执行，已在 Global Constraints 注明）；metadata.platforms 迁移（3 frontmatter + 双脚本）→ Task 2/3；"规范可当验收清单"→ 规范附录检查单；真实验证 → Task 4。无缺口。
2. **占位符扫描**：所有代码步骤含完整代码；无 TBD/"类似 Task N"。
3. **类型/命名一致性**：`skill_supports_platform`（bash）与 `Test-SkillSupportsPlatform`（ps1）名称沿用现有代码；两套测试用例一一对应（10 条）；`metadata.platforms` 格式在规范、frontmatter、双解析器、README 四处一致（空格分隔、可带引号、两空格缩进）。
