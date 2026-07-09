# 工具类 Skill 更新（子项目 2）实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 三个工具类 skill（firecrawl-scraper、crawl4ai-scraper、widget-viewer）更新到上游现状并按 `docs/skill-authoring.md` 合规，附 evals + 基线 + 真实执行验证。

**Architecture:** 每 skill 一个任务顺序执行（firecrawl → crawl4ai → widget-viewer），收尾任务做回归。firecrawl 任务的真实验证动作定向抓取 crawl4ai 官方文档页，产物同时作为 crawl4ai 任务的 ground truth 工件（credits 一次消耗双重用途）。基线采用"实施者先裸答"协议：实施者在读取任何 ground truth 或现有 SKILL.md 之前，先凭自身知识回答 evals 场景并记录——这就是"无 skill 基线"。

**Tech Stack:** Markdown、firecrawl CLI（npm）、git-bash。无新依赖。

> **⚠️ 范围变更（2026-07-09，用户决定）：Task 1（firecrawl-scraper）整体取消**——不做 firecrawl 认证，该 skill 本轮不动。Task 2 的 ground truth 从 firecrawl 抓取的文档工件降级为 WebSearch 结果（本计划各处提到的 `.git/sdd/crawl4ai-*-docs.md` 工件不再存在，Task 2 Step 3 规则 1 中"两个文档工件"一律替换为"WebSearch 结果（在报告中附来源 URL）"）。Task 4 的 README 校对不再涉及 firecrawl 描述改动。credits 预算条款作废。firecrawl-scraper 的已知漂移（browse→interact、--wait→--wait-for、--extract→-Q、glob→paths、本地 1.14.8 落后 1.19.24）记录于 progress ledger，待后续单独处理。

## Global Constraints

- **credits 硬预算 ≤10**，分配：`scrape docs.crawl4ai.com/core/cli/`（1）+ `scrape docs.crawl4ai.com/core/deep-crawling/`（1）+ `map docs.crawl4ai.com`（1）+ `search`（limit 3，≤3）+ `-Q` 页面问答（1）≈ 7，留 3 余量。任一命令失败最多重试 1 次；预算耗尽立即停止真实验证并如实记录。
- **crawl4ai 不安装、不实测**（已批准豁免）：其 SKILL.md 每条命令必须可追溯到 ground truth 工件（`.git/sdd/crawl4ai-cli-docs.md`、`.git/sdd/crawl4ai-deepcrawl-docs.md` 或 WebSearch 结果），gotchas 必须含标注："命令核对于 2026-07 官方文档（v0.9.x），未本机实测"。
- **firecrawl 前置**：用户已在会话内完成 `firecrawl login`（控制器在派发 Task 1 前确认 `firecrawl --status` 显示已认证；未认证则不派发）。
- 验收清单 = `docs/skill-authoring.md` 附录，每任务提交前逐项核对。
- `allowed-tools` 空格分隔字符串；description 第三人称 + Use when + 中英双语触发词；SKILL.md < 500 行；引用一层深。
- evals JSON 格式：`{"query": "...", "expected_behavior": ["...", "..."]}`（本计划已给全文，逐字使用）。
- `skills/` 目录经 junction 实时链接到 `~/.claude/skills`——任务内改动即时生效，属预期行为，无需处理。
- WebFetch 当前不可用（代理模型故障）；上游调研用 firecrawl scrape 或 WebSearch。
- 已知遗留不处理：PERO skill（子项目 3）；安装脚本/测试套件（除非验证暴露缺陷）。

## File Structure

| 文件 | 动作 | 职责 |
|------|------|------|
| `skills/firecrawl-scraper/SKILL.md` | 重写 | 对齐 1.19.24 --help |
| `skills/firecrawl-scraper/gotchas.md` | 重写 | 认证/credits/.firecrawl/ 缓存 |
| `skills/firecrawl-scraper/scripts/check-env.sh` | 修改 | 用 `firecrawl --status` 检测认证 |
| `skills/firecrawl-scraper/evals/*.json` + `baseline.md` | 新建 | 3 场景 + 基线记录 |
| `skills/crawl4ai-scraper/SKILL.md`、`gotchas.md` | 重写 | 对齐 v0.9.x 文档 |
| `skills/crawl4ai-scraper/examples/*.py` | 修改 | API 签名对照文档修正 |
| `skills/crawl4ai-scraper/evals/*.json` + `baseline.md` | 新建 | 3 场景 + 基线（标注未实测） |
| `skills/widget-viewer/references/`（原 reference/） | git mv | 规范目录名 |
| `skills/widget-viewer/assets/`（原 templates/） | git mv | 规范目录名 |
| `skills/widget-viewer/SKILL.md` | 修改 | 路径引用 + compatibility 字段 |
| `skills/widget-viewer/evals/*.json` + `baseline.md` | 新建 | 3 场景 + 基线 |
| `README.md` | 修改（Task 4） | 技能列表描述与新 SKILL.md 一致 |
| `.git/sdd/firecrawl-help.txt` | 新建（不提交） | Task 1 ground truth |
| `.git/sdd/crawl4ai-cli-docs.md`、`crawl4ai-deepcrawl-docs.md` | 新建（不提交） | Task 1 产出、Task 2 消费 |

