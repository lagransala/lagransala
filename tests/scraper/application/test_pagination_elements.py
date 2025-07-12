import re
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from pydantic import HttpUrl
from yarl import URL

from lagransala.scraper.application import pagination_elements
from lagransala.scraper.domain import Pagination, PaginationType
from lagransala.shared.domain import Fetcher
from lagransala.shared.domain.fetcher import Response


@pytest.mark.asyncio
async def test_pagination_elements() -> None:
    fetcher = MagicMock(spec=Fetcher)
    response = Response(
        status=200,
        content='<html><a href="/page/1">1</a><a href="/page/2">2</a></html>',
        content_type="text/html",
    )
    fetcher.fetch_urls.return_value = [response]

    pagination = Pagination(
        venue_slug="test-venue",
        type=PaginationType.SIMPLE,
        url="http://example.com?page={n}",
        limit=1,
        simple_start_from=1,
        base_url=HttpUrl("http://example.com"),
        element_url_pattern=r"/page/\d",
    )
    urls = await pagination_elements(fetcher, pagination)

    assert urls == {
        str(URL("http://example.com/page/1")),
        str(URL("http://example.com/page/2")),
    }
