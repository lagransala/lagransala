from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import HttpUrl

from lagransala.scraper.domain import CrawlResult
from lagransala.scraper.infrastructure import AiohttpCrawler


@pytest.mark.asyncio
async def test_aiohttp_crawler_basic_html_parsing():
    # This test covers the happy path of basic HTML parsing and link extraction.
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

    session_mock = MagicMock()
    response_mock = MagicMock()
    response_mock.text = AsyncMock(return_value=html_content)
    response_mock.status = 200
    response_mock.content_type = "text/html"

    def side_effect(url):
        cm_mock = MagicMock()
        cm_mock.__aenter__.return_value = response_mock
        cm_mock.__aexit__ = AsyncMock(return_value=None)
        return cm_mock

    session_mock.get.side_effect = side_effect
    crawler = AiohttpCrawler(session=session_mock)
    result: CrawlResult = await crawler.run(start_url=HttpUrl("https://example.com"))

    expected_paths = {"/page1.html", "/page2", "/page2?q=term"}
    assert result.start_url == HttpUrl("https://example.com")
    assert result.pages == expected_paths


@pytest.mark.asyncio
async def test_aiohttp_crawler_edge_cases():
    # This test covers various edge cases to ensure robust error handling.
    start_url = HttpUrl("https://example.com")
    session_mock = MagicMock()

    def get_side_effect(url):
        response = MagicMock()
        response.status = 200
        response.content_type = "text/html"
        response.text = AsyncMock(return_value="")  # Default empty response

        if url == str(start_url):
            response.text = AsyncMock(
                return_value='<a href="/ok">OK</a><a href="/404">404</a><a href="/img">IMG</a><a href="/bad">BAD</a><a href="/filtered">FIL</a>'
            )
        elif url == "https://example.com/ok":
            response.text = AsyncMock(return_value="OK")
        elif url == "https://example.com/404":
            response.status = 404
        elif url == "https://example.com/img":
            response.content_type = "image/png"
        elif url == "https://example.com/bad":
            response.text = AsyncMock(
                side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "")
            )

        cm = MagicMock()
        cm.__aenter__.return_value = response
        cm.__aexit__ = AsyncMock(return_value=None)
        return cm

    session_mock.get.side_effect = get_side_effect

    def url_filter(url: HttpUrl) -> bool:
        return "filtered" not in str(url)

    crawler = AiohttpCrawler(session=session_mock, url_filter=url_filter)
    result = await crawler.run(start_url=start_url)

    assert result.pages == {"/ok"}
