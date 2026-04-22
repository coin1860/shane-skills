"""
shane-skills CLI entrypoint.

Usage:
    shane-skills init                           Deploy skills to current project
    shane-skills list                           List available skills

    shane-skills jira <KEY>                     Fetch Jira issue as Markdown
    shane-skills jira search <text>             Search Jira issues by text
    shane-skills jira jql <query>               Execute raw JQL query
    shane-skills jira create ...                Create a new Jira issue

    shane-skills confluence search <text>       Search Confluence pages
    shane-skills confluence page <id>           Fetch Confluence page as Markdown
    shane-skills confluence create ...          Create a new Confluence page

    shane-skills web fetch <url>                Fetch web page as Markdown

    shane-skills db query <sql>                 Run a read-only SQL query
    shane-skills db schema                      List all tables
    shane-skills db describe <table>            Show table column structure
    shane-skills db connections                 List configured DB connections
    shane-skills db test <connection>           Test a DB connection

    shane-skills config                         Open settings GUI/TUI
"""
import click
from rich.console import Console

console = Console()


@click.group()
@click.version_option(package_name="shane-skills")
def main() -> None:
    """Shane's personal AI skills & agent CLI for HSBC SDLC workflows.

    \b
    Examples:
      shane-skills init                           Deploy skills to current project
      shane-skills list                           List available skills
      shane-skills config                         Open settings GUI/TUI

    \b
    Jira:
      shane-skills jira fetch <KEY>               Fetch Jira issue as Markdown
      shane-skills jira search <text>             Search Jira issues by text
      shane-skills jira jql <query>               Execute raw JQL query
      shane-skills jira create ...                Create a new Jira issue

    \b
    Confluence:
      shane-skills confluence search <text>       Search Confluence pages
      shane-skills confluence page <id>           Fetch Confluence page as Markdown
      shane-skills confluence create ...          Create a new Confluence page

    \b
    Web:
      shane-skills web fetch <url>                Fetch web page as Markdown

    \b
    Database (Read-Only):
      shane-skills db query <sql>                 Run a read-only SQL query
      shane-skills db schema                      List all tables
      shane-skills db describe <table>            Show table column structure
      shane-skills db connections                 List configured DB connections
    """
    pass


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------
@main.command()
@click.option("--target", "-t", default=".", help="Target project directory.")
@click.option(
    "--profile", "-p", default="all",
    type=click.Choice(["all", "copilot", "opencode"]),
    help="Which skill profile to deploy.",
)
@click.option("--dry-run", is_flag=True, help="Preview without writing files.")
def init(target: str, profile: str, dry_run: bool) -> None:
    """Deploy skills & agents into a project directory."""
    from shane_skills.init_cmd import run_init
    run_init(target=target, profile=profile, dry_run=dry_run)


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------
@main.command("list")
@click.option(
    "--profile", "-p", default="all",
    type=click.Choice(["all", "copilot", "opencode", "shared"]),
)
def list_skills(profile: str) -> None:
    """List all available skills and agents."""
    from shane_skills.init_cmd import list_skills as _list
    _list(profile=profile)


# ---------------------------------------------------------------------------
# Jira
# ---------------------------------------------------------------------------
@main.group()
def jira() -> None:
    """Jira operations — fetch, search, create issues."""
    pass


@jira.command("fetch")
@click.argument("issue_key")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")
def jira_fetch(issue_key: str, as_json: bool) -> None:
    """Fetch a Jira issue as Markdown (e.g. FSR-123)."""
    from shane_skills.integrations.jira_client import JiraClient
    client = JiraClient.from_config()
    client.print_issue(issue_key, as_json=as_json)


@jira.command("search")
@click.argument("text")
@click.option("--limit", "-n", default=20, help="Max results.")
def jira_search(text: str, limit: int) -> None:
    """Search Jira issues by free text."""
    from shane_skills.integrations.jira_client import JiraClient
    client = JiraClient.from_config()
    results = client.search(text, limit=limit)
    client.print_search_results(results)


@jira.command("jql")
@click.argument("query")
@click.option("--limit", "-n", default=20, help="Max results.")
def jira_jql(query: str, limit: int) -> None:
    """Execute a raw JQL query."""
    from shane_skills.integrations.jira_client import JiraClient
    client = JiraClient.from_config()
    results = client.jql(query, limit=limit)
    client.print_search_results(results)


@jira.command("create")
@click.option("--project", "-p", required=True, help="Jira project key (e.g. PROJ).")
@click.option("--summary", "-s", required=True, help="Issue summary/title.")
@click.option("--description", "-d", default="", help="Issue description.")
@click.option("--type", "issue_type", default="Task", help="Issue type (default: Task).")
def jira_create(project: str, summary: str, description: str, issue_type: str) -> None:
    """Create a new Jira issue."""
    from shane_skills.integrations.jira_client import JiraClient
    client = JiraClient.from_config()
    result = client.create_issue(project=project, summary=summary,
                                 description=description, issue_type=issue_type)
    client.print_created_issue(result)


