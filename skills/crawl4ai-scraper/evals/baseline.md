# crawl4ai-scraper 基线记录

## 重构前基线（裸答，未读 skill 文档 / 未搜索，2026-07-09）

说明：以下为模型仅凭训练记忆对 3 个 eval 场景的回答，用于对比重构后 skill 的增益。
（诚实标注：任务指令中已提前告知部分漂移点，裸答中标注了"若无提示我会怎么答"。）

### 场景 1: local-docs-crawl

> 不想花钱用云服务，帮我把 docs.example.com 整个文档站在本地抓下来喂给 LLM

裸答要点：
- 推荐 Crawl4AI（开源、完全本地、无需 API Key），CLI 命令 `crwl`。
- 深度爬取：`crwl https://docs.example.com --deep-crawl bfs --max-pages 50`。
- 输出格式：**若无提示，我会写 `-o markdown` 并提到 `fit_markdown`（过滤噪声、适合喂 LLM）**——这是旧版叫法。我记忆中的 CLI 输出值停留在 `markdown` / `markdown-fit` / `json` 混杂状态，不确定当前有效值，倾向凭旧记忆写出 `fit_markdown`。
- 深爬策略我记得有 bfs/dfs，**best-first 不确定是否在 CLI 暴露**。
- `--include-pattern` / `--exclude-pattern` 是否存在：不确定，可能凭印象编造。

判定：部分错误。核心方向对（deep-crawl + max-pages + 本地免费定位），但输出格式值会写错（fit_markdown），策略清单不全，过滤参数可能编造。

### 场景 2: css-extract

> 用 crawl4ai 从一个结构很规律的产品列表页提取名称和价格

裸答要点：
- 优先推荐 CSS schema 提取（`JsonCssExtractionStrategy`，免费、快、不烧 token），结构规律的页面不需要 LLM。
- Python API：schema 含 `baseSelector` + `fields`（name/selector/type）。
- CLI：记得有 `-e extract.yml -s schema.json -o json` 的用法，**但对 -e/-s 各自装什么（策略配置 vs schema）记忆模糊**。
- LLM 提取作为替代：`LLMExtractionStrategy` 需要 provider + API key。
- **不知道新的 `-j` 快速 JSON 提取参数**——裸答不会提。

判定：大方向正确（CSS 优先、免 LLM），CLI 细节模糊，新参数 `-j` 完全缺失。

### 场景 3: js-heavy-page

> crawl4ai 抓一个 JS 渲染很重的页面拿不到内容怎么办

裸答要点：
- Python API 层面记得较清楚：`wait_for`、`delay_before_return_html`、`js_code`、`scan_full_page`（无限滚动）、`magic=True`。
- CLI 层面：记得有 `-b`（browser config）/`-c`（crawler config）内联 key=value 或 YAML 文件，**但 -B/-C 大写变体（全局默认配置）完全不知道**。
- 不确定 `magic` 参数在 0.9.x 是否仍推荐（v0.8.5 后有自动反爬升级，我记忆中没有这个机制的细节）。
- 有编造风险的点：wait_for 的 `css:`/`js:` 前缀语法细节、`page_timeout` 默认值。

判定：Python 侧基本正确，CLI 配置体系（-B/-b/-C/-c 四件套）不完整，v0.8.5+ 自动反爬机制缺失。

### 基线小结

| 场景 | 裸答质量 | 主要缺口 |
|------|---------|---------|
| local-docs-crawl | 部分错误 | fit_markdown 旧名、best-first 缺失、过滤参数不确定 |
| css-extract | 方向对细节糊 | -e/-s 分工模糊、-j 缺失 |
| js-heavy-page | Python 对 CLI 糊 | -B/-C 全局配置缺失、自动反爬机制缺失 |

## 重构后复验（读重写后的 SKILL.md + gotchas.md 作答，2026-07-09）

### 场景 1: local-docs-crawl

- ✅ `crwl https://docs.example.com --deep-crawl bfs --max-pages <n>`（SKILL.md 模式选择表 + 深度爬取节）
- ✅ 输出格式给出 `-o markdown-fit`，并明确旧名 `fit_markdown` 已改名会报错（gotchas 首条）
- ✅ 完全本地、核心功能无需 API Key 的定位在 description 与正文首段
- 增益：best-first 策略补齐；URL 模式过滤明确指向 Python API FilterChain（裸答会编造 --include-pattern）

### 场景 2: css-extract

- ✅ 优先推荐 CSS schema（SKILL.md 结构化提取节明示"免费、快、结果确定"）
- ✅ `-e extract_css.yml -s css_schema.json -o json` 与官方 CLI 文档一致，-e/-s 分工写明，`--example` 可查样例
- ✅ LLM 替代路径（`-j`/`-q`）+ 首次交互式配 provider/token 存 global.yml
- 增益：裸答缺失的 `-j` 快速提取补齐；Python 侧 JsonCssExtractionStrategy 走 CrawlerRunConfig（examples/css_extraction.py 已核正）

### 场景 3: js-heavy-page

- ✅ `-b`/`-c` 内联 + `-B`/`-C` YAML 双通道，示例含 `scan_full_page=true,delay_before_return_html=2`（SKILL.md 配置节 + gotchas 常用键表）
- ✅ 无限滚动 → `scan_full_page`（SKILL.md 与 js_interaction.py 注释双处）
- ✅ 所有参数均有 2026-07 文档出处（-o 有效值枚举、-f 语义纠正），未编造参数；未核实的 --include-pattern 等已删除
- 增益：-B/-C 全局 YAML 配置、v0.8.5+ 自动反爬回退均为裸答完全缺失的内容

### 复验小结

3 个场景的 expected_behavior 全部命中。基线中的三类错误（旧格式名、编造过滤参数、
配置体系缺失）在重写后均有对应的正确内容与出处。命令未本机实测（已批准豁免，
gotchas 顶部标注，以 `crwl --help` 为准）。
