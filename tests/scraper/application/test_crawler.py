from unittest.mock import AsyncMock

import pytest
from pydantic import HttpUrl

from lagransala.scraper.application.crawler import Crawler
from lagransala.scraper.domain import CrawlResult
from lagransala.shared.domain.fetcher import Fetcher, Response


class MockFetcher(Fetcher):
    def __init__(self, responses: dict[str, Response]):
        self._responses = responses

    async def fetch(self, url: str) -> Response:
        return self._responses.get(
            url, Response(status=404, content="", content_type="text/html")
        )

    async def fetch_urls(self, urls: list[str]) -> list[Response]:
        return [await self.fetch(url) for url in urls]


@pytest.mark.asyncio
async def test_crawler_basic_html_parsing():
    html_content = """
        <html>
            <body>
                <a href="/page1.html">Page 1</a>
                <a href="/page2">Page 2</a>
                <a href="/page2?q=term">Page 2</a>
                <a href="/image.png">Image</a>
                <a href="mailto:someone@example.com">Email</a>
                <a href="https://otherdomain.com/page3">External</a>
            </body>
        </html>
    """

    responses = {
        "https://example.com/": Response(
            status=200, content=html_content, content_type="text/html"
        ),
        "https://example.com/page1.html": Response(
            status=200, content="", content_type="text/html"
        ),
        "https://example.com/page2": Response(
            status=200, content="", content_type="text/html"
        ),
        "https://example.com/page2?q=term": Response(
            status=200, content="", content_type="text/html"
        ),
        "https://example.com/image.png": Response(
            status=200, content="", content_type="image/png"
        ),
    }
    fetcher = MockFetcher(responses)

    crawler = Crawler(fetcher=fetcher)
    result: CrawlResult = await crawler.run(start_url=HttpUrl("https://example.com/"))

    expected_paths = {"/page1.html", "/page2", "/page2?q=term"}
    assert result.start_url == HttpUrl("https://example.com/")
    assert result.pages == expected_paths


@pytest.mark.asyncio
async def test_crawler_edge_cases():
    start_url = HttpUrl("https://example.com/")
    responses = {
        str(start_url): Response(
            status=200,
            content='<a href="/ok">OK</a><a href="/404">404</a><a href="/img">IMG</a><a href="/bad">BAD</a><a href="/filtered">FIL</a>',
            content_type="text/html",
        ),
        "https://example.com/ok": Response(
            status=200, content="OK", content_type="text/html"
        ),
        "https://example.com/404": Response(
            status=404, content="", content_type="text/html"
        ),
        "https://example.com/img": Response(
            status=200, content="", content_type="image/png"
        ),
        "https://example.com/bad": Response(
            status=200, content="", content_type="text/html"
        ),  # No unicode error check now
    }
    fetcher = MockFetcher(responses)

    def url_filter(url: HttpUrl) -> bool:
        return "filtered" not in str(url)

    crawler = Crawler(fetcher=fetcher, url_filter=url_filter)
    result = await crawler.run(start_url=start_url)

    assert result.pages == {"/ok", "/bad"}
