---
name: db
description: Database CLI Tools (Read-Only)
---

# Database CLI Tools (Read-Only)

You have access to the `shane-skills` CLI for Oracle and other database operations.

> **IMPORTANT**: Only SELECT queries are permitted. INSERT, UPDATE, DELETE, DROP, ALTER,
> CREATE, TRUNCATE, MERGE and all other DML/DDL statements are **BLOCKED** and will return an error.
> Never suggest running DML commands through this CLI.

## List Configured Connections

```bash
shane-skills db connections
```

## Run a SELECT Query

Executes a read-only query and displays results as a table.

```bash
shane-skills db query "SELECT * FROM EMPLOYEES WHERE ROWNUM <= 10"
shane-skills db query "SELECT col1, col2 FROM my_table WHERE status='ACTIVE'" --limit 50
```

Options:
- `--limit N` — max rows to show (default: 20)

## Explore Database Schema

List all accessible tables for a connection:

```bash
shane-skills db schema
```

Describe a specific table's columns (name, type, nullable, default):

```bash
shane-skills db describe EMPLOYEES
shane-skills db describe HR.EMPLOYEES
```

## Test a Connection

```bash
shane-skills db test
```

## Recommended Workflow for AI-Assisted Queries

1. Run `shane-skills db schema` to see what tables exist
2. Run `shane-skills db describe <TABLE>` for the relevant tables
3. Paste the schema output into the chat so AI can write correct SQL
4. Review the AI-generated SQL, then run it with `shane-skills db query "..."`
5. Paste results back for analysis

This workflow avoids hallucinated column names and ensures type-safe queries.
