# 工具类 Skill 更新（子项目 2）设计文档

日期：2026-07-09
状态：已批准（2026-07-09 范围变更：**firecrawl-scraper 整体跳过**——用户不做 firecrawl 认证，该 skill 本轮不重构，其已知漂移（browse→interact 等）记录在案待后续处理。子项目 2 范围收窄为 crawl4ai-scraper + widget-viewer。crawl4ai 的 ground truth 由 firecrawl 抓取降级为 WebSearch。）
前置：子项目 1（skill 编写规范，已合并 f476fe4）。本 spec 的验收标准即 `docs/skill-authoring.md`。

## 目标

将 crawl4ai-scraper、firecrawl-scraper、widget-viewer 三个工具类 skill 更新到与上游工具现状一致，并按 `docs/skill-authoring.md` 完成结构合规改造，附评估场景与真实执行验证。

## 已确认的决策

1. **crawl4ai 不在本机安装**（用户拍板）：事实核对以 v0.9.x 官方文档为准，不做真实抓取验证。这是对规范"真实执行验证"条款的**显式豁免**，须在该 skill 的 gotchas 中标注"命令核对于 2026-07 官方文档（v0.9.x），未本机实测"。
2. **firecrawl 更新到最新版**（1.14.8 → 1.19.24）并登录做真实验证：用户在会话内运行 `! firecrawl login`，验证消耗 credits 预算 <10。
3. **widget-viewer** 无上游漂移，做规范对齐 + 真实渲染验证。

## 调研基线（2026-07-09 确认的过时事实）

### firecrawl-scraper（对照本地 1.14.8 --help 已确认，最终以 1.19.24 为准）
- `browse` 命令不存在 → `interact`；`agent` 语义更新
- `--wait <ms>` → `--wait-for <ms>`；`--extract "<schema>"` 不存在 → `-Q/--query <prompt>`
- `-f <formats>` 支持多格式；截图独立为 `--screenshot` / `--full-page-screenshot`
- crawl：`--include-glob/--exclude-glob` → `--include-paths/--exclude-paths`；新增 `--sitemap`、`--crawl-entire-domain`、`--allow-subdomains`、job 状态（`--status`/`--wait`/`--progress`）
- scrape 默认保存 `.firecrawl/`（应提示加入 .gitignore）；认证：`firecrawl login` / `config` / `FIRECRAWL_API_KEY`；`firecrawl --status` 可查额度
- 新增顶层命令：`init`、`setup skills|mcp`、`env`、`view-config`、`experimental|x`

### crawl4ai-scraper（对照 v0.9.x 官方文档）
- `-o fit_markdown` → `-o markdown-fit`
- 深爬策略：bfs / dfs / **best-first**（skill 缺最后一个）
- 新增：`-j`（快速 JSON 提取）、`-B/-b/-C/-c` 配置体系（YAML 文件 + 内联参数，内联覆盖文件）、profile 认证、`--example`
- gotchas 补充：v0.8.5+ 自动反爬检测与代理升级、深爬 resume/cancel、`~/.crawl4ai/global.yml` 存 token
- `examples/*.py` 的 Python API 签名逐一对照当前文档修正

### widget-viewer
- 目录改名：`reference/` → `references/`、`templates/` → `assets/`（SKILL.md 内路径引用同步）
- frontmatter 加 `compatibility`（Windows + WebView2 + claude-widget-viewer on PATH）

## 统一动作（三个 skill 都做）

- `allowed-tools` 改为空格分隔字符串（规范 §1）；无该字段的不新增
- description 按规范模板校对（第三人称 + Use when + 中英双语触发词）
- `evals/` 目录 ≥3 个 JSON 场景（`{query, files?, expected_behavior[]}`）
- **基线先行**：重构前对每个 skill 的 evals 场景跑无-skill 基线（子代理不加载 skill 回答场景 query，记录行为差距到 `evals/baseline.md`）；重构后同场景复验
- SKILL.md < 500 行、引用一层深、术语一致、给默认方案 + 逃生舱

## 验证矩阵

| skill | 事实核对 ground truth | 真实执行 | evals+基线 |
|-------|----------------------|---------|-----------|
| firecrawl-scraper | 本地 1.19.24 `--help`（含各子命令） | ✓ scrape 单页 / map / search / `-Q` 各一次，<10 credits | ✓ |
| crawl4ai-scraper | v0.9.x 官方文档（docs.crawl4ai.com） | ✗ 已批准豁免，gotchas 标注 | ✓（标注未实测） |
| widget-viewer | 自家 repo（github.com/originem0/claude-widget-viewer） | ✓ 写真实 widget 触发 hook 渲染 | ✓ |

收尾：安装器真实运行（junction 全量刷新无 [ERR]）+ 既有三套测试回归（platform-filter 12+12、link-ops 8）+ README 技能列表与各 skill 描述一致性校对。

## 实施结构（方案 A，已确认）

每 skill 一个任务，顺序 firecrawl → crawl4ai → widget-viewer（firecrawl 有外部依赖用户登录，先做以尽早暴露阻塞），最后一个收尾验证任务。每任务独立提交、独立审查。

## 范围外

- PERO 两个 skill（子项目 3）
- crawl4ai 本机安装与实测
- skill 改名（PEROlearn/PEROfeynman 大写 name 留子项目 3）
- 安装脚本与测试套件改动（除非本子项目验证暴露缺陷）
- widget-viewer 上游 repo（exe/hook）的改动

## 验收标准

1. 三个 SKILL.md 的每条命令/参数可追溯到对应 ground truth（firecrawl: --help 输出；crawl4ai: 官方文档页；widget-viewer: 自家 repo）。
2. 规范检查单逐项通过（docs/skill-authoring.md 附录）。
3. 每 skill `evals/` ≥3 场景 + baseline.md（重构前基线 + 重构后复验记录）。
4. firecrawl 与 widget-viewer 真实执行验证留有输出记录；crawl4ai 豁免标注到位。
5. 收尾回归全绿。
