# Gotchas & Tips

## 额度管理

- 免费额度每月 500 credits，单次 scrape 消耗 1 credit
- 大规模抓取前先用 `firecrawl map <url>` 评估网站规模，避免浪费额度

## 常见问题

- 动态页面加 `--wait 3000` 等待 JS 渲染完成
- `--only-main-content` 去掉导航栏/页脚噪音，喂 LLM 时优先使用
- `--extract` 用自然语言描述 schema 即可，不需要写 JSON schema
- 遵守目标网站的 robots.txt 和使用条款

## 认证方式（优先级）

1. `firecrawl login --browser` — 浏览器登录，最简单
2. `firecrawl login --api-key fc-YOUR_API_KEY` — 直接用 API Key
3. `export FIRECRAWL_API_KEY=fc-YOUR_API_KEY` — 环境变量

## vs Crawl4AI

Firecrawl 是云服务，Crawl4AI 是本地运行。详细对比见 `../crawl4ai-scraper/gotchas.md`。
