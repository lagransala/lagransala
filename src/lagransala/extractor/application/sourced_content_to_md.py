from lagransala.extractor.domain.sourced_content import ContentFormat
from lagransala.shared.application.markdown import extract_markdown

from ..domain import SourcedContent


def sourced_content_to_md(
    content: SourcedContent, main_selector: str | None
) -> SourcedContent:
    if content.fmt == ContentFormat.MD:
        return content
    assert (
        content.fmt == ContentFormat.HTML
    ), "Content must be in HTML format to convert to Markdown"
    assert content.content is not None, "Content cannot be None for HTML format"

    md_content = extract_markdown(content.content, main_selector=main_selector)

    return SourcedContent(url=content.url, content=md_content, fmt=ContentFormat.MD)
