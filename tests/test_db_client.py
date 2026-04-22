import pytest
from unittest.mock import MagicMock, patch
from shane_skills.integrations.db_client import DBClient, _validate_readonly

def test_validate_readonly_success():
    _validate_readonly("SELECT * FROM test")
    _validate_readonly("   select id from users")
    _validate_readonly("WITH cte AS (SELECT 1) SELECT * FROM cte")

def test_validate_readonly_failure():
    with pytest.raises(ValueError, match="DML/DDL statements are not permitted"):
        _validate_readonly("DELETE FROM test")
    with pytest.raises(ValueError, match="DML/DDL statements are not permitted"):
        _validate_readonly("update users set x=1")
    with pytest.raises(ValueError, match="DML/DDL statements are not permitted"):
        _validate_readonly("DROP TABLE users")
    with pytest.raises(ValueError, match="DML/DDL statements are not permitted"):
        _validate_readonly("INSERT INTO test VALUES (1)")
    with pytest.raises(ValueError, match="DML/DDL statements are not permitted"):
        _validate_readonly("EXEC procedure")

@patch("shane_skills.integrations.db_client.Config")
@patch("shane_skills.integrations.db_client.console")
def test_from_config_not_found(mock_console, mock_config):
    mock_cfg_instance = MagicMock()
    mock_cfg_instance.get_db_connections.return_value = {}
    mock_config.load.return_value = mock_cfg_instance
    
    with pytest.raises(SystemExit):
        DBClient.from_config("missing")
    mock_console.print.assert_called()

@patch("shane_skills.integrations.db_client.Config")
def test_from_config_success(mock_config):
    mock_cfg_instance = MagicMock()
    mock_cfg_instance.get_db_connections.return_value = {"test_db": {}}
    mock_cfg_instance.build_db_url.return_value = "sqlite:///:memory:"
    mock_config.load.return_value = mock_cfg_instance
    
    client = DBClient.from_config("test_db")
    assert client.connection_name == "test_db"
    assert client.connection_url == "sqlite:///:memory:"

@patch("sqlalchemy.create_engine")
def test_get_engine(mock_create_engine):
    client = DBClient("test", "sqlite://")
    engine = client._get_engine()
    mock_create_engine.assert_called_once_with("sqlite://")
    assert engine == mock_create_engine.return_value
    # Calling again should return cached
    client._get_engine()
    assert mock_create_engine.call_count == 1

def test_is_oracle():
    assert DBClient("test", "oracle+oracledb://")._is_oracle() is True
    assert DBClient("test", "postgresql://")._is_oracle() is False

@patch("shane_skills.integrations.db_client.console")
def test_query_and_print_invalid_sql(mock_console):
    client = DBClient("test", "sqlite://")
    with pytest.raises(SystemExit):
        client.query_and_print("DELETE FROM test")
    mock_console.print.assert_called()

@patch("shane_skills.integrations.db_client.console")
@patch("shane_skills.integrations.db_client.DBClient._get_engine")
def test_query_and_print_query_error(mock_get_engine, mock_console):
    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_conn.execute.side_effect = Exception("DB error")
    mock_engine.connect.return_value.__enter__.return_value = mock_conn
    mock_get_engine.return_value = mock_engine
    
    client = DBClient("test", "sqlite://")
    with pytest.raises(SystemExit):
        client.query_and_print("SELECT 1")
    mock_console.print.assert_called()

@patch("shane_skills.integrations.db_client.console")
@patch("shane_skills.integrations.db_client.DBClient._get_engine")
def test_query_and_print_empty_result(mock_get_engine, mock_console):
    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_result = MagicMock()
    mock_result.fetchmany.return_value = []
    mock_conn.execute.return_value = mock_result
    mock_engine.connect.return_value.__enter__.return_value = mock_conn
    mock_get_engine.return_value = mock_engine
    
    client = DBClient("test", "sqlite://")
    client.query_and_print("SELECT 1")
    mock_console.print.assert_called_with("[yellow]Query returned no rows.[/yellow]")

