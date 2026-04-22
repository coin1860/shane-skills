## MODIFIED Requirements

### Requirement: DB connections tab uses atomic fields
The Settings GUI (both PyQt6 and Textual TUI) Databases tab SHALL provide a type selector (Oracle / PostgreSQL / MSSQL / MySQL) that pre-fills the default port and driver, and SHALL expose discrete form fields: Connection Name, Host, Port, Database/Service Name, Username, Password. The Password field SHALL be masked and stored via `keyring` on save.

#### Scenario: Oracle type pre-fills defaults
- **WHEN** user selects "Oracle" in the DB type dropdown
- **THEN** Port field auto-fills to "1521" and driver is set to "oracle+oracledb"

#### Scenario: PostgreSQL type pre-fills defaults
- **WHEN** user selects "PostgreSQL"
- **THEN** Port auto-fills to "5432" and driver is set to "postgresql+psycopg2"

#### Scenario: Password stored in keychain
- **WHEN** user enters a password and clicks Save
- **THEN** password is stored via `keyring.set_password("shane-skills:db:{name}", username, password)` and NOT written to config.toml

#### Scenario: Existing connection loads without password
- **WHEN** user reopens config and selects an existing DB connection
- **THEN** all fields populate from config.toml, password field shows placeholder "●●●● (stored in keychain)"
