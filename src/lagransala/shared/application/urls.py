import html
import re
from typing import Pattern
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

HTML_EXTENSIONS = {"/", ".html", ".htm", ".php", ".asp", ".aspx", ".jsp"}


def absolutize_url(base: str, url: str) -> str:
    return urljoin(base, url)


def is_html_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    if any(path.endswith(ext) for ext in HTML_EXTENSIONS):
        return True
    if "." not in path.split("/")[-1]:  # No extension, probably a route
        return True
    return False


def extract_urls(
    content: str | BeautifulSoup, url_pattern: str | Pattern[str] | None = None
) -> set[str]:
    soup = (
        BeautifulSoup(content, "html.parser") if isinstance(content, str) else content
    )
    pattern = re.compile(url_pattern) if isinstance(url_pattern, str) else None
    urls = set()

    for tag in soup.find_all(["a", "link", "script", "img", "iframe", "source"]):
        attr = tag.get("href") or tag.get("src")  # type: ignore
        if attr:
            attr = html.unescape(attr)  # type: ignore
            if urlparse(attr).scheme in {"http", "https", ""} and is_html_url(attr):
                urls.add(attr)
    if pattern:
        urls = {url for url in urls if pattern.match(url)}
    return urls