@patch("shane_skills.integrations.db_client.Table")
@patch("shane_skills.integrations.db_client.console")
@patch("shane_skills.integrations.db_client.DBClient._get_engine")
def test_query_and_print_success(mock_get_engine, mock_console, mock_table):
    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_result = MagicMock()
    mock_result.keys.return_value = ["id", "name"]
    mock_result.fetchmany.return_value = [(1, "A"), (2, None)]
    mock_conn.execute.return_value = mock_result
    mock_engine.connect.return_value.__enter__.return_value = mock_conn
    mock_get_engine.return_value = mock_engine
    
    mock_table_instance = MagicMock()
    mock_table.return_value = mock_table_instance
    
    client = DBClient("test", "sqlite://")
    client.query_and_print("SELECT *", limit=5)
    
    mock_result.fetchmany.assert_called_with(5)
    mock_table_instance.add_column.assert_any_call("id")
    mock_table_instance.add_column.assert_any_call("name")
    mock_table_instance.add_row.assert_any_call("1", "A")
    mock_table_instance.add_row.assert_any_call("2", "[dim]NULL[/dim]")
    mock_console.print.assert_any_call(mock_table_instance)

@patch("shane_skills.integrations.db_client.console")
def test_print_schema_error(mock_console):
    client = DBClient("test", "sqlite://")
    with patch.object(client, "_generic_list_tables", side_effect=Exception("err")):
        with pytest.raises(SystemExit):
            client.print_schema()
        mock_console.print.assert_called()

@patch("shane_skills.integrations.db_client.console")
def test_print_schema_empty(mock_console):
    client = DBClient("test", "sqlite://")
    with patch.object(client, "_generic_list_tables", return_value=([], [])):
        client.print_schema()
        mock_console.print.assert_called_with("[yellow]No tables found for this connection.[/yellow]")

@patch("shane_skills.integrations.db_client.Table")
@patch("shane_skills.integrations.db_client.console")
def test_print_schema_success(mock_console, mock_table):
    client = DBClient("test", "sqlite://")
    mock_table_instance = MagicMock()
    mock_table.return_value = mock_table_instance
    
    with patch.object(client, "_generic_list_tables", return_value=([("public", "users")], ["Schema", "Table"])):
        client.print_schema()
        mock_table_instance.add_column.assert_any_call("Schema")
        mock_table_instance.add_column.assert_any_call("Table")
        mock_table_instance.add_row.assert_called_with("public", "users")
        mock_console.print.assert_any_call(mock_table_instance)

@patch("shane_skills.integrations.db_client.DBClient._get_engine")
def test_oracle_list_tables(mock_get_engine):
    client = DBClient("test", "oracle+oracledb://")
    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [("HR", "EMP", 100, "date")]
    mock_conn.execute.return_value = mock_result
    mock_engine.connect.return_value.__enter__.return_value = mock_conn
    mock_get_engine.return_value = mock_engine
    
    rows, cols = client._oracle_list_tables()
    assert rows == [("HR", "EMP", 100, "date")]
    assert cols == ["Owner", "Table Name", "Num Rows", "Last Analyzed"]

@patch("sqlalchemy.inspect")
@patch("shane_skills.integrations.db_client.DBClient._get_engine")
def test_generic_list_tables(mock_get_engine, mock_inspect):
    client = DBClient("test", "sqlite://")
    mock_inspector = MagicMock()
    mock_inspector.get_schema_names.return_value = ["public", "information_schema"]
    mock_inspector.get_table_names.return_value = ["users"]
    mock_inspect.return_value = mock_inspector
    
    rows, cols = client._generic_list_tables()
    assert rows == [("public", "users")]
    assert cols == ["Schema", "Table Name"]

@patch("shane_skills.integrations.db_client.console")
def test_print_describe_error(mock_console):
    client = DBClient("test", "sqlite://")
    with patch.object(client, "_generic_describe", side_effect=Exception("err")):
        with pytest.raises(SystemExit):
            client.print_describe("t")
        mock_console.print.assert_called()

@patch("shane_skills.integrations.db_client.console")
def test_print_describe_empty(mock_console):
    client = DBClient("test", "sqlite://")
    with patch.object(client, "_generic_describe", return_value=([], [])):
        client.print_describe("t")
        mock_console.print.assert_called()

@patch("shane_skills.integrations.db_client.Table")
@patch("shane_skills.integrations.db_client.console")
def test_print_describe_success(mock_console, mock_table):
    client = DBClient("test", "sqlite://")
    mock_table_instance = MagicMock()
    mock_table.return_value = mock_table_instance
    
    with patch.object(client, "_generic_describe", return_value=([("id", "int", "NO", None)], ["Col", "Type", "Null", "Def"])):
        client.print_describe("t")
        mock_table_instance.add_row.assert_called_with("id", "int", "NO", "[dim]NULL[/dim]")
        mock_console.print.assert_any_call(mock_table_instance)

