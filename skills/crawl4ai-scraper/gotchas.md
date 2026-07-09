# Gotchas & Tips

> 本 skill 命令核对于 2026-07 官方文档（v0.9.x），未本机实测。如实际执行报错，以 `crwl --help` 为准并反馈更新。

## Crawl4AI vs Firecrawl

| 维度 | Crawl4AI | Firecrawl |
|------|----------|-----------|
| 费用 | 完全免费（Apache-2.0，本地跑） | 有限免费额度，之后按 credits 付费（额度以官网为准） |
| 运行方式 | 本地运行 | 云 API |
| API Key | 核心功能不需要（LLM 提取/问答除外） | 需要 |
| 速度 | 取决于本机和网络 | 云端集群，通常更快 |
| 反爬处理 | v0.8.5+ 内置自动反爬回退（见下） | 内置代理池和反爬绕过 |
| 结构化提取 | CSS/XPath（免费）+ LLM 双模式 | LLM extract |
| 适合场景 | 免费使用、隐私敏感、自定义需求高 | 快速接入、大规模、不想管基础设施 |

## `-b/-c` 常用配置键

内联格式为逗号分隔的 `key=value`（自动类型推断），同名键覆盖 `-B`/`-C` YAML 文件中的值：

- `-b`（浏览器）：`headless`、`viewport_width`、`user_agent_mode=random`
- `-c`（爬虫）：`scan_full_page`（无限滚动页自动滚到底）、`delay_before_return_html`、
  `wait_until`（如 `networkidle`）、`page_timeout`、`css_selector`（只取某区域）、
  `remove_overlay_elements`（去弹窗遮罩）、`scroll_delay`、`cache_mode`、`magic`

例：`crwl <url> -c "css_selector=#main,scan_full_page=true,delay_before_return_html=2"`

## Common Gotchas

- `markdown-fit` 是最适合喂 LLM 的 CLI 输出格式（旧名 `fit_markdown` 已改名，用旧名会报错）
- Python API 侧 `fit_markdown` 只在配置了 content filter（Pruning/BM25）时才有值，
  且 v0.5 起必须经 `result.markdown.fit_markdown` 访问（顶层 `result.fit_markdown` 已移除）
- 老代码把 `js_code`/`session_id`/`extraction_strategy` 直接传给 `arun()` 已过时，
  统一放进 `CrawlerRunConfig` 再以 `config=` 传入
- CSS 提取比 LLM 提取快得多且免费，结构规律的页面优先 CSS schema（`-e`/`-s` 或
  `JsonCssExtractionStrategy`）；`crwl --example` 可看配置文件样例
- LLM 提取/问答（`-j`/`-q`）首次运行会交互式配置 provider 和 API Token，
  存入 `~/.crawl4ai/global.yml`；本地 ollama 无需 token
- v0.8.5+ 反爬自动升级：被封锁时自动回退到隐身浏览器/代理逐级升级，多数情况无需手动配置
  （详见 docs.crawl4ai.com/advanced/anti-bot-and-fallback/）
- 需要登录态的站点用 `crwl profiles` 交互式创建 profile（浏览器里登录后按 `q` 保存，
  存于 `~/.crawl4ai/profiles/`）
- 深爬用 `--max-pages` 控制规模；CLI 没有 `--include-pattern`/`--exclude-pattern`，
  按 URL 模式过滤要走 Python API：`crawl4ai.deep_crawling.filters` 的
  `FilterChain` + `URLPatternFilter`（`reverse=True` 做排除）
