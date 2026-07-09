"""Crawl4AI: Session-based multi-step crawl — for pagination or login flows."""
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig


async def main():
    # 同一 session_id 的多次 arun 复用同一浏览器 tab（cookies/登录态保留）
    config = CrawlerRunConfig(session_id="my_session")

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com/page/1", config=config)
        print(f"Page 1: {len(result.markdown.raw_markdown)} chars")

        result = await crawler.arun(url="https://example.com/page/2", config=config)
        print(f"Page 2: {len(result.markdown.raw_markdown)} chars")

        # SPA 页面不重新导航、只执行 JS 更新时，后续调用在 config 里加
        # js_only=True 并配合 js_code（如点击"下一页"按钮）


asyncio.run(main())
