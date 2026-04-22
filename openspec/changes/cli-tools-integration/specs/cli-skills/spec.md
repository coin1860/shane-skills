## ADDED Requirements

### Requirement: Jira skill file
A skill Markdown file `skills/copilot/jira-tools.md` SHALL exist that teaches Copilot/OpenCode how to use `shane-skills jira` subcommands. It SHALL include usage examples for fetch, search, jql, and create.

#### Scenario: Skill deployed via init
- **WHEN** user runs `shane-skills init` in a project directory
- **THEN** `jira-tools.md` content is merged into `.github/copilot-instructions.md`

### Requirement: Confluence skill file
A skill Markdown file `skills/copilot/confluence-tools.md` SHALL exist covering `confluence search`, `confluence page`, and `confluence create` commands.

#### Scenario: Skill deployed via init
- **WHEN** user runs `shane-skills init`
- **THEN** `confluence-tools.md` content appears in `.github/copilot-instructions.md`

### Requirement: Web fetch skill file
A skill Markdown file `skills/copilot/web-tools.md` SHALL exist explaining how to use `shane-skills web fetch <url>` to retrieve web page content as Markdown for AI context.

#### Scenario: Skill deployed via init
- **WHEN** user runs `shane-skills init`
- **THEN** `web-tools.md` content appears in `.github/copilot-instructions.md`

### Requirement: DB skill file
A skill Markdown file `skills/copilot/db-tools.md` SHALL exist covering `db query`, `db schema`, `db describe`, and `db connections`. It SHALL explicitly state that only SELECT queries are permitted and explain how to use schema/describe to help AI write correct SQL.

#### Scenario: Skill deployed via init
- **WHEN** user runs `shane-skills init`
- **THEN** `db-tools.md` content appears in `.github/copilot-instructions.md`

#### Scenario: DB skill warns about DML
- **WHEN** Copilot reads the db-tools.md skill
- **THEN** it knows NOT to suggest DML commands via the CLI