# Keep backward-compat: `shane-skills jira KEY` → fetch
@main.command("jira-fetch", hidden=True)
@click.argument("issue_key")
def _jira_fetch_compat(issue_key: str) -> None:
    from shane_skills.integrations.jira_client import JiraClient
    JiraClient.from_config().print_issue(issue_key)


# ---------------------------------------------------------------------------
# Confluence
# ---------------------------------------------------------------------------
@main.group()
def confluence() -> None:
    """Confluence operations — search, fetch, create pages."""
    pass


@confluence.command("search")
@click.argument("query")
@click.option("--space", "-s", default=None, help="Confluence space key.")
@click.option("--limit", "-n", default=5, help="Max results.")
def confluence_search(query: str, space: str | None, limit: int) -> None:
    """Search Confluence pages by text."""
    from shane_skills.integrations.confluence_client import ConfluenceClient
    client = ConfluenceClient.from_config()
    client.search_and_print(query=query, space=space, limit=limit)


@confluence.command("page")
@click.argument("page_id")
def confluence_page(page_id: str) -> None:
    """Fetch a Confluence page by ID and print as Markdown."""
    from shane_skills.integrations.confluence_client import ConfluenceClient
    ConfluenceClient.from_config().print_page(page_id)


@confluence.command("create")
@click.option("--parent", "-p", required=True, help="Parent page numeric ID.")
@click.option("--title", "-t", required=True, help="New page title.")
@click.option("--content", "-c", required=True, help="Page body content.")
def confluence_create(parent: str, title: str, content: str) -> None:
    """Create a new Confluence page under a parent page."""
    from shane_skills.integrations.confluence_client import ConfluenceClient
    client = ConfluenceClient.from_config()
    result = client.create_page(parent_id=parent, title=title, content=content)
    client.print_created_page(result)


# ---------------------------------------------------------------------------
# Web
# ---------------------------------------------------------------------------
@main.group()
def web() -> None:
    """Web page utilities."""
    pass


@web.command("fetch")
@click.argument("url")
@click.option("--max-chars", "-m", default=8000, help="Truncate output at N characters (default: 8000).")
def web_fetch(url: str, max_chars: int) -> None:
    """Fetch a web page and print its content as Markdown."""
    from shane_skills.integrations.web_client import WebClient
    WebClient().print_fetch(url, max_chars=max_chars)


# ---------------------------------------------------------------------------
# DB
# ---------------------------------------------------------------------------
@main.group()
def db() -> None:
    """Database query utilities (read-only: SELECT only)."""
    pass


@db.command("query")
@click.argument("sql")
@click.option("--connection", "-c", default="default", help="Named DB connection from config.")
@click.option("--limit", "-n", default=20, help="Max rows to display.")
def db_query(sql: str, connection: str, limit: int) -> None:
    """Run a read-only SQL SELECT query. DML/DDL is blocked."""
    from shane_skills.integrations.db_client import DBClient
    DBClient.from_config(connection).query_and_print(sql=sql, limit=limit)


@db.command("schema")
@click.option("--connection", "-c", default="default", help="Named DB connection from config.")
def db_schema(connection: str) -> None:
    """List all tables for a DB connection."""
    from shane_skills.integrations.db_client import DBClient
    DBClient.from_config(connection).print_schema()


@db.command("describe")
@click.argument("table")
@click.option("--connection", "-c", default="default", help="Named DB connection from config.")
def db_describe(table: str, connection: str) -> None:
    """Show column structure for a table (useful for AI to write queries)."""
    from shane_skills.integrations.db_client import DBClient
    DBClient.from_config(connection).print_describe(table)


@db.command("connections")
def db_connections() -> None:
    """List all configured DB connections (password not shown)."""
    from shane_skills.integrations.db_client import DBClient
    DBClient.print_connections()


@db.command("test")
@click.option("--connection", "-c", default="default", hidden=True)
def db_test(connection: str) -> None:
    """Test a DB connection with a minimal query."""
    from shane_skills.integrations.db_client import DBClient
    DBClient.test_connection(connection)


# ---------------------------------------------------------------------------
# Config / Settings GUI
# ---------------------------------------------------------------------------
@main.command()
@click.option("--tui", is_flag=True, help="Force TUI mode even if GUI is available.")
def config(tui: bool) -> None:
    """Open the settings GUI to manage API keys and connections."""
    if tui:
        from shane_skills.gui.settings_tui import run_tui
        run_tui()
    else:
        try:
            from shane_skills.gui.settings_app import run_gui
            run_gui()
        except ImportError:
            console.print("[yellow]PyQt6 not installed, falling back to TUI mode.[/yellow]")
            from shane_skills.gui.settings_tui import run_tui
            run_tui()
