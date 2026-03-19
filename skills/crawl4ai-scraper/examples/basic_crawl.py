"""Crawl4AI: Basic async crawl — single page to Markdown."""
import asyncio
from crawl4ai import AsyncWebCrawler


async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com")
        print(result.markdown)       # 完整 Markdown
        print(result.fit_markdown)   # 过滤后的 Markdown


asyncio.run(main())
