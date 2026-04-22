## ADDED Requirements

### Requirement: Query-only enforcement
The `DBClient` SHALL refuse to execute any SQL statement whose first token (case-insensitive) is a DML or DDL keyword: `INSERT`, `UPDATE`, `DELETE`, `DROP`, `TRUNCATE`, `ALTER`, `CREATE`, `MERGE`, `REPLACE`, `EXEC`, `EXECUTE`, `CALL`. Any such attempt SHALL exit with a non-zero code and a human-readable error.

#### Scenario: SELECT query is allowed
- **WHEN** user runs `shane-skills db query "SELECT * FROM EMPLOYEES WHERE ROWNUM <= 5"`
- **THEN** CLI executes the query and prints results as a table

#### Scenario: DML is blocked
- **WHEN** user runs `shane-skills db query "DELETE FROM ORDERS WHERE id=1"`
- **THEN** CLI prints "Error: DML/DDL statements are not permitted. Only SELECT queries are allowed." and exits with code 1

#### Scenario: DDL is blocked
- **WHEN** user runs `shane-skills db query "DROP TABLE foo"`
- **THEN** CLI prints error and exits without executing

### Requirement: List database tables (schema)
The `DBClient` SHALL support a `shane-skills db schema` command that lists all accessible tables (name, owner/schema, type) for the configured connection.

#### Scenario: Schema list succeeds
- **WHEN** user runs `shane-skills db schema --connection prod`
- **THEN** CLI prints a table of table names, schemas, and types

#### Scenario: No tables found
- **WHEN** the user has no accessible tables
- **THEN** CLI prints "No tables found for this connection"

### Requirement: Describe table structure
The `DBClient` SHALL support a `shane-skills db describe <table>` command that prints column names, data types, nullable status, and default values for the given table — enabling AI to understand the schema before writing queries.

#### Scenario: Describe existing table
- **WHEN** user runs `shane-skills db describe EMPLOYEES --connection prod`
- **THEN** CLI prints a table with column name, type, nullable, and default for each column

#### Scenario: Table not found
- **WHEN** the specified table does not exist
- **THEN** CLI prints "Table '<name>' not found in connection '<connection>'"

### Requirement: Oracle connection support
The system SHALL support Oracle Database connections using `python-oracledb` in thin mode (no Oracle Instant Client required). The SQLAlchemy dialect SHALL be `oracle+oracledb`.

#### Scenario: Oracle thin mode connection
- **WHEN** a DB connection is configured with driver `oracle+oracledb` and valid host/port/service_name
- **THEN** `shane-skills db query "SELECT 1 FROM DUAL"` succeeds without Oracle Instant Client installed

### Requirement: Atomic connection configuration
DB connections SHALL be stored as discrete fields (`host`, `port`, `service_name` or `database`, `username`, `driver`) in `~/.shane-skills/config.toml`. Passwords SHALL be stored in the OS keychain via `keyring` using key `shane-skills:db:{connection_name}`.

#### Scenario: Add Oracle connection via config GUI
- **WHEN** user opens `shane-skills config`, selects "Oracle" from the DB type dropdown, fills in host/port/service/user/password, and saves
- **THEN** connection fields are written to config.toml and password is stored in keychain

#### Scenario: Password not in plaintext
- **WHEN** user inspects `~/.shane-skills/config.toml` after saving a DB connection
- **THEN** the file contains no password field — only host, port, service_name, username, driver

### Requirement: List configured connections
The CLI SHALL support `shane-skills db connections` to list all configured connection names and their (password-redacted) DSN.

#### Scenario: Connections listed
- **WHEN** user runs `shane-skills db connections`
- **THEN** CLI prints a table of connection names with host, port, service/db, and username (no password)
