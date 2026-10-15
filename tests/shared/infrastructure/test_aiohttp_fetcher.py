from collections import Counter
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

import pytest
from aiohttp import ClientSession, web
from aiohttp.test_utils import TestServer
from pydantic import HttpUrl

from lagransala.shared.domain.fetcher import Response
from lagransala.shared.infrastructure.aiohttp_fetcher import AiohttpFetcher
from lagransala.shared.infrastructure.memory_cache_backend import MemoryCacheBackend


@asynccontextmanager
async def serve(
    pages: dict[str, str],
) -> AsyncGenerator[tuple[ClientSession, dict[str, HttpUrl], Counter[str]]]:
    """Serve `pages` (path -> body) on a local server.

    Yields a client, the url of every page and a counter of requests per path.
    """
    hits: Counter[str] = Counter()

    def handler(body: str) -> Callable[[web.Request], Awaitable[web.Response]]:
        async def respond(request: web.Request) -> web.Response:
            hits[request.path] += 1
            return web.Response(text=body, content_type="text/html")

        return respond

    app = web.Application()
    for path, body in pages.items():
        app.router.add_get(path, handler(body))

    async with TestServer(app) as server, ClientSession() as client:
        urls = {path: HttpUrl(str(server.make_url(path))) for path in pages}
        yield client, urls, hits


@pytest.fixture
def memory_cache_backend() -> MemoryCacheBackend[Response]:
    return MemoryCacheBackend[Response]()


@pytest.mark.asyncio
async def test_fetch_without_cache() -> None:
    content = "Hello, world!"
    async with serve({"/": content}) as (client, urls, _):
        fetcher = AiohttpFetcher(client=client)
        response = await fetcher.fetch(urls["/"])
        assert response.status == 200
        assert response.content == content
        assert response.content_type == "text/html"


@pytest.mark.asyncio
async def test_fetch_with_cache(
    memory_cache_backend: MemoryCacheBackend[Response],
) -> None:
    content = "This should be cached"
    async with serve({"/cached": content}) as (client, urls, hits):
        fetcher = AiohttpFetcher(
            client=client, cache_backend=memory_cache_backend, cache_ttl=60
        )

        # First call - should fetch and cache
        response1 = await fetcher.fetch(urls["/cached"])
        assert response1.status == 200
        assert response1.content == content

        # Second call - should hit the cache
        response2 = await fetcher.fetch(urls["/cached"])
        assert response2.status == 200
        assert response2.content == content

        # Check that the request was only made once
        assert hits["/cached"] == 1


@pytest.mark.asyncio
async def test_fetch_urls() -> None:
    contents = {"/1": "Page 1", "/2": "Page 2"}

    async with serve(contents) as (client, urls, _):
        fetcher = AiohttpFetcher(client=client)
        responses = await fetcher.fetch_urls([urls["/1"], urls["/2"]])

        assert len(responses) == 2
        assert responses[0].status == 200
        assert responses[0].content == contents["/1"]
        assert responses[1].status == 200
        assert responses[1].content == contents["/2"]


@pytest.mark.asyncio
async def test_fetch_is_assigned_when_no_cache_is_provided() -> None:
    async with ClientSession() as client:
        fetcher = AiohttpFetcher(client=client)
        assert hasattr(fetcher, "fetch")
        assert callable(fetcher.fetch)
