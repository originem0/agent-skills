---
name: crawl4ai-scraper
description: >
  使用 Crawl4AI 进行开源免费的网页抓取，输出 LLM 友好的 Markdown。
  完全本地运行，无需 API Key。支持单页抓取、深度爬取、LLM 结构化提取、
  CSS/XPath 选择器提取、浏览器会话管理、代理、截图。
  触发场景：用户要求免费抓取网页、本地爬虫、不想用付费 API 时使用。
  关键词：crawl4ai, scrape, crawl, extract, free, 免费爬虫, 本地抓取
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
---

# Crawl4AI Web Scraper

开源免费、本地运行的网页爬虫。将网页转为 LLM 友好的 Markdown，支持结构化数据提取。

**前置条件：** Python 3.10+, `pip install -U crawl4ai && crawl4ai-setup`。环境有问题时运行 `scripts/check-env.sh` 诊断。

## 模式选择

| 用户需求 | 模式 | 方式 |
|----------|------|------|
| 抓取单个页面为 Markdown | CLI 单页 | `crwl <url>` |
| 深度爬取多个页面 | CLI 深度爬取 | `crwl <url> --deep-crawl bfs` |
| 用 AI 提取结构化数据 | CLI + LLM | `crwl <url> -q "提取..."` |
| 复杂场景（登录/会话/自定义） | Python API | 见 `examples/` |

## CLI 单页抓取

```bash
crwl https://example.com -o markdown          # 完整 Markdown
crwl https://example.com -o fit_markdown      # 过滤噪音，最适合 LLM
crwl https://example.com -o html              # 清洗后 HTML
crwl https://example.com -o screenshot -f screenshot.png
crwl https://example.com -o markdown > result.md
```

## CLI 深度爬取

```bash
crwl https://docs.example.com --deep-crawl bfs --max-pages 10
crwl https://docs.example.com --deep-crawl dfs --max-pages 20
crwl https://docs.example.com --deep-crawl bfs --max-pages 50 \
  --include-pattern "/docs/.*"
```

| 参数 | 说明 |
|------|------|
| `--deep-crawl bfs\|dfs` | 爬取策略 |
| `--max-pages <n>` | 最大页面数 |
| `--include-pattern <regex>` | 只爬匹配 URL |
| `--exclude-pattern <regex>` | 排除匹配 URL |

## LLM 结构化提取

```bash
crwl https://example.com/products -q "提取所有产品的名称、价格和描述"
crwl https://example.com/products -q "Extract product names and prices" \
  --llm-provider openai/gpt-4o-mini
```

需要配置 LLM API Key 环境变量（`OPENAI_API_KEY` / `ANTHROPIC_API_KEY`）。

## Python API（复杂场景）

需要登录、会话管理、JS 操作、CSS 选择器提取时用 Python。按需读取对应示例文件：

| 场景 | 示例文件 |
|------|---------|
| 基础异步抓取 | `examples/basic_crawl.py` |
| CSS 选择器提取（无需 LLM，最快） | `examples/css_extraction.py` |
| 带会话的多步抓取（翻页/登录） | `examples/session_crawl.py` |
| JS 操作（点击/滚动/等待） | `examples/js_interaction.py` |

## 更多信息

对比 Firecrawl、常见陷阱和使用建议见 `gotchas.md`。
