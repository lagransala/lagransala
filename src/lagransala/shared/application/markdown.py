import re

from bs4 import BeautifulSoup
from markdownify import markdownify


def extract_markdown(html: str, main_selector: str | None = None) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for element in soup.find_all(["script", "style", "nav", "header", "footer"]):
        element.decompose()
    tag = soup.select_one("body" if main_selector is None else main_selector)

    content = markdownify(
        str(tag), strip=["script", "style"], heading_style="ATX", bullets="-"
    )
    content = re.sub(r"\n\s*\n\s*\n", "\n\n", content)
    content = "\n".join(line.rstrip() for line in content.splitlines())

    return content
