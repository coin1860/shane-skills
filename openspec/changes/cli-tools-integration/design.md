## Context

`shane-skills` is a lightweight Python CLI tool that deploys Markdown skill files into developer projects, enabling GitHub Copilot and OpenCode to understand workflows without MCP. It already has thin stubs for Jira, Confluence, and DB integrations in `src/shane_skills/integrations/`, but they lack full functionality.

The strategy is to **port core logic from kb-agent's connectors** (which are battle-tested) into shane-skills' integration layer, while keeping dependencies minimal. The output format (Markdown-rendered rich text) MUST mirror kb-agent's style so AI tools receive consistent, structured context.

## Goals / Non-Goals

**Goals:**
- Enrich Jira client: search (text + JQL), create issue, full Markdown output
- Enrich Confluence client: page fetch by ID (full Markdown), create page
- New lightweight web fetch: URL → Markdown via `requests` + `bs4` only
- Safe Oracle DB client: DML guard, schema/describe commands, atomic config with keyring passwords
- Per-service skill Markdown files (`jira-tools.md`, etc.) deployed by `shane-skills init`
- DB config atomization: host/port/service/user in TOML, password in OS keychain

**Non-Goals:**
- No vector search / RAG / ChromaDB dependency
- No LangGraph or agent orchestration
- No MCP server or long-running daemon
- No Crawl4AI / Playwright (web fetch is requests-only)
- No DML (INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/TRUNCATE/MERGE) in DB client

## Decisions

### D1: Code strategy — port, not depend
**Decision**: Reproduce the output format and core logic from kb-agent's `connectors/` into shane-skills' `integrations/`. Do NOT add `kb-agent` as a dependency.

**Rationale**: kb-agent pulls in ChromaDB, LangGraph, embedding models — far too heavy for a CLI utility. The output format (Markdown with metadata headers) is the key shared contract, not the code itself.

**Alternative considered**: Import directly from kb-agent. Rejected — would defeat the "lightweight" goal and create a tight coupling between two separate projects.

### D2: Web fetch — requests-only, no browser
**Decision**: Use `requests` + `beautifulsoup4` + `markdownify` for web fetch. Same stack already used in kb-agent's `_fetch_with_requests` fallback.

**Rationale**: Playwright/crawl4ai adds ~100MB of browser dependencies. For developer workflow URLs (Confluence pages, GitHub, docs sites), requests-based fetch is sufficient.

### D3: DB password in keyring, connection fields atomic
**Decision**: Split DB connection from a single SQLAlchemy URL string to discrete fields (`host`, `port`, `service_name`/`database`, `username`, `driver`). Password stored via `keyring` using key `shane-skills:db:{connection_name}`.

**Rationale**: Storing plaintext passwords in `~/.shane-skills/config.toml` is a security risk. Atomic fields allow the Settings GUI to show a structured form (type selector → specific fields) rather than a raw URL. Matches the pattern already used for Jira/Confluence tokens.

**Alternative considered**: Keep URL-based config but strip password. Too fragile — URL parsing is error-prone across dialects.

### D4: Oracle driver — python-oracledb thin mode
**Decision**: Use `python-oracledb` (SQLAlchemy dialect: `oracle+oracledb`) in thin mode. Do NOT use `cx_Oracle`.

**Rationale**: `python-oracledb` thin mode requires no Oracle Instant Client system dependency. `pip install oracledb` is sufficient. Listed as optional dependency to avoid breaking non-Oracle users.

### D5: DML guard — keyword prefix check
**Decision**: Before executing any SQL, check the first non-whitespace token against a blocklist: `{INSERT, UPDATE, DELETE, DROP, TRUNCATE, ALTER, CREATE, MERGE, REPLACE, EXEC, EXECUTE, CALL}`. Raise `ValueError` and exit with error message.

**Rationale**: Simple and robust for the use case. Not trying to be a SQL parser — just block obvious write operations.

### D6: Skill files — one per service, merged by init
**Decision**: Four separate Markdown files in `skills/copilot/`: `jira-tools.md`, `confluence-tools.md`, `web-tools.md`, `db-tools.md`. `shane-skills init` merges all `skills/copilot/*.md` into `.github/copilot-instructions.md` (existing behavior).

**Rationale**: Keeps each skill focused and maintainable. Init merge is already implemented.

### D7: Settings GUI DB tab — type selector
**Decision**: Add a `QComboBox` (PyQt6) / `Select` widget (Textual TUI) for DB type: `Oracle | PostgreSQL | MSSQL | MySQL`. Each choice pre-fills default port and driver. Fields: Name, Host, Port, Database/Service, Username, Password. Password field calls `keyring.set_password` on save.

**Rationale**: Removes the need for users to know SQLAlchemy URL syntax. Matches the "atomic" config goal.

## Risks / Trade-offs

- **keyring unavailability on headless servers** → Mitigation: `keyring` falls back to plaintext if no backend is available; document this limitation. On macOS/Linux desktop, it works natively.
- **Oracle thin mode limitations** → Some advanced Oracle features (e.g., certain auth methods) may need thick mode. → Mitigation: Document; provide escape hatch via raw SQLAlchemy URL config for power users.
- **bs4 HTML parsing quality** → Some JS-heavy pages won't render correctly. → Mitigation: Clearly document limitation in `web-tools.md` skill; this is a known trade-off for keeping deps light.
- **Markdown output fidelity** → Must match kb-agent style so AI tools parse consistently. → Mitigation: Mirror the exact content structure from kb-agent's `_format_issue` and `_format_page`.
