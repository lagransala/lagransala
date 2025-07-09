import pytest

from lagransala.shared.application import extract_urls
from lagransala.shared.application.urls import is_html_url


def test_is_html_url_false(non_html_urls):
    for url in non_html_urls:
        assert not is_html_url(url), f"URL {url} should not be considered HTML"


def test_is_html_url_true(html_urls):
    for url in html_urls:
        assert is_html_url(url), f"URL {url} should be considered HTML"


def test_extract_urls():
    content = """
            <html>
            <head>
                <link rel="stylesheet" href="styles/main.css">
                <script src="scripts/app.js"></script>
            </head>
            <body>
                <a href="https://example.com/page1.html">Link 1</a>
                <a href="https://example.com/page2.php?id=1&amp;n=4906">Link 2</a>
                <img src="/images/pic.jpg">
                <a href="/relative/path/">Relative Link</a>
                <a href="mailto:test@example.com">Email</a>
                <a href="ftp://example.com/file.txt">FTP Link</a>
                <a href="javascript:void(0)">JS Link</a>
                <div src="ignored">No link here</div>
            </body>
        </html>
    """

    expected = {
        "https://example.com/page1.html",
        "https://example.com/page2.php?id=1&n=4906",
        "/relative/path/",
    }

    result = extract_urls(content)

    assert result == expected


def test_extract_urls_with_pattern():
    content = """
        <html>
            <body>
                <a href="https://example.com/page1.html">Link 1</a>
                <a href="https://example.com/page2.php?id=1&amp;n=4906">Link 2</a>
                <a href="https://example.com/help.html">Help</a>
                <a href="/internal/path/about/">About</a>
                <a href="/internal/path/contact/">Contact</a>
            </body>
        </html>
    """

    # Only include URLs that contain "page"
    pattern = r".*page.*"

    expected = {
        "https://example.com/page1.html",
        "https://example.com/page2.php?id=1&n=4906",
    }

    result = extract_urls(content, pattern)

    assert result == expected
