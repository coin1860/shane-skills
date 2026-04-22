## Why

`shane-skills` already has a `shane-skills init` mechanism to deploy AI skill files into developer projects, but the companion CLI tools (Jira, Confluence, web fetch, Oracle DB) are either missing or incomplete. GitHub Copilot and OpenCode can then use terminal commands as a lightweight, MCP-free way to retrieve context from enterprise systems—no daemon required.

## What Changes

- **Enhance Jira client**: add `jql_search`, `text_search`, and `create_issue` with full Markdown output matching kb-agent style
- **Enhance Confluence client**: add `get_page` (by ID, returns Markdown) and `create_page`
- **New Web client**: lightweight URL → Markdown fetch using `requests` + `beautifulsoup4` only (no Playwright/crawl4ai)
- **Enhance DB client**: add Oracle-specific support, query-only DML guard, `schema` (list tables) and `describe` (table DDL) commands
- **Config atomization for DB**: split DB connection URL into host/port/service/user fields; store password in OS keychain via `keyring`
- **New CLI commands**: `shane-skills jira search/jql/create`, `shane-skills confluence page/create`, `shane-skills web fetch`, `shane-skills db schema/describe`
- **New skill Markdown files**: `jira-tools.md`, `confluence-tools.md`, `web-tools.md`, `db-tools.md` deployed via `shane-skills init`
- **Update Settings GUI/TUI**: add DB type selector (Oracle / PostgreSQL / MSSQL), atomic host/port/service fields, keyring-backed password

## Capabilities

### New Capabilities

- `jira-cli`: Full Jira CLI — fetch issue (Markdown), JQL search, text search, create issue
- `confluence-cli`: Full Confluence CLI — CQL search, fetch page by ID (Markdown), create page
- `web-fetch`: Lightweight URL → Markdown fetch for giving AI web page context
- `oracle-db`: Read-only Oracle DB CLI — query, schema list, table describe; Oracle password in keyring
- `cli-skills`: Skill Markdown files teaching Copilot/OpenCode how to invoke each CLI tool

### Modified Capabilities

- `settings-gui`: DB connections tab gains type selector + atomic fields + keyring password support

## Impact

- `src/shane_skills/integrations/jira_client.py` — enhanced
- `src/shane_skills/integrations/confluence_client.py` — enhanced
- `src/shane_skills/integrations/web_client.py` — new file
- `src/shane_skills/integrations/db_client.py` — enhanced (DML guard, schema, Oracle)
- `src/shane_skills/config.py` — DB connection schema + keyring methods
- `src/shane_skills/cli.py` — new subcommands
- `src/shane_skills/gui/settings_app.py` + `settings_tui.py` — DB tab updated
- `skills/copilot/jira-tools.md` — new
- `skills/copilot/confluence-tools.md` — new
- `skills/copilot/web-tools.md` — new
- `skills/copilot/db-tools.md` — new
- `pyproject.toml` — add `oracledb`, `beautifulsoup4`, `markdownify`
