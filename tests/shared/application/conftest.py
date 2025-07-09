from pathlib import Path
from typing import cast

import pytest
from sqlalchemy import Dialect

from lagransala.shared.infrastructure import FileCacheBackend, MemoryCacheBackend

from .helpers import SimpleData


@pytest.fixture
def dummy_dialect() -> Dialect:
    return cast(Dialect, None)


@pytest.fixture
def memory_cache_backend() -> MemoryCacheBackend[SimpleData]:
    return MemoryCacheBackend[SimpleData]()


@pytest.fixture
def file_cache_backend(tmp_path: Path) -> FileCacheBackend[SimpleData]:
    cache_dir = tmp_path / "test_cache"
    return FileCacheBackend(data_type=SimpleData, cache_dir=str(cache_dir))


@pytest.fixture
def non_html_urls():
    return [
        "https://example.com/aksjdhkaj/akdsjhakjsdh/image.jpg",
        "https://example.com/script.js",
        "https://example.com//aa/style.css?v=1.0",
        "https://example.com/robots.txt",
        "https://example.com/favicon.ico",
    ]


@pytest.fixture
def html_urls():
    return [
        "https://example.com/",
        "https://example.com/index.html",
        "https://example.com/page.php",
        "https://example.com/about",
        "https://example.com/contact/",
        "https://example.com/faq.html",
        "https://example.com/faq.htm",
        "https://example.com/fichero/sad.asp",
        "https://example.com/fichero/sad.aspx",
    ]
