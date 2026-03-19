---
name: firecrawl-scraper
description: >
  使用 Firecrawl CLI 抓取网页并转换为 LLM 友好的 Markdown、结构化 JSON 或截图。
  支持单页抓取、全站爬取、站点地图发现、网页搜索、浏览器自动化。
  可处理 JS 渲染、动态内容、PDF/DOCX 解析。
  触发场景：用户要求抓取网页内容、提取网站数据、爬取整站、搜索网页信息时使用。
  关键词：scrape, crawl, web, extract, firecrawl, 抓取, 爬虫
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
---

# Firecrawl Web Scraper

云端网页抓取服务，将任意网页转换为干净的 Markdown 或结构化数据。

**前置条件：** Node.js 20.6+, `npm install -g firecrawl-cli`, API Key（[firecrawl.dev](https://firecrawl.dev)，免费 500 credits/月）。环境有问题时运行 `scripts/check-env.sh` 诊断。

## 模式选择

| 用户需求 | 命令 |
|----------|------|
| 抓取单个页面 | `firecrawl scrape <url>` |
| 爬取整个网站 | `firecrawl crawl <url>` |
| 发现网站所有 URL | `firecrawl map <url>` |
| 搜索网页内容 | `firecrawl search <query>` |
| 浏览器交互（点击/滚动/输入） | `firecrawl browse <url>` |
| AI 自动抓取（描述需求即可） | `firecrawl agent "<描述>"` |

## Scrape（单页）

```bash
firecrawl scrape https://example.com                           # Markdown
firecrawl scrape https://example.com --only-main-content       # 只正文
firecrawl scrape https://example.com -f json                   # JSON
firecrawl scrape https://example.com -f screenshot             # 截图
firecrawl scrape https://example.com --extract "提取所有产品名称和价格"
firecrawl scrape https://example.com -o result.md              # 保存到文件
```

| 参数 | 说明 |
|------|------|
| `--only-main-content` | 只提取正文 |
| `-f markdown\|html\|json\|screenshot` | 输出格式 |
| `--extract "<schema>"` | 自然语言描述要提取的结构化数据 |
| `--wait <ms>` | 等待 JS 渲染 |
| `-o <file>` | 保存到文件 |
| `--include-tags <tags>` | 只保留指定 HTML 标签 |
| `--exclude-tags <tags>` | 排除指定 HTML 标签 |

## Crawl（全站）

```bash
firecrawl crawl https://docs.example.com --limit 50
firecrawl crawl https://docs.example.com --limit 20 -o ./output/
```

| 参数 | 说明 |
|------|------|
| `--limit <n>` | 最大页面数 |
| `--max-depth <n>` | 最大深度 |
| `--include-glob <pattern>` | 只爬匹配 URL |
| `--exclude-glob <pattern>` | 排除匹配 URL |

## Map / Search / Browse / Agent

```bash
firecrawl map https://example.com                              # 发现所有 URL
firecrawl search "Python asyncio tutorial" --limit 5           # 搜索
firecrawl browse https://example.com --actions "click:#login-btn,wait:2000,screenshot"
firecrawl agent "去 Hacker News 找到今天排名前 5 的帖子及其链接"
```

## 更多信息

额度管理、认证方式、常见陷阱见 `gotchas.md`。
