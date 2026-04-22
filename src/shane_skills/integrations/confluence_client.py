"""Confluence integration client — lightweight CLI wrapper for private Confluence Server/Data Center.

Authentication: Personal Access Token (PAT) via atlassian-python-api.
Output format mirrors kb-agent's ConfluenceConnector._format_page for consistency.
"""
from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from shane_skills.config import Config

console = Console()


class ConfluenceClient:
    def __init__(self, url: str, token: str) -> None:
        self.url = url.rstrip("/")
        self.token = token
        self._confluence: Any = None

    @classmethod
    def from_config(cls) -> "ConfluenceClient":
        cfg = Config.load()
        token = cfg.get_confluence_token()
        if not cfg.confluence_url or not token:
            console.print(
                "[red]Confluence not configured. Run [bold]shane-skills config[/bold] to set up.[/red]"
            )
            raise SystemExit(1)
        return cls(url=cfg.confluence_url, token=token)

    def _get_confluence(self) -> Any:
        if self._confluence is None:
            from atlassian import Confluence
            self._confluence = Confluence(
                url=self.url,
                token=self.token,
                verify_ssl=False,
            )
        return self._confluence

    # ------------------------------------------------------------------
    # Format helpers (kb-agent style Markdown output)
    # ------------------------------------------------------------------

    def _format_page(self, data: dict[str, Any]) -> str:
        """Format a raw Confluence page JSON into rich Markdown (mirrors kb-agent style)."""
        from markdownify import markdownify as md_convert

        body_html = data.get("body", {}).get("storage", {}).get("value", "")
        content_md = md_convert(body_html, strip=["img"]) if body_html else "(No content)"

        space = data.get("space", {})
        version = data.get("version", {})
        ancestors = data.get("ancestors", [])
        ancestor_titles = [a.get("title", "") for a in ancestors] if ancestors else []

        title = data.get("title", "Untitled")
        page_id = data.get("id", "")

        # Build page URL
        web_link = data.get("_links", {}).get("webui", "")
        page_url = f"{self.url}{web_link}" if web_link else ""

        modified_by = version.get("by", {}).get("displayName", "Unknown")
        modified_when = (version.get("when") or "")[:10]

        parts = [
            f"# {title}",
            "",
            f"**Space:** {space.get('name', space.get('key', 'Unknown'))}",
            f"**Version:** {version.get('number', 'Unknown')} | "
            f"**Last Modified:** {modified_when} by {modified_by}",
            f"**Page ID:** {page_id}",
            f"**URL:** {page_url}",
        ]
        if ancestor_titles:
            path = " > ".join(ancestor_titles) + f" > {title}"
            parts.append(f"**Path:** {path}")
        parts.append("")
        parts.append("## Content")
        parts.append(content_md)

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_page(self, page_id: str) -> dict[str, Any]:
        """Fetch a Confluence page by numeric ID (raw API response)."""
        return self._get_confluence().get_page_by_id(
            page_id, expand="body.storage,space,version,ancestors,_links"
        )

    def print_page(self, page_id: str) -> None:
        """Fetch and print a Confluence page as rich Markdown."""
        page = self.get_page(page_id)
        if not page:
            console.print(f"[red]Page {page_id} not found or access denied.[/red]")
            return
        markdown_text = self._format_page(page)
        console.print(Markdown(markdown_text))

    def search_and_print(self, query: str, space: str | None = None, limit: int = 5) -> None:
        """Search Confluence pages via CQL and print results table."""
        cql = f'text ~ "{query}" AND type = "page"'
        if space:
            cql += f' AND space = "{space}"'

        results = self._get_confluence().cql(cql, limit=limit)
        pages = results.get("results", [])

        if not pages:
            console.print(f"[yellow]No results for: {query}[/yellow]")
            return

        table = Table(title=f'Confluence: "{query}"', border_style="blue")
        table.add_column("ID", style="dim", width=12)
        table.add_column("Title", style="cyan")
        table.add_column("Space", style="yellow", width=12)
        table.add_column("URL", style="dim")

        for page in pages:
            page_id = page.get("id", "")
            title = page.get("title", "")
            result_space = page.get("resultGlobalContainer", {}).get("title", space or "")
            url = self.url + page.get("url", "")
            table.add_row(page_id, title, result_space, url)

        console.print(table)
        console.print(f"[dim]Tip: fetch full content with [bold]shane-skills confluence page <ID>[/bold][/dim]")

    def create_page(
        self,
        parent_id: str,
        title: str,
        content: str,
    ) -> dict[str, Any]:
        """Create a new Confluence page as a child of parent_id.

        Args:
            parent_id: Numeric ID of the parent page.
            title: Title of the new page.
            content: Page body (plain text or Markdown — stored as-is in storage format).
        """
        confluence = self._get_confluence()

        # Resolve space key from parent
        parent = confluence.get_page_by_id(parent_id, expand="space")
        if not parent:
            return {"error": True, "content": f"Parent page {parent_id} not found."}

        space_key = parent.get("space", {}).get("key")
        if not space_key:
            return {"error": True, "content": f"Could not determine space for parent {parent_id}."}

        result = confluence.create_page(
            space=space_key,
            title=title,
            body=content,
            parent_id=parent_id,
            type="page",
            representation="storage",
        )
        if not result:
            return {"error": True, "content": "Confluence API returned no data after create_page."}

        page_id = result.get("id", "")
        web_link = result.get("_links", {}).get("webui", "")
        page_url = f"{self.url}{web_link}" if web_link else ""

        return {
            "id": page_id,
            "title": title,
            "space": space_key,
            "url": page_url,
        }

    def print_created_page(self, result: dict[str, Any]) -> None:
        """Print the result of a create_page call."""
        if result.get("error"):
            console.print(f"[red]Error: {result.get('content')}[/red]")
            return
        console.print(
            Panel(
                f"[bold green]✓ Created page '{result['title']}'[/bold green]\n"
                f"Space: [yellow]{result['space']}[/yellow] | ID: {result['id']}\n"
                f"[cyan]{result['url']}[/cyan]",
                title="Confluence Page Created",
                border_style="green",
            )
        )
