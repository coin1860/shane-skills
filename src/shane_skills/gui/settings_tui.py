"""
Settings TUI built with Textual.
Run via: shane-skills config   (or --tui flag)

Sections:
  - Jira: URL, username, API token (PAT)
  - Confluence: URL, username, API token (PAT — separate from Jira)
  - DB Connections: type selector + atomic fields + keyring password
  - Skills Root: override default skills directory
"""
from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
    TabbedContent,
    TabPane,
)

from shane_skills.config import Config, DB_TYPE_DEFAULTS


class SettingsTUI(App):
    """Shane Skills Settings."""

    CSS = """
    Screen {
        background: $surface;
    }
    .section-title {
        text-style: bold;
        color: $accent;
        margin: 1 0 0 0;
    }
    .field-label {
        width: 22;
        color: $text-muted;
        padding: 1 1 0 0;
    }
    .help-text {
        color: $text-muted;
        margin: 0 0 1 0;
    }
    .field-row {
        height: 4;
        margin: 0 0 1 0;
    }
    Input {
        width: 1fr;
    }
    Select {
        width: 1fr;
    }
    Button {
        margin: 1 1 0 0;
    }
    .save-bar {
        height: 3;
        background: $panel;
        align: right middle;
        padding: 0 2;
    }
    .status-msg {
        color: $success;
        padding: 0 2;
    }
    .tab-content {
        padding: 1 2;
    }
    .db-section {
        margin: 1 0;
        border: solid $panel;
        padding: 1 2;
    }
    .db-list-title {
        text-style: bold;
        color: $accent;
        margin: 1 0 0 0;
    }
    """

    BINDINGS = [
        Binding("ctrl+s", "save", "Save"),
        Binding("ctrl+q", "quit", "Quit"),
        Binding("escape", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.cfg = Config.load()
        self._status = ""
        self._last_added_name_val = ""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent():
            # ---- Jira Tab ----
            with TabPane("Jira", id="tab-jira"):
                with ScrollableContainer(classes="tab-content"):
                    yield Static("Jira Settings (Private Server — PAT Authentication)", classes="section-title")
                    with Horizontal(classes="field-row"):
                        yield Label("Server URL", classes="field-label")
                        yield Input(
                            value=self.cfg.jira_url,
                            placeholder="https://jira.your-company.com",
                            id="jira-url",
                        )
                    with Horizontal(classes="field-row"):
                        yield Label("Username / Email", classes="field-label")
                        yield Input(
                            value=self.cfg.jira_username,
                            placeholder="your.name@company.com",
                            id="jira-username",
                        )
                    with Horizontal(classes="field-row"):
                        yield Label("Personal Access Token", classes="field-label")
                        yield Input(
                            value=self.cfg.get_jira_token() or "",
                            placeholder="Jira Personal Access Token (PAT)",
                            password=True,
                            id="jira-token",
                        )
                    yield Static(
                        "Generate token at: {Jira URL}/secure/ViewProfile.jspa → Personal Access Tokens",
                        classes="help-text",
                    )

            # ---- Confluence Tab ----
            with TabPane("Confluence", id="tab-confluence"):
                with ScrollableContainer(classes="tab-content"):
                    yield Static("Confluence Settings (Private Server — PAT Authentication)", classes="section-title")
                    with Horizontal(classes="field-row"):
                        yield Label("Server URL", classes="field-label")
                        yield Input(
                            value=self.cfg.confluence_url,
                            placeholder="https://confluence.your-company.com",
                            id="conf-url",
                        )
                    with Horizontal(classes="field-row"):
                        yield Label("Username / Email", classes="field-label")
                        yield Input(
                            value=self.cfg.confluence_username,
                            placeholder="your.name@company.com",
                            id="conf-username",
                        )
                    with Horizontal(classes="field-row"):
                        yield Label("Personal Access Token", classes="field-label")
                        yield Input(
                            value=self.cfg.get_confluence_token() or "",
                            placeholder="Confluence Personal Access Token (PAT — separate from Jira)",
                            password=True,
                            id="conf-token",
                        )

            # ---- DB Tab ----
            with TabPane("Databases", id="tab-db"):
                with ScrollableContainer(classes="tab-content"):
                    yield Static("Database Connections", classes="section-title")
                    yield Static(
                        "Password is stored securely in OS keychain — not saved to config file.",
                        classes="help-text",
                    )

                    db_type_options = [(t, t) for t in DB_TYPE_DEFAULTS]
                    with Horizontal(classes="field-row"):
                        yield Label("DB Type", classes="field-label")
                        yield Select(
                            options=db_type_options,
                            value="Oracle",
                            id="db-type",
                        )
                    with Horizontal(classes="field-row"):
                        yield Label("Host", classes="field-label")
                        yield Input(placeholder="db-host.internal", id="db-host")
                    with Horizontal(classes="field-row"):
                        yield Label("Port", classes="field-label")
                        yield Input(placeholder="1521", id="db-port")
                    with Horizontal(classes="field-row"):
                        yield Label("Service / Database", classes="field-label")
                        yield Input(placeholder="PROD_SVC or db_name", id="db-service")
                    with Horizontal(classes="field-row"):
                        yield Label("Username", classes="field-label")
                        yield Input(placeholder="db_user", id="db-username")
                    with Horizontal(classes="field-row"):
                        yield Label("Password", classes="field-label")
                        yield Input(placeholder="●●●● (stored in keychain)", password=True, id="db-password")

                    with Horizontal():
                        yield Button("Save Connection", id="btn-add-db", variant="primary")
                        yield Button("Test", id="btn-test-db", variant="default")
                        yield Button("Delete", id="btn-del-db", variant="error")

            # ---- Skills Tab ----
            with TabPane("Skills Root", id="tab-skills"):
                with ScrollableContainer(classes="tab-content"):
                    yield Static("Skills Directory", classes="section-title")
                    with Horizontal(classes="field-row"):
                        yield Label("Skills Root", classes="field-label")
                        yield Input(
                            value=self.cfg.skills_root,
                            placeholder="(default: bundled skills/)",
                            id="skills-root",
                        )
                    yield Static(
                        "Override where shane-skills looks for .md skill files.\n"
                        "Leave blank to use the bundled skills/ directory.",
                        classes="help-text",
                    )

        with Horizontal(classes="save-bar"):
            yield Static(id="status-msg", classes="status-msg")
            yield Button("Save & Quit", id="btn-save", variant="success")
            yield Button("Quit", id="btn-quit", variant="default")

        yield Footer()

    def on_mount(self) -> None:
        self._load_default_db()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Auto-fill port when DB type is selected."""
        if event.select.id == "db-type":
            db_type = str(event.value)
            defaults = DB_TYPE_DEFAULTS.get(db_type)
            if defaults:
                default_port, _ = defaults
                self.query_one("#db-port", Input).value = str(default_port)

    def _load_default_db(self) -> None:
        conn = self.cfg.db_connections.get("default", {})
        if not conn:
            return
        
        self.query_one("#db-host", Input).value = conn.get("host", "")
        self.query_one("#db-port", Input).value = str(conn.get("port", ""))
        self.query_one("#db-service", Input).value = conn.get("service_name", "") or conn.get("database", "")
        self.query_one("#db-username", Input).value = conn.get("username", "")
        
        driver = conn.get("driver", "")
        for db_type, (_, d) in DB_TYPE_DEFAULTS.items():
            if d == driver:
                self.query_one("#db-type", Select).value = db_type
                break
                
        pwd_input = self.query_one("#db-password", Input)
        pwd_input.value = ""
        pwd_input.placeholder = "(unchanged in keychain)"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save":
            self.action_save()
            self.exit()
        elif event.button.id == "btn-quit":
            self.exit()
        elif event.button.id == "btn-add-db":
            self._add_db_connection()
        elif event.button.id == "btn-test-db":
            self._test_last_connection()
        elif event.button.id == "btn-del-db":
            self._delete_db_connection()

    def _add_db_connection(self) -> None:
        name = "default"
        host = self.query_one("#db-host", Input).value.strip()
        port_str = self.query_one("#db-port", Input).value.strip()
        service = self.query_one("#db-service", Input).value.strip()
        username = self.query_one("#db-username", Input).value.strip()
        password = self.query_one("#db-password", Input).value.strip()
        db_type = str(self.query_one("#db-type", Select).value)

        if not all([host, port_str, username]):
            self._set_status("⚠ Host, Port, and Username are required.")
            return

        try:
            port = int(port_str)
        except ValueError:
            self._set_status("⚠ Port must be a number.")
            return

        _, driver = DB_TYPE_DEFAULTS.get(db_type, (0, "postgresql+psycopg2"))

        self.cfg.add_db_connection(
            name=name, host=host, port=port, username=username,
            driver=driver, service_name=service, password=password,
        )

        self._set_status("✓ Saved DB connection (password in keychain)")

    def _delete_db_connection(self) -> None:
        name = "default"
        if name not in self.cfg.db_connections:
            self._set_status("⚠ No connection to delete.")
            return
        
        self.cfg.remove_db_connection(name)
        
        for field_id in ["#db-host", "#db-port", "#db-service", "#db-username", "#db-password"]:
            self.query_one(field_id, Input).value = ""
            self.query_one("#db-password", Input).placeholder = "●●●● (stored in keychain)"
            
        self._set_status("✓ Deleted DB connection")

    def _test_last_connection(self) -> None:
        name = "default"
        from shane_skills.integrations.db_client import DBClient
        try:
            ok = DBClient.test_connection(name)
            self._set_status(f"{'✓' if ok else '✗'} Test {'passed' if ok else 'failed'}")
        except Exception as e:
            self._set_status(f"✗ Test failed: {e}")

    def action_save(self) -> None:
        # Auto-add DB connection if the user filled the fields but didn't click "Save Connection"
        db_host = self.query_one("#db-host", Input).value.strip()
        db_user = self.query_one("#db-username", Input).value.strip()
        if db_host and db_user:
            self._add_db_connection()

        # Jira
        self.cfg.jira_url = self.query_one("#jira-url", Input).value.strip()
        self.cfg.jira_username = self.query_one("#jira-username", Input).value.strip()
        jira_token = self.query_one("#jira-token", Input).value.strip()
        if jira_token:
            self.cfg.set_jira_token(jira_token)

        # Confluence
        self.cfg.confluence_url = self.query_one("#conf-url", Input).value.strip()
        self.cfg.confluence_username = self.query_one("#conf-username", Input).value.strip()
        conf_token = self.query_one("#conf-token", Input).value.strip()
        if conf_token:
            self.cfg.set_confluence_token(conf_token)

        # Skills root
        self.cfg.skills_root = self.query_one("#skills-root", Input).value.strip()

        self.cfg.save()
        self._set_status("✓ Saved!")

    def _set_status(self, msg: str) -> None:
        self.query_one("#status-msg", Static).update(msg)


def run_tui() -> None:
    SettingsTUI().run()
