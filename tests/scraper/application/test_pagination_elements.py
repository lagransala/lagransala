import re
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from aiohttp import ClientSession
from pydantic import HttpUrl
from yarl import URL

from lagransala.scraper.application import pagination_elements
from lagransala.scraper.domain import Pagination, PaginationType


@pytest.mark.asyncio
async def test_pagination_elements() -> None:
    session = MagicMock(spec=ClientSession)
    response = MagicMock()

    async def mock_text() -> str:
        return '<html><a href="/page/1">1</a><a href="/page/2">2</a></html>'

    response.text = mock_text

    async def __aenter__(*args, **kwargs):  # type: ignore[no-untyped-def]
        return response

    async def __aexit__(*args, **kwargs):  # type: ignore[no-untyped-def]
        pass

    session.get.return_value = MagicMock(__aenter__=__aenter__, __aexit__=__aexit__)

    pagination = Pagination(
        id=uuid4(),
        type=PaginationType.SIMPLE,
        url="http://example.com?page={n}",
        limit=1,
        simple_start_from=1,
        base_url=HttpUrl("http://example.com"),
        element_url_pattern=r"/page/\d",
    )
    urls = await pagination_elements(session, pagination, re.compile(r"/page/\d"))

    assert urls == {
        str(URL("http://example.com/page/1")),
        str(URL("http://example.com/page/2")),
    }
