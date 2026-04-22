import pytest
from unittest.mock import patch, MagicMock
from shane_skills.integrations.web_client import WebClient

class MockResponse:
    def __init__(self, text, encoding="utf-8"):
        self.text = text
        self.apparent_encoding = encoding
    def raise_for_status(self):
        pass

def test_fetch_success():
    client = WebClient()
    html = """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <nav>Menu</nav>
            <main>
                <h1>Heading</h1>
                <p>Content</p>
                <div class="sidebar">Ads</div>
            </main>
            <footer>Footer</footer>
        </body>
    </html>
    """
    with patch("requests.get", return_value=MockResponse(html)):
        result = client.fetch("example.com")
        assert result["title"] == "Test Page"
        assert result["url"] == "https://example.com"
        assert "Heading" in result["content"]
        assert "Content" in result["content"]
        assert "Menu" not in result["content"]
        assert "Footer" not in result["content"]
        assert "Ads" not in result["content"]
        assert not result["truncated"]

def test_fetch_no_main_content():
    client = WebClient()
    html = """
    <html>
        <body>
            <p>Fallback content</p>
        </body>
    </html>
    """
    with patch("requests.get", return_value=MockResponse(html)):
        result = client.fetch("example.com")
        assert "Fallback content" in result["content"]

def test_fetch_empty_content():
    client = WebClient()
    html = """
    <html>
        <body>
            <script>var a = 1;</script>
        </body>
    </html>
    """
    with patch("requests.get", return_value=MockResponse(html)):
        result = client.fetch("example.com")
        assert "(No meaningful content extracted" in result["content"]

def test_fetch_truncation():
    client = WebClient()
    html = f"""
    <html>
        <main>
            <p>{"a" * 100}</p>
        </main>
    </html>
    """
    with patch("requests.get", return_value=MockResponse(html)):
        result = client.fetch("example.com", max_chars=50)
        assert len(result["content"]) > 50 # due to truncation message appended
        assert "[truncated at 50 chars]" in result["content"]
        assert result["truncated"] is True

def test_fetch_request_exception():
    client = WebClient()
    import requests
    with patch("requests.get", side_effect=requests.RequestException("conn error")):
        result = client.fetch("http://example.com")
        assert "Error fetching URL" in result["content"]

@patch("shane_skills.integrations.web_client.console")
def test_print_fetch(mock_console):
    client = WebClient()
    with patch.object(client, "fetch", return_value={"title": "T", "content": "C", "url": "U", "truncated": True}):
        client.print_fetch("http://example.com")
        mock_console.print.assert_called()

def test_fetch_no_main_or_body():
    client = WebClient()
    html = "<p>orphan</p>"
    with patch("requests.get", return_value=MockResponse(html)):
        result = client.fetch("example.com")
        assert "orphan" in result["content"]
