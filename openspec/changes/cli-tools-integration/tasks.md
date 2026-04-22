## 1. Dependencies & Config

- [ ] 1.1 Add `oracledb`, `beautifulsoup4`, `markdownify` to `pyproject.toml` dependencies
- [ ] 1.2 Update `config.py`: change DB connection schema from `{url, driver}` to `{host, port, service_name, database, username, driver}` with backward-compat URL builder
- [ ] 1.3 Add `get_db_password(name)` and `set_db_password(name, username, password)` methods to `Config` using `keyring` (key: `shane-skills:db:{name}`)
- [ ] 1.4 Add `build_db_url(name)` helper in `Config` that assembles the SQLAlchemy URL from atomic fields + keyring password

## 2. Jira Client

- [ ] 2.1 Add `_format_issue(data, comments)` method to `JiraClient` that outputs kb-agent-style Markdown (key, type, status, priority, labels, components, URL, description, comments)
- [ ] 2.2 Add `search(text, limit=20)` method: runs JQL `text ~ "..." ORDER BY updated DESC`
- [ ] 2.3 Add `jql(query, limit=20)` method: executes raw JQL string
- [ ] 2.4 Add `create_issue(project, summary, description, issue_type)` method
- [ ] 2.5 Update `print_issue()` to use `_format_issue()` for Markdown-style output instead of table rows
- [ ] 2.6 Add `print_search_results(results)` helper that prints a summary table of multiple issues

## 3. Confluence Client

- [ ] 3.1 Add `_format_page(data)` method that outputs kb-agent-style Markdown (title, space, version, last modified, URL, ancestor path, full body as Markdown via `markdownify`)
- [ ] 3.2 Add `get_page(page_id)` method: fetches page by numeric ID with `body.storage,space,version,ancestors` expand
- [ ] 3.3 Add `print_page(page_id)` that calls `get_page` and prints Markdown output
- [ ] 3.4 Add `create_page(parent_id, title, content)` method with space key resolution
- [ ] 3.5 Update `search_and_print()` to also show page IDs so users can do follow-up `confluence page <id>`

## 4. Web Client

- [ ] 4.1 Create `src/shane_skills/integrations/web_client.py`
- [ ] 4.2 Implement `WebClient.fetch(url)` using `requests` + `BeautifulSoup` + `markdownify`; strip nav/footer/script/style/sidebar/banner elements; target `<article>`, `<main>`, `<div role="main">`
- [ ] 4.3 Add `--max-chars` option (default 8000); truncate with "[truncated at N chars]" note
- [ ] 4.4 Add `print_fetch(url, max_chars)` that prints title + Markdown content

## 5. DB Client

- [ ] 5.1 Add DML/DDL guard `_validate_readonly(sql)` in `DBClient`: check first token against blocklist, raise `ValueError` with clear message
- [ ] 5.2 Update `_get_engine()` to use `Config.build_db_url(name)` (atomic fields + keyring password) instead of raw URL
- [ ] 5.3 Add `schema(connection_name)`: list all tables (Oracle: query `ALL_TABLES`; others: SQLAlchemy `inspect().get_table_names()`)
- [ ] 5.4 Add `describe(table_name, connection_name)`: list columns with type, nullable, default (Oracle: `ALL_TAB_COLUMNS`; others: SQLAlchemy `inspect().get_columns()`)
- [ ] 5.5 Update `query_and_print()` to call `_validate_readonly()` before executing
- [ ] 5.6 Add `print_schema(connection_name)` and `print_describe(table, connection_name)` for CLI output

## 6. CLI Commands

- [ ] 6.1 Add `shane-skills jira search <text>` subcommand wired to `JiraClient.search()`
- [ ] 6.2 Add `shane-skills jira jql <query>` subcommand wired to `JiraClient.jql()`
- [ ] 6.3 Add `shane-skills jira create --project --summary [--description] [--type]` subcommand
- [ ] 6.4 Add `shane-skills confluence page <page-id>` subcommand wired to `ConfluenceClient.print_page()`
- [ ] 6.5 Add `shane-skills confluence create --parent --title --content` subcommand
- [ ] 6.6 Add `shane-skills web fetch <url> [--max-chars N]` command group and subcommand
- [ ] 6.7 Add `shane-skills db schema [--connection name]` subcommand
- [ ] 6.8 Add `shane-skills db describe <table> [--connection name]` subcommand
- [ ] 6.9 Update `shane-skills db connections` to show atomic fields (host, port, service) not raw URL

## 7. Settings GUI Updates

- [ ] 7.1 Update `settings_tui.py` Databases tab: add DB type `Select` widget (Oracle/PostgreSQL/MSSQL/MySQL), atomic input fields (Host, Port, Database/Service Name, Username, Password), auto-fill port/driver on type selection
- [ ] 7.2 Update `settings_tui.py` save logic: store atomic fields to `config.db_connections`, call `cfg.set_db_password(name, username, password)` for keychain storage
- [ ] 7.3 Update `settings_tui.py` DB list display: show `host:port/service_name` instead of raw URL
- [ ] 7.4 Update `settings_app.py` (PyQt6) with same atomic DB fields, type `QComboBox`, keychain password save
- [ ] 7.5 Add "Test Connection" button in both TUI and GUI that runs `SELECT 1` (or `SELECT 1 FROM DUAL` for Oracle) and shows success/error

## 8. Skill Markdown Files

- [ ] 8.1 Create `skills/copilot/jira-tools.md` with usage examples for all `shane-skills jira` subcommands
- [ ] 8.2 Create `skills/copilot/confluence-tools.md` with usage examples for all `shane-skills confluence` subcommands
- [ ] 8.3 Create `skills/copilot/web-tools.md` with usage example for `shane-skills web fetch` and when to use it
- [ ] 8.4 Create `skills/copilot/db-tools.md` with usage examples for all `shane-skills db` subcommands, prominently noting DML is blocked and explaining schema/describe workflow for AI

## 9. Integration & Tests

- [ ] 9.1 Manually test `shane-skills jira <key>` against private Jira instance
- [ ] 9.2 Manually test `shane-skills confluence page <id>` and verify Markdown output matches kb-agent style
- [ ] 9.3 Manually test `shane-skills web fetch https://example.com`
- [ ] 9.4 Manually test `shane-skills db query "SELECT 1 FROM DUAL"` with Oracle connection
- [ ] 9.5 Verify `shane-skills db query "DELETE FROM X"` is blocked with correct error message
- [ ] 9.6 Run `shane-skills init --dry-run` and verify all 4 new skill files appear in merged output
