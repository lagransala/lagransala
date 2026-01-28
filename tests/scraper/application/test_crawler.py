from datetime import datetime
from typing import Iterable
from unittest.mock import AsyncMock

import pytest
from pydantic import HttpUrl

from lagransala.scraper.application.crawler import Crawler
from lagransala.scraper.domain import CrawlResult
from lagransala.shared.domain.fetcher import Fetcher, Response


class MockFetcher(Fetcher):
    def __init__(self, responses: dict[str, Response]):
        self._responses = responses

    async def fetch(self, url: HttpUrl) -> Response:
        return self._responses.get(
            str(url),
            Response(url=url, status=404, content="", content_type="text/html", dt=datetime.now())
        )

    async def fetch_urls(self, urls: Iterable[HttpUrl]) -> Iterable[Response]:
        return [await self.fetch(url) for url in urls]

    def fetch_task(self, url: HttpUrl) -> AsyncMock:
        return AsyncMock(return_value=self.fetch(url))

    def fetch_urls_tasks(self, urls: Iterable[HttpUrl]) -> Iterable[AsyncMock]:
        return (self.fetch_task(url) for url in urls)


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
            url=HttpUrl("https://example.com/"),
            status=200,
            content=html_content,
            content_type="text/html",
            dt=datetime.now(),
        ),
        "https://example.com/page1.html": Response(
            url=HttpUrl("https://example.com/page1.html"),
            status=200,
            content="",
            content_type="text/html",
            dt=datetime.now(),
        ),
        "https://example.com/page2": Response(
            url=HttpUrl("https://example.com/page2"),
            status=200,
            content="",
            content_type="text/html",
            dt=datetime.now(),
        ),
        "https://example.com/page2?q=term": Response(
            url=HttpUrl("https://example.com/page2?q=term"),
            status=200,
            content="",
            content_type="text/html",
            dt=datetime.now(),
        ),
        "https://example.com/image.png": Response(
            url=HttpUrl("https://example.com/image.png"),
            status=200,
            content="",
            content_type="image/png",
            dt=datetime.now(),
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
            url=start_url,
            status=200,
            content='<a href="/ok">OK</a><a href="/404">404</a><a href="/img">IMG</a><a href="/bad">BAD</a><a href="/filtered">FIL</a>',
            content_type="text/html",
            dt=datetime.now(),
        ),
        "https://example.com/ok": Response(
            url=HttpUrl("https://example.com/ok"),
            status=200,
            content="OK",
            content_type="text/html",
            dt=datetime.now(),
        ),
        "https://example.com/404": Response(
            url=HttpUrl("https://example.com/404"),
            status=404,
            content="",
            content_type="text/html",
            dt=datetime.now(),
        ),
        "https://example.com/img": Response(
            url=HttpUrl("https://example.com/img"),
            status=200,
            content="",
            content_type="image/png",
            dt=datetime.now(),
        ),
        "https://example.com/bad": Response(
            url=HttpUrl("https://example.com/bad"),
            status=200,
            content="",
            content_type="text/html",
            dt=datetime.now(),
        ),  # No unicode error check now
    }
    fetcher = MockFetcher(responses)

    def url_filter(url: HttpUrl) -> bool:
        return "filtered" not in str(url)

    crawler = Crawler(fetcher=fetcher, url_filter=url_filter)
    result = await crawler.run(start_url=start_url)

    assert result.pages == {"/ok", "/bad"}
