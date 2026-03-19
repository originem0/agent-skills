# Gotchas & Tips

## Crawl4AI vs Firecrawl

| 维度 | Crawl4AI | Firecrawl |
|------|----------|-----------|
| 费用 | 完全免费 | 免费 500 credits/月，之后付费 |
| 运行方式 | 本地运行 | 云 API |
| API Key | 不需要 | 需要 |
| 速度 | 取决于本机和网络 | 云端集群，通常更快 |
| 反爬处理 | 基础（需自己配代理） | 内置代理池和反爬绕过 |
| 结构化提取 | CSS + LLM 双模式 | LLM extract |
| 适合场景 | 免费使用、隐私敏感、自定义需求高 | 快速接入、大规模、不想管基础设施 |

## Common Gotchas

- 页面需要 JS 渲染时 CLI 默认已用 Chromium，通常无需额外配置
- CSS 提取比 LLM 提取快得多且免费，结构规律的页面优先用 CSS schema
- 大规模爬取用 `--max-pages` 控制范围，避免爬到不相关页面
- LLM 提取需要设置对应 provider 的 API Key 环境变量（`OPENAI_API_KEY` / `ANTHROPIC_API_KEY`）
- `fit_markdown` 是最适合喂给 LLM 的格式，自动去噪
