## ADDED Requirements

### Requirement: Fetch Jira issue as Markdown
The `JiraClient` SHALL fetch a Jira issue by key and return rich Markdown output including: issue key, summary, type, status, priority, labels, components, URL, description, and last 10 comments. The format SHALL mirror kb-agent's `_format_issue` output.

#### Scenario: Fetch existing issue
- **WHEN** user runs `shane-skills jira FSR-123`
- **THEN** CLI prints a rich table/markdown block with all issue fields including status, priority, description, and URL

#### Scenario: Issue not found
- **WHEN** user runs `shane-skills jira PROJ-999` and the issue does not exist
- **THEN** CLI prints a clear error message with the issue key

#### Scenario: Jira not configured
- **WHEN** Jira URL or token is missing from config
- **THEN** CLI prints an actionable error: "Run `shane-skills config` to set up Jira"

### Requirement: Search Jira by text
The `JiraClient` SHALL support free-text search using JQL `text ~ "..."` and return up to 20 matching issues as a formatted list.

#### Scenario: Text search returns results
- **WHEN** user runs `shane-skills jira search "kubernetes deployment"`
- **THEN** CLI prints a table of matching issues with key, summary, status, and URL

#### Scenario: Text search returns no results
- **WHEN** search query matches no issues
- **THEN** CLI prints "No results found for: <query>"

### Requirement: JQL search
The `JiraClient` SHALL accept a raw JQL string and execute it, returning results as a formatted list.

#### Scenario: Valid JQL query
- **WHEN** user runs `shane-skills jira jql "project=PROJ AND status=Open ORDER BY updated DESC"`
- **THEN** CLI prints a table of matching issues

#### Scenario: Invalid JQL
- **WHEN** JQL syntax is invalid
- **THEN** CLI prints the Jira API error message

### Requirement: Create Jira issue
The `JiraClient` SHALL create a new Jira issue given project key, summary, optional description, and optional issue type (default: Task).

#### Scenario: Successful creation
- **WHEN** user runs `shane-skills jira create --project PROJ --summary "Bug: login fails" --description "Steps to reproduce..."`
- **THEN** CLI prints the created issue key and browse URL

#### Scenario: Missing project key
- **WHEN** no --project is provided and no default project is configured
- **THEN** CLI prints error: "No project key provided. Use --project or configure a default."

### Requirement: Markdown output consistency
All Jira output MUST render as structured Markdown text (not just raw JSON) so AI tools can parse and understand the content.

#### Scenario: Issue content is Markdown
- **WHEN** fetching any Jira issue
- **THEN** output includes properly formatted Markdown headers, bold field labels, and human-readable values