---

### Task 1: firecrawl-scraper 更新 + 真实验证（兼产出 crawl4ai ground truth）

**Files:**
- Modify: `skills/firecrawl-scraper/SKILL.md`、`skills/firecrawl-scraper/gotchas.md`、`skills/firecrawl-scraper/scripts/check-env.sh`
- Create: `skills/firecrawl-scraper/evals/scrape-page.json`、`evals/map-site.json`、`evals/auth-setup.json`、`evals/baseline.md`
- Create（工件，不提交）: `.git/sdd/firecrawl-help.txt`、`.git/sdd/crawl4ai-cli-docs.md`、`.git/sdd/crawl4ai-deepcrawl-docs.md`

**Interfaces:**
- Consumes: 用户已登录的 firecrawl 会话；`docs/skill-authoring.md` 验收清单。
- Produces: 两个 crawl4ai 文档工件（Task 2 的 ground truth）；重写后的 skill（Task 4 校对 README 用）。

- [ ] **Step 1: 基线裸答（必须最先做，早于读任何 --help/现有 SKILL.md）**

将下列 3 个场景的 query 用自身知识作答（写出你会给用户的命令），记录到 `skills/firecrawl-scraper/evals/baseline.md`：

```markdown
# firecrawl-scraper 基线记录

## 重构前基线（实施者裸答，未读任何 ground truth）
日期：<执行日期>

### 场景 scrape-page
<裸答内容>

### 场景 map-site
<裸答内容>

### 场景 auth-setup
<裸答内容>

## 重构后复验
（重写完成后填写：对照新 SKILL.md 检查裸答中的每个错误命令/参数是否已被新文档纠正，逐条列出）
```

- [ ] **Step 2: 更新 CLI 并捕获 ground truth**

```bash
npm update -g firecrawl-cli && firecrawl --version   # 期望 1.19.24
firecrawl --status                                    # 期望显示已认证 + credits 余额，记下余额
{ firecrawl --help; for c in scrape crawl map search agent interact config login; do echo "===== $c ====="; firecrawl $c --help; done; } > .git/sdd/firecrawl-help.txt 2>&1
wc -l .git/sdd/firecrawl-help.txt                     # 期望 >150 行
```

- [ ] **Step 3: 真实验证 + 产出 crawl4ai 工件（≤7 credits，逐条记录实际输出摘要）**

```bash
firecrawl scrape https://docs.crawl4ai.com/core/cli/ --only-main-content -o .git/sdd/crawl4ai-cli-docs.md
firecrawl scrape https://docs.crawl4ai.com/core/deep-crawling/ --only-main-content -o .git/sdd/crawl4ai-deepcrawl-docs.md
firecrawl map https://docs.crawl4ai.com | head -20
firecrawl search "crawl4ai best-first deep crawl" --limit 3
firecrawl scrape https://docs.crawl4ai.com/core/cli/ -Q "crwl 的输出格式参数有哪些可选值？" 
firecrawl --status    # 记录消耗后的余额，计算实际用量
```

期望：两个 .md 工件非空（`wc -l` 各 >50）且包含 `crwl` 命令示例；map 返回 URL 列表；search 返回 3 条结果；`-Q` 返回含输出格式的回答。任一失败重试 1 次，仍失败则记录并继续（工件缺失时 Task 2 降级用 WebSearch，需在报告注明）。

- [ ] **Step 4: 写 evals（逐字）**

`evals/scrape-page.json`:
```json
{
  "query": "帮我把 https://docs.crawl4ai.com/core/cli/ 这页抓成干净的 markdown 存到本地",
  "expected_behavior": [
    "使用 firecrawl scrape 且参数在当前 CLI 中真实存在（如 --only-main-content、-o）",
    "不使用已废弃的命令或参数（browse、--extract、--wait）",
    "提到输出落盘位置（-o 指定路径或默认 .firecrawl/ 缓存目录）"
  ]
}
```

