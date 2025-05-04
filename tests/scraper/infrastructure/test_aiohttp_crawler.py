from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import HttpUrl

from lagransala.scraper.domain.crawler import CrawlResult
from lagransala.scraper.infrastructure.aiohttp_crawler import AiohttpCrawler


@pytest.mark.asyncio
async def test_aiohttp_crawler_basic_html_parsing():
    html_content = """
        <html>
            <body>
                <a href="https://example.com/page1.html">Page 1</a>
                <a href="/page2">Page 2</a>
                <a href="/page2?q=term">Page 2</a>
                <a href="https://example.com/image.png">Image</a>
                <a href="mailto:someone@example.com">Email</a>
                <a href="https://otherdomain.com/page3">External</a>
            </body>
        </html>
    """

    # Mock the response and .text()
    response_mock = MagicMock()
    response_mock.text = AsyncMock(return_value=html_content)
    response_mock.status = 200
    response_mock.content_type = "text/html"

    # Make sure the get call returns a context manager with our response
    context_manager_mock = MagicMock()
    context_manager_mock.__aenter__.return_value = response_mock
    context_manager_mock.__aexit__.return_value = AsyncMock()

    # Mock the session with get returning the context manager
    session_mock = MagicMock()
    session_mock.get.return_value = context_manager_mock

    crawler = AiohttpCrawler(session=session_mock)

    result: CrawlResult = await crawler.run(start_url=HttpUrl("https://example.com"))

    expected_paths = {"/page1.html", "/page2", "/page2?q=term"}

    assert result.start_url == HttpUrl("https://example.com")
    assert result.pages == expected_paths
