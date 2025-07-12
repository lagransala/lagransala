import asyncio

import pytest
from aiohttp import ClientSession
from aioresponses import aioresponses

from lagransala.shared.domain.fetcher import Response
from lagransala.shared.infrastructure.aiohttp_fetcher import AiohttpFetcher
from lagransala.shared.infrastructure.memory_cache_backend import MemoryCacheBackend


@pytest.fixture
def memory_cache_backend() -> MemoryCacheBackend[Response]:
    return MemoryCacheBackend[Response]()


@pytest.mark.asyncio
async def test_fetch_without_cache() -> None:
    url = "http://example.com"
    content = "Hello, world!"
    async with ClientSession() as client:
        with aioresponses() as m:
            m.get(url, status=200, body=content)
            fetcher = AiohttpFetcher(client=client)
            response = await fetcher.fetch(url)
            assert response.status == 200
            assert response.content == content


@pytest.mark.asyncio
async def test_fetch_with_cache(
    memory_cache_backend: MemoryCacheBackend[Response],
) -> None:
    url = "http://example.com/cached"
    content = "This should be cached"
    async with ClientSession() as client:
        with aioresponses() as m:
            m.get(url, status=200, body=content, repeat=True)

            fetcher = AiohttpFetcher(
                client=client, cache_backend=memory_cache_backend, cache_ttl=60
            )

            # First call - should fetch and cache
            response1 = await fetcher.fetch(url)
            assert response1.status == 200
            assert response1.content == content

            # Second call - should hit the cache
            response2 = await fetcher.fetch(url)
            assert response2.status == 200
            assert response2.content == content

            # Check that the request was only made once
            assert len(m.requests) == 1


@pytest.mark.asyncio
async def test_fetch_urls() -> None:
    urls = ["http://example.com/1", "http://example.com/2"]
    contents = ["Page 1", "Page 2"]

    async with ClientSession() as client:
        with aioresponses() as m:
            m.get(urls[0], status=200, body=contents[0])
            m.get(urls[1], status=200, body=contents[1])

            fetcher = AiohttpFetcher(client=client)
            responses = await fetcher.fetch_urls(urls)

            assert len(responses) == 2
            assert responses[0].status == 200
            assert responses[0].content == contents[0]
            assert responses[1].status == 200
            assert responses[1].content == contents[1]


@pytest.mark.asyncio
async def test_fetch_is_assigned_when_no_cache_is_provided() -> None:
    async with ClientSession() as client:
        fetcher = AiohttpFetcher(client=client)
        assert hasattr(fetcher, "fetch")
        assert callable(fetcher.fetch)