`evals/map-site.json`:
```json
{
  "query": "我想知道 docs.example.com 整个站有哪些页面，但别把我的额度用光",
  "expected_behavior": [
    "推荐先用 firecrawl map 做 URL 发现而不是直接 crawl",
    "提到 credits 消耗评估（map 便宜、crawl 按页计费）",
    "如给出 crawl 命令则使用 --limit 控制规模"
  ]
}
```

`evals/auth-setup.json`:
```json
{
  "query": "firecrawl 提示 Not authenticated，怎么配置？",
  "expected_behavior": [
    "给出当前有效的认证方式（firecrawl login / firecrawl config / FIRECRAWL_API_KEY 环境变量）",
    "提到 firecrawl --status 可查认证状态和余额",
    "不使用过时语法（如 login --browser）"
  ]
}
```

- [ ] **Step 5: 重写 SKILL.md**

规则（每条都要满足，审查者将逐条核对）：
1. 文中出现的**每个命令、每个参数**必须能在 `.git/sdd/firecrawl-help.txt` 中找到（grep 可命中）。
2. 保留现有结构骨架（前置条件 → 模式选择表 → 各命令节 → 更多信息指向 gotchas），模式选择表更新为当前命令面：scrape / crawl / map / search / agent / interact。
3. 漂移修正清单（全部落实）：`browse`→`interact`；`--wait`→`--wait-for`；`--extract`→`-Q/--query`；`--include-glob/--exclude-glob`→`--include-paths/--exclude-paths`；截图改 `--screenshot`/`--full-page-screenshot`；补 `--status` 查额度；补 scrape 默认保存 `.firecrawl/`。
4. frontmatter：`allowed-tools: Read Write Bash Glob Grep AskUserQuestion`（空格分隔字符串）；description 保持双语触发词，校对为第三人称。
5. 每个命令节给一个默认用法 + 必要时一个逃生舱，不并列等价选项；全文 <150 行。

- [ ] **Step 6: 重写 gotchas.md + 更新 check-env.sh**

gotchas 必含：认证三方式与优先级、`firecrawl --status` 查余额、`.firecrawl/` 缓存目录（建议加入 .gitignore）、map-先行的额度策略、robots.txt 提醒。
check-env.sh：认证检测改用 `firecrawl --status`（当前脚本若用旧方式则更新），保持"诊断信息友好"风格。

- [ ] **Step 7: 基线复验 + 验收清单核对**

回填 `evals/baseline.md` 的"重构后复验"节：裸答中每个错误命令逐条对照新 SKILL.md 确认已纠正。对照 `docs/skill-authoring.md` 附录检查单逐项核对并在报告中列出结果。

- [ ] **Step 8: Commit**

