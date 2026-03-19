"""Crawl4AI: Session-based multi-step crawl — for pagination or login flows."""
import asyncio
from crawl4ai import AsyncWebCrawler


async def main():
    async with AsyncWebCrawler() as crawler:
        # Step 1: open first page
        result = await crawler.arun(
            url="https://example.com/page/1",
            session_id="my_session"
        )
        print(f"Page 1: {len(result.markdown)} chars")

        # Step 2: next page in same session (cookies/state preserved)
        result = await crawler.arun(
            url="https://example.com/page/2",
            session_id="my_session"
        )
        print(f"Page 2: {len(result.markdown)} chars")


asyncio.run(main())
