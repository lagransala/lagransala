from lagransala.shared.application.markdown import extract_markdown


def test_extract_markdown() -> None:
    """Test that we can extract markdown from HTML."""
    html = """
    <html>
        <head>
            <title>My Title</title>
            <style>body { color: red; }</style>
        </head>
        <body>
            <header>My Header</header>
            <nav>My Nav</nav>
            <main>
                <h1>My H1</h1>
                <p>My paragraph.</p>
                <script>alert('hello');</script>
            </main>
            <footer>My Footer</footer>
        </body>
    </html>
    """
    expected_markdown = "# My H1\n\nMy paragraph."
    assert extract_markdown(html, main_selector="main") == expected_markdown