```bash
git add skills/firecrawl-scraper
git commit -m "feat(firecrawl-scraper): 对齐 CLI 1.19.24 命令面

browse→interact、--wait→--wait-for、--extract→-Q 等漂移修正，
以本地 --help 全量输出为 ground truth。新增 evals ×3 + 基线记录，
真实验证：scrape/map/search/-Q 各一次（输出见 task report）。

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: crawl4ai-scraper 更新（文档核对，豁免实测）

**Files:**
- Modify: `skills/crawl4ai-scraper/SKILL.md`、`gotchas.md`、`examples/basic_crawl.py`、`examples/css_extraction.py`、`examples/session_crawl.py`、`examples/js_interaction.py`
- Create: `skills/crawl4ai-scraper/evals/local-docs-crawl.json`、`evals/css-extract.json`、`evals/js-heavy-page.json`、`evals/baseline.md`

**Interfaces:**
- Consumes: `.git/sdd/crawl4ai-cli-docs.md`、`.git/sdd/crawl4ai-deepcrawl-docs.md`（Task 1 产出；若缺失，用 WebSearch 补并在报告注明降级）。
- Produces: 重写后的 skill（Task 4 校对 README 用）。

- [ ] **Step 1: 基线裸答**（同 Task 1 协议：先裸答 3 场景记入 `evals/baseline.md`，格式同 Task 1 Step 1 模板，再读工件）

- [ ] **Step 2: 写 evals（逐字）**

`evals/local-docs-crawl.json`:
```json
{
  "query": "不想花钱用云服务，帮我把 docs.example.com 整个文档站在本地抓下来喂给 LLM",
  "expected_behavior": [
    "推荐 crwl --deep-crawl 并用 --max-pages 控制规模",
    "LLM 友好输出使用当前有效的格式值（markdown-fit，而非已改名的 fit_markdown）",
    "提到完全本地运行、无需 API Key 的定位"
  ]
}
```

`evals/css-extract.json`:
```json
{
  "query": "用 crawl4ai 从一个结构很规律的产品列表页提取名称和价格",
  "expected_behavior": [
    "优先推荐 CSS schema 提取而非 LLM 提取（免费且快）",
    "给出的提取用法与当前文档一致（-e/-s 配置文件或 Python API JsonCssExtractionStrategy）",
    "提示 LLM 提取需要配置 provider API Key 作为替代路径"
  ]
}
```

`evals/js-heavy-page.json`:
```json
{
  "query": "crawl4ai 抓一个 JS 渲染很重的页面拿不到内容怎么办",
  "expected_behavior": [
    "给出当前有效的浏览器/爬虫配置手段（-b/-c 内联参数或 YAML，如 scan_full_page、delay_before_return_html）",
    "提到无限滚动页面用 scan_full_page",
    "不编造不存在的参数"
  ]
}
```

- [ ] **Step 3: 重写 SKILL.md**

规则：
1. 每个 CLI 命令/参数必须能在两个文档工件（或报告中注明的 WebSearch 结果）中找到出处；做不到的宁可删除该内容。
2. 漂移修正清单：`-o fit_markdown`→`-o markdown-fit`；深爬策略补 `best-first`；核对 `--include-pattern/--exclude-pattern` 是否仍存在（以工件为准，不存在则改为工件中的实际参数）；补 `-j` 快速提取、`-B/-b/-C/-c` 配置体系（一句话 + 指向 gotchas，不展开）、`--example`。
3. 前置条件节确认 pip 包名与 `crawl4ai-setup` 仍是当前安装方式（以工件/WebSearch 为准）。
4. frontmatter：`allowed-tools` 改空格分隔字符串；description 校对第三人称。
5. Python API 表保留按需读 examples 的结构；全文 <120 行。

- [ ] **Step 4: 修正 examples/*.py**

对照工件中的 Python API 部分核对 4 个示例的 import 路径、类名、方法签名（`AsyncWebCrawler`、`CrawlerRunConfig`、extraction strategy 类等）。工件覆盖不到的 API 用 WebSearch 核对；仍无法确认的保持原样并在文件头加注释 `# 未能对照 2026-07 文档核实，使用时如报错请查 docs.crawl4ai.com`。禁止凭记忆改签名。

- [ ] **Step 5: 重写 gotchas.md**

必含：与 Firecrawl 对比表（更新：Firecrawl 免费 500 credits/月的说法要么从 firecrawl --status 或官网确认，要么删除具体数字）；**豁免标注原文**："本 skill 命令核对于 2026-07 官方文档（v0.9.x），未本机实测。如实际执行报错，以 `crwl --help` 为准并反馈更新。"；v0.8.5+ 反爬自动升级、`~/.crawl4ai/global.yml` 存 token、markdown-fit 适合喂 LLM。

- [ ] **Step 6: 基线复验 + 验收清单核对**（同 Task 1 Step 7 协议）

- [ ] **Step 7: Commit**

