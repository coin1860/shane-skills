# shane-skills

> A personal AI skills & agent library for HSBC SDLC workflows — GitHub Copilot & OpenCode compatible.

## Overview

`shane-skills` is a CLI + GUI toolkit for managing and deploying AI coding skills/agents across projects. It supports:

- 📁 **Skills & Agents**: Markdown-based skill/agent definitions for GitHub Copilot and OpenCode
- 🚀 **`shane-skills init`**: Auto-deploy skills into any project's `.github/` or `.opencode/` directory
- 🔗 **SDLC Integrations**: CLI access to Jira, Confluence, and databases via personal API keys
- 🖥️ **Config GUI**: A secure GUI for managing personal tokens and workspace settings

## Quick Start

```bash
# Install
pip install -e .

# Add optional Oracle DB and GUI support
pip install -e ".[ora,pyqt]"

# Initialize skills in current project
shane-skills init

# Get help on available commands
shane-skills --help
shane-skills jira --help
```

## Project Structure

```
shane-skills/
├── skills/                    # Skill markdown files
│   ├── copilot/               # GitHub Copilot instructions (.github/copilot-instructions.md)
│   │   ├── hsbc-sdlc.md       # HSBC SDLC general guidelines
│   │   ├── jira-tools.md      # Jira CLI instruction skill
│   │   ├── confluence-tools.md
│   │   ├── web-tools.md
│   │   └── db-tools.md
│   ├── opencode/              # OpenCode agent definitions
│   │   └── agents/
│   │       ├── jira-agent.md
│   │       └── code-review-agent.md
│   └── shared/                # Shared content referenced by both
├── src/
│   └── shane_skills/
│       ├── __init__.py
│       ├── cli.py             # Main CLI entrypoint (Click-based)
│       ├── init_cmd.py        # `shane-skills init` command
│       ├── config.py          # Config management (keyring + TOML)
│       ├── gui/
│       │   ├── settings_app.py  # PyQt6 settings GUI
│       │   └── settings_tui.py  # Textual terminal UI
│       └── integrations/
│           ├── jira_client.py     # Jira REST API client
│           ├── confluence_client.py
│           ├── web_client.py      # URL fetcher
│           └── db_client.py       # DB query CLI helper
├── pyproject.toml
├── README.md
└── .gitignore
```

## Skills Format

### GitHub Copilot Skills
Placed at `.github/copilot-instructions.md` in your project.

### OpenCode Agents
Placed at `.opencode/agents/` or as `AGENTS.md` in project root.

## CLI Integrations & Commands

You can use `shane-skills --help` at any time to see the command list.
Run `<command> --help` to see specific subcommands (e.g., `shane-skills jira --help`).

### General
| Command | Description |
|---------|-------------|
| `shane-skills init` | Deploy skills to current project |
| `shane-skills list` | List available skills |
| `shane-skills config` | Open settings GUI (use `--tui` for terminal UI) |

### Jira
| Command | Description |
|---------|-------------|
| `shane-skills jira fetch FSR-123` | Fetch Jira issue as Markdown |
| `shane-skills jira search "login error"` | Search Jira issues by text |
| `shane-skills jira jql "project=FSR"` | Execute raw JQL query |
| `shane-skills jira create --project FSR --summary "Bug"` | Create a new Jira issue |

### Confluence
| Command | Description |
|---------|-------------|
| `shane-skills confluence search "API docs"` | Search Confluence pages |
| `shane-skills confluence page 12345` | Fetch page by ID as Markdown |
| `shane-skills confluence create --parent 123 --title "Doc" --content "..."` | Create a new page |

### Web
| Command | Description |
|---------|-------------|
| `shane-skills web fetch https://example.com` | Fetch web page as Markdown |

### Database
*(Read-only operations. DML/DDL like INSERT/UPDATE/DELETE are blocked.)*
| Command | Description |
|---------|-------------|
| `shane-skills db query "SELECT * FROM users"` | Run read-only SQL query |
| `shane-skills db schema` | List all tables for a connection |
| `shane-skills db describe my_table` | Show column structure for a table |
| `shane-skills db connections` | List configured DB connections |
| `shane-skills db test prod` | Test a DB connection |
