## ADDED Requirements

### Requirement: Fetch web page as Markdown
The `WebClient` SHALL fetch a given HTTP/HTTPS URL and convert the main content to Markdown using `requests` + `beautifulsoup4` + `markdownify`. No browser or Playwright dependency is permitted.

#### Scenario: Successful fetch
- **WHEN** user runs `shane-skills web fetch https://example.com/docs/api`
- **THEN** CLI prints the page title and Markdown content of the main content area

#### Scenario: Invalid URL
- **WHEN** URL does not start with http:// or https:// and cannot be inferred
- **THEN** CLI prints "Invalid URL. Must start with http:// or https://"

#### Scenario: Network error
- **WHEN** the URL is unreachable or returns non-200 status
- **THEN** CLI prints an error message with the HTTP status or exception

### Requirement: Content extraction focus
The fetcher SHALL strip navigation, footer, header, script, style, sidebar, cookie banner, and advertisement elements before converting to Markdown, targeting `<article>`, `<main>`, or `<div role="main">` as the primary content zone.

#### Scenario: Article page extraction
- **WHEN** fetching a documentation page with a `<main>` element
- **THEN** output contains only the main article content, not nav or footer text

### Requirement: Output length control
The `web fetch` command SHALL support a `--max-chars` option (default: 8000) to truncate output, preventing token overload when used as AI context.

#### Scenario: Long page truncation
- **WHEN** extracted Markdown exceeds `--max-chars`
- **THEN** output is truncated at the character limit with a note: "[truncated at N chars]"
