"""Crawl4AI: JS execution — click buttons, scroll, wait for dynamic content."""
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig


async def main():
    config = CrawlerRunConfig(
        # js_code 在页面加载完成后执行；可选链避免元素不存在时报错
        js_code="document.querySelector('.load-more')?.click();",
        # wait_for 支持 "css:选择器" 或 "js:() => 布尔表达式"
        wait_for="css:.loaded-content",
        # 无限滚动页面改用 scan_full_page=True 自动滚到底
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com", config=config)
        print(result.markdown.raw_markdown)


asyncio.run(main())
