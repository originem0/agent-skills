"""Crawl4AI: CSS selector extraction — no LLM needed, fastest method."""
import asyncio
import json
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

schema = {
    "name": "Products",
    "baseSelector": ".product-card",
    "fields": [
        {"name": "title", "selector": "h2", "type": "text"},
        {"name": "price", "selector": ".price", "type": "text"},
        {"name": "link", "selector": "a", "type": "attribute", "attribute": "href"}
    ]
}


async def main():
    strategy = JsonCssExtractionStrategy(schema)
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.com/products",
            extraction_strategy=strategy
        )
        data = json.loads(result.extracted_content)
        print(json.dumps(data, indent=2, ensure_ascii=False))


asyncio.run(main())
