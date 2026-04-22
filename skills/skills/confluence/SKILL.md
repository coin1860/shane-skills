---
name: confluence
description: Confluence CLI Tools
---

# Confluence CLI Tools

You have access to the `shane-skills` CLI for Confluence operations on the private Confluence server.
Run commands in the terminal and paste the output back into the chat for context.

## Search Pages

Searches Confluence pages by text using CQL. Returns a table of matching pages with their IDs.

```bash
shane-skills confluence search "kubernetes deployment guide"
shane-skills confluence search "API design standards" --space ARCH --limit 10
```

The output includes **Page IDs** — use them with the `page` command to fetch full content.

## Fetch Full Page Content

Fetches a Confluence page by its numeric ID and prints the full content as Markdown.
This is ideal for giving AI the detailed content of a specific page.

```bash
shane-skills confluence page 123456789
```

Tip: Get the page ID from `confluence search` output, or from the URL parameter `?pageId=123456789`.

## Create a Page

Creates a new Confluence page as a child of an existing page.

```bash
shane-skills confluence create \
  --parent 123456789 \
  --title "Architecture Decision Record: Use oracledb" \
  --content "# ADR\n\n## Decision\nWe will use python-oracledb thin mode..."
```

## Workflow Tips

- Always `search` first to find the right page ID
- Use `page` to retrieve full content before asking AI to summarize or reference it
- Use `create` to document decisions or meeting notes directly from the terminal