```bash
git add skills/crawl4ai-scraper
git commit -m "feat(crawl4ai-scraper): 对齐 v0.9.x 官方文档

fit_markdown→markdown-fit、深爬补 best-first、新增 -j/配置体系说明，
examples API 签名对照文档核正。文档核对未实测（已批准豁免，gotchas 标注）。
新增 evals ×3 + 基线记录。

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: widget-viewer 规范对齐 + 真实渲染验证

**Files:**
- Rename: `skills/widget-viewer/reference/` → `references/`、`skills/widget-viewer/templates/` → `assets/`（用 `git mv`）
- Modify: `skills/widget-viewer/SKILL.md`（路径引用 + frontmatter）
- Create: `skills/widget-viewer/evals/chart-request.json`、`evals/diagram-request.json`、`evals/window-not-opening.json`、`evals/baseline.md`

**Interfaces:**
- Consumes: `docs/skill-authoring.md` §2 目录定名。
- Produces: 重构后的 skill（Task 4 校对 README 用）。

- [ ] **Step 1: 基线裸答**（同协议，3 场景先裸答记入 `evals/baseline.md`）

- [ ] **Step 2: 写 evals（逐字）**

`evals/chart-request.json`:
```json
{
  "query": "画一个这个项目最近提交数量的柱状图",
  "expected_behavior": [
    "把 widget HTML 写到 .claude/widgets/<snake_case>.html 而非直接输出代码块",
    "基于 assets/chartjs.html 模板改造（type:'bar'、borderRadius），不从零手写",
    "颜色走 CSS 变量 getComputedStyle，不硬编码 hex；容器 width:100%"
  ]
}
```

`evals/diagram-request.json`:
```json
{
  "query": "给我画个安装脚本工作流程的示意图",
  "expected_behavior": [
    "选用 assets/svg-diagram.html 模板路径",
    "SVG 用 viewBox + width=100%，不设固定像素宽",
    "写入 .claude/widgets/ 触发 hook 渲染"
  ]
}
```

`evals/window-not-opening.json`:
```json
{
  "query": "让你画的图窗口没弹出来",
  "expected_behavior": [
    "指出依赖：claude-widget-viewer 在 PATH + settings.json 的 PostToolUse Write hook",
    "指向 github.com/originem0/claude-widget-viewer 安装",
    "不盲目重写同一文件重试"
  ]
}
```

- [ ] **Step 3: 目录改名 + SKILL.md 更新**

```bash
cd "D:\Development\Automation\agent-skills" && git mv skills/widget-viewer/reference skills/widget-viewer/references && git mv skills/widget-viewer/templates skills/widget-viewer/assets
```

SKILL.md 修改：全部 `templates/` 路径引用 → `assets/`（3 处模板表 + Templates 节文字），`reference/css-variables.md` → `references/css-variables.md`；frontmatter 在 `metadata:` 块前加：

```yaml
compatibility: Windows + WebView2; requires claude-widget-viewer on PATH and its PostToolUse Write hook
```

- [ ] **Step 4: 真实渲染验证**

写一个最小 widget 到 `D:\Development\Automation\agent-skills\.claude\widgets\refactor_smoke_test.html`（raw fragment：`<style>` + 一个 `width:100%` 容器 + 标题文字 "子项目 2 验证" + 空 `<script>`），Write 后：

```bash
sleep 3 && tasklist | grep -i "claude-widget-viewer" && echo "RENDER OK"
```

期望：进程存在，RENDER OK。若 hook 未触发（进程不在），按 SKILL.md 自己的排障路径诊断并在报告记录（这本身就是对 skill 排障文档的检验）。验证后删除该 html 文件。

- [ ] **Step 5: 基线复验 + 验收清单核对**（同协议）

- [ ] **Step 6: Commit**

```bash
git add -A skills/widget-viewer
git commit -m "feat(widget-viewer): 规范目录对齐 + compatibility 字段

reference/→references/、templates/→assets/（路径引用同步），
frontmatter 补 compatibility。evals ×3 + 基线 + 真实渲染验证通过。

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: 收尾回归

**Files:**
- Modify: `README.md`（技能列表节，如有失真）

**Interfaces:**
- Consumes: Task 1-3 的最终 SKILL.md。

- [ ] **Step 1: README 校对**

对照三个新 SKILL.md 核对 README 技能列表的描述与选择指南（如 firecrawl 的 "免费 500 credits/月" 若 Task 1 未能证实则同步修改；`browse` 等旧词清除）。有失真就改，无失真跳过。

- [ ] **Step 2: 安装器真实运行**

```bash
powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1 < /dev/null
```
期望：5/5 链接刷新（widget-viewer 改名目录随 junction 生效），无 [ERR]，退出码 0。

- [ ] **Step 3: 三套测试回归**

```bash
bash tests/test-platform-filter.sh
powershell -NoProfile -ExecutionPolicy Bypass -File tests/test-platform-filter.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tests/test-link-ops.ps1
```
期望：12 passed / failures: 0 / failures: 0。

- [ ] **Step 4: Commit（如有 README 改动）**

```bash
git add README.md && git commit -m "docs: README 技能描述同步子项目 2 重构结果

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Self-Review 记录

1. **Spec 覆盖**：三 skill 重构 → Task 1/2/3；统一动作（allowed-tools/description/evals/基线）在各任务步骤内；crawl4ai 豁免标注 → Task 2 Step 5 原文；firecrawl <10 credits → Global Constraints 逐项分配 + Task 1 Step 3；widget-viewer 真实渲染 → Task 3 Step 4；收尾回归 → Task 4。验收标准 1-5 全部有对应步骤。无缺口。
2. **占位符扫描**：evals JSON、豁免标注、compatibility 字段、验证命令均为全文；SKILL.md 正文内容依赖运行时 ground truth，以"每条内容可 grep 到出处"的可验证规则锁定，非占位符。
3. **一致性**：markdown-fit / --wait-for / interact 等漂移词在 Global Constraints、任务步骤、evals expected_behavior 三处一致；基线协议三个任务同构；工件路径 Task 1 产出与 Task 2 消费一致。
