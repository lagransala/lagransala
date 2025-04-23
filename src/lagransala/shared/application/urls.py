import html
from urllib.parse import urlparse

from bs4 import BeautifulSoup

HTML_EXTENSIONS = {"/", ".html", ".htm", ".php", ".asp", ".aspx", ".jsp"}


def is_html_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    if any(path.endswith(ext) for ext in HTML_EXTENSIONS):
        return True
    if "." not in path.split("/")[-1]:  # No extension, probably a route
        return True
    return False


def extract_urls(content: str) -> set[str]:
    soup = BeautifulSoup(content, "html.parser")
    urls = set()

    for tag in soup.find_all(["a", "link", "script", "img", "iframe", "source"]):
        attr = tag.get("href") or tag.get("src")  # type: ignore
        if attr:
            attr = html.unescape(attr)  # type: ignore
            if urlparse(attr).scheme in {"http", "https", ""} and is_html_url(attr):
                urls.add(attr)

    return urls
