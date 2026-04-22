"""Web page fetcher — converts a URL to clean Markdown for AI context.

Uses requests + beautifulsoup4 + markdownify only. No Playwright or browser dependency.
Targets <article>, <main>, <div role="main"> for content extraction.
"""
from __future__ import annotations

import re
from urllib.parse import urlparse

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

console = Console()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
}

# Elements to strip before extracting main content
STRIP_TAGS = ["script", "style", "nav", "footer", "header", "aside",
               "form", "button", "iframe", "noscript", "svg"]

# CSS selectors to remove inside main content area
STRIP_SELECTORS = [
    "[class*='cookie']", "[class*='banner']", "[class*='popup']",
    "[class*='modal']", "[class*='sidebar']", "[class*='advertisement']",
    "[class*='social']", "[id*='cookie']", "[id*='banner']",
]


class WebClient:
    """Lightweight HTTP → Markdown fetcher."""

    def fetch(self, url: str, max_chars: int = 8000) -> dict[str, str]:
        """Fetch a URL and return {title, content (Markdown), url}.

        Args:
            url: Full HTTP/HTTPS URL to fetch.
            max_chars: Truncate Markdown output at this many characters.

        Returns:
            Dict with keys: title, content, url, truncated (bool).
        """
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        import requests
        from bs4 import BeautifulSoup
        from markdownify import markdownify as md_convert

        try:
            resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True, verify=False)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
        except requests.RequestException as e:
            return {"title": url, "content": f"Error fetching URL: {e}", "url": url, "truncated": False}

        html = resp.text
        soup = BeautifulSoup(html, "html.parser")

        # Extract title
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()

        # Strip non-content global tags
        for tag_name in STRIP_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        # Find main content area
        main_content = (
            soup.find("article")
            or soup.find("main")
            or soup.find("div", {"role": "main"})
            or soup.find("div", class_=re.compile(r"(content|article|post|entry)", re.I))
            or soup.body
        )
        if main_content is None:
            main_content = soup

        # Strip noise elements inside main content
        for selector in STRIP_SELECTORS:
            for el in main_content.select(selector):
                if el != main_content:
                    el.decompose()

        # Convert to Markdown
        markdown = md_convert(str(main_content), heading_style="ATX", bullets="-", strip=["img"])
        markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip()

        if not markdown:
            markdown = f"(No meaningful content extracted from {url})"

        truncated = False
        if len(markdown) > max_chars:
            markdown = markdown[:max_chars]
            markdown += f"\n\n[truncated at {max_chars} chars]"
            truncated = True

        return {"title": title or url, "content": markdown, "url": url, "truncated": truncated}

    def print_fetch(self, url: str, max_chars: int = 8000) -> None:
        """Fetch URL and print title + Markdown content to terminal."""
        result = self.fetch(url, max_chars=max_chars)

        if result.get("truncated"):
            console.print(f"[dim]⚠ Output truncated at {max_chars} chars. Use --max-chars to increase.[/dim]")

        console.print(Panel(
            f"[bold]{result['title']}[/bold]\n[dim]{result['url']}[/dim]",
            title="Web Page",
            border_style="cyan",
        ))
        console.print(Markdown(result["content"]))
