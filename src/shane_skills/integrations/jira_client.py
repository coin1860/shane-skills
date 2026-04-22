"""Jira integration client — lightweight CLI wrapper for private Jira Server/Data Center.

Authentication: Personal Access Token (PAT) via atlassian-python-api.
Output format mirrors kb-agent's JiraConnector._format_issue for consistency.
"""
from __future__ import annotations

import json
import re
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from shane_skills.config import Config

console = Console()


class JiraClient:
    def __init__(self, url: str, token: str) -> None:
        self.url = url.rstrip("/")
        self.token = token
        self._jira: Any = None

    @classmethod
    def from_config(cls) -> "JiraClient":
        cfg = Config.load()
        token = cfg.get_jira_token()
        if not cfg.jira_url or not token:
            console.print(
                "[red]Jira not configured. Run [bold]shane-skills config[/bold] to set up.[/red]"
            )
            raise SystemExit(1)
        return cls(url=cfg.jira_url, token=token)

    def _get_jira(self) -> Any:
        if self._jira is None:
            from atlassian import Jira
            self._jira = Jira(
                url=self.url,
                token=self.token,
                verify_ssl=False,
            )
        return self._jira

    # ------------------------------------------------------------------
    # Format helpers (kb-agent style Markdown output)
    # ------------------------------------------------------------------

    def _format_issue(self, data: dict[str, Any], comments: list[dict] | None = None) -> str:
        """Format a raw Jira issue JSON into rich Markdown (mirrors kb-agent style)."""
        from markdownify import markdownify as md_convert

        fields = data.get("fields", {})
        rendered = data.get("renderedFields", {})

        issue_key = data.get("key", "")
        summary = fields.get("summary", "")
        issue_url = f"{self.url}/browse/{issue_key}"

        status = fields.get("status", {}).get("name", "Unknown")
        priority = fields.get("priority", {}).get("name", "Unknown")
        issuetype = fields.get("issuetype", {}).get("name", "Unknown")
        assignee = (fields.get("assignee") or {}).get("displayName", "Unassigned")
        reporter = (fields.get("reporter") or {}).get("displayName", "")
        components = [c.get("name", "") for c in fields.get("components", [])]
        labels = fields.get("labels", [])

        description = rendered.get("description") or fields.get("description") or ""
        if isinstance(description, dict):
            description = _extract_text(description)
        elif "<" in str(description):
            description = md_convert(str(description), strip=["img"])

        parts = [
            f"# {issue_key} — {summary}",
            "",
            f"**Type:** {issuetype} | **Status:** {status} | **Priority:** {priority}",
            f"**Assignee:** {assignee}" + (f" | **Reporter:** {reporter}" if reporter else ""),
        ]
        if labels:
            parts.append(f"**Labels:** {', '.join(labels)}")
        if components:
            parts.append(f"**Components:** {', '.join(components)}")
        parts.append(f"**URL:** {issue_url}")
        parts.append("")
        parts.append("## Description")
        parts.append(description or "(No description)")

        if comments:
            parts.append("\n## Comments")
            for c in comments[-10:]:
                author = c.get("author", {}).get("displayName", "Unknown")
                created = c.get("created", "")[:10]
                body = c.get("body", "")
                if isinstance(body, dict):
                    body = _extract_text(body)
                elif "<" in str(body) and ">" in str(body):
                    body = md_convert(str(body), strip=["img"])
                parts.append(f"**{author} ({created}):**\n{body}\n")

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_issue(self, issue_key: str) -> dict[str, Any]:
        """Fetch a single Jira issue (raw API response)."""
        return self._get_jira().issue(issue_key, expand="renderedFields")  # type: ignore

    def print_issue(
        self,
        issue_key: str,
        as_json: bool = False,
    ) -> None:
        """Fetch and print a Jira issue as rich Markdown."""
        issue = self.get_issue(issue_key)

        if as_json:
            console.print_json(json.dumps(issue))
            return

        # Fetch comments
        comments: list[dict] = []
        try:
            comments_data = self._get_jira().issue_get_comments(issue_key)
            comments = comments_data.get("comments", []) if comments_data else []
        except Exception:
            pass

        markdown_text = self._format_issue(issue, comments=comments)
        console.print(Markdown(markdown_text))

    def search(self, text: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search Jira issues by free text (JQL text~ search)."""
        jql = f'text ~ "{text}" ORDER BY updated DESC'
        return self._run_jql(jql, limit=limit)

    def jql(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Execute a raw JQL query."""
        return self._run_jql(query, limit=limit)

    def _run_jql(self, jql: str, limit: int = 20) -> list[dict[str, Any]]:
        """Run JQL and return list of issue dicts."""
        data = self._get_jira().jql(jql, limit=limit, expand="renderedFields")
        return data.get("issues", [])

    def print_search_results(self, issues: list[dict[str, Any]]) -> None:
        """Print a summary table of multiple issues."""
        if not issues:
            console.print("[yellow]No results found.[/yellow]")
            return

        table = Table(border_style="blue", show_header=True, header_style="bold cyan")
        table.add_column("Key", style="cyan", width=14)
        table.add_column("Type", width=10)
        table.add_column("Status", width=14)
        table.add_column("Priority", width=10)
        table.add_column("Summary")

        for issue in issues:
            f = issue.get("fields", {})
            table.add_row(
                issue.get("key", ""),
                (f.get("issuetype") or {}).get("name", ""),
                (f.get("status") or {}).get("name", ""),
                (f.get("priority") or {}).get("name", ""),
                f.get("summary", ""),
            )

        console.print(table)
        console.print(f"[dim]{len(issues)} result(s)[/dim]")

    def create_issue(
        self,
        project: str,
        summary: str,
        description: str = "",
        issue_type: str = "Task",
    ) -> dict[str, Any]:
        """Create a new Jira issue. Returns result dict."""
        if not project or not summary:
            return {"error": True, "content": "Project key and summary are required."}

        fields: dict[str, Any] = {
            "project": {"key": project.upper()},
            "summary": summary.strip(),
            "issuetype": {"name": issue_type},
        }
        if description:
            fields["description"] = description

        result = self._get_jira().create_issue(fields=fields)
        key = result.get("key", "")
        return {
            "key": key,
            "url": f"{self.url}/browse/{key}" if key else "",
            "summary": summary,
            "project": project.upper(),
            "issue_type": issue_type,
        }

    def print_created_issue(self, result: dict[str, Any]) -> None:
        """Print the result of a create_issue call."""
        if result.get("error"):
            console.print(f"[red]Error: {result.get('content')}[/red]")
            return
        console.print(
            Panel(
                f"[bold green]✓ Created {result['key']}[/bold green]\n"
                f"[cyan]{result['url']}[/cyan]\n"
                f"Summary: {result['summary']}",
                title="Jira Issue Created",
                border_style="green",
            )
        )


def _extract_text(node: Any) -> str:
    """Recursively extract plain text from Jira's Atlassian Document Format (ADF)."""
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, dict):
        if node.get("type") == "text":
            return node.get("text", "")
        parts = [_extract_text(child) for child in node.get("content", [])]
        return " ".join(p for p in parts if p)
    return str(node)