@patch("shane_skills.integrations.db_client.DBClient._get_engine")
def test_oracle_describe(mock_get_engine):
    client = DBClient("test", "oracle+oracledb://")
    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [("ID", "NUMBER", 22, "N", "")]
    mock_conn.execute.return_value = mock_result
    mock_engine.connect.return_value.__enter__.return_value = mock_conn
    mock_get_engine.return_value = mock_engine
    
    rows, cols = client._oracle_describe("HR.EMP")
    assert rows == [("ID", "NUMBER", 22, "N", "")]
    # Test without owner
    client._oracle_describe("EMP")

@patch("sqlalchemy.inspect")
@patch("shane_skills.integrations.db_client.DBClient._get_engine")
def test_generic_describe(mock_get_engine, mock_inspect):
    client = DBClient("test", "sqlite://")
    mock_inspector = MagicMock()
    mock_inspector.get_columns.return_value = [{"name": "id", "type": "int", "nullable": False, "default": "1"}]
    mock_inspect.return_value = mock_inspector
    
    rows, cols = client._generic_describe("t")
    assert rows == [("id", "int", "NO", "1")]

@patch("shane_skills.integrations.db_client.Table")
@patch("shane_skills.integrations.db_client.console")
@patch("shane_skills.integrations.db_client.Config")
def test_print_connections(mock_config, mock_console, mock_table):
    mock_cfg = MagicMock()
    mock_cfg.get_db_connections.return_value = {
        "c1": {"host": "h", "port": "1", "driver": "d", "username": "u"}
    }
    mock_config.load.return_value = mock_cfg
    
    mock_table_instance = MagicMock()
    mock_table.return_value = mock_table_instance
    
    DBClient.print_connections()
    mock_table_instance.add_row.assert_called_with("c1", "d", "h:1/", "u")
    mock_console.print.assert_any_call(mock_table_instance)

@patch("shane_skills.integrations.db_client.console")
@patch("shane_skills.integrations.db_client.Config")
def test_print_connections_empty(mock_config, mock_console):
    mock_cfg = MagicMock()
    mock_cfg.get_db_connections.return_value = {}
    mock_config.load.return_value = mock_cfg
    DBClient.print_connections()
    mock_console.print.assert_called()

@patch("shane_skills.integrations.db_client.DBClient.from_config")
@patch("shane_skills.integrations.db_client.console")
def test_test_connection_success(mock_console, mock_from_config):
    mock_client = MagicMock()
    mock_client._is_oracle.return_value = False
    mock_from_config.return_value = mock_client
    
    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_conn
    mock_client._get_engine.return_value = mock_engine
    
    assert DBClient.test_connection("test") is True

@patch("shane_skills.integrations.db_client.DBClient.from_config")
@patch("shane_skills.integrations.db_client.console")
def test_test_connection_oracle(mock_console, mock_from_config):
    mock_client = MagicMock()
    mock_client._is_oracle.return_value = True
    mock_from_config.return_value = mock_client
    
    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_conn
    mock_client._get_engine.return_value = mock_engine
    
    assert DBClient.test_connection("test") is True

@patch("shane_skills.integrations.db_client.DBClient.from_config")
@patch("shane_skills.integrations.db_client.console")
def test_test_connection_failure(mock_console, mock_from_config):
    mock_from_config.side_effect = Exception("err")
    assert DBClient.test_connection("test") is False
    mock_console.print.assert_called()

@patch("shane_skills.integrations.db_client.console")
@patch("shane_skills.integrations.db_client.Table")
def test_print_schema_oracle(mock_table, mock_console):
    client = DBClient("test", "sqlite://")
    with patch.object(client, "_is_oracle", return_value=True):
        with patch.object(client, "_oracle_list_tables", return_value=([("HR", "EMP")], ["Schema", "Table"])):
            client.print_schema()
            mock_console.print.assert_called()

@patch("shane_skills.integrations.db_client.console")
@patch("shane_skills.integrations.db_client.Table")
def test_print_describe_oracle(mock_table, mock_console):
    client = DBClient("test", "sqlite://")
    with patch.object(client, "_is_oracle", return_value=True):
        with patch.object(client, "_oracle_describe", return_value=([("ID", "NUMBER", "NO", "")], ["Col", "Type", "Null", "Def"])):
            client.print_describe("t")
            mock_console.print.assert_called()
