"""DB client — read-only Oracle/PostgreSQL/MSSQL/MySQL query interface.

SECURITY: DML and DDL statements (INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/TRUNCATE/MERGE
etc.) are BLOCKED. Only SELECT queries are permitted.

Uses SQLAlchemy with atomic connection config + keyring password from shane-skills config.
"""
from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from shane_skills.config import Config

console = Console()

# Blocked first-token keywords (case-insensitive)
_DML_DDL_BLOCKLIST = frozenset({
    "INSERT", "UPDATE", "DELETE", "DROP", "TRUNCATE",
    "ALTER", "CREATE", "MERGE", "REPLACE",
    "EXEC", "EXECUTE", "CALL",
})


def _validate_readonly(sql: str) -> None:
    """Raise ValueError if SQL is not a read-only SELECT statement."""
    first_token = sql.strip().split()[0].upper() if sql.strip() else ""
    if first_token in _DML_DDL_BLOCKLIST:
        raise ValueError(
            f"DML/DDL statements are not permitted. Only SELECT queries are allowed.\n"
            f"Blocked keyword: {first_token}"
        )


class DBClient:
    def __init__(self, connection_name: str, connection_url: str) -> None:
        self.connection_name = connection_name
        self.connection_url = connection_url
        self._engine: Any = None

    @classmethod
    def from_config(cls, connection_name: str = "default") -> "DBClient":
        cfg = Config.load()
        connections = cfg.get_db_connections()
        if connection_name not in connections:
            console.print(
                f"[red]DB connection '[bold]{connection_name}[/bold]' not found.\n"
                f"Run [bold]shane-skills config[/bold] to add connections.[/red]"
            )
            raise SystemExit(1)
        url = cfg.build_db_url(connection_name)
        return cls(connection_name=connection_name, connection_url=url)

    def _get_engine(self) -> Any:
        if self._engine is None:
            from sqlalchemy import create_engine
            self._engine = create_engine(self.connection_url)
        return self._engine

    def _is_oracle(self) -> bool:
        return "oracle" in self.connection_url.lower()

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def query_and_print(self, sql: str, limit: int = 20) -> None:
        """Execute a read-only SELECT query and print results as table."""
        try:
            _validate_readonly(sql)
        except ValueError as e:
            console.print(f"[red bold]Error:[/red bold] {e}")
            raise SystemExit(1)

        from sqlalchemy import text

        try:
            with self._get_engine().connect() as conn:
                result = conn.execute(text(sql))
                rows = result.fetchmany(limit)
                cols = list(result.keys())
        except Exception as e:
            console.print(f"[red]Query error: {e}[/red]")
            raise SystemExit(1)

        if not rows:
            console.print("[yellow]Query returned no rows.[/yellow]")
            return

        table = Table(border_style="dim", show_header=True, header_style="bold cyan")
        for col in cols:
            table.add_column(str(col))
        for row in rows:
            table.add_row(*[str(v) if v is not None else "[dim]NULL[/dim]" for v in row])

        console.print(table)
        console.print(f"[dim]Showing up to {limit} rows — connection: {self.connection_name}[/dim]")

    # ------------------------------------------------------------------
    # Schema — list tables
    # ------------------------------------------------------------------

    def print_schema(self) -> None:
        """List all accessible tables for this connection."""
        try:
            if self._is_oracle():
                rows, cols = self._oracle_list_tables()
            else:
                rows, cols = self._generic_list_tables()
        except Exception as e:
            console.print(f"[red]Schema error: {e}[/red]")
            raise SystemExit(1)

        if not rows:
            console.print("[yellow]No tables found for this connection.[/yellow]")
            return

        table = Table(
            title=f"Tables — {self.connection_name}",
            border_style="blue",
            show_header=True,
            header_style="bold cyan",
        )
        for col in cols:
            table.add_column(col)
        for row in rows:
            table.add_row(*[str(v) if v is not None else "" for v in row])
        console.print(table)
        console.print(f"[dim]{len(rows)} table(s)[/dim]")

    def _oracle_list_tables(self) -> tuple[list, list]:
        from sqlalchemy import text
        sql = (
            "SELECT OWNER, TABLE_NAME, NUM_ROWS, LAST_ANALYZED "
            "FROM ALL_TABLES "
            "ORDER BY OWNER, TABLE_NAME"
        )
        with self._get_engine().connect() as conn:
            result = conn.execute(text(sql))
            rows = result.fetchall()
            cols = ["Owner", "Table Name", "Num Rows", "Last Analyzed"]
        return rows, cols

    def _generic_list_tables(self) -> tuple[list, list]:
        from sqlalchemy import inspect
        inspector = inspect(self._get_engine())
        schema_names = inspector.get_schema_names()
        rows = []
        for schema in schema_names:
            if schema in ("information_schema", "pg_catalog"):
                continue
            for tname in inspector.get_table_names(schema=schema):
                rows.append((schema, tname))
        return rows, ["Schema", "Table Name"]

    # ------------------------------------------------------------------
    # Describe — table column structure
    # ------------------------------------------------------------------

    def print_describe(self, table_name: str) -> None:
        """Print column definitions for a given table."""
        try:
            if self._is_oracle():
                rows, cols = self._oracle_describe(table_name)
            else:
                rows, cols = self._generic_describe(table_name)
        except Exception as e:
            console.print(f"[red]Describe error: {e}[/red]")
            raise SystemExit(1)

        if not rows:
            console.print(
                f"[yellow]Table '[bold]{table_name}[/bold]' not found "
                f"in connection '{self.connection_name}'.[/yellow]"
            )
            return

        table = Table(
            title=f"{table_name} — {self.connection_name}",
            border_style="blue",
            show_header=True,
            header_style="bold cyan",
        )
        for col in cols:
            table.add_column(col)
        for row in rows:
            table.add_row(*[str(v) if v is not None else "[dim]NULL[/dim]" for v in row])
        console.print(table)

    def _oracle_describe(self, table_name: str) -> tuple[list, list]:
        from sqlalchemy import text
        # Split owner.table if provided
        parts = table_name.upper().split(".")
        if len(parts) == 2:
            owner, tname = parts
            where = "OWNER = :owner AND TABLE_NAME = :table"
            params: dict[str, Any] = {"owner": owner, "table": tname}
        else:
            where = "TABLE_NAME = :table"
            params = {"table": parts[0]}

        sql = (
            f"SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE, DATA_DEFAULT "
            f"FROM ALL_TAB_COLUMNS "
            f"WHERE {where} "
            f"ORDER BY COLUMN_ID"
        )
        with self._get_engine().connect() as conn:
            result = conn.execute(text(sql), params)
            rows = result.fetchall()
            cols = ["Column", "Type", "Length", "Nullable", "Default"]
        return rows, cols

    def _generic_describe(self, table_name: str) -> tuple[list, list]:
        from sqlalchemy import inspect
        inspector = inspect(self._get_engine())
        columns = inspector.get_columns(table_name)
        rows = [
            (
                col["name"],
                str(col["type"]),
                "YES" if col.get("nullable", True) else "NO",
                str(col.get("default", "")) or "",
            )
            for col in columns
        ]
        return rows, ["Column", "Type", "Nullable", "Default"]

    # ------------------------------------------------------------------
    # Display connections
    # ------------------------------------------------------------------

    @staticmethod
    def print_connections() -> None:
        """Print all configured DB connections (password-redacted)."""
        cfg = Config.load()
        conns = cfg.get_db_connections()
        if not conns:
            console.print(
                "[yellow]No DB connections configured. "
                "Run [bold]shane-skills config[/bold] to add one.[/yellow]"
            )
            return

        table = Table(title="DB Connections", border_style="blue", show_header=True, header_style="bold cyan")
        table.add_column("Name", style="cyan")
        table.add_column("Driver")
        table.add_column("Host:Port/Service")
        table.add_column("Username")

        for name, info in conns.items():
            host = info.get("host", "")
            port = info.get("port", "")
            service = info.get("service_name", "") or info.get("database", "")
            driver = info.get("driver", "")
            username = info.get("username", "")
            table.add_row(name, driver, f"{host}:{port}/{service}", username)

        console.print(table)

    @staticmethod
    def test_connection(connection_name: str) -> bool:
        """Run a minimal query to verify connectivity. Returns True on success."""
        try:
            client = DBClient.from_config(connection_name)
            from sqlalchemy import text
            with client._get_engine().connect() as conn:
                if client._is_oracle():
                    conn.execute(text("SELECT 1 FROM DUAL"))
                else:
                    conn.execute(text("SELECT 1"))
            console.print(Panel(
                f"[bold green]✓ Connection '{connection_name}' is working[/bold green]",
                border_style="green",
            ))
            return True
        except Exception as e:
            console.print(Panel(
                f"[bold red]✗ Connection '{connection_name}' failed[/bold red]\n{e}",
                border_style="red",
            ))
            return False
