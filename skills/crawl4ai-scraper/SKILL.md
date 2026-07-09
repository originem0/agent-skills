---
name: crawl4ai-scraper
description: >
  使用 Crawl4AI 进行开源免费的网页抓取，输出 LLM 友好的 Markdown。
  完全本地运行，核心功能无需 API Key。支持单页抓取、深度爬取、
  CSS/XPath 结构化提取、LLM 提取、浏览器会话与登录态、内容过滤。
  Use when 用户要求免费抓取网页、本地爬虫、不想用付费 API 时。
  触发词：免费爬虫, 本地抓取, crawl4ai, scrape, crawl, extract, free
allowed-tools: Read Write Bash Glob Grep AskUserQuestion
---

# Crawl4AI Web Scraper

开源免费、本地运行的网页爬虫。将网页转为 LLM 友好的 Markdown，支持结构化数据提取。

**前置条件：** Python 3.10+，`pip install -U crawl4ai && crawl4ai-setup`。
环境有问题时运行 `scripts/check-env.sh` 诊断（内部调用 `crawl4ai-doctor`）。

## 模式选择

| 用户需求 | 方式 |
|----------|------|
| 单页转 Markdown | `crwl <url> -o markdown` |
| 整站/多页爬取 | `crwl <url> --deep-crawl bfs --max-pages <n>` |
| 规律页面提取结构化数据（免费） | `crwl <url> -e extract_css.yml -s css_schema.json -o json` |
| LLM 提取/问答（需配 API Key） | `crwl <url> -j "..."` 或 `-q "..."` |
| 登录、会话、JS 操作、截图等复杂场景 | Python API，见下方 examples 表 |

## CLI 单页抓取

```bash
crwl https://example.com -o markdown                        # 完整 Markdown
crwl https://example.com -o markdown-fit                    # 过滤噪音，最适合喂 LLM
crwl https://example.com -f filter_bm25.yml -o markdown-fit # 配合内容过滤器
crwl https://example.com -o markdown > result.md
```

`-o` 有效值：`all` / `json` / `markdown`（`md`）/ `markdown-fit`（`md-fit`）。
注意 `-f` 是内容过滤器配置文件（bm25/pruning），不是输出文件名；
截图、PDF 不走 CLI，用 Python API 的 `CrawlerRunConfig(screenshot=True, pdf=True)`。

## CLI 深度爬取

```bash
crwl https://docs.example.com --deep-crawl bfs --max-pages 10
```

策略：`bfs`（逐层，默认选它）/ `dfs`（先钻深）/ `best-first`（按相关性评分优先）。
用 `--max-pages` 控制规模。需要按 URL 模式过滤（只爬 `/docs/` 之类）时 CLI
不够用，改 Python API 的 `FilterChain` + `URLPatternFilter`（见 `gotchas.md`）。

## 结构化提取

结构规律的页面优先 CSS schema 提取——免费、快、结果确定：

```bash
crwl https://example.com/products -e extract_css.yml -s css_schema.json -o json
```

`-s` 指向字段 schema（`baseSelector` + `fields`），`-e` 指向提取策略配置。
运行 `crwl --example` 可查看这两个文件的完整样例。

页面不规律时兜底用 LLM 提取（需 API Key）：

```bash
crwl https://example.com/products -j "提取所有产品的名称和价格"  # 快速 JSON 提取
crwl https://example.com -q "这一页的要点是什么"                 # 对抓取内容问答
```

首次使用 LLM 功能会交互式询问 provider 和 API Token，保存到
`~/.crawl4ai/global.yml`（本地 ollama 无需 token）。

## 浏览器与爬虫配置

JS 渲染重、拿不到内容时，用 `-b`（浏览器）/`-c`（爬虫）内联 key=value 参数，
或 `-B`/`-C` 指向 YAML 配置文件，例如无限滚动页面
`crwl <url> -c "scan_full_page=true,delay_before_return_html=2"`。
常用键与细节见 `gotchas.md`。需要登录态时用 `crwl profiles` 创建浏览器 profile。

## Python API（复杂场景）

CLI 覆盖不了的（登录会话、JS 交互、URL 过滤、截图/PDF）用 Python。
统一模式：`arun(url=..., config=CrawlerRunConfig(...))`，运行参数全部进
config 对象，不再直接传给 `arun`。按需读取对应示例文件：

| 场景 | 示例文件 |
|------|---------|
| 基础抓取 + fit markdown | `examples/basic_crawl.py` |
| CSS 选择器提取（无需 LLM，最快） | `examples/css_extraction.py` |
| 带会话的多步抓取（翻页/登录） | `examples/session_crawl.py` |
| JS 操作（点击/滚动/等待） | `examples/js_interaction.py` |

## 更多信息

与 Firecrawl 对比、`-b/-c` 常用配置键、反爬机制、常见陷阱见 `gotchas.md`。
