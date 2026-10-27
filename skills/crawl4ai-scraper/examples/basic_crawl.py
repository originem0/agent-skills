"""Crawl4AI: Basic async crawl — single page to Markdown (raw + fit)."""
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
# v0.9.4+ 默认 pruning 实现，参数与输出同旧版 PruningContentFilter（后者直接使用会报 DeprecationWarning）
from crawl4ai import PruningContentFilterLXML


async def main():
    # fit_markdown 只在配置了 content filter 时生成，否则为 None
    config = CrawlerRunConfig(
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilterLXML(threshold=0.4, threshold_type="fixed")
        )
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com", config=config)
        print(result.markdown.raw_markdown)  # 完整 Markdown
        print(result.markdown.fit_markdown)  # 过滤后的 Markdown，适合喂 LLM
        # 注意：v0.5 起 result.fit_markdown 顶层属性已移除，必须经 result.markdown 访问


asyncio.run(main())
