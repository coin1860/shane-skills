---
name: jira
description: Jira CLI Tools
---

# Jira CLI Tools

You have access to the `shane-skills` CLI for Jira operations on the private Jira server.
Run commands in the terminal and paste the output back into the chat for context.

## Fetch an Issue

Fetches a single issue and displays it as Markdown with full description and comments.

```bash
shane-skills jira fetch FSR-123
shane-skills jira fetch FSR-123 --json   # raw JSON output
```

## Search Issues by Text

Searches all Jira issues matching the given text (uses JQL `text ~ "..."`).

```bash
shane-skills jira search "kubernetes deployment failure"
shane-skills jira search "auth token expiry" --limit 10
```

## Search with Raw JQL

Executes a raw JQL query directly.

```bash
shane-skills jira jql "project=FSR AND status=Open AND assignee=currentUser()"
shane-skills jira jql "priority=High AND created >= -7d ORDER BY created DESC" --limit 5
```

## Create an Issue

Creates a new Jira issue and returns the issue key and URL.

```bash
shane-skills jira create --project FSR --summary "Bug: login fails after token refresh"
shane-skills jira create --project FSR --summary "Task: update K8s config" --description "Details..." --type Task
```

## Workflow Tips

- Use `fetch` when you know the issue key
- Use `search` when you need to find related issues by keyword
- Use `jql` for precise date/assignee/status filters
- After creating an issue, share the URL with the team
