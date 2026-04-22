---
name: web
description: Web Fetch CLI Tool
---

# Web Fetch CLI Tool

You have access to the `shane-skills` CLI to fetch web pages and convert them to Markdown.
This is useful for giving AI context from documentation sites, internal wikis, or public pages.

## Fetch a Web Page

Fetches a URL and converts the main content to clean Markdown for AI context.
Uses lightweight HTTP fetching — no browser required.

```bash
shane-skills web fetch https://kubernetes.io/docs/concepts/workloads/pods/
shane-skills web fetch https://docs.python.org/3/library/asyncio.html
shane-skills web fetch https://internal-docs.company.com/api-guide --max-chars 12000
```

## Options

- `--max-chars N` — Truncate output at N characters (default: 8000). Increase for long pages.

## When to Use

- Fetching API documentation to understand a library
- Reading an internal wiki page that isn't in Confluence
- Reviewing a GitHub README or issue before writing code
- Getting context from a blog post or technical article

## Limitations

- JavaScript-heavy pages (SPAs, dashboards) may not render fully — only static HTML is fetched
- Pages behind authentication (login walls) cannot be fetched
- For Confluence pages, use `shane-skills confluence page` instead — it has proper API access
