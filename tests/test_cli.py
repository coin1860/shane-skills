import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from shane_skills.cli import main

@pytest.fixture
def runner():
    return CliRunner()

def test_init_command(runner):
    with patch("shane_skills.init_cmd.run_init") as mock_init:
        result = runner.invoke(main, ["init", "--target", "/tmp", "--profile", "copilot", "--dry-run"])
        assert result.exit_code == 0
        mock_init.assert_called_once_with(target="/tmp", profile="copilot", dry_run=True)

def test_list_command(runner):
    with patch("shane_skills.init_cmd.list_skills") as mock_list:
        result = runner.invoke(main, ["list", "--profile", "opencode"])
        assert result.exit_code == 0
        mock_list.assert_called_once_with(profile="opencode")

@patch("shane_skills.integrations.jira_client.JiraClient")
def test_jira_fetch(mock_jira_client, runner):
    mock_instance = MagicMock()
    mock_jira_client.from_config.return_value = mock_instance
    result = runner.invoke(main, ["jira", "fetch", "FSR-123", "--json"])
    assert result.exit_code == 0
    mock_instance.print_issue.assert_called_once_with("FSR-123", as_json=True)

@patch("shane_skills.integrations.jira_client.JiraClient")
def test_jira_fetch_compat(mock_jira_client, runner):
    mock_instance = MagicMock()
    mock_jira_client.from_config.return_value = mock_instance
    result = runner.invoke(main, ["jira-fetch", "FSR-123"])
    assert result.exit_code == 0
    mock_instance.print_issue.assert_called_once_with("FSR-123")

@patch("shane_skills.integrations.jira_client.JiraClient")
def test_jira_search(mock_jira_client, runner):
    mock_instance = MagicMock()
    mock_jira_client.from_config.return_value = mock_instance
    mock_instance.search.return_value = ["res"]
    result = runner.invoke(main, ["jira", "search", "test", "--limit", "10"])
    assert result.exit_code == 0
    mock_instance.search.assert_called_once_with("test", limit=10)
    mock_instance.print_search_results.assert_called_once_with(["res"])

@patch("shane_skills.integrations.jira_client.JiraClient")
def test_jira_jql(mock_jira_client, runner):
    mock_instance = MagicMock()
    mock_jira_client.from_config.return_value = mock_instance
    mock_instance.jql.return_value = ["res"]
    result = runner.invoke(main, ["jira", "jql", "query", "--limit", "5"])
    assert result.exit_code == 0
    mock_instance.jql.assert_called_once_with("query", limit=5)
    mock_instance.print_search_results.assert_called_once_with(["res"])

@patch("shane_skills.integrations.jira_client.JiraClient")
def test_jira_create(mock_jira_client, runner):
    mock_instance = MagicMock()
    mock_jira_client.from_config.return_value = mock_instance
    mock_instance.create_issue.return_value = {"res": "ok"}
    result = runner.invoke(main, ["jira", "create", "--project", "P", "--summary", "S", "--description", "D", "--type", "Bug"])
    assert result.exit_code == 0
    mock_instance.create_issue.assert_called_once_with(project="P", summary="S", description="D", issue_type="Bug")
    mock_instance.print_created_issue.assert_called_once_with({"res": "ok"})

@patch("shane_skills.integrations.confluence_client.ConfluenceClient")
def test_confluence_search(mock_conf_client, runner):
    mock_instance = MagicMock()
    mock_conf_client.from_config.return_value = mock_instance
    result = runner.invoke(main, ["confluence", "search", "query", "--space", "S", "--limit", "3"])
    assert result.exit_code == 0
    mock_instance.search_and_print.assert_called_once_with(query="query", space="S", limit=3)

@patch("shane_skills.integrations.confluence_client.ConfluenceClient")
def test_confluence_page(mock_conf_client, runner):
    mock_instance = MagicMock()
    mock_conf_client.from_config.return_value = mock_instance
    result = runner.invoke(main, ["confluence", "page", "123"])
    assert result.exit_code == 0
    mock_instance.print_page.assert_called_once_with("123")

@patch("shane_skills.integrations.confluence_client.ConfluenceClient")
def test_confluence_create(mock_conf_client, runner):
    mock_instance = MagicMock()
    mock_conf_client.from_config.return_value = mock_instance
    mock_instance.create_page.return_value = {"res": "ok"}
    result = runner.invoke(main, ["confluence", "create", "--parent", "1", "--title", "T", "--content", "C"])
    assert result.exit_code == 0
    mock_instance.create_page.assert_called_once_with(parent_id="1", title="T", content="C")
    mock_instance.print_created_page.assert_called_once_with({"res": "ok"})

@patch("shane_skills.integrations.web_client.WebClient")
def test_web_fetch(mock_web_client, runner):
    mock_instance = MagicMock()
    mock_web_client.return_value = mock_instance
    result = runner.invoke(main, ["web", "fetch", "http://example.com", "--max-chars", "100"])
    assert result.exit_code == 0
    mock_instance.print_fetch.assert_called_once_with("http://example.com", max_chars=100)

@patch("shane_skills.integrations.db_client.DBClient")
def test_db_query(mock_db_client, runner):
    mock_instance = MagicMock()
    mock_db_client.from_config.return_value = mock_instance
    result = runner.invoke(main, ["db", "query", "SELECT 1", "--connection", "c", "--limit", "5"])
    assert result.exit_code == 0
    mock_db_client.from_config.assert_called_once_with("c")
    mock_instance.query_and_print.assert_called_once_with(sql="SELECT 1", limit=5)

@patch("shane_skills.integrations.db_client.DBClient")
def test_db_schema(mock_db_client, runner):
    mock_instance = MagicMock()
    mock_db_client.from_config.return_value = mock_instance
    result = runner.invoke(main, ["db", "schema", "--connection", "c"])
    assert result.exit_code == 0
    mock_instance.print_schema.assert_called_once()

@patch("shane_skills.integrations.db_client.DBClient")
def test_db_describe(mock_db_client, runner):
    mock_instance = MagicMock()
    mock_db_client.from_config.return_value = mock_instance
    result = runner.invoke(main, ["db", "describe", "t", "--connection", "c"])
    assert result.exit_code == 0
    mock_instance.print_describe.assert_called_once_with("t")

@patch("shane_skills.integrations.db_client.DBClient")
def test_db_connections(mock_db_client, runner):
    result = runner.invoke(main, ["db", "connections"])
    assert result.exit_code == 0
    mock_db_client.print_connections.assert_called_once()

@patch("shane_skills.integrations.db_client.DBClient")
def test_db_test(mock_db_client, runner):
    result = runner.invoke(main, ["db", "test", "--connection", "c"])
    assert result.exit_code == 0
    mock_db_client.test_connection.assert_called_once_with("c")

@patch("shane_skills.gui.settings_tui.run_tui")
def test_config_tui(mock_run_tui, runner):
    result = runner.invoke(main, ["config", "--tui"])
    assert result.exit_code == 0
    mock_run_tui.assert_called_once()

@patch("shane_skills.gui.settings_app.run_gui")
def test_config_gui(mock_run_gui, runner):
    result = runner.invoke(main, ["config"])
    assert result.exit_code == 0
    mock_run_gui.assert_called_once()

@patch("shane_skills.cli.console")
@patch("shane_skills.gui.settings_tui.run_tui")
def test_config_gui_fallback(mock_run_tui, mock_console, runner):
    with patch("shane_skills.gui.settings_app.run_gui", side_effect=ImportError("No module")):
        result = runner.invoke(main, ["config"])
        assert result.exit_code == 0
        mock_run_tui.assert_called_once()
