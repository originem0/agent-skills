"""Crawl4AI: JS execution — click buttons, scroll, wait for dynamic content."""
import asyncio
from crawl4ai import AsyncWebCrawler


async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.com",
            js_code=[
                "document.querySelector('.load-more').click()",
                "await new Promise(r => setTimeout(r, 2000))"
            ],
            wait_for="css:.loaded-content"
        )
        print(result.markdown)


asyncio.run(main())
