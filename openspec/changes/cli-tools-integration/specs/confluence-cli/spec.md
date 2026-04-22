## ADDED Requirements

### Requirement: Search Confluence pages
The `ConfluenceClient` SHALL support CQL text search returning a table of matching pages with title, space, and URL.

#### Scenario: Search returns results
- **WHEN** user runs `shane-skills confluence search "deployment guide"`
- **THEN** CLI prints a table with title, space, and URL of matching pages

#### Scenario: Search with space filter
- **WHEN** user runs `shane-skills confluence search "api docs" --space TEAM`
- **THEN** only pages in the TEAM space are returned

#### Scenario: No results
- **WHEN** search matches no pages
- **THEN** CLI prints "No results for: <query>"

### Requirement: Fetch Confluence page content as Markdown
The `ConfluenceClient` SHALL fetch a page by its numeric ID and output the full page content as Markdown. The format SHALL mirror kb-agent's `_format_page` output, including: title, space, version, last modified date/author, URL, ancestor path, and full body content.

#### Scenario: Fetch page by ID
- **WHEN** user runs `shane-skills confluence page 123456789`
- **THEN** CLI prints the full Markdown content of the page

#### Scenario: Page not found
- **WHEN** the page ID does not exist or access is denied
- **THEN** CLI prints a clear error message

#### Scenario: Confluence not configured
- **WHEN** Confluence URL or token is missing
- **THEN** CLI prints "Run `shane-skills config` to set up Confluence"

### Requirement: Create Confluence page
The `ConfluenceClient` SHALL create a new Confluence page as a child of a given parent page ID.

#### Scenario: Successful page creation
- **WHEN** user runs `shane-skills confluence create --parent 123456789 --title "New Page" --content "# Hello\n\nContent here"`
- **THEN** CLI prints the new page ID, title, and URL

#### Scenario: Missing parent ID
- **WHEN** --parent is not provided
- **THEN** CLI prints error: "--parent <page-id> is required"

### Requirement: Markdown output consistency
All Confluence output MUST render as structured Markdown so AI tools can read and reference page content.

#### Scenario: Page content is Markdown
- **WHEN** fetching any Confluence page
- **THEN** HTML storage format is converted to readable Markdown with headers, path breadcrumbs, and metadata
