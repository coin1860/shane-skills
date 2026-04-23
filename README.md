# Shane Skills

![Backend](https://img.shields.io/badge/Backend-Python_3.11+-blue?style=flat-square)
![UI](https://img.shields.io/badge/UI-Textual_TUI-green?style=flat-square)
![CLI](https://img.shields.io/badge/CLI-Click-orange?style=flat-square)
![Security](https://img.shields.io/badge/Security-OS_Keychain-red?style=flat-square)

**A modular toolkit and agentic skill-set for GitHub Copilot and OpenCode developers.**

---

**Shane Skills** is a high-performance, developer-centric CLI and TUI suite designed to bridge the gap between AI coding assistants and corporate engineering ecosystems. It provides a standardized layer for interacting with **Jira**, **Confluence**, **Oracle/SQL Databases**, and **Web content**, while hosting specialized **AI Agents** for complex tasks like JDK migrations and security reviews.

---

### 🧠 Core Capabilities

*   **Secure Credential Management**: Integration with the OS Keychain (`keyring`) ensures that sensitive tokens for Jira, Confluence, and Database passwords never touch plain-text config files.
*   **Dual Interface Model**:
    *   **CLI**: Optimized for AI Agents (Copilot/OpenCode) to execute atomic tasks.
    *   **TUI**: A rich, interactive terminal interface for humans to manage configurations and test connections.
*   **Read-Only Data Safety**: The Database skill features a strict SQL parser that blocks DML/DDL (INSERT/UPDATE/DELETE) to ensure zero-risk data exploration.
*   **Markdown-First Design**: All tool outputs are automatically converted to clean, AI-friendly Markdown for immediate context injection.

---

### 🛠️ Supported Skills

The following skills are available as atomic CLI commands under `shane-skills <skill>`.

| Skill | Category | Capabilities |
| :--- | :--- | :--- |
| **Jira** | Project Management | Fetch issues, JQL search, full-text search, and issue creation. |
| **Confluence** | Documentation | Search by CQL, recursive page fetching, and automated page creation. |
| **Database** | Data Exploration | Read-only access to **Oracle**, **PostgreSQL**, and **MySQL**. Schema discovery & table description. |
| **Web Fetch** | Intelligence | Convert any URL (documentation, wikis) into clean Markdown context. |
| **Python** | Standards | Integrated best practices for type hints, ruff linting, and async testing. |
| **Graph Build** | Intelligence | Build a knowledge graph from any folder of files. Generates clustered communities, HTML, JSON, and a report. (`/graphify`) |
| **Graph Query** | Intelligence | Query a graphify knowledge graph to traverse, explain nodes, or find shortest paths. (`/graphify query`) |

---

### 🤖 Specialized Agents

Shane Skills hosts a library of "Agent Personas" located in `skills/agents/`. These are optimized for high-reasoning tasks:

#### 1. JDK Upgrade Agent (`jdk-upgrade`)
Automates the migration of legacy Java projects:
*   **OpenJDK 8 → 17** migration path.
*   **Spring Boot 2.x → 3.x** API compatibility fixes.
*   Automated `pom.xml` dependency resolution and Jakarta EE package migration.
*   Iterative "Compile → Fix → Verify" loop.

#### 2. Code Review Agent (`code-review`)
Performs thorough reviews against HSBC engineering standards:
*   **Security**: Detects hardcoded secrets and SQL injection patterns.
*   **Quality**: Enforces SOLID principles, DRY, and strict type hinting.
*   **Testing**: Validates unit test coverage for new logic.

#### 3. GraphRAG Agent (`graph-rag`)
Knowledge graph RAG agent — builds a graph from any corpus, then answers questions by traversing it.
*   **Graph Creation**: Uses the `graph-build` skill to extract, cluster, and visualize any corpus into a knowledge graph.
*   **Graph Traversal**: Uses the `graph-query` skill to answer questions, explain nodes, and trace paths through an existing graph.
*   **Accuracy**: Never re-reads source files to answer questions, relying on the graph first. Always cites sources and never invents connections.

---

### ⚙️ Installation & Setup

**1. Install from Source**
```bash
git clone https://github.com/coin1860/shane-skills.git
cd shane-skills
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

**2. Configure the Toolkit**
Launch the interactive configuration TUI:
```bash
shane-skills config
```
*   Use the **Atlassian** tab to set up Jira/Confluence URLs and tokens.
*   Use the **Databases** tab to configure your "default" connection (Oracle, PG, etc.).
*   Passwords are automatically moved to your OS Keychain upon saving.

---

### 🚀 Usage Examples

**Database Exploration**
```bash
shane-skills db schema              # See all tables
shane-skills db describe EMPLOYEES   # View column definitions
shane-skills db query "SELECT count(*) FROM EMPLOYEES"
```

**Atlassian Integration**
```bash
shane-skills jira fetch FSR-123      # Get full context of a ticket
shane-skills confluence search "K8s" # Find internal docs
```

**Web Intelligence**
```bash
shane-skills web fetch https://docs.python.org/3/library/asyncio.html
```

---

### 🛡️ Enterprise Security
*   **No Plaintext Secrets**: All passwords/tokens are stored in `keyring`.
*   **SQL Guardrails**: Strict blocklist for `DROP`, `DELETE`, `UPDATE`, etc.
*   **Local Execution**: All processing happens on your local machine; no external telemetry.

---

© 2026 Shane Skills | Internal Developer Productivity Tools
