"""
Config management for shane-skills.

Stores:
- Non-sensitive config in ~/.shane-skills/config.toml
- Sensitive credentials in OS keychain via `keyring`

DB connections use atomic fields (host, port, service_name/database, username, driver).
Passwords are stored in keychain under: "shane-skills:db:{name}"
"""
from __future__ import annotations

import toml
import keyring
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

APP_NAME = "shane-skills"
CONFIG_DIR = Path.home() / ".shane-skills"
CONFIG_FILE = CONFIG_DIR / "config.toml"

# Keyring service names
KEYRING_JIRA_TOKEN = f"{APP_NAME}:jira_token"
KEYRING_CONFLUENCE_TOKEN = f"{APP_NAME}:confluence_token"

# DB type defaults: (default_port, driver)
DB_TYPE_DEFAULTS: dict[str, tuple[int, str]] = {
    "Oracle": (1521, "oracle+oracledb"),
    "PostgreSQL": (5432, "postgresql+psycopg2"),
    "MySQL": (3306, "mysql+pymysql"),
}


@dataclass
class Config:
    """Top-level configuration object."""

    # Jira settings
    jira_url: str = ""
    jira_username: str = ""

    # Confluence settings
    confluence_url: str = ""
    confluence_username: str = ""

    # Skills root (where skills/ folder lives)
    skills_root: str = ""

    # DB connections: { name: { host, port, service_name, database, username, driver } }
    # Passwords are stored in OS keychain, NOT here.
    db_connections: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Raw dict for forward-compat extensions
    _raw: dict[str, Any] = field(default_factory=dict, repr=False)

    # ------------------------------------------------------------------
    # Load / Save
    # ------------------------------------------------------------------
    @classmethod
    def load(cls) -> "Config":
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if not CONFIG_FILE.exists():
            return cls()
        raw = toml.load(CONFIG_FILE)
        return cls(
            jira_url=raw.get("jira", {}).get("url", ""),
            jira_username=raw.get("jira", {}).get("username", ""),
            confluence_url=raw.get("confluence", {}).get("url", ""),
            confluence_username=raw.get("confluence", {}).get("username", ""),
            skills_root=raw.get("skills", {}).get("root", ""),
            db_connections=raw.get("db", {}).get("connections", {}),
            _raw=raw,
        )

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data: dict[str, Any] = {
            "jira": {
                "url": self.jira_url,
                "username": self.jira_username,
            },
            "confluence": {
                "url": self.confluence_url,
                "username": self.confluence_username,
            },
            "skills": {
                "root": self.skills_root or str(Path(__file__).parent.parent.parent / "skills"),
            },
            "db": {
                "connections": self.db_connections,
            },
        }
        with open(CONFIG_FILE, "w") as f:
            toml.dump(data, f)

    # ------------------------------------------------------------------
    # Secrets (keyring) — Jira / Confluence
    # ------------------------------------------------------------------
    def get_jira_token(self) -> str | None:
        return keyring.get_password(KEYRING_JIRA_TOKEN, self.jira_username or "default")

    def set_jira_token(self, token: str) -> None:
        keyring.set_password(KEYRING_JIRA_TOKEN, self.jira_username or "default", token)

    def get_confluence_token(self) -> str | None:
        return keyring.get_password(KEYRING_CONFLUENCE_TOKEN, self.confluence_username or "default")

    def set_confluence_token(self, token: str) -> None:
        keyring.set_password(KEYRING_CONFLUENCE_TOKEN, self.confluence_username or "default", token)

    # ------------------------------------------------------------------
    # DB connections — atomic fields + keyring passwords
    # ------------------------------------------------------------------
    def get_db_connections(self) -> dict[str, dict[str, Any]]:
        return self.db_connections

    def add_db_connection(
        self,
        name: str,
        host: str,
        port: int,
        username: str,
        driver: str,
        service_name: str = "",
        database: str = "",
        password: str = "",
    ) -> None:
        """Add or update a DB connection. Password is stored in keychain."""
        conn: dict[str, Any] = {
            "host": host,
            "port": port,
            "username": username,
            "driver": driver,
        }
        if service_name:
            conn["service_name"] = service_name
        if database:
            conn["database"] = database
        self.db_connections[name] = conn
        self.save()
        if password:
            self.set_db_password(name, username, password)

    def remove_db_connection(self, name: str) -> None:
        conn = self.db_connections.pop(name, {})
        self.save()
        # Best-effort: remove password from keychain
        username = conn.get("username", "default")
        try:
            keyring.delete_password(f"{APP_NAME}:db:{name}", username)
        except Exception:
            pass

    def get_db_password(self, name: str) -> str | None:
        """Retrieve DB password from OS keychain."""
        conn = self.db_connections.get(name, {})
        username = conn.get("username", "default")
        return keyring.get_password(f"{APP_NAME}:db:{name}", username)

    def set_db_password(self, name: str, username: str, password: str) -> None:
        """Store DB password in OS keychain."""
        keyring.set_password(f"{APP_NAME}:db:{name}", username, password)

    def build_db_url(self, name: str) -> str:
        """Build a SQLAlchemy connection URL from atomic fields + keychain password."""
        conn = self.db_connections.get(name)
        if not conn:
            raise KeyError(f"DB connection '{name}' not found in config.")

        driver = conn.get("driver", "postgresql+psycopg2")
        host = conn.get("host", "localhost")
        port = conn.get("port", 5432)
        username = conn.get("username", "")
        service_name = conn.get("service_name", "")
        database = conn.get("database", "")
        password = self.get_db_password(name) or ""

        # URL-encode password for safety
        from urllib.parse import quote_plus
        password_encoded = quote_plus(password) if password else ""
        auth = f"{username}:{password_encoded}@" if username else ""

        if "oracle" in driver:
            # Oracle DSN: oracle+oracledb://user:pass@host:port/?service_name=SVC
            svc = service_name or database
            return f"{driver}://{auth}{host}:{port}/?service_name={svc}"

        else:
            db = database or service_name
            return f"{driver}://{auth}{host}:{port}/{db}"

    def get_db_dsn_display(self, name: str) -> str:
        """Return a password-redacted DSN string for display."""
        conn = self.db_connections.get(name, {})
        host = conn.get("host", "")
        port = conn.get("port", "")
        service = conn.get("service_name", "") or conn.get("database", "")
        username = conn.get("username", "")
        driver = conn.get("driver", "")
        return f"{driver}://{username}@{host}:{port}/{service}"

    # ------------------------------------------------------------------
    # Skills root resolution
    # ------------------------------------------------------------------
    def resolved_skills_root(self) -> Path:
        if self.skills_root:
            return Path(self.skills_root)
        # Default: skills/ relative to this package's source tree
        return Path(__file__).parent.parent.parent / "skills"
